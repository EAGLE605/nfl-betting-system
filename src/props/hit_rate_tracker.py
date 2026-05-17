"""Hit Rate Tracker - Filter for 51%+ Historical Edges

Key insight from research: Filter props with 51%+ hit rate in
comparable situations (recent form, home/away, opponent defense rank).

This module:
1. Tracks historical hit rates by player/prop/situation
2. Filters for statistically significant edges
3. Identifies "100% last 5 games" type trends
4. Distinguishes sustainable edges from regression candidates

Warning: "100% last 5" trends often regress. Use larger samples.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class HitRateRecord:
    """Historical hit rate for a prop type."""
    player: str
    prop_type: str
    line: float
    direction: str  # over/under

    # Sample sizes
    last_5_games: Tuple[int, int]  # (hits, total)
    last_10_games: Tuple[int, int]
    season_total: Tuple[int, int]

    # Situational splits
    home_rate: Optional[float]
    away_rate: Optional[float]
    vs_good_def_rate: Optional[float]  # vs top 10 defense
    vs_bad_def_rate: Optional[float]   # vs bottom 10 defense

    # Trend info
    streak: int  # Consecutive hits (positive) or misses (negative)
    trend: str   # 'hot', 'cold', 'stable'


@dataclass
class FilteredProp:
    """A prop that passes hit rate filters."""
    player: str
    team: str
    prop_type: str
    line: float
    direction: str

    # Hit rate data
    hit_rate: float
    sample_size: int
    streak: int

    # Confidence
    confidence: str  # high, medium, low
    regression_risk: str  # high, medium, low

    # Display
    trend_display: str  # e.g., "5/5 last 5 games"
    recommendation: str


class HitRateTracker:
    """
    Tracks and filters props by historical hit rates.

    Key principle: 51%+ hit rate in 10+ game sample = actionable.
    But beware: small samples and hot streaks regress.
    """

    # Minimum thresholds
    MIN_HIT_RATE = 0.51  # Need 51%+ to overcome vig
    MIN_SAMPLE_SMALL = 5
    MIN_SAMPLE_MEDIUM = 10
    MIN_SAMPLE_CONFIDENT = 20

    def __init__(self):
        self.records: Dict[str, HitRateRecord] = {}

    def add_record(
        self,
        player: str,
        prop_type: str,
        line: float,
        direction: str,
        results: List[bool],  # True = hit, False = miss
        home_results: Optional[List[bool]] = None,
        away_results: Optional[List[bool]] = None,
    ) -> HitRateRecord:
        """
        Add historical results for a prop.

        Args:
            player: Player name
            prop_type: Type of prop (pass_yards, rush_yards, etc.)
            line: The line being tracked
            direction: 'over' or 'under'
            results: List of results (most recent first)
            home_results: Results in home games only
            away_results: Results in away games only
        """
        # Calculate rates
        last_5 = (sum(results[:5]), min(5, len(results)))
        last_10 = (sum(results[:10]), min(10, len(results)))
        season = (sum(results), len(results))

        # Calculate streak
        streak = 0
        for r in results:
            if r:
                streak += 1
            else:
                break
        if not results[0]:  # Currently on miss streak
            streak = 0
            for r in results:
                if not r:
                    streak -= 1
                else:
                    break

        # Trend classification
        if streak >= 5:
            trend = 'hot'
        elif streak <= -3:
            trend = 'cold'
        else:
            trend = 'stable'

        # Home/away rates
        home_rate = sum(home_results) / len(home_results) if home_results else None
        away_rate = sum(away_results) / len(away_results) if away_results else None

        record = HitRateRecord(
            player=player,
            prop_type=prop_type,
            line=line,
            direction=direction,
            last_5_games=last_5,
            last_10_games=last_10,
            season_total=season,
            home_rate=home_rate,
            away_rate=away_rate,
            vs_good_def_rate=None,  # Would need matchup data
            vs_bad_def_rate=None,
            streak=streak,
            trend=trend,
        )

        key = f"{player}_{prop_type}_{direction}"
        self.records[key] = record
        return record

    def filter_actionable_props(
        self,
        min_rate: float = None,
        min_sample: int = None,
        require_trend: bool = False,
    ) -> List[HitRateRecord]:
        """
        Filter to actionable props that pass criteria.

        Args:
            min_rate: Minimum hit rate (default 51%)
            min_sample: Minimum sample size (default 10)
            require_trend: Require positive trend

        Returns:
            List of HitRateRecord meeting criteria
        """
        min_rate = min_rate or self.MIN_HIT_RATE
        min_sample = min_sample or self.MIN_SAMPLE_MEDIUM

        filtered = []

        for record in self.records.values():
            hits, total = record.season_total

            if total < min_sample:
                continue

            rate = hits / total
            if rate < min_rate:
                continue

            if require_trend and record.trend != 'hot':
                continue

            filtered.append(record)

        # Sort by rate descending
        filtered.sort(key=lambda r: r.season_total[0] / r.season_total[1], reverse=True)
        return filtered

    def get_hot_streaks(self, min_streak: int = 5) -> List[HitRateRecord]:
        """Get props with current hot streaks."""
        return [
            r for r in self.records.values()
            if r.streak >= min_streak
        ]

    def assess_regression_risk(self, record: HitRateRecord) -> str:
        """
        Assess risk that a hot streak will regress.

        Signs of regression risk:
        - Small sample size
        - Rate far above baseline
        - Only recent games are hits
        """
        hits, total = record.season_total
        rate = hits / total if total > 0 else 0

        # Small sample = high risk
        if total < 10:
            return 'high'

        # Rate way above 60% = regression likely
        if rate > 0.70 and total < 20:
            return 'high'

        # Hot streak but overall rate not great
        last_5_rate = record.last_5_games[0] / record.last_5_games[1] if record.last_5_games[1] > 0 else 0
        if last_5_rate >= 0.80 and rate < 0.55:
            return 'high'  # Hot streak masking mediocre overall

        # Moderate sample with good rate
        if total >= 15 and 0.55 <= rate <= 0.65:
            return 'low'

        return 'medium'


def create_filtered_prop(
    player: str,
    team: str,
    prop_type: str,
    line: float,
    direction: str,
    results: List[bool],
) -> Optional[FilteredProp]:
    """
    Create a filtered prop if it meets criteria.

    Returns None if doesn't pass filters.
    """
    tracker = HitRateTracker()
    record = tracker.add_record(
        player=player,
        prop_type=prop_type,
        line=line,
        direction=direction,
        results=results,
    )

    hits, total = record.season_total
    rate = hits / total if total > 0 else 0

    # Must meet minimum thresholds
    if total < 5:
        return None
    if rate < 0.50:
        return None

    # Assess confidence
    if total >= 20 and rate >= 0.55:
        confidence = 'high'
    elif total >= 10 and rate >= 0.52:
        confidence = 'medium'
    else:
        confidence = 'low'

    # Regression risk
    regression_risk = tracker.assess_regression_risk(record)

    # Trend display
    l5_hits, l5_total = record.last_5_games
    trend_display = f"{l5_hits}/{l5_total} last {l5_total} games"
    if record.streak >= 5:
        trend_display = f"🔥 {record.streak} in a row! ({trend_display})"

    # Recommendation
    if confidence == 'high' and regression_risk == 'low':
        recommendation = f"✅ STRONG: {rate:.0%} hit rate over {total} games"
    elif confidence == 'medium':
        recommendation = f"👍 SOLID: {rate:.0%} hit rate, {trend_display}"
    elif record.streak >= 5 and regression_risk == 'high':
        recommendation = f"⚠️ HOT but regression likely ({rate:.0%} overall)"
    else:
        recommendation = f"➖ LEAN: {rate:.0%} hit rate"

    return FilteredProp(
        player=player,
        team=team,
        prop_type=prop_type,
        line=line,
        direction=direction,
        hit_rate=rate,
        sample_size=total,
        streak=record.streak,
        confidence=confidence,
        regression_risk=regression_risk,
        trend_display=trend_display,
        recommendation=recommendation,
    )


def format_hot_props_sheet(props: List[FilteredProp]) -> str:
    """Format hot props as a visual sheet."""
    lines = []
    lines.append("")
    lines.append("=" * 60)
    lines.append("🔥 HOT PROPS - 51%+ HIT RATE")
    lines.append("=" * 60)
    lines.append("")
    lines.append("Legend: 🟢 Strong | 🟡 Solid | ⚠️ Regression Risk")
    lines.append("")

    # Group by confidence
    high_conf = [p for p in props if p.confidence == 'high']
    med_conf = [p for p in props if p.confidence == 'medium']

    if high_conf:
        lines.append("-" * 40)
        lines.append("🟢 HIGH CONFIDENCE")
        lines.append("-" * 40)
        for prop in high_conf:
            emoji = "🔥" if prop.streak >= 5 else "🟢"
            lines.append(f"""
{emoji} {prop.player} ({prop.team})
   {prop.prop_type.replace('_', ' ').title()} {prop.direction.upper()} {prop.line}
   Hit Rate: {prop.hit_rate:.0%} (n={prop.sample_size})
   {prop.trend_display}
   {prop.recommendation}
