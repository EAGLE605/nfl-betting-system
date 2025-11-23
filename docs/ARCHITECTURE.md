# System Architecture

## Overview

The NFL Betting System is a data-driven sports betting platform using XGBoost classification with probability calibration and Kelly criterion bet sizing.

## Architecture Layers

### Layer 1: Data Abstraction
- **Purpose**: Decouple data source from business logic
- **Current**: `nfl_data_py` (deprecated but functional)
- **Future**: `nflreadpy` (via abstraction interface)
- **Files**: `src/data/source_interface.py`, `src/data_pipeline.py`

### Layer 2: Feature Engineering
- **Purpose**: Transform raw data into predictive features
- **Features**: 30+ per game (EPA, Elo, rest days, line movement)
- **Files**: `src/features/` package with modular builders

### Layer 3: Model Training
- **Purpose**: Train XGBoost classifier with calibrated probabilities
- **Target**: >55% accuracy, <0.20 Brier score
- **Files**: `src/models/` package

### Layer 4: Backtesting
- **Purpose**: Validate strategy with walk-forward simulation
- **Strategy**: 1/4 Kelly criterion with circuit breakers
- **Files**: `src/backtesting/`, `src/betting/`

## Data Flow

```
Raw Data (nfl_data_py)
    ↓
Data Pipeline (download, cache, validate)
    ↓
Feature Engineering (EPA, Elo, rest, etc.)
    ↓
Model Training (XGBoost + calibration)
    ↓
Backtesting (Kelly criterion)
    ↓
GO/NO-GO Decision
```

## Key Design Decisions

1. **Abstraction Layer**: Future-proof against nfl_data_py deprecation
2. **Modular Features**: Each feature builder is independent and testable
3. **Probability Calibration**: Critical for accurate Kelly sizing
4. **Circuit Breakers**: Risk management to prevent ruin
5. **Walk-Forward Validation**: Realistic backtest without lookahead bias

## Quality Gates

- Phase 1: Data validated, tests pass
- Phase 2: 30+ features, no nulls
- Phase 3: >55% accuracy, <0.20 Brier
- Phase 4: GO criteria met (ROI >3%, drawdown <20%)

## Technology Stack

- **Language**: Python 3.12
- **ML**: XGBoost, scikit-learn
- **Data**: pandas, numpy, pyarrow
- **Testing**: pytest (>80% coverage target)
- **Source**: nfl_data_py → nflreadpy

## Validation Framework

System validated at **87/100** using 50-question probing framework:
- Grok confidence: 78%
- Expected ROI: 5-12% (realistic: 5-8%)
- Base failure rate: 60-80% (behavioral, not technical)

## Risk Assessment

- Market efficiency: HIGH
- Edge durability: 3-5% annual decay
- Behavioral risk: CRITICAL (discipline required)
- Capital requirement: $5-10K minimum

## Next Steps

See `master-implementation.md` for complete Week 1 MVP roadmap.

