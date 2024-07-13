import os
import io
import discord
import textwrap
import botemoji
import traceback
from discord.ext import commands
from discord import app_commands
from unity.interactx import Interactx
from contextlib import redirect_stdout


class EvalM(discord.ui.Modal):
    def __init__(self) -> None:
        super().__init__(title="Eval Input", timeout=60)

    answer = discord.ui.TextInput(label="Eval", style=discord.TextStyle.long)
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

    @discord.ui.button(label="Eval", style=discord.ButtonStyle.gray)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id == self.ctx.author.id:
            md = EvalM()
            await interaction.response.send_modal(md)
            await md.wait()
            self.value = md.out
            self.stop()
        else:
            await interaction.response.send_message(
                f"Chỉ có **{self.ctx.author}** ấn được thôi", ephemeral=True
            )


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self.sessions = set()

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])

        # remove `foo`
        return content.strip("` \n")

    def get_syntax_error(self, e):
        if e.text is None:
            return f"```py\n{e.__class__.__name__}: {e}\n```"
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'
    
    g_debug = app_commands.Group(name="debug", description="debug command")
    
    @g_debug.command(name="eval")
    async def eval(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction, ephemeral=True)
        """Evaluates a code"""
        if ctx.author.id != 542602170080428063:
            return await ctx.reply(
                "Command này không dành cho bạn[.](https://fantasybot.xyz/assets/Uh%20uh%20uh,%20access%20denied.mp4)"
            )
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
                "bot": self.bot,
                "ctx": ctx,
                "channel": ctx.channel,
                "author": ctx.author,
                "guild": ctx.guild,
                "message": ctx.message,
                "server": ctx.guild,
                "env": envs,
            }

            env.update(globals())

            body = self.cleanup_code(body)
            stdout = io.StringIO()

            to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

            try:
                exec(to_compile, env)  # nosec
            except Exception as e:
                return await mess.edit(content=f"```py\n{e.__class__.__name__}: {e}\n```")

            func = env["func"]
            try:
                with redirect_stdout(stdout):
                    ret = await func()
            except Exception:
                value = stdout.getvalue()
                out = f"```py\n{value}{traceback.format_exc()}\n```"
                if len(out) <= 2000:
                    await mess.edit(content=out)
                else:
                    await mess.edit(content="Check Bot Log For Output")
                    print(f"-- EVAL CONSOLE LOG --\n{out}\n-- EVAL CONSOLE END --\n")
            else:
                value = stdout.getvalue()
                try:
                    await mess.add_reaction(botemoji.yes)
                except BaseException:
                    pass

                if ret is None:
                    if value:
                        out = f"```py\n{value}\n```"
                        if len(out) <= 2000:
                            await mess.edit(content=out)
                        else:
                            await mess.edit(content="Check Bot Log For Output")
                            print(
                                f"-- EVAL CONSOLE LOG --\n{out}\n-- EVAL CONSOLE END --\n"
                            )
                else:
                    self._last_result = ret
                    out = f"```py\n{value}{ret}\n```"
                    if len(out) <= 2000:
                        await mess.edit(content=out)
                    else:
                        await mess.edit(content="Check Bot Log For Output")
                        print(
                            f"-- EVAL CONSOLE LOG --\n{out}\n-- EVAL CONSOLE END --\n"
                        )

    async def cogs_autocomplete(self, interaction: discord.Interaction, current: str):
        if interaction.user.id != 542602170080428063:
            return [app_commands.Choice(name="Bruh This is Admin Command", value=":\\")]
        return [
            app_commands.Choice(name=fruit[:-3], value=fruit[:-3])
            for fruit in os.listdir("./cogs")
            if current.lower() in fruit.lower() and fruit.endswith(".py")
        ]

    @g_debug.command(name="cogs")
    @app_commands.choices(
        ad=[
            app_commands.Choice(name="Add", value="+"),
            app_commands.Choice(name="Reload", value="r"),
            app_commands.Choice(name="remove", value="-"),
        ]
    )
    @app_commands.autocomplete(eten=cogs_autocomplete)
    async def cogs(
        self, interaction: discord.Interaction, ad: app_commands.Choice[str], eten: str
    ):
        ctx = await Interactx(interaction, ephemeral=True)
        if ctx.author.id != 542602170080428063:
            return await ctx.reply(
                "Command này không dành cho bạn[.](https://fantasybot.xyz/assets/Uh%20uh%20uh,%20access%20denied.mp4)"
            )

        ad = ad.value
        if ad == "+":
            try:
                await self.bot.load_extension(f"cogs.{eten}")
                await ctx.send(f"Đã add Cogs {eten}")
            except Exception:
                await ctx.send(f"```py\n{traceback.format_exc()}\n```")

        if ad == "r":
            try:
                await self.bot.reload_extension(f"cogs.{eten}")
                await ctx.send(f"Đã reload Cogs {eten}")
            except Exception:
                await ctx.send(f"```py\n{traceback.format_exc()}\n```")

        if ad == "-":
            try:
                await self.bot.unload_extension(f"cogs.{eten}")
                await ctx.send(f"Cogs {eten} đã bị remove")
            except Exception:
                await ctx.send(f"```py\n{traceback.format_exc()}\n```")

    @g_debug.command(name="err")
    async def err(self, interaction: discord.Interaction):
        ctx = await Interactx(interaction, ephemeral=True)
        if ctx.author.id != 542602170080428063:
            return await ctx.reply(
                "Command này không dành cho bạn[.](https://fantasybot.xyz/assets/Uh%20uh%20uh,%20access%20denied.mp4)"
            )
        raise Exception("Test Error")

async def setup(bot):
    await bot.add_cog(Admin(bot))
