# Professional Sports Betting Operations: Task List

Based on documented practices from professional bettors and syndicates including Haralabos Voulgaris, Billy Walters, Spanky (Gadoon Kyrollos), Pinnacle's market-making operations, and peer-reviewed research.

---

## Phase 1: Statistical Validation (Before Any Real Money)

**Source**: [Sports Insights Statistical Significance](https://www.sportsinsights.com/sports-investing-statistical-significance/), [Punter2Pro Sample Size](https://punter2pro.com/sample-size-betting-results-analysis/)

### 1.1 Sample Size Requirements
- [ ] Accumulate minimum **300 bets** per market type for initial validation
- [ ] Target **2,000+ bets** for 95% confidence at 57% win rate
- [ ] At 200-game sample, require **60%+ win rate** to claim significance

### 1.2 Out-of-Sample Testing
- [ ] Reserve **one full season untouched** as final holdout (never train on it)
- [ ] Run walk-forward backtest across **minimum 3 seasons**
- [ ] Validate with AUC, Brier score, and calibration plots
- [ ] Require p < 0.05 significance before proceeding

### 1.3 CLV Tracking Setup
**Source**: [VSiN CLV Importance](https://vsin.com/how-to-bet/the-importance-of-closing-line-value/), [Pikkit CLV Tracker](https://pikkit.com/closing-line-value)

- [ ] Build system to record **bet odds at time of placement**
- [ ] Build system to record **closing line** (final odds before game start)
- [ ] Calculate CLV for every bet: `(bet_odds / closing_odds) - 1`
- [ ] Target: **+2% average CLV** minimum for profitability
- [ ] Track: % of bets with positive CLV (target: >50%)

---

## Phase 2: Infrastructure Setup

**Source**: [Betting Syndicate Operations](https://www.underdogchance.com/betting-syndicate-operations/)

### 2.1 Data Pipeline (Real-Time)
- [ ] Odds API integration with **<15 second latency**
- [ ] Multiple bookmaker coverage (minimum 5-10 books)
- [ ] Historical odds database for CLV calculation
- [ ] Automated injury/news monitoring

### 2.2 Sportsbook Account Network
**Source**: [BoydsBets Professional Lifestyle](https://www.boydsbets.com/professional-sports-bettor-lifestyle/)

- [ ] Open accounts at **minimum 5-10 sportsbooks**
- [ ] Include sharp-friendly books: Pinnacle, Bookmaker, BetCRIS
- [ ] Include soft books for line shopping
- [ ] Document: limits per book, account status, betting history

### 2.3 Line Shopping System
**Source**: Universal practice among pros per [GamblingSite Daily Habits](https://www.gamblingsite.com/blog/mind-of-professional-sports-bettor-daily/)

- [ ] Real-time odds comparison across all accounts
- [ ] Alert system when line diverges from model by X%
- [ ] Track: which books have best odds by market type
- [ ] "-110 instead of -115 can be difference between profit and loss"

---

## Phase 3: Bankroll Management

**Source**: [Sports Insights Bankroll Management](https://www.sportsinsights.com/how-to-bet-on-sports/bankroll-management/betting-unit-size/), [OddsJam Bankroll](https://oddsjam.com/betting-education/bankroll-management)

### 3.1 Bankroll Sizing
- [ ] Define bankroll: **50-100 units minimum**
- [ ] Money you can afford to lose completely
- [ ] Example: $100/unit = $5,000-$10,000 bankroll

### 3.2 Bet Sizing Rules
- [ ] Standard bet: **1-3% of bankroll** (pros typically use 1%)
- [ ] Maximum single bet: **never exceed 5%**
- [ ] Use fractional Kelly: **25-50% of calculated Kelly**
- [ ] Daily loss limit: **5-10% of bankroll**

### 3.3 Position Tracking
- [ ] Log every bet: odds, size, model probability, result
- [ ] Track bankroll daily
- [ ] Review unit size when bankroll changes **25-50%**
- [ ] Monte Carlo simulation for ruin probability

---

## Phase 4: Daily Operations

**Source**: [GamblingSite Professional Bettor Daily Habits](https://www.gamblingsite.com/blog/mind-of-professional-sports-bettor-daily/)

### 4.1 Morning Routine (Before Market Opens)
Billy Walters starts "before sunrise" to catch overnight lines.

- [ ] Check overnight line movements
- [ ] Review injury reports published overnight
- [ ] Run model on today's games
- [ ] Identify games where model diverges from market by >2%
- [ ] Check account balances across books

### 4.2 Line Monitoring (Continuous)
Syndicates spend "70+ hours/week analyzing betting market and watching for line movements."

- [ ] Monitor line movements in real-time
- [ ] Alert when sharp books (Pinnacle/CRIS) move
- [ ] Alert when model-to-market edge appears
- [ ] Calculate: "what the move is worth"

### 4.3 Bet Execution
- [ ] Shop for best available line across all books
- [ ] Execute within seconds when value identified
- [ ] Record: time placed, odds obtained, book used
- [ ] Track: closing line for CLV calculation post-game

### 4.4 Post-Game
- [ ] Record closing lines for all bets
- [ ] Calculate actual CLV
- [ ] Update model with new data
- [ ] Review wins/losses for patterns

---

## Phase 5: Performance Measurement

**Source**: [Bet-Analytix Closing Odds](https://www.bet-analytix.com/academy/closing-odds-ultimate-indicator)

### 5.1 Primary Metrics (Weekly Review)
- [ ] **CLV Average** - "Consistent +2% or more typically correlates with profitability"
- [ ] **CLV Hit Rate** - % of bets beating closing line
- [ ] ROI by market type
- [ ] Win rate vs expected win rate

### 5.2 Secondary Metrics
- [ ] Sharpe ratio (risk-adjusted returns)
- [ ] Maximum drawdown
- [ ] Variance vs expected variance
- [ ] Performance by: day of week, time of day, market type

### 5.3 Model Calibration Check (Monthly)
- [ ] ECE/MCE calculation on recent bets
- [ ] Calibration curve analysis
- [ ] Compare predicted vs actual win rates by probability bucket
- [ ] Retrain model if calibration degrades

---

## Phase 6: Risk Management

**Source**: [Betting Syndicate Operations](https://www.underdogchance.com/betting-syndicate-operations/)

### 6.1 Exposure Limits
- [ ] Maximum exposure per game: X% of bankroll
- [ ] Maximum exposure per day: X% of bankroll
- [ ] Maximum correlated exposure (same team, division, etc.)
- [ ] No more than X% on any single outcome

### 6.2 Account Management
- [ ] Monitor for limits/restrictions at each book
- [ ] Rotate betting patterns to avoid detection
- [ ] Track: which accounts are limited
- [ ] Maintain relationships with sharp-friendly books

### 6.3 Variance Management
- [ ] Understand: even with 5% edge, losing streaks happen
- [ ] Monte Carlo: probability of X% drawdown
- [ ] Stress test: "what if wrong about edge?"
- [ ] Mindfulness practices (per Voulgaris) for emotional control

---

## Phase 7: Continuous Improvement

**Source**: [The Craft of Sports Betting Professionals](https://thepowerrank.com/the-craft-of-sports-betting-professionals-2/)

### 7.1 Model Updates
Voulgaris: "Around 2004 the sports books caught on to his strategies"

- [ ] Weekly: incorporate new game data
- [ ] Monthly: re-evaluate feature importance
- [ ] Quarterly: test new features/data sources
- [ ] Annually: major model overhaul if needed

### 7.2 Edge Decay Monitoring
- [ ] Track CLV trend over time (is edge shrinking?)
- [ ] Monitor: are books limiting you faster?
- [ ] Test: do edges still exist in new seasons?
- [ ] Research: what are competitors doing?

### 7.3 New Market Research
- [ ] Evaluate new bet types (player props, live betting)
- [ ] Test edges in lower-liquidity markets
- [ ] Document: time investment vs edge size

---

## Syndicate-Specific Tasks (If Operating as Group)

**Source**: [Betting Syndicate Operations](https://www.underdogchance.com/betting-syndicate-operations/), [FasterCapital Syndicate Secrets](https://fastercapital.com/content/Betting-Syndicate-Member--Syndicate-Secrets--An-Insider-s-Guide-to-Betting-Syndicates.html)

### Role Assignment
- [ ] **Data Analysts**: statistics, model development, trend identification
- [ ] **Tipsters**: domain expertise, specific sport knowledge
- [ ] **Bankroll Managers**: finances, bet sizing, risk management
- [ ] **Runners/Beards**: account access, bet placement

### Coordination
- [ ] Betting queue system for rapid execution
- [ ] Communication protocol when line moves
- [ ] Shared tracking system for all bets
- [ ] Weekly performance review meetings

---

## Current System Status vs Professional Requirements

| Requirement | Professional Standard | Your System | Gap |
|-------------|----------------------|-------------|-----|
| CLV Tracking | Every bet | ✅ Implemented | - |
| Real-Time Odds | <15 sec latency | ❌ No API | **CRITICAL** |
| Closing Line Data | Automated capture | ❌ Missing | **CRITICAL** |
| Sample Size | 2,000+ bets validated | ❓ Unknown | Validate |
| Multiple Books | 5-10 accounts | ❓ Unknown | Setup |
| Line Shopping | Real-time comparison | ❌ Missing | HIGH |
| Bankroll Rules | 1% standard bet | ✅ Kelly implemented | - |
| ECE Monitoring | Monthly check | ✅ Implemented | - |
| Walk-Forward Test | 3+ seasons | ✅ Implemented | - |

---

## Immediate Next Actions (Priority Order)

Based on professional practices, before placing any real money:

1. **Get Odds API Access** - Cannot measure true edge without closing lines
   - The Odds API: $79-199/month
   - Required for: CLV calculation, line shopping

2. **Validate Sample Size** - Run model on 3+ historical seasons
   - Calculate CLV on historical data
   - Require: positive CLV at p < 0.05

3. **Open Multiple Sportsbook Accounts**
   - Sharp-friendly: Pinnacle, Bookmaker
   - Soft books: DraftKings, FanDuel, etc.
   
4. **Paper Trade** - Track bets without real money
   - Minimum 100-300 bets
   - Verify positive CLV in live conditions

5. **Start Small** - 0.5% of bankroll per bet initially
   - Increase only after 200+ bets with positive CLV

---

## Sources

- [VSiN - Importance of Closing Line Value](https://vsin.com/how-to-bet/the-importance-of-closing-line-value/)
- [Sports Insights - Statistical Significance](https://www.sportsinsights.com/sports-investing-statistical-significance/)
- [GamblingSite - Mind of Professional Sports Bettor Daily](https://www.gamblingsite.com/blog/mind-of-professional-sports-bettor-daily/)
- [BoydsBets - Professional Sports Bettor Lifestyle](https://www.boydsbets.com/professional-sports-bettor-lifestyle/)
- [The Power Rank - Craft of Sports Betting Professionals](https://thepowerrank.com/the-craft-of-sports-betting-professionals-2/)
- [Sports Insights - Bankroll Management](https://www.sportsinsights.com/how-to-bet-on-sports/bankroll-management/betting-unit-size/)
- [Underdogchance - Betting Syndicate Operations](https://www.underdogchance.com/betting-syndicate-operations/)
- [Bet-Analytix - Closing Odds Ultimate Indicator](https://www.bet-analytix.com/academy/closing-odds-ultimate-indicator)
- [Punter2Pro - Sample Size in Betting Analysis](https://punter2pro.com/sample-size-betting-results-analysis/)
- [Pinnacle Odds Dropper - Sharp Money](https://www.pinnacleoddsdropper.com/blog/sharp-money)
