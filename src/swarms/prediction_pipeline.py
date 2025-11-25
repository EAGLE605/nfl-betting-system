"""Prediction pipeline for swarm agents.

Handles feature engineering and model prediction for live games.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from src.features.elo import EloFeatures
from src.features.encoding import CategoricalEncodingFeatures
from src.features.epa import EPAFeatures
from src.features.form import FormFeatures
from src.features.line import LineFeatures
from src.features.pipeline import FeaturePipeline
from src.features.referee import RefereeFeatures
from src.features.rest_days import RestDaysFeatures
from src.features.weather import WeatherFeatures
from src.swarms.model_loader import ModelLoader

logger = logging.getLogger(__name__)


class PredictionPipeline:
    """Generate predictions for games using trained models."""

    def __init__(self, model_name: str):
        """
        Initialize prediction pipeline.

        Args:
            model_name: Name of model to load (without .pkl extension)
        """
        self.model_name = model_name
        self.model_loader = ModelLoader()
        self.model = None
        self._feature_pipeline = None

    def _ensure_model_loaded(self):
        """Lazy load model on first use."""
        if self.model is None:
            logger.info(f"Loading model: {self.model_name}")
            self.model = self.model_loader.load_model(self.model_name)

    def _get_feature_pipeline(self, pbp_data: Optional[pd.DataFrame] = None):
        """
        Get or create feature pipeline.

        Args:
            pbp_data: Optional play-by-play data for EPA features

        Returns:
            Configured FeaturePipeline
        """
        if self._feature_pipeline is None:
            self._feature_pipeline = FeaturePipeline(pbp_data=pbp_data)

            # Add feature builders in order
            self._feature_pipeline.add_builder(LineFeatures())
            self._feature_pipeline.add_builder(RestDaysFeatures())
            self._feature_pipeline.add_builder(EloFeatures())
            self._feature_pipeline.add_builder(WeatherFeatures())
            self._feature_pipeline.add_builder(FormFeatures())
            self._feature_pipeline.add_builder(CategoricalEncodingFeatures())
            self._feature_pipeline.add_builder(RefereeFeatures())

            # Add EPA if play-by-play available
            if pbp_data is not None:
                self._feature_pipeline.add_builder(EPAFeatures())

        return self._feature_pipeline

    def predict(self, game: Dict) -> Dict:
        """
        Generate prediction for a single game.

        Args:
            game: Dictionary with game info:
                - home_team: str
                - away_team: str
                - gameday: str (YYYY-MM-DD)
                - spread_line: float (optional)
                - total_line: float (optional)

        Returns:
            Dict with:
                - pick: "home" or "away"
                - confidence: float (0-1)
                - pred_prob: float (probability of home win)
                - model_name: str
        """
        self._ensure_model_loaded()

        # Convert game dict to DataFrame
        game_df = pd.DataFrame([game])

        # Build features
        try:
            features_df = self._build_features(game_df)

            # Get model's expected features
            if hasattr(self.model, "feature_names"):
                expected_features = self.model.feature_names
            elif hasattr(self.model, "feature_name_"):  # LightGBM
                expected_features = self.model.feature_name_
            elif hasattr(self.model, "models"):  # Ensemble
                # Use first model's features
                expected_features = self.model.models[0].feature_names
            else:
                logger.warning("Model doesn't expose feature names, using all features")
                expected_features = features_df.columns.tolist()

            # Select only the features the model was trained on
            # Fill missing features with 0
            missing_features = set(expected_features) - set(features_df.columns)
            if missing_features:
                logger.warning(f"Missing features (filling with 0): {missing_features}")
                for feat in missing_features:
                    features_df[feat] = 0

            # Ensure correct order
            X = features_df[expected_features]

            # Generate prediction
            if hasattr(self.model, "predict_proba"):
                prob_home = self.model.predict_proba(X)[0, 1]
            else:
                # Fallback to predict
                pred = self.model.predict(X)[0]
                prob_home = float(pred)

            # Determine pick and confidence
            if prob_home >= 0.5:
                pick = "home"
                confidence = prob_home
            else:
                pick = "away"
                confidence = 1 - prob_home

            return {
                "pick": pick,
                "confidence": float(confidence),
                "pred_prob": float(prob_home),
                "model_name": self.model_name,
            }

        except Exception as e:
            logger.error(f"Prediction failed for game: {e}")
            # Return conservative fallback
            return {
                "pick": "home",
                "confidence": 0.51,
                "pred_prob": 0.51,
                "model_name": self.model_name,
                "error": str(e),
            }

    def predict_batch(self, games: List[Dict]) -> List[Dict]:
        """
        Generate predictions for multiple games.

        Args:
            games: List of game dicts

        Returns:
            List of prediction dicts
        """
        predictions = []
        for game in games:
            pred = self.predict(game)
            predictions.append(pred)

        return predictions

    def _build_features(self, game_df: pd.DataFrame) -> pd.DataFrame:
        """
        Build features for games.

        Args:
            game_df: DataFrame with game info

        Returns:
            DataFrame with engineered features
        """
        # Try to load play-by-play for EPA features
        pbp_data = None
        try:
            data_dir = Path("data/raw")
            # Try to load recent season's pbp
            current_season = pd.Timestamp.now().year
            pbp_path = data_dir / f"pbp_{current_season-1}_{current_season}.parquet"
            if pbp_path.exists():
                pbp_data = pd.read_parquet(pbp_path)
        except Exception as e:
            logger.warning(f"Could not load play-by-play data: {e}")

        # Get feature pipeline
        pipeline = self._get_feature_pipeline(pbp_data)

        # Build features
        features_df = pipeline.build_features(game_df, validate=False)

        return features_df

    def get_model_info(self) -> Dict:
        """Get information about loaded model."""
        self._ensure_model_loaded()

        info = {
            "model_name": self.model_name,
            "model_type": type(self.model).__name__,
        }

        if hasattr(self.model, "feature_names"):
            info["num_features"] = len(self.model.feature_names)
            info["feature_names"] = self.model.feature_names[:10]  # First 10

        return info
