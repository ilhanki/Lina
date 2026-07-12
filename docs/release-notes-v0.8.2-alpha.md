# Lina v0.8.2-alpha

## Durum

Alpha release adayı.

## Öne Çıkanlar

- Conversation title ve user/assistant text araması.
- Türkçe karakter uyumlu local search.
- `Ctrl+F` ve `Escape` klavye akışları.
- `Sohbetler`, `Sabitlenenler` ve `Arşiv` görünümleri.
- Pin/unpin ve archive/unarchive context menu aksiyonları.
- Bugün, Dün, Son 7 Gün, Son 30 Gün ve Daha Eski grupları.
- Search result plain-text snippet gösterimi.
- Mevcut rename/delete ve recent activity davranışlarının korunması.

## Gizlilik ve Sınırlamalar

- Search yalnız title ve gerçek user/assistant text içeriklerini kapsar.
- Image bytes, Base64, thumbnail, tam dosya yolu, Memory içeriği ve raw file source aranmaz.
- Harici search engine, FTS dependency, embedding ve semantic search eklenmedi.
- Clear aksiyonu bu sürümde bulunmaz.
- Search result seçimi conversation'ı açar; matched message'a otomatik scroll bu sürümde sınırlıdır.

## Çalıştırma

```text
python gui.py
```

## Test

```text
python -m pytest
python -m compileall src gui.py main.py
```

## Sonraki Adım

`v0.9.0-alpha` için Settings & System Integration Foundation planlanacaktır.
