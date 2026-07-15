"""Typed models that never expose raw live-vision frames to the UI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping
from uuid import uuid4


class LiveVisionSource(str, Enum):
    CAMERA = "camera"
    SCREEN = "screen"
    REGION = "region"


class LiveVisionState(str, Enum):
    DISABLED = "disabled"
    IDLE = "idle"
    STARTING = "starting"
    MONITORING = "monitoring"
    CHANGE_DETECTED = "change_detected"
    ANALYZING = "analyzing"
    SPEAKING = "speaking"
    PAUSED = "paused"
    STOPPING = "stopping"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class CameraConversationState(str, Enum):
    INACTIVE = "inactive"
    OBSERVING = "observing"
    ANALYZING = "analyzing"
    SPEAKING = "speaking"
    LISTENING = "listening"
    PAUSED = "paused"
    ERROR = "error"


class ChangeSensitivity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LiveVisionError(RuntimeError):
    """A safe, user-facing live vision failure."""


@dataclass(frozen=True, slots=True)
class ChangeRegion:
    """A normalized image-change rectangle; it is not an object detection."""

    x: float
    y: float
    width: float
    height: float
    score: float = 0.0

    def __post_init__(self) -> None:
        if not all(0.0 <= value <= 1.0 for value in (self.x, self.y, self.width, self.height, self.score)):
            raise ValueError("Change region values must be normalized")
        if self.width <= 0 or self.height <= 0 or self.x + self.width > 1.000001 or self.y + self.height > 1.000001:
            raise ValueError("Change region must fit within the frame")


@dataclass(frozen=True, slots=True)
class PreviewFrameEvent:
    session_id: str
    generation_id: int
    frame: "LiveVisionFrame"


@dataclass(frozen=True, slots=True)
class ChangeRegionsEvent:
    session_id: str
    generation_id: int
    regions: tuple[ChangeRegion, ...]
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class OverlayGeometry:
    x: int
    y: int
    width: int
    height: int
    screen_name: str = ""

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Overlay geometry must be positive")


@dataclass(frozen=True, slots=True)
class OverlayGeometryEvent:
    session_id: str
    generation_id: int
    geometry: OverlayGeometry


@dataclass(frozen=True, slots=True)
class SessionStoppedEvent:
    session_id: str
    generation_id: int


@dataclass(frozen=True, slots=True)
class LiveVisionConfig:
    capture_interval_seconds: float = 2.0
    minimum_analysis_interval_seconds: float = 5.0
    sensitivity: ChangeSensitivity = ChangeSensitivity.MEDIUM
    voice_feedback_enabled: bool = True
    speak_only_meaningful_changes: bool = True
    repeat_speech_cooldown_seconds: float = 30.0
    duration_seconds: float | None = 300.0
    automatic_commentary_enabled: bool = True

    def __post_init__(self) -> None:
        if not 0.25 <= self.capture_interval_seconds <= 60:
            raise ValueError("Capture interval must be between 0.25 and 60 seconds")
        if not 0 <= self.minimum_analysis_interval_seconds <= 3600:
            raise ValueError("Analysis interval must be between 0 and 3600 seconds")
        if self.duration_seconds is not None and self.duration_seconds <= 0:
            raise ValueError("Session duration must be positive")


@dataclass(frozen=True, slots=True)
class LiveVisionFrame:
    """One ephemeral encoded frame. Controllers clear references after use."""

    data: bytes
    width: int
    height: int
    captured_at: datetime
    source: LiveVisionSource
    mime_type: str = "image/png"
    source_label: str = ""

    def __post_init__(self) -> None:
        if not self.data or self.width <= 0 or self.height <= 0:
            raise LiveVisionError("Görüntü alınamadı.")
        if self.mime_type not in {"image/png", "image/jpeg"}:
            raise LiveVisionError("Görüntü biçimi desteklenmiyor.")


@dataclass(frozen=True, slots=True)
class LiveVisionSession:
    source: LiveVisionSource
    user_focus: str = ""
    config: LiveVisionConfig = field(default_factory=LiveVisionConfig)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    session_id: str = field(default_factory=lambda: uuid4().hex)

    def __post_init__(self) -> None:
        clean = " ".join(self.user_focus.split())
        if len(clean) > 500:
            raise ValueError("Takip hedefi en fazla 500 karakter olabilir")
        object.__setattr__(self, "user_focus", clean)


@dataclass(frozen=True, slots=True)
class CameraConversationContext:
    session_id: str
    state: CameraConversationState
    latest_frame: LiveVisionFrame | None = None
    latest_semantic_summary: str = ""
    latest_spoken_summary: str = ""
    last_analysis_at: datetime | None = None
    last_user_question: str = ""


@dataclass(frozen=True, slots=True)
class LiveVisionMetrics:
    captured_frame_count: int = 0
    dropped_frame_count: int = 0
    meaningful_change_count: int = 0
    analysis_request_count: int = 0
    average_analysis_duration_ms: int = 0
    last_analysis_latency_ms: int | None = None
    session_duration_seconds: float = 0.0
    source: LiveVisionSource | None = None
    empty_response_count: int = 0


@dataclass(frozen=True, slots=True)
class LiveVisionSnapshot:
    state: LiveVisionState
    source: LiveVisionSource | None = None
    source_label: str = ""
    session_id: str | None = None
    last_analysis_at: datetime | None = None
    last_result: str = ""
    user_message: str = ""
    metrics: LiveVisionMetrics = field(default_factory=LiveVisionMetrics)
    metadata: Mapping[str, str] = field(default_factory=dict)
