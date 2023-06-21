from discord.ext import commands
import os
import statcord
import discord
from unity.interactx import Interactx

class StatcordPost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.key = os.getenv("STATCORD_TOKEN")
        self.api = statcord.Client(self.bot, self.key, debug=True)
        self.api.start_loop()
        
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.application_command:
            if interaction.command is not None:
                ctx = await Interactx(interaction, start=False)
                self.api.command_run(ctx)
                


async def setup(bot):
    await bot.add_cog(StatcordPost(bot))