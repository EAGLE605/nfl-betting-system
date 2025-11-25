# AI MODELS & API USAGE GUIDE

**Date**: 2025-11-24
**Status**: Complete system analysis

---

## 🤖 AI MODELS USED IN THE SYSTEM

### 1. **Machine Learning Models (Prediction Engine)**

#### XGBoost Classifier - PRIMARY PREDICTION MODEL
- **Purpose**: Predict NFL game outcomes (home team win probability)
- **Location**: `src/models/xgboost_model.py`
- **Training**: `scripts/train_model.py`
- **Input Features**:
  - Elo ratings
  - EPA (Expected Points Added)
  - Form/momentum (rolling win %)
  - Rest days
  - Weather conditions
  - Referee tendencies
  - Spread lines
  - ~50+ total features
- **Output**: Probability of home team winning (0-1)
- **Usage**:
  - Swarm agents use these predictions
  - Backtesting engine validates strategies
  - Daily pick generation
- **Cost**: FREE (you train locally)

#### LightGBM / Ensemble Models (Optional)
- **Purpose**: Alternative/complementary ML models
- **Location**: `src/models/`
- **Status**: Supported by ModelLoader and PredictionPipeline
- **Cost**: FREE (train locally)

**Key Point**: These are YOUR trained models, saved as `.pkl` files in `models/` directory. No API calls needed during prediction - just load the model and predict.

---

### 2. **Large Language Models (LLMs) - AI Reasoning Swarm**

#### GPT-4 (OpenAI)
- **Purpose**: Strategic bet analysis and reasoning
- **Location**: `dashboard/ai_reasoning_swarm.py`
- **API Used**: OpenAI API (`openai` Python library)
- **Model**: `gpt-4`
- **Features**:
  - Analyzes bet recommendations
  - Provides 2-3 sentence expert analysis
  - Identifies key factors and risks
- **Cost**: ~$0.03 per analysis (200 tokens)
- **Requires**: `OPENAI_API_KEY`

#### Claude 3.5 Sonnet (Anthropic)
- **Purpose**: Risk assessment and validation
- **Location**: `dashboard/ai_reasoning_swarm.py`
- **API Used**: Anthropic API (`anthropic` Python library)
- **Model**: `claude-3-5-sonnet-20241022`
- **Features**:
  - Strategic value assessment
  - Risk factor identification
  - Overall bet assessment
- **Cost**: ~$0.015 per analysis (200 tokens)
- **Requires**: `ANTHROPIC_API_KEY`

#### Gemini Pro (Google)
- **Purpose**: Comprehensive review and consensus
- **Location**: `dashboard/ai_reasoning_swarm.py`
- **API Used**: Google Generative AI (`google.generativeai` library)
- **Model**: `gemini-pro`
- **Features**:
  - Value analysis
  - Concern identification
  - Confidence rating
- **Cost**: FREE tier available (15 requests/minute)
- **Requires**: `GOOGLE_API_KEY`

**How They Work Together**:
1. Your XGBoost model generates a prediction (e.g., "Home wins with 62% probability")
2. System calculates edge vs. bookmaker odds
3. All 3 LLMs analyze the bet independently
4. System synthesizes consensus (Strong/Caution/Mixed)
5. User sees multi-AI perspective before placing bet

---

## 📡 DATA APIs USED

### FREE APIs (No Key Required)

#### 1. ESPN API ✅
- **Purpose**: Live scores, team data, game schedules
- **Cost**: FREE - No API key needed
- **Location**: `src/api/espn_client.py`
- **Data**:
  - Current scoreboard
  - Team rosters
  - Game summaries
  - Weekly schedules
- **Rate Limit**: Managed by token bucket

#### 2. NOAA Weather API ✅
- **Purpose**: Stadium weather forecasts
- **Cost**: FREE - No API key needed (government funded)
- **Location**: `src/api/noaa_client.py`
- **Data**:
  - 7-day forecasts
  - Wind speed/direction
  - Temperature
  - Precipitation
  - Weather alerts
