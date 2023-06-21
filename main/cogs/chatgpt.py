import discord
import io
import traceback
from unitiprefix import get_prefix
from unity.chatgpt import ChatGPT
from unity.interactx import Interactx
from discord import app_commands
from discord.ext import commands

chatgpt_cl = ChatGPT()

class Chatgpt(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        
    
    @app_commands.command(name="chatgpt", description="Use ChatGPT by OpenAI on Discord")
    @app_commands.describe(data="Input for ChatGPT")
    async def chatgpt(self, interaction: discord.Interaction, data:str):
        ctx = await Interactx(interaction)
        if data:
            embed = discord.Embed(title="Waiting Response From ChatGPT")
            edit = await ctx.reply(embed=embed)
            embeds = []
            try:
                gptcontent = await chatgpt_cl.create_new_chat(data)
            except BaseException:
                traceback.print_exc()
                gptcontent = "No Response"
            ai = f"**AI: **{gptcontent}"
            embed = discord.Embed(title="ChatGpt", description=f"**{ctx.author.mention}: ** {discord.utils.escape_markdown(data)}")
            embeds.append(embed)
            embed = discord.Embed(description=ai)
            embeds.append(embed)
            await edit.edit(embeds=embeds)
        else:
            embed = discord.Embed(title="ChatGPT Command", description=f"**How To Use:**\n`{get_prefix(ctx)}chatgpt <data>`")
            await ctx.reply(embed=embed)
    
    @app_commands.command(name="dalle", description="Use DALL-E by OpenAI on Discord")
    @app_commands.describe(data="Input for DALL-E")
    async def dalle(self, interaction: discord.Interaction, data:str):
        ctx = await Interactx(interaction)
        if data:
            embed = discord.Embed(title="Waiting Response From DALL-E")
            edit = await ctx.reply(embed=embed)
            embed = discord.Embed(title="DALL-E")
            try:
                outdata = await chatgpt_cl.create_dalle(data)
                embed.description = f"**{ctx.author.mention}: ** {discord.utils.escape_markdown(data)}\n**AI:** "
                embed.set_image(url=f"attachment://{outdata.filename}")
                file = discord.File(fp=io.BytesIO(outdata.content), filename=outdata.filename)
                frp = [file]
            except BaseException:
                traceback.print_exc()
                embed.description = f"**{ctx.author.mention}: ** {discord.utils.escape_markdown(data)}\n**AI:** No Response"
                frp = []
            await edit.edit(embed=embed, attachments=frp)
        else:
            embed = discord.Embed(title="DALL-E Command", description=f"**How To Use:**\n`{get_prefix(ctx)}dalle <data>`")
            await ctx.reply(embed=embed)
    
async def setup(bot):
    await bot.add_cog(Chatgpt(bot))