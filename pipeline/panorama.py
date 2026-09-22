"""Equirectangular panorama to overlapping perspective views.

Stage 1 owns the projection. Yaw 0 looks at the horizontal center of the ERP.
Pitch is positive upward. Frontend consumers only need yaw / pitch.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class ViewSpec:
    name: str
    yaw_deg: float
    pitch_deg: float
    fov_deg: float
    width: int
    height: int


def default_views(size: int = 768, fov_deg: float = 90.0) -> list[ViewSpec]:
    """Horizontal views every 45 degrees, plus one up and one down."""
    views = [
        ViewSpec(
            name=f"yaw{yaw:03d}_pitch000",
            yaw_deg=float(yaw),
            pitch_deg=0.0,
            fov_deg=fov_deg,
            width=size,
            height=size,
        )
        for yaw in range(0, 360, 45)
    ]
    views.append(
        ViewSpec("yaw000_pitch060", 0.0, 60.0, fov_deg, size, size)
    )
    views.append(
        ViewSpec("yaw000_pitch-060", 0.0, -60.0, fov_deg, size, size)
    )
    return views


def _rotation(yaw_deg: float, pitch_deg: float) -> np.ndarray:
    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    rot_yaw = np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]], dtype=np.float32)
    rot_pitch = np.array([[1.0, 0.0, 0.0], [0.0, cp, sp], [0.0, -sp, cp]], dtype=np.float32)
    return rot_yaw @ rot_pitch


def perspective_pixel_to_yaw_pitch(
    x: float,
    y: float,
    view: ViewSpec,
) -> tuple[float, float]:
    """Map one pixel in a perspective view back to ERP yaw / pitch degrees."""
    fov = math.radians(view.fov_deg)
    focal = (view.width / 2.0) / math.tan(fov / 2.0)
    cam = np.array(
        [
            (x - view.width / 2.0) / focal,
            -((y - view.height / 2.0) / focal),
            1.0,
        ],
        dtype=np.float32,
    )
    world = _rotation(view.yaw_deg, view.pitch_deg) @ cam
    world = world / np.linalg.norm(world)
    yaw = math.degrees(math.atan2(float(world[0]), float(world[2])))
    pitch = math.degrees(math.asin(float(np.clip(world[1], -1.0, 1.0))))
    return yaw, pitch


def bbox_to_yaw_pitch(bbox_xyxy: list[float], view: ViewSpec) -> dict:
    """Project a perspective box to a yaw/pitch center and angular extent."""
    x1, y1, x2, y2 = bbox_xyxy
    corners = [(x1, y1), (x2, y1), (x1, y2), (x2, y2), ((x1 + x2) / 2.0, (y1 + y2) / 2.0)]
    angles = [perspective_pixel_to_yaw_pitch(x, y, view) for x, y in corners]
    yaws = [a[0] for a in angles]
    pitches = [a[1] for a in angles]
    # Unwrap yaw samples around the box center so a box crossing ±180 stays continuous.
    center_yaw = angles[-1][0]
    unwrapped = []
    for yaw in yaws:
        delta = (yaw - center_yaw + 180.0) % 360.0 - 180.0
        unwrapped.append(center_yaw + delta)
    return {
        "yaw": center_yaw,
        "pitch": angles[-1][1],
        "yaw_min": min(unwrapped[:-1]),
        "yaw_max": max(unwrapped[:-1]),
        "pitch_min": min(pitches[:-1]),
        "pitch_max": max(pitches[:-1]),
    }


def render_view(erp: np.ndarray, view: ViewSpec) -> np.ndarray:
    height, width = erp.shape[:2]
    fov = math.radians(view.fov_deg)
    focal = (view.width / 2.0) / math.tan(fov / 2.0)
    xs = (np.arange(view.width, dtype=np.float32) - view.width / 2.0) / focal
    ys = -((np.arange(view.height, dtype=np.float32) - view.height / 2.0) / focal)
    grid_x, grid_y = np.meshgrid(xs, ys)
    cam = np.stack([grid_x, grid_y, np.ones_like(grid_x)], axis=-1)
    world = cam @ _rotation(view.yaw_deg, view.pitch_deg).T
    norm = np.linalg.norm(world, axis=-1, keepdims=True)
    world = world / np.clip(norm, 1e-6, None)
    lon = np.arctan2(world[..., 0], world[..., 2])
    lat = np.arcsin(np.clip(world[..., 1], -1.0, 1.0))
    map_x = (lon / (2.0 * math.pi) + 0.5) * width
    map_y = (0.5 - lat / math.pi) * height
    map_x = np.mod(map_x, width).astype(np.float32)
    map_y = np.clip(map_y, 0, height - 1).astype(np.float32)
    return cv2.remap(erp, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)


def assert_center_maps_home(width: int = 4096, height: int = 2048) -> None:
    """Yaw 0 / pitch 0 view center must land on the ERP center."""
    view = ViewSpec("check", 0.0, 0.0, 90.0, 64, 64)
    yaw, pitch = perspective_pixel_to_yaw_pitch(32, 32, view)
    if abs(yaw) > 0.2 or abs(pitch) > 0.2:
        raise RuntimeError(f"projection center drifted: yaw={yaw} pitch={pitch}")
    erp = np.zeros((height, width, 3), dtype=np.uint8)
    erp[height // 2, width // 2] = (255, 255, 255)
    rendered = render_view(erp, ViewSpec("check", 0.0, 0.0, 90.0, 128, 128))
    if int(rendered[64, 64, 0]) < 200:
        raise RuntimeError("perspective center did not sample the ERP center")
