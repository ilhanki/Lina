# Sistem yaşam döngüsü

## Başlangıç

Bootstrap typed ayarları ve yerel yolları yükler; ardından provider, repository ve controller'ları constructor injection ile kurar. Memory veya conversation persistence kapalıysa explicit in-memory davranış kullanılır. Codex CLI probe başarısızsa bootstrap çökmez; neden kodlarını taşıyan `UnavailableCodexClient` üretir. Hiçbir bootstrap adımı mikrofonu, kamerayı veya ekran yakalamayı otomatik başlatmaz.

Warm-up yalnız ayar açıksa daemon thread'de best-effort çalışır. Model indirme, auth veya package install yapmaz.

## Aktif çalışma

`UnifiedStatusController` generation ve priority ile görünür durumu seçer. Yeni neslin state'i eski worker callback'ini geçersiz kılar. Conversation request kimliği, Voice generation, Live Vision generation, Agent generation ve Codex session kimliği kendi domain sınırlarında ayrıca korunur.

Qt `FunctionWorker` yalnız callable'ı çalıştırır. İptal sonrası result/error signal'i yayınlamaz. Gerçek I/O iptali ilgili service/controller tarafından yapılır; worker cancellation thread öldürme mekanizması değildir.

## Kapanış sırası

1. Yeni Qt worker kabulü kapatılır ve mevcut worker'lar geç sonuç üretmeyecek şekilde işaretlenir.
2. Screen/Live Vision, Agent ve Codex aktif işleri durdurulur.
3. Intent confirmation ve hands-free command session iptal edilir.
4. Recorder, STT state, TTS playback ve wake detector kapatılır.
5. Inference benchmark/model lifecycle iptal edilir.
6. Notification scheduler durdurulur, tray gizlenir.
7. Qt thread pool en fazla 1,5 saniye beklenir; UI kapanışı sınırsız bloklanmaz.

Speech shutdown idempotent'tir. Recorder state'i yarışsa bile `stop()` çağrılır; kapanış nesli sonrasında STT sonucu veya state listener callback'i kabul edilmez. Agent cancellation token'ı controller lock beklenmeden önce set edilir. Codex process runner process tree cleanup uygular ve aktif metadata'yı `interrupted` olarak saklar.

## Recovery

Recovery otomatik execution değildir. Agent ve Codex başlangıçta yalnız metadata durumunu yüzeye çıkarır. Kullanıcı incelemeden ve yeniden onaylamadan araç/CLI işi başlamaz. Codex `reviewing` aktif process sayılmaz; uygulama restart'ında değişiklik inceleme kaydı korunur.
