"""FastAPI application entry point."""
# Must be applied before uvicorn/asyncio starts to allow pytapo's internal
# asyncio.run_until_complete() to work inside FastAPI's already-running loop.
import nest_asyncio
nest_asyncio.apply()

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db import init_db
from app.routers import recordings, analysis, camera, quota


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure all data directories exist
    for directory in [settings.RECORDINGS_DIR, settings.FRAMES_DIR,
                      os.path.dirname(settings.DB_PATH)]:
        os.makedirs(directory, exist_ok=True)

    # Initialize SQLite schema
    await init_db()
    yield


app = FastAPI(
    title="Tapo Camera Intelligence",
    description="List, download, and analyze Tapo C500 recordings with GCP Vision APIs",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(recordings.router)
app.include_router(analysis.router)
app.include_router(camera.router)
app.include_router(quota.router)


@app.get("/api/frames/{filename}")
async def serve_frame(filename: str):
    """Serve an extracted keyframe image for the frontend."""
    path = os.path.join(settings.FRAMES_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Frame not found")
    return FileResponse(path, media_type="image/jpeg")


# Serve static frontend — must be mounted AFTER all API routes
static_dir = "/app/static"
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")
