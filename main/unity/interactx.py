import discord
import asyncio
from discord.ext import commands
from jkeydb import database

rate_limit = {}

class CommandRateLimit(BaseException):
    pass


async def check(userid, db):
    await asyncio.sleep(5)
    old_id = rate_limit.get(str(userid), 0)
    rate_limit[str(userid)] = old_id - 1
    if rate_limit[str(userid)] < 1:
        del rate_limit[str(userid)]

async def Interactx(obj: discord.Interaction, *, ephemeral: bool = False, start: bool = True) -> commands.Context:
    if type(obj) is discord.Interaction:
        newctx = await obj.client.get_context(obj)
        userid = obj.user.id
        if start:
            old_id = rate_limit.get(str(userid), 0)
            rate_limit[str(userid)] = old_id + 1
            asyncio.create_task(check(userid))
            with database(f"./data/ratelimit", obj.client.db) as db:
                if rate_limit.get(str(userid), 0) >= 4:
                    db[str(obj.user.id)] = True
                    raise CommandRateLimit()
            await newctx.defer(ephemeral=ephemeral)
    else:
        newctx = obj
    return newctx