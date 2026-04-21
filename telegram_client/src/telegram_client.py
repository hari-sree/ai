import logging

from telethon import TelegramClient, events
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

    @client.on(events.NewMessage(from_users=target.id))
    async def handler(event: events.NewMessage.Event) -> None:
        message = event.message
        if message.document:
            logger.info("New file message detected (message_id=%d)", message.id)
            await download_file(client, message, config.DOWNLOAD_DIR, state)
        else:
            logger.debug("Message has no document, skipping (message_id=%d)", message.id)

    logger.info("Listening for messages from %s...", config.TARGET_USER)
    await client.run_until_disconnected()
