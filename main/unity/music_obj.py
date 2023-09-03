import sclib.asyncio as sclib
import zingmp3py
from unity.yt import YT_Video
import unity.spotify as sp

async def QueueData(data):
    if type(data) is sclib.Track:
        title = data.artist + " - " + data.title
        url = data.permalink_url
    elif type(data) is YT_Video:
        title = data.title
        url = data.watch_url
    elif type(data) is zingmp3py.zasync.Song:
        url = data.link
        artist = " & ".join([i.name for i in data.artists])
        title = artist + " - " + data.title if artist else data.title
    elif type(data) is zingmp3py.LiveRadio:
        url = data.url
        title = data.title
    elif type(data) is sp.Track:
        url = data.spotify_url
        title = " & ".join([i for i in data.artist]) + " - " + data.name
    elif type(data) is sp.Episode:
        url = data.spotify_url
        title = data.name
    return (title, url)

class MusicQueue(list):
    nowplaying = -1
    loop = 0
    volume = 100

    def __init__(self):
        pass

    def get_volume_ff(self):
        return self.volume / 100

    def queue(self):
        return self[self.nowplaying:]

    def add_queue(self, data):
        return self.extend(data)

    def now_playing(self):
        return self[self.nowplaying]

    def prev(self):
        
        if self.loop == 1:
            return self[self.nowplaying]
        
        self.nowplaying -= 2
        if self.nowplaying+1 >= 0:
            return self[self.nowplaying+1]
        else:
            self.nowplaying += 2

    def __next__(self):
        self.nowplaying += 1
        if self.loop == 1:
            if self.nowplaying != 0:
                self.nowplaying -= 1
        elif self.loop == 2:
            self.append(self[self.nowplaying-1])
        if len(self[:self.nowplaying]) >= 30:
            del self[0]
            self.nowplaying -= 1
        if self.nowplaying >= len(self):
            self.nowplaying = len(self)-1
            return None
        return self[self.nowplaying]


