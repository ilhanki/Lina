# Referans UI Uygulaması

Bu belge, premium koyu masaüstü referansının Lina’nın gerçek PySide6 mimarisine
nasıl uyarlandığını açıklar. Referansın ürün hissi, bilgi hiyerarşisi, yüzey derinliği
ve spacing düzeni alınmış; Lina’da karşılığı olmayan kullanıcı profili, ücretli plan,
depolama kotası, klasör ağacı ve desteklenmeyen araç davranışları kopyalanmamıştır.

## Uygulanan ürün kararları

- **Sakin navigasyon:** Sol panel 292 px genişlikte Lina markası, Yeni sohbet, arama
  ve premium sohbet kartlarından oluşur. Seçili sohbet mavi yüzey ve ince vurgu
  işaretiyle belirgindir. 900 px altında 64 px ikon moduna geçer.
- **Minimal header:** Yalnız sohbet başlığı, kısa metinsel durum ve küçük araç/ayar
  erişimi kalır. Uzun veya teknik durumlar ana başlığı büyütmez.
- **Ferah konuşma alanı:** 820 px okunabilir merkez kolon, solda Lina surface kartı,
  sağda mavi kullanıcı balonu ve 22 px mesaj ritmi kullanılır. Saat sabit; kopyalama
  gibi eylemler progresif görünür.
- **Modern composer:** En fazla 880 px genişlik, 46–144 px büyüyen mesaj alanı,
  Dosya/Mikrofon/Ekran eylemleri, bağlamsal daha fazla menüsü, klavye ipucu ve
  dairesel gönder/durdur düğmesi tek yüzeyde birleşir.
- **İsteğe bağlı yardımcı panel:** Panel varsayılan olarak kapalıdır. Geniş düzende
  344 px dock, orta ve kompakt düzende scrim üstü drawer olur.
- **Premium tema:** Koyu lacivert katmanlar, ince sınırlar, ölçülü gradient ve mavi
  vurgu kullanılır. Açık ve sistem temaları aynı semantik tokenları korur.
- **Tutarlı marka:** Şeffaf `assets/branding/lina-mark.svg`; sidebar, karşılama alanı
  ve Lina mesaj avatarında kullanılır.

## Sağ panel içeriği

Ana araç sayfası iki sütun ve üç satırda şu gerçek kullanım alanlarını sunar:

| Araç | Kullanıcı amacı |
| --- | --- |
| Sohbet | Hızlı ve doğal konuşmaya dönmek |
| Sesli sohbet | Mikrofon ve konuşma akışını kullanmak |
| Görsel anlama | Ekran ve görselleri incelemek |
| Dosya anlama | Desteklenen belge ve dosyaları açmak |
| Hatırlatıcılar | Hatırlatıcı merkezine erişmek |
| Bellek | Hatırlanan bilgileri görmek ve yönetmek |

Kartların altında en fazla dört hassas olmayan gerçek bellek özeti ile bu cihazdaki
yerel saklama bilgisi yer alır. Agent ve Codex yalnız ilgili gelişmiş ayar etkinse
eklenir. Özelliği olmayan bir servis sahte başarı, kart veya veri göstermez.

Araç kartları yeni yetki üretmez. Ses, görsel, dosya, hatırlatıcı ve bellek eylemleri
mevcut controller/servis sinyallerini kullanır. Yerel depolama hesabı
`LocalStorageService` ile GUI thread’i dışında, 50.000 entry sınırı ve 60 saniye cache
ile çalışır; yalnız yapılandırılmış Lina data/cache konumlarına bakar. Kullanıcıya
kota veya plan karşılaştırması sunulmaz.

## Responsive davranış

| Pencere genişliği | Sol panel | Sağ panel | Composer |
| --- | --- | --- | --- |
| `< 900 px` | 64 px ikon modu | Drawer | İkincil etiketler ve klavye ipucu gizli |
| `900–1319 px` | 292 px geniş | Drawer | Tam araç satırı |
| `≥ 1320 px` | 292 px geniş | Açılırsa 344 px dock | 880 px’e kadar merkezlenmiş |

Minimum pencere 760×600’dür. Sağ panelin istenen görünürlüğü ve son bölümü, sol
panel tercihi, arayüz yoğunluğu ve azaltılmış hareket seçimi responsive geçişlerde
korunur. Kompakt moda geçiş kullanıcı tercihlerini kalıcı olarak yeniden yazmaz.

