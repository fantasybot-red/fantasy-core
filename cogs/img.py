import discord
import aiohttp
from discord import app_commands
from discord.ext import commands
from unity.interactx import Interactx

class img(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    g_img = app_commands.Group(name="img", description="images command")
    
    @g_img.command(name="anime", description="xem một ảnh anime random")
    async def anime(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.waifu.pics/sfw/waifu") as resp:
                url = await resp.json()
                url = url["url"]
        embed = discord.Embed(title="Anime")
        embed.set_image(url=url)
        await ctx.send(embed=embed)
        
    @g_img.command(name="henta_i", description="xem một ảnh haiten random", nsfw=True)
    async def ht(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        if not ctx.channel.is_nsfw():
            await ctx.send("This command can only be used in NSFW channels.")
            return
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.waifu.pics/nsfw/waifu") as resp:
                url = await resp.json()
                url = url["url"]
        embed = discord.Embed(title="Hentai")
        embed.set_image(url=url)
        await ctx.send(embed=embed)
    
async def setup(bot):
    await bot.add_cog(img(bot))
