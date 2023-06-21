import discord
import aiohttp
from unity.interactx import Interactx
from discord import app_commands
from discord.ext import commands

class img(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    @app_commands.command(name="anime", description="xem một ảnh anime random")
    async def anime(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.waifu.pics/sfw/waifu") as resp:
                url = await resp.json()
                url = url["url"]
        embed = discord.Embed(title="Anime")
        embed.set_image(url=url)
        await ctx.send(embed=embed)
        
    @app_commands.command(name="hent_n", description="xem một ảnh haiten random", nsfw=True)
    async def ht(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.waifu.pics/nsfw/waifu") as resp:
                url = await resp.json()
                url = url["url"]
        embed = discord.Embed(title="Hentai")
        embed.set_image(url=url)
        await ctx.send(embed=embed)
    
async def setup(bot):
    await bot.add_cog(img(bot))
