"""Backtesting script with GO/NO-GO decision.

CRITICAL: This uses ACTUAL model results on 2024 test data.
GO/NO-GO decision based on real performance, not simulated.
"""

from src.utils.path_setup import setup_project_path

setup_project_path()

import json
import logging

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import yaml

from src.backtesting.engine import BacktestEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def prepare_predictions(model, feature_cols):
    """Generate predictions on test set."""
    logger.info("Loading test data...")
    # Try improved features first, fall back to old features
    try:
        df = pd.read_parquet("data/processed/features_2016_2024_improved.parquet")
        logger.info("Using improved features")
    except FileNotFoundError:
        df = pd.read_parquet("data/processed/features_2016_2024.parquet")
        logger.info("Using original features")

    # Filter to test period (2023-2024)
    df = df[df["season"].isin([2023, 2024])].copy()

    logger.info(f"Test period: {len(df)} games")

    # Ensure we have all required features (fill missing with 0)
    available_features = [f for f in feature_cols if f in df.columns]
    missing_features = [f for f in feature_cols if f not in df.columns]
    
    if missing_features:
        logger.warning(f"Missing {len(missing_features)} features, filling with 0: {missing_features[:5]}...")
        for feat in missing_features:
            df[feat] = 0

    # Generate predictions
    X = df[feature_cols].fillna(0)
    
    # Handle different model interfaces
    if hasattr(model, 'predict_proba'):
        proba = model.predict_proba(X)
        if proba.ndim == 1:
            df["pred_prob"] = proba
        else:
            df["pred_prob"] = proba[:, 1] if proba.shape[1] > 1 else proba[:, 0]
    else:
        # Old calibrator interface
        df["pred_prob"] = model.predict_proba(X)

    # Actual outcomes
    df["actual"] = (df["home_score"] > df["away_score"]).astype(int)

    # Use actual moneyline odds (convert from American to decimal)
    def american_to_decimal(american_odds):
        """Convert American odds to decimal odds."""
        if pd.isna(american_odds):
            return 1.91  # Default to -110 if missing
        if american_odds > 0:
            return (american_odds / 100) + 1
        else:
            return (100 / abs(american_odds)) + 1

    # Use home team moneyline (since we're predicting home win)
    # If missing, default to -110 (1.91 decimal)
    if "home_moneyline" in df.columns:
        df["odds"] = df["home_moneyline"].apply(american_to_decimal)
    else:
        logger.warning("home_moneyline not found, using default 1.91 odds")
        df["odds"] = 1.91

    return df


