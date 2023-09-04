import discord
import asyncio
from discord.ext import commands
from jkeydb import database

rate_limit = {}

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
    get_components_d(["components"])
    return rdata
        
                
                
    return {}