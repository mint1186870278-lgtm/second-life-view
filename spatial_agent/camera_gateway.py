"""Client for the Windows-local Insta360 camera gateway.

The vendor CameraSDK is a native library that must execute on the computer
with the USB/Wi-Fi camera connection.  This client deliberately talks only to
an HTTP gateway bound to the server's loopback interface (normally reached by
an SSH reverse tunnel); it never attempts to load Windows DLLs on Linux.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx

from spatial_agent.config import Settings


class CameraGatewayError(RuntimeError):
    """The Windows camera gateway could not complete a requested operation."""


class CameraGatewayNotConfigured(CameraGatewayError):
    """The server has no loopback gateway URL or shared bearer token."""


class WindowsCameraGateway:
    """Small, authenticated client for the Windows gateway REST contract."""

    def __init__(self, settings: Settings):
        self.base_url = settings.windows_camera_gateway_url.rstrip("/")
        self.token = settings.windows_camera_gateway_token
        self.timeout = settings.windows_camera_gateway_timeout

    @property
    def configured(self) -> bool:
        return bool(self.token and self._is_loopback_tunnel_url())

    def _is_loopback_tunnel_url(self) -> bool:
        parsed = urlsplit(self.base_url)
        try:
            port = parsed.port
        except ValueError:
            return False
        return bool(
            parsed.scheme == "http"
            and parsed.hostname in {"127.0.0.1", "::1"}
            and port
            and parsed.path in {"", "/"}
            and not parsed.username
            and not parsed.password
            and not parsed.query
            and not parsed.fragment
        )

    def _require_configuration(self) -> None:
        if not self.base_url or not self.token:
            raise CameraGatewayNotConfigured(
                "Windows camera gateway is not configured; set "
                "WINDOWS_CAMERA_GATEWAY_URL and WINDOWS_CAMERA_GATEWAY_TOKEN"
            )
        if not self._is_loopback_tunnel_url():
            raise CameraGatewayNotConfigured(
                "WINDOWS_CAMERA_GATEWAY_URL must be an http://127.0.0.1 or http://[::1] SSH tunnel URL"
            )

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def _url(self, path: str) -> str:
        self._require_configuration()
        if not path.startswith("/") or path.startswith("//"):
            raise CameraGatewayError("gateway endpoint must be an absolute local path")
        return f"{self.base_url}{path}"

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout, trust_env=False) as client:
                response = await client.request(
                    method,
                    self._url(path),
                    headers=self._headers(),
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise CameraGatewayError(f"Windows camera gateway is unreachable: {exc}") from exc

        if response.is_error:
            detail = response.text.strip().replace("\n", " ")[:500]
            raise CameraGatewayError(
                f"Windows camera gateway returned HTTP {response.status_code}: {detail or 'unknown error'}"
            )
        try:
            body = response.json()
        except ValueError as exc:
            raise CameraGatewayError("Windows camera gateway returned invalid JSON") from exc
        if not isinstance(body, dict):
            raise CameraGatewayError("Windows camera gateway returned an invalid response object")
        return body

    async def status(self) -> dict[str, Any]:
        return await self._request_json("GET", "/v1/status")

    async def list_files(self) -> dict[str, Any]:
        return await self._request_json("GET", "/v1/files")

    async def capture(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request_json("POST", "/v1/capture", payload=payload)

    async def download(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request_json("POST", "/v1/download", payload=payload)

    async def download_artifact_to(
        self,
        artifact_url: str,
        destination: Path,
    ) -> str | None:
        """Download one gateway-owned artifact without accepting arbitrary URLs."""
        parsed = urlsplit(artifact_url)
        if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
            raise CameraGatewayError("gateway artifact URL must be a plain local path")
        path_parts = parsed.path.split("/")
        if (
            len(path_parts) != 4
            or path_parts[:3] != ["", "v1", "artifacts"]
            or not path_parts[3]
            or ".." in path_parts
        ):
            raise CameraGatewayError("gateway returned an invalid artifact path")

        try:
            async with httpx.AsyncClient(timeout=self.timeout, trust_env=False) as client:
                async with client.stream(
                    "GET",
                    self._url(parsed.path),
                    headers=self._headers(),
                ) as response:
                    if response.is_error:
                        detail = (await response.aread()).decode("utf-8", errors="replace").strip()[:500]
                        raise CameraGatewayError(
                            f"Windows camera artifact download failed with HTTP {response.status_code}: "
                            f"{detail or 'unknown error'}"
                        )
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        with destination.open("wb") as stream:
                            async for chunk in response.aiter_bytes():
                                stream.write(chunk)
                    except Exception:
                        destination.unlink(missing_ok=True)
                        raise
                    return response.headers.get("content-type")
        except CameraGatewayError:
            raise
        except httpx.HTTPError as exc:
            raise CameraGatewayError(f"Windows camera artifact download failed: {exc}") from exc
