# Lina Yol Haritası

Bu yol haritası Lina'nın geliştirme sırasını tanımlar. Amaç, erken aşamada karmaşık özelliklere atlamadan sağlam bir temel kurmak ve her capability'yi kontrollü şekilde büyütmektir.

## Voice ve Agent Roadmap

- `v0.9.x`: tamamlandı.
- `v0.10.0-alpha`: Voice Interaction & Inference Performance Foundation tamamlandı.
- `v0.10.1-alpha`: Wake Word & Hands-Free Conversation tamamlandı.
- `v0.11.0-alpha`: Live Vision & Camera Mode tamamlandı.
- `v0.11.1-alpha`: Live Vision Reliability & Object Tracking.
- `v0.12.0-alpha`: Agent Mode Foundation.
- `v0.13.0-alpha`: Codex Bridge.

v0.11.0-alpha; opt-in kamera/ekran/bölge snapshot takibi, deterministic change detection, bounded analysis scheduling, latest-frame-wins, sesli sonuç, privacy indicator ve tray kontrollerini tamamladı. Video kaydı, frame persistence, cloud vision, yüz tanıma, autonomous agent ve Codex bridge eklenmedi.

## Mevcut Durum: v0.11.0-alpha Live Vision & Camera Mode

`v0.10.0-alpha` Voice Interaction & Inference Performance Foundation tamamlandı ve tag’lendi.

`v0.10.1-alpha` Wake Word & Hands-Free Conversation tamamlandı ve tag’lendi.

`v0.11.0-alpha` Live Vision & Camera Mode kod, test ve dokümantasyon tarafında tamamlandı. Kamera ve ekran takibi açık onay ister; raw frame yalnız bellek içinde yaşar. Yeni ağır dependency veya cloud provider eklenmedi. Sonraki hedefler:

- `v0.11.1-alpha`: Live Vision Reliability & Object Tracking.
- `v0.12.0-alpha`: Agent Mode Foundation.
- `v0.13.0-alpha`: Codex Bridge.

`v0.3.0-alpha` tag'i oluşturuldu ve GitHub'a pushlandı. Bu tag, Lina'nın ilk anlamlı alpha sürüm çizgisini temsil eder.

`v0.3.1-alpha` stabilization hotfix tag'i oluşturuldu ve GitHub'a pushlandı. Bu sürüm, `v0.3.0-alpha` sonrasında görülen küçük güvenilirlik ve konuşma kalitesi sorunlarını kapattı.

`v0.4.0-alpha` tag'i oluşturuldu ve GitHub'a pushlandı. Bu sürüm, Lina'nın ilk gerçek local-first kalıcı hafıza altyapısını ekledi.

`v0.4.1-alpha` tag'i oluşturuldu ve GitHub'a pushlandı. Bu sürüm, explicit memory komutlarının kullanıcıya daha anlaşılır cevap vermesini, hassas bilgi korumasını ve GUI input history davranışını kapsadı.

`v0.5.0-alpha` tag'i oluşturuldu ve GitHub'a pushlandı. Bu sürüm, Lina'nın yalnızca allowlist kapsamındaki proje dosyalarını read-only okuyabilmesini ve dosya içeriğini güvenli context olarak kullanabilmesini kapsadı.

`v0.5.1-alpha` tag'i oluşturuldu ve GitHub'a pushlandı. Bu sürüm, mevcut Tkinter GUI'yi daha modern bir sohbet uygulaması düzenine taşıdı; sidebar, chat bubbles, composer ve pasif placeholder action butonlarını kapsadı.

`v0.5.2-alpha` tag'i oluşturuldu ve GitHub'a pushlandı. Bu sürüm, Lina logo asset'lerini, sidebar branding alanını ve window icon fallback desteğini kapsadı.

`v0.6.0-alpha` Speech skeleton tamamlandı. `SpeechService`, STT/TTS provider sözleşmeleri, güvenli NoOp sağlayıcılar ve GUI Mic akışı eklendi. Gerçek mikrofon, STT/TTS engine veya yeni dependency eklenmedi. Gelecekteki transkripsiyon sonucu kullanıcı onayı için input alanına yazılır ve otomatik gönderilmez.

`v0.6.1-alpha` Local Push-to-Talk STT Integration tamamlandı. `sounddevice` ile sınırlandırılmış ve yalnız kullanıcı eylemiyle başlayan kayıt, `faster-whisper` ile Türkçe local transcription, lazy model loading ve GUI Mic kayıt/durdurma akışı eklendi. Ham ses kalıcı olarak saklanmaz ve transkripsiyon otomatik gönderilmez.

