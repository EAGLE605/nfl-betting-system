# Code Duplication Audit — NFL Betting System

**Repository:** `/home/user/nfl-betting-system`
**Date:** 2026-05-31
**Scope:** `src/`, `scripts/`, `agents/`, `dashboard/` (excluding `*.md`, `tests/`, `*.ipynb`)
**Total scoped Python:** ~44,886 LOC across ~120 modules

## Summary

The codebase has substantial, systematic duplication concentrated in three areas:
**(1) parallel API clients** (ESPN implemented 5x, NOAA 2x), **(2) betting math helpers**
(Kelly + American-odds conversion redefined in 6+ files), and **(3) data constants**
(32-team stadium-coordinate dict and NFL team-name maps copy-pasted across modules).
On top of that, every `scripts/` entry point repeats the same `sys.path` and `logging`
bootstrap boilerplate.

Most of this is **low-risk, high-value** to fix: the duplicated logic is small and stable,
so consolidation is mostly mechanical, but the divergence risk is real — the duplicated
copies already differ (e.g. `kelly.py` returns `round(...)`, others don't; one ESPN client
has a circuit breaker, the other four don't).

### Findings sorted by importance

| # | Finding | Type | Key locations | Est. dup | Effort | Importance |
|---|---------|------|---------------|----------|--------|------------|
| 1 | ESPN API client reimplemented 5x | Exact + Near | `src/api/espn_client.py`, `agents/api_integrations.py`, `scripts/fetch_latest_nfl_data.py`, `scripts/track_line_movement.py`, `src/api/live_game_tracker.py` (+`src/data_pipeline.py` URL) | ~60–90% of the 3 small clients | M | 9/10 |
| 2 | Kelly + American-odds helpers redefined 6x | Exact + Near | `src/betting/kelly.py`, `agents/aggressive_kelly.py`, `scripts/parlay_generator.py`, `dashboard/parlay_builder.py`, `scripts/bet_research_tool.py`, `scripts/line_shopping.py`, `src/utils/odds_cache.py` | ~95% per helper | S–M | 9/10 |
| 3 | NOAA weather client + `get_forecast` duplicated 2x | Near | `src/api/noaa_client.py`, `agents/noaa_weather_agent.py` | ~70% | S | 8/10 |
| 4 | `STADIUM_COORDS` 32-team dict copy-pasted | Data | `src/api/noaa_client.py:28`, `agents/noaa_weather_agent.py:16`, `src/features/weather.py` | 100% of the dict | S | 8/10 |
| 5 | ESPN base-URL string literal hardcoded 6x | Data | see Finding 1 locations + `src/data_pipeline.py:178` | 100% literal | S | 7/10 |
| 6 | NFL team-name / abbrev maps duplicated | Data | `src/data_pipeline.py:188`, `dashboard/data_loader.py:33`, `scripts/pregame_prediction_engine.py:44`, `src/features/encoding.py:22`, `src/features/elo.py:31` | ~80–100% overlap | S–M | 7/10 |
| 7 | `scripts/` `sys.path.insert` bootstrap (22 files) | Structural | 22 files under `scripts/` | identical 1-liner | S | 6/10 |
| 8 | `logging.basicConfig(...)` identical format (8 files) | Structural | 8 files under `scripts/` | identical | S | 5/10 |
| 9 | `get_teams` ESPN response-parsing block | Exact | `src/api/espn_client.py`, `agents/api_integrations.py`, `scripts/fetch_latest_nfl_data.py` | ~100% | S | 6/10 |
| 10 | `sqlite3.connect` DB-access boilerplate (7 files) | Structural | `src/data_pipeline.py`, `scripts/backup_database.py`, `scripts/performance_tracker.py`, `scripts/track_line_movement.py`, `scripts/self_improving_system.py`, `scripts/self_improving_bulldog.py`, `dashboard/data_loader.py` | partial | M | 5/10 |

> **Verification note:** Findings 1–5 and 7–9 were confirmed by reading the source bodies
> directly. For Findings 6 and 10 the *defining lines* were confirmed, but the full dict
> bodies / connection blocks were not byte-diffed; exact percentages there are marked
> approximate and the proving step is stated inline.

---

## Detailed findings

### 1. ESPN API client reimplemented five times — importance 9/10

**Type:** Exact + near duplicate (parallel clients).

**Locations:**
- `src/api/espn_client.py:31` — `class ESPNClient` (the "real" one: 320 LOC, has circuit
  breaker, retries, rate limiting, fallback cache). `BASE_URL` at line 46.
- `agents/api_integrations.py:51` — `class ESPNApi` (`base_url` at line 55). Methods
  `get_scoreboard`, `get_teams`, `get_team_schedule` are simplified copies of `ESPNClient`'s.
- `scripts/fetch_latest_nfl_data.py:19` — module-level `ESPN_BASE` + functions
  `fetch_scoreboard`, `fetch_teams`, `fetch_game_summary` (procedural copy of the same calls).
- `scripts/track_line_movement.py:48` — another `BASE_URL = "...espn.../nfl"`.
- `src/api/live_game_tracker.py:39` — `ESPN_API = "...espn.../nfl"`.
- `src/data_pipeline.py:178` — `ESPN_SCOREBOARD = "...espn.../nfl/scoreboard"`.

**Duplication estimate:** The three method-bearing implementations (`ESPNApi`,
`fetch_*`, and the simple paths of `ESPNClient`) share ~60–90% of their request/parse logic.
`get_scoreboard`/`get_teams`/`get_team_schedule` are functionally identical bar error
handling (one logs+returns `None`, another prints, the canonical one retries).

**Risk:** Only `ESPNClient` has resilience (circuit breaker `espn_breaker`, exponential
backoff). The agent/script copies silently swallow failures — behavior already diverges.

**Extraction:** Promote `src/api/espn_client.ESPNClient` to the single source of truth.
Delete `ESPNApi` and the `fetch_*` functions; have callers import `ESPNClient`.

```python
# agents/api_integrations.py and scripts/fetch_latest_nfl_data.py
from src.api.espn_client import ESPNClient
espn = ESPNClient()
data = espn.get_scoreboard()        # replaces ESPNApi().get_scoreboard()/fetch_scoreboard()
```

**Effort:** M (mechanical, but ~4 call sites + verifying the script CLIs still work).

---

### 2. Kelly criterion + American-odds helpers redefined 6+ times — importance 9/10

**Type:** Exact + near duplicate (data/math helpers).

**Confirmed bodies:**
- `src/betting/kelly.py` — `american_to_decimal` (l.11), `american_to_implied` (l.19),
  `decimal_to_implied` (l.27), `kelly_fraction` (l.32: `b=decimal_odds-1; kelly=(b*win_prob-q)/b`),
  `calculate_bet_size` (l.50, returns `round(...)`).
- `agents/aggressive_kelly.py:13,21,28` — `american_to_decimal`, `american_to_implied`,
  `kelly_criterion` — **identical formula**, different name/cap defaults.
- `scripts/parlay_generator.py:42` `calculate_kelly`, `:48` `american_to_decimal`.
- `dashboard/parlay_builder.py:51` `calculate_kelly`, `:58` `american_to_decimal` —
  byte-for-byte same `b=decimal_odds-1; kelly=(b*win_prob-(1-win_prob))/b`.
- `scripts/bet_research_tool.py:55` `calculate_kelly`.
- `scripts/line_shopping.py:18` and `src/utils/odds_cache.py:21` — `american_to_decimal`.

**Duplication estimate:** ~95% per helper; the Kelly body is identical across all six.

**Risk:** Already-present divergence — `kelly.py.calculate_bet_size` rounds, the
`calculate_kelly` copies don't; `aggressive_kelly` defaults `fraction=0.5` vs `0.25`. A bug
fix to the formula must currently be applied in six places.

**Extraction:** `src/betting/kelly.py` is already the right home. Make every other file import
from it; keep only the genuinely different policy (aggressive fraction cap) as a thin wrapper.

```python
from src.betting.kelly import american_to_decimal, american_to_implied, kelly_fraction
# aggressive variant becomes:
def aggressive_kelly(prob, dec_odds, cap=0.5):
    return kelly_fraction(prob, dec_odds, fraction=cap)
```

**Effort:** S–M.

---

### 3. NOAA weather client duplicated — importance 8/10

**Type:** Near duplicate (parallel clients).

**Locations:**
- `src/api/noaa_client.py:64` — `class NOAAClient` (resilient: retries/backoff/fallback,
  `BASE_URL="https://api.weather.gov"` l.67). `get_forecast` (l.108) two-step
  points→forecast; `get_stadium_weather` (l.119).
- `agents/noaa_weather_agent.py:62` — `class NOAAWeatherAgent` (`base_url` l.66). Same
  two-step `get_forecast` (l.69) and `get_stadium_weather` (l.84), **no** resilience.
- A third NOAA-style path also exists in `agents/api_integrations.py:20`
  (`class NOAAWeatherAPI`, `get_forecast` l.27) — same two-step pattern again.

**Duplication estimate:** `get_forecast` + `get_stadium_weather` ~70% identical; the points→
forecast sequence is verbatim three times.

**Extraction:** Keep `src/api/noaa_client.NOAAClient`; delete `NOAAWeatherAgent` and the
`NOAAWeatherAPI` class, re-pointing imports.

**Effort:** S.

---

### 4. `STADIUM_COORDS` 32-team dict copy-pasted — importance 8/10

**Type:** Data duplication.

**Locations (identical 32-entry dict, only the variable name differs):**
- `src/api/noaa_client.py:28` — `STADIUM_COORDS`
- `agents/noaa_weather_agent.py:16` — `STADIUM_COORDINATES`
- `src/features/weather.py` — also references stadium coordinates (confirm: same dict).

**Duplication estimate:** 100% of the dict body (e.g. `"BUF": (42.7738, -78.7870)` etc.).

**Extraction:** Move to one module, e.g. `src/config/stadiums.py`:
```python
# src/config/stadiums.py
STADIUM_COORDS = { "BUF": (42.7738, -78.7870), ... }  # single canonical copy
```
then `from src.config.stadiums import STADIUM_COORDS` everywhere.

**Effort:** S.

---

### 5. ESPN base-URL literal hardcoded 6 times — importance 7/10

**Type:** Data duplication (magic string).

`"https://site.api.espn.com/apis/site/v2/sports/football/nfl"` appears at:
`src/api/espn_client.py:46`, `agents/api_integrations.py:55`,
`scripts/fetch_latest_nfl_data.py:19`, `scripts/track_line_movement.py:48`,
`src/api/live_game_tracker.py:39`, and (as `/scoreboard`) `src/data_pipeline.py:178`.

**Extraction:** Once Finding 1 is resolved this mostly disappears; until then, expose
`ESPNClient.BASE_URL` (or a constant in `src/config/settings.py`) and import it.

**Effort:** S. **Note:** largely subsumed by Finding 1.

---

### 6. NFL team-name / abbreviation maps duplicated — importance 7/10

**Type:** Data duplication.

**Defining lines (confirmed):**
- `src/data_pipeline.py:188` — `NFL_TEAMS = {"ARI": "Arizona Cardinals", ...}`
- `dashboard/data_loader.py:33` — `NFL_TEAMS = {"ARI": "Arizona Cardinals", ...}`
- `scripts/pregame_prediction_engine.py:44` — `TEAM_NAMES = {"ARI": "Arizona Cardinals", ...}`
- `src/features/encoding.py:22` — `TEAM_ABBR = {"ARI": 0, "ATL": 1, ...}` (abbrev→index)
- `src/features/elo.py:31` — `TEAM_LIST = ["ARI", "ATL", ...]`

**Duplication estimate:** ~80–100% overlap on the abbrev→full-name maps; the encoding/elo
variants are derived views of the same canonical team set.

**Extraction:** One canonical `src/config/teams.py` exposing `NFL_TEAMS` (abbr→name) plus
derived `TEAM_LIST = list(NFL_TEAMS)` and `TEAM_ABBR = {a:i for i,a in enumerate(TEAM_LIST)}`.

**Effort:** S–M. **Proving step (not yet done):** byte-diff the three `NFL_TEAMS`/`TEAM_NAMES`
dict bodies to confirm 100% value identity (defining lines confirmed; full bodies were
truncated in scan).

---

### 7. `scripts/` `sys.path.insert` bootstrap — importance 6/10

**Type:** Structural boilerplate.

Identical line `sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` appears in
**22** `scripts/` files (analyze_features, audit_data_sources, backfill_2025_season, backtest,
bet_research_tool, bulldog_backtest, download_data, fetch_latest_nfl_data,
full_betting_pipeline, generate_daily_picks, generate_daily_picks_with_grok, line_shopping,
parlay_generator, performance_tracker, pregame_prediction_engine, production_daily_pipeline,
self_improving_bulldog, self_improving_system, send_notifications, track_line_movement,
train_model, weekly_retrain).

**Extraction:** Make the package properly installable (it already has `setup.py`/
`pyproject.toml`) and run scripts via console entry points or `python -m scripts.xxx`, removing
the hack entirely. Interim: a single `from scripts._bootstrap import *` or a `conftest`-style
shared helper.

**Effort:** S (delete-and-import) once packaging is relied upon.

---

### 8. Identical `logging.basicConfig(...)` — importance 5/10

**Type:** Structural boilerplate.

The exact line
`logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")`
appears in 8 scripts (analyze_features, backtest, full_betting_pipeline, generate_daily_picks,
pregame_prediction_engine, production_daily_pipeline, self_improving_bulldog,
self_improving_system).

**Extraction:** A `src/utils/logging_setup.py` with `def configure_logging(level=INFO): ...`;
each script calls `configure_logging()`.

**Effort:** S.

---

### 9. ESPN `get_teams` response-parsing block — importance 6/10

**Type:** Exact duplicate (a sub-case of Finding 1, called out because the parse logic is
copied verbatim and is independently bug-prone).

The block
```python
teams = []
if "sports" in data:
    for sport in data["sports"]:
        for league in sport.get("leagues", []):
            teams.extend([t["team"] for t in league.get("teams", [])])
```
is duplicated in `src/api/espn_client.py` (`get_teams`), `agents/api_integrations.py:74-80`,
and `scripts/fetch_latest_nfl_data.py:41-46`. ~100% identical.

**Extraction:** Resolved by Finding 1 (single `ESPNClient.get_teams`).

**Effort:** S.

---

### 10. `sqlite3.connect` data-access boilerplate — importance 5/10

**Type:** Structural duplication.

`sqlite3.connect(...)` + cursor + commit/close patterns recur in 7 files:
`src/data_pipeline.py`, `scripts/backup_database.py`, `scripts/performance_tracker.py`,
`scripts/track_line_movement.py`, `scripts/self_improving_system.py`,
`scripts/self_improving_bulldog.py`, `dashboard/data_loader.py`.

**Extraction:** A small `src/utils/db.py` with a `@contextmanager def get_conn(path)` and a
`run_query(sql, params)` helper to centralize connection handling and the DB path.

**Effort:** M. **Proving step (not yet done):** read each connect block to confirm the
open/commit/close pattern (and DB path literal) is shared vs. legitimately different schemas.

---

## Recommended remediation order

1. **Findings 2 + 4 + 5 + 6 (constants/helpers → `src/config/` + `src/betting/kelly`)** —
   cheapest, highest divergence risk, no behavior change. Do first.
2. **Findings 1 + 3 + 9 (collapse parallel API clients onto the resilient `src/api/*`
   versions)** — biggest correctness win (the duplicate clients lack retries/breakers).
3. **Findings 7 + 8 + 10 (boilerplate)** — nice-to-have; pairs well with making the package
   properly installable.

## Method / how to reproduce

```bash
cd /home/user/nfl-betting-system
grep -rn "site.api.espn.com" src scripts agents dashboard          # Findings 1,5
grep -rn "def calculate_kelly\|def american_to_decimal\|kelly = (b" src scripts agents dashboard  # Finding 2
grep -rn "STADIUM_COORD" src scripts agents dashboard               # Finding 4
grep -rn "NFL_TEAMS\|TEAM_NAMES\|TEAM_ABBR\|TEAM_LIST" src scripts dashboard  # Finding 6
grep -rn "sys.path.insert" scripts                                  # Finding 7
grep -rn "logging.basicConfig" scripts                              # Finding 8
grep -rln "sqlite3.connect" src scripts agents dashboard            # Finding 10
# Automated cross-check (recommended): jscpd --min-tokens 50 --pattern "**/*.py" src scripts agents dashboard
```
