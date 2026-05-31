# Design-Pattern Implementation Review — NFL Betting System

**Date:** 2026-05-31
**Scope:** `src/` (all listed subpackages), `scripts/`, `agents/`, `dashboard/`
**Constraint:** Read-only review. No source code was modified.

---

## Architecture Overview

The codebase is a small Python pipeline that collects NFL odds/stats, engineers
features, runs ML/heuristic agents, applies betting strategies, sizes bets with
the Kelly criterion, and notifies/persists results. A `MainOrchestrator`
(`src/orchestrator/main_orchestrator.py`) sequences the whole flow.

Pattern usage today is **thin and inconsistent**. There is genuine intent behind
several patterns — a Strategy hierarchy with a registry, a Singleton registry, an
in-memory cache (Proxy-ish), a Circuit Breaker (resilience Decorator), and an
abstract `BaseAgent` template — but most are either implemented incorrectly,
unused, or undermined by a parallel hardcoded path. The dominant anti-pattern is
the **orchestrator as a god-object that hardwires concrete classes** via
function-local imports, hardcoded credentials, and direct `sqlite3` calls, which
defeats most of the abstraction the patterns are trying to provide.

The strongest pattern is the Strategy hierarchy (`BettingStrategy` + subclasses);
the weakest are the creational patterns (no real Factory, a broken/duplicated
Singleton story) and the domain layer (no DTOs, no Repository — data flows as
untyped `Dict` everywhere).

Two notable global issues that color everything below:
- **No DTO / value objects anywhere.** `grep` for `dataclass`, `NamedTuple`,
  `TypedDict`, `pydantic`, `BaseModel` returns nothing. All inter-layer data is
  raw `Dict[str, Any]`, merged ad hoc (e.g. `{**pred, **result}` at
  `main_orchestrator.py:90`).
- **Duplicated `BaseAgent` hierarchies.** `src/agents/base.py` (method
  `predict`) and `agents/base_agent.py` (method `run`) are two incompatible agent
  abstractions with no shared contract.

---

## Prioritized Findings

### 1. Strategy + Registry are bypassed by a hardcoded selector — Importance 9/10

**File:** `src/strategy_registry.py`
**Classes:** `StrategyRegistry`, `BettingStrategy` + subclasses, `select_strategy`

The Strategy pattern itself is correct and appropriate: `BettingStrategy.evaluate`
(line 42) is an abstract operation, and `ValueBettingStrategy`,
`ArbitrageStrategy`, `MLStrategy` are clean polymorphic implementations. The
registry (`register`/`get`/`get_all`, lines 19-30) is a reasonable Registry
pattern, and the orchestrator correctly iterates `registry.get_all()`
(`main_orchestrator.py:87`).

The problem is that a **parallel hardcoded factory** exists alongside the
registry and is what callers actually use:

```python
# strategy_registry.py:91
def select_strategy(strategy_type: str):
    if strategy_type == "value":
        return ValueBettingStrategy()
    elif strategy_type == "arbitrage":
        return ArbitrageStrategy()
    elif strategy_type == "ml":
        return MLStrategy()
    else:
        return None
```

`scripts/run_backtest.py:5,9` imports `select_strategy`, not the registry. So the
system has two sources of truth for "which strategies exist," and adding a new
strategy requires editing the `if/elif` chain — exactly what the registry was
supposed to eliminate (open/closed violation).

**Recommendation:** Delete `select_strategy` and route every lookup through the
registry. Even better, make registration declarative so new strategies self-register:

```python
def register_strategy(name):
    def deco(cls):
        registry.register(name, cls())
        return cls
    return deco

@register_strategy("value")
class ValueBettingStrategy(BettingStrategy): ...

def select_strategy(name):          # keep name, delegate to registry
    return registry.get(name)
```

Now `run_backtest.py` and the orchestrator share one registry and adding a
strategy is one decorator, no `if/elif` edit.

---

### 2. Broken / leaky Singleton on `StrategyRegistry` — Importance 8/10

**File:** `src/strategy_registry.py:8-17`

