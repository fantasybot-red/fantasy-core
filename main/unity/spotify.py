import aiohttp
import asyncio
from urllib.parse import urlparse
import re
import string

BASE62_ALPHABET = string.digits+string.ascii_letters

def base62_encode(bytes_obj):
    base62 = ''
    num = int.from_bytes(bytes_obj, byteorder='big')
    if num == 0:
        return '0'
    while num > 0:
        num, remainder = divmod(num, 62)
        base62 = BASE62_ALPHABET[remainder] + base62
    return base62

class Spotify:
    header = {}
    def __init__(self, api_domain, auth=None):
        self.api_domain = api_domain
        if auth != None:
           self.header = {"Authorization": self.auth}
    
    def fileurl(self, ids:str):
        return f"https://i.scdn.co/image/{ids.lower()}"

    def hex_to_id(self, hex_id):
        return base62_encode(bytes.fromhex(hex_id)).zfill(22)

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
            type = match.group(1)
            id = match.group(2)
            # Construct the URI using the type and id
            uri = f"spotify:{type}:{id}"
            return uri
        else:
            # URL format is not recognized
            return None

    def is_spotify_uri(self, uri):
        pattern = r"^spotify:(episode|album|playlist|track|show):.{22}"
        return bool(re.match(pattern, uri))

    async def get_from_url(self, url, req_type=True):
        if not self.is_spotify_uri(url):
            uri = self.url_to_uri(url)
            if uri is None:
                return None
        else:
            uri = url
        async with aiohttp.ClientSession(base_url=self.api_domain, headers=self.header) as s:
            async with s.get(f"/api/sp/loadmeta/{uri}") as r:
                if r.ok:
                    data = await r.json()
                    stype = data["type"]
                    if stype == "track":
                        outdata = Track(data, self)
                    elif stype == "playlist":
                        outdata = await asyncio.gather(*[self.get_from_url(i["uri"], req_type=False) for i in data["contents"]["items"]])
                    elif stype == "album":
                        l_uri = [f"spotify:track:{self.hex_to_id(ia['gid'])}" for i in data["disc"] for ia in i["track"]]
                        l_f = [ self.get_from_url(i, req_type=False) for i in l_uri]
                        outdata = await asyncio.gather(*l_f)
                    elif stype == "episode":
                        outdata = Episode(data, self)
                    elif stype == "show":
                        outdata = await asyncio.gather(*[self.get_from_url("spotify:episode:"+self.hex_to_id(i["gid"]), req_type=False) for i in data["episode"]])
                    if req_type:
                        return {"type": stype, "data":  outdata}
                    else:
                        return outdata
                else:
                    return {"type": None, "data":  None}


class Track:
    gid: str
    name: str
    album: dict
    number: int
    discNumber: int
    duration: int
    popularity: int
    externalId: list
    file: list
    preview: list
    restriction:list
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
        return getattr(self, "restriction", None) is None
    
    @property
    def artist(self):
        return [i["name"] for i in self._artist]

    @property
    def spotify_uri(self):
        return f"spotify:track:{self.__client.hex_to_id(self.gid)}"
    
    @property
    def spotify_url(self):
        return f"https://open.spotify.com/track/{self.__client.hex_to_id(self.gid)}"
    
    @property
    def coverImage(self):
        return { i["size"]:self.__client.fileurl(i["fileId"]) for i in self.album["coverGroup"]["image"]}


class Episode:
    gid: str
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
        return f"spotify:episode:{self.__client.hex_to_id(self.gid)}"
    
    @property
    def spotify_url(self):
        return f"https://open.spotify.com/episode/{self.__client.hex_to_id(self.gid)}"
    
    @property
    def coverImage(self):
        return { i["size"]:self.__client.fileurl(i["fileId"]) for i in self._coverImage["image"]}