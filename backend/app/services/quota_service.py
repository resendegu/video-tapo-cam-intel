"""Quota tracking service — prevents accidental overuse of GCP free tier."""
import json
from datetime import datetime

import aiosqlite

from app.config import settings

SERVICE_VIDEO = "video_intelligence"
SERVICE_VISION = "vision"


def _current_month() -> str:
    return datetime.utcnow().strftime("%Y-%m")


async def _get_usage(db: aiosqlite.Connection, service: str) -> float:
    month = _current_month()
    async with db.execute(
        "SELECT units_used FROM quota_usage WHERE service = ? AND year_month = ?",
        (service, month),
    ) as cur:
        row = await cur.fetchone()
    return float(row["units_used"]) if row else 0.0


async def get_quota_status(db: aiosqlite.Connection) -> dict:
    """Return current month's usage and limits for both services."""
    video_used = await _get_usage(db, SERVICE_VIDEO)
    vision_used = await _get_usage(db, SERVICE_VISION)
    return {
        "month": _current_month(),
        "video_intelligence": {
            "service": SERVICE_VIDEO,
            "used": round(video_used, 2),
            "limit": settings.VIDEO_INTEL_MONTHLY_LIMIT,
            "remaining": max(0, settings.VIDEO_INTEL_MONTHLY_LIMIT - video_used),
            "unit": "minutes",
        },
        "vision": {
            "service": SERVICE_VISION,
            "used": int(vision_used),
            "limit": settings.VISION_MONTHLY_LIMIT,
            "remaining": max(0, settings.VISION_MONTHLY_LIMIT - int(vision_used)),
            "unit": "units",
        },
    }


async def can_analyze_video(db: aiosqlite.Connection, duration_seconds: int) -> bool:
    used = await _get_usage(db, SERVICE_VIDEO)
    needed = duration_seconds / 60.0
    return (used + needed) <= settings.VIDEO_INTEL_MONTHLY_LIMIT


async def can_analyze_image(db: aiosqlite.Connection) -> bool:
    used = await _get_usage(db, SERVICE_VISION)
    return (used + 1) <= settings.VISION_MONTHLY_LIMIT


async def record_usage(db: aiosqlite.Connection, service: str, units: float) -> None:
    month = _current_month()
    now = datetime.utcnow().isoformat()
    await db.execute(
        """
        INSERT INTO quota_usage (service, year_month, units_used, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(service, year_month)
        DO UPDATE SET
            units_used = units_used + excluded.units_used,
            updated_at = excluded.updated_at
        """,
        (service, month, units, now),
    )
    await db.commit()
