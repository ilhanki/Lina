# Lina v0.6.0-alpha Sürüm Notları

## Durum

Bu sürüm, Speech Capability v1 için güvenli ve test edilebilir altyapı adayıdır. Gerçek mikrofon, STT veya TTS engine içermez.

## Öne Çıkanlar

- Speech durumlarını temsil eden küçük ve immutable veri modelleri eklendi.
- STT ve TTS sağlayıcı sözleşmeleri tanımlandı.
- `SpeechService`, sağlayıcı bağımsız speech orchestration katmanı olarak eklendi.
- Runtime varsayılanı olarak cihaz erişimi yapmayan NoOp sağlayıcılar kullanıldı.
- GUI içindeki `Mic` butonu `SpeechService` akışına bağlandı.
- Test sağlayıcısından gelen transkripsiyon input alanına yazılır ve otomatik gönderilmez.
- Unavailable ve hata durumlarında GUI kullanılabilir halde kalır.

## Güvenlik Sınırları

- Always-on listening yoktur.
- Kullanıcı eylemi olmadan speech akışı başlamaz.
- Gerçek mikrofon erişimi ve ses kaydı yoktur.
- Ses dosyası oluşturulmaz veya saklanmaz.
- Cloud speech servisi kullanılmaz.
- Transkripsiyon otomatik olarak ConversationService'e gönderilmez.
- Yeni runtime dependency eklenmemiştir.

## Bilinen Eksikler

- Gerçek STT engine henüz seçilmemiştir.
- Gerçek TTS engine henüz seçilmemiştir.
- Varsayılan Mic davranışı, speech engine bulunmadığını açıklayan güvenli unavailable mesajıdır.
- Mikrofon izinleri, cihaz seçimi, ses buffer yönetimi ve wake word kapsam dışıdır.

## Çalıştırma

```text
python gui.py
```

GUI içinde `Mic` butonuna basıldığında varsayılan NoOp provider güvenli unavailable mesajını gösterir. Bu davranış mikrofonu açmaz.

## Test

```text
python -m pytest
```

Son doğrulama sonucu: `399 passed`.

## Sonraki Adım

`v0.6.1-alpha` öncesinde local-first STT engine adayları; Windows uyumluluğu, dependency maliyeti, model boyutu, performans ve mahremiyet bakımından karşılaştırılmalıdır. Gerçek engine entegrasyonu ayrı kullanıcı onayıyla başlatılmalıdır.
