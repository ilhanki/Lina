# Lina Accessibility

## Temel politika

Ana eylemler klavyeyle erişilebilir, icon-only kontroller accessible name ve tooltip taşır, durum ve risk yalnız renk ile anlatılmaz. Native Qt focus, tab sırası ve Windows screen reader semantiği korunur. Frameless custom title bar kullanılmaz.

## Klavye

- Ctrl+L: composer’a odaklan.
- Ctrl+F: sohbet araması.
- Ctrl+N: yeni sohbet.
- Ctrl+Shift+P: command palette.
- Ctrl+,: Ayarlar.
- Enter: gönder; Shift+Enter: yeni satır.
- Escape: search/palette/dialog bağlamını temizle veya kapat.
- Yukarı/Aşağı: boş composer’da session içi input history.

Unavailable palette eylemleri çalıştırılmaz ve metinsel açıklama taşır. Suggestion’lar otomatik göndermez; composer’ı doldurarak kullanıcı kontrolünü korur.

## Görsel erişilebilirlik

Dark/light kritik text-surface çiftleri token testleriyle contrast kontrolünden geçer. Focus accent border ile, selected state surface + metinle, Agent/Vision/Voice status metinsel etiketle ifade edilir. %85–%135 font scale ve 720 px minimum pencere structural testlerle korunur. Reduce-motion tercihi gereksiz animasyonu kapatmak için token katmanında yer alır.

## Gizlilik ve güvenlik sinyalleri

Mikrofon, kamera, ekran izleme, speaking, Agent running ve approval state’leri unified status veya aktif kartta metinle belirtilir. Screen monitoring overlay’i renk dışı privacy etiketi taşır. Destructive reminder silme diyaloğu varsayılan olarak Vazgeç seçer.

## Manuel doğrulama

Release öncesi NVDA/Narrator ile sidebar, header, timeline action’ları, composer, command palette, Agent approval, Settings ve notification center okunmalıdır. %125/%135 Windows display scale, high-contrast system theme, klavye-only akış, secondary monitor ve runtime theme switch gerçek Windows ortamında smoke edilmelidir.

Bilinen sınır: offscreen Qt platformu host font dizinini bulamayabilir; bu durumda screenshot’larda Türkçe karakterler kutu olarak rasterize olur. Bu bir uygulama encoding hatası değildir; gerçek Windows font rendering manuel olarak doğrulanır.
