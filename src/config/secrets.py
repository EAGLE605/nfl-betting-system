"""
Centralized secrets and configuration management.

All API keys and secrets flow through this module.
Supports Streamlit secrets, environment variables, and .env files.
"""

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Try to load dotenv for local development
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent.parent.parent / ".env")
except ImportError:
    pass


class SecretsManager:
    """
    Centralized secrets management with multiple backends.

    Priority order:
    1. Streamlit secrets (for deployed apps)
    2. Environment variables
    3. .env file (for local development)
    """

    # Required API keys and their descriptions
    KNOWN_KEYS = {
        "ODDS_API_KEY": {
            "description": "The Odds API - Live betting odds",
            "url": "https://the-odds-api.com/",
            "required": False,
        },
        "XAI_API_KEY": {
            "description": "xAI/Grok API - AI analysis",
            "url": "https://x.ai/",
            "required": False,
        },
        "OPENAI_API_KEY": {
            "description": "OpenAI API - GPT models",
            "url": "https://platform.openai.com/",
            "required": False,
        },
        "ANTHROPIC_API_KEY": {
            "description": "Anthropic API - Claude models",
            "url": "https://www.anthropic.com/",
            "required": False,
        },
        "GOOGLE_API_KEY": {
            "description": "Google AI - Gemini models",
            "url": "https://ai.google.dev/",
            "required": False,
        },
        "DISCORD_WEBHOOK_URL": {
            "description": "Discord webhook for notifications",
            "url": "https://discord.com/developers/docs/resources/webhook",
            "required": False,
        },
        "EMAIL_USER": {
            "description": "Email address for notifications",
            "required": False,
        },
        "EMAIL_PASSWORD": {
            "description": "Email app password",
            "required": False,
        },
    }

    _instance = None
    _streamlit_secrets = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._cache: Dict[str, Optional[str]] = {}
        self._load_streamlit_secrets()

    def _load_streamlit_secrets(self):
        """Try to load Streamlit secrets if available."""
        try:
            import streamlit as st

            if hasattr(st, "secrets"):
                self._streamlit_secrets = st.secrets
                logger.debug("Streamlit secrets loaded")
        except Exception:
            self._streamlit_secrets = None

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a secret value.

        Args:
            key: The secret key name
            default: Default value if not found

        Returns:
            The secret value or default
        """
        # Check cache first
        if key in self._cache:
            return self._cache[key]

        value = None

        # Try Streamlit secrets first
        if self._streamlit_secrets:
            try:
                value = self._streamlit_secrets.get(key)
            except Exception:
                pass

        # Fall back to environment variable
        if not value:
            value = os.environ.get(key)

        # Cache the result
        self._cache[key] = value if value else default

        return self._cache[key]

    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all known API keys.

        Returns:
            Dict with key status information
        """
        status = {}
        for key, info in self.KNOWN_KEYS.items():
            value = self.get(key)
            status[key] = {
                "configured": bool(value),
                "masked_value": (
                    f"****{value[-4:]}" if value and len(value) > 4 else "Not set"
                ),
                **info,
            }
        return status

    def is_configured(self, key: str) -> bool:
        """Check if a key is configured."""
        return bool(self.get(key))

    def clear_cache(self):
        """Clear the secrets cache."""
        self._cache.clear()


# Global singleton instance
secrets = SecretsManager()


# Convenience functions
def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a secret value."""
    return secrets.get(key, default)


def is_configured(key: str) -> bool:
    """Check if a key is configured."""
    return secrets.is_configured(key)


@lru_cache(maxsize=1)
def get_available_ai_providers() -> Dict[str, bool]:
    """
    Get available AI providers based on configured keys.

    Returns:
        Dict of provider name to availability status
    """
    return {
        "grok": is_configured("XAI_API_KEY"),
        "gpt": is_configured("OPENAI_API_KEY"),
        "claude": is_configured("ANTHROPIC_API_KEY"),
        "gemini": is_configured("GOOGLE_API_KEY"),
    }


def get_first_available_ai_provider() -> Optional[str]:
    """Get the first available AI provider."""
    providers = get_available_ai_providers()
    for provider, available in providers.items():
        if available:
            return provider
    return None
