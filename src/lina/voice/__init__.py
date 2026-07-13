"""Framework-neutral local voice interaction foundation."""

from lina.voice.controller import VoiceController
from lina.voice.models import VoiceError, VoiceSettings, VoiceState
from lina.voice.playback import AudioPlaybackService
from lina.voice.tts_provider import WindowsSapiTTSProvider

__all__ = [
    "AudioPlaybackService",
    "VoiceController",
    "VoiceError",
    "VoiceSettings",
    "VoiceState",
    "WindowsSapiTTSProvider",
]
