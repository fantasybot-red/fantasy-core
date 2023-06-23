import discord
import os
from discord.ext import commands
from discord import app_commands
from unity.interactx import Interactx
import aiohttp

class google(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
    
    async def google_autocomplete(self, interaction, current: str):
        if current:
            pr = {"client": "chrome", "q": current, "hl": "vi"}
            async with aiohttp.ClientSession() as s:
                async with s.get("http://google.com/complete/search", params=pr) as r:
                    sugest = (await r.json(content_type=None))[1]
            rdata = [app_commands.Choice(name=s, value=s) for s in sugest]
            rdata.insert(0, app_commands.Choice(name=current, value=current))
            return rdata
        else:
            return []
    
    async def google_api_search(self, q):
        payload = {
            "key": os.getenv("GOOGLE_TOKEN"),
            "cx": os.getenv("GOOGLE_CX_ID"),
            "q": q,
            "num": 5
        }
        async with aiohttp.ClientSession() as s:
            async with s.get("https://www.googleapis.com/customsearch/v1", params=payload) as r:
                djson = await r.json()
        return djson['items']
    
    g_search = app_commands.Group(name="search", description="tempvoice command")
    
    @g_search.command(name="google", description="command that can you can use Google Search on your discord")
    @app_commands.describe(data="cái cần tìm kiếm")
    @app_commands.autocomplete(data=google_autocomplete)
    async def search_google(self, interaction, data:str):
        ctx = await Interactx(interaction)
        gsl = []
        data = await self.google_api_search(data)
        for i in data:
            snippet = f"\n`{i.get('snippet')}`" if i.get('snippet') is not None else ""
            rdata = f"{i['displayLink']}\n**[{i['title']}]({i['link']})**{snippet}"
            gsl.append(rdata)
        embed = discord.Embed(title="Google Search", description="\n\n".join(gsl))
        await ctx.send(embed=embed)
    
    
    
    

async def setup(bot):
    await bot.add_cog(google(bot))
