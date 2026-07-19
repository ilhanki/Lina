# Lina Mimari Dokümanı

## Codex Production Hardening (v0.13.2-alpha)

Codex katmanı artık `discovery -> capability probe -> authenticated execution -> session reference -> workspace snapshot -> change review -> verification` zincirini typed sınırlarla uygular. Windows discovery, doğrudan başlatılamayan paketli WindowsApps adayının ardından launchable npm `codex.cmd` adayına ilerleyebilir. `.cmd` yalnız doğrulanmış argumentlerle `cmd.exe /d /s /c` üzerinden çağrılır; prompt her zaman stdin'dedir ve process `shell=False` kalır.

CLI yardım çıktısı root, `exec` ve `exec resume` kapsamlarında ayrı ayrı parse edilir. Resume yalnız güvenli session kimliği, aynı workspace fingerprinti, uyumlu CLI minor sürümü, güncel auth, gerçek resume/JSON/stdin capability'leri ve kullanıcı onayı birlikte sağlanırsa kurulur. Persist edilen recovery kaydı prompt veya dosya içeriği değil, sınırlı metadata'dır; restart sonrası canlı remote reference bellekte yoksa otomatik devam edilmez.

Snapshot katmanı Git metadata'sını ve bounded dosya manifestini before/after toplar. Değişiklikler typed file/hunk modeline çevrilir; binary, büyük, hassas, workspace dışı veya beklenmeyen Git işlemleri güvenli karar kapısına gider. Modification sonucu kullanıcı diff review kararı vermeden tamamlanmış sayılmaz. Reddetme otomatik rollback değildir ve hiçbir dosyayı değiştirmez; yalnız review metadata'sı üretir.

Process state machine bounded stdout/stderr, timeout, cancellation, Ctrl-Break/terminate/kill fallback ve uygulama kapanış temizliğini yönetir. JSONL parser BOM, CRLF, partial, malformed, unknown future event, usage ve session kimliğini ham içerik persist etmeden işler. Qt yüzeyi eventleri sınırlı sıklıkta taşır; runtime approval otomatik kabul edilmez ve görev `paused` durumuna geçer.

## Real Codex CLI Transport (v0.13.1-alpha)

Foundation akışı korunur ve yalnız `CodexClient` sınırının arkasına resmi CLI adapter eklenir. Bootstrap, açık ayar yolunu veya kontrollü PATH discovery sonucunu probe eder; çalıştırılabilir CLI bulunur ve version/help/status kontrolleri geçerse `CodexCliClient`, aksi halde neden kodu taşıyan `UnavailableCodexClient` seçilir.

`transports/diagnostics.py` discovery, semantic version, auth özeti ve capability snapshot üretir. `process.py` argument listesiyle `shell=False` process group çalıştırır. `prompt.py` yalnız görev için gerekli minimum contexti üretir. `cli.py` promptu stdin’den `-` ile verir. `parser.py` partial-line toleranslı JSONL’yi typed bridge eventlerine çevirir. `verification.py` secret olmayan workspace dosyalarının ephemeral SHA-256 fingerprintlerini yalnız before/after karşılaştırması için bellekte tutar.

Qt ana thread’i CLI beklemez: `FunctionWorker` bridge çağrısını yürütür, typed event Qt sinyaliyle inspector’a taşınır. Kapanış bridge’i iptal eder; runner önce process group’a kontrollü sinyal, ardından terminate ve son çare kill uygular. Credential cache, token, raw prompt, raw stderr ve model reasoning Lina persistence’ına girmez.

## Codex Bridge Foundation (v0.13.0-alpha)

`lina.codex` mevcut Agent Mode'u yeniden yazmadan onun açık approval kararlarını kullanan dar bir orkestrasyon katmanıdır. Akış `workspace grant -> typed project context -> deterministic task plan -> plan approval -> client contract -> independent verification -> Lina summary` sırasındadır. İstemci sözleşmesi shell, credential, browser automation veya gizli background agent yetkisi vermez. Ayrıntılar [codex-bridge.md](codex-bridge.md) belgesindedir.

Bu doküman Lina'nın uzun vadeli mimari yönünü tanımlar. Amaç, projeyi hızlı prototip mantığıyla değil; sürdürülebilir, test edilebilir ve modüler bir masaüstü asistan platformu olarak büyütmektir.

## Reference-Driven Premium Desktop Experience (v0.12.2-alpha)

