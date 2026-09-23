from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class CaptureRecord:
    capture_id: str
    project_id: str
    scene_label: str
    status: str
    local_path: Path | None = None
    width: int | None = None
    height: int | None = None
    file_size_bytes: int | None = None
    camera_file: str | None = None
    backend: str | None = None
    in_camera_stitch: bool = True
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    extra: dict[str, Any] = field(default_factory=dict)


class CaptureStore:
    """In-memory capture sessions for the local Bridge process."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._items: dict[str, CaptureRecord] = {}
        self._busy = False

    def try_begin(self) -> bool:
        with self._lock:
            if self._busy:
                return False
            self._busy = True
            return True

    def end(self) -> None:
        with self._lock:
            self._busy = False

    @property
    def busy(self) -> bool:
        with self._lock:
            return self._busy

    def put(self, record: CaptureRecord) -> None:
        with self._lock:
            self._items[record.capture_id] = record

    def get(self, capture_id: str) -> CaptureRecord | None:
        with self._lock:
            return self._items.get(capture_id)

    def discard(self, capture_id: str) -> CaptureRecord | None:
        with self._lock:
            record = self._items.get(capture_id)
            if record is None:
                return None
            record.status = "discarded"
            path = record.local_path
            record.local_path = None
        if path is not None and path.exists():
            path.unlink(missing_ok=True)
        return record
