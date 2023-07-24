import os
import io
import time
import traceback
import aiohttp
import discord
import redis
import asyncio
import botemoji
import psutil
import uuid
import platform
import sentry_sdk
from unity.event import Event
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from datetime import datetime
from unity.net import net_usage
from unity.global_ui import delmessbt
from unity.interactx import Interactx, ratelimit_check
from discord import app_commands
from jkeydb import database
from unity.capcha import generate_captcha_image, generate_captcha_text
from discord.ext import commands, tasks
from dotenv import load_dotenv

# sentry aiohttp trackback
sentry_sdk.init(
  dsn="https://e289c11088d34861b7334c77bc0eb233@o1329236.ingest.sentry.io/4504433436000256",
  integrations=[
     AioHttpIntegration(),
  ],
  traces_sample_rate=1.0,
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
  delta_uptime = datetime.now() - startdate
  hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
  minutes, seconds = divmod(remainder, 60)
  days, hours = divmod(hours, 24)
  uptime = f"{hours} Hours, {minutes} Minutes, {seconds} Seconds"
  embed = discord.Embed(
    title=f"Info",
    description=
    f"**Made by Fantasy Team**\n**Info :**\n> **Discord.py :** {discord.__version__}\n> **Python :** {platform.python_version()}\n> **OS : **{platform.system()}\n**Shard Status**\n> **Shard Online :** {int(len(bot.shards))}/{int(len(bot.shards))} \n> **Guilds Shard Ping : **{round(shard_ping * 1000)} ms\n> **Guilds Shard ID : **{shard_id + 1}\n**Bot Status**\n> **Uptime : **{uptime}\n> **Avg ping :** {round(bot.latency * 1000)} ms\n> **Voice connect : **{len(bot.voice_clients)} Channels\n> **Guilds : **{int(len(bot.guilds))} Guilds\n> **Member : **{int(len(bot.users))} Member\n**Bot process data**\n> **CPU :  **{str(round(psutil.cpu_percent(),1))}% \n> **RAM : **{str(round(psutil.virtual_memory().percent,1))}%\n> {await net_usage()}")
  view = discord.ui.View(timeout=0)
  view.add_item(discord.ui.Button(label="Invite Bot",
                      url=discord.utils.oauth_url(931353470353674291, permissions=discord.Permissions.all())))
  await load.edit(embed=embed, view=view)
  
@bot.tree.command(name="avatar", description="Hiển thị avatar của bạn hoặc người khác")
@app_commands.describe(user="Người dùng cần hiển thị thông tin.")
async def avatar(interaction: discord.Interaction, user: discord.User = None):
    ctx = await Interactx(interaction)
    if user is None:
        user = ctx.author
    embed = discord.Embed(title=f"{user} avatar", color=0x00ff00)
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
    embed = discord.Embed(title=f'Đang Load User', color=0x00ff00)
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
    user_raw_badges = user.public_flags
    if user_raw_badges.bug_hunter:
        user_badges.append(f"{botemoji.bug_hunter} Bug Hunter")
    if user_raw_badges.verified_bot:
        user_badges.append(f"{botemoji.verified_bot} Verified Bot")
    if user_raw_badges.partner:
        user_badges.append(f"{botemoji.discord_partner} Partner")
    if user_raw_badges.bug_hunter_level_2:
        user_badges.append(f"{botemoji.bug_hunter_lvl2} Bug Hunter Level 2")
    if user_raw_badges.discord_certified_moderator:
        user_badges.append(
            f"{botemoji.badge_moderator} Discord Certified Moderator")
    if user_raw_badges.early_supporter:
        user_badges.append(f"{botemoji.early_supporter} Early Supporter")
    if user_raw_badges.early_verified_bot_developer:
        user_badges.append(
            f"{botemoji.developer_bot_verified} Verified Bot Developer")
    if user_raw_badges.staff:
        user_badges.append(f"{botemoji.discord_employee} Staff")
    if user_raw_badges.hypesquad:
        user_badges.append(f"{botemoji.discord_hypesquad} Hypesquad")
    if user_raw_badges.hypesquad_balance:
        user_badges.append(f"{botemoji.discord_balance} Hypesquad Balance")
    if user_raw_badges.hypesquad_brilliance:
        user_badges.append(
            f"{botemoji.discord_brillance} Hypesquad Brilliance")
    if user_raw_badges.hypesquad_bravery:
        user_badges.append(f"{botemoji.discord_bravery} Hypesquad Bravery")
    if user_raw_badges.system:
        user_badges.append(f"{botemoji.system} System")
    if user_raw_badges.active_developer:
        user_badges.append(f"{botemoji.active_developer} Active Developer")
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
        title=f'{user}', description=f"{nick}{global_name}**Thời gian lập acc :**\n{created}\n**Thời gian join server :**\n{joined}\n**User ID: **\n{user.id}{str_user_badges}\n**Spammer:**{isspammer}\n**Bot:** {isbot}{banner}")
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
    with database(f"./data/afk/{ctx.guild.id}", bot.db) as db:
        old_afk = db.get("afklist")
        if old_afk is None:
            db["afklist"] = [ctx.author.id]
        else:
            db["afklist"] = old_afk.append(ctx.author.id)
        db[str(ctx.author.id)] = {"reason": rest, "time": int(time.time())}
    mallow = discord.AllowedMentions(
        everyone=False, users=False, roles=False, replied_user=True)
    await ctx.reply(f"**{ctx.author.mention} đã đặt afk là :** {rest}", allowed_mentions=mallow)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.guild is None:
        return

    if message.content == f"<@{bot.user.id}>" or message.content == f"<@!{bot.user.id}>":
        await message.reply(f'**Hi tôi là {bot.user.mention} xin hay dùng `/` để dùng commands của tôi nhé nhé 😊**')
    

    with database(f"./data/afk/{message.guild.id}", bot.db) as db:
        data = db.get("afklist", [])
        if data is not None:
            if message.author.id in data:
                db["afklist"] = data.remove(message.author.id)
                if db["afklist"]:
                    del db["afklist"]
                del db[str(message.author.id)]
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
        if not db.get("afklist"):
            bot.db.delete(f"./data/afk/{message.guild.id}")

    if message.mentions:
        with database(f"./data/afk/{message.guild.id}", bot.db) as db:
            data = db.get("afklist", [])
            for user in message.mentions:
                if user.id in data:
                    user_afk_data = db[str(user.id)]
                    reason = user_afk_data["reason"]
                    since = user_afk_data["time"]
                    mallow = discord.AllowedMentions(
                        everyone=False, users=False, roles=False, replied_user=True)
                    await message.reply(f"**{user.mention} đang AFK với lý do :** {reason} **- <t:{since}:R>**", allowed_mentions=mallow, delete_after=10)

