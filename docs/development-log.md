# Lina Geliştirme Günlüğü

Bu dosya önemli geliştirme kararlarını ve milestone ilerlemesini kısa notlar halinde takip etmek için kullanılır.

## 2026-07-15 - Empty Vision Response Reliability Fix

- Ollama vision yanıtları dict/attribute `message.content`, legacy `response` ve stream chunk biçimlerinden typed olarak normalize edildi.
- Whitespace, `None`, yalnız noktalama, thinking-only, anlamsız literal ve malformed sonuçlar güvenli empty response olarak sınıflandırıldı.
- Vision provider basit görüntü isteklerinde non-stream çalışacak biçimde ayrıldı; ilk boş sonuç aynı frame ile tek deterministic retry alır.
- Otomatik kamera yorumu ikinci boş sonucu sessizce atlayıp metric artırır; doğrudan kamera sorusu kullanıcı dostu fallback verir.
- Live camera soru prompt’u geçmişsiz ve 240 karakterle sınırlı kısa vision sorusuna indirildi; safety system prompt’ta kalır.
- Capability ve PNG/image payload kontrolleri korundu; unsupported model mesajı eyleme dönük hale getirildi.
- Diagnostics yalnız format/süre/sayaç metadata’sı taşır; prompt, soru, raw response, image veya Base64 loglanmaz.

## 2026-07-14 - Realtime Camera Conversation

- Kamera preview’ü ayarlanabilir yatay ayna ve doğru yansıtılmış change-box koordinatlarıyla güncellendi; inference frame’i orijinal yönde kaldı.
- Tek kamera session’ında son geçerli kare, son semantik/sesli özet, analiz zamanı ve son kullanıcı sorusu tutuldu; stop’ta frame referansı bırakıldı.
- Yaklaşık 3 saniyelik minimum kamera analizi, tek inference, tek pending latest-frame-wins ve 10 saniyelik benzer yorum cooldown’ı eklendi.
- “Ne görüyorsun?”, “Elimde ne var?” ve “Bu ne renk?” soruları güncel ephemeral kareyle yerel vision akışına bağlandı.
- Live Vision TTS, semantik seslendirme tercihine bağlandı; hands-free barge-in, stale playback ve echo korumaları mevcut tek playback hattını kullanmaya devam etti.
- Camera vision hatası preview’ü kapatmadan güvenli metinle monitoring’e döner; STT/TTS hataları yazılı ve görsel akışı korur.
- Settings schema v5 migration eski değerleri koruyarak konuşmalı kamera, otomatik yorum, mirror, seslendirme, cooldown ve analiz aralığı tercihlerini ekledi.
- YOLO, ONNX Runtime, OpenCV, yüz/kimlik/duygu çıkarımı, cloud speech/vision, video kaydı ve frame persistence eklenmedi.

## 2026-07-13 - Voice Interaction & Inference Performance Foundation

- Framework-neutral voice state machine, single-playback service, barge-in ve shutdown cleanup eklendi.
- Opsiyonel Windows SAPI TTS, Turkish voice tercihi, unavailable fallback ve güvenli spoken-text normalizasyonu eklendi.
- Push-to-talk için insert/send davranışı, speaking/stop indicator ve tray “Sesi Durdur” aksiyonu eklendi.
- Wake-word protokolü hazırlandı; detector ve always-on mic eklenmedi, ayar varsayılan kapalı ve unavailable durumda disabled.
- Ollama streaming, privacy-safe inference metrics, async benchmark, keep-alive/max-output/context ayarları ve warm-up eklendi.
- Text/vision best-effort unload lifecycle ve deterministik pair-preserving context trimming eklendi.
- Settings schema v2 migration eski değerleri koruyacak biçimde eklendi.
- Yeni dependency, cloud audio, raw audio/image persistence, live camera veya Codex bridge eklenmedi.

## 2026-07-05

- Proje klasör yapısı oluşturuldu.
- Dokümantasyon dilinin Türkçe, kod tabanının İngilizce olması kararlaştırıldı.
- `Brain` katmanı fikri mimari olarak değerlendirildi.
- Capability tabanlı büyüme yaklaşımı benimsendi.
- Event-aware hibrit mimari yaklaşımı değerlendirildi.
- Milestone 0 kapsamında proje standartlarının yazılı hale getirilmesine başlandı.
- Milestone 0 tamamlanmış kabul edildi.
- Mevcut klasör yapısının şimdilik dondurulmasına ve `brain` / `capabilities` refactor kararının YAGNI gereği ertelenmesine karar verildi.
- Milestone 1 kapsamı yalnızca core altyapısı olarak belirlendi.
- Runtime bağımlılıkları için `requirements.txt`, geliştirme araçları için `requirements-dev.txt` ayrımı kabul edildi.
- `ApplicationContext` kapsamı `settings`, `paths` ve `logger` ile sınırlandırıldı.
- Her commit'in tek sorumluluk taşıması kararlaştırıldı.

### Day 1 Özeti

Milestone 1 - Core Infrastructure tamamlandı.

Bugün Lina'nın temel core altyapısı oluşturuldu. Her geliştirme küçük ve tek sorumluluklu commit'ler halinde yapıldı. Kod ile birlikte ilgili unit testler yazıldı ve tüm ilgili testler başarıyla geçti.

Tamamlanan commit'ler:

- `feat: add core exception types`
- `feat: add application paths`
- `feat: add settings loader`
- `feat: add logging setup`
- `feat: add application context`
- `feat: add application lifecycle`

Milestone 1 kapsamında tamamlanan başlıklar:

- Temel exception yapısı.
- Application path yönetimi.
- Settings loader.
- Logging setup.
- Application context.
- Application lifecycle.
- İlgili unit test altyapısı.

### Next Session

Bir sonraki geliştirme oturumu Milestone 2'yi başlatmadan önce `Brain v1` mimari tasarımıyla başlayacak. Yeni kod yazılmadan önce Brain katmanının sorumlulukları, sınırları, model provider ilişkisi ve Conversation Service ile bağlantısı birlikte değerlendirilecek.

## 2026-07-07

### Sprint Durumu

Sprint 1 tamamlandı.

Bu sprint sonunda Lina terminal üzerinden çalıştırılabilir hale geldi. `python main.py` komutu uygulamayı başlatıyor, CLI açılıyor, kullanıcı mesajı `ConversationService` üzerinden `Brain` katmanına ulaşıyor ve `OllamaProvider` aracılığıyla yerel Ollama modelinden yanıt alınabiliyor.

### Major Architectural Decisions

- `Brain` provider-specific logic içermeyen küçük bir orchestrator olarak tutuldu.
- `ModelProvider` abstraction eklendi ve Brain yalnızca bu contract üzerinden model sağlayıcılarla konuşacak şekilde tasarlandı.
- `OllamaProvider`, dış sistem adapter'ı olarak `integrations` katmanında konumlandırıldı.
- `ConversationService`, kullanıcı mesajını Brain'e ileten ince bir application service olarak bırakıldı.
- CLI, business logic içermeyen basit bir interface katmanı olarak tasarlandı.
- Sprint 1 kapsamında Memory, Tool sistemi, Prompt Builder, Context Manager, Planner, Event Bus ve GUI bilinçli olarak kapsam dışında bırakıldı.

### Completed Commits

- `9d45cc4 feat: add model provider contract`
- `28ce0b1 feat: add brain orchestrator`
- `36b941a feat: add ollama provider`
- `1af246f feat: add conversation service`
- `1686aea feat: add cli interface`
- `8069c1e feat: add application entrypoint`
- `a0988f8 fix: handle ollama provider errors in cli`

### Bugs Discovered

- İlk gerçek çalıştırmada kullanıcı `Merhaba` yazdığında uygulama traceback ile çöküyordu.
- Kök neden, `config/default.toml` içindeki `ollama.default_model` değerinin boş olması ve CLI'ın provider hatalarını yakalamamasıydı.
- Ollama HTTP servisi çalışıyordu ve `/api/tags` üzerinden yerel model olarak `llama3.2:3b` görüldü.

### Bugs Fixed

- `config/default.toml` içindeki `ollama.default_model` değeri `llama3.2:3b` olarak ayarlandı.
- `ModelProviderError` eklendi.
- `OllamaProviderError`, ortak provider hatası olan `ModelProviderError` altında toplandı.
- `OllamaProvider`, model adı boşsa HTTP isteği atmadan anlamlı hata üretir hale getirildi.
- CLI, `ModelProviderError` hatalarını yakalayıp traceback yerine kullanıcıya okunabilir hata mesajı gösterecek şekilde güncellendi.

### Runtime Issues Encountered

- `ollama` komutu PowerShell PATH içinde bulunamadı.
- Buna rağmen Ollama HTTP servisi `http://localhost:11434/api/tags` üzerinden erişilebilir durumdaydı.
- Gerçek çalışma testi `python main.py` ile yapıldı ve `Merhaba` mesajına Ollama modelinden yanıt alındı.

### Lessons Learned

- Provider hataları CLI seviyesinde kullanıcı dostu şekilde ele alınmalı; terminal kullanıcıya traceback göstermemeli.
- Runtime config değerleri, özellikle model adı gibi zorunlu alanlar, gerçek çalıştırma öncesinde daha görünür hale getirilmeli.
- Brain'in provider-independent kalması doğru mimari karar oldu; hata düzeltmesi Brain'e dokunmadan provider ve interface sınırlarında yapılabildi.
- Gerçek runtime smoke test, unit testlerin yakalamadığı config kaynaklı sorunları erken ortaya çıkarıyor.

### Current Project Status

- Milestone 1 - Core Infrastructure tamamlandı.
- Sprint 1 - Terminal üzerinden çalışan ilk Lina tamamlandı.
- Lina şu anda terminalden açılabiliyor, kullanıcı mesajı alabiliyor ve yerel Ollama modeliyle cevap üretebiliyor.
- Tüm proje testleri başarıyla geçti: `52 passed`.

### Next Session Goals

- Sprint 2 kapsamı netleştirilecek.
- İlk önerilen çalışma, CLI ve provider hata deneyimini daha kullanıcı dostu hale getirmek veya Conversation Flow v1'e uygun ilk minimal intent ayrımını tasarlamak.
- Prompt Builder, Context Manager, Memory ve Tool sistemi henüz başlatılmayacaksa bu sınırlar açık şekilde korunmalı.

## 2026-07-07 - Sprint 2

### Sprint Durumu

Sprint 2 tamamlandı.

Bu sprintte Lina'nın terminal üzerinden verdiği cevapların daha tutarlı, kimlikli ve Türkçe odaklı olması için ilk conversation pipeline iyileştirmeleri yapıldı. Lina artık kullanıcı mesajını ham şekilde modele göndermek yerine minimal bir system prompt ve session içi geçici konuşma geçmişiyle birlikte provider'a iletir.

### Major Architectural Decisions

- `PromptBuilder`, prompt metninin dağınık şekilde farklı modüllere yayılmasını engellemek için Brain katmanı altında konumlandırıldı.
- Default system prompt ayrı bir modülde tutuldu; böylece Lina'nın kimliği, konuşma dili ve yetenek sınırları merkezi hale getirildi.
- `Brain`, provider-specific logic içermeden küçük bir orchestrator olarak kaldı.
- Conversation history gerçek Memory olarak tasarlanmadı; yalnızca runtime session içinde yaşayan geçici bağlam olarak `ConversationService` tarafından yönetildi.
- CLI iyileştirmeleri interface katmanında tutuldu; business logic veya intent analyzer eklenmedi.

### Completed Commits

- `35a09a8 feat: add prompt builder`
- `50e4e94 feat: add default system prompt`
- `c27c30f feat: integrate prompt builder with brain`
- `1c88cd7 feat: add conversation history`
- `c2b42ce fix: improve cli user experience`

### Added Features

- Minimal `PromptBuilder` eklendi.
- Lina'nın kimliğini ve konuşma sınırlarını tanımlayan default system prompt eklendi.
- Brain, user message'ı provider'a göndermeden önce Prompt Builder üzerinden prompt üretir hale getirildi.
- Session içi geçici conversation history eklendi.
- CLI için `help` ve `?` komutları eklendi.
- Provider hatası mesajı kullanıcıya daha doğal Türkçe bir metinle gösterilir hale getirildi.

### Bugs Discovered

- Brain testlerinde eski beklenti, kullanıcı mesajının provider'a ham şekilde gönderilmesini varsayıyordu.
- Sprint 2 mimarisi gereği bu davranış değiştiği için test yeni prompt pipeline sözleşmesine göre güncellendi.

### Bugs Fixed

- Eski Brain test beklentisi yeni Prompt Builder entegrasyonuyla uyumlu hale getirildi.
- CLI hata metni İngilizce teknik ifade yerine kullanıcı dostu Türkçe mesaja dönüştürüldü.

### Runtime Issues Encountered

- Bu sprintte yeni bir runtime hata tespit edilmedi.
- Sprint sonunda tam test paketi çalıştırıldı.

### Test Results

- `python -m pytest tests/brain/test_prompt_builder.py` sonucu: `2 passed`.
- `python -m pytest tests/brain/test_prompts.py` sonucu: `4 passed`.
- `python -m pytest tests/brain/test_brain.py` sonucu: `3 passed`.
- `python -m pytest tests/brain/test_prompt_builder.py tests/brain/test_brain.py tests/services/test_conversation_service.py` sonucu: `11 passed`.
- `python -m pytest tests/interfaces/test_cli.py` sonucu: `7 passed`.
- Sprint sonu tam test paketi: `64 passed`.

### Current Project Status

- Sprint 1 ile başlayan terminal tabanlı Lina artık daha tutarlı bir asistan kimliğine sahip.
- Lina kendisini Lina olarak tanımlayan bir system prompt ile konuşma üretir.
- Kullanıcının adının İlhan olduğu prompt seviyesinde modele aktarılır.
- Conversation history sadece oturum boyunca tutulur ve kalıcı Memory kapsamına girmez.
- Memory, Tool sistemi, Vision, Speech, Automation, Browser, Event Bus, Planner, Model Router, Multi-agent ve GUI hâlâ kapsam dışıdır.

### Lessons Learned

- Prompt davranışı merkezi tutulmadığında asistan kimliği ve dil standardı kolayca dağılabilir.
- Geçici conversation history, gerçek Memory tasarlanmadan önce faydalı ama sınırları net tutulması gereken bir ara adımdır.
- Brain'in küçük kalması entegrasyonları kolaylaştırıyor; yeni davranış Brain'e provider bilgisi eklemeden kazandırılabildi.
- Kullanıcıya gösterilen hata mesajları teknik olarak doğru olduğu kadar sakin ve anlaşılır da olmalı.

### Next Session Goals

- Sprint 3'e başlamadan önce Conversation Flow v1 ve Brain Specification v1 tekrar gözden geçirilecek.
- Bir sonraki mantıklı adım, minimal intent analysis veya context yönetiminin gerçekten gerekli olup olmadığını mimari olarak değerlendirmek.
- Memory, Tool sistemi veya Planner başlatılmadan önce kapsam ve sınırlar yeniden netleştirilecek.

## 2026-07-07 - Sprint 3

### Sprint Durumu

Sprint 3 tamamlandı.

Bu sprintte Lina'ya minimal, rule-based intent analysis katmanı eklendi. Amaç, bazı basit kullanıcı isteklerini LLM'e göndermeden deterministik şekilde cevaplamak ve normal sohbet akışını bozmadan korumaktı.

### Sprint 3 Hedefi

- Kullanıcının basit amacını ilk seviyede anlamak.
- `help`, kimlik, yetenekler ve saat gibi temel istekleri LLM'e gitmeden cevaplamak.
- Normal sohbet mesajlarını `Brain -> PromptBuilder -> ModelProvider -> Ollama` akışında bırakmak.
- Memory, Tool sistemi, Git entegrasyonu, dosya okuma, Planner veya Event Bus eklemeden küçük bir altyapı kurmak.

### Eklenen Intent Analysis Yapısı

- `IntentType` ve `Intent` modelleri eklendi.
- `IntentAnalyzer`, basit string matching ile desteklenen intent'leri tespit eder hale getirildi.
- Desteklenen intent'ler:
  - `HELP`
  - `IDENTITY`
  - `CAPABILITIES`
  - `CURRENT_TIME`
  - `CHAT`
  - `UNKNOWN`
- Analyzer büyük/küçük harf, baş/son boşluk ve basit noktalama durumlarını yönetir.
- Agresif eşleşmeden kaçınıldı; normal sohbet mesajlarının yanlışlıkla deterministic intent sayılmaması önceliklendirildi.

### LLM'e Gitmeden Cevaplanan Intent'ler

- `HELP`: Kullanıcıya kısa yardım metni döndürür.
- `IDENTITY`: Lina'nın kim olduğunu kısa ve Türkçe şekilde açıklar.
- `CAPABILITIES`: Mevcut gerçek yetenekleri dürüstçe listeler ve olmayan yetenekleri varmış gibi göstermez.
- `CURRENT_TIME`: Python standart kütüphanesiyle mevcut yerel saati döndürür.

### Major Architectural Decisions

- Deterministic cevaplar için yeni bir response modeli oluşturulmadı; mevcut `ModelResponse` kullanıldı.
- `ConversationService`, intent routing'in sahibi oldu.
- Deterministic intent geldiğinde `Brain` ve `OllamaProvider` çağrılmaz.
- `CHAT` intent geldiğinde mevcut Brain akışı korunur.
- Deterministic cevaplar session history'ye eklenir; böylece sonraki normal sohbetlerde bağlam olarak kullanılabilir.
- `exit` ve `quit` davranışı CLI katmanında bırakıldı.

### Completed Commits

- `211029c feat: add intent models`
- `b249aca feat: add intent analyzer`
- `31a29d9 feat: add deterministic response handler`
- `dcc5821 feat: route deterministic intents in conversation service`

### Test Results

- Başlangıç tam test paketi: `68 passed`.
- `python -m pytest tests/brain/test_intent.py` sonucu: `2 passed`.
- `python -m pytest tests/brain/test_intent_analyzer.py` sonucu: `20 passed`.
- `python -m pytest tests/services/test_deterministic_response_service.py` sonucu: `7 passed`.
- Routing ve CLI ilgili testleri: `41 passed`.
- Sprint sonu tam test paketi: `100 passed`.

### Bugs Discovered

- `?` mesajı başlangıçta normalize edilirken boş string'e dönüşüyordu ve `HELP` yerine `CHAT` olarak algılanıyordu.
- ConversationService history testi ilk tasarımda deterministic cevabın sonraki chat çağrısına taşındığını yeterince kanıtlamıyordu.

