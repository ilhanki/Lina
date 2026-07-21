from PySide6.QtCore import Qt

from lina.brain.model_provider import ModelResponse
from lina.brain.routing.router import IntentRouter
from lina.brain.routing.tools import build_safe_tool_registry
from lina.files.file_access_service import FileAccessService
from lina.interfaces.qt.main_window import LinaMainWindow
from lina.interfaces.qt.widgets.tool_activity_card import ToolActivityCard
from lina.memory.repository import MemoryRepository
from lina.memory.service import MemoryService
from lina.notifications.repository import NotificationRepository
from lina.notifications.service import NotificationService
from lina.services.conversation_models import ConversationResult
from lina.services.model_diagnostics_service import VisionDiagnosticsResult, VisionStatus
from lina.agent import (
    AgentController,
    AgentExecutor,
    AgentPlan,
    AgentPlanner,
    AgentPolicy,
    AgentSession,
    AgentSessionRepository,
    AgentSessionStatus,
    AgentStep,
    AgentVerifier,
)
from lina.agent.templates import build_builtin_template_registry


class _Conversation:
    conversation_history_service = None

    def __init__(self):
        self.calls = []

    def handle_input(self, value):
        self.calls.append(value)
        return ConversationResult(ModelResponse("Normal sohbet"))


class _ImmediatePool:
    def start(self, worker):
        worker.run()


def _window(qtbot, tmp_path):
    (tmp_path / "README.md").write_text("README güvenli", encoding="utf-8")
    reminders = NotificationService(NotificationRepository(tmp_path / "notifications.sqlite3"))
    memory = MemoryService(MemoryRepository(tmp_path / "memory.sqlite3"))
    files = FileAccessService(tmp_path, allowed_paths=("README.md",), aliases={"readme": "README.md"})
    router = IntentRouter(build_safe_tool_registry(reminders, files, memory))
    conversation = _Conversation()
    window = LinaMainWindow(conversation, notification_service=reminders, intent_router=router, thread_pool=_ImmediatePool())
    qtbot.addWidget(window)
    return window, conversation, reminders


def _send(window, text):
    window._composer.set_text(text)
    window.send_message()


def _latest_card(window):
    return window.findChildren(ToolActivityCard)[-1]


def test_gui_clarification_confirmation_create_and_list(qtbot, tmp_path) -> None:
    window, conversation, reminders = _window(qtbot, tmp_path)
    _send(window, "Yarın spor yapmayı hatırlat")
    assert window._last_response_text == "Saat kaçta hatırlatayım?"
    _send(window, "18:00")
    qtbot.mouseClick(_latest_card(window).confirm_button, Qt.MouseButton.LeftButton)
    assert len(reminders.list()) == 1
    assert "hatırlatıcını oluşturdum" in window._last_response_text
    _send(window, "Hatırlatıcılarımı göster")
    assert "Yaklaşan 1" in window._last_response_text
    assert conversation.calls == []
    window._force_exit = True; window.close()


def test_gui_confirmation_cancel_does_not_persist(qtbot, tmp_path) -> None:
    window, _conversation, reminders = _window(qtbot, tmp_path)
    _send(window, "Yarın saat 18:00 spor yapmayı hatırlat")
    qtbot.mouseClick(_latest_card(window).cancel_button, Qt.MouseButton.LeftButton)
    assert reminders.list() == ()
    assert window._last_response_text == "İşlemden vazgeçildi."
    window._force_exit = True; window.close()


def test_gui_file_memory_vision_and_chat_fallback(qtbot, tmp_path, monkeypatch) -> None:
    window, conversation, _reminders = _window(qtbot, tmp_path)
    _send(window, "README dosyasını oku")
    assert "README güvenli" in window._last_response_text
    _send(window, "Şunu hatırla: Koyu temayı seviyorum")
    qtbot.mouseClick(_latest_card(window).confirm_button, Qt.MouseButton.LeftButton)
    assert "hafızaya" in window._last_response_text
    _send(window, "Geçen söylediğim şeyi bul")
    assert "Koyu temayı seviyorum" in window._last_response_text
    called = []
    monkeypatch.setattr(window, "handle_screen_request", lambda: called.append("screen"))
    _send(window, "Ekranı analiz et")
    _send(window, "Ekranda ne görüyorsun?")
    _send(window, "Bu ekrandaki yazıyı özetle.")
    assert called == ["screen", "screen", "screen"]
    _send(window, "Hatırlatıcılar sence faydalı mı?")
    assert len(conversation.calls) == 1
    assert window._last_response_text == "Normal sohbet"
    window._force_exit = True; window.close()


