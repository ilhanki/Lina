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
