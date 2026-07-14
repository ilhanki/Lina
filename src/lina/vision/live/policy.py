"""Safe live-vision prompt and speech policies."""

from __future__ import annotations

import re

from lina.vision.live.models import LiveVisionSource


_PROMPTS = {
    LiveVisionSource.CAMERA: (
        "Bu kamera karesini canlı bir gözlemci gibi yorumla. Yalnızca açıkça görülen, "
        "konuşmaya değer eylemi veya nesneyi tek kısa ve doğal Türkçe cümleyle söyle; "
        "örneğin el kaldırma ya da elde tutulan fare, bardak veya su şişesi. "
        "Belirsiz bir nesneyi kesinmiş gibi adlandırma. Kişi kimliği, duygu, sağlık veya "
        "biyometrik özellik çıkarımı yapma."
    ),
    LiveVisionSource.SCREEN: "Bu ekran görüntüsündeki önemli değişikliği kısa biçimde açıkla. Yeni veya dikkat edilmesi gereken şeyi belirt.",
    LiveVisionSource.REGION: "Seçili ekran bölgesindeki önemli değişikliği kısa biçimde açıkla.",
}


def build_analysis_prompt(source: LiveVisionSource, user_focus: str = "", previous_result: str = "") -> str:
    focus = sanitize_focus(user_focus)
    prompt = _PROMPTS[source]
    previous = sanitize_focus(previous_result, maximum=300)
    if source is LiveVisionSource.CAMERA and previous:
        prompt += f" Önceki gözlem: {previous} Şimdiki karede değişen eylem veya nesneyi öne çıkar."
    return prompt + (f" Kullanıcının takip hedefi: {focus}" if focus else "")


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
