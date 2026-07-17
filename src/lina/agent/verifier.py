"""Deterministic verification; model prose is never proof of success."""

from lina.agent.models import AgentStep, ExecutionResult, RiskLevel, VerificationResult, VerificationStatus


class AgentVerifier:
    def verify(self, step: AgentStep, result: ExecutionResult) -> VerificationResult:
        if not result.success:
            if result.error_code == "persistent_outcome_uncertain" or (
                result.error_code == "timeout" and step.risk_level in {RiskLevel.PERSISTENT, RiskLevel.SENSITIVE}
            ):
                return VerificationResult(VerificationStatus.UNCERTAIN, "Kalıcı işlemin sonucu doğrulanamadı; otomatik tekrar yapılmayacak.")
            return VerificationResult(VerificationStatus.FAILED, result.summary[:300])
        rule = step.verification_rule
        if rule.kind in {"typed_success", "success"}:
            if result.data is None:
                return VerificationResult(VerificationStatus.UNCERTAIN, "Adım başarılı bildirdi ancak typed kanıt dönmedi.")
            return VerificationResult(VerificationStatus.VERIFIED, result.summary[:300])
        if rule.kind == "non_empty":
            status = VerificationStatus.VERIFIED if result.data not in (None, "", (), [], {}) else VerificationStatus.FAILED
            return VerificationResult(status, result.summary[:300])
        if rule.kind == "created_id":
            identifier = result.data.get("id") if isinstance(result.data, dict) else getattr(result.data, "id", None)
            if identifier is None:
                return VerificationResult(VerificationStatus.UNCERTAIN, "Oluşturulan kaydın kimliği doğrulanamadı.")
            for name, expected in rule.expected.items():
                actual = result.data.get(name) if isinstance(result.data, dict) else getattr(result.data, name, None)
                if actual != expected:
                    return VerificationResult(VerificationStatus.FAILED, "Oluşturulan kayıt beklenen değerlerle eşleşmiyor.")
            return VerificationResult(VerificationStatus.VERIFIED, result.summary[:300])
        return VerificationResult(VerificationStatus.UNCERTAIN, "Adımın sonucu doğrulanamadı.")
