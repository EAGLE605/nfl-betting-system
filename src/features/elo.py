"""Elo rating system for NFL teams.

Elo ratings measure team strength over time, updating after each game.
Initial rating: 1500
K-factor: 20
Home advantage: +65 points
"""
from .base import FeatureBuilder
import pandas as pd
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class EloRating:
    """
    Elo rating calculator.
    
    Uses standard Elo formula with NFL-specific parameters.
    """
    
    def __init__(
        self,
        initial_rating: float = 1500,
        k_factor: float = 20,
        home_advantage: float = 65
    ):
        """
        Initialize Elo calculator.
        
        Args:
            initial_rating: Starting rating for all teams
            k_factor: Weight factor for rating updates
            home_advantage: Points added to home team rating
        """
        self.initial_rating = initial_rating
        self.k_factor = k_factor
        self.home_advantage = home_advantage
        self.ratings: Dict[str, float] = {}
    
    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """
        Calculate expected score for team A.
        
        Args:
            rating_a: Team A's rating
            rating_b: Team B's rating
            
        Returns:
            Expected score (0-1) for team A
        """
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    
    def update_ratings(
        self,
        home_team: str,
        away_team: str,
        home_score: float,
        away_score: float
    ) -> tuple:
        """
        Update ratings after a game.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            home_score: Home team score
            away_score: Away team score
            
        Returns:
            (new_home_rating, new_away_rating)
        """
        # Get current ratings
        home_rating = self.ratings.get(home_team, self.initial_rating)
        away_rating = self.ratings.get(away_team, self.initial_rating)
        
        # Calculate expected with home advantage
        expected_home = self.expected_score(
            home_rating + self.home_advantage,
            away_rating
        )
        
        # Actual outcome (1 if home win, 0 if away win, 0.5 if tie)
        if home_score > away_score:
            actual = 1.0
        elif away_score > home_score:
            actual = 0.0
        else:
            actual = 0.5
        
        # Update ratings
        new_home = home_rating + self.k_factor * (actual - expected_home)
        new_away = away_rating + self.k_factor * ((1 - actual) - (1 - expected_home))
        
        self.ratings[home_team] = new_home
        self.ratings[away_team] = new_away
        
        return new_home, new_away
    
    def get_rating(self, team: str) -> float:
        """Get team's current rating."""
        return self.ratings.get(team, self.initial_rating)


class EloFeatures(FeatureBuilder):
    """
    Elo rating features.
    
    Creates:
    - elo_home: Home team's pre-game rating
    - elo_away: Away team's pre-game rating
    - elo_diff: elo_home - elo_away
    - elo_prob_home: Win probability from Elo
    """
    
    def __init__(self, initial_rating=1500, k_factor=20, home_advantage=65):
        self.elo = EloRating(initial_rating, k_factor, home_advantage)
    
    def get_required_columns(self) -> List[str]:
        return ['game_id', 'gameday', 'season', 'home_team', 'away_team',
                'home_score', 'away_score']
    
    def build(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build Elo features."""
        self.validate_prerequisites(df)
        
        logger.info("Building Elo features...")
        
        # Sort by date to process games chronologically
        df = df.sort_values(['season', 'gameday']).copy()
        
        # Initialize columns
        df['elo_home'] = 0.0
        df['elo_away'] = 0.0
        df['elo_prob_home'] = 0.0
        
        # Process each game
        for idx, row in df.iterrows():
            # Get ratings BEFORE game
            home_rating = self.elo.get_rating(row['home_team'])
            away_rating = self.elo.get_rating(row['away_team'])
            
            # Store pre-game ratings
            df.at[idx, 'elo_home'] = home_rating
            df.at[idx, 'elo_away'] = away_rating
            
            # Calculate win probability
            prob_home = self.elo.expected_score(
                home_rating + self.elo.home_advantage,
                away_rating
            )
            df.at[idx, 'elo_prob_home'] = prob_home
            
            # Update ratings AFTER game (if scores available)
            if pd.notna(row['home_score']) and pd.notna(row['away_score']):
                self.elo.update_ratings(
                    row['home_team'],
                    row['away_team'],
                    row['home_score'],
                    row['away_score']
                )
        
        # Add derived feature
        df['elo_diff'] = df['elo_home'] - df['elo_away']
        
        logger.info(f"✓ Elo features created: {len(self.get_feature_names())} features")
        
        return df
    
    def get_feature_names(self) -> List[str]:
        return ['elo_home', 'elo_away', 'elo_diff', 'elo_prob_home']

