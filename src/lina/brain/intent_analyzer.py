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
        "nasıl kullanılır",
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
    _CASUAL_GREETING_MESSAGES = {
        "selam",
        "merhaba",
        "naber",
        "nasılsın",
        "ne haber",
        "günaydın",
        "iyi geceler",
        "iyi akşamlar",
        "selam lina",
        "merhaba lina",
        "selam lina bugün nasılsın",
        "merhaba lina bugün nasılsın",
        "selam lina nasılsın",
        "merhaba lina nasılsın",
    }
    _COMPUTER_CONTROL_STATUS_MESSAGES = {
        "bilgisayarımı yönetebilir misin",
        "bilgisayarımı kontrol edebilir misin",
        "bilgisayarıma erişebiliyor musun",
        "bilgisayarımı yönetebilecek misin",
        "ileride bilgisayarımı yönetebilecek misin",
        "bir gün bilgisayarımı yönetebilecek misin",
        "merhaba bilgisayarımı yönetebilir misin",
    }
    _MEMORY_RECALL_MESSAGES = {
        "ne hatırlıyorsun",
        "hakkımda ne biliyorsun",
        "benden ne hatırlıyorsun",
        "hafızanda ne var",
    }
    _MEMORY_LIST_MESSAGES = {
        "hafızanı listele",
        "kayıtlı bilgileri göster",
        "hatırladıklarını listele",
    }
    _MEMORY_CLEAR_MESSAGES = {
        "tüm hafızanı temizle",
        "hafızanı sıfırla",
        "bütün kayıtlı bilgileri sil",
    }
    _MEMORY_REMEMBER_PREFIXES = (
        "bunu hatırla:",
        "bunu hatırla",
        "şunu hatırla:",
        "şunu hatırla",
        "bunu kaydet:",
        "bunu kaydet",
        "bunu unutma:",
        "bunu unutma",
        "selam bunu hatırla:",
        "selam bunu hatırla",
    )
    _MEMORY_FORGET_PREFIXES = (
        "şunu unut:",
        "şunu unut",
        "bunu hafızandan sil:",
        "bunu hafızandan sil",
    )
    _FILE_LIST_ALLOWED_MESSAGES = {
        "hangi dosyaları okuyabiliyorsun",
        "izinli dosyaları listele",
        "okuyabildiğin dosyalar neler",
        "hangi proje dosyalarına erişebiliyorsun",
    }
    _FILE_CAPABILITY_MESSAGES = {
        "dosyalarımı okuyabiliyor musun",
        "bilgisayarımdaki dosyaları görebiliyor musun",
        "bilgisayarımdaki dosyaları okuyabiliyor musun",
        "proje dosyalarına erişimin var mı",
    }
    _FILE_READ_MARKERS = (
        "dosyasını oku",
        "dosyasını göster",
        "dosyayı oku",
        "dosyayı göster",
    )
    _FILE_SUMMARIZE_MARKERS = (
        "dosyasını özetle",
        "dosyasını özetler misin",
        "roadmap dosyasını özetle",
        "development log",
        "release notes",
        "ne yazıyor",
        "son ne var",
        "mimari ne durumda",
    )
    _FILE_REFERENCES = (
        "readme",
        "roadmap",
        "development log",
        "dev log",
        "architecture",
        "contributing",
        "vision",
        "brain spec",
        "conversation flow",
        "release notes",
        "docs/",
        ".md",
    )

    def analyze(self, message: str) -> Intent:
        normalized_message = self._normalize(message)

        if normalized_message in self._COMPUTER_CONTROL_STATUS_MESSAGES:
            return Intent(type=IntentType.COMPUTER_CONTROL_STATUS)

        if normalized_message in self._FILE_LIST_ALLOWED_MESSAGES:
            return Intent(type=IntentType.FILE_LIST_ALLOWED)
        if normalized_message in self._FILE_CAPABILITY_MESSAGES:
            return Intent(type=IntentType.FILE_CAPABILITIES)
        if self._looks_like_file_read(normalized_message):
            return Intent(type=IntentType.FILE_READ)
        if self._looks_like_file_summarize(normalized_message):
            return Intent(type=IntentType.FILE_SUMMARIZE)

        if self._starts_with_any(normalized_message, self._MEMORY_REMEMBER_PREFIXES):
            return Intent(type=IntentType.MEMORY_REMEMBER)
        if self._starts_with_any(normalized_message, self._MEMORY_FORGET_PREFIXES):
            return Intent(type=IntentType.MEMORY_FORGET)
        if normalized_message in self._MEMORY_CLEAR_MESSAGES:
            return Intent(type=IntentType.MEMORY_CLEAR)
        if normalized_message in self._MEMORY_LIST_MESSAGES:
            return Intent(type=IntentType.MEMORY_LIST)
        if normalized_message in self._MEMORY_RECALL_MESSAGES:
            return Intent(type=IntentType.MEMORY_RECALL)

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
        if normalized_message in self._CASUAL_GREETING_MESSAGES:
            return Intent(type=IntentType.CASUAL_GREETING)

        return Intent(type=IntentType.CHAT)

    def _normalize(self, message: str) -> str:
        stripped_message = message.strip().casefold()
        if stripped_message == "?":
            return stripped_message
        return stripped_message.rstrip("?!.,;:")

    def _starts_with_any(self, message: str, prefixes: tuple[str, ...]) -> bool:
        return any(message.startswith(prefix) for prefix in prefixes)

    def _looks_like_file_read(self, message: str) -> bool:
        if not self._contains_file_reference(message):
            return False
        return any(marker in message for marker in self._FILE_READ_MARKERS)

    def _looks_like_file_summarize(self, message: str) -> bool:
        if not self._contains_file_reference(message):
            return False
        return any(marker in message for marker in self._FILE_SUMMARIZE_MARKERS)

    def _contains_file_reference(self, message: str) -> bool:
        return any(reference in message for reference in self._FILE_REFERENCES)
