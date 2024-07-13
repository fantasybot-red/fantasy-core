import random
import asyncio
import zingmp3py
import unity.spotify as sp
import sclib.asyncio as sclib

class QueueData:
    def __init__(self, data):
        self.raw = data
        self.load()
        
    def load(self):
        data = self.raw
        if type(data) is sclib.Track:
            title = data.artist + " - " + data.title
            url = data.permalink_url
            img_url = data.artwork_url
        elif type(data) is zingmp3py.zasync.Song:
            url = data.link
            artist = " & ".join([i.name for i in data.artists])
            title = artist + " - " + data.title if artist else data.title
            img_url = data.thumbnail
        elif type(data) is zingmp3py.LiveRadio:
            url = data.url
            title = data.title
            img_url = data.thumbnail
        elif type(data) is sp.Track:
            url = data.spotify_url
            title = " & ".join([i for i in data.artist]) + " - " + data.name
            img_url = data.coverImage["DEFAULT"]
        elif type(data) is sp.Episode:
            url = data.spotify_url
            title = data.name
            img_url = data.coverImage["DEFAULT"]
        self.artwork_url = img_url
        self.title = title
        self.url = url
        if type(data) is sclib.Track:
            self.type = "Soundcloud"
        elif type(data) in (zingmp3py.zasync.Song, zingmp3py.LiveRadio):
            self.type = "Zingmp3"
        elif type(data) in (sp.Track, sp.Episode):
            self.type = "Spotify"
    
    def to_dict(self):
        return {
            "artwork_url": self.artwork_url,
            "title": self.title,
            "url": self.url,
            "type": self.type
        }


class MusicQueue(list):
    nowplaying = -1
    loop = 0
    
    def send_event(self, event):
        asyncio.create_task(self.bot.db.publish(f"music_queue_event:{self.guild_id}", event))
    
    def __init__(self, bot, guild_id):
        self.bot = bot
        self.guild_id = guild_id
        pass

    def queue(self):
        if self.loop == 2:
            og_queue = self[self.nowplaying:]
            if self.nowplaying > 0:
                og_queue += self[:self.nowplaying]
            return og_queue
        return self[self.nowplaying:]

    def add_queue(self, data):
        rdata = self.extend([QueueData(i) for i in data])
        self.send_event("queue_update")
        return rdata

    def now_playing(self):
        return self[self.nowplaying]
    
    def shuffle(self):
        new_list = self[self.nowplaying+1:]
        random.shuffle(new_list)
        self[self.nowplaying+1:] = new_list
        self.send_event("queue_update")

    def prev(self):
        if self.loop == 1:
            return self[self.nowplaying]
        elif self.loop == 2:
            if self.nowplaying == 0:
                self.nowplaying = len(self) - 2
                return self[len(self)-1]
            self.nowplaying -= 2
            return self[self.nowplaying+1]
        else:
            self.nowplaying -= 2
            if self.nowplaying+1 >= 0:
                return self[self.nowplaying+1]
            else:
                self.nowplaying += 2

    def __next__(self):
        self.send_event("queue_update")
        self.nowplaying += 1
        if self.loop == 1:
            if self.nowplaying != 0:
                self.nowplaying -= 1
        elif self.loop == 2:
            if self.nowplaying == len(self):
                self.nowplaying = 0
        if self.nowplaying >= len(self):
            self.nowplaying = len(self)-1
            return None
        return self[self.nowplaying]


