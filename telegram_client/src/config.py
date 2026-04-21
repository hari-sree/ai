import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Missing required env var: {key}")
    return value


API_ID: int = int(_require("API_ID"))
API_HASH: str = _require("API_HASH")
TARGET_USER: str = _require("TARGET_USER")
DOWNLOAD_DIR: str = os.getenv("DOWNLOAD_DIR", "./downloads")
STATE_FILE: str = os.getenv("STATE_FILE", "./data/state.json")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

SESSION_NAME: str = "tg_session"

ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".txt", ".csv", ".json", ".xml",
    ".png", ".jpg", ".jpeg", ".gif", ".mp4", ".mp3",
}
