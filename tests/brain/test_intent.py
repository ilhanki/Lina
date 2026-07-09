from lina.brain.intent import Intent, IntentType


def test_intent_type_values_are_stable() -> None:
    assert IntentType.CHAT.value == "chat"
    assert IntentType.HELP.value == "help"
    assert IntentType.IDENTITY.value == "identity"
    assert IntentType.CAPABILITIES.value == "capabilities"
    assert IntentType.CURRENT_TIME.value == "current_time"
    assert IntentType.PROJECT_STATUS.value == "project_status"
    assert IntentType.PROJECT_SUMMARY.value == "project_summary"
    assert IntentType.CASUAL_GREETING.value == "casual_greeting"
    assert IntentType.COMPUTER_CONTROL_STATUS.value == "computer_control_status"
    assert IntentType.MEMORY_REMEMBER.value == "memory_remember"
    assert IntentType.MEMORY_RECALL.value == "memory_recall"
    assert IntentType.MEMORY_FORGET.value == "memory_forget"
    assert IntentType.MEMORY_CLEAR.value == "memory_clear"
    assert IntentType.MEMORY_LIST.value == "memory_list"
    assert IntentType.FILE_LIST_ALLOWED.value == "file_list_allowed"
    assert IntentType.FILE_READ.value == "file_read"
    assert IntentType.FILE_SUMMARIZE.value == "file_summarize"
    assert IntentType.FILE_CAPABILITIES.value == "file_capabilities"
    assert IntentType.UNKNOWN.value == "unknown"


def test_intent_stores_intent_type() -> None:
    intent = Intent(type=IntentType.HELP)

    assert intent.type is IntentType.HELP