`v0.6.2-alpha` Professional UI, Readability & Accessibility Polish tamamlandı; manuel GUI smoke testi ve release tag'i bekleniyor. Windows DPI awareness, güvenli font fallback zinciri, semantik koyu tema, responsive sidebar/chat/composer düzeni, mesaj başına kopyalama, font boyutu kontrolleri ve composer klavye kısayolları eklendi. Brain, Memory, Files, Speech ve Ollama backend davranışları değiştirilmedi.

`v0.6.3-alpha` PySide6 Desktop UI Migration tamamlandı. `python gui.py` artık PySide6 tabanlı modern masaüstü arayüzünü başlatır. Legacy Tkinter GUI silinmedi ve geçici geri dönüş yolu olarak korunur. Migration yalnız interface katmanında tutuldu; Brain, Ollama `/api/chat`, Memory, Files, Speech ve core bootstrap davranışları korunur.

`v0.6.4-alpha` PySide6 UI Refinement & Chat Experience tamamlandı. Mesaj balonları, metadata footer, composer, action button hizaları, smart auto-scroll, sade sidebar, kompakt header/status chipleri ve alt status bar düzeni iyileştirildi. Bu sprint yalnız PySide6 presentation katmanında tutuldu; backend davranışları ve dependency listesi değiştirilmedi.

`v0.6.4-alpha` tag'i oluşturuldu ve GitHub'a pushlandı.

`v0.7.0-alpha` Screen Context Foundation tamamlandı ve release tag'i origin'e pushlandı. Kullanıcı eylemiyle başlayan Qt ekran yakalama, önizleme/onay dialog'u ve session-local attachment chip eklendi.

`v0.7.1-alpha` Local Vision Integration, `v0.7.2-alpha` Vision UX & Region Capture, `v0.8.0-alpha` Conversation Persistence Foundation ve `v0.8.1-alpha` Conversation Timeline & Welcome Experience tamamlandı ve tag'lendi. `v0.8.2-alpha` kapsamında local title/message search, pin/archive lifecycle, date-grouped sidebar ve keyboard search controls tamamlandı. Görsel bytes kalıcı olarak saklanmaz.

`v0.3.x` sonrasında tamamlanan önemli stabilization ve memory işleri:

- GUI typing placeholder silme akışı düzeltildi; `Yazıyor...` mesajı gerçek cevap gelince tamamen kaldırılır.
- GUI label duplication riskini azaltan render path regresyon testleri güçlendirildi.
- Türkçe konuşma kalitesi prompt seviyesinde iyileştirildi.
- Basit selamlaşmalar için `CASUAL_GREETING` deterministic intent eklendi.
- Bilgisayar kontrolü / future capability soruları için güvenli ve dürüst deterministic status cevabı eklendi.
- SQLite-backed `MemoryRepository` eklendi.
- `MemoryService` eklendi.
- Explicit memory intents ve deterministic memory command responses eklendi.
- Memory context, normal chat prompt akışına sınırlı ve şeffaf şekilde dahil edildi.
- Memory recall/list cevapları daha okunabilir numaralı listeye dönüştürüldü.
- Sensitive memory guard eklendi; şifre, token, API key, kimlik ve ödeme bilgisi gibi hassas içerikler saklanmaz.
- GUI input history eklendi; `↑` ve `↓` ile session içi önceki mesajlar gezilebilir.
- Read-only allowlisted `FileAccessService` eklendi.
- File list/read/summarize/capability intentleri eklendi.
- Dosya context'i prompt akışına güvenli ve sınırlı şekilde dahil edildi.
- Tkinter GUI modern sidebar, chat bubble layout ve composer düzenine taşındı.
- GUI branding alanı, Lina logo asset'leri ve window icon fallback desteği eklendi.
- SpeechService skeleton ve STT/TTS provider sözleşmeleri eklendi.
- GUI Mic butonu güvenli unavailable fallback ve test edilebilir transkripsiyon akışına bağlandı.
- PySide6 GUI shell, sidebar, chat bubbles, composer, diagnostics chip, mic flow ve regression testleri eklendi.
- PySide6 chat experience refinement ile mesaj okuma, auto-scroll, composer yoğunluğu ve sidebar sadeliği iyileştirildi.

Tamamlanan ana başlıklar:

