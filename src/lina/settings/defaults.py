"""Default user preference values."""

from lina.settings.models import UserSettings


def default_user_settings() -> UserSettings:
    """Return a fresh default settings value."""
    return UserSettings()
