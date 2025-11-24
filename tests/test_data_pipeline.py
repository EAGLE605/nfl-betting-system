"""
Unit Tests for NFL Data Pipeline
=================================

Tests for data download, validation, and caching logic.

Run with: pytest tests/test_data_pipeline.py -v

Author: NFL Betting System
Date: 2025-11-23
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_pipeline import NFLDataPipeline, get_available_seasons


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory for tests."""
    return str(tmp_path / "test_data")


@pytest.fixture
def pipeline(temp_data_dir):
    """Create a pipeline instance with temporary directory."""
    return NFLDataPipeline(data_dir=temp_data_dir, cache_days=7, max_retries=2)


@pytest.fixture
def sample_schedules_df():
    """Create a sample schedules DataFrame for testing."""
    return pd.DataFrame(
        {
            "game_id": ["2023_01_BUF_NYJ", "2023_01_KC_DET"],
            "season": [2023, 2023],
            "gameday": ["2023-09-07", "2023-09-07"],
            "home_team": ["NYJ", "DET"],
            "away_team": ["BUF", "KC"],
            "home_score": [16, 21],
            "away_score": [22, 20],
        }
    )


@pytest.fixture
def sample_pbp_df():
    """Create a sample play-by-play DataFrame for testing."""
    return pd.DataFrame(
        {
            "game_id": ["2023_01_BUF_NYJ"] * 5,
            "play_id": [1, 2, 3, 4, 5],
            "posteam": ["BUF", "NYJ", "BUF", "NYJ", "BUF"],
            "defteam": ["NYJ", "BUF", "NYJ", "BUF", "NYJ"],
            "epa": [0.5, -0.3, 1.2, -0.8, 0.4],
        }
    )


