"""Camera info router."""
from fastapi import APIRouter, HTTPException
from app.services import tapo_service

router = APIRouter(prefix="/api/camera", tags=["camera"])


@router.get("/info")
async def get_camera_info():
    """Return basic device information from the camera."""
    try:
        info = await tapo_service.get_camera_info()
        return {"status": "online", "info": info}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Camera unreachable: {exc}")


@router.get("/status")
async def camera_status():
    """Quick connectivity check."""
    try:
        await tapo_service.get_camera_info()
        return {"status": "online"}
    except Exception:
        return {"status": "offline"}
