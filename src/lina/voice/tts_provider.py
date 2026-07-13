"""Local text-to-speech contracts and Windows SAPI implementation."""

from __future__ import annotations

import logging
import re
import threading
import time
from typing import Any, Protocol

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtTextToSpeech import QTextToSpeech

from lina.voice.models import SystemVoice, VoicePlaybackError, VoiceUnavailableError


MAX_SPOKEN_CHARACTERS = 700
_logger = logging.getLogger("lina.voice")


class _QtSpeechBridge(QObject):
    """Own the WinRT engine on the GUI thread until real playback completes."""

    start_requested = Signal(int, str, object, float, float)
    stop_requested = Signal()
    finished = Signal(int, bool, str)

    def __init__(self) -> None:
        super().__init__()
        self._engine: QTextToSpeech | None = None
        self._request_id = 0
        self._selected_voice_id: str | None = None
        self._retried_default = False
        self._playing = False
        self._started_at = 0.0
        self._text = ""
        self._rate = 1.0
        self._volume = 1.0
        self.start_requested.connect(self._start)
        self.stop_requested.connect(self._stop)
        self._replace_engine()

    @property
    def available(self) -> bool:
        return self._engine is not None and bool(self._engine.availableVoices())

    def voices(self) -> tuple[SystemVoice, ...]:
        if self._engine is None:
            return ()
        return tuple(_qt_system_voice(voice) for voice in self._engine.availableVoices())

    def _replace_engine(self) -> bool:
        if self._engine is not None:
            self._engine.deleteLater()
        if "winrt" not in QTextToSpeech.availableEngines():
            self._engine = None
            return False
        engine = QTextToSpeech("winrt", self)
        engine.stateChanged.connect(self._state_changed)
        engine.errorOccurred.connect(self._error_occurred)
        engine.aboutToSynthesize.connect(self._about_to_synthesize)
        self._engine = engine
        return True

    @Slot(int, str, object, float, float)
    def _start(self, request_id: int, text: str, voice_id: object, rate: float, volume: float) -> None:
        if self._engine is None:
            self.finished.emit(request_id, False, "unavailable")
            return
        self._request_id = request_id
        self._selected_voice_id = voice_id if isinstance(voice_id, str) else None
        self._retried_default = False
        self._playing = False
        self._started_at = time.monotonic()
        self._text = text
        self._rate = rate
        self._volume = volume
        self._apply_voice(self._selected_voice_id)
        self._engine.setRate(max(-1.0, min(1.0, rate - 1.0)))
        self._engine.setVolume(_clamp_volume(volume))
        self._engine.say(text)

    def _apply_voice(self, voice_id: str | None) -> None:
        if self._engine is None or not voice_id:
            return
        for voice in self._engine.availableVoices():
            if _qt_voice_id(voice) == voice_id:
                self._engine.setVoice(voice)
                return

    @Slot(int)
    def _about_to_synthesize(self, _utterance_id: int) -> None:
        _logger.info("tts_synthesis_started")

    @Slot(QTextToSpeech.State)
    def _state_changed(self, state: QTextToSpeech.State) -> None:
        if not self._request_id:
            return
        _logger.info("tts_state state=%s", state.name)
        if state is QTextToSpeech.State.Speaking and not self._playing:
            self._playing = True
            _logger.info(
                "tts_synthesis_completed audio_bytes=not_exposed "
                "audio_duration_ms=not_exposed mime=audio/winrt-direct"
            )
            _logger.info("playback_started")
            return
        if state is QTextToSpeech.State.Ready and self._playing:
            duration_ms = round((time.monotonic() - self._started_at) * 1000)
            _logger.info("playback_completed audio_duration_ms=%d", duration_ms)
            request_id = self._request_id
            self._request_id = 0
            self._playing = False
            self.finished.emit(request_id, True, "")

    @Slot(QTextToSpeech.ErrorReason, str)
    def _error_occurred(self, _reason: QTextToSpeech.ErrorReason, _message: str) -> None:
        if not self._request_id:
            return
        _logger.warning("tts_engine_error error_category=playback")
        if self._selected_voice_id and not self._retried_default:
            self._retried_default = True
            self._playing = False
            if self._replace_engine() and self._engine is not None:
                self._engine.setRate(max(-1.0, min(1.0, self._rate - 1.0)))
                self._engine.setVolume(_clamp_volume(self._volume))
                self._engine.say(self._text)
                return
        request_id = self._request_id
        self._request_id = 0
        self._playing = False
        self.finished.emit(request_id, False, "playback")

    @Slot()
    def _stop(self) -> None:
        request_id = self._request_id
        self._request_id = 0
        self._playing = False
        if self._engine is not None:
            self._engine.stop()
        if request_id:
            self.finished.emit(request_id, False, "cancelled")


def _qt_voice_id(voice: Any) -> str:
    return f"{voice.name()}|{voice.locale().name()}"


