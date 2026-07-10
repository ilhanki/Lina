"""Local faster-whisper speech-to-text provider."""

from __future__ import annotations

from collections.abc import Callable
from io import BytesIO
import threading
from typing import Any

from lina.speech.models import (
    AudioRecordingResult,
    SpeechTranscriptionError,
    SpeechTranscriptionResult,
    SpeechUnavailableError,
)


ModelFactory = Callable[..., Any]


class FasterWhisperSTTProvider:
    """Transcribe in-memory recordings with a lazily loaded local model."""

    def __init__(
        self,
        model_size: str,
        language: str,
        device: str,
        compute_type: str,
        model_factory: ModelFactory | None = None,
    ) -> None:
        self._model_size = model_size
        self._language = language
        self._device = device
        self._compute_type = compute_type
        self._model_factory = model_factory or _create_whisper_model
        self._model = None
        self._model_lock = threading.Lock()

    def is_available(self) -> bool:
        return True

    def transcribe(self, recording: AudioRecordingResult) -> SpeechTranscriptionResult:
        model = self._get_model()
        try:
            segments, _ = model.transcribe(
                BytesIO(recording.audio_data),
                language=self._language,
                task="transcribe",
            )
            text = " ".join(
                segment.text.strip()
                for segment in segments
                if segment.text.strip()
            )
        except Exception as error:
            raise SpeechTranscriptionError("Local speech transcription failed") from error

        return SpeechTranscriptionResult(
            text=text,
            confidence=None,
            source="faster_whisper",
            is_final=True,
            language=self._language,
            duration_seconds=recording.duration_seconds,
        )

    def _get_model(self):
        if self._model is not None:
            return self._model

        with self._model_lock:
            if self._model is not None:
                return self._model
            try:
                self._model = self._model_factory(
                    self._model_size,
                    device=self._device,
                    compute_type=self._compute_type,
                )
            except Exception as error:
                raise SpeechUnavailableError(
                    "Local speech model could not be prepared"
                ) from error
            return self._model


def _create_whisper_model(model_size: str, **kwargs):
    from faster_whisper import WhisperModel

    return WhisperModel(model_size, **kwargs)