class TestNFLDataPipeline:
    """Test suite for NFLDataPipeline class."""

    def test_init_creates_directories(self, temp_data_dir):
        """Test that initialization creates necessary directories."""
        NFLDataPipeline(data_dir=temp_data_dir)
        
        assert Path(temp_data_dir).exists()
        assert (Path(temp_data_dir) / "raw").exists()

    def test_init_default_parameters(self, temp_data_dir):
        """Test initialization with default parameters."""
        pipeline = NFLDataPipeline(data_dir=temp_data_dir)

        assert pipeline.cache_days == 7
        assert pipeline.max_retries == 3
        assert pipeline.data_dir == Path(temp_data_dir)

    def test_should_download_missing_file(self, pipeline):
        """Test that missing file triggers download."""
        filepath = Path("nonexistent.parquet")
        seasons = [2023]

        result = pipeline._should_download(filepath, seasons)

        assert result is True

    def test_should_download_completed_season(self, pipeline, tmp_path):
        """Test that completed seasons are not re-downloaded."""
        # Create a dummy file
        filepath = tmp_path / "schedules_2020_2022.parquet"
        filepath.touch()

        # Set file modification time to 30 days ago
        old_time = datetime.now() - timedelta(days=30)
        import os

        os.utime(filepath, (old_time.timestamp(), old_time.timestamp()))

        # All seasons are completed (< current year)
        seasons = [2020, 2021, 2022]

        result = pipeline._should_download(filepath, seasons)

        assert result is False  # Should not re-download completed seasons

    def test_should_download_current_season_expired(self, pipeline, tmp_path):
        """Test that current season is re-downloaded if cache expired."""
        # Create a dummy file
        filepath = tmp_path / "schedules_2024_2024.parquet"
        filepath.touch()

        # Set file modification time to 30 days ago (> cache_days)
        old_time = datetime.now() - timedelta(days=30)
        import os

        os.utime(filepath, (old_time.timestamp(), old_time.timestamp()))

        # Include current year
        current_year = datetime.now().year
        seasons = [current_year]

        result = pipeline._should_download(filepath, seasons)

        # Should re-download if cache expired and includes current season
        if current_year in seasons:
            assert result is True

    def test_validate_data_success(self, pipeline, sample_schedules_df):
        """Test successful data validation."""
        required_columns = ["game_id", "season", "gameday"]

        # Should not raise any exception
        pipeline.validate_data(sample_schedules_df, required_columns, "test")

    def test_validate_data_empty_dataframe(self, pipeline):
        """Test validation fails for empty DataFrame."""
        df = pd.DataFrame()
        required_columns = ["game_id"]

        with pytest.raises(ValueError, match="DataFrame is empty"):
            pipeline.validate_data(df, required_columns, "test")

    def test_validate_data_missing_columns(self, pipeline, sample_schedules_df):
        """Test validation fails for missing columns."""
        required_columns = ["game_id", "nonexistent_column"]

        with pytest.raises(ValueError, match="missing columns"):
            pipeline.validate_data(sample_schedules_df, required_columns, "test")

    def test_validate_data_with_nulls(self, pipeline, sample_schedules_df):
        """Test validation warns about nulls but doesn't fail."""
        # Add nulls to a required column
        df = sample_schedules_df.copy()
        df.loc[0, "game_id"] = None

        required_columns = ["game_id", "season"]

        # Should warn but not raise exception
        pipeline.validate_data(df, required_columns, "test")

    @patch("data_pipeline.nfl.load_schedules")
    def test_get_schedules_download(self, mock_import, pipeline, sample_schedules_df):
        """Test downloading schedules."""
        mock_import.return_value = sample_schedules_df

        seasons = [2023]
        result = pipeline.get_schedules(seasons)

        # Verify API was called
        mock_import.assert_called_once_with(seasons=seasons)

        # Verify data was returned
        assert len(result) == len(sample_schedules_df)
        assert "game_id" in result.columns

        # Verify file was saved
        filepath = pipeline.raw_dir / "schedules_2023_2023.parquet"
        assert filepath.exists()

    @patch("data_pipeline.nfl.load_schedules")
    def test_get_schedules_uses_cache(self, mock_import, pipeline, sample_schedules_df):
        """Test that cached schedules are used."""
        # First download
        mock_import.return_value = sample_schedules_df
        seasons = [2020]  # Completed season
        pipeline.get_schedules(seasons)

        # Reset mock
        mock_import.reset_mock()

        # Second call should use cache (not call API)
        result = pipeline.get_schedules(seasons)

        mock_import.assert_not_called()
        assert len(result) == len(sample_schedules_df)

    @patch("data_pipeline.nfl.load_pbp")
    def test_get_play_by_play(self, mock_import, pipeline, sample_pbp_df):
        """Test downloading play-by-play data."""
        mock_import.return_value = sample_pbp_df

        seasons = [2023]
        result = pipeline.get_play_by_play(seasons)

        mock_import.assert_called_once_with(seasons=seasons)
        assert len(result) == len(sample_pbp_df)
        assert "epa" in result.columns

    @patch("data_pipeline.nfl.load_player_stats")
    def test_get_weekly_stats(self, mock_import, pipeline):
        """Test downloading weekly stats."""
        sample_weekly = pd.DataFrame(
            {
                "season": [2023] * 3,
                "week": [1, 1, 1],
                "player_id": ["P1", "P2", "P3"],
                "team": ["BUF", "KC", "NYJ"],
            }
        )
        mock_import.return_value = sample_weekly

        seasons = [2023]
        result = pipeline.get_weekly_stats(seasons, stat_type="offense")

        mock_import.assert_called_once_with(seasons=seasons)
        assert len(result) == len(sample_weekly)

    @patch("data_pipeline.nfl.load_schedules")
    def test_retry_download_success_after_failure(
        self, mock_import, pipeline, sample_schedules_df
    ):
        """Test retry logic succeeds after initial failure."""
        # Fail first time, succeed second time
        mock_import.side_effect = [Exception("Network error"), sample_schedules_df]

        seasons = [2023]
        result = pipeline.get_schedules(seasons)

        # Should have retried and succeeded
        assert mock_import.call_count == 2
        assert len(result) == len(sample_schedules_df)

    @patch("data_pipeline.nfl.load_schedules")
    def test_retry_download_all_failures(self, mock_import, pipeline):
        """Test retry logic fails after all attempts."""
        # Fail all attempts
        mock_import.side_effect = Exception("Network error")

        seasons = [2023]

        with pytest.raises(ValueError, match="Failed to download"):
            pipeline.get_schedules(seasons)

        # Should have tried max_retries times
        assert mock_import.call_count == pipeline.max_retries

    @patch("data_pipeline.nfl.load_schedules")
    @patch("data_pipeline.nfl.load_teams")
    @patch("data_pipeline.nfl.load_player_stats")
    @patch("data_pipeline.nfl.load_pbp")
    def test_download_all(
        self,
        mock_pbp,
        mock_weekly,
        mock_teams,
        mock_schedules,
        pipeline,
        sample_schedules_df,
        sample_pbp_df,
    ):
        """Test downloading all data types."""
        # Mock all API calls
        mock_schedules.return_value = sample_schedules_df
        mock_teams.return_value = pd.DataFrame(
            {
                "team_abbr": ["BUF", "KC"],
                "team_name": ["Buffalo Bills", "Kansas City Chiefs"],
            }
        )
        mock_weekly.return_value = pd.DataFrame(
            {"season": [2023], "week": [1], "player_id": ["P1"], "team": ["BUF"]}
        )
        mock_pbp.return_value = sample_pbp_df

        seasons = [2023]
        results = pipeline.download_all(seasons, include_pbp=True)

        # Verify all data types downloaded
        assert "schedules" in results
        assert "teams" in results
        assert "weekly_offense" in results
        assert "pbp" in results

        # Verify metadata saved
        metadata_path = pipeline.raw_dir / "metadata.json"
        assert metadata_path.exists()

        with open(metadata_path) as f:
            metadata = json.load(f)

        assert metadata["seasons"] == seasons
        assert "schedules" in metadata["data_types"]

    @patch("data_pipeline.nfl.load_schedules")
    @patch("data_pipeline.nfl.load_teams")
    def test_download_all_skip_pbp(
        self, mock_teams, mock_schedules, pipeline, sample_schedules_df
    ):
        """Test downloading without play-by-play data."""
        mock_schedules.return_value = sample_schedules_df
        mock_teams.return_value = pd.DataFrame(
            {"team_abbr": ["BUF"], "team_name": ["Buffalo Bills"]}
        )

        seasons = [2023]
        results = pipeline.download_all(seasons, include_pbp=False)

        # Verify pbp not downloaded
        assert "pbp" not in results
        assert "schedules" in results