`LinaMainWindow`, native `QMainWindow` davranışını koruyan responsive bir shell’dir. `ApplicationViewState` geniş/orta/kompakt sunumu typed olarak ayırır: genişte `SidebarWidget + conversation workspace + ContextInspector` kalıcı üç kolondur; orta ve kompakt genişlikte inspector, odak geri dönüşlü scrim üzerinde sağ drawer olur. Presentation state backend controller durumunun yerine geçmez.

`ContextInspector` yalnız gerçek sinyalleri sunar. Chat composer’a, Voice mevcut speech/voice durumuna, Vision mevcut controller’a, File açık dosya eylemine, Agent typed görev inspector’ına, Memory gerçek `MemoryService` repository’sine bağlıdır. Hassas bellek özetleri filtrelenir. `LocalStorageService` yalnız onaylı local data/cache klasörlerini GUI thread’i dışında, bounded ve cache’li ölçer; fake kota, hesap veya Pro verisi üretmez.

Design System V3 typed semantic surface/state token’larını, 16/18/20/24 px cache’li çizgi ikonlarını ve genişlik sınırlarını tek kaynakta toplar. Conversation repository son güvenli metni sidebar preview projection’ına ekler. Assistant rich text katmanı model HTML’ini önce escape edip yalnız başlık, liste, vurgu ve code subset’ini render eder. Response Quality V3 kabul öncesi çalışır; en fazla bir düşük-temperature, non-streaming Repair V3 denemesi vardır.

Settings schema v10 sidebar, right panel, panel bölümü/genişliği, mesaj genişliği ve son settings bölümünü migrate ederek kalıcı tutar. Pencere geometry clamp, tray, shutdown, Agent, Voice, Vision ve conversation servis sözleşmeleri korunur. Offscreen 18 yüzeylik QA matrisi geçici dosyalarla çalışır; release çıktısına screenshot eklemez.

## Product Experience Redesign (v0.12.0-alpha tag öncesi)

Qt katmanı dört yüzeye ayrılır: daraltılabilir sol navigasyon, merkez conversation workspace, varsayılan kapalı sağ DetailsInspector ve modal/overlay katmanı. LinaMainWindow signal/slot orkestrasyonunu korur; conversation, Agent, Voice, Vision, notification ve settings iş mantığı widget’lara taşınmaz. Kapalı Agent ve Vision yüzeyleri layout alanı tüketmez.

lina.ui.design typed renk, spacing, radius, typography, control, layout ve motion token’larını sunar. QSS bu token’lardan üretilir; dark/light/system palette seçimi tek kaynaktan yapılır. Qt standard pixmap’leri theme-aware icon katmanında toplanır. Rastgele widget rengi, emoji tabanlı ana kontrol ve markalı asset kullanılmaz.

Timeline merkezde 760–920 px okunabilir kolon kullanır. Assistant cevabı açık metin yüzeyi, user mesajı kompakt accent yüzeyi olarak render edilir. Kopyala/yeniden dene/seslendir eylemleri progresif gösterilir. Empty state önerileri persistence oluşturmadan composer’ı doldurur. Composer input, geçici bağlam ve Ekle/Mikrofon/Ekran/Agent/Gönder eylemlerini tek alt kolonda toplar.

CommandPalette mevcut eylemleri klavye odaklı filtreler; unavailable action’ı açıkça işaretler. Inspector sistem, Agent ve Vision teknik ayrıntılarını ana sohbetten ayırır. Unified status generation önceliğiyle stale callback’leri reddeder. Responsive eşikte sidebar ikon moduna geçer, header ikonlaşır, composer sıkışır ve inspector kapanır.

Settings schema v8; görünüm yoğunluğu ve güvenli pencere geometry persistence’ı ekler. Kayıtlı geometry negatif monitor origin’lerini destekler, ekrandan taşmış pencereyi görünür alana clamp eder. Ayarlar 11 aranabilir bölüme ayrılır; privacy sayfası local-only veri davranışını açıklar.

Response Quality V2, yabancı phrase ve Türkçe ek almış yabancı stem sızıntısını kabul öncesi yakalar. Repair bağlamı stale/cancel kontrolünden geçer; geçersiz draft history, persistence veya TTS’ye ulaşmaz. Kamera capture, inference ve lifecycle iş mantığı bu yeniden tasarımda değiştirilmemiştir.

