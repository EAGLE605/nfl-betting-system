"""
Line Shopping Integration
Automatically find best odds across all sportsbooks for maximum value
"""

import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.api_integrations import TheOddsAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LineShoppingEngine:
    """
    Line Shopping Engine for NFL Betting

    Features:
    - Compare odds across 15+ sportsbooks
    - Find best moneyline, spread, and total values
    - Calculate edge vs average odds
    - Alert on significant line movements
    - Track sharp money (RLM - Reverse Line Movement)
    """

    def __init__(self, odds_api_key: Optional[str] = None):
        """Initialize line shopping engine."""
        self.odds_api = TheOddsAPI(api_key=odds_api_key)
        self.current_odds = None
        self.last_update = None

    def fetch_odds(self) -> List[Dict]:
        """
        Fetch current NFL odds from The Odds API.

        Returns:
            List of games with odds from multiple books
        """
        logger.info("Fetching current NFL odds...")
        self.current_odds = self.odds_api.get_nfl_odds()
        self.last_update = datetime.now()

        if not self.current_odds:
            logger.warning("No odds data returned")
            return []

        logger.info(f"Fetched odds for {len(self.current_odds)} games")
        return self.current_odds

    def find_best_moneyline(self, game: Dict, team: str) -> Tuple[str, int, float]:
        """
        Find best moneyline odds for a team.

        Args:
            game: Game data from odds API
            team: Team name to find odds for

        Returns:
            Tuple of (bookmaker, odds, implied_probability)
        """
        best_book = None
        best_odds = -999999  # Start with worst possible

        for bookmaker in game["bookmakers"]:
            for market in bookmaker["markets"]:
                if market["key"] == "h2h":  # Moneyline
                    for outcome in market["outcomes"]:
                        if outcome["name"] == team:
                            odds = outcome["price"]
                            if odds > best_odds:
                                best_odds = odds
                                best_book = bookmaker["title"]

        if best_book:
            # Convert American odds to implied probability
            if best_odds > 0:
                implied_prob = 100 / (best_odds + 100)
            else:
                implied_prob = abs(best_odds) / (abs(best_odds) + 100)

            return best_book, best_odds, implied_prob

        return None, None, None

    def find_best_spread(self, game: Dict, team: str) -> Tuple[str, float, int, float]:
        """
        Find best spread odds for a team.

        Args:
            game: Game data from odds API
            team: Team name

        Returns:
            Tuple of (bookmaker, spread, odds, value_edge)
        """
        spreads = []

        for bookmaker in game["bookmakers"]:
            for market in bookmaker["markets"]:
                if market["key"] == "spreads":
                    for outcome in market["outcomes"]:
                        if outcome["name"] == team:
                            spreads.append(
                                {
                                    "book": bookmaker["title"],
                                    "spread": outcome["point"],
                                    "odds": outcome["price"],
                                }
                            )

        if not spreads:
            return None, None, None, None

        # Find best spread value (most points + best odds)
        # For favorites (negative spread): less negative is better
        # For underdogs (positive spread): more positive is better
        best = max(spreads, key=lambda x: (x["spread"], x["odds"]))

        # Calculate edge vs average
        avg_spread = np.mean([s["spread"] for s in spreads])
        edge = best["spread"] - avg_spread

        return best["book"], best["spread"], best["odds"], edge

    def find_best_total(
        self, game: Dict, over_under: str
    ) -> Tuple[str, float, int, float]:
        """
        Find best total (over/under) odds.

        Args:
            game: Game data
            over_under: 'Over' or 'Under'

        Returns:
            Tuple of (bookmaker, total, odds, value_edge)
        """
        totals = []

        for bookmaker in game["bookmakers"]:
            for market in bookmaker["markets"]:
                if market["key"] == "totals":
                    for outcome in market["outcomes"]:
                        if outcome["name"] == over_under:
                            totals.append(
                                {
                                    "book": bookmaker["title"],
                                    "total": outcome["point"],
                                    "odds": outcome["price"],
                                }
                            )

        if not totals:
            return None, None, None, None

        # For overs: lower total is better
        # For unders: higher total is better
        if over_under == "Over":
            best = min(totals, key=lambda x: (x["total"], -x["odds"]))
        else:
            best = max(totals, key=lambda x: (x["total"], x["odds"]))

        # Calculate edge vs average
        avg_total = np.mean([t["total"] for t in totals])
        edge = abs(best["total"] - avg_total)

        return best["book"], best["total"], best["odds"], edge

    def analyze_line_movement(self, game: Dict) -> Dict:
        """
        Analyze line movement and identify sharp money.

        Reverse Line Movement (RLM) indicators:
        - Line moves AGAINST public betting percentage
        - Example: 70% of bets on Team A, but line moves towards Team B

        Args:
            game: Game data

        Returns:
            Dict with movement analysis
        """
        # This requires historical line data
        # For now, we'll check spread of current odds as proxy

        home_spreads = []
        home_moneylines = []

        for bookmaker in game["bookmakers"]:
            for market in bookmaker["markets"]:
                if market["key"] == "spreads":
                    for outcome in market["outcomes"]:
                        if outcome["name"] == game["home_team"]:
                            home_spreads.append(outcome["point"])

                if market["key"] == "h2h":
                    for outcome in market["outcomes"]:
                        if outcome["name"] == game["home_team"]:
                            home_moneylines.append(outcome["price"])

        if not home_spreads:
            return {}

        # Large variance indicates sharp disagreement
        spread_std = np.std(home_spreads)
        spread_range = max(home_spreads) - min(home_spreads)

        analysis = {
            "spread_variance": spread_std,
            "spread_range": spread_range,
            "sharp_indicator": spread_range > 1.0,  # >1 point difference = sharp action
            "books_count": len(home_spreads),
        }

        return analysis

    def generate_line_shopping_report(self, game: Dict) -> Dict:
        """
        Generate comprehensive line shopping report for a game.

        Args:
            game: Game data

        Returns:
            Dict with all best lines and recommendations
        """
        home = game["home_team"]
        away = game["away_team"]

        report = {
            "game": f"{away} @ {home}",
            "game_time": game.get("commence_time", "N/A"),
            "home_team": home,
            "away_team": away,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "moneyline": {},
            "spread": {},
            "total": {},
            "line_movement": {},
        }

        # Best moneylines
        home_ml = self.find_best_moneyline(game, home)
        away_ml = self.find_best_moneyline(game, away)

        report["moneyline"]["home"] = {
            "team": home,
            "best_book": home_ml[0],
            "odds": home_ml[1],
            "implied_prob": f"{home_ml[2]*100:.1f}%" if home_ml[2] else None,
        }

        report["moneyline"]["away"] = {
            "team": away,
            "best_book": away_ml[0],
            "odds": away_ml[1],
            "implied_prob": f"{away_ml[2]*100:.1f}%" if away_ml[2] else None,
        }

        # Best spreads
        home_spread = self.find_best_spread(game, home)
        away_spread = self.find_best_spread(game, away)

        report["spread"]["home"] = {
            "team": home,
            "best_book": home_spread[0],
            "spread": home_spread[1],
            "odds": home_spread[2],
            "edge": f"{home_spread[3]:.2f}pts" if home_spread[3] else None,
        }

        report["spread"]["away"] = {
            "team": away,
            "best_book": away_spread[0],
            "spread": away_spread[1],
            "odds": away_spread[2],
            "edge": f"{away_spread[3]:.2f}pts" if away_spread[3] else None,
        }

        # Best totals
        over = self.find_best_total(game, "Over")
        under = self.find_best_total(game, "Under")

        report["total"]["over"] = {
            "best_book": over[0],
            "total": over[1],
            "odds": over[2],
            "edge": f"{over[3]:.2f}pts" if over[3] else None,
        }

        report["total"]["under"] = {
            "best_book": under[0],
            "total": under[1],
            "odds": under[2],
            "edge": f"{under[3]:.2f}pts" if under[3] else None,
        }

        # Line movement analysis
        report["line_movement"] = self.analyze_line_movement(game)

        return report

    def find_best_values(self, min_edge: float = 0.5) -> List[Dict]:
        """
        Find all games with significant line shopping value.

        Args:
            min_edge: Minimum edge (in points) to be considered valuable

        Returns:
            List of valuable betting opportunities
        """
        if not self.current_odds:
            self.fetch_odds()

        opportunities = []

        for game in self.current_odds:
            report = self.generate_line_shopping_report(game)

            # Check for significant edges
            home_spread_edge = report["spread"]["home"].get("edge", "0.0pts")
            if (
                home_spread_edge
                and float(home_spread_edge.replace("pts", "")) >= min_edge
            ):
                opportunities.append(
                    {
                        "game": report["game"],
                        "type": "spread",
                        "team": report["home_team"],
                        "edge": home_spread_edge,
                        "best_book": report["spread"]["home"]["best_book"],
                    }
                )

            # Check for sharp action
            if report["line_movement"].get("sharp_indicator"):
                opportunities.append(
                    {
                        "game": report["game"],
                        "type": "sharp_action",
                        "variance": report["line_movement"]["spread_variance"],
                        "range": report["line_movement"]["spread_range"],
                    }
                )

        return opportunities


