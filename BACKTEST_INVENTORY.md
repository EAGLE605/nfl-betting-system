# BACKTEST INVENTORY - All Available Backtests

**Date**: November 24, 2025  
**Status**: Current backtest results available

---

## 📊 Current Backtest Results

### Active Backtest: Favorites-Only Strategy

**File**: `reports/backtest_metrics.json`  
**Model**: `models/xgboost_favorites_only.pkl`  
**Features**: 41 recommended features (no betting line leakage)  
**Period**: 2023-2024 seasons  
**Strategy**: Favorites-only (odds 1.3-2.0), aggressive Kelly sizing

**Results**:
- **Total Bets**: 52
- **Wins**: 36
- **Losses**: 16
- **Win Rate**: 69.23% ✅
- **ROI**: 60.05% ✅
- **Max Drawdown**: -11.04% ✅
- **Sharpe Ratio**: 4.04 ✅
- **Final Bankroll**: $16,005.14 (from $10,000)
- **Avg CLV**: 10.74%
- **Positive CLV**: 100%

**Status**: ✅ **GO** - All criteria exceeded

---

## 📁 Backtest Files

### Results Files

1. **`reports/backtest_metrics.json`**
   - Summary metrics (win rate, ROI, Sharpe, etc.)
   - Current status: ✅ Active
   - Last updated: After favorites-only model training

2. **`reports/bet_history.csv`**
   - Detailed bet-by-bet history
   - Columns: game_id, gameday, teams, bet_size, odds, pred_prob, result, profit, bankroll, CLV, drawdown
   - Current status: ✅ Active
   - Contains: 52 bets from 2023-2024

3. **`reports/img/equity_curve.png`**
   - Visual equity curve showing bankroll evolution
   - Current status: ✅ Active

4. **`reports/img/performance_dashboard.png`**
   - Comprehensive performance dashboard
   - Current status: ✅ Active

---

## 🔄 Backtest Scripts

### Main Backtest Script

**File**: `scripts/backtest.py`

**Capabilities**:
- Loads favorites-only model (or falls back to improved model)
- Uses improved features (41 recommended features)
- Applies favorites-only filter (odds 1.3-2.0)
- Uses aggressive Kelly sizing
- Generates bet history and metrics
- Creates equity curve visualization

**Usage**:
```bash
python scripts/backtest.py
```

**Model Priority**:
1. `models/xgboost_favorites_only.pkl` (preferred)
2. `models/xgboost_improved.pkl` (fallback)
3. `models/calibrated_model.pkl` (legacy)

---

## 📈 Historical Backtest Results

### Backtest #1: Original Model (NO-GO)

**Period**: 2023-2024  
**Model**: Original calibrated model  
**Strategy**: All games, standard Kelly  
**Results**:
- Win Rate: 49.57% ❌
- ROI: -23.62% ❌
- Max Drawdown: -25.15% ❌
- Sharpe Ratio: -1.72 ❌
- **Decision**: NO-GO

**Issue**: Data leakage (betting lines in features) - FIXED

---

### Backtest #2: Improved Model (After Data Leakage Fix)

**Period**: 2023-2024  
**Model**: Improved XGBoost (no betting lines)  
**Strategy**: All games, standard Kelly  
**Results**: Unknown (not documented)

**Status**: Superseded by favorites-only strategy

---

### Backtest #3: Favorites-Only Strategy (CURRENT) ✅

**Period**: 2023-2024  
**Model**: `xgboost_favorites_only.pkl`  
**Strategy**: 
- Favorites only (odds 1.3-2.0)
- Aggressive Kelly sizing (2.5× for heavy favorites, 1.5× for small favorites)
- Hot streak bonus (+20%)
- Edge filter (3-8%)
- Confidence filter (>65%)

**Results**:
- Win Rate: 69.23% ✅
- ROI: 60.05% ✅
- Max Drawdown: -11.04% ✅
- Sharpe Ratio: 4.04 ✅
- **Decision**: GO ✅

**Status**: ✅ **ACTIVE** - Current production backtest

---

