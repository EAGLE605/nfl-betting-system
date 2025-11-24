# Architect Review: Task 002 - EPA Features

**Date**: 2025-11-24  
**Task**: EPA Feature Engineering  
**Reviewer**: Claude (Architect)  
**Status**: 🟡 IN PROGRESS - Needs Testing & Validation

---

## Code Review Summary

### ✅ GOOD Implementation Choices

1. **Anti-Lookahead**: Line 163 uses `.shift(1)` to prevent data leakage ✅
2. **Rolling Windows**: 3-game rolling average (reasonable for NFL)
3. **Separate Offense/Defense**: Properly separates EPA by possession
4. **Success Metrics**: Includes success rate (EPA > 0) and explosive plays (EPA > 1.5)
5. **Season Grouping**: Rolling averages reset per season (line 162)
6. **8 Features**: Reasonable number of EPA features

### ⚠️ POTENTIAL ISSUES

1. **Performance**: Lines 118-147 use nested loops (slow for 2,476 games)
   - Could be vectorized with pandas operations
   - Not critical for this dataset size, but suboptimal

2. **No Validation**: Should verify EPA values are in reasonable range
   - Typical EPA: -5.0 to +5.0
   - Outliers could indicate data quality issues

3. **Rolling Calculation**: Line 162-166 complex groupby + shift + rolling
   - Need to verify this works correctly
   - Potential for subtle bugs

4. **No Tests**: No unit tests for EPA features yet

---

## Required Validations

### 1. Data Leakage Check
**Critical**: Ensure features only use PAST games, not future

```python
# Test: Features at game N should only use games 1 to N-1
# The shift(1) should prevent this, but must verify
```

### 2. Feature Value Check
**Important**: Verify EPA values are reasonable

```python
# Expected ranges:
# - epa_offense: -0.2 to +0.3 (per play average)
# - epa_defense: -0.2 to +0.3
# - success_rate: 0.35 to 0.55
# - explosive_rate: 0.10 to 0.25
```

### 3. Null Check
**Important**: First few games will have nulls (no history)

```python
# Should fill with 0.0 (done on line 65)
# But verify this happens correctly
```

---

## Testing Strategy

### Test 1: Run Feature Pipeline
```powershell
python -c "
from src.features.pipeline import FeaturePipeline
import pandas as pd

# Load data
schedules = pd.read_parquet('data/raw/schedules_2016_2024.parquet')
pbp = pd.read_parquet('data/raw/pbp_2016_2024.parquet')

# Build features
pipeline = FeaturePipeline(
    schedules_df=schedules,
    pbp_df=pbp,
    weekly_stats_df=None
)
features = pipeline.build_features()

# Check EPA features exist
epa_cols = [col for col in features.columns if 'epa_' in col]
print(f'EPA features: {epa_cols}')
print(f'Feature shape: {features.shape}')
print(f'Null counts: {features[epa_cols].isnull().sum()}')
"
```

### Test 2: Value Ranges
```python
# Check if EPA values are reasonable
print(features[epa_cols].describe())

# Expected:
# - Mean should be close to 0
# - Min/Max should be reasonable (-1 to +1 for offense/defense)
# - No extreme outliers
```

### Test 3: Data Leakage Test
```python
# Critical: Verify first games of season have null/zero EPA
first_games = features.groupby(['season', 'home_team']).first()
print(first_games[epa_cols].describe())

# Expected: Many nulls or zeros (no prior games)
```

---

## Recommendations

### High Priority
1. ✅ **Run Test 1**: Verify pipeline runs without errors
2. ✅ **Run Test 2**: Check value ranges are reasonable
3. ✅ **Run Test 3**: Verify no data leakage

### Medium Priority
4. ⚠️ **Performance**: Consider vectorizing the team-game loop (lines 118-147)
5. ⚠️ **Logging**: Add more detailed logging for debugging

### Low Priority
6. 📝 **Unit Tests**: Add tests to `tests/test_epa.py`
7. 📝 **Documentation**: Add examples to docstrings

---

## Decision Points

### If Tests Pass
→ ✅ **APPROVE** Task 2  
→ Proceed to Task 3 (categorical encoding) or Task 4 (skip injuries)

### If Value Ranges Weird
→ ⚠️ **INVESTIGATE** EPA calculation logic  
→ May need to adjust aggregation or filtering

### If Data Leakage Detected
→ 🚨 **CRITICAL FIX REQUIRED**  
→ Stop all other tasks, fix shift(1) logic

---

## Next Steps

1. **Composer**: Run the feature pipeline and report results
2. **Architect**: Review output and validate ranges
3. **Decision**: Approve or request fixes

---

**Status**: 🟡 AWAITING TEST RESULTS  
**Blocker**: Need to run feature pipeline to validate  
**ETA**: 5-10 minutes

