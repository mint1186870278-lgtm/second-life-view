from __future__ import annotations

import locale
import os
import subprocess
import threading
import time
from pathlib import Path

from PIL import Image

from capture_bridge.camera.base import CameraBackend, CameraInfo, RawCapture
from capture_bridge.camera.errors import BridgeError


def _console_encoding() -> str:
    env = os.environ.get("CAPTURE_BRIDGE_DEMO_ENCODING")
    if env:
        return env
    if os.name == "nt":
        return locale.getpreferredencoding(False) or "gbk"
    return "utf-8"


def _default_demo_exe(repo_root: Path) -> Path:
    env = os.environ.get("CAPTURE_BRIDGE_DEMO_EXE")
    if env:
        return Path(env)
    return repo_root / "tools" / "insta360" / "CameraSDK" / "bin" / "CameraSDKDemo.exe"


class DemoAutoBackend(CameraBackend):
    """One-click: launch CameraSDKDemo and drive menus via stdin.

    Sequence (Chinese Demo):
      main 1           -> Photo
      photo 1          -> select mode
      mode  <index>    -> default 0 = 普通拍照 (X4 Air ERP with in-camera stitch)
      photo 10         -> take photo + download
      path  <dir>      -> download folder
      photo 0, main 0  -> exit

    Not a long-term product architecture — pragmatic verification path.
    """

    name = "demo_auto"

    def __init__(
        self,
        demo_exe: Path,
        download_dir: Path,
        timeout_sec: float = 240.0,
        photo_mode_index: int = 0,
    ) -> None:
        self.demo_exe = demo_exe
        self.download_dir = download_dir
        self.timeout_sec = timeout_sec
        self.photo_mode_index = photo_mode_index

    def health(self) -> CameraInfo:
        ok = self.demo_exe.exists()
        return CameraInfo(
            connected=ok,
            model="X4 Air (CameraSDKDemo auto)",
            detail=(
                f"Will launch {self.demo_exe} and auto-run take+download into {self.download_dir}"
                if ok
                else f"Demo not found: {self.demo_exe}"
            ),
        )

    def capture_photo(self, dest_dir: Path, capture_id: str) -> RawCapture:
        if not self.demo_exe.exists():
            raise BridgeError("SDK_INIT_FAILED", f"CameraSDKDemo not found: {self.demo_exe}")

        self.download_dir.mkdir(parents=True, exist_ok=True)
        dest_dir.mkdir(parents=True, exist_ok=True)

        before = self._snapshot()
        save_dir = str(self.download_dir.resolve()).replace("\\", "/")

        log_lines: list[str] = []
        proc = subprocess.Popen(
            [str(self.demo_exe), "--cn"],
            cwd=str(self.demo_exe.parent),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding=_console_encoding(),
            errors="replace",
            bufsize=1,
        )

        reader = threading.Thread(
            target=self._pump_stdout,
            args=(proc, log_lines),
            daemon=True,
        )
        reader.start()

        try:
            if not self._wait_for(log_lines, ("主菜单", "CameraSDK Demo", "打开相机成功", "Succeed"), self.timeout_sec * 0.4):
                raise BridgeError(
                    "CAMERA_NOT_FOUND",
                    "Demo did not reach main menu. Check USB Android mode / camera power.\n"
                    + self._tail(log_lines),
                )

            self._send(proc, "1")  # Photo
            time.sleep(1.0)
            self._send(proc, "1")  # select mode
            time.sleep(1.0)
            self._send(proc, str(self.photo_mode_index))  # e.g. 0 = 普通拍照
            time.sleep(1.5)
            self._send(proc, "10")  # take + download

            if not self._wait_for(log_lines, ("保存目录", "save directory"), 90.0):
                # Still send path in case prompt was missed in log encoding
                pass
            time.sleep(0.5)
            self._send(proc, save_dir)

            newest = self._wait_new_file(before, self.timeout_sec)
            if newest is None:
                raise BridgeError(
                    "DOWNLOAD_FAILED",
                    "Demo finished sequence but no new JPG appeared in "
                    f"{self.download_dir}.\n"
                    + self._tail(log_lines),
                )

            # Exit menus cleanly
            time.sleep(0.5)
            self._send(proc, "0")
            time.sleep(0.3)
            self._send(proc, "0")

            stable = self._wait_stable(newest)
            if stable is None:
                raise BridgeError("DOWNLOAD_FAILED", f"File did not finish writing: {newest}")

            with Image.open(stable) as img:
                width, height = img.size

            target = dest_dir / f"{capture_id}.jpg"
            target.write_bytes(stable.read_bytes())
            return RawCapture(
                local_path=target,
                width=width,
                height=height,
                camera_file=stable.name,
                in_camera_stitch=True,
            )
        finally:
            self._terminate(proc)

    def _send(self, proc: subprocess.Popen, line: str) -> None:
        if proc.stdin is None or proc.poll() is not None:
            raise BridgeError("CAPTURE_FAILED", "Demo process ended early")
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    @staticmethod
    def _pump_stdout(proc: subprocess.Popen, log_lines: list[str]) -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            log_lines.append(line.rstrip("\n"))

    @staticmethod
    def _wait_for(log_lines: list[str], needles: tuple[str, ...], timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        seen = 0
        while time.monotonic() < deadline:
            chunk = "".join(log_lines[seen:])
            seen = len(log_lines)
            if any(n in chunk for n in needles):
                return True
            if any(n in "\n".join(log_lines) for n in needles):
                return True
            time.sleep(0.2)
        return any(n in "\n".join(log_lines) for n in needles)

    def _wait_new_file(self, before: dict[Path, float], timeout: float) -> Path | None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            after = self._snapshot()
            newcomers = [
                p for p, m in after.items() if p not in before or m > before[p] + 0.01
            ]
            if newcomers:
                return max(newcomers, key=lambda p: after[p])
            time.sleep(0.5)
        return None

    def _snapshot(self) -> dict[Path, float]:
        result: dict[Path, float] = {}
        for pattern in ("*.jpg", "*.JPG", "*.jpeg", "*.JPEG"):
            for path in self.download_dir.glob(pattern):
                try:
                    result[path] = path.stat().st_mtime
                except OSError:
                    continue
        return result

    @staticmethod
    def _wait_stable(path: Path, checks: int = 4, interval: float = 0.4) -> Path | None:
        last = -1
        stable = 0
        for _ in range(checks * 5):
            try:
                size = path.stat().st_size
            except OSError:
                return None
            if size > 0 and size == last:
                stable += 1
                if stable >= checks:
                    return path
            else:
                stable = 0
                last = size
            time.sleep(interval)
        return None

    @staticmethod
    def _terminate(proc: subprocess.Popen) -> None:
        if proc.poll() is not None:
            return
        try:
            if proc.stdin:
                proc.stdin.close()
        except OSError:
            pass
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    @staticmethod
    def _tail(log_lines: list[str], n: int = 30) -> str:
        return "\n".join(log_lines[-n:])
