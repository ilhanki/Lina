# Lina v0.9.2-alpha

Bu sürüm, normal sohbeti koruyan local-only Assistant Tools & Intent Routing foundation'ını ekler.

## Routing ve araçlar

- Deterministic-first Türkçe intent classifier; belirsiz mesajlarda chat fallback.
- Typed IntentRequest, ToolResult, RequestContext ve süreli PendingIntent modelleri.
- Reminder create/list, screen/region/image, allowlisted file read ve Memory store/recall registry'si.
- Reminder create ve Memory store için zorunlu Onayla/Vazgeç akışı.
- Eksik reminder tarih/saat bilgisi için sohbet-isolated clarification.
- Ayarlar altında kapatılabilir Akıllı araç yönlendirme seçeneği.

## Güvenlik ve gizlilik

Shell/CMD/PowerShell, arbitrary execution, file write/delete/move, browser veya OS kontrolü, application launch, network, e-posta ve webhook yoktur. File read mevcut allowlist ve size/binary kontrollerini kullanır; traversal, absolute path ve symlink escape reddedilir. İşleme local cihazda kalır. Conversation dump, Memory içeriği, full path ve raw image/Base64 loglanmaz veya routing DB'sine yazılmaz.

Bu sürüm model-assisted classification kullanmaz. Doğal dil reminder parsing yalnız bugün/yarın, açık saat ve none/daily/weekly kalıplarıyla sınırlıdır. Tag manuel GUI smoke testi sonrasına bırakılmıştır.
