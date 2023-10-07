import discord
import botemoji
import datetime
from unity.interactx import Interactx
from discord import app_commands
from discord.ext import commands

class Confirm(discord.ui.View):
    def __init__(self, fu, ctx):
        super().__init__(timeout=60)
        self.value = None
        self.ctx = ctx
        self.fu = fu
            
    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji=botemoji.no)
    async def no(self, interaction: discord.Interaction,  button: discord.ui.Button):
        if interaction.user.id == self.ctx.author.id:
            await interaction.response.edit_message(content=f'**{botemoji.no} Lệnh đã bị hủy**', view=None)
            self.value = False
            self.stop()
        else:
            await interaction.response.send_message(content=f'Chỉ có **{self.ctx.author}** ấn được thôi', ephemeral=True)
            
    @discord.ui.button(style=discord.ButtonStyle.gray, emoji=botemoji.yes)
    async def confirm(self, interaction: discord.Interaction,  button: discord.ui.Button):
        if interaction.user.id == self.ctx.author.id:
            await interaction.response.edit_message(view=None)
            await self.fu
            self.value = True
            self.stop()
        else:
            await interaction.response.send_message(content=f'Chỉ có **{self.ctx.author}** ấn được thôi', ephemeral=True)

class mod(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
    
    nors = "Không có lí do"
    
    @app_commands.command(name="ban", description="Ban User mà bạn muốn ban")
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.User, reason:str=nors, delete_message_days:app_commands.Range[int, 1, 7]=0):
        ctx = await Interactx(interaction)
        mess = await ctx.send(f"**Đang Check User**")
        dms = delete_message_days * 86400
        mb = ctx.guild.get_member(user.id)
        try:
            await ctx.guild.fetch_ban(user)
            await mess.edit(content=f"**{botemoji.no} Người này đã bị ban từ trước rồi**")
            return
        except discord.NotFound:
            pass
        if mb:
            if ((mb.top_role.position >= ctx.author.top_role.position) and ctx.author.id != ctx.guild.owner_id) or mb.id == ctx.guild.owner_id:
                await mess.edit(content=f"**{botemoji.no} Bạn không thể ban người này**")
                return
            async def run():
                banuserout = False
                try:
                    await ctx.guild.ban(user, delete_message_seconds=dms, reason=f"Ban by {ctx.author} | Reason: {reason}")
                    banuserout = True
                except discord.Forbidden:
                    await mess.edit(content=f"**{botemoji.no} Bot không có đủ quyền để ban người này**")
                except discord.HTTPException:
                    await mess.edit(content=f"**{botemoji.no} Ban không thành công**")
                if banuserout:
                    await mess.edit(content=f"**{botemoji.yes} Đã Ban {user}**")
            view = Confirm(run(), ctx)
            await mess.edit(content=f"**Hãy nhấn {botemoji.yes} để ban {user}**", view=view)
            await view.wait()
            if view.value is None:
                await mess.edit(content=f"**{botemoji.no} Lệnh bị hủy do không có phản hồi**", view=None)
        else:
            async def run():
                banuserout = False
                try:
                    await ctx.guild.ban(user, delete_message_seconds=dms, reason=f"Ban by {ctx.author} | Reason: {reason}")
                    banuserout = True
                except discord.Forbidden:
                    await mess.edit(content=f"**{botemoji.no} Bot không có đủ quyền để ban người này**")
                except discord.HTTPException:
                    await mess.edit(content=f"**{botemoji.no} Ban không thành công**")
                if banuserout:
                    await mess.edit(content=f"**{botemoji.yes} Đã Ban {user}**")
            view = Confirm(run(), ctx)
            await mess.edit(content=f"**Hãy nhấn {botemoji.yes} để ban {user}**", view=view)
            await view.wait()
            if view.value is None:
                await mess.edit(content=f"**{botemoji.no} Lệnh bị hủy do không có phản hồi**", view=None)
    
    @app_commands.command(name="unban", description="Unban User mà bạn muốn gỡ ban")
    @app_commands.default_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user: discord.User, reason:str=nors):
        ctx = await Interactx(interaction)
        mess = await ctx.send(f"**Đang Check User**")
        try:
            await ctx.guild.fetch_ban(user)
        except discord.NotFound:
            await mess.edit(content=f"**{botemoji.no} Người này không bị ban**")
            return
        async def run():
            banuserout = False
            try:
                await ctx.guild.unban(user, reason=f"Unban by {ctx.author} | Reason: {reason}")
                banuserout = True
            except discord.Forbidden:
                await mess.edit(content=f"**{botemoji.no} Bot không có đủ quyền để unban người này**")
            except discord.HTTPException:
                await mess.edit(content=f"**{botemoji.no} Unban không thành công**")
            if banuserout:
                await mess.edit(content=f"**{botemoji.yes} Đã Unban {user}**")
        view = Confirm(run(), ctx)
        await mess.edit(content=f"**Hãy nhấn {botemoji.yes} để unban {user}**", view=view)
        await view.wait()
        if view.value is None:
            await mess.edit(content=f"**{botemoji.no} Lệnh bị hủy do không có phản hồi**", view=None)
    
    @app_commands.command(name="kick", description="Kick menber của bạn")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason:str=nors):
        ctx = await Interactx(interaction)
        member = await ctx.guild.fetch_member(member.id)
        mess = await ctx.send(f"**Đang Check User**")
        if ((member.top_role.position >= ctx.author.top_role.position) and ctx.author.id != ctx.guild.owner_id) or member.id == ctx.guild.owner_id:
            await mess.edit(content=f"**{botemoji.no} Bạn không thể Kick người này**")
            return
        async def run():
            banuserout = False
            try:
                await ctx.guild.kick(member, reason=f"Kick by {ctx.author} | Reason: {reason}")
                banuserout = True
            except discord.Forbidden:
                await mess.edit(content=f"**{botemoji.no} Bot không có đủ quyền để kick người này**")
            except discord.HTTPException:
                await mess.edit(content=f"**{botemoji.no} Kick không thành công**")
            if banuserout:
                await mess.edit(content=f"**{botemoji.yes} Đã Kick {member}**")   
        view = Confirm(run(), ctx)
        await mess.edit(content=f"**Hãy nhấn {botemoji.yes} để kick {member}**", view=view)
        await view.wait()
        if view.value is None:
            await mess.edit(content=f"**{botemoji.no} Lệnh bị hủy do không có phản hồi**", view=None)
            
    @app_commands.command(name="timeout", description="Set timeout cho menber của bạn")
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, reason:str=nors, days:int=0, hours:int=0, minutes:int=0, seconds:int=0):
        ctx = await Interactx(interaction)
        stime = datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        member = await ctx.guild.fetch_member(member.id)
        if not (10 <= int(stime.total_seconds()) <= (86400 * 28)):
            await ctx.send(f"**{botemoji.no} Thời gian timeout cần lớn hơn 10 giây và bé hơn 28 ngày**")
            return
        mess = await ctx.send(f"**Đang Check User**")
        if member.is_timed_out():
            await mess.edit(content=f"**{botemoji.no} Người này đang bị timeout**")
            return
        if ((member.top_role.position >= ctx.author.top_role.position) and ctx.author.id != ctx.guild.owner_id) or member.id == ctx.guild.owner_id:
            await mess.edit(content=f"**{botemoji.no} Bạn không thể timeout người này**")
            return
        async def run():
            banuserout = False
            try:
                await member.timeout(stime, reason=f"Timeout by {ctx.author} | Reason: {reason}")
                banuserout = True
            except discord.Forbidden:
                await mess.edit(content=f"**{botemoji.no} Bot không có đủ quyền để timeout người này**")
            except discord.HTTPException:
                await mess.edit(content=f"**{botemoji.no} Timeout không thành công**")
            if banuserout:
                await mess.edit(content=f"**{botemoji.yes} Đã Timeout {member} và sẽ hết timeout sau <t:{int((await ctx.guild.fetch_member(member.id)).timed_out_until.timestamp())}:R>**")
        view = Confirm(run(), ctx)
        await mess.edit(content=f"**Hãy nhấn {botemoji.yes} để timeout {member}**", view=view)
        await view.wait()
        if view.value is None:
            await mess.edit(content=f"**{botemoji.no} Lệnh bị hủy do không có phản hồi**", view=None)
        
    @app_commands.command(name="untimeout", description="Bỏ timeout cho menber của bạn")
    async def untimeout(self, interaction: discord.Interaction, member: discord.Member, reason:str=nors):
        ctx = await Interactx(interaction)
        member = await ctx.guild.fetch_member(member.id)
        mess = await ctx.send(f"**Đang Check User**")
        if not member.is_timed_out():
            await mess.edit(content=f"**{botemoji.no} Người này không bị timeout**")
            return
        if ((member.top_role.position >= ctx.author.top_role.position) and ctx.author.id != ctx.guild.owner_id) or member.id == ctx.guild.owner_id:
            await mess.edit(content=f"**{botemoji.no} Bạn không thể bỏ timeout người này**")
            return
        async def run():
            banuserout = False
            try:
                await member.timeout(None, reason=f"Remove timeout by {ctx.author} | Reason: {reason}")
                banuserout = True
            except discord.Forbidden:
                await mess.edit(content=f"**{botemoji.no} Bot không có đủ quyền để bỏ timeout người này**")
            except discord.HTTPException:
                await mess.edit(content=f"**{botemoji.no} Bỏ timeout không thành công**")
            if banuserout:
                await mess.edit(content=f"**{botemoji.yes} Đã bỏ timeout {member}**")
        view = Confirm(run(), ctx)
        await mess.edit(content=f"**Hãy nhấn {botemoji.yes} để bỏ timeout {member}**", view=view)
        await view.wait()
        if view.value is None:
            await mess.edit(content=f"**{botemoji.no} Lệnh bị hủy do không có phản hồi**", view=None)  
        
async def setup(bot):
    await bot.add_cog(mod(bot))