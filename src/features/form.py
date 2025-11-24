"""Recent form features.

Calculates team performance metrics over recent games.
"""
from .base import FeatureBuilder
import pandas as pd
from typing import List
import logging

logger = logging.getLogger(__name__)


class FormFeatures(FeatureBuilder):
    """
    Recent form features.
    
    Creates rolling averages for:
    - win_pct_home: Home team win % (last 3 games)
    - win_pct_away: Away team win % (last 3 games)
    - point_diff_home: Home team point differential (last 3 games)
    - point_diff_away: Away team point differential (last 3 games)
    """
    
    def __init__(self, window=3):
        """
        Initialize form features.
        
        Args:
            window: Number of recent games to consider
        """
        self.window = window
    
    def get_required_columns(self) -> List[str]:
        return ['game_id', 'gameday', 'season', 'home_team', 'away_team',
                'home_score', 'away_score']
    
    def build(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build form features."""
        self.validate_prerequisites(df)
        
        logger.info(f"Building form features (window={self.window})...")
        
        # Ensure datetime
        df['gameday'] = pd.to_datetime(df['gameday'])
        
        # Sort by date
        df = df.sort_values(['season', 'gameday']).copy()
        
        # Calculate win/loss and point differential for each team
        df['home_win'] = (df['home_score'] > df['away_score']).astype(int)
        df['away_win'] = (df['away_score'] > df['home_score']).astype(int)
        df['home_point_diff'] = df['home_score'] - df['away_score']
        df['away_point_diff'] = df['away_score'] - df['home_score']
        
        # Calculate rolling averages for home team
        df['win_pct_home'] = self._rolling_win_pct(df, 'home_team', 'home_win')
        df['point_diff_home'] = self._rolling_point_diff(df, 'home_team', 'home_point_diff')
        
        # Calculate rolling averages for away team
        df['win_pct_away'] = self._rolling_win_pct(df, 'away_team', 'away_win')
        df['point_diff_away'] = self._rolling_point_diff(df, 'away_team', 'away_point_diff')
        
        # Clean up temporary columns
        df = df.drop(columns=['home_win', 'away_win', 'home_point_diff', 'away_point_diff'], errors='ignore')
        
        logger.info(f"✓ Form features created: {len(self.get_feature_names())} features")
        
        return df
    
    def _rolling_win_pct(self, df: pd.DataFrame, team_col: str, win_col: str) -> pd.Series:
        """Calculate rolling win percentage."""
        # Group by team and season
        grouped = df.groupby([team_col, 'season'])[win_col]
        
        # Rolling mean (win %)
        rolling = grouped.transform(lambda x: x.shift(1).rolling(self.window, min_periods=1).mean())
        
        # Fill first game of season with 0.5 (neutral)
        rolling = rolling.fillna(0.5)
        
        return rolling
    
    def _rolling_point_diff(self, df: pd.DataFrame, team_col: str, diff_col: str) -> pd.Series:
        """Calculate rolling point differential."""
        # Group by team and season
        grouped = df.groupby([team_col, 'season'])[diff_col]
        
        # Rolling mean
        rolling = grouped.transform(lambda x: x.shift(1).rolling(self.window, min_periods=1).mean())
        
        # Fill first game of season with 0 (neutral)
        rolling = rolling.fillna(0)
        
        return rolling
    
    def get_feature_names(self) -> List[str]:
        return [
            'win_pct_home',
            'win_pct_away',
            'point_diff_home',
            'point_diff_away'
        ]

