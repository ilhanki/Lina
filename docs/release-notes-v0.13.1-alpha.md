# Lina v0.13.1-alpha — Real Codex CLI Transport

## Özet

Bu sürüm v0.13.0 foundation katmanını resmi Codex CLI’ye bağlar. Workspace seçimi, task planı, Lina approval, CLI sandbox, JSONL event stream, verification ve Türkçe sonuç sunumu tek kontrollü akışta çalışır. Credential yönetimi bütünüyle resmi CLI’de kalır.

## Eklenenler

- Windows öncelikli executable discovery ve semantic version policy.
- Gerçek help çıktısından exec/JSON/stdin/cd/sandbox/approval/resume/device-auth/doctor capability detection.
- `codex login status`, ChatGPT login, desteklenen device login ve confirmation’lı logout.
- Shell-free argument builder, stdin prompt, incremental JSONL parser ve typed errors/events.
- Timeout, cancellation, Windows process group cleanup ve shutdown interruption.
- Secret/path filtresi, redaction, sensitive-output detection ve workspace fingerprint verification.
- CLI setup inspector’ı, background Qt execution, fixed-short Voice durumları ve genişletilmiş ayarlar.
- Metadata-only audit alanları ve `0.13.1a0` / `v0.13.1-alpha` version contract.

## Güvenlik

Lina auth cache veya token okumaz. API key alanı yoktur. CLI sandbox/approval kapatılmaz; bypass/yolo/never/add-dir üretilmez. Otomatik commit, push, tag, install veya resume yoktur. Ham JSONL/stderr chat, TTS ve history’ye verilmez.

## Doğrulama

Toplam 1180 test geçer. Unit testler gerçek ağ veya kullanıcı hesabı kullanmaz; fake runner/process fixture’ları discovery, auth, builder, stream, cancel, timeout, security, verification, GUI, Voice ve shutdown sınırlarını kapsar. Compileall ve PySide6 import doğrulaması geçer. Gerçek local CLI WindowsApps altında keşfedildi ancak OS ACL process başlatmayı reddetti; bu nedenle kısa real read-only task çalıştırılmadı ve unavailable durumu dürüstçe kaydedildi.

## Bilinen sınırlamalar

- Güvenli session resume ve diff review v0.13.2 kapsamındadır.
- Non-interactive runtime approval için belgeli cevap kanalı yoksa görev interaktif devam gerektirir.
- WindowsApps ACL veya kurum politikası CLI executable’ını engellerse kullanıcı resmi kurulum/terminal politikasını düzeltmelidir; Lina bypass etmez.

Push ve `v0.13.1-alpha` tag bu sprintte yapılmaz.
