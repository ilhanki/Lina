# Lina v0.13.0-alpha — Codex Bridge Foundation

## Reliability hotfix

Gerçek kullanıcı testlerinde görülen dört kritik regresyon kapatıldı: explicit Codex komutunun chat modeline düşmesi, internal persona/prompt yankısı, bozuk Türkçe tokenların kabul edilmesi ve günlük çalışma planına yazılım lifecycle şablonunun sızması.

Codex routing artık deterministic ve operational/informational ayrımlıdır. Workspace seçimi inspector kartıyla başlar; plan her görevde approval bekler. Unavailable transport kontrollü ve dürüst sonuç verir. `.env`/credential istekleri ve tüm disk taraması erkenden engellenir.

Turkish Response Validator V4; suspicious token, suffix/anomaly, mixed-language/script, prompt leakage, instruction-block ve relevance kontrollerini ekler. Repair V4 orijinal isteği ve rejection nedenlerini korur. Repair sonrası da reddedilen metin persistence, model context ve TTS'ye aktarılmaz.

Hotfix regresyon paketiyle toplam test sayısı 1129'a yükseldi. Tag ve push yapılmadı.

Bu sürüm güvenli, kontrollü ve izlenebilir Codex orkestrasyon temelini ekler. Typed session/task/event modelleri, açık workspace izinleri, secret filtreleme, plan ve modification onayları, metadata-only history ve bağımsız verification sağlanır. Premium v0.12.2 arayüzü korunur; Codex yalnız mevcut Tools inspector ve command palette üzerinden görünür.

Sesli “Codex ile…” istekleri confirmation akışına yönlenir. Ham event, terminal logu, prompt, dosya içeriği ve model reasoning kullanıcıya veya geçmişe aktarılmaz.

Bilinen sınır: release gerçek bir Codex transport sağlayıcısı içermez. Güvenli client protokolü hazırdır; provider sonradan açık kullanıcı yapılandırmasıyla enjekte edilmelidir. Tag ve push bu sprintte yapılmaz.
