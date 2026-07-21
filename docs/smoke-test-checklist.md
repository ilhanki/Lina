# Lina Smoke Test Checklist

## v0.14.0-alpha Full-System Product Hardening

- [x] Tam otomatik regresyon paketi ilk final turunda `1384 passed` verdi.
- [x] Codex resume takip cümlesinde yalnız yeni bağlayıcı objective stdin promptuna taşınıyor.
- [x] Test istenen Codex görevi command category + başarılı exit kanıtı olmadan tamamlanmıyor.
- [x] Dosya değişikliği olan Codex session diff incelemesi tamamlanana kadar `reviewing` kalıyor.
- [x] Qt worker ve speech geç callback testleri kapanış sonrasında result/state üretmiyor.
- [x] Agent cancellation token'ı çalışan step controller lock'ını tutarken executor'a ulaşıyor.
- [x] TXT/MD/PY/JSON/CSV/PDF/DOCX/XLSX attachment çıkarımı, size/truncation/secret/bozuk belge sınırlarıyla test edildi.
- [x] Vision kapalıyken belge ekleme çalışıyor; görsel/kamera otomatik başlamıyor.
- [x] Memory hassas direct write ve conversation stale selection regresyonları kapalı.
- [x] TTS path, diff, log, JSON, code, URL ve Base64 payload okumuyor.
- [x] Version contract `0.14.0a0 / v0.14.0-alpha`.
- [ ] Windows üzerinde gerçek mikrofon STT ve WinRT TTS manuel doğrulandı.
- [ ] Kamera permission denial, preview, multi-monitor region ve DPI manuel doğrulandı.
- [ ] Authenticated Codex read-only + test evidence + resume smoke başarılı oldu. Release makinesi `Not logged in` durumunda.
- [ ] Narrator/NVDA keyboard-only ve %100/%125/%150 DPI görsel turu ürün sahibi tarafından tamamlandı.

İşaretlenmemiş maddeler sahte biçimde tamamlanmış sayılmaz; gerçek auth, donanım veya insan değerlendirmesi gerektirir.

## v0.13.2-alpha Codex Production Hardening

- [x] WindowsApps launch edilemezken sınırlı discovery npm `codex.cmd` adayını seçti; ACL/PATH/paket değişmedi.
- [x] Seçilen CLI `codex-cli 0.144.6`; root/exec/resume help kapsamları ayrı capability snapshot'a dönüştü.
- [x] `.cmd` invocation typed quoting, `%` koruması, filtered environment, stdin prompt ve `shell=False` sözleşmesini geçti.
- [x] Session ID, workspace fingerprint, CLI minor sürümü, auth, retention ve kullanıcı onayı resume builder'da zorunlu.
- [x] Restart recovery unfinished kaydı interrupted yapıyor; remote reference yoksa resume sunmuyor ve tool çalıştırmıyor.
- [x] Git ve non-Git snapshot limitleri, add/modify/delete/rename/mode, hunk, binary, large, truncation ve secret değişiklikleri fixture'larda doğrulandı.
- [x] Diff dialog dosya/özet/diff, arama, wrap, kopya ve kabul/ret kararlarını gösteriyor; ret rollback yapmıyor.
- [x] Runtime approval otomatik kabul edilmiyor; görev paused oluyor.
- [x] Timeout/cancel/shutdown cleanup ve gerçek yerel child-process sonlandırması orphan bırakmıyor.
- [x] JSONL BOM, CRLF, partial, malformed, unknown, missing-final, Unicode, huge-line ve session ID regresyonları geçiyor.
- [x] Token/private key/JWT/connection string ve hassas path redaction testleri geçiyor; sıradan teknik metin korunuyor.
- [x] Tek gerçek read-only smoke öncesi/sonrası `git status` ve binary diff boş, HEAD aynı.
- [ ] Gerçek read-only smoke başarılı sonuç üretti. Release makinesinde resmi auth `Not logged in`; tek deneme `execution_failed` oldu.
- [ ] Gerçek session resume başarılı oldu. Auth olmadığı için çalıştırılmadı; help kapsamı ve command builder doğrulandı.
- [ ] Gerçek ücretli modification/diff review tamamlandı. Auth olmadığı için yapılmadı; fake transport + gerçek geçici Git fixture'ı kullanıldı.
- [ ] Windows GUI üzerinde son manuel görsel/erişilebilirlik turu ürün sahibi tarafından tamamlandı.

Bu işaretlenmemiş maddeler otomatik test başarısızlığı değildir; auth/hizmet veya manuel kullanıcı doğrulaması gerektiren release sınırlarıdır.

