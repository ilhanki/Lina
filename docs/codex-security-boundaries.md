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
9. Modification sonucu typed diff review kararı olmadan tamamlanmaz.
10. Resume workspace, CLI sürümü, auth, capability, yaş ve kullanıcı onayıyla yeniden doğrulanır.

## Engellenen veri ve yollar

`.env*`, `auth.json`, `.npmrc`, `.pypirc`, pip config, cloud credential klasörleri, credentials/secrets, PEM/key/PFX/P12/CRT, SSH private key, browser profile/cookie/login verisi, Windows credential store ve Git credential dosyaları engellenir. Workspace root dışına resolve edilen path reddedilir; disk root workspace olamaz. Output token/API-key/private-key/JWT/connection-string pattern'i içerirse değer tekrar gösterilmeden maskelenir ve görev doğrulanmaz. Filtre sıradan e-posta ve teknik metni secret sanmamak için sınırlı örüntüler kullanır.

## Approval ve Git

Lina plan approval görevin başlamasına izin verir; CLI runtime approval ayrı katmandır. Modification her zaman Lina confirmation’ı ve CLI workspace sandbox’ı ister. `approval=never`, dangerous bypass, full disk, workspace dışı `--add-dir`, automatic approval, commit, push, force push, tag, reset, clean ve rebase yoktur.

## Persistence ve audit

Audit yalnız session/task ID, timestamp, hashed workspace, operation/risk, approval, CLI version, status, verification, duration, exit category ve bounded review özeti saklar. Token, auth output, full prompt, raw stderr, file content, diff content, secret veya reasoning saklanmaz. CLI diagnostics history'ye yazılmaz. Recovery en fazla 500 metadata kaydı tutar; restart sırasında unfinished kayıt `interrupted` olur fakat canlı remote reference yoksa resume edilmez.

## Privacy metni

Codex seçilen workspace içindeki gerekli dosyalara erişebilir ve seçilen auth yöntemine göre OpenAI hizmetlerine veri gönderebilir. Lina credential içeriğini okumaz; yalnız CLI durumu ve görev metadata’sını saklar. Hassas dosyalar filtrelenir ve görev başlamadan kullanıcı onayı gerekir.
