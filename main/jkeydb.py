import pickle  #nosec
import base64
import os
import redis
from cryptography.fernet import Fernet, MultiFernet

class database(dict):
    def __init__(self, filename, redisdb: redis.Redis, raise_on_error=False):
        self.redisdb = redisdb
        self.filename = filename
        key = self.redisdb.exists(filename)
        if key == 0 and raise_on_error is True:
            raise FileNotFoundError()

    def encode(self, data):
        key = os.getenv("DB_KEY")
        if key is None:
            raise KeyError("DB_KEY is not in env")
        if len(data) != 0:
            skey = Fernet.generate_key()
            fn = Fernet(skey)
            fn2 = Fernet(key)
            mainfn = MultiFernet([fn, fn2])
            adata = {"k": skey, "d": mainfn.encrypt(pickle.dumps(data))}
            return  base64.urlsafe_b64encode(pickle.dumps(adata))
        elif self.redisdb.exists(self.filename) == 1:
            self.redisdb.delete(self.filename)
    
    def decode(self, data):
        key = os.getenv("DB_KEY")
        if key is None:
            raise KeyError("DB_KEY is not in env")
        if self.redisdb.exists(self.filename) == 1:
            data = pickle.loads(base64.urlsafe_b64decode(data)) #nosec
            fn = Fernet(data["k"])
            fn2 = Fernet(key)
            mainfn = MultiFernet([fn, fn2])
            return pickle.loads(mainfn.decrypt(data["d"])) #nosec
        else:
            return {}
            
    def clear(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.clear(*args, **kwargs)
        self.redisdb.set(self.filename, self.encode(file))
        return data

    def copy(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.copy(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def fromkeys(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.fromkeys(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def get(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.get(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def items(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.items(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def keys(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.keys(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def pop(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.pop(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def setdefault(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.setdefault(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def update(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.update(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def values(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.values(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def __class_getitem__(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.__class_getitem__(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def __contains__(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.__contains__(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def __delitem__(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.__delitem__(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def __eq__(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.__eq__(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def __getitem__(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.__getitem__(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def __ge__(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.__ge__(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def __gt__(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.__gt__(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def __ior__(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.__ior__(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def __iter__(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.__iter__(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def __len__(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.__len__(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def __le__(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.__le__(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def __lt__(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.__lt__(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def __ne__(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.__ne__(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def __or__(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.__or__(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def __repr__(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.__repr__(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def __reversed__(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.__reversed__(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def __ror__(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.__ror__(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def __setitem__(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.__setitem__(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data

    def __sizeof__(self, *args, **kwargs):
        file = self.decode(self.redisdb.get(self.filename))
        data = file.__sizeof__(*args, **kwargs)
        save_out = self.encode(file)
        if save_out is not None:
            self.redisdb.set(self.filename, save_out)
        return data
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        pass
        

