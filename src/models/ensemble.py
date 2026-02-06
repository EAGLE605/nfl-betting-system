"""Stacked ensemble model for NFL betting predictions.

Architecture based on peer-reviewed research:
- "Stacked ensemble model for NBA game outcome prediction analysis"
  (Nature Scientific Reports, 2025)
- Walsh & Joshi (2024) calibration-first approach

Base learners: XGBoost, LightGBM, CatBoost, RandomForest, GradientBoosting
Meta-learner: MLP or LogisticRegression (calibration-optimized)
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    GradientBoostingClassifier,
    RandomForestClassifier,
    StackingClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import cross_val_predict
from sklearn.neural_network import MLPClassifier

logger = logging.getLogger(__name__)


class StackedEnsembleModel:
    """
    Stacked ensemble with heterogeneous base learners and MLP meta-learner.

    Research shows ensemble stacking outperforms single models for sports
    prediction, particularly when optimizing for calibration over accuracy.
    """

    def __init__(self, config: Dict):
        """
        Initialize ensemble with configuration.

        Args:
            config: Model configuration dict
        """
        self.config = config
        self.params = config.get("params", {})
        self.ensemble: Optional[StackingClassifier] = None
        self.feature_names: List[str] = []
        self.base_learner_weights: Dict[str, float] = {}

        # Build base learners
        self.base_learners = self._build_base_learners()
        self.meta_learner = self._build_meta_learner()

    def _build_base_learners(self) -> List[Tuple[str, object]]:
        """Build diverse base learner ensemble."""
        learners = []

        # XGBoost - proven top performer
        try:
            import xgboost as xgb
            learners.append((
                "xgboost",
                xgb.XGBClassifier(
                    n_estimators=self.params.get("n_estimators", 200),
                    max_depth=self.params.get("max_depth", 6),
                    learning_rate=self.params.get("learning_rate", 0.05),
                    objective="binary:logistic",
                    eval_metric="logloss",
                    random_state=42,
                    n_jobs=-1,
                    verbosity=0,
                )
            ))
            logger.info("Added XGBoost to ensemble")
        except ImportError:
            logger.warning("XGBoost not available")

        # LightGBM - fast and accurate (Wang et al. 2025 showed 52.6% accuracy)
        try:
            import lightgbm as lgb
            learners.append((
                "lightgbm",
                lgb.LGBMClassifier(
                    n_estimators=self.params.get("n_estimators", 200),
                    max_depth=self.params.get("max_depth", 6),
                    learning_rate=self.params.get("learning_rate", 0.05),
                    objective="binary",
                    random_state=42,
                    n_jobs=-1,
                    verbose=-1,
                )
            ))
            logger.info("Added LightGBM to ensemble")
        except ImportError:
            logger.warning("LightGBM not available")

        # CatBoost - handles categorical features well
        try:
            from catboost import CatBoostClassifier
            learners.append((
                "catboost",
                CatBoostClassifier(
                    iterations=self.params.get("n_estimators", 200),
                    depth=self.params.get("max_depth", 6),
                    learning_rate=self.params.get("learning_rate", 0.05),
                    random_state=42,
                    verbose=False,
                )
            ))
            logger.info("Added CatBoost to ensemble")
        except ImportError:
            logger.warning("CatBoost not available")

        # Random Forest - ensemble diversity
        learners.append((
            "random_forest",
            RandomForestClassifier(
                n_estimators=self.params.get("n_estimators", 200),
                max_depth=self.params.get("max_depth", 6),
                random_state=42,
                n_jobs=-1,
            )
        ))
        logger.info("Added RandomForest to ensemble")

        # Gradient Boosting - sklearn native
        learners.append((
            "gradient_boosting",
            GradientBoostingClassifier(
                n_estimators=min(self.params.get("n_estimators", 200), 100),
                max_depth=self.params.get("max_depth", 6),
                learning_rate=self.params.get("learning_rate", 0.05),
                random_state=42,
            )
        ))
        logger.info("Added GradientBoosting to ensemble")

        return learners

    def _build_meta_learner(self) -> object:
        """
        Build meta-learner (final estimator).

        Based on Nature Scientific Reports research, MLP meta-learner
        performs well. We also support LogisticRegression for interpretability.
        """
        meta_type = self.params.get("meta_learner", "mlp")

        if meta_type == "mlp":
            return MLPClassifier(
                hidden_layer_sizes=(64, 32),
                activation="relu",
                solver="adam",
                alpha=0.001,  # L2 regularization
                max_iter=500,
                random_state=42,
                early_stopping=True,
                validation_fraction=0.1,
            )
        else:
            # LogisticRegression - more interpretable, good calibration
            return LogisticRegression(
                C=1.0,
                max_iter=1000,
                random_state=42,
            )

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
    ) -> None:
        """
        Train the stacked ensemble.

        Args:
            X_train: Training features
            y_train: Training target
            X_val: Validation features (used for calibration evaluation)
            y_val: Validation target
        """
        logger.info(f"Training stacked ensemble with {len(self.base_learners)} base learners...")
        logger.info(f"Training samples: {len(X_train)}")

        self.feature_names = X_train.columns.tolist()

        # Build stacking classifier
        self.ensemble = StackingClassifier(
            estimators=self.base_learners,
            final_estimator=self.meta_learner,
            cv=5,  # 5-fold CV for generating meta-features
            stack_method="predict_proba",
            passthrough=False,  # Only use base predictions, not original features
            n_jobs=-1,
        )

        # Train ensemble
        self.ensemble.fit(X_train, y_train)

        # Evaluate base learners individually
        self._evaluate_base_learners(X_val, y_val)

        logger.info("Ensemble training complete")

    def _evaluate_base_learners(
        self, X_val: Optional[pd.DataFrame], y_val: Optional[pd.Series]
    ) -> None:
        """Evaluate individual base learner contributions."""
        if X_val is None or y_val is None:
            return

        logger.info("\nBase learner performance (validation set):")
        logger.info("-" * 50)

        for name, learner in self.ensemble.named_estimators_.items():
            try:
                proba = learner.predict_proba(X_val)[:, 1]
                brier = brier_score_loss(y_val, proba)
                acc = accuracy_score(y_val, (proba > 0.5).astype(int))
                self.base_learner_weights[name] = 1 / (brier + 0.01)  # Inverse Brier weight
                logger.info(f"  {name:20s}: Brier={brier:.4f}, Acc={acc:.4f}")
            except Exception as e:
                logger.warning(f"  {name}: Could not evaluate - {e}")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict class labels."""
        if self.ensemble is None:
            raise ValueError("Model not trained. Call train() first.")

        X = self._align_features(X)
        return self.ensemble.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict class probabilities.

        Returns probability of positive class (home win).
        """
        if self.ensemble is None:
            raise ValueError("Model not trained. Call train() first.")

        X = self._align_features(X)
        proba = self.ensemble.predict_proba(X)

        if proba.ndim == 2:
            return proba[:, 1]
        return proba

    def predict_with_uncertainty(
        self, X: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict with uncertainty quantification using base learner disagreement.

        Returns:
            (mean_proba, std_proba) - mean prediction and uncertainty
        """
        if self.ensemble is None:
            raise ValueError("Model not trained. Call train() first.")

        X = self._align_features(X)

        # Get predictions from each base learner
        base_predictions = []
        for name, learner in self.ensemble.named_estimators_.items():
            try:
                proba = learner.predict_proba(X)[:, 1]
                base_predictions.append(proba)
            except Exception:
                continue

        if not base_predictions:
            # Fallback to ensemble prediction only
            return self.predict_proba(X), np.zeros(len(X))

        # Stack predictions: (n_samples, n_learners)
        base_predictions = np.column_stack(base_predictions)

        # Mean and std across base learners
        mean_proba = base_predictions.mean(axis=1)
        std_proba = base_predictions.std(axis=1)

        return mean_proba, std_proba

    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """
        Evaluate ensemble on test data.

        Args:
            X: Test features
            y: True labels

        Returns:
            Dict with accuracy, brier_score, log_loss, roc_auc, uncertainty metrics
        """
        if self.ensemble is None:
            raise ValueError("Model not trained. Call train() first.")

        X = self._align_features(X)

        # Get predictions with uncertainty
        y_proba, uncertainty = self.predict_with_uncertainty(X)
        y_pred = (y_proba > 0.5).astype(int)

        # Calculate metrics
        metrics = {
            "accuracy": accuracy_score(y, y_pred),
            "brier_score": brier_score_loss(y, y_proba),
            "log_loss": log_loss(y, y_proba),
            "roc_auc": roc_auc_score(y, y_proba),
            "mean_uncertainty": uncertainty.mean(),
            "high_confidence_accuracy": self._high_confidence_accuracy(
                y, y_proba, uncertainty
            ),
        }

        return metrics

    def _high_confidence_accuracy(
        self,
        y_true: pd.Series,
        y_proba: np.ndarray,
        uncertainty: np.ndarray,
        threshold: float = 0.1,
    ) -> float:
        """
        Calculate accuracy on high-confidence predictions only.

        This is key for betting - we only bet when confident.
        """
        # Low uncertainty = high confidence
        high_conf_mask = uncertainty < threshold

        if high_conf_mask.sum() == 0:
            return 0.0

        y_pred = (y_proba > 0.5).astype(int)
        return accuracy_score(
            y_true.values[high_conf_mask], y_pred[high_conf_mask]
        )

    def get_feature_importance(self) -> Dict[str, float]:
        """
        Aggregate feature importance from base learners.

        Uses weighted average based on Brier score performance.
        """
        if self.ensemble is None:
            raise ValueError("Model not trained. Call train() first.")

        # Aggregate importance across base learners
        importance_sum = np.zeros(len(self.feature_names))
        weight_sum = 0

        for name, learner in self.ensemble.named_estimators_.items():
            weight = self.base_learner_weights.get(name, 1.0)

            if hasattr(learner, "feature_importances_"):
                importance_sum += learner.feature_importances_ * weight
                weight_sum += weight

        if weight_sum > 0:
            importance = importance_sum / weight_sum
        else:
            importance = importance_sum

        return dict(zip(self.feature_names, importance))

    def save(self, filepath: str) -> None:
        """Save ensemble model."""
        import joblib

        if self.ensemble is None:
            raise ValueError("Model not trained. Call train() first.")

        save_data = {
            "ensemble": self.ensemble,
            "feature_names": self.feature_names,
            "config": self.config,
            "base_learner_weights": self.base_learner_weights,
        }
        joblib.dump(save_data, filepath)
        logger.info(f"Ensemble saved to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> "StackedEnsembleModel":
        """Load ensemble model."""
        import joblib

        data = joblib.load(filepath)

        instance = cls(data.get("config", {"params": {}}))
        instance.ensemble = data["ensemble"]
        instance.feature_names = data.get("feature_names", [])
        instance.base_learner_weights = data.get("base_learner_weights", {})

        logger.info(f"Ensemble loaded from {filepath}")
        return instance

    def _align_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """Ensure features are in correct order."""
        if self.feature_names:
            for col in self.feature_names:
                if col not in X.columns:
                    X = X.copy()
                    X[col] = 0
            return X[self.feature_names]
        return X
