"""
Smart Parlay Generator

Generates intelligent parlay combinations from individual bet recommendations.

Rules:
1. Only use Tier S bets (highest confidence)
2. Check for correlation (no same game, no division rivals on same day)
3. Max 3 legs per parlay
4. Combined probability must be > 45%
5. Expected value must be positive
6. Sort by expected ROI

Usage:
    python scripts/parlay_generator.py --input reports/pregame_analysis.json
    python scripts/parlay_generator.py --input reports/pregame_analysis.json --output reports/parlays.json
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import logging
from itertools import combinations
from typing import Dict, List

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ParlayCalculator:
    """Calculates parlay odds and probabilities."""

    @staticmethod
    def american_to_decimal(american_odds: float) -> float:
        """Convert American odds to decimal."""
        if american_odds > 0:
            return (american_odds / 100) + 1
        else:
            return (100 / abs(american_odds)) + 1

    @staticmethod
    def decimal_to_american(decimal_odds: float) -> float:
        """Convert decimal odds to American."""
        if decimal_odds >= 2.0:
            return (decimal_odds - 1) * 100
        else:
            return -100 / (decimal_odds - 1)

    @staticmethod
    def calculate_parlay_odds(individual_odds: List[float]) -> float:
        """
        Calculate parlay odds from individual American odds.

        Args:
            individual_odds: List of American odds for each leg

        Returns:
            Combined American odds for parlay

        Example:
            calculate_parlay_odds([-110, -110, +150])
            # Returns: +502  (parlay pays 5.02x if all win)
        """
        # Convert all to decimal
        decimal_odds = [
            ParlayCalculator.american_to_decimal(o) for o in individual_odds
        ]

        # Multiply for parlay
        parlay_decimal = 1.0
        for odds in decimal_odds:
            parlay_decimal *= odds

        # Convert back to American
        parlay_american = ParlayCalculator.decimal_to_american(parlay_decimal)

        return parlay_american

    @staticmethod
    def calculate_combined_probability(individual_probs: List[float]) -> float:
        """
        Calculate combined win probability for parlay.

        Args:
            individual_probs: List of win probabilities (0-1) for each leg

        Returns:
            Combined probability (0-1)

        Example:
            calculate_combined_probability([0.65, 0.70, 0.60])
            # Returns: 0.273  (27.3% chance all three win)
        """
        combined = 1.0
        for prob in individual_probs:
            combined *= prob
        return combined

    @staticmethod
    def calculate_expected_value(win_prob: float, parlay_odds: float) -> float:
        """
        Calculate expected value of parlay.

        Args:
            win_prob: Combined win probability (0-1)
            parlay_odds: Parlay payout odds (American format)

        Returns:
            Expected value as decimal (e.g., 0.15 = +15% EV)
        """
        decimal_odds = ParlayCalculator.american_to_decimal(parlay_odds)

        # EV = (win_prob × payout) - (lose_prob × stake)
        # With $1 stake: EV = (win_prob × decimal_odds) - 1
        ev = (win_prob * decimal_odds) - 1

        return ev


class CorrelationChecker:
    """Checks if bets are correlated (should not be parlayed)."""

    @staticmethod
    def is_same_game(bet1: Dict, bet2: Dict) -> bool:
        """Check if two bets are from the same game."""
        return bet1["game_info"]["game_id"] == bet2["game_info"]["game_id"]

    @staticmethod
    def is_division_rivals_same_day(bet1: Dict, bet2: Dict) -> bool:
        """
        Check if bets involve division rivals playing on the same day.

        Examples of correlation:
        - KC vs DEN + LV vs LAC (both AFC West games on same day)
        - DAL vs PHI + NYG vs WAS (both NFC East games on same day)
        """
        # Get team info
        bet1_teams = {bet1["game_info"]["home_team"], bet1["game_info"]["away_team"]}
        bet2_teams = {bet2["game_info"]["home_team"], bet2["game_info"]["away_team"]}

        # Same day?
        bet1_date = bet1["game_info"].get("game_date", "")
        bet2_date = bet2["game_info"].get("game_date", "")

        if bet1_date != bet2_date:
            return False

        # Division mapping (NFL divisions)
        divisions = {
            "AFC East": [
                "Buffalo Bills",
                "Miami Dolphins",
                "New England Patriots",
                "New York Jets",
            ],
            "AFC North": [
                "Baltimore Ravens",
                "Cincinnati Bengals",
                "Cleveland Browns",
                "Pittsburgh Steelers",
            ],
            "AFC South": [
                "Houston Texans",
                "Indianapolis Colts",
                "Jacksonville Jaguars",
                "Tennessee Titans",
            ],
            "AFC West": [
                "Denver Broncos",
                "Kansas City Chiefs",
                "Las Vegas Raiders",
                "Los Angeles Chargers",
            ],
            "NFC East": [
                "Dallas Cowboys",
                "New York Giants",
                "Philadelphia Eagles",
                "Washington Commanders",
            ],
            "NFC North": [
                "Chicago Bears",
                "Detroit Lions",
                "Green Bay Packers",
                "Minnesota Vikings",
            ],
            "NFC South": [
                "Atlanta Falcons",
                "Carolina Panthers",
                "New Orleans Saints",
                "Tampa Bay Buccaneers",
            ],
            "NFC West": [
                "Arizona Cardinals",
                "Los Angeles Rams",
                "San Francisco 49ers",
                "Seattle Seahawks",
            ],
        }

        # Find divisions for both games
        bet1_division = None
        bet2_division = None

        for div, teams in divisions.items():
            if any(team in bet1_teams for team in teams):
                bet1_division = div
            if any(team in bet2_teams for team in teams):
                bet2_division = div

        # If same division and same day, they're correlated
        return bet1_division == bet2_division and bet1_division is not None

    @staticmethod
    def is_correlated(bet1: Dict, bet2: Dict) -> bool:
        """
        Check if two bets are correlated.

        Returns True if they should NOT be parlayed together.
        """
        # Same game = definitely correlated
        if CorrelationChecker.is_same_game(bet1, bet2):
            return True

        # Division rivals on same day = likely correlated
        if CorrelationChecker.is_division_rivals_same_day(bet1, bet2):
            return True

        # No correlation detected
        return False


class ParlayGenerator:
    """Generates smart parlay combinations."""

    def __init__(self):
        self.calculator = ParlayCalculator()
        self.correlation_checker = CorrelationChecker()

    def load_recommendations(self, input_file: str) -> List[Dict]:
        """
        Load bet recommendations from pre-game analysis.

        Args:
            input_file: Path to pregame_analysis.json

        Returns:
            List of bet recommendation dictionaries
        """
        with open(input_file, "r") as f:
            analyses = json.load(f)

        # Extract all recommendations
        all_recs = []
        for analysis in analyses:
            for rec in analysis["recommendations"]:
                # Add game info to recommendation
                rec["game_info"] = analysis["game_info"]
                all_recs.append(rec)

        logger.info(f"Loaded {len(all_recs)} bet recommendations")
        return all_recs

    def filter_tier_s_bets(self, recommendations: List[Dict]) -> List[Dict]:
        """
        Filter for Tier S bets only (highest confidence).

        Args:
            recommendations: List of all recommendations

        Returns:
            List of Tier S recommendations only
        """
        tier_s = [r for r in recommendations if r.get("confidence_tier") == "S"]
        logger.info(f"Filtered to {len(tier_s)} Tier S bets")
        return tier_s

    def generate_2_leg_parlays(self, bets: List[Dict]) -> List[Dict]:
        """Generate all valid 2-leg parlay combinations."""
        parlays = []

        for bet1, bet2 in combinations(bets, 2):
            # Check correlation
            if self.correlation_checker.is_correlated(bet1, bet2):
                continue

            # Calculate parlay
            parlay = self._create_parlay([bet1, bet2])

            # Only add if positive EV and >45% probability
            if parlay["expected_value"] > 0 and parlay["combined_probability"] > 0.45:
                parlays.append(parlay)

        logger.info(f"Generated {len(parlays)} valid 2-leg parlays")
        return parlays

    def generate_3_leg_parlays(self, bets: List[Dict]) -> List[Dict]:
        """Generate all valid 3-leg parlay combinations."""
        parlays = []

        for bet1, bet2, bet3 in combinations(bets, 3):
            # Check correlation (pairwise)
            if (
                self.correlation_checker.is_correlated(bet1, bet2)
                or self.correlation_checker.is_correlated(bet1, bet3)
                or self.correlation_checker.is_correlated(bet2, bet3)
            ):
                continue

            # Calculate parlay
            parlay = self._create_parlay([bet1, bet2, bet3])

            # Only add if positive EV and >40% probability (slightly lower for 3-leg)
            if parlay["expected_value"] > 0 and parlay["combined_probability"] > 0.40:
                parlays.append(parlay)

        logger.info(f"Generated {len(parlays)} valid 3-leg parlays")
        return parlays

    def _create_parlay(self, legs: List[Dict]) -> Dict:
        """Create parlay object from legs."""
        # Extract odds and probabilities
        individual_odds = []
        individual_probs = []

        for leg in legs:
            # Handle missing odds
            if leg["odds"] is None:
                # Use implied odds from probability
                prob = leg["win_probability"]
                decimal_odds = 1 / prob
                american_odds = self.calculator.decimal_to_american(decimal_odds)
                individual_odds.append(american_odds)
            else:
                individual_odds.append(leg["odds"])

            individual_probs.append(leg["win_probability"])

        # Calculate parlay odds
        parlay_odds = self.calculator.calculate_parlay_odds(individual_odds)

        # Calculate combined probability
        combined_prob = self.calculator.calculate_combined_probability(individual_probs)

        # Calculate expected value
        ev = self.calculator.calculate_expected_value(combined_prob, parlay_odds)

        # Build parlay object
        parlay = {
            "legs": [
                {
                    "team": leg["team"],
                    "bet_type": leg["bet_type"],
                    "odds": leg["odds"],
                    "win_probability": leg["win_probability"],
                    "edge_name": leg["edge_name"],
                    "game": f"{leg['game_info']['away_team']} @ {leg['game_info']['home_team']}",
                }
                for leg in legs
            ],
            "num_legs": len(legs),
            "parlay_odds": parlay_odds,
            "combined_probability": combined_prob,
            "expected_value": ev,
            "expected_roi": ev,
            "recommended_stake_pct": min(
                combined_prob * 0.5, 0.02
            ),  # Max 2% of bankroll
        }

        return parlay

    def generate_all_parlays(self, recommendations: List[Dict]) -> Dict:
        """
        Generate all valid parlay combinations.

        Returns:
            Dictionary with 2-leg and 3-leg parlays
        """
        # Filter for Tier S bets
        tier_s_bets = self.filter_tier_s_bets(recommendations)

        if len(tier_s_bets) < 2:
            logger.warning("Not enough Tier S bets for parlays (need at least 2)")
            return {"2_leg": [], "3_leg": []}

        # Generate 2-leg parlays
        two_leg = self.generate_2_leg_parlays(tier_s_bets)

        # Generate 3-leg parlays (if enough bets)
        three_leg = []
        if len(tier_s_bets) >= 3:
            three_leg = self.generate_3_leg_parlays(tier_s_bets)

        # Sort by expected ROI
        two_leg = sorted(two_leg, key=lambda x: x["expected_roi"], reverse=True)
        three_leg = sorted(three_leg, key=lambda x: x["expected_roi"], reverse=True)

        return {
            "2_leg": two_leg[:5],  # Top 5 only
            "3_leg": three_leg[:5],  # Top 5 only
        }


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Smart Parlay Generator")
    parser.add_argument(
        "--input", required=True, help="Input file (pregame_analysis.json)"
    )
    parser.add_argument(
        "--output", default="reports/parlays.json", help="Output file path"
    )

    args = parser.parse_args()

    # Initialize generator
    generator = ParlayGenerator()

    # Load recommendations
    recommendations = generator.load_recommendations(args.input)

    if not recommendations:
        logger.warning("No recommendations found in input file")
        # Create empty output
        parlays = {"2_leg": [], "3_leg": []}
    else:
        # Generate parlays
        parlays = generator.generate_all_parlays(recommendations)

    # Print results
    print(f"\n{'='*80}")
    print("PARLAY RECOMMENDATIONS")
    print(f"{'='*80}\n")

    # 2-leg parlays
    if parlays["2_leg"]:
        print(f"2-LEG PARLAYS ({len(parlays['2_leg'])} recommended):\n")
        for i, parlay in enumerate(parlays["2_leg"], 1):
            print(f"Parlay #{i}:")
            for j, leg in enumerate(parlay["legs"], 1):
                odds_str = f"{leg['odds']:+.0f}" if leg["odds"] else "N/A"
                print(f"  Leg {j}: {leg['team']} {leg['bet_type']} ({odds_str})")
                print(f"         {leg['game']}")
                print(
                    f"         Win Prob: {leg['win_probability']:.1%}, Edge: {leg['edge_name']}"
                )
            print(f"  Combined Odds: {parlay['parlay_odds']:+.0f}")
            print(f"  Combined Probability: {parlay['combined_probability']:.1%}")
            print(f"  Expected Value: {parlay['expected_value']:+.2%}")
            print(
                f"  Recommended Stake: {parlay['recommended_stake_pct']:.1%} of bankroll"
            )
            print()
    else:
        print("No 2-leg parlays recommended\n")

    # 3-leg parlays
    if parlays["3_leg"]:
        print(f"3-LEG PARLAYS ({len(parlays['3_leg'])} recommended):\n")
        for i, parlay in enumerate(parlays["3_leg"], 1):
            print(f"Parlay #{i}:")
            for j, leg in enumerate(parlay["legs"], 1):
                odds_str = f"{leg['odds']:+.0f}" if leg["odds"] else "N/A"
                print(f"  Leg {j}: {leg['team']} {leg['bet_type']} ({odds_str})")
                print(f"         {leg['game']}")
                print(
                    f"         Win Prob: {leg['win_probability']:.1%}, Edge: {leg['edge_name']}"
                )
            print(f"  Combined Odds: {parlay['parlay_odds']:+.0f}")
            print(f"  Combined Probability: {parlay['combined_probability']:.1%}")
            print(f"  Expected Value: {parlay['expected_value']:+.2%}")
            print(
                f"  Recommended Stake: {parlay['recommended_stake_pct']:.1%} of bankroll"
            )
            print()
    else:
        print("No 3-leg parlays recommended\n")

    # Save to file
    output_dir = Path(args.output).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(args.output, "w") as f:
        json.dump(parlays, f, indent=2, default=str)

    logger.info(f"\n{'='*80}")
    logger.info("[SUCCESS] PARLAY GENERATION COMPLETE")
    logger.info(f"{'='*80}")
    logger.info(f"Results saved to: {args.output}")
    logger.info(f"2-leg parlays: {len(parlays['2_leg'])}")
    logger.info(f"3-leg parlays: {len(parlays['3_leg'])}")
    logger.info(f"{'='*80}")


if __name__ == "__main__":
    main()
