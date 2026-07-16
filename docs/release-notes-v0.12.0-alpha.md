# Lina v0.12.0-alpha — Agent Mode Foundation

Bu sürüm Lina’ya güvenli, açıklanabilir ve kullanıcı kontrollü çok adımlı görev altyapısı ekler. Agent Mode varsayılan kapalıdır ve yalnız Ayarlar, ana panel veya açık Agent komutuyla devreye girer. Normal sohbet otomatik agent görevine dönüşmez.

## Eklenenler

- Typed `AgentSession`, `AgentPlan`, `AgentStep`, status, risk, approval, verification ve metrics modelleri.
- Maksimum 8 varsayılan, 3–12 ayarlanabilir ve 12 hard-limit’li plan doğrulaması.
- Duplicate step ID, invalid/circular dependency, duplicate tool+arguments ve unavailable/prohibited tool koruması.
- Secret/callback/raw environment içermeyen deterministic tool capability snapshot.
- Bir repair denemesiyle sınırlı schema-first planner.
- Registry allowlist’ine ek bağımsız read-only/persistent/sensitive/prohibited policy filtresi.
- Görünür plan approval ve kapatılamayan, bağlama özel persistent step approval.
- Schema validation, timeout, cancellation, duplicate execution guard ve safe exception normalization kullanan executor.
- Typed/deterministic verifier; model metni tek başına başarı kanıtı değildir.
- Read-only adımda en fazla bir retry; session başına en fazla bir bounded replan; persistent otomatik retry yok.
- Tek aktif session, generation/conversation isolation, pause/resume/cancel ve shutdown cleanup.
- Privacy-safe session metadata repository ve restart sonrası `interrupted`, no-auto-resume davranışı.
- Agent intent routing, voice/hands-free approval komutları, kompakt plan paneli, tray kontrolleri ve güvenli bildirimler.
- Settings schema v6 migration ve Agent tercihleri.

## Güvenlik ve gizlilik

Agent Mode shell/CMD/PowerShell, subprocess, Python/code execution, browser automation, email/message sending, git, mouse/keyboard, dosya yazma/silme/taşıma/yeniden adlandırma, sistem ayarı değişikliği ve gizli kamera/mikrofon başlatmayı yürütmez. Background gizli continuation veya sınırsız loop yoktur.

Persistence raw planner/tool payload, typed arguments, full prompt, model reasoning, raw exception, dosya içeriği, reminder/memory içeriği, image/audio veya Base64 saklamaz. Metrics yalnız sayaç, süre, tool/risk kategorisi gibi teknik metadata’dır.

## Test durumu

Başlangıçta 870 test geçti. Sprint sonunda 918 test, compileall ve PySide6 import doğrulaması geçti. Yeni runtime dependency eklenmemiştir.

## Bilinen sınırlar

- Deterministic planner yalnız mevcut ve açıkça eşlenen güvenli araçlarla plan oluşturur.
- Persistent read-back yalnız tool typed sonucu yeterli kimlik/veri sunduğunda doğrulanır.
- Session recovery otomatik devam etmez; kullanıcı kalan planı yeniden incelemelidir.
- Codex Bridge, Safe Desktop Capabilities ve genel amaçlı desktop automation bu sürümde yoktur.
- Manual realtime camera validation deferred. Kamera altyapısı bu sprintte değiştirilmemiştir.

Bu sprint `v0.12.0-alpha` tag’i oluşturmaz.
