import pytest

from lina.brain.intent import IntentType
from lina.brain.intent_analyzer import IntentAnalyzer


@pytest.mark.parametrize(
    "message",
    ["help", "?", "yardım", "komutlar", "ne yazabilirim", "nasıl kullanılır"],
)
def test_intent_analyzer_detects_help(message: str) -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze(message)

    assert intent.type is IntentType.HELP


@pytest.mark.parametrize(
    "message",
    ["sen kimsin", "kimsin", "kendini tanıt", "lina kim"],
)
def test_intent_analyzer_detects_identity(message: str) -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze(message)

    assert intent.type is IntentType.IDENTITY


@pytest.mark.parametrize(
    "message",
    [
        "neler yapabiliyorsun",
        "ne yapabiliyorsun",
        "yeteneklerin neler",
        "hangi özelliklerin var",
    ],
)
def test_intent_analyzer_detects_capabilities(message: str) -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze(message)

    assert intent.type is IntentType.CAPABILITIES


@pytest.mark.parametrize(
    "message",
    ["saat kaç", "şu an saat kaç", "zamanı söyler misin", "bugünün saati ne"],
)
def test_intent_analyzer_detects_current_time(message: str) -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze(message)

    assert intent.type is IntentType.CURRENT_TIME


@pytest.mark.parametrize(
    "message",
    ["lina projesinin durumu ne", "lina roadmap ne durumda", "projede ne var"],
)
def test_intent_analyzer_detects_project_status(message: str) -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze(message)

    assert intent.type is IntentType.PROJECT_STATUS


@pytest.mark.parametrize(
    "message",
    [
        "bugün lina projesinde ne yaptık",
        "son sprintlerde ne yaptık",
        "son sprintlerde ne eklendi",
        "son gelişmeler ne",
    ],
)
def test_intent_analyzer_detects_project_summary(message: str) -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze(message)

    assert intent.type is IntentType.PROJECT_SUMMARY


@pytest.mark.parametrize(
    "message",
    [
        "selam",
        "merhaba",
        "nasılsın",
        "naber",
        "ne haber",
        "günaydın",
        "iyi geceler",
        "iyi akşamlar",
        "selam lina bugün nasılsın",
    ],
)
def test_intent_analyzer_detects_casual_greeting(message: str) -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze(message)

    assert intent.type is IntentType.CASUAL_GREETING


@pytest.mark.parametrize(
    "message",
    ["selam, bir bug var", "selam lina bugün projede ne yaptık"],
)
def test_intent_analyzer_does_not_overmatch_casual_greeting(message: str) -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze(message)

    assert intent.type is IntentType.CHAT


@pytest.mark.parametrize(
    "message",
    [
        "bilgisayarımı yönetebilir misin",
        "bilgisayarımı kontrol edebilir misin",
        "bilgisayarıma erişebiliyor musun",
        "ileride bilgisayarımı yönetebilecek misin",
        "bir gün bilgisayarımı yönetebilecek misin",
        "merhaba bilgisayarımı yönetebilir misin",
    ],
)
def test_intent_analyzer_detects_computer_control_status(message: str) -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze(message)

    assert intent.type is IntentType.COMPUTER_CONTROL_STATUS


@pytest.mark.parametrize(
    "message",
    [
        "bunu hatırla: ben kısa cevapları seviyorum",
        "şunu hatırla: Lina projesinde memory v1'e geçtik",
        "bunu kaydet: varsayılan model llama3.2:3b",
        "bunu unutma: projede Türkçe dokümantasyon istiyorum",
        "selam bunu hatırla: kısa cevap seviyorum",
        "bunu hatırla:",
    ],
)
def test_intent_analyzer_detects_memory_remember(message: str) -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze(message)

    assert intent.type is IntentType.MEMORY_REMEMBER


@pytest.mark.parametrize(
    "message",
    [
        "ne hatırlıyorsun",
        "hakkımda ne biliyorsun",
        "benden ne hatırlıyorsun",
        "hafızanda ne var",
    ],
)
def test_intent_analyzer_detects_memory_recall(message: str) -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze(message)

    assert intent.type is IntentType.MEMORY_RECALL


