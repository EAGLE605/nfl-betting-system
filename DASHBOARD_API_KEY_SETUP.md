# Dashboard API Key Setup Guide

**New Feature**: Configure all API keys directly from the dashboard!

---

## 🎯 Quick Start

### Step 1: Launch Dashboard
```bash
cd C:\Scripts\nfl-betting-system
streamlit run dashboard/app.py
```

### Step 2: Go to Settings
1. Click the **"⚙️ Settings"** tab (far right)
2. Click the **"🔑 API Keys"** sub-tab
3. You'll see all available API configurations

---

## 🔑 API Key Manager Features

### What You Get:

**Dashboard Interface**:
- ✅ Add/update/remove API keys visually
- ✅ Test keys to verify they work
- ✅ See which keys are configured
- ✅ Masked display for security (sk-...xyz)
- ✅ Help links for getting each API key
- ✅ Automatic validation (format checking)
- ✅ Cost information for each API

**Three Organized Tabs**:
1. **📊 Data APIs** - The Odds API (betting odds)
2. **🤖 AI Reasoning** - OpenAI, Anthropic, Google Gemini
3. **⚡ Optional** - xAI Grok and others

---

## 📋 Step-by-Step: Adding Your First API Key

### Example: Adding Google Gemini (FREE)

**Why start here**: Gemini is completely FREE and easiest to set up!

#### 1. Get Your Gemini API Key

In the dashboard Settings → API Keys tab:
- Find the "Google (Gemini)" section
- Click "ℹ️ How to get Google (Gemini) API key"
- Follow the link to: https://makersuite.google.com/app/apikey
- Sign in with your Google account
- Click "Create API key"
- Copy the key

#### 2. Add Key to Dashboard

Back in the dashboard:
- Paste your key in the "Enter Google (Gemini) API Key" field
- Click **"💾 Save"**
- You'll see: ✅ Google (Gemini) key saved!

#### 3. Test It (Optional)

- Click **"🧪 Test"** button
- Wait a few seconds
- You should see: ✅ Connected! API key is valid

**Done!** Your dashboard now has AI reasoning from Google Gemini.

---

## 🤖 Setting Up Full AI Reasoning Swarm

For the full 3-AI analysis (GPT-4 + Claude + Gemini):

### 1. Google Gemini (FREE) ✅
Already done above!

### 2. OpenAI (GPT-4) - $8/season

**Get Key**:
1. Go to https://platform.openai.com/api-keys
2. Sign up / Log in
3. Click "Create new secret key"
4. Copy key (starts with `sk-...`)

**Add to Dashboard**:
1. Settings → API Keys → AI Reasoning tab
2. Find "🟢 OpenAI (GPT-4)"
3. Paste key, click Save
4. Test to verify

**Cost**: ~$0.03 per game = ~$8 for full NFL season

### 3. Anthropic (Claude) - $5/season

**Get Key**:
1. Go to https://console.anthropic.com/
2. Sign up / Log in
3. API Keys section
4. Create new key (starts with `sk-ant-...`)

**Add to Dashboard**:
1. Settings → API Keys → AI Reasoning tab
2. Find "🟣 Anthropic (Claude)"
3. Paste key, click Save
4. Test to verify

**Cost**: ~$0.015 per game = ~$5 for full NFL season

**Total Cost**: ~$15/season for full 3-AI reasoning swarm!

---

## 📊 Setting Up Betting Odds (The Odds API)

### Why You Need This:
- Get live odds from 40+ sportsbooks
- Line shopping to find best value
- Historical line movement tracking

### Free Tier: 500 Requests/Month

**Get Key**:
1. Go to https://the-odds-api.com/
2. Sign up (email required)
3. Copy your API key from dashboard

**Add to Dashboard**:
1. Settings → API Keys → Data APIs tab
2. Find "📊 The Odds API"
3. Paste key, click Save
4. Test to verify

**Free Tier**: 500 requests/month
- ~16 games per day during NFL season
- Enough for Sunday slate analysis
- Covers most betting needs

**Paid Tier**: $99/month unlimited (optional)

---

## 🔄 Managing Your Keys

### View All Keys Status

Dashboard shows at the top:
```
Configured: 3/5
Required: 1/1
AI Providers: 2/3
```

### Test All Keys at Once

1. Scroll to bottom of API Keys tab
2. Click **"🧪 Test All Keys"**
3. See status for each:
   - ✅ OpenAI (GPT-4): Connected! Found 50 models
   - ✅ Anthropic (Claude): Connected! API key is valid
   - ❌ The Odds API: Invalid API key

### Remove a Key

1. Find the API in the list
2. Click **"🗑️ Remove"** button
3. Confirm - key will be deleted

### Update a Key

