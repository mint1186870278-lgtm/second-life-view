"""Load local secrets without printing them."""

from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(path: Path | None = None) -> None:
    # Avoid OpenMP abort when both torch and some conda libs ship libiomp5.
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    env_path = path or Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            continue
        # Always take DASHSCOPE_* from .env so key / host rotation works.
        if key.startswith("DASHSCOPE_") or key not in os.environ:
            os.environ[key] = value
