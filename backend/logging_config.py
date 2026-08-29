"""
Structured logging configuration for TRANSLARA with Windows Unicode UTF-8 safety.
"""
from __future__ import annotations

import io
import sys
from loguru import logger
from backend.config import settings

# Remove default handler
logger.remove()

# Configure formatted stdout logging with UTF-8 safety
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

# Wrap stdout safely if on Windows
wrapped_sink = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace") if hasattr(sys.stdout, "buffer") else sys.stdout

logger.add(
    wrapped_sink,
    format=LOG_FORMAT,
    level=settings.log_level.upper(),
    colorize=False if sys.platform == "win32" else True,
)


def log_stage_latency(session_id: str, stage: str, latency_ms: float, extra: str = "") -> None:
    """Standardized stage latency logger for real-time observability."""
    logger.info(
        f"[LATENCY] session={session_id} stage={stage} latency={latency_ms:.1f}ms {extra}".strip()
    )


def log_pipeline_summary(
    session_id: str,
    source_lang: str,
    target_lang: str,
    total_ms: float,
    offline: bool = False,
    entities_count: int = 0,
) -> None:
    """Standardized pipeline completion summary."""
    status_str = "OFFLINE_CACHE" if offline else "LIVE_PIPELINE"
    logger.info(
        f"[PIPELINE] session={session_id} {source_lang}->{target_lang} total={total_ms:.1f}ms "
        f"mode={status_str} entities_locked={entities_count}"
    )
