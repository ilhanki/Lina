# Codex Task Recovery

## Başlangıç davranışı

Repository terminal olmayan kayıtları başlangıçta bir kez `interrupted` durumuna taşır. UI recovery kartı görev özeti, zaman ve güvenli workspace etiketi gösterir; raw prompt, diff, terminal logu, dosya içeriği ve credential göstermez. History 500 metadata kaydıyla sınırlıdır.

Kullanıcı kaydı inceleyebilir, aynı workspace ile yeni görev akışı başlatabilir veya yalnız recovery metadata'sını kaldırabilir. Hiçbir seçenek otomatik tool çalıştırmaz. “Yeniden başlat” yeni task/session, yeni plan ve yeni approval gerektirir.

## Shutdown ve process cleanup

Aktif bridge shutdown sırasında session'ı interrupted işaretler ve process runner'a kontrollü iptal gönderir. Runner process group için Ctrl-Break, grace period, terminate ve son çare PID-tree kill sırasını uygular. Stdout/stderr 2 MB sınırında tutulur; orphan child bırakmama davranışı gerçek yerel process testiyle kapsanır.

## Sınır

Persistence canlı `CodexRemoteSessionReference` saklamaz. Bu nedenle restart recovery, aynı-process session resume ile aynı şey değildir. Bu tercih credential/prompt sızıntısı ve yanlış workspace'te gizli devam riskini azaltır.
