"""
TRANSLARA Application Entrypoint (backend/app/main.py).

Allows running via:
    cd backend
    python -m uvicorn app.main:app --reload
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add project root and backend dir to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
backend_dir = Path(__file__).resolve().parent.parent

for d in [str(root_dir), str(backend_dir)]:
    if d not in sys.path:
        sys.path.insert(0, d)

try:
    from backend.server import app, lifespan
    from backend.config import settings
except ImportError:
    from server import app, lifespan
    from config import settings

__all__ = ["app", "lifespan"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
