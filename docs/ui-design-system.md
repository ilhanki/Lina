# Lina UI Design System

## İlkeler

Lina’nın arayüzü sohbeti birincil, teknik ayrıntıyı ikincil kabul eder. Accent yalnız primary action, seçim, focus ve aktif ilerleme için kullanılır. Kapalı özellikler alan tüketmez; risk, hata ve durum yalnız renkle anlatılmaz. Native Windows pencere davranışı korunur.

## Design System V3

V3; canvas/sidebar/workspace/inspector/elevated/interactive yüzeylerini ve hover/pressed/selected, user/assistant message, composer/input, accent-soft durumlarını semantik alias olarak tanımlar. Assistant mesajı canvas’a değil kendi surface token’ına bağlıdır; böylece hem koyu hem açık temada konuşma kartı zeminden ayrılır. Dark palette derin nötr lacivert yüzeyler ve ölçülü mavi accent; light palette kırık beyaz canvas, beyaz içerik yüzeyi ve koyu okunabilir metin kullanır. System teması işletim sistemi lightness değerinden dark/light seçer.

Spacing ritmi 2–64 px, message/composer radius 18/20 px, sidebar 292/64 px ve inspector 344 px hedefiyle 300–384 px sınırlarındadır. Okunabilir sohbet kolonu 820 px, composer üst sınırı 880 px’tir. Geniş düzen eşiği 1320 px, kompakt eşik 900 px; minimum pencere 760×600’dür. Elevation typed sıralaması floating/dialog/tooltip/menu katmanlarını belgeler; QSS yüzey tonu, ince sınır ve ölçülü gradient ile derinlik kurar.

İkon katmanı isim+renk+ölçü ile cache’lenir ve yalnız 16/18/20/24 px üretir. Primary navigation, tool, status, file, voice, vision, agent, memory, copy/history/pin/archive/delete ve send/stop durumları aynı çizgi dilini kullanır. Icon-only kontroller accessible name, description veya tooltip olmadan kullanılamaz.

## Token modeli

src/lina/ui/design/tokens.py immutable typed modeller sunar:

- ColorPalette: canvas/surface/border/text/accent ve semantik renkler.
- SpacingTokens: 2–64 px ortak ritim.
- RadiusTokens: 4/6/8/12/16/20, 18 px mesaj, 20 px composer ve pill.
- TypographyTokens: display, title, subtitle, body, compact, label, caption ve monospace.
- ControlMetrics: compact/default/large, 68 px sohbet kartı ve 46–144 px composer yükseklikleri.
- LayoutMetrics: 292/64 navigasyon, 820 px okunabilir sohbet, 880 px composer, 344 px inspector, 900/1320 px responsive eşikleri ve 760×600 minimum pencere.
- MotionTokens: kısa/normal süreler ve reduce-motion davranışı.

design_tokens dark, light veya system için tek erişim noktasıdır. validate_design_tokens zorunlu contrast ve ölçü ilişkilerini doğrular. Legacy QSS anahtarları geçiş süresince typed palette’ten türetilir.

## Tema ve tipografi

Dark palette tam siyah yerine `#070d18` canvas ve birbirinden ayrılan lacivert yüzeyler kullanır; seçili sohbet, kullanıcı mesajı ve birincil eylem mavi vurguyla öne çıkar. Light palette kırık beyaz canvas ve beyaz surface kullanır. System seçimi Qt/Windows lightness bilgisine göre bu iki paletten birine döner. Font zinciri Segoe UI Variable, Segoe UI, sistem sans-serif; teknik içerik Cascadia Mono, Consolas fallback’idir. %85–%135 ölçek QSS ve application fontuna birlikte uygulanır.

## İkonlar ve kontroller