@bot.tree.context_menu(name="Delete Bot Message")
async def delbotmess(interaction: discord.Interaction, message: discord.Message):
    if message.interaction is not None:
        if (message.interaction.user == interaction.user) and (message.author == bot.user):
            await message.delete()
            await interaction.response.send_message(content="**Bot Message Deleted**", ephemeral=True)
        else:
            await interaction.response.send_message(content="**This message was not commanded by you.**", ephemeral=True)
    else:
        await interaction.response.send_message(content="**This message was not sent by me.**", ephemeral=True)

async def cogs_autocomplete(interaction: discord.Interaction, current: str):
    if interaction.user.id != 542602170080428063:
        return []
    return [app_commands.Choice(name=fruit[:-3], value=fruit[:-3]) for fruit in os.listdir('./cogs') if current.lower() in fruit.lower() and fruit.endswith(".py")] 

@bot.tree.command(name="admin_cogs")
@app_commands.choices(ad=[
    app_commands.Choice(name='Add', value="+"),
    app_commands.Choice(name='Reload', value="r"),
    app_commands.Choice(name='remove', value="-")])
@app_commands.autocomplete(eten=cogs_autocomplete)
async def cogs(interaction: discord.Interaction, ad:app_commands.Choice[str], eten:str):
    if interaction.user.id != 542602170080428063:
        return
    ctx = await Interactx(interaction, ephemeral=True)
    ad = ad.value
    if ad == "+":
      try:
        await bot.load_extension(f'cogs.{eten}')
        await ctx.send(f"Đã add Cogs {eten}")
      except Exception:
        await ctx.send(f"```py\n{traceback.format_exc()}\n```")

    if ad == "r":
      try:
        await bot.reload_extension(f'cogs.{eten}')
        await ctx.send(f"Đã reload Cogs {eten}")
      except Exception:
        await ctx.send(f"```py\n{traceback.format_exc()}\n```")

    if ad == "-":
      try:
        await bot.unload_extension(f'cogs.{eten}')
        await ctx.send(f"Cogs {eten} đã bị remove")
      except Exception:
        await ctx.send(f"```py\n{traceback.format_exc()}\n```")

