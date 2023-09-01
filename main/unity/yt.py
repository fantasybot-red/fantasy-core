import urllib.parse
import aiohttp
import re


async def is_channel_url(url):
    patterns = [
        r"/(c)/([%\w\d_\-]+)(\/.*)?",
        r"/(channel)/([%\w\d_\-]+)(\/.*)?",
        r"/(u)/([%\w\d_\-]+)(\/.*)?",
        r'/(user)/([%\w\d_\-]+)(\/.*)?',
        r'/(@)([%\w\d_\-]+)(\/.*)?'
    ]
    for i in patterns:
        out = re.findall(i, url)
        if out:
            break
    if out:
        out = out[0]
        if out[0] == "@":
            async with aiohttp.ClientSession() as s:
                async with s.get(f"https://www.youtube.com/@{out[1]}") as r:
                    if r.ok:
                        return re.findall(r'<meta property="og:url" content="https://www.youtube.com/channel/(.*?)">', await r.text())[0]
                    else:
                        return None
        else:
            return out[1]
                

def video_id(url: str) -> str:
    out = re.findall(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    if out:
        return out[0]
    else:
        return None


def playlist_id(url) :
    parsed = urllib.parse.urlparse(url)
    data = urllib.parse.parse_qs(parsed.query).get('list')
    if data is None:
        return None
    return data[0]

class YT_Video:
    def __init__(self, data):
        self.video_id = data["videoId"]
        self.watch_url = f"https://www.youtube.com/watch?v={self.video_id}"
        self.thumbnails = data["thumbnails"]
        self.lengthSeconds = data["lengthSeconds"]
        self.title = data["title"]
        self.author =  data["author"]
        self.isLive = data["isLive"]
        
    def __eq__(self, other):
        return self.video_id == other.video_id
    
    def __ne__(self, other):
        return self.video_id == other.video_id

class Youtube:
    
    header = {}
    
    def __init__(self, api_domain, auth=None):
        self.api_domain = api_domain
        if auth is not None:
           self.header = {"Authorization": auth}

    async def get_video(self, url):
        vid = video_id(url)
        if vid is None:
            return None
        async with aiohttp.ClientSession(base_url=self.api_domain, headers=self.header) as s:
            async with s.get("/api/yt/video", timeout=None, params={"url": vid}) as r:
                if r.ok:
                    return YT_Video(await r.json())
                else:
                    return None

    async def get_search(self, pram):
        async with aiohttp.ClientSession(base_url=self.api_domain, headers=self.header) as s:
            async with s.get("/api/yt/search", timeout=None, params={"q": pram}) as r:
                if r.ok:
                    return YT_Video(await r.json())
                else:
                    return None

    async def get_playlist(self, url):
        pid = playlist_id(url)
        if pid is None:
            return None
        async with aiohttp.ClientSession(base_url=self.api_domain, headers=self.header) as s:
            async with s.get("/api/yt/playlist", timeout=None, params={"url": pid}) as r:
                if r.ok:
                    return [YT_Video(i) for i in await r.json()]
                else:
                    return None

    async def get_channel(self, url):
        cid = await is_channel_url(url)
        if cid is None:
            return None
        async with aiohttp.ClientSession(base_url=self.api_domain, headers=self.header) as s:
            async with s.get("/api/yt/channel", timeout=None, params={"url": cid}) as r:
                if r.ok:
                    return [YT_Video(i) for i in await r.json()]
                else:
                    return None