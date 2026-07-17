import pytest

from lina.agent.response_quality import AgentMessageKind, AgentResponseQuality


@pytest.mark.parametrize(("kind", "text"), [
    (AgentMessageKind.PLAN_READY, "Hatırlatıcı planı hazır. İnceleyip başlatabilirsin."),
    (AgentMessageKind.CLARIFICATION, "Saat kaçta hatırlatayım?"),
    (AgentMessageKind.APPROVAL, "Bu kalıcı adımı onaylıyor musun?"),
    (AgentMessageKind.COMPLETION, "Görev tamamlandı. Dört hatırlatıcı kontrol edildi."),
    (AgentMessageKind.FAILURE, "Görev tamamlanamadı. Gerekli araç kullanılamıyor."),
    (AgentMessageKind.RECOVERY, "Yarım kalan görev otomatik olarak devam ettirilmedi."),
])
def test_agent_messages_keep_short_natural_turkish(kind, text):
    result = AgentResponseQuality().prepare(text, kind)
    assert result.text
    assert "taskı" not in result.text
    assert "tool execution" not in result.text.casefold()
    assert "response verified" not in result.text.casefold()


@pytest.mark.parametrize("broken", [
    "tool execution completed response verified",
    "taskı tamamladım imagesi edited",
    "assistant: responseu tamam",
    "",
])
def test_invalid_agent_text_is_rejected_and_replaced_before_persistence_or_speech(broken):
    result = AgentResponseQuality().prepare(broken, AgentMessageKind.COMPLETION)
    assert result.rejected
    assert result.repaired
    assert result.text == "Görev tamamlandı."


def test_tts_text_is_short_and_deterministic():
    quality = AgentResponseQuality()
    spoken = quality.for_speech("Görev tamamlandı. Dört kayıt güvenli biçimde kontrol edildi.", AgentMessageKind.COMPLETION)
    assert spoken == "Görev tamamlandı."
    assert len(spoken) <= 220
