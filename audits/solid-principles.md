# SOLID Principles Review — NFL Betting System

**Scope:** `src/` (agents, api, audit, backtesting, betting, config, features, health, learning, notifications, orchestrator, self_healing, strategy_registry.py, swarms, utils, visualization), `scripts/`, `agents/`, `dashboard/`.
**Date:** 2026-05-31
**Method:** Static, read-only inspection. No source was modified. Every `file:line` below was read directly and verified against file contents. Claims that could not be confirmed are explicitly marked **Unable to verify**.

> Scope note: `src/strategy_registry.py` is a single 675-line module (not a package). `src/orchestrator/` contains only `master_pipeline.py` (there is no `main_orchestrator.py`). `src/swarms/swarm_base.py` is a 159-line module whose `SwarmBase` is not an `ABC`. Across the entire scope there are **zero** `isinstance` checks and **zero** `NotImplementedError` raises, which meaningfully limits the Liskov surface (see the L section).

---

## Summary Table

| Principle | Findings | Importance (max) | Worst offenders |
|-----------|---------:|:----------------:|-----------------|
| **S** — Single Responsibility | 3 | 9/10 | `dashboard/app.py` (DB + HTTP + AI + presentation in one module), `src/orchestrator/master_pipeline.py` (`MasterPipeline`), `agents/api_integrations.py` (`APIIntegrations`) |
| **O** — Open/Closed | 3 | 7/10 | `dashboard/app.py:596` (`get_ai_analysis` provider chain), `src/orchestrator/master_pipeline.py:310` (channel chain), `agents/api_integrations.py` (per-API methods) |
| **L** — Liskov Substitution | 1 | 3/10 | `src/swarms/swarm_base.py` (`SwarmBase` — unused base, no real subclass contract) |
| **I** — Interface Segregation | 1 | 4/10 | `src/agents/base_agent.py` (`BaseAgent` lifecycle-only base — mostly OK; minor) |
| **D** — Dependency Inversion | 3 | 9/10 | `src/orchestrator/master_pipeline.py` (concrete imports + sqlite3 inside every stage), `dashboard/app.py:233` (hardcoded sqlite3), `src/notifications/email_sender.py:21-27` (env-coupled SMTP) |

**Positive note:** `StrategyRegistry` in `src/strategy_registry.py:197` is a clean, single-purpose, well-factored class (load/save/add/update/query with injectable `registry_path`). It is the quality bar the rest of the codebase should meet.

---

## S — Single Responsibility

### S1. `dashboard/app.py` mixes persistence, HTTP, AI calls, business logic and presentation — **9/10**
**Location:** `dashboard/app.py` (2492 lines; module-level functions + one large UI helper set).
**Problem:** A single Streamlit module owns every layer:
- **Persistence:** `load_games()` opens `sqlite3.connect("data/nfl.db")` directly with a hardcoded path and inline SQL (lines 230–240).
- **External AI HTTP:** `_get_grok_analysis` (622) posts to `api.x.ai`, `_get_claude_analysis` (680), `_get_openai_analysis` (730) — provider SDK/HTTP logic lives inside the dashboard.
- **Secrets:** `get_secret()` (97) reads `st.secrets`/`os.getenv`.
- **Presentation:** ~25 `render_*`/tab functions and CSS.
- **Domain math:** odds conversion helpers `american_to_decimal` (1126), `calculate_parlay_odds` (1132).

Any change to a query, an AI endpoint, or an odds formula forces edits to the UI file, and none of it is testable without a DB and live network.

**Remediation:** Extract collaborators and keep the module presentation-only:
```python
# dashboard/services.py
class GameRepository:        # sqlite only
    def load_games(self) -> pd.DataFrame: ...
class AIAnalyst:             # one HTTP/SDK call site per provider
    def analyze(self, game) -> str: ...
class OddsMath:              # pure functions
    @staticmethod
    def american_to_decimal(o): ...
```
The render functions then receive already-loaded data.

### S2. `MasterPipeline` coordinates *and* implements every low-level adapter — **8/10**
**Location:** `src/orchestrator/master_pipeline.py`, `class MasterPipeline` (102).
**Problem:** Beyond legitimately sequencing stages (the `self.stages` list at 120–129 is good design), the class also *is* the persistence layer and the notifier: `_stage_persistence` opens `sqlite3.connect(...)` inline (262), `_save_predictions` (293) and `_save_bets` (300) each re-open their own sqlite connection, and `_send_email_alert` / `_send_slack_alert` (582/604) embed channel logic. The orchestrator should delegate persistence and notification to injected services, not contain them.
**Aggravating duplication:** `_initialize_components` is defined twice (284 and 467); `_calculate_kelly_stakes` (677) is shadowed by a dead `_calculate_kelly_stakes_OLD` (719). Duplicate `def`s mean the earlier definition is silently discarded by Python — dead, confusing code that obscures responsibilities.
**Remediation:** Inject `repository`, `notifier`, and `kelly` collaborators; delete the `_OLD`/duplicate methods; keep `MasterPipeline` to stage orchestration only.

