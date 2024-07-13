import os
import discord
import asyncio
import botemoji
import traceback
import zingmp3py
import unity.spotify as sp
import sclib.asyncio as sclib
from discord.ext import commands
from discord import app_commands
from songbird import SongBirdError
from unity.music_obj import QueueData
from unity.interactx import Interactx
from unity.global_ui import Input_Modal, Music_bt
from unity.music_client_obj import Voice_Client_Music


scclient = sclib.SoundcloudAPI()
zclient = zingmp3py.ZingMp3Async()
rspotify = sp.Spotify(os.getenv("MUISC_API_URL"), os.getenv("MUISC_API_AUTH"))


def get_music_loop(ctx):
    return ctx.voice_client.queue.loop


def set_music_loop(ctx, loop_mode):
    ctx.voice_client.queue.loop = loop_mode


def get_music_loop_text(ctx):
    loopid = get_music_loop(ctx)
    if loopid == 0:
        return "Off"
    elif loopid == 1:
        return "Track"
    elif loopid == 2:
        return "Queue"


def human_format(num):
    round_to = 1
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num = round(num / 1000.0, round_to)
    return "{:.{}f}{}".format(num, round_to, ["", "K", "M", "G", "T", "P"][magnitude])

class Music(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

        async def check_m(ctx):
            interaction = ctx.interaction
            if ctx.author.voice is None:
                return await ctx.reply("**Bạn chưa vào voice**", ephemeral=True)
            if ctx.voice_client is None:
                oldmess = interaction.message
                mess = await ctx.reply("**Bot Đang chả play gì cả**", ephemeral=True)
                await oldmess.edit(view=None)
                return mess
            if type(ctx.voice_client) is not Voice_Client_Music:
                return await ctx.reply(
                    "**Bot đang không chạy tác vụ chơi nhạc**", ephemeral=True
                )
            if ctx.author.voice.channel != ctx.voice_client.channel:
                return await ctx.reply(
                    "**Bạn không ở chung voice với bot**", ephemeral=True
                )

        @bot.ev.interaction(name=r"m\.skip")
        async def on_skip(interaction: discord.Interaction):
            ctx = await Interactx(interaction, start=False)
            if (await check_m(ctx)) is not None:
                return
            if ctx.voice_client.queue.loop == 1:
                await ctx.reply(
                    "**Skip không dùng được khi loop mode là Track**", ephemeral=True
                )
                return
            queue = ctx.voice_client.queue.queue()
            loop_mode = get_music_loop(ctx)
            if len(queue) > 1 or loop_mode > 0:
                if len(queue) > 1 and loop_mode == 0:
                    nextd = queue[1]
                elif loop_mode == 1:
                    nextd = queue[0]
                elif loop_mode == 2:
                    if len(queue) > 1:
                        nextd = queue[1]
                    else:
                        nextd = queue[0]
                text_loop_mode = get_music_loop_text(ctx)
                await ctx.voice_client.stop()
                embed = discord.Embed(
                    title="Skip",
                    description=f"**Loop mode:** {text_loop_mode}\n**Volume:** {ctx.voice_client.volume}%",
                )
                embed.add_field(
                    name="Đã skip:", value=f"**[{queue[0].title}]({queue[0].url})**", inline=False
                )
                embed.add_field(
                    name="Đang Play",
                    value=f"**[{nextd.title}]({nextd.url})**",
                    inline=False,
                )
                await ctx.reply(embed=embed, ephemeral=True)
                await self.update_status(interaction.message, ctx.voice_client.queue)
            elif len(queue) == 1:
                await ctx.voice_client.stop()
                await ctx.reply("**Hết queue rồi tôi thoát đây :>**", ephemeral=True)

        @bot.ev.interaction(name=r"m\.previous")
        async def on_previous(interaction: discord.Interaction):
            ctx = await Interactx(interaction, start=False)
            if (await check_m(ctx)) is not None:
                return
            if ctx.voice_client.queue.loop == 1:
                await ctx.reply(
                    "**Previous không dùng được khi loop mode là Track**",
                    ephemeral=True,
                )
                return
            nowp = ctx.voice_client.queue.now_playing()
            prev = ctx.voice_client.queue.prev()
            if prev is not None:
                text_loop_mode = get_music_loop_text(ctx)
                await ctx.voice_client.stop()
                embed = discord.Embed(
                    title="Previous",
                    description=f"**Loop mode:** {text_loop_mode}\n**Volume:** {ctx.voice_client.volume}%",
                )
                embed.add_field(
                    name="Đã previous:",
                    value=f"**[{prev.title}]({prev.url})**",
                    inline=False,
                )
                embed.add_field(
                    name="Đang Play",
                    value=f"**[{nowp.title}]({nowp.url})**",
                    inline=False,
                )
                await ctx.reply(embed=embed, ephemeral=True)
                await self.update_status(interaction.message, ctx.voice_client.queue)
            else:
                await ctx.reply("**Không có bài trước đấy :/**", ephemeral=True)

        @bot.ev.interaction(name=r"m\.resume|pause")
        async def on_pause(interaction: discord.Interaction):
            ctx = await Interactx(interaction, start=False)
            if (await check_m(ctx)) is not None:
                return
            if ctx.voice_client.is_paused():
                await ctx.voice_client.resume()
                await ctx.reply(f"**Đã tiếp tục nhạc {botemoji.yes}**", ephemeral=True)
            else:
                await ctx.voice_client.pause()
                await ctx.reply(f"**Đã tạm dừng nhạc {botemoji.yes}**", ephemeral=True)
            await self.update_status(interaction.message, ctx.voice_client.queue)

        @bot.ev.interaction(name=r"m\.shuffle")
        async def on_shuffle(interaction: discord.Interaction):
            ctx = await Interactx(interaction, start=False)
            if (await check_m(ctx)) is not None:
                return
            ctx.voice_client.queue.shuffle()
            embed = discord.Embed(title="Đã xáo trộn Queue")
            await ctx.send(embed=embed, ephemeral=True)
            await self.update_status(interaction.message, ctx.voice_client.queue)

        @bot.ev.interaction(name=r"m\.queue")
        async def on_queue(interaction: discord.Interaction):
            ctx = await Interactx(interaction, start=False)
            if (await check_m(ctx)) is not None:
                return
            await self.queue.callback(self, ctx)
            await self.update_status(interaction.message, ctx.voice_client.queue)

        @bot.ev.interaction(name=r"m\.reload")
        async def on_reload(interaction: discord.Interaction):
            ctx = await Interactx(interaction, start=False)
            if (await check_m(ctx)) is not None:
                return
            await interaction.response.defer()
            await self.update_status(interaction.message, ctx.voice_client.queue)

        @bot.ev.interaction(name=r"m\.loop")
        async def on_volume(interaction: discord.Interaction):
            ctx = await Interactx(interaction, start=False)
            if (await check_m(ctx)) is not None:
                return
            mode = interaction.data["values"][0]
            if mode.lower() == "off":
                set_music_loop(ctx, 0)
                embed = discord.Embed(title="Loop mode: Off")
            elif mode.lower() == "track":
                set_music_loop(ctx, 1)
                embed = discord.Embed(title="Loop mode: Track")
            elif mode.lower() == "queue":
                set_music_loop(ctx, 2)
                embed = discord.Embed(title="Loop mode: Queue")
            await ctx.reply(embed=embed, ephemeral=True)
            await self.update_status(interaction.message, ctx.voice_client.queue)

        @bot.ev.interaction(name=r"m\.volume_bt")
        async def on_volume_bt(interaction: discord.Interaction):
            ctx = await Interactx(interaction, start=False)
            if (await check_m(ctx)) is not None:
                return
            await interaction.response.send_modal(
                Input_Modal(
                    title="Set Volume (từ 0 -> 100)",
                    custom_id="m.volume_md",
                    custom_id_input="m.voice_ip",
                    label="Số phần trăm volume",
                    min_length=1,
                    max_length=3,
                )
            )

        @bot.ev.interaction(name=r"m\.volume_md")
        async def on_volume_md(interaction: discord.Interaction, data_input: dict):
            ctx = await Interactx(interaction, start=False)
            if (await check_m(ctx)) is not None:
                return
            dataout = data_input.get("m.voice_ip")
            try:
                data = int(dataout)
            except ValueError:
                return await ctx.reply("**Input không hợp lệ**", ephemeral=True)
            if not (0 <= data <= 100):
                return await ctx.reply(
                    "**Input cần trong khoảng 0 đến 100**", ephemeral=True
                )
            await ctx.guild.voice_client.set_volume(data)
            await ctx.reply(f"**Đã set {data}% volume**", ephemeral=True)
            await self.update_status(interaction.message, ctx.voice_client.queue)

    async def update_status(self, mess: discord.Message, audio_obj):
        audio = audio_obj.now_playing()
        embed = discord.Embed()
        if type(audio) is sclib.Track:
            embed.add_field(name="Likes", value=human_format(audio.raw.likes_count))
            embed.add_field(
                name="Playback Count", value=human_format(audio.raw.playback_count)
            )
        embed.title = "Đang Play:"
        embed.description = f"**[{audio.title}]({audio.url})**"
        embed.set_thumbnail(url=audio.artwork_url)
        nbt = Music_bt(audio_obj.loop)
        await mess.edit(view=nbt)
        emb = None if len(mess.embeds) == 0 else mess.embeds[0]
        if embed != emb:
            await mess.edit(embed=embed, view=nbt)

    async def check_m_command(self, ctx):
        if ctx.author.voice is None:
            return await ctx.reply("**Bạn chưa vào voice**")
        if ctx.voice_client is None:
            return await ctx.reply("**Bot Đang chả play gì cả**")
        if type(ctx.voice_client) is not Voice_Client_Music:
            return await ctx.reply("**Bot đang không chạy tác vụ chơi nhạc**")
        if ctx.author.voice.channel != ctx.voice_client.channel:
            return await ctx.reply("**Bạn không ở chung voice với bot**")

    async def music_autocomplete(self, interaction, current: str):
        current = current.strip()
        if current:
            if not (current.startswith("http://") or current.startswith("https://")):
                if current.lower().startswith("sc:"):
                    msg = current[3:]
                    data = await scclient.autocomplete(msg)
                    rdata = [
                        app_commands.Choice(name="sc:" + s, value="sc:" + s)
                        for s in data
                    ]
                    rdata.insert(0, app_commands.Choice(name=current, value=current))
                else:
                    rdata = []
                    rdata.insert(0, app_commands.Choice(name=current, value=current))
                return rdata
            else:
                return []
        else:
            return []

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
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
                        else:
                            try:
                                await member.guild.change_voice_state(
                                    channel=after.channel,
                                    self_mute=False,
                                    self_deaf=True,
                                )
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

    async def play_audio(self, ctx, queue_obj: QueueData, mess):
        try:
            embed = discord.Embed(title="**Đang Load Audio**")
            if mess is not None:
                try:
                    await mess.edit(embed=embed)
                except BaseException:
                    pass
            audio = queue_obj.raw
            embed = discord.Embed()
            audio_type = None
            if type(audio) is sclib.Track:
                embed.add_field(name="Likes", value=human_format(audio.likes_count))
                embed.add_field(
                    name="Playback Count", value=human_format(audio.playback_count)
                )
                URL = await audio.get_stream_url()
            elif type(audio) is zingmp3py.zasync.Song:
                list_has_checked = [
                    i for i in (await audio.getStreaming()) if not i.isVIP
                ]
                URL = list_has_checked[-1].url
            elif type(audio) is zingmp3py.LiveRadio:
                URL = audio.streaming_url
            elif type(audio) is sp.Track:
                if not audio.is_playable:
                    raise PermissionError("not playable")
                URL = f"{os.getenv('MUISC_AUDIO_URL')}/api/v1/sp/audio/{audio.spotify_uri}?api_key={os.getenv('MUISC_API_AUTH')}"
            elif type(audio) is sp.Episode:
                URL = f"{os.getenv('MUISC_AUDIO_URL')}/api/v1/sp/audio/{audio.spotify_uri}?api_key={os.getenv('MUISC_API_AUTH')}"
            await ctx.voice_client.play(
                URL, type=audio_type, after=lambda e: self.autoskip(e, ctx, mess)
            )
            embed.title = "Đang Play:"
            embed.description = f"**[{queue_obj.title}]({queue_obj.url})**"
            embed.set_thumbnail(url=queue_obj.artwork_url)
            if mess is not None:
                try:
                    await mess.edit(
                        embed=embed, view=Music_bt(ctx.voice_client.queue.loop)
                    )
                except BaseException:
                    traceback.print_exc()
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

    async def autoskip(self, e, ctx, mess):
        if e:
            if mess != None:
                try:
                    embed = discord.Embed(title="Skip bài này do lỗi")
                    await mess.edit(embed=embed)
                except BaseException:
                    pass
        asyncio.create_task(self.skip_audio(ctx), name=os.urandom(16).hex())

    async def skip_audio(self, ctx, mess=None):
        check = ctx.voice_client
        if check is not None:
            audio = next(ctx.voice_client.queue)
            if audio is not None:
                await self.play_audio(ctx, audio, mess)
            else:
                try:
                    await ctx.voice_client.disconnect(force=True)
                except BaseException:
                    pass
        else:
            try:
                await ctx.voice_client.disconnect(force=True)
            except BaseException:
                pass

    async def load_audio(self, mess, url):
        url = url.strip()
        queue = []
        types_mess = 1
        if (
            url.startswith("http://")
            or url.startswith("https://")
            or rspotify.is_spotify_uri(url)
        ):
            types_mess = 0
            if "spotify.com" in url or rspotify.is_spotify_uri(url):
                data = await rspotify.get_from_url(url)
                if data is not None:
                    rdata = data[0]
                    tdata = data[1]
                    if tdata == "track" or tdata == "episode":
                        queue.append(rdata)
                        try:
                            await mess.edit(content="**Đã add song vào queue**")
                        except BaseException:
                            pass
                    else:
                        rdata = [i for i in rdata if i is not None]
                        if tdata == "show":
                            rdata.reverse()
                        if rdata:
                            queue.extend(rdata)
                            try:
                                await mess.edit(
                                    content=f"**Đã add {len(rdata)} song vào queue**"
                                )
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
                            await mess.edit(
                                content=f"**Đã add {len(out.tracks)} Track vào queue**"
                            )
                        except BaseException:
                            pass
                    elif type(out) is sclib.USER:
                        queue.extend(out.tracks)
                        try:
                            await mess.edit(
                                content=f"**Đã add {len(out.tracks)} Track vào queue**"
                            )
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
                    if playlist is not None:
                        queue.extend(playlist.songs)
                        try:
                            await mess.edit(
                                content=f"**Đã add {len(playlist.songs)} song vào queue**"
                            )
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
            else:
                try:
                    await mess.edit(content="**Link không hợp lệ**")
                except BaseException:
                    pass
        elif url.lower().startswith("sc:"):
            msg = url[3:]
            try:
                out = (await scclient.search(msg, limit=1))[0]
            except BaseException:
                out = None
            if out is not None:
                if type(out) is sclib.Playlist:
                    queue.extend(out.tracks)
                    try:
                        await mess.edit(
                            content=f"**Đã add {len(out.tracks)} Track vào queue**"
                        )
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
        else:
            track = await rspotify.search(url)
            if track:
                queue.append(track)
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
        if await self.check_m_command(ctx):
            return
        try:
            await ctx.voice_client.disconnect(force=True)
        except BaseException:
            pass
        await ctx.send("**Đã dừng nhạc và thoát**")

    @app_commands.command(name="loop", description="Turn on/off loop mode")
    @app_commands.describe(mode="Mode loop")
    @app_commands.choices(
        mode=[
            app_commands.Choice(name="Off", value="off"),
            app_commands.Choice(name="Track", value="track"),
            app_commands.Choice(name="Queue", value="queue"),
        ]
    )
    async def loop(
        self, interaction: discord.Interaction, mode: app_commands.Choice[str]
    ):
        mode = mode.value
        ctx = await Interactx(interaction)
        if await self.check_m_command(ctx):
            return
        if mode.lower() == "off":
            set_music_loop(ctx, 0)
            embed = discord.Embed(title="Loop mode: Off")
        elif mode.lower() == "track":
            set_music_loop(ctx, 1)
            embed = discord.Embed(title="Loop mode: Track")
        elif mode.lower() == "queue":
            set_music_loop(ctx, 2)
            embed = discord.Embed(title="Loop mode: Queue")
        else:
            embed = discord.Embed(
                title="List Loop Mode", description="**`Track`, `Queue`, `Off`**"
            )
        await ctx.reply(embed=embed)

    @app_commands.command(name="volume", description="Set music volume")
    async def volume(
        self, interaction: discord.Interaction, volume: app_commands.Range[int, 0, 100]
    ):
        ctx = await Interactx(interaction)
        if await self.check_m_command(ctx):
            return
        await ctx.guild.voice_client.set_volume(volume)
        await ctx.reply(f"**Đã set {volume}% volume**")

    @app_commands.command(name="shuffle", description="Shuffle music queue")
    async def shuffle(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        if await self.check_m_command(ctx):
            return
        ctx.voice_client.queue.shuffle()
        await ctx.reply("**Đã xáo trộn queue**")

    @app_commands.command(name="skip", description="Skip music")
    async def skip(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        if await self.check_m_command(ctx):
            return
        if ctx.voice_client.queue.loop == 1:
            await ctx.reply("**Skip không dùng được khi loop mode là Track**")
            return
        queue = ctx.voice_client.queue.queue()
        loop_mode = get_music_loop(ctx)
        if len(queue) > 1 or loop_mode > 0:
            if len(queue) > 1 and loop_mode == 0:
                nextd = queue[1]
            elif loop_mode == 1:
                nextd = queue[0]
            elif loop_mode == 2:
                if len(queue) > 1:
                    nextd = queue[1]
                else:
                    nextd = queue[0]
            text_loop_mode = get_music_loop_text(ctx)
            embed = discord.Embed(
                title="Skip",
                description=f"**Loop mode:** {text_loop_mode}\n**Volume:** {ctx.voice_client.volume}%",
            )
            embed.add_field(
                name="Đã skip:", value=f"**[{queue[0].title}]({queue[0].url})**", inline=False
            )
            embed.add_field(
                name="Đang Play", value=f"**[{nextd.title}]({nextd.url})**", inline=False
            )
            await ctx.reply(embed=embed)
            await ctx.voice_client.stop()
        elif len(queue) == 1:
            await ctx.reply("**Hết queue rồi tôi thoát đây :>**")
            await ctx.voice_client.stop()

    @app_commands.command(name="previous", description="Play previous music")
    async def previous(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        if await self.check_m_command(ctx):
            return
        if ctx.voice_client.queue.loop == 1:
            await ctx.reply("**Previous không dùng được khi loop mode là Track**")
            return
        nowp = ctx.voice_client.queue.now_playing()
        prev = ctx.voice_client.queue.prev()
        if prev is not None:
            text_loop_mode = get_music_loop_text(ctx)
            embed = discord.Embed(
                title="Previous",
                description=f"**Loop mode:** {text_loop_mode}\n**Volume:** {ctx.voice_client.volume}%",
            )
            embed.add_field(
                name="Đã previous:", value=f"**[{nowp.title}]({nowp.url})**", inline=False
            )
            embed.add_field(
                name="Đang Play", value=f"**[{prev.title}]({prev.url})**", inline=False
            )
            await ctx.reply(embed=embed)
            await ctx.voice_client.stop()
        else:
            await ctx.reply("**Không có bài trước đấy :/**")

    @app_commands.command(name="pause", description="Pause music")
    async def pause(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        if await self.check_m_command(ctx):
            return
        await ctx.voice_client.pause()
        await ctx.reply(f"**Đã tạm dừng nhạc {botemoji.yes}**")

    @app_commands.command(name="resume", description="Resume music")
    async def resume(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        if await self.check_m_command(ctx):
            return
        await ctx.voice_client.resume()
        await ctx.reply(f"**Đã tiếp tục nhạc {botemoji.yes}**")

    @app_commands.command(name="queue", description="Queue music")
    async def queue(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        if await self.check_m_command(ctx):
            return
        embed = discord.Embed(title="Đang load queue")
        edit = await ctx.reply(embed=embed)
        queue = ctx.voice_client.queue.queue()
        queuelist = []
        for t, i in enumerate(queue[:6]):
            if not t == 0:
                queuelist.append(f"**{t}. [{i.title}]({i.url})**")
        if len(queue) > 6:
            queuelist.append(f"**Còn {len(queue) - 6} bài nữa**")
        if len(queuelist) == 0:
            queuelist = ""
        else:
            queuelist = "\n" + "\n".join(queuelist)
        loop_mode = get_music_loop_text(ctx)
        embed = discord.Embed(
            title="Queue",
            description=f"**Loop mode:** {loop_mode}\n**Volume:** {ctx.voice_client.volume}%\n**Đang play: [{queue[0].title}]({queue[0].url})**{queuelist}",
        )
        await edit.edit(embed=embed)

    @app_commands.command(
        name="nowplaying", description="Xem bàì đang play và bài tiếp theo."
    )
    async def nowplaying(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        if await self.check_m_command(ctx):
            return
        listu = ctx.voice_client.queue.queue()
        loop_mode = get_music_loop_text(ctx)
        embed = discord.Embed(
            title="Now Playing",
            description=f"**Loop Mode:** {loop_mode}\n**Volume:** {ctx.voice_client.volume}%",
        )
        embed.add_field(
            name="Đang phát:", value=f"**[{listu[0].title}]({listu[0].url})**", inline=False
        )
        try:
            embed.add_field(
                name="Bài tiếp theo:", value=f"**[{listu[1].title}]({listu[1].url})**", inline=False
            )
        except BaseException:
            pass
        await ctx.send(embed=embed)

    @app_commands.command(name="play", description="Play music")
    @app_commands.describe(url="tên or Link của bài hát")
    @app_commands.autocomplete(url=music_autocomplete)
    @app_commands.rename(url="input")
    async def play(self, interaction: discord.Interaction, url: str = None):
        ctx = await Interactx(interaction)
        if url is None:
            embed = discord.Embed(
                title="Play Command",
                description="**Support Url:**\nSoundcloud\nSpotify\nZingMp3\n**Search:**\nSpotify : default\nSoundcloud : `sc:<data>`\n**How to Use:**\n`/play <url or search>`",
            )
            await ctx.send(embed=embed)

        if url is not None:
            if ctx.author.voice is None:
                return await ctx.reply("**Vào voice để dùng music bro**")

            if (ctx.voice_client is None) and (ctx.guild.me.voice is None):
                mess = await ctx.reply("**Đang Join Voice**")
                try:
                    try:
                        await ctx.author.voice.channel.connect(cls=Voice_Client_Music)
                    except SongBirdError:
                        try:
                            await mess.edit(
                                content="**Tạm thời không thể chơi do không có Music Node online**"
                            )
                        except BaseException:
                            pass
                        return
                    try:
                        await ctx.guild.change_voice_state(
                            channel=ctx.author.voice.channel,
                            self_mute=False,
                            self_deaf=True,
                        )
                    except BaseException:
                        pass
                    if ctx.author.voice.channel.type == discord.ChannelType.stage_voice:
                        try:
                            await ctx.guild.me.edit(suppress=False)
                        except BaseException:
                            pass
                except BaseException:
                    traceback.print_exc()
                    pass
                try:
                    await mess.edit(content="**Đang load link**")
                except BaseException:
                    pass
                queue = await self.load_audio(mess, url)
                if queue is not None and (ctx.voice_client is not None):
                    ctx.voice_client.queue.add_queue(queue)
                    asyncio.create_task(self.skip_audio(ctx, mess))
                else:
                    try:
                        await ctx.voice_client.disconnect(force=True)
                    except BaseException:
                        pass
            else:
                if type(ctx.voice_client) is not Voice_Client_Music:
                    return await ctx.reply(
                        "**Bạn không thể chơi nhạc khi bot đang chạy tác vụ khác ở trong voice**"
                    )
                if ctx.voice_client.channel != ctx.author.voice.channel:
                    return await ctx.reply("**Bạn không ở chung voice với bot**")
                mess = await ctx.reply("**Đang load link**")
                nqueue = await self.load_audio(mess, url)
                if nqueue is None:
                    return
                try:
                    await ctx.author.voice.channel.connect(cls=Voice_Client_Music)
                    try:
                        await ctx.guild.change_voice_state(
                            channel=ctx.author.voice.channel,
                            self_mute=False,
                            self_deaf=True,
                        )
                    except BaseException:
                        pass
                    if ctx.author.voice.channel.type == discord.ChannelType.stage_voice:
                        try:
                            await ctx.guild.me.edit(suppress=False)
                        except BaseException:
                            pass
                except BaseException:
                    pass
                ctx.voice_client.queue.add_queue(nqueue)


async def setup(bot):
    await bot.add_cog(Music(bot))
