# Lina v0.4.0-alpha Release Notes

## Sürüm

`v0.4.0-alpha`

## Durum

Memory Capability v1 geliştirme hattı.

Bu sürüm, Lina'ya ilk gerçek local-first kalıcı hafıza altyapısını ekler. Memory v1 yalnız açık kullanıcı komutlarıyla kayıt yapar; otomatik hassas bilgi kaydetme, embedding, vector database veya cloud sync içermez.

## Öne Çıkanlar

- SQLite-backed `MemoryRepository`.
- `MemoryService`.
- Explicit memory intents.
- Deterministic memory command responses.
- ConversationService memory command routing.
- Memory context'in normal chat prompt akışına sınırlı eklenmesi.
- Config üzerinden memory ayarları.
- Bootstrap içinde GUI ve CLI için ortak MemoryService wiring.

## Memory Komutları

```text
bunu hatırla: kısa cevapları seviyorum
ne hatırlıyorsun
hafızanı listele
şunu unut: kısa cevapları seviyorum
hafızanı sıfırla
```

## Privacy ve Safety

- Lina v1'de yalnız explicit memory komutlarıyla kayıt yapar.
- Hassas bilgiler otomatik kaydedilmez.
- Memory local SQLite dosyasında tutulur.
- Varsayılan dosya yolu `data/lina_memory.sqlite3` değeridir.
- Runtime SQLite dosyaları Git'e eklenmez.
- Forget ve clear komutları deterministic olarak çalışır.

## Bilinen Sınırlamalar

- Vector database yoktur.
- Embeddings yoktur.
- Semantic search yoktur.
- Cloud sync yoktur.
- Multi-user memory yoktur.
- Long-term autonomous monitoring yoktur.
- Sensitive personal data auto-save yoktur.
- Agent memory planning yoktur.
- Memory UX / Recall polish bir sonraki hedef sürümdedir.

## Test

```bash
python -m pytest
```

Bu geliştirme sırasında tam test paketi `294 passed` sonucu vermiştir.

## Sonraki Adımlar

1. Manuel GUI/CLI smoke test.
2. Memory UX / Recall polish.
3. Memory kayıtlarının daha iyi kategorize edilmesi.
4. Forget/delete UX değerlendirmesi.
5. `v0.4.0-alpha` tag kararının manuel smoke test sonrası verilmesi.