## 🧪 Planned/Proposed Backtests

### Bet Reconstruction Backtest

**File**: `bet_reconstruction_backtest.md`  
**Status**: ⏳ Proposed (not implemented)

**Concept**:
- Walk-forward backtest
- Train model on historical data up to each week
- Generate bets as system would have made them
- Analyze patterns and high-ROI insights

**Purpose**: Discover hidden patterns and validate strategy robustness

---

## 📊 Backtest Comparison

| Backtest | Model | Strategy | Win Rate | ROI | Status |
|----------|-------|----------|----------|-----|--------|
| #1 | Original | All games | 49.57% | -23.62% | ❌ NO-GO |
| #2 | Improved | All games | Unknown | Unknown | ⚠️ Superseded |
| #3 | Favorites-Only | Favorites only | 69.23% | 60.05% | ✅ GO |

---

## 🎯 Backtest Configuration

### Current Configuration

**Model**: Favorites-only specialist  
**Features**: 41 recommended (no betting lines)  
**Filter**: Odds 1.3-2.0 (favorites only)  
**Sizing**: Aggressive Kelly (2.5×/1.5× multipliers)  
**Bankroll**: $10,000 starting  
**Period**: 2023-2024 seasons

### Key Settings

- **Kelly Fraction**: 0.25 (quarter Kelly)
- **Min Edge**: 2%
- **Min Probability**: 55%
- **Max Bet**: 10% (aggressive mode)
- **Hot Streak Threshold**: 75% win rate (last 10)

---

## 📋 Running New Backtests

### To Run Current Backtest

```bash
# Run favorites-only backtest
python scripts/backtest.py
```

### To Run Custom Backtest

Modify `scripts/backtest.py`:
- Change model path
- Adjust filter parameters
- Modify Kelly settings
- Change test period

### To Run Historical Backtest

1. Load historical data
2. Train model on data up to specific date
3. Generate predictions for that week
4. Apply filters and Kelly sizing
5. Record results
6. Repeat for each week

---

## ✅ Backtest Validation

### Current Backtest Status

- ✅ Model loaded successfully
- ✅ Features validated (no leakage)
- ✅ Filter applied correctly
- ✅ Kelly sizing calculated
- ✅ Metrics generated
- ✅ Visualizations created
- ✅ Results validated (69.23% win rate, 60.05% ROI)

### Data Integrity

- ✅ No betting line features
- ✅ Temporal ordering maintained
- ✅ No future data leakage
- ✅ Features match training data

---

## 📈 Performance Metrics

### Current Backtest Metrics

- **Win Rate**: 69.23% (Target: >55%) ✅ +14.23%
- **ROI**: 60.05% (Target: >3%) ✅ +57.05%
- **Max Drawdown**: -11.04% (Target: <-20%) ✅ Better
- **Sharpe Ratio**: 4.04 (Target: >0.5) ✅ Excellent
- **Total Bets**: 52 (Selective, high quality)
- **Positive CLV**: 100% (All bets have positive closing line value)

---

## 🎯 Summary

### Available Backtests

1. **Current**: Favorites-only strategy (2023-2024) ✅
   - 69.23% win rate, 60.05% ROI
   - Status: GO ✅

2. **Historical**: Original model (2023-2024) ❌
   - 49.57% win rate, -23.62% ROI
   - Status: NO-GO (superseded)

3. **Proposed**: Bet reconstruction backtest ⏳
   - Not yet implemented
   - Status: Planned

### Files

- ✅ `reports/backtest_metrics.json` - Current metrics
- ✅ `reports/bet_history.csv` - Current bet history
- ✅ `reports/img/equity_curve.png` - Equity curve
- ✅ `reports/img/performance_dashboard.png` - Dashboard
- ✅ `scripts/backtest.py` - Backtest script

**Status**: ✅ **ONE ACTIVE BACKTEST** (Favorites-only strategy)

---

**Last Updated**: November 24, 2025  
**Current Backtest**: Favorites-Only Strategy (2023-2024)  
**Status**: ✅ **GO** - Ready for paper trading

