# Agent Kurtarma ve Güvenilirlik

Bu belge `v0.12.1-alpha` Agent yürütme, hata, retry, checkpoint, restart ve gizlilik davranışını tanımlar. Temel kural şudur: belirsiz veya kalıcı bir işlem güvenlik uğruna otomatik tekrarlanmaz.

## Hata sınıfları

Agent hataları raw exception yerine sabit teknik kod ve kısa Türkçe mesaj taşır:

- capability: `tool_unavailable`, `unsupported_request`, `prohibited`;
- input/policy: `invalid_arguments`, `permission_denied`, `approval_required`;
- lifecycle: `user_cancelled`, `stale_result`, `interrupted`;
- execution: `timeout`, `transient_failure`, `internal_error`, `storage_failure`;
- verification: `verification_failed`, `verification_uncertain`, `persistent_outcome_uncertain`;
- plan: `dependency_failed`, `loop_detected`, `step_limit_reached`, `replan_limit_reached`.

UI hata koduna göre yalnız güvenli eylemleri sunar. Örneğin unavailable adım tekrar availability kontrolü, invalid input bilgi tamamlama, persistent uncertain sonuç mevcut kaydı kontrol etme seçeneği verir.

## Retry ve replan

| Durum | Otomatik davranış |
| --- | --- |
| Read-only `timeout` / `transient_failure` | En fazla bir retry. |
| Read-only deterministic verification failure | Retry yok; sonuç ve recovery action gösterilir. |
| Persistent veya sensitive adım | Otomatik retry yok. |
| `persistent_outcome_uncertain` | Otomatik retry ve recreate yok; kullanıcı mevcut kaydı kontrol eder. |
| Kullanıcı iptali, permission, approval, invalid argument | Retry yok. |
| Replan | Session başına en fazla bir; tamamlanmış adımlar korunur. |

Backoff sleep ile GUI thread’i bekletilmez. Cancellation token, conversation ve generation kimliği her sonuçta yeniden kontrol edilir; stale callback UI veya persistence’a uygulanmaz.

## Idempotency ve duplicate koruması

Her adım, normalize edilmiş tool+typed-argument hash’i ve session/step kimliğinden idempotency key alır. Aynı execution kimliği ikinci kez yürütülemez. Kalıcı reminder/Memory yazımı öncesinde mevcut kayıt okunur. Persistent adım timeout veya restart sınırında kalırsa session `uncertain`/`interrupted` olur ve yeniden çalıştırma duplicate kontrolü gerektirir.

Bu korumalar tam distributed transaction garantisi değildir. Amaç, Lina’nın aynı kalıcı işlemi sessizce ikinci kez üretmesini engellemektir.

## Event ve checkpoint geçmişi

Session; plan oluşturma/değiştirme/onay, step başlangıç/onay/doğrulama/hata/atlama, pause/resume, replan ve terminal olaylarını bounded listede tutar. Step checkpoint şu güvenli alanlardan oluşur:

- step ve execution kimliği;
- tool adı ve risk sınıfı;
- durum ve verification durumu;
- sabit kısa sonuç özeti;
- timezone-aware timestamp.

Repository son 50 olayı ve 24 checkpoint’i aşmayacak şekilde metadata kaydeder. Raw kullanıcı isteği, typed argüman, tool result/payload, reminder/Memory/dosya içeriği, prompt, model reasoning, exception, image/audio ve Base64 kaydedilmez.

## Uygulama yeniden başlatma

Başlangıçta `running`, `planning`, `ready`, approval/input bekleyen, `replanning` veya `paused` metadata bir kez `interrupted` durumuna çevrilir. Hiçbir planner, tool veya TTS otomatik başlatılmaz. Ayar açıksa tek genel bildirim yarım görev sayısını gösterir.

Task Center geçmiş kaydı incelemeye ve silmeye izin verir. Raw parametreler bilinçli olarak persist edilmediği için eski bir görevi arka planda birebir yeniden kurmaz; kullanıcı ilgili şablonu açıp değerleri yeniden doğrular. Aynı runtime içindeki terminal session için safe clone:

- yeni session, plan ve step kimlikleri üretir;
- result, error, retry, verification ve idempotency alanlarını temizler;
- kalıcı adımlar için yeni approval ister;
- önceki adım sonucu belirsizse duplicate kontrol işaretini taşır.

## Geçmiş saklama ve silme

Agent geçmiş tercihi 7, 30, 90 gün veya sınırsızdır; varsayılan 30 gündür. Başlangıç temizliği aktif, approval bekleyen, paused ve interrupted metadata’yı korur. “Geçmişten kaldır” yalnız Agent metadata’sını siler; oluşturulmuş reminder, Memory kaydı, sohbet veya dosya etkilenmez.

Repository bozuk veya yazılamazsa Agent kontrollü hata verir; normal sohbet çalışmaya devam eder. JSON geçici dosyaya yazılıp atomik replace edilir ve process içi kilitle korunur.

## Loop ve plan kalite koruması

Tekrarlanan tool+argüman, aynı clarification ve ilerlemesiz replan imzası bounded eşikte görevi durdurur. Plan kalite kapısı duplicate operation, belirsiz adım, gereksiz kalıcı risk, unavailable araç, invalid dependency ve step limit sorunlarını execution’dan önce reddeder. Serbest planner çıktısı için yalnız bir repair denemesi vardır.

## Voice ve bildirimler

Agent onay, önemli olay ve tamamlanma sesleri ayrı ayarlardır. Session+event kimliği aynı olayın ikinci kez okunmasını engeller. Playback stop/barge-in yalnız TTS’i keser; Agent session’ını iptal etmez. Tray metni görev içeriği yerine genel durum taşır ve aynı event bir kez gösterilir.