## v0.13.1-alpha Real Codex CLI Transport

- [ ] Başlangıçta `codex --version` ve `codex login status` yalnız resmi CLI üzerinden çalışır; token veya credential içeriği görünmez.
- [ ] Inspector CLI yok, oturum gerekli, güncelleme gerekli ve hazır durumlarını doğru gösterir.
- [ ] ChatGPT login yalnız kullanıcı confirmation’ından sonra ayrı resmi CLI terminalinde başlar.
- [ ] Device Code düğmesi yalnız `--device-auth` gerçek help çıktısında varsa görünür.
- [ ] Logout uyarısı “Bu işlem Codex CLI oturumunu bu cihazda kapatacak.” der; Lina conversation/memory verisini silmez.
- [ ] API key alanı yoktur; key clipboard, process argümanı, log veya GUI state içine alınmaz.
- [ ] “Lina, Codex ile bu projeyi analiz et.” workspace → plan → approval → status → exec → verification akışını izler.
- [ ] `codex exec` argument listesiyle ve `shell=False` çalışır; prompt command line yerine stdin’den verilir.
- [ ] Read-only görevde sandbox `read-only`, modification görevinde `workspace-write` olur; `never`, `--yolo`, bypass ve `--add-dir` yoktur.
- [ ] JSONL partial/unknown/malformed eventler GUI’yi bozmaz; ham terminal logu chat’e basılmaz.
- [ ] Runtime approval event otomatik onaylanmaz; görev manual approval required sonucu ile durur.
- [ ] Cancel ve uygulama shutdown sonrası Codex/child process kalmaz; timeout typed ve kısa kullanıcı mesajı üretir.
- [ ] `.env`, `auth.json`, credentials/secrets, PEM/key/PFX/P12/CRT, SSH key ve workspace escape engellenir.
- [ ] Secret benzeri output maskelenir, persistence’a girmez ve verification fail olur.
- [ ] Read-only smoke öncesi/sonrası `git status` aynı; `git diff --check` temizdir.
- [ ] TTS yalnız “Codex çalışıyor”, “Analiz tamamlandı”, “Codex oturumu gerekli” gibi kısa sabit durumları okur; path/diff/log okumaz.
- [ ] `codex doctor --json` yalnız CLI help bunu doğrularsa çalışır; redacted rapor history’ye yazılmaz.
- [ ] `python -m pytest`, compileall, PySide6 import ve `git diff --check` geçer.

## v0.13.0-alpha Reliability Hotfix

