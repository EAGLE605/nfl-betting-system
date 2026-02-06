"""Uncertainty quantification for NFL betting predictions.

Implements Monte Carlo Dropout for Bayesian uncertainty estimation.
Based on:
- Gal & Ghahramani (2016) "Dropout as a Bayesian Approximation"
- MDPI (2024) "Uncertainty-Aware Machine Learning for NBA Forecasting"

Key insight: Only bet when model is confident (low uncertainty) AND
has positive expected value.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, brier_score_loss

logger = logging.getLogger(__name__)


class MCDropoutPredictor:
    """
    Monte Carlo Dropout for uncertainty quantification.

    Runs multiple forward passes with dropout enabled to estimate
    prediction uncertainty. Higher variance = higher uncertainty.
    """

    def __init__(
        self,
        n_iterations: int = 50,
        dropout_rate: float = 0.2,
    ):
        """
        Initialize MC Dropout predictor.

        Args:
            n_iterations: Number of stochastic forward passes
            dropout_rate: Dropout probability
        """
        self.n_iterations = n_iterations
        self.dropout_rate = dropout_rate
        self.model = None
        self.feature_names: List[str] = []

    def build_model(self, input_dim: int) -> None:
        """
        Build neural network with dropout for MC inference.

        Architecture based on MDPI uncertainty-aware forecasting research.
        """
        try:
            import torch
            import torch.nn as nn

            class MCDropoutNet(nn.Module):
                def __init__(self, input_dim, dropout_rate):
                    super().__init__()
                    self.layers = nn.Sequential(
                        nn.Linear(input_dim, 128),
                        nn.ReLU(),
                        nn.Dropout(dropout_rate),
                        nn.Linear(128, 64),
                        nn.ReLU(),
                        nn.Dropout(dropout_rate),
                        nn.Linear(64, 32),
                        nn.ReLU(),
                        nn.Dropout(dropout_rate),
                        nn.Linear(32, 1),
                        nn.Sigmoid(),
                    )

                def forward(self, x):
                    return self.layers(x)

            self.model = MCDropoutNet(input_dim, self.dropout_rate)
            self._torch_available = True
            logger.info(f"Built PyTorch MC Dropout model with {input_dim} input features")

        except ImportError:
            logger.warning("PyTorch not available, using sklearn fallback")
            self._torch_available = False
            self._build_sklearn_fallback(input_dim)

    def _build_sklearn_fallback(self, input_dim: int) -> None:
        """Build sklearn-based ensemble for uncertainty when PyTorch unavailable."""
        from sklearn.neural_network import MLPClassifier

        # Create multiple MLPs with different random states for ensemble uncertainty
        self.ensemble_models = [
            MLPClassifier(
                hidden_layer_sizes=(128, 64, 32),
                activation="relu",
                solver="adam",
                alpha=0.001,
                max_iter=500,
                random_state=42 + i,
                early_stopping=True,
            )
            for i in range(self.n_iterations)
        ]
        logger.info(f"Built sklearn ensemble fallback with {self.n_iterations} models")

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
        epochs: int = 100,
    ) -> None:
        """Train the MC Dropout model."""
        self.feature_names = X_train.columns.tolist()
        input_dim = X_train.shape[1]

        if self.model is None:
            self.build_model(input_dim)

        if self._torch_available:
            self._train_torch(X_train, y_train, X_val, y_val, epochs)
        else:
            self._train_sklearn(X_train, y_train)

    def _train_torch(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame],
        y_val: Optional[pd.Series],
        epochs: int,
    ) -> None:
        """Train PyTorch model."""
        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader, TensorDataset

        # Convert to tensors
        X_tensor = torch.FloatTensor(X_train.values)
        y_tensor = torch.FloatTensor(y_train.values).unsqueeze(1)

        dataset = TensorDataset(X_tensor, y_tensor)
        loader = DataLoader(dataset, batch_size=64, shuffle=True)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        criterion = nn.BCELoss()

        # Training loop
        self.model.train()
        for epoch in range(epochs):
            epoch_loss = 0
            for X_batch, y_batch in loader:
                optimizer.zero_grad()
                outputs = self.model(X_batch)
                loss = criterion(outputs, y_batch)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()

            if (epoch + 1) % 20 == 0:
                logger.info(f"Epoch {epoch + 1}/{epochs}, Loss: {epoch_loss / len(loader):.4f}")

        logger.info("PyTorch MC Dropout training complete")

    def _train_sklearn(self, X_train: pd.DataFrame, y_train: pd.Series) -> None:
        """Train sklearn ensemble fallback."""
        logger.info(f"Training {len(self.ensemble_models)} ensemble models...")

        for i, model in enumerate(self.ensemble_models):
            model.fit(X_train, y_train)
            if (i + 1) % 10 == 0:
                logger.info(f"Trained {i + 1}/{len(self.ensemble_models)} models")

        logger.info("Sklearn ensemble training complete")

    def predict_with_uncertainty(
        self, X: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Predict with uncertainty quantification.

        Args:
            X: Features

        Returns:
            (mean_proba, std_proba, predictions) where:
            - mean_proba: Mean probability across MC samples
            - std_proba: Standard deviation (uncertainty)
            - predictions: Array of all MC sample predictions
        """
        X = self._align_features(X)

        if self._torch_available:
            return self._predict_torch(X)
        else:
            return self._predict_sklearn(X)

    def _predict_torch(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Run MC Dropout inference with PyTorch."""
        import torch

        X_tensor = torch.FloatTensor(X.values)

        # Enable dropout during inference
        self.model.train()  # Keep dropout active

        predictions = []
        with torch.no_grad():
            for _ in range(self.n_iterations):
                pred = self.model(X_tensor).numpy().flatten()
                predictions.append(pred)

        predictions = np.array(predictions)  # (n_iterations, n_samples)

        mean_proba = predictions.mean(axis=0)
        std_proba = predictions.std(axis=0)

        return mean_proba, std_proba, predictions

    def _predict_sklearn(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Run ensemble inference with sklearn."""
        predictions = []

        for model in self.ensemble_models:
            proba = model.predict_proba(X)[:, 1]
            predictions.append(proba)

        predictions = np.array(predictions)  # (n_models, n_samples)

        mean_proba = predictions.mean(axis=0)
        std_proba = predictions.std(axis=0)

        return mean_proba, std_proba, predictions

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get mean probability prediction."""
        mean_proba, _, _ = self.predict_with_uncertainty(X)
        return mean_proba

    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """
        Evaluate model with uncertainty-aware metrics.

        Key insight from research: High-confidence predictions should
        have higher accuracy than overall predictions.
        """
        mean_proba, std_proba, _ = self.predict_with_uncertainty(X)
        y_pred = (mean_proba > 0.5).astype(int)

        metrics = {
            "accuracy": accuracy_score(y, y_pred),
            "brier_score": brier_score_loss(y, mean_proba),
            "mean_uncertainty": std_proba.mean(),
            "median_uncertainty": np.median(std_proba),
        }

        # Accuracy at different confidence levels
        for threshold in [0.05, 0.10, 0.15]:
            mask = std_proba < threshold
            if mask.sum() > 0:
                conf_acc = accuracy_score(y.values[mask], y_pred[mask])
                metrics[f"accuracy_uncertainty_lt_{threshold}"] = conf_acc
                metrics[f"n_samples_uncertainty_lt_{threshold}"] = mask.sum()

        return metrics

    def _align_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """Ensure features are in correct order."""
        if self.feature_names:
            for col in self.feature_names:
                if col not in X.columns:
                    X = X.copy()
                    X[col] = 0
            return X[self.feature_names]
        return X


def calculate_confidence_score(
    probability: float,
    uncertainty: float,
    edge: float,
    max_uncertainty: float = 0.15,
) -> float:
    """
    Calculate composite confidence score for betting decisions.

    Based on uncertainty-aware betting research.

    Args:
        probability: Model probability prediction
        uncertainty: Standard deviation from MC Dropout
        edge: Expected edge (probability - implied probability)
        max_uncertainty: Maximum acceptable uncertainty

    Returns:
        Confidence score (0-1), higher = more confident bet
    """
    if uncertainty > max_uncertainty:
        return 0.0

    # Components
    uncertainty_score = 1 - (uncertainty / max_uncertainty)
    edge_score = min(edge / 0.10, 1.0)  # Cap at 10% edge
    probability_score = abs(probability - 0.5) * 2  # Distance from 50%

    # Weighted combination
    confidence = (
        0.4 * uncertainty_score +
        0.4 * edge_score +
        0.2 * probability_score
    )

    return max(0, min(1, confidence))
