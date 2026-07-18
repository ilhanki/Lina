# Codex Security Boundaries

## Defense in depth

1. Deterministic operational intent normal chat modelinden önce çalışır.
2. Kullanıcı workspace’i açıkça seçer ve planı onaylar.
3. Resolved path containment symlink/junction escape’ini engeller.
4. Secret path/request filtresi transport başlamadan çalışır.
5. CLI kendi `read-only` veya `workspace-write` sandbox’ını korur.
6. Runtime approval otomatik yanıtlanmaz.
7. Output redaction ve sensitive-output verification uygulanır.
8. Before/after fingerprint, exit code ve changed-file containment bağımsız doğrulanır.

## Engellenen veri ve yollar

`.env*`, `auth.json`, credentials/secrets, PEM/key/PFX/P12/CRT, SSH private key, browser profile, Windows credential store ve Git credential dosyaları engellenir. Workspace root dışına resolve edilen path reddedilir; disk root workspace olamaz. Output token/API-key pattern’i içerirse değer tekrar gösterilmeden maskelenir ve görev doğrulanmaz.

## Approval ve Git

Lina plan approval görevin başlamasına izin verir; CLI runtime approval ayrı katmandır. Modification her zaman Lina confirmation’ı ve CLI workspace sandbox’ı ister. `approval=never`, dangerous bypass, full disk, workspace dışı `--add-dir`, automatic approval, commit, push, force push, tag, reset, clean ve rebase yoktur.

## Persistence ve audit

Audit yalnız session/task ID, timestamp, hashed workspace, operation/risk, approval, CLI version, status, verification, duration ve exit category saklar. Token, auth output, full prompt, raw stderr, file content, secret veya reasoning saklanmaz. CLI diagnostics history’ye yazılmaz. Resume için yalnız metadata saklanabilir; v0.13.1 sahte resume üretmez.

## Privacy metni

Codex seçilen workspace içindeki gerekli dosyalara erişebilir ve seçilen auth yöntemine göre OpenAI hizmetlerine veri gönderebilir. Lina credential içeriğini okumaz; yalnız CLI durumu ve görev metadata’sını saklar. Hassas dosyalar filtrelenir ve görev başlamadan kullanıcı onayı gerekir.

