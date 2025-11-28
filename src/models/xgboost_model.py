"""XGBoost model wrapper for NFL betting predictions.

Provides a clean interface for training, evaluation, and persistence
of XGBoost classifiers with NFL-specific defaults.
"""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score

logger = logging.getLogger(__name__)


class XGBoostNFLModel:
    """
    XGBoost classifier wrapper for NFL game prediction.

    Handles training with early stopping, evaluation metrics,
    feature importance, and model persistence.
    """

    def __init__(self, config: Dict):
        """
        Initialize model with configuration.

        Args:
            config: Model configuration dict with 'params' key containing:
                - n_estimators: Number of boosting rounds
                - max_depth: Maximum tree depth
                - learning_rate: Learning rate (eta)
                - early_stopping_rounds: Rounds for early stopping
        """
        self.config = config
        self.params = config.get("params", {})
        self.model: Optional[xgb.XGBClassifier] = None
        self.feature_names: List[str] = []

        # Extract parameters with defaults
        self.n_estimators = self.params.get("n_estimators", 200)
        self.max_depth = self.params.get("max_depth", 6)
        self.learning_rate = self.params.get("learning_rate", 0.05)
        self.early_stopping_rounds = self.params.get("early_stopping_rounds", 10)

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
    ) -> None:
        """
        Train the XGBoost model.

        Args:
            X_train: Training features
            y_train: Training target (0/1)
            X_val: Validation features for early stopping
            y_val: Validation target
        """
        logger.info(f"Training XGBoost with {len(X_train)} samples...")
        logger.info(f"Parameters: n_estimators={self.n_estimators}, "
                    f"max_depth={self.max_depth}, lr={self.learning_rate}")

        # Store feature names
        self.feature_names = X_train.columns.tolist()

        # Initialize model
        self.model = xgb.XGBClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            objective="binary:logistic",
            eval_metric="logloss",
            early_stopping_rounds=self.early_stopping_rounds,
            random_state=42,
            n_jobs=-1,
            verbosity=0,
        )

        # Prepare eval set
        eval_set = None
        if X_val is not None and y_val is not None:
            eval_set = [(X_val, y_val)]
            logger.info(f"Using {len(X_val)} validation samples for early stopping")

        # Train
        self.model.fit(
            X_train,
            y_train,
            eval_set=eval_set,
            verbose=False,
        )

        # Log best iteration if early stopping used
        if eval_set and hasattr(self.model, "best_iteration"):
            logger.info(f"Best iteration: {self.model.best_iteration}")

        logger.info("Training complete")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict class labels.

        Args:
            X: Features

        Returns:
            Binary predictions (0 or 1)
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        # Ensure column order matches training
        X = self._align_features(X)
        return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict class probabilities.

        Args:
            X: Features

        Returns:
            Probability of class 1 (home win)
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        X = self._align_features(X)
        proba = self.model.predict_proba(X)

        # Return probability of positive class
        if proba.ndim == 2:
            return proba[:, 1]
        return proba

    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """
        Evaluate model on test data.

        Args:
            X: Test features
            y: True labels

        Returns:
            Dict with accuracy, brier_score, log_loss, roc_auc
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        X = self._align_features(X)

        # Get predictions
        y_pred = self.model.predict(X)
        y_proba = self.predict_proba(X)

        # Calculate metrics
        metrics = {
            "accuracy": accuracy_score(y, y_pred),
            "brier_score": brier_score_loss(y, y_proba),
            "log_loss": log_loss(y, y_proba),
            "roc_auc": roc_auc_score(y, y_proba),
        }

        return metrics

    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance scores.

        Returns:
            Dict mapping feature name to importance score
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        importance = self.model.feature_importances_
        return dict(zip(self.feature_names, importance))

    def save(self, filepath: str) -> None:
        """
        Save model to JSON file.

        Args:
            filepath: Path to save model (should end in .json)
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        # Save the underlying booster to JSON
        self.model.save_model(filepath)
        logger.info(f"Model saved to {filepath}")

        # Also save feature names alongside
        import json
        meta_path = filepath.replace(".json", "_meta.json")
        with open(meta_path, "w") as f:
            json.dump({
                "feature_names": self.feature_names,
                "config": self.config,
            }, f, indent=2)
        logger.info(f"Metadata saved to {meta_path}")

    @classmethod
    def load(cls, filepath: str) -> "XGBoostNFLModel":
        """
        Load model from JSON file.

        Args:
            filepath: Path to saved model

        Returns:
            Loaded XGBoostNFLModel instance
        """
        import json

        # Load metadata
        meta_path = filepath.replace(".json", "_meta.json")
        try:
            with open(meta_path, "r") as f:
                meta = json.load(f)
            config = meta.get("config", {"params": {}})
            feature_names = meta.get("feature_names", [])
        except FileNotFoundError:
            config = {"params": {}}
            feature_names = []

        # Create instance
        instance = cls(config)
        instance.feature_names = feature_names

        # Load model
        instance.model = xgb.XGBClassifier()
        instance.model.load_model(filepath)

        logger.info(f"Model loaded from {filepath}")
        return instance

    def _align_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """Ensure features are in correct order."""
        if self.feature_names:
            # Add missing columns with zeros
            for col in self.feature_names:
                if col not in X.columns:
                    X = X.copy()
                    X[col] = 0

            # Select and order columns
            return X[self.feature_names]
        return X
