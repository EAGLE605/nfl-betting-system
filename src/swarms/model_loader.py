"""Model loader for swarm agents.

Loads trained models from disk and caches them for efficient reuse.
"""

import logging
from pathlib import Path
from typing import Dict, Optional

import joblib

logger = logging.getLogger(__name__)


class ModelLoader:
    """Singleton model loader with caching."""

    _instance = None
    _models_cache: Dict[str, any] = {}

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize model loader."""
        if self._initialized:
            return

        self.models_dir = Path("models")
        self._initialized = True

        logger.info(f"ModelLoader initialized. Models directory: {self.models_dir}")

    def load_model(self, model_name: str, model_type: Optional[str] = None):
        """
        Load a trained model from disk.

        Args:
            model_name: Name of model file (without .pkl extension)
            model_type: Type hint for model (xgboost, lightgbm, ensemble)

        Returns:
            Loaded model object

        Raises:
            FileNotFoundError: If model file doesn't exist
        """
        # Check cache first
        if model_name in self._models_cache:
            logger.debug(f"Model '{model_name}' loaded from cache")
            return self._models_cache[model_name]

        # Construct file path
        model_path = self.models_dir / f"{model_name}.pkl"

        if not model_path.exists():
            available_models = self.list_available_models()
            raise FileNotFoundError(
                f"Model '{model_name}' not found at {model_path}. "
                f"Available models: {available_models}"
            )

        # Load model
        try:
            logger.info(f"Loading model: {model_name} from {model_path}")
            model = joblib.load(model_path)

            # Cache for future use
            self._models_cache[model_name] = model

            logger.info(f"Successfully loaded model: {model_name}")
            return model

        except Exception as e:
            logger.error(f"Failed to load model '{model_name}': {e}")
            raise

    def list_available_models(self) -> list:
        """List all available model files."""
        if not self.models_dir.exists():
            logger.warning(f"Models directory not found: {self.models_dir}")
            return []

        model_files = list(self.models_dir.glob("*.pkl"))
        return [f.stem for f in model_files]

    def get_model_metadata(self, model_name: str) -> Dict:
        """
        Get metadata about a model without fully loading it.

        Args:
            model_name: Name of model

        Returns:
            Dict with metadata (file_size, modified_time, etc.)
        """
        model_path = self.models_dir / f"{model_name}.pkl"

        if not model_path.exists():
            return {"exists": False}

        stat = model_path.stat()
        return {
            "exists": True,
            "file_path": str(model_path),
            "size_mb": stat.st_size / (1024 * 1024),
            "modified_time": stat.st_mtime,
        }

    def get_default_models(self) -> Dict[str, str]:
        """
        Get default model names for each agent type.

        Returns:
            Dict mapping agent roles to model names
        """
        available = self.list_available_models()

        defaults = {}

        # Priority order for model selection
        model_preferences = {
            "xgboost_agent": [
                "xgboost_evolved_75pct",
                "xgboost_favorites_only",
                "xgboost_model",
            ],
            "lightgbm_agent": ["lightgbm_improved", "lightgbm_model"],
            "ensemble_agent": ["ensemble_model", "calibrated_model"],
            "calibrated_agent": ["calibrated_model"],
        }

        for agent_role, preferences in model_preferences.items():
            for model_name in preferences:
                if model_name in available:
                    defaults[agent_role] = model_name
                    break

        logger.info(f"Default model assignments: {defaults}")
        return defaults

    def clear_cache(self):
        """Clear the model cache to free memory."""
        self._models_cache.clear()
        logger.info("Model cache cleared")

    def reload_model(self, model_name: str):
        """
        Force reload a model from disk, bypassing cache.

        Args:
            model_name: Name of model to reload

        Returns:
            Reloaded model object
        """
        # Remove from cache
        if model_name in self._models_cache:
            del self._models_cache[model_name]

        # Load fresh copy
        return self.load_model(model_name)
