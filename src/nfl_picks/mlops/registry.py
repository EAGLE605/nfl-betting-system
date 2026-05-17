"""Model registry for versioning and tracking."""

import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import joblib


@dataclass
class ModelVersion:
    """A versioned model with metadata."""
    version: str
    model_type: str
    accuracy: float
    roi: float
    sample_size: int
    features: list[str]
    created_at: datetime = field(default_factory=datetime.now)
    test_years: list[int] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "model_type": self.model_type,
            "accuracy": self.accuracy,
            "roi": self.roi,
            "sample_size": self.sample_size,
            "features": self.features,
            "created_at": self.created_at.isoformat(),
            "test_years": self.test_years,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ModelVersion":
        return cls(
            version=data["version"],
            model_type=data["model_type"],
            accuracy=data["accuracy"],
            roi=data["roi"],
            sample_size=data["sample_size"],
            features=data["features"],
            created_at=datetime.fromisoformat(data["created_at"]),
            test_years=data.get("test_years", []),
            notes=data.get("notes", ""),
        )


class ModelRegistry:
    """Registry for model versions with promotion stages."""

    STAGES = ["dev", "staging", "production"]

    def __init__(self, registry_dir: Path = Path("models/registry")):
        self.registry_dir = registry_dir
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self._versions: dict[str, ModelVersion] = {}
        self._stages: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        """Load registry from disk."""
        meta_file = self.registry_dir / "registry.json"
        if meta_file.exists():
            with open(meta_file) as f:
                data = json.load(f)
            self._versions = {
                v: ModelVersion.from_dict(d) for v, d in data.get("versions", {}).items()
            }
            self._stages = data.get("stages", {})

    def _save(self) -> None:
        """Save registry to disk."""
        meta_file = self.registry_dir / "registry.json"
        with open(meta_file, "w") as f:
            json.dump({
                "versions": {v: m.to_dict() for v, m in self._versions.items()},
                "stages": self._stages,
            }, f, indent=2)

    def register(
        self,
        model,
        scaler,
        accuracy: float,
        roi: float,
        sample_size: int,
        features: list[str],
        test_years: list[int],
        notes: str = "",
    ) -> str:
        """Register a new model version."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        version = f"v{timestamp}"

        model_version = ModelVersion(
            version=version,
            model_type=type(model).__name__,
            accuracy=accuracy,
            roi=roi,
            sample_size=sample_size,
            features=features,
            test_years=test_years,
            notes=notes,
        )

        model_path = self.registry_dir / f"{version}_model.joblib"
        scaler_path = self.registry_dir / f"{version}_scaler.joblib"

        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)

        self._versions[version] = model_version
        self._save()

        return version

    def get_version(self, version: str) -> Optional[ModelVersion]:
        """Get metadata for a version."""
        return self._versions.get(version)

    def load_model(self, version: str) -> tuple:
        """Load model and scaler for a version."""
        model_path = self.registry_dir / f"{version}_model.joblib"
        scaler_path = self.registry_dir / f"{version}_scaler.joblib"

        if not model_path.exists():
            raise ValueError(f"Model not found: {version}")

        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path) if scaler_path.exists() else None

        return model, scaler

    def promote(self, version: str, stage: str) -> None:
        """Promote a version to a stage."""
        if stage not in self.STAGES:
            raise ValueError(f"Invalid stage: {stage}. Must be one of {self.STAGES}")
        if version not in self._versions:
            raise ValueError(f"Version not found: {version}")

        self._stages[stage] = version
        self._save()

    def get_production(self) -> Optional[tuple]:
        """Get the production model."""
        version = self._stages.get("production")
        if not version:
            return None
        return self.load_model(version)

    def list_versions(self) -> list[ModelVersion]:
        """List all versions sorted by accuracy."""
        return sorted(
            self._versions.values(),
            key=lambda v: v.accuracy,
            reverse=True,
        )

    def get_stage(self, stage: str) -> Optional[str]:
        """Get the version at a stage."""
        return self._stages.get(stage)
