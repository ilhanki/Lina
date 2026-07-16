"""Unambiguous text and voice approval parsing."""

import re

from lina.agent.models import ApprovalDecision


_APPROVE = {"evet", "onayla", "tamam", "yap", "başlat", "baslat", "planı başlat", "plani baslat"}
_SKIP = {"atla", "bu adımı atla", "bu adimi atla", "hayır", "hayir"}
_MODIFY = {"planı düzenle", "plani duzenle", "düzenle", "duzenle"}
_CANCEL = {"iptal", "iptal et", "vazgeç", "vazgec", "görevi iptal et", "gorevi iptal et"}


def parse_approval(text: str) -> ApprovalDecision:
    normalized = re.sub(r"[^\wçğıöşü]+", " ", text.casefold()).strip()
    matches = []
    for decision, choices in (
        (ApprovalDecision.APPROVE, _APPROVE), (ApprovalDecision.SKIP, _SKIP),
        (ApprovalDecision.MODIFY, _MODIFY), (ApprovalDecision.CANCEL, _CANCEL),
    ):
        if normalized in choices:
            matches.append(decision)
    return matches[0] if len(matches) == 1 else ApprovalDecision.AMBIGUOUS
