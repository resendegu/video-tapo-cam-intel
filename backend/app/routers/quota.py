"""Quota status router."""
import aiosqlite
from fastapi import APIRouter, Depends
from app.db import get_db
from app.services import quota_service

router = APIRouter(prefix="/api/quota", tags=["quota"])


@router.get("")
async def get_quota(db: aiosqlite.Connection = Depends(get_db)):
    """Return current month's GCP API usage vs free tier limits."""
    return await quota_service.get_quota_status(db)
