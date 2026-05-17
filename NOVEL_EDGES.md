# Novel Edges - Research Findings

**Date**: May 17, 2026  
**Status**: Ideas for future implementation  
**Source**: Deep research via web search + nflverse analysis

---

## Priority 1: Referee Tendencies

**Signal**: Crew assignments announced Tuesday, lines often don't adjust until Thursday.

| Example | Finding |
|---------|---------|
| Alex Kemp | Under hits 11/16; favorites 30-3 SU |
| Shawn Smith | 23 DPI calls in 2025 - favors passing |
| DPI-heavy crews | Hurt RB props |

**Data**: `nfl.import_officials([2026])` - already available  
**Build**: Create crew tendency database, alert on favorable matchups

---

## Priority 2: Year-2 RB Props

**Signal**: Rookie RBs show +93% fantasy point jump in Year 2.

| Position | Y1 to Y2 Change |
|----------|-----------------|
| **RB** | **+93%** |
| WR | +19% |
| QB | -6% |

**Data**: nflverse (have it)  
**Action**: Target Year-2 RB over props, avoid "QB breakout" narratives

---

## Priority 3: Sharp Money Detection (RLM)

**Signal**: When 30% of bets get 60% of money = Reverse Line Movement (sharp action).

**Implementation**:
- Track bet% vs money% discrepancy
- Alert when RLM detected
- Best window: Sunday mornings before NFL

**Data**: Requires Odds API with bet/money splits (Action Network, VegasInsider)

---

## Priority 4: Wind Threshold Alerts

**Signal**: Wind 15+ mph = -20 passing yards per team.

| Condition | Impact |
|-----------|--------|
| Wind 15+ mph | -20 pass yards/team |
| Rain | -12% passing production |
| Snow | FG conversion drops to 76% |
| Heavy snow | -25% points scored |

**Data**: NOAA (already integrated)  
**Build**: Alert on totals when wind forecast exceeds 15 mph

---

## Priority 5: Triage Agent

**Concept**: Route roster changes to appropriate actions based on priority.

```
TRANSACTION_PRIORITY = {
    # CRITICAL - Retrain model
    'qb_starter_change': 10,
    'trade_deadline_star': 9,
    'top_50_pick_signs': 8,
    
    # MEDIUM - Update projections  
    'pro_bowl_injury': 7,
    'fa_signing': 6,
    'depth_chart_change': 5,
    
    # LOW - Log only
    'practice_squad': 3,
    'ir_move': 4,
}
```

**Data Sources** (all available via nflverse):
```python
nfl.import_draft_picks([2026])
nfl.import_weekly_rosters([2026])
nfl.import_injuries([2026])
nfl.import_depth_charts([2026])
```

**Routing**:
- CRITICAL (8-10): Retrain model, alert user
- MEDIUM (5-7): Update team projections
- LOW (1-4): Log for weekly batch

---

## Priority 6: Social Sentiment

**Signal**: Aggregate fan "pre-match anxiety" correlates with outcomes (CMU research).

**Implementation**:
- Twitter/Reddit sentiment aggregation
- Weight by follower count / karma
- Contrarian signal when public heavily favors one side

**Data**: Twitter API, Reddit API  
**Effort**: High (API costs, NLP pipeline)

---

## Additional Validated Edges

### Injury Report Timing
- Friday reports most predictive
- Game-day 90-minute window creates final edge
- "Questionable" designation = volatility opportunity

### Trade Integration Period
- Fade teams first 1-2 games post-trade
- Back them after week 4 (scheme integration complete)

### Home Field Advantage Decline
- Dropped from 57-60% (pre-2019) to 52-53%
- Market adjustment: 3 points → 1.5 points
- Surface mismatches (turf vs grass) still create edges

---

## Data Sources Summary

| Source | Already Have | Need to Add |
|--------|--------------|-------------|
| nflverse (EPA, rosters, officials) | Yes | - |
| NOAA weather | Yes | - |
| Odds API (lines) | Yes | Bet%/money% splits |
| ESPN transactions | Partial | Real-time feed |
| Referee database | No | Build from officials data |
| Twitter sentiment | No | API + NLP |

---

## Not Validated (Avoid)

| Myth | Reality |
|------|---------|
| West Coast travel disadvantage | Market has adjusted |
| QB "breakout" Year 2 | Actually -6% |
| General coaching changes | Too noisy without specifics |

---

## Sources

- CMU Research: Twitter sentiment for NFL (arxiv.org/abs/1310.6998)
- Covers: Weather effects, home field decline
- NXTBets: Referee betting trends
- OddsShopper: Reverse line movement
- nflverse: Draft picks, rosters, officials
- Fantasy Points: Year-2 leap analysis
