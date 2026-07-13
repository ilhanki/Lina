# Lina Mimari Dokümanı

Bu doküman Lina'nın uzun vadeli mimari yönünü tanımlar. Amaç, projeyi hızlı prototip mantığıyla değil; sürdürülebilir, test edilebilir ve modüler bir masaüstü asistan platformu olarak büyütmektir.

## Voice Interaction & Inference Performance Foundation (v0.10.0-alpha)

`lina.voice` GUI’den bağımsız typed katmandır. `VoiceController` idle, listening, transcribing, thinking, speaking, interrupted, error ve disabled durumlarını yönetir. `AudioPlaybackService` generation kimliğiyle tek aktif playback sağlar; stop eski callback’i geçersiz kılar. Mic speaking sırasında başlatılırsa barge-in önce playback’i keser, sonra listening’e geçer.

`WindowsSapiTTSProvider` yeni paket veya shell çalıştırmadan, sistemde mevcutsa opsiyonel `win32com` üzerinden SAPI kullanır. Her konuşma dedicated worker thread’inde kendi COM bağlamını açar. SAPI bulunmazsa provider unavailable olur; timeline’daki yazılı cevap normal çalışır. TTS öncesi kod blokları, uzun URL, JSON/trace/Base64 benzeri içerik çıkarılır ve yalnız ses kopyası sınırlandırılır.

Wake-word için yalnız `WakeWordDetector` protokolü ve unavailable default bulunur. Detector olmadan ayar disable edilir; always-on microphone veya sahte detection yoktur.

`InferenceMetrics` yalnız provider/model ve süre/sayaç metadata’sı taşır. Ollama stream satırlarının alınma zamanı first-token ölçümünü, final Ollama metadata’sı prompt/eval token ve nanosecond duration değerlerini sağlar. Eksik metadata tahmin edilmez. `InferenceDiagnosticsService` sabit history’siz benchmark prompt’u; `ModelLifecycleService` warm-up, cancel ve text/vision best-effort unload koordinasyonunu sağlar.

Context manager, görünür conversation’ı değiştirmeden modele gönderilen en yeni complete user/assistant turn’lerini karakter bütçesine göre deterministik biçimde seçer. Image data URI, uzun Base64 ve işaretlenmiş internal/tool debug metadata modele aktarılmaz.

Shutdown sırası mic stop, voice playback/TTS stop, benchmark cancel, warm-up/model lifecycle cancel, notification scheduler stop ve tray cleanup’tır. Audio bytes loglanmaz; kayıt veya TTS çıktısı kalıcı depolanmaz.

## Temel Mimari İlkeler

- Kod tabanı İngilizce, dokümantasyon Türkçe olacaktır.
- Business logic kullanıcı arayüzünden ayrı tutulacaktır.
- Her capability kendi sorumluluğunu taşıyacaktır.
- Dış sistem entegrasyonları adapter katmanları arkasında izole edilecektir.
- Yeni özellikler doğrudan merkezi servislere gömülmeyecek, modüler yapıya uygun eklenecektir.
- Güvenlik, izin ve kullanıcı onayı özellikle automation ve file management için temel tasarım konusu olacaktır.

## Katmanlar

Lina'nın mimarisi şu ana katmanlara dayanır:

```text
interfaces
  -> services
    -> brain
      -> integrations
    -> capabilities
      -> tools
      -> integrations
core
utils
```

Bu şema nihai dosya yapısını birebir temsil etmek zorunda değildir; mimari bağımlılık yönünü anlatır.

## Core Katmanı

`core` katmanı uygulamanın temel altyapısını taşır:

- Configuration loading.
- Logging setup.
- Application lifecycle.
- Ortak protocol ve contract tanımları.
- Event sistemi.
- Ortak hata tipleri.

Bu katman capability detaylarını bilmemelidir.

## Brain Katmanı

`brain` katmanı Lina'nın LLM odaklı düşünme orkestrasyonundan sorumlu olacaktır.

Planlanan sorumluluklar:

- Prompt oluşturma.
- Context yönetimi.
- Memory entegrasyonu.
- Model seçimi.
- Tool planlama.
- Model cevaplarını doğrulama.
- Gelecekte agent koordinasyonuna zemin hazırlama.

