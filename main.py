import os
import io
import sys
import time
import uuid
import psutil
import aiohttp
import discord
import asyncio
import botemoji
import platform
import songbird
import traceback
import sentry_sdk
from jkeydb import database
import redis.asyncio as redis
from unity.event import Event
from datetime import datetime
from dotenv import load_dotenv
from unity.net import net_usage
from discord import app_commands
from unity.global_ui import delmessbt
from discord.ext import commands, tasks
from unity.interactx import Interactx, get_components
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.aiohttp import AioHttpIntegration

# sentry aiohttp trackback
sentry_sdk.init(
  dsn="https://e289c11088d34861b7334c77bc0eb233@o1329236.ingest.sentry.io/4504433436000256",
  integrations=[
     AioHttpIntegration(),
     RedisIntegration(),
  ],
  traces_sample_rate=1.0,
  trace_propagation_targets=[]
)

load_dotenv()

async def bot_prefix(bot, message):
    return uuid.uuid4().hex

shard = 3
intents = discord.Intents.default()
intents.members = True
bot = commands.AutoShardedBot(
    command_prefix=bot_prefix, intents=intents, shard_count=shard , help_command=None)
bot.db = redis.Redis(host='localhost', port=6379, db=0, password=os.getenv("REDIS_PASS"), username="default")
bot.ev = Event()
bot.voice_manager = songbird.NodeManager()
startdate = datetime.now()

@bot.tree.command(name="server", description="Hiển thị thông tin server.")
async def server(interaction: discord.Interaction):
    ctx = await Interactx(interaction)
    owner = ctx.guild.owner.mention
    member_count = ctx.guild.member_count
    bots = len([m for m in ctx.guild.members if m.bot])
    users = member_count - bots
    server_created = int(ctx.guild.created_at.timestamp())
    str_server_created = f"<t:{server_created}:d><t:{server_created}:T>\n(<t:{server_created}:R>)"
    emoji_count = len(ctx.guild.emojis)
    str_emoji_count = f"{emoji_count}/{ctx.guild.emoji_limit}"
    sticker = len(ctx.guild.stickers)
    str_sticker = f"{sticker}/{ctx.guild.sticker_limit}"
    boost = ctx.guild.premium_subscription_count
    description = ctx.guild.description or "No description"
    embed = discord.Embed(title=f"{ctx.guild.name}", description=f"**Owner:** {owner}\n**Description:** \n{description}\n**Member:** {member_count}\n**Bot:** {bots}\n**User:** {users}\n**Emoji:** {str_emoji_count}\n**Sticker:** {str_sticker}\n**Boost:** {boost}\n**Server Created:**\n{str_server_created}")
    if ctx.guild.icon is not None:
        embed.set_thumbnail(url=ctx.guild.icon.url.replace("webp", "png"))
    if ctx.guild.banner is not None:
        embed.set_image(url=ctx.guild.banner.url.replace("webp", "png"))
    await ctx.send(embed=embed)

@bot.tree.command(name="info", description="Hiển thị thông tin của bot.")
async def info(interaction: discord.Interaction):
  ctx = await Interactx(interaction)
  embed = discord.Embed(title=f"Đang load info Bot")
  load = await ctx.reply(embed=embed)
  shard_id = ctx.guild.shard_id
  shard = bot.get_shard(shard_id)
  shard_ping = shard.latency
  uptime_date_obj = int(startdate.timestamp())
  uptime = f"<t:{uptime_date_obj}:d><t:{uptime_date_obj}:T>\n(<t:{uptime_date_obj}:R>)"
  embed = discord.Embed(
    title=f"Info",
    description=
    f"**Made by Fantasy Team**\n**Info :**\n> **Discord.py :** {discord.__version__}\n> **Python :** {platform.python_version()}\n> **OS : **{platform.system()}\n**Shard Status**\n> **Shard Online :** {len([i for i in bot.shards.values() if not i.is_closed()])}/{len(bot.shards)} \n> **Guilds Shard Ping : **{round(shard_ping * 1000)} ms\n> **Guilds Shard ID : **{shard_id + 1}\n**Bot Status**\n> **Uptime : **{uptime}\n> **Avg ping :** {round(bot.latency * 1000)} ms\n> **Voice connect : **{len(bot.voice_clients)} Channels\n> **Guilds : **{int(len(bot.guilds))} Guilds\n> **Member : **{int(len(bot.users))} Member\n**Bot process data**\n> **CPU :  **{str(round(psutil.cpu_percent(),1))}% \n> **RAM : **{str(round(psutil.virtual_memory().percent,1))}%\n> {await net_usage()}")
  view = discord.ui.View(timeout=0)
  view.add_item(discord.ui.Button(label="Invite Bot",
                      url=discord.utils.oauth_url(bot.user.id, permissions=discord.Permissions.all())))
  await load.edit(embed=embed, view=view)
  
