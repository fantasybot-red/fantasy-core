import aiohttp
from collections import namedtuple
from enum import Enum, unique
from urllib.parse import urljoin, urlparse


@unique
class Extension(Enum):
    JPG = 'j'
    PNG = 'p'
    GIF = 'g'


class Doujin():
    """
    Class representing a doujin.

    :ivar int id:			Doujin id.
    :ivar dict titles:		Doujin titles (language:title).
    :ivar Doujin.Tag tags:	Doujin tag list.
    :ivar str cover:		Doujin cover image url.
    :ivar str thumbnail:	Doujin thumbnail image url.
    """
    Tag = namedtuple("Tag", ["id", "type", "name", "url", "count"])
    Pages = namedtuple("Page", ["url", "width", "height"])

    def __init__(self, data):
        self.id = data["id"]
        self.media_id = data["media_id"]
        self.titles = data["title"]
        self.favorites = data["num_favorites"]
        self.url = f"https://nhentai.net/g/{self.id}"
        images = data["images"]

        self.pages = [Doujin.__makepage__(
            self.media_id, num, **_) for num, _ in enumerate(images["pages"], start=1)]
        self.tags = [Doujin.Tag(**_) for _ in data["tags"]]

        thumb_ext = Extension(images["thumbnail"]["t"]).name.lower()
        self.thumbnail = f"https://t.nhentai.net/galleries/{self.media_id}/thumb.{thumb_ext}"

        cover_ext = Extension(images["cover"]["t"]).name.lower()
        self.cover = f"https://t.nhentai.net/galleries/{self.media_id}/cover.{cover_ext}"

    def __getitem__(self, key: int):
        """
        Returns a page by index.

        :rtype: Doujin.Page 
        """
        return self.pages[key]

    def __makepage__(media_id: int, num: int, t: str, w: int, h: int):
        return Doujin.Pages(f"https://i.nhentai.net/galleries/{media_id}/{num}.{Extension(t).name.lower()}",
                            w, h)


async def _get(endpoint) -> dict:
    async with aiohttp.ClientSession() as s:
        urlpram = urljoin("https://nhentai.net/api/", endpoint)
        pram = {"sl": "fil", "tl": "en", "hl": "fil",
                "u": urlpram, "client": "webapp"}
        async with s.get("https://translate.google.com/translate", params=pram) as r:
            return await r.json()
        


async def get_doujin(id: int) -> Doujin:
    """
    Get a doujin by its id.

    :param int id: A doujin's id.

    :rtype: Doujin
    """
    try:
        return Doujin(await _get(f"gallery/{id}"))
    except KeyError:
        raise ValueError("A doujin with the given id wasn't found")


async def get_random_id() -> int:
    async with aiohttp.ClientSession() as s:
        urlpram = "https://nhentai.net/random/"
        pram = {"sl": "fil", "tl": "en", "hl": "fil",
                "u": urlpram, "client": "webapp"}
        async with s.get("https://translate.google.com/translate", params=pram) as r:
            redirect = urlparse(str(r.url)).path.split("/")[-2]
            return int(redirect)
