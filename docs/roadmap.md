# Lina Yol Haritası

Bu yol haritası Lina'nın geliştirme sırasını tanımlar. Amaç, erken aşamada karmaşık özelliklere atlamadan sağlam bir temel kurmak ve her capability'yi kontrollü şekilde büyütmektir.

## Mevcut Durum: v0.3.0-alpha Release Candidate

Tamamlanan ana başlıklar:

- Proje standartları ve dokümantasyon temeli.
- Core infrastructure.
- Brain v1.
- Ollama provider entegrasyonu.
- Conversation flow.
- CLI arayüzü.
- Tkinter Desktop UI v2 (Durum çubuğu ve profesyonel görünüm).
- Runtime conversation context.
- Project awareness v2 (İzinli dokümanlar ve Git desteği).
- Safe tool foundation v2 (PermissionDecision UX yapısı).
- SAFE tool routing ile current time cevabı.

Henüz kapsam dışı olan büyük başlıklar:

- Kalıcı Memory.
- Genel dosya capability'si.
- Shell command execution.
- Browser, camera, speech, vision ve Windows automation.
- Multi-agent architecture.
- Packaging, installer ve release automation.

## Milestone 0: Proje Standartları

Amaç:

- Dil standardını netleştirmek.
- Dokümantasyonu Türkçeye çevirmek.
- Kodlama ve mimari standartları belirlemek.
- Yol haritasını yazılı hale getirmek.

Neden ilk sırada:

Proje uzun vadeli olacağı için ekip tek kişi olsa bile yazılı standartlara ihtiyaç vardır. Bu standartlar teknik borcu azaltır.

Teknolojiler:

- Markdown.
- `pyproject.toml`.
- Python 3.11+ hedefi.

## Milestone 1: Core Altyapısı

Amaç:

- Configuration loading.
- Logging setup.
- Path management.
- Application lifecycle.
- Application context.
- Temel exception yapısı.
- İlk unit test altyapısı.

Neden bu sırada:

Tüm sonraki modüller config, logging ve lifecycle altyapısına ihtiyaç duyacaktır.

Kapsam dışı:

- LLM entegrasyonu.
- Brain implementasyonu.
- Memory implementasyonu.
- Vision implementasyonu.
- Speech implementasyonu.
- Automation implementasyonu.
- Tool sistemi.
- Event bus implementasyonu.

Teknolojiler:

- Python standard library.
- `tomllib`.
- `logging`.
- `pathlib`.
- `dataclasses`.
- `pytest` geliştirme bağımlılığı.

Geliştirme notları:

- Runtime bağımlılıkları `requirements.txt` içinde tutulur.
- Geliştirme araçları `requirements-dev.txt` içinde tutulur.
- `ApplicationContext` yalnızca `settings`, `paths` ve `logger` taşır.
- Kullanılmayan soyutlama, factory, manager veya registry yapısı eklenmez.
- Her değişiklik küçük ve tek sorumluluklu commit'lerle yapılır.

## Milestone 2: Brain v1

Amaç:

- Kullanıcı mesajını işleyen temel brain orchestration katmanını kurmak.
- Prompt ve context hazırlığı için ilk contract'ları tanımlamak.
- Model provider bağımlılığını soyutlamak.

Neden bu sırada:

Lina'nın LLM sağlayıcısına doğrudan bağımlı kalmaması için brain katmanı erken tanımlanmalıdır.

Teknolojiler:

- Python Protocol.
- `dataclasses`.
- Type hints.

## Milestone 3: LLM Provider Entegrasyonu v1

Amaç:

- İlk model sağlayıcı olarak Ollama entegrasyonunu eklemek.
- Provider contract üzerinden model çağrısı yapmak.

Neden bu sırada:

Gerçek model cevabı alınmadan conversation flow doğrulanamaz.

Teknolojiler:

- Ollama HTTP API.
- Üçüncü parti HTTP client ihtiyacı ayrıca değerlendirilecektir.

## Milestone 4: Conversation Flow

Amaç:

- Kullanıcı mesajı, brain çağrısı, model cevabı ve conversation event'lerini düzenlemek.

Neden bu sırada:

Memory, speech ve GUI gibi modüller conversation flow üzerine bağlanacaktır.

Teknolojiler:

- Application services.
- In-memory event bus.
- Unit tests.

## Milestone 5: Memory Capability v1

Amaç:

- Konuşma geçmişi ve temel kullanıcı hafızası için yerel kalıcılık sağlamak.

Neden bu sırada:

Asistanın kişiselleşmesi için hafıza erken ama conversation flow sonrasında eklenmelidir.

Teknolojiler:

- SQLite.
- Repository pattern.
- Python standard library `sqlite3`.

## Milestone 6: Tool Sistemi v1

Amaç:

- Tool contract, registry, result ve permission altyapısını kurmak.

Neden bu sırada:

Automation, files, browser ve coding capability'leri güvenli tool sistemi olmadan eklenmemelidir.

Teknolojiler:

- Python Protocol.
- `dataclasses`.
- Permission policy.

## Milestone 7: Files Capability v1

Amaç:

- Güvenli dosya listeleme, okuma ve sınırlı yazma işlemlerini desteklemek.

Neden bu sırada:

Dosya yönetimi asistanın en temel pratik yeteneklerinden biridir; automation'dan önce güvenli permission modeli test edilir.

Teknolojiler:

- `pathlib`.
- Tool system.
- Permission checks.

## Milestone 8: Speech Capability v1

Amaç:

- Speech-to-text ve text-to-speech için adapter altyapısını kurmak.

Neden bu sırada:

Metin tabanlı conversation flow oturduktan sonra ses katmanı bir interface/capability olarak bağlanabilir.

Teknolojiler:

- Whisper, faster-whisper, Vosk veya benzeri çözümler değerlendirilecektir.
- TTS için Piper, pyttsx3 veya alternatifleri değerlendirilecektir.

## Milestone 9: Vision Capability v1

Amaç:

- Ekran görüntüsü alma, OCR ve temel ekran analizini desteklemek.

Neden bu sırada:

Windows automation güvenli çalışabilmek için ekran farkındalığına ihtiyaç duyacaktır.

Teknolojiler:

- `mss`.
- Pillow.
- OCR aracı ayrıca değerlendirilecektir.

## Milestone 10: Automation Capability v1

Amaç:

- Windows üzerinde güvenli ve onay kontrollü otomasyon sağlamak.

Neden bu sırada:

Automation riskli bir capability olduğu için tool, permission, event ve vision altyapısından sonra gelmelidir.

Teknolojiler:

- pywinauto.
- pyautogui.
- Windows API adapter'ları.

## Milestone 11: Agents v1

Amaç:

- Planner, executor ve reviewer gibi rolleri destekleyen ilk agent mimarisini kurmak.

Neden bu sırada:

Agent yapısı ancak brain, memory ve tool sistemi olgunlaştıktan sonra anlamlıdır.

Teknolojiler:

- Hafif, proje içi agent orchestration.
- Dış framework yalnızca açık ihtiyaç oluşursa değerlendirilir.

## Milestone 12: Desktop GUI

Amaç:

- Lina için masaüstü kullanıcı arayüzü geliştirmek.

Neden bu sırada:

Önce iş mantığı ve servisler test edilebilir hale gelmelidir. GUI business logic taşımamalıdır.

Teknolojiler:

- PySide6 veya alternatif masaüstü arayüz çözümleri değerlendirilecektir.

## Milestone 13: Local API

Amaç:

- GUI, script veya diğer istemcilerin Lina ile yerel API üzerinden konuşmasını sağlamak.

Neden bu sırada:

API katmanı, temel servisler kararlı hale geldikten sonra eklenmelidir.

Teknolojiler:

- FastAPI.
- WebSocket desteği.
- Local-only güvenlik kontrolleri.

## Milestone 14: Ürünleştirme

Amaç:

- Paketleme, kurulum, yedekleme, güvenlik ve bakım süreçlerini tamamlamak.

Neden bu sırada:

Önce ürün davranışı netleşmeli, sonra dağıtım ve bakım süreçleri olgunlaştırılmalıdır.

Teknolojiler:

- PyInstaller veya Nuitka.
- Structured logging.
- Backup/export mekanizmaları.
