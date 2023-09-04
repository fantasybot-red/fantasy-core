import discord
import os
import traceback
import aiohttp
import asyncio
import sync_to_async
import zingmp3py
import botemoji
import youtube_dl
import sclib.asyncio as sclib
import spotipy2.types.track as sptypes
import unity.twitch as twitch
import unity.spotify as sp
from spotipy2 import Spotify
from spotipy2.auth import ClientCredentialsFlow
from unitiprefix import get_prefix
from unity.music_obj import QueueData, MusicQueue
from unity.yt import YT_Video, Youtube
from discord import FFmpegPCMAudio
from discord.ext import commands
from discord import app_commands
from unity.interactx import Interactx
from unity.global_ui import Music_Volume, Music_bt

scclient = sclib.SoundcloudAPI()
zclient = zingmp3py.ZingMp3Async()
tw = twitch.TwitchHelix(client_id=os.getenv("TWITCH_ID"), client_secret=os.getenv("TWITCH_SECRER"))
ytclient = Youtube(os.getenv("MUISC_API_URL"), os.getenv("MUISC_API_AUTH"))
rspotify = sp.Spotify(os.getenv("MUISC_API_URL"), os.getenv("MUISC_API_AUTH"))

FFMPEG_OPTIONS_O = {
    'before_options': f'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 10', 'options': '-vn'
}


musisc_queue = {}


def get_music_loop(guild_id):
    return musisc_queue[str(guild_id)].loop

def set_music_loop(guild_id, loop_mode):
    musisc_queue[str(guild_id)].loop = loop_mode
            
def get_music_loop_text(guild_id):
    loopid = get_music_loop(guild_id)
    if loopid == 0:
        return "Off"
    elif loopid == 1:
        return "Track"
    elif loopid == 2:
        return "Queue"

def human_format(num):
    round_to = 0
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num = round(num / 1000.0, round_to)
    return '{:.{}f}{}'.format(num, round_to, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])

