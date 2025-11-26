"""
Consolidated Configuration Management

Single source of truth for ALL configuration in the NFL Betting System.

Sources (in order of priority):
1. Environment variables (highest priority)
2. .env file
3. Streamlit secrets (dashboard only)
4. config.yaml
5. Default values (lowest priority)

BEGINNER GUIDE:
---------------
Why centralized config matters:
- No more hunting through 4+ files for a setting
- Easy to see what can be configured
- Validation catches errors early
- Secrets are handled securely

How to use:
    from src.config.settings import settings

    # Access any setting
    api_key = settings.odds_api_key
    kelly_fraction = settings.betting.kelly_fraction

    # Check if feature is enabled
    if settings.features.use_llm_council:
        run_council()

Configuration priority example:
    If ODDS_API_KEY is set as env var: uses env var
    If ODDS_API_KEY is in .env file: uses .env
    If odds_api_key is in secrets.toml: uses secrets
    Otherwise: uses default (None)
"""

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Load .env file BEFORE any other imports that might need env vars
try:
    from dotenv import load_dotenv
    # Load from project root .env
    _env_path = Path(__file__).parent.parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
        logging.getLogger(__name__).debug(f"Loaded .env from {_env_path}")
except ImportError:
    pass  # python-dotenv not installed, rely on pydantic-settings

try:
    from pydantic import Field, field_validator
    from pydantic_settings import BaseSettings, SettingsConfigDict
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseSettings = object  # Fallback

logger = logging.getLogger(__name__)

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent


# =============================================================================
# CONFIGURATION CLASSES
# =============================================================================