- **Rate Limit**: Generous (government service)

#### 3. nflverse (nflfastR) ✅
- **Purpose**: Historical play-by-play data, advanced stats
- **Cost**: FREE - No API key needed
- **Source**: GitHub data repository
- **Data**:
  - Play-by-play (2016-present)
  - Player stats
  - Game schedules
  - Advanced analytics (EPA, WPA, etc.)

#### 4. Reddit API ✅
- **Purpose**: Public sentiment, injury news, insider info
- **Cost**: FREE - No API key needed
- **Source**: Public Reddit posts
- **Subreddits**: r/nfl, r/sportsbook, team subreddits

### PAID/KEY REQUIRED APIs

#### 5. The Odds API ⚠️
- **Purpose**: Live betting odds from 40+ sportsbooks
- **Cost**:
  - FREE tier: 500 requests/month
  - Paid: $99/month (unlimited)
- **Location**: `src/utils/odds_cache.py`
- **Data**:
  - Live spreads
  - Moneylines
  - Totals (over/under)
  - 40+ bookmakers
- **Requires**: `ODDS_API_KEY`
- **Signup**: https://the-odds-api.com/

---

## 💡 CAN YOU USE SUBSCRIPTION LOGINS INSTEAD OF APIs?

### SHORT ANSWER: **YES - With Caveats**

### DETAILED BREAKDOWN:

#### 1. **Sportsbook Data (DraftKings, FanDuel, etc.)**

**Option A: Web Scraping (Your Subscription Account)**
```python
✅ PROS:
- Use your existing DraftKings/FanDuel account
- No additional API costs
- Access ALL odds/lines you can see on the site
- Real-time data

⚠️ CONS:
- Violates most sportsbook Terms of Service
- Risk of account suspension/ban
- Requires Selenium/Playwright (browser automation)
- More fragile (breaks when site updates)
- Slower than APIs (1-2 seconds per page)
- Needs headless browser setup
```

**Implementation Path**:
```python
# Install browser automation
pip install selenium playwright

# Example scraper (DraftKings)
from selenium import webdriver
from selenium.webdriver.common.by import By

def scrape_draftkings_odds(game_url):
    driver = webdriver.Chrome()
    driver.get(game_url)

    # Extract odds from page
    spreads = driver.find_elements(By.CLASS_NAME, "sportsbook-outcome-cell")

    # Parse and return
    return parse_odds(spreads)
```

**Reality Check**:
- ⚠️ **Legal Risk**: Against TOS, could lose account
- ⚠️ **Ethical**: Gray area for personal use
- ⚠️ **Reliability**: Sites change HTML frequently
- ✅ **Cost**: Free if you have account

**Recommendation**: Use for **personal testing ONLY**. Don't automate high-frequency scraping.

---

#### 2. **ESPN/NFL.com Data**

**Option: Web Scraping (No Account Needed)**
```python
✅ CURRENT SOLUTION IS BETTER:
- ESPN has a FREE public API (no scraping needed)
- You're already using it: `src/api/espn_client.py`
- No login required
- Faster and more reliable than scraping

❌ DON'T SCRAPE:
- Unnecessary when API exists
- Slower
- More fragile
```

---

#### 3. **PFF (Pro Football Focus) Subscription**

**Scenario**: You pay $39.99/month for PFF Elite

**Option A: Manual Export**
```python
✅ ALLOWED:
- Download CSV exports from your account
- Use data for personal analysis
- Load CSVs into your system

❌ NOT ALLOWED:
- Automated scraping of subscriber content
- Sharing PFF data publicly
- Reselling insights
```

**Implementation**:
```python
# You manually download PFF grades to:
# data/pff/week12_grades.csv

import pandas as pd

df = pd.read_csv('data/pff/week12_grades.csv')
# Now use in your models as features
```

---

#### 4. **AI Models (GPT-4, Claude, Gemini)**

**Can You Use ChatGPT Subscription Instead of API?**

**Short Answer**: NO - Different products

