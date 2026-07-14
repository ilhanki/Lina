# Lina v0.10.1-alpha

## Wake Word & Hands-Free Conversation

- Varsayılan kapalı ve açık privacy onaylı hands-free conversation.
- `WakeWordDetector` protokolünü tamamlayan local `STTWakeWordDetector`.
- Yeni ağır model veya dependency olmadan sounddevice + faster-whisper reuse.
- Sessizliği full STT’ye göndermeyen enerji kapılı `SoundDeviceWakeAudioSource`.
- Conservative `hey lina`, `he lina` ve punctuation/casing normalization.
- Görünür `wake_listening`, `wake_detected`, `command_listening`, `transcribing`, `thinking`, `speaking`, `cooldown` durumları.

## VAD, Cooldown ve Barge-in

- Peak-energy tabanlı bounded PCM VAD.
- Yaklaşık 1 saniye trailing silence, 250 ms minimum speech ve bounded no-speech/max duration.
- Sessizlik, kısa gürültü, speech end ve maximum duration ayrımı.
- Playback sonrası 1.5 saniye wake cooldown.
- TTS sırasında kısa gürültüyü reddeden, wake phrase zorunlu barge-in politikası.
- Playback generation invalidation ile stale callback ve duplicate response koruması.

## Command & Voice Confirmation

- Wake phrase audio’sundan ayrı yeni command recording session.
- Başarılı transcription’ı mevcut normal send/intent routing yoluna otomatik aktarma.
- Boş, düşük confidence, no-input ve STT failure için kontrollü Türkçe geri bildirim.
- Reminder ve Memory confirmation sorularını seslendirme.
- Exact yes/no variant allowlist’i, ambiguous re-prompt ve 25 saniyelik safe timeout.
- New chat, conversation switch, delete, archive ve exit sırasında pending hands-free cleanup.

## Settings, UI, Tray ve Devices

- Settings schema v3 ve schema v1/v2 backward migration.
- Hands-free, wake word, wake phrase, indicator, return-to-wake, voice confirmation ve barge-in tercihleri.
- Etkinleştir/Vazgeç butonlu privacy confirmation.
- Header’da metinsel mic state, hands-free toggle ve pause/resume.
- Tray’de Hands-free Aç/Kapat, Dinlemeyi Duraklat ve Sesi Durdur.
- Asenkron input-device refresh/test, default device ve missing-device fallback.
- Dark/light/system theme ve mevcut font-scale stylesheet’iyle uyumlu standart kontroller.

## Privacy, Performance & Reliability

- Raw audio, transcription text, prompt veya TTS içeriği loglanmaz.
- Audio conversation/Memory/notification veritabanlarına yazılmaz.
- Audio cloud’a gönderilmez; cloud wake-word servisi eklenmez.
- Bounded queue ve PCM buffer; yalnız enerji kapılı speech segmentlerinde STT.
- Privacy-safe wake count, false-wake count, command/transcription duration ve end-to-end latency metadata’sı.
- Idempotent pause/cancel/shutdown ve detector/command worker join sınırları.

## Bilinen Sınırlar

- Wake accuracy faster-whisper modeline, input device’a, oda akustiğine ve gürültüye bağlıdır.
- Özel keyword engine veya acoustic echo cancellation yoktur.
- Barge-in yanlış kesmeyi azaltmak için doğrudan konuşma yerine wake phrase gerektirir.
- Uygulama tamamen kapalıyken hands-free çalışmaz; tray mode gerçek exit değildir.
- Camera/live vision `v0.11.0-alpha`, Agent Mode `v0.12.0-alpha`, Codex Bridge `v0.13.0-alpha` kapsamındadır.

Bu sprint `v0.10.1-alpha` tag’ini oluşturmaz.
