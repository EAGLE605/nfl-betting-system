# Codebase Audit: Subtle Issues & Handoff Problems

**Date**: 2025-11-24  
**Status**: ⚠️ **CRITICAL ISSUES FOUND**

---

## 🚨 Critical Issues Found

### 1. **🚨 CRITICAL: DATA LEAKAGE - Betting Line Features in Model** ✅ **FIXED**

**Problem**: `home_favorite`, `line_movement`, and `total_movement` were in `recommended_features.csv` and were being used in the trained model!

**Status**: ✅ **FIXED** - These features are now excluded from:
- `scripts/analyze_features.py` 
- `scripts/train_improved_model.py`
- `scripts/backtest.py`

**⚠️ ACTION REQUIRED**: Model was trained WITH these features. Need to:
1. Regenerate `recommended_features.csv` (run `analyze_features.py`)
2. **RETRAIN MODEL** without betting line features
3. Re-run backtest

**Impact**: **HIGH** - Current 75% accuracy may be inflated due to data leakage

---

### 2. **🚨 CRITICAL: Referee Temporal Leakage** ✅ **FIXED**

**Problem**: Referee stats calculated from ALL games including future games.

**Status**: ✅ **FIXED** - Now calculates only from games BEFORE current game

**Impact**: **HIGH** - Was causing temporal data leakage

---

### 3. **DATA LEAKAGE RISK: Betting Line Features Still Created**

**Problem**: `LineFeatures` creates betting line features (`spread_line`, `total_line`, `line_movement`, `total_movement`, `home_favorite`) that are then excluded in training scripts. However:

- ✅ These ARE excluded in `train_improved_model.py` 
- ✅ These ARE excluded in `backtest.py`
- ⚠️ **BUT**: They're still in `config/config.yaml` as "core features" (lines 34-36)
- ⚠️ **RISK**: If someone uses `config.yaml` to determine features, they'll include betting lines

**Location**: 
- `src/features/line.py` - Creates the features
- `config/config.yaml` - Lists them as core features (WRONG)

**Impact**: Medium - Currently excluded but config is misleading

**Fix Needed**: Remove from config.yaml or clearly mark as "DO NOT USE"

---

### 2. **EPA Rolling Calculation: Potential Lookahead Bug**

**Problem**: In `src/features/epa.py`, the `_add_rolling_features` method iterates through games row-by-row, which is inefficient and could have subtle bugs.

**Location**: `src/features/epa.py:111-180`

**Issues**:
- Iterates through DataFrame rows (slow for 2,476 games)
- Uses `.iloc[0]` which assumes single match (could fail silently)
- No validation that metrics exist for each game

**Impact**: Low-Medium - Works but inefficient, could fail on edge cases

**Fix Needed**: Use vectorized operations with proper groupby/merge

---

### 3. **Injury Feature: Potential Future Leakage** ✅ **FIXED**

**Problem**: In `src/features/injury.py`, when no date column exists, fallback uses entire season, which could include injuries AFTER the game date.

**Status**: ✅ **FIXED** - Now filters by week when dates unavailable

**Impact**: Low-Medium - Only affects games with missing injury dates

---

### 4. **Centralized Feature Loader** ✅ **CREATED**

**Problem**: Feature selection logic duplicated across scripts.

**Status**: ✅ **CREATED** - `src/utils/feature_loader.py` provides centralized feature loading

**Impact**: Medium - Reduces risk of inconsistencies

---

### 4. **Feature Column Mismatch Risk**

**Problem**: Multiple places determine feature columns differently:

- `train_improved_model.py`: Uses `recommended_features.csv` OR excludes metadata
- `backtest.py`: Uses `recommended_features.csv` OR excludes metadata  
- `train_model.py`: Hardcoded exclude list (OLD script, uses old features)
- `tune_hyperparameters.py`: Hardcoded exclude list

**Risk**: If `recommended_features.csv` is deleted or modified, different scripts might use different feature sets.

**Impact**: High - Could cause model/feature mismatches

**Fix Needed**: Centralize feature selection logic

---

### 5. **Missing Feature Validation**

**Problem**: No validation that:
- Model expects same features as provided
- Feature order matches training
- Feature types match (numeric vs categorical)

**Location**: All training/backtest scripts

**Impact**: Medium - XGBoost will error, but error message might be unclear

**Fix Needed**: Add feature validation before prediction

---

### 6. **Model Save/Load Inconsistency**

**Problem**: 
- `train_improved_model.py` saves models as `.pkl` files
- `train_model.py` saves XGBoost as `.json` (different format)
- No standard model metadata (feature names, version, training date)

**Impact**: Medium - Hard to track which model uses which features

**Fix Needed**: Standardize model saving with metadata

---

### 7. **EPA Feature: Missing Error Handling**

