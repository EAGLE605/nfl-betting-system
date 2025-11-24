"""Retrain model on recent data only (2023-2024).

This addresses the critical finding that the model trained on 2016-2024
performed perfectly in 2020-2022 but failed in 2023-2024.

Strategy:
- Train on 2023 data only
- Validate/test on 2024 data
- Capture current market patterns, not historical ones
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

import joblib
import pandas as pd
import yaml

from src.models.calibration import ModelCalibrator
from src.models.xgboost_model import XGBoostNFLModel

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_data():
    """Load and prepare data."""
    logger.info("Loading features...")
    try:
        df = pd.read_parquet("data/processed/features_2016_2024_improved.parquet")
        logger.info("Using improved features")
    except FileNotFoundError:
        df = pd.read_parquet("data/processed/features_2016_2024.parquet")
        logger.info("Using original features")

    # Create target: 1 if home wins, 0 if away wins
    df["target"] = (df["home_score"] > df["away_score"]).astype(int)

    # Define feature columns (exclude metadata and target)
    exclude = [
        "game_id",
        "gameday",
        "home_team",
        "away_team",
        "season",
        "week",
        "home_score",
        "away_score",
        "result",
        "total",
        "game_type",
        "weekday",
        "gametime",
        "location",
        "overtime",
        "old_game_id",
        "gsis",
        "nfl_detail_id",
        "pfr",
        "pff",
        "espn",
        "ftn",
        "away_qb_id",
        "home_qb_id",
        "away_qb_name",
        "home_qb_name",
        "away_coach",
        "home_coach",
        "referee",
        "stadium_id",
        "stadium",
        "roof",
        "surface",
        # CRITICAL: Exclude betting line features (data leakage)
        "home_moneyline",
        "away_moneyline",
        "spread_line",
        "home_spread_odds",
        "away_spread_odds",
        "total_line",
        "over_odds",
        "under_odds",
        "line_movement",
        "total_movement",
        "home_favorite",
        "spread_home",
    ]

    feature_cols = [col for col in df.columns if col not in exclude]
    feature_cols = [
        col for col in feature_cols if df[col].dtype in ["float64", "int64"]
    ]

    logger.info(f"Games: {len(df)}")
    logger.info(f"Features: {len(feature_cols)}")

    return df, feature_cols


def recent_temporal_split(df):
    """
    Split data temporally for recent model training.

    Train: 2023 only (capture current market)
    Test: 2024 only (validate on most recent data)
    """
    train_df = df[df["season"] == 2023].copy()
    test_df = df[df["season"] == 2024].copy()

    logger.info(f"Train: {len(train_df)} games (2023 only)")
    logger.info(f"Test:  {len(test_df)} games (2024 only)")

    if len(train_df) == 0:
        raise ValueError("No 2023 training data found!")
    if len(test_df) == 0:
        raise ValueError("No 2024 test data found!")

    return train_df, test_df


def main():
    logger.info("=" * 70)
    logger.info("RETRAINING MODEL ON RECENT DATA (2023-2024)")
    logger.info("=" * 70)
    logger.info("")
    logger.info("CRITICAL: This addresses the finding that models trained on")
    logger.info("2016-2024 data failed in 2023-2024. Training on recent data only.")
    logger.info("")

    # Load config
    with open("config/config.yaml") as f:
        config = yaml.safe_load(f)

    # Load data
    df, feature_cols = load_data()

    # Recent temporal split
    train_df, test_df = recent_temporal_split(df)

    # Prepare sets
    X_train, y_train = train_df[feature_cols], train_df["target"]
    X_test, y_test = test_df[feature_cols], test_df["target"]

    # Handle missing features (align with model expectations)
    # Fill missing features with 0
    for col in feature_cols:
        if col not in X_train.columns:
            X_train[col] = 0
        if col not in X_test.columns:
            X_test[col] = 0

    # Ensure same columns in same order
    X_train = X_train[feature_cols]
    X_test = X_test[feature_cols]

    # Handle missing values
    X_train = X_train.fillna(0)
    X_test = X_test.fillna(0)

    logger.info(f"Using {len(feature_cols)} features")
    logger.info(f"Training samples: {len(X_train)}")
    logger.info(f"Test samples: {len(X_test)}")

    # Train model
    logger.info("\n" + "=" * 70)
    logger.info("TRAINING MODEL ON 2023 DATA")
    logger.info("=" * 70)

    # Use validation set from 2023 (split 80/20)
    split_idx = int(len(X_train) * 0.8)
    X_train_split = X_train.iloc[:split_idx]
    y_train_split = y_train.iloc[:split_idx]
    X_val_split = X_train.iloc[split_idx:]
    y_val_split = y_train.iloc[split_idx:]

    model = XGBoostNFLModel(config["model"])
    model.train(X_train_split, y_train_split, X_val_split, y_val_split)

    # Evaluate on test set (2024)
    logger.info("\n" + "=" * 70)
    logger.info("EVALUATING ON 2024 TEST SET")
    logger.info("=" * 70)

    metrics = model.evaluate(X_test, y_test)
    logger.info(f"Accuracy:    {metrics['accuracy']:.4f}")
    logger.info(f"Brier Score: {metrics['brier_score']:.4f}")
    logger.info(f"Log Loss:    {metrics['log_loss']:.4f}")
    logger.info(f"ROC AUC:     {metrics['roc_auc']:.4f}")

    # Calibrate model
    logger.info("\n" + "=" * 70)
    logger.info("CALIBRATING MODEL")
    logger.info("=" * 70)

    calibrator = ModelCalibrator(model, method="sigmoid", cv="prefit")
    calibrator.calibrate(X_val_split, y_val_split)

    # Evaluate calibration
    logger.info("\n" + "=" * 70)
    logger.info("CALIBRATED MODEL EVALUATION (2024)")
    logger.info("=" * 70)

    cal_metrics = calibrator.evaluate_calibration(X_test, y_test)
    logger.info(f"Brier (uncalibrated): {cal_metrics['brier_uncalibrated']:.4f}")
    logger.info(f"Brier (calibrated):   {cal_metrics['brier_calibrated']:.4f}")

    # Use calibrated model for evaluation
    metrics_cal = model.evaluate(X_test, y_test)
    logger.info(f"Accuracy:    {metrics_cal['accuracy']:.4f}")
    logger.info(f"Brier Score: {metrics_cal['brier_score']:.4f}")
    logger.info(f"Log Loss:    {metrics_cal['log_loss']:.4f}")
    logger.info(f"ROC AUC:     {metrics_cal['roc_auc']:.4f}")

    # Save model (with calibrator)
    output_path = Path("models/xgboost_recent_2023.pkl")
    output_path.parent.mkdir(exist_ok=True)
    joblib.dump(model, output_path)
    logger.info(f"\n✓ Model saved to: {output_path}")

    # Save calibrator separately
    calibrator_path = Path("models/xgboost_recent_2023_calibrator.pkl")
    joblib.dump(calibrator, calibrator_path)
    logger.info(f"✓ Calibrator saved to: {calibrator_path}")

    # GO/NO-GO decision
    logger.info("\n" + "=" * 70)
    logger.info("GO/NO-GO DECISION")
    logger.info("=" * 70)

    accuracy_ok = metrics_cal["accuracy"] >= 0.55
    brier_ok = metrics_cal["brier_score"] <= 0.20
    roc_ok = metrics_cal["roc_auc"] >= 0.60

    logger.info(f"Accuracy >= 0.55: {accuracy_ok} ({metrics_cal['accuracy']:.3f})")
    logger.info(f"Brier <= 0.20:    {brier_ok} ({metrics_cal['brier_score']:.3f})")
    logger.info(f"ROC AUC >= 0.60:  {roc_ok} ({metrics_cal['roc_auc']:.3f})")

    if accuracy_ok and brier_ok and roc_ok:
        logger.info("\n✅ MODEL MEETS MINIMUM CRITERIA")
        logger.info("   → Proceed to backtest on 2024 data")
        logger.info("   → If backtest profitable → Paper trade")
        logger.info("   → If paper trade successful → Deploy cautiously")
    else:
        logger.warning("\n⚠️ MODEL DOES NOT MEET MINIMUM CRITERIA")
        logger.warning("   → DO NOT DEPLOY")
        logger.warning("   → Consider feature engineering or different approach")

    logger.info("\n" + "=" * 70)
    logger.info("NEXT STEP: Run backtest on 2024 data")
    logger.info("=" * 70)
    logger.info(
        "python scripts/bulldog_backtest.py --model models/xgboost_recent_2023.pkl --test-season 2024"
    )


if __name__ == "__main__":
    main()
