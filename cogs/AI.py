import discord
import traceback
from discord import app_commands
from discord.ext import commands
from unity.chatgpt import ChatGPT
from unity.image_ai import AI_NSFW
from unity.interactx import Interactx

chatgpt_cl = ChatGPT()
img_ai = AI_NSFW()

class AI(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    g_ai = app_commands.Group(name="ai", description="ai command")

    @g_ai.command(name="chatgpt", description="Use ChatGPT by OpenAI on Discord")
    @app_commands.describe(data="Input for ChatGPT")
    async def chatgpt(self, interaction: discord.Interaction, data: str):
        ctx = await Interactx(interaction)
        embed = discord.Embed(title="Waiting Response From ChatGPT")
        edit = await ctx.reply(embed=embed)
        embeds = []
        try:
            gptcontent = await chatgpt_cl.create_new_chat(data)
        except BaseException:
            traceback.print_exc()
            gptcontent = "No Response"
        ai = f"**AI: **{gptcontent}"
        embed = discord.Embed(title="ChatGpt", description=f"**{ctx.author.mention}: ** {discord.utils.escape_markdown(data[:4096])}")
        embeds.append(embed)
        embed = discord.Embed(description=ai)
        embeds.append(embed)
        await edit.edit(embeds=embeds)
    
    @g_ai.command(name="image_generator", description="Use Dall-E by OpenAI on Discord")
    @app_commands.describe(data="Input for Use Dall-E")
    async def dalle(self, interaction: discord.Interaction, data: str):
        ctx = await Interactx(interaction)
        embed = discord.Embed(title="Waiting Response From Use Dall-E")
        edit = await ctx.reply(embed=embed)
        try:
            gptcontent = await chatgpt_cl.create_new_image(data)
        except BaseException:
            traceback.print_exc()
            embed = discord.Embed(title="Dall-E Error")
            await edit.edit(embed=embed)
            return
        embed = discord.Embed(title="Dall-E")
        embed.set_image(url=gptcontent)
        await edit.edit(embed=embed)
        
    async def style_name_autocomplete(self, interaction, current: str):
        if not current:
            return [app_commands.Choice(name=key, value=key) for key in await img_ai.get_styles_list()][:23]
        return [app_commands.Choice(name=key, value=key) for key in await img_ai.get_styles_list() if current.lower() in key.lower()][:23]
    
    async def engine_name_autocomplete(self, interaction, current: str):
        if not current:
            return [app_commands.Choice(name=key, value=key) for key in await img_ai.get_engines_list()][:23]
        return [app_commands.Choice(name=key, value=key) for key in await img_ai.get_engines_list() if current.lower() in key.lower()][:23]
    
    describe_nsfw_image_generator = {
        "prompt": "AI tries to make you what you write in the prompt. Start off with a simple prompt and start adding words and sentences. Add (paranthesis around) to emphasize words; this means the AI will pay more attention to them", 
        "negative_prompt": "AI avoids rendering the concepts written here. Add ((paranthesis around)) to emphasize words; this means the AI will be 'reminded' to really avoid them", 
        "seed": "Same seed with same prompt generates the same image.", 
        "engine_name": "The engine (model) is what the AI uses to generate the image.", 
        "style_name": "Style is a combination of 'engine', prompts and negative prompts.",
        "width": "Image Width", 
        "height": "Image Height", 
        "denoising_strength": "Denoising strength determines how much noise is added to an image before the sampling steps.", 
        "cfg": "Classifier-Free Guidance tells the AI how much prompt instructions are followed."
    }
    
    @g_ai.command(name="nsfw_image_generator", description="Make an NSFW image from prompt", nsfw=True)
    @app_commands.autocomplete(style_name=style_name_autocomplete, engine_name=engine_name_autocomplete)
    @app_commands.describe(**describe_nsfw_image_generator)
    async def nsfw_image_generator(self, interaction: discord.Interaction, prompt: str, style_name: str, negative_prompt: str="", seed: app_commands.Range[int, 1, img_ai.max_seed-1] = 0, engine_name: str=None, width: app_commands.Range[int, 512, 760]=512, height: app_commands.Range[int, 512, 760]=640, denoising_strength: app_commands.Range[int, 0, 10] = 4, cfg: float=7.5):
        ctx = await Interactx(interaction)
        if not ctx.channel.is_nsfw():
            await ctx.send("This command can only be used in NSFW channels.")
            return
        elif engine_name is not None and engine_name not in await img_ai.get_engines_list():
            await ctx.send("**Invalid engine name.**")
            return
        elif style_name not in await img_ai.get_styles_list():
            await ctx.send("**Invalid style name.**")
            return
        mess = await ctx.send(embed=discord.Embed(title="Generating image..."))
        config = {
            "prompt": prompt, 
            "style_name": style_name, 
            "negative_prompt": negative_prompt, 
            "seed": seed, 
            "engine_name": engine_name, 
            "width": width, 
            "height": height, 
            "denoisingStrength": (denoising_strength / 10),
            "cfg": cfg
        }
        try:
            img, seed = await img_ai.generate_image(**config)
        except KeyError:
            embed = discord.Embed(title="AI generate failed", description=f"System Overload")
            return await mess.edit(embed=embed)
        except BaseException:
            traceback.print_exc()
            embed = discord.Embed(title="AI generate error")
            return await mess.edit(embed=embed)
        embed = discord.Embed(title="Nsfw AI Img", description=f"**Seed_ID:** {seed}")
        embed.set_image(url="attachment://image.png")
        file = discord.File(img, filename="image.png")
        await mess.edit(embed=embed, attachments=[file])
        



async def setup(bot):
    await bot.add_cog(AI(bot))
