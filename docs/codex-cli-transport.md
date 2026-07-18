# Codex CLI Transport

## Mimari

`CodexCliClient`, mevcut `CodexClient` protocol’ünün resmi CLI adapterıdır. Business orchestration bridge’te, process ayrıntıları transport katmanında kalır:

- `diagnostics.py`: discovery, version, auth özeti ve capability detection.
- `process.py`: `shell=False`, stream, timeout, cancel ve process-tree cleanup.
- `parser.py`: incremental JSONL ve typed event mapping.
- `prompt.py`: minimum task-only prompt.
- `verification.py`: ephemeral before/after workspace fingerprintleri.
- `cli.py`: command builder, auth eylemleri, exec ve error mapping.

## Discovery ve capability

Kullanıcı ayarındaki tam yol varsa yalnız o doğrulanır. Yoksa `shutil.which("codex")`, `shutil.which("codex.exe")` ve sınırlı npm prefix adayları kullanılır. Tüm disk veya registry taranmaz. Sürüm semantic olarak parse edilir; asıl uyumluluk `--help` çıktısında `exec`, JSONL, stdin, workspace, sandbox, approval, device auth, resume ve doctor seçeneklerinin gerçekten bulunmasıyla belirlenir.

## Command construction

Argument listesi kullanılır; shell interpolation yoktur. Global flag yalnız root help’te, subcommand flag yalnız exec help’te görüldüğü konuma yerleştirilir. Prompt process listesine yazılmaz; resmi CLI’nin `PROMPT = -` sözleşmesiyle stdin’den verilir. `--ephemeral` mevcutsa CLI rollout persistence’ını azaltmak için kullanılır.

Tehlikeli bypass, `--yolo`, approval `never`, `--add-dir`, full filesystem, automatic commit/push/tag ve shell bypass builder tarafından üretilmez.

## Stream ve lifecycle

Stdout/stderr ayrı reader thread’lerinde tüketilir; partial JSON satırı buffer’da kalır. Unknown event analiz progress’i olarak güvenli biçimde taşınır, malformed satır sayılır. Raw stderr chat’e veya history’ye verilmez. Windows’ta yeni process group kullanılır; iptal/timeout önce kontrollü sinyal, sonra terminate, son çare kill uygular. App shutdown bridge shutdown’ını çağırır.

## Diagnostics ve Windows

CLI help `doctor --json` desteğini doğrularsa yalnız redacted JSON support report çalıştırılır ve persistence’a yazılmaz. Kurulum/güncelleme otomatik yapılmaz; inspector resmi [Codex CLI rehberini](https://developers.openai.com/codex/cli) açar. Bu makinede WindowsApps altındaki CLI yolu keşfedildi ancak OS ACL doğrudan process başlatmayı reddetti; dolayısıyla real smoke “CLI kullanılamıyor” sonucu verdi.

## Bilinen sınırlamalar

Resume capability algılanır fakat güvenli workspace/session handshake v0.13.2’ye bırakılmıştır. Non-interactive runtime approval için belgeli bir cevap kanalı doğrulanmadığında görev durur ve interaktif CLI’ye yönlendirilir.