def test_explicit_camera_command_is_routed_before_inactive_camera_fallback(
    qtbot, tmp_path, monkeypatch
) -> None:
    window, _conversation, _reminders = _window(qtbot, tmp_path)
    routed = []
    monkeypatch.setattr(
        window,
        "_handle_routed_intent",
        lambda request, _text, _created_at: routed.append(request),
    )

    _send(window, "Kamerayı aç, elimde ne var söyle.")

    assert len(routed) == 1
    assert routed[0].intent.value == "camera_analyze"
    assert routed[0].extracted_arguments["user_focus"] == "elimde ne var söyle."
    window._force_exit = True; window.close()


def test_new_chat_clears_pending_intent(qtbot, tmp_path) -> None:
    window, _conversation, reminders = _window(qtbot, tmp_path)
    _send(window, "Yarın spor yapmayı hatırlat")
    window.start_new_chat()
    _send(window, "18:00")
    assert reminders.list() == ()
    window._force_exit = True; window.close()


def test_text_cancel_cancels_open_confirmation_card(qtbot, tmp_path) -> None:
    window, _conversation, reminders = _window(qtbot, tmp_path)
    _send(window, "Yarın saat 18:00 spor yapmayı hatırlat")
    card = _latest_card(window)
    _send(window, "vazgeç")
    assert reminders.list() == ()
    assert "İptal edildi" in card._status.text()
    assert window._last_response_text == "İşlemden vazgeçildi."
    window._force_exit = True; window.close()


def test_combined_clarification_message(qtbot, tmp_path) -> None:
    window, _conversation, _reminders = _window(qtbot, tmp_path)
    _send(window, "Yarın beni hatırlat")
    assert window._last_response_text == "Saat kaçta ve neyi hatırlatayım?"
    window._force_exit = True; window.close()


def test_vision_availability_reason_prevents_capture(qtbot, tmp_path, monkeypatch) -> None:
    window, _conversation, _reminders = _window(qtbot, tmp_path)
    window._vision_status = VisionDiagnosticsResult(VisionStatus.OLLAMA_UNREACHABLE, "vision", "yok")
    called = []; monkeypatch.setattr(window, "handle_screen_request", lambda: called.append(True))
    _send(window, "Ekranı analiz et")
    assert called == []
    assert "Ollama" in window._last_response_text
    card = _latest_card(window)
    assert not card.retry_button.isHidden()
    qtbot.mouseClick(card.retry_button, Qt.MouseButton.LeftButton)
    assert "Kullanılamıyor" in card._status.text()
    window._force_exit = True; window.close()


def test_agent_plan_is_visible_approved_and_executed_once(qtbot, tmp_path) -> None:
    (tmp_path / "README.md").write_text("safe", encoding="utf-8")
    reminders = NotificationService(NotificationRepository(tmp_path / "notifications.sqlite3"))
    memory = MemoryService(MemoryRepository(tmp_path / "memory.sqlite3"))
    files = FileAccessService(tmp_path, allowed_paths=("README.md",), aliases={"readme": "README.md"})
    registry = build_safe_tool_registry(reminders, files, memory)
    router = IntentRouter(registry)
    policy = AgentPolicy()
    controller = AgentController(AgentPlanner(policy), AgentExecutor(registry), AgentVerifier(), policy)
    window = LinaMainWindow(_Conversation(), notification_service=reminders, intent_router=router, agent_controller=controller, thread_pool=_ImmediatePool())
    qtbot.addWidget(window)
    window.show()

    _send(window, "Agent modunda hatırlatıcılarımı kontrol et")
    assert controller.session.status.value == "awaiting_plan_approval"
    assert window._agent_panel.isVisibleTo(window)
    assert window._agent_panel.start_button.isEnabled()
    qtbot.mouseClick(window._agent_panel.start_button, Qt.MouseButton.LeftButton)
    assert controller.session.status.value == "completed"
    assert controller.session.metrics.executed_step_count == 1
    window._force_exit = True; window.close()


