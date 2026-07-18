"""Minimal task-only prompt construction for Codex CLI execution."""

from pathlib import Path

from lina.codex.models import CodexExecutionMode, CodexTask, ProjectContext


def build_task_prompt(task: CodexTask, context: ProjectContext, mode: CodexExecutionMode) -> str:
    allowed = tuple(
        str(path.relative_to(context.root_path))
        for path in context.allowed_files[:200]
        if path != context.root_path
    )
    mode_text = "salt-okunur; hiçbir dosyayı değiştirme" if mode is not CodexExecutionMode.CONTROLLED_MODIFICATION else (
        "kontrollü değişiklik; yalnız onaylanan amaç için gerekli dosyaları değiştir"
    )
    allowed_text = ", ".join(allowed) if allowed else "workspace içindeki secret olmayan proje dosyaları"
    return "\n".join((
        "Görev:", task.objective.strip(), "",
        f"Çalışma alanı: {context.root_path}",
        f"Çalışma modu: {mode_text}.",
        f"İzin verilen kapsam: {allowed_text}.",
        "Workspace dışına çıkma; symlink veya junction üzerinden sınırı aşma.",
        "Secret, credential, token, anahtar, sertifika veya auth dosyalarını okuma ve çıktıya taşıma.",
        "Git push, tag, force push, reset, clean, rebase veya commit yapma.",
        f"Beklenen çıktı: {task.expected_output.description}.",
        "Doğrulama: sonucu ve varsa test kanıtını kısa biçimde bildir.",
        "Yanıt dili: Türkçe.",
    ))

