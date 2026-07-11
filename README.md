<p align="center">
  <img src="assets/branding/lina-logo.png" alt="Lina Logo" width="180">
</p>

# Lina

**Local-first çalışan, hafıza, güvenli proje dosyası erişimi, yerel konuşmayı metne çevirme ve modern PySide6 masaüstü arayüzü sunan kişisel yapay zekâ asistanı.**

> Bu proje kişisel kullanım amacıyla geliştirildiği için dokümantasyon dili Türkçedir. Kod tabanı ise uluslararası yazılım geliştirme standartlarına uygun olarak İngilizce yazılmaktadır.

## Proje Durumu

- **Sürüm:** `v0.6.3-alpha`
- **Durum:** Alpha / aktif geliştirme
- **Platform:** Windows masaüstü
- **Çalışma modeli:** Local-first

Lina; Ollama üzerinden yerel model kullanır, konuşma rollerini structured `/api/chat` mesajlarıyla ayırır, açık kullanıcı komutlarıyla yerel hafızaya kayıt yapar, yalnız izinli proje dosyalarını read-only okuyabilir ve push-to-talk ile Türkçe konuşmayı yerelde metne çevirebilir. PySide6 tabanlı modern masaüstü arayüzü günlük kullanıma odaklanırken capability sınırları privacy-first ve safety-first ilkeleriyle korunur.

## Öne Çıkan Özellikler

### Sohbet

- Ollama `/api/chat` entegrasyonu.
- Ayrı `system`, `user` ve `assistant` rolleriyle structured mesajlaşma.
- Oturum içi conversation history ve sınırlı history bounding.
- Basit istekler için deterministic intent cevapları.
- Model gerektirmeyen işlemler için no-model fallback.
- Türkçe-first, kısa ve dürüst cevap davranışı.

### Memory

- Yerel SQLite tabanlı kalıcı hafıza.
- Açık `remember`, `list`, `forget` ve `clear` işlemleri.
- Duplicate kayıt önleme.
- Sensitive memory guard.
- Kullanıcı istemeden hassas bilgi kaydetmeme.

```text
bunu hatırla: kısa cevapları seviyorum
ne hatırlıyorsun
şunu unut: kısa cevapları seviyorum
hafızanı sıfırla
```

### Files

- Yalnız açıkça allowlist içine alınmış proje dosyalarına read-only erişim.
- Path traversal ve absolute path reddi.
- Dosya yazma, silme, taşıma veya yeniden adlandırma yeteneği yoktur.
- Dosya özetlerinin okunan içerikle sınırlandırıldığı grounded summary akışı.

```text
hangi dosyaları okuyabiliyorsun
README dosyasını oku
roadmap dosyasını özetle
development log'da son ne var
```

### Speech

- Kullanıcı eylemiyle başlayan local push-to-talk STT.
- `sounddevice` ile sınırlı mikrofon kaydı.
- `faster-whisper` ile yerel Türkçe transcription.
- Varsayılan `base` model, `cpu` cihazı ve `int8` compute type.
- Transcription mevcut input alanına yazılır, otomatik gönderilmez.
- Ham ses kalıcı tutulmaz; always-on listening yoktur.
- TTS henüz aktif değildir.

### Masaüstü Arayüzü

- PySide6 tabanlı profesyonel koyu sohbet arayüzü ve Lina branding.
- Windows DPI awareness ve güvenli font fallback.
- Responsive sidebar, chat alanı ve composer.
- Lina ve kullanıcı için ayrı chat bubbles.
- Sidebar daraltma/genişletme.
- Oturum içi `A−` / `A+` font kontrolleri.
- Mesaj saatleri ve mesaj başına kopyalama.
- Buton tooltips ve belirgin disabled durumları.
- `↑` / `↓` ile input history.
- `Enter`: Gönder.
- `Shift+Enter`: Yeni satır.
- `Ctrl+L`: Composer'a odaklan.
- `Ctrl+N` veya `Ctrl+K`: Yeni sohbet.
- Eski Tkinter GUI kodu geçici legacy fallback olarak korunur; varsayılan `python gui.py` akışı PySide6 kullanır.

## Güvenlik ve Gizlilik

Lina'nın mevcut capability sınırları bilinçli olarak dardır:

- Genel dosya sistemi erişimi yoktur.
- Shell command execution yoktur.
- Dosya yazma, silme veya taşıma yoktur.
- Kamera, screen capture ve ekran anlama henüz aktif değildir.
- Browser veya Windows automation yoktur.
- Always-on microphone yoktur; kayıt yalnız kullanıcı eylemiyle başlar.
- Ses kayıtları kalıcı olarak saklanmaz.
- Memory yalnız explicit komutlarla yazılır.
- Hassas bilgiler otomatik kaydedilmez.
- Cloud sync yoktur.
- LLM kendi başına capability veya tool çalıştıramaz.

Bu sınırlar eksik özelliklerden ibaret değildir. Lina'nın ileride kazanacağı yeteneklerin kullanıcı kontrolü, açık izin ve denetlenebilir davranış üzerine kurulmasını sağlar.

## Kurulum

### Gereksinimler

