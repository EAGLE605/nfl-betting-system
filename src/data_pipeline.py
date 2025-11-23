"""
NFL Data Pipeline
=================

Downloads and validates NFL data from nfl_data_py (nflverse).
Handles caching, validation, and error recovery.

Author: NFL Betting System
Date: 2025-11-23
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import time

import pandas as pd
import nfl_data_py as nfl
from tqdm import tqdm

# Per-module logging (not module-level config)
logger = logging.getLogger(__name__)


class NFLDataPipeline:
    """
    Pipeline for downloading and validating NFL data from nflverse.
    
    Features:
    - Smart caching (avoids re-downloading completed seasons)
    - Data validation (schema, nulls, ranges)
    - Error handling with retries
    - Progress tracking and metadata
    
    Attributes:
        data_dir: Root directory for data storage
        raw_dir: Directory for raw downloaded data
        cache_days: Number of days before re-downloading current season data
    """
    
    def __init__(
        self,
        data_dir: str = "data",
        cache_days: int = 7,
        max_retries: int = 3,
        strict_mode: bool = False
    ):
        """
        Initialize the data pipeline.
        
        Args:
            data_dir: Root directory for data storage
            cache_days: Days before re-downloading current season data
            max_retries: Maximum number of retry attempts for failed downloads
        """
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.cache_days = cache_days
        self.max_retries = max_retries
        self.strict_mode = strict_mode
        
        # Create directories
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized NFLDataPipeline (data_dir={self.data_dir}, strict_mode={strict_mode})")
    
    def _should_download(
        self,
        filepath: Path,
        seasons: List[int]
    ) -> bool:
        """
        Determine if data should be downloaded based on cache status.
        
        Args:
            filepath: Path to the cached file
            seasons: List of seasons in the cached file
            
        Returns:
            True if data should be downloaded, False if cache is valid
        """
        if not filepath.exists():
            return True
        
        # Check file age
        file_age = datetime.now() - datetime.fromtimestamp(filepath.stat().st_mtime)
        
        # If all seasons are completed (< current year), never re-download
        current_year = datetime.now().year
        all_completed = all(season < current_year for season in seasons)
        
        if all_completed:
            logger.info(f"✓ Using cached {filepath.name} (all seasons completed)")
            return False
        
        # If includes current season, re-download if older than cache_days
        if file_age > timedelta(days=self.cache_days):
            logger.info(f"↻ Cache expired for {filepath.name} ({file_age.days} days old)")
            return True
        
        logger.info(f"✓ Using cached {filepath.name} ({file_age.days} days old)")
        return False
    
    def _check_file_integrity(self, filepath: Path, expected_rows: Optional[int] = None) -> bool:
        """
        Verify cached file has correct row count.
        
        Args:
            filepath: Path to cached file
            expected_rows: Expected number of rows (optional)
            
        Returns:
            True if integrity check passes, False otherwise
        """
        if not filepath.exists():
            return False
        
        try:
            df = pd.read_parquet(filepath)
            if expected_rows and len(df) != expected_rows:
                logger.warning(
                    f"⚠ Integrity fail: {filepath.name} has {len(df)} rows, "
                    f"expected {expected_rows}"
                )
                return False
            return True
        except Exception as e:
            logger.warning(f"⚠ Integrity check failed for {filepath.name}: {e}")
            return False
    
    def _retry_download(
        self,
        download_func: callable,
        data_type: str,
        **kwargs
    ) -> Optional[pd.DataFrame]:
        """
        Execute download function with retry logic.
        
        Args:
            download_func: Function to call for download
            data_type: Name of data type for logging
            **kwargs: Arguments to pass to download function
            
        Returns:
            Downloaded DataFrame or None if all retries failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Downloading {data_type} (attempt {attempt}/{self.max_retries})...")
                df = download_func(**kwargs)
                logger.info(f"✓ Downloaded {len(df):,} rows of {data_type}")
                return df
            except Exception as e:
                logger.error(f"✗ Download failed (attempt {attempt}/{self.max_retries}): {e}")
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"✗ All retry attempts failed for {data_type}")
                    return None
    
    def get_schedules(
        self,
        seasons: List[int],
        force_download: bool = False
    ) -> pd.DataFrame:
        """
        Download NFL game schedules.
        
        Contains: game results, scores, home/away teams, dates, etc.
        Critical for: Training labels (game outcomes), team matchups
        
        Args:
            seasons: List of seasons to download (e.g., [2016, 2017, 2018])
            force_download: If True, ignore cache and re-download
            
        Returns:
            DataFrame with game schedule data
            
        Raises:
            ValueError: If download fails after all retries
        """
        filepath = self.raw_dir / f"schedules_{min(seasons)}_{max(seasons)}.parquet"
        
        if not force_download and not self._should_download(filepath, seasons):
            return pd.read_parquet(filepath)
        
        df = self._retry_download(nfl.import_schedules, "schedules", years=seasons)
        
        if df is None:
            raise ValueError("Failed to download schedules after all retries")
        
        # Validate
        self.validate_data(
            df,
            required_columns=['game_id', 'season', 'gameday', 'home_team', 'away_team'],
            data_type='schedules'
        )
        
        # Save
        df.to_parquet(filepath, index=False)
        logger.info(f"✓ Saved schedules to {filepath}")
        
        return df
    
    def get_play_by_play(
        self,
        seasons: List[int],
        force_download: bool = False
    ) -> pd.DataFrame:
        """
        Download play-by-play data.
        
        Contains: Every play, EPA, success_rate, WPA, etc.
        Critical for: Advanced features (EPA/play, success rate, play distribution)
        Note: Large dataset (~50K plays/season = ~450K rows for 9 seasons)
        
        Args:
            seasons: List of seasons to download
            force_download: If True, ignore cache and re-download
            
        Returns:
            DataFrame with play-by-play data
            
        Raises:
            ValueError: If download fails after all retries
        """
        filepath = self.raw_dir / f"pbp_{min(seasons)}_{max(seasons)}.parquet"
        
        if not force_download and not self._should_download(filepath, seasons):
            return pd.read_parquet(filepath)
        
        df = self._retry_download(nfl.import_pbp_data, "play-by-play", years=seasons)
        
        if df is None:
            raise ValueError("Failed to download play-by-play data after all retries")
        
        # Validate
        self.validate_data(
            df,
            required_columns=['game_id', 'play_id', 'posteam', 'defteam', 'epa'],
            data_type='play-by-play'
        )
        
        # Save
        df.to_parquet(filepath, index=False)
        logger.info(f"✓ Saved play-by-play to {filepath}")
        
        return df
    
    def get_weekly_stats(
        self,
        seasons: List[int],
        stat_type: str = 'offense',
        force_download: bool = False
    ) -> pd.DataFrame:
        """
        Download weekly team statistics.
        
        Contains: Team performance metrics by week (passing yards, rushing yards, etc.)
        Critical for: Team form, recent performance trends
        
        Args:
            seasons: List of seasons to download
            stat_type: Type of stats ('offense', 'defense', or 'special')
            force_download: If True, ignore cache and re-download
            
        Returns:
            DataFrame with weekly stats
            
        Raises:
            ValueError: If download fails after all retries
        """
        filepath = self.raw_dir / f"weekly_{stat_type}_{min(seasons)}_{max(seasons)}.parquet"
        
        if not force_download and not self._should_download(filepath, seasons):
            return pd.read_parquet(filepath)
        
        df = self._retry_download(
            nfl.import_weekly_data,
            f"weekly {stat_type} stats",
            years=seasons
        )
        
        if df is None:
            raise ValueError(f"Failed to download weekly {stat_type} stats after all retries")
        
        # Validate
        self.validate_data(
            df,
            required_columns=['season', 'week', 'player_id', 'recent_team'],
            data_type=f'weekly_{stat_type}'
        )
        
        # Save
        df.to_parquet(filepath, index=False)
        logger.info(f"✓ Saved weekly {stat_type} stats to {filepath}")
        
        return df
    
    def get_team_descriptions(self) -> pd.DataFrame:
        """
        Download team descriptions and metadata.
        
        Contains: Team abbreviations, colors, divisions, conferences
        Critical for: Team mapping, validation
        
        Returns:
            DataFrame with team metadata
        """
        filepath = self.raw_dir / "teams.parquet"
        
        # Teams data rarely changes, so cache indefinitely
        if filepath.exists():
            logger.info(f"✓ Using cached {filepath.name}")
            return pd.read_parquet(filepath)
        
        df = self._retry_download(nfl.import_team_desc, "team descriptions")
        
        if df is None:
            raise ValueError("Failed to download team descriptions after all retries")
        
        df.to_parquet(filepath, index=False)
        logger.info(f"✓ Saved team descriptions to {filepath}")
        
        return df
    
    def validate_data(
        self,
        df: pd.DataFrame,
        required_columns: List[str],
        data_type: str,
        expected_rows: Optional[int] = None
    ) -> None:
        """
        Validate data quality.
        
        Checks:
        1. Schema: Required columns exist
        2. Nulls: Critical columns are not null
        3. Size: DataFrame is not empty
        4. Row count: Within 10% of expected (if provided)
        
        Args:
            df: DataFrame to validate
            required_columns: List of columns that must exist and not be null
            data_type: Name of data type for error messages
            expected_rows: Expected number of rows (optional)
            
        Raises:
            ValueError: If validation fails
        """
        # Check if DataFrame is empty
        if df.empty:
            raise ValueError(f"Validation failed: {data_type} DataFrame is empty")
        
        # Check for required columns
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(
                f"Validation failed: {data_type} missing columns: {missing_cols}"
            )
        
        # Check row count within 10% of expected
        if expected_rows and not (expected_rows * 0.9 < len(df) < expected_rows * 1.1):
            logger.warning(
                f"⚠ Row count {len(df)} outside expected ~{expected_rows} "
                f"(±10%: {int(expected_rows * 0.9)}-{int(expected_rows * 1.1)})"
            )
        
        # Check for nulls in required columns
        null_counts = df[required_columns].isnull().sum()
        null_cols = null_counts[null_counts > 0]
        
        if not null_cols.empty:
            logger.warning(
                f"⚠ {data_type} has nulls in critical columns:\n{null_cols}"
            )
            # Fail on nulls in strict mode
            if self.strict_mode:
                raise ValueError(
                    f"Validation failed: {data_type} has nulls in critical columns: {null_cols.to_dict()}"
                )
        
        logger.info(f"✓ Validation passed for {data_type} ({len(df):,} rows)")
    
    def download_all(
        self,
        seasons: List[int],
        include_pbp: bool = True,
        force_download: bool = False
    ) -> Dict[str, pd.DataFrame]:
        """
        Download all essential data for the betting system.
        
        Uses parallel downloads with progress bars for better UX.
        
        Args:
            seasons: List of seasons to download
            include_pbp: Whether to download play-by-play (large dataset)
            force_download: If True, ignore cache and re-download all
            
        Returns:
            Dictionary mapping data type to DataFrame
        """
        logger.info(f"Starting download for seasons {min(seasons)}-{max(seasons)}")
        start_time = time.time()
        
        results = {}
        
        # Prepare download tasks
        tasks = [
            ('schedules', self.get_schedules, (seasons,), {'force_download': force_download}),
            ('teams', self.get_team_descriptions, (), {}),
            ('weekly_offense', self.get_weekly_stats, (seasons, 'offense'), {'force_download': force_download}),
        ]
        
        if include_pbp:
            tasks.append(
                ('pbp', self.get_play_by_play, (seasons,), {'force_download': force_download})
            )
        
        # Download with progress bar
        with ThreadPoolExecutor(max_workers=4) as executor:
            with tqdm(total=len(tasks), desc="Downloading", unit="dataset") as pbar:
                futures = {}
                for name, func, args, kwargs in tasks:
                    future = executor.submit(func, *args, **kwargs)
                    futures[future] = name
                
                for future in as_completed(futures):
                    name = futures[future]
                    try:
                        results[name] = future.result()
                        pbar.update(1)
                        time.sleep(1)  # Rate limiting
                    except Exception as e:
                        logger.error(f"✗ Failed to download {name}: {e}")
                        if name in ['schedules', 'teams']:
                            # Critical failures should raise
                            raise
                        # Non-critical failures continue
                        pbar.update(1)
        
        # Save metadata
        self._save_metadata(seasons, results)
        
        elapsed = time.time() - start_time
        logger.info(f"✓ Download complete in {elapsed:.1f} seconds")
        
        return results
    
    def _save_metadata(
        self,
        seasons: List[int],
        results: Dict[str, pd.DataFrame]
    ) -> None:
        """
        Save metadata about the download.
        
        Args:
            seasons: List of seasons downloaded
            results: Dictionary of downloaded DataFrames
        """
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'seasons': seasons,
            'data_types': {
                name: {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'size_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
                }
                for name, df in results.items()
            }
        }
        
        metadata_path = self.raw_dir / 'metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"✓ Saved metadata to {metadata_path}")


def get_available_seasons() -> List[int]:
    """
    Get list of available NFL seasons.
    
    Returns:
        List of seasons from 1999 to current year
    """
    current_year = datetime.now().year
    # NFL season year refers to the year it starts (e.g., 2024 season runs 2024-2025)
    return list(range(1999, current_year + 1))


if __name__ == "__main__":
    # Example usage
    pipeline = NFLDataPipeline()
    
    # Download recent seasons
    seasons = list(range(2016, 2025))
    results = pipeline.download_all(seasons, include_pbp=True)
    
    print("\n" + "="*60)
    print("DOWNLOAD SUMMARY")
    print("="*60)
    for name, df in results.items():
        print(f"{name:20s}: {len(df):8,} rows, {len(df.columns):3d} columns")
    print("="*60)


