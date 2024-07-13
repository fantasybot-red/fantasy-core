from jkeydb import database

async def savesetting(serverid, setting, value, db):
    async with database(f"./data/setting/{serverid}", db) as db:
        if value is not None:
            await db.set(setting, value)
        else:
            try:
                await db.remove(setting)
            except KeyError:
                pass
          
async def getsetting(serverid, setting, db):
    async with database(f"./data/setting/{serverid}", db) as db:
        config = await db.get(setting)
    return config 