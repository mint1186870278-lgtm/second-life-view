from __future__ import annotations

import uvicorn

from capture_bridge.config import HOST, PORT


def main() -> None:
    uvicorn.run(
        "capture_bridge.app:app",
        host=HOST,
        port=PORT,
        reload=False,
    )


if __name__ == "__main__":
    main()