Önemli karar: `brain` her şeyi yapan dev bir sınıf olmayacaktır. Küçük ve uzman bileşenleri koordine eden bir orchestration layer olarak tasarlanacaktır.

## Capability Yaklaşımı

Lina'nın büyük özellikleri capability olarak ele alınacaktır.

Örnek capability alanları:

- `memory`
- `speech`
- `vision`
- `automation`
- `browser`
- `files`
- `camera`
- `coding`
- `calendar`
- `mail`

Bir capability; kendi servislerini, tool kayıtlarını, event handler'larını ve gerektiğinde adapter bağımlılıklarını tanımlayabilir. Ancak capability'ler birbirine doğrudan sıkı bağlanmamalıdır.

## Integration Katmanı

`integrations` katmanı dış sistemlerle konuşan adapter'ları içerir.

Örnekler:

- Ollama adapter.
- LM Studio adapter.
- OpenAI adapter.
- Gemini adapter.
- Windows API adapter.
- Browser automation adapter.
- Speech engine adapter.

Üst katmanlar dış sistemlerin detaylarını doğrudan bilmemelidir.

## Service Katmanı

`services` katmanı uygulama use-case akışlarını koordine eder.

Örnek:

```text
ConversationService
  -> Brain
  -> EventBus
  -> Memory capability
```

Servisler UI bilmemelidir. GUI, CLI veya API sadece servisleri çağırmalıdır.

## Interface Katmanı

`interfaces` katmanı Lina'nın kullanıcıya açılan yüzlerini barındırır. Bu katmandaki kod business logic üretmez; yalnızca kullanıcı etkileşimini toplar, servisleri çağırır ve sonucu kullanıcıya anlaşılır biçimde gösterir.

Mevcut masaüstü arayüzünde PySide6 birincil GUI teknolojisidir. `python gui.py` varsayılan olarak PySide6 arayüzünü başlatır. Eski Tkinter GUI geçici legacy fallback olarak korunur; backend servislerinin sözleşmeleri bu migration nedeniyle değişmez.

GUI katmanı şu sorumluluklarla sınırlıdır:

- Mesaj yazma, gönderme, görüntüleme ve kopyalama.
- Kullanıcı eylemiyle başlatılan mic akışını `SpeechService` üzerinden tetikleme.
- Model durumunu `ModelDiagnosticsService` üzerinden göstermeye çalışma.
- UI durumunu, placeholder'ları, input history'yi ve erişilebilirlik kontrollerini yönetme.
- Açık kullanıcı eylemiyle screen capture adapter'ını çağırma, önizleme/onay alma ve geçici context yaşam döngüsünü gösterme.

GUI katmanı şunları yapmamalıdır:

- Brain, Memory, Files veya Speech iş kurallarını kendi içinde uygulamak.
- Ollama veya başka model sağlayıcılarına doğrudan bağlanmak.
- Genel dosya sistemi, shell veya Windows automation yeteneği eklemek.
- Servisleri global state veya service locator gibi kullanmak.

## Screen Context Sınırı

Screen Context Foundation, ekran yakalama ile gelecekteki görsel analiz sorumluluklarını birbirinden ayırır.

- `screen` paketi Qt'den bağımsız immutable `ScreenContext` modelini ve capture contract'ını taşır.
- PySide6 adapter'ı cursor ekranını, fallback olarak primary screen'i Qt ekran API'leriyle yakalar.
- Screenshot yalnız bellekte PNG byte representation olarak tutulur; disk veya geçici dosya kullanılmaz.
- Preview dialog açık kullanıcı onayı ister. İptal edilen görüntü session context'e bağlanmaz.
- GUI yalnız tek aktif context taşır; replace, kaldırma, yeni sohbet, temizleme ve kapanış referansı temizler.
- Context Memory, Files, SQLite, prompt veya Ollama payload'una aktarılmaz.
- Pixel içeriği loglanmaz.

Local Vision Integration, bu geçici context'i yalnız açık kullanıcı sorusu sırasında ayrı bir provider sınırı üzerinden tüketir. Screen capture kendi başına model çağrısı başlatmaz.

## Local Vision Provider Sınırı

Vision request akışı text sohbetinden ayrı ancak mevcut Brain/provider contract'larıyla uyumludur:

```text
GUI ScreenContext
  -> ConversationInput + ImageAttachment
  -> ConversationService intent policy
  -> Vision Brain
  -> OllamaProvider /api/chat
  -> ConversationResult
  -> GUI attachment lifecycle
```

- `ImageAttachment` yalnız MIME type, PNG bytes, boyut ve capture metadata taşır; Qt tipi veya dosya yolu içermez.
- Base64 yalnız `OllamaProvider` JSON payload'unu hazırlarken üretilir.
- Normal text Brain mevcut text modelini kullanır; vision Brain ayrı model, prompt, timeout ve byte limiti kullanır.
- `VisionDiagnosticsService`, `/api/show` içindeki açık `vision` capability değerini doğrular.
- Attachment yalnız son user mesajının `images` alanına eklenir ve geçmiş image'lar tekrar gönderilmez.
- Başarılı vision response metin olarak history'ye girebilir; raw image ve Base64 history, Memory, Files veya loglara yazılmaz.
- Memory, Files ve deterministic intent'ler attachment'ı modele göndermez ve tüketmez.
- Görseldeki yazılar güvenilmeyen içeriktir; tool veya capability yetkisi vermez.
- Başarılı istek aktif attachment'ı tüketir, başarısız istek yeniden deneme için korur.
- Vision provider hatasında normal text modele görüntüyü görmüş gibi davranan fallback yapılmaz.

## Vision UX ve Geçici Attachment Yaşam Döngüsü

`v0.7.2-alpha` ile ekran bağlamı iki açık kullanıcı akışını destekler: tam ekran yakalama ve alan seçerek yakalama. Her iki akış da aynı `ScreenContext` modelini kullanır; alan seçimi yalnızca yakalanacak dikdörtgeni belirler ve provider sınırını değiştirmez.

Görsel attachment yalnızca aktif oturum içinde bellekte tutulur. Composer chip'i thumbnail, değiştirme ve kaldırma kontrollerini; gönderilen kullanıcı balonu ise görsel önizleme, analiz durumu ve başarısızlık sonrası yeniden analiz hazırlama davranışını sunar. `Yeniden analiz et` görseli composer'a geri yükler, otomatik gönderim başlatmaz.

Bu UX katmanı görseli kalıcı hafızaya, dosya sistemine veya bulut servisine taşımaz. Önizleme aynı bellekteki bytes üzerinden açılır; kaynak dosya yeniden okunmaz. Vision başarısız olduğunda attachment korunur ve kullanıcıya tekrar deneme imkanı verilir.

## Conversation Persistence Foundation

Conversation persistence, Memory repository'den ayrı bir domain/application özelliğidir. `ConversationRepository` yalnız `conversations` ve `conversation_messages` tablolarını yönetir; `ConversationHistoryService` session yaşam döngüsünü, başlık politikasını ve Brain için bounded text history üretimini yönetir. Qt katmanı SQL çalıştırmaz.

Varsayılan veritabanı `data/conversations.sqlite3` konumundadır ve Memory veritabanından ayrıdır. Repository her operasyon için kısa ömürlü SQLite connection açar, `PRAGMA foreign_keys = ON` kullanır ve schema'yı idempotent şekilde hazırlar. Foreign key cascade delete ile bir session silindiğinde mesajları da güvenli biçimde silinir.

Mesaj tablosu yalnız metin ve güvenli metadata taşır: role, content, sequence, message type, `had_image`, güvenli image source ve isteğe bağlı model adı. Image bytes, Base64, thumbnail veya dosya yolu için hiçbir kolon bulunmaz. Uygulama yeniden açıldığında vision user mesajı gerçek görsel yerine güvenli placeholder olarak gösterilir; yeniden analiz yalnız canlı session belleğindeki attachment için mümkündür.

ConversationService aktif session history'sini Brain context'ine bounded biçimde aktarır. Session değişiminde in-memory history tamamen yenilenir; eski session mesajlarının yeni session'a sızmasına izin verilmez. Persistence hatası model sohbetini durdurmaz; servis in-memory devam eder ve kullanıcıya kontrollü durum bilgisi sunabilir.

## Conversation Timeline ve Welcome Sınırı