- [ ] “Merhaba Lina, kendini tek cümlede tanıt.” doğal, tek cümlelik Türkçe yanıt verir.
- [ ] “Bugün için bana kısa bir çalışma planı hazırla.” süre, odak bloğu, ara ve tekrar içeren günlük plan verir; Agent lifecycle listesi vermez.
- [ ] Liste/tuple açıklaması değiştirilebilirlik farkını doğal Türkçeyle anlatır.
- [ ] Operational Codex komutu normal typing/model yoluna girmez; workspace kartını açar.
- [ ] Aynı Codex komutunun tekrarı aynı workspace akışını üretir; duplicate dispatch oluşmaz.
- [ ] “Codex nedir?” normal bilgi sorusu olarak kalır.
- [ ] `.env`, credential, key/certificate istekleri workspace seçiminden önce engellenir.
- [ ] `C:\` veya tüm disk taraması engellenir.
- [ ] Workspace sonrası read-only plan ve approval kartı görünür.
- [ ] Approval sonrası transport yoksa controlled unavailable mesajı görünür; sahte başarı ve ham exception yoktur.
- [ ] Prompt/persona/role marker sızıntısı repair edilir veya güvenli fallback'e döner.
- [ ] Rejected yanıt DB/history/TTS'ye girmez; sonraki cevap temiz context kullanır.
- [ ] `python -m pytest`, compileall ve `git diff --check` geçer.

## v0.13.0-alpha Codex Bridge Foundation

- [ ] Tools içinde “Codex ile Çalış” görünür; aktif değilken inspector yer kaplamaz.
- [ ] “Codex ile analiz et” komutu workspace seçimi ister ve tüm bilgisayarı taramaz.
- [ ] Env, key/cert, credentials ve secrets dosyaları context dışında kalır.
- [ ] Plan gösterilmeden ve kullanıcı onaylamadan client çağrılmaz.
- [ ] Modification görevi Onayla / Reddet / Düzenle kartı gösterir.
- [ ] Progress typed eventlerden güncellenir; ham event ve terminal logu kullanıcıya verilmez.
- [ ] Sonuç verification sonrası tamamlanır; stale/kanıtsız sonuç başarı sayılmaz.
- [ ] Geçmişte yalnız metadata bulunur; prompt, secret ve dosya içeriği bulunmaz.
- [ ] “Lina Codex ile bu projeye bak” sesli komutu confirmation akışına gider.
- [ ] Codex güvenlik ilkeleri ayarlardan kapatılamaz.
- [ ] `python -m pytest`, compileall ve `git diff --check` geçer.

Bu doküman release öncesi manuel doğrulama adımlarını tanımlar.

## Premium Assistant Desktop Experience

- 1440×900 dark/light/system temalarında 292 px sidebar + chat düzenini; isteğe bağlı 344 px inspector üçüncü kolonunu; 1100 px’de sağ drawer’ı; 800 px’de 64 px sidebar + overlay drawer’ı doğrula.
- Drawer’ı araç düğmesi, scrim, close ve Escape ile aç/kapat; kapatınca klavye odağının araç düğmesine döndüğünü doğrula.
- Sidebar’da şeffaf Lina işareti, gerçek son mesaj preview/time, debounce search ve rename/pin/archive/delete context eylemlerini doğrula. Sahte profil, Pro planı veya klasör ağacı görünmemeli.
- Kısa/uzun user ve assistant mesajları, başlık/list/bold/inline code/fenced code, streaming finalize, image preview ve hover eylemlerinde taşma/HTML çalıştırma olmadığını doğrula.
- Composer multiline auto-grow, Enter/Shift+Enter, Dosya/Mikrofon/Ekran/Daha Fazla, send/stop, attachment remove/change ve kompakt görünümü doğrula.
- Sağ panel ana sayfasında Sohbet, Sesli sohbet, Görsel anlama, Dosya anlama, Hatırlatıcılar ve Bellek kartlarının 2×3 düzende, yatay scrollbar olmadan göründüğünü doğrula. Agent/Codex yalnız ilgili gelişmiş ayar etkinse eklenmeli.
- Bellek bölümünde yalnız gerçek ve hassas olmayan 2–4 özet/empty state; yerel saklama bölümünde gerçek data/cache ölçümü ve kullanıcı eylemli klasör açmayı doğrula. Sahte kota, hesap veya Pro verisi olmamalı.
- Settings’te theme, sidebar başlangıcı, right panel görünürlük/genişlik, message genişliği ve son bölüm tercihlerini kaydet; restart ve schema v9→v10 migration’ını doğrula.
- Ctrl+N, Ctrl+K, Ctrl+Shift+P, Ctrl+,, Ctrl+L, Ctrl+F ve Escape’i; accessible name/tooltip, focus ring, yalnız renge bağlı olmayan status’ları Narrator/NVDA ile doğrula.
- Türkçe kalite hatası üret; invalid draft’ın history/DB/TTS/notification’a gitmediğini, yalnız bir non-streaming repair yapıldığını ve gerekirse sabit güvenli fallback’in gösterildiğini doğrula.
- `scripts/render_ui_preview.py` ile sabit `2026-01-20 10:30 UTC` saati altında dark/light/compact PNG üret; iki ardışık çalıştırmada zaman kaynaklı kart/sıra farkı olmamalı.
- Windows’ta minimize/maximize/restore/snap/drag/resize, %125/%150 DPI, çoklu monitör, tray close/exit, aktif worker kapanışı, mikrofon/kamera privacy lifecycle’ını smoke et.

## v0.12.1-alpha Agent Reliability, Task Templates & Recovery

- Agent Mode kapalıyken doğal “yarın sporu hatırlat” isteğinin normal routing davranışını koruduğunu; açıkken güvenli şablona eşlenip eksik yalnız saat bilgisini sorduğunu doğrula.
- “Hatırlatıcı nedir?”, “Agent neden hata yapar?” ve düşük güvenli belirsiz isteklerin hazır göreve dönüşmeden normal sohbette kaldığını doğrula.
- Hazır Görevler’i composer, command palette ve menüden aç; yalnız available reminders, Memory, Files ve explicit Vision capability’lerinin listelendiğini doğrula.
- Hatırlatıcı oluşturma formunda tarih/saat/tekrar alanlarını doldur; plan görünmeden ve plan+step onayı verilmeden kayıt oluşmadığını doğrula.
- Bu hafta hatırlatıcı özeti ile yarın çakışma kontrolünü çalıştır; tarih filtresini ve aynı saate denk gelen kayıtların sabit sırasını doğrula.
- Plan Review’da salt-okunur optional adımı atla/kaldır, güvenli sırayı değiştir ve regenerate et; invalid dependency ile persistent risk düşürmenin reddedildiğini doğrula.
- Değiştirilen planın added/removed/moved/changed farklarını incele; eski plan onayının yeni revision için geçerli olmadığını doğrula.
- Task Center V2’de aktif, onay bekleyen, duraklatılmış, yarım, tamamlanan, başarısız ve iptal edilen sekmeleri; boş durumları ve klavye erişimini doğrula.
- Çalışan veya onay bekleyen görev sırasında uygulamayı gerçek exit ile kapatıp yeniden aç; görevin bir kez `interrupted` görünmesini, hiçbir tool’un otomatik çalışmamasını ve tek genel recovery bildirimi gelmesini doğrula.
- Yarım görevin geçmiş kopyasını seç; raw parametre saklanmadığından şablonu yeniden açıp değerleri doğrulama mesajını gör. Canlı terminal görevi safe clone edildiğinde yeni session kimliği ve yeni plan onayı oluşmalı.
- Read-only araçta yapay timeout/transient hata oluştur; yalnız bir retry olmalı. Persistent timeout/uncertain sonucunda retry olmamalı ve “mevcut kaydı kontrol et” recovery eylemi görünmeli.
- Aynı Agent onay/tamamlanma olayının tray ve TTS’te yalnız bir kez üretildiğini; “Sesi Durdur”un Agent görevini iptal etmediğini doğrula.
- Ayarlar’da hazır görev önerisi, başlangıç recovery bildirimi ve 7/30/90 gün/sınırsız geçmiş seçeneklerini değiştir; restart persistence ve terminal geçmiş temizliğini doğrula.
- Task Center/Inspector teknik görünümünde raw kullanıcı isteği, reminder/Memory içeriği, dosya içeriği, typed argüman, prompt, exception veya reasoning görünmediğini doğrula.

## v0.12.0-alpha Complete Product Experience Redesign

- İlk açılışta sohbet ana odak, inspector kapalı, Agent/Vision büyük panelleri gizli, composer odakta ve header minimal olmalı.
- Sidebar’da yalnız Lina, Yeni Sohbet, arama ve sohbet listesi görünmeli; local/device metni ve utility kısayolları ana yüzeyi doldurmamalı.
- Composer’da Dosya, Mikrofon, Ekran ve Gönder görünmeli; kompakt düzende taşınan eylemler Daha Fazla menüsünde mevcut işlevlerini korumalı.
- Bildirim ikonu yalnız okunmamış bildirim olduğunda görünmeli; sıfır durumda header’da yer kaplamamalı.
- Yeni sohbet, kısa/uzun cevap, kod bloğu, çok uzun user mesajı, streaming, repair ve error durumlarında yatay taşma veya duplicate final olmamalı.
- Yapay zekâ ajanı nedir? sorusu 2–4 doğal Türkçe cümle vermeli; Vietnamca/İngilizce sızıntısı, bozuk ek, ilgisiz selamlama ve tekrar olmamalı; reddedilen draft TTS’ye gitmemeli.
- Sidebar’da collapse/expand, search/Escape, sohbet seçimi, rename/pin/archive/delete ve tooltip’leri klavye/fareyle doğrula.
- 760 px minimum pencerede 64 px ikon sidebar, kompakt header/composer ve dikey suggestion’lar çakışmamalı; yatay scrollbar oluşmamalı.
- 1080p/maximized pencerede timeline ve composer aynı merkez kolonda, assistant satırları okunabilir ve sağda anlamsız boşluk olmamalı.
- Inspector sistem, Agent ve Vision ayrıntılarıyla açılıp kapanmalı; dar pencereye geçince güvenle kapanmalı.
- Ctrl+Shift+P palette’i açmalı; arama, ok/Enter, unavailable action ve Escape/focus restore davranışını doğrula.
- Agent plan approval, running progress, step approval, pause/resume/cancel, completed/failed/interrupted ve inspector özetlerini ayrı ayrı dene.
- Voice ready/listening/transcribing/speaking/error, stop speech, hands-free ve wake durumları unified status’ta metinle anlaşılmalı.
- Kamera/screen monitoring açıkken kaynak ve gizlilik metni görünmeli; stop/exit sonrası preview, overlay, timer ve cihaz handle’ı kalmamalı.
- Notification Center’da yeni/düzenle/tamamla/ertele; silmede varsayılan Vazgeç davranışını kontrol et.
- Ayarlar aramasıyla theme, density, calibration, wake, Agent ve privacy tercihlerini bul; Kaydet/Uygula/Vazgeç/Varsayılanlar davranışını dene.
- Ayarlar navigasyonunun yedi bölüm olduğunu; uzun Ses ve Gelişmiş sayfalarında dikey scroll olup yatay scroll olmadığını doğrula.
- Dark, light ve system temayı runtime değiştir; aktif draft, conversation ve panel state kaybolmamalı.
- %85, %100, %125 ve %135 fontta buton kesilmesi, sidebar taşması, kayıp focus ring veya okunamayan disabled state olmamalı.
- Yalnız klavye ile yeni sohbet, arama, composer, gönderme, palette, settings ve dialog iptal akışını tamamla; status sadece renge dayanmamalı.
- Pencere konumunu secondary/negatif-origin monitörde kaydet; yeniden açılışta görünür alanda restore edildiğini ve kaldırılan monitör sonrası primary ekrana clamp edildiğini doğrula.
- Tray’den aç, yeni sohbet, hands-free, Agent, Vision, bildirimler, ayarlar ve gerçek çıkışı dene; duplicate action veya orphan process kalmamalı.

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
python -m ruff check src tests scripts
```

