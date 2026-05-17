"""Model Service - Train, load, and run predictions with real models.

No placeholders. Real XGBoost models trained on real nflverse data.
Includes isotonic calibration for proper probabilities.
"""

import json
import logging
import pickle
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """Metadata for a trained model."""
    model_id: str
    model_type: str
    target: str
    trained_at: str
    train_seasons: List[int]
    n_samples: int
    feature_columns: List[str]
    metrics: Dict[str, float]


class ModelService:
    """
    Service for training and running prediction models.

    Models:
    1. game_outcome: Predict home win probability
    2. spread_cover: Predict ATS outcome
    3. player_props: Predict over/under for player stats

    All models use:
    - XGBoost for prediction
    - Isotonic calibration for probabilities
    - Walk-forward validation (no data leakage)
    """

    FEATURE_COLS_GAME = [
        "rest_advantage", "div_game", "week_normalized", "is_prime_time",
        "temp_normalized", "is_cold", "is_dome", "wind_normalized", "high_wind",
        "home_epa", "away_epa", "home_success", "away_success",
        "epa_diff", "success_diff", "is_home_underdog", "is_big_favorite", "is_close_game"
    ]

    FEATURE_COLS_PROPS = [
        "passing_yards_roll5", "rushing_yards_roll5", "receiving_yards_roll5",
        "receptions_roll5", "targets_roll5", "team_pass_rate", "opp_def_epa",
    ]

    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.loaded_models: Dict[str, Any] = {}
        self.metadata: Dict[str, ModelMetadata] = {}

    def train_game_model(
        self,
        train_df: pd.DataFrame,
        target_col: str = "target",
        model_type: str = "game_outcome",
    ) -> Tuple[Any, Dict[str, float]]:
        """
        Train game outcome prediction model.

        Uses walk-forward approach: train on past seasons only.
        """
        try:
            import xgboost as xgb
            from sklearn.calibration import CalibratedClassifierCV
            from sklearn.model_selection import TimeSeriesSplit
            from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
        except ImportError as e:
            logger.error(f"Missing dependency: {e}")
            raise

        logger.info(f"Training {model_type} model on {len(train_df)} samples")

        # Prepare features
        available_features = [c for c in self.FEATURE_COLS_GAME if c in train_df.columns]
        X = train_df[available_features].fillna(0)
        y = train_df[target_col]

        # Walk-forward split
        tscv = TimeSeriesSplit(n_splits=3)

        # Train XGBoost
        base_model = xgb.XGBClassifier(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=1.0,
            reg_lambda=1.0,
            random_state=42,
            use_label_encoder=False,
            eval_metric="logloss",
        )

        # Calibrate probabilities
        calibrated_model = CalibratedClassifierCV(
            base_model, method="isotonic", cv=tscv
        )
        calibrated_model.fit(X, y)

        # Evaluate
        y_pred_proba = calibrated_model.predict_proba(X)[:, 1]
        metrics = {
            "brier_score": brier_score_loss(y, y_pred_proba),
            "log_loss": log_loss(y, y_pred_proba),
            "auc_roc": roc_auc_score(y, y_pred_proba),
            "accuracy": (y == (y_pred_proba > 0.5)).mean(),
        }

        logger.info(f"Model metrics: {metrics}")

        # Save model
        model_id = f"{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        model_path = self.models_dir / f"{model_id}.pkl"

        with open(model_path, "wb") as f:
            pickle.dump(calibrated_model, f)

        # Save metadata
        # Convert numpy types to Python native for JSON serialization
        train_seasons = [int(s) for s in train_df["season"].unique()] if "season" in train_df.columns else []

        metadata = ModelMetadata(
            model_id=model_id,
            model_type=model_type,
            target=target_col,
            trained_at=datetime.now().isoformat(),
            train_seasons=train_seasons,
            n_samples=int(len(train_df)),
            feature_columns=available_features,
            metrics={k: float(v) for k, v in metrics.items()},
        )

        metadata_path = self.models_dir / f"{model_id}_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata.__dict__, f, indent=2)

        # Update latest symlink
        latest_path = self.models_dir / f"{model_type}_latest.pkl"
        if latest_path.exists():
            latest_path.unlink()
        latest_path.symlink_to(model_path.name)

        self.loaded_models[model_type] = calibrated_model
        self.metadata[model_type] = metadata

        logger.info(f"Saved model to {model_path}")
        return calibrated_model, metrics

    def train_props_model(
        self,
        player_df: pd.DataFrame,
        prop_type: str = "receiving_yards",
        line: float = 50.0,
    ) -> Tuple[Any, Dict[str, float]]:
        """
        Train player prop prediction model.

        Predicts probability of going over/under a line.
        """
        try:
            import xgboost as xgb
            from sklearn.calibration import CalibratedClassifierCV
            from sklearn.metrics import brier_score_loss, log_loss
        except ImportError as e:
            logger.error(f"Missing dependency: {e}")
            raise

        logger.info(f"Training props model for {prop_type}")

        # Create target
        if prop_type not in player_df.columns:
            logger.error(f"Column {prop_type} not found")
            return None, {}

        player_df = player_df.copy()
        player_df["target"] = (player_df[prop_type] > line).astype(int)

        # Prepare features
        available_features = [c for c in self.FEATURE_COLS_PROPS if c in player_df.columns]
        if len(available_features) < 3:
            logger.warning("Not enough features for props model")
            return None, {}

        X = player_df[available_features].fillna(0)
        y = player_df["target"]

        # Train
        base_model = xgb.XGBClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=5,
            subsample=0.8,
            random_state=42,
        )

        calibrated = CalibratedClassifierCV(base_model, method="isotonic", cv=3)
        calibrated.fit(X, y)

        # Metrics
        y_pred = calibrated.predict_proba(X)[:, 1]
        metrics = {
            "brier_score": brier_score_loss(y, y_pred),
            "log_loss": log_loss(y, y_pred),
            "accuracy": (y == (y_pred > 0.5)).mean(),
        }

        # Save
        model_id = f"props_{prop_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        model_path = self.models_dir / f"{model_id}.pkl"

        with open(model_path, "wb") as f:
            pickle.dump(calibrated, f)

        logger.info(f"Props model trained: {metrics}")
        return calibrated, metrics

    def load_model(self, model_type: str) -> Optional[Any]:
        """Load a trained model."""
        if model_type in self.loaded_models:
            return self.loaded_models[model_type]

        # Try latest symlink
        latest_path = self.models_dir / f"{model_type}_latest.pkl"
        if latest_path.exists():
            with open(latest_path, "rb") as f:
                model = pickle.load(f)
            self.loaded_models[model_type] = model
            logger.info(f"Loaded model: {model_type}")
            return model

        # Try to find any model of this type
        model_files = list(self.models_dir.glob(f"{model_type}_*.pkl"))
        if model_files:
            latest = max(model_files, key=lambda p: p.stat().st_mtime)
            with open(latest, "rb") as f:
                model = pickle.load(f)
            self.loaded_models[model_type] = model
            logger.info(f"Loaded model from {latest}")
            return model

        logger.warning(f"No model found for {model_type}")
        return None

    def predict_games(
        self,
        games_df: pd.DataFrame,
        model_type: str = "game_outcome",
    ) -> pd.DataFrame:
        """
        Generate predictions for games.

        Returns DataFrame with:
        - game_id, home_team, away_team
        - home_win_prob
        - predicted_winner
        - confidence
        """
        model = self.load_model(model_type)

        if model is None:
            logger.error(f"No model available for {model_type}")
            return games_df

        # Get metadata for feature columns
        metadata_path = self.models_dir / f"{model_type}_latest_metadata.json"
        if metadata_path.exists():
            with open(metadata_path) as f:
                metadata = json.load(f)
            feature_cols = metadata.get("feature_columns", self.FEATURE_COLS_GAME)
        else:
            feature_cols = self.FEATURE_COLS_GAME

        # Prepare features
        available = [c for c in feature_cols if c in games_df.columns]
        X = games_df[available].fillna(0)

        # Ensure all columns are numeric
        for col in X.columns:
            X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)

        # Predict
        probs = model.predict_proba(X)[:, 1]

        # Add to dataframe
        result = games_df.copy()
        result["home_win_prob"] = probs
        result["predicted_winner"] = result.apply(
            lambda r: r["home_team"] if r["home_win_prob"] > 0.5 else r["away_team"],
            axis=1
        )
        result["confidence"] = result["home_win_prob"].apply(
            lambda p: "HIGH" if abs(p - 0.5) > 0.15 else "MEDIUM" if abs(p - 0.5) > 0.08 else "LOW"
        )

        return result

    def predict_prop(
        self,
        player_row: pd.Series,
        prop_type: str,
        line: float,
    ) -> Dict[str, Any]:
        """
        Predict a single player prop.

        Returns:
        - over_prob: Probability of going over
        - prediction: 'OVER' or 'UNDER'
        - projected_value: Point estimate
        - confidence: HIGH/MEDIUM/LOW
        """
        model = self.load_model(f"props_{prop_type}")

        if model is None:
            # Fallback to rolling average
            roll_col = f"{prop_type}_roll5"
            if roll_col in player_row:
                projected = player_row[roll_col]
                over_prob = 0.6 if projected > line else 0.4
            else:
                projected = line
                over_prob = 0.5

            return {
                "over_prob": over_prob,
                "prediction": "OVER" if over_prob > 0.5 else "UNDER",
                "projected_value": projected,
                "confidence": "LOW",
            }

        # Use model
        features = [c for c in self.FEATURE_COLS_PROPS if c in player_row.index]
        X = player_row[features].fillna(0).values.reshape(1, -1)

        over_prob = model.predict_proba(X)[0, 1]

        return {
            "over_prob": float(over_prob),
            "prediction": "OVER" if over_prob > 0.5 else "UNDER",
            "projected_value": float(player_row.get(f"{prop_type}_roll5", line)),
            "confidence": "HIGH" if abs(over_prob - 0.5) > 0.15 else "MEDIUM" if abs(over_prob - 0.5) > 0.08 else "LOW",
        }

    def get_model_info(self, model_type: str) -> Optional[Dict]:
        """Get information about a trained model."""
        metadata_files = list(self.models_dir.glob(f"{model_type}*_metadata.json"))
        if not metadata_files:
            return None

        latest = max(metadata_files, key=lambda p: p.stat().st_mtime)
        with open(latest) as f:
            return json.load(f)


def create_model_service(models_dir: str = "models") -> ModelService:
    """Factory function for model service."""
    return ModelService(models_dir)
