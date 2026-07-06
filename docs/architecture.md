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
