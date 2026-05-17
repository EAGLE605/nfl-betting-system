"""Defense vs Position Matchup Analysis

Key edge source: Books are slow to adjust props for defense matchups.
"Most/least yards allowed to QBs, RBs, WRs, TEs" drives prop value.

This module:
1. Tracks defense rankings by position
2. Identifies favorable/unfavorable matchups
3. Adjusts prop projections accordingly
4. Flags exploitable spots

Sources:
- Pro Football Reference defense stats
- NFL Next Gen Stats
- Fantasy football defensive rankings
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


class Position(Enum):
    QB = "QB"
    RB = "RB"
    WR = "WR"
    TE = "TE"


class MatchupGrade(Enum):
    """Matchup quality grades."""
    SMASH = "smash"      # Top 5 easiest (ranks 28-32)
    PLUS = "plus"        # Good (ranks 21-27)
    NEUTRAL = "neutral"  # Average (ranks 12-20)
    TOUGH = "tough"      # Difficult (ranks 6-11)
    AVOID = "avoid"      # Elite defense (ranks 1-5)


@dataclass
class DefenseRanking:
    """Defense ranking against a position."""
    team: str
    position: Position
    rank: int  # 1 = best defense, 32 = worst
    yards_allowed_per_game: float
    tds_allowed_per_game: float
    grade: MatchupGrade


@dataclass
class MatchupAnalysis:
    """Analysis of player vs defense matchup."""
    player: str
    team: str
    position: Position
    opponent: str
    defense_rank: int
    grade: MatchupGrade
    yards_adjustment: float  # Multiplier (1.15 = +15%)
    recommendation: str
    confidence: str


# 2024-2025 Defense Rankings (would be updated dynamically in production)
# Format: {team: {position: (rank, ypg_allowed, td_allowed)}}
DEFENSE_RANKINGS_2024 = {
    # Elite pass defenses
    'BAL': {Position.QB: (2, 185, 1.2), Position.WR: (3, 140, 0.9), Position.TE: (8, 42, 0.3)},
    'BUF': {Position.QB: (4, 195, 1.3), Position.WR: (5, 155, 1.0), Position.TE: (12, 48, 0.4)},
    'SF': {Position.QB: (6, 200, 1.4), Position.WR: (4, 150, 0.9), Position.TE: (6, 40, 0.3)},
    'DEN': {Position.QB: (3, 190, 1.2), Position.WR: (7, 160, 1.0), Position.TE: (15, 52, 0.4)},

    # Elite rush defenses
    'BAL': {Position.RB: (1, 75, 0.4)},
    'DET': {Position.RB: (5, 90, 0.6)},
    'PHI': {Position.RB: (3, 82, 0.5)},

    # Weak pass defenses (TARGET THESE)
    'CAR': {Position.QB: (32, 275, 2.1), Position.WR: (31, 210, 1.8), Position.TE: (29, 68, 0.7)},
    'NYG': {Position.QB: (30, 265, 2.0), Position.WR: (28, 195, 1.6), Position.TE: (27, 62, 0.6)},
    'NE': {Position.QB: (29, 260, 1.9), Position.WR: (30, 200, 1.7), Position.TE: (25, 58, 0.5)},
    'LV': {Position.QB: (28, 255, 1.8), Position.WR: (29, 198, 1.6), Position.TE: (30, 70, 0.7)},
    'TEN': {Position.QB: (27, 250, 1.8), Position.WR: (26, 188, 1.5), Position.TE: (28, 65, 0.6)},

    # Weak rush defenses (TARGET THESE)
    'CAR': {Position.RB: (32, 145, 1.2)},
    'NYG': {Position.RB: (30, 135, 1.1)},
    'LV': {Position.RB: (29, 130, 1.0)},
    'MIA': {Position.RB: (28, 128, 1.0)},
    'SEA': {Position.RB: (27, 125, 0.9)},

    # Average defenses
    'KC': {Position.QB: (15, 225, 1.5), Position.WR: (14, 172, 1.3), Position.RB: (16, 105, 0.7)},
    'DAL': {Position.QB: (18, 232, 1.6), Position.WR: (16, 178, 1.4), Position.RB: (14, 100, 0.7)},
    'GB': {Position.QB: (12, 218, 1.4), Position.WR: (15, 175, 1.3), Position.RB: (20, 112, 0.8)},
}


def get_rank(rank: int) -> MatchupGrade:
    """Convert rank to grade."""
    if rank >= 28:
        return MatchupGrade.SMASH
    elif rank >= 21:
        return MatchupGrade.PLUS
    elif rank >= 12:
        return MatchupGrade.NEUTRAL
    elif rank >= 6:
        return MatchupGrade.TOUGH
    else:
        return MatchupGrade.AVOID


def get_adjustment_multiplier(grade: MatchupGrade) -> float:
    """Get projection adjustment based on matchup grade."""
    return {
        MatchupGrade.SMASH: 1.18,    # +18% boost
        MatchupGrade.PLUS: 1.08,     # +8% boost
        MatchupGrade.NEUTRAL: 1.00,  # No adjustment
        MatchupGrade.TOUGH: 0.92,    # -8% reduction
        MatchupGrade.AVOID: 0.85,    # -15% reduction
    }[grade]


class DefenseMatchupAnalyzer:
    """
    Analyzes player-defense matchups for prop edges.

    Key insight: 5-10% edges appear more often in props when
    defense matchups are properly accounted for.
    """

    def __init__(self, rankings: Optional[Dict] = None):
        """
        Initialize with defense rankings.

        Args:
            rankings: Custom rankings dict, or uses 2024 defaults
        """
        self.rankings = rankings or DEFENSE_RANKINGS_2024

    def analyze_matchup(
        self,
        player: str,
        player_team: str,
        position: Position,
        opponent: str,
        baseline_projection: float,
    ) -> MatchupAnalysis:
        """
        Analyze a player's matchup against opponent defense.

        Args:
            player: Player name
            player_team: Player's team
            position: Position (QB, RB, WR, TE)
            opponent: Opponent team
            baseline_projection: Base yards/stats projection

        Returns:
            MatchupAnalysis with adjusted projection and recommendation
        """
        # Get opponent's defense ranking for this position
        opp_defense = self.rankings.get(opponent, {})
        pos_ranking = opp_defense.get(position)

        if pos_ranking:
            rank, ypg, td_rate = pos_ranking
        else:
            # Default to league average if not found
            rank = 16
            ypg = 200 if position == Position.QB else 100
            td_rate = 1.0

        grade = get_rank(rank)
        adjustment = get_adjustment_multiplier(grade)

        adjusted_projection = baseline_projection * adjustment

        # Generate recommendation
        if grade == MatchupGrade.SMASH:
            recommendation = f"🎯 SMASH SPOT: {opponent} allows most to {position.value}s"
            confidence = "high"
        elif grade == MatchupGrade.PLUS:
            recommendation = f"✅ Good matchup vs {opponent} (rank {rank})"
            confidence = "medium"
        elif grade == MatchupGrade.NEUTRAL:
            recommendation = f"➖ Neutral matchup vs {opponent}"
            confidence = "low"
        elif grade == MatchupGrade.TOUGH:
            recommendation = f"⚠️ Tough matchup vs {opponent} (rank {rank})"
            confidence = "low"
        else:
            recommendation = f"🚫 AVOID: {opponent} has elite {position.value} defense (rank {rank})"
            confidence = "none"

        return MatchupAnalysis(
            player=player,
            team=player_team,
            position=position,
            opponent=opponent,
            defense_rank=rank,
            grade=grade,
            yards_adjustment=adjustment,
            recommendation=recommendation,
            confidence=confidence,
        )

    def get_smash_spots(self, position: Position) -> List[str]:
        """
        Get teams that are smash spots for a position.

        Returns list of team abbreviations.
        """
        smash_teams = []

        for team, pos_ranks in self.rankings.items():
            if position in pos_ranks:
                rank = pos_ranks[position][0]
                if rank >= 28:
                    smash_teams.append(team)

        return smash_teams

    def get_avoid_spots(self, position: Position) -> List[str]:
        """Get teams to avoid for a position."""
        avoid_teams = []

        for team, pos_ranks in self.rankings.items():
            if position in pos_ranks:
                rank = pos_ranks[position][0]
                if rank <= 5:
                    avoid_teams.append(team)

        return avoid_teams

    def print_weekly_matchup_sheet(self, games: List[Dict]):
        """
        Print matchup cheat sheet for the week.

        games: List of dicts with home_team, away_team
        """
        print("\n" + "=" * 65)
        print("🏈 WEEKLY DEFENSE MATCHUP CHEAT SHEET")
        print("=" * 65)

        for position in [Position.QB, Position.RB, Position.WR, Position.TE]:
            print(f"\n{position.value} MATCHUPS:")
            print("-" * 40)

            smash = []
            avoid = []

            for game in games:
                home = game['home_team']
                away = game['away_team']

                # Check home team's offense vs away defense
                away_def = self.rankings.get(away, {}).get(position)
                if away_def and away_def[0] >= 28:
                    smash.append(f"{home} vs {away} (rank {away_def[0]})")
                elif away_def and away_def[0] <= 5:
                    avoid.append(f"{home} vs {away} (rank {away_def[0]})")

                # Check away team's offense vs home defense
                home_def = self.rankings.get(home, {}).get(position)
                if home_def and home_def[0] >= 28:
                    smash.append(f"{away} @ {home} (rank {home_def[0]})")
                elif home_def and home_def[0] <= 5:
                    avoid.append(f"{away} @ {home} (rank {home_def[0]})")

            if smash:
                print(f"  🎯 SMASH: {', '.join(smash)}")
            if avoid:
                print(f"  🚫 AVOID: {', '.join(avoid)}")
            if not smash and not avoid:
                print(f"  ➖ No extreme matchups")

        print("\n" + "=" * 65)
        print("Use this to filter prop bets. Smash spots = overs, Avoid = unders/pass")
        print("=" * 65)


def create_prop_with_matchup_adjustment(
    player: str,
    team: str,
    position: Position,
    opponent: str,
    prop_type: str,
    book_line: float,
    base_projection: float,
) -> Dict:
    """
    Create a prop projection with matchup adjustment built in.

    Returns dict with all analysis.
    """
    analyzer = DefenseMatchupAnalyzer()
    matchup = analyzer.analyze_matchup(
        player=player,
        player_team=team,
        position=position,
        opponent=opponent,
        baseline_projection=base_projection,
    )

    adjusted_projection = base_projection * matchup.yards_adjustment
    edge = (adjusted_projection - book_line) / book_line

    direction = 'over' if adjusted_projection > book_line else 'under'

    return {
        'player': player,
        'team': team,
        'opponent': opponent,
        'prop_type': prop_type,
        'book_line': book_line,
        'base_projection': base_projection,
        'adjusted_projection': round(adjusted_projection, 1),
        'matchup_grade': matchup.grade.value,
        'matchup_rank': matchup.defense_rank,
        'adjustment': matchup.yards_adjustment,
        'edge': edge,
        'direction': direction,
        'recommendation': matchup.recommendation,
        'confidence': matchup.confidence,
    }
