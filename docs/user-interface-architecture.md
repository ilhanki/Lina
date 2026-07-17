# Lina User Interface Architecture

## v0.12.2 responsive app shell

Geniş pencerede sol navigation, conversation workspace ve sağ contextual inspector aynı anda görünür. 900–1319 px aralığında sidebar açık kalır, inspector kullanıcı eylemiyle scrim üzerinde sağ drawer olur. 760–899 px aralığında sidebar ikon moduna geçer; composer ikincil araç etiketlerini gizler ve aynı drawer davranışını korur. Escape drawer’ı kapatır, odak inspector düğmesine döner; genişliğe bağlı otomatik kapanma kullanıcının kalıcı tercih değerini silmez.

Header konuşma başlığı, metinsel hazır/aktif durum ve iki icon-only eylemle sınırlıdır. Timeline 820 px readable hedefi kullanır; kısa assistant kartı 360 px’e kadar doğal kalabilir. Assistant avatarı ve güvenli zengin içerik; user için sağ hizalı accent yüzeyi vardır. Composer borderless multiline input, Dosya/Mikrofon/Ekran/Daha Fazla, dairesel send/stop ve yerel model/disclaimer footer’ından oluşur.

Context inspector ana sayfası Tools, güvenli Memory özetleri ve gerçek local storage durumunu birleştirir. Tool detayları aynı stacked yüzeyde progresif açılır. Memory repository yoksa veya boşsa bunun metinsel boş durumu gösterilir. Local storage hesaplaması async ve bounded’dır; hayali kota gösterilmez.

## App shell

LinaMainWindow native QMainWindow olarak kalır. Sol SidebarWidget, merkez workspace ve sağ DetailsInspector yatay shell’i oluşturur. Merkezde minimal header, conversation timeline, yalnız aktifken Agent/Vision bağlamı ve composer vardır. Confirmation, Settings, Command Palette, calibration, wake test ve critical errors modal/overlay katmanındadır.

## Bilgi hiyerarşisi

Kullanıcının ilk gördüğü aktif sohbet, Lina cevabı, composer ve unified status’tur. Model/provider/device ayrıntısı status menüsünde; Agent step ve Vision session ayrıntısı inspector’dadır. Inspector varsayılan kapalıdır ve kompakt pencereye geçişte kapanır.

## Navigasyon

Expanded sidebar 280 px, collapsed sidebar 60 px’tir. Görünür expanded yüzey branding, sakin birincil yeni sohbet eylemi, arama ve tarih gruplu session listesinden oluşur. Aktif sohbet yalnız listede vurgulanır; aynı başlık ikinci bir “bu oturum” bloğunda tekrarlanmaz. Filtrelenmiş sohbet görünümleri, Agent, notification, settings ve sistem ayrıntıları header’daki Araçlar menüsü veya command palette üzerinden açılır. Hover context menu mevcut conversation servislerine signal yollar. Collapsed modda metinler gizlenir; yeni sohbet ikonu, accessible name ve tooltip kalır.

## Timeline ve composer

Timeline viewport’a göre en fazla 820 px readable kolon hesaplar ve her message row’u merkezler. Assistant yanıtı en fazla 720 px ince çerçeveli surface kartta, user mesajı en fazla 560 px sağ hizalı lacivert bubble’da görünür. Streaming aynı widget’ı finalize eder; repair finali duplicate message oluşturmaz. Composer aynı merkez kolona bağlı, tek 860 px yüzeydir; multiline auto-grow ve icon-only send/stop state’ini korur. Görünür eylemler Ekle, Araçlar ve gönder ikonudur; Mikrofon, Ekran ve Agent sinyalleri tek bağlamsal menüden mevcut controller zincirlerine gider.

## Agent, Voice ve Vision

Agent paneli typed session render eder; plan onayı, ilgili step eylemleri ve progress dışındaki kontrolleri gizler. Composer Araçlar menüsü ve command palette, Hazır Görevler ile Agent Görev Merkezi’ni açar. Template Browser capability snapshot’a göre filtrelenir; Parameter Dialog typed değerleri toplar fakat yürütme yapmaz. Plan Review yeniden sıralama, optional kaldırma/atlama, regenerate ve başlatma sinyallerini controller’a yollar; her değişiklik policy ve dependency doğrulamasından geçer.

Task Center V2 persisted safe metadata’dan durum sekmeleri ve bağlamsal eylemler üretir. Aktif session açıldığında Inspector V2’ye gider. Uygulama yeniden başlatıldıktan sonra raw argümanlar gizlilik nedeniyle saklanmadığından geçmiş görev sessizce kurulmaz; kullanıcı ilgili şablonu yeniden açıp parametreleri doğrular. Başlangıç recovery bildirimi yalnız yarım görev sayısını söyler.

Voice ayrı büyük panel yerine unified status ve composer mic action’ıyla görünür. Agent onay, önemli olay ve sonuç sesleri ayrı ayarlara bağlıdır; aynı session/event iki kez seslendirilmez. Vision kapalıyken yer kaplamaz; aktif kaynak, privacy metni ve minimum kontroller kompakt kartta, ayrıntılar inspector’dadır.

## Settings

Settings dialog ürün başlığı + arama + 204 px sabit navigasyon + scroll edilebilir stacked page yapısı kullanır. Her ayar grubu aynı spacing ve border token’larına bağlı bağımsız bir section card’dır. Yedi ana bölüm Genel, Görünüm, Modeller, Ses, Vision, Hatırlatıcılar ve Gelişmiş’tir. Hands-Free Ses altında; Agent, Gizlilik, Sistem ve Hakkında/Tanılama Gelişmiş altında gruplandırılır. Agent alanında şablon önerisi, başlangıç recovery bildirimi, geçmiş saklama, ses/bildirim tercihleri ve değiştirilemez persistent-approval güvenlik açıklaması bulunur. Dialog local draft üzerinde çalışır; Apply/Save servis katmanına typed UserSettings gönderir.

## State ve lifecycle

UI güncellemeleri session/request/generation kimliğiyle stale sonuçları bastırır. Theme switch mevcut conversation ve draft’ı yeniden oluşturmaz. Window geometry settings repository’de saklanır; monitor seti değişirse visible geometry’ye clamp edilir. Gerçek exit worker, Agent, notification scheduler, speech, live vision, preview, overlay ve tray cleanup zincirini kullanır.

## Responsive katmanlar

- Compact: 800 px altı veya density=compact; icon sidebar/header, compact composer, inspector kapalı.
- Medium: expanded sidebar ve merkez workspace; inspector isteğe bağlı.
- Large: 1120 px ve üstünde readable content maksimumda kalır, boşluk iki yana dengeli dağılır.

Minimum pencere 720×560’tır. Empty state suggestion grid dar alanda tek kolona geçer; chat horizontal scrollbar’ı kullanmaz.
