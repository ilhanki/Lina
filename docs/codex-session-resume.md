# Codex Session Resume

## Güvenlik sözleşmesi

Lina yalnız resmi CLI'nin JSONL akışından alınmış, güvenli biçimli remote session kimliğini kullanır. Resume şu kapıların tamamını ister:

- Kullanıcı açıkça devam etmeyi onaylar.
- Canonical workspace yolu ve salt-okunur fingerprint eşleşir.
- CLI aynı major/minor uyumluluk çizgisindedir.
- Auth güncel ve başarılıdır.
- Root `--cd`/sandbox/approval ile `exec resume` JSON/stdin/session capability'leri gerçek help çıktısında vardır.
- Reference retention süresini aşmamıştır.

Komut `codex [root flags] exec resume --json SESSION_ID -` biçiminde kurulur. Yeni prompt stdin'den verilir; prompt, auth verisi veya reasoning history'ye yazılmaz.

## Recovery'den farkı

Resume canlı remote session'a devam eder. Recovery ise uygulama kapanırken unfinished kalan Lina metadata kaydını kullanıcıya gösterir. Restart sonrasında remote reference bellekte yoksa Lina otomatik resume yapmaz, fake bir session oluşturmaz ve background process başlatmaz. Kullanıcı aynı workspace'i seçerek yeni görev başlatabilir.

## Hata davranışı

Stale reference, workspace/sürüm uyuşmazlığı, auth kaybı, eksik capability veya geçersiz session kimliği typed bir ret nedeni üretir. Lina daha gevşek flag, sandbox bypass veya yeni kimlik tahminiyle tekrar denemez.