- Proje standartları ve dokümantasyon temeli.
- Core infrastructure.
- Brain v1.
- Ollama provider entegrasyonu.
- Conversation flow.
- CLI arayüzü.
- Tkinter Desktop UI v2 (legacy fallback).
- PySide6 Desktop UI v1.
- PySide6 Chat Experience Refinement.
- Runtime conversation context.
- Memory Capability v1 (explicit local SQLite memory).
- Project awareness v2 (İzinli dokümanlar ve Git desteği).
- Safe tool foundation v2 (PermissionDecision UX yapısı).
- SAFE tool routing ile current time cevabı.

Henüz kapsam dışı olan büyük başlıklar:

- Kalıcı Memory.
- Genel dosya capability'si.
- Shell command execution.
- Gerçek STT/TTS, browser, camera, vision ve Windows automation.
- Multi-agent architecture.
- Packaging, installer ve release automation.

## v0.3.x Stabilization Gate

`v0.3.1-alpha` öncesi stabilization gate aşağıdaki durumlara göre değerlendirilir:

- GUI label duplication bug için gerçek render path testleri vardır.
- Typing placeholder gerçek cevap gelince tamamen silinir.
- `selam`, `naber`, `nasılsın` gibi basit selamlaşmalar LLM'e gitmeden deterministic cevaplanır.
- `neler yapabiliyorsun` cevabı mevcut gerçek yetenekleri ve eksikleri dürüstçe listeler.
- `bilgisayarımı yönetebilir misin` gibi bilgisayar kontrolü soruları LLM'e gitmeden güvenli ve dürüst cevaplanır.
- Ollama çalışmıyorken deterministic intent'ler çalışmaya devam eder.
- Tam test paketi geçmelidir.

Bu gate tamamlandığında küçük polish işleri ana roadmap'i durdurmamalıdır. Kullanımı engellemeyen kalite eksikleri known issue olarak takip edilir; yeni capability işleri ilgili milestone'a taşınır.

## Release Policy

Lina'da release kararları üç ayrı kategoriyle değerlendirilir.

### Release Blocker

Release blocker; uygulamayı bozan, çökerten, yanlış vaat veren, güvenlik riski oluşturan veya kullanıcının güvenini zedeleyen sorundur.

Örnekler:

- GUI'nin normal mesaj gönderme akışında cevabı bozuk göstermesi.
- Lina'nın sahip olmadığı bir yeteneği varmış gibi iddia etmesi.
- Deterministic olması gereken güvenlik cevabının LLM'e gidip yanlış vaat üretmesi.
- Test paketinin kırılması.
- Kullanıcı verisi veya bilgisayar üzerinde riskli bir işlemin izinsiz tetiklenmesi.

Release blocker kapatılmadan yeni alpha/hotfix tag oluşturulmaz.

### Known Issue

Known issue; kullanımı tamamen engellemeyen, ancak kalite, UX veya tutarlılık açısından takip edilmesi gereken eksiktir.

Örnekler:

- Bazı serbest LLM cevaplarında Türkçe üslubun hâlâ iyileştirme istemesi.
- GUI'nin görsel olarak daha profesyonel hale getirilebilecek alanları.
- Yerel model performansının kullanılan Ollama modeline göre değişmesi.

Known issue'lar release notes veya development log içinde açıkça yazılır; gizlenmez. Ancak release blocker değilse ana milestone ilerleyişini durdurmaz.

### Roadmap Feature

Roadmap feature; yeni capability veya büyük mimari geliştirmedir.

Örnekler:

- Memory UX / Recall polish.
- Files capability.
- Speech, Vision veya Windows Automation.
- Browser automation.
- Multi-agent architecture.

Roadmap feature'lar küçük hotfix sprintlerine sıkıştırılmaz. Kendi milestone kapsamı, test planı ve güvenlik değerlendirmesiyle ele alınır.

## Hedef Sürüm Hattı

Bu sürümler hedef plan olarak kabul edilir; kesin tarih içermez.

