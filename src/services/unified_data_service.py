"""Unified Data Service - Single source of truth for all data.

Connects all data sources into one coherent interface:
- nflverse: Schedules, play-by-play, rosters (FREE)
- The Odds API: Live odds, line movement (FREE tier available)
- Local cache: DuckDB for fast queries

This replaces ALL placeholder data with real sources.
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class DataConfig:
    """Configuration for data service."""
    data_dir: str = "data"
    cache_hours: int = 6
    odds_api_key: Optional[str] = None
    seasons: List[int] = None

    def __post_init__(self):
        if self.seasons is None:
            current_year = datetime.now().year
            self.seasons = [current_year - 2, current_year - 1, current_year]
        if self.odds_api_key is None:
            self.odds_api_key = os.environ.get("ODDS_API_KEY")


class UnifiedDataService:
    """
    Single interface for all NFL betting data.

    Data Sources:
    1. nflverse (nfl_data_py): Schedules, PBP, rosters - ALWAYS FREE
    2. The Odds API: Live odds - FREE tier (500 req/month)
    3. DuckDB cache: Fast local queries

    Usage:
        service = UnifiedDataService()
        games = service.get_current_week_games()
        odds = service.get_live_odds(games)
        features = service.get_prediction_features(games)
    """

    def __init__(self, config: Optional[DataConfig] = None):
        self.config = config or DataConfig()
        self._setup_directories()
        self._init_cache()

    def _setup_directories(self):
        """Create data directory structure."""
        dirs = ["raw", "processed", "predictions", "cache", "models"]
        for d in dirs:
            Path(f"{self.config.data_dir}/{d}").mkdir(parents=True, exist_ok=True)

    def _init_cache(self):
        """Initialize DuckDB cache."""
        try:
            import duckdb
            cache_path = f"{self.config.data_dir}/cache/nfl_cache.db"
            self.db = duckdb.connect(cache_path)
            logger.info(f"Cache initialized at {cache_path}")
        except ImportError:
            logger.warning("DuckDB not installed. Using file-based cache.")
            self.db = None

    def refresh_all_data(self) -> Dict[str, int]:
        """
        Download fresh data from all sources.

        Returns count of records downloaded.
        """
        logger.info("Refreshing all data sources...")
        counts = {}

        # 1. nflverse schedules
        schedules = self._download_schedules()
        counts["schedules"] = len(schedules)

        # 2. nflverse play-by-play
        pbp = self._download_pbp()
        counts["plays"] = len(pbp)

        # 3. Live odds (if API key available)
        if self.config.odds_api_key:
            odds = self._download_odds()
            counts["odds_games"] = len(odds)
        else:
            counts["odds_games"] = 0
            logger.warning("No ODDS_API_KEY - skipping live odds")

        logger.info(f"Data refresh complete: {counts}")
        return counts

    def _download_schedules(self) -> pd.DataFrame:
        """Download NFL schedules from nflverse."""
        try:
            import nfl_data_py as nfl
            schedules = nfl.import_schedules(self.config.seasons)

            # Save to cache
            path = f"{self.config.data_dir}/raw/schedules.parquet"
            schedules.to_parquet(path, index=False)

            # Also cache in DuckDB if available
            if self.db:
                self.db.execute("DROP TABLE IF EXISTS schedules")
                self.db.execute("CREATE TABLE schedules AS SELECT * FROM schedules")

            logger.info(f"Downloaded {len(schedules)} games")
            return schedules

        except ImportError:
            logger.error("nfl_data_py not installed. Run: pip install nfl_data_py")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Schedule download failed: {e}")
            return pd.DataFrame()

    def _download_pbp(self) -> pd.DataFrame:
        """Download play-by-play from nflverse."""
        try:
            import nfl_data_py as nfl

            # Only download recent seasons for PBP (large files)
            recent_seasons = self.config.seasons[-2:]
            pbp = nfl.import_pbp_data(recent_seasons)

            path = f"{self.config.data_dir}/raw/pbp.parquet"
            pbp.to_parquet(path, index=False)

            logger.info(f"Downloaded {len(pbp)} plays")
            return pbp

        except Exception as e:
            logger.error(f"PBP download failed: {e}")
            return pd.DataFrame()

    def _download_odds(self) -> List[Dict]:
        """Download live odds from The Odds API."""
        from src.api.odds_client import OddsAPIClient

        client = OddsAPIClient(api_key=self.config.odds_api_key)
        odds = client.get_live_odds()

        # Cache odds snapshot
        if odds:
            import json
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            path = f"{self.config.data_dir}/raw/odds_{timestamp}.json"
            with open(path, "w") as f:
                json.dump(odds, f)

        return odds

    def get_current_week_games(self) -> pd.DataFrame:
        """
        Get games for the current NFL week.

        Returns DataFrame with:
        - game_id, home_team, away_team
        - spread_line, total_line
        - gameday, gametime
        - weather info
        """
        # Load cached schedules
        path = f"{self.config.data_dir}/raw/schedules.parquet"

        if not Path(path).exists():
            self._download_schedules()

        if not Path(path).exists():
            logger.error("No schedule data available")
            return pd.DataFrame()

        schedules = pd.read_parquet(path)

        # Find current week
        today = datetime.now().date()

        # Filter to games without scores (upcoming)
        upcoming = schedules[schedules["home_score"].isna()].copy()

        if len(upcoming) == 0:
            logger.warning("No upcoming games found")
            return pd.DataFrame()

        # Get current week
        upcoming["gameday"] = pd.to_datetime(upcoming["gameday"]).dt.date
        current_week = upcoming["week"].min()

        games = upcoming[upcoming["week"] == current_week].copy()
        logger.info(f"Found {len(games)} games for week {current_week}")

        return games

    def get_live_odds(self, games: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Get live odds for games.

        If no API key, uses spread_line from nflverse schedules.
        """
        if self.config.odds_api_key:
            from src.api.odds_client import OddsAPIClient
            client = OddsAPIClient(api_key=self.config.odds_api_key)
            odds_data = client.get_live_odds()

            if odds_data:
                return self._parse_odds_response(odds_data)

        # Fallback to schedule lines
        if games is not None and "spread_line" in games.columns:
            logger.info("Using spread lines from schedule (no live odds API)")
            return games[["game_id", "home_team", "away_team", "spread_line", "total_line"]]

        return pd.DataFrame()

    def _parse_odds_response(self, odds_data: List[Dict]) -> pd.DataFrame:
        """Parse The Odds API response into DataFrame."""
        rows = []

        for game in odds_data:
            home_team = game.get("home_team", "")
            away_team = game.get("away_team", "")

            # Get consensus line (average across books)
            spreads = []
            totals = []

            for bookmaker in game.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    if market["key"] == "spreads":
                        for outcome in market["outcomes"]:
                            if outcome["name"] == home_team:
                                spreads.append(outcome.get("point", 0))
                    elif market["key"] == "totals":
                        for outcome in market["outcomes"]:
                            if outcome["name"] == "Over":
                                totals.append(outcome.get("point", 0))

            rows.append({
                "game_id": game.get("id", ""),
                "home_team": home_team,
                "away_team": away_team,
                "spread_line": sum(spreads) / len(spreads) if spreads else 0,
                "total_line": sum(totals) / len(totals) if totals else 45,
                "commence_time": game.get("commence_time", ""),
            })

        return pd.DataFrame(rows)

    def get_team_stats(self, n_games: int = 5) -> pd.DataFrame:
        """
        Get rolling team statistics.

        Calculates EPA, success rate, etc. from play-by-play.
        """
        path = f"{self.config.data_dir}/raw/pbp.parquet"

        if not Path(path).exists():
            self._download_pbp()

        if not Path(path).exists():
            logger.error("No PBP data available")
            return pd.DataFrame()

        pbp = pd.read_parquet(path)

        from src.data.nfl_data import calculate_team_stats
        return calculate_team_stats(pbp, n_games)

    def get_prediction_features(self, games: pd.DataFrame) -> pd.DataFrame:
        """
        Build complete feature set for predictions.

        Combines:
        - Schedule features (rest, division, primetime)
        - Team stats (EPA, success rate)
        - Weather
        - Betting line features
        """
        from src.data.nfl_data import prepare_features

        team_stats = self.get_team_stats()

        if len(team_stats) > 0:
            features = prepare_features(games, team_stats, for_prediction=True)
        else:
            features = prepare_features(games, for_prediction=True)

        return features

    def get_player_stats(self, position: str = "ALL") -> pd.DataFrame:
        """
        Get player statistics for props.

        Args:
            position: Filter by position (QB, RB, WR, TE, ALL)
        """
        try:
            import nfl_data_py as nfl

            # Get weekly stats
            seasons = self.config.seasons[-2:]
            weekly = nfl.import_weekly_data(seasons)

            if position != "ALL":
                weekly = weekly[weekly["position"] == position]

            # Calculate rolling averages
            stat_cols = ["passing_yards", "rushing_yards", "receiving_yards",
                        "receptions", "targets", "passing_tds", "rushing_tds", "receiving_tds"]

            for col in stat_cols:
                if col in weekly.columns:
                    weekly[f"{col}_roll5"] = weekly.groupby("player_id")[col].transform(
                        lambda x: x.rolling(5, min_periods=1).mean().shift(1)
                    )

            return weekly

        except Exception as e:
            logger.error(f"Failed to get player stats: {e}")
            return pd.DataFrame()

    def get_defense_rankings(self) -> pd.DataFrame:
        """
        Get defensive rankings vs each position.

        Used for matchup analysis.
        """
        path = f"{self.config.data_dir}/raw/pbp.parquet"

        if not Path(path).exists():
            return pd.DataFrame()

        pbp = pd.read_parquet(path)

        # Calculate defensive EPA allowed by position
        plays = pbp[pbp["play_type"].isin(["pass", "run"]) & pbp["epa"].notna()]

        def_stats = plays.groupby(["defteam", "season", "week"]).agg({
            "epa": ["mean", "sum"],
            "play_id": "count",
        }).reset_index()

        def_stats.columns = ["team", "season", "week", "epa_allowed_per_play",
                            "total_epa_allowed", "plays_against"]

        return def_stats


def create_data_service(config: Optional[DataConfig] = None) -> UnifiedDataService:
    """Factory function for data service."""
    return UnifiedDataService(config)


# CLI for data refresh
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="NFL Data Service")
    parser.add_argument("--refresh", action="store_true", help="Refresh all data")
    parser.add_argument("--games", action="store_true", help="Show current week games")
    parser.add_argument("--odds", action="store_true", help="Show live odds")

    args = parser.parse_args()

    service = UnifiedDataService()

    if args.refresh:
        counts = service.refresh_all_data()
        print(f"Refreshed: {counts}")

    if args.games:
        games = service.get_current_week_games()
        print(games[["game_id", "home_team", "away_team", "spread_line", "gameday"]])

    if args.odds:
        odds = service.get_live_odds()
        print(odds)
