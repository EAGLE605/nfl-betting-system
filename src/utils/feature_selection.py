"""Feature selection utilities.

Helps identify and remove redundant or low-importance features.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple
from sklearn.feature_selection import mutual_info_classif
import logging

logger = logging.getLogger(__name__)


def analyze_feature_correlations(df: pd.DataFrame, feature_cols: List[str],
                                threshold: float = 0.95) -> pd.DataFrame:
    """
    Identify highly correlated features.
    
    Args:
        df: DataFrame with features
        feature_cols: List of feature column names
        threshold: Correlation threshold (default: 0.95)
    
    Returns:
        DataFrame with correlated feature pairs
    """
    corr_matrix = df[feature_cols].corr().abs()
    
    high_corr_pairs = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            corr_val = corr_matrix.iloc[i, j]
            if corr_val > threshold:
                high_corr_pairs.append({
                    "feature1": corr_matrix.columns[i],
                    "feature2": corr_matrix.columns[j],
                    "correlation": corr_val
                })
    
    return pd.DataFrame(high_corr_pairs)


def select_features_by_importance(df: pd.DataFrame, y: pd.Series,
                                feature_cols: List[str],
                                top_k: int = None,
                                min_importance: float = 0.0) -> List[str]:
    """
    Select features using mutual information.
    
    Args:
        df: DataFrame with features
        y: Target variable
        feature_cols: List of feature column names
        top_k: Select top K features (if None, use min_importance)
        min_importance: Minimum importance threshold
    
    Returns:
        List of selected feature names
    """
    X = df[feature_cols].fillna(0)
    
    # Calculate mutual information
    mi_scores = mutual_info_classif(X, y, random_state=42)
    
    # Create feature importance dataframe
    importance_df = pd.DataFrame({
        "feature": feature_cols,
        "importance": mi_scores
    }).sort_values("importance", ascending=False)
    
    logger.info(f"Feature importance range: {importance_df['importance'].min():.4f} - "
               f"{importance_df['importance'].max():.4f}")
    
    # Select features
    if top_k:
        selected = importance_df.head(top_k)["feature"].tolist()
    else:
        selected = importance_df[importance_df["importance"] >= min_importance]["feature"].tolist()
    
    logger.info(f"Selected {len(selected)} features from {len(feature_cols)}")
    
    return selected, importance_df


def remove_redundant_features(df: pd.DataFrame, feature_cols: List[str],
                             correlation_threshold: float = 0.95) -> List[str]:
    """
    Remove redundant features based on correlation.
    
    When two features are highly correlated, keeps the one with higher variance.
    
    Args:
        df: DataFrame with features
        feature_cols: List of feature column names
        correlation_threshold: Correlation threshold
    
    Returns:
        List of features to keep
    """
    corr_matrix = df[feature_cols].corr().abs()
    
    to_remove = set()
    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            if corr_matrix.iloc[i, j] > correlation_threshold:
                feat1 = corr_matrix.columns[i]
                feat2 = corr_matrix.columns[j]
                
                # Keep feature with higher variance
                var1 = df[feat1].var()
                var2 = df[feat2].var()
                
                if var1 < var2:
                    to_remove.add(feat1)
                else:
                    to_remove.add(feat2)
    
    selected = [f for f in feature_cols if f not in to_remove]
    
    logger.info(f"Removed {len(to_remove)} redundant features: {to_remove}")
    
    return selected

