"""Central user-facing labels for persisted workflow enum values."""

from lina.codex.models import CodexRiskLevel, CodexSessionStatus


_CODEX_STATUS = {
    CodexSessionStatus.CREATED: "Hazır",
    CodexSessionStatus.ANALYZING: "Analiz ediliyor",
    CodexSessionStatus.PLANNING: "Görev hazırlanıyor",
    CodexSessionStatus.WAITING_APPROVAL: "Onay bekliyor",
    CodexSessionStatus.RUNNING: "Çalışıyor",
    CodexSessionStatus.VERIFYING: "Doğrulanıyor",
    CodexSessionStatus.REVIEWING: "Değişiklik incelemesi bekliyor",
    CodexSessionStatus.PAUSED: "Duraklatıldı",
    CodexSessionStatus.COMPLETED: "Tamamlandı",
    CodexSessionStatus.FAILED: "Başarısız",
    CodexSessionStatus.CANCELLED: "İptal edildi",
    CodexSessionStatus.INTERRUPTED: "Kesintiye uğradı",
}

_CODEX_RISK = {
    CodexRiskLevel.READ_ONLY: "Salt-okunur",
    CodexRiskLevel.ANALYSIS: "Analiz",
    CodexRiskLevel.SUGGESTION: "Öneri",
    CodexRiskLevel.MODIFICATION: "Dosya değişikliği",
}


def codex_status_label(status: CodexSessionStatus | str | object) -> str:
    try:
        value = status if isinstance(status, CodexSessionStatus) else CodexSessionStatus(str(status))
    except ValueError:
        return "Bilinmiyor"
    return _CODEX_STATUS[value]


def codex_risk_label(risk: CodexRiskLevel | str | object) -> str:
    try:
        value = risk if isinstance(risk, CodexRiskLevel) else CodexRiskLevel(str(risk))
    except ValueError:
        return "Bilinmiyor"
    return _CODEX_RISK[value]
