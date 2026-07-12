# Lina v0.8.1-alpha

## Durum

Alpha release adayı.

## Öne Çıkanlar

- Persisted mesajların gerçek gönderim saatlerinin restart sonrasında korunması.
- UTC storage ve yerel saat presentation politikası.
- Legacy naive ve malformed timestamp için güvenli parse fallback'i.
- Recent activity temelli conversation sıralaması.
- Sidebar item'larında muted tarih metadata'sı.
- Header'da aktif conversation tarihi.
- Boş yeni sohbetler için zamana duyarlı profesyonel welcome alanı.
- İlk user mesajında welcome alanının temiz biçimde kaldırılması.

## Gizlilik ve Sınırlamalar

- Welcome alanı UI-only'dir; conversation database'ine veya Brain history'sine yazılmaz.
- Görsel bytes, Base64, thumbnail ve tam dosya yolu persistence dışında kalır.
- Conversation search, export/import, cloud sync ve pagination bu sürümde yoktur.

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

`v0.8.2-alpha` için Conversation Search & Management UX planlanacaktır.
