# Lina User Interface Architecture

## Güncel responsive uygulama kabuğu

Lina’nın PySide6 arayüzü sohbeti birincil çalışma alanı kabul eder. Sol navigasyon,
merkez konuşma alanı ve varsayılan olarak kapalı sağ yardımcı panel aynı
`LinaMainWindow` kabuğunda yaşar. Pencere en az 760×600’dür ve üç yerleşim katmanı
kullanır:

- **Kompakt:** 900 px altı. Sol panel 64 px ikon görünümüne geçer, composer’ın
  ikincil etiketleri gizlenir ve sağ panel scrim üzerinde drawer olarak açılır.
- **Orta:** 900–1319 px. Sol panel 292 px kalır; sağ panel gerektiğinde drawer’dır.
- **Geniş:** 1320 px ve üstü. Sağ panel açılırsa 344 px üçüncü kolon olarak dock
  edilir; merkez içerik boşluğu iki yana dengeli dağıtır.

Escape drawer’ı kapatır ve odağı açma düğmesine döndürür. Responsive geçişin geçici
olarak paneli daraltması, kullanıcının kaydedilmiş sol panel veya sağ panel
tercihini değiştirmez. Geniş görünüme dönüldüğünde istenen sağ panel görünürlüğü ve
son seçili bölüm güvenle geri yüklenir.

## Bilgi hiyerarşisi

İlk bakışta yalnız Lina markası, sohbetler, aktif konuşma, kısa durum ve mesaj alanı
öne çıkar. Header sohbet başlığı, metinsel hazır/aktif durumu ve küçük araç/ayar
erişimiyle sınırlıdır. Model, sağlayıcı, cihaz ve gelişmiş yürütme ayrıntıları ana
timeline’da kalıcı yer kaplamaz; durum menüsüne veya ilgili yardımcı panel sayfasına
taşınır. Durum yalnız renkle değil metin ve erişilebilir adla da ifade edilir.

## Sol navigasyon

`SidebarWidget` geniş görünümde 292 px, kompakt görünümde 64 px’tir. Geniş yüzey:

1. şeffaf vektör Lina markası ve ürün adı,
2. belirgin **Yeni sohbet** eylemi,
3. debounce kullanan **Sohbetlerde ara…** alanı,
4. başlık, son etkinlik ve kısa önizlemeyi ayrı hiyerarşide sunan sohbet kartları,
5. en altta Ayarlar erişimi

öğelerinden oluşur. Aktif sohbet mavi vurgu yüzeyi ve ince seçim işaretiyle yalnız
bir kez belirtilir. Yeniden adlandırma, sabitleme, arşivleme ve silme mevcut sohbet
servislerine sinyal gönderir. Kompakt görünümde metinler gizlenir; marka, yeni sohbet,
genişletme ve ayarlar eylemleri tooltip ve erişilebilir adlarıyla kalır. Örnek profil,
ücretli plan, klasör ağacı veya hesap özeti üretilmez.

## Timeline ve mesajlar

Timeline viewport’a göre en fazla 820 px okunabilir kolon hesaplar ve satırları
merkezler. Lina yanıtı solda 36 px marka avatarıyla, ince çerçeveli koyu yüzey kartında;
kullanıcı mesajı sağda mavi vurgu balonunda görünür. Mesajlar arasında 22 px dikey
ritim vardır. Saat bilgisi sabit kalır; kopyalama, yeniden deneme ve seslendirme gibi
ikincil eylemler hover veya klavye odağında belirginleşir ve görünürken yerleşimi
zıplatmaz.

Model HTML’i doğrudan çalıştırılmaz. Kontrollü başlık, liste, kalın, satır içi kod ve
kod bloğu alt kümesi güvenli biçimde render edilir. Streaming aynı mesaj widget’ını
finalize eder; kalite onarımı ikinci bir final mesaj üretmez.

## Composer