if PYDANTIC_AVAILABLE:

    class APISettings(BaseSettings):
        """API configuration."""

        # Odds API
        odds_api_key: Optional[str] = Field(default=None, description="The Odds API key")
        odds_api_base_url: str = "https://api.the-odds-api.com/v4"
        odds_api_rate_limit: int = Field(default=500, description="Monthly request limit")

        # LLM APIs (all optional)
        openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
        anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
        xai_api_key: Optional[str] = Field(default=None, description="xAI Grok API key")
        google_api_key: Optional[str] = Field(default=None, description="Google Gemini API key")

        # ESPN (no key needed)
        espn_base_url: str = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"

        model_config = SettingsConfigDict(
            env_prefix="",
            extra="ignore",
        )


    class ModelSettings(BaseSettings):
        """Model training configuration."""

        # XGBoost
        xgb_n_estimators: int = 200
        xgb_max_depth: int = 6
        xgb_learning_rate: float = 0.05
        xgb_subsample: float = 0.8
        xgb_colsample_bytree: float = 0.8
        xgb_min_child_weight: int = 3
        xgb_early_stopping_rounds: int = 50

        # LightGBM
        lgb_n_estimators: int = 200
        lgb_max_depth: int = 6
        lgb_learning_rate: float = 0.05
        lgb_num_leaves: int = 31

        # Ensemble weights
        ensemble_xgb_weight: float = 0.6
        ensemble_lgb_weight: float = 0.3
        ensemble_elo_weight: float = 0.1

        # Validation thresholds
        min_accuracy: float = 0.55
        min_auc: float = 0.60
        min_brier: float = 0.25

        model_config = SettingsConfigDict(
            env_prefix="MODEL_",
            extra="ignore",
        )


    class BettingSettings(BaseSettings):
        """Betting configuration."""

        # Kelly criterion
        kelly_fraction: float = Field(default=0.25, ge=0.0, le=1.0)
        max_bet_fraction: float = Field(default=0.05, ge=0.0, le=0.5)

        # Bankroll management
        initial_bankroll: float = 1000.0
        min_bet: float = 5.0
        max_bet: float = 100.0

        # Confidence thresholds
        min_confidence: float = 0.55
        min_edge: float = 0.03

        # Profiles
        active_profile: str = "medium"

        model_config = SettingsConfigDict(
            env_prefix="BETTING_",
            extra="ignore",
        )

        @field_validator("kelly_fraction")
        @classmethod
        def validate_kelly(cls, v):
            if v < 0 or v > 1:
                raise ValueError("Kelly fraction must be between 0 and 1")
            return v


    class FeatureSettings(BaseSettings):
        """Feature engineering configuration."""

        # Feature groups
        use_elo: bool = True
        use_epa: bool = True
        use_weather: bool = True
        use_rest_days: bool = True
        use_injuries: bool = True
        use_referee: bool = True
        use_line_movement: bool = True

        # Elo settings
        elo_k_factor: int = 20
        elo_home_advantage: int = 65
        elo_initial: int = 1500

        # Lookback periods
        form_lookback_games: int = 5
        season_lookback_years: int = 3

        model_config = SettingsConfigDict(
            env_prefix="FEATURE_",
            extra="ignore",
        )


    class DashboardSettings(BaseSettings):
        """Dashboard configuration."""

        # Display
        refresh_interval_seconds: int = 300
        max_games_display: int = 50
        timezone: str = "America/New_York"

        # Features
        show_llm_council: bool = True
        show_parlay_builder: bool = True
        show_live_tracking: bool = True
        show_strategy_manager: bool = True

        model_config = SettingsConfigDict(
            env_prefix="DASHBOARD_",
            extra="ignore",
        )


    class NotificationSettings(BaseSettings):
        """Notification configuration."""

        # Email
        smtp_host: str = "smtp.gmail.com"
        smtp_port: int = 587
        smtp_user: Optional[str] = None
        smtp_password: Optional[str] = None
        email_recipients: List[str] = Field(default_factory=list)

        # SMS (Twilio)
        twilio_account_sid: Optional[str] = None
        twilio_auth_token: Optional[str] = None
        twilio_phone_number: Optional[str] = None
        sms_recipients: List[str] = Field(default_factory=list)

        # Settings
        notify_on_picks: bool = True
        notify_on_errors: bool = True
        min_confidence_for_alert: float = 0.60

        model_config = SettingsConfigDict(
            env_prefix="NOTIFY_",
            extra="ignore",
        )


    class PathSettings(BaseSettings):
        """Path configuration."""

        data_dir: Path = PROJECT_ROOT / "data"
        models_dir: Path = PROJECT_ROOT / "models"
        reports_dir: Path = PROJECT_ROOT / "reports"
        logs_dir: Path = PROJECT_ROOT / "logs"
        backups_dir: Path = PROJECT_ROOT / "backups"
        cache_dir: Path = PROJECT_ROOT / "data" / "cache"

        model_config = SettingsConfigDict(
            env_prefix="PATH_",
            extra="ignore",
        )


    class Settings(BaseSettings):
        """
        Master settings class.

        Combines all sub-settings into one unified configuration.
        """

        # Sub-settings
        api: APISettings = Field(default_factory=APISettings)
        model: ModelSettings = Field(default_factory=ModelSettings)
        betting: BettingSettings = Field(default_factory=BettingSettings)
        features: FeatureSettings = Field(default_factory=FeatureSettings)
        dashboard: DashboardSettings = Field(default_factory=DashboardSettings)
        notifications: NotificationSettings = Field(default_factory=NotificationSettings)
        paths: PathSettings = Field(default_factory=PathSettings)

        # Environment
        environment: str = Field(default="development")
        debug: bool = Field(default=False)
        log_level: str = Field(default="INFO")

        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._load_yaml_config()
            self._load_streamlit_secrets()

        def _load_yaml_config(self):
            """Load config.yaml and merge with settings."""
            yaml_path = PROJECT_ROOT / "config" / "config.yaml"
            if yaml_path.exists():
                try:
                    with open(yaml_path) as f:
                        yaml_config = yaml.safe_load(f)

                    # Merge YAML config (lower priority than env vars)
                    if yaml_config:
                        self._merge_yaml(yaml_config)
                except Exception as e:
                    logger.warning(f"Failed to load config.yaml: {e}")

        def _merge_yaml(self, yaml_config: Dict):
            """Merge YAML config into settings."""
            # Model params
            if "model" in yaml_config and "params" in yaml_config["model"]:
                params = yaml_config["model"]["params"]
                if not os.getenv("MODEL_XGB_N_ESTIMATORS"):
                    self.model.xgb_n_estimators = params.get("n_estimators", self.model.xgb_n_estimators)
                if not os.getenv("MODEL_XGB_MAX_DEPTH"):
                    self.model.xgb_max_depth = params.get("max_depth", self.model.xgb_max_depth)
                if not os.getenv("MODEL_XGB_LEARNING_RATE"):
                    self.model.xgb_learning_rate = params.get("learning_rate", self.model.xgb_learning_rate)

            # Betting profiles
            if "betting" in yaml_config:
                active = yaml_config["betting"].get("active_profile", "medium")
                if active in yaml_config["betting"]:
                    profile = yaml_config["betting"][active]
                    if not os.getenv("BETTING_KELLY_FRACTION"):
                        self.betting.kelly_fraction = profile.get("kelly_fraction", self.betting.kelly_fraction)
                    if not os.getenv("BETTING_MAX_BET"):
                        self.betting.max_bet = profile.get("max_bet", self.betting.max_bet)

        def _load_streamlit_secrets(self):
            """Load secrets from Streamlit (if running in dashboard)."""
            try:
                import streamlit as st
                if hasattr(st, "secrets"):
                    secrets = st.secrets

                    # API keys
                    if "ODDS_API_KEY" in secrets and not self.api.odds_api_key:
                        self.api.odds_api_key = secrets["ODDS_API_KEY"]
                    if "XAI_API_KEY" in secrets and not self.api.xai_api_key:
                        self.api.xai_api_key = secrets["XAI_API_KEY"]
                    if "OPENAI_API_KEY" in secrets and not self.api.openai_api_key:
                        self.api.openai_api_key = secrets["OPENAI_API_KEY"]
                    if "ANTHROPIC_API_KEY" in secrets and not self.api.anthropic_api_key:
                        self.api.anthropic_api_key = secrets["ANTHROPIC_API_KEY"]
                    if "GOOGLE_API_KEY" in secrets and not self.api.google_api_key:
                        self.api.google_api_key = secrets["GOOGLE_API_KEY"]

            except Exception:
                pass  # Not running in Streamlit

        # Convenience properties for common access patterns
        @property
        def odds_api_key(self) -> Optional[str]:
            return self.api.odds_api_key

        @property
        def has_llm_keys(self) -> bool:
            return any([
                self.api.openai_api_key,
                self.api.anthropic_api_key,
                self.api.xai_api_key,
                self.api.google_api_key,
            ])

        def get_llm_keys(self) -> Dict[str, str]:
            """Get all available LLM API keys."""
            keys = {}
            if self.api.openai_api_key:
                keys["openai"] = self.api.openai_api_key
            if self.api.anthropic_api_key:
                keys["anthropic"] = self.api.anthropic_api_key
            if self.api.xai_api_key:
                keys["xai"] = self.api.xai_api_key
            if self.api.google_api_key:
                keys["google"] = self.api.google_api_key
            return keys

        def to_dict(self) -> Dict[str, Any]:
            """Export settings as dictionary (hides secrets)."""
            return {
                "environment": self.environment,
                "debug": self.debug,
                "log_level": self.log_level,
                "api": {
                    "odds_api_key": "***" if self.api.odds_api_key else None,
                    "has_openai": bool(self.api.openai_api_key),
                    "has_anthropic": bool(self.api.anthropic_api_key),
                    "has_xai": bool(self.api.xai_api_key),
                    "has_google": bool(self.api.google_api_key),
                },
                "model": {
                    "xgb_n_estimators": self.model.xgb_n_estimators,
                    "xgb_max_depth": self.model.xgb_max_depth,
                    "xgb_learning_rate": self.model.xgb_learning_rate,
                },
                "betting": {
                    "kelly_fraction": self.betting.kelly_fraction,
                    "min_confidence": self.betting.min_confidence,
                    "min_edge": self.betting.min_edge,
                    "active_profile": self.betting.active_profile,
                },
                "features": {
                    "use_elo": self.features.use_elo,
                    "use_epa": self.features.use_epa,
                    "use_weather": self.features.use_weather,
                },
                "paths": {
                    "data_dir": str(self.paths.data_dir),
                    "models_dir": str(self.paths.models_dir),
                },
            }


    @lru_cache()
    def get_settings() -> Settings:
        """
        Get cached settings instance.

        Uses lru_cache to ensure only one Settings instance exists.
        """
        return Settings()


    # Global settings instance
    settings = get_settings()

