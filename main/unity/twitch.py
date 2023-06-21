import sync_to_async
import re
import time
import aiohttp
import youtube_dl
from dataclasses import dataclass

class ytdls_main:
    url = None

    @sync_to_async.run
    def audio_url(self):
        if not self.url:
            raise ValueError
        with youtube_dl.YoutubeDL({'format': 'best', "quiet": True}) as ydl:
            info = ydl.extract_info(self.url, download=False)
            return info["formats"][len(info["formats"]) - 1]["url"]


@dataclass
class User(ytdls_main):
    id: str = None
    user_id: str = None
    user_login: str = None
    user_name: str = None
    game_id: str = None
    game_name: str = None
    type: str = None
    title: str = None
    viewer_count: int = None
    started_at: str = None
    language: str = None
    thumbnail_url: str = None
    tag_ids: list = None
    tags: list = None
    is_mature: bool = None
    obj_type: str = None

    @property
    def url(self):
        return f"https://www.twitch.tv/{self.user_login}"

    @property
    def thumbnail(self):
        return self.thumbnail_url.replace("%{", "{").format(width=320, height=180)


@dataclass
class Clip(ytdls_main):
    id: str = None
    url: str = None
    embed_url: str = None
    broadcaster_id: str = None
    broadcaster_name: str = None
    creator_id: str = None
    creator_name: str = None
    video_id: str = None
    game_id: str = None
    language: str = None
    title: str = None
    view_count: int = None
    created_at: str = None
    thumbnail_url: str = None
    duration: int = None
    vod_offset: int = None
    obj_type: str = None

    @property
    def thumbnail(self):
        return self.thumbnail_url


@dataclass
class Video(ytdls_main):
    id: str = None
    stream_id: str = None
    user_id: str = None
    user_login: str = None
    user_name: str = None
    title: str = None
    description: str = None
    created_at: str = None
    published_at: str = None
    url: str = None
    thumbnail_url: str = None
    viewable: str = None
    view_count: int = None
    language: str = None
    type: str = None
    duration: str = None
    muted_segments: None = None
    obj_type: str = None

    @property
    def thumbnail(self):
        return self.thumbnail_url.replace("%{", "{").format(width=320, height=180)


class TwitchHelix:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.expires_in = 0

    async def _get_access_token(self):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials'
        }
        async with aiohttp.ClientSession() as session:
            async with session.post('https://id.twitch.tv/oauth2/token', headers=headers, data=data) as resp:
                if resp.status == 200:
                    json = await resp.json()
                    self.access_token = json['access_token']
                    self.expires_in = json['expires_in']

    async def _refresh_access_token(self):
        if self.expires_in <= int(time.time()):
            await self._get_access_token()

    async def get_video(self, video_id):
        await self._refresh_access_token()
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Client-ID': self.client_id
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.twitch.tv/helix/videos', params={"id": video_id},
                                   headers=headers) as resp:
                if resp.status == 200:
                    data = (await resp.json())['data'][0]
                    data["obj_type"] = 'video'
                    return Video(**data)

    async def get_user(self, login):
        await self._refresh_access_token()
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Client-ID': self.client_id
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.twitch.tv/helix/streams', params={"user_login": login},
                                   headers=headers) as resp:
                if resp.status == 200:
                    data = (await resp.json())['data'][0]
                    data["obj_type"] = 'user'
                    return User(**data)

    async def get_clips(self, clip_id):
        await self._refresh_access_token()
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Client-ID': self.client_id
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.twitch.tv/helix/clips', params={"id": clip_id},
                                   headers=headers) as resp:
                if resp.status == 200:
                    data = (await resp.json())['data'][0]
                    data["obj_type"] = 'clips'
                    return Clip(**data)

    async def resolve_url(self, url):
        video_id = re.findall(r"https?://(?:(?:www|go|m)\.)?twitch\.tv/videos/(\d+)", url)
        if video_id:
            data = video_id[0]
            if data.endswith("/"):
                data = data[:-1]
            return await self.get_video(data)
        clip_id = re.findall(r"https?://(?:(?:www|go|m)\.)?twitch\.tv/\S+/clip/(\S+)", url)
        clip_id.extend(re.findall(r"https?://clips\.twitch\.tv/(\S+)", url))
        if clip_id:
            data = clip_id[0]
            if data.endswith("/"):
                data = data[:-1]
            return await self.get_clips(data)
        user_id = re.findall(r"https?://(?:(?:www|go|m)\.)?twitch\.tv/(\S+)", url)
        if user_id:
            data = user_id[0]
            if data.endswith("/"):
                data = data[:-1]
            return await self.get_user(data)
        raise ModuleNotFoundError
