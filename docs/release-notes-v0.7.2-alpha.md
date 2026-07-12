# Lina v0.7.2-alpha

## Durum

Alpha release adayı.

## Öne Çıkanlar

- Tam ekran yakalama ve alan seçerek ekran görüntüsü alma.
- Composer attachment chip'inde görsel thumbnail, `Değiştir` ve `Kaldır` kontrolleri.
- Composer ve kullanıcı mesaj balonunda tıklanabilir görsel önizleme.
- Görsel analiz durumlarının görünür olması.
- Başarısız analiz sonrası görseli otomatik göndermeden yeniden analize hazırlama.
- Session-local görsel yaşam döngüsü; kalıcı veya bulut tabanlı görsel depolama yoktur.

## Sınırlamalar

- Vision yalnız açık kullanıcı eylemiyle başlar.
- Görsel analiz için yerel Ollama ve vision destekli model gerekir.
- Kamera, sürekli ekran izleme, OCR ve otomatik bilgisayar kontrolü bu sürümün kapsamı dışındadır.
- Görsel attachment'lar oturum süresince bellekte tutulur; kalıcı memory'ye yazılmaz.

## Çalıştırma

```text
python main.py
python gui.py
```

## Test

```text
python -m pytest
```

## Sonraki Adımlar

Conversation persistence foundation için mimari ve gizlilik planlaması yapılacaktır.
