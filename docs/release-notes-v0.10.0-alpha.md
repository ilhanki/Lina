# Lina v0.10.0-alpha

## Voice Interaction

- İsteğe bağlı local Windows SAPI ile Türkçe sesli yanıt.
- Yazılı timeline ve final-response TTS birlikte çalışır.
- Push-to-talk için composer’a ekle / otomatik gönder seçenekleri.
- Mic barge-in, “Sesi Durdur” ve stale playback callback koruması.
- Voice state indicator ve tek aktif playback garantisi.
- Production detector içermeyen, varsayılan kapalı wake-word foundation.

## Performance Foundation

- Ollama streaming ve privacy-safe `InferenceMetrics`.
- İlk token, toplam süre, prompt/generated token, token/sn, load ve eval duration alanları.
- History ve kullanıcı verisi kullanmayan async Performans Testi.
- Keep-alive, maximum output, context budget ve opt-in background warm-up.
- Düşük VRAM için text/vision best-effort unload lifecycle.
- En yeni complete pair’leri koruyan deterministik context trimming.

## Privacy ve Safety

- Cloud TTS/speech servisi, shell execution ve yeni dependency yok.
- Mikrofon yalnız açık kullanıcı eylemiyle başlar; wake word default kapalıdır.
- Raw audio ve TTS çıktısı persist edilmez; audio bytes loglanmaz.
- Metrics içinde prompt, mesaj veya dosya içeriği yoktur.
- TTS hatası yazılı sohbeti durdurmaz.

## Bilinen Sınırlar

- Yerel TTS mevcut PySide6 Windows WinRT/SAPI motorunu kullanır; sistem motoru veya voice yoksa güvenli unavailable fallback devreye girer.
- Production wake-word/hands-free detector v0.10.1-alpha kapsamındadır.
- Full camera/live vision v0.11.0-alpha, agent mode v0.12.0-alpha ve Codex bridge v0.13.0-alpha kapsamındadır.
- Gerçek Windows voice, audio device, Ollama VRAM ve font scaling davranışı release öncesi manuel smoke test gerektirir.

Bu sprint `v0.10.0-alpha` tag’ini oluşturmaz.
