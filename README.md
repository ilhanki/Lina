# Lina

> Bu proje kişisel kullanım amacıyla geliştirildiği için dokümantasyon dili Türkçedir. Kod tabanı ise uluslararası yazılım geliştirme standartlarına uygun olarak İngilizce yazılmaktadır.

Lina, Windows üzerinde yerel öncelikli çalışan kişisel yapay zeka asistanı projesidir. Projenin hedefi yalnızca sohbet eden bir bot oluşturmak değil; zaman içinde konuşabilen, ekranı anlayabilen, bilgisayarı kontrollü şekilde kullanabilen, yerel modellerle çalışabilen, hafızası olan ve geliştirici iş akışlarında yardımcı olabilen profesyonel bir masaüstü asistan geliştirmektir.

Bu depo şu anda `v0.5.1-alpha` Professional Chat UI Refresh geliştirme hattındadır. `v0.5.0-alpha` Files Capability v1 tag'i oluşturulmuş, ardından Tkinter GUI daha modern bir sohbet uygulaması düzenine taşınmıştır. Lina terminal ve Tkinter tabanlı masaüstü arayüz üzerinden çalışabilir, Ollama ile yerel modele bağlanabilir, bazı basit intent'leri deterministik olarak cevaplayabilir, sınırlı proje farkındalığı için izinli dokümanlardan bağlam alabilir, açık kullanıcı komutlarıyla yerel SQLite hafızasına bilgi kaydedebilir ve yalnızca allowlist kapsamındaki proje dosyalarını read-only okuyabilir.

## Projenin Amacı

Lina'nın amacı, kişisel bilgisayarda çalışan güvenilir, modüler ve uzun ömürlü bir yapay zeka asistanı oluşturmaktır.

Temel öncelikler:

- Yerel öncelikli çalışma.
- Modüler ve genişletilebilir mimari.
- Gereksiz üçüncü parti bağımlılıklardan kaçınma.
- Kod ile kullanıcı arayüzü arasında net ayrım.
- Yetki, güvenlik ve kullanıcı onay mekanizmalarını erken tasarım kararı olarak ele alma.
- Her yeni özelliği test edilebilir ve izole bir modül olarak geliştirme.

## Uzun Vadeli Vizyon

Lina zamanla şu yeteneklere sahip bir masaüstü asistanına dönüşmelidir:

- Yerel LLM sağlayıcılarıyla konuşma.
- Farklı model sağlayıcılarını destekleme.
- Konuşma ve kullanıcı hafızası.
- Ses tanıma ve metinden sese konuşma.
- Wake word desteği.
- Ekran görüntüsü alma ve ekranı anlama.
- Kamera ve görsel algı desteği.
- Windows otomasyonu.
- Dosya yönetimi.
- Tarayıcı otomasyonu.
- Araç ve plugin sistemi.
- Çoklu ajan mimarisi.
- Masaüstü GUI.
- Gerekirse yerel API katmanı.
- Kod geliştirme süreçlerinde yardımcı modüller.

## Planlanan Özellikler

Mevcut çalışan özellikler:

- `Brain` orchestration katmanı.
- `ModelProvider` contract.
- Ollama provider entegrasyonu.
- Default system prompt ve prompt builder.
- Runtime conversation context.
- Session içi geçici conversation history.
- Local-first SQLite Memory Capability v1.
- Read-only allowlisted Files Capability v1.
- Explicit memory commands.
- Rule-based intent analyzer.
- Deterministic response flow.
- Sınırlı project awareness.
- SAFE tool foundation ve current time tool routing.
- CLI arayüzü.
- Modern Tkinter masaüstü GUI; sidebar, chat bubbles, composer ve placeholder action butonları.
- Unit test altyapısı.

Planlanan uzun vadeli özellikler:

- Memory UX / Recall polish.
- Daha gelişmiş tool sistemi.
- Speech ve TTS.
- Vision ve screen understanding.
- Windows automation.
- Browser automation.
- Multi-agent architecture.
- Packaging ve release süreci.

## Geliştirme Yol Haritası

Ayrıntılı yol haritası [docs/roadmap.md](docs/roadmap.md) dosyasında tutulur.

Mevcut release candidate, core altyapı, Brain v1, Ollama entegrasyonu, conversation flow, GUI v2, project awareness v2 (Git destekli) ve safe tool foundation v2 (PermissionDecision UX) aşamalarını içerir.

## Kullanılan Teknolojiler

Planlanan temel teknoloji tercihleri:

- Python 3.11 veya üzeri.
- `src` layout.
- `pytest` test yapısı.
- `ruff` lint ve format standardı.
- Standart kütüphane öncelikli geliştirme.
- Yerel yapılandırma için `toml` ve `.env` yaklaşımı.
- İlk LLM entegrasyonu için Ollama.

