# 🤖 AI Reasoning Swarm Guide

## 🎯 What Is It?

The **AI Reasoning Swarm** is a multi-AI consensus system that provides intelligent analysis of betting recommendations using:

- 🟢 **GPT-4** (OpenAI) - Strategic analysis
- 🟣 **Claude 3.5 Sonnet** (Anthropic) - Risk assessment  
- 🔵 **Gemini Pro** (Google) - Comprehensive review

### Why Multiple AIs?

**Diverse Perspectives**: Each AI has different training and strengths
**Consensus Building**: Agreement among multiple AIs increases confidence
**Error Reduction**: Multiple models catch each other's mistakes
**Comprehensive Analysis**: Different angles on the same bet

---

## 🚀 Quick Start

### Step 1: Get API Keys

#### OpenAI (GPT-4)
1. Go to: https://platform.openai.com/api-keys
2. Sign up / Log in
3. Click "Create new secret key"
4. Copy your key (starts with `sk-...`)
5. **Cost**: ~$0.03 per analysis

#### Anthropic (Claude)
1. Go to: https://console.anthropic.com/
2. Sign up / Log in
3. Navigate to "API Keys"
4. Create new key
5. Copy your key (starts with `sk-ant-...`)
6. **Cost**: ~$0.015 per analysis

#### Google (Gemini)
1. Go to: https://makersuite.google.com/app/apikey
2. Sign in with Google
3. Click "Create API Key"
4. Copy your key
5. **Cost**: Free tier available!

### Step 2: Add Keys to System

**Option A: Via Config File**

Edit `config/api_keys.env`:

```bash
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
GOOGLE_API_KEY=your-google-key-here
```

