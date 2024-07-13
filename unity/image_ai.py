import asyncio
import io
import hashlib
import os
import random
import uuid
import demjson3
import time
import aiohttp
import re
import socket

defult_header = {
    'User-Agent': 'Mozilla/5.0 (compatible; FantasyBot/0.1; +https://fantasybot.xyz/support)',
    'Referer': 'https://onlyfakes.app/app',
    'Origin': 'https://onlyfakes.app'
}

class AI_NSFW:
    def __init__(self, is_proxy=True):
        self.cache = {}
        self.proxy = "http://localhost:9001" if is_proxy else None
        self.max_seed = 4294967295
        pass

    async def get_styles_engines(self):
        if int(time.time()) - self.cache.get('styles_last_update', 0) < 3600:
            return self.cache['styles'], self.cache['engine']
        conn = aiohttp.TCPConnector(family=socket.AF_INET)
        async with aiohttp.ClientSession(base_url='https://onlyfakes.app', connector=conn) as session:
            async with session.get('/app') as resp:
                script_url = re.search(r"src=\"(/static/js/main\..*\.js)\"></script>", await resp.text()).group(1)
            async with session.get(script_url) as resp:
                body = await resp.text()
                rtype_raw = re.search(r",a=(\w+)\(\"babes_v2\"\);return(\[.*?])", body)
                rtypes = rtype_raw.group(2).replace("void 0", "null")
                rmodels = re.search(r",_r=(\[.*?])", body).group(1).replace("!0", "true")
                var_mode = re.findall(fr"([a-z]+)={rtype_raw.group(1)}\(\"(.*?)\"\)", body)
                mode_engine = {i[0]: i[1] for i in var_mode}
                jmodels = demjson3.decode(rmodels)
                engine_id_list = {i['modelId']: i for i in jmodels}
                engine_list = {i['name']: i for i in jmodels}
                def engine_re(x: re.Match):
                    engine_name = mode_engine.get(x.group(1))
                    return f",engine:{engine_id_list.get(engine_name, 'null')},"
                rtypes = re.sub(",engine:([a-z]+),", engine_re, rtypes)
                jtypes = demjson3.decode(rtypes)
                jtypes = {i['name']: i for i in jtypes}
                self.cache['styles'] = jtypes
                self.cache['engine'] = engine_list
                self.cache['styles_last_update'] = int(time.time())
                return jtypes, engine_list

    async def get_styles(self):
        data = await self.get_styles_engines()
        return data[0]

    async def get_engines(self):
        data = await self.get_styles_engines()
        return data[1]

    async def get_styles_list(self):
        data = await self.get_styles_engines()
        return list(data[0].keys())

    async def get_engines_list(self):
        data = await self.get_styles_engines()
        return list(data[1].keys())

    def validate_seed(self, seed=None):
        if 0 < seed < self.max_seed:
            return seed
        return int(random.random() * self.max_seed) # nosec

    async def generate_image(self, *, prompt, negative_prompt="", seed=0, style_name="No style", engine_name=None, width=512, height=640, denoisingStrength=0.4, cfg=7.5):
        tracking_id = uuid.uuid4().__str__()
        style = (await self.get_styles())[style_name]
        if engine_name is not None:
            engine = (await self.get_engines())[engine_name]
        elif style['engine'] is None:
            engine = list((await self.get_engines()).values())[0]
            del style['engine']
        else:
            engine = style['engine']
        async with aiohttp.ClientSession(base_url='https://onlyfakes.app', headers=defult_header) as session:
            while True:
                jbody = {"fingerprint": hashlib.md5(os.urandom(16), usedforsecurity=False).hexdigest()}
                async with session.post('/.netlify/functions/checkFingerPrintForFirstTimeUser', json=jbody, proxy=self.proxy) as resp:
                    data = await resp.json(content_type="text/plain")
                    if data['isFirstTimeUser']:
                        ftoken = data['token']
                        break
            seed = self.validate_seed(seed)
            jbody = {
                "generateImageObject": {
                    "fullPrompt": prompt,
                    "negativePrompt": negative_prompt,
                    "seed": seed,
                    "size": {
                        "width": str(width),
                        "height": str(height)
                    },
                    "engine": engine,
                    "cfg": cfg,
                    "trackId": tracking_id,
                    "amountToGenerate": 1,
                    "speedMode": "turbo",
                    "uploadedImageUrl": "",
                    "denoisingStrength": denoisingStrength,
                    "style": style,
                    "selectedTags": [],
                    "firstTimeUserToken": ftoken
                }
            }
            while True:
                async with session.post('/.netlify/functions/generateImageAJ', json=jbody, proxy=self.proxy) as resp:
                    data = await resp.json(content_type="text/plain")
                    if (data.get("queue") is not None) and (jbody["generateImageObject"]["speedMode"] != "normal"):
                        print("speed mode change")
                        jbody["generateImageObject"]["speedMode"] = "normal"
                        del jbody["generateImageObject"]["firstTimeUserToken"]
                        continue
                    fetchToken = data['fetchToken']
                    break
            await asyncio.sleep(16 if jbody["generateImageObject"]["speedMode"] == "turbo" else 240)
            firstcheck = int(time.time())
            while True:
                async with session.post('/.netlify/functions/getImageData', json={"trackId": tracking_id}, cookies={"fetchToken": fetchToken}, proxy=self.proxy) as resp:
                    data = await resp.json(content_type="text/plain")
                    if data['imageUrl'] != "generating":
                        break
                    elif int(time.time()) - firstcheck > 120:
                        raise TimeoutError()
                    await asyncio.sleep(5)
        async with aiohttp.ClientSession() as session:
            async with session.get(data['imageUrl']) as resp:
                return io.BytesIO(await resp.read()), seed