1. Enter new key in the input field
2. Click **"💾 Save"**
3. Old key is replaced

---

## 🔒 Security Features

### Your Keys are Safe

**Masked Display**:
- Keys shown as `sk-...xyz` (first 7 + last 4 chars)
- Full key never displayed after saving

**Password Input**:
- Key entry fields use `type="password"`
- Hidden as you type

**Local Storage**:
- Keys saved in `config/api_keys.env`
- File stays on your computer
- Never uploaded anywhere

**Environment Variables**:
- Keys loaded as environment variables
- Accessible only to your Python code
- Standard secure practice

### .env File Location

Your keys are stored here:
```
C:\Scripts\nfl-betting-system\config\api_keys.env
```

**Backup this file!** If you lose it, you'll need to re-enter all keys.

---

## ❓ Troubleshooting

### "Failed to save key"

**Causes**:
- File permission issues
- Invalid file path

**Fix**:
1. Check `config/api_keys.env` exists
2. Ensure you have write permissions
3. Try running dashboard as administrator

### "❌ Invalid API key" when testing

**Causes**:
- Wrong key format
- Key expired/revoked
- Insufficient permissions

**Fix**:
1. Re-copy key from provider (no extra spaces)
2. Check key hasn't expired
3. Verify key has correct permissions

### "⚠️ Required library not installed"

**Cause**: Missing Python package for that API

**Fix**:
```bash
# For OpenAI
pip install openai

# For Anthropic
pip install anthropic

# For Google
pip install google-generativeai

# Or install all
pip install -r requirements.txt
```

### API key format warnings

The manager validates key formats:

**OpenAI**: Must start with `sk-`
**Anthropic**: Must start with `sk-ant-`
**Others**: Length check (minimum 20 characters)

If you get a format warning but key is correct, you can still save it.

---

## 🎓 Which APIs Do I Actually Need?

### Minimum Setup (FREE)

**Just Predictions**:
- ✅ Your trained XGBoost models (FREE)
- ✅ ESPN API (FREE, auto-configured)
- ✅ NOAA Weather (FREE, auto-configured)
- ❌ No paid APIs needed

**Result**: Full game predictions with 67%+ win rate

### Budget Setup ($0/month)

Add:
- ✅ Google Gemini API (FREE)
- ✅ The Odds API free tier (FREE, 500 requests)

**Result**: AI bet analysis + automated odds

### Recommended Setup ($1.25/month)

Add:
- ✅ OpenAI API (~$0.75/month during season)
- ✅ Anthropic API (~$0.50/month during season)

**Result**: Full 3-AI reasoning swarm with consensus

### Pro Setup ($26/month during season)

Add:
- ✅ The Odds API paid ($99/month, but only 4 months)

**Result**: Unlimited odds, full automation

**Note**: NFL season = ~4 months (Sep-Dec)
- $99/month × 4 = $396/year for odds
- But most can use free tier!

---

## 🔗 Quick Links

**Get API Keys**:
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/
- Google Gemini: https://makersuite.google.com/app/apikey
- The Odds API: https://the-odds-api.com/

**Documentation**:
- See `AI_MODELS_AND_API_GUIDE.md` for full API details
- See `API_COMPLETE_GUIDE.md` for technical integration

**Help**:
- Dashboard has built-in help for each API
- Click "ℹ️ How to get..." expanders
- Includes signup links and cost info

---

## 💡 Pro Tips

### Start with Free Options

1. Use Google Gemini (FREE) for AI analysis
2. Use The Odds API free tier (500/month)
3. Upgrade to paid AIs only if you want full 3-AI consensus

### Test Before Betting

Always click **"🧪 Test"** after adding a new key to verify it works!

### Backup Your Keys

Copy `config/api_keys.env` to a safe location in case you need to reinstall.

### Monitor Usage

Some APIs have usage limits:
- Gemini: 15 requests/minute (FREE tier)
- The Odds API: 500 requests/month (FREE tier)

Dashboard doesn't track usage yet, so check provider dashboards.

### Reload After Changes

If you manually edit `config/api_keys.env`:
1. Go to Settings → API Keys
2. Click **"🔄 Reload Keys"**
3. Changes will be picked up

---

## 🎉 You're All Set!

Once your keys are configured:

1. **Picks Tab**: See AI-analyzed bet recommendations
2. **Click any bet**: Get 3-AI reasoning swarm analysis
3. **Performance Tab**: Track ROI and win rate
4. **Bankroll Tab**: Manage Kelly Criterion bet sizing

**No more command-line configuration needed!**

Just add your keys in the dashboard and you're ready to find +EV bets!

---

**Last Updated**: 2025-11-24
**Dashboard Version**: 1.0 with API Key Manager
