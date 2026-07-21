# Codex Bridge

## v0.13.2-alpha production workflow

Bridge, başarılı CLI başlangıcında güvenli remote session reference'ını bellekte tutar. Kullanıcı aynı workspace ve uyumlu CLI ile açıkça devam etmek istediğinde `codex exec resume` capability kapsamı doğrulanır; root flag'leri alt komuttan önce, resume flag'leri `exec resume` sonrasında yerleştirilir. Session kimliği command line'a eklenebilir, görev promptu yalnız stdin'den gider. Stale, başka workspace'e ait, auth'suz veya capability'siz reference reddedilir.

Modification görevi before/after snapshot'tan typed `CodexChangeSet` üretir ve `reviewing` durumuna geçer. Inspector ve diff dialog dosya durumunu, hunk'ları, truncation/binary/secret uyarılarını, arama ve kabul/ret kararlarını gösterir. Secret işaretli değişiklik kabul edilemez. Kabul yalnız review kararını kaydeder; ret dosyaları geri almaz. Bridge commit, reset, checkout veya başka bir rollback komutu çalıştırmaz.

Eksik kapanmış metadata kayıtları başlangıçta `interrupted` olarak yüzeye çıkarılır. Kullanıcı kaydı inceleyebilir, aynı workspace ile yeni görev başlatabilir veya recovery metadata'sını kaldırabilir. Restart sonrasında remote reference bellekte bulunmadığı için sahte resume düğmesi gösterilmez ve arka planda otomatik çalışma başlamaz.

## v0.13.1-alpha gerçek CLI bağlantısı

Bridge artık `CodexCliClient` ile resmi CLI’yi kullanabilir. Discovery sırası açık executable ayarı, `codex`, `codex.exe` ve güvenli npm prefix adaylarıdır; disk/registry taraması yoktur. Bulunan binary ancak absolute path, beklenen ad, `--version`, help capability ve `login status` probe’larından sonra seçilir.

Auth yalnız resmi CLI’ye aittir. Lina `~/.codex/auth.json`, OS credential store, cookie, token veya API key okumaz. ChatGPT login `codex login`, desteklenen device flow `codex login --device-auth`, status `codex login status`, açık onaylı çıkış `codex logout` ile yapılır. API key için yalnız resmi terminal rehberi gösterilir.

Execution `codex exec`, doğrulanmış `--cd`, `--json`, `--sandbox`, approval ve stdin capability’leriyle kurulur. Prompt argument listesine eklenmez; `-` üzerinden stdin’e verilir. Salt-okunur görev `read-only`, onaylı modification `workspace-write` sandbox kullanır. CLI runtime approval event’i non-interactive kanalda güvenle yanıtlanamıyorsa işlem durur; Lina otomatik approve etmez.

Result, before/after fingerprint, exit code, changed path containment ve sensitive output sinyaliyle bağımsız doğrulanır. Process Qt thread’i dışında çalışır; timeout/cancel/shutdown process group cleanup uygular. Ayrıntılar [CLI transport](codex-cli-transport.md), [authentication](codex-authentication.md) ve [security boundaries](codex-security-boundaries.md) belgelerindedir.

## v0.13.0-alpha reliability hotfix

Gerçek kullanıcı testinde açık “Codex ile…” komutunun varsayılan kapalı ayar nedeniyle normal chat modeline düştüğü görüldü. Routing artık ayardan bağımsız, modelden önce çalışan deterministic operational/informational sınıflandırıcıyı kullanır. `Codex`, `kodex`, `kodeks`, apostroflu ve bitişik ekli varyasyonlar desteklenir. “Codex nedir?” gibi bilgi soruları chat olarak kalırken analiz, inceleme, geliştirme, düzeltme, geçmiş ve ayar komutları bridge akışına gider.

Workspace seçilmeden görev hazırlanmaz. Inspector “Klasör Seç / İptal” kartını, ardından read-only planı ve approval kartını gösterir. Gerçek transport yoksa kullanıcıya kontrollü unavailable mesajı verilir; hazırlanmış workspace/plan metadata'sı history'den silinir ve sahte tamamlanma üretilmez. Secret dosya istekleri ve disk kökü taraması workspace seçiminden önce engellenir.

Normal chat system promptundan Codex/Agent görev dili ve sızıntıda yankılanan persona cümlesi çıkarıldı. Operational Codex isteği conversation servisine ulaşsa bile typed routing hatasıyla model çağrısı engellenir.

## Amaç

