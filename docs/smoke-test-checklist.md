# Lina Smoke Test Checklist

Bu doküman release öncesi manuel doğrulama adımlarını tanımlar.

## v0.12.0-alpha Interaction Quality & Voice Stabilization

- `Yapay zekâ ajanı nedir?` sorusunda 2–4 cümlelik doğrudan Türkçe cevap, bağlamsız selamlama/dil karışması/persona karışması/tekrar olmamalı.
- `Nasılsın Lina?` kısa ve doğal yanıt vermeli; ansiklopedi paragrafına dönüşmemeli.
- Mikrofondan `Bugün saat yedide spor yapmayı hatırlat.` söyle; ilk/son kelime korunmalı ve duplicate mesaj oluşmamalı.
- Ayarlar > Konuşma’da kalibrasyonu çalıştır: iki saniye sessiz kal, istenen cümleyi söyle, sonucu onayla veya vazgeç; audio dosyası oluşmamalı.
- Wake testinde `Hey Lina`/`He Lina` algılanmalı; `Lira`, `Leyla`, `Hey millet` tetiklememeli ve test normal chat/Agent komutu başlatmamalı.
- Agent read-only özet görevinde plan/onay ve final durumunun ayarlara göre bir kez seslendirildiğini doğrula.
- Lina konuşurken barge-in yap; eski ses durmalı, wake listening geri dönmeli ve stale callback yeni sesi bozmamalı.
- Agent, Voice ve Vision birlikte açıkken ana durum metni aktif işi göstermeli; durum yalnız renkle anlatılmamalı.
- Gerçek WinRT voice, farklı mikrofonlar, sessiz/gürültülü oda, dar pencere, %85/%135 font, light/dark/system tema ve tray eşleşmesini Windows’ta manuel doğrula.
- Manual realtime camera validation deferred; kamera sistemi bu sprintte değiştirilmedi.

## Windows Agent Mode Foundation Smoke Test

- Temiz ayar profiliyle aç; Agent Mode kapalı, maksimum adım 8, maksimum replan 1, auto-start kapalı, plan göster açık ve persistent approval kilitli/açık olmalı.
- Normal “Agent mode güvenli mi?” ve “Bir plan nasıl hazırlanır?” sorularının sohbet olarak kaldığını doğrula.
- “Agent modunda hatırlatıcılarımı kontrol et” de; görünür plan kartı gelmeden tool çalışmamalı.
- Plan kartında özet, adım sayısı, tool adı, risk ve onay işaretini; Ayrıntıları Göster/Gizle davranışını kontrol et.
- Planı Başlat; read-only liste adımı bir kez çalışmalı, verifying ardından tamamlandı görünmeli.
- Persistent hatırlatıcı planında genel plan onayından sonra ayrı step approval beklenmeli; onaylamadan kayıt oluşmamalı.
- Onayla, Atla, Planı Düzenle ve İptal seçeneklerini ayrı oturumlarda dene; belirsiz “belki” hiçbir işlem yapmamalı.
- “Duraklat”, “Devam et”, “Agent görevini iptal et” ve “Şu anda hangi adımdasın?” metin/ses komutlarını dene.
- Tray’de Agent Modu, Aktif Görevi Göster, Duraklat/Devam Et ve İptal eylemlerini; aktif görev yokken disabled durumunu doğrula.
- Agent çalışırken sohbet değiştir; eski sonuç yeni sohbete yazılmamalı. İptal sonrası geç callback görünmemeli.
- Uygulamayı onay beklerken kapatıp aç; session interrupted olmalı, otomatik devam veya persistent tekrar olmamalı.
- Shell, PowerShell, browser, git, dosya yazma/silme, mouse/keyboard ve kamera/mikrofonu gizlice başlatma isteklerinin blocked/prohibited olduğunu doğrula.
- `data/agent-sessions.json` ve logları incele; raw arguments/tool payload, prompt, reasoning, reminder/memory content, dosya içeriği, image/audio/Base64 veya secret olmamalı.
- Tamamlanan/başarısız/onay bekleyen görev bildirimlerinin hassas içerik göstermediğini ve aynı session için duplicate bildirim oluşmadığını doğrula.
- Dark/light/system temaları ve %85/%100/%135 font ölçeğinde panel metninin, butonların ve status ikonlarının okunabildiğini kontrol et.
- Manual realtime camera validation deferred; mevcut kamera smoke listesini ayrıca kullanıcı tarafında uygula.

## Windows Realtime Camera Conversation Smoke Test