@bot.event
async def on_member_remove(member: discord.Member):
    try:
        with database(f"./data/afk/{member.guild.id}", bot.db, True) as db:
            data = db["afklist"]
            if data is not None:
                if member.id in data:
                    db["afklist"] = data.remove(member.id)
                    del db[str(member.id)]
            if db["afklist"] is None:
                bot.db.delete(f"./data/afk/{member.guild.id}")
    except BaseException:
        pass
    try:
        with database(f"./data/level/{member.guild.id}", bot.db, True) as db:
            del db[str(member.id)]
    except BaseException:
        pass


@bot.event
async def on_guild_remove(guild: discord.Guild):
    keys = ["afk", "level", "setting", "tempvoice", "voicehub"]
    for i in keys:
        if bot.db.exists(f"./data/{i}/{guild.id}") == 1:
            bot.db.delete(f"./data/{i}/{guild.id}")

@bot.event
async def setup_hook():
    async def add_c(i):
        try:
            await bot.load_extension(f'cogs.{i[:-3]}')
            print(f'Loaded {i}')
        except Exception:
            traceback.print_exc()
    await asyncio.gather(*[add_c(i) for i in os.listdir('./cogs') if i.endswith('.py')])
    try:
        await bot.tree.sync()
        print("sync slash command done")
    except Exception:
        traceback.print_exc()
    
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

class Reply_Capcha(discord.ui.Modal):
    reply = discord.ui.TextInput(
        label='Capcha Code',
        max_length=6,
        min_length=6,
        style=discord.TextStyle.short
    )
    
    def __init__(self, code, def_f):
        super().__init__(title='Enter Capcha code', timeout=300)
        self.code = code
        self.def_f = def_f

    async def on_submit(self, interaction: discord.Interaction):
        if self.code == str(self.reply).upper():
            await self.def_f
            await interaction.response.edit_message(content="**Mã capcha hợp lệ giờ bạn có thể dùng bot tiếp rồi**", attachments=[], embed=None, view=None)
        else:
            await interaction.response.send_message("**Mã capcha không hợp lệ**", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)
        traceback.print_exception(type(error), error, error.__traceback__)

class Capcha_BT(discord.ui.View):
        def __init__(self, code, def_f):
            super().__init__(timeout=300)
            self.code = code
            self.def_f = def_f

        @discord.ui.button(style=discord.ButtonStyle.gray, label="Enter Capcha Code")
        async def start(self, interaction: discord.Interaction,  button: discord.ui.Button):
            await interaction.response.send_modal(Reply_Capcha(self.code, self.def_f))    