Beklenen sonuç:

- Tüm testler ve lint kontrolü başarılı olmalı.

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

- Lina penceresi açılır; sidebar, minimal sohbet header’ı, empty state ve tek composer görünür.
- Composer input alanı focus alır.
- Yeni sohbet, arama, session listesi, kısa durum ve Araçlar erişilebilir durumdadır.
- `help` kısa yardım cevabı verir.
- `Saat kaç?` yerel saati döndürür.
- `Sen kimsin?` Lina kimlik cevabı verir.
- `Neler yapabiliyorsun?` mevcut gerçek yetenekleri dürüstçe söyler.
- `selam Lina bugün nasılsın?` normal chat olarak Ollama'ya gider.
- Cevap beklenirken input kullanılabilir kalır, gönder ikonu stop eylemine dönüşür ve kısa durum güncellenir.
- Cevap gelince stop eylemi tekrar gönder eylemine döner.
- Yeni mesajlarda sohbet alanı aşağı kayar.
- Assistant mesajına hover/focus ile gelen Kopyala eylemi mesajı panoya aktarır.
- Yeni Sohbet eylemi mevcut konuşmayı silmeden yeni session açar.

## Premium Workstation UI Smoke Test

- 1440×900 koyu temada sidebar’ın 292 px kaldığını; aktif sohbetin yalnız listede bir kez, yüzey ve ince vurgu işaretiyle seçildiğini doğrula.
- Header’da başlık, kısa durum ve araç/ayar erişimi dışında kalıcı teknik panel olmadığını; uzun durumun elide edilip tamamının tooltip ve erişilebilir açıklamada korunduğunu doğrula.
- Assistant kartlarının 820 px okunabilir kolon içinde kaldığını, user bubble’larının sağa hizalandığını ve uzun satırların yatay scrollbar üretmediğini doğrula.
- Composer’ın 880 px içinde tek yüzey gibi göründüğünü; Dosya/Mikrofon/Ekran/gönder kontrollerinin klavye focus’u, tooltip’i ve accessible name’i olduğunu doğrula.
- Yanıt beklerken gönder ikonunun stop ikonuna dönüştüğünü, input’un kullanılabilir kaldığını ve iptalin mevcut controller zincirini kullandığını doğrula.
- 900 px altına inerken sidebar’ın 64 px’e çöktüğünü, inspector’ın drawer olduğunu ve mesaj/composer alanının taşmadığını doğrula.
- Ayarlar’da yedi ana navigasyon maddesini, aranabilir section card’ları, %135 font ölçeğini ve kaydet/uygula davranışını doğrula.
- Sağ paneli açıp 344 px genişlikte 2×3 temel araç kartını, Bellek ve Bu cihazda kartlarını doğrula; fake Pro, kota, profil veya klasör listesi bulunmamalı.
- Agent, Codex ve diğer gelişmiş yüzeylerin kapalıyken ana ekranda alan tüketmediğini; aktifken mevcut panel/inspector’a açıldığını doğrula.
- Dark, light ve system temalarında çizgi ikonların okunur olduğunu; focus ve seçimlerin yalnız renkle anlatılmadığını doğrula.
- Türkçe normal yanıtta rol etiketi, iç prompt, yabancı kalıp giriş/kapanış veya bozuk teknik ek sızıntısı olmadığını doğrula.

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