## Agent Reliability, Task Templates & Recovery (v0.12.1-alpha)

`lina.agent.templates` framework bağımsız bir `TaskTemplate` sözleşmesi, registry, conservative matcher, typed parametre normalizasyonu ve preflight renderer sağlar. Şablonlar yalnız `AgentPolicy.capability_snapshot()` içinde gerçekten available görünen araçlarla listelenir. Doğal dil eşlemesi explanation sorularını ve düşük güvenli sonuçları normal sohbette bırakır; explicit şablon seçimi capability filtresini atlayamaz.

Yerleşik katalog; hatırlatıcı oluşturma, tarih aralıklı hatırlatıcı özeti, deterministik aynı-zaman çakışma kontrolü, Memory store/recall, allowlist dosya okuma ve explicit tek-kare Vision akışlarıyla sınırlıdır. `system.status` ve `conversation.search` registry capability’si olmadığı için şablon olarak sunulmaz. Şablon factory’si yalnız typed `AgentPlan` üretir; tool çalıştırmaz.

`AgentPlanEditor`, tool schema, dependency graph ve risk politikasını yeniden doğrulayarak sıralama, optional kaldırma/atlama ve typed argüman değişikliğini uygular. Persistent risk read-only’ye düşürülemez; tamamlanmış adımlar regenerate sırasında korunur. Eski/yeni plan farkı eklenen, kaldırılan, taşınan ve değişen adımları kullanıcı onayından önce gösterir. `AgentPlanQualityValidator` belirsiz açıklama, duplicate operation, gereksiz persistent adım ve dependency sorunlarını tek bounded repair sınırı içinde yakalar.

Yürütme öncesi capability availability yeniden kontrol edilir. Hatalar sabit `AgentErrorCode` taxonomy’sine normalize edilir. Yalnız read-only `timeout` ve `transient_failure` en fazla bir kez retry alır; persistent/sensitive adımlar ve `uncertain` sonuçlar otomatik tekrarlanmaz. Normalize operation hash, session+step idempotency key, replay guard ve duplicate read-before-write denetimi çift kalıcı işlem riskini sınırlar. Loop detector tekrarlanan tool+argüman, açıklama ve ilerlemesiz replan döngülerini durdurur.

Her session bounded user-visible event ve step checkpoint geçmişi üretir. Repository yalnız güvenli başlık, durum, risk, sayaç, teknik kod ve kısa sabit özetleri saklar; raw istek, typed argüman, tool payload, dosya/Memory/reminder içeriği veya model reasoning saklanmaz. Başlangıçta yarım durumlar bir kez `interrupted` olarak persist edilir ve hiçbir tool otomatik sürdürülmez. Geçmişten yeniden başlatma ham parametre gerektiriyorsa kullanıcı şablonu yeniden açıp doğrular; canlı terminal görev safe clone ile yeni session/generation kimliği ve yeni plan onayı alır.

Task Center V2 aktif, onay bekleyen, duraklatılmış, yarım, tamamlanan, başarısız ve iptal edilen projection’ları repository metadata’sından üretir. Settings schema v9; şablon önerisi, başlangıç recovery bildirimi ve 7/30/90 gün veya sınırsız Agent geçmiş saklama tercihlerini ekler. Temizlik interrupted/active metadata’yı korur ve yalnız terminal geçmişi siler; tool-created veri bu işlemden etkilenmez.

Agent metinleri modelden bağımsız kısa Türkçe kalite kapısından geçer. Voice event kimliği session içinde deduplicate edilir; TTS durdurma veya barge-in Agent session’ını iptal etmez. Tray bildirimi yalnız genel görev başlığı/durumu taşır ve aynı olay ikinci kez gösterilmez.

## Agent Mode Foundation (v0.12.0-alpha)

### Tag öncesi interaction quality ve voice stabilization

`lina.quality` GUI’den bağımsız ortak kabul kapısıdır. Unicode normalize edilmiş model cevabında dil karışması, belirgin bozuk token/persona, ilgisiz giriş, yarım cevap ve cümle/paragraf/n-gram tekrarını deterministic ölçer. Geçersiz taslak history veya kalıcı mesaj olmaz; yalnız kullanıcı sorusu ve bounded taslakla, düşük sıcaklıkta tek repair yapılır. İkinci başarısızlık güvenli kısa fallback üretir. Context builder exact duplicate, tool/internal içerik, Base64 ve ham Agent planını çıkarır; stream parser cumulative ve duplicate chunk’ları bastırır.

