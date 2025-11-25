# 🚀 Dashboard Launch Guide

## Quick Answer

**To launch the dashboard:**

```bash
streamlit run dashboard/app.py
```

**Does it start the backend automatically?** 
✅ **YES!** The dashboard includes everything - frontend UI and all backend logic run together.

---

## 📋 Understanding the Architecture

### All-in-One Design

```
┌─────────────────────────────────────────┐
│         STREAMLIT DASHBOARD             │
│  (Frontend + Backend Together)          │
├─────────────────────────────────────────┤
│  🎨 UI Components                       │
│  ├─ Pick Display                        │
│  ├─ Performance Charts                  │
│  ├─ Backtesting Lab                     │
│  └─ Settings Panel                      │
│                                          │
│  🔧 Backend Logic (Auto-Loaded)         │
│  ├─ Model Inference                     │
│  ├─ API Integrations                    │
│  ├─ Data Caching                        │
│  └─ Feature Engineering                 │
└─────────────────────────────────────────┘
```

**Key Point:** Streamlit runs a Python web server that handles BOTH the UI and the backend logic. When you start the dashboard, everything starts together!

---

## 🎯 Launch Options

### Option 1: Simple Launch (Recommended)

**Windows:**
```bash
streamlit run dashboard/app.py
```

**Mac/Linux:**
```bash
streamlit run dashboard/app.py
```

**What happens:**
- ✅ Dashboard opens in your browser at `http://localhost:8501`
- ✅ All backend logic loads automatically
- ✅ API connections initialize on first use
- ✅ Models load when needed (lazy loading)
- ✅ Cache system activates automatically

---

### Option 2: With Virtual Environment

**Windows:**
```bash
# Activate venv
.venv\Scripts\activate

# Launch dashboard
streamlit run dashboard/app.py
```

**Mac/Linux:**
```bash
# Activate venv
source .venv/bin/activate

# Launch dashboard
streamlit run dashboard/app.py
```

---

### Option 3: Using Startup Scripts

**Windows:**
```bash
# Launch with authentication (app_complete.py)
start_dashboard_auth.bat
```

**Mac/Linux:**
```bash
# Launch with authentication
./start_dashboard_auth.sh
```

**Note:** These scripts use `app_complete.py` which includes authentication. For the new Backtesting Lab, use `app.py` directly.

---

## 🔄 What Gets Loaded Automatically

### On Dashboard Startup

```python
1. Streamlit Server Starts
   ├─ Loads app.py
   └─ Initializes session state

2. UI Components Render
   ├─ Tabs load (Picks, Performance, Bankroll, Tracker, Backtest, Settings)
   └─ Custom CSS applies

3. Backend Stays Ready
   ├─ Imports cached (but not executed)
   └─ Functions ready to call
```

### On First User Action

```python
When you click "Generate Picks":
1. Imports needed modules
   ├─ from agents.api_integrations import TheOddsAPI
   ├─ from src.models.xgboost_model import XGBoostNFLModel
   └─ from src.utils.odds_cache import OddsCache

2. Initializes services
   ├─ Cache system activates
   ├─ API client connects
   └─ Model loads into memory

3. Executes request
   ├─ Fetches data (from cache or API)
   ├─ Runs predictions
   └─ Displays results
```

**This is GOOD:**
- Fast initial load
- Only loads what you use
- Saves memory
- Better performance

---

## 📊 Dashboard Components

### Main Dashboard (`dashboard/app.py`)

**What it includes:**

```
Tab 1: 🎯 Picks
├─ Today's best bets
├─ Confidence scoring
└─ Line shopping

Tab 2: 📊 Performance
├─ Win rate tracking
├─ ROI charts
└─ Equity curve

Tab 3: 💰 Bankroll
├─ Kelly sizing calculator
├─ Bet size recommendations
└─ Risk management

Tab 4: 🔔 Tracker
├─ Bet tracking
├─ Results logging
└─ History export

Tab 5: 🧪 Backtest (NEW!)
├─ 🧪 Training Lab (Visual AI training)
└─ 📊 Results (Traditional backtest view)

Tab 6: ⚙️ Settings
├─ API key management
├─ Notification preferences
└─ About
```

### Backend Services (Auto-Load)

**Loaded when needed:**

```python
# API Integrations (agents/api_integrations.py)
- TheOddsAPI: Fetches NFL odds
- ESPNAPI: Gets team/game data
- NOAAAPI: Weather data

# Models (src/models/)
- XGBoostNFLModel: Main prediction model
- Ensemble models when available

# Caching (src/utils/odds_cache.py)
- Multi-layer cache (memory/file/database)
- Automatic rate limiting
- Historical data storage

# Feature Engineering (src/features/)
- ELO ratings
- EPA metrics
- Weather adjustments
```

---

## 🛠️ Configuration

### Before First Launch

1. **Set API Keys** (optional but recommended):
   ```bash
   # Edit config/api_keys.env
   ODDS_API_KEY=your_key_here
   NOAA_API_KEY=not_required
   ESPN_API_KEY=not_required
   ```

2. **Verify Models Exist**:
   ```bash
   # Check for trained models
   ls models/
   # Should see: xgboost_*.pkl, ensemble_model.pkl, etc.
   ```

3. **Verify Data** (for backtesting):
   ```bash
   ls data/processed/
   # Should see: features_*.parquet files
   ```

---

## 🚀 Step-by-Step Launch

### First Time Setup

```bash
# 1. Navigate to project directory
cd C:\Scripts\nfl-betting-system

# 2. Activate virtual environment
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux

# 3. Install dashboard dependencies (if not done)
pip install streamlit plotly pandas

# 4. Launch dashboard
streamlit run dashboard/app.py
```

