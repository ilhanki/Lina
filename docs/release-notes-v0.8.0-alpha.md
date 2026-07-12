# Lina v0.8.0-alpha

## Durum

Alpha release adayı.

## Öne Çıkanlar

- Local SQLite tabanlı kalıcı conversation history.
- Uygulama açılışında son session ve text mesajlarının geri yüklenmesi.
- Gerçek sidebar session listesi.
- Yeni sohbet, session seçimi, yeniden adlandırma ve silme.
- `Temizle` confirmation akışı.
- Brain model context'i için bounded conversation history.
- Persistence hatasında in-memory sohbet fallback'i.
- Vision mesajlarında güvenli metadata placeholder'ları.

## Gizlilik ve Sınırlamalar

- Screenshot, local image, thumbnail, raw bytes ve Base64 kalıcı olarak saklanmaz.
- Tam dosya yolu conversation database'e yazılmaz.
- Restart sonrasında vision görseli yeniden analiz edilemez; yalnız metadata placeholder gösterilir.
- Conversation search, pagination, export/import, cloud sync ve multi-user yapı bu sürümde yoktur.
- SQLite veritabanı local `data/conversations.sqlite3` altında tutulur.

## Çalıştırma

```text
python main.py
python gui.py
```

## Test

```text
python -m pytest
python -m compileall src gui.py main.py
```

## Sonraki Adım

`v0.8.1-alpha` için Conversation Search and Management kapsamı planlanacaktır.