```python
class StrategyRegistry:
    _instance = None
    _strategies: Dict[str, Any] = {}      # class attribute — shared by ALL instances

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

Issues:
- `_strategies` is a **class attribute**, so even if `__new__` failed to enforce
  the singleton, all instances would still share state — the singleton is doing
  nothing useful. The instance-uniqueness and the shared-state are conflated.
- `__new__` runs every construction but `__init__` (none defined) would re-run on
  every `StrategyRegistry()` call if added later — a classic Singleton-via-`__new__`
  footgun.
- A module-level instance `registry = StrategyRegistry()` (line 67) already exists,
  so the Singleton machinery is redundant: in Python a module-level object *is*
  the idiomatic singleton.

**Recommendation:** Drop `__new__` and the class-level `_strategies`; make
`_strategies` an instance attribute initialized in `__init__`, and rely on the
module-level `registry` as the single shared instance:

```python
class StrategyRegistry:
    def __init__(self):
        self._strategies: dict[str, Any] = {}
    ...
registry = StrategyRegistry()   # the one shared instance
```

This is simpler and removes the false sense of safety the `__new__` guard gives.

---

### 3. Orchestrator is a god-object that hardwires concrete classes (missing Factory / DI) — Importance 9/10

**File:** `src/orchestrator/main_orchestrator.py`

The orchestrator is a reasonable **Facade** in spirit (`run_pipeline` exposes one
simple entry point over a six-step flow, lines 23-45), but its internals defeat
every abstraction:

- Each step does a **function-local import + direct instantiation** of a concrete
  class: `OddsAPIClient`/`SportsDataClient` (lines 60-64), `FeatureEngineer`
  (74), `EnsembleAgent` (80), `Notifier` (106), `calculate_kelly` (95). This makes
  the pipeline impossible to test or reconfigure without monkeypatching imports.
- **Hardcoded secret:** `OddsAPIClient(api_key="hardcoded_key_123")` (line 63) —
  ignores `src/config/settings.py` which already reads `ODDS_API_KEY` from env.
- **Direct persistence:** `_save_results` (lines 110-117) opens `sqlite3` inline
  with raw SQL, duplicating `DataPipeline` (`src/features/data_pipeline.py`) and
  bypassing it entirely.
- `self.data_pipeline`, `self.feature_engineer`, `self.models`, `self.strategies`
  are initialized to `None`/`{}` (lines 17-20) and **never used** — dead fields
  hinting at an intended-but-unbuilt DI design.

**Recommendation:** Introduce constructor injection (a simple Factory or just
passing collaborators in), and read config from `settings`:

```python
class MainOrchestrator:
    def __init__(self, clients=None, feature_engineer=None,
                 agent=None, notifier=None, repo=None):
        self.clients = clients or default_clients(settings)
        self.feature_engineer = feature_engineer or FeatureEngineer()
        self.agent = agent or EnsembleAgent()
        self.notifier = notifier or Notifier()
        self.repo = repo or DataPipeline()
```

Now tests inject fakes, secrets come from `settings`, and persistence goes
through the repository. A small `client_factory(settings)` would centralize the
API-client construction (the missing Factory).

---

### 4. CircuitBreaker (resilience Decorator) is defined but never used — Importance 7/10

**File:** `src/self_healing/circuit_breaker.py`

The `CircuitBreaker` class (lines 17-52) is a correct, idiomatic state-machine
implementation (CLOSED/OPEN/HALF_OPEN, timeout-based recovery). However:

- `grep` across `src/`, `agents/`, `dashboard/`, `scripts/` shows **zero usages** —
  it is dead resilience code.
- It imports `wraps` and `Enum` (lines 5-6) suggesting an intended `@decorator`
  form, but only exposes a `.call(func, *args)` wrapper, not a decorator. The
  resilience-Decorator pattern is half-built.
- HALF_OPEN handling is subtly incomplete: a single success in HALF_OPEN closes
  the circuit (`_on_success`, line 43-45), but there is no limit on concurrent
  HALF_OPEN trial calls.

The natural place to apply it — the network calls in
`src/api/odds_api_client.py` and `src/api/sports_data_client.py` — uses bare
`try/except` returning `[]` (e.g. `odds_api_client.py:30-32`), with no breaker,
retry, or backoff.

**Recommendation:** Expose a decorator form and wrap the API clients:

```python
def circuit(breaker):
    def deco(fn):
        @wraps(fn)
        def wrapper(*a, **k):
            return breaker.call(fn, *a, **k)
        return wrapper
    return deco

