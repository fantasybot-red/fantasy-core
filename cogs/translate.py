import discord
import aiohttp
import re, json
from urllib.parse import quote
from discord import app_commands
from discord.ext import commands
from gpytranslate import Translator
from unity.interactx import Interactx
from songbird import SongBirdError
from unity.music_client_obj import Voice_Client_TTS

tran = Translator()
lang_list = {}



class Translate(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.ctx_menus = []
        tran_to_vi = app_commands.ContextMenu(
            name="Dịch sang tiếng Việt",
            callback=self.translate_to_vi,
        )
        self.ctx_menus.append(tran_to_vi)
        tran_to_en = app_commands.ContextMenu(
            name="Translate to English",
            callback=self.translate_to_en,
        )
        self.ctx_menus.append(tran_to_en)
        for ctx_menu in self.ctx_menus:
            self.bot.tree.add_command(ctx_menu)

    async def cog_unload(self) -> None:
        for ctx_menu in self.ctx_menus:
            self.bot.tree.remove_command(ctx_menu.name, type=ctx_menu.type)
    
    async def autocomplete_language(self, interaction: discord.Interaction, current: str, lang_list):
        if current:
            return [app_commands.Choice(name=key, value=key) for key in lang_list if current.lower() in key.lower()][:23]
        else:
            return [app_commands.Choice(name=key, value=key) for key in lang_list][:23]
    
    async def autocomplete_language_from(self, interaction: discord.Interaction, current: str):
        return await self.autocomplete_language(interaction, current, lang_list.values())
    
    async def autocomplete_language_to(self, interaction: discord.Interaction, current: str):
        return await self.autocomplete_language(interaction, current, list(lang_list.values())[1:])
    
    def get_lang_id(self, language):
        lang_id = None
        if language is None:
            lang_id = list(lang_list.keys())[0]
        else:
            for key, value in lang_list.items():
                if language.lower() == key.lower():
                    lang_id = key
                    break
                elif language.lower() == value.lower():
                    lang_id = key
                    break
        return lang_id
    
    async def translate_to_en(self, interaction: discord.Interaction, message: discord.Message):
        ctx = await Interactx(interaction)
        text = message.clean_content
        if not text:
            return await ctx.send("**Has no content to translate**")
        lang_id_to = "en"
        embed = discord.Embed(title="Translating...")
        edit = await ctx.reply(embed=embed)
        out_text = await tran.translate(text, targetlang=lang_id_to)
        embed = discord.Embed(title="Translate to English", description=out_text.text)
        await edit.edit(embed=embed)
    
    async def translate_to_vi(self, interaction: discord.Interaction, message: discord.Message):
        ctx = await Interactx(interaction)
        text = message.clean_content
        if not text:
            return await ctx.send("**Tin nhắn không có nội dung để dịch**")
        lang_id_to = "vi"
        embed = discord.Embed(title="Đang dịch văn bản")
        edit = await ctx.reply(embed=embed)
        out_text = await tran.translate(text, targetlang=lang_id_to)
        embed = discord.Embed(title="Dịch sang tiếng Việt", description=out_text.text)
        await edit.edit(embed=embed)
    
    @app_commands.command(name="translate", description="Dịch văn bản ban nhập vào")
    @app_commands.rename(from_="from")
    @app_commands.autocomplete(from_=autocomplete_language_from, to=autocomplete_language_to)
    @app_commands.describe(text="Nội dung bot cần dịch", from_="Ngỗn Ngữ vào | măc định: `Detect language`", to="Dích Đến Ngôn Ngữ")
    async def translate(self, interaction: discord.Interaction, text: app_commands.Range[str, 1, 2000], to: str, from_: str=None):
        ctx = await Interactx(interaction)
        lang_id_from = self.get_lang_id(from_)
        lang_id_to = self.get_lang_id(to)
        if lang_id_from is None or lang_id_to is None:
            return await ctx.reply("**Ngôn ngữ không hơp lệ**")
        elif lang_id_to == 'auto':
            return await ctx.reply("**Ngôn ngữ không hơp lệ**")
        elif lang_id_from == lang_id_to:
            return await ctx.reply("**Bruh thế cần gì phải dịch**")
        embed = discord.Embed(title="Đang dịch văn bản")
        edit = await ctx.reply(embed=embed)
        out_text = await tran.translate(text, sourcelang=lang_id_from, targetlang=lang_id_to)
        embed_from = discord.Embed(title=f"From {lang_list[lang_id_from]}", description=text)
        embed_to = discord.Embed(title=f"To {lang_list[lang_id_to]}", description=out_text.text)
        await edit.edit(embeds=[embed_from, embed_to])
        
    
    @app_commands.command(name="tts", description="Bot sẽ join vào voice của bạn và nói")
    @app_commands.autocomplete(language=autocomplete_language_from)
    @app_commands.describe(text="Nội dung bot cần nói", language="Giọng nói kiểu nước nào | măc định: `Detect language`")
    async def tts(self, interaction: discord.Interaction, text: app_commands.Range[str, 1, 200], language: str=None):
        ctx = await Interactx(interaction)
        
        lang_id = self.get_lang_id(language)
        
        if lang_id is None:
            return await ctx.reply("**Vui lòng nhập `language` hơp lệ**")
        
        if ctx.author.voice is None:
            return await ctx.reply("**Vào voice để dùng tts bro**")
        
        if ctx.voice_client is not None:
            if type(ctx.voice_client) is not Voice_Client_TTS:
                return await ctx.reply("**Bạn không thể chạy tts khi bot đang chạy tác vụ khác ở trong voice**")
            else:
                return await ctx.reply("**Vui long đợi bot chạy tts xong thì mới dùng command**")
        else:
            try:
                await ctx.author.voice.channel.connect(cls=Voice_Client_TTS)
            except SongBirdError:
                return await ctx.reply("**Tạm thời không thể chơi do không có TTS Node online**")
            await ctx.guild.change_voice_state(channel=ctx.channel, self_mute=False, self_deaf=True)
            if ctx.author.voice.channel.type == discord.ChannelType.stage_voice:
                try:
                    await ctx.guild.me.edit(suppress=False)
                except BaseException:
                    pass
            lang_str = await tran.detect(text) if lang_id == "auto" else lang_id
            audio_url = f"https://translate.google.com/translate_tts?tl={lang_str}&q={quote(text)}&client=tw-ob"
            async def after(is_err):
                await ctx.voice_client.disconnect()
            if ctx.voice_client is None:
                return await ctx.reply("**Bot hiện đang không ở trong voice để nói**")
            await ctx.voice_client.play(audio_url, after=after)
            await ctx.reply(f"**Đang nói: ```{discord.utils.escape_markdown(text)}```**")
        
        
        
        
async def setup(bot):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://translate.google.com/?hl=en") as resp:
            data = re.search(r"data:\[(\[\[\"auto\",\"Detect language\"].*?]]),", await resp.text()).group(1)
            for ids, name in json.loads(data):
                lang_list[ids] = name
    await bot.add_cog(Translate(bot))
