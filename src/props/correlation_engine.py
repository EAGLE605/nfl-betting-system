"""SGP Correlation Engine - The Core of Prop Value

Correlation determines SGP success. Books price positive correlation in,
so edge comes from finding UNDERPRICED correlations.

Key Correlations (Research-Backed):
HIGH POSITIVE:
  - QB pass yards + WR1 receiving yards (0.65-0.75)
  - Team total over + skill position overs (0.50-0.60)
  - QB pass yards + WR1 receptions (0.60-0.70)
  - Game total over + anytime TD scorers (0.40-0.50)

LOW/NEGATIVE:
  - RB rush yards + QB pass yards (-0.30 to -0.40)
  - Two RBs same team in committee (-0.20 to -0.30)
  - WR1 yards + WR2 yards same team (0.10-0.20, lower than expected)

Sources:
- DraftKings prop correlation data
- Historical SGP analysis
- Statistical modeling research
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class PropType(Enum):
    """Player prop types."""
    PASS_YARDS = "pass_yards"
    PASS_TDS = "pass_tds"
    PASS_ATTEMPTS = "pass_attempts"
    COMPLETIONS = "completions"
    RUSH_YARDS = "rush_yards"
    RUSH_ATTEMPTS = "rush_attempts"
    REC_YARDS = "rec_yards"
    RECEPTIONS = "receptions"
    ANYTIME_TD = "anytime_td"
    FIRST_TD = "first_td"


@dataclass
class CorrelationPair:
    """Correlation between two prop types."""
    prop1: PropType
    prop2: PropType
    same_player: bool
    same_team: bool
    correlation: float  # -1 to 1
    confidence: str  # high, medium, low
    notes: str


# Research-backed correlation matrix
CORRELATION_MATRIX: Dict[Tuple[str, str, bool, bool], float] = {
    # Same player correlations
    (PropType.PASS_YARDS, PropType.PASS_TDS, True, True): 0.55,
    (PropType.PASS_YARDS, PropType.COMPLETIONS, True, True): 0.80,
    (PropType.RUSH_YARDS, PropType.RUSH_ATTEMPTS, True, True): 0.75,
    (PropType.REC_YARDS, PropType.RECEPTIONS, True, True): 0.70,
    (PropType.RECEPTIONS, PropType.ANYTIME_TD, True, True): 0.25,

    # Same team, different players (QB + WR)
    (PropType.PASS_YARDS, PropType.REC_YARDS, False, True): 0.65,
    (PropType.PASS_YARDS, PropType.RECEPTIONS, False, True): 0.60,
    (PropType.PASS_TDS, PropType.ANYTIME_TD, False, True): 0.35,
    (PropType.COMPLETIONS, PropType.RECEPTIONS, False, True): 0.55,

    # Same team negatives (RB vs QB in same game)
    (PropType.RUSH_YARDS, PropType.PASS_YARDS, False, True): -0.35,
    (PropType.RUSH_ATTEMPTS, PropType.PASS_ATTEMPTS, False, True): -0.40,

    # Same team RB committee (both RBs)
    (PropType.RUSH_YARDS, PropType.RUSH_YARDS, False, True): -0.25,

    # Opponent correlations (opposite teams)
    (PropType.PASS_YARDS, PropType.PASS_YARDS, False, False): 0.15,
    (PropType.RUSH_YARDS, PropType.RUSH_YARDS, False, False): 0.05,
}


class CorrelationEngine:
    """
    Calculates and scores correlations for SGP building.

    Key insight: Books price in obvious correlations.
    Edge comes from finding correlations they've underpriced.
    """

    def __init__(self):
        self.correlation_cache = {}

    def get_correlation(
        self,
        prop1_type: PropType,
        prop2_type: PropType,
        same_player: bool,
        same_team: bool,
    ) -> float:
        """
        Get correlation coefficient between two props.

        Returns value from -1 (negative) to 1 (positive).
        """
        # Check both orderings
        key1 = (prop1_type, prop2_type, same_player, same_team)
        key2 = (prop2_type, prop1_type, same_player, same_team)

        if key1 in CORRELATION_MATRIX:
            return CORRELATION_MATRIX[key1]
        elif key2 in CORRELATION_MATRIX:
            return CORRELATION_MATRIX[key2]
        else:
            # Default: slight positive for same team, neutral otherwise
            if same_team:
                return 0.15
            return 0.0

    def score_sgp_correlation(
        self,
        legs: List[Dict],
    ) -> Tuple[float, str, List[str]]:
        """
        Score an SGP's overall correlation strength.

        Args:
            legs: List of dicts with keys:
                  player, team, prop_type, direction (over/under)

        Returns:
            (score, rating, warnings)
            score: -1 to 1 composite correlation
            rating: 'excellent', 'good', 'neutral', 'poor', 'conflicting'
            warnings: List of potential issues
        """
        if len(legs) < 2:
            return 0.0, 'neutral', ['Need 2+ legs for SGP']

        correlations = []
        warnings = []

        # Check all pairs
        for i, leg1 in enumerate(legs):
            for leg2 in legs[i+1:]:
                same_player = leg1['player'] == leg2['player']
                same_team = leg1['team'] == leg2['team']

                corr = self.get_correlation(
                    PropType(leg1['prop_type']),
                    PropType(leg2['prop_type']),
                    same_player,
                    same_team,
                )

                # Adjust for direction
                # Over + Over with positive correlation = good
                # Over + Under with positive correlation = bad
                dir1_mult = 1 if leg1['direction'] == 'over' else -1
                dir2_mult = 1 if leg2['direction'] == 'over' else -1

                if dir1_mult != dir2_mult:
                    corr = -corr

                correlations.append(corr)

                # Check for warnings
                if corr < -0.2:
                    warnings.append(
                        f"⚠️ Negative correlation: {leg1['player']} {leg1['prop_type']} "
                        f"vs {leg2['player']} {leg2['prop_type']}"
                    )

        # Composite score
        avg_corr = np.mean(correlations) if correlations else 0.0

        # Rating
        if avg_corr >= 0.4:
            rating = 'excellent'
        elif avg_corr >= 0.2:
            rating = 'good'
        elif avg_corr >= -0.1:
            rating = 'neutral'
        elif avg_corr >= -0.3:
            rating = 'poor'
        else:
            rating = 'conflicting'

        return float(avg_corr), rating, warnings

    def suggest_correlated_adds(
        self,
        current_legs: List[Dict],
        available_props: List[Dict],
    ) -> List[Tuple[Dict, float, str]]:
        """
        Suggest props to add that correlate well with current legs.

        Returns list of (prop, correlation_boost, reason).
        """
        suggestions = []

        for prop in available_props:
            # Skip if already in legs
            if any(
                l['player'] == prop['player'] and l['prop_type'] == prop['prop_type']
                for l in current_legs
            ):
                continue

            # Calculate how adding this prop affects correlation
            test_legs = current_legs + [prop]
            new_score, new_rating, _ = self.score_sgp_correlation(test_legs)
            old_score, _, _ = self.score_sgp_correlation(current_legs)

            boost = new_score - old_score

            if boost > 0.1:
                reason = f"Adds {boost:+.2f} correlation with existing legs"
                suggestions.append((prop, boost, reason))

        # Sort by boost
        suggestions.sort(key=lambda x: -x[1])
        return suggestions[:5]


def build_correlated_sgp(
    game_props: List[Dict],
    max_legs: int = 3,
    min_correlation: float = 0.2,
) -> Tuple[List[Dict], float, str]:
    """
    Automatically build best correlated SGP from available props.

    Strategy:
    1. Start with highest-edge prop
    2. Add props that positively correlate
    3. Stop at max_legs or when correlation drops

    Returns:
        (legs, correlation_score, rating)
    """
    if len(game_props) < 2:
        return [], 0.0, 'insufficient_props'

    engine = CorrelationEngine()

    # Sort by edge (highest first)
    sorted_props = sorted(game_props, key=lambda p: p.get('edge', 0), reverse=True)

    # Start with best prop
    sgp_legs = [sorted_props[0]]
    remaining = sorted_props[1:]

    while len(sgp_legs) < max_legs and remaining:
        # Find best addition
        best_add = None
        best_score = -999

        for prop in remaining:
            test_legs = sgp_legs + [prop]
            score, rating, _ = engine.score_sgp_correlation(test_legs)

            if score > best_score and score >= min_correlation:
                best_score = score
                best_add = prop

        if best_add:
            sgp_legs.append(best_add)
            remaining.remove(best_add)
        else:
            break

    final_score, final_rating, _ = engine.score_sgp_correlation(sgp_legs)
    return sgp_legs, final_score, final_rating


# Pre-built correlation templates for common SGPs
SGP_TEMPLATES = {
    'qb_stack': {
        'description': 'QB + WR1 stack (high correlation)',
        'legs': [
            {'role': 'qb', 'prop_type': 'pass_yards', 'direction': 'over'},
            {'role': 'wr1', 'prop_type': 'rec_yards', 'direction': 'over'},
        ],
        'expected_correlation': 0.65,
    },
    'shootout': {
        'description': 'High-scoring game stack',
        'legs': [
            {'role': 'qb', 'prop_type': 'pass_yards', 'direction': 'over'},
            {'role': 'wr1', 'prop_type': 'receptions', 'direction': 'over'},
            {'role': 'anytime_scorer', 'prop_type': 'anytime_td', 'direction': 'over'},
        ],
        'expected_correlation': 0.50,
    },
    'ground_game': {
        'description': 'Run-heavy game script',
        'legs': [
            {'role': 'rb1', 'prop_type': 'rush_yards', 'direction': 'over'},
            {'role': 'rb1', 'prop_type': 'rush_attempts', 'direction': 'over'},
        ],
        'expected_correlation': 0.75,
    },
    'volume_receiver': {
        'description': 'Target hog stack',
        'legs': [
            {'role': 'wr1', 'prop_type': 'receptions', 'direction': 'over'},
            {'role': 'wr1', 'prop_type': 'rec_yards', 'direction': 'over'},
        ],
        'expected_correlation': 0.70,
    },
}


def print_correlation_analysis(legs: List[Dict]):
    """Print correlation analysis for SGP."""
    engine = CorrelationEngine()
    score, rating, warnings = engine.score_sgp_correlation(legs)

    rating_emoji = {
        'excellent': '🟢',
        'good': '🟡',
        'neutral': '⚪',
        'poor': '🟠',
        'conflicting': '🔴',
    }

    print(f"\n{'='*50}")
    print("SGP CORRELATION ANALYSIS")
    print(f"{'='*50}")
    print(f"\nLegs: {len(legs)}")
    for leg in legs:
        print(f"  • {leg['player']} ({leg['team']}): {leg['prop_type']} {leg['direction']}")

    print(f"\nCorrelation Score: {score:+.2f}")
    print(f"Rating: {rating_emoji.get(rating, '?')} {rating.upper()}")

    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  {w}")

    if rating in ['excellent', 'good']:
        print("\n✅ This SGP has favorable correlation!")
    elif rating == 'conflicting':
        print("\n❌ These legs work AGAINST each other. Reconsider.")

    print(f"{'='*50}")
