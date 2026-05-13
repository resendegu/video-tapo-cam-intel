"""SQLite database setup and connection management."""
import aiosqlite
from app.config import settings

_DB_PATH = settings.DB_PATH


async def get_db() -> aiosqlite.Connection:
    """FastAPI dependency — yields an open DB connection."""
    async with aiosqlite.connect(_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def init_db() -> None:
    """Create all tables if they don't exist. Called on app startup."""
    async with aiosqlite.connect(_DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS recordings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                date        TEXT    NOT NULL,
                start_time  INTEGER NOT NULL UNIQUE,
                end_time    INTEGER NOT NULL,
                duration    INTEGER NOT NULL,
                clip_type   TEXT    NOT NULL DEFAULT 'motion',
                filename    TEXT,
                file_size   INTEGER,
                downloaded  INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                recording_id   INTEGER NOT NULL REFERENCES recordings(id),
                service        TEXT    NOT NULL,  -- 'video_intelligence' | 'vision'
                status         TEXT    NOT NULL DEFAULT 'pending',
                result_json    TEXT,
                units_used     REAL    NOT NULL DEFAULT 0,
                error_message  TEXT,
                created_at     TEXT    NOT NULL DEFAULT (datetime('now')),
                completed_at   TEXT
            );

            CREATE TABLE IF NOT EXISTS quota_usage (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                service     TEXT    NOT NULL,
                year_month  TEXT    NOT NULL,  -- 'YYYY-MM'
                units_used  REAL    NOT NULL DEFAULT 0,
                updated_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                UNIQUE(service, year_month)
            );
        """)
        await db.commit()