### Bugs Fixed

- `?` özel komut olarak korunacak şekilde normalize işlemi düzeltildi.
- ConversationService testi, deterministic cevabın sonraki `CHAT` çağrısında Brain'e history olarak iletildiğini doğrulayacak şekilde güçlendirildi.

### Current Project Status

- Lina artık bazı basit intent'leri LLM'e göndermeden cevaplayabiliyor.
- Normal sohbet akışı korunuyor.
- Memory, Git entegrasyonu, dosya okuma, Tool sistemi, Vision, Speech, Automation, Browser, Planner, Event Bus, GUI ve Multi-agent hâlâ kapsam dışında.
- Test kapsamı 100 teste ulaştı ve tüm testler başarıyla geçti.

### Known Limits

- Intent analysis yalnızca basit ve deterministik string matching kullanır.
- Karmaşık doğal dil, bağlamdan intent çıkarma veya entity extraction yoktur.
- `CURRENT_TIME` yalnızca yerel sistem saatini söyler; tarih, takvim veya zaman dilimi yorumu yapmaz.
- Deterministic cevaplar özelleştirilebilir prompt/persona sistemiyle bağlı değildir; Sprint 3 için bilinçli olarak küçük tutuldu.

### Sprint 4 Önerisi

- Sprint 4 öncesinde Context Manager v1 gerçekten gerekli mi, yoksa önce deterministic intent kapsamı mı genişletilmeli mimari olarak değerlendirilmeli.
- Eğer Context Manager seçilirse kapsam yalnızca conversation context ve runtime context ile sınırlı tutulmalı.
- Memory veya Tool sistemi başlatılmadan önce izin, güvenlik ve veri sınırları ayrıca netleştirilmeli.

## 2026-07-07 - Sprint 4

### Sprint Durumu

Sprint 4 tamamlandı.

Bu sprintte Lina için ilk masaüstü sohbet arayüzü eklendi. Amaç final görsel tasarım yapmak değil, terminal dışına çıkan ve mevcut `ConversationService` akışını kullanan sade, sürdürülebilir bir Desktop UI v1 oluşturmaktı.

### Sprint 4 Hedefi

- `python gui.py` komutuyla basit masaüstü sohbet penceresi açmak.
- Mevcut Brain, IntentAnalyzer, DeterministicResponseService, ConversationService ve OllamaProvider akışını korumak.
- CLI davranışını bozmamak.
- Tkinter ile dependency eklemeden ilk desktop UI temelini kurmak.
- Model cevapları beklenirken UI thread'in donmasını engellemek.

### Tkinter Seçimi

Tkinter seçildi çünkü Python standart kütüphanesinde bulunur, Windows üzerinde ek kurulum gerektirmez ve ilk masaüstü UI için yeterlidir. Bu sprintte PyQt, Electron, web frontend veya üçüncü parti UI kütüphanesi eklenmedi.

### Eklenen Yapı

- `gui.py` GUI entrypoint olarak eklendi.
- `src/lina/interfaces/gui.py` altında `LinaGui` Tkinter arayüzü eklendi.
- `src/lina/core/bootstrap.py` ile CLI ve GUI entrypoint'leri için ortak application wiring oluşturuldu.
- `main.py`, CLI davranışı korunarak ortak bootstrap kullanımına geçirildi.

### ConversationService Entegrasyonu

GUI doğrudan business logic içermez. Kullanıcıdan mesaj alır, `ConversationService` içine verir ve dönen `ModelResponse` değerini sohbet alanında gösterir. Bu sayede mevcut intent routing ve normal chat akışı korunur.

### Background Thread Davranışı

- Kullanıcı mesaj gönderdiğinde input ve gönder butonu geçici olarak disable edilir.
- Sohbet alanına `Lina: yazıyor...` mesajı eklenir.
- `ConversationService.handle_message()` background thread içinde çalıştırılır.
- UI güncellemesi Tkinter ana thread'ine `after()` ile döner.
- Aynı anda birden fazla mesaj gönderimi şimdilik engellenir.

### Hata Yönetimi

GUI, `ModelProviderError` hatalarını traceback göstermeden sohbet mesajı olarak gösterir. Kullanıcıya şu tarz kısa ve Türkçe bir hata döner:

`Lina şu anda modele ulaşamadı. Ollama çalışıyor mu kontrol edebilir misin?`

CLI hata davranışı değiştirilmedi.

### Completed Commits

- `ed101b3 feat: add gui application wiring`
- `c740b6f feat: add tkinter chat window`
- `028efff feat: run gui requests in background thread`
- `4c42fda fix: show gui errors as chat messages`
- `09f0f4b fix: keep logging setup deterministic`

### Test Results

- Başlangıç tam test paketi: `100 passed`.
- GUI wiring testleri: `3 passed`.
- GUI window ve entrypoint testleri: `5 passed`.
- GUI threading testleri: `5 passed`.
- GUI ve CLI error handling testleri: `14 passed`.
- Logging izolasyon düzeltmesi sonrası ilgili testler: `8 passed`.
- Sprint sonu tam test paketi: `109 passed`.

### Bugs Discovered

- Kök seviyede `tests/test_gui.py` ve interface seviyesinde `tests/interfaces/test_gui.py` aynı modül adıyla çakıştı. Entry point testi `tests/test_gui_entrypoint.py` olarak yeniden adlandırıldı.
- Tam test paketinde yeni bootstrap testleri sonrası logging testleri kırıldı. Kök neden, `configure_logging()` fonksiyonunun dış handler'ları kendi yönettiği handler gibi kabul etmesiydi.

### Bugs Fixed

- GUI entrypoint test dosyası yeniden adlandırılarak test import çakışması giderildi.
- `configure_logging()`, yalnız Lina tarafından yönetilen handler'ı takip edecek şekilde deterministik hale getirildi.

### Current Project Status

- Lina terminalden `python main.py` ile çalışmaya devam eder.
- Lina masaüstü arayüzden `python gui.py` ile çalıştırılabilir.
- GUI üzerinden deterministic intent cevapları ve normal Ollama chat akışı kullanılabilir.
- UI model cevabı beklerken donmamak için background thread kullanır.
- Memory, Tool sistemi, Vision, Speech, Automation, Browser, Camera, Planner, Event Bus, GUI ayar ekranı, packaging ve installer hâlâ kapsam dışıdır.

### Known Limits

- UI görsel olarak minimaldir; tema, ikon, modern tasarım sistemi veya system tray yoktur.
- Aynı anda yalnızca bir mesaj gönderimi desteklenir.
- Shift+Enter desteği yoktur.
- GUI unit testleri gerçek Tkinter `mainloop` çalıştırmaz; helper ve davranış seviyesinde test edilir.
- Paketleme veya `.exe` üretimi yapılmadı.

### Sprint 5 Önerisi

- Sprint 5 öncesinde masaüstü UI'ın mı iyileştirileceği, yoksa Context Manager v1 / conversation context tarafına mı geçileceği mimari olarak değerlendirilmeli.
- Eğer UI devam edecekse önerilen küçük adım: GUI mesaj görünümünü ve kullanıcı deneyimini iyileştirmek, ama yeni framework veya tema sistemi eklememek.
- Eğer Brain tarafı devam edecekse önerilen adım: Context Manager v1 kapsamını yalnız runtime conversation context ile sınırlamak.

## 2026-07-07 - Sprint 5

### Sprint Durumu

Sprint 5 tamamlandı.

Bu sprintte Lina'nın Tkinter tabanlı masaüstü arayüzü daha okunabilir ve düzenli hale getirildi. Ek olarak, Türkçe cevap kalitesini güçlendirmek için default system prompt daha açık yönergelerle güncellendi.

### Sprint 5 Hedefi

- GUI'nin ham Tkinter demo hissini azaltmak.
- Pencere boyutu, minimum boyut, spacing ve resize davranışını iyileştirmek.
- Sohbet mesajlarını daha okunabilir hale getirmek.
- Input focus ve cevap sonrası kullanım akışını güçlendirmek.
- Türkçe cevaplarda karışık dil kırpıntılarını azaltmak.
- README'ye CLI ve GUI kullanım notu eklemek.

### GUI UX İyileştirmeleri

- Pencere başlangıç boyutu `780x620`, minimum boyutu `520x420` olarak ayarlandı.
- Ana içerik `ttk.Frame` içinde padding ile düzenlendi.
- Chat alanı, input alanı ve gönder butonu daha dengeli grid layout ile hizalandı.
- Chat alanı için daha okunabilir `Segoe UI` fontu kullanıldı.
- Mesaj formatı gönderen ve içerik ayrı satırlarda olacak şekilde sadeleştirildi.
- `Lina: Yazıyor...` geçici mesajı satır sayısına bağlı silme yerine metin aralığı takip edilerek kaldırılır hale getirildi.
- Pencere açıldığında input focus alır.
- Cevap veya hata sonrası input tekrar enable edilir ve focus input'a döner.

### Türkçe Cevap Kalitesi

- Default system prompt, Türkçe cümle içinde kırpılmış veya uydurma yabancı kelimeleri engelleyecek şekilde güçlendirildi.
- Teknik terimlerin gerektiğinde İngilizce kalabileceği açıkça belirtildi.
- Lina'nın bilmediği konularda "bunu kesin bilmiyorum" diyebilmesi için dürüst belirsizlik yönergesi eklendi.
- İlhan'a samimi ama abartısız hitap etmesi vurgulandı.

### README Güncellemesi

- `README.md` içine `python main.py` ile CLI çalıştırma bilgisi eklendi.
- `python gui.py` ile masaüstü GUI çalıştırma bilgisi eklendi.
- Normal sohbet cevapları için Ollama'nın çalışıyor olması ve yapılandırılmış modelin yüklü olması gerektiği not edildi.

### Completed Commits

- `e1d204f improve gui layout and spacing`
- `f56e73c improve chat message rendering`
- `e1f7814 improve gui input behavior`
- `793bd92 fix: improve Turkish response guidance`
- `f815dbb docs: update README usage instructions`

### Test Results

- Başlangıç tam test paketi: `109 passed`.
- GUI layout sonrası interface testleri: `7 passed`.
- Chat rendering sonrası interface testleri: `7 passed`.
- Input davranışı sonrası interface testleri: `7 passed`.
- Prompt güncellemesi sonrası ilgili testler: `15 passed`.
- Sprint sonu tam test paketi: `112 passed`.

### Current Project Status

- Lina CLI üzerinden `python main.py` ile çalışmaya devam eder.
- Lina GUI üzerinden `python gui.py` ile çalıştırılabilir.
- GUI daha okunabilir, daha dengeli ve daha profesyonel bir ilk masaüstü deneyimi sunar.
- Türkçe cevap rehberliği daha nettir.
- Yeni dependency eklenmedi.

### Known Limits

- GUI hâlâ minimal Tkinter arayüzüdür; özel tema sistemi, ikon, system tray veya paketleme yoktur.
- Shift+Enter desteği yoktur.
- Aynı anda tek mesaj gönderimi desteklenir.
- Türkçe kalitesi prompt ile iyileştirildi; language detector veya post-processor eklenmedi.
- Memory, Tool sistemi, dosya okuma, GitHub entegrasyonu, Vision, Speech ve Automation hâlâ kapsam dışıdır.

### Sprint 6 Önerisi

- Sprint 6 öncesinde iki yönden biri seçilmeli:
  - GUI v1.1: küçük görsel iyileştirmeler, pencere kapanış davranışı ve kullanıcı deneyimi detayları.
  - Brain Context v1: yalnız runtime conversation context ile sınırlı, Memory olmayan küçük context yönetimi.
- Büyük özellik eklemeden önce seçilecek yönün roadmap ve Brain Specification ile ilişkisi kısa mimari değerlendirmeyle netleştirilmeli.

## 2026-07-07 - Sprint 6

### Sprint Durumu

Sprint 6 tamamlandı.

Bu sprintte Lina'ya sınırlı ve güvenli Project Awareness v1 eklendi. Lina artık proje durumu veya son sprintlerle ilgili belirli sorularda genel dosya erişimi kazanmadan, yalnız izinli proje dokümanlarından bağlam toplayıp Brain'e iletebilir.

### Eklenen Yapı

- `ProjectContextService` eklendi.
- İzinli doküman allowlist'i tanımlandı:
  - `README.md`
  - `docs/development-log.md`
  - `docs/roadmap.md`
- `PROJECT_STATUS` ve `PROJECT_SUMMARY` intent türleri eklendi.
- `PromptBuilder`, optional project context desteği kazandı.
- `ConversationService`, project awareness intent geldiğinde project context toplayıp Brain'e iletir hale getirildi.
- Bootstrap sırasında `ProjectContextService`, repo root ile açık şekilde oluşturuldu.

### Güvenlik Sınırları

- Genel file browser eklenmedi.
- Kullanıcı dosyaları okunmadı.
- Git command, GitHub API, tool sistemi veya Memory eklenmedi.
- Path traversal engellendi.
- Allowlist dışı dosyalar okunmaz.
- Eksik dokümanlar uygulamayı çökertmez.
- Okunan içerik dosya başına karakter limitiyle sınırlandırıldı.

### Completed Commits

- `9e36c54 feat: add project context service`
- `1068ad4 feat: add project awareness intent`
- `3ca5e43 feat: include project context in prompts`
- `9bacab3 feat: route project awareness requests`

### Test Results

- Sprint başlangıç tam test paketi: `112 passed`.
- `ProjectContextService` testleri: `5 passed`.
- Intent model ve analyzer testleri: `29 passed`.
- PromptBuilder ve Brain project context testleri: `9 passed`.
- ConversationService ve bootstrap routing testleri: `10 passed`.
- Sprint sonu tam test paketi: `128 passed`.

### Current Project Status

- Lina, "Lina projesinin durumu ne?", "Bugün Lina projesinde ne yaptık?", "Son sprintlerde ne eklendi?" gibi sorularda izinli proje dokümanlarından bağlam sağlayabilir.
- Bu cevaplar hâlâ Brain ve model üzerinden üretilir; deterministic summary motoru eklenmedi.
- Model prompt'u, verilen proje bağlamında olmayan proje geçmişi, commit, URL, dosya veya yapılan iş uydurmaması için açıkça yönlendirilir.

### Known Limits

- Project Awareness yalnız üç izinli dokümandan metin toplar.
- Git geçmişi, GitHub, commit listesi veya dosya sistemi taraması yoktur.
- Project context basit metin olarak verilir; embedding, vector database veya RAG framework yoktur.
- Bağlam uzunluğu karakter limitiyle sade şekilde kontrol edilir.

### Sprint 7 Notu

Sprint 7 için doğal sonraki adım, conversation history ve project context akışını küçük bir `ContextManager` altında sadeleştirmektir. Bu adım Memory değildir ve kalıcı depolama içermemelidir.

## 2026-07-07 - Sprint 7

### Sprint Durumu

Sprint 7 tamamlandı.

Bu sprintte runtime conversation context akışı küçük ve test edilebilir bir Context Manager katmanına taşındı. Bu çalışma Memory değildir; kalıcı depolama, embedding, özetleme veya vector database içermez.

### Eklenen Yapı

- `ConversationContext` modeli eklendi.
- `ContextManager` eklendi.
- ContextManager sınırlı conversation history sağlar.
- Project awareness intent geldiğinde project context toplama sorumluluğu ContextManager'a taşındı.
- `PromptBuilder`, `ConversationContext` üzerinden prompt üretebilir hale geldi.
- `Brain`, `respond_with_context()` ile context tabanlı cevap üretme akışı kazandı.
- `ConversationService`, context toplama detaylarından arındırıldı.

### Mimari Kararlar

- `ApplicationContext` ile karışmaması için runtime bağlam modeli `ConversationContext` olarak adlandırıldı.
- Token counting, summarization, Memory veya embedding eklenmedi.
- ConversationService hâlâ intent routing ve history append akışının sahibidir.
- ContextManager yalnız o anki kullanıcı mesajı için sınırlı runtime context üretir.

### Completed Commits

- `0f2b874 feat: add conversation context models`
- `8702455 feat: add context manager`
- `92d952f feat: integrate context with prompt builder`
- `5a3c870 refactor: simplify conversation service context flow`

### Test Results

- Sprint başlangıç tam test paketi: `128 passed`.
- ConversationContext testleri: `1 passed`.
- ContextManager testleri: `4 passed`.
- PromptBuilder, Brain ve context model testleri: `12 passed`.
- ConversationService, ContextManager ve bootstrap testleri: `14 passed`.
- Sprint sonu tam test paketi: `135 passed`.

### Current Project Status

- Lina'nın conversation history ve project context akışı daha düzenli hale geldi.
- Project awareness, normal chat ve deterministic intent davranışları korunuyor.
- Kalıcı Memory hâlâ kapsam dışıdır.

### Known Limits

- ContextManager yalnız basit string context ve sınırlı history taşır.
- Token limiti, semantic retrieval, summarization ve long-term memory yoktur.
- Project context hâlâ yalnız allowlist dokümanlardan alınır.

### Sprint 8 Notu

Bir sonraki mantıklı adım güvenli tool altyapısının temelini atmaktır. Sprint 8 kapsamında gerçek shell, dosya yazma/silme veya otomasyon olmadan yalnız tool contract, permission model ve safe builtin tool eklenmelidir.

## 2026-07-07 - Sprint 8

### Sprint Durumu

Sprint 8 tamamlandı.

Bu sprintte Lina için Safe Tool Foundation v1 eklendi. Amaç gerçek bilgisayar kontrolü vermek değil, gelecekteki tool sisteminin güvenli kontrat, permission ve registry temelini atmaktı.

### Eklenen Yapı

- `PermissionLevel` modeli eklendi.
- Yalnız `SAFE` permission seviyesinin otomatik çalıştırılabileceği kuralı eklendi.
- `Tool` protocol yapısı eklendi.
- `ToolResult` modeli eklendi.
- `ToolRegistry` eklendi.
- Duplicate tool kaydı reddedilir hale getirildi.
- Unknown tool için temiz `ToolRegistryError` eklendi.
- Güvenli builtin tool olarak `EchoTool` eklendi.

### Güvenlik Sınırları

- Shell command execution yoktur.
- Dosya okuma/yazma/silme yoktur.
- Browser, camera, screen veya OS automation yoktur.
- LLM otomatik tool seçemez.
- GUI veya CLI üzerinden tool execution bağlanmadı.
- Bu sprintte yalnız tool altyapısı ve testleri eklendi.

