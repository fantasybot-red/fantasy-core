import dataclasses
import aiohttp
from aiohttp.client_exceptions import ClientResponseError

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
        messlist = [{"role": "system", "content": "AI has markdown support and your name is ChatGPT and made by OpenAI and AI output must below 4000 characters."}]
        messlist.extend(data)
        headers = headers_real.copy()
        while True:
            try:
                async with aiohttp.ClientSession(headers=headers) as s:
                    async with s.post("https://us-central1-chat-for-chatgpt.cloudfunctions.net/plusUserRequestChatGPT",
                                    timeout=None,
                                    ssl=self.SSL_Mode,
                                    raise_for_status=True,
                                    json={"data" : {
                                            "messages": messlist
                                            }}
                                    ) as r:
                        return (await r.json())["result"]["choices"][0]["message"]["content"].strip()
            except ClientResponseError as e:
                if e.status != 429:
                    raise e

