"""High Accuracy Picks - Documented 60%+ Win Rate Angles

Focus: HIT RATE and FUN over CLV grinding.

These are research-backed situations with documented success rates.
For beer money entertainment betting.

PROVEN ANGLES (60%+ documented):
1. Divisional underdogs: 71% ATS since 2014
2. Fade heavy public (>60%): 63.3% win rate
3. Road favorites off bye: 60.8% ATS
4. Divisional home underdogs Week 1: 79.3% ATS
5. Divisional road dogs ≤6.5: 72.4% ATS
6. Divisional dogs + low total (≤42): 59.6% ATS

Sources:
- NxtBets: https://nxtbets.com/most-consistent-nfl-betting-trends-for-2025/
- Odds Shark: https://www.oddsshark.com/nfl/trends
- VSiN: https://vsin.com/nfl/seven-successful-nfl-week-1-betting-systems/
- BetMGM research
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


class PickConfidence(Enum):
    """Confidence levels based on historical hit rates."""
    ELITE = "elite"      # 70%+ historical
    STRONG = "strong"    # 60-70% historical
    SOLID = "solid"      # 55-60% historical
    LEAN = "lean"        # 52-55% historical


@dataclass
class HighAccuracyPick:
    """A pick based on documented high-accuracy angles."""
    game_id: str
    game: str  # "KC @ BUF"
    pick: str  # "BUF +3"
    pick_team: str
    spread: float

    # The angle that triggered this pick
    angle_name: str
    historical_rate: float  # e.g., 0.71 for 71%
    sample_info: str  # e.g., "37-15-1 since 2014"

    confidence: PickConfidence
    fun_factor: int  # 1-5 scale for excitement

    # Betting info
    recommended_units: float
    notes: str


# NFL Divisions
NFL_DIVISIONS = {
    'AFC East': ['BUF', 'MIA', 'NE', 'NYJ'],
    'AFC North': ['BAL', 'CIN', 'CLE', 'PIT'],
    'AFC South': ['HOU', 'IND', 'JAX', 'TEN'],
    'AFC West': ['DEN', 'KC', 'LAC', 'LV'],
    'NFC East': ['DAL', 'NYG', 'PHI', 'WAS'],
    'NFC North': ['CHI', 'DET', 'GB', 'MIN'],
    'NFC South': ['ATL', 'CAR', 'NO', 'TB'],
    'NFC West': ['ARI', 'LAR', 'SEA', 'SF'],
}

TEAM_TO_DIV = {}
for div, teams in NFL_DIVISIONS.items():
    for team in teams:
        TEAM_TO_DIV[team] = div


class HighAccuracyEngine:
    """
    Identifies games matching proven high-accuracy angles.

    Priority: HIT RATE > CLV > Model probability
    """

    # Documented angles with historical performance
    ANGLES = {
        'divisional_underdog': {
            'rate': 0.71,
            'sample': '37-15-1 since 2014',
            'confidence': PickConfidence.ELITE,
            'fun_factor': 4,
            'description': 'Divisional underdogs cover 71% ATS',
        },
        'div_home_dog_week1': {
            'rate': 0.793,
            'sample': '23-6 since 2009',
            'confidence': PickConfidence.ELITE,
            'fun_factor': 5,
            'description': 'Week 1 divisional home underdogs',
        },
        'div_road_dog_small': {
            'rate': 0.724,
            'sample': '21-8-1 since 2013',
            'confidence': PickConfidence.ELITE,
            'fun_factor': 4,
            'description': 'Divisional road dogs 6.5 or less',
        },
        'div_dog_low_total': {
            'rate': 0.596,
            'sample': '84-57-4 last 5 years',
            'confidence': PickConfidence.STRONG,
            'fun_factor': 3,
            'description': 'Divisional dog + total ≤42',
        },
        'road_fav_off_bye': {
            'rate': 0.608,
            'sample': 'Since 1999',
            'confidence': PickConfidence.STRONG,
            'fun_factor': 3,
            'description': 'Road favorites coming off bye week',
        },
        'fade_heavy_public': {
            'rate': 0.633,
            'sample': '2024 early season',
            'confidence': PickConfidence.STRONG,
            'fun_factor': 4,
            'description': 'Fade teams getting 60%+ public bets',
        },
        'early_season_big_dog': {
            'rate': 0.867,
            'sample': '13-2 ATS weeks 1-3 2024',
            'confidence': PickConfidence.ELITE,
            'fun_factor': 5,
            'description': 'Weeks 1-3 underdogs of 5.5+',
        },
    }

    def __init__(self):
        self.picks: List[HighAccuracyPick] = []

    def analyze_game(
        self,
        game_id: str,
        home_team: str,
        away_team: str,
        spread: float,  # Negative = home favorite
        total: float,
        week: int,
        home_off_bye: bool = False,
        away_off_bye: bool = False,
        public_home_pct: Optional[float] = None,
    ) -> List[HighAccuracyPick]:
        """
        Analyze a game for high-accuracy angles.

        Returns list of picks matching proven angles.
        """
        picks = []
        game = f"{away_team} @ {home_team}"

        # Determine underdog
        if spread > 0:
            dog_team = home_team
            dog_spread = spread
            dog_is_home = True
        else:
            dog_team = away_team
            dog_spread = abs(spread)
            dog_is_home = False

        # Check if divisional game
        is_divisional = TEAM_TO_DIV.get(home_team) == TEAM_TO_DIV.get(away_team)

        # 1. ELITE: Divisional Underdog (71% ATS)
        if is_divisional and dog_spread >= 2.5:
            angle = self.ANGLES['divisional_underdog']
            picks.append(HighAccuracyPick(
                game_id=game_id,
                game=game,
                pick=f"{dog_team} +{dog_spread}",
                pick_team=dog_team,
                spread=dog_spread,
                angle_name='divisional_underdog',
                historical_rate=angle['rate'],
                sample_info=angle['sample'],
                confidence=angle['confidence'],
                fun_factor=angle['fun_factor'],
                recommended_units=2.0,
                notes=f"🔥 ELITE ANGLE: {angle['description']}",
            ))

        # 2. ELITE: Week 1 Divisional Home Dog (79.3% ATS)
        if is_divisional and dog_is_home and week == 1:
            angle = self.ANGLES['div_home_dog_week1']
            picks.append(HighAccuracyPick(
                game_id=game_id,
                game=game,
                pick=f"{dog_team} +{dog_spread}",
                pick_team=dog_team,
                spread=dog_spread,
                angle_name='div_home_dog_week1',
                historical_rate=angle['rate'],
                sample_info=angle['sample'],
                confidence=angle['confidence'],
                fun_factor=angle['fun_factor'],
                recommended_units=2.5,
                notes=f"🔥🔥 ELITE: {angle['description']} - BEST ANGLE",
            ))

        # 3. ELITE: Divisional Road Dog ≤6.5 (72.4% ATS)
        if is_divisional and not dog_is_home and dog_spread <= 6.5:
            angle = self.ANGLES['div_road_dog_small']
            picks.append(HighAccuracyPick(
                game_id=game_id,
                game=game,
                pick=f"{dog_team} +{dog_spread}",
                pick_team=dog_team,
                spread=dog_spread,
                angle_name='div_road_dog_small',
                historical_rate=angle['rate'],
                sample_info=angle['sample'],
                confidence=angle['confidence'],
                fun_factor=angle['fun_factor'],
                recommended_units=2.0,
                notes=f"🔥 ELITE: {angle['description']}",
            ))

        # 4. STRONG: Divisional Dog + Low Total (59.6% ATS)
        if is_divisional and dog_spread >= 2.5 and total <= 42:
            angle = self.ANGLES['div_dog_low_total']
            picks.append(HighAccuracyPick(
                game_id=game_id,
                game=game,
                pick=f"{dog_team} +{dog_spread}",
                pick_team=dog_team,
                spread=dog_spread,
                angle_name='div_dog_low_total',
                historical_rate=angle['rate'],
                sample_info=angle['sample'],
                confidence=angle['confidence'],
                fun_factor=angle['fun_factor'],
                recommended_units=1.5,
                notes=f"💪 STRONG: {angle['description']}",
            ))

        # 5. STRONG: Road Favorite Off Bye (60.8% ATS)
        if spread > 0 and away_off_bye:  # Away is favorite and off bye
            fav_team = away_team
            angle = self.ANGLES['road_fav_off_bye']
            picks.append(HighAccuracyPick(
                game_id=game_id,
                game=game,
                pick=f"{fav_team} {-spread}",
                pick_team=fav_team,
                spread=-spread,
                angle_name='road_fav_off_bye',
                historical_rate=angle['rate'],
                sample_info=angle['sample'],
                confidence=angle['confidence'],
                fun_factor=angle['fun_factor'],
                recommended_units=1.5,
                notes=f"💪 STRONG: {angle['description']}",
            ))

        # 6. STRONG: Fade Heavy Public (63.3%)
        if public_home_pct is not None:
            if public_home_pct > 0.60:
                # Fade home team (bet away)
                angle = self.ANGLES['fade_heavy_public']
                fade_spread = abs(spread) if spread < 0 else -spread
                picks.append(HighAccuracyPick(
                    game_id=game_id,
                    game=game,
                    pick=f"{away_team} {fade_spread:+.1f}",
                    pick_team=away_team,
                    spread=fade_spread,
                    angle_name='fade_heavy_public',
                    historical_rate=angle['rate'],
                    sample_info=angle['sample'],
                    confidence=angle['confidence'],
                    fun_factor=angle['fun_factor'],
                    recommended_units=1.5,
                    notes=f"💪 FADE PUBLIC: {public_home_pct:.0%} on {home_team}",
                ))
            elif public_home_pct < 0.40:
                # Fade away team (bet home)
                angle = self.ANGLES['fade_heavy_public']
                fade_spread = spread
                picks.append(HighAccuracyPick(
                    game_id=game_id,
                    game=game,
                    pick=f"{home_team} {fade_spread:+.1f}",
                    pick_team=home_team,
                    spread=fade_spread,
                    angle_name='fade_heavy_public',
                    historical_rate=angle['rate'],
                    sample_info=angle['sample'],
                    confidence=angle['confidence'],
                    fun_factor=angle['fun_factor'],
                    recommended_units=1.5,
                    notes=f"💪 FADE PUBLIC: {1-public_home_pct:.0%} on {away_team}",
                ))

        # 7. ELITE: Early Season Big Underdog (86.7% - Weeks 1-3 only)
        if week <= 3 and dog_spread >= 5.5:
            angle = self.ANGLES['early_season_big_dog']
            picks.append(HighAccuracyPick(
                game_id=game_id,
                game=game,
                pick=f"{dog_team} +{dog_spread}",
                pick_team=dog_team,
                spread=dog_spread,
                angle_name='early_season_big_dog',
                historical_rate=angle['rate'],
                sample_info=angle['sample'],
                confidence=angle['confidence'],
                fun_factor=angle['fun_factor'],
                recommended_units=2.0,
                notes=f"🔥🔥 ELITE: {angle['description']}",
            ))

        self.picks.extend(picks)
        return picks

    def get_best_picks(self, max_picks: int = 5) -> List[HighAccuracyPick]:
        """Get the best picks sorted by historical rate."""
        # Dedupe by game (take highest rate angle per game)
        best_by_game = {}
        for pick in self.picks:
            if pick.game_id not in best_by_game:
                best_by_game[pick.game_id] = pick
            elif pick.historical_rate > best_by_game[pick.game_id].historical_rate:
                best_by_game[pick.game_id] = pick

        # Sort by rate
        sorted_picks = sorted(
            best_by_game.values(),
            key=lambda p: (p.historical_rate, p.fun_factor),
            reverse=True
        )

        return sorted_picks[:max_picks]


def format_high_accuracy_pick(pick: HighAccuracyPick) -> str:
    """Format a single pick for display."""
    stars = {
        PickConfidence.ELITE: "⭐⭐⭐",
        PickConfidence.STRONG: "⭐⭐",
        PickConfidence.SOLID: "⭐",
        PickConfidence.LEAN: "",
    }[pick.confidence]

    lines = []
    lines.append(f"\n{stars} {pick.game}")
    lines.append(f"   📍 PICK: {pick.pick}")
    lines.append(f"   📊 Historical: {pick.historical_rate:.0%} ({pick.sample_info})")
    lines.append(f"   🎯 Angle: {pick.angle_name.replace('_', ' ').title()}")
    lines.append(f"   💰 Units: {pick.recommended_units}")
    lines.append(f"   {pick.notes}")

    return "\n".join(lines)


def print_high_accuracy_card(picks: List[HighAccuracyPick]):
    """Print the full high-accuracy card."""
    print("\n" + "=" * 65)
    print("🎯 HIGH ACCURACY PICKS - DOCUMENTED 60%+ WIN RATES")
    print("=" * 65)
    print("Focus: HIT RATE & FUN over CLV grinding")
    print("-" * 65)

    if not picks:
        print("\nNo high-accuracy angles match this week's slate.")
        return

    # Group by confidence
    elite = [p for p in picks if p.confidence == PickConfidence.ELITE]
    strong = [p for p in picks if p.confidence == PickConfidence.STRONG]

    if elite:
        print("\n🔥 ELITE PLAYS (70%+ Historical)")
        print("-" * 40)
        for pick in elite:
            print(format_high_accuracy_pick(pick))

    if strong:
        print("\n💪 STRONG PLAYS (60-70% Historical)")
        print("-" * 40)
        for pick in strong:
            print(format_high_accuracy_pick(pick))

    # Summary
    total_units = sum(p.recommended_units for p in picks)
    avg_rate = sum(p.historical_rate for p in picks) / len(picks)

    print("\n" + "=" * 65)
    print(f"SUMMARY: {len(picks)} plays | {total_units:.1f} total units | {avg_rate:.0%} avg historical rate")
    print("=" * 65)
    print("\n⚠️  Historical rates are not guarantees. Gamble responsibly!")
    print("📚 Sources: NxtBets, VSiN, BetMGM, Odds Shark research")


def analyze_week_for_accuracy(games_df: pd.DataFrame) -> List[HighAccuracyPick]:
    """Analyze a week's games for high-accuracy angles."""
    engine = HighAccuracyEngine()

    for idx, row in games_df.iterrows():
        engine.analyze_game(
            game_id=row.get('game_id', f'game_{idx}'),
            home_team=row['home_team'],
            away_team=row['away_team'],
            spread=row.get('spread_line', 0),
            total=row.get('total_line', 45),
            week=row.get('week', 1),
            home_off_bye=row.get('home_off_bye', False),
            away_off_bye=row.get('away_off_bye', False),
            public_home_pct=row.get('public_home_pct', None),
        )

    return engine.get_best_picks()