# odds_api_client.py
@circuit(odds_breaker)
def get_odds(self, week): ...
```

This turns a defined-but-dead pattern into actual resilience at the integration
boundary, importance bumped by the fact that these are flaky third-party APIs.

---

### 5. Proxy/cache (`OddsCache`) is instantiated but never consulted — Importance 7/10

**File:** `src/utils/odds_cache.py`; **use site:** `src/orchestrator/main_orchestrator.py:16`

`OddsCache` (lines 9-35) is a correct TTL cache (get checks expiry and evicts,
set stamps time). It is the closest thing to a caching **Proxy** in the codebase.
But:

- The orchestrator does `self.cache = OddsCache()` (line 16) and then **never
  calls `get`/`set`** — `_collect_data` (lines 57-69) hits the APIs every run.
- There are two competing cache instances: the per-orchestrator `self.cache` and
  a module-level `_global_cache` (line 39) with `get_cached_odds`/`cache_odds`
  helpers — also unused. Two caches, neither wired in.
- A true Proxy would sit *in front of* `OddsAPIClient` so callers cannot bypass
  it; here the cache is a sibling object that everyone forgets to use.

**Recommendation:** Implement a caching proxy that wraps the client so caching is
unbypassable:

```python
class CachedOddsClient:
    def __init__(self, inner: OddsAPIClient, cache: OddsCache):
        self._inner, self._cache = inner, cache
    def get_odds(self, week):
        key = f"odds:{week}"
        hit = self._cache.get(key)
        if hit is not None:
            return hit
        data = self._inner.get_odds(week)
        self._cache.set(key, data)
        return data
```

Inject `CachedOddsClient` where the raw client is used today. Delete the unused
`_global_cache` to remove the second source of truth.

---

### 6. No Repository pattern — data access is scattered and duplicated — Importance 8/10

**Files:** `src/features/data_pipeline.py`, `src/orchestrator/main_orchestrator.py:110-117`

`DataPipeline` is *almost* a Repository (it owns the `games` table and exposes
`save_game`/`get_games`), which is appropriate. Problems:

- It is misplaced under `src/features/` (feature engineering), not a data/persistence
  package, and `fetch_and_store` (lines 61-67) mixes API fetching *into* the
  repository with another hardcoded `api_key="key"`, blending Repository with a
  data-source — two responsibilities.
- The orchestrator's `_save_results` opens its own `sqlite3` connection with raw
  SQL (lines 112-116), **completely bypassing** `DataPipeline`. So persistence
  logic lives in two places against the same DB file (`betting.db`).
- Every method opens/closes its own connection with no connection management,
  transactions, or a shared interface — there is no `Repository` abstraction that
  callers depend on.

**Recommendation:** Define a `GameRepository` interface, keep only persistence
concerns in it (move `fetch_and_store`'s API call out to the service/orchestrator
layer), and route **all** writes (including `_save_results`) through it:

```python
class GameRepository(Protocol):
    def save_game(self, week: int, data: dict) -> None: ...
    def get_games(self, week: int) -> list[dict]: ...
    def save_result(self, result: dict) -> None: ...
```

Inject one repository instance; delete the inline `sqlite3` in the orchestrator.

---

### 7. No DTO / value objects — untyped `Dict` everywhere — Importance 6/10

**Files:** pervasive; representative: `strategy_registry.py:42-63`,
`main_orchestrator.py:90`, `ensemble_agent.py:33`

Every boundary passes `Dict[str, Any]`. Strategy results are dicts
(`{"bet": True, "confidence": ..., "type": ...}`), predictions are dicts, and the
orchestrator blends them with `{**pred, **result}` (line 90), which silently
allows key collisions and typos (`"ml_probability"` vs `"probability"` — see the
inconsistency between `feature_engineering.py:19` and consumers). There is no
compile-time or runtime contract.

**Recommendation:** Introduce small `@dataclass` value objects for the key
contracts (`Prediction`, `BetSignal`, `SizedBet`). They document the schema, make
collisions impossible, and give type checkers something to verify:

```python
@dataclass(frozen=True)
class BetSignal:
    bet: bool
    confidence: float
    strategy_type: str