""")

    if med_conf:
        lines.append("-" * 40)
        lines.append("🟡 MEDIUM CONFIDENCE")
        lines.append("-" * 40)
        for prop in med_conf:
            risk_emoji = "⚠️" if prop.regression_risk == 'high' else "🟡"
            lines.append(f"""
{risk_emoji} {prop.player} ({prop.team})
   {prop.prop_type.replace('_', ' ').title()} {prop.direction.upper()} {prop.line}
   Hit Rate: {prop.hit_rate:.0%} (n={prop.sample_size})
   {prop.trend_display}
""")

    lines.append("=" * 60)
    lines.append("⚠️ Remember: 'Last 5 games' trends often regress.")
    lines.append("Larger samples (15+ games) are more reliable.")
    lines.append("=" * 60)

    return "\n".join(lines)


# Example demo data
def generate_demo_hot_props() -> List[FilteredProp]:
    """Generate demo hot props for testing."""

    demo_data = [
        ("Jared Goff", "DET", "pass_yards", 225.5, "over", [True]*5 + [True, True, False, True, True, True, False, True]),
        ("CeeDee Lamb", "DAL", "rec_yards", 70.5, "over", [True]*4 + [False] + [True]*6 + [False, True]),
        ("De'Von Achane", "MIA", "rush_yards", 55.5, "over", [True, True, True, True, False, True, True, False, True, True]),
        ("Travis Kelce", "KC", "receptions", 5.5, "over", [True]*6 + [False, True, True, False, True, True]),
        ("Patrick Mahomes", "KC", "pass_yards", 250.5, "over", [True, True, False, True, True, True, True, False, True, True, True]),
    ]

    props = []
    for player, team, prop_type, line, direction, results in demo_data:
        prop = create_filtered_prop(player, team, prop_type, line, direction, results)
        if prop:
            props.append(prop)

    return props
