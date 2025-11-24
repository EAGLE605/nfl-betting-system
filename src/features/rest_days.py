"""Rest days and schedule features.

Calculates days since team's last game, identifies back-to-back games,
and post-bye week games.
"""
from .base import FeatureBuilder
import pandas as pd
from typing import List
import logging

logger = logging.getLogger(__name__)


class RestDaysFeatures(FeatureBuilder):
    """
    Rest days features.
    
    Creates:
    - rest_days_home: Days since home team's last game
    - rest_days_away: Days since away team's last game
    - is_back_to_back_home: 1 if <=4 days rest (Thu after Sun)
    - is_back_to_back_away: 1 if <=4 days rest
    - post_bye_home: 1 if >10 days rest (bye week)
    - post_bye_away: 1 if >10 days rest
    """
    
    def get_required_columns(self) -> List[str]:
        return ['game_id', 'gameday', 'season', 'home_team', 'away_team']
    
    def build(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build rest days features."""
        self.validate_prerequisites(df)
        
        logger.info("Building rest days features...")
        
        # Ensure gameday is datetime
        df['gameday'] = pd.to_datetime(df['gameday'])
        
        # Sort by date
        df = df.sort_values(['season', 'gameday']).copy()
        
        # Calculate rest days for home and away teams
        df['rest_days_home'] = self._calculate_rest_days(df, 'home_team')
        df['rest_days_away'] = self._calculate_rest_days(df, 'away_team')
        
        # Back-to-back indicators (Thu after Sun = 4 days)
        df['is_back_to_back_home'] = (df['rest_days_home'] <= 4).astype(int)
        df['is_back_to_back_away'] = (df['rest_days_away'] <= 4).astype(int)
        
        # Post-bye indicators (>10 days rest)
        df['post_bye_home'] = (df['rest_days_home'] > 10).astype(int)
        df['post_bye_away'] = (df['rest_days_away'] > 10).astype(int)
        
        logger.info(f"✓ Rest days features created: {len(self.get_feature_names())} features")
        
        return df
    
    def _calculate_rest_days(self, df: pd.DataFrame, team_col: str) -> pd.Series:
        """Calculate days since team's last game."""
        # Group by team and season, calculate days between games
        rest_days = df.groupby([team_col, 'season'])['gameday'].diff().dt.days
        
        # First game of season: default to 7 days
        rest_days = rest_days.fillna(7)
        
        return rest_days
    
    def get_feature_names(self) -> List[str]:
        return [
            'rest_days_home',
            'rest_days_away',
            'is_back_to_back_home',
            'is_back_to_back_away',
            'post_bye_home',
            'post_bye_away'
        ]

