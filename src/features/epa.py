"""EPA (Expected Points Added) features.

Aggregates EPA from play-by-play data to create team performance metrics.
"""

from .base import FeatureBuilder
import pandas as pd
import numpy as np
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class EPAFeatures(FeatureBuilder):
    """
    EPA features from play-by-play data.

    Creates:
    - epa_offense_home/away: Offensive EPA per play (rolling window)
    - epa_defense_home/away: Defensive EPA allowed per play (rolling window)
    - epa_success_rate_home/away: Success rate (EPA > 0) (rolling window)
    - epa_explosive_rate_home/away: Explosive play rate (EPA > 1.5) (rolling window)
    """

    def __init__(self, pbp_data: Optional[pd.DataFrame] = None, window=3):
        """
        Initialize EPA features.

        Args:
            pbp_data: Play-by-play DataFrame
            window: Rolling window size for averages (default: 3 games)
        """
        self.pbp_data = pbp_data
        self.window = window

    def get_required_columns(self) -> List[str]:
        return ["game_id", "gameday", "season", "home_team", "away_team"]

    def build(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build EPA features."""
        self.validate_prerequisites(df)

        if self.pbp_data is None:
            logger.warning("No play-by-play data provided, skipping EPA features")
            # Add dummy columns
            for col in self.get_feature_names():
                df[col] = 0.0
            return df

        logger.info("Building EPA features...")

        # Ensure datetime
        df["gameday"] = pd.to_datetime(df["gameday"])
        df = df.sort_values(["season", "gameday"]).copy()

        # Calculate EPA metrics per game for each team
        epa_metrics = self._calculate_epa_metrics()

        # Calculate rolling averages for each team
        df = self._add_rolling_features(df, epa_metrics)

        # Fill missing values (first games of season)
        for col in self.get_feature_names():
            df[col] = df[col].fillna(0)

        logger.info(f"✓ EPA features created: {len(self.get_feature_names())} features")

        return df

    def _calculate_epa_metrics(self) -> pd.DataFrame:
        """Calculate EPA metrics per game for each team."""
        pbp = self.pbp_data.copy()

        # Filter out plays without EPA or team info
        pbp = pbp.dropna(subset=["epa", "posteam", "defteam"])

        # Offensive metrics: when team has the ball
        off_metrics = pbp.groupby(["game_id", "posteam"]).agg(
            epa_mean=("epa", "mean"),
            epa_sum=("epa", "sum"),
            plays=("epa", "count"),
            success_rate=("epa", lambda x: (x > 0).mean()),
            explosive_rate=("epa", lambda x: (x > 1.5).mean()),
        ).reset_index()
        off_metrics.columns = [
            "game_id", "team", "epa_offense", "epa_offense_total",
            "plays_offense", "success_rate_offense", "explosive_rate_offense"
        ]

        # Defensive metrics: when team is on defense (negative EPA is good)
        def_metrics = pbp.groupby(["game_id", "defteam"]).agg(
            epa_mean=("epa", "mean"),
            epa_sum=("epa", "sum"),
            plays=("epa", "count"),
            success_rate=("epa", lambda x: (x > 0).mean()),  # Offense success = defense failure
            explosive_rate=("epa", lambda x: (x > 1.5).mean()),
        ).reset_index()
        def_metrics.columns = [
            "game_id", "team", "epa_defense", "epa_defense_total",
            "plays_defense", "success_rate_defense", "explosive_rate_defense"
        ]

        # Merge offensive and defensive metrics
        metrics = off_metrics.merge(
            def_metrics, on=["game_id", "team"], how="outer"
        ).fillna(0)

        return metrics

    def _add_rolling_features(self, df: pd.DataFrame, epa_metrics: pd.DataFrame) -> pd.DataFrame:
        """Add rolling EPA features for home and away teams."""
        # Merge game dates into metrics
        game_dates = df[["game_id", "gameday", "season", "home_team", "away_team"]].copy()
        
        # Create team-game level dataframe with all metrics
        team_games_list = []
        for _, row in game_dates.iterrows():
            # Home team metrics
            home_metrics = epa_metrics[epa_metrics["game_id"] == row["game_id"]]
            home_metrics = home_metrics[home_metrics["team"] == row["home_team"]]
            if not home_metrics.empty:
                team_games_list.append({
                    "game_id": row["game_id"],
                    "gameday": row["gameday"],
                    "season": row["season"],
                    "team": row["home_team"],
                    "epa_offense": home_metrics.iloc[0]["epa_offense"],
                    "epa_defense": home_metrics.iloc[0]["epa_defense"],
                    "success_rate_offense": home_metrics.iloc[0]["success_rate_offense"],
                    "explosive_rate_offense": home_metrics.iloc[0]["explosive_rate_offense"],
                })
            
            # Away team metrics
            away_metrics = epa_metrics[epa_metrics["game_id"] == row["game_id"]]
            away_metrics = away_metrics[away_metrics["team"] == row["away_team"]]
            if not away_metrics.empty:
                team_games_list.append({
                    "game_id": row["game_id"],
                    "gameday": row["gameday"],
                    "season": row["season"],
                    "team": row["away_team"],
                    "epa_offense": away_metrics.iloc[0]["epa_offense"],
                    "epa_defense": away_metrics.iloc[0]["epa_defense"],
                    "success_rate_offense": away_metrics.iloc[0]["success_rate_offense"],
                    "explosive_rate_offense": away_metrics.iloc[0]["explosive_rate_offense"],
                })
        
        team_games = pd.DataFrame(team_games_list)
        if team_games.empty:
            logger.warning("No team-game metrics found, returning zeros")
            for col in self.get_feature_names():
                df[col] = 0.0
            return df
        
        # Sort by team, season, and date
        team_games = team_games.sort_values(["team", "season", "gameday"])
        
        # Calculate rolling averages per team per season (shift to avoid lookahead)
        for metric in ["epa_offense", "epa_defense", "success_rate_offense", "explosive_rate_offense"]:
            team_games[f"{metric}_rolling"] = (
                team_games.groupby(["team", "season"])[metric]
                .shift(1)  # Avoid lookahead bias
                .rolling(window=self.window, min_periods=1)
                .mean()
                .reset_index(0, drop=True)
            )
        
        # Merge rolling features back to main dataframe
        # Home team features
        home_rolling = team_games[["game_id", "team", "epa_offense_rolling", "epa_defense_rolling",
                                  "success_rate_offense_rolling", "explosive_rate_offense_rolling"]]
        home_rolling = home_rolling.rename(columns={
            "epa_offense_rolling": "epa_offense_home",
            "epa_defense_rolling": "epa_defense_home",
            "success_rate_offense_rolling": "epa_success_rate_home",
            "explosive_rate_offense_rolling": "epa_explosive_rate_home",
        })
        df = df.merge(
            home_rolling,
            left_on=["game_id", "home_team"],
            right_on=["game_id", "team"],
            how="left"
        ).drop(columns=["team"])
        
        # Away team features
        away_rolling = team_games[["game_id", "team", "epa_offense_rolling", "epa_defense_rolling",
                                  "success_rate_offense_rolling", "explosive_rate_offense_rolling"]]
        away_rolling = away_rolling.rename(columns={
            "epa_offense_rolling": "epa_offense_away",
            "epa_defense_rolling": "epa_defense_away",
            "success_rate_offense_rolling": "epa_success_rate_away",
            "explosive_rate_offense_rolling": "epa_explosive_rate_away",
        })
        df = df.merge(
            away_rolling,
            left_on=["game_id", "away_team"],
            right_on=["game_id", "team"],
            how="left"
        ).drop(columns=["team"])
        
        return df

    def get_feature_names(self) -> List[str]:
        return [
            "epa_offense_home",
            "epa_defense_home",
            "epa_offense_away",
            "epa_defense_away",
            "epa_success_rate_home",
            "epa_explosive_rate_home",
            "epa_success_rate_away",
            "epa_explosive_rate_away",
        ]
