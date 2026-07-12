# Lina v0.9.0-alpha

## Durum

Alpha / aktif geliştirme.

## Öne Çıkanlar

- Local AppData altında persistent `user-settings.json` desteği.
- Schema version, güvenli default fallback ve atomik JSON yazma.
- PySide6 Ayarlar penceresi: Genel, Görünüm, Modeller, Konuşma, Vision, Sistem ve Hakkında bölümleri.
- Dark, light ve system tema seçenekleri ile yüzde 85-135 font ölçeği.
- Text ve vision model tercihlerinin gelecek Ollama isteklerine uygulanması.
- Speech ve Vision kontrollerinin ayarlardan güvenli biçimde açılıp kapatılması.
- PySide6 system tray menüsü ve `exit`, `tray`, `ask` kapanış davranışları.
- Tray desteklenmeyen ortamlarda güvenli normal kapanış fallback'i.

## Gizlilik Sınırları

- Ayar dosyasına conversation içeriği, Memory içeriği, raw image, Base64, secret veya token yazılmaz.
- Autostart, registry yazımı, cloud sync ve otomatik model indirme eklenmedi.
- Conversation ve Memory database'leri değiştirilmedi.

## Test

```text
python -m pytest
610 passed
```

## Bilinen Sınırlamalar

- Ollama model refresh yalnız kurulu modelleri asenkron olarak listeler; otomatik indirme yapmaz.
- Vision model seçimleri `/api/show` içindeki açık `vision` capability alanıyla doğrulanır.
- Gerçek Windows system tray davranışı bu ortamda manuel smoke test edilmedi.
- v0.9.0-alpha release tag'i manuel GUI smoke testi sonrasına bırakıldı.