def main():
    """Demo line shopping functionality."""
    import sys

    sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 80)
    print("NFL LINE SHOPPING ENGINE")
    print("=" * 80)

    # Initialize
    engine = LineShoppingEngine()

    # Fetch current odds
    print("\n[1] Fetching current odds...")
    odds = engine.fetch_odds()

    if not odds:
        print("No odds available. Check your API key in config/api_keys.env")
        return

    print(f"[OK] Found {len(odds)} games with odds")

    # Generate reports for all games
    print("\n[2] Generating line shopping reports...\n")

    for i, game in enumerate(odds[:3], 1):  # Show first 3 games
        print(f"\nGAME {i}: {game['away_team']} @ {game['home_team']}")
        print("-" * 80)

        report = engine.generate_line_shopping_report(game)

        # Moneyline
        print("\nBEST MONEYLINE:")
        print(
            f"  {report['moneyline']['home']['team']}: {report['moneyline']['home']['odds']:+d} @ {report['moneyline']['home']['best_book']}"
        )
        print(
            f"  {report['moneyline']['away']['team']}: {report['moneyline']['away']['odds']:+d} @ {report['moneyline']['away']['best_book']}"
        )

        # Spread
        print("\nBEST SPREAD:")
        if report["spread"]["home"]["spread"]:
            print(
                f"  {report['spread']['home']['team']} {report['spread']['home']['spread']:+.1f} ({report['spread']['home']['odds']:+d}) @ {report['spread']['home']['best_book']}"
            )
            print(
                f"  {report['spread']['away']['team']} {report['spread']['away']['spread']:+.1f} ({report['spread']['away']['odds']:+d}) @ {report['spread']['away']['best_book']}"
            )

        # Total
        print("\nBEST TOTAL:")
        if report["total"]["over"]["total"]:
            print(
                f"  Over {report['total']['over']['total']} ({report['total']['over']['odds']:+d}) @ {report['total']['over']['best_book']}"
            )
            print(
                f"  Under {report['total']['under']['total']} ({report['total']['under']['odds']:+d}) @ {report['total']['under']['best_book']}"
            )

        # Sharp indicator
        if report["line_movement"].get("sharp_indicator"):
            print("\n  [ALERT] Sharp money detected! Large variance across books")

        print()

    # Find best values
    print("\n[3] Finding best line shopping opportunities...")
    opportunities = engine.find_best_values(min_edge=0.3)

    if opportunities:
        print(f"\n[OK] Found {len(opportunities)} valuable opportunities:")
        for opp in opportunities:
            if opp["type"] == "spread":
                print(
                    f"  - {opp['game']}: {opp['team']} {opp['edge']} edge @ {opp['best_book']}"
                )
            elif opp["type"] == "sharp_action":
                print(f"  - {opp['game']}: Sharp action (range: {opp['range']:.1f}pts)")
    else:
        print("No significant edges found at this time")

    print("\n" + "=" * 80)
    print("LINE SHOPPING COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