Composer merkez kolonla hizalanan, en fazla 880 px genişliğinde tek bir yüzeydir.
46–144 px arasında büyüyen multiline input, odaklandığında ölçülü mavi sınır ve yüzey
derinliği kazanır. **Dosya**, **Mikrofon** ve **Ekran** araçları aynı toolbar ritminde;
daha fazla araç menüsü yalnız kompakt düzende veya gelişmiş eylem bulunduğunda
görünür. Sağdaki dairesel düğme gönderme sırasında durdurma eylemine dönüşür.

Geniş görünümde “Enter ile gönder · Shift+Enter ile yeni satır” ipucu gösterilir;
kompakt düzende alan kazanmak için gizlenir. Geçici dosya/ekran bağlamı composer
içinde önizleme, değiştirme ve kaldırma kontrolleriyle sunulur. Agent ve hazır görev
eylemleri ancak ilgili gelişmiş ayarlar etkinleştirildiğinde menüye katılır.

## Sağ yardımcı panel

`ContextInspector` başlangıçta kapalıdır. Ana sayfası 2×3 kart düzeninde **Sohbet**,
**Sesli sohbet**, **Görsel anlama**, **Dosya anlama**, **Hatırlatıcılar** ve **Bellek**
araçlarını gösterir. Altında yalnız hassas olmayan gerçek bellek özetleri ve yerel
saklama açıklaması bulunur. Kullanım kotası, Pro planı veya uydurma sistem özeti
gösterilmez. Agent ve Codex kartları yalnız özellikleri kullanıcı tarafından
etkinleştirilmişse eklenir.

Araç kartları yeni yetki üretmez; mevcut controller ve servis sinyallerine gider.
Detaylar aynı stacked yüzeyde progresif açılır. Eski detail widget görünümden hemen
çıkarılır ve `deleteLater()` ile temizlenir; stale panel içeriği kalmaz. Yerel depolama
ölçümü GUI thread’i dışında, sınırlandırılmış ve önbellekli çalışır; yalnız
yapılandırılmış Lina veri konumlarını inceler.

## Tema ve ayarlar

Koyu tema derin lacivert yüzey, okunaklı nötr metin, ince border ve ölçülü mavi
vurguyu temel alır. Açık ve sistem temaları aynı semantik token sözleşmesini ve tüm
işlevleri korur. Tema değişimi aktif sohbeti, composer taslağını veya panel durumunu
yeniden oluşturmaz. Görünüm ayarlarında tema, yazı ölçeği, yoğunluk, sol panel
başlangıcı, sağ panel görünürlüğü/bölümü/genişliği ve mesaj genişliği kalıcıdır.

Settings dialog arama, sabit navigasyon ve scroll edilebilir section card yapısı
kullanır. Genel, Görünüm, Modeller, Ses, Vision, Hatırlatıcılar ve Gelişmiş ana
bölümlerinden oluşur; Agent, Codex, gizlilik ve tanılama ikincil Gelişmiş bölümünde
kalır.

## State, callback ve kapanış güvenliği

`ApplicationViewState` responsive mode, sol panel durumu, sağ panel görünürlüğü ve
seçili bölüm gibi yalnız sunuma ait state’i taşır. Backend controller state’i burada
çoğaltılmaz. UI callback’leri session/request/generation kimliğiyle stale sonuçları
bastırır. Azaltılmış hareket tercihi tekrarlanan scroll timer’larını sınırlar.

Window geometry görünür monitöre clamp edilir. Gerçek çıkış worker, Agent,
notification scheduler, speech, canlı görüntü, preview, overlay ve tray cleanup
zincirini kullanır; geç callback’in kapanan pencereye yazmasına izin verilmez.

## Görsel doğrulama

`scripts/render_ui_preview.py` ana pencere ve ayarları koyu/açık tema, farklı pencere
boyutları ve panel durumlarıyla offscreen render eder. Önizleme saati sabit
`2026-01-20 10:30 UTC` değeridir; sohbet sırası ve PNG çıktısı çalıştırma zamanından
etkilenmez. Render testi istenen boyutta, boş olmayan koyu, açık ve kompakt PNG
üretimini doğrular. Gerçek Windows DPI, ekran okuyucu, çoklu monitör, tray ve medya
cihazı davranışı manuel smoke ile tamamlanır.