- Vision provider’ı ilk istekte boş, ikinci istekte geçerli cevap döndürecek şekilde test et; yalnız iki HTTP isteği ve geçerli kısa yorum görülmeli.
- İki isteği de whitespace/thinking-only döndür; otomatik yorum hata balonu oluşturmadan izlemeli ve sonraki değişiklikleri analiz edebilmeli.
- Aynı çift-boş senaryoda `Ne görüyorsun?` sorusunun “Görüntüyü şu anda yorumlayamadım. Birkaç saniye sonra tekrar deneyelim.” cevabını verdiğini doğrula.
- Retry sürerken kamerayı kapat; aktif response kapanmalı, üçüncü istek/stale sonuç/tekrarlanan hata oluşmamalı.
- Privacy loglarını incele; yalnız format, content length, chunk/retry sayacı, model ve süre olmalı; prompt, kullanıcı sorusu, raw response, image bytes veya Base64 olmamalı.

- Ayarlar → Vision’da Realtime camera conversation, Automatic camera commentary, Mirror camera preview ve Speak semantic changes varsayılan açık; cooldown `10 sn`, kamera analiz aralığı `3 sn` olmalı.
- `Kamerayı aç` onayından sonra preview’ün aynalı, inference sonucunun yön açısından doğal ve sol/sağ change box’ların aynalı görüntüyle hizalı olduğunu doğrula; mirror ayarını kapatıp tekrar dene.
- Preview’de `Konuşmalı Kamera`, `Otomatik Yorum`, `Sessize Al`, `Şimdi Bak` ve `Kamerayı Kapat` kontrollerini dene.
- El kaldır, fare/şişe göster, nesneyi kaldır ve kadraja yeni nesne sok; yalnız anlamlı değişikliklerde kısa Türkçe yorum duyulmalı, küçük hareketlerde konuşmamalı.
- Aynı nesneyi sabit tut; aynı/benzer cümle 10 saniye içinde tekrarlanmamalı. Farklı yeni olay cooldown beklemeden söylenebilmeli.
- Hands-free ile `Ne görüyorsun?`, `Elimde ne var?`, `Bu ne renk?`, `Bunu tarif et.` ve `Şu an ne yapıyorum?` sorularını dene; cevap o anki kareye dayanmalı ve seslendirilmelidir.
- Lina konuşurken `Hey Lina` ile barge-in yap; playback kesilmeli, yeni kamera sorusu yanıtlanmalı ve eski playback callback’i yeni durumu bozmamalı.
- Vision modelini durdur; `Görüntüyü şu anda yorumlayamıyorum.` görünürken preview ve kamera handle’ı açık kalmalı. STT/TTS’yi ayrı ayrı kullanılamaz yap; monitoring sürmeli.
- Kamerayı kapatıp `Ne görüyorsun?` de; `Kamera şu anda açık değil.` yanıtını doğrula.
- Stop, source switch ve gerçek exit sonrasında kamera LED’i sönmeli; `data`, conversation DB, logs ve temp altında frame, PNG/JPEG, Base64, video veya audio artefact oluşmamalı.

## Windows Live Preview & Monitoring Overlay Smoke Test

- Kamera monitoring’i onayla; `Lina Kamera` penceresinin gerçek canlı görüntü, cihaz adı ve `Kamera aktif` metnini gösterdiğini doğrula.
- Preview’ü yeniden boyutlandır; 16:9/4:3 görüntünün aspect ratio korunarak letterbox edildiğini doğrula.
- Preview’den Şimdi Analiz Et, Duraklat/Devam Et ve Takibi Durdur kontrollerini dene.
- Preview’i gizle; kamera session’ının sürdüğünü, ana panel ve tray’de `Kamera takibi aktif` göstergesinin kaldığını doğrula. Panelden aynı preview’ü yeniden göster.
- Kamera önünde belirgin hareket oluştur; beyaz `Değişiklik` kutularının doğru bölgeye ölçeklendiğini ve yaklaşık 2,5 saniye yenilenmezse silindiğini gözle.
- Sabit görüntü ve küçük sensör noise’ında kutu oluşmadığını; birden fazla bölgede en fazla beş kutu gösterildiğini doğrula.
- Kutuların nesne adı vermediğini ve yalnız `Değişiklik` etiketi taşıdığını doğrula.
- Full-screen monitoring başlat; doğru monitor kenarında beyaz border ve `Lina ekranı izliyor` etiketi görünmeli, mouse/keyboard etkileşimi engellenmemeli.
- Secondary monitor seç; capture ve border’ın aynı monitörde olduğunu doğrula.
- Region monitoring başlat; border yalnız seçilen alanı çevrelemeli ve `Lina bu bölgeyi izliyor` demeli.
- Windows display scale, resolution veya monitor origin değiştir; border geometry’nin güncellendiğini ya da geçersiz region session’ının güvenle durduğunu doğrula.
- Pause’da border’ın soluk/kesikli, resume’da normal olduğunu doğrula.
- Border’ı işletim sistemi üzerinden kapatmayı dene; gizli screen monitoring kalmamalı.
- Camera disconnect/permission failure, source switch, Vision disable, stop ve gerçek exit sonrasında preview, border, camera LED ve orphan window kalmadığını doğrula.
- `data`, conversation DB ve logs altında preview frame, PNG/JPEG, Base64 veya temp video oluşmadığını kontrol et.

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
