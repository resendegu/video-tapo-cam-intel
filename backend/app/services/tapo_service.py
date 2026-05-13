"""Tapo camera service — listing and downloading SD card recordings.

Architecture note
-----------------
pytapo's AsyncHandler calls asyncio.run_until_complete() internally (via
python-kasa). This normally conflicts with FastAPI's already-running uvloop.
We apply nest_asyncio in main.py (before the loop starts) which patches asyncio
to allow nested run_until_complete calls — solving this cleanly.

All blocking pytapo calls (Tapo(), getRecordings*, getTimeCorrection) are
dispatched via run_in_executor so they don't block FastAPI's event loop.

The Downloader.download() is a native async generator and runs directly in
FastAPI's event loop once nest_asyncio is applied.
"""
import asyncio
import os
from typing import AsyncGenerator

from pytapo import Tapo
from pytapo.media_stream.downloader import Downloader

from app.config import settings


def _make_tapo() -> Tapo:
    """Blocking constructor — run via executor, never in the event loop thread."""
    return Tapo(
        settings.TAPO_IP,
        settings.TAPO_EMAIL,
        settings.TAPO_CLOUD_PASS,
        cloudPassword=settings.TAPO_CLOUD_PASS,
    )


async def _in_executor(fn, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, fn, *args)


# ── Public API ────────────────────────────────────────────────────────────────

async def get_camera_info() -> dict:
    tapo = await _in_executor(_make_tapo)
    info = await _in_executor(tapo.getBasicInfo)
    return info.get("device_info", {}).get("basic_info", {})


async def list_recording_dates() -> list[str]:
    tapo = await _in_executor(_make_tapo)
    raw = await _in_executor(tapo.getRecordingsList)
    dates: list[str] = []
    for item in raw:
        for key in item:
            entry = item[key]
            if "date" in entry:
                dates.append(entry["date"])
    return sorted(set(dates), reverse=True)


async def list_clips(date: str) -> list[dict]:
    tapo = await _in_executor(_make_tapo)
    raw = await _in_executor(tapo.getRecordings, date)
    clips: list[dict] = []
    for item in raw:
        for key in item:
            entry = item[key]
            start = entry.get("startTime", 0)
            end = entry.get("endTime", 0)
            vtype_raw = entry.get("vedio_type", "0")  # typo exists in pytapo itself
            clip_type = "motion" if str(vtype_raw) in ("1", "2") else "continuous"
            clips.append({
                "start_time": start,
                "end_time": end,
                "duration": end - start,
                "clip_type": clip_type,
                "date": date,
                "filename": f"{start}-{end}.mp4",
            })
    clips.sort(key=lambda c: c["start_time"], reverse=True)
    return clips


async def download_clip(
    start_time: int,
    end_time: int,
    date: str,
) -> AsyncGenerator[dict, None]:
    """
    Download a clip from the camera SD card, yielding progress dicts.

    With nest_asyncio applied, pytapo's Downloader (an async generator) runs
    directly in FastAPI's event loop. Blocking calls (Tapo(), getTimeCorrection)
    are still dispatched via run_in_executor to avoid blocking requests.
    """
    tapo = await _in_executor(_make_tapo)
    time_correction = await _in_executor(tapo.getTimeCorrection)

    output_dir = settings.RECORDINGS_DIR
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{start_time}-{end_time}.mp4"

    downloader = Downloader(
        tapo,
        start_time,
        end_time,
        time_correction,
        output_dir,
        overwriteFiles=True,
        window_size=settings.DOWNLOAD_WINDOW_SIZE,
        fileName=filename,
    )

    async for status in downloader.download():
        yield status