### Completed Commits

- `157d5a2 feat: add tool models and permissions`
- `ca105a6 feat: add tool registry`
- `f14f026 feat: add safe builtin tool`

### Test Results

- Sprint başlangıç tam test paketi: `135 passed`.
- Permission ve tool model testleri: `3 passed`.
- Tool registry testleri: `4 passed`.
- Builtin, permission ve registry testleri: `8 passed`.
- Sprint sonu tam test paketi: `144 passed`.

### Current Project Status

- Lina artık güvenli tool altyapısının temel modellerine sahip.
- Tool sistemi henüz conversation flow'a bağlanmadı.
- Sadece SAFE tool'ların otomatik çalıştırılabileceği temel kural tanımlandı.

### Known Limits

- Tool execution service henüz yok.
- Intent routing tool sistemine bağlı değil.
- Permission confirmation UI yok.
- Dangerous, read-only veya confirmation gerektiren tool'lar otomatik çalıştırılmaz.

### Sprint 9 Notu

Sprint 9 için doğal sonraki adım, SAFE tool'ların kontrollü şekilde ConversationService akışına bağlanmasıdır. Bu bağlama yalnız deterministic intent üzerinden olmalı; LLM'in kendi başına tool çalıştırmasına izin verilmemelidir.

## 2026-07-07 - Sprint 9

### Sprint Durumu

Sprint 9 tamamlandı.

Bu sprintte Sprint 8'de eklenen safe tool altyapısı kontrollü şekilde conversation flow'a bağlandı. LLM'in kendi kendine tool seçmesine izin verilmedi; yalnız deterministic intent üzerinden SAFE tool çalıştırma yolu eklendi.

### Eklenen Yapı

- `ToolExecutionService` eklendi.
- Tool execution sırasında permission check uygulanır hale getirildi.
- `CurrentTimeTool` eklendi.
- `CURRENT_TIME` intent'i, uygun durumda `ToolExecutionService` üzerinden `current_time` safe tool'una yönlendirilir hale getirildi.
- Bootstrap sırasında `ToolRegistry`, `EchoTool`, `CurrentTimeTool` ve `ToolExecutionService` açık şekilde oluşturuldu.

### Güvenlik Sınırları

- SAFE olmayan tool'lar otomatik çalıştırılmaz.
- Shell execution yoktur.
- Dosya write/delete yoktur.
- Browser, camera, screen veya OS automation yoktur.
- LLM tool seçmez; routing deterministic intent üzerinden yapılır.

### Completed Commits

- `98f4529 feat: add tool execution service`
- `2338398 feat: route safe tool intents`

### Test Results

- Sprint başlangıç tam test paketi: `144 passed`.
- ToolExecutionService, registry ve permission testleri: `8 passed`.
- CurrentTimeTool, ConversationService routing, bootstrap ve execution testleri: `17 passed`.
- Sprint sonu tam test paketi: `149 passed`.

### Current Project Status

- Lina artık güvenli tool altyapısını conversation flow içinde kontrollü şekilde kullanabiliyor.
- `Saat kaç?` gibi current time intent'i Brain/Ollama çağırmadan safe tool üzerinden cevaplanabilir.
- Deterministic intent ve normal chat akışları korunuyor.

### Known Limits

- Tool execution sadece SAFE tool'larla sınırlıdır.
- Permission confirmation UI yoktur.
- LLM function calling veya otomatik tool planning yoktur.
- Dangerous, read-only veya confirmation gerektiren tool'lar otomatik çalıştırılmaz.

### Sprint 10 Notu

Sprint 10 için yeni büyük özellik eklenmemeli. Odak v0.2.0-alpha release candidate hazırlığı, README/roadmap güncellemesi, smoke test checklist ve bilinen sınırlamaların dokümante edilmesi olmalıdır.

## 2026-07-07 - Sprint 10

### Sprint Durumu

Sprint 10 tamamlandı.

Bu sprintte Lina `v0.2.0-alpha` release candidate için dokümantasyon ve kalite açısından toparlandı. Yeni büyük özellik eklenmedi; odak README, roadmap, smoke test checklist ve release hazırlığıydı.

### Eklenen / Güncellenen Dokümantasyon

- `docs/smoke-test-checklist.md` eklendi.
- `README.md`, mevcut `v0.2.0-alpha` durumunu yansıtacak şekilde güncellendi.
- `docs/roadmap.md`, tamamlanan ana başlıkları ve henüz kapsam dışı olan büyük özellikleri gösterecek şekilde güncellendi.
- Development log'a Sprint 10 kapanışı eklendi.

### Release Candidate Özeti

`v0.2.0-alpha` seviyesinde Lina şunları destekler:

- CLI arayüzü.
- Tkinter Desktop UI.
- Ollama ile yerel LLM cevabı.
- Brain orchestration.
- PromptBuilder ve Türkçe response guidance.
- Runtime conversation context.
- Session içi geçici history.
- Rule-based intent analyzer.
- Deterministic responses.
- Sınırlı project awareness.
- Safe tool foundation.
- Current time safe tool routing.
- Unit test suite.

### Completed Commits

- `6d4d057 docs: add smoke test checklist`
- `6629c86 docs: update README for v0.2.0-alpha`
- `9c0a8fd docs: update roadmap after sprint 10`

### Test Results

- Sprint başlangıç tam test paketi: `149 passed`.
- Sprint final tam test paketi bu log yazıldıktan sonra çalıştırılacaktır.

### Known Limits

- Kalıcı Memory yoktur.
- Genel dosya capability'si yoktur.
- Shell command execution yoktur.
- Browser, camera, speech, vision ve Windows automation yoktur.
- Tool sistemi yalnız SAFE foundation seviyesindedir.
- Project awareness yalnız allowlist dokümanlarla sınırlıdır.
- Packaging, installer ve `.exe` üretimi yoktur.

### Tag Önerisi

Önerilen release tag:

`v0.2.0-alpha`

Tag otomatik oluşturulmadı. Tag oluşturma ayrıca kullanıcı onayı gerektirir.

## 2026-07-07 - v0.3.0-alpha Release Candidate Hotfix

### Amaç

Manuel GUI smoke testte görülen kritik kullanıcı deneyimi ve cevap kalitesi sorunları düzeltildi. Yeni büyük özellik eklenmedi.

### Düzeltilenler

- GUI chat render katmanında asistan etiketi çiftlenmesi düzeltildi.
- Assistant response `Lina:` ile başlıyorsa ekranda ikinci kez `Lina:` gösterilmemesi sağlandı.
- Kullanıcı etiketi için de aynı çiftleme koruması eklendi.
- Deterministic capabilities cevabı mevcut gerçek yetenekleri yansıtacak şekilde güncellendi.
- Capabilities cevabı, olmayan yetenekleri ve Git işlemi sınırlarını daha açık belirtir hale getirildi.
- HELP intent matching regression testleri güçlendirildi.
- Gelecek yeteneklerle ilgili normal sohbet sorularının `CHAT` olarak kalması testlendi.
- Türkçe reliability guidance daha kısa, net ve sert hale getirildi.

### Test Sonucu

- Hotfix öncesi başlangıç test paketi: `196 passed`.
- Hotfix sonrası final test paketi: `206 passed`.

### Completed Commits

- `8a7a53c fix: correct gui assistant label rendering`
- `3132d50 fix: update deterministic capability response`
- `4722b04 fix: tighten help intent matching`
- `47d79fc fix: strengthen Turkish reliability guidance`

### v0.3.0-alpha Durumu

Bu hotfix sonrası `v0.3.0-alpha` tag için teknik olarak daha hazır durumdadır. Tag otomatik oluşturulmadı; kullanıcı onayı gerektirir.

## 2026-07-07 - v0.3.0-alpha Release Blocker Fix

### Amaç

Manuel GUI smoke testte tekrar görülen release blocker seviyesindeki sorunlar incelendi ve düzeltildi. Yeni büyük özellik eklenmedi.

### Düzeltilenler

- GUI gerçek render path üzerinde tekrarlı `Lina:` / `İlhan:` etiketleri normalize edilir hale getirildi.
- `Lina:Lina:` gibi tekrarlı asistan etiketi regression test ile güvenceye alındı.
- Tek bir mesaj gönderiminde final cevabın iki kez append edilmemesi testlendi.
- Model diagnostics, Ollama unreachable, model not available ve timeout durumlarını daha net ayırır hale getirildi.
- GUI provider hata mesajları hata türüne göre daha açıklayıcı hale getirildi.
- Ollama provider timeout hatasını ayrı domain mesajına dönüştürür hale getirildi.

### Config Kontrolü

- `config/default.toml` içindeki model adı `llama3.2:3b` olarak korunuyor.
- `settings -> bootstrap -> OllamaProvider` zincirinde `base_url`, `default_model` ve `request_timeout` aktarımı doğrulandı.
- CLI ve GUI aynı configuration/bootstrap hattını kullanıyor.

### Test Sonucu

- Hotfix öncesi başlangıç test paketi: `206 passed`.
- Release blocker fix sonrası final test paketi: `218 passed`.

### Completed Commits

- `c8fdc6d fix: resolve gui label duplication in render path`
- `aab77bf fix: improve model connection diagnostics`

### v0.3.0-alpha Durumu

Bu düzeltmelerden sonra `v0.3.0-alpha` tag için bloklayıcı görünen GUI render ve diagnostics sorunları giderildi. Tag otomatik oluşturulmadı.

## 2026-07-07 - Sprint 11

### Sprint Durumu

Sprint 11 tamamlandı.

Bu sprintte kod tabanı kalite ve mimari sertleştirme açısından denetlendi. Büyük mimari refactor yapılmadı; public davranış korunarak küçük bir error handling tutarlılığı iyileştirildi.

### Audit Bulguları

- TODO/FIXME veya açık yarım bırakılmış işaret bulunmadı.
- Test paketi sprint başında temizdi.
- Tool execution hatalarının interface katmanlarına sızma riski olduğu görüldü.

### Yapılan İyileştirme

- `ToolExecutionService`, registry kaynaklı tool hatalarını `ToolExecutionError` altında toplar hale getirildi.
- `ConversationService`, current time safe tool çalıştırması başarısız olursa deterministic response fallback'i kullanır hale getirildi.
- CLI ve GUI davranışı korunarak tool error handling daha tutarlı hale getirildi.

### Completed Commits

- `b3fffda refactor: improve tool error handling consistency`

### Test Results

- Sprint başlangıç tam test paketi: `149 passed`.
- İlgili service/interface testleri: `28 passed`.
- Sprint sonu tam test paketi: `151 passed`.

### Current Project Status

- Tool execution hata sınırları daha tutarlı.
- SAFE current time akışı başarısız olsa bile kullanıcıya cevap üretme yolu korunuyor.
- Büyük mimari değişiklik yapılmadı.

### Sprint 12 Notu

Bir sonraki adım runtime configuration seçeneklerini geriye uyumlu şekilde genişletmek olmalıdır. Config formatı kırılmamalı ve optional ayarlar default değer almalıdır.

## 2026-07-07 - Sprint 12

### Sprint Durumu

Sprint 12 tamamlandı.

Bu sprintte Lina'nın runtime configuration sistemi geriye uyumlu şekilde genişletildi. Mevcut config formatı kırılmadı; yeni ayarlar eksik olduğunda güvenli default değerleriyle çalışır.

### Eklenen Ayarlar

- `ollama.request_timeout`
- `runtime.conversation_history_limit`
- `runtime.project_context_max_characters`

### Kullanım Noktaları

- Ollama provider timeout değeri settings üzerinden verilir.
- ConversationService history limiti settings üzerinden verilir.
- ProjectContextService doküman karakter limiti settings üzerinden verilir.

### Completed Commits

- `7ff69aa feat: add runtime configuration options`
- `2a4f68c docs: document runtime configuration`
- `af69da3 fix: preserve settings dataclass defaults`

### Test Results

- Sprint başlangıç tam test paketi: `151 passed`.
- Settings, bootstrap ve project context testleri: `18 passed`.
- Geriye uyumluluk düzeltmesi sonrası ilgili core testleri: `21 passed`.
- Sprint sonu tam test paketi: `155 passed`.

### Current Project Status

- Runtime config daha merkezi ve test edilebilir hale geldi.
- Eski `AppSettings`, `OllamaSettings` ve config kullanımları geriye uyumlu kalır.
- Yeni dependency eklenmedi.

### Known Limits

- GUI ayar ekranı yoktur.
- Ayarlar runtime sırasında kullanıcı arayüzünden değiştirilemez.
- Environment variable override sistemi hâlâ yoktur.

### Sprint 13 Notu

Bir sonraki adım Ollama diagnostics ve model status görünürlüğüdür. Amaç model indirmek veya Ollama kurmak değil, kullanıcıya bağlantı durumunu daha anlaşılır göstermektir.

## 2026-07-07 - Sprint 13

### Sprint Durumu

Sprint 13 tamamlandı.

Bu sprintte Lina'ya Ollama bağlantı durumunu kontrol eden `ModelDiagnosticsService` eklendi. GUI açılışında model status göstergesi eklenerek kullanıcı bağlantı durumunu daha net görebilir hale geldi.

### Eklenen Yapı

- `ModelDiagnosticsService` eklendi.
- `ModelStatus` enum modeli eklendi: `READY`, `CONNECTING`, `OLLAMA_UNREACHABLE`, `MODEL_NOT_CONFIGURED`.
- `DiagnosticsResult` modeli eklendi.
- `format_status_message()` fonksiyonu ile kullanıcı dostu Türkçe durum mesajları üretilir.
- Ollama erişilebilirliği `/api/tags` endpoint'ine GET isteğiyle kontrol edilir.
- GUI'ye status label eklendi; açılışta background thread ile diagnostics çalıştırılır.
- Bootstrap'a `ModelDiagnosticsService` eklendi ve `ApplicationServices`'e dahil edildi.
- GUI entrypoint, diagnostics service'i LinaGui'ye inject eder hale getirildi.

### Güvenlik Sınırları

- Model indirme veya `ollama pull` yapılmaz.
- Shell command execution yoktur.
- Yeni dependency eklenmedi.
- CLI davranışı korundu.
- Mevcut ConversationService akışı bozulmadı.

### Completed Commits

- `22115aa feat: add model diagnostics service`
- `99679b9 feat: show model status in gui`

### Test Results

- Diagnostics service testleri: `13 passed`.
- GUI diagnostics testleri: `3 passed`.
- Sprint sonu tam test paketi: `171 passed`.

### Current Project Status

- Lina GUI açıldığında Ollama bağlantı durumunu kontrol eder ve status bar'da gösterir.
- Reachable, unreachable ve model not configured durumları test edilmiştir.
- CLI davranışı değişmedi.

### Known Limits

- CLI tarafında diagnostics göstergesi yoktur.
- Diagnostics yalnız uygulama başlangıcında çalışır; periyodik kontrol yoktur.
- Model listesinden gerçekten yüklü model kontrolü yapılmaz; yalnız Ollama erişilebilirliği doğrulanır.

### Sprint 14 Notu

Bir sonraki adım GUI'yi daha profesyonel ve kullanışlı hale getirmektir.

## 2026-07-07 - Sprint 14

### Sprint Durumu

Sprint 14 tamamlandı.

Bu sprintte Lina'nın Tkinter GUI'si daha profesyonel ve kullanışlı hale getirildi. Yeni dependency eklenmedi, mevcut ConversationService akışı korundu.

### GUI İyileştirmeleri

- Üst başlık alanı eklendi: "Lina — Yapay Zekâ Masaüstü Asistanı".
- Alt status bar eklendi: bağlantı durumu, cevap bekleme durumu gösterilir.
- "Sohbeti Temizle" butonu eklendi.
- "Son Cevabı Kopyala" butonu eklendi.
- Pencere boyutu 820x660'a yükseltildi.
- Hata mesajı daha açıklayıcı hale getirildi.
- Başlangıç mesajı daha profesyonel ve sıcak hale getirildi.
- Pencere kapatma davranışı `WM_DELETE_WINDOW` ile temiz şekilde yönetilir.
- Header ve content arasında separator eklendi.
- Input alanı ve butonlar ayrı frame'lerde düzenlendi.
- Son cevap text'i takip edilerek kopyalama fonksiyonu sağlandı.

### Completed Commits

- `adc0702 feat: add gui status bar and chat controls`

### Test Results

- GUI interface testleri: `17 passed`.
- Sprint sonu tam test paketi: `178 passed`.

### Current Project Status

- GUI daha profesyonel bir görünüme sahip.
- Clear chat ve copy last response fonksiyonları çalışıyor.
- Status bar bağlantı ve cevap durumunu gösteriyor.
- CLI davranışı değişmedi.

### Known Limits

- Tema sistemi eklenmedi.
- Shift+Enter desteği hâlâ yok.
- İkon ve system tray yoktur.

### Sprint 15 Notu

### Sprint 15 Notu

Bir sonraki adım read-only Git context desteği ile project awareness'ı güçlendirmektir.

## 2026-07-07 - Sprint 15

### Sprint Durumu

Sprint 15 tamamlandı.

Lina'nın "Project Awareness" yeteneği read-only Git context desteği ile güçlendirildi. `GitContextService` geliştirilerek aktif branch, son commitler ve working tree durumu proje sorularına dahil edildi.

### Eklenen Yapı

- `GitContextService` eklendi. Sadece "branch", "log" ve "status" komutlarını kullanarak güvenli bilgi toplar.
- `ContextManager`, proje sorularında (`PROJECT_STATUS`, `PROJECT_SUMMARY`) hem dokümanlardan hem de git üzerinden bağlam toplayacak şekilde genişletildi.
- `Bootstrap` üzerinde `GitContextService` uygulamaya dâhil edilerek ContextManager'a enjekte edildi.
- İzinli olmayan komut veya girdilerin sisteme dâhil olmasını engellemek için `GitContextService` içinde sabit argüman listeleri kullanıldı. (shell=True kullanılmadı).

### Güvenlik Sınırları

- Yalnızca "read-only" git komutları kullanılır.
- Kullanıcı girdisi komutlara doğrudan eklenmez.
- `shell=True` kesinlikle kapalıdır.
- Güvenli zaman aşımları (`timeout`) tanımlandı. Hata durumları uygulamayı çökertmeyecek şekilde (`False`, None, vs.) yönetildi.

### Completed Commits

- `5e33120 feat: add read-only git context service`

