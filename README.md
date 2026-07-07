# Lina

> Bu proje kişisel kullanım amacıyla geliştirildiği için dokümantasyon dili Türkçedir. Kod tabanı ise uluslararası yazılım geliştirme standartlarına uygun olarak İngilizce yazılmaktadır.

Lina, Windows üzerinde yerel öncelikli çalışan kişisel yapay zeka asistanı projesidir. Projenin hedefi yalnızca sohbet eden bir bot oluşturmak değil; zaman içinde konuşabilen, ekranı anlayabilen, bilgisayarı kontrollü şekilde kullanabilen, yerel modellerle çalışabilen, hafızası olan ve geliştirici iş akışlarında yardımcı olabilen profesyonel bir masaüstü asistan geliştirmektir.

Bu depo şu anda `v0.3.0-alpha` release candidate seviyesindedir. Lina terminal ve Tkinter tabanlı masaüstü arayüz üzerinden çalışabilir, Ollama ile yerel modele bağlanabilir, bazı basit intent'leri deterministik olarak cevaplayabilir ve sınırlı proje farkındalığı için izinli dokümanlardan bağlam alabilir.

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
- Rule-based intent analyzer.
- Deterministic response flow.
- Sınırlı project awareness.
- SAFE tool foundation ve current time tool routing.
- CLI arayüzü.
- Tkinter tabanlı masaüstü GUI.
- Unit test altyapısı.

Planlanan uzun vadeli özellikler:

- Kalıcı Memory capability.
- Daha gelişmiş tool sistemi.
- Files capability.
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

Normal sohbet cevapları için Ollama'nın çalışıyor olması ve `config/default.toml` içinde yapılandırılmış modelin yerelde yüklü olması gerekir. `help`, `sen kimsin`, `neler yapabiliyorsun` ve `saat kaç` gibi bazı temel istekler LLM'e gitmeden deterministik olarak cevaplanır.

## Runtime Configuration

Temel çalışma ayarları `config/default.toml` içinde tutulur.

Önemli ayarlar:

- `logging.level`: Uygulama log seviyesi.
- `ollama.base_url`: Ollama HTTP adresi.
- `ollama.default_model`: Kullanılacak yerel model adı.
- `ollama.request_timeout`: Ollama istek timeout değeri.
- `runtime.conversation_history_limit`: Session içi konuşma geçmişi limiti.
- `runtime.project_context_max_characters`: İzinli proje dokümanı başına okunacak maksimum karakter sayısı.

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

- Kalıcı Memory sistemi yoktur.
- Genel dosya okuma/yazma capability'si yoktur.
- Shell command execution yoktur.
- Browser, camera, speech, vision ve Windows automation henüz uygulanmamıştır.
- Project awareness izinli dokümanlar ve okunabilir Git context (status, log, branch) ile sınırlıdır.
- Tool sistemi SAFE araçları çalıştırabilir, interaktif onay mekanizması (PermissionDecision UX) altyapısı vardır ancak UI entegrasyonu yoktur.
- GUI Tkinter tabanlı asistan arayüzüdür (v2); paketleme veya installer yoktur.

## Geliştirme Durumu

Mevcut durum: **v0.3.0-alpha release candidate**

Lina şu anda CLI ve masaüstü GUI üzerinden çalışabilen, Ollama ile yerel model cevabı alabilen, sınırlı intent routing, güvenilir cevap mekanizması (groundedness), Git proje farkındalığı ve güvenli tool temeline sahip erken aşama bir masaüstü asistanıdır.