### S3. `APIIntegrations` is a single class fused to three unrelated providers + caching — **6/10**
**Location:** `agents/api_integrations.py`, `class APIIntegrations` (11).
**Problem:** One class reaches into The Odds API (`get_odds`, 21), OpenWeatherMap (`get_weather`, 30), and NewsAPI (`get_news`, 39), each building URLs and calling `requests.get` inline, while also implementing a TTL cache (`_get_cached`). Three independent integration responsibilities plus caching live in one type, so a change to any provider touches the shared class.
**Remediation:** One small client class per provider behind a common `fetch()` contract, and a separate `CachingClient` decorator that wraps any client.

---

## O — Open/Closed

### O1. AI-provider selection via `if/elif` on a `provider` string — **7/10**
**Location:** `dashboard/app.py`, `get_ai_analysis` (594): `if provider == "grok"` / `elif "claude"` / `elif "openai"` / `elif "gpt4"` / `else` (596–605).
**Problem:** Adding a provider requires editing this function *and* writing a new `_get_*_analysis`. (Also note dead code: the `return None` at 607 and `return _get_grok_analysis(...)` at 609 are unreachable after the `if/elif/else` — a smell that this dispatch has been edited repeatedly.)
**Remediation:** A registry/dict of providers:
```python
PROVIDERS = {
    "grok":   GrokAnalyst(),
    "claude": ClaudeAnalyst(),
    "openai": OpenAIAnalyst(),
}
def get_ai_analysis(game, provider="grok"):
    return PROVIDERS.get(provider, PROVIDERS["grok"]).analyze(game)
```
New providers register without touching existing code.

### O2. Notification channel dispatch via `if/elif` on channel name — **6/10**
**Location:** `src/orchestrator/master_pipeline.py`, `_send_notifications` (307): `for channel in channels: if channel == "email": ... elif channel == "slack": ...` (311–314).
**Problem:** Each new channel (SMS, webhook, desktop — senders for several already exist under `src/notifications/`) requires editing this branch plus adding a `_send_*` method on the pipeline. Extension forces modification of the orchestrator.
**Remediation:** Map channel name to a `Notifier` object and iterate:
```python
NOTIFIERS = {"email": EmailSender(), "slack": SlackSender(), "sms": SMSSender()}
for name in channels:
    if n := NOTIFIERS.get(name):
        n.send(context)
```

### O3. `APIIntegrations` adds new data sources only by editing the class — **5/10**
**Location:** `agents/api_integrations.py` (`get_odds`/`get_weather`/`get_news`, 21/30/39).
**Problem:** Each external source is a hardcoded method on one class; a new source means a new method on the existing class rather than a new pluggable client. This is the OCP face of S3.
**Remediation:** Same as S3 — a provider interface + registry so sources are added by registration, not class edits.

---

## L — Liskov Substitution

### L1. `SwarmBase` is an unused base class — no real substitution contract exists — **3/10**
**Location:** `src/swarms/swarm_base.py`, `class SwarmBase` (36).
**Problem:** `SwarmBase` defines a consensus contract (`make_decision`/`_collect_votes`/`_reach_consensus`), but **nothing inherits it**: `ConsensusSwarm` (`consensus_swarm.py:9`), `PredictionPipeline` (`prediction_pipeline.py:12`), `ValidationSwarm` (`validation_swarm.py:15`) and `StrategyGenerationSwarm` (`strategy_generation_swarm.py:14`) are all standalone classes. There is therefore no LSP violation in practice, but the base is dead weight that misleads readers into thinking a polymorphic swarm hierarchy exists. (`_collect_votes` at 116–123 also returns hardcoded `"approve"`/`0.8` stubs, so even direct use would not honor any contract.)
**Remediation:** Either make the real swarms subclass `SwarmBase` and conform to its contract, or delete `SwarmBase`. As-is it is a phantom abstraction.
**Note on the rest of L:** With no `isinstance` checks, no `NotImplementedError` overrides, and no other shared base hierarchies in the scope, there are no further substitution violations to report. `BaseAgent.run` (`base_agent.py:197`) is a legitimate `@abstractmethod` and is not an LSP problem.

---

## I — Interface Segregation