Codex Bridge, Lina'nın kullanıcı isteğini güvenli bir proje görevine dönüştürmesini sağlar. Bu katman sınırsız otonom geliştirme veya bilgisayar kontrolü değildir. Shell çalıştırmaz, paket kurmaz, git commit/push yapmaz, browser ya da credential erişimi sunmaz.

## Mimari

`models.py` session/task/context/event/result modellerini; `permissions.py` workspace ve secret politikasını; `planner.py` deterministic risk sınıflandırmasını; `bridge.py` açık lifecycle'ı; `client.py` dar transport sözleşmesini; `validator.py` bağımsız sonuç kontrolünü; `repository.py` metadata-only geçmişi içerir. `events.py`, `quality.py` ve `voice.py` ham teknik veriyi kısa Lina diline çevirir.

## Session ve görev

Session durumları `created`, `analyzing`, `planning`, `waiting_approval`, `running`, `verifying`, `reviewing`, `paused`, `completed`, `failed`, `cancelled` ve `interrupted` değerleridir. Görev riski varsayılan `read_only`; analiz ve öneri ayrıca typed risklerdir. `modification` her zaman approval gerektirir. Execution mode yalnız `plan_only`, `read_only` veya `controlled_modification` olabilir. Değişiklikli başarılı execution `reviewing` durumuna geçer; kullanıcı tüm diff kararlarını kabul edip incelemeyi tamamlamadan `completed` olmaz.

## Workspace ve gizlilik

Kullanıcı klasörü açıkça seçer. Varsayılan izin `one_time`; `session` ve açıkça hatırlanan izinler desteklenir. Context yalnız root, izinli dosya yolları, proje türü, algılanan diller, framework ipuçları ve güvenli git durum özetini taşır. Dosya içeriği otomatik olarak bridge geçmişine yazılmaz. Workspace dışına çözülen path/symlink ve env, key/certificate, credentials/secrets yolları engellenir.

## Approval ve execution

Her görev önce plan olarak gösterilir. Client yalnız açık plan onayından sonra çağrılır. Modification işinin typed görevinde ayrıca zorunlu approval bilgisi bulunur. Onay kararları mevcut Agent sisteminin `ApprovalDecision` modeliyle işlenir: onayla, reddet/iptal et veya düzenle. Reddedilen görev hiçbir işlem yapmadan `cancelled` olur.

## Events, GUI ve voice

Client yalnız typed event üretir. Bridge session kimliğini ve progress sınırını doğrular; GUI'ye ham payload vermez. Sağ Tools alanında kompakt inspector aktif görev, durum, workspace, progress ve approval kartını gösterir; terminal görevler metadata geçmişinde görünür. Command palette analiz, görev oluşturma, aktif görev, geçmiş ve ayar eylemlerini içerir. Açık Codex sesli komutu kısa bir confirmation mesajı üretir; teknik ayrıntılar TTS'e verilmez.

## Verification ve response quality

Modelin “tamamlandı” demesi kanıt değildir. Validator boş/stale sonucu, workspace taşmasını ve modification için değişmiş dosya kanıtını kontrol eder; sonuç `success`, `uncertain` veya `failed` olur. Kullanıcı yeni takip görevinde test çalıştırmayı istediyse parser ham komutu saklamadan yalnız güvenli test kategorisini ve tamamlanan komut exit sonucunu kanıta dönüştürür. Bu kanıt başarılı değilse görev fail olur. Response-quality terminal/debug satırlarını çıkarır, metni sınırlar ve doğrulama durumunu Lina dilinde açıklar.

## History ve ayarlar

Geçmiş yalnız session kimliği, görev özeti, tarih, durum ve kısa sonuç özetidir. Prompt, secret, dosya içeriği, tool payload veya model reasoning tutulmaz. Bridge etkinliği, remembered workspace listesi, analiz önerileri ve retention ayarlanabilir. Approval enforcement, workspace restriction, secret filtering, metadata-only privacy ve audit logging kapatılamaz.

## Bilinen sınırlar

Resume yalnız canlı görevden alınmış remote reference ve tüm güvenlik kapıları mevcutsa kullanılabilir; restart recovery metadata'sı tek başına resume yetkisi değildir. “Önceki göreve devam et. Bu kez yalnız…” biçimindeki komutta ikinci cümle yeni, bağlayıcı görev olarak planlanır. Önceki görev remote oturum bağlamıdır ve yeniden objective yapılmaz. Resmi CLI bulunamaz, çalıştırılamaz, çok eski veya gerekli exec/JSON/stdin/sandbox capability’lerinden yoksunsa bootstrap güvenli `UnavailableCodexClient` kullanır. Otomatik commit, push, tag, paket kurulumu, rollback ve gizli background devamı yoktur.
