"""Referee and officiating crew features.

Adds features related to referee statistics and tendencies.
"""

import logging
from typing import List

import pandas as pd

from .base import FeatureBuilder

logger = logging.getLogger(__name__)


class RefereeFeatures(FeatureBuilder):
    """
    Referee and officiating crew features.

    Creates:
    - referee_home_win_rate: Historical home team win rate with this referee
    - referee_penalty_rate: Average penalties per game
    - referee_home_penalty_rate: Home team penalty rate
    """

    def get_required_columns(self) -> List[str]:
        return ["referee", "game_id", "home_team", "result"]

    def build(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build referee features."""
        # Check for required columns
        missing = [col for col in self.get_required_columns() if col not in df.columns]
        if missing:
            logger.warning(
                f"Missing columns for referee features: {missing}, using defaults"
            )
            for col in self.get_feature_names():
                df[col] = 0.0
            return df

        logger.info("Building referee features...")

        # Calculate referee statistics from historical data
        referee_stats = self._calculate_referee_stats(df)

        # Merge with current games by game_id (referee_stats has game_id)
        df = df.merge(referee_stats, on="game_id", how="left", suffixes=("", "_ref"))

        # Fill missing values (new referees)
        for col in self.get_feature_names():
            df[col] = df[col].fillna(0.5)  # Default to neutral

        logger.info(
            f"✓ Referee features created: {len(self.get_feature_names())} features"
        )

        return df

    def _calculate_referee_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate historical referee statistics.

        CRITICAL: Uses only PAST games to avoid temporal leakage.
        For each game, calculates stats from games BEFORE that game.
        """
        # Ensure sorted by date
        df = df.sort_values(["season", "gameday"]).copy()
        df["gameday"] = pd.to_datetime(df["gameday"])

        # Calculate rolling stats per referee per game
        stats_list = []
        for idx, game in df.iterrows():
            referee = game["referee"]
            if pd.isna(referee):
                # Missing referee - use neutral values
                stats_list.append(
                    {
                        "game_id": game["game_id"],
                        "referee": referee,
                        "referee_home_win_rate": 0.5,
                        "referee_penalty_rate": 0.5,
                        "referee_home_penalty_rate": 0.5,
                    }
                )
                continue

            # Get all games BEFORE this game with same referee
            past_games = df[
                (df["gameday"] < game["gameday"]) & (df["referee"] == referee)
            ]

            if len(past_games) > 0:
                # Calculate stats from past games only
                home_wins = (past_games["result"] > 0).sum()
                total_past = len(past_games)
                home_win_rate = home_wins / total_past if total_past > 0 else 0.5
            else:
                # No past games - use neutral (first game for this referee)
                home_win_rate = 0.5

            stats_list.append(
                {
                    "game_id": game["game_id"],
                    "referee": referee,
                    "referee_home_win_rate": home_win_rate,
                    "referee_penalty_rate": 0.5,  # Placeholder - would need PBP data
                    "referee_home_penalty_rate": 0.5,  # Placeholder
                }
            )

        return pd.DataFrame(stats_list)

    def get_feature_names(self) -> List[str]:
        return [
            "referee_home_win_rate",
            "referee_penalty_rate",
            "referee_home_penalty_rate",
        ]
