# Codex CLI Transport

## Mimari

`CodexCliClient`, mevcut `CodexClient` protocol’ünün resmi CLI adapterıdır. Business orchestration bridge’te, process ayrıntıları transport katmanında kalır:

- `diagnostics.py`: discovery, version, auth özeti ve capability detection.
- `process.py`: `shell=False`, stream, timeout, cancel ve process-tree cleanup.
- `parser.py`: incremental JSONL ve typed event mapping.
- `prompt.py`: minimum task-only prompt.
- `snapshot.py`: bounded before/after workspace ve Git metadata snapshot'ları.
- `changes.py`: typed file/hunk değişiklikleri ve review kararları.
- `verification.py`: snapshot bütünlüğü, exit ve güvenlik kanıtı.
- `cli.py`: command builder, auth eylemleri, exec ve error mapping.

## Discovery ve capability

Kullanıcı ayarındaki tam yol varsa önce o doğrulanır. Otomatik discovery Windows'ta PATH üzerindeki `codex.cmd`, `codex.exe`, extensionless wrapper ve sınırlı npm global/prefix adaylarını launchability sırasıyla dener. WindowsApps paketi keşfedilse bile doğrudan çalıştırılamazsa daha düşük öncelikli npm adayına ilerlenir; tüm disk veya registry taranmaz. Başarısız probe 30 saniye cache'lenir, kullanıcı yenilemesi cache'i temizler. Sürüm semantic olarak parse edilir; asıl uyumluluk root, `exec` ve `exec resume --help` çıktılarından ayrı ayrı çıkarılır.

## Command construction

Native executable argument listesiyle çalışır ve shell interpolation yoktur. Windows `.cmd` wrapper için yalnız doğrulanmış ve quote edilmiş argumentlerden `cmd.exe /d /s /c` invocation'ı kurulur; control karakteri ve quote reddedilir, `%` genişlemesi etkisizleştirilir, process yine `shell=False` çalışır. Global flag yalnız root help'te, subcommand flag yalnız ilgili help'te görüldüğü konuma yerleştirilir. Prompt process listesine yazılmaz; resmi CLI'nin `PROMPT = -` sözleşmesiyle stdin'den verilir. Resume kapalıysa desteklenen `--ephemeral` kullanılabilir; resumable session'da remote reference korunabilsin diye ephemeral kullanılmaz.

Resume komutu `codex [root flags] exec resume [resume flags] SESSION_ID -` biçimindedir. Builder, session kimliğini güvenli UUID biçimiyle, workspace'i canonical path/fingerprint ile, sürümü aynı minor çizgisiyle ve auth/capability durumunu tekrar doğrular.

Tehlikeli bypass, `--yolo`, approval `never`, `--add-dir`, full filesystem, automatic commit/push/tag ve shell bypass builder tarafından üretilmez.

## Stream ve lifecycle

Stdout/stderr ayrı reader thread’lerinde tüketilir; partial JSON satırı buffer’da kalır. Unknown event analiz progress’i olarak güvenli biçimde taşınır, malformed satır sayılır. Raw stderr chat’e veya history’ye verilmez. Windows’ta yeni process group kullanılır; iptal/timeout önce kontrollü sinyal, sonra terminate, son çare kill uygular. App shutdown bridge shutdown’ını çağırır.

## Diagnostics ve Windows

CLI help `doctor --json` desteğini doğrularsa yalnız redacted JSON support report çalıştırılır ve persistence'a yazılmaz. Kurulum/güncelleme otomatik yapılmaz; inspector resmi [Codex CLI rehberini](https://developers.openai.com/codex/cli) açar. Release doğrulamasında WindowsApps paketi launchable bulunmadı, ancak `%APPDATA%\npm\codex.cmd` güvenle seçildi ve `codex-cli 0.144.6` olarak probe edildi. O anda resmi `codex login status` sonucu `Not logged in` olduğundan tek gerçek read-only görev `execution_failed` ile sonuçlandı; çalışma ağacı, diff ve HEAD değişmedi.

## Bilinen sınırlamalar

Gerçek resume yalnız mevcut süreçte yakalanmış remote reference için mümkündür; restart recovery kaydı prompt/session secret saklamadığı için otomatik resume yapmaz. Non-interactive runtime approval için belgeli bir cevap kanalı doğrulanmadığında görev `paused` olur ve kullanıcıya yönlendirme gösterilir. Auth bulunmayan release makinesinde gerçek başarılı exec/resume ve gerçek ücretli modification smoke'u yapılmadı.
