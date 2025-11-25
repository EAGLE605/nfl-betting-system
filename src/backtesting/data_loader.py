"""Data loader for backtesting.

Loads historical game data for walk-forward backtesting.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


class BacktestDataLoader:
    """Load historical data for backtesting."""

    def __init__(self, data_dir: str = "data"):
        """
        Initialize data loader.

        Args:
            data_dir: Base data directory
        """
        self.data_dir = Path(data_dir)
        self.schedules_dir = self.data_dir / "schedules"
        self.pbp_dir = self.data_dir / "play_by_play"
        self.raw_dir = self.data_dir / "raw"

    def load_historical_games(
        self,
        seasons: Optional[List[int]] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Load historical game schedules.

        Args:
            seasons: List of specific seasons (e.g., [2020, 2021, 2022])
            start_year: Start year (alternative to seasons list)
            end_year: End year (alternative to seasons list)

        Returns:
            DataFrame with game schedules
        """
        if seasons is None:
            if start_year is None or end_year is None:
                raise ValueError("Must provide either seasons or start_year/end_year")
            seasons = list(range(start_year, end_year + 1))

        logger.info(f"Loading schedules for seasons: {seasons}")

        # Try to load from consolidated parquet first
        try:
            min_season = min(seasons)
            max_season = max(seasons)
            consolidated_path = (
                self.raw_dir / f"schedules_{min_season}_{max_season}.parquet"
            )

            if consolidated_path.exists():
                logger.info(f"Loading from consolidated file: {consolidated_path}")
                df = pd.read_parquet(consolidated_path)
                # Filter to requested seasons
                df = df[df["season"].isin(seasons)]
                logger.info(f"Loaded {len(df)} games")
                return df

        except Exception as e:
            logger.warning(f"Could not load consolidated file: {e}")

        # Fall back to loading individual season files
        dataframes = []
        for season in seasons:
            season_path = self.schedules_dir / f"{season}.csv"

            if not season_path.exists():
                logger.warning(f"Schedule not found for season {season}")
                continue

            try:
                df = pd.read_csv(season_path)
                df["season"] = season
                dataframes.append(df)
                logger.info(f"Loaded {len(df)} games from season {season}")
            except Exception as e:
                logger.error(f"Failed to load season {season}: {e}")

        if not dataframes:
            raise FileNotFoundError(f"No schedule data found for seasons {seasons}")

        combined_df = pd.concat(dataframes, ignore_index=True)
        logger.info(f"Total games loaded: {len(combined_df)}")

        return combined_df

    def load_play_by_play(
        self,
        seasons: Optional[List[int]] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> Optional[pd.DataFrame]:
        """
        Load play-by-play data for EPA features.

        Args:
            seasons: List of specific seasons
            start_year: Start year
            end_year: End year

        Returns:
            DataFrame with play-by-play data, or None if not available
        """
        if seasons is None:
            if start_year is None or end_year is None:
                return None
            seasons = list(range(start_year, end_year + 1))

        logger.info(f"Loading play-by-play for seasons: {seasons}")

        # Try consolidated parquet first
        try:
            min_season = min(seasons)
            max_season = max(seasons)
            consolidated_path = self.raw_dir / f"pbp_{min_season}_{max_season}.parquet"

            if consolidated_path.exists():
                logger.info(f"Loading from consolidated PBP file: {consolidated_path}")
                df = pd.read_parquet(consolidated_path)
                # Filter to requested seasons
                if "season" in df.columns:
                    df = df[df["season"].isin(seasons)]
                logger.info(f"Loaded {len(df)} plays")
                return df

        except Exception as e:
            logger.warning(f"Could not load consolidated PBP file: {e}")

        # Try individual season files
        dataframes = []
        for season in seasons:
            pbp_path = self.pbp_dir / f"{season}.csv"

            if not pbp_path.exists():
                logger.debug(f"PBP not found for season {season}")
                continue

            try:
                df = pd.read_csv(pbp_path)
                if "season" not in df.columns:
                    df["season"] = season
                dataframes.append(df)
                logger.info(f"Loaded {len(df)} plays from season {season}")
            except Exception as e:
                logger.warning(f"Failed to load PBP for season {season}: {e}")

        if not dataframes:
            logger.warning("No play-by-play data found")
            return None

        combined_df = pd.concat(dataframes, ignore_index=True)
        logger.info(f"Total plays loaded: {len(combined_df)}")

        return combined_df

    def get_backtest_data(
        self, data_period: Dict[str, any]
    ) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
        """
        Load data for backtesting based on period specification.

        Args:
            data_period: Dict with:
                - start_year: int
                - end_year: int
                - focus: "recent" or "full"

        Returns:
            Tuple of (schedules_df, pbp_df)
        """
        start_year = data_period.get("start_year")
        end_year = data_period.get("end_year")

        schedules = self.load_historical_games(start_year=start_year, end_year=end_year)
        pbp = self.load_play_by_play(start_year=start_year, end_year=end_year)

        return schedules, pbp

    def get_available_seasons(self) -> List[int]:
        """
        Get list of available seasons.

        Returns:
            List of available season years
        """
        seasons = []

        # Check schedules directory
        if self.schedules_dir.exists():
            for file in self.schedules_dir.glob("*.csv"):
                try:
                    season = int(file.stem)
                    seasons.append(season)
                except ValueError:
                    pass

        # Check raw directory for consolidated files
        if self.raw_dir.exists():
            for file in self.raw_dir.glob("schedules_*.parquet"):
                try:
                    # Extract years from filename like "schedules_2016_2024.parquet"
                    parts = file.stem.split("_")
                    if len(parts) >= 3:
                        start = int(parts[1])
                        end = int(parts[2])
                        seasons.extend(range(start, end + 1))
                except (ValueError, IndexError):
                    pass

        return sorted(set(seasons))

    def validate_data_availability(
        self, start_year: int, end_year: int
    ) -> Dict[str, any]:
        """
        Check what data is available for requested period.

        Args:
            start_year: Start year
            end_year: End year

        Returns:
            Dict with availability info
        """
        available_seasons = self.get_available_seasons()
        requested_seasons = list(range(start_year, end_year + 1))

        missing_seasons = [s for s in requested_seasons if s not in available_seasons]

        return {
            "available_seasons": available_seasons,
            "requested_seasons": requested_seasons,
            "missing_seasons": missing_seasons,
            "has_all_data": len(missing_seasons) == 0,
            "coverage_pct": (
                (len(requested_seasons) - len(missing_seasons))
                / len(requested_seasons)
                * 100
                if requested_seasons
                else 0
            ),
        }
