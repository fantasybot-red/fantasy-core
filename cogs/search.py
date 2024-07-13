import json
import os, re
import discord
import aiohttp
from discord.ext import commands
from discord import app_commands
from unity.interactx import Interactx

headers_real = {"User-Agent": "Mozilla/5.0 (compatible; FantasyBot/0.1; +https://fantasybot.xyz/support)"}

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
        async with aiohttp.ClientSession(headers=headers_real) as s:
            async with s.get("https://www.googleapis.com/customsearch/v1", params=payload) as r:
                djson = await r.json()
        return djson['items']
    
    async def chplay_search(self, sdata):
        async with aiohttp.ClientSession(headers=headers_real, base_url="https://play.google.com") as s:
            async with s.get(f"/store/search", params={"q": sdata, "c": "apps"}) as r:
                url_ids = re.findall("<a.*?href=\"(/store/apps/details\?id=.*?)\".*?>", await r.text())
            if url_ids:
                async with s.get(url_ids[0], params={"hl": "en", "gl": "US"}) as r:
                    out = re.findall("<script type=\"application/ld\+json\" nonce=\".*?\">(.*?)</script>", await r.text())
                    if out:
                        data = json.loads(out[0])
                        return data

    async def appstore_search(self, sdata):
        async with aiohttp.ClientSession(headers=headers_real) as s:
            async with s.get(f"https://itunes.apple.com/search", params={"media": "software", "term": sdata, "limit": "1"}) as r:
                data = await r.json(content_type="text/javascript")
                if data["resultCount"]:
                    return data["results"][0]
    
    g_search = app_commands.Group(name="search", description="search command")
    
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
        
    @g_search.command(name="chplay", description="command that can you can search Google CHplay on your discord")
    @app_commands.describe(data="cái cần tìm kiếm")
    async def search_chplay(self, interaction, data:str):
        ctx = await Interactx(interaction)
        data = await self.chplay_search(data)
        embed = discord.Embed(title="Không có kết quả tìm kiếm")
        view = None
        if data is not None:
            embed = discord.Embed(title=data["name"], description=data["description"])
            embed.add_field(name="Developer", value=data['author']['name'])
            if int(data["offers"][0]["price"]) == 0:
                price = "Free"
            else:
                price = data["offers"][0]["price"] + " " + data["offers"][0]["priceCurrency"]
            embed.add_field(name="Price", value=price)
            embed.add_field(name="Rating", value=f"{float(data['aggregateRating']['ratingValue']):.1f}")
            embed.set_thumbnail(url=data["image"])
            view = discord.ui.View(timeout=0)
            view.add_item(discord.ui.Button(label="View on Chplay", url=data["url"]))
        await ctx.send(embed=embed, view=view)
    
    @g_search.command(name="appstore", description="command that can you can search App Store on your discord")
    @app_commands.describe(data="cái cần tìm kiếm")
    async def search_appstore(self, interaction, data:str):
        ctx = await Interactx(interaction)
        data = await self.appstore_search(data)
        embed = discord.Embed(title="Không có kết quả tìm kiếm")
        view = None
        if data is not None:
            embed = discord.Embed(title=data["trackName"])
            embed.add_field(name="Developer", value=data['artistName'])
            embed.add_field(name="Price", value=data["formattedPrice"])
            embed.add_field(name="Rating", value=f"{data['averageUserRating']:.1f}")
            embed.set_thumbnail(url=data["artworkUrl512"])
            view = discord.ui.View(timeout=0)
            view.add_item(discord.ui.Button(label="View on App Store", url=data["trackViewUrl"]))
        await ctx.send(embed=embed, view=view)
    
    
    

async def setup(bot):
    await bot.add_cog(google(bot))
