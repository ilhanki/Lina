# Lina v0.11.2-alpha — Realtime Camera Conversation

## Öne çıkanlar

- Kamera preview’ü varsayılan olarak aynalıdır; vision inference orijinal yönü korur ve change box koordinatları aynalı görünüme çevrilir.
- Lina yeni ve anlamlı kamera eylem/nesnelerini tek kısa Türkçe cümleyle yorumlayıp isteğe bağlı seslendirir.
- `Ne görüyorsun?`, `Elimde ne var?`, `Bu ne renk?`, `Bunu tarif et.` ve `Şu an ne yapıyorum?` soruları en güncel ephemeral kamera karesiyle yanıtlanır.
- Preview; konuşmalı kamera, otomatik yorum, sessize alma, şimdi bak ve kamerayı kapatma kontrollerini ve gerçek observing/analyzing/listening/speaking durumlarını gösterir.

## Performans ve tekrar politikası

- Change detection her capture’da çalışır; vision inference her frame’de çalışmaz.
- Varsayılan kamera analiz aralığı 3 saniye, yorum cooldown’ı 10 saniyedir.
- Aynı anda tek inference ve en fazla tek pending latest frame vardır.
- Aynı veya çok benzer yorum cooldown içinde bastırılır; farklı yeni olay hemen konuşabilir.
- Donanım/model yavaşsa Lina yalnız gerçek durumunu gösterir; “anlık” gecikme garantisi vermez.

## Gizlilik ve güvenlik

- Kamera yalnız açık kullanıcı onayıyla başlar ve görünür gösterge session boyunca kalır.
- Yalnız son frame bellekte tutulur; stop’ta temizlenir. Frame history, video, temp image, Base64 archive veya conversation DB image persistence yoktur.
- Vision, STT ve TTS yerel sağlayıcıları kullanır; cloud fallback yoktur.
- Kimlik/yüz tanıma ve duygu, sağlık, etnik köken veya biyometrik çıkarım yapılmaz.
- Change box’lar semantik nesne kutuları değildir.

## Bilinen sınırlar

- YOLO/ONNX/OpenCV tabanlı nesne detector/tracker yoktur; nesne açıklaması yalnız local vision modelinin tek-kare yorumudur.
- Özel acoustic echo cancellation yoktur; barge-in mevcut exact wake phrase korumasını kullanır.
- GTX 1650/4 GB VRAM performansı seçili Ollama vision modeline ve sahneye bağlıdır; gerçek Windows donanım smoke testi gerekir.
