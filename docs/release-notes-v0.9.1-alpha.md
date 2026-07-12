# Lina v0.9.1-alpha

Bu sürüm yerel Notification Center ve background reminder foundation'ını tamamlar.

## Öne çıkanlar

- Zil butonu, unread badge ve Yaklaşanlar/Geçmiş/Tamamlananlar görünümleri.
- Reminder oluşturma, düzenleme, tamamlama, silme, snooze ve daily/weekly recurrence.
- Event'i önce SQLite'a yazan tray presenter akışı ve güvenli in-app fallback.
- Startup missed reminder işleme, duplicate önleme ve 4+ için tek desktop özeti.
- Runtime reminder/desktop/missed ayarları ve temiz scheduler shutdown.

## Sınırlar ve gizlilik

Gerçek zamanlı reminder için Lina açık veya tray'de olmalıdır. Tamamen kapalıyken notification gösteremez; sonraki açılışta missed reminder işlenir. Cloud push, e-posta, SMS ve webhook yoktur. Veriler local SQLite'tadır. Notification DB conversation, Memory, ham image veya Base64 data içermez.

Yeni dependency eklenmedi. Release tag'i manuel GUI smoke testi sonrasına bırakılmıştır.
