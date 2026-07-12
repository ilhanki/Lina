# Lina v0.9.3-alpha

Bu sürüm v0.9.x Settings, Notifications, Reminder ve Assistant Tools altyapısını UX ve reliability açısından stabilize eder.

## Tool UX

- Timeline içinde Türkçe ve erişilebilir tool status kartları.
- İşlem, açıklama, güvenli argüman, risk ve Onayla/Vazgeç içeren confirmation kartı.
- Enter/Escape, focus, detail toggle ve font/theme mirası.
- Anlamlı assistant sonucu conversation history içinde korunur; interaktif kart state'i restart'ta persist edilmez.

## Reliability

- Read-only işlemler için güvenli retry; persistent işlemlerde yeni confirmation ve execution ID.
- Text cancel komutları ve conversation lifecycle cleanup.
- Ortak validation/permission/unavailable/timeout/cancelled/persistence/execution/stale/unsupported kategorileri.
- Registry availability reason ve Vision diagnostics preflight.
- Reminder duplicate guard, 10-result list sınırı ve local timezone sunumu.
- Files canonical casing, allowlist, traversal, absolute/UNC, symlink, binary ve size sınırları.
- Memory store confirmation/sensitive content ve recall maksimum beş sonuç politikası.

## Gizlilik ve sınırlar

Ayrı tool-history database yoktur. Loglar yalnız intent/tool/status/duration metadata içerir; kullanıcı mesajı, reminder/memory içeriği, path/file content, prompt ve image/Base64 içermez. Yeni tool, dependency, cloud, shell, browser automation veya confirmation bypass eklenmedi.

Gerçek Windows GUI/tray smoke testi release tag öncesinde manuel yapılmalıdır. `v0.9.3-alpha` tag'i bu sprintte oluşturulmaz.
