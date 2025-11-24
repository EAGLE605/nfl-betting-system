#!/usr/bin/env python3
"""Hyperparameter tuning with Optuna.

Tunes XGBoost and LightGBM models using Optuna optimization.
"""

import argparse
import logging
import pickle
import sys
from pathlib import Path

import lightgbm as lgb
import optuna
import xgboost as xgb
from sklearn.metrics import brier_score_loss

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from features.pipeline import create_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_data(seasons_train: list, seasons_val: list):
    """Load and prepare training/validation data."""
    logger.info(
        f"Loading features for training: {seasons_train}, validation: {seasons_val}"
    )

    # Load training features
    df_train = create_features(seasons_train)

    # Load validation features
    df_val = create_features(seasons_val)

    # Get feature columns (exclude metadata)
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
    ]
    feature_cols = [col for col in df_train.columns if col not in exclude]

    # Prepare X and y
    X_train = df_train[feature_cols].fillna(0)
    y_train = (df_train["result"] > 0).astype(int)  # Home win

    X_val = df_val[feature_cols].fillna(0)
    y_val = (df_val["result"] > 0).astype(int)

    logger.info(f"Training: {len(X_train)} samples, {len(feature_cols)} features")
    logger.info(f"Validation: {len(X_val)} samples")

    return X_train, y_train, X_val, y_val, feature_cols


def objective_xgboost(trial, X_train, y_train, X_val, y_val):
    """Optuna objective for XGBoost."""
    params = {
        "objective": "binary:logistic",
        "eval_metric": "logloss",
        "tree_method": "hist",
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "max_depth": trial.suggest_int("max_depth", 3, 10),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "n_estimators": trial.suggest_int("n_estimators", 100, 1000),
        "reg_alpha": trial.suggest_float("reg_alpha", 0, 10),
        "reg_lambda": trial.suggest_float("reg_lambda", 0, 10),
    }

    model = xgb.XGBClassifier(**params, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

    y_pred_proba = model.predict_proba(X_val)[:, 1]
    brier = brier_score_loss(y_val, y_pred_proba)

    return brier


def objective_lightgbm(trial, X_train, y_train, X_val, y_val):
    """Optuna objective for LightGBM."""
    params = {
        "objective": "binary",
        "metric": "binary_logloss",
        "boosting_type": "gbdt",
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "max_depth": trial.suggest_int("max_depth", 3, 10),
        "min_child_samples": trial.suggest_int("min_child_samples", 5, 100),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "n_estimators": trial.suggest_int("n_estimators", 100, 1000),
        "reg_alpha": trial.suggest_float("reg_alpha", 0, 10),
        "reg_lambda": trial.suggest_float("reg_lambda", 0, 10),
        "verbosity": -1,
    }

    model = lgb.LGBMClassifier(**params, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

    y_pred_proba = model.predict_proba(X_val)[:, 1]
    brier = brier_score_loss(y_val, y_pred_proba)

    return brier


def main():
    parser = argparse.ArgumentParser(description="Hyperparameter tuning with Optuna")
    parser.add_argument(
        "--model",
        type=str,
        choices=["xgboost", "lightgbm", "both"],
        default="both",
        help="Model to tune",
    )
    parser.add_argument(
        "--trials", type=int, default=200, help="Number of Optuna trials"
    )
    parser.add_argument(
        "--train-seasons",
        type=str,
        default="2016-2022",
        help="Training seasons (e.g., 2016-2022)",
    )
    parser.add_argument(
        "--val-seasons",
        type=str,
        default="2023",
        help="Validation seasons (e.g., 2023)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models",
        help="Output directory for tuned models",
    )

    args = parser.parse_args()

    # Parse seasons
    train_seasons = list(
        range(
            int(args.train_seasons.split("-")[0]),
            int(args.train_seasons.split("-")[1]) + 1,
        )
    )
    val_seasons = [int(s) for s in args.val_seasons.split(",")]

    # Load data
    X_train, y_train, X_val, y_val, feature_cols = load_data(train_seasons, val_seasons)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Tune XGBoost
    if args.model in ["xgboost", "both"]:
        logger.info("Tuning XGBoost...")
        study_xgb = optuna.create_study(direction="minimize")
        study_xgb.optimize(
            lambda trial: objective_xgboost(trial, X_train, y_train, X_val, y_val),
            n_trials=args.trials,
            show_progress_bar=True,
        )

        logger.info(f"Best XGBoost Brier score: {study_xgb.best_value:.4f}")
        logger.info(f"Best XGBoost params: {study_xgb.best_params}")

        # Save best model
        best_params = study_xgb.best_params.copy()
        best_params.update(
            {
                "objective": "binary:logistic",
                "eval_metric": "logloss",
                "tree_method": "hist",
                "random_state": 42,
                "n_jobs": -1,
            }
        )
        best_model_xgb = xgb.XGBClassifier(**best_params)
        best_model_xgb.fit(X_train, y_train)

        with open(output_dir / "xgboost_tuned.pkl", "wb") as f:
            pickle.dump(best_model_xgb, f)

        # Save study
        with open(output_dir / "xgboost_study.pkl", "wb") as f:
            pickle.dump(study_xgb, f)

    # Tune LightGBM
    if args.model in ["lightgbm", "both"]:
        logger.info("Tuning LightGBM...")
        study_lgb = optuna.create_study(direction="minimize")
        study_lgb.optimize(
            lambda trial: objective_lightgbm(trial, X_train, y_train, X_val, y_val),
            n_trials=args.trials,
            show_progress_bar=True,
        )

        logger.info(f"Best LightGBM Brier score: {study_lgb.best_value:.4f}")
        logger.info(f"Best LightGBM params: {study_lgb.best_params}")

        # Save best model
        best_params = study_lgb.best_params.copy()
        best_params.update(
            {
                "objective": "binary",
                "metric": "binary_logloss",
                "boosting_type": "gbdt",
                "random_state": 42,
                "n_jobs": -1,
                "verbosity": -1,
            }
        )
        best_model_lgb = lgb.LGBMClassifier(**best_params)
        best_model_lgb.fit(X_train, y_train)

        with open(output_dir / "lightgbm_tuned.pkl", "wb") as f:
            pickle.dump(best_model_lgb, f)

        # Save study
        with open(output_dir / "lightgbm_study.pkl", "wb") as f:
            pickle.dump(study_lgb, f)

    logger.info("Hyperparameter tuning complete!")


if __name__ == "__main__":
    main()
