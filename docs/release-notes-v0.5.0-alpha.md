# Lina v0.5.0-alpha Release Notes

## Durum

`v0.5.0-alpha`, Lina'ya ilk güvenli Files Capability v1 desteğini ekleyen alpha sürümüdür.

Bu sürüm genel dosya sistemi erişimi vermez. Amaç, yalnızca izinli proje dosyalarını read-only okuyabilen, test edilmiş ve sınırları açık bir dosya context altyapısı kurmaktır.

## Yeni Özellikler

- Read-only allowlisted file access.
- `FileAccessService`.
- File list/read/summarize/capability intentleri.
- Güvenli alias çözümleme:
  - `readme`
  - `roadmap`
  - `development log`
  - `architecture`
  - `vision`
  - `brain spec`
  - `conversation flow`
  - `release notes v0.4.1`
- Dosya içeriğini prompt içinde ayrı `File context` bölümü olarak kullanma.
- GUI normal chat input üzerinden dosya komutlarını gösterme.

## Güvenlik Sınırları

- Lina rastgele bilgisayar dosyalarını okuyamaz.
- Proje klasörü dışına çıkamaz.
- Absolute path istekleri reddedilir.
- Path traversal istekleri reddedilir.
- Allowlist dışı dosyalar okunmaz.
- Wildcard allowlist yoktur.
- Tüm `docs/` klasörü otomatik açılmaz.
- Dosya yazma, silme, taşıma, rename veya copy yoktur.
- Shell command execution yoktur.
- LLM kendi başına dosya okuyamaz.

## Kullanım Örnekleri

```text
hangi dosyaları okuyabiliyorsun
README dosyasını oku
roadmap dosyasını özetle
development log'da son ne var
docs/roadmap.md dosyasını oku
release notes v0.4.1'de ne yazıyor
bilgisayarımdaki dosyaları okuyabiliyor musun
```

Güvenli şekilde reddedilmesi beklenen örnekler:

```text
C:/Users/Ilhan/Desktop/test.txt dosyasını oku
../README.md dosyasını oku
secret.txt dosyasını oku
```

## Mevcut Özellikler

- CLI.
- Tkinter GUI.
- Ollama local model entegrasyonu.
- PromptBuilder.
- IntentAnalyzer.
- Deterministic responses.
- Session history.
- Runtime ContextManager.
- Project Awareness.
- Read-only Git context.
- Safe Tool Foundation.
- ToolExecutionService.
- Model diagnostics.
- Local-first SQLite Memory Capability v1.
- Sensitive memory guard.
- GUI input history.
- Read-only Files Capability v1.

## Bilinen Eksikler

- Semantic file search yoktur.
- Vector database veya embeddings yoktur.
- Genel dosya capability yoktur.
- Dosya yazma/düzenleme yoktur.
- Allowlist v1'de kod içinde sabittir.
- Büyük dosyalarda yalnız limitli preview/context kullanılır.
- Speech, vision, camera, browser automation ve Windows automation henüz yoktur.

## Test

Bu sprint boyunca ilgili testler çalıştırıldı:

```text
FileAccessService: 14 passed
Intent: 89 passed
Prompt/context: 20 passed
Conversation/bootstrap/files: 51 passed
Deterministic/conversation: 44 passed
GUI: 48 passed
```

Final release öncesi tam test:

```powershell
python -m pytest
```

## Sonraki Adımlar

- Manuel GUI/CLI smoke test.
- `v0.5.0-alpha` tag değerlendirmesi.
- Files Capability v1 sonrası Files UX polish veya Speech Capability v1 hazırlığı.
