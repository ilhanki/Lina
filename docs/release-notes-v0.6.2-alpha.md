# Lina v0.6.2-alpha Sürüm Notları

## Durum

`v0.6.2-alpha`, Professional UI, Readability & Accessibility Polish sürüm adayıdır. Geliştirme tamamlanmıştır; tag oluşturulmadan önce manuel GUI smoke testi beklenmektedir.

## Öne Çıkanlar

- Windows DPI awareness ve sınırlı Tk scaling desteği eklendi.
- Kurulu fontları denetleyen güvenli font fallback zinciri eklendi.
- Koyu tema renkleri okunabilir semantik sabitlerde toplandı.
- Sidebar, header, chat alanı ve composer responsive yerleşime geçirildi.
- Sidebar daraltma/genişletme ve oturum içi font boyutu kontrolleri eklendi.
- Mesaj balonlarına saat ve mesaj başına kopyalama aksiyonu eklendi.
- Uzun mesajların pencereyi yatay büyütmesini önleyen dinamik wrap davranışı eklendi.
- Kullanıcı yukarıdaki mesajları okurken scroll konumunun korunması sağlandı.
- Composer placeholder, boş mesaj kontrolü, tooltips ve klavye kısayolları eklendi.
- İlk anlamlı kullanıcı mesajından LLM kullanmadan session başlığı üretilir hale getirildi.

## Klavye Kısayolları

- `Enter`: Mesajı gönderir.
- `Shift+Enter`: Yeni satır ekler.
- `Ctrl+L`: Composer alanına odaklanır.
- `Ctrl+N` veya `Ctrl+K`: Yeni sohbet başlatır.
- `↑` / `↓`: Oturum içi input geçmişinde gezinir.

## Korunan Davranışlar

- Structured Ollama `/api/chat` akışı.
- Memory ve Files komutları.
- Project context ve deterministic response akışları.
- Push-to-talk kayıt, transcription ve input'a yazma davranışı.
- Transcription sonucunun otomatik gönderilmemesi.
- Typing placeholder, hata kurtarma ve background thread akışı.
- Logo ve window icon fallback desteği.

## Bilinen Sınırlamalar

- Kalıcı sohbet geçmişi yoktur; sidebar yalnız mevcut oturumu gösterir.
- `+` ve `Screen` kontrolleri henüz gerçek capability başlatmaz.
- TTS, vision, screen capture ve Windows automation uygulanmamıştır.
- Görsel kalite ekran ölçeklendirmesi ve sistem fontlarına göre değişebilir; Windows üzerinde manuel smoke test gereklidir.
- Tkinter native widget sınırları nedeniyle özel markdown veya kod bloğu renderer'ı yoktur.

## Test Sonucu

- Hedefli GUI testleri: `84 passed`
- Tam test paketi: `459 passed`
- Testlerde gerçek Ollama, mikrofon veya GUI mainloop kullanılmadı.

## Çalıştırma

```powershell
python gui.py
```

## Sonraki Adım

Manuel GUI smoke testi tamamlandıktan sonra `v0.6.2-alpha` tag kararı verilecektir. Sonraki büyük hedef `v0.7.0-alpha` Vision / Screen Awareness v1 için ayrı mimari ve güvenlik planlamasıdır.