Mikrofon hattı bellekte DC-offset düzeltme, bounded gain, clipping koruması, pre-roll ve adaptive noise floor uygular. STT çıktısı Unicode/whitespace/noise-marker açısından normalize edilir ve iki saniyelik duplicate pencereyle korunur. Kalibrasyon ilk iki saniyeyi ortam, kalan bölümü konuşma olarak yalnız bellekte ölçer; ham audio yazılmaz. Wake detector phrase normalization ve cooldown kullanır; ayarlardaki test modu normal command listener’larını çalıştırmaz.

Her TTS isteği source, session/generation, priority ve cancellable metadata’sı taşır. Aynı source+generation+metin ikinci kez okunmaz; stop eski playback callback’ini stale yapar. Agent approval ve completion sesleri normal chat voice tercihinden bağımsız açılabilir. `UnifiedStatusController` generation kontrolüyle eski callback’in yeni durumu geri çevirmesini önler.

Agent katmanı `lina.agent` altında framework bağımsızdır. `AgentController` tek aktif session kuralını, lifecycle geçişlerini, plan ve step onaylarını, pause/resume/cancel, bounded retry/replan, completion ve shutdown cleanup’ı koordine eder. `AgentSession`, `AgentPlan`, `AgentStep`, status/risk/verification enum’ları ve metrics typed modellerdir; raw planner dict’i veya tool payload’ı GUI’ye taşınmaz.

`AgentPlanner`, yalnızca sanitized `CapabilitySnapshot` ve bounded `AgentContext` görür. Snapshot araç adı, kısa açıklama, argüman türleri, sonuç türü, availability, risk ve approval bilgisinden oluşur; callback, servis nesnesi, secret, environment, dosya içeriği veya tam log içermez. Serbest planner çıktısı schema parse edilir; ilk hata sonrası yalnızca bir repair denenir. Duplicate tool+arguments, geçersiz dependency, cycle ve 12 üstü step güvenli plan hatasıdır.

`AgentPolicy`, registry’den bağımsız ikinci allowlist katmanıdır. Read-only araçlar görünür plan onayından sonra yürüyebilir. Persistent ve sensitive adımlar her defasında bağlama özel step approval ister; bu ayar kapatılamaz. Shell/CMD/PowerShell, process/code execution, browser, email/message, git, mouse/keyboard, dosya yazma/silme/taşıma ve gizli cihaz başlatma prohibited’dır. Bilinmeyen araç varsayılan olarak prohibited kabul edilir.

`AgentExecutor`, aracı yalnızca `SafeToolRegistry.get_by_name` üzerinden bulur; unknown argümanı reddeder, required alan ve Python türlerini doğrular, timeout/cancel uygular, raw exception’ı sabit hata koduna normalize eder ve aynı step’in duplicate execution’ını engeller. `AgentVerifier`, typed success+data, object ID, beklenen alan veya deterministic non-empty kuralları kullanır. Modelin başarı cümlesi tek başına kanıt değildir; uncertain persistent sonuç otomatik tekrarlanmaz.

Read-only/idempotent adım en fazla bir otomatik retry alır. Replan varsayılan ve hard maksimum 1’dir; yalnız failed step kimliği, typed hata kodu, tamamlanan kısa özetler ve capability snapshot kullanılır. Tamamlanan adımlar korunur; aynı persistent signature yeni planda yinelenemez. Yeni persistent risk planı yeniden kullanıcı onayına döndürür.

Session persistence yalnız metadata, bounded request özeti, plan/step başlığı, tool adı, risk, status, kısa sonuç, timestamp ve privacy-safe sayaçları JSON olarak saklar. Typed arguments, raw tool data, prompt/reasoning, exception, dosya/görüntü/ses/Base64 saklanmaz. Uygulama yeniden açıldığında running/planning/approval durumları `interrupted` olur ve otomatik devam etmez.

Qt `AgentPanel`, plan özeti, ilerleme, metin+ikon durumları, risk ve kontrollere typed session üzerinden bağlanır. Tray aktif görev yokken pause/cancel eylemlerini kapatır. Explicit agent intent’leri normal sohbet açıklamalarından ayrılır; hands-free komutları aynı GUI dispatch yolunu kullanır ve TTS playback agent komutu sayılmaz. Shutdown cancellation token’ı işaretler, generation’ı geçersiz kılar ve worker pool’u temizler.