icons.py platformdan bağımsız çizgi ikonlarını anlamlı adlarla sunar. İkon rengi aktif dark/light palette’ten gelir; ana kontroller emoji veya eski platform dosya ikonları kullanmaz. Lina’nın şeffaf `lina-mark.svg` işareti sidebar, karşılama yüzeyi ve assistant avatarında aynı marka dilini korur. Her icon-only eylem accessible name ve tooltip taşır. Bir yüzeyde tek baskın primary action hedeflenir; destructive confirmation varsayılanı iptaldir.

## Bileşen ritmi

- Sohbet kartları 68 px yüksekliğinde; başlık, etkinlik zamanı ve önizleme ayrı tipografik katmanlardadır. Seçim hem yüzey hem ince vurgu işaretiyle anlatılır.
- Header 72 px hedef yüksekliğinde kalır; uzun durum metni elide edilir, tam metin tooltip ve erişilebilir açıklamada korunur.
- Assistant ve kullanıcı mesajları arasında 22 px dikey boşluk vardır. Zaman bilgisi yerini korur; hover eylemleri açıldığında timeline yeniden akmaz.
- Composer input’u 46–144 px arasında büyür. Dosya, Mikrofon ve Ekran 36 px araç ritminde; gönder düğmesi 42 px dairesel birincil eylemdir.
- Sağ panel araç kartları 112 px yüksekliğinde 2×3 grid oluşturur. Başlık ve iki satırlık açıklama dar 344 px panelde yatay scrollbar üretmez.

## Kullanım kuralları

- Yeni renk veya spacing eklemeden önce mevcut token’ı kullan.
- Büyük kart/border yerine surface tonu ve boşlukla hiyerarşi kur.
- Accent rengini birincil eylem, focus, seçim ve aktif ilerleme dışında kullanma.
- Birincil sohbet ekranında kapalı Agent, Codex veya diğer gelişmiş yüzeyler için boş alan ayırma.
- Widget içine servis/business logic taşıma.
- Teknik ayrıntıyı status popover veya inspector’a koy.
- Layout testi için pixel-perfect screenshot yerine structural assertion kullan.
- Dark/light/system, 760 px minimum genişlik ve %135 font etkisini birlikte düşün.
- Referansta bulunsa bile Lina’da gerçek karşılığı olmayan Pro planı, kota, profil veya klasör bilgisini üretme.

## Agent görev yüzeyleri

- Hazır Görevler yalnız available capability’lerle desteklenen şablonları kategori bazında gösterir; unavailable özelliği sahte veya disabled kart olarak çoğaltmaz.
- Typed parametre formu aracı çalıştırmaz. Birincil eylem yalnız plan hazırlar; kalıcı iş plan ve adım onayından sonra yürür.
- Plan Review başlık, adım sırası, risk, araç, onay ve bağımlılığı metinle gösterir. Risk yalnız renkle anlatılmaz.
- Task Center V2 durumları ayrı sekmelere böler; boş durumlar, ilerleme yüzdesi ve bağlamsal eylemler klavye ve screen reader ile erişilebilir kalır.
- Inspector V2 Özet, Plan, Geçmiş ve Teknik Durum katmanlarıyla progressive disclosure uygular. Raw payload veya özel içerik teknik sekmeye taşınmaz.
- `uncertain` ve `interrupted`, başarısızlıktan ayrı metin/ikon durumlarıdır; kullanıcıya otomatik tekrar yapılmayacağı açıkça söylenir.

## Görsel regresyon stratejisi

`scripts/render_ui_preview.py` kontrollü önizleme verisiyle aktif sohbet ve Settings yüzeylerini deterministik olarak offscreen render eder. Saat `2026-01-20 10:30 UTC` değerine sabittir; çıktı çalıştırıldığı güne göre değişmez. Render testi koyu, açık ve kompakt ana pencere PNG’lerinin istenen boyutta ve boş olmayan içerikle oluştuğunu doğrular. Screenshot’lar geçici geliştirme artefact’ıdır ve repository’ye eklenmez. CI; token, selector, visibility, geometry, accessible name, focus ve state assertion’larına dayanır. Gerçek Windows font/DPI ve native tray/media davranışı manuel smoke ile tamamlanır.