```

Start with the Strategy return type since it is the most-copied dict shape.

---

### 8. Duplicated, incompatible agent hierarchies (Template Method split in two) — Importance 6/10

**Files:** `src/agents/base.py` vs `agents/base_agent.py`

There are two `BaseAgent` ABCs with **different contracts**: `src/agents/base.py`
mandates `predict(features) -> List[Dict]` (used by `EnsembleAgent`), while
`agents/base_agent.py` mandates `run(data) -> Dict` (used by
`DataCollectorAgent`, `PredictionAgent`). Both use `@abstractmethod` correctly in
isolation (a fine Template Method), but having two parallel package trees
(`src/agents` and top-level `agents`) means agents cannot be used
interchangeably, and `SwarmCoordinator.coordinate` (`swarm_coordinator.py:18-23`)
calls `agent.predict(data)` — which the top-level `run`-based agents do not
implement, so the swarm can only ever hold `src/agents` agents.

**Recommendation:** Collapse to one agent package and one base contract
(pick `predict` or `run`, not both). Have `SwarmCoordinator` depend on that single
interface. This also removes the dead top-level `agents/` package.

---

### 9. Logger factory is fine but is not a Singleton-managed component — Importance 3/10

**File:** `src/utils/logger.py`

`get_logger` (lines 6-17) is a thin **Factory Method** over `logging.getLogger`
and is correct: it guards against duplicate handlers with `if not logger.handlers`.
This is appropriate and needs no Singleton — `logging` already returns the same
logger object per name. Minor: most modules call `logging.getLogger(__name__)`
directly (e.g. `kelly.py:5`, `notifier.py:5`) and **ignore** `get_logger`, so the
nice formatter/handler setup is inconsistently applied across the codebase.

**Recommendation:** Either standardize on `get_logger` everywhere or move handler
configuration into a single `logging.config.dictConfig` call at app startup and
let modules use plain `getLogger`. Pick one; today it is mixed.

---

### 10. `Settings` is a reasonable config singleton but is not actually used — Importance 4/10

**File:** `src/config/settings.py`

`Settings` (lines 6-16) reads all config from env with sensible defaults and is
exported as a module-level singleton `settings` (line 20) — an appropriate,
idiomatic pattern. The issue is purely that **callers ignore it**: API keys are
hardcoded at call sites (`main_orchestrator.py:63`, `data_pipeline.py:64`) and
Kelly fraction defaults are re-declared in `kelly.py:8` rather than read from
`settings.kelly_fraction`. The pattern is correct; adoption is zero.

**Recommendation:** Inject `settings` into the components that need config and
delete the hardcoded literals (ties into findings #3 and #6).

---

## Missing Patterns Worth Adding

- **Observer / event bus (Importance 6/10):** `AuditLogger`
  (`src/audit/audit_logger.py`) and `Notifier` (`src/notifications/notifier.py`)
  are both reactive sinks that the orchestrator must call imperatively
  (`_notify`, line 103). An Observer/pub-sub would let audit, notification, and
  the dashboard subscribe to pipeline events (`bet_placed`, `pipeline_complete`)
  without the orchestrator knowing about each sink. `Notifier` even has an unused
  `self.channels = []` (notifier.py:12) hinting at a multi-subscriber design that
  was never built.

- **Chain of Responsibility for bet filtering (Importance 5/10):** Bet
  acceptance currently mixes thresholds across `strategy.evaluate`, Kelly sizing,
  and `settings.min_edge`/`max_bet_size` (unused). A small chain of validators
  (min-edge → bankroll cap → max-bet-size → exposure limit) would make the
  risk rules explicit, ordered, and individually testable instead of implicit in
  scattered `if` checks.

- **Command pattern for the pipeline steps (Importance 4/10):** The six
  `_collect / _engineer / _predict / _apply / _size / _notify` steps in
  `run_pipeline` are a fixed sequence. Modeling each as a `Step`/Command object in
  a list would enable retry, logging, skipping, and reordering uniformly — and
  pairs naturally with the CircuitBreaker (finding #4) wrapping each command.

- **Adapter for API clients (Importance 5/10):** `OddsAPIClient` and
  `SportsDataClient` expose different method names/shapes (`get_odds` vs
  `get_stats`, different auth: query param vs header). A common
  `DataSource`/Adapter interface would let `_collect_data` treat them uniformly
  and make adding a new provider a drop-in.

---

## Items Unable to Verify

- Whether any runtime wiring (e.g. dependency-injection container, plugin loader)
  exists outside the reviewed Python files (config files, entry points). Only the
  in-scope `.py` files were inspected.
- Actual behavior of `SwarmCoordinator` with mixed agent types at runtime — no
  call site instantiates it in the reviewed code, so the incompatibility in
  finding #8 is inferred from the interfaces, not observed at runtime.
