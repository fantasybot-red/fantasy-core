import uuid
import re
import aiohttp
import hashlib


default_headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'referer': 'https://www.google.com/',
    'user-agent': "Mozilla/5.0 (compatible; FantasyBot/0.1; +https://fantasybot.xyz/support)",
}


def digestMessage(r):
    e = r.encode()
    t = hashlib.sha256(e).digest()
    return ''.join(format(byte, '02x') for byte in t)


class ChatGPT:
    SSL_Mode = None
    System_Prompt = "AI has markdown support and your name is ChatGPT and made by OpenAI and AI output MUST below 4000 characters."
    
    def __init__(self):
        pass
    
    def make_message(self, role, content):
        mess = {"content": content, "id": uuid.uuid4().__str__()}
        if role == "user":
            mess["from"] = "you"
        elif role == "assistant":
            mess["from"] = "ChatGPT"
        return mess

    async def create_new_chat(self, data, system_prompt=System_Prompt):
        messages = []
        if type(data) is str:
            messages.append(self.make_message("user", data))
        else:
            for i in data:
                messages.append(self.make_message(i["role"], i["content"]))
        async with aiohttp.ClientSession(headers=default_headers, base_url="https://talkai.info", raise_for_status=True) as s:
            json_data = {
                'type': 'chat',
                'messagesHistory': messages,
                'settings': {
                    'model': 'gpt-3.5-turbo',
                },
            }
            async with s.post('/chat/send/', json=json_data) as r:
                data = await r.text()
                data = re.findall("\ndata: (.+?)\n", data)
                r_str = "".join(data[:-1]).replace("\\n", "\n").replace("\\t", "\t")
                return r_str
    
    async def create_new_image(self, data):
        async with aiohttp.ClientSession(headers=default_headers, base_url="https://talkai.info", raise_for_status=True) as s:
            json_data = {
                'type': 'image',
                'messagesHistory': [self.make_message("user", data)],
                'settings': {
                    'model': 'gpt-3.5-turbo',
                },
            }
            async with s.post('/chat/send/', json=json_data) as r:
                data = await r.json()
                return data["data"][0]["url"]
                