@pytest.mark.parametrize(
    "message",
    ["hafızanı listele", "kayıtlı bilgileri göster", "hatırladıklarını listele"],
)
def test_intent_analyzer_detects_memory_list(message: str) -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze(message)

    assert intent.type is IntentType.MEMORY_LIST


@pytest.mark.parametrize(
    "message",
    [
        "şunu unut: ben kısa cevapları seviyorum",
        "bunu hafızandan sil: varsayılan model llama3.2:3b",
        "şunu unut:",
    ],
)
def test_intent_analyzer_detects_memory_forget(message: str) -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze(message)

    assert intent.type is IntentType.MEMORY_FORGET


@pytest.mark.parametrize(
    "message",
    ["tüm hafızanı temizle", "hafızanı sıfırla", "bütün kayıtlı bilgileri sil"],
)
def test_intent_analyzer_detects_memory_clear(message: str) -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze(message)

    assert intent.type is IntentType.MEMORY_CLEAR


@pytest.mark.parametrize(
    "message",
    [
        "hangi dosyaları okuyabiliyorsun",
        "izinli dosyaları listele",
        "okuyabildiğin dosyalar neler",
        "hangi proje dosyalarına erişebiliyorsun",
    ],
)
def test_intent_analyzer_detects_file_list_allowed(message: str) -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze(message)

    assert intent.type is IntentType.FILE_LIST_ALLOWED


@pytest.mark.parametrize(
    "message",
    [
        "README dosyasını oku",
        "docs/roadmap.md dosyasını göster",
        "release notes v0.4.1 dosyasını oku",
        "contributing dosyasını oku",
    ],
)
def test_intent_analyzer_detects_file_read(message: str) -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze(message)

    assert intent.type is IntentType.FILE_READ


@pytest.mark.parametrize(
    "message",
    [
        "README dosyasını özetle",
        "roadmap dosyasını özetler misin",
        "development log'da son ne var",
        "release notes v0.4.1'de ne yazıyor",
        "architecture dosyasına göre mimari ne durumda",
    ],
)
def test_intent_analyzer_detects_file_summarize(message: str) -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze(message)

    assert intent.type is IntentType.FILE_SUMMARIZE


@pytest.mark.parametrize(
    "message",
    [
        "dosyalarımı okuyabiliyor musun",
        "bilgisayarımdaki dosyaları görebiliyor musun",
        "bilgisayarımdaki dosyaları okuyabiliyor musun",
        "proje dosyalarına erişimin var mı",
    ],
)
def test_intent_analyzer_detects_file_capabilities(message: str) -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze(message)

    assert intent.type is IntentType.FILE_CAPABILITIES


def test_intent_analyzer_prefers_file_summarize_over_casual_greeting() -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze("selam README dosyasını özetler misin")

    assert intent.type is IntentType.FILE_SUMMARIZE


def test_intent_analyzer_falls_back_to_chat() -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze("Bugün nasılsın Lina?")

    assert intent.type is IntentType.CHAT


def test_intent_analyzer_handles_case_whitespace_and_punctuation() -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze("  SeN KiMsiN?  ")

    assert intent.type is IntentType.IDENTITY


def test_intent_analyzer_does_not_match_aggressively() -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze("Saat kaçta çalışmaya başlayalım?")

    assert intent.type is IntentType.CHAT


@pytest.mark.parametrize(
    "message",
    [
        "bir gün yönetecek misin",
        "ileride bilgisayarımı yönetebilecek misin",
        "gelecekte ne yapacaksın",
        "seni geliştirecek miyiz",
        "ne zaman daha fazla şey yapacaksın",
    ],
)
def test_intent_analyzer_keeps_future_capability_questions_as_chat(message: str) -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze(message)

    if "bilgisayarımı" in message:
        assert intent.type is IntentType.COMPUTER_CONTROL_STATUS
    else:
        assert intent.type is IntentType.CHAT
