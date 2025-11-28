"""Probability calibration for NFL betting models.

Calibrates raw model probabilities to be statistically valid using
Platt Scaling (sigmoid) or Isotonic Regression. Critical for Kelly
Criterion bet sizing where accurate probabilities are essential.
"""

import logging
from pathlib import Path
from typing import Dict, Literal, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import brier_score_loss

logger = logging.getLogger(__name__)


class ModelCalibrator:
    """
    Probability calibrator using Platt Scaling or Isotonic Regression.

    Wraps a trained model and adjusts its probability outputs to be
    well-calibrated (i.e., when the model says 70% probability, the
    actual win rate should be ~70%).
    """

    def __init__(
        self,
        model,
        method: Literal["sigmoid", "isotonic"] = "sigmoid",
        cv: Union[int, str] = "prefit",
    ):
        """
        Initialize calibrator.

        Args:
            model: Trained model with predict_proba method (e.g., XGBoostNFLModel)
            method: Calibration method - 'sigmoid' (Platt) or 'isotonic'
            cv: Cross-validation strategy. Use 'prefit' for pre-trained models.
        """
        self.base_model = model
        self.method = method
        self.cv = cv
        self.calibrated_model: Optional[CalibratedClassifierCV] = None
        self._is_calibrated = False

    def calibrate(self, X: pd.DataFrame, y: pd.Series) -> "ModelCalibrator":
        """
        Fit the calibrator on validation data.

        CRITICAL: Use data NOT used for training to avoid bias.
        Typically use the validation set (2023 season in our setup).

        Args:
            X: Validation features
            y: Validation target

        Returns:
            self for chaining
        """
        logger.info(f"Calibrating probabilities using {self.method} method...")
        logger.info(f"Calibration data: {len(X)} samples")

        # Get the underlying sklearn model for calibration
        if hasattr(self.base_model, "model"):
            # XGBoostNFLModel wraps xgb.XGBClassifier
            sklearn_model = self.base_model.model
        else:
            sklearn_model = self.base_model

        # Create calibrated classifier
        # Handle cv='prefit' deprecation in sklearn 1.6+
        if self.cv == "prefit":
            try:
                from sklearn.frozen import FrozenEstimator
                self.calibrated_model = CalibratedClassifierCV(
                    estimator=FrozenEstimator(sklearn_model),
                    method=self.method,
                    cv=None,
                )
            except ImportError:
                # Fallback for older sklearn versions
                self.calibrated_model = CalibratedClassifierCV(
                    estimator=sklearn_model,
                    method=self.method,
                    cv=self.cv,
                )
        else:
            self.calibrated_model = CalibratedClassifierCV(
                estimator=sklearn_model,
                method=self.method,
                cv=self.cv,
            )

        # Fit calibrator
        self.calibrated_model.fit(X, y)
        self._is_calibrated = True

        logger.info("Calibration complete")
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get calibrated probability predictions.

        Args:
            X: Features

        Returns:
            Calibrated probabilities for positive class (home win)
        """
        if not self._is_calibrated:
            raise ValueError("Calibrator not fit. Call calibrate() first.")

        # Align features if base model has feature alignment
        if hasattr(self.base_model, "_align_features"):
            X = self.base_model._align_features(X)

        proba = self.calibrated_model.predict_proba(X)

        # Return probability of positive class
        if proba.ndim == 2:
            return proba[:, 1]
        return proba

    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        """
        Get calibrated class predictions.

        Args:
            X: Features
            threshold: Decision threshold

        Returns:
            Binary predictions
        """
        proba = self.predict_proba(X)
        return (proba >= threshold).astype(int)

    def evaluate_calibration(
        self, X: pd.DataFrame, y: pd.Series
    ) -> Dict[str, float]:
        """
        Evaluate calibration quality.

        Args:
            X: Test features
            y: True labels

        Returns:
            Dict with brier_uncalibrated, brier_calibrated, improvement_pct
        """
        if not self._is_calibrated:
            raise ValueError("Calibrator not fit. Call calibrate() first.")

        # Get uncalibrated probabilities from base model
        if hasattr(self.base_model, "predict_proba"):
            uncalibrated_proba = self.base_model.predict_proba(X)
        else:
            uncalibrated_proba = self.base_model.predict_proba(X)

        # Ensure 1D array
        if uncalibrated_proba.ndim == 2:
            uncalibrated_proba = uncalibrated_proba[:, 1]

        # Get calibrated probabilities
        calibrated_proba = self.predict_proba(X)

        # Calculate Brier scores
        brier_uncalibrated = brier_score_loss(y, uncalibrated_proba)
        brier_calibrated = brier_score_loss(y, calibrated_proba)

        # Calculate improvement
        if brier_uncalibrated > 0:
            improvement_pct = (
                (brier_uncalibrated - brier_calibrated) / brier_uncalibrated
            ) * 100
        else:
            improvement_pct = 0.0

        metrics = {
            "brier_uncalibrated": brier_uncalibrated,
            "brier_calibrated": brier_calibrated,
            "improvement_pct": improvement_pct,
        }

        logger.info(f"Brier (uncalibrated): {brier_uncalibrated:.4f}")
        logger.info(f"Brier (calibrated):   {brier_calibrated:.4f}")
        logger.info(f"Improvement:          {improvement_pct:.2f}%")

        return metrics

    def plot_calibration_curve(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        n_bins: int = 10,
        save_path: Optional[str] = None,
    ) -> None:
        """
        Plot calibration curve comparing uncalibrated vs calibrated.

        Args:
            X: Test features
            y: True labels
            n_bins: Number of bins for calibration curve
            save_path: Path to save figure (optional)
        """
        import matplotlib.pyplot as plt

        if not self._is_calibrated:
            raise ValueError("Calibrator not fit. Call calibrate() first.")

        # Get probabilities
        if hasattr(self.base_model, "predict_proba"):
            uncalibrated_proba = self.base_model.predict_proba(X)
        else:
            uncalibrated_proba = self.base_model.predict_proba(X)

        if uncalibrated_proba.ndim == 2:
            uncalibrated_proba = uncalibrated_proba[:, 1]

        calibrated_proba = self.predict_proba(X)

        # Calculate calibration curves
        prob_true_uncal, prob_pred_uncal = calibration_curve(
            y, uncalibrated_proba, n_bins=n_bins, strategy="uniform"
        )
        prob_true_cal, prob_pred_cal = calibration_curve(
            y, calibrated_proba, n_bins=n_bins, strategy="uniform"
        )

        # Create figure
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        # Calibration plot
        ax1 = axes[0]
        ax1.plot([0, 1], [0, 1], "k--", label="Perfectly calibrated")
        ax1.plot(
            prob_pred_uncal,
            prob_true_uncal,
            "s-",
            color="red",
            label="Uncalibrated",
        )
        ax1.plot(
            prob_pred_cal,
            prob_true_cal,
            "o-",
            color="green",
            label="Calibrated",
        )
        ax1.set_xlabel("Mean Predicted Probability")
        ax1.set_ylabel("Fraction of Positives")
        ax1.set_title("Calibration Curve")
        ax1.legend(loc="lower right")
        ax1.grid(True, alpha=0.3)

        # Histogram of predicted probabilities
        ax2 = axes[1]
        ax2.hist(
            uncalibrated_proba,
            bins=30,
            alpha=0.5,
            label="Uncalibrated",
            color="red",
        )
        ax2.hist(
            calibrated_proba,
            bins=30,
            alpha=0.5,
            label="Calibrated",
            color="green",
        )
        ax2.set_xlabel("Predicted Probability")
        ax2.set_ylabel("Count")
        ax2.set_title("Distribution of Predictions")
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save if path provided
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            logger.info(f"Calibration curve saved to {save_path}")

        plt.close()

    def get_calibration_data(
        self, X: pd.DataFrame, y: pd.Series, n_bins: int = 10
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Get raw calibration curve data for custom plotting.

        Returns:
            (prob_true_uncal, prob_pred_uncal, prob_true_cal, prob_pred_cal)
        """
        if not self._is_calibrated:
            raise ValueError("Calibrator not fit. Call calibrate() first.")

        # Get probabilities
        if hasattr(self.base_model, "predict_proba"):
            uncalibrated_proba = self.base_model.predict_proba(X)
        else:
            uncalibrated_proba = self.base_model.predict_proba(X)

        if uncalibrated_proba.ndim == 2:
            uncalibrated_proba = uncalibrated_proba[:, 1]

        calibrated_proba = self.predict_proba(X)

        prob_true_uncal, prob_pred_uncal = calibration_curve(
            y, uncalibrated_proba, n_bins=n_bins, strategy="uniform"
        )
        prob_true_cal, prob_pred_cal = calibration_curve(
            y, calibrated_proba, n_bins=n_bins, strategy="uniform"
        )

        return prob_true_uncal, prob_pred_uncal, prob_true_cal, prob_pred_cal
