from __future__ import annotations

from exceptions import InvalidURL
from logger import logger
import re
import requests
from urllib.parse import urlparse


class TSRUrl:
    def __init__(self, url: str):
        if self.__isValidUrl(url):
            self.url = url
            self._html: str | None = None
            self.itemId = self.__getItemId(url)
            self.downloadUrl = f"https://www.thesimsresource.com/downloads/download/itemId/{self.itemId}"
        else:
            raise InvalidURL(url)

    @classmethod
    def __getItemId(cls, url: str) -> int | None:
        itemId = (
            re.search(r"(?<=/id/)\d+", url)
            or re.search(r"(?<=/itemId/)\d+", url)
            or re.search(r"(?<=.com/downloads/)\d+", url)
        )

        logger.debug(f"Got ItemId: {itemId[0] if itemId else 'None'} from Url: {url}")
        return int(itemId[0]) if itemId else None

    @classmethod
    def __isValidUrl(cls, url: str) -> bool:
        isUrlValid = "thesimsresource.com/" in url and cls.__getItemId(url) is not None
        logger.debug(f"Is url valid: {isUrlValid}")
        return isUrlValid

    @property
    def creator(self) -> str | None:
        path = urlparse(self.url).path.strip("/").split("/")

        if "members" in path:
            return path[path.index("members") + 1]

        if "artists" in path:
            return path[path.index("artists") + 1].strip("-")

        html = self._get_html()

        m = re.search(
            r'<a[^>]*href="/(?:members|artists)/([^/]+)/"[^>]*class="[^"]*big-creator[^"]*"',
            html,
        )
        if m:
            return m.group(1).strip("-")

        return None

    def isVipExclusive(self) -> bool:
        r = requests.get(self.url)
        return "VIP Exclusive" in r.text

    @staticmethod
    def getRequiredItems(url: "TSRUrl") -> list["TSRUrl"]:
        def convertHrefToTSRUrl(href: str) -> TSRUrl:
            logger.debug(f"Converting {href} to TSRUrl")
            return TSRUrl(f"https://www.thesimsresource.com{href}")

        logger.debug(f"Getting required items for {url.url}")

        r = requests.get(f"https://www.thesimsresource.com/downloads/{url.itemId}")

        return list(
            map(
                convertHrefToTSRUrl,
                re.findall(
                    r'(?<=<li class="required-download-item"><a href=")/downloads/\d+(?=")',
                    r.text,
                ),
            )
        )

    def _get_html(self) -> str:
        if self._html is None:
            r = requests.get(self.url)
            r.raise_for_status()
            self._html = r.text
        return self._html
