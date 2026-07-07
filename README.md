# Lina

> Bu proje kişisel kullanım amacıyla geliştirildiği için dokümantasyon dili Türkçedir. Kod tabanı ise uluslararası yazılım geliştirme standartlarına uygun olarak İngilizce yazılmaktadır.

Lina, Windows üzerinde yerel öncelikli çalışan kişisel yapay zeka asistanı projesidir. Projenin hedefi yalnızca sohbet eden bir bot oluşturmak değil; zaman içinde konuşabilen, ekranı anlayabilen, bilgisayarı kontrollü şekilde kullanabilen, yerel modellerle çalışabilen, hafızası olan ve geliştirici iş akışlarında yardımcı olabilen profesyonel bir masaüstü asistan geliştirmektir.

Bu depo şu anda temel mimari ve proje standartları aşamasındadır. Henüz asistan davranışı, LLM entegrasyonu, hafıza sistemi, araç sistemi veya masaüstü arayüzü uygulanmamıştır.

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

- `Brain` katmanı ile prompt, context, model seçimi ve cevap orkestrasyonu.
- `capabilities` yaklaşımı ile bağımsız yetenek modülleri.
- Event-aware mimari ile modüller arası gevşek bağlılık.
- Ollama ile ilk yerel model entegrasyonu.
- İleride LM Studio, OpenAI, Gemini gibi sağlayıcılar için provider adapter yapısı.
- Hafıza için yerel kalıcı depolama.
- Güvenli tool execution ve permission sistemi.
- GUI katmanı gelmeden önce test edilebilir servis mimarisi.

## Geliştirme Yol Haritası

Ayrıntılı yol haritası [docs/roadmap.md](docs/roadmap.md) dosyasında tutulur.

Özet milestone sırası:

1. Proje standartları ve mimari temel.
2. Core infrastructure.
3. Brain v1.
4. LLM provider entegrasyonu.
5. Conversation flow.
6. Memory capability.
7. Tool sistemi.
8. Files capability.
9. Speech capability.
10. Vision capability.
11. Automation capability.
12. Agent mimarisi.
13. Desktop GUI.
14. Local API.
15. Paketleme, güvenlik ve ürünleştirme.

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

## Geliştirme Durumu

Mevcut durum: **Milestone 0 - Proje Standartlarını Oluşturma**

Henüz uygulama özelliği geliştirilmemiştir. Bu aşamada amaç; dil standardı, mimari yön, yol haritası, katkı kuralları ve geliştirme prensiplerini netleştirmektir.
