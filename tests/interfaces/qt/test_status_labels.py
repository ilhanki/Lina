from lina.codex.models import CodexRiskLevel, CodexSessionStatus
from lina.interfaces.qt.status_labels import codex_risk_label, codex_status_label


def test_all_codex_statuses_have_turkish_labels() -> None:
    labels = {codex_status_label(status) for status in CodexSessionStatus}
    assert len(labels) == len(CodexSessionStatus)
    assert codex_status_label(CodexSessionStatus.REVIEWING) == "Değişiklik incelemesi bekliyor"
    assert not any("_" in label for label in labels)


def test_codex_risk_and_unknown_values_are_user_friendly() -> None:
    assert codex_risk_label(CodexRiskLevel.READ_ONLY) == "Salt-okunur"
    assert codex_risk_label("modification") == "Dosya değişikliği"
    assert codex_status_label("future-state") == "Bilinmiyor"