Bilinen sınır: ilk sürüm deterministic planner’ı yalnız açıkça eşlenebilen mevcut araçlarla çalışır; genel amaçlı masaüstü otomasyonu, shell, browser, dosya değişikliği, gizli background devam ve Codex Bridge yoktur. Manual realtime camera validation deferred; kamera altyapısı bu sprintte değiştirilmemiştir.

## Realtime Camera Conversation (v0.11.2-alpha)

Empty vision response reliability provider sınırında çözülür. Ollama adapter’ı `message.content`, attribute tabanlı `message.content`, legacy `response` alanı ve tüm stream chunk’larını typed bir normalize sonucuna dönüştürür. `None`, whitespace, yalnız noktalama, thinking-only ve `null`/`none` gibi anlamsız literal sonuçlar boş kabul edilir; raw provider modeli UI’ya taşınmaz.

Vision provider kamera ve tek-görsel isteklerinde `stream=false` kullanır. İlk normalize sonuç boşsa aynı doğrulanmış ephemeral frame yalnız bir kez, kısa sabit prompt, `temperature=0` ve `stream=false` ile yeniden istenir. İkinci sonuç da boşsa otomatik yorum hata balonu üretmeden `empty_response_count` metriğini artırır ve izlemeyi sürdürür; doğrudan kullanıcı sorusu “Görüntüyü şu anda yorumlayamadım. Birkaç saniye sonra tekrar deneyelim.” mesajına döner. Stop/cancel aktif non-stream response handle’ını kapatır; retry backlog veya stale sonuç oluşturmaz.

Response diagnostics yalnız format türü, content alanı varlığı, content uzunluğu, chunk sayısı, retry kullanımı, model adı, süre ve boş cevap sayısını loglar. Prompt, kullanıcı sorusu, frame bytes, Base64, raw response ve görüntü içeriği loglanmaz.

Kamera preview’ü varsayılan yatay aynalıdır; bu dönüşüm yalnız `CameraPreviewCanvas` üzerinde uygulanır. Vision inference orijinal frame yönünü korur ve normalized değişiklik kutularının x koordinatı preview aynalıysa `1 - x - width` olarak çizilir. Screen ve region kaynakları bu dönüşüme girmez.

`LiveVisionController` tek kamera session’ında yalnız son geçerli frame referansını, son semantik özeti, son seslendirmeyi, analiz zamanını ve son kullanıcı sorusunu taşır. Frame history, video, Base64 archive, disk image ve conversation DB image kaydı yoktur; yeni kare eskisinin yerini alır ve stop/shutdown referansı temizler. Kamera açıkken normal chat veya hands-free sorusu yeni ephemeral capture ile mevcut image-attachment inference yoluna girer, cevap aynı session’ın TTS hattından okunur.

Change detector her capture’da ucuz luminance farkını çalıştırır; vision her karede çalışmaz. Kamera varsayılan minimum analiz aralığı 3 saniyedir, tek aktif inference ve en fazla bir pending latest frame korunur. Model yavaşsa UI `Kamerayı izliyorum`, `Görüntüyü analiz ediyorum`, `Seni dinliyorum` veya `Cevap veriyorum` durumunu gösterir; sahte gerçek zaman vaadi verilmez. GTX 1650/4 GB VRAM gecikmesi model ve sahneye bağlıdır.

Semantik prompt yalnız açık görülen yeni eylem veya nesneyi tek kısa Türkçe cümleyle ister, önceki özeti tekrar bağlamı olarak verir ve kimlik, yüz, duygu, sağlık, etnik köken veya biyometrik çıkarımı yasaklar. Normalize metin benzerliği aynı/çok yakın özeti varsayılan 10 saniyelik cooldown içinde bastırır; farklı yeni olay beklemeden konuşabilir. Beyaz change box’lar hâlâ yalnız piksel değişikliği bölgeleridir, semantik nesne kutuları değildir.

Live Vision seslendirmesi kullanıcıdaki `Speak semantic changes` tercihine bağlıdır ve normal chat voice-response anahtarından ayrıdır. Hands-free açıkken mevcut wake phrase, barge-in, playback generation ve stale callback korumaları kullanılır; Lina’nın kendi TTS’si doğrudan yeni komut sayılmaz. Vision analizi hata verirse kamera preview’ü açık kalır ve monitoring devam eder; kullanıcı sorusu yeni capture ile arka plan yorumundan öncelikli ayrı conversation isteği oluşturur.