### Test Results

- Git context service testleri dahil tüm suite çalıştırıldı: `194 passed`.

### Current Project Status

- Lina artık "Projenin durumu ne?" gibi sorulara sadece dokümanları değil, bulunduğu deponun "main" dalında olup olmadığını ve okunabilir git log'larını/status durumunu da referans alarak daha iyi cevaplar verebilir.
- CLI ve GUI davranışları başarılı şekilde aynı bağlam yönetimini kullanır.

### Known Limits

- Sadece o an bulunulan deponun kök dizinine dair bilgi verir, çoklu depo desteği yoktur.
- Son 10 commit sabittir.
- Git yüklü değilse hata vermeden sessizce git verisini atlar.

### Sprint 16 Notu

Bir sonraki adım, Tool Execution yeteneğinin yetkilendirme (PermissionDecision) UX süreçlerini güçlendirmektir.

## 2026-07-07 - Sprint 16

### Sprint Durumu

Sprint 16 tamamlandı.

Tool Execution sürecindeki yetkilendirme modeli daha kullanıcı dostu bir hale getirilerek `PermissionDecision` yapısına taşındı.

### Eklenen Yapı

- `PermissionDecision` veri modeli (`is_allowed` ve `reason`) oluşturuldu.
- `can_execute_automatically` fonksiyonu yerine daha zengin bilgi sunan `check_tool_permission` eklendi.
- `ToolExecutionService` güncellenerek araç otomatik çalıştırma reddedildiğinde kullanıcının anlayabileceği `reason` mesajını hata olarak dönmesi sağlandı.

### Güvenlik Sınırları

- Daha önce `SAFE` araçlarda olan otomatik çalıştırma yetkisi korundu.
- Kullanıcı onayı (interactive mode) veya UI entegrasyonu eklenmedi, sadece yetkilendirme altyapısı genişletildi.

### Completed Commits

- `cb4e178 feat: enhance tool permissions UX model`

### Test Results

- Tool Execution ve Permission testleri suite genelinde başarılı: `194 passed`.

### Current Project Status

- Araçlar yetkilendirme sınırlarını daha anlamlı hata mesajlarıyla kontrol ediyor.
- Lina'nın araç kullanım altyapısı gelecekte GUI üzerinde onay pencereleri çıkarabilmeye uygun bir formata kavuştu.

### Sprint 17 Notu

Bir sonraki adım, Assistant Reliability (Prompt/Guidance) iyileştirmelerini yapmak ve Türkçe cevapların kalitesini garanti altına almaktır.

## 2026-07-07 - Sprint 17

### Sprint Durumu

Sprint 17 tamamlandı.

Lina'nın sistem promptu (DEFAULT_SYSTEM_PROMPT) yeniden düzenlenerek daha güvenilir, doğru ve bağlama uygun cevaplar üretmesi sağlandı.

### Eklenen Yapı

- `DEFAULT_SYSTEM_PROMPT` içeriğine **Güvenilirlik ve Dürüstlük (Groundedness)** bölümü eklendi.
- Lina'nın uydurma (hallucination) yapmasını önlemek adına, özellikle proje bağlamı ("Project context" veya "Kaynak: git") verildiğinde yalnızca bu bağlamdaki bilgilere dayanarak cevap vermesi sıkı şekilde tembihlendi.
- Eski sürümde yer alan "proje hafızası veya git entegrasyonu olmadığı için" kısıtlaması kaldırıldı; yerine mevcut bağlamla senkronize kurallar getirildi.
- Promptu test eden `tests/brain/test_prompts.py` içeriği yeni kurallara göre güncellendi.

### Güvenlik Sınırları

- Dil bariyerleri ve kod alanlarındaki istisnalar korundu (örn. terminal komutlarının, class isimlerinin İngilizce kalması).
- "Erişimin yoksa dürüstçe belirt" ve "Bilmiyorsan kesin konuşma" yönergeleri daha belirgin hale getirildi.

### Completed Commits

- `fc07ecd feat: refine assistant prompts for reliability and groundedness`

### Test Results

- Prompt testleri dahil tüm testler başarıyla geçti: `194 passed`.

### Current Project Status

- Lina, proje bazlı soruları cevaplarken artık çok daha kararlı ve halüsinasyondan uzak yanıtlar verecek şekilde yönlendiriliyor.
- Geliştirilmiş prompt, son zamanlarda eklenen ContextManager (Git ve Doküman entegrasyonu) özellikleriyle tam uyumlu hale geldi.

### Sprint 18 Notu

Bir sonraki adım, Developer Experience v1: Dokümantasyon, README ve hızlı başlangıç rehberlerini iyileştirmektir.

## 2026-07-07 - Sprint 18

### Sprint Durumu

Sprint 18 tamamlandı.

Projenin dokümantasyonları ve geliştirici deneyimi, son zamanlarda eklenen `v2` özellikleri yansıtacak şekilde güncellendi.

### Eklenen Yapı

- `README.md` dosyasında bulunan "Project awareness yalnız izinli dokümanlarla sınırlıdır" veya "GUI minimal Tkinter arayüzüdür" gibi v1'den kalma, yeni özellikleri (Git entegrasyonu, Tool yetkilendirme altyapısı, GUI yenilikleri) göz ardı eden kısımlar güncellendi.
- `docs/roadmap.md` dosyasında tamamlanan aşamalar arasına `GUI v2`, `Project awareness v2` ve `Safe tool foundation v2 (PermissionDecision)` ifadeleri eklendi.
- `docs/smoke-test-checklist.md` dosyası güncellenerek, test adımlarına arayüzdeki "Durum Çubuğu", "Clear Chat" ve "Copy Last Response" özellikleri ile CLI üzerinden Git project awareness durumunu doğrulayan senaryolar eklendi.

### Güvenlik Sınırları

- Koda doğrudan etki edecek yeni bir özellik eklenmedi. Tüm çalışma izole olarak markdown dokümanları üzerinden yürütüldü.

### Completed Commits

- `6e8ad66 docs: improve developer experience and update outdated features`

### Test Results

- Herhangi bir kod değişmediği için otomatik test paketinin bozulması söz konusu değildir. Test sayısı korundu (194 passed).

### Current Project Status

- Projenin README, Yol Haritası ve Smoke Testleri kod tabanının güncel gerçeğiyle senkronize hale getirildi. Artık geliştiriciler ve projeye sonradan bakanlar için daha tutarlı bir durum söz konusu.

### Sprint 19 Notu

Bir sonraki adım, Regression & Test Hardening: Mevcut test suite'i genel olarak güçlendirmek ve edge case'leri sıkılaştırmaktır.

## 2026-07-07 - Sprint 19

### Sprint Durumu

Sprint 19 (Regression & Test Hardening) tamamlandı.

Yeni bir public özellik veya dependency eklenmeden, mevcut kritik sistemlerin (Conversation, Tool Execution, Context ve Bootstrap) hata yönetimi ve bağlama senaryoları (edge cases) test suite içine eklendi.

### Eklenen Yapı

- `test_conversation_service.py` içine `ContextManager` entegrasyonunu ve formatlama yeteneğini garanti altına alan test eklendi.
- `test_tool_execution_service.py` içine araç içi fırlatılan iç hataların (internal execution error) ToolExecutionService tarafından yakalanıp yutulmadığını, uygun şekilde yukarıya (bubble up) fırlatıldığını doğrulayan edge case eklendi.
- `tests/core/test_bootstrap.py` oluşturularak `create_application_services` fonksiyonunun config ayarlarını parse edip servisleri (`ConversationService`, `ContextManager`, `DiagnosticsService`) doğru timeout ve limitlerle bağladığını (wiring) doğrulayan test eklendi.

### Güvenlik Sınırları

- Hiçbir bağımlılık veya public özellik eklenmedi. Tüm çalışma sadece `tests/` klasörüyle sınırlandırıldı. 
- Mimari büyük bir refactor işlemi yapılmadı, mevcut testlerin kararlılığı korundu.

### Completed Commits

- `aaa638a test: harden test suite for edge cases and regressions`

### Test Results

- Test paketi sayısı artırılarak kapsam genişletildi ve `196 passed` durumuyla mevcut tüm davranışlar korundu.

### Current Project Status

- Projenin `v0.2.0-alpha` yapısı tüm özellikleri, testleri ve dokümantasyonlarıyla stabil hale getirildi. Artık sürüm duyurusu öncesi release hazırlıkları yapılabilir.

### Sprint 20 Notu

Bir sonraki adım, v0.3.0-alpha Release Prep: Dokümantasyon, sürüm notları ve son rötuşların yapılarak yeni stabil bir adıma geçilmesidir.

## 2026-07-07 - Sprint 20

### Sprint Durumu

Sprint 20 (v0.3.0-alpha Release Prep) tamamlandı.

Lina'nın yeni yeteneklerini yansıtan `v0.3.0-alpha` sürümü için gerekli tüm statik versiyon metinleri güncellendi ve release candidate hazırlandı.

### Eklenen Yapı

- `src/lina/interfaces/cli.py` içerisindeki CLI karşılama banner'ı `v0.3.0-alpha` olarak güncellendi.
- İlgili CLI ve Main testlerindeki beklenen sürüm logları (`tests/interfaces/test_cli.py`, `tests/test_main.py`) `v0.3.0-alpha` olarak güncellendi.
- `README.md`, `docs/roadmap.md` ve `docs/smoke-test-checklist.md` içindeki mevcut sürüm ibareleri `v0.3.0-alpha` yapıldı.

### Güvenlik Sınırları

- Sadece versiyon etiketleri güncellendi. Hiçbir yeni mantık veya paket (dependency) eklenmedi.

### Completed Commits

- `9adb709 chore: prepare v0.3.0-alpha release candidate`

### Test Results

- Sürüm etiketlerine bağlı olan testler dahil olmak üzere 196 testin tamamı sorunsuz çalışmaya devam ediyor.

### Current Project Status

- Lina, Project Awareness v2, GUI v2, Tool Execution Security (PermissionDecision) ve Hardened Test Suite ile birlikte yepyeni, kararlı bir kilometre taşına (v0.3.0-alpha) ulaşmış durumda. Hazır ve temiz bir zemin.

## 2026-07-07 - v0.3.0-alpha Release Polish

### Sprint Durumu

v0.3.0-alpha öncesi manuel GUI smoke testte görülen son kritik polish sorunları ele alındı.

### Major Architectural Decisions

- Yeni özellik, dependency veya büyük refactor eklenmedi.
- GUI mesaj render path içinde etiket normalizasyonu güçlendirildi; düzeltme yalnızca test helper seviyesinde bırakılmadı.
- Ollama generation ayarı mevcut provider tasarımının içinde daha muhafazakâr hale getirildi.
- Türkçe yanıt kalitesi prompt seviyesinde dar kapsamlı şekilde sıkılaştırıldı.

### Commits Completed Today

- `45f81d9 fix: polish release candidate behavior`

### Bugs Discovered

- GUI bazı gerçek akışlarda `Lina:Lina:` benzeri çift etiketli çıktı gösterebiliyordu.
- Model yanıtlarında Türkçe cümlelere yabancı kelime kırpıntıları karışabiliyordu.
- Genel provider hatası kullanıcıya yeterince ayrıştırılmış bir mesajla yansımayabiliyordu.

### Bugs Fixed

- `Lina:`, `Lina:Lina:`, `Lina: Lina:`, `Lina : Lina :` ve satır kırılmış tekrarlar gerçek `_append_message` render path içinde normalize edildi.
- Error response ve deterministic identity response için tek `Lina:` etiketi garantileyen regresyon testleri eklendi.
- Ollama generation `temperature` değeri `0.1` yapılarak daha sakin ve tutarlı yanıt üretimi hedeflendi.
- Genel `Ollama request failed` durumu için daha anlaşılır GUI hata mesajı eklendi.

### Runtime Issues Encountered

- Manuel GUI testte görülen çift etiket sorunu otomatik regresyon kapsamına alındı.
- Timeout değeri sonsuza çekilmedi; mevcut sınırlı timeout davranışı korundu.

### Lessons Learned

- GUI formatlama hataları yalnızca yardımcı fonksiyon testleriyle değil, gerçek append/render path üzerinden de doğrulanmalı.
- Prompt güvenilirliği ve generation ayarları küçük ama ölçülü değişikliklerle iyileştirilmeli; mimari bu tip polish işleri için gereksiz büyütülmemeli.

### Test Results

- `python -m pytest tests/interfaces/test_gui.py tests/integrations/test_ollama_provider.py tests/brain/test_prompts.py` -> `52 passed`
- `python -m pytest` -> `224 passed`

### Current Project Status

- v0.3.0-alpha release candidate için GUI etiket render path, Ollama hata ayrıştırması ve Türkçe yanıt güvenilirliği daha sağlam hale getirildi.
- Tag oluşturulmadı.

### Next Session Goals

- Manuel GUI smoke test yeniden çalıştırılmalı.
- Eğer manuel test temiz geçerse v0.3.0-alpha tag/release adımı ayrıca onayla başlatılmalı.

## 2026-07-08 - Gün Sonu Kapanışı - v0.3.0-alpha Tag

### Günün Kapanış Durumu

Bugün Sprint 19, Sprint 20 ve v0.3.0-alpha release hotfix/polish çalışmaları tamamlanmış kabul edildi. Bu kapanış, yeni özellik geliştirme veya refactor amacı taşımadı; mevcut durum test edildi, dokümante edildi ve alpha sürüm etiketi için hazırlanacak hale getirildi.

### Test Durumu

- Başlangıç kontrolünde `python -m pytest` çalıştırıldı.
- Son durumda `224 passed` sonucu alındı.
- Testler geçtiği için release tag adımına geçilmesi güvenli kabul edildi.

### Push Durumu

- `main` branch başlangıçta `origin/main` ile senkron durumdaydı.
- Gün sonu dokümantasyon commit’i sonrası `main` branch tekrar pushlanacaktır.

### v0.3.0-alpha Tag Durumu

- `v0.3.0-alpha` tag’i, testler geçtikten ve dokümantasyon güncellendikten sonra oluşturulacak alpha sürüm etiketi olarak planlandı.
- Bu sürüm bilinçli olarak alpha statüsündedir; bilinen sorunlar saklanmadan aşağıda listelenmiştir.

### Mevcut Yetenekler

- CLI üzerinden Lina ile konuşma.
- Tkinter tabanlı masaüstü GUI.
- Ollama local model entegrasyonu.
- `PromptBuilder` ile temel prompt üretimi.
- `IntentAnalyzer` ile minimal intent analizi.
- Deterministic responses ile bazı güvenli ve sabit yanıtlar.
- Session history.
- Runtime `ContextManager`.
- Project Awareness.
- Read-only Git context.
- Safe Tool Foundation.
- `ToolExecutionService`.
- Model diagnostics.

### Bilinen Sorunlar

- GUI’de bazı gerçek kullanıcı akışlarında `Lina:Lina:` çift etiket problemi hâlâ görülebiliyor olabilir.
- Türkçe LLM cevap kalitesi yerel modele bağlıdır ve hâlâ iyileştirme istemektedir.
- “Bir gün bilgisayarımı yönetebilecek misin?” gibi gelecek capability / bilgisayar kontrolü soruları için deterministic intent henüz eklenmemiştir; LLM bazen fazla iddialı cevap verebilir.
- Ollama timeout durumları kullanıcıya daha düzgün gösterilmektedir, ancak model performansı ve yavaşlık hâlâ kullanılan yerel modele bağlıdır.
- Kalıcı memory henüz yok.
- Speech, vision, camera, browser automation, Windows automation ve gerçek bilgisayar kontrolü henüz yok.

### Yarın İçin Önerilen İlk İşler

1. GUI actual render path label duplication sorununu kesin olarak düzeltmek.
2. Computer control / future capability soruları için deterministic response eklemek.
3. Türkçe response reliability polish çalışmasını sürdürmek.
4. Sonrasında `v0.3.1-alpha` veya `v0.3.0-alpha` hotfix değerlendirmesi yapmak.

## 2026-07-08 - Conversation Quality Polish

### Sprint Durumu

Lina'nın Türkçe konuşma kalitesini iyileştirmek için prompt, intent ve deterministic response tarafında dar kapsamlı polish çalışması yapıldı. Yeni dependency, büyük mimari refactor veya yeni capability eklenmedi.

### Yapılan Değişiklikler

- Default system prompt daha profesyonel, kısa ve yönlendirici hale getirildi.
- Doğal selamlaşma, samimiyet seviyesi, casual chat ve teknik konuşma ayrımı daha net yazıldı.
- `Selamlarsın`, `about`, `progressu`, `starting pointina`, `today'de`, `tentang`, `lavoro`, `algunos` gibi karışık veya çeviri kokan ifadeler açıkça yasaklandı.
- GUI zaten konuşmacı etiketini gösterdiği için modelin cevap başına `Lina:`, `İlhan:`, `Cevap:` veya `Yanıt:` prefix'i yazmaması gerektiği prompt içinde netleştirildi.
- `CASUAL_GREETING` intent eklendi.
- `selam`, `merhaba`, `naber`, `nasılsın`, `ne haber`, `günaydın`, `iyi geceler`, `iyi akşamlar` gibi basit selamlaşmalar LLM'e gitmeden kısa ve doğal deterministic cevapla karşılanır hale getirildi.
- Greeting eşleşmesi bilinçli olarak dar tutuldu; `selam, bir bug var`, `selam lina bugün projede ne yaptık` ve `merhaba bilgisayarımı yönetebilir misin` gibi anlamlı mesajlar greeting olarak yakalanmıyor.

### Test Sonucu

- İlgili testler: `84 passed`
- Tam test paketi: `243 passed`

### Bilinen Sınırlar

- Computer control / future capability soruları için ayrı deterministic intent bu sprintte eklenmedi; bu iş ayrı bir sprint konusu olarak bırakıldı.
- Türkçe yanıt kalitesi prompt ve deterministic greeting ile iyileştirildi, ancak LLM kullanılan serbest chat cevaplarında kalite hâlâ yerel modele bağlıdır.

### Sonraki Önerilen İş

Computer control / future capability soruları için küçük, deterministik ve dürüst bir intent/response akışı eklemek.

## 2026-07-08 - Roadmap Realignment & v0.3.1 Stabilization Gate

### Sprint Durumu