```python
❌ CHATGPT PLUS ($20/month):
- Web interface only
- Can't programmatically call from Python
- No way to integrate with your betting system
- Can't analyze 100 games automatically

✅ OPENAI API (Pay-per-use):
- Direct Python integration
- Automated analysis
- ~$0.03 per game analysis
- Works in your system

💰 COST COMPARISON:
- ChatGPT Plus: $20/month (web UI only, can't automate)
- OpenAI API: ~$3-5/month if analyzing 100-150 games
  (YOU PAY LESS with API if using it programmatically!)
```

**Same Story for Claude**:
```python
❌ CLAUDE PRO ($20/month):
- Web interface only

✅ ANTHROPIC API:
- ~$0.015 per analysis
- Cheaper than subscription for automation
```

---

## 🎯 RECOMMENDED SETUP FOR COST OPTIMIZATION

### Tier 1: ZERO COST (Predictions Only)
```yaml
Required:
  - Train your own XGBoost models (FREE)
  - Use nflverse data (FREE)
  - Use ESPN API (FREE)
  - Use NOAA weather (FREE)

Skip:
  - The Odds API (use manual odds entry)
  - LLM reasoning swarm (optional)

Result:
  - Full predictions
  - No ongoing costs
  - Manual bet placement
```

### Tier 2: MINIMAL COST (Automated + AI Insights)
```yaml
Required:
  - Everything from Tier 1
  - The Odds API FREE tier (500 requests/month)
  - Google Gemini API (FREE tier)

Cost: $0/month

Result:
  - Automated odds fetching (limited)
  - AI bet analysis (Gemini only)
  - 500 games/month coverage
```

### Tier 3: FULL AUTOMATION (Recommended)
```yaml
Required:
  - Everything from Tier 2
  - OpenAI API ($5-10/month estimated)
  - Anthropic API ($3-5/month estimated)
  - The Odds API paid ($99/month) OR manual scraping

Cost: $8-15/month (without odds API)
      $107-115/month (with odds API)

Result:
  - Full 3-AI reasoning swarm
  - Unlimited predictions
  - Professional-grade analysis
```

---

## 🚨 WEB SCRAPING: LEGAL & ETHICAL CONSIDERATIONS

### Personal Use Scraping (DraftKings/FanDuel)

**Legal Gray Area**:
```
✅ PROBABLY OKAY:
- Scraping YOUR OWN account data
- For personal betting decisions only
- Low frequency (once per game, not every second)
- Not sharing scraped data
- Not competing with the sportsbook

⚠️ QUESTIONABLE:
- High-frequency automated scraping (100s of requests/minute)
- Using data to compete with the sportsbook
- Sharing odds publicly

❌ DEFINITELY ILLEGAL:
- Bypassing authentication/paywalls
- DDoS-level request volumes
- Reselling scraped odds data
- Creating competing odds service
```

**Terms of Service**:
Most sportsbooks prohibit:
- Automated access
- Data scraping/harvesting
- Bots/scripts

**Consequence**:
- Account suspension/ban
- Loss of deposited funds (depends on TOS)
- Legal action (rare for personal use)

### Safer Alternatives to Scraping

#### Option 1: Manual Odds Entry
```python
# Quick manual entry script
def enter_odds_manually():
    game = input("Game: ")
    spread = float(input("Spread: "))
    # Store in database
    db.store_odds(game, spread, ...)
```

#### Option 2: Use The Odds API FREE Tier
```python
# 500 requests/month = ~16 games/day for NFL season
# Enough for Sunday slate analysis
```

#### Option 3: Desktop Odds Tracker
```python
# Use your browser to view DraftKings
# Manually copy/paste odds into spreadsheet
# Import spreadsheet to system
```

---

## 📊 COST ANALYSIS: APIs vs Subscriptions

### Scenario: Analyze Every NFL Game (272 games/season)

