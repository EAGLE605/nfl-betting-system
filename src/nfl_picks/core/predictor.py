"""Core prediction engine - the validated V4 RB-NGS model."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler

from .pick import Pick

# Validated feature set from v4_rb_optimized_model.py
FEATURES = [
    "epa_diff",
    "diff_rb_efficiency_roll",
    "diff_rb_stacked_box_pct_roll",
    "diff_rb_time_to_los_roll",
    "diff_rb_ypc_roll",
]

# Optimal threshold from validation: 62% confidence
CONFIDENCE_THRESHOLD = 0.62

# Model performance (validated on 2023-2024, n=317)
MODEL_METRICS = {
    "accuracy": 0.656,
    "roi": 0.253,
    "p_value": 0.0000,
    "sample_size": 317,
    "test_years": [2023, 2024],
}


@dataclass
class PredictorConfig:
    """Configuration for the predictor."""
    data_dir: Path = Path("data/raw")
    min_training_games: int = 100
    rolling_epa_window: int = 5
    rolling_ngs_window: int = 3
    min_week: int = 4  # Need history for rolling features


class Predictor:
    """V4 RB-NGS prediction engine.

    Validated performance:
    - 65.6% accuracy on high-confidence picks
    - +25.3% ROI at -110 odds
    - p < 0.0001 (statistically significant)
    """

    def __init__(self, config: Optional[PredictorConfig] = None):
        self.config = config or PredictorConfig()
        self.model: Optional[GradientBoostingClassifier] = None
        self.scaler: Optional[StandardScaler] = None
        self._pbp: Optional[pd.DataFrame] = None
        self._ngs: Optional[pd.DataFrame] = None

    def load_data(self) -> None:
        """Load play-by-play and Next Gen Stats data."""
        try:
            import nfl_data_py as nfl
        except ImportError:
            raise ImportError("nfl_data_py required: pip install nfl_data_py")

        pbp_path = self.config.data_dir / "pbp_4seasons.parquet"
        if pbp_path.exists():
            self._pbp = pd.read_parquet(pbp_path)
        else:
            print("Downloading play-by-play data...")
            self._pbp = nfl.import_pbp_data([2022, 2023, 2024, 2025])
            self._pbp.to_parquet(pbp_path)

        print("Loading Next Gen Stats...")
        self._ngs = nfl.import_ngs_data("rushing", [2022, 2023, 2024, 2025])

    def _compute_epa_features(self) -> pd.DataFrame:
        """Compute EPA rolling features."""
        pbp = self._pbp
        assert pbp is not None

        # Game outcomes
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

        # Team EPA per game
        plays = pbp[pbp["play_type"].isin(["pass", "run"]) & pbp["epa"].notna()]
        team_epa = plays.groupby(["game_id", "posteam"])["epa"].mean().reset_index()
        team_epa.columns = ["game_id", "team", "epa"]

        # Add season/week for rolling
        game_info = games[["game_id", "season", "week"]].drop_duplicates()
        team_epa = team_epa.merge(game_info, on="game_id")
        team_epa = team_epa.sort_values(["team", "season", "week"])

        # Rolling average (prior games only via shift)
        team_epa["epa_roll"] = team_epa.groupby("team")["epa"].transform(
            lambda x: x.shift(1).rolling(
                self.config.rolling_epa_window, min_periods=1
            ).mean()
        )

        return games, team_epa

    def _compute_ngs_features(self) -> pd.DataFrame:
        """Compute Next Gen Stats rolling features."""
        ngs = self._ngs
        assert ngs is not None

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

        # Rolling averages
        for col in ["rb_efficiency", "rb_stacked_box_pct", "rb_time_to_los", "rb_ypc"]:
            rb_stats[f"{col}_roll"] = rb_stats.groupby("team")[col].transform(
                lambda x: x.shift(1).rolling(
                    self.config.rolling_ngs_window, min_periods=1
                ).mean()
            )

        return rb_stats

    def _build_feature_matrix(
        self,
        games: pd.DataFrame,
        team_epa: pd.DataFrame,
        rb_stats: pd.DataFrame,
    ) -> pd.DataFrame:
        """Build the full feature matrix."""
        roll_cols = [
            "rb_efficiency_roll", "rb_stacked_box_pct_roll",
            "rb_time_to_los_roll", "rb_ypc_roll"
        ]

        # Home team features
        home_rb = rb_stats[["season", "week", "team"] + roll_cols].copy()
        home_rb.columns = ["season", "week", "home_team"] + [f"home_{c}" for c in roll_cols]

        # Away team features
        away_rb = rb_stats[["season", "week", "team"] + roll_cols].copy()
        away_rb.columns = ["season", "week", "away_team"] + [f"away_{c}" for c in roll_cols]

        df = games.merge(home_rb, on=["season", "week", "home_team"], how="left")
        df = df.merge(away_rb, on=["season", "week", "away_team"], how="left")

        # EPA features
        home_epa = team_epa[["game_id", "team", "epa_roll"]].rename(
            columns={"team": "home_team", "epa_roll": "home_epa"}
        )
        away_epa = team_epa[["game_id", "team", "epa_roll"]].rename(
            columns={"team": "away_team", "epa_roll": "away_epa"}
        )

        df = df.merge(home_epa, on=["game_id", "home_team"], how="left")
        df = df.merge(away_epa, on=["game_id", "away_team"], how="left")

        # Create differentials (home - away)
        df["epa_diff"] = df["home_epa"].fillna(0) - df["away_epa"].fillna(0)
        for col in roll_cols:
            df[f"diff_{col}"] = df[f"home_{col}"].fillna(0) - df[f"away_{col}"].fillna(0)

        return df

    def train(self, max_season: int, max_week: int) -> None:
        """Train model on all data before the specified point."""
        if self._pbp is None:
            self.load_data()

        games, team_epa = self._compute_epa_features()
        rb_stats = self._compute_ngs_features()
        df = self._build_feature_matrix(games, team_epa, rb_stats)

        # Filter to training data (before max_season/week)
        train = df[
            (df["season"] < max_season) |
            ((df["season"] == max_season) & (df["week"] < max_week))
        ]
        train = train[train["week"] >= self.config.min_week]
        train = train.dropna(subset=["home_win"])

        if len(train) < self.config.min_training_games:
            raise ValueError(f"Not enough training data: {len(train)} games")

        X = train[FEATURES].fillna(0)
        y = train["home_win"]

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        self.model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.1,
            random_state=42,
        )
        self.model.fit(X_scaled, y)

        print(f"Trained on {len(train)} games")

    def predict_week(self, season: int, week: int) -> list[Pick]:
        """Generate picks for a specific week."""
        if self.model is None:
            self.train(season, week)

        games, team_epa = self._compute_epa_features()
        rb_stats = self._compute_ngs_features()
        df = self._build_feature_matrix(games, team_epa, rb_stats)

        # Get this week's games
        week_games = df[(df["season"] == season) & (df["week"] == week)]

        if len(week_games) == 0:
            return []

        picks = []
        for _, row in week_games.iterrows():
            X = pd.DataFrame([row[FEATURES].fillna(0).values], columns=FEATURES)
            X_scaled = self.scaler.transform(X)

            prob = self.model.predict_proba(X_scaled)[0, 1]

            features = {f: row.get(f, 0) for f in FEATURES}

            pick = Pick.from_prediction(
                game_id=row["game_id"],
                season=int(row["season"]),
                week=int(row["week"]),
                home_team=row["home_team"],
                away_team=row["away_team"],
                home_win_prob=prob,
                features=features,
            )
            picks.append(pick)

        return sorted(picks, key=lambda p: p.confidence, reverse=True)

    def predict_game(
        self,
        home_team: str,
        away_team: str,
        season: int,
        week: int,
    ) -> Pick:
        """Predict a single game."""
        picks = self.predict_week(season, week)
        for pick in picks:
            if pick.home_team == home_team and pick.away_team == away_team:
                return pick
        raise ValueError(f"Game not found: {away_team} @ {home_team}")