`v0.3.0-alpha` sonrası hotfix ve polish çalışmaları stabilization gate üzerinden değerlendirildi. Amaç küçük polish döngülerinde takılı kalmadan, release blocker / known issue / roadmap feature ayrımını netleştirmek ve Memory Capability v1'e geçiş zeminini hazırlamaktı.

### v0.3.0-alpha Sonrası Hotfix Durumu

- GUI typing placeholder silme akışı düzeltildi.
- GUI label duplication için gerçek render path regresyon testleri mevcut.
- Türkçe conversation style prompt seviyesinde iyileştirildi.
- `CASUAL_GREETING` intent ile basit selamlaşmalar LLM'e gitmeden cevaplanıyor.
- Bilgisayar kontrolü / future capability soruları için güvenli deterministic status cevabı eklendi.

### Release Policy Kararı

Roadmap içine üçlü ayrım eklendi:

- Release blocker: Uygulamayı bozan, çökerten, yanlış vaat veren veya güvenlik riski oluşturan sorunlar.
- Known issue: Kullanımı engellemeyen kalite veya UX eksikleri.
- Roadmap feature: Yeni capability veya büyük geliştirme.

Bu ayrım, küçük kalite eksiklerinin ana milestone ilerleyişini gereksiz yere durdurmaması için eklendi.

### Roadmap Realignment

Roadmap güncel durum olarak `v0.3.1-alpha` stabilization hotfix adayına taşındı. Hedef sürüm hattı şu şekilde netleştirildi:

- `v0.3.1-alpha`: Stabilization hotfix.
- `v0.4.0-alpha`: Memory Capability v1.
- `v0.4.1-alpha`: Memory UX / Recall polish.
- `v0.5.0-alpha`: Files Capability v1.
- `v0.6.0-alpha`: Speech Capability v1.
- `v0.7.0-alpha`: Vision / Screen Awareness v1.
- `v0.8.0-alpha`: Safe Windows Automation v1.

### Memory v1 Hazırlığı

Memory Capability v1 için kapsam dokümante edildi:

- Local-first.
- SQLite.
- Kalıcı conversation summary.
- User preference memory.
- Project decision memory.
- `MemoryService`.
- `MemoryRepository`.
- Explicit memory operations.
- Privacy-first.
- Hassas bilgileri kullanıcı istemeden saklamama.
- Forget/delete capability için ileride genişletilebilir zemin.

Kapsam dışı alanlar da netleştirildi: vector database, embeddings, cloud sync, multi-user memory, autonomous monitoring, sensitive personal data auto-save ve agent memory planning.

### Test Sonucu

- Başlangıç testi: `243 passed`
- Stabilization gate sonrası final test: `250 passed`

### Sonraki Ana İş

Bir sonraki ana geliştirme hattı `v0.4.0-alpha - Memory Capability v1` olmalıdır. `v0.3.1-alpha` tag kararı için önce manuel smoke test çalıştırılmalıdır.

## 2026-07-08 - Memory Capability v1

### Sprint Durumu

`v0.4.0-alpha` hattı kapsamında Lina'ya ilk local-first, SQLite tabanlı ve explicit komutlarla çalışan kalıcı hafıza altyapısı eklendi. Bu çalışma yeni dependency eklemeden, Python standard library `sqlite3` kullanılarak tamamlandı.

### Eklenen Yapı

- `MemoryType` ve `MemoryRecord` modelleri eklendi.
- SQLite-backed `MemoryRepository` eklendi.
- `MemoryService` eklendi.
- Explicit memory intents eklendi:
  - `MEMORY_REMEMBER`
  - `MEMORY_RECALL`
  - `MEMORY_LIST`
  - `MEMORY_FORGET`
  - `MEMORY_CLEAR`
- Memory commands `ConversationService` içinde deterministic olarak işlendi.
- Memory command'leri Brain/Ollama çağırmadan cevaplanır hale getirildi.
- Memory responses session history'ye normal conversation turn olarak eklenir hale getirildi.
- `ConversationContext` içine `memory_context` eklendi.
- `ContextManager`, MemoryService üzerinden sınırlı memory context üretebilir hale getirildi.
- `PromptBuilder`, memory context varsa prompt'a ayrı ve güvenli bir bölüm olarak ekler hale getirildi.
- Bootstrap içinde MemoryRepository / MemoryService wiring eklendi.
- GUI ve CLI aynı bootstrap üzerinden memory altyapısını kullanır hale getirildi.

### Config

`config/default.toml` içine `[memory]` bölümü eklendi:

- `enabled`
- `database_path`
- `max_context_items`
- `max_context_characters`

Varsayılan database yolu `data/lina_memory.sqlite3` olarak belirlendi. `data/*` zaten `.gitignore` kapsamında olduğu için runtime SQLite dosyaları Git'e eklenmez.

### Privacy ve Safety

- Memory v1 yalnız explicit memory komutlarıyla kayıt yapar.
- Hassas bilgi otomatik kaydedilmez.
- LLM ile memory extraction yapılmaz.
- Vector database, embeddings, cloud sync ve autonomous monitoring eklenmedi.
- Forget ve clear komutları deterministic çalışır.

### Bilinen Sınırlar

- Memory v1 semantic search yapmaz.
- Memory v1 kullanıcı profili çıkarımı yapmaz.
- Memory v1 agent memory planning içermez.
- Memory UX / Recall polish sonraki `v0.4.1-alpha` hattına bırakıldı.

### Test Sonucu

- İlgili memory repository/service testleri: `10 passed`
- Memory intent ve conversation routing testleri: `92 passed`
- Prompt/context integration testleri: `38 passed`
- Settings/bootstrap testleri: `21 passed`
- Tam test paketi: `294 passed`

### Sonraki Ana İş

Manuel GUI/CLI smoke test sonrası `v0.4.0-alpha` tag değerlendirmesi yapılmalıdır. Sonraki geliştirme hattı `v0.4.1-alpha - Memory UX / Recall polish` olmalıdır.

## 2026-07-08 - Memory GUI Hang Hotfix

### Sorun

Memory komutları CLI ve normal service akışında çalışırken GUI içinde `Yazıyor...` placeholder durumunda takılı kalabiliyordu.

Örnek:

```text
bunu hatırla: kısa cevapları seviyorum
```

GUI'de cevap gelmeden şu durumda kalabiliyordu:

- `Lina: Yazıyor...`
- Status: `Cevap bekleniyor...`

### Kök Neden

İki riskli nokta tespit edildi:

- GUI background worker yalnız `ModelProviderError` yakalıyordu. Memory/SQLite gibi beklenmeyen bir hata olursa worker thread sessizce sonlanabiliyor ve UI resetlenmiyordu.
- `MemoryRepository` SQLite connection'ı bootstrap sırasında ana thread'de oluşturuluyor, GUI response generation ise background thread'de çalışıyordu. Bu SQLite thread kısıtı nedeniyle memory komutlarında hata üretebilecek bir akıştı.

### Düzeltme

- GUI response worker beklenmeyen exception durumlarını da yakalar hale getirildi.
- Beklenmeyen hata durumunda `Yazıyor...` placeholder temizlenir, kullanıcı dostu hata mesajı gösterilir, input ve gönder butonu yeniden aktifleşir, status `Hata oluştu` durumuna döner.
- Hata `logging.exception` ile loglanır.
- `MemoryRepository` SQLite connection'ı `check_same_thread=False` ile açıldı ve repository operasyonları lock ile korunur hale getirildi.

### Testler

- GUI hızlı deterministic memory response aldığında bekleme durumundan çıkıyor.
- GUI beklenmeyen exception aldığında placeholder temizleniyor ve status takılı kalmıyor.
- MemoryRepository temp SQLite database ile worker thread benzeri kullanımda çalışıyor.
- Tam test paketi: `299 passed`

### Durum

Memory komutlarının GUI'de `Yazıyor...` durumunda takılı kalmasına yol açan ana thread/worker thread riski kapatıldı.

## 2026-07-08 - Memory Duplicate Prevention Hotfix

### Sorun

Memory v1 içinde aynı explicit bilgi tekrar tekrar kaydedilebiliyordu.

Örnek:

```text
bunu hatırla: kısa cevapları seviyorum
bunu hatırla: kısa cevapları seviyorum
```

Bu akış ikinci komutta yeni kayıt oluşturmamalıdır.

### Düzeltme

- Aynı active memory content tekrar kaydedilmez hale getirildi.
- Duplicate kontrolü `MemoryService` içinde normalize edilmiş content üzerinden yapılır.
- Büyük/küçük harf farkları duplicate sayılır.
- Baş/son boşluk ve birden fazla boşluk farkları duplicate sayılır.
- Semantic similarity, embedding, fuzzy matching veya LLM comparison eklenmedi.
- Forget sonrasında aynı bilgi tekrar kaydedilebilir.

### Kullanıcıya Dönen Cevap

Duplicate durumda Lina şu kısa deterministic cevabı döndürür:

```text
Bunu zaten hatırlıyorum İlhan.
```

### Test Sonucu

- İlgili memory/conversation testleri: `35 passed`
- Tam test paketi: `307 passed`

### Durum

Memory v1, `v0.4.0-alpha` tag için duplicate prevention hotfix ile daha stabil hale getirildi.

## 2026-07-09 - Memory UX / Recall Polish + GUI Input History

### Amaç

`v0.4.1-alpha` hattında Memory v1'in kullanıcı deneyimini iyileştirmek ve GUI içinde terminal benzeri input history davranışı eklemek hedeflendi.

### Yapılanlar

- Memory recall/list cevapları numaralı liste formatına taşındı.
- Boş memory recall cevabı daha doğal ve kişisel hale getirildi.
- Forget ve clear cevapları daha açık Türkçe ifadelerle güncellendi.
- Aynı içerik farklı büyük/küçük harf veya boşluk kullanımıyla unutulmak istendiğinde normalize edilmiş eşleşme yapılır hale getirildi.
- Sensitive memory guard eklendi; şifre, token, API key, kimlik ve ödeme bilgisi gibi hassas içerikler memory içine kaydedilmez.
- GUI input history eklendi; mesaj alanında `↑` önceki mesajları, `↓` daha yeni mesajları getirir.
- GUI input history session-only tasarlandı; SQLite memory sistemiyle karıştırılmadı.
- Help/capabilities cevapları explicit memory komutlarını kısa şekilde gösterecek biçimde güncellendi.

### Mimari Notlar

- Memory UX iyileştirmeleri `ConversationService` ve `MemoryService` sınırları içinde tutuldu.
- Yeni dependency eklenmedi.
- Memory için vector database, embedding veya otomatik memory extraction eklenmedi.
- GUI input history yalnızca arayüz state'i olarak tutuldu; business logic veya kalıcı memory katmanına taşınmadı.

### Test Sonucu

- Memory service ve conversation service testleri: `40 passed`
- GUI testleri: `47 passed`
- Deterministic response ve conversation service testleri: `36 passed`
- Tam test paketi: `321 passed`

### Durum

`v0.4.1-alpha` için Memory UX / Recall polish ve GUI input history geliştirmeleri tamamlandı. Manuel smoke test sonrası tag değerlendirmesi yapılabilir.

## 2026-07-09 - Files Capability v1

### Amaç

`v0.5.0-alpha` hattında Lina'ya genel dosya sistemi erişimi vermeden, yalnızca izinli proje dosyalarını read-only okuyabilen güvenli bir Files Capability v1 eklemek hedeflendi.

### Yapılanlar

- `FileAccessService` eklendi.
- Sabit ve küçük bir allowlist tanımlandı.
- `README.md`, `contributing.md` ve izinli `docs/*.md` dosyaları için read-only erişim sağlandı.
- Alias desteği eklendi: `readme`, `roadmap`, `development log`, `release notes v0.4.1` gibi ifadeler izinli dosyalara çözümlenir.
- Absolute path istekleri reddedilir hale getirildi.
- `../` ve backslash tabanlı path traversal istekleri reddedilir hale getirildi.
- Unknown veya allowlist dışı dosya istekleri Brain/Ollama çağrılmadan güvenli cevapla reddedilir.
- `FILE_LIST_ALLOWED`, `FILE_READ`, `FILE_SUMMARIZE` ve `FILE_CAPABILITIES` intentleri eklendi.
- `FILE_READ`, Brain/Ollama çağırmadan güvenli preview döndürür.
- `FILE_SUMMARIZE`, yalnız allowlisted dosya okunduktan sonra dosya context'ini Brain'e verir.
- File context `PromptBuilder` içinde ayrı bir bölüm olarak eklendi.
- Help/capabilities cevapları Files v1 sınırlarını ve örnek komutları gösterecek şekilde güncellendi.
- GUI normal chat render path'i file command response için regression test ile korundu.

### Güvenlik Sınırları

- Genel dosya sistemi erişimi eklenmedi.
- Proje dışı dosya erişimi eklenmedi.
- Dosya yazma, silme, taşıma, rename veya copy capability eklenmedi.
- Shell command execution eklenmedi.
- LLM tool-calling veya LLM'in kendi başına dosya seçmesi eklenmedi.
- Yeni dependency eklenmedi.

### Test Sonucu

- FileAccessService testleri: `14 passed`
- Intent testleri: `89 passed`
- Prompt/context testleri: `20 passed`
- Conversation/bootstrap/file service testleri: `51 passed`
- Deterministic response ve conversation service testleri: `44 passed`
- GUI testleri: `48 passed`

### Bilinen Eksikler

- Files v1 semantic file search yapmaz.
- Allowlist config üzerinden yönetilmiyor; v1 için kod içinde sabit tutuluyor.
- Genel dosya capability yoktur.
- Dosya yazma veya düzenleme yoktur.
- Büyük dosyalar yalnız limitli context/preview olarak kullanılır.

### Durum

Files Capability v1 uygulandı. Final tam test ve manuel smoke test sonrasında `v0.5.0-alpha` tag değerlendirmesi yapılabilir.

## 2026-07-09 - Files Summarize Model Fallback Hotfix

### Sorun

GUI içinde `roadmap dosyasını özetle` komutu dosyayı başarıyla okuyordu, ancak bazı durumlarda `Dosyayı okuyabildim ama özetlemek için yerel modele bağlı değilim` fallback cevabına düşebiliyordu.

### Düzeltme

- `FILE_SUMMARIZE` akışında Brain'e gönderilen kullanıcı mesajı daha açık bir dosya özetleme talimatına dönüştürüldü.
- File context aynı şekilde yalnız `FileAccessService` tarafından güvenli şekilde oluşturulmaya devam eder.
- `ModelProviderError` fallback'i daraltıldı; yalnız gerçek model unavailable durumlarında preview fallback döner.
- Timeout gibi bağlantı-dışı provider hataları artık yanlış şekilde `yerel modele bağlı değilim` diye etiketlenmez.

### Doğrulama

- `ollama list` içinde `llama3.2:3b` modelinin yüklü olduğu görüldü.
- Gerçek servis çağrısıyla `roadmap dosyasını özetle` komutunun fallback'e düşmeden model cevabı döndürdüğü doğrulandı.
- Tam test paketi: `366 passed`

### Durum

Files summarize akışı artık Ollama kullanılabilirken model cevabını döndürür. Ollama gerçekten erişilemezse güvenli preview fallback davranışı korunur.

## 2026-07-09 - Files Summary Grounding Hotfix

### Sorun

Manuel GUI testte `selam naber` sonrasında `roadmap dosyasını özetle` komutu dosya içeriğini özetlemek yerine önceki casual greeting akışına benzeyen alakasız bir cevap üretebiliyordu.

### Düzeltme

- `FILE_SUMMARIZE` prompt'u dosya özetleme görevine özel ve daha kompakt hale getirildi.
- File context prompt içinde birincil kaynak olarak güçlendirildi.
- Dosya özetleme sırasında selamlama, sohbet sorusu ve meta başlık üretimi engellendi.
- `FILE_SUMMARIZE` sırasında önceki casual conversation history'sinin modeli saptırması engellendi.
- `selam naber` sonrası `roadmap dosyasını özetle` regression testi eklendi.

### Test Sonucu

- Hedefli testler: `136 passed`
- Tam test paketi: `368 passed`

### Durum

Files summary akışı artık dosya bağlamını birincil kaynak olarak kullanacak şekilde daha güçlü biçimde yönlendiriliyor. `v0.5.0-alpha` tag öncesi manuel smoke test önerilir.

## 2026-07-09 - Files Path Traversal Security Hotfix

### Sorun

Manuel smoke testte `../README.md dosyasını oku` gibi path traversal içeren dosya isteklerinin, alias çözümleme sırasına bağlı olarak güvenli biçimde reddedilmeden allowlisted `README.md` dosyasına eşleşebilme riski görüldü.

Ayrıca uzun sohbetlerde conversation history büyüdükçe model prompt'unun gereksiz şekilde şişebildiği ve bazı cevap kalitesi/stabilite sorunlarına zemin hazırlayabildiği değerlendirildi.

### Düzeltme

- `FileAccessService`, alias çözümlemeden önce traversal ve absolute path sözdizimini reddedecek şekilde güçlendirildi.
- `ConversationService`, dosya referansı çıkarırken yasaklı path ifadelerini önce güvenlik kontrolüne yönlendirecek şekilde dar kapsamlı güncellendi.
- `IntentAnalyzer`, `C:/...` ve `../...` gibi path benzeri dosya okuma isteklerini genel sohbet yerine dosya akışında tutacak şekilde düzeltildi.
- Uzun conversation history alanları `PromptBuilder` içinde sınırlandırıldı; mevcut kullanıcı mesajı korunurken eski çok uzun mesajlar prompt içinde kısaltılıyor.

### Regression Testleri

- Traversal path istekleri alias çözümlemeden önce reddediliyor.
- Absolute Windows path istekleri Brain çağrılmadan güvenli dosya hatasıyla sonuçlanıyor.
- Yasaklı dosya okuma istekleri intent seviyesinde `FILE_READ` akışında kalıyor.
- Uzun conversation history alanları prompt içinde tam metin olarak taşınmıyor.

### Test Sonucu

- Hedefli testler: `161 passed`
- PromptBuilder hedefli testleri: `12 passed`
- Tam test paketi: `379 passed`

### Durum

Files v1 güvenlik sınırı path traversal ve absolute path denemelerine karşı daha net hale getirildi. Uzun sohbetlerde prompt büyümesini azaltan küçük stabilizasyon eklendi. Tag oluşturulmadı.

## 2026-07-09 - Professional Chat UI Refresh

### Amaç

