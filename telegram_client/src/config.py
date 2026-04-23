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

# Extension filter for downloads. Empty set = allow all.
# Can be converted to an allowlist (add extensions here) or a blacklist
# (invert the check in downloader.py) as needed.
ALLOWED_EXTENSIONS: set[str] = set()
