import io
import discord
import setting
from jkeydb import database
from discord.ext import commands
from discord import app_commands
from unity.rankcard import rank_card
from unity.interactx import Interactx


class Level(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.guild is None:
            return

        seting = await setting.getsetting(message.guild.id, "level", self.bot.db)
        if seting is None:
            async with database(f"./data/level/{message.guild.id}", self.bot.db) as db:
                for i in await db.get("channel_disable", []):
                    if message.guild.get_channel(i) is None:
                        out_ch = await db.get("channel_disable")
                        out_ch.discard(i)
                        await db.set("channel_disable", out_ch)
                d_ch = await db.get("channel_disable", [])
                ctr = None
                if message.channel.category is not None:
                    ctr = message.channel.category.id
                p_th_id = None
                try:
                    p_th_id = message.channel.parent_id
                except BaseException:
                    pass
                if message.channel.id in d_ch or ctr in d_ch or p_th_id in d_ch:
                    return
                odata = await db.get(str(message.author.id), {"level": 0, "exp": 0})
                exp_max = 50 if odata["level"] == 0 else 100 * odata["level"]
                if odata["exp"] >= exp_max:
                    odata["level"] += 1
                    odata["exp"] = 0
                    await message.channel.send(
                        f"{message.author.mention}, đã lên level **`{odata['level']}`**."
                    )
                else:
                    odata["exp"] += 1
                await db.set(str(message.author.id), odata)
                if (await db.get("level-role")) is not None:
                    rlevel = await db.get("level-role", {})
                    level_user = [i for i in rlevel.keys() if int(i) <= odata["level"]]
                    for i in sorted(level_user, key=lambda x: int(x)):
                        role = message.guild.get_role(rlevel[i])
                        if role is not None:
                            user_has_role = message.author.get_role(rlevel[i])
                            if user_has_role is None:
                                try:
                                    await message.author.add_roles(
                                        role, reason=f"Đã đạt level {i}"
                                    )
                                    await message.author.send(
                                        f"**Bạn đã nhận đạt level {i} và nhận role {role.name}**"
                                    )
                                except BaseException:
                                    pass
                        else:
                            dbout = await db.get("level-role", {})
                            if dbout.get(i) is not None:
                                del dbout[i]
                            if dbout.items():
                                await db.set("level-role", dbout)
                            else:
                                await db.remove("level-role")

    @app_commands.command(
        name="level_role_list", description="Xem danh sách chat level role"
    )
    async def level_role_list(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        async with database(f"./data/level/{ctx.guild.id}", self.bot.db) as db:
            dbout = await db.get("level-role", {})
            soft = sorted(dbout.items(), key=lambda x: int(x[0]))
            listr = "\n".join([f"lv {i[0]}: <@&{i[1]}>" for i in soft])
        embed = discord.Embed(title="Level role list", description=listr)
        await ctx.send(embed=embed)

    @app_commands.command(
        name="add_level_role", description="Set role phần thưởng cho chat level."
    )
    @app_commands.default_permissions(manage_guild=True)
    async def add_level_role(
        self,
        interaction: discord.Interaction,
        level: app_commands.Range[int, 0, None],
        role: discord.Role,
    ):
        ctx = await Interactx(interaction)
        async with database(f"./data/level/{ctx.guild.id}", self.bot.db) as db:
            dbout = await db.get("level-role", {})
            dbout[str(level)] = role.id
            await db.set("level-role", dbout)
        await ctx.send(f"**Đã set role {role.name} cho level {level}**")

    @app_commands.command(
        name="remove_level_role", description="Xóa role phần thưởng cho chat level."
    )
    @app_commands.default_permissions(manage_guild=True)
    async def remove_level_role(
        self, interaction: discord.Interaction, level: app_commands.Range[int, 0, None]
    ):
        ctx = await Interactx(interaction)
        async with database(f"./data/level/{ctx.guild.id}", self.bot.db) as db:
            dbout = await db.get("level-role", {})
            isdel = False
            if dbout.get(str(level)) is not None:
                del dbout[str(level)]
                isdel = True
            if dbout.items():
                await db.set("level-role", dbout)
            else:
                await db.remove("level-role")
        if isdel:
            await ctx.send(f"**Đã xóa role của level {level}**")
        else:
            await ctx.send(f"**Bạn chưa set role cho level {level}**")

    @app_commands.command(
        name="level_channel_setting",
        description="Tắt/Bật chat level của một kênh nhất định.",
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.choices(
        value=[
            app_commands.Choice(name="Off", value=0),
            app_commands.Choice(name="On", value=1),
        ]
    )
    async def level_channel_setting(
        self,
        interaction: discord.Interaction,
        channel: discord.abc.GuildChannel,
        value: app_commands.Choice[int],
    ):
        ctx = await Interactx(interaction)
        if (await setting.getsetting(ctx.guild.id, "level", self.bot.db)) is None:
            async with database(f"./data/level/{ctx.guild.id}", self.bot.db) as db:
                dbout = await db.get("channel_disable", [])
                if not value.value:
                    dbout.append(channel.id)
                else:
                    dbout.discard(channel.id)
                if dbout:
                    await db.set("channel_disable", dbout)
                else:
                    await db.remove("channel_disable")
            await ctx.send(f"**Đã {value.name} level của kênh {channel.mention}**")
        else:
            await ctx.send("Server này đã tắt hệ thống level")

    @app_commands.command(
        name="rank", description="Xem chat rank/level của bạn hoặc người khác"
    )
    @app_commands.describe(member="Member cần xem rank/level")
    async def rank(
        self, interaction: discord.Interaction, member: discord.Member = None
    ):
        ctx = await Interactx(interaction)
        if (await setting.getsetting(ctx.guild.id, "level", self.bot.db)) is None:
            if member is None:
                member = ctx.author
            if not member.bot:
                async with database(f"./data/level/{ctx.guild.id}", self.bot.db) as db:
                    data = await db.get(str(member.id), {"level": 0, "exp": 0})
                exp_max = 50 if data["level"] == 0 else 100 * data["level"]
                img = await rank_card(
                    username=member.nick or member.global_name or member.name,
                    avatar=member.display_avatar.with_format("png").url,
                    level=data["level"],
                    rank=1,
                    current_xp=data["exp"],
                    xp_color="#a38aff",
                    next_level_xp=exp_max,
                )
                try:
                    await ctx.reply(file=discord.File(io.BytesIO(img), "rank.png"))
                except BaseException:
                    pass
            else:
                await ctx.send("Bot không có rank.")
        else:
            await ctx.send("Server này đã tắt hệ thống level")

    @app_commands.command(
        name="top", description="Xem top 10 chat level cao nhất ở server này."
    )
    async def top(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        if (await setting.getsetting(ctx.guild.id, "level", self.bot.db)) is None:
            try:
                async with database(
                    f"./data/level/{ctx.guild.id}", self.bot.db, True
                ) as db:
                    keys = await db.items()
            except FileNotFoundError:
                keys = []
            users = []

            for user, level in keys:
                if not user.isnumeric():
                    continue
                full_exp = 0
                for i in range(level["level"] + 1):
                    full_exp += 100 * i
                if level["level"] > 0:
                    full_exp += 50
                exp = full_exp + level["exp"]
                users.append((user, exp))
            soft = sorted(users, key=lambda x: x[1], reverse=True)
            data = soft[:10]
            list_data = [f"`#{n} `: <@{i[0]}> `{i[1]}`" for n, i in enumerate(data)]
            embed = discord.Embed(
                title=f"Top 10 level", description="\n".join(list_data)
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("Server này đã tắt hệ thống level")

    @app_commands.command(
        name="lvsetting", description="Setting hệ thống chat level của server bạn."
    )
    @app_commands.describe(value="On/Off")
    @app_commands.choices(
        value=[
            app_commands.Choice(name="Off", value="off"),
            app_commands.Choice(name="On", value="on"),
        ]
    )
    @app_commands.default_permissions(manage_guild=True)
    async def lvsetting(
        self, interaction: discord.Interaction, value: app_commands.Choice[str]
    ):
        ctx = await Interactx(interaction)
        value = value.value
        if value.lower() == "on":
            lvsetting = None
        elif value.lower() == "off":
            lvsetting = 0
        await setting.savesetting(ctx.guild.id, "level", lvsetting, self.bot.db)
        await ctx.send(f"Level is {value.lower()}")


async def setup(bot):
    await bot.add_cog(Level(bot))
