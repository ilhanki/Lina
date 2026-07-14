# Lina v0.11.0-alpha — Live Vision & Camera Mode

## Özet

Bu sürüm, açık kullanıcı onayıyla kamera, tam ekran ve seçili ekran bölgesini periyodik snapshot’larla izleyen local-first Live Vision altyapısını ekler. Bu bir sürekli video kayıt veya her kareyi vision modeline gönderme sistemi değildir.

## Eklenenler

- Qt’den bağımsız typed `LiveVisionController`, session/state/metrics modelleri ve stale-result guard.
- PySide6 Qt Multimedia tabanlı kamera source; mevcut ekran ve region capture altyapısının yeniden kullanımı.
- Tek kare kamera analizi, periyodik kamera/ekran/bölge takibi, pause/resume/stop ve manuel “Şimdi Analiz Et”.
- 16×16 luminance signature ile dependency-free deterministic change detection.
- Varsayılan 2 saniye capture ve 5 saniye minimum analiz aralığı.
- Tek aktif inference, maksimum bir pending frame ve latest-frame-wins backpressure.
- Source-aware güvenli prompt, 500 karakter user-focus sınırı ve kimlik/biometric çıkarım yasağı.
- Opsiyonel kısa voice feedback ve aynı sonuç için konuşma cooldown’u.
- Kamera/ekran explicit privacy confirmation, metinsel ana panel göstergesi ve tray kontrolleri.
- Settings schema v4: source, interval, sensitivity, voice, kamera ve ekran tercihleri.
- Conversation-safe panel policy: Live Vision sonuçları otomatik olarak chat veritabanına yazılmaz.
- Content-free frame/drop/change/request/latency/session metrics.

## Gizlilik ve güvenlik

- Raw frame, screenshot, video veya Base64 kalıcı depolanmaz.
- Temp image/video dosyası oluşturulmaz.
- Cloud vision, cloud camera stream, yüz tanıma ve biometric identification yoktur.
- Frame/focus/prompt/full response loglanmaz.
- Stop, source switch ve exit pending frame’i temizler; kamera handle’ı bırakılır.

## Performans

- Her capture vision inference üretmez.
- Backlog oluşmaz; analiz sırasında yalnız son anlamlı kare tutulabilir.
- Mevcut text/vision unload koordinasyonu düşük VRAM sistemler için korunur.
- Yeni dependency eklenmedi; OpenCV kullanılmadı.

## Test durumu

- Başlangıç: `774 passed`.
- Sprint test turu: `809 passed`.
- Controller, source, change detector, routing, settings, UI, privacy indicator ve shutdown akışları test edildi.
- Gerçek Windows camera/screen/Ollama/VRAM smoke testi release tag kararı öncesinde manuel yapılmalıdır.

## Bilinen sınırlar

- Kamera preview yoktur.
- Neural object tracking ve OCR pipeline yoktur; bunlar `v0.11.1-alpha` değerlendirmesidir.
- Gerçek permission dialog metni ve camera availability işletim sistemi/driver’a bağlıdır.
- `v0.11.0-alpha` tag’i bu sprintte oluşturulmaz.

## Sonraki hedefler

- `v0.11.1-alpha` — Live Vision Reliability & Object Tracking.
- `v0.12.0-alpha` — Agent Mode Foundation.
- `v0.13.0-alpha` — Codex Bridge.