- Windows 10 veya üzeri.
- Python `3.11` veya üzeri.
- Yerel olarak çalışan [Ollama](https://ollama.com/).
- Speech için kullanılabilir bir mikrofon ve Windows mikrofon izni.

```powershell
git clone https://github.com/ilhanki/Lina.git
cd Lina
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Geliştirme ve test bağımlılıkları:

```powershell
python -m pip install -r requirements-dev.txt
```

Varsayılan Ollama modelini hazırlamak için:

```powershell
ollama pull llama3.2:3b
ollama run llama3.2:3b
```

## Çalıştırma

Masaüstü GUI:

```powershell
python gui.py
```

Terminal arayüzü:

```powershell
python main.py
```

Testler:

```powershell
python -m pytest
```

## Speech İlk Kullanım Notu

İlk `Mic` kullanımında `faster-whisper` modeli indirilebilir veya yerel kullanım için hazırlanabilir. Bu işlem bağlantı ve sistem performansına göre zaman alabilir; sonraki kullanımlar local cache üzerinden devam eder. Model cache'i repository'ye commitlenmez.

Windows mikrofon izni gerekebilir. Transcription yalnız composer input alanına yazılır; kullanıcı kontrol etmeden otomatik gönderilmez.

## Konfigürasyon

Varsayılan ayarlar [`config/default.toml`](config/default.toml) içinde tutulur.

| Bölüm | Mevcut ayarlar | Amaç |
| --- | --- | --- |
| `ollama` | `base_url`, `default_model`, `request_timeout` | Ollama adresi, model ve HTTP timeout değeri |
| `runtime` | `conversation_history_limit`, `project_context_max_characters` | Oturum geçmişi ve proje context sınırları |
| `memory` | `enabled`, `database_path`, `max_context_items`, `max_context_characters` | Yerel memory deposu ve prompt context sınırları |
| `speech` | `enabled`, `stt_provider`, `model_size`, `language`, `device`, `compute_type`, kayıt ve sessizlik sınırları, `auto_send` | Yerel STT çalışma ve güvenlik ayarları |
| `logging` | `level` | Uygulama log seviyesi |
| `paths` | `data`, `logs`, `models`, `cache` | Uygulama çalışma dizinleri |

Files allowlist için şu anda ayrı bir `[files]` config bölümü yoktur. İzin verilen yollar uygulama tarafından açık ve sabit bir read-only listeyle yönetilir; genel dosya erişimine dönüşmez.

## Mimari

Lina, business logic ile kullanıcı arayüzünü ayıran modüler bir `src` yapısı kullanır:

- `core`: Application lifecycle, settings, paths, logging ve bootstrap.
- `brain`: Provider-independent orchestration, intent ve prompt contract'ları.
- `services`: Conversation ve capability koordinasyonu.
- `memory`: SQLite repository ve explicit memory işlemleri.
- `files`: Güvenli read-only allowlisted proje dosyası erişimi.
- `speech`: Kayıt, STT/TTS provider contract'ları ve speech orchestration.
- `integrations`: Ollama gibi dış sistem adapter'ları.
- `interfaces`: CLI, birincil PySide6 GUI ve legacy Tkinter GUI.

Ayrıntılı dokümanlar:

- [Mimari](docs/architecture.md)
- [Brain Specification v1](docs/brain-specification-v1.md)
- [Conversation Flow v1](docs/conversation-flow-v1.md)
- [Speech Architecture v1](docs/speech-architecture-v1.md)
- [Roadmap](docs/roadmap.md)
- [Development Log](docs/development-log.md)

## Roadmap Özeti

- `v0.4.x`: Local-first Memory Capability.
- `v0.5.x`: Files Capability, Professional GUI ve Branding.
- `v0.6.0-alpha`: Speech Skeleton ve GUI Mic Flow.
- `v0.6.1-alpha`: Local Push-to-Talk STT ve Structured Chat.
- `v0.6.2-alpha`: UI Readability & Accessibility Polish.
- `v0.6.3-alpha`: PySide6 Desktop UI Migration.
- `v0.7.0-alpha`: Vision / Screen Awareness planlaması.

Detaylı sürüm hattı için [docs/roadmap.md](docs/roadmap.md) dosyasına bakın.

## Bilinen Sınırlar

- Proje alpha aşamasındadır; API ve kullanıcı deneyimi değişebilir.
- Speech doğruluğu modele, mikrofona, işlemciye ve ortam gürültüsüne bağlıdır.
- TTS yoktur.
- Screen capture ve Vision yoktur.
- Kalıcı multi-session conversation history yoktur.
- Genel dosya sistemi erişimi yoktur.
- Browser ve Windows automation yoktur.
- PySide6 GUI yeni varsayılan arayüzdür; legacy Tkinter kodu kısa süreli geri dönüş yolu olarak korunur.
- PySide6 migration sonrası gerçek kullanıcı deneyimi manuel smoke testlerle izlenmeye devam etmelidir.

## Test Durumu

`v0.6.3-alpha` migration doğrulamasında tam test paketi:

```text
474 passed
```

Testler gerçek Ollama, mikrofon, Tkinter mainloop veya PySide6 event loop çalıştırmadan izole fake provider ve servislerle çalışır.

## Geliştirme İlkeleri

- Python `>=3.11` ve type hints.
- Standard library first yaklaşımı.
- YAGNI, küçük ve tek sorumluluklu commitler.
- Conventional Commits.
- Kod değişiklikleriyle birlikte zorunlu testler.
- Repository içinde secret, token veya kişisel veri tutmama.
- Local-first, privacy-first ve safety-first kararlar.

Katkı kuralları için [contributing.md](contributing.md) dosyasına bakın.

## Lisans

Bu proje şu anda kişisel kullanım amacıyla geliştirilen proprietary bir projedir. Kullanım ve dağıtım koşulları proje sahibi tarafından belirlenir.
