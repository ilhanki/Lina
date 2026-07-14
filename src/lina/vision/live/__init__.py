"""Privacy-first, framework-neutral live vision orchestration."""

from lina.vision.live.change_detector import FrameChangeDetector
from lina.vision.live.controller import LiveVisionController
from lina.vision.live.frame_source import CameraFrameSource, FrameSource, RegionFrameSource, ScreenFrameSource
from lina.vision.live.models import (
    CameraConversationContext,
    CameraConversationState,
    ChangeRegion,
    ChangeRegionsEvent,
    ChangeSensitivity,
    LiveVisionConfig,
    LiveVisionError,
    LiveVisionFrame,
    LiveVisionMetrics,
    LiveVisionSession,
    LiveVisionSnapshot,
    LiveVisionSource,
    LiveVisionState,
    OverlayGeometry,
    OverlayGeometryEvent,
    PreviewFrameEvent,
    SessionStoppedEvent,
)

__all__ = [
    "CameraConversationContext", "CameraConversationState", "CameraFrameSource", "ChangeRegion", "ChangeRegionsEvent", "ChangeSensitivity", "FrameChangeDetector", "FrameSource",
    "LiveVisionConfig", "LiveVisionController", "LiveVisionError", "LiveVisionFrame",
    "LiveVisionMetrics", "LiveVisionSession", "LiveVisionSnapshot", "LiveVisionSource",
    "LiveVisionState", "OverlayGeometry", "OverlayGeometryEvent", "PreviewFrameEvent",
    "RegionFrameSource", "ScreenFrameSource", "SessionStoppedEvent",
]
