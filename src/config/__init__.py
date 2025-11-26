"""Configuration module."""

from .secrets import (
    SecretsManager,
    get_available_ai_providers,
    get_first_available_ai_provider,
    get_secret,
    is_configured,
    secrets,
)

# Import new unified settings
from .settings import settings, reload_settings, print_settings

__all__ = [
    # Legacy secrets API (for backwards compatibility)
    "secrets",
    "get_secret",
    "is_configured",
    "get_available_ai_providers",
    "get_first_available_ai_provider",
    "SecretsManager",
    # New unified settings API
    "settings",
    "reload_settings",
    "print_settings",
]