Üçüncü parti bağımlılıklar yalnızca gerçek ihtiyaç oluştuğunda ve mimari gerekçesi açıklandıktan sonra eklenecektir.

## Kurulum

Bu aşamada proje yalnızca mimari ve dokümantasyon iskeletidir.

Önerilen geliştirme ortamı:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Gelecekte bağımlılıklar eklendiğinde:

```powershell
pip install -r requirements.txt
```

Geliştirme araçları için:

```powershell
pip install -r requirements-dev.txt
```

Yerel ortam değişkenleri için:

```powershell
Copy-Item .env.example .env
```

## Kullanım

CLI arayüzünü çalıştırmak için:

```powershell
python main.py
```

Masaüstü GUI arayüzünü çalıştırmak için:

```powershell
python gui.py
```

Normal sohbet cevapları için Ollama'nın çalışıyor olması ve `config/default.toml` içinde yapılandırılmış modelin yerelde yüklü olması gerekir. `help`, `sen kimsin`, `neler yapabiliyorsun`, `saat kaç`, basit selamlaşmalar, bilgisayar kontrolüyle ilgili güvenlik soruları, explicit memory komutları ve güvenli dosya listeleme/okuma komutları gibi bazı temel istekler LLM'e gitmeden deterministik olarak cevaplanır.

### Modern GUI

`v0.5.1-alpha` ile Tkinter GUI profesyonel sohbet uygulaması düzenine taşınmıştır.

- Sol tarafta sohbet listesi için sidebar bulunur.
- GUI, `assets/branding` altındaki Lina logo/icon dosyalarını destekler.
- Logo yoksa uygulama güvenli fallback ile yalnızca metin başlık kullanarak açılır.
- `Yeni Sohbet` mevcut oturumu temizler.
- Ana alanda Lina mesajları solda, kullanıcı mesajları sağda bubble görünümüyle gösterilir.
- Alt composer içinde `+`, `Mic`, `Screen` ve `Gönder` butonları bulunur.
- `+`, `Mic` ve `Screen` butonları şimdilik gerçek capability başlatmaz; güvenli placeholder Lina mesajı gösterir.
- `Enter` ile gönderme, `↑` / `↓` input history, `Sohbeti Temizle`, `Son Cevabı Kopyala`, typing placeholder ve background model response akışı korunur.

Memory komut örnekleri:

```text
bunu hatırla: kısa cevapları seviyorum
ne hatırlıyorsun
hafızanı listele
şunu unut: kısa cevapları seviyorum
hafızanı sıfırla
```

Memory v1 privacy notu:

- Lina v1'de yalnız explicit memory komutlarıyla kayıt yapar.
- Hassas bilgiler otomatik kaydedilmez.
- Memory local SQLite dosyasında tutulur.
- Varsayılan database yolu `data/lina_memory.sqlite3` değeridir ve Git'e eklenmez.

### Files Capability v1

Lina v1'de genel dosya sistemi erişimine sahip değildir. Sadece proje içindeki açıkça izin verilmiş dosyaları read-only okuyabilir.

Örnek komutlar:

```text
hangi dosyaları okuyabiliyorsun
README dosyasını oku
roadmap dosyasını özetle
development log'da son ne var
docs/roadmap.md dosyasını oku
```

Güvenlik sınırları:

- Lina rastgele bilgisayar dosyalarını okuyamaz.
- `C:/Users/...` gibi absolute path istekleri reddedilir.
- `../` path traversal istekleri reddedilir.
- Dosya yazma, silme, taşıma, rename veya copy yeteneği yoktur.
- Allowlist wildcard kullanmaz; tüm `docs/` klasörü otomatik açılmaz.

### Memory UX Notları

- Lina yalnızca açık memory komutlarıyla kayıt yapar; normal sohbeti otomatik hafızaya yazmaz.
- Şifre, token, API key, kimlik ve ödeme bilgisi gibi hassas içerikler memory kaydı olarak reddedilir.
- Aynı bilgi art arda tekrar kaydedilmeye çalışılırsa Lina duplicate kayıt oluşturmaz.

### GUI Input History

Tkinter GUI içinde mesaj yazma alanındayken:

- `↑` önceki gönderilen mesajı getirir.
- `↓` daha yeni gönderilen mesaja döner.
- History session-only çalışır; SQLite memory sistemiyle karışmaz.
- Boş mesajlar ve art arda aynı mesajlar input history içine eklenmez.

## Runtime Configuration

Temel çalışma ayarları `config/default.toml` içinde tutulur.

Önemli ayarlar:

