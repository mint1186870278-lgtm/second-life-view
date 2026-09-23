"""Durable, content-addressed artifacts for the picture-demo fast path.

The sample pictures are deliberately useful for a live end-to-end demo, but
calling every remote provider on every click makes that demo unnecessarily
slow.  This store keeps the *result* of a provider call alongside an input
fingerprint.  A changed source picture, prompt or object definition naturally
misses the cache and is handled by the normal online flow.

Generated media stays in ``run_artifacts/demo_precompute`` by default.  That
directory is suitable for a persistent demo volume and is intentionally not a
Git asset bundle; provider keys, signed URLs and large models must not be
committed with source code.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "run_artifacts" / "demo_precompute"
SCHEMA_VERSION = 1


def stable_digest(value: Any) -> str:
    """Hash JSON-compatible input deterministically without exposing it."""
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(serialized.encode("utf-8")).hexdigest()


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DemoArtifactStore:
    """Small manifest + local-media store used by demo endpoints and warmup."""

    def __init__(self, root: Path | str | None = None):
        configured = os.environ.get("DEMO_PRECOMPUTE_DIR", "").strip()
        self.root = Path(root or configured or DEFAULT_ROOT).resolve()
        self.manifest_path = self.root / "manifest.json"
        self.root.mkdir(parents=True, exist_ok=True)

    def _read(self) -> dict[str, Any]:
        if not self.manifest_path.exists():
            return self._empty_manifest()
        try:
            payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return self._empty_manifest()
        if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
            return self._empty_manifest()
        for section in ("scenes", "components", "worlds", "analyses"):
            payload.setdefault(section, {})
        return payload

    @staticmethod
    def _empty_manifest() -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "created_at": utcnow_iso(),
            "scenes": {},
            "components": {},
            "worlds": {},
            "analyses": {},
        }

    def _write(self, payload: dict[str, Any]) -> None:
        payload["updated_at"] = utcnow_iso()
        temporary = self.manifest_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self.manifest_path)

    @staticmethod
    def _safe_token(value: str) -> str:
        return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._") or "artifact"

    def _resolve_asset(self, relative: str) -> Path | None:
        candidate = (self.root / relative).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError:
            return None
        return candidate

    def _write_bytes(self, section: str, key: str, content: bytes, suffix: str) -> str:
        filename = f"{self._safe_token(key)}-{stable_digest(key)[:12]}{suffix}"
        relative = str(Path(section) / filename)
        destination = self._resolve_asset(relative)
        assert destination is not None
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_bytes(content)
        temporary.replace(destination)
        return relative

    def _read_bytes(self, relative: object) -> bytes | None:
        if not isinstance(relative, str):
            return None
        path = self._resolve_asset(relative)
        if path is None or not path.is_file():
            return None
        try:
            return path.read_bytes()
        except OSError:
            return None

    def cached_scene_annotation(self, scene_id: str, fingerprint: str) -> bytes | None:
        record = self._read()["scenes"].get(scene_id, {})
        if record.get("fingerprint") != fingerprint:
            return None
        return self._read_bytes(record.get("annotation_file"))

    def save_scene_annotation(
        self,
        scene_id: str,
        fingerprint: str,
        annotation: bytes,
        *,
        yolo: dict[str, Any],
    ) -> None:
        payload = self._read()
        record = dict(payload["scenes"].get(scene_id, {}))
        record.update({
            "fingerprint": fingerprint,
            "annotation_file": self._write_bytes("annotations", scene_id, annotation, ".jpg"),
            "yolo": yolo,
            "updated_at": utcnow_iso(),
        })
        payload["scenes"][scene_id] = record
        self._write(payload)

    def cached_crop(self, group_id: str, fingerprint: str) -> bytes | None:
        record = self._read()["components"].get(group_id, {})
        if record.get("fingerprint") != fingerprint:
            return None
        return self._read_bytes(record.get("crop_file"))

    def crop_path(self, group_id: str, fingerprint: str) -> Path | None:
        record = self._read()["components"].get(group_id, {})
        if record.get("fingerprint") != fingerprint:
            return None
        path = self._resolve_asset(str(record.get("crop_file") or ""))
        return path if path and path.is_file() else None

    def save_crop(self, group_id: str, fingerprint: str, crop: bytes) -> None:
        payload = self._read()
        record = dict(payload["components"].get(group_id, {}))
        record.update({
            "fingerprint": fingerprint,
            "crop_file": self._write_bytes("crops", group_id, crop, ".jpg"),
            "updated_at": utcnow_iso(),
        })
        payload["components"][group_id] = record
        self._write(payload)

    def cached_advice(self, group_id: str, fingerprint: str, advice_key: str) -> dict[str, Any] | None:
        record = self._read()["components"].get(group_id, {})
        if record.get("fingerprint") != fingerprint:
            return None
        advice = (record.get("advice") or {}).get(advice_key)
        return dict(advice) if isinstance(advice, dict) else None

    def save_advice(self, group_id: str, fingerprint: str, advice_key: str, advice: dict[str, Any]) -> None:
        payload = self._read()
        record = dict(payload["components"].get(group_id, {}))
        record["fingerprint"] = fingerprint
        saved = dict(record.get("advice") or {})
        saved[advice_key] = {**advice, "cached_at": utcnow_iso()}
        record["advice"] = saved
        record["updated_at"] = utcnow_iso()
        payload["components"][group_id] = record
        self._write(payload)

    def cached_preview(self, group_id: str, fingerprint: str, preview_key: str) -> dict[str, Any] | None:
        record = self._read()["components"].get(group_id, {})
        if record.get("fingerprint") != fingerprint:
            return None
        preview = (record.get("previews") or {}).get(preview_key)
        if not isinstance(preview, dict) or self._read_bytes(preview.get("image_file")) is None:
            return None
        return dict(preview)

    def latest_preview(self, group_id: str, fingerprint: str) -> dict[str, Any] | None:
        record = self._read()["components"].get(group_id, {})
        if record.get("fingerprint") != fingerprint:
            return None
        preview_key = record.get("latest_preview_key")
        return self.cached_preview(group_id, fingerprint, str(preview_key)) if preview_key else None

    def save_preview(
        self,
        group_id: str,
        fingerprint: str,
        preview_key: str,
        image: bytes,
        *,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        payload = self._read()
        record = dict(payload["components"].get(group_id, {}))
        record["fingerprint"] = fingerprint
        previews = dict(record.get("previews") or {})
        saved = {
            **metadata,
            "image_file": self._write_bytes("previews", f"{group_id}-{preview_key[:12]}", image, ".jpg"),
            "cached_at": utcnow_iso(),
        }
        previews[preview_key] = saved
        record["previews"] = previews
        record["latest_preview_key"] = preview_key
        record["updated_at"] = utcnow_iso()
        payload["components"][group_id] = record
        self._write(payload)
        return saved

    def cached_model(self, group_id: str, fingerprint: str, model_key: str) -> dict[str, Any] | None:
        record = self._read()["components"].get(group_id, {})
        if record.get("fingerprint") != fingerprint:
            return None
        model = (record.get("models") or {}).get(model_key)
        return dict(model) if isinstance(model, dict) else None

    def latest_model(self, group_id: str, fingerprint: str) -> dict[str, Any] | None:
        record = self._read()["components"].get(group_id, {})
        if record.get("fingerprint") != fingerprint:
            return None
        key = record.get("latest_model_key")
        return self.cached_model(group_id, fingerprint, str(key)) if key else None

    def save_model(self, group_id: str, fingerprint: str, model_key: str, model: dict[str, Any]) -> None:
        payload = self._read()
        record = dict(payload["components"].get(group_id, {}))
        record["fingerprint"] = fingerprint
        models = dict(record.get("models") or {})
        models[model_key] = {**model, "cached_at": utcnow_iso()}
        record["models"] = models
        record["latest_model_key"] = model_key
        record["updated_at"] = utcnow_iso()
        payload["components"][group_id] = record
        self._write(payload)

    def preview_bytes(self, preview: dict[str, Any]) -> bytes | None:
        return self._read_bytes(preview.get("image_file"))

    def preview_relative_path(self, preview: dict[str, Any]) -> str | None:
        value = preview.get("image_file")
        return value if isinstance(value, str) and self._resolve_asset(value) else None

    def asset_path(self, relative: str) -> Path | None:
        """Return a validated local artifact path for FastAPI or a provider."""
        return self._resolve_asset(relative)

    def cached_world(self, scene_id: str, fingerprint: str, world_key: str) -> dict[str, Any] | None:
        record = self._read()["worlds"].get(scene_id, {})
        if record.get("fingerprint") != fingerprint:
            return None
        world = (record.get("variants") or {}).get(world_key)
        return dict(world) if isinstance(world, dict) else None

    def latest_world(self, scene_id: str, fingerprint: str) -> dict[str, Any] | None:
        record = self._read()["worlds"].get(scene_id, {})
        if record.get("fingerprint") != fingerprint:
            return None
        key = record.get("latest_key")
        return self.cached_world(scene_id, fingerprint, str(key)) if key else None

    def save_world(self, scene_id: str, fingerprint: str, world_key: str, world: dict[str, Any]) -> None:
        payload = self._read()
        record = dict(payload["worlds"].get(scene_id, {}))
        record["fingerprint"] = fingerprint
        variants = dict(record.get("variants") or {})
        variants[world_key] = {**world, "cached_at": utcnow_iso()}
        record["variants"] = variants
        record["latest_key"] = world_key
        record["updated_at"] = utcnow_iso()
        payload["worlds"][scene_id] = record
        self._write(payload)

    def cached_analysis(self, key: str) -> dict[str, Any] | None:
        record = self._read()["analyses"].get(key)
        return dict(record) if isinstance(record, dict) else None

    def save_analysis(self, key: str, *, fingerprint: str, state: dict[str, Any], response: dict[str, Any]) -> None:
        payload = self._read()
        payload["analyses"][key] = {
            "fingerprint": fingerprint,
            "state": state,
            "response": response,
            "cached_at": utcnow_iso(),
        }
        self._write(payload)

    def status(self) -> dict[str, int | str]:
        payload = self._read()
        components = payload["components"]
        return {
            "root": str(self.root),
            "scenes": len(payload["scenes"]),
            "crops": sum(1 for item in components.values() if isinstance(item, dict) and item.get("crop_file")),
            "advice": sum(len((item.get("advice") or {})) for item in components.values() if isinstance(item, dict)),
            "previews": sum(len((item.get("previews") or {})) for item in components.values() if isinstance(item, dict)),
            "models": sum(len((item.get("models") or {})) for item in components.values() if isinstance(item, dict)),
            "worlds": sum(len((item.get("variants") or {})) for item in payload["worlds"].values() if isinstance(item, dict)),
            "analyses": len(payload["analyses"]),
        }
