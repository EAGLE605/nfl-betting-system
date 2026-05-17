"""Configuration via pydantic-settings."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Paths
    data_dir: Path = Field(default=Path("data/raw"))
    picks_file: Path = Field(default=Path("PICKS.json"))

    # Model
    confidence_threshold: float = Field(default=0.62)
    model_version: str = Field(default="v4-rb-ngs")

    # Bankroll (optional)
    bankroll: Optional[float] = Field(default=None)
    unit_size: Optional[float] = Field(default=None)  # If None, calculated from bankroll

    # Sportsbooks
    draftkings_enabled: bool = Field(default=True)
    fanduel_enabled: bool = Field(default=True)

    # Server
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)
    debug: bool = Field(default=False)

    @property
    def calculated_unit_size(self) -> Optional[float]:
        """Calculate unit size from bankroll (1% default)."""
        if self.unit_size:
            return self.unit_size
        if self.bankroll:
            return self.bankroll * 0.01
        return None


# Global settings instance
settings = Settings()