`v0.5.1-alpha` hattında mevcut Tkinter GUI daha profesyonel bir sohbet uygulaması görünümüne taşındı. Bu sprint yalnızca GUI/UX yenileme kapsamındadır; Brain, Memory, Files, Tool, Ollama, Settings ve Core mimarisi değiştirilmedi.

### Yapılanlar

- Sol sidebar eklendi.
- `Yeni Sohbet` butonu mevcut oturumu temizleyen güvenli davranışa bağlandı.
- Ana chat alanı bubble-based layout'a taşındı.
- Lina mesajları sol tarafta, kullanıcı mesajları sağ tarafta gösterilecek şekilde ayrıştırıldı.
- Alt composer modernleştirildi.
- `+`, `Mic` ve `Screen` placeholder action butonları eklendi.
- Placeholder action butonları gerçek capability başlatmadan Lina mesajı olarak güvenli bilgilendirme gösterir.
- `Enter` ile gönderme, GUI input history, typing placeholder cleanup, status bar, model response background thread, error handling, Clear Chat ve Copy Last Response davranışları korundu.
- Memory ve Files komut akışlarına dokunulmadı.

### Test Sonucu

- GUI hedefli testler: `50 passed`
- Tam test paketi: `381 passed`

### Durum

Professional Chat UI Refresh tamamlandı. `v0.5.1-alpha` tag'i oluşturulmadı; manuel GUI smoke testten sonra ayrıca değerlendirilecektir.

## 2026-07-10 - Branding Polish

### Amaç

Professional Chat UI içine Lina logosunu güvenli ve küçük kapsamlı bir GUI/branding polish olarak eklemek.

### Yapılanlar

- `assets/branding/lina-logo.png` ve `assets/branding/lina-icon.png` proje içine eklendi.
- GUI için logo/icon yükleme helper'ı eklendi.
- Pencere icon'u destekleniyorsa `lina-icon.png` ile ayarlanır.
- Sidebar üst kısmında logo için branding alanı oluşturuldu.
- Logo dosyası yoksa veya yüklenemezse GUI metin başlıkla güvenli şekilde açılmaya devam eder.
- Brain, Memory, Files, Tool, Ollama, Settings ve Core logic değiştirilmedi.

### Test Sonucu

- GUI hedefli testler: `53 passed`
- Tam test paketi: `384 passed`

### Durum

Branding Polish tamamlandı. Tag oluşturulmadı.

## 2026-07-10 - Day-End Close - v0.5.x GUI and Branding Stabilization

### Kapanan Çalışmalar

- `v0.5.0-alpha` Files Capability v1 taglendi.
- Files Capability v1 içinde read-only allowlisted file access tamamlandı.
- File summary fallback ve grounding bugları kapatıldı.
- Path traversal güvenlik bug'ı kapatıldı.
- Prompt history bounding eklendi.
- `v0.5.1-alpha` Professional Chat UI Refresh taglendi.
- GUI modern koyu temaya geçti.
- Sidebar, chat bubbles, composer ve placeholder action buttons eklendi.
- `v0.5.2-alpha` Branding Polish adayı hazırlandı.
- `assets/branding/lina-logo.png` ve `assets/branding/lina-icon.png` projeye dahil edildi.
- GUI sidebar branding ve window icon fallback desteği eklendi.

### Test Sonucu

- Tam test paketi: `384 passed`

### Durum

`v0.5.x` hattı Files Capability v1, Professional Chat UI Refresh ve Branding Polish çalışmalarını kapsayacak şekilde kapatılmaya hazırdır. `v0.5.1-alpha` tag'ine dokunulmadı ve taşınmadı.

### Sonraki Büyük Hedef

Sıradaki büyük hedef `v0.6.0-alpha` Speech Capability v1 olacaktır. Speech geliştirmesine geçmeden önce kısa bir Speech Architecture & Safety Planning sprinti yapılmalıdır.

## 2026-07-10 - Speech Architecture & Safety Planning

### Amaç

`v0.6.0-alpha` Speech Capability v1 implementation başlamadan önce speech kapsamı, güvenlik sınırları, GUI Mic butonu davranışı, dependency politikası ve test stratejisi planlandı.

### Alınan Kararlar

- Always-on listening yasaklandı.
- Mikrofon erişiminin yalnız explicit user action ile başlaması planlandı.
- Ses verisinin varsayılan olarak kaydedilmemesi ilkesi belirlendi.
- Local-first speech yaklaşımı önceliklendirildi.
- Speech engine yoksa graceful fallback davranışı tanımlandı.
- GUI içinde mikrofon aktifken net visual status gösterilmesi gerektiği yazıldı.
- SpeechService, STTProvider ve TTSProvider taslak sorumlulukları planlandı.
- `IDLE`, `LISTENING`, `TRANSCRIBING`, `SPEAKING`, `ERROR` ve `UNAVAILABLE` speech state modeli tanımlandı.
- İlk implementation için `Push-to-talk STT skeleton + optional no-op TTS interface` önerildi.

### Kapsam Dışı

- Mikrofon erişimi eklenmedi.
- Ses kaydı alınmadı.
- STT/TTS implementation yapılmadı.
- Yeni dependency eklenmedi.
- Always-on listening tasarlanmadı.

### Test Sonucu

- Tam test paketi: `384 passed`

### Durum

Speech capability için mimari ve güvenlik planı hazırlandı. Implementation'a geçmeden önce TTS/STT önceliği, local-only zorunluluğu, yeni dependency izni ve transcription UX kararı kullanıcıyla netleştirilmelidir.

## 2026-07-10 - Speech Skeleton + GUI Mic Flow

### Yapılanlar

- `SpeechService` ve speech state modeli eklendi.
- STT/TTS provider sözleşmeleri ile güvenli `NoOpSTTProvider` ve `NoOpTTSProvider` varsayılanları eklendi.
- GUI içindeki `Mic` butonu placeholder davranışından çıkarılıp `SpeechService` akışına bağlandı.
- Kullanılabilir bir STT provider olduğunda transkripsiyon background thread üzerinde çalışacak ve sonuç otomatik gönderilmeden input alanına yazılacak şekilde tasarlandı.
- Unavailable, boş sonuç ve provider exception yollarında GUI kontrollerinin ve status bilgisinin güvenli biçimde sıfırlanması sağlandı.
- Bootstrap, SpeechService'i NoOp sağlayıcılarla oluşturup yalnız GUI'ye aktarıyor; CLI davranışı değiştirilmedi.

### Güvenlik Sınırları

- Gerçek mikrofon erişimi ve ses kaydı eklenmedi.
- STT/TTS engine veya yeni dependency eklenmedi.
- Always-on listening, background recording, cloud speech ve otomatik mesaj gönderme yoktur.
- Testler gerçek cihaz veya mikrofon izni gerektirmez.

### Test Sonucu

- Speech unit testleri: `10 passed`
- Hedefli Speech/GUI/bootstrap testleri: `71 passed`
- Tam test paketi: `399 passed`

### Durum

`v0.6.0-alpha` Speech Skeleton + GUI Mic Flow tamamlandı. Gerçek STT engine seçimi ve dependency kararı `v0.6.1-alpha` öncesinde ayrı bir mimari ve güvenlik değerlendirmesi gerektirir.

## 2026-07-10 - Local Push-to-Talk STT Integration

### Yapılanlar

- Runtime dependency olarak yalnız `faster-whisper` ve `sounddevice` eklendi.
- `SoundDeviceAudioRecorder`, sınırlandırılmış mono kaydı kalıcı dosya oluşturmadan bellekte WAV verisine dönüştürecek şekilde eklendi.
- Sessizlik algılama, maksimum kayıt süresi ve kullanıcı kontrollü stop desteği eklendi.
- `FasterWhisperSTTProvider`, lazy model loading ve fake model factory ile test edilebilir biçimde eklendi.
- Varsayılan STT ayarları multilingual `base`, `tr`, `cpu` ve `int8` olarak belirlendi.
- `SpeechService` akışı `IDLE -> LISTENING -> TRANSCRIBING -> IDLE` olarak genişletildi; duplicate kayıt engellendi.
- GUI Mic butonu kayıt/durdurma durumlarına bağlandı; transkripsiyon mevcut taslağın sonuna ekleniyor ve otomatik gönderilmiyor.
- Pencere aktif kayıt sırasında kapanırsa recorder'ın durdurulması ve geç GUI callback'lerinin atlanması sağlandı.

### Privacy ve Güvenlik

- Always-on listening ve kullanıcı eylemi olmadan kayıt yoktur.
- Ham ses yalnız bellekte işlenir; temp veya kalıcı ses dosyası oluşturulmaz.
- Ham ses ve transcription debug loglarına yazılmaz.
- Cloud speech, CUDA, TTS ve otomatik mesaj gönderme eklenmedi.

### Test Sonucu

- Hedefli Speech/GUI/bootstrap testleri: `94 passed`
- Tam test paketi: `430 passed`
- Otomatik testlerde gerçek mikrofon açılmadı ve gerçek model indirilmedi.

### Bilinen Sınırlamalar

- İlk kullanımda `base` modelin indirilmesi ve hazırlanması zaman alabilir.
- Transcription hızı ve kalitesi CPU performansına, mikrofona ve ortam gürültüsüne bağlıdır.
- TTS, wake word, cihaz seçimi ve ses ayarı GUI'si henüz yoktur.

## 2026-07-10 - Speech Input Injection Hotfix

### Sorun ve Kök Neden

Gerçek mikrofon testinde transcription başarıyla üretilmesine rağmen disabled durumdaki Tkinter `Text` widget üzerinde `delete` ve `insert` işlemleri sessizce uygulanmıyordu. Exception oluşmadığı için input boş kalırken başarı mesajı gösteriliyordu. Önceki test, gerçek `_set_input_text` yolunu lambda ile değiştirdiği için bu davranışı yakalamıyordu.

### Düzeltme

- Transcription Tkinter ana thread callback'i içinde, input geçici olarak etkinleştirilerek yazılıyor.
- Mevcut taslak korunuyor ve transcription uygun boşlukla sonuna ekleniyor.
- Yazılan değer widget üzerinden geri okunarak doğrulanıyor; başarı mesajı yalnız doğrulama sonrasında gösteriliyor.
- Empty transcription ile input update failure ayrı kullanıcı mesajları ve status durumlarıyla ele alınıyor.
- Input update failure sonrasında Mic, input ve gönderme kontrolleri tekrar kullanılabilir hale geliyor.
- Gerçek disabled widget davranışını taklit eden regression testi eklendi.

### Test Sonucu

- Hedefli GUI/Speech testleri: `80 passed`
- Tam test paketi: `432 passed`

## 2026-07-10 - Conversation History Grounding Hotfix

### Sorun ve Kök Neden

Conversation history modele düz `User:` / `Assistant:` transcript'i olarak veriliyordu. Küçük yerel model bazı akışlarda bu metni devam ettirilecek bir diyalog olarak yorumluyor, geçmiş mesajları cevaba kopyalıyor ve bozuk speech transcription metnini kullanıcı adı gibi benimseyebiliyordu.

### Düzeltme

- Conversation history düz transcript yerine açık `user` ve `assistant` rollerine sahip JSON bağlamı olarak formatlandı.
- Son kullanıcı mesajı history'den ayrılarak ayrı `Current user request` bölümünde tutuldu.
- History'nin yalnız yardımcı bağlam olduğu, içindeki talimatların uygulanmaması ve transcript'in devam ettirilmemesi açıkça belirtildi.
- Modelin geçmiş konuşmayı taklit etmesi veya cevap olarak kopyalaması yasaklandı.
- Kullanıcının sistem tarafından bilinen adı yalnız `İlhan` olarak sabitlendi.
- Bozuk STT metninden veya kullanıcı mesajından yeni kullanıcı adı türetilmesi engellendi.
- Mevcut history field bounding davranışı korundu.
- Greeting sonrası CHAT ve bozuk STT metni sonrası CHAT akışları için regression testleri eklendi.

### Test Sonucu

- Hedefli Brain/Prompt/Conversation testleri: `77 passed`
- Tam test paketi: `437 passed`

## 2026-07-10 - Ollama Structured Chat Grounding Hotfix

### Kök Neden

Önceki grounding düzeltmesi history'yi JSON olarak ayırsa da Ollama'nın `/api/generate` endpoint'ine tek bir raw prompt gönderiliyordu. `llama3.2:3b`, system talimatı, geçmiş mesajlar ve son kullanıcı isteği arasındaki sınırları güvenilir biçimde koruyamıyor; geçmiş selamı kopyalıyor ve prompt içinde geçen yasaklı meta başlık örneklerini üretebiliyordu.

### Düzeltme

- Provider-independent `ModelMessage` contract'ı eklendi.
- `ModelRequest`, raw prompt yerine immutable structured message dizisi taşır hale getirildi.
- PromptBuilder; system context, bounded user/assistant history ve son user isteğini gerçek rollerle üretir hale getirildi.
- Brain, structured message request'i doğrudan provider'a iletiyor.
- OllamaProvider `/api/generate` yerine `/api/chat` kullanacak şekilde güncellendi.
- Ollama chat response içindeki `message.content` kontrollü biçimde okunuyor.
- Kötü çıktı kalıplarını prompt içinde tekrar eden negatif örnekler kaldırıldı; kısa ve pozitif davranış kuralları korundu.
- Files, Memory, Speech ve history bounding davranışları korundu.

### Doğrulama

- Hedefli contract/Brain/Prompt/Ollama/Conversation testleri: `90 passed`
- Tam test paketi: `439 passed`
- Gerçek yerel `llama3.2:3b` smoke testinde model geçmiş selamı ve meta başlığı tekrarlamadan son kullanıcı isteğine doğrudan cevap verdi.
- Cevap çıktısına filtre veya post-processing uygulanmadı.

## 2026-07-10 - Professional UI, Readability & Accessibility Polish

### Yapılanlar

- Windows'ta Tk root oluşturulmadan önce güvenli DPI awareness fallback zinciri eklendi.
- Tk scaling değeri ekran DPI bilgisine göre güvenli sınırlar içinde ayarlanır hale getirildi.
- `Segoe UI Variable`, `Segoe UI`, `Arial` ve `TkDefaultFont` sırasını kullanan font fallback sistemi eklendi.
- Dağınık GUI renkleri, yüksek kontrastlı semantik koyu tema sabitlerinde toplandı.
- Sidebar, header, chat alanı ve composer responsive yerleşim için yenilendi.
- Sidebar daraltma/genişletme, dürüst mevcut oturum görünümü ve deterministik session başlığı eklendi.
- Mesaj balonlarına saat ve mesaj başına kopyalama aksiyonu eklendi; uzun mesaj wrap değeri pencere genişliğine bağlandı.
- Kullanıcı eski mesajları okurken scroll konumunu koruyan, yalnız alt bölgeye yakınken çalışan auto-scroll davranışı eklendi.
- Composer placeholder, boş mesajda disabled gönderme durumu, `Enter` / `Shift+Enter`, `Ctrl+L`, `Ctrl+N` ve `Ctrl+K` davranışları eklendi.
- `+`, `Mic`, `Screen` ve `Gönder` kontrollerine dependency gerektirmeyen tooltip desteği eklendi.
- Oturum içi `A−` / `A+` font boyutu kontrolleri `9–16` sınırlarıyla eklendi.
- Memory, Files, Speech, structured Ollama chat ve background thread davranışları değiştirilmeden korundu.

### Test Sonucu

- Hedefli GUI testleri: `84 passed`
- Tam test paketi: `459 passed`
- Testlerde gerçek Ollama, mikrofon veya Tkinter mainloop başlatılmadı.

## 2026-07-10 - README Refresh for v0.6.2-alpha

- README güncel capability'lere ve `v0.6.2-alpha` release durumuna göre yenilendi.
- Memory, Files, Speech, Structured Chat ve Professional GUI bölümleri güncellendi.
- Kurulum, çalıştırma, gerçek konfigürasyon anahtarları, güvenlik sınırları, roadmap ve bilinen sınırlamalar netleştirildi.
- Lina logosu repository-relative asset yoluyla README üst bölümüne eklendi.
- Final test sonucu: `459 passed`.

## 2026-07-11 - PySide6 Desktop UI Migration

### Yapılanlar

- Runtime dependency olarak `PySide6`, development dependency olarak `pytest-qt` eklendi.
- `python gui.py` varsayılan akışı PySide6 GUI launcher'a taşındı.
- Eski Tkinter GUI silinmedi ve geçici legacy fallback olarak korundu.
- PySide6 tabanlı `LinaMainWindow`, sidebar, header, chat area, composer, status alanı ve worker altyapısı eklendi.
- Conversation gönderimi, typing placeholder temizleme, assistant label normalization ve hata durumunda UI reset davranışı PySide6 render path içinde test edildi.
- Model diagnostics ve speech status bilgileri PySide6 arayüzüne bağlandı.
- Mic akışı transkripsiyonu composer input alanına yazar; otomatik gönderme davranışı eklenmedi.
- Input history, yeni sohbet, son cevabı kopyalama ve oturum içi font boyutu kontrolleri PySide6 arayüzünde desteklendi.

### Mimari Kararlar

- Migration yalnız `interfaces` katmanında tutuldu.
- Brain, Ollama `/api/chat`, Memory, Files, Speech ve core bootstrap davranışları değiştirilmedi.
- Legacy Tkinter GUI kısa vadeli fallback olarak korunur; birincil masaüstü geliştirme yönü PySide6 olacaktır.
- GUI testleri gerçek model, mikrofon veya event loop başlatmadan fake servisler ve `pytest-qt` ile çalışır.

### Test Sonucu

- PySide6 hedefli testler: `15 passed`
- Entrypoint + PySide6 hedefli testler: `17 passed`
- Tam test paketi: `474 passed`

### Durum

`v0.6.3-alpha` PySide6 Desktop UI Migration kod tarafında tamamlandı. Tag oluşturulmadı. Sıradaki adım manuel PySide6 GUI smoke testi ve ardından release değerlendirmesidir.

## 2026-07-11 - PySide6 Chat Experience Refinement

### Yapılanlar

