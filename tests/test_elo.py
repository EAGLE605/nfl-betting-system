"""Tests for Elo rating features."""
import pytest
import pandas as pd
from src.features.elo import EloRating, EloFeatures


def test_elo_rating_initialization():
    """Test Elo rating initializes correctly."""
    elo = EloRating(initial_rating=1500)
    
    assert elo.get_rating('BUF') == 1500
    assert elo.get_rating('KC') == 1500


def test_elo_expected_score():
    """Test expected score calculation."""
    elo = EloRating()
    
    # Equal ratings = 50% expected
    assert elo.expected_score(1500, 1500) == pytest.approx(0.5, abs=0.01)
    
    # Higher rating = higher expected score
    assert elo.expected_score(1600, 1500) > 0.5
    assert elo.expected_score(1500, 1600) < 0.5


def test_elo_update_ratings():
    """Test rating updates after game."""
    elo = EloRating(k_factor=20)
    
    # BUF beats KC
    new_buf, new_kc = elo.update_ratings('BUF', 'KC', 24, 21)
    
    # Winner gains rating, loser loses rating
    assert new_buf > 1500
    assert new_kc < 1500
    
    # Ratings are stored
    assert elo.get_rating('BUF') == new_buf
    assert elo.get_rating('KC') == new_kc


def test_elo_features_build():
    """Test EloFeatures builder."""
    # Sample data
    df = pd.DataFrame({
        'game_id': ['2023_01_BUF_KC', '2023_02_KC_BUF'],
        'gameday': pd.to_datetime(['2023-09-07', '2023-09-14']),
        'season': [2023, 2023],
        'home_team': ['KC', 'BUF'],
        'away_team': ['BUF', 'KC'],
        'home_score': [21, 24],
        'away_score': [24, 20]
    })
    
    builder = EloFeatures()
    result = builder.build(df)
    
    # Check features created
    assert 'elo_home' in result.columns
    assert 'elo_away' in result.columns
    assert 'elo_diff' in result.columns
    assert 'elo_prob_home' in result.columns
    
    # First game should have initial ratings
    assert result.iloc[0]['elo_home'] == 1500
    assert result.iloc[0]['elo_away'] == 1500
    
    # Second game should have updated ratings
    assert result.iloc[1]['elo_home'] != 1500  # BUF rating changed
    assert result.iloc[1]['elo_away'] != 1500  # KC rating changed
    
    # Elo diff should be home - away
    assert result.iloc[0]['elo_diff'] == pytest.approx(
        result.iloc[0]['elo_home'] - result.iloc[0]['elo_away']
    )