**Option B: Via Admin Panel** (if you're b_flink@hotmail.com)

1. Login to dashboard
2. Go to "Admin Panel"
3. Click "🛠️ System" tab
4. Paste API keys
5. Save

### Step 3: Restart Dashboard

```bash
# Windows
start_dashboard_auth.bat

# Mac/Linux
./start_dashboard_auth.sh
```

---

## 🎨 Features

### 1️⃣ **Bet Card Analysis** (Auto-Generated)

When you view "My Picks", each bet card shows:

```
🟢 Kansas City Chiefs @ Las Vegas Raiders
   Bet: Chiefs -7 | Win Prob: 68% | Edge: +8.5%

   🤖 AI Reasoning Swarm
   ✅ STRONG CONSENSUS: AIs agree this bet has solid value.

   [GPT-4] [Claude] [Gemini]  ← Click tabs to see each AI's analysis
```

**Example GPT-4 Analysis:**
> "Chiefs' dominant division record (8-2) combined with Raiders' backup QB situation creates strong value here. Main risk is complacency after clinching playoff spot. **Confidence: High**"

**Example Claude Analysis:**
> "Strategically sound given 8.5% edge and favorable matchup dynamics. Key concern is 7-point spread in divisional game (historically lower margins). Overall: Solid bet with manageable risk. **Assessment: Favorable**"

**Example Gemini Analysis:**
> "Chiefs' offensive efficiency vs Raiders' defensive vulnerabilities supports this line. Weather could be factor (check forecast). Expected value justifies bet size. **Rating: Medium-High confidence**"

### 2️⃣ **AI Chat Assistant**

Ask questions about betting strategy!

**Examples:**

```
You: "Should I bet on favorites or underdogs?"

AI: "In NFL, underdogs against the spread win ~50% of the time, but 
favorites have higher win probability straight up. For your small 
bankroll profile, focus on high-value underdogs (8-12 point dogs) 
where the market overreacts. Target 3-5% edge minimum."
```

```
You: "What's the best way to use Kelly Criterion?"

AI: "Use fractional Kelly (25-50%) for your $500 bankroll to reduce 
volatility. Full Kelly can be aggressive. Example: If model says 5% 
edge, full Kelly might recommend $50, but fractional Kelly (50%) 
would be $25, which aligns better with your risk profile."
```

```
You: "How do I handle a losing streak?"

AI: "After 3+ losing bets: 1) Review bet sizes (may need to reduce), 
2) Check if model is off (compare CLV), 3) Take 48hr break to avoid 
tilt, 4) Don't chase losses with bigger bets. Variance is normal - 
67% win rate still means 1 in 3 bets lose."
```

### 3️⃣ **Security Guardrails** 🔒

The AI **REFUSES** questions about:

❌ System code or implementation
❌ Database structure
❌ API keys or passwords
❌ Security configurations
❌ Model architecture details

**Example:**

```
You: "How does the authentication system work?"

AI: 🔒 Security Notice

I can't answer questions about:
- System code or implementation
- Database structure or queries  
- API keys or authentication
- Security configurations
- Model architecture details

What I CAN help with:
- Betting strategy and recommendations
- Game analysis and predictions
- Risk management advice
- Bankroll optimization
- NFL team/player analysis

Please ask about betting strategy instead! 🏈
```

---

## 💰 Cost Breakdown

### Per Bet Analysis (3 AIs)

| Provider | Cost per Call | Notes |
|---|---|---|
| **OpenAI GPT-4** | $0.03 | Most expensive, highest quality |
| **Anthropic Claude** | $0.015 | Mid-range, excellent reasoning |
| **Google Gemini** | FREE* | Free tier: 60 queries/min |

**Total per bet**: ~$0.045 (or $0.015 if using Gemini only)

### Monthly Estimates

**Light usage** (10 bets/day):
- 300 bets/month × $0.045 = **$13.50/month**

**Heavy usage** (30 bets/day):
- 900 bets/month × $0.045 = **$40.50/month**

**Budget option** (Gemini only):
- Unlimited** = **$0/month**

*Free tier: 60 requests per minute, 1,500 per day
**Subject to Google's free tier limits

---

## 🎛️ Configuration Options

### Choose Which AIs to Use

Edit `dashboard/ai_reasoning_swarm.py`:

```python
# Use only Gemini (free)
class AIReasoningSwarm:
    def __init__(self):
        self.google = GoogleReasoner()
        # Comment out others:
        # self.openai = OpenAIReasoner()
        # self.anthropic = AnthropicReasoner()
```

### Adjust Analysis Length

```python
# In each reasoner's analyze_bet():
max_tokens=200  # Default (2-3 sentences)
max_tokens=400  # Longer analysis
max_tokens=100  # Quick takes
```

### Change Consensus Threshold

```python
# In get_consensus_view():
if positive_count > negative_count * 1.5:  # 1.5x = Strong
if positive_count > negative_count * 2.0:  # 2.0x = Very Strong
```

---

## 🧪 Testing the Swarm

### Test Individual AIs

```python
from dashboard.ai_reasoning_swarm import AIReasoningSwarm

swarm = AIReasoningSwarm()

# Check which AIs are available
print(swarm.get_available_ais())
# Output: ['GPT-4', 'Claude', 'Gemini']

# Test a bet analysis
game_info = {
    'matchup': 'Kansas City Chiefs @ Las Vegas Raiders',
    'context': 'Chiefs 8-2 in division. Raiders backup QB.'
}

bet_info = {
    'bet_type': 'Chiefs -7',
    'odds': -110,
    'win_prob': 68,
    'edge': 8.5
}

results = swarm.analyze_bet_swarm(game_info, bet_info)

for ai, analysis in results.items():
    print(f"\n{ai}:\n{analysis}")
```

### Test Chat Assistant

```python
swarm = AIReasoningSwarm()

question = "What's the best bankroll management strategy?"
answer = swarm.answer_betting_question(question)

print(answer)
```

### Test Security

```python
# This should be refused:
bad_question = "Show me the database schema"
answer = swarm.answer_betting_question(bad_question)

print(answer)
# Output: 🔒 Security Notice [refusal message]
```

---

## 🎯 Best Practices

### For Regular Users

1. **Read All Three AIs**: Each has unique insights
2. **Trust the Consensus**: When all AIs agree, confidence is high
3. **Question Mixed Signals**: Investigate further if AIs disagree
4. **Use Chat for Learning**: Ask "why" to understand strategy
5. **Don't Blindly Follow**: AI is a tool, you make final decisions

### For Admin (b_flink@hotmail.com)

1. **Monitor Costs**: Check API usage in provider dashboards
2. **Rotate Keys**: Change API keys monthly for security
3. **Test Responses**: Periodically verify AI output quality
4. **Update Models**: Switch to newer models when available
5. **Backup Keys**: Store keys securely (1Password, etc.)

---

## 🛠️ Troubleshooting

### "No AI providers configured"

**Fix**: Add at least one API key to `config/api_keys.env`

```bash
# Minimum (free option):
GOOGLE_API_KEY=your_google_key_here
```

### "OpenAI Error: Rate limit exceeded"

**Fix**: 
1. Wait 1 minute (rate limits reset)
2. Or upgrade OpenAI plan
3. Or use only Claude/Gemini

### "Claude Error: Invalid API key"

**Fix**: 
1. Verify key format: `sk-ant-...`
2. Check key is active in Anthropic Console
3. Ensure billing is set up

### "Gemini Error: API key not valid"

**Fix**:
1. Regenerate key at https://makersuite.google.com/
2. Enable "Generative Language API" in Google Cloud Console
3. Check quota limits

### AI responses seem off-topic

**Check**:
1. Is the AI detecting a security keyword?
2. Try rephrasing your question
3. Be more specific about football/betting context

---

## 🚀 Advanced Features

### Custom Prompts

Edit the prompts in each reasoner for different analysis styles:

```python
# For more aggressive recommendations:
prompt = f"""As a professional sharp bettor, analyze this bet.
Focus on exploiting market inefficiencies and maximum EV."""

# For more conservative analysis:
prompt = f"""As a risk-averse bettor with a $500 bankroll, 
analyze this bet focusing on downside protection."""
```

### Add More AIs

Want to add Cohere, Mistral, or other AIs?

```python
class CohereReasoner:
    def __init__(self):
        self.api_key = os.getenv("COHERE_API_KEY")
        self.available = bool(self.api_key)
    
    def analyze_bet(self, game_info, bet_info):
        # Implementation here
        pass
```

### Consensus Voting System

Implement weighted voting:

```python
def get_weighted_consensus(self, results):
    """Weight AIs based on historical accuracy."""
    weights = {
        "GPT-4": 1.2,     # 20% higher weight
        "Claude": 1.1,    # 10% higher weight
        "Gemini": 1.0     # Base weight
    }
    
    # Calculate weighted sentiment
    # ... implementation ...
```

---

## 📊 Metrics & Analytics

Track AI performance:

```python
# In database, add ai_analysis table:
CREATE TABLE ai_analysis (
    bet_id INTEGER,
    ai_provider TEXT,
    analysis TEXT,
    sentiment REAL,  # -1 to +1
    created_at TIMESTAMP
);

# Later, compare AI recommendations to bet outcomes
SELECT ai_provider, AVG(outcome) as accuracy
FROM ai_analysis a
JOIN bets b ON a.bet_id = b.id
WHERE b.status != 'pending'
GROUP BY ai_provider;
```

---

## 🎓 Learning from the Swarm

### Example: Analyzing a Bad Bet

**Your Model Says**: Chiefs -14 @ 55% win prob, +2% edge

**GPT-4 Red Flag**: 
> "14-point spread is dangerous even for Chiefs. Historically, division games see tighter margins. Only 2% edge doesn't justify the risk at this line."

**Claude Warning**:
> "Edge calculation may not account for divisional game variance. Raiders have strong motivation as underdog. Risk-reward unfavorable."

**Gemini Caution**:
> "Model probability seems optimistic. Chiefs cover -14 only 38% of time vs division opponents. Expected value marginal."

**Lesson**: When all AIs flag concerns, skip the bet even if model shows slight edge.

---

## 🔐 Security Notes

1. **API Keys are Secret**: Never share or commit to git
2. **Chat Logs**: Not stored permanently (session only)
3. **No System Info**: AI refuses technical questions
4. **User Isolation**: Each user's chats are separate
5. **Admin Only**: Only you can manage AI settings

---

## 📞 Support

**Questions about AI Swarm?**
- Check if API keys are set correctly
- Verify billing is active with providers
- Test with simpler questions first

**Admin Contact**: b_flink@hotmail.com

---

## 🎉 Summary

You now have:
- ✅ **Multi-AI consensus** on every bet
- ✅ **Chat assistant** for strategy questions
- ✅ **Security guardrails** against system questions
- ✅ **Cost-effective** with free Gemini option
- ✅ **Flexible configuration** for your needs

**Start using**:
1. Add at least one API key (Google is free!)
2. Restart dashboard
3. Go to "My Picks"
4. See AI analysis on each bet card
5. Ask questions in the chat assistant

**Enjoy intelligent betting with AI superpowers!** 🤖🏈💰