Mesaj timestamp'inin sahibi conversation akışıdır. User zamanı request oluşturulurken, assistant zamanı anlamlı response tamamlandığında bir kez üretilir; aynı değer repository'ye ve UI widget'ına taşınır. SQLite UTC timezone-aware ISO-8601 saklar. Presentation katmanı timestamp'i kullanıcının yerel saatine çevirir. Legacy naive değerler UTC varsayımıyla okunur; malformed değerler güvenli mevcut zaman fallback'iyle tüm sohbeti düşürmez.

Conversation sıralaması `last_message_at DESC`, ardından `created_at DESC` ve `id DESC` ile deterministiktir. Yeni boş session'larda `last_message_at`, `created_at` ile başlatılır. Rename veya yalnız session seçimi sıralamayı değiştirmez; gerçek mesaj aktivitesi session'ı üste taşır.

Boş conversation için gösterilen `WelcomeStateWidget` yalnız PySide6 presentation state'idir. Normal assistant message değildir, Brain history'sine girmez, last response sayılmaz ve database'e yazılmaz. İlk user mesajında kaldırılır; clear veya yeni boş session'da yeniden oluşturulur. Greeting saat aralığına göre, ikincil metin ise gün/session verisiyle deterministik seçilir.

## Conversation Search ve Management Sınırı

ConversationRepository v0.8.1 schema'sını transaction-safe biçimde v0.8.2 alanlarıyla genişletir: `is_pinned`, `is_archived`, `pinned_at` ve `archived_at`. Migration mevcut session/message kayıtlarını korur, Memory tablolarına dokunmaz ve `PRAGMA user_version` değerini 2'ye taşır. Pin/archive işlemleri `last_message_at` veya message content'i değiştirmez.

Search kapsamı yalnız conversation title, user text ve assistant text'tir. Bu sürümde harici arama motoru veya embedding kullanılmaz; SQLite görünür kayıtları alır ve Python `casefold()` ile Türkçe karakter uyumlu plain-text eşleştirme yapar. Kullanıcı sorgusu SQL'e string interpolation ile eklenmez; wildcard karakterleri literal kabul edilir. Search result framework-neutral `ConversationSearchResult` olarak döner.

Sidebar filtreleri `chats`, `pinned` ve `archive` görünümlerini temsil eder. Normal görünüm arşivlenmemiş session'ları, pinned görünüm sabitlenmiş arşivlenmemiş session'ları, archive görünümü arşivlenmiş session'ları gösterir. Tarih grupları local calendar day üzerinden `Bugün`, `Dün`, `Son 7 Gün`, `Son 30 Gün` ve `Daha Eski` olarak hazırlanır. Aktif chat filtre değişiminde korunur; aktif session arşivlenirse güvenli yeni session açılır.

Search UI query'yi sidebar presentation state'inde tutar; `Ctrl+F` focus verir, `Escape` temizler. Search sonuçları plain text snippet olarak gösterilir. Image bytes, Base64, thumbnail, path, system prompt ve Memory içeriği search kapsamına girmez. Clear aksiyonu bu UX'e dahil değildir.

Gelecekte farklı local vision provider'ları aynı framework-neutral image request sınırını uygulayabilir. Region capture ve çoklu image desteği bu sürümün kapsamı dışındadır.

## Tool Katmanı

`tools` katmanı Lina'nın kontrollü şekilde çalıştırabileceği araç altyapısını tanımlar.

Bu katman:

- Tool contract.
- Tool registry.
- Tool result.
- Permission policy.
- Audit logging.

gibi konuları barındıracaktır.

## Event-Aware Mimari

Lina tamamen event-driven bir sistem olarak başlamayacaktır. Bunun yerine hibrit yaklaşım izlenecektir:

- Ana use-case akışları açık servis çağrılarıyla yürütülür.
- Modüller arası bildirimler event bus ile yapılır.
- Uzun süren veya opsiyonel yan etkiler event handler olarak çalışır.
- Automation gibi riskli işlemler command ve permission modeliyle kontrol edilir.

İlk event sistemi in-memory ve basit tutulacaktır. Harici message broker kullanılmayacaktır.

## Model Provider Yaklaşımı

Lina yalnızca Ollama'ya bağlı kalmayacaktır. Model sağlayıcıları ortak bir provider contract üzerinden desteklenecektir.

Planlanan sağlayıcılar:

