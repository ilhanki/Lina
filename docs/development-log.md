# Lina Geliştirme Günlüğü

Bu dosya önemli geliştirme kararlarını ve milestone ilerlemesini kısa notlar halinde takip etmek için kullanılır.

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
