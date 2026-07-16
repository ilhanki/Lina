# Lina User Interface Architecture

## App shell

LinaMainWindow native QMainWindow olarak kalır. Sol SidebarWidget, merkez workspace ve sağ DetailsInspector yatay shell’i oluşturur. Merkezde minimal header, conversation timeline, yalnız aktifken Agent/Vision bağlamı ve composer vardır. Confirmation, Settings, Command Palette, calibration, wake test ve critical errors modal/overlay katmanındadır.

## Bilgi hiyerarşisi

Kullanıcının ilk gördüğü aktif sohbet, Lina cevabı, composer ve unified status’tur. Model/provider/device ayrıntısı status menüsünde; Agent step ve Vision session ayrıntısı inspector’dadır. Inspector varsayılan kapalıdır ve kompakt pencereye geçişte kapanır.

## Navigasyon

Expanded sidebar 264 px, collapsed sidebar 64 px’tir. Yeni sohbet, arama, filtre, tarih gruplu session listesi ve hover context menu mevcut conversation servislerine signal yollar. Collapsed modda metinler gizlenir; Qt icon, accessible name ve tooltip kalır. Agent, notification, settings ve local status alt bölgede ikincildir.

## Timeline ve composer

Timeline viewport’a göre en fazla 880 px readable width hesaplar ve her message row’u merkezler. Assistant metni açık surface’te, user mesajı sağ hizalı accent bubble’da görünür. Streaming aynı widget’ı finalize eder; repair finali duplicate message oluşturmaz. Composer aynı merkez kolona bağlıdır, multiline auto-grow ve stop state’ini korur.

## Agent, Voice ve Vision

Agent paneli typed session render eder; plan onayı, ilgili step eylemleri ve progress dışındaki kontrolleri gizler. Voice ayrı büyük panel yerine unified status ve composer mic action’ıyla görünür. Vision kapalıyken yer kaplamaz; aktif kaynak, privacy metni ve minimum kontroller kompakt kartta, ayrıntılar inspector’dadır.

## Settings

Settings dialog arama + sabit navigasyon + stacked page yapısı kullanır. Genel, Görünüm, Modeller, Ses ve Mikrofon, Hands-Free, Vision, Agent, Bildirimler, Gizlilik, Gelişmiş ve Hakkında bölümleri ayrı sorumluluk taşır. Dialog local draft üzerinde çalışır; Apply/Save servis katmanına typed UserSettings gönderir.

## State ve lifecycle

UI güncellemeleri session/request/generation kimliğiyle stale sonuçları bastırır. Theme switch mevcut conversation ve draft’ı yeniden oluşturmaz. Window geometry settings repository’de saklanır; monitor seti değişirse visible geometry’ye clamp edilir. Gerçek exit worker, Agent, notification scheduler, speech, live vision, preview, overlay ve tray cleanup zincirini kullanır.

## Responsive katmanlar

- Compact: 760 px altı veya density=compact; icon sidebar/header, compact composer, inspector kapalı.
- Medium: expanded sidebar ve merkez workspace; inspector isteğe bağlı.
- Large: readable content maksimumda kalır, boşluk iki yana dengeli dağılır.

Minimum pencere 720×560’tır. Empty state suggestion grid dar alanda tek kolona geçer; chat horizontal scrollbar’ı kullanmaz.