| Method | Setup | Season Cost | Notes |
|--------|-------|-------------|-------|
| **Manual Everything** | XGBoost + nflverse | $0 | You enter odds by hand |
| **Free APIs Only** | Add ESPN + NOAA | $0 | Limited odds coverage |
| **The Odds API Free** | 500 requests/month | $0 | Covers most games |
| **The Odds API Paid** | Unlimited odds | $396/year | 4 months NFL = $396 |
| **LLM APIs** | GPT-4 + Claude + Gemini | $20-40/season | ~$0.05 per game |
| **Scraping** | Selenium + Your DK account | $0 | Risk of ban |
| **PFF Subscription** | Manual CSV export | $160/season | 4 months @ $40/mo |

**Best Value for Automation**:
```
XGBoost Models (FREE)
+ nflverse data (FREE)
+ ESPN/NOAA (FREE)
+ The Odds API free tier (FREE)
+ Gemini API (FREE)
= $0/month, 90% functionality
```

**Full Pro Setup**:
```
All of above
+ OpenAI API (~$10/season)
+ Anthropic API (~$5/season)
+ The Odds API paid ($396/season)
= ~$411 total for entire NFL season
  (Pays for itself with 2-3 winning bets)
```

---

## 🎬 FINAL RECOMMENDATIONS

### For You Specifically:

#### 1. **Keep Using ML Models** ✅
- Your XGBoost models are FREE
- No subscriptions/APIs needed for predictions
- Already integrated and working

#### 2. **Keep Using Free APIs** ✅
- ESPN: FREE forever
- NOAA: FREE forever
- nflverse: FREE forever
- These are better than scraping

#### 3. **For Betting Odds** - Choose One:

**Option A: The Odds API Free Tier** (RECOMMENDED)
- 500 requests/month = plenty for NFL
- Legal, reliable, fast
- No risk of account bans

**Option B: Manual Entry**
- Copy odds from DraftKings while browsing
- Enter into system manually
- 100% legal, zero cost

**Option C: Light Scraping** (USE AT YOUR RISK)
- Once per game, personal use only
- Risk: Possible DK account suspension
- Benefit: Fully automated

#### 4. **For AI Reasoning** - Choose One:

**Option A: Free (Gemini Only)**
- Use Google Gemini API (FREE tier)
- One AI perspective instead of three
- Good enough for most decisions

**Option B: Full Swarm ($15-20/season)**
- Add GPT-4 + Claude APIs
- Three AI perspectives
- Best insights, very cheap

---

## 🔑 API KEY SETUP (Current System)

Your system already supports these in `config/api_keys.env`:

```bash
# ML Models (no keys needed - local models)
# Trained models in models/*.pkl

# Data APIs
ODDS_API_KEY=your_key_here          # The Odds API
# ESPN_API_KEY not needed (free)
# NOAA_API_KEY not needed (free)

# AI Reasoning Swarm
OPENAI_API_KEY=sk-...               # GPT-4 reasoning
ANTHROPIC_API_KEY=sk-ant-...        # Claude reasoning
GOOGLE_API_KEY=...                  # Gemini reasoning (FREE tier)

# Optional
XAI_API_KEY=...                     # Grok (if using)
```

---

## 💬 QUESTIONS?

**Q: Can I use my ChatGPT Plus subscription for the AI reasoning swarm?**
A: No - ChatGPT Plus is web UI only. You need the OpenAI API for programmatic access. The API is actually cheaper (~$0.03/game vs $20/month for web UI you can't automate).

**Q: Is it illegal to scrape DraftKings if I have an account?**
A: Not illegal, but violates TOS. Risk is account suspension. Better to use The Odds API or manual entry.

**Q: Can I avoid all API costs?**
A: Yes! Use XGBoost models + nflverse + ESPN + manual odds entry = $0 total cost. You lose automation and AI insights.

**Q: Which AI is best for betting analysis?**
A: They're complementary. GPT-4 is strategic, Claude is risk-focused, Gemini is comprehensive. Using all 3 gives best consensus.

**Q: Do I need PFF subscription?**
A: No - nflverse has most advanced stats for free. PFF is nice-to-have, not required.

---

**Last Updated**: 2025-11-24
**Status**: All systems operational with free alternatives available
