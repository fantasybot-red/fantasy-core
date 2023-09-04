import discord
import traceback
from unity.interactx import Interactx
from unity import nhentai 
from discord.ext import commands
from discord import app_commands

class Confirm(discord.ui.View):
    def __init__(self, a, ctx):
        super().__init__(timeout=60)
        self.page = 0
        self.value = None
        self.ctx = ctx
        self.titles = a.titles["pretty"]
        self.pages = a.pages
        self.id = a.id
        self.value = None
        self.ctx = ctx
        self.url = a.url
        self.add_item(discord.ui.Button(label="Read on Browser", url=f"https://nhentai.net/g/{self.id}"))

    @discord.ui.button(label='Read on Discord', style=discord.ButtonStyle.gray)
    async def confirm(self, interaction: discord.Interaction,  button: discord.ui.Button):
        if interaction.user.id == self.ctx.author.id:
          embed = discord.Embed(title=self.titles,
                                      description=f"**Code:** [{self.id}]({self.url})\n**Page:** {self.page + 1}/{len(self.pages)}")
          embed.set_image(url=self.pages[self.page].url)
          await interaction.response.edit_message(embed=embed)
          self.value = True
          self.stop()
        else:
          await interaction.response.send_message(f'Chỉ có **{self.ctx.author}** ấn được thôi', ephemeral=True)

class nhentais(discord.ui.View):
        def __init__(self, a, ctx):
            super().__init__(timeout=600)
            self.page = 0
            self.value = None
            self.ctx = ctx
            self.titles = a.titles["pretty"]
            self.pages = a.pages
            self.id = a.id
            self.url = a.url

        @discord.ui.button(style=discord.ButtonStyle.gray, label="<<")
        async def start(self, interaction: discord.Interaction,  button: discord.ui.Button):
            if interaction.user.id == self.ctx.author.id:
                self.page = 0
                embed = discord.Embed(title=self.titles,
                                      description=f"**Code:** [{self.id}]({self.url})\n**Page:** {self.page + 1}/{len(self.pages)}")
                embed.set_image(url=self.pages[self.page].url)
                await interaction.response.edit_message(embed=embed)
            else:
                await interaction.response.send_message(f'Chỉ có **{self.ctx.author}** ấn được thôi', ephemeral=True)

        @discord.ui.button(style=discord.ButtonStyle.gray, label="<")
        async def back(self, interaction: discord.Interaction,  button: discord.ui.Button):
            if interaction.user.id == self.ctx.author.id:
                if 0 < self.page:
                  self.page -= 1
                  embed = discord.Embed(title=self.titles, description=f"**Code:** [{self.id}]({self.url})\n**Page:** {self.page + 1}/{len(self.pages)}")
                  embed.set_image(url=self.pages[self.page].url)
                  await interaction.response.edit_message(embed=embed)
            else:
                await interaction.response.send_message(f'Chỉ có **{self.ctx.author}** ấn được thôi', ephemeral=True)

        @discord.ui.button(style=discord.ButtonStyle.gray, label=">")
        async def skip(self, interaction: discord.Interaction,  button: discord.ui.Button):
            if interaction.user.id == self.ctx.author.id:
                if self.page < int(len(self.pages) - 1):
                    self.page += 1
                    embed = discord.Embed(title=self.titles,
                                          description=f"**Code:** [{self.id}]({self.url})\n**Page:** {self.page + 1}/{len(self.pages)}")
                    embed.set_image(url=self.pages[self.page].url)
                    await interaction.response.edit_message(embed=embed)
            else:
                await interaction.response.send_message(f'Chỉ có **{self.ctx.author}** ấn được thôi', ephemeral=True)

        @discord.ui.button(style=discord.ButtonStyle.gray, label=">>")
        async def end(self, interaction: discord.Interaction,  button: discord.ui.Button):
            if interaction.user.id == self.ctx.author.id:
                self.page = len(self.pages) - 1
                embed = discord.Embed(title=self.titles,
                                      description=f"**Code:** [{self.id}]({self.url})\n**Page:** {self.page + 1}/{len(self.pages)}")
                embed.set_image(url=self.pages[self.page].url)
                await interaction.response.edit_message(embed=embed)
            else:
                await interaction.response.send_message(f'Chỉ có **{self.ctx.author}** ấn được thôi', ephemeral=True)

class nhentaia(commands.Cog):
    def __init__(self, bot):
      self.bot = bot

    @app_commands.command(name="nhenta_i", description="Đọc or xem info truyên trên nhaiten", nsfw=True)
    @app_commands.describe(arg="ID Doujin")
    @app_commands.rename(arg="code")
    async def nht(self, interaction: discord.Interaction, arg:int):
        ctx = await Interactx(interaction)

        if not arg is None:
            embed = discord.Embed(title="Loading Doujin")
            edit = await ctx.reply(embed=embed)
            try:
                a = await nhentai.get_doujin(int(arg))
                tags = [f"[`{i.name}`](https://nhentai.net{i.url})" for i in a.tags if i.type == "tag"]
                embed = discord.Embed(title=a.titles["pretty"], description=f"**Code:** {a.id}\n**Tag:** {', '.join(tags)}")
                embed.set_image(url=a.thumbnail)
                view = Confirm(a, ctx)
                await edit.edit(embed=embed, view=view)
                await view.wait()
                if view.value is None:
                   try:
                        await edit.edit("**TimeOut**", view=discord.ui.View(timeout=0).clear_items())
                   except BaseException:
                      pass
                if view.value:
                  view = nhentais(a, ctx)
                  await edit.edit(view=view)
                  await view.wait()
                  if view.value is None:
                    try:
                        await edit.edit("**TimeOut**", view=discord.ui.View(timeout=0).clear_items())
                    except BaseException:
                        pass
            except Exception:
                traceback.print_exc()
                embed = discord.Embed(title="**ID Không Đúng**")
                await edit.edit(embed=embed)
        

    
async def setup(bot):
    await bot.add_cog(nhentaia(bot))