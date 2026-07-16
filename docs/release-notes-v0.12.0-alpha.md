# Lina v0.12.0-alpha — Agent Mode Foundation

Bu sürüm Lina’ya güvenli, açıklanabilir ve kullanıcı kontrollü çok adımlı görev altyapısı ekler. Agent Mode varsayılan kapalıdır ve yalnız Ayarlar, ana panel veya açık Agent komutuyla devreye girer. Normal sohbet otomatik agent görevine dönüşmez.

## Tag Öncesi Complete Product Experience Redesign

- Typed dark/light/system renk, spacing, radius, typography, control, layout ve motion token sistemi.
- Codex’ten yalnız odak ve progresif disclosure ilkelerini alan, Lina kimliğini koruyan yeni PySide6 app shell.
- 264/64 px daraltılabilir sidebar; görünür yüzey yalnız branding, yeni sohbet, arama ve gruplu conversation history’den oluşur.
- Minimal conversation header, generation-safe unified status ve varsayılan kapalı sistem/Agent/Vision inspector’ı.
- Merkezlenmiş 760–920 px timeline, açık assistant sunumu, kompakt user bubble ve progresif mesaj eylemleri.
- Taşma oluşturmayan responsive empty state; tek composer ve Ekle/Araçlar/Gönder hiyerarşisi. Mikrofon, Ekran ve Agent bağlamsal Araçlar menüsündedir.
- Ctrl+Shift+P command palette; Ctrl+L, Ctrl+F, Ctrl+N, Ctrl+, ve mevcut composer kısayolları.
- Aktifken görünen kompakt Agent ilerlemesi ve Live Vision kartı; ayrıntılar inspector’a taşındı.
- Yedi aranabilir Settings bölümü; Ses altında Hands-Free, Gelişmiş altında Agent/Gizlilik/Sistem/Tanılama, compact/comfortable density ve schema v8 migration.
- Sıfır okunmamış bildirimde gizlenen header bildirimi; sohbet görünümü, bildirimler, sistem ayrıntıları ve Ayarlar için tek utility menüsü.
- Genel yardım/selamlama kalıbı, yabancı kelime kırıntısı ve bozuk teknik ekleri yakalayan odaklı Türkçe response quality polish.
- Negatif monitor koordinatlarını destekleyen window state restore, off-screen clamp ve maximize persistence.
- Qt standard, theme-aware ikonlar; emoji ana kontrolü, OpenAI/Codex asset’i veya yeni UI dependency yok.
- Yabancı phrase, dil sızıntısı, bozuk Türkçe ek ve ilgisiz selamlamayı yakalayan Response Quality V2; stale/cancelled repair sonucu gösterilmez, saklanmaz ve seslendirilmez.
- Offscreen dark/light/compact/settings görsel QA ve structural layout regresyon testleri.

Bilinen sınırlar: Qt offscreen test ortamı sistem fontlarını rasterize edemeyebilir; gerçek Segoe UI, Windows DPI, çoklu ekran, tray, mikrofon/TTS ve kamera doğrulaması manuel smoke gerektirir. Kamera business logic’i değiştirilmemiştir. Sürüm 0.12.0a0 kalır ve tag oluşturulmaz.

Redesign doğrulamasında tam paket 949 test, compileall, PySide6 import ve diff check kapılarından geçmiştir.

UI simplification ve response quality polish sonrasında tam paket 955 teste yükselmiştir; yeni dependency, kamera iş mantığı değişikliği, sürüm artışı veya tag yoktur.

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

## Tag Öncesi Interaction Quality & Voice Stabilization

- Normal chat, vision ve model sonuçları ortak Türkçe dil/repetition/malformed kalite kapısından geçer; reddedilen taslak persist edilmez.
- Repair en fazla bir kez, düşük sıcaklıkta ve full history/system prompt olmadan çalışır; ikinci başarısızlık güvenli fallback’tir.
- Context duplicate/internal/tool/raw Agent plan verisini filtreler; stream parser duplicate/cumulative chunk’ları bastırır.
- Mikrofon PCM’i yalnız bellekte DC offset, bounded gain ve clipping korumasından geçer. VAD pre-roll ve adaptive noise floor kullanır.
- STT metni Unicode/noise marker/whitespace açısından normalize edilir; düşük kaliteli ve kısa aralıklı duplicate transcription işaretlenir.
- Kalibrasyon ham sesi saklamadan ortam/konuşma enerjisini ölçer ve kullanıcı onayıyla hassasiyet önerir. Wake test normal komut çalıştırmaz.
- Wake phrase normalization, cooldown ve `lira`/`leyla`/`hey millet` false-positive koruması eklendi.
- TTS source/session/generation/priority metadata’sı ve duplicate/stale playback koruması eklendi; Markdown, URL, kod ve emoji konuşma kopyasından temizlenir.
- Agent plan/onay/tamamlanma/hata gibi önemli olayları ayrı tercihlerle seslendirebilir.
- Settings schema v7 ve stale callback korumalı `Lina Durumu` temeli eklendi.
- Tam prompt, full model response, transcription metni, repair içeriği ve raw audio teknik loglara veya persistence’a yazılmaz.

Gerçek Windows mikrofon, gürültülü oda, WinRT sesleri, tray ve realtime kamera davranışı manuel smoke test gerektirir. Kamera sistemi bu geçişte değiştirilmemiştir. Yeni dependency ve tag yoktur.

Stabilizasyon başlangıcında 918 test geçti; finalde 931 test, `compileall` ve PySide6 import kapıları başarılıdır.
