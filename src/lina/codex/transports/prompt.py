"""Minimal task-only prompt construction for Codex CLI execution."""


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
    verification = (
        "Bu görev test yürütme doğrulaması istiyor. Uygun test komutunu gerçekten çalıştır; "
        "test komutu başarıyla tamamlanmadan başarı iddiasında bulunma. Testi çalıştıramazsan "
        "bunu açıkça bildir."
        if any(rule.kind == "test_execution_succeeded" for rule in task.verification_rules)
        else "Sonucu doğrula; test çalıştırdıysan sonucu kısa biçimde bildir."
    )
    return "\n".join((
        "Görev:", task.objective.strip(), "",
        f"Çalışma alanı: {context.root_path}",
        f"Çalışma modu: {mode_text}.",
        f"İzin verilen kapsam: {allowed_text}.",
        "Workspace dışına çıkma; symlink veya junction üzerinden sınırı aşma.",
        "Secret, credential, token, anahtar, sertifika veya auth dosyalarını okuma ve çıktıya taşıma.",
        "Git push, tag, force push, reset, clean, rebase veya commit yapma.",
        f"Beklenen çıktı: {task.expected_output.description}.",
        f"Doğrulama: {verification}",
        "Yanıt dili: Türkçe.",
    ))


def build_resume_prompt(task: CodexTask, context: ProjectContext,
                        mode: CodexExecutionMode, previous_summary: str) -> str:
    boundary = build_task_prompt(task, context, mode)
    return "\n".join((
        "Yeni ve bağlayıcı takip görevi:",
        task.objective.strip(),
        "",
        "Önceki oturum yalnız bağlamdır; eski görevi veya eski yanıtı tekrarlama.",
        f"Önceki görev özeti: {previous_summary[:160]}",
        "Yeni talimattaki ‘yalnız’, ‘sadece’, ‘bu kez’, ‘çalıştır’ ve ‘doğrula’ sınırlarını koru.",
        "",
        boundary,
    ))
