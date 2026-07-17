"""Built-in templates backed only by Lina's real allowlisted capabilities."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from uuid import uuid4

from lina.agent.models import AgentPlan, AgentStep, RiskLevel, VerificationRule
from lina.agent.templates.models import TaskTemplate, TaskTemplateCategory
from lina.agent.templates.registry import TaskTemplateRegistry


def build_builtin_template_registry() -> TaskTemplateRegistry:
    registry = TaskTemplateRegistry()
    for template in _templates():
        registry.register(template)
    return registry


def _templates() -> tuple[TaskTemplate, ...]:
    return (
        TaskTemplate(
            "reminders.create", "Hatırlatıcı oluştur", "Tarih ve saati doğrulayıp onaydan sonra hatırlatıcı oluşturur.",
            TaskTemplateCategory.REMINDERS, ("Yarın saat 10'da toplantıyı hatırlat.",),
            frozenset({"reminder.create"}), frozenset({"reminder.list"}),
            {"title": str, "due_at": datetime, "recurrence": str}, _reminder_create,
            "Kalıcı kayıt oluşturur; ayrı onay ve sonuç doğrulaması gerekir.",
        ),
        TaskTemplate(
            "reminders.summary", "Hatırlatıcıları özetle", "Yaklaşan hatırlatıcıları salt okunur biçimde getirir.",
            TaskTemplateCategory.REMINDERS, ("Bu haftaki hatırlatıcılarımı özetle.",),
            frozenset({"reminder.list"}), frozenset(), {"range": str}, _reminder_list,
        ),
        TaskTemplate(
            "reminders.conflicts", "Hatırlatıcı çakışmalarını kontrol et", "Hatırlatıcıları okuyup aynı zamana denk gelen kayıtları incelemeye hazırlar.",
            TaskTemplateCategory.REMINDERS, ("Yarınki hatırlatıcılarım çakışıyor mu?",),
            frozenset({"reminder.list"}), frozenset(), {"range": str}, _reminder_conflicts,
        ),
        TaskTemplate(
            "memory.store", "Hafızaya kaydet", "Açıkça belirtilen tercihi onaydan sonra yerel hafızaya kaydeder.",
            TaskTemplateCategory.MEMORY, ("Bundan sonra cevaplarını kısa tutmamı hatırla.",),
            frozenset({"memory.store"}), frozenset({"memory.recall"}),
            {"content": str, "category": str}, _memory_store,
            "Kalıcı hafıza kaydı oluşturur; ayrı onay gerekir.",
        ),
        TaskTemplate(
            "memory.recall", "Hafızayı kontrol et", "Hassas olmayan yerel hafıza kayıtlarını salt okunur getirir.",
            TaskTemplateCategory.MEMORY, ("Benim hakkımda neleri hatırlıyorsun?",),
            frozenset({"memory.recall"}), frozenset(), {"query": str}, _memory_recall,
        ),
        TaskTemplate(
            "files.summarize", "İzinli dosyayı oku", "Files Capability allowlist'indeki metin dosyasını salt okunur açar.",
            TaskTemplateCategory.FILES_READ_ONLY, ("Bu metin dosyasını oku ve özetle.",),
            frozenset({"files.read"}), frozenset(), {"target": str, "summary_length": str}, _file_read,
        ),
        TaskTemplate(
            "vision.single_frame", "Tek kareyi analiz et", "Açıkça sağlanan tek görüntüyü mevcut Vision UI akışında analiz eder.",
            TaskTemplateCategory.VISION, ("Bu ekran görüntüsünde önemli olan şeyi söyle.",),
            frozenset({"vision.image"}), frozenset(), {}, _vision_image,
        ),
    )


def _plan(template_id: str, title: str, steps: list[AgentStep]) -> AgentPlan:
    return AgentPlan(uuid4().hex, title, steps, template_id=template_id, title=title)


def _reminder_create(values: Mapping[str, object]) -> AgentPlan:
    step = AgentStep(
        "create-reminder", "Hatırlatıcıyı oluştur", "Onaylanan tarih ve başlıkla kalıcı kaydı oluştur.",
        "reminder.create", {"title": values["title"], "due_at": values["due_at"], "recurrence": values["recurrence"]},
        RiskLevel.PERSISTENT, True, verification_rule=VerificationRule("created_id"),
    )
    return _plan("reminders.create", "Hatırlatıcı oluşturma planı", [step])


def _reminder_list(values: Mapping[str, object]) -> AgentPlan:
    step = AgentStep("list-reminders", "Hatırlatıcıları getir", "İlgili hatırlatıcıları salt okunur listele.", "reminder.list", {}, verification_rule="non_empty")
    return _plan("reminders.summary", f"Hatırlatıcı özeti ({values['range']})", [step])


def _reminder_conflicts(values: Mapping[str, object]) -> AgentPlan:
    step = AgentStep("check-reminders", "Çakışmaları kontrol et", "Hatırlatıcı kayıtlarını salt okunur getir ve zamanlarını karşılaştır.", "reminder.list", {}, verification_rule="typed_success")
    return _plan("reminders.conflicts", f"Hatırlatıcı çakışma kontrolü ({values['range']})", [step])


def _memory_store(values: Mapping[str, object]) -> AgentPlan:
    step = AgentStep(
        "store-memory", "Bilgiyi hafızaya kaydet", "Onaylanan bilgiyi yerel hafızaya kaydet.",
        "memory.store", {"content": values["content"]}, RiskLevel.PERSISTENT, True,
        verification_rule=VerificationRule("typed_success", read_back_tool="memory.recall"),
    )
    return _plan("memory.store", "Hafıza kaydetme planı", [step])


def _memory_recall(values: Mapping[str, object]) -> AgentPlan:
    step = AgentStep("recall-memory", "Hafızayı getir", "İlgili yerel hafıza kayıtlarını salt okunur getir.", "memory.recall", {"query": values["query"]}, verification_rule="typed_success")
    return _plan("memory.recall", "Hafıza kontrolü", [step])


def _file_read(values: Mapping[str, object]) -> AgentPlan:
    step = AgentStep("read-file", "Dosyayı güvenli biçimde oku", "Allowlist, boyut ve tür sınırlarıyla dosyayı salt okunur aç.", "files.read", {"target": values["target"]}, verification_rule="typed_success")
    return _plan("files.summarize", f"İzinli dosyayı oku ({values['summary_length']})", [step])


def _vision_image(_values: Mapping[str, object]) -> AgentPlan:
    step = AgentStep("analyze-image", "Tek kareyi analiz et", "Kullanıcının sağladığı tek görüntüyü analiz et.", "vision.image", {}, verification_rule="typed_success")
    return _plan("vision.single_frame", "Tek kare Vision analizi", [step])
