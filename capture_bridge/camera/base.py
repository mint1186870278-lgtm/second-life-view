from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CameraInfo:
    connected: bool
    model: str | None = None
    firmware: str | None = None
    detail: str | None = None


@dataclass
class RawCapture:
    local_path: Path
    width: int
    height: int
    camera_file: str | None = None
    in_camera_stitch: bool = True


class CameraBackend(ABC):
    name: str

    @abstractmethod
    def health(self) -> CameraInfo:
        ...

    @abstractmethod
    def capture_photo(self, dest_dir: Path, capture_id: str) -> RawCapture:
        """Take a photo and download into dest_dir. Raise BridgeError on failure."""
        ...
