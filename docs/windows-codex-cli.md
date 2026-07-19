# Windows Codex CLI Reliability

## Discovery sırası

Lina explicit ayarı ve sınırlı adayları dener: PATH `codex.cmd`, native `codex.exe`, extensionless wrapper ve npm global/prefix yolları. Her aday absolute path, izinli ad, `--version`, help ve auth status ile probe edilir. Launchable ilk uyumlu aday seçilir; başarısız daha yüksek öncelikli aday tüm discovery'yi durdurmaz.

Bu release makinesinde `where.exe codex` yalnız WindowsApps paketini gösterdi. Buna rağmen `Get-Command codex -All` ve sınırlı npm yolları `C:\Users\kilic\AppData\Roaming\npm\codex.cmd` adayını doğruladı. WindowsApps üzerinde ACL değiştirilmedi; seçilen npm wrapper `codex-cli 0.144.6` döndürdü.

## `.cmd` invocation

Windows batch wrapper doğrudan executable değildir. Lina command metnini kullanıcı girdisinden birleştirmez; doğrulanmış executable ve argumentleri quote eder, `%` genişlemesini etkisizleştirir, quote/control karakterini reddeder ve `cmd.exe /d /s /c` çağrısını `shell=False` ile başlatır. Prompt argument değildir, stdin'den gider. Child environment yalnız gerekli Windows/path değişkenlerini içerir; token, secret, password, API key ve credential adları aktarılmaz.

## Capability kapsamı

Root, `exec` ve `exec resume` help çıktıları ayrı parse edilir. `--cd`, sandbox ve approval root flag'i ise alt komuttan önce; JSON/session/output schema gibi resume flag'leri alt komuttan sonra yerleştirilir. Bilinmeyen capability tahmin edilmez.

## Sorun giderme

Inspector seçilen path, kaynak, sürüm, auth sınıfı ve capability özetini gösterir. Kullanıcı yenilemesi kısa başarısız-probe cache'ini temizler. Lina kurulum, paket güncelleme, PATH veya ACL değişikliği yapmaz; resmi [Codex CLI rehberine](https://developers.openai.com/codex/cli) yönlendirir.
