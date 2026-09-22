"""Aliyun OSS asset gateway.

The camera is connected to Windows, while models run on Linux.  Uploading a
completed file to OSS gives both sides a durable hand-off and gives providers
such as Lux3D and Tripo a temporary HTTP(S) URL.  The bucket can remain
private: URLs returned here are signed and expire automatically.
"""
from __future__ import annotations

import mimetypes
import os
import re
import tempfile
from pathlib import Path
from typing import Any, BinaryIO
from uuid import uuid4

from spatial_agent.config import Settings


class OSSClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._bucket: Any = None

    @property
    def enabled(self) -> bool:
        return bool(
            self.settings.oss_access_key_id
            and self.settings.oss_access_key_secret
            and self.settings.oss_bucket
            and self.settings.oss_endpoint
        )

    @property
    def endpoint(self) -> str:
        endpoint = self.settings.oss_endpoint.strip()
        if not endpoint:
            return ""
        return endpoint if endpoint.startswith("http") else f"https://{endpoint}"

    def _get_bucket(self) -> Any:
        if not self.enabled:
            raise RuntimeError(
                "OSS is not configured; set OSS_ACCESS_KEY_ID, "
                "OSS_ACCESS_KEY_SECRET, OSS_BUCKET and OSS_ENDPOINT"
            )
        if self._bucket is None:
            try:
                import oss2
            except ImportError as exc:  # pragma: no cover - environment error
                raise RuntimeError("Install oss2 to enable Aliyun OSS uploads") from exc
            auth = oss2.Auth(
                self.settings.oss_access_key_id,
                self.settings.oss_access_key_secret,
            )
            self._bucket = oss2.Bucket(auth, self.endpoint, self.settings.oss_bucket)
        return self._bucket

    @staticmethod
    def _safe_name(name: str) -> str:
        # Preserve the extension but prevent path traversal and control chars.
        clean = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(name).name).strip("._")
        return clean or "asset.bin"

    def key_for(self, filename: str, *, session_id: str | None = None) -> str:
        prefix = self.settings.oss_prefix.strip("/") or "second-life-view"
        scope = re.sub(r"[^A-Za-z0-9._-]+", "_", session_id or "ingest")
        return f"{prefix}/{scope}/{uuid4().hex[:12]}-{self._safe_name(filename)}"

    def _signed_url(self, key: str, *, expires: int | None = None) -> str:
        bucket = self._get_bucket()
        ttl = int(expires or self.settings.oss_signed_url_ttl)
        return bucket.sign_url("GET", key, ttl)

    def upload_stream(
        self,
        stream: BinaryIO,
        filename: str,
        *,
        session_id: str | None = None,
        content_type: str | None = None,
    ) -> dict[str, Any]:
        """Upload a seekable or non-seekable stream and return signed access."""
        bucket = self._get_bucket()
        key = self.key_for(filename, session_id=session_id)
        headers: dict[str, str] = {}
        guessed = content_type or mimetypes.guess_type(filename)[0]
        if guessed:
            headers["Content-Type"] = guessed
        result = bucket.put_object(key, stream, headers=headers or None)
        return {
            "bucket": self.settings.oss_bucket,
            "endpoint": self.endpoint,
            "key": key,
            "oss_uri": f"oss://{self.settings.oss_bucket}/{key}",
            "url": self._signed_url(key),
            "expires_in": int(self.settings.oss_signed_url_ttl),
            "etag": getattr(result, "etag", None),
            "content_type": guessed,
        }

    def upload_file(
        self,
        path: str | os.PathLike[str],
        *,
        session_id: str | None = None,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> dict[str, Any]:
        source = Path(path)
        if not source.is_file():
            raise FileNotFoundError(source)
        with source.open("rb") as stream:
            return self.upload_stream(
                stream,
                filename or source.name,
                session_id=session_id,
                content_type=content_type,
            )

    def signed_url(self, key: str, *, expires: int | None = None) -> str:
        # Only accept an object key; callers cannot turn this endpoint into an
        # arbitrary URL signer for another bucket.
        normalized = key.lstrip("/")
        if normalized.startswith(f"{self.settings.oss_bucket}/"):
            normalized = normalized.split("/", 1)[1]
        return self._signed_url(normalized, expires=expires)


def save_upload_to_temp(upload: Any, max_bytes: int) -> tuple[str, int]:
    """Stream a FastAPI UploadFile to a temporary file with a hard size cap."""
    suffix = Path(getattr(upload, "filename", "asset.bin") or "asset.bin").suffix
    total = 0
    fd, path = tempfile.mkstemp(prefix="spatial-upload-", suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as out:
            while True:
                chunk = upload.file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError(f"upload exceeds {max_bytes // (1024 * 1024)} MiB limit")
                out.write(chunk)
        return path, total
    except Exception:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
        raise
