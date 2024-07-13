import os
import base64
import pickle  # nosec
from typing import Self
import redis.asyncio as redis
from cryptography.fernet import Fernet, MultiFernet

class database:
    def __init__(self, filename, redisdb: redis.Redis, raise_on_error=False):
        self.redisdb = redisdb
        self.filename = filename
        self.raise_on_error = raise_on_error

    async def __aenter__(self) -> Self:
        if self.raise_on_error is True:
            if (await self.redisdb.exists(self.filename)) == 0:
                raise FileNotFoundError()
        return self

    async def encode(self, data):
        key = os.getenv("DB_KEY")
        if key is None:
            raise KeyError("DB_KEY is not in env")
        if len(data) != 0:
            skey = Fernet.generate_key()
            fn = Fernet(skey)
            fn2 = Fernet(key)
            mainfn = MultiFernet([fn, fn2])
            adata = {"k": skey, "d": mainfn.encrypt(pickle.dumps(data))}
            raw_encrypted = base64.urlsafe_b64encode(pickle.dumps(adata))  # nosec
            await self.redisdb.set(self.filename, raw_encrypted)
        else:
            await self.redisdb.delete(self.filename)

    async def decode(self) -> dict:
        data = await self.redisdb.get(self.filename)
        key = os.getenv("DB_KEY")
        if key is None:
            raise KeyError("DB_KEY is not in env")
        if (await self.redisdb.exists(self.filename)) == 1:
            data = pickle.loads(base64.urlsafe_b64decode(data))  # nosec
            fn = Fernet(data["k"])
            fn2 = Fernet(key)
            mainfn = MultiFernet([fn, fn2])
            return pickle.loads(mainfn.decrypt(data["d"]))  # nosec
        else:
            return {}

    async def clear(self, *args, **kwargs):
        file = await self.decode()
        data = file.clear(*args, **kwargs)
        await self.encode(file)
        return data

    async def get(self, *args, **kwargs):
        file = await self.decode()
        data = file.get(*args, **kwargs)
        await self.encode(file)
        return data
    
    async def set(self, key, value):
        file = await self.decode()
        file[key] = value
        await self.encode(file)
    
    async def remove(self, key):
        file = await self.decode()
        try:
            del file[key]
            await self.encode(file)
        except KeyError:
            pass
        
    
    async def items(self, *args, **kwargs):
        file = await self.decode()
        data = file.items(*args, **kwargs)
        await self.encode(file)
        return data

    async def keys(self, *args, **kwargs):
        file = await self.decode()
        data = file.keys(*args, **kwargs)
        await self.encode(file)
        return data

    async def pop(self, *args, **kwargs):
        file = await self.decode()
        data = file.pop(*args, **kwargs)
        await self.encode(file)
        return data

    async def popitem(self, *args, **kwargs):
        file = await self.decode()
        data = file.popitem(*args, **kwargs)
        await self.encode(file)
        return data

    async def setdefault(self, *args, **kwargs):
        file = await self.decode()
        data = file.setdefault(*args, **kwargs)
        await self.encode(file)
        return data

    async def update(self, *args, **kwargs):
        file = await self.decode()
        data = file.update(*args, **kwargs)
        await self.encode(file)
        return data

    async def values(self, *args, **kwargs):
        file = await self.decode()
        data = file.values(*args, **kwargs)
        await self.encode(file)
        return data

    async def all(self):
        file = await self.decode()
        return file

    def __aexit__(self, exc_type, exc_val, exc_tb):
        return self

    def __await__(self):
        return self.__aenter__().__await__()
