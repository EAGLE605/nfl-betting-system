# Handoff & Subtle Issues Audit

**Date**: 2025-11-24  
**Status**: ⚠️ **ISSUES FOUND & FIXED**

---

## ✅ Fixed Critical Issues

### 1. ✅ Data Leakage: Betting Line Features
- **Issue**: `home_favorite`, `line_movement`, `total_movement` were in recommended features
- **Status**: ✅ **FIXED** - Excluded from all scripts, regenerated recommended_features.csv
- **Action**: ⚠️ **MODEL NEEDS RETRAINING** (was trained with leakage)

### 2. ✅ Referee Temporal Leakage
- **Issue**: Referee stats calculated from all games (including future)
- **Status**: ✅ **FIXED** - Now uses only past games
- **Impact**: Prevents temporal data leakage

### 3. ✅ Injury Future Leakage
- **Issue**: Used entire season when dates missing
- **Status**: ✅ **FIXED** - Now filters by week when dates unavailable
- **Impact**: Prevents future information leakage

---

## ⚠️ Remaining Subtle Issues

### 1. **Model Was Trained With Data Leakage**

**Problem**: Current model (`xgboost_improved.pkl`) was trained with betting line features.

**Impact**: 
- 75% accuracy may be inflated
- 73.72% backtest win rate may not be valid
- Model needs retraining

**Action Required**:
```bash
# Regenerate features (already done - 41 features, no betting lines)
# Retrain model
python scripts/train_improved_model.py

# Re-run backtest  
python scripts/backtest.py
```

---

### 2. **EPA Rolling Calculation: Inefficient & Fragile**

**Location**: `src/features/epa.py:111-180`

**Issues**:
- Iterates through 2,476 games row-by-row (slow)
- Uses `.iloc[0]` assuming single match (could fail if multiple)
- No error handling if EPA data missing for a game
- Creates team_games_list in loop (memory inefficient)

**Impact**: Low-Medium
- Works but slow (~30 seconds for 2,476 games)
- Could fail silently on edge cases
- Not scalable for larger datasets

**Fix Needed**: Use vectorized pandas operations:
```python
# Instead of iterating, use merge + groupby
epa_metrics_pivot = epa_metrics.pivot_table(
    index=['game_id', 'team'], 
    values=['epa_offense', 'epa_defense', ...]
)
# Then merge and calculate rolling
```

---

### 3. **Feature Column Selection: Multiple Code Paths**

**Problem**: Feature selection logic duplicated in 4+ places:
- `scripts/train_improved_model.py`
- `scripts/backtest.py`
- `scripts/analyze_features.py`
- `scripts/tune_hyperparameters.py`
- `scripts/train_model.py` (old)

**Risk**: 
- If exclude list changes, must update multiple files
- Easy to miss one and cause inconsistency
- Different fallback logic in each

**Status**: ✅ **PARTIALLY FIXED** - Created `src/utils/feature_loader.py` but not yet integrated

**Action**: Update all scripts to use centralized loader

---

### 4. **Model Metadata Missing**

**Problem**: Saved models don't include:
- Feature names used for training
- Feature order (critical for XGBoost)
- Training date/version
- Data file used

**Impact**: Medium
- Hard to track which model uses which features
- Risk of feature mismatch errors
- Can't verify model/data compatibility

**Fix Needed**: Save model metadata:
```python
model_metadata = {
    "feature_names": feature_cols,
    "feature_order": feature_cols,  # XGBoost is order-sensitive
    "training_date": datetime.now(),
    "data_file": "features_2016_2024_improved.parquet",
    "n_features": len(feature_cols)
}
joblib.dump({"model": model, "metadata": model_metadata}, path)
```

---

### 5. **Config.yaml Lists Betting Lines as Features**

**Location**: `config/config.yaml:34-36`

**Problem**: Lists `spread_line`, `total_line`, `home_favorite` as "core features"

**Impact**: Low-Medium
- Misleading documentation
- Could confuse future developers
- Doesn't match actual usage

**Fix Needed**: Remove or mark as "DO NOT USE - DATA LEAKAGE"

---

### 6. **EPA Feature: Missing Data Handling**

**Problem**: In `_add_rolling_features`, if EPA data missing for a game:
- Silently skips (no warning)
- Game gets zeros for EPA features
- No logging of how many games affected

**Impact**: Low
- Works but hides data quality issues
- Could mask problems

**Fix Needed**: Add logging:
```python
missing_count = len(df) - len(team_games) // 2  # Divide by 2 (home+away)
if missing_count > 0:
    logger.warning(f"EPA data missing for {missing_count} games")
```

