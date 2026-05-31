# Code Quality & Complexity Metrics Audit — nfl-betting-system

**Date:** 2026-05-31
**Scope:** `src/`, `scripts/`, `agents/`, `dashboard/` (Python only). Excludes `*.md`, tests, notebooks.
**Method:** Full AST-level manual read of all 12 in-scope Python files (Bash/`radon` were unavailable in this environment, so cyclomatic/cognitive complexity was computed by hand from branch and nesting counts; line counts taken from file extents). No source was modified.

## Summary

The codebase is small (12 files, ~1,150 LOC), well-modularized by concern (data / features / models / betting / backtest / agents / dashboard), and mostly within healthy size and complexity thresholds. **No file exceeds 300 lines and no class exceeds 500 lines.** Overall cohesion and coupling are good: modules are single-responsibility and the dependency graph is a clean acyclic fan-in toward `scripts/run_pipeline.py`.

There is **one clear outlier** — `EdgeDetector.find_edges_nested` — which is deeply nested, exceeds 50 lines, AND contains two latent runtime bugs (undefined names) plus a syntax error. A handful of secondary smells (duplicated odds-conversion helpers across 3 modules, a dead `if/else` branch, an unbounded `while True` loop) round out the findings.

### Top-10 longest files (in-scope)

| Rank | File | Lines | Classes | Top-level + methods (def) |
|------|------|------:|--------:|--------------------------:|
| 1 | `src/backtest/engine.py` | 174 | 2 | 12 |
| 2 | `src/betting/edge_detector.py` | 172 | 1 | 8 |
| 3 | `src/features/feature_engineering.py` | 132 | 1 | 7 |
| 4 | `scripts/run_pipeline.py` | 115 | 0 | 3 |
| 5 | `src/data/odds_api_client.py` | ~89 | 2 | 4 |
| 6 | `src/models/spread_model.py` | 84 | 1 | 7 |
| 7 | `dashboard/app.py` | 82 | 0 | 6 |
| 8 | `agents/research_agent.py` | 74 | 2 | 5 |
| 9 | `agents/line_monitor.py` | 68 | 2 | 4 |
| 10 | `src/models/totals_model.py` | 66 | 1 | 4 |

(Not shown: `src/data/nflfastr_loader.py` 48, `src/betting/kelly.py` 48.)

### Top-10 longest / most-complex functions

Cyclomatic complexity (CC) estimated as 1 + count of branch/loop/boolean-operator decision points. Max nesting = deepest indentation of control structures.

| Rank | Function | File:line | LOC | CC (est.) | Max nesting | Notes |
|------|----------|-----------|----:|----------:|------------:|-------|
| 1 | `EdgeDetector.find_edges_nested` | `edge_detector.py:106` | ~54 | ~14 | 9 | Deep nesting; uses undefined `model_prob`/`bkey`; missing `:` (syntax error) |
| 2 | `run` (pipeline) | `run_pipeline.py:37` | ~68 | ~9 | 3 | Orchestration; mixes load/train/predict/size/persist in one function |
| 3 | `BacktestEngine.run` | `engine.py:62` | ~48 | ~10 | 4 | Nested loop (games x markets) with several continue guards |
| 4 | `EdgeDetector.find_edges` | `edge_detector.py:36` | ~43 | ~11 | 6 | 4-level nested loop + guard chain |
| 5 | `FeatureEngineer.build_features` | `feature_engineering.py:23` | ~33 | ~6 | 3 | Row-wise loop building dict; readable |
| 6 | `FeatureEngineer._compute_team_game_stats` | `feature_engineering.py:57` | ~26 | ~9 | 2 | Many inline ternaries inside dict literal (cognitive load) |
| 7 | `BacktestEngine._settle` | `engine.py:134` | ~20 | ~8 | 2 | if/elif/else over markets + conditional expressions |
| 8 | `OddsAPIClient._normalize` | `odds_api_client.py:65` | ~24 | ~5 | 4 | 3-level nested comprehension/loops over events/books/markets |
| 9 | `OddsAPIClient._get` | `odds_api_client.py:37` | ~16 | ~6 | 3 | Retry loop with try/except; acceptable |
| 10 | `LineMonitor.poll_loop` | `line_monitor.py:51` | ~17 | ~6 | 3 | `while True` loop (see finding) |

