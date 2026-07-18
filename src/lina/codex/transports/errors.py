"""Typed, user-safe failures raised by the official Codex CLI transport."""


class CodexTransportError(RuntimeError):
    code = "transport_error"
    user_message = "Codex görevi tamamlanamadı."


class CodexCliNotFound(CodexTransportError):
    code = "cli_not_found"
    user_message = "Codex CLI bulunamadı."


class CodexCliTooOld(CodexTransportError):
    code = "cli_too_old"
    user_message = "Codex CLI güncel değil. Lütfen resmi kurulum yöntemiyle güncelle."


class CodexNotAuthenticated(CodexTransportError):
    code = "not_authenticated"
    user_message = "Codex oturumu gerekli."


class CodexLoginRequired(CodexNotAuthenticated):
    code = "login_required"


class CodexExecutionFailed(CodexTransportError):
    code = "execution_failed"
    user_message = "Codex görevi güvenli biçimde tamamlanamadı."


class CodexTimeout(CodexTransportError):
    code = "timeout"
    user_message = "Codex görevi zaman aşımına uğradı."


class CodexCancelled(CodexTransportError):
    code = "cancelled"
    user_message = "Codex görevi iptal edildi."


class CodexOutputInvalid(CodexTransportError):
    code = "output_invalid"
    user_message = "Codex çıktısı güvenilir biçimde okunamadı."


class CodexWorkspaceDenied(CodexTransportError):
    code = "workspace_denied"
    user_message = "Codex çalışma alanı güvenlik sınırını aştı."


class CodexApprovalRequired(CodexTransportError):
    code = "runtime_approval_required"
    user_message = "Codex çalışma sırasında ek onay istedi. İnteraktif Codex oturumunda devam etmelisin."


class CodexRateLimited(CodexTransportError):
    code = "rate_limited"
    user_message = "Codex kullanım sınırına ulaşıldı. Daha sonra tekrar deneyebilirsin."


class CodexNetworkUnavailable(CodexTransportError):
    code = "network_unavailable"
    user_message = "Codex ağına ulaşılamıyor."


class CodexProviderUnavailable(CodexTransportError):
    code = "provider_unavailable"
    user_message = "Codex hizmeti şu anda kullanılamıyor."


class CodexProcessCrashed(CodexTransportError):
    code = "process_crashed"
    user_message = "Codex işlemi beklenmedik biçimde kapandı."