class Music(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot, sp):
        self.bot = bot
        self.spotify = sp
        
        async def check_m(ctx):
            if ctx.author.voice is None:
                return await ctx.reply("**Bạn chưa vào voice**", ephemeral=True)
            if ctx.voice_client is None:
                return await ctx.reply("**Bot Đang chả play gì cả**", ephemeral=True)
            if ctx.author.voice.channel != ctx.voice_client.channel:
                return await ctx.reply("**Bạn không ở chung voice với bot**", ephemeral=True)
        
        @bot.ev.interaction(name=r"m\.skip")
        async def on_skip(interaction: discord.Interaction):
            ctx = await Interactx(interaction, start=False)
            if (await check_m(ctx)) is not None:
                return
            await self.skip.callback(self, ctx)
            oldct = interaction.message.content
            await interaction.message.edit(content=interaction.user.mention)
            await interaction.message.edit(content=oldct)
        
        @bot.ev.interaction(name=r"m\.previous")
        async def on_previous(interaction: discord.Interaction):
            ctx = await Interactx(interaction, start=False)
            if (await check_m(ctx)) is not None:
                return
            await self.previous.callback(self, ctx)
            oldct = interaction.message.content      
            await interaction.message.edit(content=interaction.user.mention)
            await interaction.message.edit(content=oldct)
        
        
        @bot.ev.interaction(name=r"m\.resume|pause")
        async def on_pause(interaction: discord.Interaction):
            ctx = await Interactx(interaction, start=False)
            if (await check_m(ctx)) is not None:
                return
            if ctx.voice_client.is_paused():
                await self.resume.callback(self, ctx)
            else:
                await self.pause.callback(self, ctx)
            oldct = interaction.message.content         
            await interaction.message.edit(content=interaction.user.mention)
            await interaction.message.edit(content=oldct)
        
        @bot.ev.interaction(name=r"m\.nowplaying")
        async def on_nowplaying(interaction: discord.Interaction):
            ctx = await Interactx(interaction, start=False)
            if (await check_m(ctx)) is not None:
                return
            await self.nowplaying.callback(self, ctx)
            oldct = interaction.message.content      
            await interaction.message.edit(content=interaction.user.mention)
            await interaction.message.edit(content=oldct)
        
        @bot.ev.interaction(name=r"m\.queue")
        async def on_queue(interaction: discord.Interaction):
            ctx = await Interactx(interaction, start=False)
            if (await check_m(ctx)) is not None:
                return
            await self.queue.callback(self, ctx)
            oldct = interaction.message.content
            await interaction.message.edit(content=interaction.user.mention)
            await interaction.message.edit(content=oldct)
        
        @bot.ev.interaction(name=r"m\.loop")
        async def on_volume(interaction: discord.Interaction):
            ctx = await Interactx(interaction, start=False)
            oldct = interaction.message.content
            if (await check_m(ctx)) is not None:
                await interaction.message.edit(content=interaction.user.mention)
                await interaction.message.edit(content=oldct)
                return
            mode = interaction.data["values"][0]
            await self.loop.callback(self, ctx, mode=app_commands.Choice(name="a", value=mode))
            
            await interaction.message.edit(content=interaction.user.mention)
            await interaction.message.edit(content=oldct)
        
        @bot.ev.interaction(name=r"m\.volume_bt")
        async def on_volume_bt(interaction: discord.Interaction):
            ctx = await Interactx(interaction, start=False)
            if (await check_m(ctx)) is not None:
                return
            await interaction.response.send_modal(Music_Volume())
            
        
        @bot.ev.interaction(name=r"m\.volume_md")
        async def on_volume_md(interaction: discord.Interaction, data_input:dict):
            ctx = await Interactx(interaction, start=False)
            if (await check_m(ctx)) is not None:
                return
            dataout = data_input.get("m.voice_ip")
            try:
                data = int(dataout)
            except ValueError:
                return await ctx.reply("**Input không hợp lệ**", ephemeral=True)
            if 0 <= data <= 100:
                return await ctx.reply(f"**Input cần lớn hơn -1 và bé hơn 101 :>**", ephemeral=True)
            await self.volume.callback(self, ctx, volume=data)
                
                
    async def music_autocomplete(self, interaction, current: str):
        current = current.strip()
        if current:
            if not (current.startswith("http://") or current.startswith("https://")):
                if current.lower().startswith("sc:"):
                    msg = current[3:]
                    data = await scclient.autocomplete(msg)
                    rdata = [app_commands.Choice(name="sc:"+s, value="sc:"+s) for s in data]
                    rdata.insert(0, app_commands.Choice(name=current, value=current))
                elif current.lower().startswith("sf:"):
                    rdata = []
                    rdata.insert(0, app_commands.Choice(name=current, value=current))
                else:
                    async with aiohttp.ClientSession() as s:
                        data = {"input": current, "context":{"client":{"clientName": "WEB_REMIX", "clientVersion": "1.20230501.01.00"}}}
                        pram = {"key": "AIzaSyC9XL3ZjWddXya6X74dJoCTL-WEYFDNX30", "prettyPrint": "false"}
                        header = {"Referer": "https://music.youtube.com/"}
                        async with s.post("https://music.youtube.com/youtubei/v1/music/get_search_suggestions", headers=header, params=pram, json=data) as r:
                            data = await r.json()
                            a = [current+c["text"] for i in data["contents"][0]["searchSuggestionsSectionRenderer"]["contents"] for c in i["searchSuggestionRenderer"]["suggestion"]["runs"] if c.get("bold") is None]
                            sugest = list(dict.fromkeys(a))
                    rdata = [app_commands.Choice(name=s, value=s) for s in sugest]
                    rdata.insert(0, app_commands.Choice(name=current, value=current))
                return rdata
            else:
                return []
        else:
            return []
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member:discord.Member, before:discord.VoiceState, after:discord.VoiceState):
        if member != self.bot.user:
            if before.channel is not None:
                if before.channel != after.channel:
                    if self.bot.user.id in [a.id for a in before.channel.members]:
                        if len([i for i in before.channel.members if not i.bot]) == 0:
                            try:
                                await member.guild.voice_client.disconnect(force=True)
                            except BaseException:
                                pass
                            try:
                                member.guild.voice_client.cleanup()
                            except BaseException:
                                pass
                            try:
                                del musisc_queue[str(member.guild.id)]
                            except BaseException:
                                pass

        else:
            if before.channel is not None:
                if after.channel is not None:
                    if before.channel.id != after.channel.id:
                        if len([i for i in after.channel.members if not i.bot]) == 0:
                                try:
                                    await member.guild.voice_client.disconnect(force=True)
                                except BaseException:
                                    pass
                                try:
                                    member.guild.voice_client.cleanup()
                                except BaseException:
                                    pass
                                try:
                                    del musisc_queue[str(member.guild.id)]
                                except BaseException:
                                    pass
                        else:
                            try:
                                await member.guild.change_voice_state(channel=after.channel, self_mute=False, self_deaf=True)
                            except BaseException:
                                pass
                            try:
                                member.guild.voice_client.resume()
                            except BaseException:
                                pass
                else:
                    try:
                        await member.guild.voice_client.disconnect(force=True)
                    except BaseException:
                        pass
                    try:
                        member.guild.voice_client.cleanup()
                    except BaseException:
                        pass
                    try:
                        del musisc_queue[str(member.guild.id)]
                    except BaseException:
                        pass                

    async def play_audio(self, ctx, audio, mess):
        try:
            embed = discord.Embed(title="**Đang Load Audio**")
            if mess is not None:
                try:
                    await mess.edit(embed=embed)
                except BaseException:
                    pass
            FFMPEG_OPTIONS = FFMPEG_OPTIONS_O.copy()
            embed = discord.Embed()
            if type(audio) is YT_Video:
                pageurl = audio.watch_url
                title = audio.title
                img_url = f"https://img.youtube.com/vi/{audio.video_id}/mqdefault.jpg"
                async with aiohttp.ClientSession() as s:
                    async with s.get("https://returnyoutubedislikeapi.com/Votes", params={"videoId": audio.video_id}) as r:
                        ytdata = await r.json()
                embed.add_field(name="Likes", value=human_format(ytdata["likes"]))
                embed.add_field(name="Dislikes", value=human_format(ytdata["dislikes"]))
                embed.add_field(name="View Count", value=human_format(ytdata["viewCount"]))
                @sync_to_async.run
                def load_yt_audio():
                    with youtube_dl.YoutubeDL({'format': 'bestaudio/best', "quiet": True, 'noplaylist': True}) as ydl:
                        info = ydl.extract_info(pageurl, ie_key="Youtube", download=False)
                        return info["formats"][0]["url"]
                URL = await load_yt_audio()
            elif type(audio) is sclib.Track:
                pageurl = audio.permalink_url
                img_url = audio.artwork_url
                title = audio.artist + " - " + audio.title
                embed.add_field(name="Likes", value=human_format(audio.likes_count))
                embed.add_field(name="Playback Count", value=human_format(audio.playback_count))
                URL = await audio.get_stream_url()
            elif type(audio) is zingmp3py.zasync.Song:
                pageurl = audio.link
                img_url = audio.thumbnail
                artist = " & ".join([i.name for i in audio.artists])
                title = artist + " - " + audio.title if artist else audio.title
                list_has_checked = [i for i in (await audio.getStreaming()) if not i.isVIP]
                URL = list_has_checked[-1].url
            elif type(audio) is zingmp3py.LiveRadio:
                pageurl = audio.url
                img_url = audio.thumbnail
                title = audio.title
                URL = audio.streaming_url
            elif type(audio) is sp.Track:
                pageurl = audio.spotify_url
                img_url = audio.coverImage["LARGE"]
                title = " & ".join([i for i in audio.artist]) + " - " +audio.name
                if not audio.is_playable:
                    raise PermissionError("not playable")
                URL = f"{os.getenv('MUISC_API_URL')}/api/sp/{audio.spotify_uri}?auth={os.getenv('MUISC_API_AUTH')}"
            elif type(audio) is sp.Episode:
                pageurl = audio.spotify_url
                img_url = audio.coverImage["LARGE"]
                title = audio.name
                URL = f"{os.getenv('MUISC_API_URL')}/api/sp/{audio.spotify_uri}?auth={os.getenv('MUISC_API_AUTH')}"
            url = discord.PCMVolumeTransformer(FFmpegPCMAudio(URL, **FFMPEG_OPTIONS), volume=musisc_queue[str(ctx.guild.id)].get_volume_ff())
            ctx.voice_client.play(url, after=lambda e: asyncio.run_coroutine_threadsafe(self.autoskip(e, ctx), self.bot.loop))
            embed.title = "Đang Play:"
            embed.description = f"**[{title}]({pageurl})**"
            embed.set_thumbnail(url=img_url)
            if mess is not None:
                try:
                    await mess.edit(embed=embed, view=Music_bt())
                except BaseException:
                    pass
        except Exception:
            if mess != None:
                try:
                    embed = discord.Embed(title="Skip bài này do lỗi")
                    await mess.edit(embed=embed)
                except BaseException:
                    pass
            await self.skip_audio(ctx)
            traceback.print_exc()

    async def autoskip(self, e, ctx):
        asyncio.create_task(self.skip_audio(ctx), name=os.urandom(16).hex())
        if e:
            raise e

    async def skip_audio(self, ctx, mess=None):
        queue = musisc_queue.get(str(ctx.guild.id), None)
        check = ctx.voice_client
        if (check is not None) and (queue is not None):
            audio = next(musisc_queue[str(ctx.guild.id)])
            if audio is not None:
                await self.play_audio(ctx, audio, mess)
            else:
                try:
                    del musisc_queue[str(ctx.guild.id)]
                except BaseException:
                    pass
                try:
                    await ctx.voice_client.disconnect(force=True)
                except BaseException:
                    pass
                try:
                    ctx.voice_client.cleanup()
                except BaseException:
                    pass
        else:
            try:
                del musisc_queue[str(ctx.guild.id)]
            except BaseException:
                pass
            try:
                await ctx.voice_client.disconnect(force=True)
            except BaseException:
                pass
            try:
                ctx.voice_client.cleanup()
            except BaseException:
                pass

    async def load_audio(self, mess, url):
        url = url.strip()
        queue = []
        types_mess = 1
        if url.startswith("http://") or url.startswith("https://") or rspotify.is_spotify_uri(url):
            types_mess = 0
            if "youtu" in url:
                if "list=" in url:
                    listpl = await ytclient.get_playlist(url)
                    if listpl is None:
                        listpl = []
                    if "/watch" in url:
                        video = await ytclient.get_video(url)
                        if video is not None:
                            if listpl:
                                data = listpl.index(video)
                                listpl.extend(listpl[:data])
                                del listpl[:data]
                            else:
                                listpl.append(video)
                    if len(listpl) == 1:
                        try:
                            await mess.edit(content="**Đã add song vào queue**")
                        except BaseException:
                            pass
                        queue.extend(listpl)
                    elif len(listpl) > 1:
                        try:
                            await mess.edit(content=f"**Đã add {len(listpl)} song vào queue**")
                        except BaseException:
                            pass
                        queue.extend(listpl)
                    else:
                        try:
                            await mess.edit(content="**Link không hợp lệ**")
                        except BaseException:
                            pass
                elif ("/c/" in url) or ("/channel/" in url) or ("/u/" in url) or ("/user/" in url) or ("/@" in url):
                    cvideos = await ytclient.get_channel(url)
                    if cvideos is not None:
                        try:
                            await mess.edit(content=f"**Đã add {len(cvideos)} song vào queue**")
                        except BaseException:
                            pass
                        queue.extend(cvideos)
                    else:
                        try:
                            await mess.edit(content="**Link không hợp lệ**")
                        except BaseException:
                            pass 
                else:
                    video = await ytclient.get_video(url)
                    if video is not None:
                        queue.append(video)
                        try:
                            await mess.edit(content="**Đã add song vào queue**")
                        except BaseException:
                            pass
                    else:
                        try:
                            await mess.edit(content="**Link không hợp lệ**")
                        except BaseException:
                            pass

            elif "spotify.com" in url or rspotify.is_spotify_uri(url):
                data = await rspotify.get_from_url(url)
                rdata = data["data"]
                if rdata is not None:
                    if data["type"] == "track" or data["type"] == "episode":
                        queue.append(rdata)
                        try:
                            await mess.edit(content="**Đã add song vào queue**")
                        except BaseException:
                            pass
                    else:
                        rdata = [i for i in rdata if i is not None]
                        if data["type"] == "show":
                            rdata.reverse()
                        if rdata:
                            queue.extend(rdata)
                            try:
                                await mess.edit(content=f"**Đã add {len(rdata)} song vào queue**")
                            except BaseException:
                                pass
                        else:
                            try:
                                await mess.edit(content="**Link không hợp lệ**")
                            except BaseException:
                                pass
                else:
                    try:
                        await mess.edit(content="**Link không hợp lệ**")
                    except BaseException:
                        pass
            elif "soundcloud.com" in url:
                try:
                    out = await scclient.resolve(url)
                except BaseException:
                    out = None
                if out is not None:
                    if type(out) is sclib.Playlist:
                        queue.extend(out.tracks)
                        try:
                            await mess.edit(content=f"**Đã add {len(out.tracks)} Track vào queue**")
                        except BaseException:
                            pass
                    elif type(out) is sclib.USER:
                        queue.extend(out.tracks)
                        try:
                            await mess.edit(content=f"**Đã add {len(out.tracks)} Track vào queue**")
                        except BaseException:
                            pass
                    elif type(out) is sclib.Track:
                        queue.append(out)
                        try:
                            await mess.edit(content="**Đã add song vào queue**")
                        except BaseException:
                            pass
                else:
                    try:
                        await mess.edit(content="**Link không hợp lệ**")
                    except BaseException:
                        pass
            elif "zingmp3.vn" in url:
                outlinktype = zingmp3py.getUrlTypeAndID(url)
                if outlinktype["type"] == "liveradio":
                    try:
                        lives = await zclient.getRadioInfo(outlinktype["id"])
                    except BaseException:
                        lives = None
                    if not lives is None:
                        queue.append(lives)
                        try:
                            await mess.edit(content="**Đã add song vào queue**")
                        except BaseException:
                            pass
                    else:
                        try:
                            await mess.edit(content="**Link không hợp lệ**")
                        except BaseException:
                            pass
                elif outlinktype["type"] == "bai-hat":
                    try:
                        song = await zclient.getSongInfo(outlinktype["id"])
                    except BaseException:
                        song = None
                    if not song is None:
                        queue.append(song)
                        try:
                            await mess.edit(content="**Đã add song vào queue**")
                        except BaseException:
                            pass
                    else:
                        try:
                            await mess.edit(content="**Link không hợp lệ**")
                        except BaseException:
                            pass
                elif outlinktype["type"] == "album":
                    try:
                        playlist = await zclient.getDetailPlaylist(outlinktype["id"])
                    except BaseException:
                        playlist = None
                    if not playlist is None:
                        queue.extend(playlist.songs)
                        try:
                            await mess.edit(content=f"**Đã add {len(playlist.songs)} song vào queue**")
                        except BaseException:
                            pass
                    else:
                        try:
                            await mess.edit(content="**Link không hợp lệ**")
                        except BaseException:
                            pass
                else:
                    try:
                        await mess.edit(content="**Link không hợp lệ**")
                    except BaseException:
                        pass
        elif url.lower().startswith("sc:"):
            msg =  url[3:]
            try:
                out = (await scclient.search(msg, limit=1))[0]
            except BaseException:
                out = None
            if out is not None:
                if type(out) is sclib.Playlist:
                    queue.extend(out.tracks)
                    try:
                        await mess.edit(content=f"**Đã add {len(out.tracks)} Track vào queue**")
                    except BaseException:
                        pass
                elif type(out) is sclib.Track:
                    queue.append(out)
                    try:
                        await mess.edit(content="**Đã add song vào queue**")
                    except BaseException:
                        pass
            else:
                try:
                    await mess.edit(content="**Không có kết quả tìm kiếm**")
                except BaseException:
                    pass
        elif url.lower().startswith("sf:"):
            msg =  url[3:]
            data = await self.spotify._get("markets")
            track = (await self.spotify.search(query=msg, types=[sptypes.Track], limit=1, market=data["markets"]))['tracks'].items
            if track:
                queue.extend(await rspotify.get_from_url(track.uri))
                try:
                    await mess.edit(content=f"**Added song to the queue**")
                except BaseException:
                    pass
            else:
                try:
                    await mess.edit(content="**Không có kết quả tìm kiếm**")
                except BaseException:
                    pass
        else:
            data = await ytclient.get_search(url)
            if data is not None:
                queue.append(data)
                try:
                    await mess.edit(content=f"**Added song to the queue**")
                except BaseException:
                    pass
            else:
                try:
                    await mess.edit(content="**Không có kết quả tìm kiếm**")
                except BaseException:
                    pass
        types_mess + 1
        if not queue:
            return None
        else:
            return queue
    
    @app_commands.command(name="stop", description="Stop music")
    async def stop(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        if ctx.author.voice is not None:
            if ctx.voice_client is not None:
                if ctx.author.voice.channel == ctx.voice_client.channel:
                    try:
                        await ctx.voice_client.disconnect(force=True)
                    except BaseException:
                        pass
                    try:
                        ctx.voice_client.cleanup()
                    except BaseException:
                        pass
                    try:
                        del musisc_queue[str(ctx.guild.id)]
                    except BaseException:
                        pass
                    await ctx.send("**Đã dừng nhạc và thoát**")
                else:
                    await ctx.reply("**Bạn không ở chung voice với bot**")
            else:
                await ctx.reply("**Bot Đang chả play gì cả**")
        else:
            await ctx.reply("**Bạn chưa vào voice**")
    
    @app_commands.command(name="loop", description="Turn on/off loop mode")
    @app_commands.describe(mode="Mode loop")
    @app_commands.choices(mode=[
    app_commands.Choice(name='Off', value="off"),
    app_commands.Choice(name='Track', value="track"),
    app_commands.Choice(name='Queue', value="queue"),])
    async def loop(self, interaction: discord.Interaction, mode: app_commands.Choice[str]):
        mode = mode.value
        ctx = await Interactx(interaction)
        if ctx.author.voice is not None:
            if ctx.voice_client is not None:
                if ctx.author.voice.channel == ctx.voice_client.channel:
                    if mode.lower() == "off":
                        set_music_loop(ctx.guild.id, 0)
                        embed = discord.Embed(title="Loop mode: Off")
                    elif mode.lower() == "track":
                        set_music_loop(ctx.guild.id, 1)
                        embed = discord.Embed(title="Loop mode: Track")
                    elif mode.lower() == "queue":
                        set_music_loop(ctx.guild.id, 2)
                        embed = discord.Embed(title="Loop mode: Queue")
                    else:
                        embed = discord.Embed(title="List Loop Mode", description="**`Track`, `Queue`, `Off`**")
                    await ctx.reply(embed=embed)
                else:
                    await ctx.reply("**Bạn không ở chung voice với bot**")
            else:
                await ctx.reply("**Bot Đang chả play gì cả**")
        else:
            await ctx.reply("**Bạn chưa vào voice**")
    
    @app_commands.command(name="volume", description="Set music volume")
    async def volume(self, interaction: discord.Interaction, volume:app_commands.Range[int, 0, 100]):
        ctx = await Interactx(interaction)
        if ctx.author.voice is not None:
            if ctx.voice_client is not None:
                if ctx.author.voice.channel == ctx.voice_client.channel:
                    musisc_queue[str(ctx.guild.id)].volume = volume
                    ctx.voice_client.source.volume = musisc_queue[str(ctx.guild.id)].get_volume_ff()
                    await ctx.reply(f"**Đã set {volume}% volume**")
                else:
                    await ctx.reply("**Bạn không ở chung voice với bot**")
            else:
                await ctx.reply("**Bot Đang chả play gì cả**")
        else:
            await ctx.reply("**Bạn chưa vào voice**")
    
    @app_commands.command(name="skip", description="Skip music")
    async def skip(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        if ctx.author.voice is not None:
            if ctx.voice_client is not None:
                if ctx.author.voice.channel == ctx.voice_client.channel:
                    if musisc_queue[str(ctx.guild.id)].loop == 1:
                        await ctx.reply("**Skip không dùng được khi loop mode là Track**")
                        return
                    queue = musisc_queue[str(ctx.guild.id)].queue()
                    loop_mode = get_music_loop(ctx.guild.id)
                    if len(queue) > 1 or loop_mode > 0:
                        skipd = await QueueData(queue[0])
                        if len(queue) > 1 and loop_mode == 0:
                            nextd = await QueueData(queue[1])
                        elif loop_mode == 1:
                            nextd = await QueueData(queue[0])
                        elif loop_mode == 2:
                            if len(queue) > 1:
                                nextd = await QueueData(queue[1])
                            else:
                                nextd = await QueueData(queue[0])
                        text_loop_mode = get_music_loop_text(ctx.guild.id)
                        embed = discord.Embed(title="Skip", description=f"**Loop mode: {text_loop_mode}**")
                        embed.add_field(name="Đã skip:", value=f"**[{skipd[0]}]({skipd[1]})**", inline=False)
                        embed.add_field(name="Đang Play", value=f"**[{nextd[0]}]({nextd[1]})**", inline=False)
                        await ctx.reply(embed=embed)
                        ctx.voice_client.stop()
                    elif len(queue) == 1:
                        await ctx.reply("**Hết queue rồi tôi thoát đây :>**")
                        ctx.voice_client.stop()
                else:
                    await ctx.reply("**Bạn không ở chung voice với bot**")
            else:
                await ctx.reply("**Bot Đang chả play gì cả**")
        else:
            await ctx.reply("**Bạn chưa vào voice**")
    
    @app_commands.command(name="previous", description="Play previous music")
    async def previous(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        if ctx.author.voice is not None:
            if ctx.voice_client is not None:
                if ctx.author.voice.channel == ctx.voice_client.channel:
                    if musisc_queue[str(ctx.guild.id)].loop == 1:
                        await ctx.reply("**Previous không dùng được khi loop mode là Track**")
                        return
                    nowp = musisc_queue[str(ctx.guild.id)].queue()[0]
                    prev = musisc_queue[str(ctx.guild.id)].prev()
                    if prev is not None:
                        skipd = await QueueData(nowp)
                        nextd = await QueueData(prev)
                        text_loop_mode = get_music_loop_text(ctx.guild.id)
                        embed = discord.Embed(title="Previous", description=f"**Loop mode: {text_loop_mode}**")
                        embed.add_field(name="Đã previous:", value=f"**[{skipd[0]}]({skipd[1]})**", inline=False)
                        embed.add_field(name="Đang Play", value=f"**[{nextd[0]}]({nextd[1]})**", inline=False)
                        await ctx.reply(embed=embed)
                        ctx.voice_client.stop()
                    else:
                        await ctx.reply("**Không có bài trước đấy :/**")
                else:
                    await ctx.reply("**Bạn không ở chung voice với bot**")
            else:
                await ctx.reply("**Bot Đang chả play gì cả**")
        else:
            await ctx.reply("**Bạn chưa vào voice**")

    @app_commands.command(name="pause", description="Pause music")
    async def pause(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        if ctx.author.voice is not None:
            if ctx.voice_client is not None:
                if ctx.author.voice.channel == ctx.voice_client.channel:
                    ctx.voice_client.pause()
                    await ctx.reply(f"**Đã tạm dừng nhạc {botemoji.yes}**")
                else:
                    await ctx.reply("**Bạn không ở chung voice với bot**")
            else:
                await ctx.reply("**Bot Đang chả play gì cả**")
        else:
            await ctx.reply("**Bạn chưa vào voice**")
            
    @app_commands.command(name="resume", description="Resume music")
    async def resume(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        if ctx.author.voice is not None:
            if ctx.voice_client is not None:
                if ctx.author.voice.channel == ctx.voice_client.channel:
                    ctx.voice_client.resume()
                    await ctx.reply(f"**Đã tiếp tục nhạc {botemoji.yes}**")
                else:
                    await ctx.reply("**Bạn không ở chung voice với bot**")
            else:
                await ctx.reply("**Bot Đang chả play gì cả**")
        else:
            await ctx.reply("**Bạn chưa vào voice**")
    
    @app_commands.command(name="queue", description="Queue music")
    async def queue(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        if ctx.author.voice is not None:
            if ctx.voice_client is not None:
                if ctx.author.voice.channel == ctx.voice_client.channel:
                    embed = discord.Embed(title="Đang load queue")
                    edit = await ctx.reply(embed=embed)
                    queue = musisc_queue[str(ctx.guild.id)].queue()
                    queuelist = []
                    for t, i in enumerate(queue[:6]):
                        if not t == 0:
                            data = await QueueData(i)
                            queuelist.append(f"**{t}. [{data[0]}]({data[1]})**")
                    if len(queue) > 6:
                        queuelist.append(f"**Còn {len(queue) - 6} bài nữa**")
                    if len(queuelist) == 0:
                        queuelist = ""
                    else:
                        queuelist = "\n"+"\n".join(queuelist)
                    data = await QueueData(queue[0])
                    loop_mode = get_music_loop_text(ctx.guild.id)
                    embed = discord.Embed(title="Queue", description=f"**Loop mode: {loop_mode}**\n**Đang play: [{data[0]}]({data[1]})**{queuelist}")
                    await edit.edit(embed=embed)
                else:
                    await ctx.reply("**Bạn không ở chung voice với bot**")
            else:
                await ctx.reply("**Bot Đang chả play gì cả**")
        else:
            await ctx.reply("**Bạn chưa vào voice**")
    
    @app_commands.command(name="player_control", description="mở music player control.")
    async def player(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        await ctx.send(view=Music_bt())
    
    @app_commands.command(name="nowplaying", description="Xem bàì đang play và bài tiếp theo.")
    async def nowplaying(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        if ctx.author.voice is not None:
            if ctx.voice_client is not None:
                if ctx.author.voice.channel == ctx.voice_client.channel:
                    listu = musisc_queue[str(ctx.guild.id)].queue()
                    loop_mode = get_music_loop_text(ctx.guild.id)
                    embed = discord.Embed(title="Now Playing", description=f"**Loop Mode:** {loop_mode}")
                    data = await QueueData(listu[0])
                    embed.add_field(name=f"Đang phát:",
                                    value=f"**[{data[0]}]({data[1]})**",
                                    inline=False)
                    try:
                        data = await QueueData(listu[1])
                        embed.add_field(name="Bài tiếp theo:",
                                        value=f"**[{data[0]}]({data[1]})**",
                                        inline=False)
                    except BaseException:
                        pass
                    await ctx.send(embed=embed)
                else:
                    await ctx.reply("**Bạn không ở chung voice với bot**")
            else:
                await ctx.reply("**Bot Đang chả play gì cả**")
        else:
            await ctx.reply("**Bạn chưa vào voice**")
          
    @app_commands.command(name="play", description="Play music")
    @app_commands.describe(url="tên or Link của bài hát")
    @app_commands.autocomplete(url=music_autocomplete)
    @app_commands.rename(url="input")
    async def play(self, interaction: discord.Interaction, url: str=None):
        ctx = await Interactx(interaction)
        if url is None:
            embed = discord.Embed(title="Play Command", description=f"**Support Url:**\nYoutube\nSoundcloud\nSpotify\nZingMp3\n**Search:**\nYoutube : default\nSoundcloud : `sc:<data>`\nSpotify : `sf:<data>`\n**How to Use:**\n`{get_prefix(ctx)}play <url or search>`")
            await ctx.send(embed=embed)
            
        if url is not None:
            if ctx.author.voice is not None:
                if (ctx.voice_client is None) and (ctx.guild.me.voice is None):
                    mess = await ctx.reply(f"**Đang Join Voice**")
                    try:
                        await ctx.author.voice.channel.connect()
                        try:
                            await ctx.guild.change_voice_state(channel=ctx.author.voice.channel, self_mute=False, self_deaf=True)
                        except BaseException:
                            pass
                        if ctx.author.voice.channel.type == discord.ChannelType.stage_voice:
                            try:
                                await ctx.guild.me.edit(suppress = False)
                            except BaseException:
                                pass
                    except BaseException:
                        pass
                    try:
                        await mess.edit(content=f"**Đang load link**")
                    except BaseException:
                        pass
                    queue = await self.load_audio(mess, url)
                    if queue is not None and (ctx.voice_client is not None):
                        ql = musisc_queue.get(str(ctx.guild.id))
                        if ql is None:
                            musisc_queue[str(ctx.guild.id)] = MusicQueue()
                        musisc_queue[str(ctx.guild.id)].add_queue(queue)
                        asyncio.create_task(self.skip_audio(ctx, mess))
                    else:
                        try:
                            await ctx.voice_client.disconnect(force=True)
                        except BaseException:
                            pass
                else:
                    if ctx.voice_client.channel == ctx.author.voice.channel:
                        mess = await ctx.reply(f"**Đang load link**")
                        nqueue = await self.load_audio(mess, url)
                        if nqueue is not None:
                            try:
                                await ctx.author.voice.channel.connect()
                                try:
                                    await ctx.guild.change_voice_state(channel=ctx.author.voice.channel, self_mute=False, self_deaf=True)
                                except BaseException:
                                    pass
                                if ctx.author.voice.channel.type == discord.ChannelType.stage_voice:
                                    try:
                                        await ctx.guild.me.edit(suppress = False)
                                    except BaseException:
                                        pass
                            except BaseException:
                                pass
                            ql = musisc_queue.get(str(ctx.guild.id))
                            if ql is None:
                                musisc_queue[str(ctx.guild.id)] = MusicQueue()
                            musisc_queue[str(ctx.guild.id)].add_queue(nqueue)
                    else:
                        await ctx.reply("**Bạn không ở chung voice với bot**")
            else:
                await ctx.reply("**Vào voice để dùng music bro**")

        
async def setup(bot):
    spotify = Spotify(
            ClientCredentialsFlow(
                client_id=os.getenv("SPOTIFY_ID"),
                client_secret=os.getenv("SPOTIFY_SECRER"),
            )
        )
    await bot.add_cog(Music(bot, spotify))