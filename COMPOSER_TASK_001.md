# Composer Task 001: Download Play-by-Play Data

**Task ID**: comp1-01  
**Assigned To**: Composer (AI Coder)  
**Architect**: Claude (Oversight)  
**Priority**: HIGH (blocking other EPA tasks)  
**Estimated Time**: 15-20 minutes

---

## Objective

Download NFL play-by-play (PBP) data for seasons 2016-2024 to enable EPA feature engineering.

---

## Current State

The system currently downloads:
- ✅ Schedules (game results)
- ✅ Weekly offense stats
- ✅ Team descriptions

But does NOT download:
- ❌ Play-by-play data (needed for EPA features)

The `download_data.py` script has a `--no-pbp` flag but **by default it should download PBP**. Currently, the PBP download is either:
- Not implemented, OR
- Implemented but commented out, OR  
- Has a bug

---

## Requirements

### 1. Verify Current Implementation

**File**: `scripts/download_data.py`

Check if PBP download exists:
```python
# Look for something like:
pbp = pipeline.get_play_by_play(seasons, force_download=args.force)
```

### 2. Implement PBP Download (if missing)

**Expected API** (from nfl_data_py):
```python
import nfl_data_py as nfl

# Download play-by-play data
pbp_df = nfl.import_pbp_data(years=[2023, 2024])
```

**Integration Points**:

a) **In `src/data_pipeline.py`**: Add method if missing
```python
def get_play_by_play(self, seasons: List[int], force_download: bool = False) -> pd.DataFrame:
    """
    Download play-by-play data from nflverse.
    
    Args:
        seasons: List of season years (e.g., [2023, 2024])
        force_download: If True, ignore cache and re-download
        
    Returns:
        DataFrame with play-by-play data including EPA
    """
    # Implementation here
```

b) **In `scripts/download_data.py`**: Add to download logic
```python
if not args.no_pbp:
    print("\n3. Downloading play-by-play data...")
    pbp = pipeline.get_play_by_play(seasons, force_download=args.force)
    print(f"✓ Play-by-play: {len(pbp):,} plays")
```

### 3. Data Storage

**Filename Pattern**: `data/raw/pbp_YYYY_YYYY.parquet`
- Example: `data/raw/pbp_2016_2024.parquet`

**Expected Columns** (verify these exist):
- `game_id` - Unique game identifier
- `play_id` - Unique play identifier  
- `posteam` - Possession team abbreviation
- `defteam` - Defensive team abbreviation
- `epa` - Expected Points Added (CRITICAL!)
- `qtr` - Quarter
- `down` - Down (1-4)
- `ydstogo` - Yards to go
- `play_type` - Play type (pass, run, etc.)
- `success` - Binary success indicator

### 4. Data Validation

After download, validate:
```python
assert 'epa' in pbp.columns, "EPA column missing!"
assert 'game_id' in pbp.columns, "game_id column missing!"
assert len(pbp) > 400000, f"Expected 400K+ plays, got {len(pbp)}"
assert pbp['epa'].notna().sum() > 0, "All EPA values are null!"
```

### 5. Update Progress Display

Add progress bars/status for PBP download (might take 2-5 minutes):
```python
print(f"Downloading PBP data for {len(seasons)} seasons...")
# Show progress if possible
```

---

## Implementation Steps

### Step 1: Read Existing Code
```bash
# Read these files to understand current implementation
- scripts/download_data.py
- src/data_pipeline.py (look for get_play_by_play or similar)
```

### Step 2: Check if PBP Method Exists
- If exists: Ensure it's being called in download_data.py
- If missing: Implement in data_pipeline.py

### Step 3: Implement/Fix PBP Download

**Key points**:
- Use `nfl_data_py.import_pbp_data(years=seasons)`
- Save to parquet: `data/raw/pbp_{min}_{max}.parquet`
- Add caching logic (check if file exists and is recent)
- Handle errors gracefully

### Step 4: Test the Download
```powershell
# Test with single season first
python scripts/download_data.py --seasons 2023 --force

# Should see output like:
# 3. Downloading play-by-play data...
# ✓ Play-by-play: 31,234 plays

# Verify file exists
ls data/raw/pbp_2023_2023.parquet
```

### Step 5: Download Full Dataset
```powershell
# Download all seasons (2016-2024)
python scripts/download_data.py --force

# Expected output:
# ✓ Play-by-play: ~450,000 plays
# File size: ~150 MB
```

---

## Acceptance Criteria

- [ ] `data/raw/pbp_2016_2024.parquet` exists
- [ ] File size: 100-200 MB
- [ ] Row count: 400,000 - 500,000 plays
- [ ] Contains `epa` column with numeric values
- [ ] Contains `game_id` column matching schedules
- [ ] Script completes without errors
- [ ] Cache functionality works (re-run doesn't re-download)

---

## Testing Commands

```powershell
# 1. Activate environment
.venv\Scripts\activate

# 2. Test download
python scripts/download_data.py --seasons 2023 --force

# 3. Verify in Python
python -c "import pandas as pd; pbp = pd.read_parquet('data/raw/pbp_2023_2023.parquet'); print(f'Rows: {len(pbp):,}'); print(f'Columns: {list(pbp.columns[:10])}'); print(f'EPA nulls: {pbp.epa.isna().sum()}')"

# Expected output:
# Rows: 30,000-35,000
# Columns: ['game_id', 'play_id', 'epa', ...]
# EPA nulls: <5000 (some plays don't have EPA)
```

---

## Known Issues / Edge Cases

1. **Large Download**: PBP data is ~150MB, may take 2-5 minutes
2. **EPA Nulls**: Some plays (kickoffs, penalties) don't have EPA - this is normal
3. **Memory Usage**: Loading 450K plays requires ~500MB RAM
4. **nflverse API**: Sometimes slow, may need retry logic

---

## What NOT to Do

❌ Don't modify feature engineering yet (that's Task 2)  
❌ Don't change existing download logic for schedules/weekly stats  
❌ Don't add EPA features yet (just download raw data)  
❌ Don't run backtest or training (just download data)

---

## Deliverables

1. **Code Changes**:
   - `src/data_pipeline.py` (if method missing/broken)
   - `scripts/download_data.py` (ensure PBP is called)

2. **Data File**:
   - `data/raw/pbp_2016_2024.parquet`

3. **Verification**:
   - Run test command and paste output
   - Confirm file size and row count

---

## Architect Review Checklist

After Composer completes this task, I (Claude) will verify:

- [ ] Code follows existing patterns in data_pipeline.py
- [ ] Caching logic is consistent with other methods
- [ ] Error handling is robust
- [ ] Data validation checks are present
- [ ] EPA column exists and has reasonable values
- [ ] No data leakage (PBP data is historical, before games)
- [ ] File size and row counts are reasonable

---

## Next Task (After This Completes)

**Task 002**: Implement EPA feature engineering using the downloaded PBP data.

---

**Status**: 🟡 IN PROGRESS  
**Created**: 2025-11-24  
**Assigned**: Composer (AI Coder)  
**Architect**: Claude (will review upon completion)