- Mesaj balonları yeniden tasarlandı; Lina etiketi, mesaj metni, timestamp ve `Kopyala` aksiyonu daha bütünlüklü hale getirildi.
- Composer başlangıç yüksekliği kompakt hale getirildi ve multiline büyüme maksimum yükseklikle sınırlandı.
- `+`, `Mic`, `Screen` ve `Gönder` action butonları eşit yükseklik ve tutarlı spacing ile hizalandı.
- Smart auto-scroll davranışı `bottom mode` eşiği ve Qt layout/rangeChanged akışıyla güçlendirildi.
- Kullanıcı eski mesajları okumak için yukarıdaysa scroll konumu korunur; tekrar alta dönüldüğünde auto-scroll yeniden aktif olur.
- Sidebar sadeleştirildi; `A-`, `A+` ve collapse kontrolleri kaldırıldı.
- Local mode bilgisi ve header model/mic status chipleri daha kompakt hale getirildi.
- Alt status bar daha ince bir satıra dönüştürüldü.
- Plus ve Screen placeholder aksiyonları chat'e tekrar tekrar mesaj eklemeden status feedback verir.
- Speech UI buton durumları `Mic`, `Durdur` ve `Çevriliyor` akışlarına uygun hale getirildi.

### Mimari Sınırlar

- Değişiklikler yalnız PySide6 presentation katmanında tutuldu.
- Brain, Ollama `/api/chat`, Memory, Files, Speech backend ve Core davranışları değiştirilmedi.
- Yeni dependency eklenmedi.
- Tag oluşturulmadı.

### Test Sonucu

- PySide6 hedefli testler: `20 passed`
- Tam test paketi: `479 passed`

## 2026-07-11 - Screen Context Foundation

### Yapılanlar

- `v0.6.4-alpha` annotated tag'i `485f397` commit'i üzerinde oluşturuldu ve origin'e pushlandı.
- Screen capture yalnız açık kullanıcı eylemiyle çalışan bir akış olarak eklendi.
- Qt adapter cursor ekranını, fallback olarak primary screen'i yakalar ve görüntüyü yalnız bellekte PNG byte verisi olarak tutar.
- Modal preview dialog ekran adı, çözünürlük, capture saati ve gizlilik açıklaması gösterir.
- Kullanıcı screenshot'ı iptal edebilir veya `Sohbete Ekle` ile session-local context olarak onaylayabilir.
- Composer üzerinde tek aktif screen context'i gösteren, kaldırılabilir attachment chip eklendi.
- Yeni screenshot eskisini değiştirir; yeni sohbet, temizleme ve uygulama kapanışı context'i temizler.

### Mimari ve Güvenlik Kararları

- Qt'den bağımsız `ScreenContext` modeli ve capture contract'ı `screen` paketinde tutuldu.
- Qt ekran erişimi presentation adapter'ında izole edildi.
- Screenshot diske, temp klasörüne, Memory'ye, SQLite'a, Files capability'sine veya modele gönderilmez.
- Pixel içeriği loglanmaz; sürekli izleme, OCR, vision model ve background capture eklenmedi.
- Brain, Ollama, Memory, Files ve Speech davranışları değiştirilmedi.
- Yeni dependency eklenmedi.

### Test Sonucu

- Screen capture adapter testleri: `4 passed`
- Preview dialog testleri: `4 passed`
- Screen context dahil hedefli Qt testleri: `45 passed`
- Tam test paketi: `508 passed`

### Durum

`v0.7.0-alpha` Screen Context Foundation kod ve dokümantasyon tarafında tamamlandı. Tag oluşturulmadı. Sıradaki hedef `v0.7.1-alpha` Vision Provider Architecture çalışmasıdır.

## 2026-07-11 - Local Vision Integration

### Yapılanlar

- `v0.7.0-alpha` Screen Context Foundation tag'i `4db831b` commit'i üzerinde doğrulandı.
- Normal text modeli ile vision modeli ayrı provider ve Brain instance'ları olarak yapılandırıldı.
- Varsayılan local vision modeli `qwen3-vl:2b` olarak eklendi.
- Ollama `/api/show` cevabındaki `vision` capability için ayrı diagnostics akışı eklendi.
- Framework-neutral `ImageAttachment`, `ConversationInput` ve `ConversationResult` modelleri eklendi.
- PNG bytes yalnız provider sınırında Base64'e çevrilip `/api/chat` son user mesajının `images` alanına ekleniyor.
- Vision system prompt görseldeki talimatları güvenilmeyen içerik kabul edecek şekilde sınırlandırıldı.
- Başarılı vision isteğinde attachment tüketiliyor; hata durumunda yeniden deneme için korunuyor.
- Memory, Files ve deterministic intent'ler attachment'ı vision modeline göndermiyor ve tüketmiyor.
- GUI vision isteğinde ayrı typing metni, status feedback ve stale attachment koruması kullanıyor.

### Yerel Model Doğrulaması

- Ollama sürümü: `0.31.2`
- Kurulu vision modeli: `qwen3-vl:2b`
- `/api/show` capabilities: `completion, vision, tools, thinking`
- Resmî minimum Ollama sürümü: `0.12.7`
- Bellek içi 1×1 test PNG'siyle yerel `/api/chat` smoke testi başarılı.

### Güvenlik ve Kalıcılık

- Screenshot diske, temp klasörüne, Memory'ye, SQLite'a, Files capability'sine veya history'ye yazılmıyor.
- Raw image, Base64 ve full payload loglanmıyor.
- Cloud API, OCR dependency, kamera, otomasyon veya sürekli izleme eklenmedi.
- Yeni Python dependency eklenmedi.

### Test Sonucu

- Vision config ve model testleri: `31 passed`
- Diagnostics testleri: `24 passed`
- Provider/Brain testleri: `22 passed`
- Brain/prompt/conversation testleri: `72 passed`
- Qt/bootstrap hedefli testler: `47 passed`
- Tam test paketi: `541 passed`

### Durum

`v0.7.1-alpha` Local Vision Integration kod ve dokümantasyon tarafında tamamlandı. Tag oluşturulmadı; gerçek GUI screenshot smoke testi bekleniyor.

## 2026-07-12 - Vision Response and Image Upload Hotfix

### Kök Neden ve Düzeltme

- Ollama vision response içindeki boş `message.content` değeri başarılı cevap kabul edildiği için GUI boş Lina balonu gösterebiliyordu.
- Image request payload'una `think = false` eklendi; kullanıcıya dönük cevap içeriği boşsa provider artık kontrollü hata üretiyor.
- Hata durumunda attachment korunuyor ve boş mesaj balonu oluşturulmuyor.
- Bellekte oluşturulan mavi PNG ile gerçek local `qwen3-vl:2b` smoke testinde `Mavi` cevabı doğrulandı.

### Görsel Yükleme ve Önizleme

- Composer `+` butonu PNG, JPEG, WebP ve BMP dosyaları için kullanıcı kontrollü seçim dialog'una bağlandı.
- Seçilen görsel Qt ile yalnız bellekte PNG'ye normalize ediliyor; disk yazımı veya yeni dependency yok.
- Kaynak dosya ve pixel boyutu için güvenli üst sınırlar eklendi.
- Yüklenen görsel dosya adı ve çözünürlüğü attachment chip içinde gösteriliyor.
- Gönderilen kullanıcı mesaj balonunda görsel, metnin üstünde aspect ratio korunan thumbnail olarak gösteriliyor.
- Balon yalnız küçültülmüş QPixmap tutuyor; original image bytes conversation history'ye yazılmıyor.

### Test Sonucu

- Provider hotfix testleri: `12 passed`
- Qt image loader ve GUI hedefli testleri: `49 passed`
- Tam test paketi: `548 passed`

### Durum

Hotfix ve image upload akışı tamamlandı. `v0.7.1-alpha` tag oluşturulmadı; gerçek GUI ile Screen ve `+` yükleme akışlarının manuel smoke testi bekleniyor.

## 2026-07-12 - Vision UX and Region Capture

### Yapılanlar

- Screen menüsüne tam ekran ve alan seçerek yakalama seçenekleri eklendi.
- Region capture için Qt overlay, minimum seçim boyutu, iptal ve DPI ölçekleme davranışı eklendi.
- Composer attachment chip'ine thumbnail, `Değiştir`, `Kaldır` ve büyük önizleme akışı eklendi.
- Kullanıcı mesaj balonunda görsel thumbnail'i, analiz durumu ve başarısızlık sonrası `Yeniden analiz et` kontrolü eklendi.
- Yeniden analiz görseli composer'a geri yükler; otomatik gönderim yapmaz.
- Görseller session-local bellekte tutulur; kalıcı memory, cloud sync ve sürekli ekran izleme eklenmedi.

### Test Sonucu

- Region capture ve Qt attachment hedefli testleri: `61 passed`.
- Tam test paketi: `562 passed`.

### Durum

`v0.7.2-alpha` Vision UX & Region Capture kapsamı kod ve test tarafında tamamlandı. Release tag'i final smoke kontrolünden sonra oluşturulacaktır. Sonraki ana hedef conversation persistence foundation hazırlığıdır.

## 2026-07-12 - Conversation Persistence Foundation

### Yapılanlar

- Memory veritabanından ayrı `data/conversations.sqlite3` SQLite repository'si eklendi.
- Idempotent schema, foreign key cascade delete ve kısa ömürlü connection politikası uygulandı.
- Conversation session/message modelleri yalnız text ve güvenli visual metadata taşıyacak şekilde sınırlandı.
- `ConversationHistoryService` ile startup restore, yeni session, session switch, rename, delete, clear ve bounded Brain history eklendi.
- PySide6 sidebar gerçek sohbet listesini, aktif state'i ve rename/delete context menu akışını destekliyor.
- Vision mesajları kalıcı thumbnail veya raw bytes yerine güvenli placeholder metadata ile geri yükleniyor.
- Persistence kapalı veya erişilemez olduğunda in-memory fallback korunuyor.

### Güvenlik Sınırı

- Image bytes, Base64, thumbnail ve tam dosya yolu database'e yazılmıyor.
- Memory tabloları değiştirilmedi; yeni conversation tabloları ayrı database'te tutuluyor.

### Test Sonucu

- Conversation repository/service testleri: `11 passed`.
- Qt, bootstrap ve conversation hedefli testler: `64 passed`.
- Tam test paketi: `574 passed`.

### Durum

`v0.8.0-alpha` Conversation Persistence Foundation kod ve test tarafında tamamlandı. Manuel GUI restart, session isolation, management ve vision placeholder smoke testleri release öncesi yapılmalıdır.

## 2026-07-12 - Conversation Timeline and Welcome Experience

### Yapılanlar

- Persisted mesaj timestamp'leri repository'den UI widget'larına taşındı; restart sonrası gerçek mesaj saatleri korunuyor.
- Database timestamp politikası UTC timezone-aware ISO-8601 olarak sabitlendi; local saat presentation katmanında gösteriliyor.
- Legacy naive ve malformed timestamp parse davranışı veri silmeden güvenli fallback ile ele alındı.
- Conversation sıralaması recent activity temelli hale getirildi; yeni mesaj alan session sidebar'da üste taşınıyor.
- Sidebar item'larına muted tarih metadata'sı, header'a aktif conversation tarihi eklendi.
- Boş session'lar için zamana duyarlı `WelcomeStateWidget` eklendi.
- Welcome alanı UI-only tutuldu; database, Brain history ve last response içine yazılmıyor.
- İlk user mesajında welcome kaldırılıyor; clear ve yeni session sonrası yeniden gösteriliyor.

### Test Sonucu

- Timeline, repository ve Qt hedefli testler: `120 passed`.
- Tam test paketi: `580 passed`.
- Compile ve PySide6 import kontrolleri başarılı.

### Durum

`v0.8.1-alpha` Conversation Timeline & Welcome Experience kod ve test tarafında tamamlandı. Manuel timestamp, ordering, header/sidebar date ve welcome smoke testleri release öncesi yapılmalıdır.

## 2026-07-12 - Conversation Search and Management UX

### Yapılanlar

- Conversation schema'sı veri kaybı olmadan v2 alanlarıyla genişletildi: pin/archive metadata.
- Title ve user/assistant text içeriklerinde case-insensitive, Türkçe uyumlu local search eklendi.
- Search fallback'i yalnız mevcut SQLite ve Python standard library kullanıyor; FTS/harici motor dependency'si eklenmedi.
- `Sohbetler`, `Sabitlenenler` ve `Arşiv` filtreleri eklendi.
- Tarih grupları, search result snippet'leri ve `Ctrl+F`/`Escape` davranışları eklendi.
- Context menu'ya Sabitle, Arşivle ve karşıt durum aksiyonları eklendi.
- Delete/rename korunurken Clear aksiyonu geri getirilmedi.
- Image bytes, Base64, thumbnail, path ve Memory içeriği search/persistence sınırlarının dışında tutuldu.

### Test Sonucu

- Repository migration/search/pin/archive testleri: `9 passed`.
- Conversation service testleri: `17 passed`.
- Qt search/management hedefli testleri: `40 passed`.
- Tam test paketi: `586 passed`.

### Durum

`v0.8.2-alpha` Conversation Search & Management UX kod ve test tarafında tamamlandı. Manuel search, pin, archive, grouping ve regression smoke testleri release öncesi yapılmalıdır.
## 2026-07-12 - Lazy Conversation Creation and Delete Lifecycle

### Yapılanlar

- `Yeni Sohbet` ve uygulama açılışı artık boş SQLite conversation satırı oluşturmadan ephemeral draft ile başlıyor.
- İlk user message, conversation satırı ve ilk mesajla aynı transaction içinde persist ediliyor; yarım kayıt oluşması engelleniyor.
- Boş draft sidebar, search, pin, archive, rename ve delete listelerine dahil edilmiyor.
- Son conversation silindiğinde yeni boş satır oluşturulmuyor; welcome draft gösteriliyor.
- Aktif conversation silindiğinde veya arşivlendiğinde varsa en yeni görünür conversation UI'a yükleniyor.
- Legacy varsayılan başlıklı ve sıfır mesajlı kayıtlar veri silinmeden listelerde gizleniyor.

### Mimari Kararlar

- Draft state persistence katmanının kalıcı session modeliyle karıştırılmadı.
- Model isteğinden önce ilk mesaj persistence işlemi tamamlanıyor; persistence hatasında model çağrısı başlatılmıyor.
- Mevcut ConversationRepository, ConversationHistoryService ve PySide6 UI sınırları korundu; yeni dependency veya büyük refactor eklenmedi.

### Test Sonucu

- Conversation repository/service ve Qt hedefli testler başarılı.
- Tam test paketi: `590 passed`.
- `python -m compileall -q src main.py gui.py` baÅŸarÄ±lÄ±.

### Durum ve Sonraki Adım

`v0.8.3-alpha` Lazy Conversation Creation ve Delete Lifecycle Fix kod ve test tarafında hazırlandı. Manuel GUI smoke testinde yeni sohbet, ilk mesaj, son sohbet silme ve kalan sohbete otomatik dönüş akışları doğrulanmalı; ardından release tag kararı verilmelidir.
## 2026-07-12 - Settings and System Integration Foundation

### Yapılanlar

- Local AppData altında persistent user settings modeli, JSON repository, schema version ve atomik yazma eklendi.
- Bozuk veya gelecekteki settings dosyasında güvenli default fallback korundu.
- PySide6 settings dialog ve Ctrl+, erişimi eklendi.
- Appearance theme/font scale runtime uygulaması eklendi.
- Model tercihleri gelecekteki Ollama isteklerine bağlandı.
- Speech/Vision toggle kontrolleri ve Vision attachment temizleme akışı eklendi.
- QSystemTrayIcon, tray menüsü, close behavior ve start minimized fallback'i eklendi.

### Commitler

- `7b93a72` `feat: add persistent user settings foundation`
- `0918f8c` `feat: wire user settings into application bootstrap`
- `12d4427` `feat: add pyside6 settings dialog`
- `f78530a` `feat: add appearance settings runtime apply`
- `2039bf6` `feat: apply user model preferences`
- `601e1c1` `feat: apply speech and vision preferences`
- `517c59f` `feat: add system tray close behavior`

### Test ve Durum

- Tam test paketi: `610 passed`.
- Compile kontrolü başarılı.
- Yeni dependency eklenmedi; tüm yeni persistence kodu Python standard library kullanıyor.
- Ollama model refresh/capability doğrulaması ve gerçek Windows tray smoke testi sonraki doğrulama dilimine bırakıldı.
- v0.9.0-alpha tag'i manuel GUI smoke testi tamamlanmadan oluşturulmadı.
## 2026-07-12 - v0.9.0 Completion Patch

- `6b24021` `feat: add ollama model refresh`
- `1db6062` `feat: validate vision model capability`
- Settings dialog'unda asenkron `/api/tags` model refresh eklendi.
- `/api/show` capability kontrolü ile vision model doğrulaması eklendi.
- Ollama unavailable, boş liste ve stale worker sonuçlarında mevcut model seçimleri korunuyor.
- Otomatik model download/pull eklenmedi.
- Tam test paketi: `610 passed`.
- Manuel Windows tray ve GUI smoke testi hâlâ release öncesi yapılmalı.

## 2026-07-12 - Notifications & Background Tasks Foundation

- Notification Center zil/badge, Yaklaşanlar/Geçmiş/Tamamlananlar görünümleri ve empty state'ler tamamlandı.
- Reminder create/edit/complete/delete, confirmation, 10 dakika/1 saat/yarın snooze ve none/daily/weekly recurrence eklendi.
- Event-before-present delivery, delivery status, tray fallback, duplicate guard ve thread-local SQLite bağlantıları tamamlandı.
- Startup missed handling recurrence'ı geleceğe taşır; 4+ missed reminder tek desktop özetine çöker. Ayarlar popup/event üretimini runtime'da kontrol eder.
- Scheduler tray modunda sürer ve gerçek exit sırasında idempotent biçimde durur.
- Tam test paketi: `628 passed`. Yeni dependency eklenmedi.

## 2026-07-12 - Assistant Tools & Intent Routing Foundation

- Typed intent/request/context/result modelleri ve deterministic-first classifier eklendi.
- Safe registry yalnız mevcut reminder, vision, allowlisted files ve memory servislerine bağlandı.
- Reminder create ve Memory store için değiştirilemez confirmation; reminder eksikleri için conversation-isolated clarification eklendi.
- Normal chat fallback, routing-disabled davranışı, duplicate execution guard ve stale pending cleanup doğrulandı.
- Files traversal/absolute/unauthorized istekleri içerik sızdırmadan reddediliyor; raw image persistence ve unsafe tool eklenmedi.
- Routing logları content-free metadata ile sınırlandı. Model-assisted fallback kullanılmadı.
- Tam test paketi dokümantasyon öncesi `652 passed`; yeni dependency eklenmedi.

## 2026-07-13 - Tool UX, Reliability & v0.9 Stabilization

