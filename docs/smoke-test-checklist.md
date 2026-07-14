# Lina Smoke Test Checklist

Bu doküman release öncesi manuel doğrulama adımlarını tanımlar.

## Windows Live Vision & Camera Smoke Test

- Ayarlar → Vision içinde Live Vision default değerlerinin açık, capture `2 sn`, minimum analiz `5 sn`, süre `5 dakika`, sensitivity `Orta` olduğunu doğrula; 1/5/15 dakika ve kullanıcı durdurana kadar seçenekleriyle restart persistence’ı kontrol et.
- `Kamerayı aç` de; explicit yerel analiz/no persistence onayı görünmeden kameranın başlamadığını doğrula. `Vazgeç` ile cihaz LED/handle’ının kapalı kaldığını kontrol et.
- Onayla; panelde metinsel `Kamera · Takip ediliyor`, cihaz adı, Şimdi Analiz Et, Duraklat ve Durdur kontrollerini gör.
- `Kamerayı aç, elimdeki şeye bak` ile tek kare analizi çalıştır; sonuç geldikten sonra kamera handle’ının bırakıldığını doğrula.
- Kamera unavailable ve permission denied durumlarında raw exception yerine sırasıyla `Kameraya erişilemiyor.` ve `Kamera izni verilmedi.` mesajlarını doğrula.
- `Ekranı takip et, hata çıkarsa söyle` akışını onayla; panel/tray privacy indicator ve kısa sonucu doğrula.
- `Bu bölgeyi izle, indirme bitince haber ver` de; alanı seç, aynı alanın periyodik yakalandığını ve ekran geometrisi değişince güvenli durduğunu doğrula.
- Aynı statik görüntüde vision isteklerinin tekrarlanmadığını; anlamlı değişiklikte analiz başladığını gözle.
- Analiz sürerken birkaç hızlı değişiklik üret; backlog oluşmadığını ve yalnız en son anlamlı durumun işlendiğini doğrula.
- Şimdi Analiz Et, Duraklat, Devam Et ve Durdur kontrollerini hem panelden hem tray’den doğrula.
- Voice feedback açık/kapalı, meaningful-only ve aynı sonuç cooldown davranışlarını dene; uzun sonuç panelde tam kalırken sesin kısa olduğunu kontrol et.
- Hands-free ile `Hey Lina` → kamera komutu → sesli onay → kısa sonuç akışını doğrula; barge-in ve stop komutunu dene.
- Conversation değiştir; Live Vision sonucunun yeni sohbet timeline’ına otomatik yazılmadığını, yalnız panelde kaldığını doğrula.
- Vision disabled ve Ollama unavailable durumlarında normal chat/voice akışının çalışmaya devam ettiğini doğrula.
- Görev Yöneticisi/Ollama ile aynı anda birden fazla vision inference olmadığını ve text/vision modellerinin 4 GB VRAM’de gereksiz birlikte resident kalmadığını gözle.
- Uygulamayı gerçek exit ile kapat; kamera LED’i, screen scheduler, pending inference, TTS ve live worker kalmadığını doğrula.
- `data`, `logs` ve conversation DB içinde PNG/JPEG signature, screenshot, Base64 veya video dosyası oluşmadığını kontrol et.

## Windows Wake Word, Hands-Free & Performance Smoke Test

- Ayarlar temizken hands-free ve wake word seçeneklerinin kapalı olduğunu; uygulama açılışında mikrofonun dinlemediğini doğrula.
- Hands-free’i aç; privacy metninde yerel listening, no persistence ve no cloud sınırlarını gör. `Vazgeç` ile mikrofonun kapalı kaldığını doğrula.
- `Etkinleştir` sonrasında header’da metinsel `Hey Lina bekleniyor` ve mic göstergesini gör.
- “Hey Lina” de; `Dinliyorum` → `Yazıya çeviriyorum` → `Düşünüyorum` → `Konuşuyorum` → cooldown → `Hey Lina bekleniyor` akışını doğrula.
- `he lina` ve `hey, lina` varyasyonlarını dene; “şey Lina”, yalnız “Lina” ve ortam konuşmasının false wake üretmediğini gözle.
- Wake sonrasında normal komut söyle; sessizlikle kaydın otomatik bittiğini ve metnin composer’da beklemeden gönderildiğini doğrula.
- Yalnız sessizlikte `Bir şey duyamadım.`, anlaşılmayan seste `Seni anlayamadım.` geri bildirimini doğrula.
- Reminder veya Memory store başlat; confirmation sorusunun seslendirildiğini, `evet/onayla/tamam` ile çalıştığını, `hayır/iptal/vazgeç` ile iptal olduğunu doğrula.
- Confirmation’a belirsiz cevap ver; kalıcı işlemin çalışmadığını ve `Onaylıyor musun, iptal mi ediyorsun?` sorusunu duy.
- Confirmation’a cevap verme; yaklaşık 25 saniyede işlemin güvenli iptal edildiğini doğrula.
- Lina konuşurken kısa gürültü yap; playback’in kesilmediğini doğrula. Ardından “Hey Lina” diyerek wake-phrase barge-in ile sesi kes ve yeni komut ver.
- Playback bitince yaklaşık 1–3 saniye cooldown olduğunu ve Lina’nın kendi TTS’sinin wake üretmediğini doğrula.
- Header ve tray’den dinlemeyi duraklat/sürdür; hands-free kapatıldığında mikrofonun hemen bırakıldığını doğrula.
- Pencereyi tray’e kapat; ayar açıksa wake listening’in sürdüğünü ve tray tooltip’in durumu gösterdiğini doğrula.
- Seçili mikrofonu ayır; `Seçili mikrofon kullanılamıyor. Varsayılan mikrofon kullanılıyor.` fallback’ini doğrula.
- Ayarlar’dan mikrofon listesini yenile ve `Mikrofonu Test Et` sonucunu doğrula; UI bloklanmamalı.
- Uygulamayı gerçek exit ile kapat; wake, recorder, STT, TTS ve scheduler worker’larının kalmadığını doğrula.