- `v0.3.1-alpha`: Stabilization hotfix.
- `v0.4.0-alpha`: Memory Capability v1.
- `v0.4.1-alpha`: Memory UX / Recall polish.
- `v0.5.0-alpha`: Files Capability v1.
- `v0.5.1-alpha`: Professional Chat UI Refresh.
- `v0.5.2-alpha`: Branding Polish.
- `v0.6.0-alpha`: Speech Skeleton + GUI Mic Flow.
- `v0.6.1-alpha`: Local Push-to-Talk STT Integration.
- `v0.6.2-alpha`: Professional UI, Readability & Accessibility Polish.
- `v0.6.3-alpha`: PySide6 Desktop UI Migration.
- `v0.6.4-alpha`: PySide6 UI Refinement & Chat Experience.
- `v0.7.0-alpha`: Screen Context Foundation.
- `v0.7.1-alpha`: Vision Provider Architecture tamamlandı.
- `v0.7.2-alpha`: Vision UX & Region Capture tamamlandı.
- `v0.8.0-alpha`: Conversation Persistence Foundation tamamlandı.
- `v0.8.1-alpha`: Conversation Timeline & Welcome Experience tamamlandı.
- `v0.8.2-alpha`: Conversation Search & Management UX tamamlandı.
- `v0.9.0-alpha`: Settings & System Integration Foundation hedefi.
- `v0.8.0-alpha`: Safe Windows Automation v1.

## Milestone 0: Proje Standartları

Amaç:

- Dil standardını netleştirmek.
- Dokümantasyonu Türkçeye çevirmek.
- Kodlama ve mimari standartları belirlemek.
- Yol haritasını yazılı hale getirmek.

Neden ilk sırada:

Proje uzun vadeli olacağı için ekip tek kişi olsa bile yazılı standartlara ihtiyaç vardır. Bu standartlar teknik borcu azaltır.

Teknolojiler:

- Markdown.
- `pyproject.toml`.
- Python 3.11+ hedefi.

## Milestone 1: Core Altyapısı

Amaç:

- Configuration loading.
- Logging setup.
- Path management.
- Application lifecycle.
- Application context.
- Temel exception yapısı.
- İlk unit test altyapısı.

Neden bu sırada:

Tüm sonraki modüller config, logging ve lifecycle altyapısına ihtiyaç duyacaktır.

Kapsam dışı:

- LLM entegrasyonu.
- Brain implementasyonu.
- Memory implementasyonu.
- Vision implementasyonu.
- Speech implementasyonu.
- Automation implementasyonu.
- Tool sistemi.
- Event bus implementasyonu.

Teknolojiler:

- Python standard library.
- `tomllib`.
- `logging`.
- `pathlib`.
- `dataclasses`.
- `pytest` geliştirme bağımlılığı.

Geliştirme notları:

- Runtime bağımlılıkları `requirements.txt` içinde tutulur.
- Geliştirme araçları `requirements-dev.txt` içinde tutulur.
- `ApplicationContext` yalnızca `settings`, `paths` ve `logger` taşır.
- Kullanılmayan soyutlama, factory, manager veya registry yapısı eklenmez.
- Her değişiklik küçük ve tek sorumluluklu commit'lerle yapılır.

## Milestone 2: Brain v1

Amaç:

- Kullanıcı mesajını işleyen temel brain orchestration katmanını kurmak.
- Prompt ve context hazırlığı için ilk contract'ları tanımlamak.
- Model provider bağımlılığını soyutlamak.

Neden bu sırada:

Lina'nın LLM sağlayıcısına doğrudan bağımlı kalmaması için brain katmanı erken tanımlanmalıdır.

Teknolojiler:

- Python Protocol.
- `dataclasses`.
- Type hints.

## Milestone 3: LLM Provider Entegrasyonu v1

Amaç:

- İlk model sağlayıcı olarak Ollama entegrasyonunu eklemek.
- Provider contract üzerinden model çağrısı yapmak.

Neden bu sırada:

Gerçek model cevabı alınmadan conversation flow doğrulanamaz.

Teknolojiler:

- Ollama HTTP API.
- Üçüncü parti HTTP client ihtiyacı ayrıca değerlendirilecektir.

## Milestone 4: Conversation Flow

Amaç:

- Kullanıcı mesajı, brain çağrısı, model cevabı ve conversation event'lerini düzenlemek.

Neden bu sırada:

Memory, speech ve GUI gibi modüller conversation flow üzerine bağlanacaktır.

Teknolojiler:

- Application services.
- In-memory event bus.
- Unit tests.

## Milestone 5: Memory Capability v1

Durum:

- Tamamlandı / `v0.4.0-alpha` tag'i oluşturuldu.
- İlk local-first SQLite repository, MemoryService, explicit memory intents, ConversationService routing ve prompt memory context entegrasyonu tamamlandı.
- Memory UX polish çalışmaları `v0.4.1-alpha` hattında sürdürülür.

Amaç:

- Konuşma geçmişi, kullanıcı tercihleri ve proje kararları için yerel öncelikli, açık ve güvenli bir hafıza temeli kurmak.