### What You'll See

```
Terminal Output:
===============
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.x:8501

  For better performance, try:
  streamlit run dashboard/app.py --server.enableCORS false
```

**Browser automatically opens to:** `http://localhost:8501`

---

## ⚡ Performance Tips

### Faster Startup

```bash
# Disable CORS checking (local use only)
streamlit run dashboard/app.py --server.enableCORS false

# Increase max file size for larger datasets
streamlit run dashboard/app.py --server.maxUploadSize 500

# Custom port
streamlit run dashboard/app.py --server.port 8080
```

### Better Caching

```python
# Dashboard uses Streamlit's built-in caching
@st.cache_data  # For data/DataFrames
@st.cache_resource  # For models/connections

# Cache automatically:
- Loads models once
- Caches API responses
- Stores computed features
- Persists across sessions
```

---

## 🔍 What Happens Behind the Scenes

### On `streamlit run dashboard/app.py`

```python
1. Streamlit Server Starts
   └─ Python web server on localhost:8501
   
2. app.py Loads
   └─ Executes top-level imports
   └─ Defines functions (doesn't run them)
   
3. Browser Connects
   └─ Sends initial page request
   
4. First Render
   └─ Executes app.py from top to bottom
   └─ Displays UI
   
5. User Interaction
   └─ Click button → triggers function
   └─ Function imports needed modules
   └─ Modules load backend logic
   └─ Result displays in UI
```

### Memory Management

```
Initial Load:
├─ Streamlit: ~100MB
├─ Dashboard UI: ~50MB
└─ Session State: ~10MB
Total: ~160MB

After Using Features:
├─ Loaded Models: +200MB
├─ Cache Data: +50MB
├─ API Connections: +20MB
Total: ~430MB

Max Usage: ~500MB (very reasonable!)
```

---

## 🐛 Troubleshooting

### Dashboard Won't Start

**Error:** `ModuleNotFoundError: No module named 'streamlit'`

**Solution:**
```bash
pip install streamlit plotly pandas
```

---

**Error:** `Port 8501 is already in use`

**Solution:**
```bash
# Option 1: Use different port
streamlit run dashboard/app.py --server.port 8502

# Option 2: Kill existing process
# Windows:
taskkill /F /IM streamlit.exe

# Mac/Linux:
pkill -f streamlit
```

---

### Backend Features Not Working

**Issue:** "No picks available" or "API error"

**Check:**

1. **API Keys Set?**
   ```bash
   cat config/api_keys.env
   # Should see: ODDS_API_KEY=your_key
   ```

2. **Models Exist?**
   ```bash
   ls models/
   # Should see .pkl files
   ```

3. **Cache Writable?**
   ```bash
   ls -la data/odds_cache/
   # Should have write permissions
   ```

---

### Backtesting Lab Won't Load

**Error:** "Error loading Backtesting Lab"

**Solution:**

1. **Check file exists:**
   ```bash
   ls dashboard/backtesting_lab.py
   ```

2. **Switch to Results view:**
   - Dashboard → Backtest tab
   - Select "📊 Results" instead of "🧪 Training Lab"

3. **Check logs:**
   - Look for error message in dashboard
   - Check terminal output for stack trace

---

## 🎓 Advanced Usage

### Running in Production

```bash
# With optimizations
streamlit run dashboard/app.py \
  --server.port 80 \
  --server.enableCORS false \
  --server.enableXsrfProtection true \
  --server.maxUploadSize 1000
```

### Running as Background Service

**Windows (PowerShell):**
```powershell
Start-Process streamlit -ArgumentList "run dashboard/app.py" -WindowStyle Hidden
```

**Mac/Linux:**
```bash
nohup streamlit run dashboard/app.py > dashboard.log 2>&1 &
```

### Multiple Dashboards

```bash
# Main dashboard (port 8501)
streamlit run dashboard/app.py

# Admin panel (port 8502)
streamlit run dashboard/admin_panel.py --server.port 8502

# AI Reasoning (port 8503)
streamlit run dashboard/ai_reasoning_swarm.py --server.port 8503
```

---

## 📝 Summary

### Simple Answer

```bash
# Just run this:
streamlit run dashboard/app.py

# Everything starts automatically:
✅ Frontend UI
✅ Backend logic
✅ API connections
✅ Cache system
✅ Model loading
```

### Architecture

- **Streamlit = Frontend + Backend** (all-in-one)
- **No separate backend server needed**
- **Components load on-demand** (lazy loading)
- **Cache prevents redundant work**
- **Session state persists data**

### When Things Load

- **On Startup**: UI components, basic imports
- **On First Use**: Models, API clients, heavy data
- **On Demand**: Features you actually use
- **Never**: Things you don't need

### Memory-Efficient

- Initial: ~160MB
- Full Usage: ~430MB
- Max: ~500MB
- ✅ Very reasonable for a complete betting system!

---

## 🎯 Quick Reference

| Task | Command |
|------|---------|
| Launch dashboard | `streamlit run dashboard/app.py` |
| Custom port | `streamlit run dashboard/app.py --server.port 8080` |
| Stop dashboard | `Ctrl+C` in terminal |
| Clear cache | In dashboard: Settings → Clear Cache |
| View logs | Check terminal output |
| Access remotely | Use Network URL shown in terminal |

---

**Questions?**

- Dashboard not loading? → Check [Troubleshooting](#-troubleshooting)
- Want to customize? → Edit `dashboard/app.py`
- Need help with Lab? → See `dashboard/BACKTESTING_LAB_README.md`

**Ready to launch?** Just run: `streamlit run dashboard/app.py` 🚀

