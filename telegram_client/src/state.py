import json
import logging
import os
from typing import Set

logger = logging.getLogger(__name__)


class State:
    def __init__(self, path: str):
        self.path = path
        self._downloaded: Set[int] = set()
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path) as f:
                data = json.load(f)
            self._downloaded = set(data.get("downloaded_message_ids", []))
            logger.debug("Loaded %d message IDs from state", len(self._downloaded))
        except Exception as e:
            logger.warning("Could not load state file: %s", e)

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w") as f:
            json.dump({"downloaded_message_ids": list(self._downloaded)}, f)

    def is_downloaded(self, message_id: int) -> bool:
        return message_id in self._downloaded

    def mark_downloaded(self, message_id: int) -> None:
        self._downloaded.add(message_id)
        self._save()