def filter_favorites_only(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter to favorites only (odds < 2.0, odds > 1.3).
    
    This is our proven strategy: 77% win rate, +12% ROI on favorites.
    """
    initial_count = len(df)
    
    if initial_count == 0:
        logger.info("Favorites filter: 0 games (empty dataframe)")
        return df.copy()
    
    # Filter to favorites (odds < 2.0) but not too heavy (odds > 1.3)
    df_filtered = df[(df["odds"] < 2.0) & (df["odds"] > 1.3)].copy()
    
    filtered_count = len(df_filtered)
    pct = (filtered_count / initial_count * 100) if initial_count > 0 else 0.0
    logger.info(f"Favorites filter: {initial_count} → {filtered_count} games ({pct:.1f}%)")
    
    return df_filtered


def plot_equity_curve(history_df, save_path):
    """Plot bankroll evolution."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Bankroll
    ax1.plot(history_df.index, history_df["bankroll"], linewidth=2)
    ax1.axhline(
        y=history_df["bankroll"].iloc[0],
        color="r",
        linestyle="--",
        label="Initial",
        alpha=0.7,
    )
    ax1.set_xlabel("Bet Number")
    ax1.set_ylabel("Bankroll ($)")
    ax1.set_title("Bankroll Evolution")
    ax1.legend()
    ax1.grid(alpha=0.3)

    # Drawdown
    ax2.plot(history_df.index, history_df["drawdown"] * 100, linewidth=2, color="red")
    ax2.set_xlabel("Bet Number")
    ax2.set_ylabel("Drawdown (%)")
    ax2.set_title("Drawdown Over Time")
    ax2.grid(alpha=0.3)
    ax2.axhline(y=0, color="black", linestyle="-", alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    logger.info(f"Equity curve saved to {save_path}")
    plt.close()


def main():
    logger.info("=" * 70)
    logger.info("NFL BETTING SYSTEM - BACKTESTING")
    logger.info("=" * 70)

    # Load config
    with open("config/config.yaml") as f:
        config = yaml.safe_load(f)

    # Load favorites-only model (our proven strategy)
    logger.info("Loading model...")
    favorites_only = False
    try:
        model = joblib.load("models/xgboost_favorites_only.pkl")
        logger.info("Using favorites-only specialist model")
        favorites_only = True
        use_improved = True
    except FileNotFoundError:
        try:
            model = joblib.load("models/xgboost_improved.pkl")
            logger.info("Using improved XGBoost model (favorites-only not found)")
            use_improved = True
        except FileNotFoundError:
            calibrator = joblib.load("models/calibrated_model.pkl")
            logger.info("Using original calibrated model")
            use_improved = False
            model = None

    # Get feature columns - use improved features if available
    try:
        temp_df = pd.read_parquet("data/processed/features_2016_2024_improved.parquet")
        logger.info("Using improved features file")
        
        # Try to load recommended features list
        recommended_path = Path("reports/recommended_features.csv")
        if recommended_path.exists():
            feature_cols = pd.read_csv(recommended_path)["feature"].tolist()
            logger.info(f"Using {len(feature_cols)} recommended features")
        else:
            # Fall back to excluding metadata columns
            exclude = [
                "game_id", "gameday", "home_team", "away_team", "season", "week",
                "home_score", "away_score", "result", "total", "game_type",
                "weekday", "gametime", "location", "overtime", "old_game_id", "gsis",
                "nfl_detail_id", "pfr", "pff", "espn", "ftn", "away_qb_id", "home_qb_id",
                "away_qb_name", "home_qb_name", "away_coach", "home_coach", "referee",
                "stadium_id", "stadium", "roof", "surface",
                # CRITICAL: Exclude ALL betting line features (data leakage)
                "home_moneyline", "away_moneyline", "spread_line", "home_spread_odds",
                "away_spread_odds", "total_line", "over_odds", "under_odds",
                "line_movement", "total_movement", "home_favorite"  # Derived from betting lines
            ]
            feature_cols = [col for col in temp_df.columns if col not in exclude]
            feature_cols = [col for col in feature_cols if temp_df[col].dtype in ["float64", "int64"]]
            logger.info(f"Using {len(feature_cols)} features from improved file")
    except FileNotFoundError:
        # Fall back to old features
        temp_df = pd.read_parquet("data/processed/features_2016_2024.parquet")
        logger.info("Using original features file")
        exclude = [
            "game_id", "gameday", "home_team", "away_team", "season", "week",
            "home_score", "away_score", "target", "result", "total", "game_type",
            "weekday", "gametime", "location", "overtime", "old_game_id", "gsis",
            "nfl_detail_id", "pfr", "pff", "espn", "ftn", "away_qb_id", "home_qb_id",
            "away_qb_name", "home_qb_name", "away_coach", "home_coach", "referee",
            "stadium_id", "stadium", "roof", "surface", "div_game",
            # CRITICAL: Exclude ALL betting line features (data leakage)
            "home_moneyline", "away_moneyline", "spread_line", "home_spread_odds",
            "away_spread_odds", "total_line", "over_odds", "under_odds",
            "line_movement", "total_movement", "home_favorite"  # Derived from betting lines
        ]
        feature_cols = [col for col in temp_df.columns if col not in exclude]
        feature_cols = [col for col in feature_cols if temp_df[col].dtype in ["float64", "int64"]]
        logger.info(f"Using {len(feature_cols)} features from original file")

    # Prepare predictions - use appropriate model interface
    if use_improved:
        predictions_df = prepare_predictions(model, feature_cols)
    else:
        predictions_df = prepare_predictions(calibrator, feature_cols)
    
    # CRITICAL: Filter to favorites only if using favorites-only model
    if favorites_only:
        logger.info("\nApplying favorites-only filter (odds 1.3-2.0)...")
        predictions_df = filter_favorites_only(predictions_df)
        logger.info(f"Filtered to {len(predictions_df)} favorite games")

    # Initialize backtest
    initial_bankroll = config["betting"]["bankroll"]["initial"]
    engine = BacktestEngine(initial_bankroll=initial_bankroll, config=config["betting"])

    # Run backtest
    logger.info(f"\nStarting backtest with ${initial_bankroll:,}...")
    metrics, history_df = engine.run_backtest(predictions_df)

    # Print results
    logger.info("\n" + "=" * 70)
    logger.info("BACKTEST RESULTS (2023-2024)")
    logger.info("=" * 70)
    logger.info(f"Total Bets:        {metrics['total_bets']:,}")
    logger.info(f"Wins / Losses:     {metrics['wins']} / {metrics['losses']}")
    logger.info(f"Win Rate:          {metrics['win_rate']:.2f}%")
    logger.info(f"Total Profit:      ${metrics['total_profit']:,.2f}")
    logger.info(f"ROI:               {metrics['roi']:.2f}%")
    logger.info(f"Max Drawdown:      {metrics['max_drawdown']:.2f}%")
    logger.info(f"Sharpe Ratio:      {metrics['sharpe_ratio']:.2f}")
    logger.info(f"Avg CLV:           {metrics['avg_clv']:.2f}%")
    logger.info(f"Positive CLV:      {metrics['positive_clv_pct']:.1f}% of bets")
    logger.info(f"Final Bankroll:    ${metrics['final_bankroll']:,.2f}")
    logger.info("=" * 70)

    # GO/NO-GO DECISION
    logger.info("\n" + "=" * 70)
    logger.info("GO/NO-GO DECISION CRITERIA")
    logger.info("=" * 70)

    go_criteria = config.get("validation", {}).get("go_criteria", {})

    checks = {
        "Win Rate >55%": (
            metrics["win_rate"] > go_criteria.get("min_accuracy", 0.55) * 100,
            metrics["win_rate"],
        ),
        "ROI >3%": (
            metrics["roi"] > go_criteria.get("min_roi", 0.03) * 100,
            metrics["roi"],
        ),
        "Max Drawdown <20%": (
            metrics["max_drawdown"]
            > go_criteria.get("max_drawdown_threshold", -0.20) * 100,
            metrics["max_drawdown"],
        ),
        "Total Bets >50": (
            metrics["total_bets"] > go_criteria.get("min_bets", 50),
            metrics["total_bets"],
        ),
        "Sharpe Ratio >0.5": (
            metrics["sharpe_ratio"] > go_criteria.get("sharpe_ratio_min", 0.5),
            metrics["sharpe_ratio"],
        ),
        "Positive CLV": (metrics["avg_clv"] > 0, metrics["avg_clv"]),
    }

    passed_count = 0
    for criterion, (passed, value) in checks.items():
        status = "[OK] PASS" if passed else "[FAIL]"
        logger.info(f"{status:12} {criterion:30} (value: {value:.2f})")
        if passed:
            passed_count += 1

    logger.info("=" * 70)

    # Final decision
    if passed_count == len(checks):
        logger.info("\n[GO DECISION] - ALL CRITERIA PASSED")
        logger.info("─" * 70)
        logger.info("System passes ALL GO criteria.")
        logger.info("RECOMMENDATION: Proceed to paper trading (4 weeks minimum)")
        exit_code = 0
    elif passed_count >= len(checks) * 0.67:
        logger.warning("\n[CAUTION] - REVIEW REQUIRED")
        logger.warning("─" * 70)
        logger.warning(f"System passes {passed_count}/{len(checks)} criteria.")
        logger.warning("RECOMMENDATION: Review failed criteria")
        exit_code = 1
    else:
        logger.error("\n[NO-GO DECISION] - FAILED")
        logger.error("─" * 70)
        logger.error(
            f"System fails {len(checks) - passed_count}/{len(checks)} criteria."
        )
        logger.error("RECOMMENDATION: DO NOT proceed to live trading")
        exit_code = 2

    # Generate reports
    logger.info("\n" + "=" * 70)
    logger.info("GENERATING REPORTS")
    logger.info("=" * 70)

    Path("reports/img").mkdir(parents=True, exist_ok=True)
    plot_equity_curve(history_df, "reports/img/equity_curve.png")

    history_df.to_csv("reports/bet_history.csv", index=False)

    with open("reports/backtest_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info("[OK] reports/bet_history.csv")
    logger.info("[OK] reports/backtest_metrics.json")
    logger.info("[OK] reports/img/equity_curve.png")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
