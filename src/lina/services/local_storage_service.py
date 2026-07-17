"""Bounded, cached local workspace storage measurement."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from time import monotonic


@dataclass(frozen=True, slots=True)
class LocalStorageSnapshot:
    total_bytes: int
    file_count: int
    locations: tuple[Path, ...]
    truncated: bool = False


class LocalStorageService:
    """Measure approved local data folders off the GUI thread with a hard bound."""

    def __init__(
        self,
        locations: tuple[Path, ...],
        *,
        max_entries: int = 50_000,
        cache_seconds: float = 60.0,
    ) -> None:
        self.locations = tuple(path.resolve(strict=False) for path in locations)
        self.max_entries = max(1, max_entries)
        self.cache_seconds = max(0.0, cache_seconds)
        self._cached: LocalStorageSnapshot | None = None
        self._cached_at = 0.0
        self._lock = Lock()

    def measure(self, *, force: bool = False) -> LocalStorageSnapshot:
        with self._lock:
            if (
                not force
                and self._cached is not None
                and monotonic() - self._cached_at <= self.cache_seconds
            ):
                return self._cached
            total_bytes = 0
            file_count = 0
            truncated = False
            for location in self.locations:
                if not location.exists():
                    continue
                candidates = (location,) if location.is_file() else location.rglob("*")
                for candidate in candidates:
                    if file_count >= self.max_entries:
                        truncated = True
                        break
                    try:
                        if candidate.is_file() and not candidate.is_symlink():
                            total_bytes += candidate.stat().st_size
                            file_count += 1
                    except OSError:
                        continue
                if truncated:
                    break
            snapshot = LocalStorageSnapshot(
                total_bytes=total_bytes,
                file_count=file_count,
                locations=self.locations,
                truncated=truncated,
            )
            self._cached = snapshot
            self._cached_at = monotonic()
            return snapshot


def format_storage_size(value: int) -> str:
    size = max(0, int(value))
    units = ("B", "KB", "MB", "GB", "TB")
    amount = float(size)
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            return f"{amount:.1f} {unit}" if unit != "B" else f"{int(amount)} B"
        amount /= 1024
    return f"{size} B"