- Sesli yanıt kapalıyken normal chat ve tool cevaplarının yazılı kaldığını doğrula.
- Sistem Türkçe sesi varsa seç, “Merhaba İlhan” yanıtını rate/volume değiştirerek dinle.
- Sistem TTS yoksa “Sesli yanıt şu anda kullanılamıyor.” durumunu ve yazılı cevabın korunduğunu doğrula.
- Push-to-talk `insert` modunda transcription’ın composer’a geldiğini, `send` modunda otomatik gönderildiğini doğrula.
- Lina konuşurken mic’e bas; sesin kesilip listening durumuna geçtiğini doğrula.
- Header ve tray “Sesi Durdur” ile yalnız playback’in durduğunu, mesajın silinmediğini doğrula.
- Input device veya local STT yoksa wake seçeneklerinin unavailable kaldığını ve normal text chat’in çalıştığını doğrula.
- Performans Testi sırasında UI’ın responsive kaldığını; first token, token/sn, total ve mevcut token/load alanlarının gösterildiğini doğrula.
- Keep-alive seçeneklerini, warm-up kapalı varsayılanını ve restart persistence’ı doğrula.
- Ardışık normal chat → vision → normal chat ile iki modelin gereksiz birlikte resident kalmadığını Ollama/VRAM üzerinden gözle.
- New chat, conversation switch ve gerçek exit sırasında mic/playback/benchmark/warm-up worker kalmadığını doğrula.

## Ön Koşullar

- Python sanal ortamı aktif olmalı.
- Geliştirme bağımlılıkları kurulmuş olmalı.
- Normal sohbet testi için Ollama çalışıyor olmalı.
- `config/default.toml` içinde tanımlı model yerelde yüklü olmalı.

## Otomatik Test

```powershell
python -m pytest
```

Beklenen sonuç:

- Tüm testler başarılı olmalı.

## CLI Smoke Test

```powershell
python main.py
```

Kontroller:

- CLI banner görünür.
- `help` kısa yardım cevabı verir.
- `Saat kaç?` yerel saati döndürür.
- `Sen kimsin?` Lina kimlik cevabı verir.
- `Neler yapabiliyorsun?` mevcut gerçek yetenekleri dürüstçe söyler.
- `selam Lina` normal chat olarak Ollama'ya gider.
- `exit` veya `quit` uygulamayı kapatır.

## GUI Smoke Test

```powershell
python gui.py
```

Kontroller:

- Lina penceresi açılır. Özel header ("Lina", "Personal AI Assistant") ve sağ alt köşede status bar ("Bağlanıyor...", "Bağlı") görünür.
- Input alanı focus alır.
- Üstte "Clear Chat" ve "Copy Last Response" butonları mevcuttur.
- `help` kısa yardım cevabı verir.
- `Saat kaç?` yerel saati döndürür.
- `Sen kimsin?` Lina kimlik cevabı verir.
- `Neler yapabiliyorsun?` mevcut gerçek yetenekleri dürüstçe söyler.
- `selam Lina bugün nasılsın?` normal chat olarak Ollama'ya gider.
- Cevap beklenirken input alanı disable olur, status bar "Düşünüyor..." veya benzeri durumu yansıtır.
- Cevap gelince input tekrar aktif olur.
- Yeni mesajlarda sohbet alanı aşağı kayar.
- "Copy Last Response" butonuna basıldığında son asistan cevabı panoya kopyalanır.
- "Clear Chat" butonuna basıldığında sohbet geçmişi temizlenir.

## Ollama Kapalıyken Davranış

Ollama kapalıyken GUI başlat.

Beklenen sonuç:

- Sağ alt status bar "Ulaşılamıyor" (Kırmızı) durumuna geçer.
- Ollama kapalıyken mesaj atıldığında uygulama çökmez.
- Traceback gösterilmez.
- Kullanıcıya kısa Türkçe hata mesajı gösterilir.

## Project Awareness Smoke Test

CLI veya GUI içinde şu mesajları dene:

```text
Lina projesinin durumu ne?
Şu an hangi branch üzerindeyim ve working tree nasıl?
Bugün Lina projesinde ne yaptık?
Son sprintlerde ne eklendi?
```

Beklenen sonuç:

- Lina, izinli proje dokümanlarına ve aktif okunabilir Git verisine (branch, status, log) dayalı cevap verir.
- Sahte GitHub URL, sahte commit veya sahte dosya uydurmaz.
- Bilmediği noktaları dürüstçe sınırlar.

## Safe Tool Smoke Test

```text
Saat kaç?
```

Beklenen sonuç:

- Cevap Brain/Ollama'ya gitmeden SAFE tool akışı üzerinden üretilir.
- Shell, dosya sistemi veya tehlikeli işlem çalışmaz.

## Bilinen Sınırlar

- Bu checklist otomatik release testi değildir.
- GUI görsel doğrulaması manuel yapılır.
- Ollama model kalitesi yerel modele bağlıdır.
