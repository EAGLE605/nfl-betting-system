"""Centralized feature loading utility.

Ensures consistent feature selection across all scripts.
"""

from pathlib import Path
from typing import List
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def get_feature_columns(
    df: pd.DataFrame,
    use_recommended: bool = True,
    recommended_path: str = "reports/recommended_features.csv"
) -> List[str]:
    """
    Get feature columns consistently across all scripts.
    
    Args:
        df: DataFrame with features
        use_recommended: If True, try to load recommended_features.csv
        recommended_path: Path to recommended features CSV
    
    Returns:
        List of feature column names
    """
    # Try to load recommended features first
    if use_recommended:
        rec_path = Path(recommended_path)
        if rec_path.exists():
            try:
                recommended = pd.read_csv(rec_path)["feature"].tolist()
                # Validate all recommended features exist in dataframe
                available = [f for f in recommended if f in df.columns]
                missing = [f for f in recommended if f not in df.columns]
                
                if missing:
                    logger.warning(f"Recommended features missing from data: {missing}")
                
                if available:
                    logger.info(f"Using {len(available)} recommended features")
                    return available
            except Exception as e:
                logger.warning(f"Could not load recommended features: {e}, using fallback")
    
    # Fallback: exclude metadata columns
    exclude_cols = [
        # Game metadata
        "game_id", "gameday", "home_team", "away_team", "season", "week",
        "home_score", "away_score", "target", "result", "total", "game_type",
        "weekday", "gametime", "location", "overtime",
        
        # ID columns
        "old_game_id", "gsis", "nfl_detail_id", "pfr", "pff", "espn", "ftn",
        
        # Team/player metadata
        "away_qb_id", "home_qb_id", "away_qb_name", "home_qb_name",
        "away_coach", "home_coach", "referee", "stadium_id", "stadium",
        
        # Categorical (raw, not encoded)
        "roof", "surface", "div_game",
        
        # CRITICAL: Exclude ALL betting line features (data leakage)
        "home_moneyline", "away_moneyline", "spread_line", "home_spread_odds",
        "away_spread_odds", "total_line", "over_odds", "under_odds",
        "line_movement", "total_movement", "home_favorite",  # Derived from betting lines
    ]
    
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Filter to numeric features only
    numeric_features = df[feature_cols].select_dtypes(include=["float64", "int64"]).columns.tolist()
    
    logger.info(f"Using {len(numeric_features)} features (fallback method)")
    
    return numeric_features


def validate_features(
    model_features: List[str],
    data_features: List[str],
    model_name: str = "model"
) -> bool:
    """
    Validate that model features match data features.
    
    Args:
        model_features: Features expected by model
        data_features: Features available in data
        model_name: Name of model for error messages
    
    Returns:
        True if features match, False otherwise
    """
    model_set = set(model_features)
    data_set = set(data_features)
    
    missing = model_set - data_set
    extra = data_set - model_set
    
    if missing:
        logger.error(f"{model_name} expects {len(missing)} features not in data: {list(missing)[:5]}...")
        return False
    
    if extra:
        logger.warning(f"Data has {len(extra)} features not in {model_name}: {list(extra)[:5]}...")
    
    # Check order (XGBoost is sensitive to feature order)
    if model_features != data_features:
        logger.warning(f"Feature order differs between {model_name} and data")
        # Reorder data features to match model
        reordered = [f for f in model_features if f in data_features]
        return reordered
    
    logger.info(f"✓ Feature validation passed: {len(model_features)} features match")
    return True

