# Lina v0.6.4-alpha Release Notes

## Durum

`v0.6.4-alpha`, PySide6 migration sonrası masaüstü sohbet deneyimini daha kompakt, okunabilir ve profesyonel hale getiren UI refinement sürümüdür.

Bu sürüm yalnız presentation/UI katmanını değiştirir. Brain, Ollama, Memory, Files, Speech, Core ve capability davranışları korunmuştur.

## Öne Çıkanlar

- Mesaj balonları tek bir bütün gibi görünecek şekilde yeniden düzenlendi.
- Lina etiketi, mesaj metni, saat ve `Kopyala` aksiyonu daha doğal bir hiyerarşiye taşındı.
- Assistant ve user mesajları daha dengeli genişlik ve hizalama ile gösterilir.
- Smart auto-scroll davranışı iyileştirildi.
- Kullanıcı eski mesajları okumak için yukarı kaydırdıysa scroll konumu korunur.
- Composer daha kompakt hale getirildi.
- `+`, `Mic`, `Screen` ve `Gönder` butonları eşit yükseklik ve tutarlı spacing ile hizalandı.
- Sidebar sadeleştirildi; `A-`, `A+` ve collapse kontrolleri kaldırıldı.
- Local mode bilgisi daha kompakt gösterilir.
- Header model/mic status chipleri küçültüldü.
- Alt status bar daha ince ve sade hale getirildi.
- Plus ve Screen placeholder aksiyonları chat'i spamlemeden status feedback verir.
- Speech UI buton durumu `Mic`, `Durdur` ve `Çevriliyor` akışlarına hazır hale getirildi.

## Korunan Davranışlar

- Ollama structured `/api/chat` entegrasyonu değişmedi.
- Brain, PromptBuilder, IntentAnalyzer ve ConversationService davranışları değişmedi.
- Memory ve SQLite repository davranışı değişmedi.
- Files read-only allowlist güvenliği değişmedi.
- Speech backend ve STT motoru değişmedi.
- Yeni dependency eklenmedi.
- Tag oluşturulmadı.

## Test

```powershell
python -m pytest
```

Son doğrulama:

```text
479 passed
```

## Bilinen Sınırlamalar

- Bu sürüm otomatik görsel snapshot testi içermez; manuel GUI smoke test hâlâ gereklidir.
- PySide6 arayüzün gerçek Windows render davranışı font ve DPI ayarlarına göre küçük farklılıklar gösterebilir.
- Vision, screen awareness, TTS, wake word ve Windows automation hâlâ kapsam dışıdır.

## Manuel Smoke Test Önerisi

1. `python gui.py`
2. Composer başlangıçta kompakt mı?
3. Plus, Mic, Screen ve Gönder aynı yükseklikte mi?
4. Lina ve kullanıcı mesaj balonları doğal görünüyor mu?
5. Saat ve Kopyala aksiyonu mesajla birlikte duruyor mu?
6. Yeni mesajlarda chat en alta kayıyor mu?
7. Eski mesajlara scroll yapınca konum korunuyor mu?
8. Mic transcription input alanına yazılıyor ve otomatik gönderilmiyor mu?
9. Plus ve Screen placeholder feedback'i status alanında görünüyor mu?