@bot.tree.command(name="avatar", description="Hiển thị avatar của bạn hoặc người khác")
@app_commands.describe(user="Người dùng cần hiển thị thông tin.")
async def avatar(interaction: discord.Interaction, user: discord.User = None):
    ctx = await Interactx(interaction)
    if user is None:
        user = ctx.author
    embed = discord.Embed(title=f"{user} avatar")
    embed.set_image(url=user.display_avatar.url.replace("webp", "png"))
    joind = "Đã tham gia" if ctx.guild.get_member(
        user.id) is not None else "Chưa tham gia"
    embed.set_footer(text=f"User ID: {user.id}\n{joind} server.")
    await ctx.send(embed=embed)

@bot.tree.context_menu(name="Get Author Avatar")
async def avatar_ms(interaction: discord.Interaction, message: discord.Message):
    ctx = await Interactx(interaction, ephemeral=True)
    await avatar.callback(ctx, user=message.author)

@bot.tree.context_menu(name="Get User Avatar")
async def avatar_us(interaction: discord.Interaction, use: discord.Member):
    ctx = await Interactx(interaction, ephemeral=True)
    await avatar.callback(ctx, user=use)


@bot.tree.command(name="user", description="Hiển thị thông tin người dùng.")
@app_commands.describe(user="Người dùng cần hiển thị thông tin.")
async def user(interaction: discord.Interaction, user: discord.User = None):
    ctx = await Interactx(interaction)
    embed = discord.Embed(title=f'Đang Load User')
    load = await ctx.send(embed=embed)
    if user is None:
        user = ctx.author
    created = int(user.created_at.timestamp())
    created = f"<t:{created}:d> <t:{created}:T>\n(<t:{created}:R>)"
    joined = "Chưa tham gia server"
    nick = ""
    if ctx.guild.get_member(user.id) is not None:
        member = ctx.guild.get_member(user.id)
        joined = int(member.joined_at.timestamp())
        joined = f"<t:{joined}:d> <t:{joined}:T>\n(<t:{joined}:R>)"
        if member.nick is not None:
            nick = f"**Nickname:**\n{member.nick}\n"
    user_badges = []
    for k, _ in user.public_flags.all():
        emoji = getattr(botemoji, "flag_"+k, None)
        if emoji is None:
            continue
        name_str = k.replace("_", " ").title()
        user_badges.append(f"{emoji} {name_str}")
    if len(user_badges) != 0:
        str_user_badges = "\n**Badges:**\n"+"\n".join(user_badges)
    else:
        str_user_badges = ""
    buser = await bot.fetch_user(user.id)
    banner = "\n**User Banner:**" if buser.banner is not None else ""
    isbot = botemoji.yes if user.bot else botemoji.no
    isspammer = botemoji.yes if user.public_flags.spammer else botemoji.no
    global_name = "**Tên hiển thị: **\n"+user.global_name+"\n" if user.global_name is not None else ""
    embed = discord.Embed(
        title=f'{user}', description=f"{nick}{global_name}**Thời gian lập acc :**\n{created}\n**Thời gian join server :**\n{joined}\n**User ID: **\n{user.id}{str_user_badges}\n**Spammer:** {isspammer}\n**Bot:** {isbot}{banner}")
    embed.set_thumbnail(url=user.display_avatar.url.replace(".webp", ".png"))
    if buser.banner is not None:
        embed.set_image(url=buser.banner.url.replace(".webp", ".png"))
    await load.edit(embed=embed)
    
@bot.tree.context_menu(name="Get Author Info")
async def user_ms(interaction: discord.Interaction, message: discord.Message):
    ctx = await Interactx(interaction, ephemeral=True)
    await user.callback(ctx, user=message.author)

@bot.tree.context_menu(name="Get User Info")
async def user_us(interaction: discord.Interaction, use: discord.Member):
    ctx = await Interactx(interaction, ephemeral=True)
    await user.callback(ctx, user=use)