## Tema ve görsel hiyerarşi

Design System V3 semantic colors, spacing, radius, typography, control, layout,
elevation ve motion token’larına dayanır. Koyu palette canvas `#070d18`; workspace,
sidebar, inspector, assistant mesajı ve elevated kartlar birbirinden ayrı semantik
yüzeylerdir. Assistant mesaj yüzeyi canvas’a map edilmez. Mavi accent yalnız yeni
sohbet, gönderme, seçim, odak ve aktif durum gibi anlamlı noktalarda kullanılır.

Sohbet kartı başlık, etkinlik zamanı ve önizlemeyi ayrı widget’larda render eder;
elision dar alanlarda düzeni korur. Header durum metni maksimum genişlikte elide
edilir ve tam değer tooltip/accessible description içinde kalır. Composer odağı
`active` property’siyle yüzeye yansır. Hover mesaj eylemleri için önceden ayrılan
metadata alanı, timeline reflow’unu engeller.

## State, persistence ve lifecycle

`ApplicationViewState` responsive mode, sidebar, right panel bölümü ve görünürlüğünü
typed sunum state’i olarak taşır. Backend controller state’i burada çoğaltılmaz.
Settings schema sidebar başlangıcı, right panel görünürlük/bölüm/genişlik, message
genişliği, compact mode, reduce motion ve son settings bölümünü saklar. Pencere
geometry’si görünür monitöre clamp edilir.

Resize sırasında dock/drawer geçişi re-entrant native layout çağrısına yol açmasın
diye sağ panel görünürlük uygulaması Qt event loop’una ertelenir ve responsive guard
ile korunur. Reduce-motion açıkken yinelenen scroll timer’ları azaltılır. Detail
widget değişiminde eski widget hemen gizlenir ve `deleteLater()` ile temizlenir;
stale callback veya overlay yeni içeriğin üstünde kalmaz.

## Türkçe mikro kopya

Ana akış kısa ve doğal Türkçe kullanır: “Yeni sohbet”, “Sohbetlerde ara…”, “Mesaj
yaz…”, “Dosya”, “Mikrofon”, “Ekran”, “Araçlar”, “Bellek” ve “Bu cihazda”. Ham enum,
source/kind alanı, sağlayıcı ayrıntısı ve İngilizce durum etiketi kullanıcıya doğrudan
gösterilmez. Agent ve Codex isimleri yalnız özellik adı olarak Gelişmiş yüzeylerde
kalır; normal asistan deneyiminin birincil terminolojisi değildir.

## Erişilebilirlik

Ana kontroller accessible name, tooltip ve klavye odağı taşır. Ctrl+N, Ctrl+K,
Ctrl+Shift+P, Ctrl+,, Ctrl+L, Ctrl+F ve Escape desteklenir. Drawer close/scrim/Escape
ile kapanır ve odak açma düğmesine döner. Status renk yanında metinle verilir. Native
Windows title bar; snap, DPI, taskbar ve ekran okuyucu güvenilirliği için korunur.

## Deterministik görsel QA

`scripts/render_ui_preview.py` ana pencere ve Settings’i koyu/açık tema, geniş/orta/
kompakt boyut ve tools/memory/system/voice/vision/agent/codex durumlarında offscreen
render edebilir. Önizleme zamanı `2026-01-20 10:30 UTC` değerine sabittir; sohbet
kartlarındaki saat ve tarih grupları çalıştırma gününe göre değişmez.

`tests/interfaces/qt/test_render_ui_preview.py`; sabit saati ve koyu, açık, kompakt
PNG’lerin istenen çözünürlükte boş olmayan görüntü üretmesini doğrular. QA PNG’leri
geçici geliştirme artefact’ıdır ve repository’ye eklenmez.

## Manuel Windows smoke sınırı

- Native title bar referanstaki özel pencere düğmelerini birebir kopyalamaz.
- Gerçek Narrator/NVDA, %125/%150 DPI, çoklu monitör, system theme değişimi, tray
  shutdown, mikrofon/TTS ve kamera lifecycle’ı Windows üzerinde manuel smoke ister.
- Görsel benzerlik yeni capability veya veri paylaşımı izni vermez; dosya, ekran,
  kamera, Agent ve Codex mevcut güvenlik/onay sınırlarını korur.
- Release tag ve push yalnız açık kullanıcı izniyle yapılır.
