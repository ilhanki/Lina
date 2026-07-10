# Lina v0.6.1-alpha Sürüm Notları

## Durum

Bu sürüm local-first, kullanıcı kontrollü Push-to-Talk Speech-to-Text entegrasyonudur.

## Yeni Özellikler

- `sounddevice` tabanlı tek seferlik ve sınırlandırılmış mikrofon kaydı.
- `faster-whisper` tabanlı yerel Türkçe transcription.
- GUI Mic butonunda `Dinliyorum`, `Durdur` ve transcription durumları.
- Transkripsiyonu mevcut composer taslağının sonuna ekleme.
- Sessizlikte erken bitirme ve maksimum kayıt süresi.
- Lazy model loading ve güvenli unavailable/error fallback.

## Dependency'ler

- `faster-whisper`
- `sounddevice`

Kurulum:

```powershell
pip install -r requirements.txt
```

## Varsayılanlar

- Model: multilingual `base`
- Dil: `tr`
- Cihaz: `cpu`
- Compute type: `int8`
- Sample rate: `16000`
- Kanal: mono
- Maksimum kayıt: `12` saniye
- Otomatik gönderme: kapalı

## Kullanım

1. `python gui.py` ile GUI'yi açın.
2. `Mic` butonuna basıp konuşun.
3. İkinci kez basarak kaydı durdurun veya sessizlik/süre sınırını bekleyin.
4. Input alanına yazılan metni kontrol edin ve kendiniz gönderin.

İlk kullanımda modelin indirilmesi ve yerel cache içinde hazırlanması zaman alabilir. Model cache'i repository içine yazılmaz.

## Privacy ve Güvenlik

- Kayıt yalnız açık Mic eylemiyle başlar.
- Always-on listening ve background recording yoktur.
- Ham ses bellekte işlenir; ses dosyası saklanmaz.
- Ses verisi ağ üzerindeki bir speech servisine gönderilmez.
- Transkripsiyon otomatik gönderilmez veya Memory'ye otomatik kaydedilmez.

## Bilinen Eksikler

- TTS ve wake word yoktur.
- Mikrofon cihazı seçme arayüzü yoktur.
- İlk model hazırlığı internet bağlantısı gerektirebilir.
- CPU transcription süresi sisteme göre değişebilir.
- Gerçek mikrofon davranışı manuel smoke test gerektirir.

## Test

```powershell
python -m pytest
```

Son otomatik doğrulama sonucu: `430 passed`. Testler gerçek mikrofon veya model indirmesi kullanmaz.
