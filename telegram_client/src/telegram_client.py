import logging

from telethon import TelegramClient
from telethon.tl.types import User

import config
from downloader import download_file
from state import State

logger = logging.getLogger(__name__)


async def resolve_target_user(client: TelegramClient) -> User:
    logger.info("Resolving target user: %s", config.TARGET_USER)
    entity = await client.get_entity(config.TARGET_USER)
    if not isinstance(entity, User):
        raise ValueError(f"TARGET_USER resolved to a non-user entity: {type(entity)}")
    name = f"{entity.first_name or ''} {entity.last_name or ''}".strip()
    logger.info("Target user resolved: %s (id=%d)", name, entity.id)
    return entity


async def run() -> None:
    state = State(config.STATE_FILE)

    client = TelegramClient(config.SESSION_NAME, config.API_ID, config.API_HASH)

    await client.start()
    logger.info("Authenticated successfully")

    target = await resolve_target_user(client)

    logger.info("Scanning message history for last file from %s...", config.TARGET_USER)

    # Walk through message history (newest first) and find the last file message
    async for message in client.iter_messages(target, filter=None):
        if not message.document:
            continue

        if state.is_downloaded(message.id):
            logger.info("Last file (message_id=%d) already downloaded, nothing to do.", message.id)
        else:
            await download_file(client, message, config.DOWNLOAD_DIR, state)

        break  # Only process the single most recent file message
    else:
        logger.info("No file messages found in history with %s.", config.TARGET_USER)

    await client.disconnect()
