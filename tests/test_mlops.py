"""Tests for MLOps infrastructure."""

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestModelRegistry:
    """Tests for model registry."""

    @pytest.fixture
    def registry(self, tmp_path):
        from nfl_picks.mlops import ModelRegistry
        return ModelRegistry(registry_dir=tmp_path / "registry")

    @pytest.fixture
    def mock_model(self):
        from sklearn.linear_model import LogisticRegression
        return LogisticRegression()

    @pytest.fixture
    def mock_scaler(self):
        from sklearn.preprocessing import StandardScaler
        import numpy as np
        scaler = StandardScaler()
        scaler.fit(np.array([[1, 2], [3, 4]]))
        return scaler

    def test_register_model(self, registry, mock_model, mock_scaler):
        version = registry.register(
            model=mock_model,
            scaler=mock_scaler,
            accuracy=65.6,
            roi=25.3,
            sample_size=317,
            features=["epa_diff", "rb_efficiency"],
            test_years=[2023, 2024],
            notes="Test model",
        )

        assert version.startswith("v")
        assert registry.get_version(version) is not None
        assert registry.get_version(version).accuracy == 65.6

    def test_load_model(self, registry, mock_model, mock_scaler):
        version = registry.register(
            model=mock_model,
            scaler=mock_scaler,
            accuracy=65.6,
            roi=25.3,
            sample_size=317,
            features=["epa_diff"],
            test_years=[2023],
        )

        loaded_model, loaded_scaler = registry.load_model(version)
        assert loaded_model is not None
        assert loaded_scaler is not None

    def test_promote_to_production(self, registry, mock_model, mock_scaler):
        version = registry.register(
            model=mock_model,
            scaler=mock_scaler,
            accuracy=65.6,
            roi=25.3,
            sample_size=317,
            features=["epa_diff"],
            test_years=[2023],
        )

        registry.promote(version, "production")
        assert registry.get_stage("production") == version

    def test_promote_invalid_stage(self, registry, mock_model, mock_scaler):
        version = registry.register(
            model=mock_model,
            scaler=mock_scaler,
            accuracy=65.6,
            roi=25.3,
            sample_size=317,
            features=["epa_diff"],
            test_years=[2023],
        )

        with pytest.raises(ValueError, match="Invalid stage"):
            registry.promote(version, "invalid")

    def test_list_versions_sorted(self, registry, mock_model, mock_scaler):
        # Register two models with different accuracy
        registry.register(
            model=mock_model,
            scaler=mock_scaler,
            accuracy=60.0,
            roi=15.0,
            sample_size=200,
            features=["epa_diff"],
            test_years=[2023],
        )
        registry.register(
            model=mock_model,
            scaler=mock_scaler,
            accuracy=70.0,
            roi=30.0,
            sample_size=200,
            features=["epa_diff"],
            test_years=[2023],
        )

        versions = registry.list_versions()
        assert len(versions) == 2
        assert versions[0].accuracy == 70.0
        assert versions[1].accuracy == 60.0

    def test_get_production_none(self, registry):
        result = registry.get_production()
        assert result is None


class TestModelVersion:
    """Tests for ModelVersion dataclass."""

    def test_to_dict_and_back(self):
        from nfl_picks.mlops import ModelVersion
        from datetime import datetime

        original = ModelVersion(
            version="v20260101",
            model_type="GradientBoostingClassifier",
            accuracy=65.6,
            roi=25.3,
            sample_size=317,
            features=["epa_diff", "rb_efficiency"],
            test_years=[2023, 2024],
            notes="Test",
        )

        data = original.to_dict()
        restored = ModelVersion.from_dict(data)

        assert restored.version == original.version
        assert restored.accuracy == original.accuracy
        assert restored.features == original.features


class TestFeatureConfig:
    """Tests for FeatureConfig."""

    def test_default_config(self):
        from nfl_picks.mlops import FeatureConfig

        config = FeatureConfig()
        assert config.cache_ttl_hours == 24
        assert config.rolling_epa_window == 5
        assert config.min_week == 4
