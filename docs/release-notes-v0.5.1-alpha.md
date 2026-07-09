# Lina v0.5.1-alpha Release Notes

## Sürüm

`v0.5.1-alpha`

## Durum

Alpha / Manuel smoke test adayı.

Bu sürüm, `v0.5.0-alpha` Files Capability v1 sonrasında gelen profesyonel GUI yenileme sürümüdür. Yeni capability eklemez; mevcut Tkinter arayüzünü daha modern, okunabilir ve sohbet uygulamasına yakın bir düzene taşır.

## Öne Çıkanlar

- Modern koyu tema.
- Sol sidebar.
- Lina logo/icon desteği.
- Bubble-based chat layout.
- Modern input composer.
- `+`, `Mic` ve `Screen` placeholder action butonları.
- `Yeni Sohbet` butonu.
- Mevcut GUI davranışlarının korunması.

## Yeni GUI

Tkinter GUI artık tek düz metin alanı yerine daha profesyonel bir sohbet düzeni kullanır.

- Lina mesajları sol tarafta gösterilir.
- Kullanıcı mesajları sağ tarafta gösterilir.
- `Yazıyor...` mesajı Lina bubble olarak görünür ve cevap gelince temizlenir.
- Mesajlar otomatik scroll davranışını korur.
- `Lina:Lina:` gibi label duplication hatalarına karşı mevcut normalize render path korunur.

## Sidebar

Sol sidebar şimdilik session odaklı bir UI alanıdır.

- Logo dosyası varsa üst branding alanında gösterilir.
- `Lina` başlığı.
- `Yeni Sohbet` butonu.
- Placeholder sohbet listesi.
- Sürüm ve local mode bilgisi.

`Yeni Sohbet` mevcut oturumu temizler. Kalıcı conversation persistence bu sürümde yoktur.

## Composer Buttons

Alt composer şu butonları içerir:

- `+`
- `Mic`
- `Screen`
- `Gönder`

`+`, `Mic` ve `Screen` butonları şimdilik gerçek capability başlatmaz. Tıklandıklarında Lina kısa ve güvenli bir placeholder mesajı gösterir:

- Dosya yükleme henüz aktif değildir.
- Mikrofon henüz aktif değildir.
- Ekran paylaşımı/görme henüz aktif değildir.

## Korunan Özellikler

- Normal mesaj gönderme.
- `Enter` ile gönderme.
- GUI input history için `↑` ve `↓`.
- Typing placeholder cleanup.
- Background model response thread.
- GUI error handling.
- Clear Chat.
- Copy Last Response.
- Status bar / model status.
- Memory komutları.
- Files komutları.
- Deterministic responses.
- Ollama unavailable fallback.
- Project/file/memory context akışı.

## Bilinen Sınırlar

- `+`, `Mic` ve `Screen` butonları gerçek dosya yükleme, mikrofon veya ekran capture başlatmaz.
- Conversation persistence yoktur; sidebar sohbet listesi placeholder amaçlıdır.
- Logo dosyası eksikse GUI metin başlıkla güvenli şekilde açılır.
- GUI hâlâ Tkinter tabanlıdır; ileri sürümlerde daha gelişmiş desktop framework değerlendirilebilir.
- Paketleme veya installer yoktur.
- Speech, Vision, Camera, Browser Automation ve Windows Automation henüz yoktur.

## Test

```powershell
python -m pytest
```

Son test sonucu:

- `381 passed`

## Çalıştırma

CLI:

```powershell
python main.py
```

GUI:

```powershell
python gui.py
```

## Manuel Smoke Test Önerisi

1. `python gui.py`
2. `selam` gönder.
3. `roadmap dosyasını özetle` gönder.
4. `bunu hatırla: kısa cevapları seviyorum` gönder.
5. `ne hatırlıyorsun` gönder.
6. `↑` / `↓` input history davranışını dene.
7. `+` butonuna bas.
8. `Mic` butonuna bas.
9. `Screen` butonuna bas.
10. `Yeni Sohbet` veya `Sohbeti Temizle` davranışını dene.
11. `Son Cevabı Kopyala` davranışını dene.

## Sonraki Adımlar

- Manuel GUI smoke test.
- Gerekirse küçük UI hotfix.
- `v0.5.1-alpha` tag değerlendirmesi.
- Sonraki büyük hedef olarak `v0.6.0-alpha` Speech Capability v1 hazırlığı.
