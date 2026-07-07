from lina.brain.intent import Intent, IntentType


def test_intent_type_values_are_stable() -> None:
    assert IntentType.CHAT.value == "chat"
    assert IntentType.HELP.value == "help"
    assert IntentType.IDENTITY.value == "identity"
    assert IntentType.CAPABILITIES.value == "capabilities"
    assert IntentType.CURRENT_TIME.value == "current_time"
    assert IntentType.PROJECT_STATUS.value == "project_status"
    assert IntentType.PROJECT_SUMMARY.value == "project_summary"
    assert IntentType.UNKNOWN.value == "unknown"


def test_intent_stores_intent_type() -> None:
    intent = Intent(type=IntentType.HELP)

    assert intent.type is IntentType.HELP