---

## Prioritized recommendations (worst offenders first)

### 1. `EdgeDetector.find_edges_nested` — refactor and/or delete. Importance: 9/10
**File:** `src/betting/edge_detector.py:106-159`

This "legacy" method is the single worst quality item:

- **Cognitive/cyclomatic complexity:** ~9 levels of nesting (event → gid-if → book → filter-if → market → mkey-if → outcome → side-if → mp-if → edge-if → min_price-if), CC ~14. It is an arrow/pyramid anti-pattern.
- **Latent bug 1:** line 137 references `model_prob`, which is never defined in this method (the local is `mp`). At runtime this raises `NameError`.
- **Latent bug 2:** line 156 references `bkey`, also undefined in this method (only defined in `find_edges`). Another `NameError`.
- **Syntax error:** line 144 ends a parenthesized `if (...)` condition without the trailing `:`, so the file as written would fail to import. (Flagged as written; if the on-disk file differs, treat as "unable to verify" — but as read it is invalid.)

**Recommendation:** If `find_edges` is the canonical path (it is, per `run_pipeline.py:78`), delete `find_edges_nested` entirely. If the filter behavior is wanted, fold it into `find_edges` via early-`continue` guards instead of nesting:

```python
def find_edges(self, model_probs, odds, filters=None):
    filters = filters or {}
    books = filters.get("books")
    min_price = filters.get("min_price")
    devig_markets = filters.get("devig_markets", ["totals"])
    edges = []
    for event in odds:
        model = model_probs.get(event.get("game_id"))
        if model is None:
            continue
        for book in event.get("books", []):
            if books is not None and book.get("key") not in books:
                continue
            for market, outcomes in book.get("markets", {}).items():
                mkey = self._market_key(market)
                if mkey not in model:
                    continue
                for o in outcomes:
                    edge = self._eval_outcome(model, mkey, market, o, outcomes,
                                              devig_markets, min_price,
                                              event["game_id"], book.get("key"))
                    if edge is not None:
                        edges.append(edge)
    return edges
```
Each `continue` flattens nesting from 9 levels to ~4 and eliminates the undefined-name bugs by construction.

### 2. De-duplicate odds/probability conversion helpers. Importance: 6/10
The same American-odds math is reimplemented in **three** modules, a cohesion/DRY problem and a correctness risk (fixes must be applied in 3 places):

- `src/betting/kelly.py:18` `american_to_decimal`
- `src/betting/edge_detector.py:23` `american_to_prob`
- `src/backtest/engine.py:155-173` `_implied_prob`, `_decimal_odds`, `_american_from_prob` (static methods)

**Recommendation:** Create `src/betting/odds_math.py` (or `src/utils/odds.py`) exposing `american_to_decimal`, `american_to_prob`, `decimal_to_prob`, `prob_to_american`, and import it everywhere. Removes ~30 duplicated lines and makes `BacktestEngine`'s three static math methods unnecessary. Note `engine.py:167 _american_from_prob` appears unused — verify and drop if dead.

### 3. `scripts/run_pipeline.py:run` — split orchestration into stages. Importance: 6/10
**File:** `scripts/run_pipeline.py:37-104` (~68 LOC, over the 50-line guideline)

`run()` does six distinct jobs: load data, train models, fetch odds, build per-game model probabilities, detect edges, size bets, and persist state. Mixed abstraction levels (DataFrame plumbing next to JSON I/O).

