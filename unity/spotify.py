import re
import string
import aiohttp
import asyncio
from urllib.parse import urlparse

BASE62_ALPHABET = string.digits + string.ascii_letters

class Spotify:
    header = {}

    def __init__(self, api_domain, auth=None):
        self.api_domain = api_domain
        if auth is not None:
            self.header = {"Authorization": auth}

    def fileurl(self, ids: str):
        return f"https://i.scdn.co/image/{ids.lower()}"

    def url_to_uri(self, url):
        # Parse the URL to extract the domain and path
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if not re.match(r"(^|.*\.)spotify\.com$", domain):
            # URL is not from spotify.com domain
            return None
        path = parsed_url.path
        # Match the type and id using regular expression
        match = re.search(r"/(\w+)/([\w\d]+)", path)
        if match:
            # Extract the type and id from the match object
            type_id = match.group(1)
            id = match.group(2)
            # Construct the URI using the type and id
            uri = f"spotify:{type_id}:{id}"
            return uri, type_id
        else:
            # URL format is not recognized
            return None

    def is_spotify_uri(self, uri):
        pattern = r"^spotify:(episode|album|playlist|track|show):.{22}"
        return bool(re.match(pattern, uri))

    async def data_process(self, data, type_id):
        if type_id == "episode":
            return Episode(data, self)
        elif type_id == "album":
            list_future = [self.get_from_url(j, False) for i in data["discs"] for j in i["tracks"]]
            return await asyncio.gather(*list_future)
        elif type_id == "playlist":
            list_future = [self.get_from_url(i["id"], False) for i in data["contents"]["items"]]
            return await asyncio.gather(*list_future)
        elif type_id == "track":
            return Track(data, self)
        elif type_id == "show":
            list_future = [self.get_from_url(i, False) for i in data["episodes"]]
            return await asyncio.gather(*list_future)
        else:
            return None

    async def search(self, url):
        async with aiohttp.ClientSession(base_url=self.api_domain, headers=self.header) as s:
            async with s.get(f"/api/v1/sp/search", params={"q": url}) as r:
                data = await r.json()
        tracks = data["results"]["tracks"]
        if tracks["total"] == 0:
            return None
        track_uri = tracks["hits"][0]["uri"]
        return await self.get_from_url(track_uri, False)

    async def get_from_url(self, url, type_r=True):
        if not self.is_spotify_uri(url):
            uri, type_id = self.url_to_uri(url)
            if uri is None:
                return None
        else:
            uri = url
            type_id = uri.split(":")[1]
        async with aiohttp.ClientSession(base_url=self.api_domain, headers=self.header) as s:
            async with s.get(f"/api/v1/sp/metadata/{uri}") as r:
                if r.ok:
                    data = await r.json()
                    pdata = await self.data_process(data, type_id)
                    if not type_r:
                        return pdata
                    return pdata, type_id
                else:
                    return None


class Track:
    id: str
    name: str
    album: dict
    number: int
    discNumber: int
    duration: int
    popularity: int
    externalId: list
    file: list
    preview: list
    restrictions: list
    earliestLiveTimestamp: int
    hasLyrics: bool
    licensor: dict
    type: str

    def __init__(self, data: dict, client: Spotify):
        self.__client = client
        for k, v in data.items():
            k = "_" + k if k in dir(self) else k
            setattr(self, k, v)

    @property
    def is_playable(self):
        return not self.restrictions

    @property
    def artist(self):
        return [i["name"] for i in self.artists]

    @property
    def spotify_uri(self):
        return self.id

    @property
    def spotify_url(self):
        return f"https://open.spotify.com/track/{self.id.split(':')[-1]}"

    @property
    def coverImage(self):
        return {i["size"]: self.__client.fileurl(i["id"]) for i in self.album["covers"]}


class Episode:
    id: str
    name: str
    duration: int
    audio: list
    description: str
    publishTime: dict
    language: str
    explicit: bool
    show: dict
    audioPreview: list
    restriction: list
    allowBackgroundPlayback: bool
    externalUrl: str

    def __init__(self, data: dict, client: Spotify):
        self.__client = client
        for k, v in data.items():
            k = "_" + k if k in dir(self) else k
            setattr(self, k, v)

    @property
    def spotify_uri(self):
        return self.id

    @property
    def spotify_url(self):
        return f"https://open.spotify.com/episode/{self.id.split(':')[-1]}"

    @property
    def coverImage(self):
        return {i["size"]: self.__client.fileurl(i["id"]) for i in self.covers}