- Ollama.
- LM Studio.
- OpenAI.
- Gemini.

İlk entegrasyon Ollama ile yapılacaktır; diğerleri ihtiyaç oldukça eklenecektir.

## Bağımlılık Yönü

Bağımlılık yönü içe doğru olmalıdır:

- UI, service katmanını bilir.
- Service, brain ve capability contract'larını bilir.
- Brain, provider contract'larını bilir.
- Adapter'lar contract'ları uygular.
- Core, üst seviye özellik detaylarını bilmez.

Bu yaklaşım test edilebilirliği ve sağlayıcı değiştirilebilirliğini korur.
## Lazy Conversation Creation ve Delete Lifecycle

Yeni sohbet presentation ve in-memory state içinde ephemeral draft olarak başlar. Uygulama açılışında veya `Yeni Sohbet` sonrasında boş bir conversation satırı oluşturulmaz; draft sidebar, search, pin, archive, rename ve delete akışlarına dahil edilmez.

İlk anlamlı user message geldiğinde conversation ve ilk user message aynı SQLite transaction içinde persist edilir. Transaction başarısız olursa model isteği başlatılmaz ve yarım bir conversation satırı bırakılmaz.

Son kalıcı conversation silindiğinde servis yeni boş database satırı oluşturmadan welcome draft'a döner. Başka görünür conversation varsa en yenisi yüklenir. Legacy varsayılan başlıklı ve sıfır mesajlı kayıtlar veri kaybı olmadan normal chat ve search görünümlerinde gizlenir.
## User Settings ve System Integration Foundation

Uygulama konfigürasyonu ile kullanıcı tercihleri ayrıdır. `AppSettings` ve `config/default.toml` çalışma ortamı varsayılanlarını taşırken `UserSettings` yalnız kullanıcı tarafından değiştirilebilen, güvenli ve framework-neutral tercihleri taşır. `ApplicationContext` bu nedenle genişletilmez; `ApplicationServices` user settings service'i açık bir bağımlılık olarak sağlar.

Kullanıcı ayarları proje köküne yazılmaz. `UserSettingsRepository` Windows Local AppData altındaki JSON dosyasını okur; testler injected temporary path kullanır. Save akışı UTF-8 JSON, flush, mümkünse fsync ve `os.replace` adımlarından oluşur. Bozuk veya gelecekteki schema dosyası silinmez; güvenli default değerler kullanılır.

PySide6 `SettingsDialog` JSON veya TOML okumaz. Dialog çalışma kopyasıyla çalışır; Uygula/Kaydet service üzerinden validation ve persistence yapar, Vazgeç kalıcı durumu değiştirmez, Varsayılanlara Dön yalnız formu default değerlere getirir. Settings service Qt bilmez ve subscriber callback ile runtime katmanına bildirim yapar.

Model seçimi yalnız yeni Ollama isteklerini etkiler; provider request başlangıcında model değerini snapshot olarak alır. Speech ve Vision kapatıldığında GUI kontrolleri devre dışı kalır, aktif görsel context güvenli biçimde temizlenebilir; conversation, Memory ve raw image persistence sınırları değişmez.

System tray yalnız PySide6 `QSystemTrayIcon` ile ve platform desteği varsa oluşturulur. `exit`, `tray` ve `ask` kapanış davranışları user settings üzerinden seçilir. Tray yoksa `tray` ve `start_minimized` normal pencere davranışına güvenli fallback yapar. Windows autostart ve registry yazımı bu sürümde uygulanmaz.
Model refresh ayarlar dialog'unda mevcut worker altyapısıyla asenkron çalışır. `/api/tags` yalnız kurulu modelleri listeler; sonuç settings dosyasına otomatik yazılmaz. Dialog kapanmışsa veya refresh generation güncel değilse worker sonucu UI'a uygulanmaz.

Vision model seçimi `/api/show` cevabındaki `capabilities` listesine dayanır. `vision` açıkça bulunmuyorsa yeni seçim kaydedilmez; malformed veya ulaşılamayan cevaplarda mevcut kayıtlı seçim korunur ve kullanıcı uyarılır. Text model için vision capability şartı yoktur.

## Notifications ve Background Tasks

