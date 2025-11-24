"""Model training script.

CRITICAL DATA SPLIT:
- Train: 2016-2022 (7 seasons)
- Validation: 2023 (1 season) - for calibration
- Test: 2024 (1 season) - for final evaluation

NEVER use test data (2024) until final evaluation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import yaml
import joblib
import logging
from src.models.xgboost_model import XGBoostNFLModel
from src.models.calibration import ModelCalibrator

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_data():
    """Load and prepare data."""
    logger.info("Loading features...")
    df = pd.read_parquet("data/processed/features_2016_2024.parquet")

    # Create target: 1 if home wins, 0 if away wins
    df["target"] = (df["home_score"] > df["away_score"]).astype(int)

    # Define feature columns (exclude metadata and target)
    exclude_cols = [
        "game_id",
        "gameday",
        "home_team",
        "away_team",
        "season",
        "week",
        "home_score",
        "away_score",
        "target",
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
        # CRITICAL: Exclude betting lines (data leakage - Vegas odds already encode all info)
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
        "home_favorite",  # Derived from betting lines
        "div_game",
        "roof",
        "surface",  # Categorical, not useful as-is
    ]
    feature_cols = [col for col in df.columns if col not in exclude_cols]

    logger.info(f"Features: {len(feature_cols)}")
    logger.info(f"Games: {len(df)}")

    return df, feature_cols


def temporal_split(df):
    """
    Split data temporally (NO random shuffle).

    Train: 2016-2022
    Val: 2023
    Test: 2024
    """
    train_df = df[df["season"] <= 2022].copy()
    val_df = df[df["season"] == 2023].copy()
    test_df = df[df["season"] == 2024].copy()

    logger.info(f"Train: {len(train_df)} games (2016-2022)")
    logger.info(f"Val:   {len(val_df)} games (2023)")
    logger.info(f"Test:  {len(test_df)} games (2024)")

    return train_df, val_df, test_df


def main():
    logger.info("=" * 70)
    logger.info("NFL BETTING SYSTEM - MODEL TRAINING")
    logger.info("=" * 70)

    # Load config
    with open("config/config.yaml") as f:
        config = yaml.safe_load(f)

    # Load data
    df, feature_cols = load_data()

    # Temporal split
    train_df, val_df, test_df = temporal_split(df)

    # Prepare sets
    X_train, y_train = train_df[feature_cols], train_df["target"]
    X_val, y_val = val_df[feature_cols], val_df["target"]
    X_test, y_test = test_df[feature_cols], test_df["target"]

    # Remove non-numeric columns (XGBoost requires numeric)
    numeric_cols = X_train.select_dtypes(include=["float64", "int64"]).columns.tolist()
    X_train = X_train[numeric_cols]
    X_val = X_val[numeric_cols]
    X_test = X_test[numeric_cols]

    logger.info(f"Using {len(numeric_cols)} numeric features")

    # Handle missing values (should be minimal after Phase 2)
    # CRITICAL: Fit imputation on train only, then transform val/test
    X_train = X_train.fillna(0)
    X_val = X_val.fillna(0)
    X_test = X_test.fillna(0)

    # Train base model
    logger.info("\n" + "=" * 70)
    logger.info("TRAINING BASE MODEL")
    logger.info("=" * 70)

    model = XGBoostNFLModel(config["model"])
    model.train(X_train, y_train, X_val, y_val)

    # Evaluate on test set (base model)
    logger.info("\n" + "=" * 70)
    logger.info("BASE MODEL EVALUATION (2024 Test Set)")
    logger.info("=" * 70)

    metrics_base = model.evaluate(X_test, y_test)
    logger.info(f"Accuracy:    {metrics_base['accuracy']:.4f}")
    logger.info(f"Brier Score: {metrics_base['brier_score']:.4f}")
    logger.info(f"Log Loss:    {metrics_base['log_loss']:.4f}")
    logger.info(f"ROC AUC:     {metrics_base['roc_auc']:.4f}")

    # Check GO criteria
    if metrics_base["accuracy"] < 0.55:
        logger.warning(f"⚠ Accuracy {metrics_base['accuracy']:.3f} < 0.55 threshold")
    if metrics_base["brier_score"] > 0.20:
        logger.warning(f"⚠ Brier {metrics_base['brier_score']:.3f} > 0.20 threshold")

    # Calibrate probabilities
    logger.info("\n" + "=" * 70)
    logger.info("CALIBRATING PROBABILITIES")
    logger.info("=" * 70)

    calibrator = ModelCalibrator(model, method="sigmoid", cv="prefit")
    calibrator.calibrate(X_val, y_val)

    # Evaluate calibration
    cal_metrics = calibrator.evaluate_calibration(X_test, y_test)
    logger.info(f"Brier (uncalibrated): {cal_metrics['brier_uncalibrated']:.4f}")
    logger.info(f"Brier (calibrated):   {cal_metrics['brier_calibrated']:.4f}")
    logger.info(f"Improvement:          {cal_metrics['improvement_pct']:.2f}%")

    # Plot calibration curve
    Path("reports/img").mkdir(parents=True, exist_ok=True)
    calibrator.plot_calibration_curve(
        X_test, y_test, save_path="reports/img/calibration_curve.png"
    )

    # Feature importance
    logger.info("\n" + "=" * 70)
    logger.info("TOP 15 FEATURES")
    logger.info("=" * 70)

    importance = model.get_feature_importance()
    importance_df = pd.DataFrame(
        {"feature": importance.keys(), "importance": importance.values()}
    ).sort_values("importance", ascending=False)

    print(importance_df.head(15).to_string(index=False))

    Path("reports").mkdir(exist_ok=True)
    importance_df.to_csv("reports/feature_importance.csv", index=False)

    # Save models
    logger.info("\n" + "=" * 70)
    logger.info("SAVING MODELS")
    logger.info("=" * 70)

    Path("models").mkdir(exist_ok=True)
    model.save("models/xgboost_mvp.json")
    joblib.dump(calibrator, "models/calibrated_model.pkl")

    logger.info("✓ Base model: models/xgboost_mvp.json")
    logger.info("✓ Calibrator: models/calibrated_model.pkl")

    # GO/NO-GO check
    logger.info("\n" + "=" * 70)
    logger.info("MODEL VALIDATION (GO/NO-GO CRITERIA)")
    logger.info("=" * 70)

    checks = {
        "Accuracy >55%": metrics_base["accuracy"] > 0.55,
        "Brier <0.20 (calibrated)": cal_metrics["brier_calibrated"] < 0.20,
        "Calibration improves Brier": cal_metrics["improvement_pct"] > 0,
    }

    for criterion, passed in checks.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status:12} {criterion}")

    if all(checks.values()):
        logger.info("\n✓ Model meets criteria. Ready for backtesting.")
        return 0
    else:
        logger.warning("\n⚠ Model fails some criteria. Review before backtesting.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
