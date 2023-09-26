import discord, typing, string
from discord.ext import commands
from discord import app_commands
from unity.interactx import Interactx
from jkeydb import database

class vh(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_temp(self, ctx, channel, db):
        if str(channel.id) not in db.keys():
                embed = discord.Embed(title="Kênh này không phải TempVoice")
                await ctx.send(embed=embed)
                return True
        if channel.permissions_for(ctx.author).manage_channels:
            pass
        elif db[str(channel.id)]["owner"] == ctx.author.id:
            pass
        else:
            embed = discord.Embed(title="Kênh TempVoice không phải của bạn")
            await ctx.send(embed=embed)
            return True
        return False

    @commands.Cog.listener()
    async def on_voice_state_update(self, member:discord.Member, before:discord.VoiceState, after:discord.VoiceState):
        if before.channel != after.channel:
            if before.channel is not None:
                with database(f"./data/tempvoice/{member.guild.id}", self.bot.db) as db:
                    if str(before.channel.id) in db.keys():
                        if len([ i for i in before.channel.members if not i.bot]) == 0:
                            del db[str(before.channel.id)]
                            try:
                                await before.channel.delete()
                            except BaseException:
                                pass
            
            if after.channel is not None:
                with database(f"./data/voicehub/{member.guild.id}", self.bot.db) as db:
                    if str(after.channel.id) in db.keys() and (not member.bot):
                        edit_dict = {}
                        main_cf = db[str(after.channel.id)]
                        voicename = member.name if main_cf.get("name") is None else string.Template(main_cf["name"]).safe_substitute(name=member.name, nick=member.nick or member.global_name or member.name)
                        voicename = voicename[:100]
                        if main_cf["type"] == "vc":
                            ch = await member.guild.create_voice_channel(voicename, reason=f"VoiceHub | Create Temp Voice Channel For {member}", category=after.channel.category)
                            pr = {}
                            if main_cf.get("full_control"):
                                pr["manage_permissions"] = True
                            await ch.set_permissions(member, view_channel=True, connect=True, manage_channels=True, **pr)
                            
                            if main_cf.get("bitrate") is not None:
                                if (int(member.guild.bitrate_limit) / 1000) < main_cf["bitrate"]:
                                    a = db[str(after.channel.id)]
                                    a["bitrate"] = (int(member.guild.bitrate_limit) / 1000)
                                    db[str(after.channel.id)] = a 
                                edit_dict["bitrate"] = main_cf["bitrate"] * 1000
                        elif main_cf["type"] == "sc":
                            ch = await member.guild.create_stage_channel(voicename, position=2147483647, reason=f"VoiceHub | Create Temp Stage Channel For {member}", category=after.channel.category)
                            if main_cf.get("bitrate") is not None:
                                edit_dict["bitrate"] = main_cf["bitrate"] * 1000
                            pr = {}
                            if main_cf.get("full_control"):
                                pr["manage_permissions"] = True
                            await ch.set_permissions(member, view_channel=True, connect=True, manage_channels=True, mute_members=True, move_members=True, **pr)
                        if member.voice.channel is not None:
                            await member.move_to(ch, reason=f"VoiceHub | Move {member} To Temp Voice")
                            
                        if main_cf.get("user_limit") is not None:
                                edit_dict["user_limit"] = main_cf["user_limit"]
                        if main_cf.get("nsfw") is not None:
                            edit_dict["nsfw"] = main_cf["nsfw"]
                        if main_cf.get("slowmode") is not None:
                            edit_dict["slowmode_delay"] = main_cf["slowmode"]
                        if main_cf.get("private") is not None:
                            await ch.set_permissions(ch.guild.default_role, view_channel=False)
                            
                        if len(edit_dict):
                            await ch.edit(**edit_dict, reason="VoiceHub Config")
                        with database(f"./data/tempvoice/{member.guild.id}", self.bot.db) as tdb:
                            tdb[str(ch.id)] = {"owner": member.id, "prcf": main_cf}
                            
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel:discord.abc.GuildChannel):
        with database(f"./data/tempvoice/{channel.guild.id}", self.bot.db) as tdb:
            if str(channel.id) in tdb.keys():
                del tdb[str(channel.id)]
                
        with database(f"./data/voicehub/{channel.guild.id}", self.bot.db) as db:
            if str(channel.id) in db.keys():
                del db[str(channel.id)]

    
    voicehub_g = app_commands.Group(name="voicehub", description="voicehub command", default_permissions=discord.Permissions(manage_channels=True))
    
    @voicehub_g.command(name="create", description="Tạo VoiceHub")
    @app_commands.describe(name="Tên Kênh", v_type="Loại Kênh")
    @app_commands.choices(v_type=[
    app_commands.Choice(name='Voice Channel', value="vc"),
    app_commands.Choice(name='Stage Channels', value="sc")])
    @app_commands.rename(v_type="voice_type")
    async def vh_create(self, interaction: discord.Interaction, name:str, v_type:app_commands.Choice[str], category:discord.CategoryChannel=None):
        ctx = await Interactx(interaction)
        embed = discord.Embed(title="Đang tạo VoiceHub")
        edit = await ctx.send(embed=embed)
        if category is None:
            try:
                a = await ctx.guild.create_category(name="VoiceHub")
            except BaseException:
                embed = discord.Embed(title="Không Thể Tạo VoiceHub")
                await edit.edit(embed=embed)
                return
        else:
            a = category
        try:
            ch = await a.create_voice_channel(name)
        except BaseException:
            embed = discord.Embed(title="Không Thể Tạo VoiceHub")
            await edit.edit(embed=embed)
            return
        with database(f"./data/voicehub/{ctx.guild.id}", self.bot.db) as db:
            db[str(ch.id)] = {"type": v_type.value}
        embed = discord.Embed(description=f"**Đã tạo xong VoiceHub: {ch.mention}**\nNote: Để chỉnh quyền mặc định cho kênh hãy chỉnh\nquền chỉnh của thư mục mà VoiceHub ở trong\n (trừ quyền của chủ kênh và thông số kênh temp voice cần chỉnh bằng command \n`/voicehub edit <...>`)")
        await edit.edit(embed=embed)
    
    edit_vh_g = app_commands.Group(name="edit", description="voicehub edit command", parent=voicehub_g, default_permissions=discord.Permissions(manage_channels=True))
    
    @edit_vh_g.command(name="temp_name", description="Set tên mặc định của TempVoice")
    @app_commands.describe(channel="Kênh VoiceHub", name="${name} = Username | ${nick} = User Display Name")
    async def vh_cf_temp_name(self, interaction: discord.Interaction, channel:discord.VoiceChannel, name:app_commands.Range[str, 1, 50] = None):
        ctx = await Interactx(interaction)
        with database(f"./data/voicehub/{ctx.guild.id}", self.bot.db) as db:
            if str(channel.id) not in db.keys():
                embed = discord.Embed(title="Kênh này không phải VoiceHub")
                await ctx.send(embed=embed)
                return
            a = db[str(channel.id)]
            if (a.get("name") is not None) and name == "{name}":
                del a["name"]
            elif name is not None:
                a["name"] = name
            elif a.get("name") is not None:
                del a["name"]
            db[str(channel.id)] = a
            embed = discord.Embed(title=f"Đã set tên mặc định của TempVoice")
            await ctx.send(embed=embed)
    
    @edit_vh_g.command(name="bitrate", description="Chỉnh VoiceHub Bitrate")
    @app_commands.describe(channel="Kênh VoiceHub", bitrate="Số Bitrate muốn set")
    async def vh_cf_bitrate(self, interaction: discord.Interaction, channel:discord.VoiceChannel, bitrate:app_commands.Range[int, 8, 384]):
        ctx = await Interactx(interaction)
        with database(f"./data/voicehub/{ctx.guild.id}", self.bot.db) as db:
            if str(channel.id) not in db.keys():
                embed = discord.Embed(title="Kênh này không phải VoiceHub")
                await ctx.send(embed=embed)
                return
            if db[str(channel.id)]["type"] == "vc":
                if bitrate > int(ctx.guild.bitrate_limit / 1000):
                    embed = discord.Embed(title=f"Bitrate ở server bạn phải bé hơn {int(ctx.guild.bitrate_limit / 1000)}")
                    await ctx.send(embed=embed)
                    return
                if bitrate != 64:
                    a = db[str(channel.id)]
                    a["bitrate"] = bitrate
                    db[str(channel.id)] = a
                else:
                    if "bitrate" in db[str(channel.id)].keys():
                        a = db[str(channel.id)]
                        del a["bitrate"]
                        db[str(channel.id)] = a
            if db[str(channel.id)]["type"] == "sc":
                if bitrate > 64:
                    embed = discord.Embed(title=f"Giới hạn bitrate của Stage Channels là 64")
                    await ctx.send(embed=embed)
                    return
                if bitrate != 64:
                    a = db[str(channel.id)]
                    a["bitrate"] = bitrate
                    db[str(channel.id)] = a
                else:
                    if "bitrate" in db[str(channel.id)].keys():
                        a = db[str(channel.id)]
                        del a["bitrate"]
                        db[str(channel.id)] = a
            embed = discord.Embed(title=f"Đã set VoiceHub bitrate thành {bitrate}")
            await ctx.send(embed=embed)
    
    @edit_vh_g.command(name="full_control", description="Cho phép chủ kênh có mọi quyền kiểm soát temp voice của họ")
    @app_commands.describe(channel="Kênh VoiceHub", var="on/off")
    @app_commands.choices(var=[
    app_commands.Choice(name='On', value=1),
    app_commands.Choice(name='Off', value=0)])
    async def vh_cf_full_control(self, interaction: discord.Interaction, channel:discord.VoiceChannel, var:app_commands.Choice[int]):
        ctx = await Interactx(interaction)
        with database(f"./data/voicehub/{ctx.guild.id}", self.bot.db) as db:
            if str(channel.id) not in db.keys():
                embed = discord.Embed(title="Kênh này không phải VoiceHub")
                await ctx.send(embed=embed)
                return
            if var.value == 1:
                a = db[str(channel.id)]
                a["full_control"] = True
                db[str(channel.id)] = a
            elif db[str(channel.id)].get("full_control") is not None:
                a = db[str(channel.id)]
                del a["full_control"]
                db[str(channel.id)] = a
            embed = discord.Embed(title=f"Đã set full control thành {var.name}")
            await ctx.send(embed=embed)
    
    @edit_vh_g.command(name="nsfw", description="Set nsfw cho kênh temp voice tạo từ VoiceHub")
    @app_commands.describe(channel="Kênh VoiceHub", var="on/off")
    @app_commands.choices(var=[
    app_commands.Choice(name='On', value=1),
    app_commands.Choice(name='Off', value=0)])
    async def vh_cf_nsfw(self, interaction: discord.Interaction, channel:discord.VoiceChannel, var:app_commands.Choice[int]):
        ctx = await Interactx(interaction)
        with database(f"./data/voicehub/{ctx.guild.id}", self.bot.db) as db:
            if str(channel.id) not in db.keys():
                embed = discord.Embed(title="Kênh này không phải VoiceHub")
                await ctx.send(embed=embed)
                return
            if var.value == 1:
                a = db[str(channel.id)]
                a["nsfw"] = True
                db[str(channel.id)] = a
            elif db[str(channel.id)].get("nsfw") is not None:
                a = db[str(channel.id)]
                del a["nsfw"]
                db[str(channel.id)] = a
            embed = discord.Embed(title=f"Đã set nsfw thành {var.name}")
            await ctx.send(embed=embed)
    
    @edit_vh_g.command(name="lock", description="Set lock cho kênh temp tạo từ VoiceHub")
    @app_commands.describe(channel="Kênh VoiceHub", var="on/off")
    @app_commands.choices(var=[
    app_commands.Choice(name='On', value=1),
    app_commands.Choice(name='Off', value=0)])
    async def vh_cf_lock(self, interaction: discord.Interaction, channel:discord.VoiceChannel, var:app_commands.Choice[int]):
        ctx = await Interactx(interaction)
        with database(f"./data/voicehub/{ctx.guild.id}", self.bot.db) as db:
            if str(channel.id) not in db.keys():
                embed = discord.Embed(title="Kênh này không phải VoiceHub")
                await ctx.send(embed=embed)
                return
            if var.value == 1:
                a = db[str(channel.id)]
                a["private"] = True
                db[str(channel.id)] = a
            elif db[str(channel.id)].get("private") is not None:
                a = db[str(channel.id)]
                del a["private"]
                db[str(channel.id)] = a
            embed = discord.Embed(title=f"Đã set lock thành {var.name}")
            await ctx.send(embed=embed) 
            
    @edit_vh_g.command(name="user_limit", description="Chỉnh VoiceHub user limit")
    @app_commands.describe(channel="Kênh VoiceHub", user_limit="Số lương người muốn giới hạn (0 = ∞)")
    async def vh_cf_user_limit(self, interaction: discord.Interaction, channel:discord.VoiceChannel, user_limit:app_commands.Range[int, 0, 10000]):
        ctx = await Interactx(interaction)
        with database(f"./data/voicehub/{ctx.guild.id}", self.bot.db) as db:
            if str(channel.id) not in db.keys():
                embed = discord.Embed(title="Kênh này không phải VoiceHub")
                await ctx.send(embed=embed)
                return
            if db[str(channel.id)]["type"] == "vc":
                if user_limit > 99:
                    embed = discord.Embed(title=f"Giới hạn user limit của Voice Channels là 99")
                    await ctx.send(embed=embed)
                    return
            if user_limit != 0 :
                a = db[str(channel.id)]
                a["user_limit"] = user_limit
                db[str(channel.id)] = a
            elif db[str(channel.id)].get("user_limit") is not None:
                a = db[str(channel.id)]
                del a["user_limit"]
                db[str(channel.id)] = a
            if user_limit == 0:
                user_limit = "∞"
            embed = discord.Embed(title=f"Đã set user limit thành {user_limit}")
            await ctx.send(embed=embed)
        
    @edit_vh_g.command(name="slowmode", description="Chỉnh VoiceHub slowmode")
    @app_commands.describe(channel="Kênh VoiceHub")
    async def vh_cf_slowmode(self, interaction: discord.Interaction, channel:discord.VoiceChannel, seconds:app_commands.Range[int, 0, 21600]):
        ctx = await Interactx(interaction)
        with database(f"./data/voicehub/{ctx.guild.id}", self.bot.db) as db:
            if str(channel.id) not in db.keys():
                embed = discord.Embed(title="Kênh này không phải VoiceHub")
                await ctx.send(embed=embed)
                return
            if seconds != 0 :
                a = db[str(channel.id)]
                a["slowmode"] = seconds
                db[str(channel.id)] = a
            elif db[str(channel.id)].get("slowmode") is not None:
                a = db[str(channel.id)]
                del a["slowmode"]
                db[str(channel.id)] = a
            embed = discord.Embed(title=f"Đã set slowmode thành {seconds}s")
            await ctx.send(embed=embed)
            
    voice_g = app_commands.Group(name="tempvoice", description="tempvoice command")
    
    voice_edit_g = app_commands.Group(name="edit", description="tempvoice edit command", parent=voice_g)
    
    @voice_g.command(name="claim", description="claim kênh thành của bạn")
    async def v_claim(self, interaction: discord.Interaction, channel:typing.Union[discord.VoiceChannel, discord.StageChannel]):
        ctx = await Interactx(interaction)
        with database(f"./data/tempvoice/{ctx.guild.id}", self.bot.db) as db:
            if await self.check_temp(ctx, channel, db):
                return
            old_user = ctx.guild.get_member(db[str(channel.id)]["owner"])
            if ctx.author not in channel.members:
                embed = discord.Embed(title=f"Bạn không ở trong kênh này")
                await ctx.send(embed=embed)
                return
            if old_user in channel.members:
                embed = discord.Embed(title=f"Chủ kênh vẫn còn trong ở trong kênh")
                await ctx.send(embed=embed)
                return
            await channel.set_permissions(old_user, overwrite=None)
            pr = {}
            if db[str(channel.id)]["prcf"].get("full_control"):
                pr["manage_permissions"] = True
            await channel.set_permissions(ctx.author, view_channel=True, connect=True, manage_channels=True, mute_members=True, move_members=True, **pr)
            preconfig = db[str(channel.id)]
            preconfig["owner"] = ctx.author.id
            db[str(channel.id)] = preconfig
            embed = discord.Embed(title=f"Bạn đã thành chủ của kênh này")
            await ctx.send(embed=embed)
    
    @voice_edit_g.command(name="lock", description="Set kênh của bạn thành lock")
    @app_commands.describe(channel="Kênh Temp", var="on/off")
    @app_commands.choices(var=[
    app_commands.Choice(name='On', value=1),
    app_commands.Choice(name='Off', value=0)])
    async def v_private(self, interaction: discord.Interaction, channel:typing.Union[discord.VoiceChannel, discord.StageChannel], var:app_commands.Choice[int]):
        ctx = await Interactx(interaction)
        with database(f"./data/tempvoice/{ctx.guild.id}", self.bot.db) as db:
            if await self.check_temp(ctx, channel, db):
                return
            await channel.set_permissions(channel.guild.default_role, view_channel=False if var.value == 1 else None)
            embed = discord.Embed(title=f"Đã set lock thành {var.name}")
            await ctx.send(embed=embed)
    
    @voice_edit_g.command(name="nsfw", description="Set kênh của bạn thành nsfw")
    @app_commands.describe(channel="Kênh Temp", var="on/off")
    @app_commands.choices(var=[
    app_commands.Choice(name='On', value=1),
    app_commands.Choice(name='Off', value=0)])
    async def v_nsfw(self, interaction: discord.Interaction, channel:typing.Union[discord.VoiceChannel, discord.StageChannel], var:app_commands.Choice[int]):
        ctx = await Interactx(interaction)
        with database(f"./data/tempvoice/{ctx.guild.id}", self.bot.db) as db:
            if await self.check_temp(ctx, channel, db):
                return
            await channel.edit(nsfw=True if var.value == 1 else False)
            embed = discord.Embed(title=f"Đã set nsfw thành {var.name}")
            await ctx.send(embed=embed)
            
    @voice_edit_g.command(name="bitrate", description="Chỉnh Bitrate của TempVoice")
    @app_commands.describe(channel="Kênh Temp", bitrate="Số Bitrate muốn set")
    async def v_bitrate(self, interaction: discord.Interaction, channel:typing.Union[discord.VoiceChannel, discord.StageChannel], bitrate:app_commands.Range[int, 8, 384]):
        ctx = await Interactx(interaction)
        with database(f"./data/tempvoice/{ctx.guild.id}", self.bot.db) as db:
            if await  self.check_temp(ctx, channel, db):
                return
            
            if channel.type == discord.ChannelType.voice and bitrate > int(ctx.guild.bitrate_limit / 1000):
                    embed = discord.Embed(title=f"Bitrate ở server bạn phải bé hơn {int(ctx.guild.bitrate_limit / 1000)}")
                    await ctx.send(embed=embed)
                    return
            if channel.type == discord.ChannelType.stage_voice and bitrate > 64:
                    embed = discord.Embed(title=f"Giới hạn bitrate của Stage Channels là 64")
                    await ctx.send(embed=embed)
                    return
            await channel.edit(bitrate=bitrate*1000)
            embed = discord.Embed(title=f"Đã set VoiceHub bitrate thành {bitrate}")
            await ctx.send(embed=embed) 

    @voice_edit_g.command(name="user_limit", description="Chỉnh TempVoice user limit")
    @app_commands.describe(channel="Kênh Temp", user_limit="Số lương người muốn giới hạn (0 = ∞)")
    async def v_user_limit(self, interaction: discord.Interaction, channel:typing.Union[discord.VoiceChannel, discord.StageChannel], user_limit:app_commands.Range[int, 0, 10000]):
        ctx = await Interactx(interaction)
        with database(f"./data/tempvoice/{ctx.guild.id}", self.bot.db) as db:
            if await  self.check_temp(ctx, channel, db):
                return

            if channel.type == discord.ChannelType.voice and user_limit > 99:
                embed = discord.Embed(title=f"Giới hạn user limit của Voice Channels là 99")
                await ctx.send(embed=embed)
                return
            await channel.edit(user_limit=user_limit if user_limit != 0 else None)
            if user_limit == 0:
                user_limit = "∞"
            embed = discord.Embed(title=f"Đã set user limit thành {user_limit}")
            await ctx.send(embed=embed)
    
    @voice_edit_g.command(name="rename", description="Chỉnh tên TempVoice")
    @app_commands.describe(channel="Kênh Temp", name="Tên mới của kênh")
    async def v_rename(self, interaction: discord.Interaction, channel:typing.Union[discord.VoiceChannel, discord.StageChannel], name:str):
        ctx = await Interactx(interaction)
        with database(f"./data/tempvoice/{ctx.guild.id}", self.bot.db) as db:
            if await self.check_temp(ctx, channel, db):
                return
            if channel.permissions_for(ctx.author).manage_channels:
                pass
            elif db[str(channel.id)]["owner"] == ctx.author.id:
                pass
            else:
                embed = discord.Embed(title="Kênh TempVoice không phải của bạn")
                await ctx.send(embed=embed)
                return
            await channel.edit(name=name)
            embed = discord.Embed(title=f"Đã set tên kênh thành {channel.mention}")
            await ctx.send(embed=embed)
            
    @voice_edit_g.command(name="slowmode", description="Chỉnh slowmode của TempVoice")
    @app_commands.describe(channel="Kênh Temp")
    async def v_slowmode(self, interaction: discord.Interaction, channel:typing.Union[discord.VoiceChannel, discord.StageChannel], seconds:app_commands.Range[int, 0, 21600]):
        ctx = await Interactx(interaction)
        with database(f"./data/tempvoice/{ctx.guild.id}", self.bot.db) as db:
            if await self.check_temp(ctx, channel, db):
                return
            await channel.edit(slowmode_delay=seconds)
            embed = discord.Embed(title=f"Đã set slowmode là {seconds}s")
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(vh(bot))