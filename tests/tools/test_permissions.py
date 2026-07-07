from lina.tools.permissions import PermissionLevel, check_tool_permission


def test_permission_level_values_are_stable() -> None:
    assert PermissionLevel.SAFE.value == "safe"
    assert PermissionLevel.READ_ONLY.value == "read_only"
    assert PermissionLevel.REQUIRES_CONFIRMATION.value == "requires_confirmation"
    assert PermissionLevel.DANGEROUS.value == "dangerous"


def test_only_safe_tools_can_execute_automatically() -> None:
    decision = check_tool_permission(PermissionLevel.SAFE)
    assert decision.is_allowed
    assert "Güvenli araç" in decision.reason

    for level in (
        PermissionLevel.READ_ONLY,
        PermissionLevel.REQUIRES_CONFIRMATION,
        PermissionLevel.DANGEROUS,
    ):
        decision = check_tool_permission(level)
        assert not decision.is_allowed
        assert "Onay gerekiyor" in decision.reason
        assert level.value in decision.reason
