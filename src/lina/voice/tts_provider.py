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


class QtWindowsTTSProvider:
    """Use PySide6's installed Windows WinRT/SAPI engines without new dependencies."""

    def __init__(self, engine_factory: Any | None = None, synthesis_timeout: float = 60.0) -> None:
        self._cancelled = threading.Event()
        self._engine_factory = engine_factory
        self._synthesis_timeout = max(1.0, synthesis_timeout)

    def _create_engine(self):
        if self._engine_factory is not None:
            return self._engine_factory()
        try:
            from PySide6.QtCore import QCoreApplication
            from PySide6.QtTextToSpeech import QTextToSpeech
        except ImportError:
            return None
        if QCoreApplication.instance() is None:
            return None
        engines = QTextToSpeech.availableEngines()
        selected = next((name for name in ("winrt", "sapi") if name in engines), None)
        try:
            return QTextToSpeech(selected) if selected else QTextToSpeech()
        except Exception:
            return None

    def is_available(self) -> bool:
        engine = self._create_engine()
        if engine is None:
            return False
        try:
            state_name = getattr(engine.state(), "name", str(engine.state()).rsplit(".", 1)[-1])
            return state_name != "Error" and bool(engine.availableVoices())
        except Exception:
            return False

    def list_voices(self) -> tuple[SystemVoice, ...]:
        engine = self._create_engine()
        if engine is None:
            return ()
        voices: list[SystemVoice] = []
        try:
            for voice in engine.availableVoices():
                locale = voice.locale().name()
                voices.append(
                    SystemVoice(
                        id=f"{voice.name()}|{locale}",
                        name=voice.name(),
                        language="tr" if locale.casefold().startswith("tr") else locale,
                    )
                )
        except Exception:
            return ()
        return tuple(voices)

    def speak(self, text: str, voice_id: str | None, rate: float, volume: float) -> None:
        try:
            from PySide6.QtCore import QEventLoop, QTimer
            from PySide6.QtTextToSpeech import QTextToSpeech
        except ImportError as error:
            raise VoiceUnavailableError("Sesli yanıt şu anda kullanılamıyor.") from error
        engine = self._create_engine()
        if engine is None:
            raise VoiceUnavailableError("Sesli yanıt şu anda kullanılamıyor.")
        self._cancelled.clear()
        try:
            selected = self._select_voice(engine, voice_id)
            if selected is not None:
                engine.setVoice(selected)
            engine.setRate(max(-1.0, min(1.0, rate - 1.0)))
            engine.setVolume(max(0.0, min(1.0, volume)))
            loop = QEventLoop()
            timer = QTimer()
            timer.setInterval(50)
            started = time.monotonic()
            timed_out = [False]

            def poll_cancel() -> None:
                if self._cancelled.is_set():
                    engine.stop()
                    loop.quit()
                elif time.monotonic() - started >= self._synthesis_timeout:
                    timed_out[0] = True
                    engine.stop()
                    loop.quit()

            def state_changed(state) -> None:
                if state in {QTextToSpeech.State.Ready, QTextToSpeech.State.Error}:
                    loop.quit()

            timer.timeout.connect(poll_cancel)
            engine.stateChanged.connect(state_changed)
            timer.start()
            engine.say(text)
            if engine.state() not in {QTextToSpeech.State.Ready, QTextToSpeech.State.Error}:
                loop.exec()
            timer.stop()
            if timed_out[0]:
                raise VoicePlaybackError("Sesli yanıt oluşturulamadı.")
            if engine.state() is QTextToSpeech.State.Error:
                raise VoicePlaybackError("Sesli yanıt oynatılamadı.")
        except VoicePlaybackError:
            raise
        except Exception as error:
            raise VoicePlaybackError("Sesli yanıt oynatılamadı.") from error

    def _select_voice(self, engine: Any, voice_id: str | None):
        voices = list(engine.availableVoices())
        if voice_id:
            for voice in voices:
                identifier = f"{voice.name()}|{voice.locale().name()}"
                if identifier == voice_id:
                    return voice
        for voice in voices:
            if voice.locale().name().casefold().startswith("tr"):
                return voice
        return voices[0] if voices else None

    def stop(self) -> None:
        self._cancelled.set()


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
