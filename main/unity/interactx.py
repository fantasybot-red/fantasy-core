import discord
import asyncio
from discord.ext import commands
from jkeydb import database

rate_limit = {}

class CommandRateLimit(Exception):
    pass


async def check(userid):
    await asyncio.sleep(4)
    old_id = rate_limit.get(str(userid), 0)
    rate_limit[str(userid)] = old_id - 1
    if rate_limit[str(userid)] < 1:
        del rate_limit[str(userid)]
        
async def ratelimit_check(obj):
    userid = obj.user.id
    old_id = rate_limit.get(str(userid), 0)
    rate_limit[str(userid)] = old_id + 1
    with database(f"./data/ratelimit", obj.client.db) as db:
        if rate_limit.get(str(userid), 0) >= 3 or db.get(str(obj.user.id)):
            del rate_limit[str(userid)]
            db[str(obj.user.id)] = True
            return True
    asyncio.create_task(check(userid))
    return False

async def Interactx(obj: discord.Interaction, *, ephemeral: bool = False, start: bool = True) -> commands.Context:
    if type(obj) is discord.Interaction:
        newctx = await obj.client.get_context(obj)
        userid = obj.user.id
        if start:
            await newctx.defer(ephemeral=ephemeral)
    else:
        newctx = obj
    return newctx