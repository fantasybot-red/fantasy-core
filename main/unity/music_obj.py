import sclib.asyncio as sclib
import chiasenhac.asyncio as chiasenhac
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
    elif type(data) is chiasenhac.Song:
        url = data.url
        title = data.titleraw
    elif type(data) is sp.Track:
        url = data.spotify_url
        title = " & ".join([i for i in data.artist]) + " - " + data.name
    elif type(data) is sp.Episode:
        url = data.spotify_url
        title = data.name
    return (title, url)

