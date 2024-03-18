import os
import json
import threading
import time

import feedparser

from library.log import logger


class Feed:

    def __init__(
        self,
        url: str,
        title: str = "",
        limit: int = 10,
    ):
        self.url = url
        self.title = title or url
        self.limit = limit
        self._feeds: list[dict[str, str]] = []
        self._updating = False
        self._updated = 0

        self._cache_path = f".cache/rss/{self.title}.json"
        if os.path.exists(self._cache_path):
            with open(self._cache_path, "r", encoding="utf8") as reader:
                self._feeds = json.load(reader)
            self._updated = os.path.getmtime(self._cache_path)

        self.get_items()

    def get_items(self) -> list[dict[str, str]]:
        if time.time() - self._updated > 1800:
            t = threading.Thread(target=self._update)
            t.start()
        return self._feeds[:self.limit]

    def _update(self, url: str = "") -> bool:
        if self._updating:
            return False
        
        self._updating = True
        try:
            parsed = feedparser.parse(url or self.url)["entries"]
        except Exception as e:
            logger.error("Exception while parsing rss feed: %s" % str(e))
            self._updating = False
            return False

        feeds = []
        for entry in parsed:
            item = {
                "title": entry.title,
                "link": entry.link,
                "published": getattr(entry, "published", ""),
                "summary": getattr(entry, "summary", ""),
            }
            feeds.append(item)
        try:
            os.makedirs(os.path.dirname(self._cache_path), exist_ok=True)
            with open(self._cache_path, "w", encoding="utf8") as writer:
                json.dump(feeds, writer, ensure_ascii=False, separators=(",", ":"))
        except Exception as e:
            logger.warn("Cannot write to cache: %s" % str(e))
        self._feeds = feeds
        self._updated = time.time()
        logger.debug(f"Updated feed: {self.title} ({len(self._feeds)} items)")
        self._updating = False
        return True
