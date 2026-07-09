# Lina v0.5.2-alpha Release Notes

## Sürüm

`v0.5.2-alpha`

## Durum

Alpha / Branding Polish.

Bu sürüm, `v0.5.1-alpha` Professional Chat UI Refresh sonrasında gelen küçük GUI/branding polish sürümüdür. Yeni backend capability eklemez; mevcut GUI içine Lina marka görselini güvenli fallback davranışıyla dahil eder.

## Öne Çıkanlar

- Lina logo asset'leri projeye eklendi.
- Sidebar branding alanı eklendi.
- Window icon yükleme desteği eklendi.
- Logo yokken veya yüklenemezken GUI'nin crash etmemesi sağlandı.
- Mevcut chat, memory ve files davranışları korundu.

## Eklenen Asset'ler

- `assets/branding/lina-logo.png`
- `assets/branding/lina-icon.png`

Bu dosyalar GUI tarafından opsiyonel olarak kullanılır. Dosyalar eksikse Lina metin başlıkla açılmaya devam eder.

## GUI Davranışı

- Sidebar üst kısmında Lina branding alanı bulunur.
- Logo dosyası varsa sidebar içinde gösterilir.
- Icon dosyası varsa pencere icon'u olarak denenir.
- Platform veya Tkinter icon desteği sorun çıkarırsa sessiz fallback uygulanır.

## Korunan Özellikler

- Normal chat akışı.
- Memory komutları.
- Files komutları.
- Deterministic responses.
- Ollama unavailable fallback.
- GUI input history.
- Placeholder action buttons.
- Clear Chat ve Copy Last Response.

## Bilinen Sınırlar

- Logo işleme için Pillow veya başka bir görsel işleme bağımlılığı eklenmedi.
- Logo boyutlandırma yalnızca Tkinter `PhotoImage` kabiliyetleriyle sınırlıdır.
- Bu sürüm Speech, Vision, Camera, Browser Automation veya Windows Automation eklemez.

## Test

```powershell
python -m pytest
```

Son test sonucu:

- `384 passed`

## Sonraki Adım

Sıradaki büyük hedef `v0.6.0-alpha` Speech Capability v1'dir. Speech geliştirmesine başlamadan önce kısa bir Speech Architecture & Safety Planning sprinti yapılmalıdır.