@bot.tree.command(name="afk", description="Đặt trạng thái AFK để hiển thị khi bạn được đề cập.")
@app_commands.describe(rest="tin nhắn AFK")
@app_commands.rename(rest="message")
async def afk(interaction: discord.Interaction, rest: str = "AFK"):
    ctx = await Interactx(interaction)
    if ctx.author.nick is None:
        try:
            await ctx.author.edit(nick=(ctx.author.global_name or ctx.author.name) + " [AFK]")
        except BaseException:
            pass
    elif " [AFK]" not in ctx.author.nick:
        try:
            await ctx.author.edit(nick=ctx.author.nick + " [AFK]")
        except BaseException:
            pass
    async with database(f"./data/afk/{ctx.guild.id}", bot.db) as db:
        old_afk = await db.get("afklist")
        if old_afk is None:
            await db.set("afklist", [ctx.author.id])
        else:
            await db.set("afklist", old_afk.append(ctx.author.id))
        await db.set(str(ctx.author.id), {"reason": rest, "time": int(time.time())})
    mallow = discord.AllowedMentions(everyone=False, users=False, roles=False, replied_user=True)
    await ctx.reply(f"**{ctx.author.mention} đã đặt afk là :** {rest}", allowed_mentions=mallow)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.guild is None:
        return

    if message.content == f"<@{bot.user.id}>" or message.content == f"<@!{bot.user.id}>":
        await message.reply(f'**Hi tôi là {bot.user.mention} xin hay dùng `/fantasy` để xem hết commands của tôi nhé 😊**')
    

    async with database(f"./data/afk/{message.guild.id}", bot.db) as db:
        data = await db.get("afklist", [])
        if data is not None:
            if message.author.id in data:
                data.remove(message.author.id)
                if data:
                    await db.set("afklist", data) 
                else:
                    await db.remove("afklist")
                await db.remove(str(message.author.id))
                if message.author.nick is not None:
                    check = message.author.nick.replace(" [AFK]", "")
                    if check == (message.author.global_name or message.author.name):
                        try:
                            await message.author.edit(nick=None)
                        except BaseException:
                            pass
                    else:
                        try:
                            await message.author.edit(nick=check)
                        except BaseException:
                            pass
                await message.reply(f'**Chào mừng quay trở lại {message.author.mention} . Tôi đã bỏ AFK cho bạn rồi đó.**', delete_after=10)
        if not (await db.get("afklist")):
            await bot.db.delete(f"./data/afk/{message.guild.id}")

    if message.mentions:
        async with database(f"./data/afk/{message.guild.id}", bot.db) as db:
            data = await db.get("afklist", [])
            for user in message.mentions:
                if user.id in data:
                    user_afk_data = await db.get(str(user.id))
                    reason = user_afk_data["reason"]
                    since = user_afk_data["time"]
                    mallow = discord.AllowedMentions(
                        everyone=False, users=False, roles=False, replied_user=True)
                    await message.reply(f"**{user.mention} đang AFK với lý do :** {reason} **- <t:{since}:R>**", allowed_mentions=mallow, delete_after=10)

@bot.tree.context_menu(name="Delete Bot Message")
async def delbotmess(interaction: discord.Interaction, message: discord.Message):
    if message.interaction is not None:
        if message.author == bot.user:
            await message.delete()
            await interaction.response.send_message(content="**Bot Message Deleted**", delete_after=10)
        else:
            await interaction.response.send_message(content="**This message was not sent by me.**", ephemeral=True)
    else:
        await interaction.response.send_message(content="**This message was not sent by me.**", ephemeral=True)



@bot.event
async def on_member_remove(member: discord.Member):
    async with database(f"./data/afk/{member.guild.id}", bot.db) as db:
        data = await db.get("afklist")
        if data is not None:
            if member.id in data:
                data.remove(member.id)
                await db.set("afklist", data)
                await db.remove(str(member.id))
    try:
        async with database(f"./data/level/{member.guild.id}", bot.db) as db:
            await db.remove(str(member.id))
    except BaseException:
        pass


@bot.event
async def on_guild_remove(guild: discord.Guild):
    keys = ["afk", "level", "setting", "tempvoice", "voicehub"]
    for i in keys:
        await bot.db.delete(f"./data/{i}/{guild.id}")

@bot.event
async def setup_hook():
    len_cogs = []
    async def add_c(i):
        try:
            await bot.load_extension(f'cogs.{i[:-3]}')
            print(f'Loaded {i}')
        except Exception:
            print(f'------- Cogs Err {i} -------')
            traceback.print_exc()
            print(f'------- Cogs Err {i} End -------')
            len_cogs.append(i)
    task_add = [add_c(i) for i in os.listdir('./cogs') if i.endswith('.py')]
    await asyncio.gather(*task_add)
    print("Loading cogs done: ", len(task_add)-len(len_cogs), "/", len(task_add))
    try:
        if len(len_cogs) == 0:
            await bot.tree.sync()
            print("sync slash command done")
        else:
            print("Cogs err: ", ", ".join(len_cogs))
            print("Sync slash command skip")
    except Exception:
        traceback.print_exc()
    list_nodes = [
                    ["http://localhost:1999", os.getenv('MUISC_PLAYER_AUTH')]
                ]
    await bot.voice_manager.add_nodes(*list_nodes)
    print("Voice manager loading done")
    
@bot.event
async def on_ready():
    print(f'login as {bot.user}')
    try:
        status_c.start()
        print("status task was created")
    except BaseException:
        pass
    try:
        topgg_post.start()
        print("topgg post task was created")
    except BaseException:
        pass


