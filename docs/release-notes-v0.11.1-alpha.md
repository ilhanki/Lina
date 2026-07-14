# Lina v0.11.1-alpha — Live Preview & Monitoring Overlays

## Özet

Bu sürüm, Live Vision’ın kullanıcı tarafından görsel olarak doğrulanmasını sağlar: kamera monitoring gerçek canlı preview açar; görüntü değişiklikleri geçici kutularla, ekran/region monitoring ise zorunlu click-through beyaz border ile gösterilir.

## Kamera preview

- PySide6 `QCamera`, `QVideoSink`, `QVideoFrame` ve QImage tabanlı `Lina Kamera` penceresi.
- Yeniden boyutlandırılabilir yaklaşık 640×360/480 preview canvas.
- Kamera aktif göstergesi, cihaz adı ve starting/monitoring/analyzing/paused durumları.
- Şimdi Analiz Et, Duraklat/Devam Et, Takibi Durdur ve Preview’i Gizle kontrolleri.
- Preview gizlense bile ana panel ve tray privacy göstergesi aktif kalır.
- Tek bir preview instance; stale session frame’i yeni preview’e uygulanmaz.

## Değişiklik kutuları

- 16×16 luminance grid ve dependency-free block difference.
- Dört yönlü komşu blok birleştirme, tek-blok noise filtresi ve maksimum beş kutu.
- Normalized coordinate scaling ve 2,5 saniyelik box expiry/refresh.
- Kutular yalnız görüntü değişikliği/hareket bölgesidir; semantic object detection değildir.

## Screen/region privacy border

- Frameless, always-on-top, taskbar dışı `Qt.Tool` overlay.
- Mouse/keyboard input pass-through ve focus almayan pencere.
- 3 px beyaz border ile `Lina ekranı izliyor` / `Lina bu bölgeyi izliyor` etiketi.
- Pause’da soluk/kesikli, resume’da normal görünüm.
- Monitor geometry/DPI origin güncellemesi ve explicit secondary-screen capture.
- Border gösterilemezse monitoring başlamaz; beklenmedik kapanırsa session durur.

## Privacy, performans ve cleanup

- Preview QImage hattı inference’dan bağımsızdır; her preview frame JPEG/Base64 encode edilmez.
- Raw frame, preview, screenshot veya video persistence yoktur.
- OpenCV, YOLO, ONNX veya yeni dependency eklenmedi.
- Latest-frame-wins, tek inference ve düşük VRAM model lifecycle değişmedi.
- Stop/source switch/error/Vision disable/exit sırasında preview, boxes, overlay, timer, listener, camera ve frame referansları temizlenir.

## Test durumu

- Başlangıç: `809 passed`.
- Sprint: `833 passed`.
- Preview, stale frame, hide/show, device error, region merge/limit/scale, overlay flags/geometry/pause/close, mandatory privacy border ve no-persistence yolları kapsandı.

## Bilinen sınırlar

- Kutular nesne kimliği vermez.
- Kamera preview kalitesi cihaz/driver’a bağlıdır.
- Windows mixed-DPI ve fiziksel multi-monitor davranışı release öncesi manuel smoke gerektirir.
- Semantic object detection feasibility, ONNX/YOLO dependency ve GTX 1650 performansı sonraki sprintte değerlendirilir.
- Bu sprint `v0.11.1-alpha` tag’i oluşturmaz.
