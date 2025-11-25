"""Prediction generator for backtesting.

Generates model predictions on historical data for backtesting.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from src.features.pipeline import FeaturePipeline
from src.features.elo import EloFeatures
from src.features.encoding import CategoricalEncodingFeatures
from src.features.epa import EPAFeatures
from src.features.form import FormFeatures
from src.features.line import LineFeatures
from src.features.referee import RefereeFeatures
from src.features.rest_days import RestDaysFeatures
from src.features.weather import WeatherFeatures
from src.swarms.model_loader import ModelLoader

logger = logging.getLogger(__name__)


class PredictionGenerator:
    """Generate predictions on historical data for backtesting."""

    def __init__(self):
        """Initialize prediction generator."""
        self.model_loader = ModelLoader()

    def generate_predictions(
        self,
        schedules_df: pd.DataFrame,
        strategy: Dict[str, Any],
        pbp_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Generate predictions for all games in schedules.

        Args:
            schedules_df: Historical game schedules
            strategy: Strategy config with:
                - model_name: Name of model to use
                - model_config: Optional model parameters
            pbp_df: Optional play-by-play data for EPA features

        Returns:
            DataFrame with columns:
                - game_id, gameday, home_team, away_team
                - pred_prob: Model probability of home win (0-1)
                - actual: Actual outcome (1=home win, 0=away win)
                - odds: Decimal odds for home team
        """
        model_name = strategy.get("model_name", "xgboost_model")

        logger.info(
            f"Generating predictions for {len(schedules_df)} games using {model_name}"
        )

        # Load model
        try:
            model = self.model_loader.load_model(model_name)
        except FileNotFoundError:
            logger.error(f"Model not found: {model_name}")
            # Try to get any available model
            available = self.model_loader.list_available_models()
            if not available:
                raise FileNotFoundError("No trained models available for backtesting")
            model_name = available[0]
            logger.warning(f"Using fallback model: {model_name}")
            model = self.model_loader.load_model(model_name)

        # Build features
        logger.info("Building features...")
        features_df = self._build_features(schedules_df, pbp_df)

        # Get model's expected features
        if hasattr(model, "feature_names"):
            expected_features = model.feature_names
        elif hasattr(model, "feature_name_"):  # LightGBM
            expected_features = model.feature_name_
        elif hasattr(model, "models"):  # Ensemble
            expected_features = model.models[0].feature_names
        else:
            logger.warning("Model doesn't expose feature names, using all available")
            expected_features = [
                col
                for col in features_df.columns
                if col
                not in [
                    "game_id",
                    "gameday",
                    "home_team",
                    "away_team",
                    "home_score",
                    "away_score",
                    "result",
                    "season",
                ]
            ]

        # Handle missing features
        missing_features = set(expected_features) - set(features_df.columns)
        if missing_features:
            logger.warning(
                f"Missing {len(missing_features)} features, filling with 0"
            )
            for feat in missing_features:
                features_df[feat] = 0

        # Prepare feature matrix
        X = features_df[expected_features]

        # Generate predictions
        logger.info("Generating predictions...")
        if hasattr(model, "predict_proba"):
            pred_probs = model.predict_proba(X)[:, 1]
        else:
            pred_probs = model.predict(X)

        # Build prediction DataFrame
        predictions_df = pd.DataFrame(
            {
                "game_id": features_df.get("game_id", range(len(features_df))),
                "gameday": features_df["gameday"],
                "home_team": features_df["home_team"],
                "away_team": features_df["away_team"],
                "pred_prob": pred_probs,
            }
        )

        # Add actual outcomes
        predictions_df = self._add_actual_outcomes(predictions_df, features_df)

        # Add odds
        predictions_df = self._add_odds(predictions_df, features_df)

        # Filter to only games with complete data
        complete_mask = (
            predictions_df["actual"].notna()
            & predictions_df["odds"].notna()
            & (predictions_df["odds"] > 1.0)
        )
        predictions_df = predictions_df[complete_mask].copy()

        logger.info(
            f"Generated {len(predictions_df)} predictions "
            f"(filtered from {len(features_df)} total games)"
        )

        return predictions_df

    def _build_features(
        self, schedules_df: pd.DataFrame, pbp_df: Optional[pd.DataFrame]
    ) -> pd.DataFrame:
        """Build features for games."""
        # Initialize feature pipeline
        pipeline = FeaturePipeline(pbp_data=pbp_df)

        # Add feature builders
        pipeline.add_builder(LineFeatures())
        pipeline.add_builder(RestDaysFeatures())
        pipeline.add_builder(EloFeatures())
        pipeline.add_builder(WeatherFeatures())
        pipeline.add_builder(FormFeatures())
        pipeline.add_builder(CategoricalEncodingFeatures())
        pipeline.add_builder(RefereeFeatures())

        if pbp_df is not None:
            pipeline.add_builder(EPAFeatures())

        # Build features
        features_df = pipeline.build_features(schedules_df, validate=False)

        return features_df

    def _add_actual_outcomes(
        self, predictions_df: pd.DataFrame, features_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Add actual game outcomes.

        Args:
            predictions_df: Predictions DataFrame
            features_df: Features DataFrame (may contain scores)

        Returns:
            DataFrame with 'actual' column (1=home win, 0=away win)
        """
        # Try to get actual outcomes from features_df
        if "home_score" in features_df.columns and "away_score" in features_df.columns:
            actual = (features_df["home_score"] > features_df["away_score"]).astype(int)
            predictions_df["actual"] = actual.values
        elif "result" in features_df.columns:
            # result might be 1 for home win, 0 for away win
            predictions_df["actual"] = features_df["result"].values
        else:
            logger.warning(
                "No actual outcomes found in data, predictions incomplete"
            )
            predictions_df["actual"] = np.nan

        return predictions_df

    def _add_odds(
        self, predictions_df: pd.DataFrame, features_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Add betting odds.

        Args:
            predictions_df: Predictions DataFrame
            features_df: Features DataFrame (may contain spread_line)

        Returns:
            DataFrame with 'odds' column (decimal odds)
        """
        # Try to derive odds from spread line
        if "spread_line" in features_df.columns:
            spread = features_df["spread_line"].values

            # Convert spread to implied probability to odds
            # Simplified: home team favored by X points
            # This is a rough approximation
            implied_prob = self._spread_to_probability(spread)
            odds = 1.0 / implied_prob
            predictions_df["odds"] = odds
        else:
            logger.warning("No odds/spread data found, using default odds of 2.0")
            predictions_df["odds"] = 2.0

        return predictions_df

    def _spread_to_probability(self, spread: np.ndarray) -> np.ndarray:
        """
        Convert point spread to implied probability.

        Args:
            spread: Point spread (negative = home favored)

        Returns:
            Implied probability of home win
        """
        # Rough conversion: each point ~ 3-4% win probability change
        # NFL average spread of -3 => ~60% home win probability
        base_prob = 0.50  # 50-50 on neutral field
        prob = base_prob + (spread * -0.03)  # Negative spread favors home

        # Clip to reasonable range
        prob = np.clip(prob, 0.1, 0.9)

        return prob
