# Agent Görev Şablonları

Bu belge `v0.12.1-alpha` içindeki hazır Agent görevlerinin sözleşmesini ve güvenlik sınırını açıklar. Şablonlar yeni yetki vermez; yalnız mevcut `SafeToolRegistry` capability’lerinden typed ve incelenebilir plan üretir.

## Yaşam döngüsü

```text
Kullanıcı seçimi veya güvenli doğal dil eşleşmesi
→ capability availability filtresi
→ typed parametre normalizasyonu
→ gerekiyorsa tek açıklama sorusu
→ plan üretimi ve kalite/policy doğrulaması
→ kullanıcı plan incelemesi
→ kalıcı adım için ayrı onay
→ yürütme ve deterministic doğrulama
```

Matcher Agent Mode kapalıyken çalışmaz. “Hatırlatıcı nedir?” gibi açıklama soruları, düşük güvenli veya desteklenmeyen istekler normal sohbette kalır. Açık şablon seçimi eşleşme önceliği kazanır fakat unavailable capability’yi veya policy’yi aşamaz. Eksik bilgi yalnız aynı conversation ve generation içinde tamamlanabilir.

## Yerleşik katalog

| Şablon | Araç | Girdi | Risk ve davranış |
| --- | --- | --- | --- |
| `reminders.create` | `reminder.create` | başlık, timezone-aware tarih/saat, tekrar | Kalıcıdır; plan ve adım onayı gerekir. Duplicate kayıt önce okunur. |
| `reminders.summary` | `reminder.summary` | `upcoming`, `tomorrow`, `week` | Salt okunur; aralığı deterministik filtreler ve sonucu 10 satırda sınırlar. |
| `reminders.conflicts` | `reminder.conflicts` | tarih aralığı | Salt okunur; aynı `due_at` değerine sahip kayıtları sabit sırada gruplar. |
| `memory.store` | `memory.store` | içerik, kategori | Kalıcıdır; hassas içerik reddedilir, duplicate kayıt oluşturulmaz. |
| `memory.recall` | `memory.recall` | bounded sorgu | Salt okunur; en fazla beş yerel kayıt getirir. |
| `files.summarize` | `files.read` | allowlist hedefi, özet tercihi | Salt okunur; dosya erişim, boyut, UTF-8 ve traversal sınırlarını aynen korur. |
| `vision.single_frame` | `vision.image` | explicit kullanıcı görseli | Mevcut Vision UI onay akışını gerektirir; gizli capture başlatmaz. |

`system.status` ve `conversation.search` bu sürümde Agent tool capability’si olmadığı için şablon değildir. Shell, process, code execution, browser, git, email/message, mouse/keyboard, dosya yazma/silme/taşıma ve gizli kamera/mikrofon hiçbir şablonda kullanılamaz.

## Typed parametreler

Şablon schema’sı yalnız bilinen alanları ve Python türlerini kabul eder. Unknown alan, boş zorunlu değer, geçmiş tarih veya yanlış tür plan oluşturulmadan reddedilir. Tarih/saat GUI’de ayrı kontrollerle, enum benzeri değerler sabit seçeneklerle alınır. Parametre formundaki “Planı Hazırla” herhangi bir aracı çalıştırmaz.

Doğal hatırlatıcı isteğinde parser başlık, tarih, saat ve recurrence çıkarır. Örneğin “Yarın sporu hatırlat” yalnız saati sorar; bütün isteği yeniden istemez. Tekrarlanan aynı açıklama döngü olarak yakalanır.

## Plan inceleme ve düzenleme

Plan Review her adım için başlık, açıklama, tool, risk, approval ve dependency bilgisini gösterir. Düzenleme katmanı:

- bağımlılıkları bozmayan yeniden sıralamaya;
- yalnız optional adımı kaldırmaya veya atlamaya;
- tool schema’ya uyan typed argüman güncellemesine;
- bounded plan regeneration’a izin verir.

Policy dışı araç ekleme, completed adım değiştirme, persistent riski düşürme, cycle/invalid dependency ve step limit aşımı reddedilir. Plan değişince revision artar, eski onay geçersiz olur ve added/removed/moved/changed farkı gösterilir.

## Availability ve hata davranışı

Capability hem katalog listelenirken hem yürütmeden hemen önce kontrol edilir. Plan hazırlandıktan sonra servis kapanırsa adım `tool_unavailable` ile bloklanır; başka bir araca sessiz fallback yapılmaz. Read-only timeout/transient hata en fazla bir otomatik retry alabilir. Kalıcı işlem, izin/onay hatası, validation hatası ve uncertain sonuç otomatik retry almaz.

## Bilinen sınırlar

- Katalog kullanıcı tanımlı plugin/remote şablon yüklemez.
- Dosya görevi Agent aracında yalnız allowlist metnini güvenli biçimde okur; genel dosya sistemi erişimi veya yazma sağlamaz.
- Tek-kare Vision şablonu UI etkileşimi ister; background kamera başlatmaz.
- Şablon önerisi ayarlardan kapatılabilir; explicit Hazır Görevler erişimi capability filtresini korur.

