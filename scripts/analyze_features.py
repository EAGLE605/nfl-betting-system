#!/usr/bin/env python3
"""Feature correlation analysis and selection.

Analyzes feature correlations and importance to identify redundant features.
"""

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.feature_selection import (
    analyze_feature_correlations,
    remove_redundant_features,
    select_features_by_importance,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze feature correlations and importance"
    )
    parser.add_argument(
        "--features",
        type=str,
        default="data/processed/features_2016_2024_improved.parquet",
        help="Path to features file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports/feature_analysis.csv",
        help="Output path for analysis results",
    )
    parser.add_argument(
        "--correlation-threshold",
        type=float,
        default=0.95,
        help="Correlation threshold for redundant features",
    )

    args = parser.parse_args()

    logger.info("Loading features...")
    df = pd.read_parquet(args.features)

    # Create target
    df["target"] = (df["home_score"] > df["away_score"]).astype(int)

    # Define feature columns (exclude metadata)
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
        "roof",
        "surface",  # Original categoricals
        # CRITICAL: Exclude ALL betting line features (data leakage)
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
    ]

    feature_cols = [col for col in df.columns if col not in exclude_cols]

    # Filter to numeric features only
    numeric_features = (
        df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
    )

    logger.info(f"Total features: {len(numeric_features)}")
    logger.info(f"Games: {len(df)}")

    # Fill missing values for analysis
    X = df[numeric_features].fillna(0)
    y = df["target"]

    # 1. Correlation analysis
    logger.info("\n" + "=" * 70)
    logger.info("CORRELATION ANALYSIS")
    logger.info("=" * 70)

    corr_pairs = analyze_feature_correlations(
        X, numeric_features, threshold=args.correlation_threshold
    )

    if len(corr_pairs) > 0:
        logger.info(
            f"Found {len(corr_pairs)} highly correlated pairs (>={args.correlation_threshold}):"
        )
        print(corr_pairs.to_string(index=False))
        corr_pairs.to_csv("reports/high_correlations.csv", index=False)
    else:
        logger.info("No highly correlated features found")

    # 2. Feature importance (mutual information)
    logger.info("\n" + "=" * 70)
    logger.info("FEATURE IMPORTANCE (Mutual Information)")
    logger.info("=" * 70)

    selected_features, importance_df = select_features_by_importance(
        X, y, numeric_features, min_importance=0.0
    )

    logger.info("\nTop 20 features by importance:")
    print(importance_df.head(20).to_string(index=False))

    # Save importance
    importance_df.to_csv("reports/feature_importance_mi.csv", index=False)

    # 3. Remove redundant features
    logger.info("\n" + "=" * 70)
    logger.info("REMOVING REDUNDANT FEATURES")
    logger.info("=" * 70)

    non_redundant = remove_redundant_features(
        X, numeric_features, correlation_threshold=args.correlation_threshold
    )

    logger.info(f"Original features: {len(numeric_features)}")
    logger.info(f"After removing redundant: {len(non_redundant)}")
    logger.info(f"Removed: {len(numeric_features) - len(non_redundant)} features")

    # 4. Summary
    logger.info("\n" + "=" * 70)
    logger.info("FEATURE SELECTION SUMMARY")
    logger.info("=" * 70)

    summary = {
        "total_features": len(numeric_features),
        "highly_correlated_pairs": len(corr_pairs),
        "redundant_features_removed": len(numeric_features) - len(non_redundant),
        "recommended_features": len(non_redundant),
        "top_10_features": importance_df.head(10)["feature"].tolist(),
    }

    summary_df = pd.DataFrame([summary])
    summary_df.to_csv(args.output, index=False)

    logger.info(f"\nSummary saved to: {args.output}")
    logger.info(f"\nRecommended feature set ({len(non_redundant)} features):")
    logger.info("  - Use these features for model training")
    logger.info(f"  - Top 10: {', '.join(summary['top_10_features'])}")

    # Save recommended features list
    pd.Series(non_redundant, name="feature").to_csv(
        "reports/recommended_features.csv", index=False
    )


if __name__ == "__main__":
    main()
