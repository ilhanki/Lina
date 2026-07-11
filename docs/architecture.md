# Lina Mimari Dokümanı

Bu doküman Lina'nın uzun vadeli mimari yönünü tanımlar. Amaç, projeyi hızlı prototip mantığıyla değil; sürdürülebilir, test edilebilir ve modüler bir masaüstü asistan platformu olarak büyütmektir.

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
