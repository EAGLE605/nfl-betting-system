# Novel Edges - Future Ideas

**Date**: May 17, 2026  
**Status**: Research complete, not built yet

---

## 1. Referee Tracking

**What**: Different referee crews call games differently. Some call more penalties, some favor offense.

**Why it matters**: Crew assignments come out Tuesday. Betting lines don't adjust until Thursday. That's a 2-day window.

**Example**: 
- One crew's games go Under the point total 11 out of 16 times
- Another crew calls lots of pass interference = more points

**What we'd build**: Database of each crew's tendencies. Alert when a favorable matchup appears.

**Data**: Already available in nflverse.

---

## 2. Second-Year Running Backs

**What**: Running backs improve dramatically in their second NFL season.

**The numbers**:
- Running backs: +93% production Year 1 → Year 2
- Wide receivers: +19%
- Quarterbacks: -6% (they actually get worse)

**Why it matters**: Betting markets don't fully price this in. Target second-year RBs for player props.

**Data**: Already have it.

---

## 3. Follow the Big Money

**What**: Track where the professional bettors are putting money, not just how many people bet each side.

**How it works**: 
- If 70% of bets are on Team A, but 60% of the *money* is on Team B
- That means a few big bettors (pros) like Team B
- The line moves toward Team B despite fewer bets

**Why it matters**: Professionals win long-term. Following their money beats following the crowd.

**Data**: Need to add bet percentage tracking from odds providers.

---

## 4. Wind Alerts

**What**: Strong wind kills passing games and lowers scores.

**The numbers**:
- Wind over 15 mph = 20 fewer passing yards per team
- Rain = 12% less passing
- Heavy snow = 25% fewer points

**Why it matters**: Weather forecasts are free. If wind spikes before a game, the Under (fewer points) becomes valuable.

**Data**: Already connected to weather service.

---

## 5. Triage Agent (Your Idea)

**What**: An automated system that watches for roster changes and routes them appropriately.

**How it works**:

| Event | Priority | Action |
|-------|----------|--------|
| Starting QB injured/traded | Critical | Retrain model, alert you |
| Star player traded | Critical | Update team strength |
| Key injury (starter) | Medium | Adjust projections |
| Depth signing | Low | Log it, batch update weekly |
| Practice squad move | Low | Ignore |

**Why it matters**: Draft just happened. Trades happen. Injuries happen. The system should automatically know what matters and what doesn't.

**Data**: All available in nflverse (rosters, injuries, depth charts).

---

## 6. Social Media Mood (Lower Priority)

**What**: Measure fan confidence/anxiety before games via Twitter/Reddit.

**Why it might work**: Research shows crowd mood correlates with outcomes. When fans are overly confident, fade them.

**Why it's lower priority**: Requires Twitter API (costs money), natural language processing, and more validation.

---

## What We Already Have vs. What We Need

| Data | Have It? |
|------|----------|
| Player stats, team stats | Yes |
| Weather | Yes |
| Betting lines | Yes |
| Referee crews | Yes (need to build database) |
| Roster changes | Yes |
| Where pros bet | No (need odds provider upgrade) |
| Social sentiment | No (lower priority) |

---

## Things That Don't Work (Skip These)

| Myth | Reality |
|------|---------|
| West coast teams struggle traveling east | Used to be true, markets adjusted |
| Quarterbacks break out in Year 2 | Data says they get slightly worse |
| Team just made a big trade = instant improvement | Takes 3-4 weeks to integrate |

---

## Sources

- Carnegie Mellon research on Twitter + NFL
- Covers.com weather analysis
- NXTBets referee data
- nflverse (our main data source)
