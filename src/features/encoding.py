"""Categorical feature encoding.

Encodes categorical features like roof type, surface, weather conditions.
"""

from .base import FeatureBuilder
import pandas as pd
from typing import List
import logging

logger = logging.getLogger(__name__)


class CategoricalEncodingFeatures(FeatureBuilder):
    """
    Categorical feature encoding.

    Creates one-hot encoded features for:
    - Roof type (outdoor, dome, retractable)
    - Surface type (grass, turf)
    - Weather conditions (clear, rain, snow, etc.)
    """

    def get_required_columns(self) -> List[str]:
        return ["roof", "surface"]

    def build(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build categorical encoding features."""
        # Check for required columns (some may be missing)
        missing = [col for col in self.get_required_columns() if col not in df.columns]
        if missing:
            logger.warning(f"Missing columns for encoding: {missing}, using defaults")

        logger.info("Building categorical encoding features...")

        # Roof type encoding
        if "roof" in df.columns:
            roof_dummies = pd.get_dummies(df["roof"], prefix="roof", dummy_na=False)
            # Ensure we have standard columns
            for roof_type in ["outdoors", "dome", "closed", "open"]:
                col_name = f"roof_{roof_type}"
                if col_name not in roof_dummies.columns:
                    roof_dummies[col_name] = 0
            df = pd.concat([df, roof_dummies], axis=1)
        else:
            # Add dummy columns if roof not available
            df["roof_outdoors"] = 1
            df["roof_dome"] = 0
            df["roof_closed"] = 0
            df["roof_open"] = 0

        # Surface type encoding
        if "surface" in df.columns:
            surface_dummies = pd.get_dummies(df["surface"], prefix="surface", dummy_na=False)
            # Ensure we have standard columns
            for surface_type in ["grass", "turf", "fieldturf"]:
                col_name = f"surface_{surface_type}"
                if col_name not in surface_dummies.columns:
                    surface_dummies[col_name] = 0
            df = pd.concat([df, surface_dummies], axis=1)
        else:
            # Add dummy columns if surface not available
            df["surface_grass"] = 1
            df["surface_turf"] = 0

        # Temperature encoding (buckets)
        if "temp" in df.columns:
            df["temp_cold"] = (df["temp"] < 40).astype(int)
            df["temp_moderate"] = ((df["temp"] >= 40) & (df["temp"] < 70)).astype(int)
            df["temp_warm"] = (df["temp"] >= 70).astype(int)
            df["temp_missing"] = df["temp"].isna().astype(int)
        else:
            df["temp_cold"] = 0
            df["temp_moderate"] = 1
            df["temp_warm"] = 0
            df["temp_missing"] = 1

        # Wind encoding
        if "wind" in df.columns:
            df["wind_high"] = (df["wind"] > 15).astype(int)
            df["wind_moderate"] = ((df["wind"] > 5) & (df["wind"] <= 15)).astype(int)
            df["wind_low"] = (df["wind"] <= 5).astype(int)
            df["wind_missing"] = df["wind"].isna().astype(int)
        else:
            df["wind_high"] = 0
            df["wind_moderate"] = 0
            df["wind_low"] = 1
            df["wind_missing"] = 1

        logger.info(f"✓ Categorical encoding features created: {len(self.get_feature_names())} features")

        return df

    def get_feature_names(self) -> List[str]:
        return [
            "roof_outdoors",
            "roof_dome",
            "roof_closed",
            "roof_open",
            "surface_grass",
            "surface_turf",
            "temp_cold",
            "temp_moderate",
            "temp_warm",
            "temp_missing",
            "wind_high",
            "wind_moderate",
            "wind_low",
            "wind_missing",
        ]

