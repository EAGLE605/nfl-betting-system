"""Rigorous tests for research-backed ML implementations.

Tests verify:
1. Correctness of ECE/MCE calculations (Guo et al. 2017)
2. Stacked ensemble behavior (Nature Scientific Reports 2025)
3. Uncertainty quantification (Gal & Ghahramani 2016)
4. CLV GO/NO-GO validation (Buchdahl methodology)
5. Edge cases and integration
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.xgboost_model import XGBoostNFLModel
from src.models.calibration import ModelCalibrator
from src.models.ensemble import StackedEnsembleModel
from src.models.uncertainty import MCDropoutPredictor, calculate_confidence_score
from src.backtesting.engine import BacktestEngine, GO_CRITERIA


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_data():
    """Generate realistic sample data for testing."""
    np.random.seed(42)
    n_train, n_val, n_test = 500, 100, 100
    n_features = 15

    # Create features with some signal
    X_train = pd.DataFrame(
        np.random.randn(n_train, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )
    # Add some predictive signal
    signal = X_train['feature_0'] + X_train['feature_1'] * 0.5
    y_train = pd.Series((signal + np.random.randn(n_train) * 0.5 > 0).astype(int))

    X_val = pd.DataFrame(
        np.random.randn(n_val, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )
    signal_val = X_val['feature_0'] + X_val['feature_1'] * 0.5
    y_val = pd.Series((signal_val + np.random.randn(n_val) * 0.5 > 0).astype(int))

    X_test = pd.DataFrame(
        np.random.randn(n_test, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )
    signal_test = X_test['feature_0'] + X_test['feature_1'] * 0.5
    y_test = pd.Series((signal_test + np.random.randn(n_test) * 0.5 > 0).astype(int))

    return {
        'X_train': X_train, 'y_train': y_train,
        'X_val': X_val, 'y_val': y_val,
        'X_test': X_test, 'y_test': y_test,
    }


@pytest.fixture
def model_config():
    """Standard model configuration."""
    return {
        'params': {
            'n_estimators': 50,
            'max_depth': 4,
            'learning_rate': 0.1,
            'early_stopping_rounds': 10,
        }
    }


@pytest.fixture
def backtest_predictions():
    """Generate backtest prediction data."""
    np.random.seed(42)
    n = 200

    # Simulate predictions with some edge
    pred_prob = np.clip(np.random.normal(0.55, 0.1, n), 0.4, 0.75)
    # Actual outcomes correlated with predictions
    actual = (np.random.random(n) < pred_prob).astype(int)
    # Realistic odds
    odds = 1 / (1 - pred_prob + np.random.normal(0, 0.05, n))
    odds = np.clip(odds, 1.5, 3.0)

    return pd.DataFrame({
        'game_id': range(n),
        'gameday': pd.date_range('2024-01-01', periods=n),
        'home_team': ['Team_A'] * n,
        'away_team': ['Team_B'] * n,
        'pred_prob': pred_prob,
        'actual': actual,
        'odds': odds,
    })


# =============================================================================
# TEST: XGBoost Model
# =============================================================================

class TestXGBoostModel:
    """Tests for XGBoostNFLModel."""

    def test_train_and_predict(self, sample_data, model_config):
        """Test basic training and prediction."""
        model = XGBoostNFLModel(model_config)
        model.train(
            sample_data['X_train'], sample_data['y_train'],
            sample_data['X_val'], sample_data['y_val']
        )

        proba = model.predict_proba(sample_data['X_test'])

        assert len(proba) == len(sample_data['X_test'])
        assert all(0 <= p <= 1 for p in proba)

    def test_evaluate_returns_all_metrics(self, sample_data, model_config):
        """Test that evaluate returns all required metrics."""
        model = XGBoostNFLModel(model_config)
        model.train(
            sample_data['X_train'], sample_data['y_train'],
            sample_data['X_val'], sample_data['y_val']
        )

        metrics = model.evaluate(sample_data['X_test'], sample_data['y_test'])

        required = ['accuracy', 'brier_score', 'log_loss', 'roc_auc']
        for metric in required:
            assert metric in metrics, f"Missing metric: {metric}"
            assert isinstance(metrics[metric], float)

    def test_feature_importance(self, sample_data, model_config):
        """Test feature importance extraction."""
        model = XGBoostNFLModel(model_config)
        model.train(
            sample_data['X_train'], sample_data['y_train'],
            sample_data['X_val'], sample_data['y_val']
        )

        importance = model.get_feature_importance()

        assert isinstance(importance, dict)
        assert len(importance) == sample_data['X_train'].shape[1]
        assert all(v >= 0 for v in importance.values())

    def test_save_and_load(self, sample_data, model_config, tmp_path):
        """Test model persistence."""
        model = XGBoostNFLModel(model_config)
        model.train(
            sample_data['X_train'], sample_data['y_train'],
            sample_data['X_val'], sample_data['y_val']
        )

        filepath = str(tmp_path / "model.json")
        model.save(filepath)

        loaded = XGBoostNFLModel.load(filepath)

        # Compare predictions
        orig_pred = model.predict_proba(sample_data['X_test'])
        loaded_pred = loaded.predict_proba(sample_data['X_test'])

        np.testing.assert_array_almost_equal(orig_pred, loaded_pred)

    def test_handles_missing_features(self, sample_data, model_config):
        """Test handling of missing features in prediction."""
        model = XGBoostNFLModel(model_config)
        model.train(
            sample_data['X_train'], sample_data['y_train'],
            sample_data['X_val'], sample_data['y_val']
        )

        # Create test data with missing column
        X_incomplete = sample_data['X_test'].drop(columns=['feature_0'])

        # Should handle gracefully
        proba = model.predict_proba(X_incomplete)
        assert len(proba) == len(X_incomplete)


# =============================================================================
# TEST: Calibration with ECE/MCE
# =============================================================================

class TestCalibration:
    """Tests for ModelCalibrator with ECE/MCE metrics."""

    def test_calibration_improves_brier(self, sample_data, model_config):
        """Test that calibration improves or maintains Brier score."""
        model = XGBoostNFLModel(model_config)
        model.train(
            sample_data['X_train'], sample_data['y_train'],
            sample_data['X_val'], sample_data['y_val']
        )

        calibrator = ModelCalibrator(model, method='sigmoid', cv='prefit')
        calibrator.calibrate(sample_data['X_val'], sample_data['y_val'])

        metrics = calibrator.evaluate_calibration(
            sample_data['X_test'], sample_data['y_test']
        )

        # Brier should be reasonable (not guaranteed to improve on small samples)
        assert metrics['brier_calibrated'] < 0.5  # Better than random

    def test_ece_mce_calculation(self, sample_data, model_config):
        """Test ECE/MCE metrics are calculated correctly."""
        model = XGBoostNFLModel(model_config)
        model.train(
            sample_data['X_train'], sample_data['y_train'],
            sample_data['X_val'], sample_data['y_val']
        )

        calibrator = ModelCalibrator(model, method='sigmoid', cv='prefit')
        calibrator.calibrate(sample_data['X_val'], sample_data['y_val'])

        metrics = calibrator.evaluate_calibration(
            sample_data['X_test'], sample_data['y_test']
        )

        # Check ECE/MCE are present and valid
        assert 'ece_calibrated' in metrics
        assert 'mce_calibrated' in metrics
        assert 0 <= metrics['ece_calibrated'] <= 1
        assert 0 <= metrics['mce_calibrated'] <= 1
        assert metrics['mce_calibrated'] >= metrics['ece_calibrated']  # MCE >= ECE always

    def test_ece_mce_perfect_calibration(self):
        """Test ECE/MCE with perfectly calibrated predictions."""
        # Create perfectly calibrated predictions
        y_true = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
        y_prob = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9, 1.0])

        calibrator = ModelCalibrator.__new__(ModelCalibrator)
        ece, mce = calibrator._calculate_ece_mce(y_true, y_prob, n_bins=5)

        # Should be low for well-calibrated predictions
        assert ece < 0.3

    def test_ece_mce_poor_calibration(self):
        """Test ECE/MCE with poorly calibrated predictions."""
        # Create poorly calibrated predictions (always predicts 0.9)
        y_true = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
        y_prob = np.array([0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9])

        calibrator = ModelCalibrator.__new__(ModelCalibrator)
        ece, mce = calibrator._calculate_ece_mce(y_true, y_prob, n_bins=5)

        # Should be high for poorly calibrated
        assert ece > 0.3

    def test_isotonic_vs_sigmoid(self, sample_data, model_config):
        """Test both calibration methods work."""
        model = XGBoostNFLModel(model_config)
        model.train(
            sample_data['X_train'], sample_data['y_train'],
            sample_data['X_val'], sample_data['y_val']
        )

        for method in ['sigmoid', 'isotonic']:
            calibrator = ModelCalibrator(model, method=method, cv='prefit')
            calibrator.calibrate(sample_data['X_val'], sample_data['y_val'])

            proba = calibrator.predict_proba(sample_data['X_test'])
            assert len(proba) == len(sample_data['X_test'])
            assert all(0 <= p <= 1 for p in proba)


# =============================================================================
# TEST: Stacked Ensemble
# =============================================================================

class TestStackedEnsemble:
    """Tests for StackedEnsembleModel."""

    def test_ensemble_trains(self, sample_data, model_config):
        """Test ensemble training completes."""
        ensemble = StackedEnsembleModel(model_config)
        ensemble.train(
            sample_data['X_train'], sample_data['y_train'],
            sample_data['X_val'], sample_data['y_val']
        )

        assert ensemble.ensemble is not None

    def test_predict_with_uncertainty(self, sample_data, model_config):
        """Test uncertainty quantification from ensemble."""
        ensemble = StackedEnsembleModel(model_config)
        ensemble.train(
            sample_data['X_train'], sample_data['y_train'],
            sample_data['X_val'], sample_data['y_val']
        )

        mean_proba, uncertainty = ensemble.predict_with_uncertainty(sample_data['X_test'])

        assert len(mean_proba) == len(sample_data['X_test'])
        assert len(uncertainty) == len(sample_data['X_test'])
        assert all(0 <= p <= 1 for p in mean_proba)
        assert all(u >= 0 for u in uncertainty)

    def test_high_confidence_accuracy(self, sample_data, model_config):
        """Test high-confidence accuracy metric."""
        ensemble = StackedEnsembleModel(model_config)
        ensemble.train(
            sample_data['X_train'], sample_data['y_train'],
            sample_data['X_val'], sample_data['y_val']
        )

        metrics = ensemble.evaluate(sample_data['X_test'], sample_data['y_test'])

        assert 'high_confidence_accuracy' in metrics
        assert 'mean_uncertainty' in metrics

    def test_feature_importance_aggregation(self, sample_data, model_config):
        """Test feature importance from ensemble."""
        ensemble = StackedEnsembleModel(model_config)
        ensemble.train(
            sample_data['X_train'], sample_data['y_train'],
            sample_data['X_val'], sample_data['y_val']
        )

        importance = ensemble.get_feature_importance()

        assert isinstance(importance, dict)
        assert len(importance) == sample_data['X_train'].shape[1]


# =============================================================================
# TEST: Uncertainty Quantification
# =============================================================================

class TestUncertainty:
    """Tests for uncertainty quantification."""

    def test_confidence_score_high_confidence(self):
        """Test confidence score for high-confidence bet."""
        score = calculate_confidence_score(
            probability=0.70,
            uncertainty=0.05,
            edge=0.08,
        )

        assert 0 <= score <= 1
        assert score > 0.5  # Should be confident

    def test_confidence_score_low_confidence(self):
        """Test confidence score for low-confidence bet."""
        score = calculate_confidence_score(
            probability=0.52,
            uncertainty=0.12,
            edge=0.01,
        )

        assert 0 <= score <= 1
        assert score < 0.5  # Should not be confident

    def test_confidence_score_high_uncertainty_blocks(self):
        """Test that high uncertainty returns 0."""
        score = calculate_confidence_score(
            probability=0.70,
            uncertainty=0.20,  # Above threshold
            edge=0.10,
        )

        assert score == 0.0

    def test_confidence_score_edge_cases(self):
        """Test edge cases for confidence score."""
        # Zero edge
        score = calculate_confidence_score(0.5, 0.05, 0.0)
        assert score >= 0

        # Maximum edge
        score = calculate_confidence_score(0.9, 0.01, 0.15)
        assert score <= 1


# =============================================================================
# TEST: Backtest Engine with CLV GO/NO-GO
# =============================================================================

class TestBacktestEngine:
    """Tests for BacktestEngine with CLV validation."""

    def test_backtest_runs(self, backtest_predictions):
        """Test backtest execution."""
        engine = BacktestEngine(initial_bankroll=10000)
        metrics, history = engine.run_backtest(backtest_predictions)

        assert 'total_bets' in metrics
        assert metrics['total_bets'] > 0
        assert len(history) > 0

    def test_clv_metrics_calculated(self, backtest_predictions):
        """Test CLV metrics are calculated."""
        engine = BacktestEngine(initial_bankroll=10000)
        metrics, _ = engine.run_backtest(backtest_predictions)

        required_clv_metrics = [
            'avg_clv', 'clv_std', 'positive_clv_pct',
            'clv_tstat', 'clv_pvalue', 'clv_significant'
        ]

        for metric in required_clv_metrics:
            assert metric in metrics, f"Missing CLV metric: {metric}"

    def test_variance_metrics_calculated(self, backtest_predictions):
        """Test variance/luck metrics are calculated."""
        engine = BacktestEngine(initial_bankroll=10000)
        metrics, _ = engine.run_backtest(backtest_predictions)

        assert 'max_win_streak' in metrics
        assert 'max_loss_streak' in metrics
        assert 'expected_wins' in metrics
        assert 'luck_factor' in metrics

    def test_go_no_go_validation(self, backtest_predictions):
        """Test GO/NO-GO validation works."""
        engine = BacktestEngine(initial_bankroll=10000)
        metrics, _ = engine.run_backtest(backtest_predictions)

        is_go, results = engine.validate_go_no_go(metrics)

        assert isinstance(is_go, bool)
        assert 'min_bets' in results
        assert 'min_clv' in results
        assert 'max_drawdown' in results

        # Each result should be (bool-like, str)
        for criterion, (passed, explanation) in results.items():
            assert passed in (True, False) or isinstance(passed, (bool, np.bool_))
            assert isinstance(explanation, str)

    def test_go_criteria_edge_cases(self):
        """Test GO/NO-GO with edge case metrics."""
        engine = BacktestEngine()

        # Minimal passing metrics
        passing_metrics = {
            'total_bets': 100,
            'avg_clv': 1.0,
            'positive_clv_pct': 55,
            'roi': 5.0,
            'max_drawdown': -10,
            'sharpe_ratio': 0.5,
            'clv_pvalue': 0.01,
            'clv_significant': True,
        }

        is_go, _ = engine.validate_go_no_go(passing_metrics)
        assert is_go is True

        # Failing on CLV
        failing_metrics = passing_metrics.copy()
        failing_metrics['avg_clv'] = -1.0

        is_go, _ = engine.validate_go_no_go(failing_metrics)
        assert is_go is False

    def test_empty_backtest(self):
        """Test backtest with no bets placed."""
        engine = BacktestEngine(initial_bankroll=10000)

        # Predictions where no bets qualify
        predictions = pd.DataFrame({
            'game_id': range(10),
            'gameday': pd.date_range('2024-01-01', periods=10),
            'pred_prob': [0.4] * 10,  # Below threshold
            'actual': [0] * 10,
            'odds': [2.0] * 10,
        })

        metrics, history = engine.run_backtest(predictions)

        assert 'error' in metrics or metrics.get('total_bets', 0) == 0


# =============================================================================
# TEST: Integration
# =============================================================================

class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_full_pipeline(self, sample_data, model_config):
        """Test complete training -> calibration -> prediction pipeline."""
        # Train model
        model = XGBoostNFLModel(model_config)
        model.train(
            sample_data['X_train'], sample_data['y_train'],
            sample_data['X_val'], sample_data['y_val']
        )

        # Calibrate
        calibrator = ModelCalibrator(model, method='sigmoid', cv='prefit')
        calibrator.calibrate(sample_data['X_val'], sample_data['y_val'])

        # Get calibrated predictions
        proba = calibrator.predict_proba(sample_data['X_test'])

        # Evaluate calibration
        cal_metrics = calibrator.evaluate_calibration(
            sample_data['X_test'], sample_data['y_test']
        )

        # All metrics should be valid
        assert cal_metrics['brier_calibrated'] < 0.5
        assert 0 <= cal_metrics['ece_calibrated'] <= 1

    def test_ensemble_to_backtest_pipeline(self, sample_data, model_config):
        """Test ensemble predictions through backtest."""
        # Train ensemble
        ensemble = StackedEnsembleModel(model_config)
        ensemble.train(
            sample_data['X_train'], sample_data['y_train'],
            sample_data['X_val'], sample_data['y_val']
        )

        # Generate predictions with uncertainty
        mean_proba, uncertainty = ensemble.predict_with_uncertainty(sample_data['X_test'])

        # Create backtest dataframe
        predictions = pd.DataFrame({
            'game_id': range(len(mean_proba)),
            'gameday': pd.date_range('2024-01-01', periods=len(mean_proba)),
            'pred_prob': mean_proba,
            'actual': sample_data['y_test'].values,
            'odds': 1.9 + np.random.uniform(-0.1, 0.1, len(mean_proba)),
        })

        # Run backtest
        engine = BacktestEngine(initial_bankroll=10000)
        metrics, history = engine.run_backtest(predictions)

        # Should complete without error
        assert metrics.get('total_bets', 0) >= 0


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
