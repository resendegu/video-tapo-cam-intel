"""Analysis API router — GCP Video Intelligence and Cloud Vision."""
import os

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.db import get_db
from app.services import analysis_service, quota_service

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


class AnalyzeVideoRequest(BaseModel):
    recording_id: int
    filename: str


class AnalyzeFrameRequest(BaseModel):
    recording_id: int
    filename: str


@router.post("/video")
async def trigger_video_analysis(
    request: AnalyzeVideoRequest, db: aiosqlite.Connection = Depends(get_db)
):
    """Analyze a downloaded recording with Video Intelligence API."""
    video_path = os.path.join(settings.RECORDINGS_DIR, request.filename)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Recording file not found. Download it first.")

    # Get duration from DB
    async with db.execute(
        "SELECT duration FROM recordings WHERE id = ?", (request.recording_id,)
    ) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Recording not found in database")

    duration = row["duration"]

    if not await quota_service.can_analyze_video(db, duration):
        quota = await quota_service.get_quota_status(db)
        raise HTTPException(
            status_code=429,
            detail=f"Monthly Video Intelligence quota would be exceeded. "
                   f"Remaining: {quota['video_intelligence']['remaining']} minutes",
        )

    try:
        result = await analysis_service.analyze_video(
            request.recording_id, video_path, duration, db
        )
        return {"status": "completed", "result": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/frame")
async def trigger_frame_analysis(
    request: AnalyzeFrameRequest, db: aiosqlite.Connection = Depends(get_db)
):
    """Extract a keyframe and analyze it with Cloud Vision API."""
    video_path = os.path.join(settings.RECORDINGS_DIR, request.filename)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Recording file not found. Download it first.")

    if not await quota_service.can_analyze_image(db):
        quota = await quota_service.get_quota_status(db)
        raise HTTPException(
            status_code=429,
            detail=f"Monthly Vision API quota would be exceeded. "
                   f"Remaining: {quota['vision']['remaining']} units",
        )

    try:
        result = await analysis_service.analyze_frame(
            request.recording_id, video_path, db
        )
        return {"status": "completed", "result": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{recording_id}")
async def get_analysis(recording_id: int, db: aiosqlite.Connection = Depends(get_db)):
    """Retrieve stored analysis results for a recording."""
    import json

    async with db.execute(
        "SELECT * FROM analyses WHERE recording_id = ? ORDER BY created_at DESC",
        (recording_id,),
    ) as cur:
        rows = await cur.fetchall()

    results = []
    for row in rows:
        entry = dict(row)
        if entry.get("result_json"):
            entry["result"] = json.loads(entry["result_json"])
            del entry["result_json"]
        results.append(entry)

    return {"recording_id": recording_id, "analyses": results}


@router.get("")
async def list_analyses(db: aiosqlite.Connection = Depends(get_db)):
    """List all completed analyses with summary information."""
    import json

    async with db.execute(
        """
        SELECT a.id, a.recording_id, a.service, a.status, a.units_used,
               a.created_at, a.completed_at, r.filename, r.date, r.start_time
        FROM analyses a
        JOIN recordings r ON a.recording_id = r.id
        ORDER BY a.created_at DESC
        LIMIT 100
        """
    ) as cur:
        rows = await cur.fetchall()

    return {"analyses": [dict(r) for r in rows]}