## Live Preview & Monitoring Overlays (v0.11.1-alpha)

Kamera preview hattı inference scheduling’den ayrıdır. `QVideoSink.videoFrameChanged`, `QVideoFrame.toImage()` ile en yeni QImage’ı doğrudan `CameraPreviewWindow` içindeki canvas’a taşır. Preview kareleri JPEG/Base64 olarak yeniden encode edilmez, diske veya conversation DB’ye yazılmaz ve queue oluşturulmaz. Vision analizi v0.11.0’daki 2 saniyelik capture, 5 saniyelik minimum analysis ve latest-frame-wins politikasını aynen kullanır.

Framework-neutral controller dört typed event hattı sağlar: `PreviewFrameEvent`, `ChangeRegionsEvent`, `OverlayGeometryEvent` ve `SessionStoppedEvent`. Tüm eventler session ve generation kimliği taşır. Qt katmanı yalnız aktif session ID ile eşleşen frame ve region’ları uygular; source switch veya stop sonrasında geç gelen preview callback’leri yok sayılır.

`FrameChangeDetector`, 16×16 luminance signature’daki eşik üstü blokları dört yönlü komşulukla birleştirir. Tek blokluk noise elenir, en büyük beş bölge normalized koordinatlarla UI’ya gider ve 2,5 saniye içinde yenilenmezse silinir. Kamera canvas’ındaki `Değişiklik` kutuları semantik object detection değildir: yalnız hareket, yeni beliren, kaybolan veya görsel olarak değişen bölgeleri gösterir. Telefon/insan/bardak gibi nesne sınıfı iddiası yapılmaz.

Full-screen ve region monitoring, `MonitoringBorderOverlay` olmadan başlamaz. Overlay frameless, always-on-top, `Qt.Tool`, `WindowTransparentForInput`, translucent ve mouse-transparent’tır; keyboard focus veya taskbar entry almaz. Beyaz 3 px border ve metinsel privacy etiketi yalnız renge bağlı olmayan aktif monitoring göstergesi sağlar. Pause’da opacity düşer ve border kesikli olur; resume’da normale döner. QTimer ekran geometry’sini takip eder ve DPI/monitor değişiminde çerçeveyi günceller. Region koordinatı seçilen ekranın güncel global origin’ine göre yeniden hesaplanır; artık sığmayan region güvenli capture hatasıyla session’ı kapatır.

Preview penceresini kapatmak yalnız preview’ü gizler; ana panel ve tray kamera monitoring göstergesini korur. Panelde `Preview’i Göster` ile aynı singleton pencere yeniden açılır. Mandatory screen border beklenmedik biçimde kapanırsa monitoring de durur. Stop, source switch, permission/device error, Vision disable ve gerçek application exit; preview image/box referanslarını, QTimer’ları, border window’u, QVideoSink listener’larını, pending frame’i ve camera handle’ını temizler.

Gerçek semantic object detection bu sürümde yoktur. ONNX/YOLO, model boyutu, yeni dependency, GTX 1650 latency/VRAM maliyeti ve privacy etkisi `v0.11.3-alpha` çalışmasında ayrıca değerlendirilmelidir.

## Live Vision & Camera Mode (v0.11.0-alpha)

Live Vision çekirdeği `lina.vision.live` altında Qt’den bağımsızdır. `LiveVisionController`, typed `LiveVisionSession` ve `LiveVisionSnapshot` modelleriyle start/stop, pause/resume, manuel analiz, süre sınırı, metrics ve stale-result generation kontrolünü yönetir. `FrameSource` protokolünün kamera, ekran ve bölge implementasyonları yalnız tek ephemeral encoded frame döndürür; raw dict UI’ya taşınmaz.

Kamera adaptörü mevcut PySide6 Qt Multimedia `QMediaDevices`, `QCamera`, `QMediaCaptureSession`, `QVideoSink` ve `QVideoFrame` API’lerini kullanır. OpenCV veya yeni image-processing dependency yoktur. En son `QImage` memory’de tutulur, istek anında PNG’ye memory içinde encode edilir ve stop/shutdown sırasında kamera handle’ı ile frame referansı bırakılır. Ekran ve bölge kaynakları mevcut `QtScreenCaptureService` üzerinden çalışır; `QtCaptureInvoker` QScreen çağrılarını GUI thread’ine taşır. Region ekran geometrisi değişirse session güvenli hata verir.

