"""Safe live-vision prompt and speech policies."""

from __future__ import annotations

import re

from lina.vision.live.models import LiveVisionSource


_PROMPTS = {
    LiveVisionSource.CAMERA: (
        "Görüntüde açıkça görülen yeni nesneyi veya hareketi tek kısa Türkçe "
        "cümleyle söyle. Emin değilsen bunu belirt."
    ),
    LiveVisionSource.SCREEN: "Bu ekran görüntüsündeki önemli değişikliği kısa biçimde açıkla. Yeni veya dikkat edilmesi gereken şeyi belirt.",
    LiveVisionSource.REGION: "Seçili ekran bölgesindeki önemli değişikliği kısa biçimde açıkla.",
}


def build_analysis_prompt(source: LiveVisionSource, user_focus: str = "", previous_result: str = "") -> str:
    focus = sanitize_focus(user_focus)
    prompt = _PROMPTS[source]
    return prompt + (f" Kullanıcının takip hedefi: {focus}" if focus else "")


def build_camera_question_prompt(question: str) -> str:
    clean = sanitize_focus(question, maximum=240)
    return f"Bu görüntüye bakarak şu soruyu kısa Türkçe yanıtla: {clean}"


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
