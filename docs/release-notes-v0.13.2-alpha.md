# Lina v0.13.2-alpha Release Notes

## Özet

Bu alpha, gerçek Codex CLI transportunu Windows wrapper güvenilirliği, güvenli session resume, interrupted task recovery, bounded workspace snapshot, zorunlu diff review ve üretim odaklı process/parser sınırlarıyla tamamlar. Yeni yetki, otomatik approval, rollback, commit, push veya tag davranışı eklemez.

## Windows CLI güvenilirliği

- Discovery launch edilemeyen WindowsApps adayında durmaz; sınırlı npm global/prefix adaylarına ilerler.
- Native executable ve `.cmd` wrapper için ayrı typed invocation kullanılır.
- Prompt stdin'den gider; child environment token/secret/password/API key/credential isimlerini taşımaz.
- Root, `exec` ve `exec resume` yardım kapsamları gerçek çıktıya göre ayrı parse edilir.
- Başarısız probe kısa süre cache'lenir; kullanıcı yenilemesi cache'i temizler.

## Session, recovery ve review

- Remote session kimliği JSONL'den typed reference olarak alınır.
- Resume workspace fingerprint, CLI sürümü, auth, capability, yaş ve kullanıcı onayı ister.
- Unfinished metadata startup'ta interrupted görünür; otomatik background resume yoktur.
- Before/after snapshot Git metadata'sını ve bounded non-Git manifesti kapsar.
- Modification sonucu typed file/hunk review olmadan tamamlanmaz.
- Secret değişiklik kabul edilemez; ret yalnız metadata kararıdır, rollback değildir.

## Process, parser ve güvenlik

- Process state machine bounded stdout/stderr, stdin, timeout, cancel, shutdown ve PID-tree cleanup uygular.
- JSONL parser partial/malformed/unknown future olaylarda forward-compatible ve fail-closed davranır.
- Runtime approval otomatik yanıtlanmaz; task paused olur.
- Unexpected Git operation sinyalleri raw komut persist edilmeden verification'a eklenir.
- Settings schema v11 resume/review/history/diagnostics tercihlerini güvenli migration ile taşır.

## Kullanıcı deneyimi

- Codex panelinde setup, active task, review, history ve recovery kartları ayrıştırıldı.
- Responsive diff dialog özet, dosya, hunk, arama ve karar kontrolleri sunar.
- Task Center ve command palette durdur/devam/değişiklikleri göster eylemlerini gerçek capability'lere bağlar.
- Voice yalnız kısa sabit durumları ve güvenli kontrol intentlerini kullanır; path, diff veya log okumaz.

## Doğrulama kanıtı

Release hazırlığında seçilen CLI `C:\Users\kilic\AppData\Roaming\npm\codex.cmd`, sürüm `codex-cli 0.144.6` idi. Resmi `codex login status` sonucu `Not logged in` döndü. Kullanıcının istediği tek gerçek read-only görev denendi ve `execution_failed` oldu; öncesi/sonrası Git status ve binary diff boş, HEAD aynıydı. Tek-deneme sınırı nedeniyle tekrar çalıştırılmadı.

Başarılı gerçek resume ve gerçek ücretli modification smoke'u auth olmadığı için yapılmadı. Bu yollar fake transport, gerçek geçici Git/process fixture'ları ve gerçek CLI help/command-builder kanıtıyla test edildi. Release, dış koşula bağlı uçtan uca başarıyı iddia etmez.

## Bilinen sınırlar

- Restart recovery canlı remote reference saklamaz; kullanıcı yeni görev akışı başlatır.
- Runtime approval için güvenli cevap kanalı yoksa görev paused kalır.
- Büyük, binary ve secret diff içerikleri güvenli metadata ile sınırlanır.
- Diff ret kararı dosyaları geri almaz.
- Gerçek hizmet işlemleri resmi CLI auth ve ağ erişimine bağlıdır.

## Release işlemleri

Sürüm `0.13.2a0` / `v0.13.2-alpha` olarak güncellendi. Bu sprintte paket kurulmadı, credential dosyası okunmadı, ACL değiştirilmedi, push yapılmadı ve tag oluşturulmadı.
