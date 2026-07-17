# Referans UI Uygulaması

Bu belge, `v0.12.2-alpha` için verilen premium koyu masaüstü referansının Lina’nın gerçek PySide6 mimarisine nasıl uyarlandığını açıklar. Referans görsel bir ürün yönü olarak kullanılmış; sahte kullanıcı, hesap, ücretli plan, depolama kotası ve desteklenmeyen araç davranışı kopyalanmamıştır.

## Uygulanan yönler

- Geniş pencerede 280 px sidebar, esnek conversation workspace ve 300–360 px contextual inspector’dan oluşan üç kolon.
- Orta genişlikte açık sidebar + sağ drawer; kompakt genişlikte 60 px icon sidebar + scrim üstü drawer.
- Branding, Yeni Sohbet, debounce arama, tarih grupları, son mesaj preview/time ve context menu içeren sakin navigasyon.
- Başlık + metinsel status + icon-only status/tools eylemlerinden oluşan minimal header.
- Sağ hizalı user bubble; Lina avatarı, surface kartı, güvenli Markdown/code subset’i ve progresif eylemler içeren assistant mesajı.
- Borderless multiline input; Dosya, Mikrofon, Ekran, Daha Fazla ve dairesel send/stop içeren tek composer. Alt satırda hata uyarısı ve gerçek yerel model adı bulunur.
- Tools, gerçek ve hassas olmayan Memory özetleri, gerçek local data/cache ölçümü içeren sağ inspector.
- Dark/light/system temaları ve aranabilir premium Settings yüzeyi.

## Gerçek entegrasyon sınırı

Tool satırları yeni yetki üretmez. Chat composer’a odaklanır; Voice mevcut STT/TTS durumunu, Vision mevcut controller snapshot’ını, File mevcut açık dosya akışını, Agent typed task inspector’ını, Memory `MemoryService` repository’sini kullanır. Unavailable servis metinsel boş durum gösterir. Local storage hesaplaması `LocalStorageService` ile GUI thread’i dışında, 50.000 entry sınırı ve 60 saniye cache ile yapılır; yalnız yapılandırılmış Lina data/cache konumlarına bakar.

## State ve persistence

`ApplicationViewState` responsive mode, sidebar, right panel bölümü ve görünürlüğünü typed sunum state’i olarak taşır. Backend controller state’i bu modelde çoğaltılmaz. Settings schema v10; sidebar başlangıcı, right panel görünürlük/bölüm/genişlik, message genişliği ve son settings bölümünü saklar. Pencere geometry’si görünür monitöre clamp edilir.

## Tasarım sistemi ve performans

Design System V3 semantic colors, spacing, radius, control, layout, elevation ve motion token’larına dayanır. İkonlar isim/renk/ölçü anahtarıyla cache edilir. Sidebar araması 250 ms debounce kullanır. Storage ölçümü bounded worker’dır. Inspector detail widget’ları değiştirilirken eski widget önce gizlenir ve `deleteLater()` ile temizlenir; stale overlay kalmaz.

## Kalite ve güvenlik

Assistant model HTML’i escape edilir; yalnız kontrollü başlık, liste, bold ve code yapıları render edilir. Response Quality V3 yabancı dil kırıntısı, bozuk yabancı root+Türkçe ek, persona/meta sızıntısı, alakasız selamlama, tekrar ve yarım çıktıyı reddeder. En fazla bir Repair V3 çalışır. Geçersiz draft final assistant mesajı sayılmaz; repair da reddedilirse deterministic güvenli fallback kullanılır.

## Erişilebilirlik ve responsive davranış

Ana kontroller accessible name, tooltip ve klavye odağı taşır. Ctrl+N, Ctrl+K, Ctrl+Shift+P, Ctrl+,, Ctrl+L, Ctrl+F ve Escape desteklenir. Drawer close/scrim/Escape ile kapanır; odak açma düğmesine döner. Status renk yanında metinle verilir. Native Windows title bar korunur.

## Görsel QA

`scripts/render_ui_preview.py`; main/settings, dark/light, large/medium/compact ve tools/memory/system/voice/vision/agent durumlarını deterministic offscreen render edebilir. Sprintte 18 yüzey incelendi. Orta/kompakt inspector refresh sırasında görülen stale Memory widget çakışması yakalanıp eski widget’ı önce gizleme ve bounded minimum section ölçüleriyle düzeltildi. QA PNG’leri release artifact’i değildir ve doğrulama sonunda silinir.

## Bilinen sınırlar ve Windows smoke

- Native title bar referanstaki özel pencere düğmelerini birebir kopyalamaz; snap, DPI, taskbar ve accessibility güvenilirliği için bilinçli olarak korunur.
- Yerel dosya action’ı mevcut image/file akışının desteklediği türlerle sınırlıdır; PDF/DOCX/XLSX için sahte destek etiketi yoktur.
- Gerçek Narrator/NVDA, %125/%150 DPI, multi-monitor, system theme değişimi, tray shutdown, gerçek mikrofon/TTS ve kamera lifecycle’ı Windows üzerinde manuel smoke gerektirir.
- `v0.12.2-alpha` tag’i bu sprintte oluşturulmaz. Sonraki mimari hedef `v0.13.0-alpha` Codex Bridge’dir.
