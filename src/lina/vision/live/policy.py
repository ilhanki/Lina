"""Safe live-vision prompt and speech policies."""

from __future__ import annotations

import re

from lina.vision.live.models import LiveVisionSource


_PROMPTS = {
    LiveVisionSource.CAMERA: "Bu kamera karesinde önemli olan şeyi kısa ve doğal biçimde açıkla. Kişi kimliği veya biyometrik çıkarım yapma.",
    LiveVisionSource.SCREEN: "Bu ekran görüntüsündeki önemli değişikliği kısa biçimde açıkla. Yeni veya dikkat edilmesi gereken şeyi belirt.",
    LiveVisionSource.REGION: "Seçili ekran bölgesindeki önemli değişikliği kısa biçimde açıkla.",
}


def build_analysis_prompt(source: LiveVisionSource, user_focus: str = "") -> str:
    focus = sanitize_focus(user_focus)
    return _PROMPTS[source] + (f" Kullanıcının takip hedefi: {focus}" if focus else "")


def sanitize_focus(value: str, maximum: int = 500) -> str:
    clean = " ".join(value.split())[:maximum]
    clean = re.sub(r"(?i)(system|developer|assistant)\s*:", "", clean)
    return clean.strip()


def speech_summary(text: str, maximum: int = 180) -> str:
    clean = " ".join(text.split())
    if len(clean) <= maximum:
        return clean
    sentence = re.split(r"(?<=[.!?])\s+", clean)[0]
    return sentence if len(sentence) <= maximum else clean[: maximum - 1].rstrip() + "…"
