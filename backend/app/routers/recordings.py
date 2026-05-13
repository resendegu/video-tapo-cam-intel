"""Recordings API router."""
import json
import os
from datetime import datetime
from typing import AsyncGenerator

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from app.config import settings
from app.db import get_db
from app.services import tapo_service

router = APIRouter(prefix="/api/recordings", tags=["recordings"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class DownloadRequest(BaseModel):
    start_time: int
    end_time: int
    date: str


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/dates")
async def get_recording_dates():
    """List all dates with SD card recordings."""
    try:
        dates = await tapo_service.list_recording_dates()
        return {"dates": dates}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Camera unreachable: {exc}")


@router.get("/{date}")
async def get_clips_for_date(date: str, db: aiosqlite.Connection = Depends(get_db)):
    """List all clips for a given date (YYYYMMDD). Caches metadata in SQLite."""
    try:
        clips = await tapo_service.list_clips(date)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Camera unreachable: {exc}")

    # Upsert clip metadata into DB
    now = datetime.utcnow().isoformat()
    for clip in clips:
        filename = clip["filename"]
        file_path = os.path.join(settings.RECORDINGS_DIR, filename)
        downloaded = 1 if os.path.exists(file_path) else 0
        file_size = os.path.getsize(file_path) if downloaded else None

        await db.execute(
            """
            INSERT INTO recordings (date, start_time, end_time, duration, clip_type,
                                    filename, file_size, downloaded, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(start_time) DO UPDATE SET
                downloaded = excluded.downloaded,
                file_size  = excluded.file_size
            """,
            (
                clip["date"],
                clip["start_time"],
                clip["end_time"],
                clip["duration"],
                clip["clip_type"],
                filename,
                file_size,
                downloaded,
                now,
            ),
        )
    await db.commit()

    # Return from DB (includes download status)
    async with db.execute(
        "SELECT * FROM recordings WHERE date = ? ORDER BY start_time DESC", (date,)
    ) as cur:
        rows = await cur.fetchall()
    return {"date": date, "clips": [dict(r) for r in rows]}


@router.post("/download")
async def download_clip(request: DownloadRequest):
    """
    Download a clip from the camera's SD card.
    Returns Server-Sent Events with download progress.
    """
    filename = f"{request.start_time}-{request.end_time}.mp4"
    file_path = os.path.join(settings.RECORDINGS_DIR, filename)

    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            async for status in tapo_service.download_clip(
                request.start_time, request.end_time, request.date
            ):
                yield f"data: {json.dumps(status)}\n\n"

        except Exception as exc:
            err_str = str(exc)
            # "no active connection" is a known pytapo cleanup error that fires
            # after convert.save() succeeds — the file is already on disk.
            # Treat it as non-fatal if the file was actually created.
            if "no active connection" not in err_str.lower() or not os.path.exists(file_path):
                yield f"data: {json.dumps({'error': err_str})}\n\n"
                return

        # Mark as downloaded in DB (runs on both clean finish and graceful cleanup error)
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else None
        if file_size:
            async with aiosqlite.connect(settings.DB_PATH) as db:
                await db.execute(
                    """
                    UPDATE recordings SET downloaded = 1, file_size = ?
                    WHERE start_time = ?
                    """,
                    (file_size, request.start_time),
                )
                await db.commit()
            yield f"data: {json.dumps({'done': True, 'filename': filename, 'size_bytes': file_size})}\n\n"
        else:
            yield f"data: {json.dumps({'error': 'File not found after download'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/files/list")
async def list_downloaded_files():
    """List all already-downloaded .mp4 files."""
    recordings_dir = settings.RECORDINGS_DIR
    if not os.path.exists(recordings_dir):
        return {"files": []}

    files = []
    for name in os.listdir(recordings_dir):
        if name.endswith(".mp4") and not name.endswith("_compressed.mp4"):
            path = os.path.join(recordings_dir, name)
            files.append(
                {
                    "filename": name,
                    "size_bytes": os.path.getsize(path),
                    "modified_at": datetime.fromtimestamp(os.path.getmtime(path)).isoformat(),
                }
            )
    files.sort(key=lambda f: f["modified_at"], reverse=True)
    return {"files": files}


@router.get("/files/{filename}")
async def serve_recording(filename: str):
    """Serve a downloaded recording for in-browser playback."""
    file_path = os.path.join(settings.RECORDINGS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Recording not found")
    return FileResponse(file_path, media_type="video/mp4")
