import discord
import io
from jkeydb import database
from discord.ext import commands
from unity.rankcard import rank_card
from discord import app_commands
from unity.interactx import Interactx
import setting

class Level(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.guild is None:
            return

        seting = setting.getsetting(message.guild.id, "level", self.bot.db)
        if seting is None:
            with database(f"./data/level/{message.guild.id}.db", self.bot.db) as db:
                odata = db.get(str(message.author.id), {"level": 0, "exp": 0})
                if odata["exp"] >= 100:
                    odata["level"] += 1
                    odata["exp"] = 0
                    await message.channel.send(f"{message.author.mention}, đã lên level **`{odata['level']}`**.")
                else:
                    odata["exp"] += 1
                db[str(message.author.id)] = odata
                if db.get("level-role") is not None:
                    rlevel = db.get("level-role", {})
                    level_user = [i for i in rlevel.keys() if int(i) <= odata["level"]]
                    for i in sorted(level_user):
                        role = message.guild.get_role(rlevel[i])
                        if role is not None:
                            if message.author.get_role(rlevel[i]) is None:
                                try:
                                    await message.author.add_roles(role, reason=f"Đã đạt level {i}")
                                    await message.author.send(f"**Bạn đã nhận đạt level {i} và nhận role {role.name}**")
                                except BaseException:
                                    pass
                        else:
                            dbout = db.get("level-role", {})
                            if dbout.get(i) is not None:
                                del dbout[i]
                            if dbout.items():
                                db["level-role"] = dbout
                            elif db.get("level-role") is not None:
                                del db["level-role"]
                                
    @app_commands.command(name="level_role_list", description="Xem danh sach level role")
    async def level_role_list(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        with database(f"./data/level/{ctx.guild.id}.db", self.bot.db) as db:
            dbout = db.get("level-role", {})
            soft = sorted(dbout.items(), key=lambda x: int(x[0]))
            listr = "\n".join([ f"lv {i[0]}: <@&{i[1]}>" for i in soft])
        embed = discord.Embed(title="Level role list", description=listr)
        await ctx.send(embed=embed)
    
    @app_commands.command(name="add_level_role", description="Set role phần thưởng cho level.")
    @app_commands.default_permissions(manage_roles=True)
    async def add_level_role(self, interaction: discord.Interaction, level:app_commands.Range[int, 0, None], role: discord.Role):
        ctx = await Interactx(interaction)
        with database(f"./data/level/{ctx.guild.id}.db", self.bot.db) as db:
            dbout = db.get("level-role", {})
            dbout[str(level)] = role.id
            if dbout.items():
                db["level-role"] = dbout
        await ctx.send(f"**Đã set role {role.name} cho level {level}**")
    
    @app_commands.command(name="remove_level_role", description="Xóa role phần thưởng cho level.")
    @app_commands.default_permissions(manage_roles=True)
    async def remove_level_role(self, interaction: discord.Interaction, level:app_commands.Range[int, 0, None]):
        ctx = await Interactx(interaction)
        with database(f"./data/level/{ctx.guild.id}.db", self.bot.db) as db:
            dbout = db.get("level-role", {})
            isdel = False
            if dbout.get(str(level)) is not None:
                del dbout[str(level)]
                isdel = True
            if dbout.items():
                db["level-role"] = dbout
            elif db.get("level-role") is not None:
                del db["level-role"]
        if isdel:
            await ctx.send(f"**Đã xóa role của level {level}**")
        else:
            await ctx.send(f"**Bạn chưa set role cho level {level}**")
            
        
    @app_commands.command(name="rank", description="Xem rank/level của bạn")
    @app_commands.describe(member="Member cần xem rank/level")
    async def rank(self, interaction: discord.Interaction, member: discord.Member=None):
        ctx = await Interactx(interaction)
        if setting.getsetting(ctx.guild.id, "level", self.bot.db) is None:
                if member is None:
                    member = ctx.author
                if not member.bot:
                    with database(f"./data/level/{ctx.guild.id}.db", self.bot.db) as db:
                        data = db.get(str(member.id), {"level": 0, "exp": 0})
                    img = await rank_card(username=member.nick or member.name,
                                        avatar=member.display_avatar.with_format(
                                            "png").url,
                                        level=data["level"],
                                        rank=1,
                                        current_xp=data["exp"],
                                        xp_color="#a38aff",
                                        next_level_xp=100)
                    try:
                        await ctx.reply(file=discord.File(io.BytesIO(img), "rank.png"))
                    except BaseException:
                        pass
                else:
                    await ctx.send("Bot không có rank.")
        else:
            await ctx.send("Server này đã tắt hệ thống level")
    
    @app_commands.command(name="top", description="Xem top 10 level cao nhất ở server này.")
    async def top(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        if setting.getsetting(ctx.guild.id, "level", self.bot.db) is None:
                try:
                    with database(f"./data/level/{ctx.guild.id}.db", self.bot.db, True) as db:
                        keys = db.items()
                except FileNotFoundError:
                    keys = []
                users = []
                
                for user, level in keys:
                    if not user.isnumeric():
                        continue
                    exp = level["level"] * 100 + level["exp"]
                    users.append((user, exp))
                soft = sorted(users, key=lambda x: x[1], reverse=True)
                data = soft[:10]
                list_data = [f"`#{n} `: <@{i[0]}> `{i[1]}`" for n, i in enumerate(data)]
                embed = discord.Embed(title=f"Top 10 level", description="\n".join(list_data), color=0x00ff00)
                await ctx.send(embed=embed)
        else:
            await ctx.send("Server này đã tắt hệ thống level")

    @app_commands.command(name="lvsetting", description="Setting hệ thống level của server bạn.")
    @app_commands.describe(value="On/Off")
    @app_commands.choices(value=[
    app_commands.Choice(name='Off', value="off"),
    app_commands.Choice(name='On', value="on")])
    @app_commands.default_permissions(manage_guild=True)
    async def lvsetting(self, interaction: discord.Interaction, value: app_commands.Choice[str]):
        ctx = await Interactx(interaction)
        value = value.value
        if value.lower() == "on":
            lvsetting = None
        elif value.lower() == "off":
            lvsetting = 0
        setting.savesetting(ctx.guild.id, "level", lvsetting, self.bot.db)
        await ctx.send(f"Level is {value.lower()}")
    
async def setup(bot):
    await bot.add_cog(Level(bot))
