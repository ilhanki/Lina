"""Conservative deterministic intent classifier."""

import re

from lina.brain.routing.models import IntentRequest, IntentType
from lina.brain.routing.validation import extract_file_target, extract_memory_content, parse_reminder_arguments
from lina.codex.intent import CodexIntentKind, classify_codex_intent


class DeterministicIntentClassifier:
    def classify(self, text: str) -> IntentRequest:
        original = text.strip()
        normalized = " ".join(original.casefold().replace("i\u0307", "i").split())
        if not normalized:
            return self._request(IntentType.CHAT, original, 0.0)
        codex_intent = classify_codex_intent(original)
        if codex_intent.kind is CodexIntentKind.OPERATIONAL:
            return self._request(
                IntentType.CODEX_OPERATIONAL, original, 1.0, {"request": original}, True
            )
        if codex_intent.kind is CodexIntentKind.INFORMATIONAL:
            return self._request(IntentType.CHAT, original, 1.0)
        agent_discussion = (
            "yapay zekâ ajanı nedir", "yapay zeka ajani nedir", "agent mode güvenli mi",
            "agent mode guvenli mi", "bir plan nasıl hazırlanır", "bir plan nasil hazirlanir",
            "görev şablonu nedir", "gorev sablonu nedir", "agent neden hata yapar",
            "retry ne demek",
        )
        if any(phrase in normalized for phrase in agent_discussion):
            return self._request(IntentType.CHAT, original, 0.99)
        if any(phrase in normalized for phrase in ("agent görevini iptal et", "agent gorevini iptal et", "görevi iptal et", "gorevi iptal et")):
            return self._request(IntentType.AGENT_CANCEL, original, 1.0)
        if any(phrase in normalized for phrase in ("hazır agent görevlerini göster", "hazir agent gorevlerini goster", "hazır görevleri göster", "hazir gorevleri goster")):
            return self._request(IntentType.AGENT_TEMPLATE_LIST, original, 1.0)
        if "şablonunu kullan" in normalized or "sablonunu kullan" in normalized:
            return self._request(IntentType.AGENT_TEMPLATE_USE, original, 0.99, {"request": original})
        if any(phrase in normalized for phrase in ("agent görev geçmişi", "agent gorev gecmisi", "agent görevlerimi göster", "agent gorevlerimi goster")):
            return self._request(IntentType.AGENT_TASK_HISTORY, original, 0.99)
        if any(phrase in normalized for phrase in ("yarım kalan görevimi göster", "yarim kalan gorevimi goster", "yarım görev", "yarim gorev")):
            return self._request(IntentType.AGENT_TASK_RECOVERY, original, 0.99)
        if any(phrase in normalized for phrase in ("güvenli şekilde yeniden başlat", "guvenli sekilde yeniden baslat", "güvenli kopya olarak yeniden başlat", "guvenli kopya olarak yeniden baslat")):
            return self._request(IntentType.AGENT_TASK_RESTART, original, 1.0)
        if any(phrase in normalized for phrase in ("ikinci adımı kaldır", "ikinci adimi kaldir", "adımı atla", "adimi atla")):
            return self._request(IntentType.AGENT_STEP_SKIP, original, 0.99)
        if any(phrase in normalized for phrase in ("salt okunur adımı tekrar dene", "salt okunur adimi tekrar dene", "tekrar dene")) and "agent" in normalized:
            return self._request(IntentType.AGENT_RETRY_READ_ONLY, original, 0.98)
        if any(phrase in normalized for phrase in ("belirsiz sonucu kontrol et", "sonucun oluşup oluşmadığını kontrol et", "sonucun olusup olmadigini kontrol et")):
            return self._request(IntentType.AGENT_CHECK_UNCERTAIN_RESULT, original, 0.99)
        if any(phrase in normalized for phrase in ("görevi duraklat", "gorevi duraklat", "agentı duraklat", "agenti duraklat")):
            return self._request(IntentType.AGENT_PAUSE, original, 1.0)
        if any(phrase in normalized for phrase in ("agent görevine devam et", "agent gorevine devam et", "göreve devam et", "goreve devam et")):
            return self._request(IntentType.AGENT_RESUME, original, 1.0)
        if any(phrase in normalized for phrase in ("şu anda hangi adımdasın", "su anda hangi adimdasin", "agent durumu", "durum ne")):
            return self._request(IntentType.AGENT_STATUS, original, 0.99)
        if any(phrase in normalized for phrase in ("agent planını düzenle", "agent planini duzenle", "planı değiştir", "plani degistir")):
            return self._request(IntentType.AGENT_PLAN_EDIT, original, 0.99)
        if any(phrase in normalized for phrase in ("önce plan çıkar", "once plan cikar", "agent planı hazırla", "agent plani hazirla")):
            return self._request(IntentType.AGENT_PLAN, original, 0.99, {"request": original})
        explicit_agent = any(phrase in normalized for phrase in ("agent modunda", "agent mode ile", "bunu adım adım yap", "bunu adim adim yap"))
        if explicit_agent:
            return self._request(IntentType.AGENT_EXECUTE, original, 0.99, {"request": original})
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
