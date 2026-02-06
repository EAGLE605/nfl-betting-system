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
        self, X: pd.DataFrame, y: pd.Series, n_bins: int = 10
    ) -> Dict[str, float]:
        """
        Evaluate calibration quality with comprehensive metrics.

        Metrics based on Guo et al. (2017) "On Calibration of Modern Neural Networks"
        and Walsh & Joshi (2024) sports betting calibration research.

        Args:
            X: Test features
            y: True labels
            n_bins: Number of bins for ECE/MCE calculation

        Returns:
            Dict with brier scores, ECE, MCE, and improvement metrics
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

        # Calculate ECE and MCE for both
        ece_uncalibrated, mce_uncalibrated = self._calculate_ece_mce(
            y.values, uncalibrated_proba, n_bins
        )
        ece_calibrated, mce_calibrated = self._calculate_ece_mce(
            y.values, calibrated_proba, n_bins
        )

        # Calculate improvement
        if brier_uncalibrated > 0:
            improvement_pct = (
                (brier_uncalibrated - brier_calibrated) / brier_uncalibrated
            ) * 100
        else:
            improvement_pct = 0.0

        if ece_uncalibrated > 0:
            ece_improvement_pct = (
                (ece_uncalibrated - ece_calibrated) / ece_uncalibrated
            ) * 100
        else:
            ece_improvement_pct = 0.0

        metrics = {
            "brier_uncalibrated": brier_uncalibrated,
            "brier_calibrated": brier_calibrated,
            "improvement_pct": improvement_pct,
            "ece_uncalibrated": ece_uncalibrated,
            "ece_calibrated": ece_calibrated,
            "ece_improvement_pct": ece_improvement_pct,
            "mce_uncalibrated": mce_uncalibrated,
            "mce_calibrated": mce_calibrated,
        }

        logger.info(f"Brier (uncalibrated): {brier_uncalibrated:.4f}")
        logger.info(f"Brier (calibrated):   {brier_calibrated:.4f}")
        logger.info(f"Brier improvement:    {improvement_pct:.2f}%")
        logger.info(f"ECE (uncalibrated):   {ece_uncalibrated:.4f}")
        logger.info(f"ECE (calibrated):     {ece_calibrated:.4f}")
        logger.info(f"ECE improvement:      {ece_improvement_pct:.2f}%")
        logger.info(f"MCE (calibrated):     {mce_calibrated:.4f}")

        return metrics

    def _calculate_ece_mce(
        self, y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10
    ) -> Tuple[float, float]:
        """
        Calculate Expected Calibration Error (ECE) and Maximum Calibration Error (MCE).

        ECE = Σ (|Bm|/n) * |acc(Bm) - conf(Bm)|
        MCE = max_m |acc(Bm) - conf(Bm)|

        Based on Guo et al. (2017) "On Calibration of Modern Neural Networks"

        Args:
            y_true: True binary labels
            y_prob: Predicted probabilities
            n_bins: Number of bins

        Returns:
            (ECE, MCE) tuple
        """
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        mce = 0.0
        n_samples = len(y_true)

        for i in range(n_bins):
            # Find samples in this bin
            in_bin = (y_prob > bin_boundaries[i]) & (y_prob <= bin_boundaries[i + 1])
            prop_in_bin = in_bin.sum() / n_samples

            if in_bin.sum() > 0:
                # Accuracy in bin (fraction of positives)
                accuracy_in_bin = y_true[in_bin].mean()
                # Average confidence in bin
                avg_confidence_in_bin = y_prob[in_bin].mean()
                # Calibration error for this bin
                calibration_error = abs(accuracy_in_bin - avg_confidence_in_bin)

                ece += prop_in_bin * calibration_error
                mce = max(mce, calibration_error)

        return ece, mce

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