`FrameChangeDetector` görüntüyü 16×16 luminance signature’a küçültür ve düşük/orta/yüksek sensitivity eşiğiyle deterministik ortalama fark hesaplar. İlk frame baseline’dır; aynı veya küçük değişiklik vision isteği üretmez. Varsayılan capture aralığı 2 saniye, minimum analiz aralığı 5 saniye ve takip süresi 5 dakikadır; 1/5/15 dakika ya da açıkça kullanıcı durdurana kadar seçilebilir. Gerçek zamanlı video anlayışı veya her kareyi modele gönderme yoktur.

Controller aynı anda yalnız bir vision inference çalıştırır. Analiz sürerken en fazla son anlamlı frame referansı tutulur; yenisi geldiğinde eskisi drop edilir. Bu latest-frame-wins politikası backlog ve büyüyen raw frame queue oluşmasını engeller. Stop/source switch/exit generation’ı artırır, pending frame’i temizler, provider cancel çağırır ve geç dönen sonucu yok sayar. Text analizi öncesi vision unload, vision analizi öncesi text unload ve inference sonrası kısa `keep_alive=0` mevcut `ModelLifecycleService` ile korunur.

Prompt’lar source türüne göre sabittir. Kullanıcı focus metni 500 karakterle sınırlanır, role etiketi temizlenir ve system safety kurallarının yerine geçmez. Kamera prompt’u kişi kimliği veya biyometrik çıkarımı açıkça yasaklar. UI sonucu sohbet veritabanına otomatik yazmaz: session application-level sürer, conversation değişse de sonuç yalnız Live Vision panelinde kalır. Böylece yanlış conversation’a result yazma riski yoktur.

Kamera/ekran başlangıcı explicit confirmation ister. Ana panel ve tray kaynak adı, aktif/pause durumu ve stop action gösterir; yalnız renge dayanmaz. Ayarlar capture/analysis aralığı, sensitivity, cihaz/ekran ve voice feedback tercihlerini schema v4 ile taşır. Log ve metrics yalnız frame sayısı, drop/change/request sayısı, süre ve source tipidir; frame bytes, Base64, focus, prompt ve tam model cevabı loglanmaz.

Bilinen sınırlar: camera preview, neural object tracking, OCR pipeline, face recognition, video recording ve cloud stream yoktur. Kamera izni, fiziksel cihaz, çoklu ekran/DPI ve gerçek Ollama/4 GB VRAM davranışı Windows üzerinde manuel smoke test gerektirir.

## Wake Word & Hands-Free Conversation (v0.10.1-alpha)

Hands-free lifecycle `lina.voice` içinde framework-neutral tutulur. `WakeWordDetector` protokolü `start`, `stop`, `is_available`, `is_running`, `set_phrase` ve `shutdown` sözleşmelerini tanımlar. Runtime implementasyonu yeni bir keyword modeli indirmez: `SoundDeviceWakeAudioSource` düşük maliyetli peak-energy VAD ile bounded PCM segmentleri üretir, `STTWakeWordDetector` yalnız geçerli segmentlerde mevcut local faster-whisper provider’ını çağırır. Sessizlik ve minimum sürenin altındaki gürültü full STT’ye gitmez.

Wake phrase Unicode NFKC, casing, whitespace ve punctuation açısından normalize edilir. Varsayılan phrase için yalnız `hey lina`, `he lina` ve punctuation varyasyonu kabul edilir; fuzzy eşleşme yoktur. Detector veya input device kullanılamıyorsa UI özelliği unavailable gösterir ve normal chat etkilenmez.

Typed hands-free state akışı:

```text
idle
→ wake_listening
→ wake_detected
→ command_listening
→ transcribing
→ thinking
→ speaking
→ cooldown
→ wake_listening
```

`VoiceStateMachine` invalid transition’ı exception ile GUI’ye taşımak yerine reddeder. `HandsFreeConversationService` wake callback’inden sonra ayrı bounded command session başlatır; wake phrase audio’su komut kaydına dahil edilmez. Transcription başarıyla tamamlanırsa aynı GUI send path’i kullanılır, dolayısıyla normal intent routing, reminder/memory confirmation, conversation isolation ve stale request korumaları değişmez.