@bot.event
async def on_shard_connect(shard_id):
    await bot.change_presence(status=discord.Status.dnd, shard_id=shard_id)

@bot.event
async def on_error(event, *args, **kwargs):
    traceback.print_exc()

@bot.tree.error
async def on_error_tree(interaction: discord.Interaction, error):
    bugid = os.urandom(16).hex()
    user = f"{interaction.user} ({interaction.user.id})"
    channel = f"{interaction.channel.name} ({interaction.channel.id})" if interaction.channel is not None else "DMs"
    guild = f"{interaction.guild.name} ({interaction.guild.id})" if interaction.guild is not None else "DMs"
    a = traceback.format_exception(type(error), error, error.__traceback__)
    out = "".join(a)
    view = discord.ui.View(timeout=0)
    view.add_item(delmessbt(interaction.user.id))
    try:
        embed = discord.Embed(title="Bug Report", description="Có lỗi xảy ra khi xử lý lệnh của bạn. Nó có thể không được thực hiện chính xác.\nĐể hỗ trợ và báo cáo về vấn đề này:\nhttps://discord.gg/5meeJDbmUG")
        await interaction.user.send(content=f"**Bug ID:** {bugid}", embed=embed, view=view)
    except BaseException:
        pass
    try:
        embed = discord.Embed(description=f"**Bug ID:** {bugid}\n**Author :** {user}\n**Channel :** {channel}\n**Guild :** {guild}\n**Error :** ```py\n{out}```")
        await bot.get_channel(933981853159923752).send(embed=embed)
    except discord.HTTPException:
        embed = discord.Embed(description=f"**Bug ID:** {bugid}\n**Author :** {user}\n**Channel :** {channel}\n**Guild :** {guild}\n**Error :** check output file")
        outf = io.BytesIO(out.encode("utf8"))
        file = discord.File(fp=outf, filename="log.py")
        await bot.get_channel(933981853159923752).send(embed=embed, file=file)
    with sentry_sdk.push_scope() as scope:
        scope.set_extra("Bug ID", bugid)
        scope.user = { "username": str(interaction.user), "id": str(interaction.user.id) }
        scope.set_extra("Channel", channel)
        scope.set_extra("Guild", guild)
        sentry_sdk.capture_exception(error)
    sys.stderr.write(out)
        

@bot.ev.interaction(name=r"delmess\.(\d+)")
async def on_delmess(interaction: discord.Interaction, user_id):
    if user_id == str(interaction.user.id):
        await interaction.response.pong()
        await interaction.message.delete()
    else:
        await interaction.response.send_message(f'**Nút này không dành cho bạn**', ephemeral=True)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component or interaction.type == discord.InteractionType.modal_submit:
        components = get_components(interaction)
        out = await bot.ev.trigger(interaction.data["custom_id"], interaction, components)
        bt = bool(not interaction.data["custom_id"] in list(bot._connection._view_store._modals.keys()))
        md = bool(not interaction.data["custom_id"] in [e[1] for i in bot._connection._view_store._views.values() for e in i.keys()])
        if (bt and md) and (not out):
            await interaction.response.send_message("**Timeout**", ephemeral=True)

async def interaction_check(interaction: discord.Interaction):
    if interaction.type is not discord.InteractionType.application_command:
        return True
    elif interaction.guild is None:
        await interaction.response.send_message("**All command can only be used in servers.**", ephemeral=True)
        return False
    elif type(interaction.user) is discord.User:
        view = discord.ui.View(timeout=0)
        view.add_item(discord.ui.Button(label="Invite Bot", url=discord.utils.oauth_url(bot.user.id, permissions=discord.Permissions.all())))
        await interaction.response.send_message("**Please use reinvite bot to use this command.**", view=view, ephemeral=True)
        return False
    else:
        return True 

bot.tree.interaction_check = interaction_check

@tasks.loop(seconds=60)
async def topgg_post():
    data = {"server_count": len(bot.guilds), "shard_count": len(bot.shards)}
    headers = {"Authorization": os.getenv("TOPGG_TOKEN")}
    async with aiohttp.ClientSession() as s:
        async with s.post(f"https://top.gg/api/bots/{bot.user.id}/stats", json=data, headers=headers) as r:
            if r.status == 429:
                outdata = await r.json()
                await asyncio.sleep(outdata["retry-after"])
            

@tasks.loop(seconds=10)
async def status_c():
    for i, _ in bot.shards.items():
        await bot.change_presence(shard_id=i, activity=discord.Activity(type=discord.ActivityType.playing, name=f"Shard {i+1} | fantasybot.xyz"))
    await asyncio.sleep(10)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(bot.guilds)} Guilds"))
    await asyncio.sleep(10)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{len(bot.users)} Users"))
    await asyncio.sleep(10)

if __name__ == "__main__":
    bot.run(os.getenv('TOKEN'), reconnect=True)