async def interaction_check(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.application_command:
        if await ratelimit_check(interaction):
            await interaction.response.defer(ephemeral=True, thinking=True)
            async def capcha_valid():
                with database(f"./data/ratelimit", bot.db) as db:
                    if db.get(str(interaction.user.id)):
                        del db[str(interaction.user.id)]
            embed = discord.Embed(title="Bạn đang bị rate limit vui lòng nhập capcha", description="- Vui lòng nhập dòng chữ màu 🔴 (Đỏ)\n- Không quan tâm là mã capcha là viết HOA hay thường\n- Mã sẽ có hiệu lực trong 5p sau 5p vui lòng chạy lại lệnh để làm capcha\n- Gõ các ký tự được tô màu 🔴 (Đỏ) từ trái sang phải.")
            embed.set_image(url="attachment://image.png")
            capcha_code = generate_captcha_text()
            file_byte = await generate_captcha_image(capcha_code)
            view = Capcha_BT(capcha_code, capcha_valid())
            out = await interaction.followup.send(file=discord.File(io.BytesIO(file_byte), "image.png"), view=view, embed=embed, ephemeral=True)
            await view.wait()
            with database(f"./data/ratelimit", bot.db) as db:
                if db.get(str(interaction.user.id)):
                    try:
                        await out.edit("Hết thời gian", attachments=[], view=None)
                    except BaseException:
                        pass
            return False
    return True

setattr(bot.tree, "interaction_check", interaction_check)

@bot.tree.error
async def on_error_tree(interaction: discord.Interaction, error):
        error = error.original
        bugid = os.urandom(16).hex()
        a = traceback.format_exception(type(error), error, error.__traceback__)
        out = "".join(a)
        view = discord.ui.View(timeout=0)
        view.add_item(delmessbt(interaction.user.id))
        try:
            embed = discord.Embed(title="Bug Report", description="Có lỗi xảy ra khi xử lý lệnh của bạn. Nó có thể không được thực hiện chính xác.\nĐể hỗ trợ và báo cáo về vấn đề này:\nhttps://discord.gg/5meeJDbmUG")
            embed.add_field(name="Bug ID", value=bugid)
            await interaction.user.send(embed=embed, view=view)
        except BaseException:
            pass
        try:
            embed = discord.Embed(description=f"**Bug ID:** {bugid}\n**Author :** {interaction.user} ({interaction.user.id})\n**Channel :** {interaction.channel.name} ({interaction.channel.id})\n**Guild :** {interaction.guild.name} ({interaction.guild.id})\n**Error :** ```py\n{out}```")
            await bot.get_channel(933981853159923752).send(embed=embed)
        except discord.HTTPException:
            embed = discord.Embed(description=f"**Bug ID:** {bugid}\n**Author :** {interaction.user} ({interaction.user.id})\n**Channel :** {interaction.channel.name} ({interaction.channel.id})\n**Guild :** {interaction.guild.name} ({interaction.guild.id})\n**Error :** check output file")
            outf = io.BytesIO(out.encode("utf8"))
            file = discord.File(fp=outf, filename="log.py")
            await bot.get_channel(933981853159923752).send(embed=embed, file=file)
        except AttributeError:
            try:
                embed = discord.Embed(description=f"**Bug ID:** {bugid}\n**Author :** {interaction.user} ({interaction.user.id})\n**Channel :** DMs\n**Error :** ```py\n{out}```")
                await bot.get_channel(933981853159923752).send(embed=embed)
            except discord.HTTPException:
                embed = discord.Embed(description=f"**Bug ID:** {bugid}\n**Author :** {interaction.user} ({interaction.user.id})\n**Channel :** DMs\n**Error :** check output file")
                outf = io.BytesIO(out.encode("utf8"))
                file = discord.File(fp=outf, filename="log.py")
                await bot.get_channel(933981853159923752).send(embed=embed, file=file)

@bot.ev.interaction(name=r"delmess\.(\d*)")
async def on_delmess(interaction: discord.Interaction, user_id):
    if user_id == str(interaction.user.id):
        await interaction.response.pong()
        await interaction.message.delete()
    else:
        await interaction.response.send_message(f'**Nút này không dành cho bạn**', ephemeral=True)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.modal_submit:
        if not interaction.data["custom_id"] in list(bot._connection._view_store._modals.keys()):
            await interaction.response.send_message("**Timeout**", ephemeral=True)
    elif interaction.type == discord.InteractionType.component:
        out = await bot.ev.trigger(interaction.data["custom_id"], interaction)
        if (not interaction.data["custom_id"] in [e[1] for i in bot._connection._view_store._views.values() for e in i.keys()]) and (not out):
            await interaction.response.send_message("**Timeout**", ephemeral=True)


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
    await bot.change_presence(activity=discord.Game(name="We has move to slash now :>"))
    await asyncio.sleep(10)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(bot.guilds)} Guilds"))
    await asyncio.sleep(10)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{len(bot.users)} Users"))
    await asyncio.sleep(10)
        
bot.run(os.getenv('TOKEN'), reconnect=True)
