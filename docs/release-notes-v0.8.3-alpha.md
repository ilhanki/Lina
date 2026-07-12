# Lina v0.8.3-alpha

## Durum

Alpha / aktif geliştirme.

## Lazy Conversation Creation ve Delete Lifecycle Fix

- `Yeni Sohbet` artık boş bir SQLite conversation satırı oluşturmaz; ephemeral draft olarak başlar.
- İlk gerçek kullanıcı mesajı conversation ve ilk user message ile aynı transaction içinde persist edilir.
- Boş draft sidebar, search, pin, archive, rename ve delete akışlarına dahil edilmez.
- Son kalıcı sohbet silindiğinde yeni boş database satırı oluşturulmaz ve welcome draft gösterilir.
- Birden fazla sohbet olduğunda aktif sohbet silme veya arşivleme sonrası en yeni görünür sohbet yüklenir.
- Legacy varsayılan başlıklı ve boş conversation kayıtları veri kaybı olmadan görünür listelerden gizlenir.

## Korunan sınırlar

- Brain, Ollama, Memory, Files, Speech ve Vision davranışları değiştirilmedi.
- Yeni dependency eklenmedi.
- Clear davranışı geri getirilmedi.

## Test

```text
python -m pytest
590 passed
```

Manuel GUI smoke testi release kapanışından önce yapılmalıdır.
