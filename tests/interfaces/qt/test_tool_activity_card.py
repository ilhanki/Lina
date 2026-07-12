from PySide6.QtCore import Qt

from lina.brain.routing.models import ToolStatus
from lina.interfaces.qt.widgets.tool_activity_card import ToolActivityCard


def test_confirmation_card_accessibility_keyboard_and_statuses(qtbot) -> None:
    card = ToolActivityCard("Hatırlatıcı oluştur", "Yarın 09:00", "“Spor yap”", "Kalıcı değişiklik", True)
    qtbot.addWidget(card); card.show()
    confirmed = []; cancelled = []
    card.confirmed.connect(lambda: confirmed.append(True)); card.cancelled.connect(lambda: cancelled.append(True))
    assert card.accessibleName() == "Araç işlemi: Hatırlatıcı oluştur"
    assert card.confirm_button.accessibleName()
    qtbot.keyPress(card, Qt.Key.Key_Return)
    assert confirmed == [True]
    qtbot.keyPress(card, Qt.Key.Key_Escape)
    assert cancelled == [True]
    for status, label in ((ToolStatus.RUNNING, "Çalışıyor"), (ToolStatus.SUCCESS, "Tamamlandı"), (ToolStatus.FAILURE, "Başarısız"), (ToolStatus.CANCELLED, "İptal edildi"), (ToolStatus.UNAVAILABLE, "Kullanılamıyor")):
        card.set_status(status, retryable=status in {ToolStatus.FAILURE, ToolStatus.UNAVAILABLE})
        assert label in card._status.text()


def test_retry_button_only_for_retryable_failure(qtbot) -> None:
    card = ToolActivityCard("Dosyayı oku", "Hazırlanıyor")
    qtbot.addWidget(card)
    retried = []; card.retry_requested.connect(lambda: retried.append(True))
    card.set_status(ToolStatus.FAILURE, "Tekrar denenebilir", retryable=True)
    assert not card.retry_button.isHidden()
    qtbot.mouseClick(card.retry_button, Qt.MouseButton.LeftButton)
    assert retried == [True]
    card.set_status(ToolStatus.SUCCESS)
    assert card.retry_button.isHidden()
