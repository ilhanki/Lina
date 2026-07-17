# Lina v0.12.1-alpha — Agent Reliability, Task Templates & Recovery

Bu sürüm Agent Mode Foundation’ı daha öngörülebilir, düzenlenebilir ve yeniden başlatma sınırlarında güvenli hale getirir. Hazır görevler yalnız Lina’nın gerçekten sahip olduğu local capability’lerden üretilir. Yeni shell, browser, desktop automation, network veya dosya yazma yetkisi eklenmemiştir.

## Hazır görevler

- Framework bağımsız typed `TaskTemplate`, registry, conservative matcher, schema validator ve preflight modelleri.
- Hatırlatıcı oluşturma, aralıklı özet, deterministik çakışma kontrolü, Memory store/recall, allowlist dosya okuma ve explicit tek-kare Vision şablonları.
- Agent Mode, capability availability, explanation-question ve ambiguity korumaları.
- Eksik parametre için conversation/generation izole tek clarification; typed GUI parametre formu.
- Yalnız real tool’ların katalogda görünmesi; unsupported system status ve conversation search şablonlarının sunulmaması.

## Plan inceleme ve kalite

- Typed step argümanı, dependency, risk ve approval doğrulayan `AgentPlanEditor`.
- Güvenli yeniden sıralama, optional kaldırma/atlama, regenerate ve revision-aware plan farkı.
- Added, removed, moved ve changed diff projection’ı.
- Duplicate operation, cycle, belirsiz adım, unavailable tool, gereksiz persistent risk ve step limit kalite kapısı.
- Tamamlanmış adımları ve kalıcı risk seviyesini koruyan bounded replan.

## Reliability ve recovery

- Sabit `AgentErrorCode` taxonomy’si ve kullanıcıya uygun recovery action’lar.
- Yalnız read-only timeout/transient failure için en fazla bir otomatik retry.
- Persistent/sensitive veya uncertain sonuç için no-auto-retry.
- Normalize operation hash, session/step idempotency key, duplicate execution guard ve reminder/Memory read-before-write.
- Tekrarlanan tool+argüman, clarification ve ilerlemesiz replan loop detection.
- Bounded user-visible events ve step checkpoint’leri.
- Startup sırasında bir kez `interrupted` işaretleme ve kesin no-auto-resume davranışı.
- Yeni kimlik, temiz runtime alanları, yeniden approval ve duplicate-check işaretiyle safe clone.

## Task Center V2 ve arayüz

- Aktif, onay bekleyen, duraklatılmış, yarım, tamamlanan, başarısız ve iptal edilen görev bölümleri.
- Capability-filtered Template Browser, typed Parameter Dialog, Plan Review ve dört sekmeli Inspector V2.
- Composer Araçlar menüsü, command palette, tray ve doğal dil akışlarıyla entegrasyon.
- Geçmiş görevde raw parametre saklanmadığı için sessiz restart yerine şablonu yeniden doğrulama yönlendirmesi.
- Ayarlar schema v9: şablon önerisi, startup recovery bildirimi ve 7/30/90 gün veya sınırsız geçmiş saklama.

## Yanıt, ses ve bildirim kalitesi

- Plan, clarification, approval, progress, completion, partial, failure ve recovery için kısa Türkçe Agent message kalitesi.
- Ham exception, JSON, traceback, Base64, İngilizce boilerplate ve gereksiz tekrar için güvenli fallback.
- Aynı Agent session/event için TTS deduplication; TTS kesintisinin Agent session’ını iptal etmemesi.
- Privacy-safe ve event-deduplicated tray bildirimleri.

## Gizlilik ve güvenlik

Agent repository raw kullanıcı isteği, typed argüman, tool payload, reminder/Memory/dosya içeriği, prompt, reasoning, exception, image/audio veya Base64 saklamaz. Geçmiş silme yalnız Agent metadata’sını etkiler. Persistent approval kapatılamaz. Shell, process, code execution, browser, git, email/message, mouse/keyboard, dosya yazma/silme/taşıma ve gizli cihaz başlatma prohibited kalır.

## Doğrulama

- Tam otomatik paket: `1039 passed`.
- `python -m compileall -q src tests` başarılı.
- PySide6 import ve `git diff --check` kapıları başarılıdır.
- Yeni runtime dependency eklenmemiştir.

Gerçek Windows tray, WinRT TTS, mikrofon/wake, DPI, çoklu monitör ve kamera davranışları manuel smoke checklist kapsamındadır.

## Bilinen sınırlar

- Uygulama yeniden açıldığında Agent görevi otomatik devam etmez.
- Privacy-safe geçmiş raw parametre saklamadığı için kapanıştan sonraki restart kullanıcıdan şablon değerlerini yeniden doğrulamasını ister.
- Files şablonu yalnız mevcut allowlist içindeki metni okur; genel dosya yöneticisi veya yazma aracı değildir.
- Vision şablonu explicit UI etkileşimi ister ve background capture başlatmaz.
- Codex Bridge ve Safe Desktop Capabilities sonraki sürümlerin konusudur.

Bu sprint `v0.12.1-alpha` tag’i oluşturmaz ve açık kullanıcı izni olmadan push yapmaz.
