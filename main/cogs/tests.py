import discord
from discord.ext import commands
import traceback
import textwrap
from discord import app_commands
from contextlib import redirect_stdout
import io
import botemoji
from unity.interactx import Interactx

class EvalM(discord.ui.Modal):
    def __init__(self) -> None:
        super().__init__(title='Eval Input', timeout=60)
    
    answer = discord.ui.TextInput(label='Eval', style=discord.TextStyle.long)
    out = None
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.out = self.answer.value

# to expose to the eval command

class EvalE(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.value = None
        self.ctx = ctx

    @discord.ui.button(label='Eval', style=discord.ButtonStyle.gray)
    async def confirm(self, interaction: discord.Interaction,  button: discord.ui.Button):
        if interaction.user.id == self.ctx.author.id:
            md = EvalM()
            await interaction.response.send_modal(md)
            await md.wait()
            self.value = md.out
            self.stop()
        else:
            await interaction.response.send_message(f'Chỉ có **{self.ctx.author}** ấn được thôi', ephemeral=True)

class Admin(commands.Cog):
  def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self.sessions = set()

  def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

  def get_syntax_error(self, e):
        if e.text is None:
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

  @app_commands.command(name="admin_eval")
  async def eval(self, interaction: discord.Interaction):
    ctx = await Interactx(interaction, ephemeral=True)
    """Evaluates a code"""
    if ctx.author.id == 542602170080428063:
        view = EvalE(ctx)
        mess = await ctx.send(view=view)
        await view.wait()
        body = view.value
        if not body:
            return
        await mess.edit(content="**Loading Eval**", view=None)
        envs = """
bot = self.bot
ctx = ctx
channel = ctx.channel
author = ctx.author
guild = ctx.guild
message = ctx.message
server = ctx.guild
"""
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            'server': ctx.guild,
            'env' : envs
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env) #nosec
        except Exception as e:
            return await ctx.reply(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception:
            value = stdout.getvalue()
            out = f'```py\n{value}{traceback.format_exc()}\n```'
            if len(out) <= 2000:
                await mess.edit(content=out)
            else:
                await ctx.reply("Check Bot Log For Output")
                print(f"-- EVAL CONSOLE LOG --\n{out}\n-- EVAL CONSOLE END --\n")
        else:
            value = stdout.getvalue()
            try:
                await mess.add_reaction(botemoji.yes)
            except BaseException:
                pass

            if ret is None:
                if value:
                    out = f'```py\n{value}\n```'
                    if len(out) <= 2000:
                        await mess.edit(content=out)
                    else:
                        await ctx.reply("Check Bot Log For Output")
                        print(f"-- EVAL CONSOLE LOG --\n{out}\n-- EVAL CONSOLE END --\n")
            else:
                self._last_result = ret
                out = f'```py\n{value}{ret}\n```'
                if len(out) <= 2000:
                    await mess.edit(content=out)
                else:
                    await ctx.reply("Check Bot Log For Output")
                    print(f"-- EVAL CONSOLE LOG --\n{out}\n-- EVAL CONSOLE END --\n")
          

async def setup(bot):
    await bot.add_cog(Admin(bot))
