import discord
import aiohttp
from discord import app_commands
from discord.ext import commands
from unity.interactx import Interactx
from unity.photo_math import get_answer

class photo_math(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    photo_math_g = app_commands.Group(name="photo_math", description="photo_math command")
    
    @photo_math_g.command(name="url", description="Sử dụng giải toán bàng cách cung cấp link ")
    async def anime(self, interaction: discord.Interaction, url: str):
        ctx = await Interactx(interaction)
        embed = discord.Embed(title="Đang Xử lí Ảnh")
        edit = await ctx.send(embed=embed)
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get("https://api.allorigins.win/raw", params={"url": url}, raise_for_status=True) as r:
                    if "image/" not in r.content_type:
                        raise TypeError("content_type is not img")
                    img_body = await r.read()
        except BaseException:
            embed = discord.Embed(title="Lỗi Không Thể Tải Ảnh")
            await edit.edit(embed=embed)
            return
        all = await get_answer(img_body)
        if not all:
            embed = discord.Embed(title="Không có câu trả lời")
            await edit.edit(embed=embed)
            return
        embeds = []
        embed_org = discord.Embed(title=f"Câu Hỏi Gốc")
        embed_org.set_image(url=url)
        embeds.append(embed_org)
        for t, i in enumerate(all, 1):
            print
            embed_q = discord.Embed(title=f"Câu Hỏi {t}", description=i["question"]["text"])
            embed_q.set_image(url=i["question"]["img"])
            embed_a = discord.Embed(title=f"Câu Trả Lời {t}", description=i["answer"]["text"])
            embed_a.set_image(url=i["answer"]["img"])
            embeds.append(embed_q)
            embeds.append(embed_a)
        await edit.edit(embeds=embeds)
        
        
    @photo_math_g.command(name="file", description="Sử dụng giải toán bàng cách upload file ảnh")
    async def ht(self, interaction: discord.Interaction, file: discord.Attachment):
        ctx = await Interactx(interaction)
        embed = discord.Embed(title="Đang Xử lí Ảnh")
        edit = await ctx.send(embed=embed)
        img_body = await file.read()
        all = await get_answer(img_body)
        if not all:
            embed = discord.Embed(title="Không có câu trả lời")
            await edit.edit(embed=embed)
            return
        embeds = []
        embed_org = discord.Embed(title=f"Câu Hỏi Gốc")
        embed_org.set_image(url=file.url)
        embeds.append(embed_org)
        for t, i in enumerate(all, 1):
            print
            embed_q = discord.Embed(title=f"Câu Hỏi {t}", description=i["question"]["text"])
            embed_q.set_image(url=i["question"]["img"])
            embed_a = discord.Embed(title=f"Câu Trả Lời {t}", description=i["answer"]["text"])
            embed_a.set_image(url=i["answer"]["img"])
            embeds.append(embed_q)
            embeds.append(embed_a)
        await edit.edit(embeds=embeds)
    
async def setup(bot):
    await bot.add_cog(photo_math(bot))
