# NFL Betting System

**Status**: Week 1 MVP - Data Pipeline Complete ✓  
**Target**: 55-60% accuracy, 5-12% ROI on $5-10K bankroll  
**Model**: XGBoost classifier with probability calibration

---

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment (Python 3.12)
py -3.12 -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Download Data

```bash
# Download 2016-2024 seasons (default)
python scripts/download_data.py

# Download specific seasons
python scripts/download_data.py --seasons 2020-2024

# Force re-download (ignore cache)
python scripts/download_data.py --force

# Skip play-by-play (faster, fewer features)
python scripts/download_data.py --no-pbp
```

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_data_pipeline.py -v
```

---

## 🔐 Security & API Keys

**IMPORTANT**: This project requires API keys that must be kept secure.

### First-Time Setup

1. **Copy the API keys template:**
   ```powershell
   Copy-Item config/api_keys.env.template config/api_keys.env
   ```

2. **Get your API keys:**
   - **The Odds API** (Required): https://the-odds-api.com/
     - Free tier: 500 requests/month
     - Sign up and copy your API key
   
   - **xAI Grok API** (Optional): https://x.ai/api
     - For AI-powered analysis and insights

3. **Add keys to `config/api_keys.env`:**
   ```bash
   ODDS_API_KEY=your_actual_key_here
   XAI_API_KEY=your_xai_key_here  # Optional
   ```

4. **Verify protection:**
   ```powershell
   # This should show the file is gitignored
   git check-ignore -v config/api_keys.env
   ```

### ⚠️ Security Rules

- ✅ **DO**: Store keys in `config/api_keys.env` (gitignored)
- ✅ **DO**: Use `os.getenv('KEY_NAME')` to load keys
- ❌ **DON'T**: Hardcode API keys in code
- ❌ **DON'T**: Commit `config/api_keys.env` to git
- ❌ **DON'T**: Share keys in issues or pull requests

📖 **See [SECURITY.md](SECURITY.md) for full security guidelines**

---

## Project Structure

```
nfl-betting-system/
├── data/
│   ├── raw/                    # Raw downloads from nflverse
│   │   ├── schedules_*.parquet
│   │   ├── pbp_*.parquet
│   │   ├── weekly_*.parquet
│   │   ├── teams.parquet
│   │   └── metadata.json
│   ├── processed/              # Engineered features (Day 3-4)
│   └── models/                 # Trained models (Day 5-6)
│
├── src/
│   ├── data_pipeline.py        # ✓ Data download & validation
│   ├── feature_engineering.py  # TODO: EPA, Elo, rest days
│   ├── model.py                # TODO: XGBoost + calibration
│   └── backtesting.py          # TODO: Historical validation
│
├── scripts/
│   ├── download_data.py        # ✓ CLI data downloader
│   ├── train_model.py          # TODO: Model training
│   └── backtest.py             # TODO: Backtest runner
│
├── tests/
│   ├── test_data_pipeline.py   # ✓ Data pipeline tests
│   ├── test_features.py        # TODO: Feature tests
│   └── test_model.py           # TODO: Model tests
│
├── requirements.txt            # ✓ Dependencies
├── pytest.ini                  # ✓ Test configuration
└── README.md                   # ✓ This file
```

---

## Data Pipeline (✓ Complete)

### What Data is Downloaded?

| Data Type | Size | Purpose |
|-----------|------|---------|
| **Schedules** | ~2,500 games | Game results, scores, home/away |
| **Play-by-play** | ~450K plays | EPA, success rate, play distribution |
| **Weekly Stats** | ~15K player-weeks | Team performance metrics |
| **Teams** | ~32 teams | Team metadata, divisions |

### Data Quality

- ✓ Schema validation (required columns)
- ✓ Null checks (warn on critical nulls)
- ✓ Range validation (dates within seasons)
- ✓ Smart caching (avoid re-downloads)

### API Source

Uses **nfl_data_py** (nflverse):
- Free, unlimited access
- Updated weekly during season
- Historical data back to 1999
- No API keys required

---

## Next Steps (Week 1 Roadmap)

### ✓ Day 1-2: Data Pipeline (COMPLETE)
- [x] Download schedules, play-by-play, weekly stats
- [x] Parquet storage with caching
- [x] Data validation
- [x] Unit tests

### TODO: Day 3-4: Feature Engineering (8-10 hours)
- [ ] EPA (Expected Points Added) per play
- [ ] Elo ratings for team strength
- [ ] Rest days between games
- [ ] Home/away splits
- [ ] Recent form (last 3 games)

### TODO: Day 5-6: Model Training (8-10 hours)
- [ ] XGBoost classifier
- [ ] Probability calibration (Platt scaling)
- [ ] Train/validation split (time-based)
- [ ] Hyperparameter tuning

### TODO: Day 7: Backtesting (4-6 hours)
- [ ] 1/4 Kelly criterion bet sizing
- [ ] Calculate accuracy, ROI, Sharpe ratio
- [ ] GO/NO-GO decision (≥55% accuracy required)

---

## Testing

### Run Tests

```bash
# All tests
pytest

# Verbose output
pytest -v

# Coverage report
pytest --cov=src --cov-report=html tests/

# Specific test
pytest tests/test_data_pipeline.py::TestNFLDataPipeline::test_get_schedules_download -v
```

### Test Coverage

Current: ~85% (data pipeline only)  
Target: >80% for all modules

---

## Development Workflow

1. **Activate environment**: `.venv\Scripts\activate`
2. **Make changes**: Edit code in `src/`
3. **Run tests**: `pytest`
4. **Check types**: `mypy src/`
5. **Format code**: `black src/ tests/`
6. **Lint**: `ruff check src/ tests/`

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'nfl_data_py'"

```bash
pip install -r requirements.txt
```

### "Download failed: HTTP 404"

- Check internet connection
- Verify season years are valid (1999-2024)
- Try with `--no-pbp` flag

### "Validation failed: missing columns"

- Re-download with `--force` flag
- Check nfl_data_py version: `pip show nfl-data-py`
- Update if needed: `pip install --upgrade nfl-data-py`

---

## Resources

- **nflverse docs**: https://nflreadr.nflverse.com/
- **nfl_data_py**: https://github.com/cooperdff/nfl_data_py
- **XGBoost**: https://xgboost.readthedocs.io/
- **Calibration**: https://scikit-learn.org/stable/modules/calibration.html

---

## License

MIT License - See LICENSE file for details

---

**Last Updated**: 2025-11-23  
**Status**: Data Pipeline Complete ✓  
**Next**: Feature Engineering (Day 3-4)