**Recommendation:** Extract helpers so `run()` becomes a readable top-level script:
```python
def run(args):
    pbp, schedule = _load_data(args.seasons)
    features = FeatureEngineer().build_features(pbp, schedule)
    spread_model, totals_model = _train_models(features, schedule)
    raw_odds = _fetch_odds(args.odds_key)
    model_probs = _predict_probs(features, spread_model, totals_model)
    edges = EdgeDetector(min_edge=args.min_edge).find_edges(model_probs, raw_odds)
    bets = _size_bets(edges, args.bankroll)
    return _persist(args.output, bankroll=args.bankroll, bets=bets)
```
Also note a likely logic bug at `run_pipeline.py:53` — `spread_model.train(features, margins)` trains on the full unmerged `features`/`margins` even though `merged` was computed for alignment; the row counts may not correspond. Worth verifying alignment of `features` vs `schedule` before training. Importance of that sub-item: 5/10.

### 4. Dead / vestigial branch in `BacktestEngine._compute_edge`. Importance: 4/10
**File:** `src/backtest/engine.py:111-119`

The `if market == "spread" or market == "total": model_prob = pred  else: model_prob = pred` branch assigns the same value in both arms — a no-op `if/else` that signals unfinished logic (moneyline edge is presumably meant to differ).

**Recommendation:** Either implement the intended per-market handling or collapse to `model_prob = pred` and drop the branch. Add a test documenting intended moneyline behavior.

### 5. `LineMonitor.poll_loop` — unbounded `while True`. Importance: 4/10
**File:** `agents/line_monitor.py:51-68`

`while True` with `time.sleep(self.poll_interval)` and the only exit being `iterations and count >= iterations`. When `iterations=0` (the default) this never terminates and has no signal/exception handling, making it hard to stop or test cleanly.

**Recommendation:** Convert to a bounded/abortable loop, e.g. accept a `stop: threading.Event` or `should_continue: Callable[[], bool]`, and wrap the body in try/except so a fetch error doesn't kill the monitor. Keeps the function testable without relying on the `iterations` shortcut.

### 6. `FeatureEngineer._compute_team_game_stats` — inline-ternary-heavy dict. Importance: 3/10
**File:** `src/features/feature_engineering.py:57-82`

The per-row `dict` literal (lines 65-79) packs multiple multi-line conditional expressions (`g.loc[...].mean() if "epa" in g and "play_type" in g else 0.0`) inline. CC ~9 concentrated in a literal; readability suffers and the `"epa"/"play_type"` guards are repeated.

**Recommendation:** Precompute guard flags and a small helper, e.g. `def _safe_mean(frame, col): return frame[col].mean() if col in frame else 0.0`, and compute `pass_epa`/`rush_epa` as named locals before assembling the dict.

---

## Coupling & Cohesion notes

- **Efferent coupling (fan-out):** `scripts/run_pipeline.py` imports 8 internal modules (data, features, both models, edge_detector, kelly, backtest) — expected for the entry point; not a smell.
- **Afferent coupling (fan-in):** `src/betting/kelly.py` and the conversion helpers are reused by pipeline and engine. Centralizing odds math (rec #2) would make this fan-in cleaner.
- **No circular imports** detected; dependency direction flows data → features → models → betting → backtest, with `scripts`/`dashboard`/`agents` at the edges. The `agents/` modules (`ResearchAgent`, `LineMonitor`) are currently standalone — not wired into `run_pipeline.py`, so verify they are intended to be integrated or are scaffolding.
- **Cohesion:** Each class is single-responsibility (loader, feature builder, one model per market, edge detector, sizer, backtester). Good. The only cohesion violation is the duplicated math (rec #2) and the dual `find_edges`/`find_edges_nested` (rec #1).

## Items marked "Unable to verify"
- Exact byte-accurate line counts and `radon`-grade CC/MI scores could not be produced because Bash/`wc`/`radon` were disabled in this environment; figures above are AST-level manual estimates (file extents are exact from reads).
- Whether the on-disk `edge_detector.py` truly contains the syntax error at line 144 / undefined names, versus a transcription artifact, should be confirmed by running `python -m py_compile src/betting/edge_detector.py` once tooling is available.