**Problem**: In `_add_rolling_features`, if a game has no EPA data, it silently continues:

```python
if not home_metrics.empty:
    # Add metrics
# No else clause - silently skips
```

**Impact**: Low - Missing games get zeros, but should log warning

**Fix Needed**: Add logging for games with missing EPA data

---

### 8. **Referee Features: Historical Calculation Issue**

**Problem**: `RefereeFeatures` calculates stats from ALL games in the dataframe, including future games when calculating for a specific game.

**Location**: `src/features/referee.py:47-60`

**Issue**: 
```python
def _calculate_referee_stats(self, df: pd.DataFrame) -> pd.DataFrame:
    # Groups by referee across ALL games
    referee_games = df.groupby("referee").agg(...)
```

This includes future games when calculating for past games (temporal leakage).

**Impact**: **HIGH** - This is temporal data leakage!

**Fix Needed**: Calculate referee stats only from games BEFORE current game

---

### 9. **Feature Pipeline Order Dependency**

**Problem**: Feature builders are added in a specific order, and some depend on others:

- `LineFeatures` must come first (creates `spread_line`)
- `CategoricalEncodingFeatures` needs `roof`, `surface` from raw data
- `EPAFeatures` needs `game_id` to match with PBP

**Risk**: If order changes, features might break silently

**Impact**: Medium - Currently works but fragile

**Fix Needed**: Add dependency validation or make order explicit

---

### 10. **Missing Data Handling Inconsistency**

**Problem**: Different features handle missing data differently:
- EPA: Fills with 0
- Injury: Fills with 0
- Weather: Creates "missing" indicator columns
- Referee: Fills with 0.5 (neutral)

**Impact**: Low - Works but inconsistent

**Fix Needed**: Standardize missing data strategy

---

## ⚠️ Handoff Issues

### Script-to-Script Handoffs

1. **Feature File Paths**:
   - ✅ `train_improved_model.py` → `features_2016_2024_improved.parquet`
   - ✅ `backtest.py` → `features_2016_2024_improved.parquet`
   - ⚠️ `train_model.py` → `features_2016_2024.parquet` (OLD)
   - **Issue**: Two different training scripts use different files

2. **Model File Paths**:
   - ✅ `train_improved_model.py` → saves `xgboost_improved.pkl`
   - ✅ `backtest.py` → loads `xgboost_improved.pkl`
   - ⚠️ `train_model.py` → saves `xgboost_mvp.json` (different format)
   - **Issue**: Inconsistent model formats

3. **Feature List**:
   - ✅ Both use `recommended_features.csv` if available
   - ⚠️ Fallback logic differs slightly
   - **Issue**: Could diverge if CSV is missing

---

## 🔧 Recommended Fixes (Priority Order)

### Priority 1: Critical Bugs

1. **Fix Referee Temporal Leakage** (HIGH)
   - Calculate referee stats only from past games
   - Use rolling window per referee per season

2. **Fix Injury Future Leakage** (MEDIUM)
   - Add week-based filtering when dates missing
   - Ensure injuries are before game date

3. **Remove Betting Lines from Config** (MEDIUM)
   - Remove from `config.yaml` or mark as "DO NOT USE"
   - Add validation to prevent using betting line features

### Priority 2: Handoff Improvements

4. **Centralize Feature Selection** (HIGH)
   - Create `src/utils/feature_loader.py`
   - Single function to get feature columns
   - Used by all scripts

5. **Standardize Model Saving** (MEDIUM)
   - Save feature names with model
   - Add model metadata (version, date, features)
   - Validate on load

6. **Add Feature Validation** (MEDIUM)
   - Validate feature names match
   - Validate feature types
   - Validate feature order

### Priority 3: Code Quality

7. **Fix EPA Rolling Calculation** (LOW)
   - Use vectorized operations
   - Add error handling
   - Add logging for missing data

8. **Document Feature Dependencies** (LOW)
   - Add dependency graph
   - Validate order in pipeline

---

## ✅ What's Working Well

1. ✅ **No betting line leakage in models** - Properly excluded
2. ✅ **Temporal splits** - Correct train/val/test splits
3. ✅ **Feature file handoff** - Both scripts use improved features
4. ✅ **Model loading** - Handles both old and new models
5. ✅ **Missing feature handling** - Fills with 0 (safe default)

---

## 📋 Quick Fix Checklist

- [ ] Fix referee temporal leakage
- [ ] Fix injury future leakage  
- [ ] Remove betting lines from config.yaml
- [ ] Create centralized feature loader
- [ ] Add feature validation
- [ ] Standardize model saving with metadata
- [ ] Fix EPA rolling calculation efficiency
- [ ] Add logging for missing EPA data

---

**Next Steps**: Fix Priority 1 issues before paper trading!