- Erişilebilir timeline ToolActivityCard ile ortak preparing/confirmation/running/success/failure/cancelled/unavailable durumları eklendi.
- Persistent confirmation modal yerine Onayla/Vazgeç kartına taşındı; Enter/Escape ve detail toggle eklendi.
- Retry read-only intent'lerle sınırlandı; persistent retry yeni ID ve confirmation gerektiriyor. Duplicate reminder create engellendi.
- Cancel komutları, expiration, routing disable, new/switch/delete/archive/close cleanup tamamlandı.
- Ortak error kategorileri, registry availability reason ve Vision diagnostics preflight eklendi.
- Reminder list 10 satırla sınırlandı; local timezone ve kalan kayıt özeti eklendi.
- File allowlist canonical casing güvenli biçimde çözümleniyor; traversal/absolute/UNC/symlink/binary/oversize sınırları korunuyor.
- v0.9.0 Settings, v0.9.1 Notifications ve v0.9.2 Routing regresyonları birlikte geçti. Dokümantasyon öncesi tam paket `663 passed`.

## 2026-07-13 - Light Theme Polish & Visual Consistency

- Light theme içindeki dark token sızıntıları kaldırıldı; tüm selector'lar semantic palette'e bağlandı.
- Main/sidebar/header/composer/input ile conversation hover, active, selected, disabled ve focus durumları ayrıştırıldı.
- User/assistant bubble, timestamp, welcome, typing ve attachment yüzeyleri light palette ile uyumlu hale getirildi.
- Tool/confirmation kartlarına semantic success/error/warning/info durum selector'ları ve metinsel durum işaretleri eklendi.
- Notification Center, Reminder dialog ve Settings navigation için merkezi component selector'ları eklendi.
- ComboBox, CheckBox, Slider, menu, tooltip, scrollbar ve dialog yüzeyleri merkezi QSS içinde tamamlandı.
- System theme light/dark fallback'i ve runtime açık dialog repolish akışı doğrulandı.
- %85, %100 ve %135 font scale; Tool card ve Notification Center selector'larıyla test edildi.
- Dark theme temel token'ları korunarak tam regresyon paketi `670 passed` tamamlandı. Yeni dependency eklenmedi.

## 2026-07-14 - Wake Word & Hands-Free Conversation

- Başlangıç kapısında working tree ve `origin/main` senkron, local/remote `v0.10.0-alpha` tag’i mevcut, `720 passed` ve compile başarılı olarak doğrulandı.
- Existing sounddevice/faster-whisper hattını kullanan enerji kapılı local `STTWakeWordDetector` eklendi; yeni dependency, cloud speech veya model download eklenmedi.
- Wake phrase normalization `hey lina`, `he lina` ve punctuation/casing varyasyonlarıyla conservative tutuldu; fuzzy false-positive eşleme eklenmedi.
- Bounded PCM VAD; silence-only, short noise, speech end, minimum speech, maximum duration ve no-input davranışlarını ayırıyor.
- Typed hands-free state machine ve wake → command → transcription → thinking → speaking → cooldown → wake lifecycle tamamlandı.
- Hands-free command transcription normal GUI send ve intent routing yoluna bağlandı; wake audio yeni command session’a taşınmıyor.
- Voice confirmation yes/no allowlist’i, ambiguous re-prompt, 25 saniyelik timeout ve conversation cleanup eklendi.
- Barge-in politikası TTS sırasında exact wake phrase gerektirecek şekilde sabitlendi; stale playback generation koruması korundu.
- Settings schema v3 migration, hands-free privacy confirmation, wake/confirmation/return tercihleri ve microphone device seçimi eklendi.
- Header/tray durumları, pause/resume, hands-free toggle, input device refresh/test ve missing-device default fallback tamamlandı.
- Audio/TTS persistence yok; raw audio/transcription loglanmıyor. Metrics content-free metadata ile sınırlı.
- Foundation commit’i `e1c6ffe`, runtime lifecycle commit’i `821c3c7` olarak `origin/main`’e pushlandı.
- Dokümantasyon öncesi full suite `774 passed`; compile ve `git diff --check` başarılı.

## 2026-07-14 - Live Vision & Camera Mode

- Başlangıç kapısında temiz/senkron `main`, local/remote `v0.10.1-alpha`, `774 passed` ve başarılı compile doğrulandı.
- `lina.vision.live` altında typed session/state/metrics, frame source, deterministic change detector, safe prompt policy ve bounded controller eklendi.
- PySide6 Qt Multimedia kamera adaptörü ve mevcut ekran/region capture servislerini GUI thread’inde kullanan bridge eklendi; OpenCV veya yeni dependency eklenmedi.
- Varsayılan 2 saniye capture, 5 saniye minimum analiz, sensitivity preset, tek aktif inference ve latest-frame-wins backpressure tamamlandı.
- Stop/source switch/exit generation isolation, pending clear, provider cancel, camera release ve stale result suppression eklendi.
- Kamera/ekran başlangıcı explicit confirmation’a; hands-free confirmation mevcut voice akışına bağlandı.
- Source-aware Live Vision paneli, metinsel privacy indicator, last result, manual analyze, pause/resume/stop ve tray kontrolleri eklendi.
- Settings schema v4 migration; default source, interval, sensitivity, voice, camera ve screen tercihleri eklendi.
- Sonuçlar conversation switch sonrası yanlış chat’e yazılmıyor; yalnız application-level panelde gösteriliyor.
- Raw frame/screenshot/Base64/temp file persistence ve content logging eklenmedi. Metrics yalnız teknik sayaç ve sürelerden oluşuyor.
- Foundation `ad13a63`, runtime integration `625b9b1` ve tests `d94f4c7` commitleri origin/main’e pushlandı.
- Dokümantasyon öncesi tam test paketi `809 passed`; compile ve diff check başarılı.
- Gerçek Windows kamera, çoklu ekran, 4 GB VRAM, Ollama ve tray smoke testi tag kararından önce manuel yapılmalıdır. `v0.11.0-alpha` tag oluşturulmadı.

## 2026-07-14 - Live Preview & Monitoring Overlays

- Başlangıçta temiz/senkron main, `809 passed`, compile ve `QCamera/QVideoSink` import doğrulandı.
- QVideoSink’ten QImage’a doğrudan, disk/Base64 kullanmayan ve inference’dan bağımsız kamera preview hattı eklendi.
- `Lina Kamera` singleton window; cihaz/status/privacy metni, analyze, pause/resume, stop, hide/show ve stale-session guard tamamlandı.
- 16×16 grid block-difference, komşu merge, tiny-noise filtresi, maksimum beş normalized region ve box timeout eklendi.
- Değişiklik kutularının semantic object detection olmadığı UI ve dokümantasyonda açıklandı.
- Full-screen ve region için click-through, focus almayan, taskbar dışı zorunlu privacy border eklendi.
- Explicit screen capture, secondary monitor geometry, region global-coordinate düzeltmesi ve periyodik geometry refresh tamamlandı.
- Pause opacity/dashed state, unexpected border close → stop ve stop/source/error/disable/exit visual cleanup eklendi.
- Controller preview/change/geometry/stopped typed eventleri session/generation kimliğiyle genişletildi.
- Preview timer’ın deleted widget’a callback yapma regresyonu child QTimer lifecycle ile düzeltildi.
- Feature commitleri `22c61ca`, `5799ebe`; test commit’i `c4c0bf3` olarak yerelde oluşturuldu.
- Dokümantasyon öncesi tam paket `833 passed`; yeni dependency, OpenCV, YOLO, frame persistence veya semantic detection yok.
- `origin/main` push güvenlik katmanı tarafından ek açık kullanıcı onayı beklediği için henüz yapılmadı.

## 2026-07-16 - Agent Mode Foundation

- Başlangıç kapısında temiz ve senkron `main`, `HEAD == origin/main`, 870 test ve başarılı compile doğrulandı.
- `lina.agent` altında typed models, planner, policy, controller, executor, verifier, approvals, bounded context, errors ve safe persistence katmanları eklendi.
- Capability snapshot yalnız ad, açıklama, şema türü, availability, result/risk/approval metadata’sı taşır; callback, secret, raw environment veya kullanıcı içeriği taşımaz.
- Default 8, hard 12 step; bir repair, bir read-only retry, bir replan; duplicate/cycle/loop ve unknown/prohibited tool guard tamamlandı.
- Persistent/sensitive adımlarda plan onayından ayrı ve kapatılamayan step approval; uncertain persistent sonuçta no-retry uygulandı.
- Single active session, execution/session/generation identity, conversation isolation, pause/resume/cancel, stale suppression ve shutdown cleanup eklendi.
- Safe repository yalnız bounded metadata saklar; running session restart sonrası interrupted olur ve otomatik devam etmez.
- Settings schema v6, explicit Agent intent’leri, voice approval, typed Qt panel, tray kontrolleri ve privacy-safe completion notification eklendi.
- Normal sohbet, reminders, memory, files, voice, hands-free, Live Vision ve kamera regression kapsamı korundu; kamera kodu değiştirilmedi.
- Manual realtime camera validation deferred.
- Yeni dependency eklenmedi. Foundation commit’i `410c854`, entegrasyon commit’i `246a74d`.
- Dokümantasyon öncesi tam paket 917 passed; compile başarılı.

## 2026-07-16 - Tag Öncesi Interaction Quality & Voice Stabilization

- Kısa katmanlı system prompt, dengeli normal-chat generation seçenekleri ve düşük sıcaklıklı tek repair zinciri eklendi.
- Türkçe dil karışması, tekrar, persona bozulması, anlamsız token ve eksik cevaplar ortak quality gate ile kabul öncesi denetleniyor.
- Context duplicate/internal/raw-plan temizliği ve cumulative stream chunk bastırması eklendi.
- STT için in-memory DC düzeltme, bounded gain, clipping koruması ve transcription duplicate/low-quality sinyali eklendi.
- VAD pre-roll/adaptive noise floor; wake phrase normalization, false-positive listesi ve cooldown ile güçlendirildi.
- TTS request metadata, stale callback koruması, generation deduplication ve deterministic spoken-text temizliği eklendi.
- Agent approval/completion/important event ses tercihleri; mikrofon kalibrasyonu, wake test aracı ve stale-safe birleşik durum modeli eklendi.
- Settings schema v7 eski şemaları koruyarak migration yapar. Yeni dependency, cloud speech, raw audio persistence veya kamera kodu değişikliği yoktur.
- Başlangıçta 918, finalde 931 test geçti; compileall ve PySide6 import doğrulandı.

## 2026-07-16 - Complete Product Experience Redesign

- Başlangıçta temiz/senkron main, 931 test, compileall, 0.12.0a0 ve tag bulunmadığı doğrulandı.
- Typed palette, spacing, radius, typography, control, layout, motion ve contrast design token katmanı eklendi.
- Sidebar/app shell, minimal header, unified status, merkez timeline, empty state ve tek composer yeniden kuruldu.
- Varsayılan kapalı details inspector ve klavye odaklı command palette eklendi.
- Agent ve Live Vision yalnız aktifken görünen kompakt ilerleme yüzeylerine dönüştü; kamera iş mantığı değişmedi.
- Settings 11 aranabilir bölüme ayrıldı; density ve window geometry persistence ile schema v8’e geçti.
- Qt standard icon sistemi, accessible name/tooltip’ler, compact breakpoint, off-screen clamp ve yatay taşma korumaları eklendi.
- Response Quality V2 yabancı phrase, yabancı stem + Türkçe ek ve ilgisiz selamlama sızıntılarını; Repair V2 stale/cancel sonucunu reddeder.
- Dark/light/compact/settings ekranları fake içerikle offscreen render edilip incelendi; geçici binary’ler repository’ye eklenmedi.
- Yeni dependency, branded asset, version bump veya tag eklenmedi. Windows DPI/mikrofon/TTS/kamera/tray turu manuel smoke kapsamındadır.
- Final tam regresyon paketi 949 test geçti; compileall, PySide6 import ve diff check başarılıdır.

## 2026-07-16 - UI Simplification & Response Quality Polish

- Product Experience Redesign üzerinde ikinci bir yoğunluk audit’i yapıldı; backend ve controller zincirleri değiştirilmeden kalan görünür kalabalık çıkarıldı.
- Sidebar görünür içeriği branding, yeni sohbet, arama ve session listesiyle sınırlandı; filtre, local status ve utility kısayolları Araçlar/command palette erişimine taşındı.
- Header kısa unified status + Araçlar düzeyine indi; bildirim ikonu yalnız unread count sıfırdan büyükken görünür.
- Composer Ekle/Araçlar/Gönder hiyerarşisine geçti; Mikrofon, Ekran ve Agent signal’ları tek menüde korunur.
- Settings 11 maddeden yedi ana bölüme konsolide edildi; uzun sayfalara dikey scroll, row wrapping ve yatay taşma koruması eklendi.
- Türkçe quality gate genel selamlama/yardım kalıpları, yabancı kelime kırıntıları ve bozuk teknik ekler için güçlendirildi; İngilizce istenen yanıtlara müdahale edilmez.
- Dark/light/720 px compact ve Settings/Gelişmiş ekranları fake veriyle offscreen render edildi; geçici artefact’lar temizlendi.
- Başlangıçtaki 949 test finalde 955 teste yükseldi; tam paket, compileall, PySide6 import ve diff check başarılıdır.

## 2026-07-17 - Agent Reliability, Task Templates & Recovery

- Temiz ve `origin/main` ile senkron `main`, mevcut `v0.12.0-alpha` local/remote tag’i, 955 test ve compileall başlangıç kapıları doğrulandı.
- Framework bağımsız typed görev şablonu registry/matcher/validator/renderer katmanı ve yalnız gerçek capability’lere bağlı yedi yerleşik görev eklendi.
- Hatırlatıcı özet aracı tarih aralığını gerçekten filtreleyecek, çakışma aracı aynı `due_at` kayıtlarını deterministik gruplayacak biçimde SafeToolRegistry’ye eklendi.
- Plan editor, revision-aware diff, dependency/risk koruması ve plan kalite/loop denetimi eklendi.
- Error taxonomy, read-only tek retry, persistent no-retry, idempotency key, replay guard, duplicate read-before-write, event ve checkpoint altyapısı tamamlandı.
- Startup recovery yarım session’ları bir kez `interrupted` olarak persist eder; auto-resume veya tool yürütmez. Privacy-safe Task Center V2 ve safe clone davranışı eklendi.
- Template Browser, typed parametre formu, Plan Review ve Inspector V2; composer, command palette, tray ve doğal dil akışlarıyla bağlandı.
- Agent yanıt kalite kapısı, event bazlı TTS/bildirim deduplication, recovery bildirimi ve Settings schema v9 entegrasyonu tamamlandı.
- `pyproject.toml` sürümü `0.12.1a0`, uygulama etiketi `v0.12.1-alpha` oldu; yeni dependency veya tag eklenmedi.
- Sprint boyunca yedi doğal yerel commit oluşturuldu. Final tam paket 1.039 test, compileall ve diff check kapılarından geçti.

## 2026-07-17 - Premium AI Workstation UI & Response Polish

- Backend controller ve persistence zincirleri değiştirilmeden PySide6 shell, sidebar, header, timeline, composer, tool kartları, Agent yüzeyi ve Settings yeniden yoğunluk denetiminden geçirildi.
- Dark palette derin lacivert surface hiyerarşisine; layout 280/60 navigasyon, 820 px sohbet, 720/560 px mesaj ve 860 px composer ölçülerine taşındı.
- Aktif sohbetin yinelenen “bu oturum” bloğu kaldırıldı; kapalı Agent/Vision/Voice/notification yüzeyleri progressive disclosure davranışını korudu.
- Assistant ve user mesajları ayrışan bounded kartlara; composer tek yüzeye ve icon-only send/stop davranışına geçti.
- Platform dosya ikonları yerine aktif palette bağlı, kod tabanlı 20 px çizgi ikon sistemi eklendi.
- Settings yedi ana bölümünü koruyarak ürün başlığı, 204 px navigation ve ortak section card hiyerarşisine geçti.
- Tool ayrıntıları varsayılan kapalı hale getirildi; Agent paneli yalnız gerçek session varken görünen profesyonel progress card olarak kaldı.
- Türkçe prompt ilk cümlede sonuç, doğal ifade ve iç talimat/rol sızıntısını önleme kurallarıyla; kalite kapısı yüksek güvenli meta leakage tespitiyle güçlendirildi.
- `scripts/render_ui_preview.py` ile ana sohbet ve Settings offscreen render edilip görsel olarak incelendi; binary QA artefact’ları repository’ye eklenmedi.

## 2026-07-17 - Reference-Driven Premium Desktop Experience

- Premium referans ile mevcut uygulama shell’i; kolonlar, bilgi yoğunluğu, header, message, composer, contextual tools ve responsive davranış açısından karşılaştırıldı.
- Design System V3 semantic yüzey/state alias’ları, genişlik/radius/control/elevation token’ları ve isim+renk+ölçü anahtarlı icon cache ile tamamlandı.
- Typed `ApplicationViewState` ile geniş kalıcı üç kolon, orta sağ drawer ve kompakt icon sidebar + drawer davranışı eklendi; native Windows title bar korundu.
- Conversation repository son mesaj preview projection’ı, sidebar üç satırlı başlık/preview/time kartları ve mevcut context eylemleriyle zenginleştirildi.
- Assistant avatarı, güvenli Markdown/code subset’i, adaptive message kartı ve Dosya/Mikrofon/Ekran/Daha Fazla içeren premium composer eklendi.
- Context inspector gerçek Chat/Voice/Vision/File/Agent/Memory sinyallerine, hassas içerik filtreli `MemoryService` kayıtlarına ve async/cache’li bounded local storage ölçümüne bağlandı.
- Settings schema v10 sidebar/right panel/message genişliği/son settings bölümü state’ini migrate edip persist eder hale geldi.
- Response Quality V3 teknik allowlist ve kullanıcı terimi farkındalığıyla; Repair V3 exact prompt, tek non-streaming deneme ve sabit güvenli fallback ile tamamlandı.
- Dark/light, large/medium/compact, tools/memory/system/voice/vision/agent ve settings dahil 18 offscreen yüzey incelendi. Stale Memory widget çakışması yakalanıp lifecycle düzeltmesi uygulandı; geçici PNG’ler temizlendi.
- Sürüm `0.12.2a0` / `v0.12.2-alpha` olarak güncellendi. Yeni ağır dependency veya tag eklenmedi; push açık kullanıcı izni bekler.
