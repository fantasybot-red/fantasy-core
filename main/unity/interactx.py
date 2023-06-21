import datetime
import discord
from discord.ext import commands

class permissions(Exception):
    pass

class timeout(Exception):
    pass

class RAWInteractx(commands.Context):
    startd = False
    def __init__(self, obj: discord.Interaction, ephemeral: bool) -> None:
        self.obj = obj
        self.author = obj.user
        self.channel = obj.channel
        self.guild = obj.guild
        self.bot = obj.client
        self.command = obj.command
        self.command_failed = obj.command_failed
        self.interaction = obj
        self.is_expired = False
        self.ephemeral = ephemeral
        self.bot_permissions = obj.app_permissions

    async def start(self):
        if not self.startd:
            self.startd = True
            self.message = None
            if self.channel.permissions_for(self.guild.me).send_messages:
                if discord.utils.utcnow() <= (self.obj.created_at + datetime.timedelta(seconds=3)):
                    await self.obj.response.defer(thinking=True, ephemeral=self.ephemeral)
                    self.message = None
                else:
                    raise timeout()
            else:
                if discord.utils.utcnow() <= (self.obj.created_at + datetime.timedelta(seconds=3)):
                    await self.obj.response.send_message("**Bot không có quyền gửi tin nhắn ở kênh này!**", ephemeral=True)
                raise permissions()
            return self

    @property
    def voice_client(self):
        return self.guild.voice_client

    async def send(self, content=None, **data):
        if content is not None:
            data["content"] = content
        if not self.is_expired:
            self.message = await self.obj.followup.send(**data)
        else:
            self.message = await self.message.reply(**data)
        return self.message
    
    async def reply(
        self, content=None, **data):
        
        if content is not None:
            data["content"] = content
    
        message = await self.send(**data)
        return message
        
async def Interactx(obj: discord.Interaction, *, ephemeral:bool=False, start:bool=True) -> RAWInteractx:
    if type(obj) is discord.Interaction:
        newctx = RAWInteractx(obj=obj, ephemeral=ephemeral)
    else:
        newctx = obj
    if start:
        await newctx.start()
    return newctx
    