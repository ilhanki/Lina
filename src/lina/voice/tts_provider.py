"""Local text-to-speech contracts and Windows SAPI implementation."""

from __future__ import annotations

import re
import threading
import time
from typing import Any, Protocol

from lina.voice.models import SystemVoice, VoicePlaybackError, VoiceUnavailableError


MAX_SPOKEN_CHARACTERS = 700


class TextToSpeechProvider(Protocol):
    def is_available(self) -> bool: ...
    def list_voices(self) -> tuple[SystemVoice, ...]: ...
    def speak(self, text: str, voice_id: str | None, rate: float, volume: float) -> None: ...
    def stop(self) -> None: ...


def normalize_spoken_text(text: str, max_characters: int = MAX_SPOKEN_CHARACTERS) -> str:
    """Remove unsafe/noisy content while leaving the written response untouched."""
    value = re.sub(r"```[\s\S]*?```", " ", text)
    value = re.sub(r"`[^`\n]{1,200}`", " ", value)
    value = re.sub(r"https?://\S{40,}", " bağlantı ", value)
    value = re.sub(r"(?m)^\s*[\{\[][^\n]{40,}[\}\]]\s*$", " ", value)
    value = re.sub(r"(?i)\b[A-Za-z0-9+/]{120,}={0,2}\b", " ", value)
    value = re.sub(r"(?m)^\s*(?:Traceback|File \".*\", line \d+).*$", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= max_characters:
        return value
    shortened = value[:max_characters].rsplit(" ", 1)[0].rstrip(" ,;:")
    return f"{shortened}. Yanıtın devamı ekranda."


class UnavailableTTSProvider:
    def is_available(self) -> bool:
        return False

    def list_voices(self) -> tuple[SystemVoice, ...]:
        return ()

    def speak(self, text: str, voice_id: str | None, rate: float, volume: float) -> None:
        raise VoiceUnavailableError("Sesli yanıt şu anda kullanılamıyor.")

    def stop(self) -> None:
        return None


class WindowsSapiTTSProvider:
    """Use installed Windows SAPI voices when optional COM bindings are present."""

    def __init__(self, dispatch: Any | None = None, synthesis_timeout: float = 60.0) -> None:
        self._dispatch = dispatch
        self._cancelled = threading.Event()
        self._synthesis_timeout = max(1.0, synthesis_timeout)
        if self._dispatch is None:
            try:
                from win32com.client import Dispatch  # type: ignore[import-not-found]
            except ImportError:
                return
            self._dispatch = Dispatch

    def _get_speaker(self) -> Any | None:
        if self._dispatch is None:
            return None
        _initialize_com()
        try:
            return self._dispatch("SAPI.SpVoice")
        except Exception:
            return None

    def is_available(self) -> bool:
        return self._get_speaker() is not None

    def list_voices(self) -> tuple[SystemVoice, ...]:
        speaker = self._get_speaker()
        if speaker is None:
            return ()
        voices: list[SystemVoice] = []
        try:
            collection = speaker.GetVoices()
            for index in range(collection.Count):
                token = collection.Item(index)
                description = str(token.GetDescription())
                identifier = str(token.Id)
                voices.append(SystemVoice(identifier, description, _voice_language(description)))
        except Exception:
            return ()
        return tuple(voices)

    def speak(self, text: str, voice_id: str | None, rate: float, volume: float) -> None:
        speaker = self._get_speaker()
        if speaker is None:
            raise VoiceUnavailableError("Sesli yanıt şu anda kullanılamıyor.")
        try:
            self._cancelled.clear()
            selected = self._select_voice(speaker, voice_id)
            if selected is not None:
                speaker.Voice = selected
            speaker.Rate = round((max(0.5, min(rate, 2.0)) - 1.0) * 5)
            speaker.Volume = round(max(0.0, min(volume, 1.0)) * 100)
            speaker.Speak(text, 1)  # asynchronous on the dedicated playback thread
            started = time.monotonic()
            while not bool(speaker.WaitUntilDone(50)):
                if self._cancelled.is_set():
                    speaker.Speak("", 3)
                    return
                if time.monotonic() - started >= self._synthesis_timeout:
                    speaker.Speak("", 3)
                    raise VoicePlaybackError("Sesli yanıt oluşturulamadı.")
        except VoiceUnavailableError:
            raise
        except Exception as error:
            raise VoicePlaybackError("Sesli yanıt oynatılamadı.") from error

    def _select_voice(self, speaker: Any, voice_id: str | None) -> Any | None:
        collection = speaker.GetVoices()
        tokens = [collection.Item(index) for index in range(collection.Count)]
        if voice_id:
            for token in tokens:
                if str(token.Id) == voice_id:
                    return token
        for token in tokens:
            if "turkish" in str(token.GetDescription()).casefold() or "türk" in str(token.GetDescription()).casefold():
                return token
        return tokens[0] if tokens else None

    def stop(self) -> None:
        self._cancelled.set()


def _voice_language(description: str) -> str | None:
    normalized = description.casefold()
    return "tr" if "turkish" in normalized or "türk" in normalized else None


def _initialize_com() -> None:
    try:
        import pythoncom  # type: ignore[import-not-found]
    except ImportError:
        return
    try:
        pythoncom.CoInitialize()
    except Exception:
        return