Neden bu sırada:

Asistanın kişiselleşmesi için hafıza erken ama conversation flow sonrasında eklenmelidir.

Kapsam:

- Local-first memory yaklaşımı.
- Python standard library `sqlite3` ile SQLite tabanlı yerel kalıcılık.
- Explicit conversation note kayıtları.
- Kalıcı conversation summary için temel zemin.
- User preference memory.
- Project decision memory.
- `MemoryService` ile uygulama use-case akışı.
- `MemoryRepository` ile kalıcılık sınırı.
- Explicit memory operations: Lina neyi sakladığını açıkça bilmeli ve kullanıcıya gerektiğinde söyleyebilmelidir.
- Privacy-first davranış: kullanıcı istemeden hassas bilgi saklanmamalıdır.
- Forget/delete capability için ileride genişletilebilir tasarım.

v1 komut örnekleri:

- `bunu hatırla: kısa cevapları seviyorum`
- `ne hatırlıyorsun`
- `hafızanı listele`
- `şunu unut: kısa cevapları seviyorum`
- `hafızanı sıfırla`

Kapsam dışı:

- Vector database.
- Embeddings.
- Cloud sync.
- Multi-user memory.
- Long-term autonomous monitoring.
- Sensitive personal data auto-save.
- Agent memory planning.

Teknolojiler:

- SQLite.
- Repository pattern.
- Python standard library `sqlite3`.

## Milestone 6: Tool Sistemi v1

Amaç:

- Tool contract, registry, result ve permission altyapısını kurmak.

Neden bu sırada:

Automation, files, browser ve coding capability'leri güvenli tool sistemi olmadan eklenmemelidir.

Teknolojiler:

- Python Protocol.
- `dataclasses`.
- Permission policy.

## Milestone 7: Files Capability v1

Amaç:

- Güvenli, read-only ve allowlisted dosya listeleme/okuma işlemlerini desteklemek.
- Dosya içeriğini kontrollü context olarak kullanmak.

Neden bu sırada:

Dosya yönetimi asistanın en temel pratik yeteneklerinden biridir; automation'dan önce güvenli permission modeli test edilir.

Durum:

- Uygulama aşamasında / `v0.5.0-alpha` hattında.
- `FileAccessService` yalnız allowlist kapsamındaki proje dosyalarını okur.
- Absolute path, path traversal ve allowlist dışı dosya istekleri reddedilir.
- Dosya yazma, silme, taşıma, rename veya copy yeteneği yoktur.
- LLM kendi başına dosya okuyamaz; dosya okuma deterministic `ConversationService -> FileAccessService` akışından geçer.

Teknolojiler:

- `pathlib`.
- Python standard library.
- Deterministic intent routing.
- Prompt context limitleri.

## Milestone 8: Speech Capability v1

Amaç:

- Speech-to-text ve text-to-speech için adapter altyapısını kurmak.
- GUI Mic butonunu explicit kullanıcı eylemine bağlı, güvenli ve test edilebilir bir akışa bağlamak.

Neden bu sırada:

Metin tabanlı conversation flow oturduktan sonra ses katmanı bir interface/capability olarak bağlanabilir.

Teknolojiler:

- Python standard library tabanlı `Protocol`, immutable veri modelleri ve servis orchestration.
- Runtime varsayılanı olarak cihaz erişimi yapmayan NoOp sağlayıcılar.
- Gerçek STT için `faster-whisper` ve mikrofon kaydı için `sounddevice` seçildi.
- TTS için Piper, pyttsx3 veya alternatifleri ayrı bir dependency ve güvenlik kararı gerektirir.

Durum:

- `v0.6.0-alpha` Speech Skeleton + GUI Mic Flow tamamlandı.
- `v0.6.1-alpha` Local Push-to-Talk STT Integration tamamlandı.
- `v0.6.2-alpha` Professional UI, Readability & Accessibility Polish tamamlandı; manuel GUI smoke testi ve tag bekleniyor.
- Sonraki büyük hedef `v0.7.2-alpha` Vision UX & Region Capture için kapsam ve güvenlik planlamasıdır.

## Milestone 9: Vision Capability v1

Amaç:

- Önce açık kullanıcı eylemiyle çalışan güvenli screen context temelini kurmak.
- Sonraki aşamada OCR ve görsel analiz provider sınırlarını ayrı değerlendirmek.

Neden bu sırada:

Windows automation güvenli çalışabilmek için ekran farkındalığına ihtiyaç duyacaktır.

