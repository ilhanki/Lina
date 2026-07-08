import pytest

from lina.brain.intent import IntentType
from lina.brain.intent_analyzer import IntentAnalyzer


@pytest.mark.parametrize(
    "message",
    [
        "help",
        "?",
        "yardım",
        "komutlar",
        "ne yazabilirim",
        "nasıl kullanılır",
    ],
)
def test_intent_analyzer_detects_help(message: str) -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze(message)

    assert intent.type is IntentType.HELP


@pytest.mark.parametrize(
    "message",
    [
        "sen kimsin",
        "kimsin",
        "kendini tanıt",
        "lina kim",
    ],
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
    [
        "saat kaç",
        "şu an saat kaç",
        "zamanı söyler misin",
        "bugünün saati ne",
    ],
)
def test_intent_analyzer_detects_current_time(message: str) -> None:
    analyzer = IntentAnalyzer()

    intent = analyzer.analyze(message)

    assert intent.type is IntentType.CURRENT_TIME


@pytest.mark.parametrize(
    "message",
    [
        "lina projesinin durumu ne",
        "lina roadmap ne durumda",
        "projede ne var",
    ],
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
    [
        "selam, bir bug var",
        "selam lina bugün projede ne yaptık",
    ],
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
