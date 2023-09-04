import discord
import traceback
import aiohttp
from unity.interactx import Interactx
from unity.global_ui import Bard_bt, Bard_Disabled
from discord import app_commands
from discord.ext import commands

async def chat(m, chat=None):
    params = {"m": m, "key": "2937ad785c504b09b6f6b486f44ee3de"}
    if chat:
        params["conversation_id"] = chat
    async with aiohttp.ClientSession() as session:
        async with session.get("https://bard.tuanduong2.repl.co/bard", params=params, timeout=None) as response:
            return await response.json()

class Reply_TextBox(discord.ui.Modal):
    reply = discord.ui.TextInput(
        label='Bard Reply',
        max_length=4000,
        min_length=1,
        style=discord.TextStyle.paragraph
    )
    
    def __init__(self, chat_id):
        super().__init__(title='Bard')
        self.chat_id = chat_id

    async def on_submit(self, interaction: discord.Interaction):
        view = discord.ui.View(timeout=0)
        view.add_item(Bard_Disabled(interaction.user.id, self.chat_id))
        embed = discord.Embed(title="Waiting Response From Bard")
        await interaction.response.edit_message(embed=embed, view=view)
        view = discord.ui.View(timeout=0)
        try:
            data = await chat(self.reply.value, self.chat_id)
            bardcontent = data["content"]
        except BaseException:
            bardcontent = "No Response"
        embeds = []
        ai = f"**AI: **{bardcontent}"
        embed = discord.Embed(title="Bard", description=f"**{interaction.user.mention}: ** {discord.utils.escape_markdown(self.reply.value)}")
        embeds.append(embed)
        embed = discord.Embed(description=ai)
        embeds.append(embed)
        view.add_item(Bard_bt(interaction.user.id, data["conversation_id"]))
        await interaction.message.edit(embeds=embeds, view=view)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)

        # Make sure we know what the error actually is
        traceback.print_exception(type(error), error, error.__traceback__)

class Bard(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        
        @bot.ev.interaction(name=r"bard_ai\.(\d+)\.(.+)")
        async def on_delmess(interaction: discord.Interaction, user_id, chat_id):
            if user_id == str(interaction.user.id):
                await interaction.response.send_modal(Reply_TextBox(chat_id))
            else:
                await interaction.response.send_message(f'**Nút này không dành cho bạn**', ephemeral=True)
        

    @app_commands.command(name="bard", description="Use bard on Discord")
    async def bard(self, interaction: discord.Interaction, data:str):
        ctx = await Interactx(interaction)
        if data:
            embed = discord.Embed(title="Waiting Response From Bard")
            edit = await ctx.reply(embed=embed)
            embeds = []
            view = discord.ui.View(timeout=0)
            try:
                outdata = await chat(data)
                gptcontent = outdata["content"]
                view.add_item(Bard_bt(ctx.author.id, outdata["conversation_id"]))
            except BaseException:
                traceback.print_exc()
                gptcontent = "No Response"
            ai = f"**AI: **{gptcontent}"
            embed = discord.Embed(title="Bard", description=f"**{ctx.author.mention}: ** {discord.utils.escape_markdown(data)}")
            embeds.append(embed)
            embed = discord.Embed(description=ai)
            embeds.append(embed)
            await edit.edit(embeds=embeds, view=view)
    
async def setup(bot):
    await bot.add_cog(Bard(bot))