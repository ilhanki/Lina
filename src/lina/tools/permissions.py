"""Tool permission levels for Lina."""

from enum import Enum


class PermissionLevel(Enum):
    """Permission levels used by Lina tools."""

    SAFE = "safe"
    READ_ONLY = "read_only"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    DANGEROUS = "dangerous"


def can_execute_automatically(permission_level: PermissionLevel) -> bool:
    return permission_level is PermissionLevel.SAFE