def test_agent_enabled_natural_template_match_asks_only_missing_time_then_builds_plan(qtbot, tmp_path) -> None:
    reminders = NotificationService(NotificationRepository(tmp_path / "notifications.sqlite3"))
    memory = MemoryService(MemoryRepository(tmp_path / "memory.sqlite3"))
    files = FileAccessService(tmp_path, allowed_paths=())
    registry = build_safe_tool_registry(reminders, files, memory)
    policy = AgentPolicy()
    controller = AgentController(
        AgentPlanner(policy, template_registry=build_builtin_template_registry()),
        AgentExecutor(registry), AgentVerifier(), policy,
    )
    conversation = _Conversation()
    window = LinaMainWindow(conversation, intent_router=IntentRouter(registry), agent_controller=controller, thread_pool=_ImmediatePool())
    qtbot.addWidget(window)
    window._agent_enabled = True
    window.show()

    _send(window, "Yarın sporu hatırlat.")
    assert controller.session.status.value == "awaiting_input"
    assert window._last_response_text == "Saat kaçta hatırlatayım?"
    assert conversation.calls == []

    _send(window, "10'da.")
    assert controller.session.status.value == "awaiting_plan_approval"
    assert controller.session.plan.template_id == "reminders.create"
    assert controller.session.plan.steps[0].approval_required
    window._force_exit = True; window.close()


def test_agent_template_clarification_is_conversation_isolated_and_explanations_stay_chat(qtbot, tmp_path) -> None:
    reminders = NotificationService(NotificationRepository(tmp_path / "notifications.sqlite3"))
    memory = MemoryService(MemoryRepository(tmp_path / "memory.sqlite3"))
    registry = build_safe_tool_registry(reminders, None, memory)
    policy = AgentPolicy()
    controller = AgentController(
        AgentPlanner(policy, template_registry=build_builtin_template_registry()),
        AgentExecutor(registry), AgentVerifier(), policy,
    )
    conversation = _Conversation()
    window = LinaMainWindow(conversation, intent_router=IntentRouter(registry), agent_controller=controller, thread_pool=_ImmediatePool())
    qtbot.addWidget(window)
    window._agent_enabled = True
    _send(window, "Yarın sporu hatırlat.")
    original_conversation = controller.session.conversation_id
    window._routing_session_key = original_conversation + 1
    _send(window, "10'da.")
    assert controller.session.status.value == "awaiting_input"
    assert controller.session.conversation_id == original_conversation

    controller.cancel(controller.session.session_id)
    _send(window, "Hatırlatıcı nedir?")
    assert conversation.calls[-1].text == "Hatırlatıcı nedir?"
    window._force_exit = True; window.close()


def test_historical_safe_restart_reopens_template_for_private_parameter_confirmation(qtbot, tmp_path) -> None:
    reminders = NotificationService(NotificationRepository(tmp_path / "notifications.sqlite3"))
    registry = build_safe_tool_registry(reminders, None, None)
    policy = AgentPolicy()
    repository = AgentSessionRepository(tmp_path / "agent.json")
    source = AgentSession.create(8, "private historical request")
    source.status = AgentSessionStatus.INTERRUPTED
    source.plan = AgentPlan(
        "plan", "Hatırlatıcı planı", [AgentStep("one", "Oluştur", "Oluştur", "reminder.create", {})],
        template_id="reminders.create",
    )
    repository.save(source)
    controller = AgentController(
        AgentPlanner(policy, template_registry=build_builtin_template_registry()),
        AgentExecutor(registry), AgentVerifier(), policy, repository,
    )
    window = LinaMainWindow(_Conversation(), intent_router=IntentRouter(registry), agent_controller=controller, thread_pool=_ImmediatePool())
    qtbot.addWidget(window)
    selected = []
    window._prepare_task_template = selected.append

    window._restart_agent_task(source.session_id)

    assert selected == ["reminders.create"]
    assert "yeniden doğrula" in window._status_label.text().casefold()
    window._force_exit = True; window.close()
