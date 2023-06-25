from jkeydb import database

def get_prefix(ctx):
    guild =  str(ctx.guild.id)
    db = ctx.bot.db
    with database("./data/prefix", db) as db:
        default_prefix = get_prefix_db(guild, db)
    return default_prefix

def get_prefix_db(guild, db):
    try:
        del db[str(guild)]
    except BaseException:
        default_prefix = "/"
    return default_prefix