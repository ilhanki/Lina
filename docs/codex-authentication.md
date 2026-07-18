# Codex Authentication

## Credential izolasyonu

Kimlik doğrulamanın sahibi resmi Codex CLI’dir. Lina `~/.codex/auth.json`, işletim sistemi credential store’u, browser cookie, access/refresh token veya API key okumaz, parse etmez, kopyalamaz ve saklamaz. GUI’da API key alanı yoktur; key clipboard’tan veya environment’tan alınmaz ve process argumentine eklenmez.

Lina yalnız şu metadata’yı kullanır: signed-in durumu, genel auth yöntemi (`ChatGPT`, `API key`, `access token`, `unknown`), CLI version ve kontrol zamanı. Status çıktısı redaction katmanından geçer; ham çıktı persistence’a girmez.

## Resmi akışlar

- ChatGPT: açık confirmation sonrası görünür terminalde `codex login`.
- Device code: yalnız help’te destekleniyorsa `codex login --device-auth`.
- Status: `codex login status`; başarılı auth için exit code 0 beklenir.
- Logout: “Bu işlem Codex CLI oturumunu bu cihazda kapatacak.” confirmation’ından sonra `codex logout`.
- API key: Lina key istemez; kullanıcı resmi CLI dokümantasyonundaki stdin/environment yöntemini kendi terminalinde uygular.

Resmi referanslar: [Codex authentication](https://developers.openai.com/codex/auth) ve [CLI reference](https://developers.openai.com/codex/cli/reference).

## Login ve logout etkisi

Login tamamlandıktan sonra kullanıcı “Durumu Yenile” ile tekrar probe eder. Logout yalnız CLI credential oturumunu etkiler; Lina conversation, memory, task history veya workspace ayarlarını silmez. Login process’i interactive olduğu için Lina stdout/token yakalamaz.

