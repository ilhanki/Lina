"""Conservative deterministic intent classifier."""

import re

from lina.brain.routing.models import IntentRequest, IntentType
from lina.brain.routing.validation import extract_file_target, extract_memory_content, parse_reminder_arguments


class DeterministicIntentClassifier:
    def classify(self, text: str) -> IntentRequest:
        original = text.strip()
        normalized = " ".join(original.casefold().split())
        if not normalized:
            return self._request(IntentType.CHAT, original, 0.0)
        if any(phrase in normalized for phrase in ("kamera nasıl çalışır", "kamera nasil calisir", "ekran takibi güvenli mi", "ekran takibi guvenli mi", "vision modeli nedir")):
            return self._request(IntentType.CHAT, original, 0.99)
        if any(phrase in normalized for phrase in ("şu an neyi izliyorsun", "su an neyi izliyorsun", "takip durumu", "canlı takip durumu", "canli takip durumu")):
            return self._request(IntentType.LIVE_VISION_STATUS, original, 0.99)
        if any(phrase in normalized for phrase in ("takibi duraklat", "izlemeyi duraklat", "canlı takibi duraklat", "canli takibi duraklat", "konuşmayı durdur", "konusmayi durdur")):
            return self._request(IntentType.LIVE_VISION_PAUSE, original, 0.99)
        if any(phrase in normalized for phrase in ("takibe devam et", "tekrar devam et", "izlemeye devam et", "yorum yapmaya devam et")):
            return self._request(IntentType.LIVE_VISION_RESUME, original, 0.99)
        if any(phrase in normalized for phrase in ("takibi durdur", "izlemeyi durdur", "kamerayı kapat", "kamerayi kapat", "canlı takibi kapat", "canli takibi kapat")):
            return self._request(IntentType.LIVE_VISION_STOP, original, 0.99)
        focus = original.split(",", 1)[1].strip() if "," in original else ""
        if "kamera" in normalized and any(term in normalized for term in ("takip et", "izle", "canlı", "canli")):
            return self._request(IntentType.CAMERA_MONITOR, original, 0.99, {"user_focus": focus}, True)
        if "kamera" in normalized and any(term in normalized for term in ("bak", "analiz", "incele")):
            return self._request(IntentType.CAMERA_ANALYZE, original, 0.99, {"user_focus": focus}, True)
        if any(phrase in normalized for phrase in ("kamerayı aç", "kamerayi ac", "kamerayı ac", "kamerayi aç")):
            return self._request(IntentType.CAMERA_OPEN, original, 0.99, {"user_focus": focus}, True)
        if ("bölge" in normalized or "bolge" in normalized or "alan" in normalized) and any(term in normalized for term in ("takip et", "izle")):
            return self._request(IntentType.REGION_MONITOR, original, 0.99, {"user_focus": focus}, True)
        if "ekran" in normalized and any(term in normalized for term in ("takip et", "izle")):
            return self._request(IntentType.SCREEN_MONITOR, original, 0.99, {"user_focus": focus}, True)
        if any(term in normalized for term in ("powershell", "cmd.exe", "shell çalıştır", "komut çalıştır", "dosyayı sil", "fareyi kontrol", "klavyeyi kontrol")):
            return self._request(IntentType.UNSAFE, original, 1.0)
        if any(term in normalized for term in ("e-posta gönder", "email gönder", "webhook", "uygulamayı aç", "tarayıcıyı kontrol")):
            return self._request(IntentType.UNSUPPORTED, original, 1.0)
        if re.search(r"\b(hatırlatıcılarımı|hatırlatıcıları|hatırlatmalarımı|hatirlaticilarimi|hatirlaticilari)\s+(göster|listele)", normalized):
            return self._request(IntentType.LIST_REMINDERS, original, 0.99)
        if "hatırlatıcı" in normalized and any(word in normalized for word in ("faydalı", "nedir", "sence", "nasıl çalışır")):
            return self._request(IntentType.CHAT, original, 0.95)
        if any(phrase in normalized for phrase in ("ekran analizi nasıl", "ekran analizi nedir", "memory sistemi güvenli", "dosya okumak tehlikeli", "readme nedir")):
            return self._request(IntentType.CHAT, original, 0.95)
        if re.search(r"\b(hatırlat|hatırlatıcı oluştur)\b", normalized):
            arguments, missing = parse_reminder_arguments(original)
            arguments["missing_fields"] = missing
            return self._request(IntentType.CREATE_REMINDER, original, 0.98, arguments, True)
        if "bölge" in normalized and any(term in normalized for term in ("analiz", "incele", "ekran")):
            return self._request(IntentType.ANALYZE_REGION, original, 0.98)
        if "ekran" in normalized and any(term in normalized for term in ("analiz", "incele", "bak")):
            return self._request(IntentType.ANALYZE_SCREEN, original, 0.97)
        if any(term in normalized for term in ("görseli analiz", "görseli incele", "resmi analiz", "resmi incele")):
            return self._request(IntentType.ANALYZE_IMAGE, original, 0.97)
        if re.search(r"\b(dosya(?:sını|yı)?\s+oku|readme(?:\.md)?\s+(?:dosyasını\s+)?oku|roadmap(?:\.md)?\s+(?:dosyasını\s+)?oku)", normalized):
            return self._request(IntentType.READ_FILE, original, 0.98, {"target": extract_file_target(original)})
        if any(term in normalized for term in ("şunu hatırla", "bunu kaydet", "unutma")):
            return self._request(IntentType.MEMORY_STORE, original, 0.98, {"content": extract_memory_content(original)}, True)
        if any(term in normalized for term in ("ne hatırlıyorsun", "hafızanda", "geçen söylediğim", "hatırladıklarını")):
            return self._request(IntentType.MEMORY_RECALL, original, 0.95, {"query": original})
        return self._request(IntentType.CHAT, original, 0.9)

    @staticmethod
    def _request(intent, text, confidence, arguments=None, confirmation=False):
        return IntentRequest(intent, confidence, text, arguments or {}, confirmation, "deterministic")
