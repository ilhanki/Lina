# Lina v0.4.1-alpha Release Notes

## Durum

`v0.4.1-alpha`, `v0.4.0-alpha` Memory Capability v1 sonrasında gelen Memory UX / Recall polish sürümüdür.

Bu sürüm yeni büyük capability eklemez. Amaç, mevcut explicit memory davranışını daha anlaşılır, daha güvenli ve GUI içinde daha kullanışlı hale getirmektir.

## Öne Çıkanlar

- Memory recall/list cevapları numaralı liste formatına taşındı.
- Empty recall cevabı daha doğal hale getirildi.
- Forget ve clear cevapları daha açık Türkçe ifadelerle güncellendi.
- Sensitive memory guard eklendi.
- GUI input history navigation eklendi.
- Help/capabilities cevapları memory komutlarını gösterecek şekilde güncellendi.

## Mevcut Özellikler

- CLI ve Tkinter GUI üzerinden sohbet.
- Ollama ile local model entegrasyonu.
- PromptBuilder ve runtime context.
- Rule-based IntentAnalyzer.
- Deterministic responses.
- Session history.
- Project Awareness.
- Read-only Git context.
- Safe Tool Foundation ve ToolExecutionService.
- Model diagnostics.
- Local-first SQLite Memory Capability v1.
- Explicit memory commands.

## Memory UX

Desteklenen temel explicit memory komutları:

```text
bunu hatırla: kısa cevapları seviyorum
ne hatırlıyorsun
hafızanı listele
şunu unut: kısa cevapları seviyorum
hafızanı sıfırla
```

Memory kayıtları otomatik oluşturulmaz. Lina yalnızca kullanıcı açıkça memory komutu verdiğinde kayıt yapar.

## Sensitive Memory Guard

Lina, şifre, token, API key, kimlik ve ödeme bilgisi gibi hassas görünen içerikleri memory içine kaydetmez.

Bu koruma basit keyword tabanlıdır. Nihai güvenlik mekanizması değildir; yine de Memory v1 için güvenli varsayılan davranışı güçlendirir.

## GUI Input History

Tkinter GUI mesaj alanında:

- `↑` önceki gönderilen mesajı getirir.
- `↓` daha yeni mesaja döner.
- En sona gelindiğinde input temizlenir.
- Boş mesajlar history içine eklenmez.
- Art arda aynı mesaj tekrar history içine eklenmez.
- Bu history session-only çalışır ve SQLite memory sistemine yazılmaz.

## Bilinen Sınırlamalar

- Memory semantic search desteklemez.
- Vector database veya embeddings yoktur.
- Cloud sync yoktur.
- Autonomous memory extraction yoktur.
- Sensitive memory guard keyword tabanlıdır.
- Speech, vision, camera, browser automation ve Windows automation henüz yoktur.

## Çalıştırma

CLI:

```powershell
python main.py
```

GUI:

```powershell
python gui.py
```

## Test

```powershell
python -m pytest
```

Son doğrulama sonucu:

```text
321 passed
```

## Sonraki Adımlar

- Manuel GUI/CLI smoke test.
- `v0.4.1-alpha` tag değerlendirmesi.
- Sonraki ana milestone olarak Files Capability v1 hazırlığı.