### I1. `BaseAgent` base is broadly OK; only minor over-provisioning — **4/10**
**Location:** `src/agents/base_agent.py`, `class BaseAgent(ABC)` (58).
**Problem:** This base is actually well-segregated: it forces only one abstract method (`run`, 197) and otherwise supplies optional lifecycle/messaging/memory helpers. The mild ISP concern is that **every** agent inherits tool-registry (`register_tool`/`get_tool`), message-queue, and memory machinery even if a given agent uses none of it, widening the surface each subclass and its tests must understand. This is a low-severity smell, not a forced-stub problem (no subclass is compelled to implement unused abstract methods).
**Remediation (optional):** Split optional concerns into mixins/protocols (`Messaging`, `ToolUsing`, `Memoryful`) and have `BaseAgent` provide only lifecycle + the abstract `run`. Agents opt in to the mixins they need.
**Unable to verify:** whether concrete agents (`research_agent`, `worker_agents`, etc.) actually leave the inherited tool/memory features unused — not all subclasses were read in full.

---

## D — Dependency Inversion

### D1. `MasterPipeline` hard-imports concrete components inside every stage and opens sqlite3 directly — **9/10**
**Location:** `src/orchestrator/master_pipeline.py`. Each stage does an inline `from ... import` of a concrete type and instantiates it:
```
192  pipeline = DataPipeline()                      # _stage_data_collection
201  feature_pipeline = FeaturePipeline()           # _stage_feature_engineering
213  pred_pipeline = PredictionPipeline()           # _stage_model_prediction
225  swarm = ConsensusSwarm()                        # _stage_consensus
249  kelly = KellyCriterion()                        # _stage_risk_management
262  conn = sqlite3.connect(self.config.get("db_path", "data/nfl.db"))   # _stage_persistence
```
**Problem:** The highest-level orchestrator depends directly on every concrete low-level implementation and on `sqlite3`, so it cannot be unit-tested without real components/DB and cannot swap implementations (e.g. a different consensus engine or an in-memory store) without editing the stage methods. The lazy in-method imports also hide the dependency graph.
**Remediation:** Constructor-inject the collaborators against abstractions and resolve them once in a composition root:
```python
class MasterPipeline:
    def __init__(self, data: DataSource, features: FeatureEngine,
                 predictor: Predictor, consensus: ConsensusEngine,
                 kelly: StakeSizer, repo: Repository, notifier: Notifier,
                 config=None): ...
```

### D2. `dashboard/app.py` depends directly on sqlite3 and a hardcoded DB path — **8/10**
**Location:** `dashboard/app.py`, `load_games()` (230–240): `db_path = "data/nfl.db"` then `sqlite3.connect(db_path)` with inline SQL.
**Problem:** Presentation depends directly on a concrete database and a literal path, duplicating persistence knowledge already needed elsewhere; the dashboard can never be rendered/tested against a fake data source.
**Remediation:** Depend on the injected `GameRepository` from S1; the dashboard should never import `sqlite3`. Source the path from config rather than a literal.

### D3. `EmailSender` reads its own environment and binds to SMTP at construction — **7/10**
**Location:** `src/notifications/email_sender.py`, `__init__` (19–27): six `os.getenv(...)` reads; `send()` (29–52) builds and drives `smtplib.SMTP` directly.
**Problem:** The class is its own config source and transport, so callers cannot inject configuration or a fake transport for testing, and switching providers means editing the class. (It is also riddled with duplicate method definitions — `send_bet_alert` at 54 *and* 60, `_format_bet_email` at 71 *and* 121 — where Python silently keeps only the last definition; a correctness/clarity defect alongside the DIP issue.)
**Remediation:** Inject an `EmailConfig` dataclass and an SMTP-transport abstraction:
```python
class EmailSender:
    def __init__(self, config: EmailConfig, transport: SmtpTransport): ...
```
Build `EmailConfig` from env at the composition root, not inside the sender. Remove the duplicate `def`s.

---

## Recommended order of attack
1. **D1 + S2** — introduce a composition root and inject `MasterPipeline`'s stage collaborators; delete the duplicate/`_OLD` methods. This unlocks testing of the central orchestrator and removes the inline sqlite3 coupling.
2. **S1 + D2** — split `dashboard/app.py` into repository / AI-analyst / odds-math services + a presentation-only view.
3. **O1 + O2** — replace the provider and channel `if/elif` chains with small registries (the `StrategyRegistry` pattern already in the codebase is the template).
4. **S3 + O3** — break `APIIntegrations` into one client per provider behind a common interface, with a caching decorator.
5. **D3** — inject config/transport into `EmailSender` and remove its duplicate method definitions.
6. **L1** — either wire the real swarms onto `SwarmBase` or delete the phantom base; **I1** is optional polish.
