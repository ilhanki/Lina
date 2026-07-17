# Lina v0.12.2-alpha — Reference-Driven Premium Desktop Experience

## Özet

Bu sürüm, Lina’nın mevcut PySide6 uygulamasını referans odaklı premium bir masaüstü çalışma alanına dönüştürür. Backend yetkileri ve local-first gizlilik sınırları korunurken app shell, sidebar, chat, composer, contextual inspector, settings, responsive davranış ve Türkçe cevap kalite kapısı birlikte yenilendi.

## Arayüz

- Genişte kalıcı üç kolon; ortada sağ drawer; kompakt genişlikte icon sidebar + overlay drawer.
- Son mesaj preview/time ve mevcut yönetim eylemleriyle zenginleştirilmiş conversation navigation.
- Minimal conversation header ve metinsel unified status.
- Lina avatarı, uyarlanabilir kart genişliği, güvenli Markdown/list/code render ve progresif message actions.
- Dosya/Mikrofon/Ekran/Daha Fazla, multiline auto-grow ve send/stop durumlu premium composer.
- Gerçek Chat, Voice, Vision, File, Agent ve Memory sinyallerini açan contextual Tools paneli.
- Hassas içeriği dışlayan gerçek Memory özetleri ve async/cache’li gerçek local storage ölçümü.
- Sidebar/right panel/message width/son settings bölümü için Settings schema v10 persistence.

## Design System V3

Semantic canvas/sidebar/workspace/inspector/message/composer yüzeyleri, yeni spacing/radius/control/layout/elevation token’ları ve 16/18/20/24 px cache’li çizgi ikon sistemi eklendi. Dark, light ve system tema zinciri tek typed palette kaynağını kullanır.

## Response Quality ve Repair V3

Teknik allowlist framework, Git, GitHub, Python, PySide6, Ollama, model adları ve kullanıcı tarafından özellikle kullanılan İngilizce terimleri korur. Gereksiz yabancı kırıntı, bozuk ek, persona/meta sızıntısı, boilerplate, tekrar ve yarım cevap kabul edilmez. En fazla bir düşük-temperature, `stream=False` repair çalışır; başarısızsa sabit güvenli fallback gösterilir.

## Doğrulama

- Tasarım/theme, settings migration, responsive shell/drawer, context tools, Memory/storage, sidebar preview, rich content, composer ve quality/repair için otomatik testler eklendi veya güncellendi.
- Dark/light ve large/medium/compact dahil 18 offscreen yüzey görsel olarak incelendi.
- Yeni ağır UI dependency eklenmedi; native Qt/Windows title bar davranışı korundu.
- Fake user/account/Pro/storage quota verisi eklenmedi.

## Bilinen sınırlar

Narrator/NVDA, gerçek DPI/multi-monitor, tray exit, mikrofon/TTS ve kamera lifecycle’ı gerçek Windows oturumunda manuel smoke gerektirir. Native title bar referanstaki özel chrome’u birebir kopyalamaz. Desteklenmeyen belge türleri araç panelinde vaat edilmez.

`v0.12.2-alpha` tag ve push işlemleri yalnız açık kullanıcı izniyle yapılır.
