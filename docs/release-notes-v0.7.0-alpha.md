# Lina v0.7.0-alpha Sürüm Notları

## Durum

`v0.7.0-alpha`, Screen Context Foundation geliştirmesini temsil eden alpha adayıdır. Release tag'i henüz oluşturulmamıştır.

## Öne Çıkanlar

- PySide6 composer içindeki `Ekran` butonu aktif hale getirildi.
- Capture yalnız açık kullanıcı tıklamasıyla başlar.
- Cursor'ın bulunduğu ekran, fallback olarak primary screen yakalanır.
- Screenshot için modal önizleme, metadata, gizlilik açıklaması ve onay akışı eklendi.
- Onaylanan görüntü session-local screen context olarak kompakt attachment chip ile gösterilir.
- Tek aktif screenshot replace edilebilir veya kullanıcı tarafından kaldırılabilir.
- Yeni sohbet, temizleme ve uygulama kapanışı context referansını temizler.

## Gizlilik ve Güvenlik

- Screenshot diske veya temp klasörüne yazılmaz.
- Memory, SQLite ve Files capability'lerine aktarılmaz.
- Ollama veya başka bir modele gönderilmez.
- Screenshot pixel içeriği loglanmaz.
- Sürekli ekran izleme, otomatik capture ve background capture yoktur.
- Yeni dependency eklenmemiştir; yalnız mevcut PySide6 / Qt ekran API'leri kullanılır.

## Bilinen Sınırlamalar

- OCR yoktur.
- Vision provider veya multimodal model entegrasyonu yoktur.
- Lina screenshot içeriğini henüz analiz edemez.
- Aynı anda yalnız tek aktif screen context desteklenir.
- Multi-monitor seçim dialog'u yoktur; cursor ekranı otomatik seçilir.
- Screenshot kalıcı tutulmaz ve uygulama kapandığında kaybolur.

## Test

```powershell
python -m pytest
```

Son doğrulama sonucu:

```text
508 passed
```

## Sonraki Adım

Sıradaki hedef `v0.7.1-alpha` Vision Provider Architecture çalışmasıdır. Görsel verinin bir modele gönderilmesi ancak ayrı izin, gizlilik, provider ve veri sınırı kararı sonrasında değerlendirilecektir.
