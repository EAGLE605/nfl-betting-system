"""Injury and roster features.

Adds features related to team injuries and roster changes.
"""

import logging
from typing import List, Optional

import pandas as pd

from .base import FeatureBuilder

logger = logging.getLogger(__name__)


class InjuryFeatures(FeatureBuilder):
    """
    Injury and roster features from nflverse data.

    Creates:
    - injury_count_home/away: Number of key player injuries (last 2 weeks)
    - roster_changes_home/away: Number of roster changes (last 2 weeks)
    """

    def __init__(self, injury_data: Optional[pd.DataFrame] = None):
        """
        Initialize injury features.

        Args:
            injury_data: Injury DataFrame from nflverse
        """
        self.injury_data = injury_data

    def get_required_columns(self) -> List[str]:
        return ["game_id", "gameday", "season", "week", "home_team", "away_team"]

    def build(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build injury features."""
        if self.injury_data is None or len(self.injury_data) == 0:
            logger.warning("No injury data provided, skipping injury features")
            df["injury_count_home"] = 0
            df["injury_count_away"] = 0
            df["roster_changes_home"] = 0
            df["roster_changes_away"] = 0
            return df

        logger.info("Building injury features...")

        # Ensure datetime
        df["gameday"] = pd.to_datetime(df["gameday"])
        df = df.sort_values(["season", "gameday"]).copy()

        # Process injury data
        injury_metrics = self._calculate_injury_metrics(df)

        # Merge home team injuries
        df = df.merge(
            injury_metrics,
            left_on=["game_id", "home_team"],
            right_on=["game_id", "team"],
            how="left",
            suffixes=("", "_home")
        )
        df["injury_count_home"] = df["injury_count"].fillna(0)
        df["roster_changes_home"] = df["roster_changes"].fillna(0)
        df = df.drop(columns=["team", "injury_count", "roster_changes"], errors="ignore")

        # Merge away team injuries
        df = df.merge(
            injury_metrics,
            left_on=["game_id", "away_team"],
            right_on=["game_id", "team"],
            how="left",
            suffixes=("", "_away")
        )
        df["injury_count_away"] = df["injury_count"].fillna(0)
        df["roster_changes_away"] = df["roster_changes"].fillna(0)
        df = df.drop(columns=["team", "injury_count", "roster_changes"], errors="ignore")

        logger.info(f"✓ Injury features created: {len(self.get_feature_names())} features")

        return df

    def _calculate_injury_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate injury metrics per game."""
        injuries = self.injury_data.copy()
        
        # Ensure date columns are datetime
        if "report_date" in injuries.columns:
            injuries["report_date"] = pd.to_datetime(injuries["report_date"], errors='coerce')
        elif "date" in injuries.columns:
            injuries["report_date"] = pd.to_datetime(injuries["date"], errors='coerce')
        else:
            logger.warning("No date column in injury data, using season-based approximation")
            # Create approximate dates from season
            injuries["report_date"] = pd.to_datetime(
                injuries["season"].astype(int).astype(str) + "-09-01", 
                errors='coerce'
            )
        
        # Filter to last 2 weeks before each game
        metrics_list = []
        for _, game in df.iterrows():
            game_date = pd.to_datetime(game["gameday"])
            cutoff_date = game_date - pd.Timedelta(days=14)
            
            # Get injuries in the 2 weeks before this game (or same season if no dates)
            if injuries["report_date"].notna().any():
                recent_injuries = injuries[
                    (injuries["report_date"] >= cutoff_date) &
                    (injuries["report_date"] < game_date) &
                    (injuries["season"] == game["season"])
                ]
            else:
                # Fallback: use same season but filter by week if available
                if "week" in injuries.columns and "week" in game:
                    # Only use injuries from weeks before this game
                    recent_injuries = injuries[
                        (injuries["season"] == game["season"]) &
                        (injuries["week"] < game["week"])
                    ]
                else:
                    # Last resort: use same season (could leak future, but better than nothing)
                    logger.warning(f"No date/week info for injuries, using entire season {game['season']} (potential future leakage)")
                    recent_injuries = injuries[injuries["season"] == game["season"]]
            
            # Count injuries by team
            for team in [game["home_team"], game["away_team"]]:
                team_injuries = recent_injuries[recent_injuries["team"] == team]
                metrics_list.append({
                    "game_id": game["game_id"],
                    "team": team,
                    "injury_count": len(team_injuries),
                    "roster_changes": len(team_injuries) if "practice_status" in team_injuries.columns else 0
                })
        
        return pd.DataFrame(metrics_list)

    def get_feature_names(self) -> List[str]:
        return [
            "injury_count_home",
            "injury_count_away",
            "roster_changes_home",
            "roster_changes_away",
        ]