def _qt_system_voice(voice: Any) -> SystemVoice:
    locale = voice.locale().name()
    return SystemVoice(
        id=_qt_voice_id(voice),
        name=voice.name(),
        language="tr" if locale.casefold().startswith("tr") else locale,
    )


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
    """Use only PySide6's Windows WinRT engine without mixing SAPI voices."""

    def __init__(self, engine_factory: Any | None = None, synthesis_timeout: float = 60.0) -> None:
        self._cancelled = threading.Event()
        self._engine_factory = engine_factory
        self._synthesis_timeout = max(1.0, synthesis_timeout)
        self._bridge: _QtSpeechBridge | None = None
        self._request_lock = threading.Lock()
        self._request_sequence = 0
        self._pending: dict[int, tuple[threading.Event, list[object]]] = {}

    def _ensure_bridge(self) -> _QtSpeechBridge | None:
        if self._bridge is not None:
            return self._bridge
        try:
            from PySide6.QtCore import QCoreApplication
        except ImportError:
            return None
        application = QCoreApplication.instance()
        if application is None or QThread.currentThread() is not application.thread():
            return None
        bridge = _QtSpeechBridge()
        bridge.finished.connect(self._bridge_finished)
        self._bridge = bridge
        return bridge

    def _bridge_finished(self, request_id: int, success: bool, category: str) -> None:
        with self._request_lock:
            pending = self._pending.get(request_id)
        if pending is None:
            return
        event, result = pending
        result[:] = [success, category]
        event.set()

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
        if "winrt" not in engines:
            return None
        try:
            return QTextToSpeech("winrt")
        except Exception:
            return None

    def is_available(self) -> bool:
        if self._engine_factory is None:
            bridge = self._ensure_bridge()
            return bool(bridge and bridge.available)
        engine = self._create_engine()
        if engine is None:
            return False
        try:
            state_name = getattr(engine.state(), "name", str(engine.state()).rsplit(".", 1)[-1])
            return state_name != "Error" and bool(engine.availableVoices())
        except Exception:
            return False

    def list_voices(self) -> tuple[SystemVoice, ...]:
        if self._engine_factory is None:
            bridge = self._ensure_bridge()
            return bridge.voices() if bridge is not None else ()
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
        if self._engine_factory is None:
            self._speak_via_bridge(text, voice_id, rate, volume)
            return
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
            self._speak_once(engine, text, rate, volume, QEventLoop, QTimer, QTextToSpeech)
        except VoicePlaybackError:
            if not voice_id:
                raise
            fallback_engine = self._create_engine()
            if fallback_engine is None:
                raise
            self._cancelled.clear()
            self._speak_once(
                fallback_engine,
                text,
                rate,
                volume,
                QEventLoop,
                QTimer,
                QTextToSpeech,
            )
        except Exception as error:
            if voice_id:
                fallback_engine = self._create_engine()
                if fallback_engine is not None:
                    try:
                        self._cancelled.clear()
                        self._speak_once(
                            fallback_engine,
                            text,
                            rate,
                            volume,
                            QEventLoop,
                            QTimer,
                            QTextToSpeech,
                        )
                        return
                    except Exception:
                        pass
            raise VoicePlaybackError("Sesli yanıt oynatılamadı.") from error

    def _speak_once(self, engine: Any, text: str, rate: float, volume: float, event_loop_type: Any, timer_type: Any, tts_type: Any) -> None:
        engine.setRate(max(-1.0, min(1.0, rate - 1.0)))
        engine.setVolume(_clamp_volume(volume))
        loop = event_loop_type()
        timer = timer_type()
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
            if state in {tts_type.State.Ready, tts_type.State.Error}:
                loop.quit()

        timer.timeout.connect(poll_cancel)
        engine.stateChanged.connect(state_changed)
        timer.start()
        engine.say(text)
        if engine.state() not in {tts_type.State.Ready, tts_type.State.Error}:
            loop.exec()
        timer.stop()
        if timed_out[0]:
            raise VoicePlaybackError("Sesli yanıt oluşturulamadı.")
        if engine.state() is tts_type.State.Error:
            raise VoicePlaybackError("Sesli yanıt oynatılamadı.")

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
        if self._bridge is not None:
            self._bridge.stop_requested.emit()

    def _speak_via_bridge(self, text: str, voice_id: str | None, rate: float, volume: float) -> None:
        bridge = self._bridge
        if bridge is None:
            raise VoiceUnavailableError("Sesli yanıt şu anda kullanılamıyor.")
        self._cancelled.clear()
        with self._request_lock:
            self._request_sequence += 1
            request_id = self._request_sequence
            event = threading.Event()
            result: list[object] = []
            self._pending[request_id] = (event, result)
        bridge.start_requested.emit(request_id, text, voice_id, rate, volume)
        completed = event.wait(self._synthesis_timeout)
        with self._request_lock:
            self._pending.pop(request_id, None)
        if not completed:
            bridge.stop_requested.emit()
            raise VoicePlaybackError("Sesli yanıt zaman aşımına uğradı.")
        success = bool(result and result[0])
        category = str(result[1]) if len(result) > 1 else "playback"
        if not success and category != "cancelled":
            raise VoicePlaybackError("Sesli yanıt oynatılamadı.")


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


def _clamp_volume(volume: float) -> float:
    """Return the Qt audio volume in its documented zero-to-one range."""
    return max(0.0, min(1.0, volume))


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
