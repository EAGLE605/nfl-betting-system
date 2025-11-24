"""Betting line features.

Extracts and creates features from betting lines (spread, total, odds).
"""

import logging
from typing import List

import pandas as pd

from .base import FeatureBuilder

logger = logging.getLogger(__name__)


class LineFeatures(FeatureBuilder):
    """
    Betting line features.

    Creates:
    - spread_line: Point spread (negative = home favorite)
    - total_line: Over/under total points
    - line_movement: Change in spread from open to close (if available)
    - total_movement: Change in total from open to close (if available)
    - home_favorite: 1 if home team is favorite (spread < 0)
    """

    def get_required_columns(self) -> List[str]:
        return ["game_id"]

    def build(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build line features."""
        self.validate_prerequisites(df)

        logger.info("Building line features...")

        # Check which line columns exist
        has_spread = "spread_line" in df.columns
        has_total = "total_line" in df.columns
        has_spread_open = "spread_open" in df.columns
        has_total_open = "total_open" in df.columns

        # Spread features
        if has_spread:
            df["spread_line"] = df["spread_line"].fillna(0)
            df["home_favorite"] = (df["spread_line"] < 0).astype(int)
        else:
            df["spread_line"] = 0.0
            df["home_favorite"] = 0

        # Total features
        if has_total:
            df["total_line"] = df["total_line"].fillna(
                df["total_line"].median() if df["total_line"].notna().any() else 45
            )
        else:
            df["total_line"] = 45.0  # Default NFL total

        # Line movement (if available)
        if has_spread_open and has_spread:
            df["line_movement"] = (df["spread_line"] - df["spread_open"]).fillna(0)
        else:
            df["line_movement"] = 0.0

        if has_total_open and has_total:
            df["total_movement"] = (df["total_line"] - df["total_open"]).fillna(0)
        else:
            df["total_movement"] = 0.0

        logger.info(
            f"✓ Line features created: {len(self.get_feature_names())} features"
        )

        return df

    def get_feature_names(self) -> List[str]:
        return [
            "spread_line",
            "total_line",
            "line_movement",
            "total_movement",
            "home_favorite",
        ]