---

### 7. **Referee Feature: Merge Issue**

**Problem**: Referee stats merged by `referee` only, but should merge by `game_id` + `referee` to ensure correct mapping.

**Location**: `src/features/referee.py:43`

**Current**:
```python
df.merge(referee_stats, on="referee", ...)
```

**Issue**: If same referee has multiple games on same day, could merge incorrectly.

**Status**: ✅ **FIXED** - Now merges on `["game_id", "referee"]`

---

### 8. **Feature Pipeline Order Dependency**

**Problem**: Feature builders must be added in specific order:
1. `LineFeatures` - Creates `spread_line` (needed for exclusions)
2. `CategoricalEncodingFeatures` - Needs raw `roof`, `surface`
3. `EPAFeatures` - Needs `game_id` to match PBP

**Risk**: If order changes, features might break silently

**Impact**: Medium - Currently works but fragile

**Fix Needed**: Add dependency validation or make explicit

---

### 9. **Missing Feature Validation**

**Problem**: No validation that:
- Model features match data features
- Feature order matches (XGBoost requirement)
- Feature types match

**Impact**: Medium
- XGBoost will error, but error might be unclear
- Could waste time debugging

**Status**: ✅ **PARTIALLY FIXED** - Created `validate_features()` in `feature_loader.py` but not used

---

### 10. **Injury Feature: Week Column Assumption**

**Problem**: Injury fallback assumes `week` column exists:
```python
if "week" in injuries.columns and "week" in game:
```

**Issue**: Injury data might not have `week` column

**Impact**: Low - Falls back to season-level (with warning)

**Fix Needed**: More robust fallback logic

---

## 🔄 Handoff Issues

### Script-to-Script Handoffs

| Handoff | Status | Issue |
|---------|--------|-------|
| `train_improved_model.py` → `backtest.py` | ✅ Good | Both use `recommended_features.csv` |
| Feature file path | ✅ Good | Both use `features_2016_2024_improved.parquet` |
| Model file path | ✅ Good | Both use `xgboost_improved.pkl` |
| Feature exclusion | ⚠️ **FIXED** | Now consistent (betting lines excluded) |

### Data-to-Feature Handoffs

| Handoff | Status | Issue |
|---------|--------|-------|
| Raw → Processed | ✅ Good | Clear file naming |
| Feature generation | ⚠️ Fragile | Order-dependent, no validation |
| Missing data | ⚠️ Inconsistent | Different strategies per feature |

### Model Handoffs

| Handoff | Status | Issue |
|---------|--------|-------|
| Training → Backtest | ⚠️ **NEEDS RETRAIN** | Model trained with leakage |
| Model saving | ⚠️ Missing metadata | No feature names saved |
| Model loading | ✅ Works | Handles both old/new formats |

---

## 📋 Priority Fix Checklist

### Immediate (Before Paper Trading)

- [x] Fix betting line feature exclusion ✅
- [x] Fix referee temporal leakage ✅
- [x] Fix injury future leakage ✅
- [ ] **RETRAIN MODEL** (without betting lines) ⚠️ **REQUIRED**
- [ ] **RE-RUN BACKTEST** (with honest model) ⚠️ **REQUIRED**

### High Priority (Before Production)

- [ ] Integrate centralized feature loader
- [ ] Add model metadata saving
- [ ] Add feature validation
- [ ] Remove betting lines from config.yaml

### Medium Priority (Code Quality)

- [ ] Optimize EPA rolling calculation
- [ ] Add logging for missing EPA data
- [ ] Document feature dependencies
- [ ] Standardize missing data handling

---

## 🎯 Summary

### What's Working ✅

1. ✅ No data leakage in current code (fixed)
2. ✅ Temporal splits correct
3. ✅ Feature file handoffs consistent
4. ✅ Model loading handles both formats
5. ✅ Missing feature handling (fills with 0)

### What Needs Attention ⚠️

1. ⚠️ **MODEL RETRAINING REQUIRED** (was trained with leakage)
2. ⚠️ Feature selection duplicated (needs centralization)
3. ⚠️ Model metadata missing (hard to track)
4. ⚠️ EPA calculation inefficient (works but slow)
5. ⚠️ Config.yaml misleading (lists betting lines)

### Critical Action Items

**BEFORE USING MODEL**:
1. Retrain model without betting line features
2. Re-run backtest with honest model
3. Validate results still meet GO criteria

**The 75% accuracy is likely inflated due to data leakage!**

---

**Next Steps**: See `CRITICAL_FIXES_REQUIRED.md` for retraining instructions.

