import logging
import os
from pathlib import Path

from telethon import TelegramClient
from telethon.tl.types import Message

from config import ALLOWED_EXTENSIONS
from state import State

logger = logging.getLogger(__name__)


def _safe_filename(name: str, download_dir: str) -> str:
    """Return a non-colliding path for the file."""
    base = Path(download_dir) / name
    if not base.exists():
        return str(base)
    stem, suffix = base.stem, base.suffix
    counter = 1
    while True:
        candidate = Path(download_dir) / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return str(candidate)
        counter += 1


async def download_file(
    client: TelegramClient,
    message: Message,
    download_dir: str,
    state: State,
) -> None:
    if state.is_downloaded(message.id):
        logger.debug("Skipping duplicate message_id=%d", message.id)
        return

    doc = message.document
    if doc is None:
        return

    # Determine filename
    filename = None
    for attr in doc.attributes:
        if hasattr(attr, "file_name") and attr.file_name:
            filename = attr.file_name
            break
    if not filename:
        filename = f"file_{message.id}"

    ext = Path(filename).suffix.lower()
    if ext and ext not in ALLOWED_EXTENSIONS:
        logger.info("Skipping unsupported extension %s (message_id=%d)", ext, message.id)
        return

    dest = _safe_filename(filename, download_dir)
    os.makedirs(download_dir, exist_ok=True)

    logger.info("Downloading '%s' (message_id=%d)...", filename, message.id)
    try:
        await client.download_media(message, file=dest)
        state.mark_downloaded(message.id)
        logger.info("Saved to %s", dest)
    except Exception as e:
        logger.error("Failed to download message_id=%d: %s", message.id, e)