Teknolojiler:

- Screen Context Foundation için mevcut PySide6 / Qt ekran API'leri.
- Qt'den bağımsız immutable screen context modeli ve capture contract'ı.
- OCR ve vision provider teknolojileri ayrı mimari ve dependency kararı gerektirir.

Durum:

- `v0.7.0-alpha` Screen Context Foundation tamamlandı ve tag'lendi.
- `v0.7.1-alpha` Local Vision Integration tamamlandı ve tag'lendi.
- `v0.7.2-alpha` Vision UX & Region Capture tamamlandı ve release adayıdır.

## Milestone 10: Conversation Persistence Foundation

Amaç:

- Kullanıcı sohbetlerini local-first ve gizlilik sınırlarıyla kalıcı hale getirmek.
- Session izolasyonu, sidebar yönetimi ve bounded model context sağlamak.

Durum:

- `v0.8.0-alpha` tamamlandı.
- Görsel içerik kalıcılaştırılmadı; yalnız güvenli metadata saklandı.

## Milestone 11: Automation Capability v1

Amaç:

- Windows üzerinde güvenli ve onay kontrollü otomasyon sağlamak.

Neden bu sırada:

Automation riskli bir capability olduğu için tool, permission, event ve vision altyapısından sonra gelmelidir.

Teknolojiler:

- pywinauto.
- pyautogui.
- Windows API adapter'ları.

## Milestone 11: Agents v1

Amaç:

- Planner, executor ve reviewer gibi rolleri destekleyen ilk agent mimarisini kurmak.

Neden bu sırada:

Agent yapısı ancak brain, memory ve tool sistemi olgunlaştıktan sonra anlamlıdır.

Teknolojiler:

- Hafif, proje içi agent orchestration.
- Dış framework yalnızca açık ihtiyaç oluşursa değerlendirilir.

## Milestone 12: Desktop GUI

Amaç:

- Lina için masaüstü kullanıcı arayüzü geliştirmek.

Neden bu sırada:

Önce iş mantığı ve servisler test edilebilir hale gelmelidir. GUI business logic taşımamalıdır.

Teknolojiler:

- PySide6 veya alternatif masaüstü arayüz çözümleri değerlendirilecektir.

## Milestone 13: Local API

Amaç:

- GUI, script veya diğer istemcilerin Lina ile yerel API üzerinden konuşmasını sağlamak.

Neden bu sırada:

API katmanı, temel servisler kararlı hale geldikten sonra eklenmelidir.

Teknolojiler:

- FastAPI.
- WebSocket desteği.
- Local-only güvenlik kontrolleri.

## Milestone 14: Ürünleştirme

Amaç:

- Paketleme, kurulum, yedekleme, güvenlik ve bakım süreçlerini tamamlamak.

Neden bu sırada:

Önce ürün davranışı netleşmeli, sonra dağıtım ve bakım süreçleri olgunlaştırılmalıdır.

Teknolojiler:

- PyInstaller veya Nuitka.
- Structured logging.
- Backup/export mekanizmaları.
## v0.9.0-alpha: Settings ve System Integration Foundation

Durum: Kod ve test temeli tamamlandı; manuel GUI/tray smoke testi ve release değerlendirmesi bekleniyor.

Tamamlananlar:

- Persistent local user settings, schema version ve atomik yazma.
- PySide6 settings dialog ve runtime appearance uygulaması.
- Model, Speech ve Vision tercihleri için güvenli temel.
- System tray ve kapanış davranışı foundation.

Sonraki hedefler:

- Ollama model refresh ve vision capability doğrulamalı seçim.
- Bildirimler ve background tasks için `v0.9.1-alpha` değerlendirmesi.
- `v0.9.1-alpha`: Notification Center, reminder CRUD/snooze/recurrence, tray presenter, missed policy ve scheduler lifecycle tamamlandı.
- `v0.9.2-alpha`: Assistant Tools & Intent Routing Foundation tamamlandı.
- `v0.9.3-alpha`: Tool UX, Reliability ve v0.9.x Stabilization tamamlandı.
- `v0.9.4-alpha`: Light Theme Polish & Visual Consistency tamamlandı.
- v0.9.x, v0.10.x ve `v0.11.0-alpha` tamamlandı; sonraki aktif hedef `v0.11.1-alpha` Live Vision Reliability & Object Tracking.
- Stability ve packaging foundation, voice/live vision/agent temellerinden sonra yeniden değerlendirilecek.
