# Codex Diff Review

## Snapshot ve change set

Her modification görevi öncesi ve sonrası bounded snapshot alınır. Git repository'sinde HEAD, branch, porcelain v2 status, upstream, staged/merge/rebase sinyali, tag hash ve remote URL hash metadata'sı; Git dışı klasörde sınırlı dosya manifesti kullanılır. En fazla 5.000 giriş ve 50 MB toplam içerik incelenir; tek dosyada hash 5 MB, diff içeriği 512 KB ile sınırlıdır.

`CodexChangeSet`, eklenen/değiştirilen/silinen/yeniden adlandırılan/mode değişen dosyaları ve parse edilebilen hunk'ları taşır. Binary, büyük, truncate edilmiş ve secret işaretli dosyalar içerik yerine güvenli metadata gösterir. `.git`, dependency, build, virtual environment ve cache klasörleri dışlanır.

## Kullanıcı kararı

Qt dialog dosya listesi, özet, diff, arama, önceki/sonraki eşleşme, satır kaydırma ve güvenli seçim kopyalama sunar. Kullanıcı dosya bazında veya tüm güvenli dosyalarda kabul/ret seçebilir; secret değişiklik kabul edilemez. “İncele”, “Açıkla” ve “Codex'e geri gönder” eylemleri yeni yetki vermeden bağlam sağlar.

Kabul değişiklikleri commit etmez. Ret rollback değildir; dosya silmez, reset/checkout çalıştırmaz ve yalnız review metadata'sı kaydeder. Kullanıcı dosyaları nasıl geri alacağına kendisi karar verir.

## Verification

Workspace dışı path, snapshot bütünlük kaybı, secret, unexpected Git operation, eksik modification kanıtı veya başarısız process sonucu başarı sayılmaz. Parser push/fetch/reset/clean/commit/tag/checkout/switch sinyallerini raw komutu saklamadan structured reason olarak işaretler.
