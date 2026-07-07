"""Rule-based intent analysis for Lina."""

from lina.brain.intent import Intent, IntentType


class IntentAnalyzer:
    """Analyzes user messages with simple deterministic rules."""

    _HELP_MESSAGES = {
        "help",
        "?",
        "yardım",
        "komutlar",
        "ne yazabilirim",
    }
    _IDENTITY_MESSAGES = {
        "sen kimsin",
        "kimsin",
        "kendini tanıt",
        "lina kim",
    }
    _CAPABILITY_MESSAGES = {
        "neler yapabiliyorsun",
        "ne yapabiliyorsun",
        "yeteneklerin neler",
        "hangi özelliklerin var",
    }
    _CURRENT_TIME_MESSAGES = {
        "saat kaç",
        "şu an saat kaç",
        "zamanı söyler misin",
        "bugünün saati ne",
    }
    _PROJECT_STATUS_MESSAGES = {
        "lina projesinin durumu ne",
        "lina roadmap ne durumda",
        "projede ne var",
    }
    _PROJECT_SUMMARY_MESSAGES = {
        "bugün lina projesinde ne yaptık",
        "son sprintlerde ne yaptık",
        "son sprintlerde ne eklendi",
        "son gelişmeler ne",
    }

    def analyze(self, message: str) -> Intent:
        normalized_message = self._normalize(message)

        if normalized_message in self._HELP_MESSAGES:
            return Intent(type=IntentType.HELP)
        if normalized_message in self._IDENTITY_MESSAGES:
            return Intent(type=IntentType.IDENTITY)
        if normalized_message in self._CAPABILITY_MESSAGES:
            return Intent(type=IntentType.CAPABILITIES)
        if normalized_message in self._CURRENT_TIME_MESSAGES:
            return Intent(type=IntentType.CURRENT_TIME)
        if normalized_message in self._PROJECT_STATUS_MESSAGES:
            return Intent(type=IntentType.PROJECT_STATUS)
        if normalized_message in self._PROJECT_SUMMARY_MESSAGES:
            return Intent(type=IntentType.PROJECT_SUMMARY)

        return Intent(type=IntentType.CHAT)

    def _normalize(self, message: str) -> str:
        stripped_message = message.strip().lower()
        if stripped_message == "?":
            return stripped_message
        return stripped_message.rstrip("?!.,;:")
