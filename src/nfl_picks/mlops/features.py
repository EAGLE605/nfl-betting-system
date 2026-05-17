"""Feature pipeline for data refresh and processing."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd


@dataclass
class FeatureConfig:
    """Configuration for feature pipeline."""
    data_dir: Path = Path("data/raw")
    cache_ttl_hours: int = 24
    rolling_epa_window: int = 5
    rolling_ngs_window: int = 3
    min_week: int = 4


class FeaturePipeline:
    """Pipeline for loading and computing features."""

    def __init__(self, config: Optional[FeatureConfig] = None):
        self.config = config or FeatureConfig()
        self._pbp: Optional[pd.DataFrame] = None
        self._ngs: Optional[pd.DataFrame] = None
        self._last_refresh: Optional[datetime] = None

    @property
    def needs_refresh(self) -> bool:
        """Check if data needs refresh."""
        if self._last_refresh is None:
            return True
        ttl = timedelta(hours=self.config.cache_ttl_hours)
        return datetime.now() - self._last_refresh > ttl

    def refresh(self, seasons: list[int] = None) -> None:
        """Refresh data from nflverse."""
        try:
            import nfl_data_py as nfl
        except ImportError:
            raise ImportError("nfl_data_py required: pip install nfl_data_py")

        seasons = seasons or [2022, 2023, 2024, 2025]

        pbp_path = self.config.data_dir / "pbp_4seasons.parquet"
        if pbp_path.exists():
            self._pbp = pd.read_parquet(pbp_path)
        else:
            print(f"Downloading play-by-play for {seasons}...")
            self._pbp = nfl.import_pbp_data(seasons)
            self.config.data_dir.mkdir(parents=True, exist_ok=True)
            self._pbp.to_parquet(pbp_path)

        print(f"Loading Next Gen Stats for {seasons}...")
        self._ngs = nfl.import_ngs_data("rushing", seasons)

        self._last_refresh = datetime.now()

    def get_epa_features(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Compute EPA rolling features."""
        if self._pbp is None:
            self.refresh()

        pbp = self._pbp

        games = pbp.groupby(
            ["game_id", "season", "week", "home_team", "away_team"]
        ).agg({
            "total_home_score": "max",
            "total_away_score": "max",
        }).reset_index()
        games.columns = [
            "game_id", "season", "week", "home_team", "away_team",
            "home_score", "away_score"
        ]
        games = games.dropna(subset=["home_score", "away_score"])
        games["home_win"] = (games["home_score"] > games["away_score"]).astype(int)

        plays = pbp[pbp["play_type"].isin(["pass", "run"]) & pbp["epa"].notna()]
        team_epa = plays.groupby(["game_id", "posteam"])["epa"].mean().reset_index()
        team_epa.columns = ["game_id", "team", "epa"]

        game_info = games[["game_id", "season", "week"]].drop_duplicates()
        team_epa = team_epa.merge(game_info, on="game_id")
        team_epa = team_epa.sort_values(["team", "season", "week"])

        team_epa["epa_roll"] = team_epa.groupby("team")["epa"].transform(
            lambda x: x.shift(1).rolling(
                self.config.rolling_epa_window, min_periods=1
            ).mean()
        )

        return games, team_epa

    def get_ngs_features(self) -> pd.DataFrame:
        """Compute Next Gen Stats rolling features."""
        if self._ngs is None:
            self.refresh()

        ngs = self._ngs

        rb_stats = ngs.groupby(["season", "week", "team_abbr"]).agg({
            "efficiency": "mean",
            "percent_attempts_gte_eight_defenders": "mean",
            "avg_time_to_los": "mean",
            "avg_rush_yards": "mean",
        }).reset_index()
        rb_stats.columns = [
            "season", "week", "team",
            "rb_efficiency", "rb_stacked_box_pct", "rb_time_to_los", "rb_ypc"
        ]
        rb_stats = rb_stats.sort_values(["team", "season", "week"])

        for col in ["rb_efficiency", "rb_stacked_box_pct", "rb_time_to_los", "rb_ypc"]:
            rb_stats[f"{col}_roll"] = rb_stats.groupby("team")[col].transform(
                lambda x: x.shift(1).rolling(
                    self.config.rolling_ngs_window, min_periods=1
                ).mean()
            )

        return rb_stats

    def build_features(
        self,
        season: int,
        week: int,
        include_target: bool = True,
    ) -> pd.DataFrame:
        """Build feature matrix for a specific week."""
        games, team_epa = self.get_epa_features()
        rb_stats = self.get_ngs_features()

        roll_cols = [
            "rb_efficiency_roll", "rb_stacked_box_pct_roll",
            "rb_time_to_los_roll", "rb_ypc_roll"
        ]

        home_rb = rb_stats[["season", "week", "team"] + roll_cols].copy()
        home_rb.columns = ["season", "week", "home_team"] + [f"home_{c}" for c in roll_cols]

        away_rb = rb_stats[["season", "week", "team"] + roll_cols].copy()
        away_rb.columns = ["season", "week", "away_team"] + [f"away_{c}" for c in roll_cols]

        df = games.merge(home_rb, on=["season", "week", "home_team"], how="left")
        df = df.merge(away_rb, on=["season", "week", "away_team"], how="left")

        home_epa = team_epa[["game_id", "team", "epa_roll"]].rename(
            columns={"team": "home_team", "epa_roll": "home_epa"}
        )
        away_epa = team_epa[["game_id", "team", "epa_roll"]].rename(
            columns={"team": "away_team", "epa_roll": "away_epa"}
        )

        df = df.merge(home_epa, on=["game_id", "home_team"], how="left")
        df = df.merge(away_epa, on=["game_id", "away_team"], how="left")

        df["epa_diff"] = df["home_epa"].fillna(0) - df["away_epa"].fillna(0)
        for col in roll_cols:
            df[f"diff_{col}"] = df[f"home_{col}"].fillna(0) - df[f"away_{col}"].fillna(0)

        week_df = df[(df["season"] == season) & (df["week"] == week)]

        if not include_target:
            week_df = week_df.drop(columns=["home_win", "home_score", "away_score"], errors="ignore")

        return week_df
