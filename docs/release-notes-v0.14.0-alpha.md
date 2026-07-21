# Lina v0.14.0-alpha

Bu sürüm yeni bir “her şeyi yapar” yetkisi eklemek yerine mevcut ürünün entegrasyonlarını denetler, gerçek hata yollarını onarır ve kullanıcıya gösterilen sonuçları kanıta bağlar.

## Başlıca değişiklikler

- Uygulama, durum ve shutdown sözleşmeleri tekleştirildi. Qt worker sonuçları kapanıştan sonra UI'ya dönmez; speech nesil koruması geç state callback'lerini engeller.
- Codex geçmişi atomik ve thread-safe yazılır. Resume cümlesindeki yeni talimat ayrı bağlayıcı görevdir; eski görev yalnız remote session bağlamıdır.
- Test çalıştırılması istenen Codex görevi, güvenli test kategorisi ve başarılı command exit kanıtı olmadan tamamlanmış sayılmaz.
- Dosya değiştiren Codex görevi `reviewing` durumunda kalır; kullanıcı değişiklik incelemesini kabul etmeden `completed` olmaz.
- Agent iptal jetonu, çalışan adım controller kilidini tutarken bile executor'a hemen ulaşır.
- TXT, Markdown, Python, JSON, CSV, PDF, DOCX ve XLSX dosyaları açık kullanıcı seçimiyle, salt-okunur ve bounded belge bağlamı olarak eklenebilir.
- Memory doğrudan servis çağrılarında da boş/hassas içeriği reddeder; pasif kayıtlar şeffaf geçmiş sorgusunda görülebilir.
- TTS kopyası path, diff, log, multiline JSON, kod, URL ve Base64 yüklerini seslendirmez; yazılı yanıt değişmez.
- Bulunamayan bir conversation kimliği artık sağlam SQLite geçmişini tüm oturum için kapatmaz.
- Codex durum ve risk değerleri arayüzde merkezi Türkçe etiketlerle gösterilir.

## Güvenlik sınırları

- Mikrofon, kamera, ekran, dosya seçimi, Agent ve Codex işlemleri açık kullanıcı eylemi ister.
- Belge ekleri bellekte tutulur; ham içerik conversation, Agent veya Codex metadata geçmişine yazılmaz.
- Codex CLI credential/auth dosyası Lina tarafından okunmaz. Sandbox ve approval birbirinden bağımsız kapılardır; runtime approval otomatik kabul edilmez.
- Bridge commit, push, tag, reset, clean, rebase, paket kurulumu veya rollback yapmaz.

## Doğrulama özeti

- Tam otomatik paket: `1384 passed` (ilk tam v0.14 turu).
- `compileall` ve `pip check` release kapanışında yeniden çalıştırılır.
- Gerçek Codex CLI bulundu (`0.144.6`) ancak yerel oturum açık olmadığı için başarılı remote smoke yapılamadı; bu durum testle taklit edilmedi.
- Mikrofon yalnız enumerate edildi. Kamera/mikrofon kaydı otomatik başlatılmadı.

## Bilinen sınırlar

- Alpha veri ve UI sözleşmeleri kararlı sürümden önce değişebilir.
- PDF çıkarımı metin taşıyan bounded content stream'lerle sınırlıdır; OCR ve şifre çözme yoktur.
- Hatırlatıcı delivery için Lina'nın açık veya system tray'de olması gerekir.
- Gerçek Ollama model kalitesi, TTS voice, kamera, multi-monitor/DPI ve Codex auth smoke'ları hedef Windows makinesinde manuel doğrulama ister.
