# Lina v0.9.4-alpha

Bu sürüm light theme kontrastını, widget durumlarını ve uygulama genelindeki görsel tutarlılığı iyileştirir. Feature ve persistence davranışları değiştirilmemiştir.

## Görsel iyileştirmeler

- Semantic light palette; daha belirgin text, muted text, border, focus, selected, hover, pressed ve disabled token'ları.
- User bubble üzerinde yüksek kontrastlı metin ve assistant bubble ayrımı.
- Sidebar active/search/filter/group/empty state tutarlılığı.
- Tool ve confirmation kartlarında success, failure, cancelled ve unavailable durumlarının metin + işaret ile gösterimi.
- Notification Center, Reminder dialog ve Settings navigation yüzeyleri.
- Input, ComboBox, CheckBox, Slider, menu, tooltip ve scrollbar state'leri.
- Görünür focus ring ve okunabilir disabled kontroller.

## Theme runtime ve erişilebilirlik

System theme, işletim sistemi palette lightness değerine göre light veya dark seçer. Runtime theme değişimi tüm açık top-level dialog/widget'ları yeniden polish eder; eski stylesheet cache'i bırakılmaz. %85–135 font scale aralığı korunur.

Dark theme semantic token'ları değiştirilmedi. Durumlar yalnız renkle aktarılmaz. Widget dosyalarına yeni theme-specific hex renk dağıtılmadı; capture overlay'nin sabit çizim renkleri bilinçli istisnadır.

Gerçek Windows light/dark/system ve yüksek DPI smoke testi release tag öncesinde manuel yapılmalıdır. Yeni dependency eklenmedi ve `v0.9.4-alpha` tag'i bu sprintte oluşturulmaz.
