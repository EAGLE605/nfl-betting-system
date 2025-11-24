"""Weather features.

Extracts weather-related features from game data.
"""

import logging
from typing import List

import pandas as pd

from .base import FeatureBuilder

logger = logging.getLogger(__name__)


class WeatherFeatures(FeatureBuilder):
    """
    Weather features.

    Creates:
    - temp: Temperature (Fahrenheit)
    - wind: Wind speed (mph)
    - is_dome: 1 if indoor/dome stadium
    - is_cold: 1 if temperature < 40F
    - is_windy: 1 if wind > 15 mph
    """

    def get_required_columns(self) -> List[str]:
        return ["game_id"]

    def build(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build weather features."""
        self.validate_prerequisites(df)

        logger.info("Building weather features...")

        # Temperature
        if "temp" in df.columns:
            df["temp"] = df["temp"].fillna(
                df["temp"].median() if df["temp"].notna().any() else 65
            )
        else:
            df["temp"] = 65.0  # Default moderate temperature

        # Wind
        if "wind" in df.columns:
            df["wind"] = df["wind"].fillna(
                df["wind"].median() if df["wind"].notna().any() else 5
            )
        else:
            df["wind"] = 5.0  # Default low wind

        # Dome indicator (check roof column or stadium)
        if "roof" in df.columns:
            df["is_dome"] = (df["roof"].isin(["dome", "closed", "retractable"])).astype(
                int
            )
        elif "stadium" in df.columns:
            # Common dome stadiums
            dome_stadiums = [
                "Mercedes-Benz Superdome",
                "AT&T Stadium",
                "Lucas Oil Stadium",
                "Ford Field",
                "U.S. Bank Stadium",
                "NRG Stadium",
                "SoFi Stadium",
            ]
            df["is_dome"] = df["stadium"].isin(dome_stadiums).astype(int)
        else:
            df["is_dome"] = 0

        # Derived features
        df["is_cold"] = (df["temp"] < 40).astype(int)
        df["is_windy"] = (df["wind"] > 15).astype(int)

        logger.info(
            f"✓ Weather features created: {len(self.get_feature_names())} features"
        )

        return df

    def get_feature_names(self) -> List[str]:
        return ["temp", "wind", "is_dome", "is_cold", "is_windy"]
