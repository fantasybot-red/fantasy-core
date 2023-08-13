import dataclasses
import aiohttp

headers_real = {"User-Agent": "Mozilla/5.0 (compatible; FantasyBot/0.1; +https://fantasybot.tech/support)"}


@dataclasses.dataclass
class Image:
    filename: str
    content: bytes


class ChatGPT:
    SSL_Mode = None

    def __init__(self):
        pass
    
    async def create_new_chat(self, data):
        async with aiohttp.ClientSession() as s:
            data = {
                "prompt": data,
                "options": {},
                "systemMessage": ".",
                "temperature": 0.8,
                "top_p": 1,
                "model": "gpt-3.5-turbo",
                "user": None
            }
            async with s.post("https://p5.v50.ltd/api/chat-process", json=data) as r:
                return await r.text()