"""GCP analysis service — Video Intelligence API and Cloud Vision API."""
import json
import os
import subprocess
from datetime import datetime

import aiosqlite
from google.cloud import videointelligence, vision

from app.config import settings
from app.services import quota_service


def _compress_video_if_needed(src_path: str) -> str:
    """
    If video exceeds the 20 MB limit for Video Intelligence API inline content,
    re-encode at 720p/lower bitrate using FFmpeg and return path to temp file.
    Returns src_path unchanged if within limits.
    """
    if os.path.getsize(src_path) <= settings.VIDEO_SIZE_LIMIT_BYTES:
        return src_path

    compressed_path = src_path.replace(".mp4", "_compressed.mp4")
    if os.path.exists(compressed_path):
        return compressed_path

    cmd = [
        "ffmpeg", "-y",
        "-i", src_path,
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease",
        "-c:v", "libx264",
        "-crf", "28",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "96k",
        compressed_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return compressed_path


def _extract_keyframe(video_path: str) -> str | None:
    """Extract a single frame from the middle of the video using FFmpeg."""
    frame_dir = settings.FRAMES_DIR
    os.makedirs(frame_dir, exist_ok=True)

    basename = os.path.splitext(os.path.basename(video_path))[0]
    frame_path = os.path.join(frame_dir, f"{basename}.jpg")

    if os.path.exists(frame_path):
        return frame_path

    # Probe duration
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        video_path,
    ]
    try:
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        duration = float(json.loads(result.stdout)["format"]["duration"])
        midpoint = duration / 2
    except Exception:
        midpoint = 5  # fallback

    extract_cmd = [
        "ffmpeg", "-y",
        "-ss", str(midpoint),
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "2",
        frame_path,
    ]
    try:
        subprocess.run(extract_cmd, check=True, capture_output=True)
        return frame_path
    except subprocess.CalledProcessError:
        return None


async def analyze_video(
    recording_id: int,
    video_path: str,
    duration_seconds: int,
    db: aiosqlite.Connection,
) -> dict:
    """
    Submit video to Video Intelligence API for label detection,
    shot change detection, and object tracking.
    Returns the parsed analysis result dict.
    """
    if not await quota_service.can_analyze_video(db, duration_seconds):
        raise ValueError("Monthly Video Intelligence quota exceeded")

    # Create a pending analysis record
    now = datetime.utcnow().isoformat()
    async with db.execute(
        """
        INSERT INTO analyses (recording_id, service, status, created_at)
        VALUES (?, ?, 'pending', ?)
        """,
        (recording_id, quota_service.SERVICE_VIDEO, now),
    ) as cur:
        analysis_id = cur.lastrowid
    await db.commit()

    try:
        target_path = _compress_video_if_needed(video_path)

        with open(target_path, "rb") as f:
            input_content = f.read()

        client = videointelligence.VideoIntelligenceServiceClient()
        features = [
            videointelligence.Feature.LABEL_DETECTION,
            videointelligence.Feature.SHOT_CHANGE_DETECTION,
            videointelligence.Feature.OBJECT_TRACKING,
        ]
        operation = client.annotate_video(
            request={"features": features, "input_content": input_content}
        )
        raw_result = operation.result(timeout=600)

        result = _parse_video_result(raw_result)
        units_used = duration_seconds / 60.0

        completed_at = datetime.utcnow().isoformat()
        await db.execute(
            """
            UPDATE analyses SET
                status = 'completed',
                result_json = ?,
                units_used = ?,
                completed_at = ?
            WHERE id = ?
            """,
            (json.dumps(result), units_used, completed_at, analysis_id),
        )
        await quota_service.record_usage(db, quota_service.SERVICE_VIDEO, units_used)
        await db.commit()
        return result

    except Exception as exc:
        await db.execute(
            "UPDATE analyses SET status = 'failed', error_message = ? WHERE id = ?",
            (str(exc), analysis_id),
        )
        await db.commit()
        raise


def _parse_video_result(result) -> dict:
    """Convert Video Intelligence API result to a serializable dict."""
    output: dict = {"labels": [], "shots": [], "objects": []}

    for annotation_result in result.annotation_results:
        # Segment labels
        for label in annotation_result.segment_label_annotations:
            entry = {"description": label.entity.description, "segments": []}
            for seg in label.segments:
                entry["segments"].append(
                    {
                        "start_s": seg.segment.start_time_offset.total_seconds(),
                        "end_s": seg.segment.end_time_offset.total_seconds(),
                        "confidence": round(seg.confidence, 3),
                    }
                )
            output["labels"].append(entry)

        # Shot changes
        for shot in annotation_result.shot_annotations:
            output["shots"].append(
                {
                    "start_s": shot.start_time_offset.total_seconds(),
                    "end_s": shot.end_time_offset.total_seconds(),
                }
            )

        # Object tracking
        for obj in annotation_result.object_annotations:
            output["objects"].append(
                {
                    "description": obj.entity.description,
                    "confidence": round(obj.confidence, 3),
                    "frames": len(obj.frames),
                }
            )

    return output


async def analyze_frame(
    recording_id: int,
    video_path: str,
    db: aiosqlite.Connection,
) -> dict:
    """
    Extract a keyframe and analyze it with Cloud Vision API (label detection).
    """
    if not await quota_service.can_analyze_image(db):
        raise ValueError("Monthly Vision API quota exceeded")

    frame_path = _extract_keyframe(video_path)
    if not frame_path:
        raise RuntimeError("Failed to extract keyframe from video")

    now = datetime.utcnow().isoformat()
    async with db.execute(
        """
        INSERT INTO analyses (recording_id, service, status, created_at)
        VALUES (?, ?, 'pending', ?)
        """,
        (recording_id, quota_service.SERVICE_VISION, now),
    ) as cur:
        analysis_id = cur.lastrowid
    await db.commit()

    try:
        client = vision.ImageAnnotatorClient()

        with open(frame_path, "rb") as f:
            content = f.read()

        image = vision.Image(content=content)
        response = client.annotate_image(
            {
                "image": image,
                "features": [
                    {"type_": vision.Feature.Type.LABEL_DETECTION, "max_results": 20},
                    {"type_": vision.Feature.Type.OBJECT_LOCALIZATION, "max_results": 10},
                ],
            }
        )

        result = {
            "labels": [
                {
                    "description": l.description,
                    "score": round(l.score, 3),
                    "topicality": round(l.topicality, 3),
                }
                for l in response.label_annotations
            ],
            "objects": [
                {
                    "name": obj.name,
                    "score": round(obj.score, 3),
                    "bounding_box": {
                        "left": round(obj.bounding_poly.normalized_vertices[0].x, 4),
                        "top": round(obj.bounding_poly.normalized_vertices[0].y, 4),
                        "right": round(obj.bounding_poly.normalized_vertices[2].x, 4),
                        "bottom": round(obj.bounding_poly.normalized_vertices[2].y, 4),
                    },
                }
                for obj in response.localized_object_annotations
            ],
            "frame_path": os.path.basename(frame_path),
        }

        completed_at = datetime.utcnow().isoformat()
        await db.execute(
            """
            UPDATE analyses SET
                status = 'completed',
                result_json = ?,
                units_used = 1,
                completed_at = ?
            WHERE id = ?
            """,
            (json.dumps(result), completed_at, analysis_id),
        )
        await quota_service.record_usage(db, quota_service.SERVICE_VISION, 1)
        await db.commit()
        return result

    except Exception as exc:
        await db.execute(
            "UPDATE analyses SET status = 'failed', error_message = ? WHERE id = ?",
            (str(exc), analysis_id),
        )
        await db.commit()
        raise
