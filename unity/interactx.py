import discord
from discord.ext import commands
from discord.ext.commands.view import StringView   

async def Interactx(obj: discord.Interaction, *, ephemeral: bool = False, start: bool = True) -> commands.Context:
    if type(obj) is discord.Interaction:
        if obj.command is None:
            bot  = obj.client
            data = obj.data
            command = discord.app_commands.Command(name="_", description="_", callback=lambda x: x)
            synthetic_payload = {
                    'id': obj.id,
                    'reactions': [],
                    'embeds': [],
                    'mention_everyone': False,
                    'tts': False,
                    'pinned': False,
                    'edited_timestamp': None,
                    'type': discord.MessageType.chat_input_command,
                    'flags': 64,
                    'content': '',
                    'mentions': [],
                    'mention_roles': [],
                    'attachments': [],
                }

            if obj.channel_id is None:
                raise RuntimeError('interaction channel ID is null, this is probably a Discord bug')

            channel = obj.channel or discord.PartialMessageable(
                state=obj._state, guild_id=obj.guild_id, id=obj.channel_id
            )
            message = discord.Message(state=obj._state, channel=channel, data=synthetic_payload)  # type: ignore
            message.author = obj.user
            message.attachments = [a for _, a in obj.namespace if isinstance(a, discord.Attachment)]

            prefix = '/' if data.get('type', 1) == 1 else '\u200b'  # Mock the prefix
            ctx = commands.Context(
                message=message,
                bot=bot,
                view=StringView(''),
                args=[],
                kwargs={},
                prefix=prefix,
                interaction=obj,
                invoked_with=command.name,
                command=command,
            )
            obj._baton = ctx
            ctx.command_failed = obj.command_failed
            newctx = ctx
        else:
            newctx = await obj.client.get_context(obj)
        if start:
            await newctx.defer(ephemeral=ephemeral)
    else:
        newctx = obj
    return newctx

def get_components(obj: discord.Interaction) -> dict:
    rdata = {}
    def get_components_d(data: list):
        for i in data:
            if i["type"] == 1:
                get_components_d(i["components"])
            elif i["type"] == 4:
                rdata[i["custom_id"]] = i["value"]
            elif i["type"] == 3:
                rdata[i["custom_id"]] = i["values"]
            else:
                rdata[i["custom_id"]] = None
    if obj.data.get("components") is None:
        return
    get_components_d(obj.data["components"])
    return rdata