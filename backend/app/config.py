"""Application configuration loaded from environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Tapo Camera
    TAPO_IP: str = os.getenv("TAPO_IP", "")
    TAPO_EMAIL: str = os.getenv("TAPO_EMAIL", "")
    TAPO_CLOUD_PASS: str = os.getenv("TAPO_CLOUD_PASS", "")
    ONVIF_USER: str = os.getenv("ONVIF_USER", "admin")
    ONVIF_PASS: str = os.getenv("ONVIF_PASS", "")

    # GCP
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "")
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS", "/app/credentials/service-account.json"
    )

    # Quota limits (free tier defaults)
    VIDEO_INTEL_MONTHLY_LIMIT: int = int(os.getenv("VIDEO_INTEL_MONTHLY_LIMIT", "1000"))
    VISION_MONTHLY_LIMIT: int = int(os.getenv("VISION_MONTHLY_LIMIT", "1000"))

    # Download settings
    DOWNLOAD_WINDOW_SIZE: int = int(os.getenv("DOWNLOAD_WINDOW_SIZE", "50"))
    DATA_DIR: str = os.getenv("DATA_DIR", "/app/data")
    RECORDINGS_DIR: str = os.path.join(os.getenv("DATA_DIR", "/app/data"), "recordings") + os.sep
    FRAMES_DIR: str = os.path.join(os.getenv("DATA_DIR", "/app/data"), "frames") + os.sep
    DB_PATH: str = os.path.join(os.getenv("DATA_DIR", "/app/data"), "db", "app.db")

    # Video Intelligence 20MB limit — re-encode threshold in bytes
    VIDEO_SIZE_LIMIT_BYTES: int = 19 * 1024 * 1024  # 19 MB safety margin


settings = Settings()
