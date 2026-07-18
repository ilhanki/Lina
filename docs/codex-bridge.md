# Codex Bridge

## Amaç

Codex Bridge, Lina'nın kullanıcı isteğini güvenli bir proje görevine dönüştürmesini sağlar. Bu katman sınırsız otonom geliştirme veya bilgisayar kontrolü değildir. Shell çalıştırmaz, paket kurmaz, git commit/push yapmaz, browser ya da credential erişimi sunmaz.

## Mimari

`models.py` session/task/context/event/result modellerini; `permissions.py` workspace ve secret politikasını; `planner.py` deterministic risk sınıflandırmasını; `bridge.py` açık lifecycle'ı; `client.py` dar transport sözleşmesini; `validator.py` bağımsız sonuç kontrolünü; `repository.py` metadata-only geçmişi içerir. `events.py`, `quality.py` ve `voice.py` ham teknik veriyi kısa Lina diline çevirir.

## Session ve görev

Session durumları `created`, `analyzing`, `planning`, `waiting_approval`, `running`, `paused`, `completed`, `failed`, `cancelled` ve `interrupted` değerleridir. Görev riski varsayılan `read_only`; analiz ve öneri ayrıca typed risklerdir. `modification` her zaman approval gerektirir. Execution mode yalnız `plan_only`, `read_only` veya `controlled_modification` olabilir.

## Workspace ve gizlilik

Kullanıcı klasörü açıkça seçer. Varsayılan izin `one_time`; `session` ve açıkça hatırlanan izinler desteklenir. Context yalnız root, izinli dosya yolları, proje türü, algılanan diller, framework ipuçları ve güvenli git durum özetini taşır. Dosya içeriği otomatik olarak bridge geçmişine yazılmaz. Workspace dışına çözülen path/symlink ve env, key/certificate, credentials/secrets yolları engellenir.

## Approval ve execution

Her görev önce plan olarak gösterilir. Client yalnız açık plan onayından sonra çağrılır. Modification işinin typed görevinde ayrıca zorunlu approval bilgisi bulunur. Onay kararları mevcut Agent sisteminin `ApprovalDecision` modeliyle işlenir: onayla, reddet/iptal et veya düzenle. Reddedilen görev hiçbir işlem yapmadan `cancelled` olur.

## Events, GUI ve voice

Client yalnız typed event üretir. Bridge session kimliğini ve progress sınırını doğrular; GUI'ye ham payload vermez. Sağ Tools alanında kompakt inspector aktif görev, durum, workspace, progress ve approval kartını gösterir; terminal görevler metadata geçmişinde görünür. Command palette analiz, görev oluşturma, aktif görev, geçmiş ve ayar eylemlerini içerir. Açık Codex sesli komutu kısa bir confirmation mesajı üretir; teknik ayrıntılar TTS'e verilmez.

## Verification ve response quality

Modelin “tamamlandı” demesi kanıt değildir. Validator boş/stale sonucu, workspace taşmasını ve modification için değişmiş dosya kanıtını kontrol eder; sonuç `success`, `uncertain` veya `failed` olur. Response-quality terminal/debug satırlarını çıkarır, metni sınırlar ve doğrulama durumunu Lina dilinde açıklar.

## History ve ayarlar

Geçmiş yalnız session kimliği, görev özeti, tarih, durum ve kısa sonuç özetidir. Prompt, secret, dosya içeriği, tool payload veya model reasoning tutulmaz. Bridge etkinliği, remembered workspace listesi, analiz önerileri ve retention ayarlanabilir. Approval enforcement, workspace restriction, secret filtering, metadata-only privacy ve audit logging kapatılamaz.

## Bilinen sınırlar

Bu foundation sürümü gerçek Codex transport/kimlik doğrulama sağlayıcısını paketlemez; bootstrap güvenli `UnavailableCodexClient` ile başlar. Uygulama ancak kullanıcı tarafından yapılandırılan ve `CodexClient` sözleşmesini uygulayan bir adaptör enjekte edildiğinde gerçek çalışma başlatır. Otomatik commit, push, paket kurulumu, dosya silme ve gizli background devamı bilerek yoktur.
