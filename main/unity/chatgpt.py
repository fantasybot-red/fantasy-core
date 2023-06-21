import dataclasses
import uuid
import aiohttp
import base64
import random
from aiohttp.client_exceptions import ClientResponseError

headers_real = {"User-Agent": "Mozilla/5.0 (compatible; FantasyBot/0.1; +https://fantasybot.tech/support)"}


@dataclasses.dataclass
class Image:
    filename: str
    content: bytes


class ChatGPT:
    SSL_Mode = None

    def __init__(self):
        self.tokenlist = ["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"]

    async def authenticate(self):
        return "Bearer " + random.choice(self.tokenlist)  # nosec

    async def create_new_chat(self, data, web=False):
        limit = ""
        if not web:
            limit = "and AI output must below 4000 characters"
        messlist = [{"role": "system", "content": f"AI has markdown support and your name is ChatGPT and made by OpenAI{limit}."}]
        if type(data) is str:
            messlist.extend([{"role": "user", "content": data}])
        else:
            messlist.extend(data)
        headers = headers_real.copy()
        while True:
            headers["Authorization"] = await self.authenticate()
            try:
                async with aiohttp.ClientSession(headers=headers) as s:
                    async with s.post(f"https://api.openai.com/v1/chat/completions",
                                    timeout=None,
                                    ssl=self.SSL_Mode,
                                    raise_for_status=True,
                                    json={
                                            "model": "gpt-3.5-turbo",
                                            "messages": messlist,
                                            "temperature": 0.6
                                            }
                                    ) as r:
                        return (await r.json())["choices"][0]["message"]["content"].strip()
            except ClientResponseError as e:
                if e.status != 429:
                    raise e

    async def create_dalle(self, data, token=None):
        headers = headers_real.copy()
        headers["Authorization"] = await self.authenticate() if token is None else "Bearer " + token
        async with aiohttp.ClientSession(headers=headers) as s:
            async with s.post(f"https://api.openai.com/v1/images/generations",
                              timeout=None,
                              raise_for_status=True,
                              json={
                                  "prompt": data,
                                  "response_format": "b64_json"
                              }) as r:
                base64data = (await r.json())["data"][0]["b64_json"]
                imgdata = base64.b64decode(base64data)
                filename = f'{uuid.uuid4().hex}.jpg'
                return Image(**{"filename": filename, "content": imgdata})