- `logging.level`: Uygulama log seviyesi.
- `ollama.base_url`: Ollama HTTP adresi.
- `ollama.default_model`: Kullanılacak yerel model adı.
- `ollama.request_timeout`: Ollama istek timeout değeri.
- `runtime.conversation_history_limit`: Session içi konuşma geçmişi limiti.
- `runtime.project_context_max_characters`: İzinli proje dokümanı başına okunacak maksimum karakter sayısı.
- `memory.enabled`: Memory capability açık/kapalı durumu.
- `memory.database_path`: Local SQLite memory dosyasının yolu.
- `memory.max_context_items`: Prompt'a eklenecek maksimum memory kaydı.
- `memory.max_context_characters`: Prompt'a eklenecek maksimum memory context karakter sayısı.

Eksik optional runtime ayarları güvenli default değerleriyle çalışır.

## Testler

Tam test paketini çalıştırmak için:

```powershell
python -m pytest
```

Manuel doğrulama adımları için [docs/smoke-test-checklist.md](docs/smoke-test-checklist.md) dosyasına bakın.

## Proje Yapısı

```text
Lina/
  config/
  data/
  docs/
  logs/
  models/
  cache/
  scripts/
  src/
    lina/
      agents/
      automation/
      core/
      integrations/
      interfaces/
      memory/
      services/
      speech/
      tools/
      utils/
      vision/
  tests/
```

Kısa açıklama:

- `src/lina/core`: Config, logging, lifecycle ve ortak kontratlar.
- `src/lina/services`: Uygulama use-case akışları.
- `src/lina/integrations`: Dış sistem adapter'ları.
- `src/lina/interfaces`: CLI, GUI veya API gibi kullanıcıya dönük katmanlar.
- `src/lina/tools`: Lina'nın kontrollü çalıştırabileceği araç altyapısı.
- `src/lina/agents`: Gelecekteki çoklu ajan yapısı.
- `src/lina/memory`: Hafıza ve geri çağırma sistemleri.
- `src/lina/speech`: Ses tanıma, TTS ve wake word altyapısı.
- `src/lina/vision`: Ekran, OCR ve görsel algı altyapısı.
- `src/lina/automation`: Windows otomasyonu.
- `tests`: Kaynak yapısını takip eden testler.

Mimari yön güncellendikçe bu yapı kontrollü şekilde `brain` ve `capabilities` katmanlarıyla genişletilecektir.

## Geliştirme Standartları

Geliştirme kuralları [contributing.md](contributing.md) dosyasında tanımlanır.

Temel kurallar:

- Dokümantasyon Türkçe yazılır.
- Kod, dosya adları, klasör adları ve API isimleri İngilizce yazılır.
- Python kodunda type hint kullanılır.
- Her modül tek sorumluluk prensibine göre tasarlanır.
- Yeni bağımlılık eklenmeden önce gerekçesi açıklanır.
- Runtime bağımlılıkları ve geliştirme bağımlılıkları ayrı tutulur.
- Business logic UI katmanından ayrı tutulur.
- Test edilebilirlik mimari kararların parçasıdır.
- YAGNI prensibi uygulanır; kullanılmayan soyutlama eklenmez.

## Katkıda Bulunma

Bu proje kişisel kullanım amacıyla geliştirilmektedir. Katkı kuralları ve kod standardı için [contributing.md](contributing.md) dosyasına bakın.

Commit mesajları İngilizce ve Conventional Commits formatında yazılmalıdır.

Örnek:

```text
docs: update architecture roadmap
feat: add configuration loader
test: cover event bus behavior
```

## Lisans

Bu aşamada proje özel kullanım için geliştirilmekte ve lisans durumu `Proprietary` olarak kabul edilmektedir.

## Mevcut Sınırlamalar

- Memory v1 yalnız explicit komutlarla kayıt yapar; otomatik memory extraction yoktur.
- Files v1 yalnız allowlist kapsamındaki proje dosyalarını read-only okuyabilir; genel dosya okuma/yazma capability'si yoktur.
- Shell command execution yoktur.
- Browser, camera, speech, vision ve Windows automation henüz uygulanmamıştır.
- Project awareness izinli dokümanlar ve okunabilir Git context (status, log, branch) ile sınırlıdır.
- Tool sistemi SAFE araçları çalıştırabilir, interaktif onay mekanizması (PermissionDecision UX) altyapısı vardır ancak UI entegrasyonu yoktur.
- GUI Tkinter tabanlı modern sohbet arayüzüdür; `+`, `Mic` ve `Screen` butonları şimdilik placeholder davranışına sahiptir.
- Paketleme veya installer yoktur.

## Geliştirme Durumu

Mevcut durum: **v0.5.1-alpha Professional Chat UI Refresh geliştirme hattı**

Lina şu anda CLI ve modern Tkinter masaüstü GUI üzerinden çalışabilen, Ollama ile yerel model cevabı alabilen, sınırlı intent routing, güvenilir cevap mekanizması (groundedness), Git proje farkındalığı, güvenli tool temeli, explicit local SQLite memory altyapısı ve read-only allowlisted proje dosyası erişimine sahip erken aşama bir masaüstü asistanıdır.
