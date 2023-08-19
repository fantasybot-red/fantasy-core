import dataclasses
import aiohttp
import hashlib
import time

headers_real = {"User-Agent": "Mozilla/5.0 (compatible; FantasyBot/0.1; +https://fantasybot.tech/support)"}


@dataclasses.dataclass
class Image:
    filename: str
    content: bytes
    


def digestMessage(r):
    e = r.encode()
    t = hashlib.sha256(e).digest()
    return ''.join(format(byte, '02x') for byte in t)


class ChatGPT:
    SSL_Mode = None

    def __init__(self):
        pass
    
    async def create_new_chat(self, data):
        async with aiohttp.ClientSession() as s:
            times_ms = int(time.time() * 1000)
            sign = digestMessage(f"{times_ms}:{data}:")
            data = {
                "messages": [
                    {
                        "role": "user",
                        "content": data
                    }
                ],
                "time": times_ms,
                "pass": None,
                "sign": sign
            }
            async with s.post('https://d.aifree.site/api/generate', json=data) as r:
                return await r.text()