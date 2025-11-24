"""Base classes for feature engineering.

All feature builders inherit from FeatureBuilder and implement:
- build(): Transform dataframe
- get_feature_names(): Return list of created features
- get_required_columns(): Return list of required input columns
"""
from abc import ABC, abstractmethod
import pandas as pd
from typing import List
import logging

logger = logging.getLogger(__name__)


class FeatureBuilder(ABC):
    """Abstract base for feature builders."""
    
    @abstractmethod
    def build(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add features to dataframe.
        
        Args:
            df: Input dataframe
            
        Returns:
            DataFrame with added features
        """
        pass
    
    @abstractmethod
    def get_feature_names(self) -> List[str]:
        """Return list of feature names this builder creates."""
        pass
    
    @abstractmethod
    def get_required_columns(self) -> List[str]:
        """Return list of required input columns."""
        pass
    
    def validate_prerequisites(self, df: pd.DataFrame) -> None:
        """Validate required columns exist."""
        required = self.get_required_columns()
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(
                f"{self.__class__.__name__} missing columns: {missing}"
            )
        logger.debug(f"{self.__class__.__name__}: Prerequisites validated")

