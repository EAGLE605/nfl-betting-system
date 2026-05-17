# CLAUDE.md - Project Guidelines & Honest Assessment

## Self-Reflection (May 2026 Session)

### What I Did Wrong

1. **Speculated without data**: Said "books probably know this" about RB dual-threat pricing without any evidence.

2. **Accepted theoretical values uncritically**: Used correlation values from "research" (0.40 for RB dual-threat) that turned out to be completely wrong (-0.13 empirically).

3. **Previous sessions inflated metrics**: The README claims 428% ROI and 67% win rate. Transparent backtest shows **63.1%** - the previous numbers had data leakage.

4. **Confused descriptive stats with predictions**: Reported "77% rushing hit rate" which is just how often players exceed a line historically, NOT a predictive model output.

### Rules for This Project

1. **NO GUESSING**: Only state what the data shows. If you don't have data, say "I don't know."

2. **VALIDATE EVERYTHING**: Check against empirical data. 4 seasons of nflverse available.

3. **WALK-FORWARD ONLY**: Train on past, test on future. No exceptions.

4. **CITE YOUR SOURCES**: Include sample size (n=), confidence intervals, data source.

5. **ADMIT UNCERTAINTY**: Don't hide limitations.

6. **NO DATA LEAKAGE**: Never use same-game data to predict same-game outcomes.

7. **ESCAPE PROPERLY IN CODE BLOCKS**: When writing large code blocks, avoid nested quotes that break parsing. Use single quotes inside double quotes, or escape with backslash. Test: if the block splits unexpectedly, fix the escaping.

---

## Project Overview

NFL betting system for **recreational bettors** focused on:
- High accuracy / hit rates over ROI grinding
- Popular bet types (props, SGPs, parlays)
- Fun factor alongside +EV

### ACTUAL Performance (Walk-Forward, No Leakage)

Tested: May 2026 | Data: nflverse 2021-2024 | Method: Train on 2021-22, test on 2023-24

**Overall (all games):**
| Test Year | Accuracy | N Games |
|-----------|----------|---------|
| 2023 | 58.6% | 237 |
| 2024 | 62.0% | 237 |
| **Overall** | **60.3%** | **474** |

**High Confidence Only (model prob >58% or <42%):**
| Test Year | Accuracy | ROI | N Games |
|-----------|----------|-----|---------|
| 2023 | 59.3% | +13.3% | 150 |
| 2024 | 72.0% | +37.5% | 150 |
| **Overall** | **65.7%** | **+25.4%** | **300** |

**By Confidence Bucket:**
| Bucket | Accuracy | ROI | N |
|--------|----------|-----|---|
| 65-70% | 79.7% | +52.2% | 69 |
| 80%+ | 76.3% | +45.8% | 38 |

### What These Numbers Mean

- High-confidence picks (65.7%) are profitable at -110 odds
- BUT: 2023 vs 2024 variance is large (59% vs 72%)
- Sample size is small (300 games, 150/year)
- Could be skill, could be luck - more data needed
- Baseline (home team): 55.9%

### Key Features (by importance)
1. EPA differential (26.3%)
2. Success rate differential (24.3%)
3. Efficiency differential (17.5%)
4. Defensive EPA differential (16.1%)
5. Week of season (9.5%)

### Prop Hit Rates (DESCRIPTIVE, Not Predictive)

These are historical rates, NOT model predictions:

| Prop Type | Line | Historical Hit Rate | N |
|-----------|------|---------------------|---|
| Rushing yards | >55.5 | 18.9% +/- 0.8% | 8,627 |
| Rushing yards | >65.5 | 14.0% +/- 0.7% | 8,627 |
| Receiving yards | >45.5 | 26.8% +/- 0.7% | 15,907 |
| Receiving yards | >55.5 | 19.8% +/- 0.6% | 15,907 |

**Important**: These are how often players exceed lines historically. They are NOT predictions. Saying "77% hit rate" was misleading.

---

## Empirically Validated Correlations

From analysis of 198,513 plays (2021-2024 nflverse data):

