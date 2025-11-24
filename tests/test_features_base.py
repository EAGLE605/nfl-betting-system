"""Tests for feature base class."""
import pytest
import pandas as pd
from src.features.base import FeatureBuilder


class DummyBuilder(FeatureBuilder):
    """Dummy builder for testing."""
    
    def build(self, df):
        self.validate_prerequisites(df)
        df['dummy_feature'] = 1
        return df
    
    def get_feature_names(self):
        return ['dummy_feature']
    
    def get_required_columns(self):
        return ['game_id']


def test_feature_builder_validates_prerequisites():
    """Test prerequisite validation."""
    builder = DummyBuilder()
    
    # Should pass with required column
    df = pd.DataFrame({'game_id': [1, 2, 3]})
    builder.validate_prerequisites(df)
    
    # Should fail without required column
    df = pd.DataFrame({'other_col': [1, 2, 3]})
    with pytest.raises(ValueError, match="missing columns"):
        builder.validate_prerequisites(df)


def test_feature_builder_builds():
    """Test building features."""
    builder = DummyBuilder()
    df = pd.DataFrame({'game_id': [1, 2, 3]})
    
    result = builder.build(df)
    
    assert 'dummy_feature' in result.columns
    assert all(result['dummy_feature'] == 1)
    assert builder.get_feature_names() == ['dummy_feature']

