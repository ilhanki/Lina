# Lina UI Design System

## İlkeler

Lina’nın arayüzü sohbeti birincil, teknik ayrıntıyı ikincil kabul eder. Accent yalnız primary action, seçim, focus ve aktif ilerleme için kullanılır. Kapalı özellikler alan tüketmez; risk, hata ve durum yalnız renkle anlatılmaz. Native Windows pencere davranışı korunur.

## Design System V3

V3; canvas/sidebar/workspace/inspector/elevated/interactive yüzeylerini ve hover/pressed/selected, user/assistant message, composer/input, accent-soft durumlarını semantik alias olarak tanımlar. Dark palette derin nötr lacivert yüzeyler ve ölçülü mavi accent; light palette kırık beyaz canvas, beyaz içerik yüzeyi ve koyu okunabilir metin kullanır. System teması işletim sistemi lightness değerinden dark/light seçer.

Spacing ritmi 2–64 px, message/composer radius 16/18 px, sidebar 280/60 px, inspector 300–360 px, readable message 720–900 px ayarlanabilir sınırlarındadır. Large eşik 1320 px, compact eşik 900 px; minimum pencere 760×600’dür. Elevation typed sıralaması floating/dialog/tooltip/menu katmanlarını belgeler; mevcut QSS gölge yerine yüzey ve sınır ayrımını tercih eder.

İkon katmanı isim+renk+ölçü ile cache’lenir ve yalnız 16/18/20/24 px üretir. Primary navigation, tool, status, file, voice, vision, agent, memory, copy/history/pin/archive/delete ve send/stop durumları aynı çizgi dilini kullanır. Icon-only kontroller accessible name, description veya tooltip olmadan kullanılamaz.

## Token modeli

src/lina/ui/design/tokens.py immutable typed modeller sunar:

- ColorPalette: canvas/surface/border/text/accent ve semantik renkler.
- SpacingTokens: 2–64 px ortak ritim.
- RadiusTokens: 4/6/8/12/16 ve pill.
- TypographyTokens: display, title, subtitle, body, compact, label, caption ve monospace.
- ControlMetrics: compact/default/large/composer yükseklikleri.
- LayoutMetrics: 280/60 navigasyon, 820 px readable chat, 720 px assistant kartı, 860 px composer ve 320 px inspector limitleri.
- MotionTokens: kısa/normal süreler ve reduce-motion davranışı.

design_tokens dark, light veya system için tek erişim noktasıdır. validate_design_tokens zorunlu contrast ve ölçü ilişkilerini doğrular. Legacy QSS anahtarları geçiş süresince typed palette’ten türetilir.

## Tema ve tipografi

Dark palette tam siyah yerine derin nötr canvas, light palette kirli beyaz canvas ve beyaz surface kullanır. System seçimi Qt/Windows lightness bilgisine göre bu iki paletten birine döner. Font zinciri Segoe UI Variable, Segoe UI, sistem sans-serif; teknik içerik Cascadia Mono, Consolas fallback’idir. %85–%135 ölçek QSS ve application fontuna birlikte uygulanır.

## İkonlar ve kontroller

icons.py platformdan bağımsız, 20 px çizgi ikonlarını anlamlı adlarla sunar. İkon rengi aktif dark/light palette’ten gelir; ana kontroller emoji veya eski platform dosya ikonları kullanmaz. Her icon-only eylem accessible name ve tooltip taşır. Bir yüzeyde tek baskın primary action hedeflenir; destructive confirmation varsayılanı iptaldir.

## Kullanım kuralları

- Yeni renk veya spacing eklemeden önce mevcut token’ı kullan.
- Büyük kart/border yerine surface tonu ve boşlukla hiyerarşi kur.
- Accent rengini birincil eylem, focus, seçim ve aktif ilerleme dışında kullanma.
- Birincil sohbet ekranında kapalı Agent, Vision, Voice ve bildirim yüzeyleri için boş alan ayırma.
- Widget içine servis/business logic taşıma.
- Teknik ayrıntıyı status popover veya inspector’a koy.
- Layout testi için pixel-perfect screenshot yerine structural assertion kullan.
- Dark/light/system, 720 px ve %135 font etkisini birlikte düşün.

## Agent görev yüzeyleri

- Hazır Görevler yalnız available capability’lerle desteklenen şablonları kategori bazında gösterir; unavailable özelliği sahte veya disabled kart olarak çoğaltmaz.
- Typed parametre formu aracı çalıştırmaz. Birincil eylem yalnız plan hazırlar; kalıcı iş plan ve adım onayından sonra yürür.
- Plan Review başlık, adım sırası, risk, araç, onay ve bağımlılığı metinle gösterir. Risk yalnız renkle anlatılmaz.
- Task Center V2 durumları ayrı sekmelere böler; boş durumlar, ilerleme yüzdesi ve bağlamsal eylemler klavye ve screen reader ile erişilebilir kalır.
- Inspector V2 Özet, Plan, Geçmiş ve Teknik Durum katmanlarıyla progressive disclosure uygular. Raw payload veya özel içerik teknik sekmeye taşınmaz.
- `uncertain` ve `interrupted`, başarısızlıktan ayrı metin/ikon durumlarıdır; kullanıcıya otomatik tekrar yapılmayacağı açıkça söylenir.

## Görsel regresyon stratejisi

`scripts/render_ui_preview.py` fake/demo veriyle active chat ve Settings yüzeylerini deterministik olarak offscreen render eder. Screenshot’lar geçici geliştirme artefact’ıdır ve repository’ye eklenmez. CI; token, selector, visibility, geometry, accessible name, focus ve state assertion’larına dayanır. Gerçek Windows font/DPI ve native tray/media davranışı manuel smoke ile tamamlanır.
