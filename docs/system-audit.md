# Lina Full-System Audit

## Amaç ve yöntem

Bu belge `v0.14.0-alpha` ürün sertleştirme turunun kısa, sürdürülebilir sistem haritasıdır. Ham sınıf/dosya dökümü değildir. Her satır bir sorumluluk sınırını, kalıcı state'i, eşzamanlı çalışma biçimini ve doğrulama odağını gösterir. Audit; kaynak kod, başlangıçta geçen 1.350 test, gerçek CLI/Ollama probe'ları ve güvenli cihaz enumeration'ı üzerinden yapılmıştır.

## Sistem sözleşmeleri

| Sistem | Giriş ve sorumluluk | Çıkış/state/persistence | Worker ve hata sınırı | Kullanıcı yüzeyi ve test odağı |
| --- | --- | --- | --- | --- |
| Core | Config, paths ve servis bootstrap | `LinaApplication`, typed service container | Warm-up worker; kontrollü startup/shutdown | Entry point, dependency failure, shutdown |
| Brain | Son kullanıcı mesajı ve güvenli context | Typed model request/response; rejected draft persist edilmez | Provider cancellation ve tek repair | Doğal Türkçe, leakage, relevance |
| Routing | Deterministic intent + aktif bağlam | Typed request/result/pending intent | Generation ve conversation isolation | Operational/informational ayrımı |
| Conversations | Mesaj, sohbet seçimi ve metadata | SQLite session/message; bounded model history | GUI worker sonucu request ID ile doğrulanır | Lazy create, switch, archive, delete |
| Memory | Açık kullanıcı kaydı ve safe retrieval | SQLite active memory records | Hassas içerik filtresi | Listeleme, silme, bounded context |
| Files | Açıkça seçilmiş/izinli dosya | Bounded text/document context | Path, size, parser ve secret kapıları | Attachment chip, hata ve kaldırma |
| Vision | Image/screen/region/camera frame | Session/generation bağlı in-memory frame | Capture ve analysis worker'ları | Preview, privacy, pause/stop |
| Voice | Device, PCM, VAD, STT ve TTS | Typed voice/speech state; audio persist edilmez | Recorder, wake, hands-free ve playback worker'ları | Tek voice status, barge-in, cihaz kaybı |
| Agent | Plan, approval ve safe tool registry | Metadata-only JSON checkpoint/history | Cancellation token ve executor | Plan/review/recovery/task center |
| Codex | Workspace, approval ve resmi CLI | Metadata-only history, remote reference, diff review | Bounded process/JSONL lifecycle | Setup, task, review, recovery |
| Notifications | Reminder/timezone/recurrence | SQLite reminders ve idempotent events | Scheduler thread | Center, unread, snooze, tray |
| Settings | Validated user preferences | Atomik schema-versioned JSON | Subscriber hatası diğerlerini bozmamalı | Ayrı ürün bölümleri, reset/live apply |
| GUI | Typed service/controller state | Presentation-only view state | Qt thread pool ve timers | Shell, composer, inspector, dialogs |
| Windows/tray | Window geometry ve close policy | Bounded persisted geometry | Exit tüm worker/timer/process'i kapatır | Restore, tray, multi-monitor |

## Başlangıç kanıtı

- Dal `main`; HEAD ve `origin/main` `f610707165507cad81ed98753d574fafc71637f4`; çalışma ağacı temiz.
- `1350 passed`; compile ve `pip check` başarılı; PySide6 `6.11.1`.
- Public core sınıfı `LinaApplication`; eski `Application` import sözleşmesi uyumsuz.
- npm Codex CLI `0.144.6` launchable, fakat resmi auth durumu logged-out.
- Ollama `0.32.1` mevcut.
- Ses enumeration'ı kayıt başlatmadan başarılı; input ve output cihazları mevcut.

## Öncelikli uyuşmazlıklar

### P0

1. Codex history dosyası doğrudan hedefe yazılıyor. Kapanma/disk hatası recovery metadata'sını bozabilir. Atomik temp + flush + replace ve eşzamanlı erişim kilidi gerekli.

### P1

1. Codex modification sonucu review beklerken session `completed` durumuna geçebiliyor. Ayrı `reviewing` durumu ve review sonrası completion gerekli.
2. Resume follow-up promptu gönderiliyor fakat “bu kez yalnız test çalıştır” gibi yeni objective için command/test evidence zorunlu değil. Follow-up ve kanıt sözleşmesi gerekli.
3. Main window kapanışı servisleri durduruyor fakat sahip olduğu Qt worker havuzunu bounded biçimde beklemiyor.
4. Speech service shutdown state/generation kapısı taşımıyor; geç worker callback'i UI state'ini geri çevirebilir.
5. Composer “Dosya” eylemi yalnız görsel loader'a bağlı. Desteklenen belge türleri ile kullanıcı metni çelişiyor.
6. Core import kontrolü `Application` bekliyor, public API yalnız `LinaApplication` sunuyor.

### P2

1. `Mic`, `Vision`, `Live Vision`, `workspace` ve raw status adları bazı yüzeylerde Türkçe terminolojiyle karışıyor.
2. Settings Agent/Codex/Voice/Vision seçeneklerini yoğun bir yapıda sunuyor; arama ve bölüm adları sadeleştirilmeli.
3. Sağ inspector birden çok capability bilgisini aynı anda gösterebiliyor; seçili bağlam önceliği güçlendirilmeli.
4. Dokümanlarda eski test sayıları, sürüm metinleri ve v0.13 dönemi sınırlamaları dağınık.

## Düzeltme ilkeleri

- P0/P1 kapanmadan görsel polish release readiness sayılmaz.
- Async sonuçlar session/generation/request kimliğiyle kabul edilir.
- Agent onayı Codex runtime approval yerine geçmez; review bekleyen sonuç completed değildir.
- Credential, prompt, raw output, audio, frame ve dosya içeriği diagnostics/history'ye yazılmaz.
- File/vision/voice erişimi yalnız açık kullanıcı eylemiyle başlar.
- Ret/reject kararı otomatik rollback değildir.
- Her dikey düzeltme hedefli regression ve integration journey testiyle kapatılır.