class TestUtilityFunctions:
    """Test suite for utility functions."""

    def test_get_available_seasons(self):
        """Test getting available seasons."""
        seasons = get_available_seasons()

        assert isinstance(seasons, list)
        assert len(seasons) > 0
        assert 1999 in seasons  # First year of nflverse data
        assert max(seasons) == datetime.now().year


class TestIntegration:
    """Integration tests for data pipeline (require network)."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_download_single_season(self, temp_data_dir):
        """Test downloading a single season (integration test)."""
        pipeline = NFLDataPipeline(data_dir=temp_data_dir, max_retries=2)

        # Download 2023 season
        seasons = [2023]
        schedules = pipeline.get_schedules(seasons)

        # Verify data quality
        assert len(schedules) > 0
        assert "game_id" in schedules.columns
        assert "season" in schedules.columns
        assert "home_team" in schedules.columns
        assert "away_team" in schedules.columns

        # Verify all games are from 2023
        assert schedules["season"].min() == 2023
        assert schedules["season"].max() == 2023

        # Verify file was cached
        filepath = pipeline.raw_dir / "schedules_2023_2023.parquet"
        assert filepath.exists()

    @pytest.mark.integration
    @pytest.mark.slow
    def test_cache_functionality(self, temp_data_dir):
        """Test that cache works correctly."""
        pipeline = NFLDataPipeline(data_dir=temp_data_dir, max_retries=2)

        seasons = [2020]  # Completed season

        # First download
        import time

        start1 = time.time()
        schedules1 = pipeline.get_schedules(seasons)
        elapsed1 = time.time() - start1

        # Second download (should use cache)
        start2 = time.time()
        schedules2 = pipeline.get_schedules(seasons)
        elapsed2 = time.time() - start2

        # Verify data is the same
        assert len(schedules1) == len(schedules2)

        # Verify cache is faster (should be <10s as per requirements)
        assert elapsed2 < 10, f"Cache re-read took {elapsed2:.1f}s, expected <10s"
        assert elapsed2 < elapsed1, "Cache should be faster than download"

    @pytest.mark.integration
    @pytest.mark.slow
    def test_data_quality_validation(self, temp_data_dir):
        """Test data quality checks on real data."""
        pipeline = NFLDataPipeline(data_dir=temp_data_dir, max_retries=2)

        seasons = [2023]
        schedules = pipeline.get_schedules(seasons)

        # Check for expected row count (2023 season has ~272 games)
        # Regular season: 17 weeks * 16 games/week = 272 games
        # Plus playoffs: ~13 games
        # Total: ~285 games
        expected_min = 250
        expected_max = 300

        assert (
            expected_min <= len(schedules) <= expected_max
        ), f"Expected ~285 games, got {len(schedules)}"

        # Check for nulls in critical columns
        critical_cols = ["game_id", "season", "home_team", "away_team"]
        null_counts = schedules[critical_cols].isnull().sum()

        # Should have no nulls in critical columns
        assert (
            null_counts.sum() == 0
        ), f"Found nulls in critical columns:\n{null_counts[null_counts > 0]}"

        # Check data types
        assert schedules["season"].dtype in [
            "int64",
            "int32",
        ], f"Season should be integer, got {schedules['season'].dtype}"

    @pytest.mark.integration
    @pytest.mark.slow
    def test_strict_mode_validation(self, temp_data_dir):
        """Test strict mode validation."""
        pipeline = NFLDataPipeline(
            data_dir=temp_data_dir, strict_mode=True, max_retries=2
        )

        # This should work fine with good data
        seasons = [2023]
        schedules = pipeline.get_schedules(seasons)

        # Verify it worked
        assert len(schedules) > 0

    @pytest.mark.integration
    @pytest.mark.slow
    def test_file_integrity_check(self, temp_data_dir):
        """Test file integrity checking."""
        pipeline = NFLDataPipeline(data_dir=temp_data_dir, max_retries=2)

        seasons = [2023]
        schedules = pipeline.get_schedules(seasons)

        filepath = pipeline.raw_dir / "schedules_2023_2023.parquet"

        # Check integrity with correct expected rows
        expected_rows = len(schedules)
        assert pipeline._check_file_integrity(filepath, expected_rows) is True

        # Check integrity with wrong expected rows
        assert pipeline._check_file_integrity(filepath, expected_rows + 1000) is False

    @pytest.mark.integration
    @pytest.mark.slow
    def test_download_all_components(self, temp_data_dir):
        """Test downloading all data components."""
        pipeline = NFLDataPipeline(data_dir=temp_data_dir, max_retries=2)

        seasons = [2023]
        results = pipeline.download_all(
            seasons, include_pbp=False
        )  # Skip PBP for speed

        # Verify all components downloaded
        assert "schedules" in results
        assert "teams" in results
        assert "weekly_offense" in results

        # Verify data quality
        assert len(results["schedules"]) > 0
        assert len(results["teams"]) > 0
        assert len(results["weekly_offense"]) > 0

        # Verify metadata saved
        metadata_path = pipeline.raw_dir / "metadata.json"
        assert metadata_path.exists()

        import json

        with open(metadata_path) as f:
            metadata = json.load(f)

        assert metadata["seasons"] == seasons
        assert "schedules" in metadata["data_types"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