`NotificationRepository` her işlemde kısa ömürlü bir SQLite bağlantısı açar; bağlantılar scheduler thread'i ile GUI arasında paylaşılmaz. Reminder ve notification event tabloları conversation, Memory ve image persistence katmanlarından ayrıdır. Event, presenter çağrısından önce duplicate-safe biçimde persist edilir; teslim sonucu daha sonra `delivery_status` alanına yazılır.

Framework-neutral scheduler ayarları her turda runtime provider üzerinden okur. Gerçek exit `stop()` ile thread'i birleştirir; tray'e kapanma scheduler'ı durdurmaz. Qt presenter yalnız `QSystemTrayIcon.showMessage` sınırında bulunur ve tray yoksa güvenli in-app statüsü döndürür.

Startup missed policy geçmiş daily/weekly occurrence'ları tek tek üretmez; her reminder için bir event korur ve `next_due_at` değerini gelecekteki ilk occurrence'a ilerletir. Dört veya daha fazla missed reminder tek desktop özetine çöker. `show_missed_reminders` kapalıysa eventler korunur fakat popup gösterilmez.

## Assistant Tools ve Intent Routing

`lina.brain.routing` Qt'den bağımsız typed modeller, conservative deterministic classifier, argument validation, safe registry ve pending intent koordinasyonundan oluşur. Raw dictionary yalnız `IntentRequest.extracted_arguments` içindeki sınırlandırılmış tool argümanlarıdır; GUI ve execution sonuçları typed `IntentRequest`, `RequestContext` ve `ToolResult` taşır.

Routing deterministic-first çalışır. Bu sürüm local model-assisted fallback kullanmaz; classifier'ın açıkça eşleştirmediği mesaj chat'tir. Bir model fallback gelecekte eklenirse sonucu hiçbir zaman doğrudan execution başlatmayacak, schema validation ve confirmation yine zorunlu olacaktır.

Merkezi registry yalnız `reminder.create`, `reminder.list`, `vision.screen`, `vision.region`, `vision.image`, `files.read`, `memory.store` ve `memory.recall` adlarını içerir. Persistent reminder/memory işlemleri confirmation olmadan registry callback'ine ulaşamaz; duplicate intent ID ikinci kez execute edilmez. Clarification pending state conversation key ve on dakikalık expiration ile izole edilir, restart'ta persist edilmez.

Files mevcut allowlist service'ini kullanır; traversal, absolute/UNC/drive escape ve symlink escape aynı servis sınırında reddedilir. Vision mevcut explicit capture/upload UI akışlarını kullanır ve image bytes persist etmez. Routing logları yalnız intent type/source/confidence bucket, tool success ve duration içerir; mesaj, content, full path, prompt veya image içermez.

## Tool UX ve Reliability

`ToolActivityCard` chat timeline içinde framework-neutral `ToolStatus` değerlerini Türkçe ve yalnız renge bağlı olmayan metinlerle gösterir. Confirmation kartı işlem adı, kısa açıklama, kullanıcıya gösterilebilir argümanlar, risk, Onayla ve Vazgeç kontrollerini taşır. Enter onaylar, Escape vazgeçer; tüm aksiyonların accessible name'i vardır. Kartın kendisi restart sonrası interaktif persist edilmez, fakat doğal assistant sonucu normal conversation history'ye yazılır.

Retry policy intent allowlist'ine dayanır. Reminder list, Memory recall, Files read ve Vision read-only akışları retry edilebilir. Reminder create ve Memory store aynı execution ID ile retry edilmez; yeni request ID ve yeni confirmation gerekir. Reminder create callback'i aynı aktif title/due/recurrence kaydını duplicate olarak yeniden yazmaz.

Ortak hata kategorileri validation_error, permission_denied, unavailable, timeout, cancelled, persistence_error, execution_error, stale_request ve unsupported olarak sınırlandırılmıştır. Raw exception timeline'a veya karta taşınmaz. Tool availability registry unavailable message'i ve Vision diagnostics preflight ile açıklanır.

Pending clarification/confirmation conversation key'e bağlıdır; metin cancel komutları, confirmation Vazgeç, routing disable, new chat, switch, delete, archive, expiration ve gerçek exit state'i temizler. Ayrı tool-history veritabanı yoktur. Diagnostics yalnız intent/tool/status/duration gibi içeriksiz metadata loglar.
