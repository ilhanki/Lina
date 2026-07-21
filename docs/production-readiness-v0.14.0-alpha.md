# v0.14.0-alpha production readiness

## Karar

Bu sürüm kontrollü alpha dağıtımı için adaydır; genel erişilebilir kararlı sürüm değildir. Otomatik doğrulama yeşil olsa da gerçek donanım ve authenticated Codex smoke'ları tamamlanmadan “production ready” etiketi verilmez.

## Otomatik kapılar

| Kapı | Beklenti |
| --- | --- |
| Git | Sprint başlangıç commit'i korunur; final worktree temizdir |
| Test | En az 150 anlamlı test; tam suite sıfır failure |
| Compile | `python -m compileall -q src tests` sıfır exit |
| Dependencies | `python -m pip check` broken requirement bildirmez |
| Version | Paket `0.14.0a0`, görünür sürüm `v0.14.0-alpha` |
| Privacy | Secret/path/raw audio/image/reasoning persistence yok |
| Approval | Agent persistent adım ve Codex plan/runtime kapıları otomatik geçilmez |

İlk full-system regression turu 1.384 testle geçti. Final sayı release kapanışında bu belgeye işlenir.

## Gerçek ortam kanıtı

- Ollama CLI kuruludur; model erişimi final smoke'ta ayrıca raporlanır.
- Codex CLI discovery npm wrapper ve WindowsApps adaylarını buldu. Doğrulanmış npm CLI sürümü `0.144.6`.
- `codex login status` sonucu `Not logged in` olduğundan gerçek remote read-only görev başarıyla çalıştırılmadı. Lina auth dosyası okumadı ve sahte başarı üretmedi.
- Ses cihazları yalnız enumerate edildi; kayıt başlatılmadı. Kamera otomatik açılmadı.

Codex CLI sandbox ve approval iki ayrı güvenlik katmanıdır. Lina read-only görevde `read-only`, kontrollü değişiklikte ancak kullanıcı plan onayından sonra `workspace-write` ister. Non-interactive runtime approval güvenle yanıtlanamıyorsa görev pause/failure olarak yüzeye çıkar; otomatik approve edilmez. Güncel resmi davranış için [OpenAI Codex CLI belgeleri](https://developers.openai.com/codex/cli/) kaynak kabul edilmelidir.

## Manuel no-go koşulları

- Uygulama açılış/kapanışında traceback veya asılı process.
- Mikrofon/kamera/ekranın kullanıcı eylemi olmadan başlaması.
- Geç worker sonucunun başka conversation'a yazılması.
- Codex test görevinin command completion kanıtı olmadan tamamlanması.
- Modification görevinin diff review kabulünden önce completed görünmesi.
- Secret, credential, ham audio/image veya belge içeriğinin metadata geçmişine/loga yazılması.
- Authenticated gerçek Codex smoke'ında workspace dışı değişiklik ya da beklenmeyen Git işlemi.

## Manuel takip listesi

Windows 10/11 üzerinde dark/light/system, %100/%125/%150 DPI, keyboard-only navigation, screen reader names, tray close, gerçek STT/TTS, kamera permission denial, multi-monitor region capture, Ollama text/vision ve authenticated Codex read-only/test-evidence senaryoları uygulanmalıdır.
