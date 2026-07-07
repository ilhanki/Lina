"""Tool permission levels and decision logic for Lina."""

from dataclasses import dataclass
from enum import Enum


class PermissionLevel(Enum):
    """Permission levels used by Lina tools."""

    SAFE = "safe"
    READ_ONLY = "read_only"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    DANGEROUS = "dangerous"


@dataclass(frozen=True)
class PermissionDecision:
    """Result of a tool permission check."""

    is_allowed: bool
    reason: str


def check_tool_permission(permission_level: PermissionLevel) -> PermissionDecision:
    """Check if a tool can be executed automatically."""
    if permission_level is PermissionLevel.SAFE:
        return PermissionDecision(
            is_allowed=True,
            reason="Güvenli araç otomatik olarak çalıştırılabilir.",
        )
    
    return PermissionDecision(
        is_allowed=False,
        reason=f"Bu aracın seviyesi ({permission_level.value}) otomatik çalıştırmaya uygun değil. Onay gerekiyor.",
    )
