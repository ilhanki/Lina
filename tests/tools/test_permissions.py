from lina.tools.permissions import PermissionLevel, can_execute_automatically


def test_permission_level_values_are_stable() -> None:
    assert PermissionLevel.SAFE.value == "safe"
    assert PermissionLevel.READ_ONLY.value == "read_only"
    assert PermissionLevel.REQUIRES_CONFIRMATION.value == "requires_confirmation"
    assert PermissionLevel.DANGEROUS.value == "dangerous"


def test_only_safe_tools_can_execute_automatically() -> None:
    assert can_execute_automatically(PermissionLevel.SAFE)
    assert not can_execute_automatically(PermissionLevel.READ_ONLY)
    assert not can_execute_automatically(PermissionLevel.REQUIRES_CONFIRMATION)
    assert not can_execute_automatically(PermissionLevel.DANGEROUS)
