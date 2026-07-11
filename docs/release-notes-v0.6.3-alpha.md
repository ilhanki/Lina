# Lina v0.6.3-alpha Release Notes

## Durum

`v0.6.3-alpha`, Lina'nın masaüstü arayüzünü PySide6 tabanlı profesyonel bir GUI kabuğuna taşıyan alpha migration sürümüdür.

Bu sürüm yeni Brain, Memory, Files, Speech veya Automation capability'si eklemez. Odak, mevcut yetenekleri daha sürdürülebilir ve modern bir masaüstü UI katmanında sunmaktır.

## Öne Çıkanlar

- `python gui.py` artık varsayılan olarak PySide6 GUI başlatır.
- Legacy Tkinter GUI silinmedi; kısa vadeli fallback olarak korunur.
- PySide6 tabanlı sidebar, header, chat bubbles, composer ve status alanları eklendi.
- Lina logo/branding desteği PySide6 arayüzünde korunur.
- Model diagnostics ve speech status bilgileri GUI içinde görünür hale getirildi.
- `Mic` akışı PySide6 composer input'una transkripsiyon yazacak şekilde bağlandı.
- `Lina:Lina:` gibi tekrar eden assistant label prefixleri gerçek render path içinde normalize edilir.
- Mesaj kopyalama, oturum içi font büyütme/küçültme, input history ve yeni sohbet davranışları korunur.

## Korunan Davranışlar

- Ollama structured `/api/chat` akışı değişmedi.
- Brain, PromptBuilder, IntentAnalyzer ve ConversationService davranışları değiştirilmedi.
- Memory capability ve SQLite repository davranışı değiştirilmedi.
- Files capability read-only allowlist sınırları değiştirilmedi.
- Speech backend, faster-whisper ve sounddevice akışları değiştirilmedi.
- Shell command execution, genel dosya erişimi, browser automation veya Windows automation eklenmedi.

## Bilinen Sınırlamalar

- Bu sürüm UI migration sürümüdür; gerçek kullanıcı deneyimi manuel smoke testlerle izlenmelidir.
- Legacy Tkinter GUI geçici olarak korunur, ancak birincil geliştirme yönü PySide6 olacaktır.
- PySide6 dependency'si runtime bağımlılığıdır; testlerde `pytest-qt` development dependency olarak kullanılır.
- TTS, wake word, Vision, screen awareness ve Windows automation hâlâ kapsam dışıdır.

## Çalıştırma

```powershell
python gui.py
```

Terminal arayüzü:

```powershell
python main.py
```

## Test

```powershell
python -m pytest
```

Son doğrulama:

```text
474 passed
```

## Manuel Smoke Test Önerisi

1. `python gui.py`
2. İlk pencerenin PySide6 arayüzüyle açıldığını doğrula.
3. `selam naber` mesajını gönder.
4. `roadmap dosyasını özetle` mesajını gönder.
5. `bunu hatırla: kısa cevapları seviyorum` komutunu dene.
6. `Mic` ile kısa bir konuşmayı input alanına yazdır.
7. Transkripsiyonun otomatik gönderilmediğini doğrula.
8. `Lina:Lina:` veya transcript taklidi oluşmadığını kontrol et.

## Sonraki Adımlar

- v0.6.3-alpha manuel GUI smoke testi.
- PySide6 UI küçük UX buglarının release blocker / known issue ayrımıyla takip edilmesi.
- v0.7.0-alpha Vision / Screen Awareness öncesi güvenlik ve mimari planlama.
