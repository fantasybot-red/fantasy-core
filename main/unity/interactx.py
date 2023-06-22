import discord
from discord.ext import commands

async def Interactx(obj: discord.Interaction, *, ephemeral: bool = False, start: bool = True) -> commands.Context:
    if type(obj) is discord.Interaction:
        newctx = await obj.client.get_context(obj)
        if start:
            await newctx.defer(ephemeral=ephemeral)
    else:
        newctx = obj
    return newctx