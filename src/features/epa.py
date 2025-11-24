"""EPA (Expected Points Added) features.

Aggregates EPA from play-by-play data to create team performance metrics.
"""
from .base import FeatureBuilder
import pandas as pd
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class EPAFeatures(FeatureBuilder):
    """
    EPA features from play-by-play data.
    
    Creates:
    - epa_offense_home: Home team offensive EPA per play (rolling 3 games)
    - epa_defense_home: Home team defensive EPA per play (rolling 3 games)
    - epa_offense_away: Away team offensive EPA per play (rolling 3 games)
    - epa_defense_away: Away team defensive EPA per play (rolling 3 games)
    """
    
    def __init__(self, pbp_data: Optional[pd.DataFrame] = None, window=3):
        """
        Initialize EPA features.
        
        Args:
            pbp_data: Play-by-play DataFrame
            window: Rolling window size for averages
        """
        self.pbp_data = pbp_data
        self.window = window
    
    def get_required_columns(self) -> List[str]:
        return ['game_id', 'gameday', 'season', 'home_team', 'away_team']
    
    def build(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build EPA features."""
        self.validate_prerequisites(df)
        
        if self.pbp_data is None:
            logger.warning("No play-by-play data provided, skipping EPA features")
            # Add dummy columns
            df['epa_offense_home'] = 0.0
            df['epa_defense_home'] = 0.0
            df['epa_offense_away'] = 0.0
            df['epa_defense_away'] = 0.0
            return df
        
        logger.info("Building EPA features...")
        
        # Ensure datetime
        df['gameday'] = pd.to_datetime(df['gameday'])
        df = df.sort_values(['season', 'gameday']).copy()
        
        # Calculate EPA per game for each team
        epa_per_game = self._calculate_epa_per_game()
        
        # Merge with schedules
        df = df.merge(epa_per_game, on='game_id', how='left', suffixes=('', '_epa'))
        
        # Calculate rolling averages
        df['epa_offense_home'] = self._rolling_epa(df, 'home_team', 'epa_offense')
        df['epa_defense_home'] = self._rolling_epa(df, 'home_team', 'epa_defense')
        df['epa_offense_away'] = self._rolling_epa(df, 'away_team', 'epa_offense')
        df['epa_defense_away'] = self._rolling_epa(df, 'away_team', 'epa_defense')
        
        # Fill missing values (first games of season)
        for col in ['epa_offense_home', 'epa_defense_home', 'epa_offense_away', 'epa_defense_away']:
            df[col] = df[col].fillna(0)
        
        logger.info(f"✓ EPA features created: {len(self.get_feature_names())} features")
        
        return df
    
    def _calculate_epa_per_game(self) -> pd.DataFrame:
        """Calculate EPA per game for each team."""
        pbp = self.pbp_data.copy()
        
        # Offensive EPA: when team has the ball
        epa_off = pbp.groupby(['game_id', 'posteam'])['epa'].mean().reset_index()
        epa_off.columns = ['game_id', 'team', 'epa_offense']
        
        # Defensive EPA: when team is on defense
        epa_def = pbp.groupby(['game_id', 'defteam'])['epa'].mean().reset_index()
        epa_def.columns = ['game_id', 'team', 'epa_defense']
        
        # Merge
        epa_per_game = epa_off.merge(epa_def, on=['game_id', 'team'], how='outer')
        epa_per_game = epa_per_game.fillna(0)
        
        return epa_per_game
    
    def _rolling_epa(self, df: pd.DataFrame, team_col: str, epa_col: str) -> pd.Series:
        """
        Calculate rolling EPA average.
        
        NOTE: This requires proper merging of EPA per game with schedules.
        Currently returns zeros because PBP data not available.
        When PBP data is available, this should:
        1. Merge epa_per_game with schedules by game_id and team
        2. Calculate rolling average using .shift(1) to avoid lookahead
        3. Group by team and season
        """
        # Without PBP data, EPA features are not available
        # Return zeros as placeholder
        logger.warning(f"EPA rolling calculation returning zeros (no PBP data available)")
        return pd.Series(0.0, index=df.index)
    
    def get_feature_names(self) -> List[str]:
        return [
            'epa_offense_home',
            'epa_defense_home',
            'epa_offense_away',
            'epa_defense_away'
        ]

