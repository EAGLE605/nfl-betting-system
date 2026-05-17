"""Feature Store - Medallion Architecture

Bronze → Silver → Gold data pipeline.
Grounded in nflverse ecosystem + production best practices.

Architecture:
- Bronze: Raw data from nflverse (play-by-play, rosters, schedules)
- Silver: Feature engineering (rolling stats, interactions, matchups)
- Gold: Model-ready features + predictions

Sources:
- nflfastR/nflverse (gold standard since 2018)
- Medallion architecture (Databricks pattern)
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class FeatureStoreConfig:
    """Configuration for feature store."""
    bronze_path: str = "data/bronze"
    silver_path: str = "data/silver"
    gold_path: str = "data/gold"
    rolling_windows: List[int] = None  # Default: [3, 5, 8]

    def __post_init__(self):
        if self.rolling_windows is None:
            self.rolling_windows = [3, 5, 8]


class FeatureStore:
    """
    Medallion architecture feature store.

    Bronze: Raw nflverse data
    Silver: Engineered features
    Gold: Model-ready datasets
    """

    def __init__(self, config: Optional[FeatureStoreConfig] = None):
        self.config = config or FeatureStoreConfig()
        self._ensure_paths()

    def _ensure_paths(self):
        """Create directory structure."""
        for path in [self.config.bronze_path, self.config.silver_path, self.config.gold_path]:
            Path(path).mkdir(parents=True, exist_ok=True)

    # ==================== BRONZE LAYER ====================

    def ingest_bronze(self, seasons: List[int]) -> Dict[str, pd.DataFrame]:
        """
        Ingest raw data from nflverse into bronze layer.

        Returns dict of DataFrames: pbp, schedules, rosters
        """
        logger.info(f"Ingesting bronze layer for seasons {seasons}")

        try:
            import nfl_data_py as nfl

            # Play-by-play (EPA, CPOE, success rate)
            pbp = nfl.import_pbp_data(seasons)
            pbp_path = Path(self.config.bronze_path) / f"pbp_{min(seasons)}_{max(seasons)}.parquet"
            pbp.to_parquet(pbp_path, index=False)
            logger.info(f"Bronze PBP: {len(pbp)} plays")

            # Schedules (game info, betting lines)
            schedules = nfl.import_schedules(seasons)
            sched_path = Path(self.config.bronze_path) / f"schedules_{min(seasons)}_{max(seasons)}.parquet"
            schedules.to_parquet(sched_path, index=False)
            logger.info(f"Bronze schedules: {len(schedules)} games")

            # Rosters (player info)
            rosters = nfl.import_seasonal_rosters(seasons)
            roster_path = Path(self.config.bronze_path) / f"rosters_{min(seasons)}_{max(seasons)}.parquet"
            rosters.to_parquet(roster_path, index=False)
            logger.info(f"Bronze rosters: {len(rosters)} player-seasons")

            return {'pbp': pbp, 'schedules': schedules, 'rosters': rosters}

        except Exception as e:
            logger.error(f"Bronze ingestion failed: {e}")
            raise

    def load_bronze(self, data_type: str, seasons: List[int]) -> pd.DataFrame:
        """Load bronze data from disk."""
        path = Path(self.config.bronze_path) / f"{data_type}_{min(seasons)}_{max(seasons)}.parquet"
        if path.exists():
            return pd.read_parquet(path)
        else:
            raise FileNotFoundError(f"Bronze data not found: {path}")

    # ==================== SILVER LAYER ====================

    def build_silver_player_features(
        self,
        pbp: pd.DataFrame,
        schedules: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Build player-level silver features.

        Features (per blueprint):
        - Rolling 3/5/8-game target share
        - Red-zone looks
        - Snap %
        - YAC/reception
        - Air yards share
        """
        logger.info("Building silver player features...")

        # Calculate player game stats from PBP
        player_stats = self._calculate_player_game_stats(pbp)

        # Add rolling features
        for window in self.config.rolling_windows:
            player_stats = self._add_rolling_features(player_stats, window)

        # Add matchup features
        player_stats = self._add_matchup_features(player_stats, schedules)

        # Save
        silver_path = Path(self.config.silver_path) / "player_features.parquet"
        player_stats.to_parquet(silver_path, index=False)
        logger.info(f"Silver player features: {len(player_stats)} player-games")

        return player_stats

    def _calculate_player_game_stats(self, pbp: pd.DataFrame) -> pd.DataFrame:
        """Calculate player stats per game from play-by-play."""
        # Filter to regular plays
        plays = pbp[pbp['play_type'].isin(['pass', 'run'])].copy()

        # Receiving stats
        rec_stats = plays[plays['complete_pass'] == 1].groupby(
            ['game_id', 'receiver_player_id', 'receiver_player_name', 'posteam']
        ).agg({
            'yards_gained': 'sum',
            'play_id': 'count',
            'touchdown': 'sum',
            'yards_after_catch': 'sum',
            'air_yards': 'sum',
            'epa': 'sum',
        }).reset_index()
        rec_stats.columns = ['game_id', 'player_id', 'player_name', 'team',
                             'receiving_yards', 'receptions', 'receiving_tds',
                             'yac', 'air_yards', 'receiving_epa']

        # Rushing stats
        rush_stats = plays[plays['play_type'] == 'run'].groupby(
            ['game_id', 'rusher_player_id', 'rusher_player_name', 'posteam']
        ).agg({
            'yards_gained': 'sum',
            'play_id': 'count',
            'touchdown': 'sum',
            'epa': 'sum',
        }).reset_index()
        rush_stats.columns = ['game_id', 'player_id', 'player_name', 'team',
                              'rushing_yards', 'carries', 'rushing_tds', 'rushing_epa']

        # Passing stats
        pass_stats = plays[plays['play_type'] == 'pass'].groupby(
            ['game_id', 'passer_player_id', 'passer_player_name', 'posteam']
        ).agg({
            'yards_gained': 'sum',
            'complete_pass': 'sum',
            'play_id': 'count',
            'pass_touchdown': 'sum',
            'epa': 'sum',
            'cpoe': 'mean',
        }).reset_index()
        pass_stats.columns = ['game_id', 'player_id', 'player_name', 'team',
                              'passing_yards', 'completions', 'attempts',
                              'passing_tds', 'passing_epa', 'cpoe']

        # Target share calculation
        team_targets = plays[plays['play_type'] == 'pass'].groupby(
            ['game_id', 'posteam']
        )['play_id'].count().reset_index()
        team_targets.columns = ['game_id', 'team', 'team_targets']

        rec_stats = rec_stats.merge(team_targets, on=['game_id', 'team'], how='left')
        rec_stats['target_share'] = rec_stats['receptions'] / rec_stats['team_targets'].replace(0, 1)

        # Combine all stats
        all_stats = pd.concat([
            rec_stats.assign(position='WR'),
            rush_stats.assign(position='RB'),
            pass_stats.assign(position='QB'),
        ], ignore_index=True)

        return all_stats

    def _add_rolling_features(self, df: pd.DataFrame, window: int) -> pd.DataFrame:
        """Add rolling window features."""
        df = df.sort_values(['player_id', 'game_id'])

        # Numeric columns to roll
        roll_cols = [
            'receiving_yards', 'receptions', 'target_share',
            'rushing_yards', 'carries',
            'passing_yards', 'completions', 'cpoe'
        ]

        for col in roll_cols:
            if col in df.columns:
                df[f'{col}_roll_{window}'] = df.groupby('player_id')[col].transform(
                    lambda x: x.rolling(window, min_periods=1).mean().shift(1)
                )

        return df

    def _add_matchup_features(
        self,
        player_stats: pd.DataFrame,
        schedules: pd.DataFrame,
    ) -> pd.DataFrame:
        """Add opponent/matchup features."""
        # Get opponent from schedules
        games = schedules[['game_id', 'home_team', 'away_team']].copy()

        # Join to get opponent
        player_stats = player_stats.merge(games, on='game_id', how='left')
        player_stats['opponent'] = player_stats.apply(
            lambda r: r['away_team'] if r['team'] == r['home_team'] else r['home_team'],
            axis=1
        )

        return player_stats

    def build_silver_game_features(
        self,
        schedules: pd.DataFrame,
        pbp: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Build game-level silver features.

        Features:
        - Rest differential
        - EPA differentials
        - Weather
        - Divisional flags
        """
        logger.info("Building silver game features...")

        games = schedules.copy()

        # Rest days
        games = games.sort_values(['home_team', 'gameday'])
        games['home_rest'] = games.groupby('home_team')['gameday'].diff().dt.days.fillna(7)

        games = games.sort_values(['away_team', 'gameday'])
        games['away_rest'] = games.groupby('away_team')['gameday'].diff().dt.days.fillna(7)

        games['rest_diff'] = games['home_rest'] - games['away_rest']

        # Team EPA from PBP
        team_epa = self._calculate_team_epa(pbp)
        games = games.merge(
            team_epa.add_prefix('home_'),
            left_on=['home_team', 'season', 'week'],
            right_on=['home_team', 'home_season', 'home_week'],
            how='left'
        )

        # Divisional flags
        games['is_divisional'] = games.apply(
            lambda r: self._same_division(r['home_team'], r['away_team']),
            axis=1
        )

        # Save
        silver_path = Path(self.config.silver_path) / "game_features.parquet"
        games.to_parquet(silver_path, index=False)

        return games

    def _calculate_team_epa(self, pbp: pd.DataFrame) -> pd.DataFrame:
        """Calculate rolling team EPA."""
        plays = pbp[pbp['epa'].notna()].copy()

        team_game = plays.groupby(['game_id', 'posteam', 'season', 'week']).agg({
            'epa': 'mean',
            'success': 'mean',
        }).reset_index()
        team_game.columns = ['game_id', 'team', 'season', 'week', 'epa_per_play', 'success_rate']

        # Rolling
        team_game = team_game.sort_values(['team', 'season', 'week'])
        team_game['epa_roll_5'] = team_game.groupby('team')['epa_per_play'].transform(
            lambda x: x.rolling(5, min_periods=1).mean().shift(1)
        )

        return team_game

    def _same_division(self, home: str, away: str) -> bool:
        """Check if same division."""
        divisions = {
            'AFC East': ['BUF', 'MIA', 'NE', 'NYJ'],
            'AFC North': ['BAL', 'CIN', 'CLE', 'PIT'],
            'AFC South': ['HOU', 'IND', 'JAX', 'TEN'],
            'AFC West': ['DEN', 'KC', 'LAC', 'LV'],
            'NFC East': ['DAL', 'NYG', 'PHI', 'WAS'],
            'NFC North': ['CHI', 'DET', 'GB', 'MIN'],
            'NFC South': ['ATL', 'CAR', 'NO', 'TB'],
            'NFC West': ['ARI', 'LAR', 'SEA', 'SF'],
        }
        for teams in divisions.values():
            if home in teams and away in teams:
                return True
        return False

    # ==================== GOLD LAYER ====================

    def build_gold_training_set(
        self,
        target: str = 'receiving_yards',
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Build gold layer model-ready training set.

        Returns (DataFrame, feature_columns)
        """
        logger.info(f"Building gold training set for target: {target}")

        # Load silver
        player_path = Path(self.config.silver_path) / "player_features.parquet"
        game_path = Path(self.config.silver_path) / "game_features.parquet"

        if not player_path.exists() or not game_path.exists():
            raise FileNotFoundError("Silver layer not built. Run build_silver_* first.")

        player_features = pd.read_parquet(player_path)
        game_features = pd.read_parquet(game_path)

        # Merge
        gold = player_features.merge(
            game_features[['game_id', 'rest_diff', 'is_divisional']],
            on='game_id',
            how='left'
        )

        # Filter to rows with target
        gold = gold[gold[target].notna()]

        # Define feature columns
        feature_cols = [
            col for col in gold.columns
            if col.endswith(('_roll_3', '_roll_5', '_roll_8'))
            or col in ['rest_diff', 'is_divisional', 'target_share']
        ]

        # Save
        gold_path = Path(self.config.gold_path) / f"training_{target}.parquet"
        gold.to_parquet(gold_path, index=False)

        logger.info(f"Gold training set: {len(gold)} rows, {len(feature_cols)} features")
        return gold, feature_cols

    def get_feature_columns(self) -> List[str]:
        """Get list of all feature columns."""
        return [
            # Rolling receiving
            'receiving_yards_roll_3', 'receiving_yards_roll_5', 'receiving_yards_roll_8',
            'receptions_roll_3', 'receptions_roll_5', 'receptions_roll_8',
            'target_share_roll_3', 'target_share_roll_5', 'target_share_roll_8',
            # Rolling rushing
            'rushing_yards_roll_3', 'rushing_yards_roll_5', 'rushing_yards_roll_8',
            'carries_roll_3', 'carries_roll_5', 'carries_roll_8',
            # Rolling passing
            'passing_yards_roll_3', 'passing_yards_roll_5', 'passing_yards_roll_8',
            'cpoe_roll_3', 'cpoe_roll_5', 'cpoe_roll_8',
            # Game context
            'rest_diff', 'is_divisional',
            # Current usage
            'target_share',
        ]


def create_feature_store(config: Optional[FeatureStoreConfig] = None) -> FeatureStore:
    """Factory function for feature store."""
    return FeatureStore(config)
