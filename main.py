"""
TRANSLARA Root Entrypoint.
"""
from __future__ import annotations

import uvicorn
from backend.server import app, lifespan
from backend.config import settings

__all__ = ["app", "lifespan"]

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
