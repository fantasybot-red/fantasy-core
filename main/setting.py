from jkeydb import database

def savesetting(serverid, setting, value, db):
    if value is not None:
        with database(f"./data/setting/{serverid}", db) as db:
            db[setting] = value
    else:
        with database(f"./data/setting/{serverid}", db) as db:
            try:
                del db[setting]
            except KeyError:
                pass

def save_setting_list_add(serverid, setting, value, db):
    with database(f"./data/setting/{serverid}", db) as db:
        a = db.get(setting, [])
        a.append(value)

def save_setting_list_remove(serverid, setting, value, db):
    with database(f"./data/setting/{serverid}", db) as db:
        a:list = db.get(setting, [])
        if value in a:
            a.remove(value)
            if len(a) > 0:
                db[setting] = a
            else:
                try:
                    del db[setting]
                except KeyError:
                    pass
          
def getsetting(serverid, setting, db):
    with database(f"./data/setting/{serverid}", db) as db:
        config = db.get(setting)
    return config 