VAD ayarları internal’dır: noise threshold, yaklaşık 1 saniye trailing silence, 250 ms minimum konuşma, 5 saniye no-speech timeout ve bounded maximum recording. PCM yalnız bellekte tutulur; kabul edilmeyen buffer temizlenir. Audio, transcription text’i ve raw exception loglanmaz. Metrics yalnız wake count, false-wake cancel count, command/transcription duration ve end-to-end latency metadata’sı taşır.

Kalıcı işlem confirmation’ında soru normal final-response TTS yoluyla okunur. Hands-free açık ve voice confirmation etkinse playback sonrası cooldown’ın ardından doğrudan kısa command capture başlar. Onay/iptal kelimeleri exact allowlist ile sınırlıdır; ambiguous cevap işlemi çalıştırmaz. Confirmation 25 saniyede güvenli biçimde iptal edilir.

Barge-in politikası hands-free sırasında wake phrase zorunlu olacak şekilde sabittir. TTS devam ederken enerji kapılı detector çalışabilir, ancak yalnız exact wake phrase playback’i keser; kısa gürültü kesmez. Stop generation kimliğini artırdığı için eski playback callback’i stale olur. Playback bittiğinde detector durdurulur, 1.5 saniye cooldown uygulanır ve sonra wake listening yeniden başlar. Özel acoustic echo cancellation bulunmadığından keyword accuracy mikrofon/oda akustiğine bağlıdır.

Input devices `AudioInputDeviceService` ile listelenir. Seçili cihaz kaybolursa privacy-safe log üretilir ve varsayılan input’a fallback yapılır. Refresh ve test işlemleri Qt worker üzerinde çalışır. Gerçek exit sırası hands-free cancel/join, recorder stop, wake detector shutdown, TTS stop, inference cancel, scheduler stop ve tray cleanup’tır. Tray’e kapanma gerçek exit değildir; kullanıcı tercihi açıksa wake listening sürdürülebilir.

Hands-free ve wake-word varsayılan kapalıdır. İlk etkinleştirmede açık privacy confirmation gerekir. Cloud speech/wake servisi, audio persistence, custom voice, camera, shell veya automation yetkisi eklenmez.

## Voice Interaction & Inference Performance Foundation (v0.10.0-alpha)

`lina.voice` GUI’den bağımsız typed katmandır. `VoiceController` idle, listening, transcribing, thinking, speaking, interrupted, error ve disabled durumlarını yönetir. `AudioPlaybackService` generation kimliğiyle tek aktif playback sağlar; stop eski callback’i geçersiz kılar. Mic speaking sırasında başlatılırsa barge-in önce playback’i keser, sonra listening’e geçer.

`QtWindowsTTSProvider` mevcut PySide6 içindeki Windows WinRT motorunu yeni paket veya shell çalıştırmadan kullanır ve Türkçe WinRT sesini önceliklendirir. Motor GUI thread’inde kalıcı bir bridge tarafından gerçek `Speaking → Ready` yaşam döngüsü tamamlanana kadar tutulur; bu nedenle worker tamamlanması playback tamamlanması gibi yorumlanmaz. PySide6 WinRT binding’i sentezlenen byte stream’i dışarı açmadığından ses Qt tarafından doğrudan varsayılan output device’a verilir ve geçici ya da kalıcı audio dosyası oluşturulmaz. SAPI/System.Speech voice listesi WinRT listesine karıştırılmaz; yalnız SAPI tarafında bulunan sesler UI’da gösterilmez. Opsiyonel COM tabanlı `WindowsSapiTTSProvider` ayrı abstraction olarak korunur ancak runtime WinRT provider’a voice enjekte etmez. WinRT motoru bulunmazsa provider unavailable olur; timeline’daki yazılı cevap normal çalışır. TTS öncesi kod blokları, uzun URL, JSON/trace/Base64 benzeri içerik çıkarılır ve yalnız ses kopyası sınırlandırılır. Chat/Ollama olmadan gerçek Windows hattı `python scripts/tts_smoke.py` ile doğrulanabilir.

v0.10.0’da yalnız foundation olarak bulunan `WakeWordDetector`, v0.10.1’de enerji kapılı local STT implementasyonuna bağlanmıştır. Detector olmadan ayar disable edilir; sahte detection veya cloud fallback yoktur.

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