| Correlation | Theoretical | **Empirical** | N | Status |
|-------------|-------------|---------------|---|--------|
| QB + WR1 yards | 0.72 | **0.68** | 2,278 | ✅ Validated |
| WR receptions + yards | 0.75 | **0.80** | 16,327 | ✅ Validated |
| WR1 + WR2 yards | 0.15 | **0.49** | 2,278 | ⚠️ Theory wrong |
| RB rush + rec (same player) | 0.40 | **-0.13** | 4,581 | ❌ Theory wrong |
| Team total yards + TDs | 0.55 | **0.61** | 2,278 | ✅ Validated |

### Key Finding: RB Dual-Threat is NEGATIVE Correlation

The popular bet of stacking RB rushing + receiving yards is **negatively correlated**. Game script explains this:
- Run game working → keep running → fewer catches
- Run game not working → pass more → more catches, fewer rush yards

**I do not know how books price these SGPs.** I have no data on sportsbook correlation pricing.

---

## Data Sources

### Real Data (Use These)
- `data/raw/pbp_4seasons.parquet` - 198,513 plays from 2021-2024
- `data/raw/schedules.parquet` - nflverse schedules with spreads
- nfl_data_py library - live nflverse access

### What's NOT Validated
- The 428% ROI in README - needs walk-forward verification
- The 67% win rate in README - needs walk-forward verification
- Any metrics from previous sessions without cited methodology

---

## Code Structure

```
src/
├── models/
│   ├── advanced_copula.py      # Gaussian/Multivariate copula
│   ├── empirical_correlations.py # Data-validated correlations
│   └── ...
├── recreational/
│   └── popular_bets.py         # Focus on popular bet types
├── services/
│   ├── unified_data_service.py # Single data interface
│   └── model_service.py        # XGBoost with calibration
├── props/
│   ├── correlation_engine.py   # SGP correlation scoring
│   └── hit_rate_tracker.py     # Track prop performance
└── ...

backend/
├── main.py                     # FastAPI server
└── routers/
    ├── recreational.py         # Popular bet endpoints
    └── ...

models/
└── game_outcome_*.pkl          # Trained XGBoost models
```

---

## Commands

```bash
# Refresh data from nflverse
python cli.py refresh

# Train model (walk-forward)
python cli.py train

# Generate predictions
python cli.py predict

# Start API server
python cli.py serve

# Run correlation audit
python scripts/deep_correlation_audit.py
```

---

## What Needs Work

1. **Fix README**: Remove false claims of 428% ROI and 67% win rate. Replace with actual 63.1%.

2. **Build actual prop models**: Current "hit rates" are just historical distributions, not predictions.

3. **Live testing**: All metrics are from backtesting. Need paper trading on live games.

4. **Get sportsbook data**: Cannot calculate true edge without knowing how books price correlations.

5. **Confidence calibration**: Model probabilities may not be well-calibrated.

---

## What This System Actually Does Well

1. **Correlation discovery**: Found real empirical correlations from 198,513 plays
2. **Data pipeline**: Clean nflverse data loading and processing
3. **Walk-forward methodology**: Proper backtesting without leakage (when done correctly)
4. **Recreational focus**: Prioritizes popular bet types

## What This System Does NOT Do

1. **Guarantee profits**: 63% accuracy at -110 odds is roughly break-even
2. **Predict props**: No validated predictive prop models exist
3. **Know book pricing**: Cannot determine if books misprice correlations
4. **Beat the market**: No evidence of consistent edge

---

## Principles

1. The model serves the bettor, not the other way around
2. Recreational betting should be fun AND informed
3. Honesty about limitations builds trust
4. Data beats theory every time
5. If you don't know, say you don't know
6. Never confuse descriptive stats with predictions
7. Always validate with walk-forward testing

---

## New Package (May 2026)

Branch: `claude/implement-logic-layer-01VgpL6wwzu41UHkXsSDc2wX`

```bash
pip install -e .
picks --week 1 --season 2026   # Generate picks
picks --serve                   # Start web app at localhost:8000
```

Package: `src/nfl_picks/` with 28 passing tests.

---

## Machine-Readable Data

All research and config stored as JSON for programmatic access:

- `src/nfl_picks/data/model_config.json` - Model performance, features, thresholds
- `src/nfl_picks/data/novel_edges.json` - Future ideas with priority and data sources
- `src/nfl_picks/data/package_structure.json` - Package layout and commands

---

## Session Persistence

To resume without losing context:
- Use `/resume` or `claude --continue`
- Key findings are in this CLAUDE.md (auto-loaded every session)
- Detailed research in `data/*.json` (read on demand)
