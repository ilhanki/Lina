"""Play a fixed sentence through Lina's real WinRT playback path."""

from __future__ import annotations

import logging
from pathlib import Path
import sys
import threading
import time

from PySide6.QtWidgets import QApplication


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lina.voice.playback import AudioPlaybackService  # noqa: E402
from lina.voice.tts_provider import QtWindowsTTSProvider  # noqa: E402


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    application = QApplication.instance() or QApplication([])
    provider = QtWindowsTTSProvider()
    if not provider.is_available():
        logging.error("tts_failed error_category=unavailable")
        return 1

    completed = threading.Event()
    outcomes = []
    playback = AudioPlaybackService(provider)
    playback.play(
        "Selam İlhan, Lina ses testi.",
        voice_id=None,
        rate=1.0,
        volume=1.0,
        callback=lambda _generation, result: (outcomes.append(result), completed.set()),
    )

    deadline = time.monotonic() + 20
    while not completed.is_set() and time.monotonic() < deadline:
        application.processEvents()
        time.sleep(0.01)
    playback.shutdown()
    return 0 if outcomes and outcomes[0].completed else 1


if __name__ == "__main__":
    raise SystemExit(main())
