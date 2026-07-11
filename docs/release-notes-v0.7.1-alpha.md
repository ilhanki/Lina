# Lina v0.7.1-alpha Sürüm Notları

## Durum

`v0.7.1-alpha`, Local Vision Integration geliştirmesini temsil eden alpha adayıdır. Release tag'i henüz oluşturulmamıştır.

## Öne Çıkanlar

- Kullanıcı tarafından açıkça eklenen screen context yerel vision modeliyle analiz edilebilir.
- Normal sohbet ve görüntülü sohbet için ayrı model yapılandırması kullanılır.
- Varsayılan vision modeli `qwen3-vl:2b` olarak belirlendi.
- Ollama `/api/show` cevabındaki `vision` capability zorunlu olarak doğrulanır.
- Görüntü Ollama `/api/chat` son user mesajındaki `images` alanıyla gönderilir.
- Base64 yalnız provider payload sınırında ve bellekte oluşturulur.
- GUI vision isteğinde `Lina ekranı inceliyor...` durumunu gösterir.
- Başarılı analiz attachment'ı tüketir; hata attachment'ı yeniden deneme için korur.

## Güvenlik ve Gizlilik

- Capture yalnız kullanıcı `Ekran` butonuna bastığında gerçekleşir.
- Screenshot yalnız ilgili kullanıcı sorusu için local Ollama endpointine gönderilir.
- Screenshot diske, temp klasörüne, Memory'ye, SQLite'a, Files capability'sine veya conversation history'ye yazılmaz.
- Raw bytes, Base64 payload ve screenshot içeriği loglanmaz.
- Görsel içindeki talimatlar güvenilmeyen içerik kabul edilir.
- Vision cevabı tool, mouse, klavye, browser veya Windows automation çalıştıramaz.
- Vision başarısız olduğunda text model sahte görsel analiz fallback'i üretmez.
- Yeni Python dependency veya cloud API eklenmemiştir.

## Yapılandırma

```toml
[vision]
enabled = true
model = "qwen3-vl:2b"
request_timeout = 120.0
max_image_bytes = 8388608
consume_attachment_on_success = true
```

Model kurulumu:

```powershell
ollama pull qwen3-vl:2b
```

Qwen3-VL için resmî minimum sürüm Ollama `0.12.7` olarak belirtilir.

## Bilinen Sınırlamalar

- Aynı anda yalnız tek screenshot desteklenir.
- Region capture ve monitör seçim dialog'u yoktur.
- Sürekli ekran izleme, kamera, ayrı OCR paketi ve otomasyon yoktur.
- Vision doğruluğu yerel modele, ekran çözünürlüğüne ve görüntü netliğine bağlıdır.
- `v0.7.1-alpha` tag'i manuel gerçek GUI smoke testinden sonra değerlendirilecektir.

## Test

```text
541 passed
```

Yerel `qwen3-vl:2b` modeliyle bellek içi küçük PNG üzerinden `/api/chat` smoke testi başarıyla tamamlandı. Gerçek screenshot otomatik yakalanmadı.