else:
    # Fallback when pydantic-settings not installed
    class FallbackSettings:
        """Minimal fallback settings without pydantic."""

        def __init__(self):
            self.odds_api_key = os.getenv("ODDS_API_KEY")
            self.xai_api_key = os.getenv("XAI_API_KEY")
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
            self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
            self.google_api_key = os.getenv("GOOGLE_API_KEY")

            # Load from YAML
            yaml_path = PROJECT_ROOT / "config" / "config.yaml"
            if yaml_path.exists():
                with open(yaml_path) as f:
                    self._yaml = yaml.safe_load(f) or {}
            else:
                self._yaml = {}

            # Betting settings
            betting = self._yaml.get("betting", {})
            active = betting.get("active_profile", "medium")
            profile = betting.get(active, {})

            self.kelly_fraction = profile.get("kelly_fraction", 0.25)
            self.min_confidence = 0.55
            self.min_edge = 0.03

            # Paths
            self.data_dir = PROJECT_ROOT / "data"
            self.models_dir = PROJECT_ROOT / "models"
            self.reports_dir = PROJECT_ROOT / "reports"

        @property
        def has_llm_keys(self) -> bool:
            return any([
                self.openai_api_key,
                self.anthropic_api_key,
                self.xai_api_key,
                self.google_api_key,
            ])

    settings = FallbackSettings()
    logger.warning("pydantic-settings not installed, using fallback configuration")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def reload_settings():
    """Force reload of settings (clears cache)."""
    if PYDANTIC_AVAILABLE:
        get_settings.cache_clear()
        global settings
        settings = get_settings()


def print_settings():
    """Print current settings (for debugging)."""
    if PYDANTIC_AVAILABLE:
        import json
        print(json.dumps(settings.to_dict(), indent=2))
    else:
        print(f"Odds API Key: {'***' if settings.odds_api_key else 'Not set'}")
        print(f"Kelly Fraction: {settings.kelly_fraction}")


if __name__ == "__main__":
    print_settings()
