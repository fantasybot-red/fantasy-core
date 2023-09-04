import discord
import botemoji
import aiohttp
from unity.interactx import Interactx
from discord import app_commands
from discord.ext import commands

async def get_game():
    async with aiohttp.ClientSession(headers={"Origin":"https://guesstherank.org"}) as s:
        async with s.get("https://api.guesstherank.org/api/getVideo?game=valorant") as r:
            data = await r.json()
            out = data["video"]
            return out

class getrank(commands.Cog):
    
    ranklist = [
                discord.SelectOption(label="Iron", emoji=botemoji.valorant_iron, value="1"),
                discord.SelectOption(label="Bronze", emoji=botemoji.valorant_bronze, value="2"),
                discord.SelectOption(label="Silver", emoji=botemoji.valorant_silver, value="3"),
                discord.SelectOption(label="Gold", emoji=botemoji.valorant_gold, value="4"),
                discord.SelectOption(label="Platinum", emoji=botemoji.valorant_platinum, value="5"),
                discord.SelectOption(label="Diamond", emoji=botemoji.valorant_diamond, value="6"),
                discord.SelectOption(label="Ascendant", emoji=botemoji.valorant_ascendant, value="7"),
                discord.SelectOption(label="Immortal", emoji=botemoji.valorant_immortal, value="8"),
                discord.SelectOption(label="Radiant", emoji=botemoji.valorant_radiant, value="9")
               ]
    
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        
        @bot.ev.interaction(name=r"grank_rep\.(\d+)")
        async def on_grank_rep(interaction: discord.Interaction, user_id):
            if user_id == str(interaction.user.id):
                embed = discord.Embed(title="Loading Video")
                await interaction.response.edit_message(embed=embed, view=None, content=None)
                view = discord.ui.View(timeout=0)
                out = await get_game()
                view.add_item(discord.ui.Select(placeholder="Chọn Rank Của Người Chơi Này", custom_id=f"grank.{user_id}.{out['rank']}", options=self.ranklist))
                await interaction.message.edit(content=out["link"], embed=None, view=view)
            else:
                await interaction.response.send_message(f'**Nút này không dành cho bạn**', ephemeral=True)
        
        @bot.ev.interaction(name=r"grank\.(\d+)\.(\d+)")
        async def on_grank(interaction: discord.Interaction, user_id, real_rank):
            if user_id == str(interaction.user.id):
                userrank = self.ranklist[int(interaction.data["values"][0])-1]
                realrank = self.ranklist[int(real_rank)-1]
                view = discord.ui.View(timeout=0)
                view.add_item(discord.ui.Button(label="Chơi Lại", custom_id=f"grank_rep.{user_id}"))
                await interaction.response.edit_message(content=f'**Rank Bạn Chọn:** {userrank.emoji} {userrank.label}\n**Đáp Án:** {realrank.emoji} {realrank.label}\n\n{interaction.message.content}', view=view)
            else:
                await interaction.response.send_message(f'**Nút này không dành cho bạn**', ephemeral=True)
    
    @app_commands.command(name="guess_val_rank", description="Play Guess Valorant Rank on Discord")
    async def guessrank(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction)
        embed = discord.Embed(title="Loading Video")
        edit = await ctx.reply(embed=embed)
        view = discord.ui.View(timeout=0)
        out = await get_game()
        view.add_item(discord.ui.Select(placeholder="Chọn Rank Của Người Chơi Này", custom_id=f"grank.{ctx.author.id}.{out['rank']}", options=self.ranklist))
        await edit.edit(content=out["link"], embed=None, view=view)
    
async def setup(bot):
    await bot.add_cog(getrank(bot))