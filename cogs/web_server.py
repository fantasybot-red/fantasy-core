import os
import jwt
import time
import json
import discord
import aiohttp
import asyncio
import traceback
import async_timeout
from aiohttp import web
from urllib.parse import urljoin
from nacl.signing import VerifyKey
from cryptography.fernet import Fernet
from discord.ext import commands, tasks
from nacl.exceptions import BadSignatureError
from unity.music_client_obj import Voice_Client_Music
from unity.web_obj import CustomRouteTable, RateLimit, UnAuth

Authorization_KEY = "JWT_KEY"
Cache_KEY = "CC_KEY"

API_ENDPOINT = 'https://discord.com/api/v10'

class server(commands.Cog):
    
    routes = CustomRouteTable()
    
    def __init__(self, bot: discord.AutoShardedClient):
        self.bot = bot
        self.app = web.Application(debug=True)
        self.routes.setup(self.app, self)
        self.app.middlewares.append(self.cors_middleware)
        self.app.middlewares.append(self.jwt_middleware)
        self.app.middlewares.append(self.errtb)
        self.web_server.start()
        
    @routes.post('/dep')
    async def dep(self, request: web.BaseRequest):
        PUBLIC_KEY = os.getenv("TOKEN_PL")
        verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))
        signature = request.headers.get("X-Signature-Ed25519")
        timestamp = request.headers.get("X-Signature-Timestamp")
        if not (signature and timestamp):
            raise web.HTTPUnauthorized()
        body = (await request.read()).decode("utf-8")
        try:
            verify_key.verify(f'{timestamp}{body}'.encode(), bytes.fromhex(signature))
        except BadSignatureError:
            raise web.HTTPUnauthorized()
        data = await request.json()
        if data.get("type") == 1:
            return web.json_response({"type": 1})
        else:
            datas = {'t': 'INTERACTION_CREATE', 'op': 0, 'd': data}
            if data.get("guild_id") is not None:
                sid = int(data.get("guild_id"))
            else:
                sid = 0
            try:
                asyncio.create_task(self.bot._get_websocket(sid).received_message(json.dumps(datas)))
                await asyncio.sleep(120)
            except BaseException:
                pass
            raise web.HTTPOk()
    
    @routes.view("/robots.txt")
    async def robots_txt(self, request: aiohttp.web.Request):
        return web.Response(body="User-agent: *\nDisallow: /", content_type="text/plain")
    
    @routes.get('/')
    async def index(self, request: web.BaseRequest):
        raise web.HTTPOk()
    
    @routes.get('/info')
    async def supporturl(self, request: web.BaseRequest):
        inv_url = discord.utils.oauth_url(931353470353674291, permissions=discord.Permissions.all())
        return web.json_response({"url": "https://discord.gg/tJSDj6bc3s", "invite": inv_url})
    
    # dash
        
    @routes.view("/login")
    async def login(self, request: aiohttp.web.Request):
        code = await request.json()
        data = await self.exchange_code(code["code"], code["redirect_uri"])
        session = request[Authorization_KEY]
        if data:
            session["access_token"] = data["access_token"]
            session["refresh_token"] = data["refresh_token"]
            session["token_type"] = data["token_type"]
            session["expires_in"] = int(time.time()) + data["expires_in"]
            return web.json_response({"login": True})
        return web.json_response({"login": False}, status=401)
    
    @routes.view("/logout")
    async def logout(self, request: aiohttp.web.Request):
        session = request[Authorization_KEY]
        if len(session) != 0:
            await self.revoke_token(session["refresh_token"])
            request[Cache_KEY].clear()
            return web.json_response({"ok": True})
        return web.json_response({"ok": False}, status=401) 

    @routes.view("/guild/{guild_id:\d+}/music_events")
    async def guilds_music_event(self, request: aiohttp.web.Request):
        guild_id = request.match_info['guild_id']
        guild = (await self.getguilds(request))["guilds"].get(guild_id)
        if guild is None:
            return web.json_response({"status": False}, status=403)
        vc = self.bot.get_guild(int(guild_id))
        if vc is None:
            return web.json_response({"status": False}, status=403)
        proko = ()
        auth_ws_header = request.headers.get("Sec-Websocket-Protocol")
        if auth_ws_header:
            try:
                proko = auth_ws_header.split(",")
            except ValueError:
                pass
        ws = web.WebSocketResponse(protocols=proko)
        await ws.prepare(request)
        pubsub = self.bot.db.pubsub()
        await pubsub.subscribe(f'music_client_event:{guild_id}', f'music_queue_event:{guild_id}')
        async def ping():
            while not ws.closed:
                await ws.send_json({"event": "ping"})
                await asyncio.sleep(30)
        tk = asyncio.create_task(ping())
        while not ws.closed:
            try:
                async with async_timeout.timeout(1):
                    message = await pubsub.get_message()
                    if message and message["type"] == "message":
                        event = "player" if message["channel"].decode().startswith("music_client_event") else "queue"
                        await ws.send_json({"event": event, "data": message["data"].decode()})
            except (asyncio.TimeoutError):
                pass
        tk.cancel()
        await tk
        return ws
        
    
    @routes.view("/guild/{guild_id:\d+}/music_queue")
    async def guilds_music(self, request: aiohttp.web.Request):
        guild_id = request.match_info['guild_id']
        guild = (await self.getguilds(request))["guilds"].get(guild_id)
        if guild is None:
            return web.json_response({"status": False}, status=403)
        rdict = {}
        guild_id = request.match_info['guild_id']
        vc = self.bot.get_guild(int(guild_id))
        if vc is None:
            rdict["status"] = False
            return web.json_response(rdict, status=403)
        rdict["is_music_voice"] = type(vc.voice_client) is Voice_Client_Music
        rdict["status"] = True
        if not rdict["is_music_voice"]:
            return web.json_response(rdict)
        vc: Voice_Client_Music = vc.voice_client
        rdict["queue"] = [i.to_dict() for i in vc.queue]
        rdict["loop"] = vc.queue.loop
        rdict["is_playing"] = not vc.is_paused()
        rdict["volume"] = vc.volume
        rdict["now_playing"] = vc.queue.nowplaying
        return web.json_response(rdict)

    @routes.view("/guild/{guild_id:\d+}/music_control")
    async def guilds_music_control(self, request: aiohttp.web.Request):
        guild_id = request.match_info['guild_id']
        control = (await request.json()).get("event")
        guild = (await self.getguilds(request))["guilds"].get(guild_id)
        user_id = (await self.getuser(request))["id"]
        if guild is None:
            return web.json_response({"status": False}, status=403)
        rdict = {}
        guild_id = request.match_info['guild_id']
        vc = self.bot.get_guild(int(guild_id))
        if vc is None:
            rdict["status"] = False
            return web.json_response(rdict, status=403)
        is_music_voice = type(vc.voice_client) is Voice_Client_Music
        if not is_music_voice:
            return web.HTTPBadRequest(text="Not a music voice channel")
        elif not [i for i in vc.voice_client.channel.members if i.id == int(user_id)]:
            return web.HTTPBadRequest(text="You are not in that channel")
        vc: Voice_Client_Music = vc.voice_client
        if control is None:
            return web.HTTPBadRequest(text="Not a music voice channel")
        elif control == "play":
            await vc.resume()
        elif control == "pause":
            await vc.pause()
        elif control == "skip":
            await vc.stop()
        elif control == "previous":
            pre = vc.queue.previous()
            if pre is not None:
                await vc.stop()
            else:
                return web.HTTPGone(text="No previous track")
        return web.HTTPNoContent()
    
    @routes.view("/guild/{guild_id:\d+}")
    async def guild(self, request: aiohttp.web.Request):
        guild_id = request.match_info['guild_id']
        guild = (await self.getguilds(request))["guilds"].get(guild_id)
        if guild is None:
            return web.json_response({"status": False}, status=403)
        return web.json_response({"status": True, "data": guild})
    
    @routes.view("/@me")
    async def api_me(self, request: aiohttp.web.Request):
        data = await self.getuser(request)
        data["status"] = True
        return web.json_response(data)
    
    @routes.view("/@me/guilds")
    async def api_me_guilds(self, request: aiohttp.web.Request):
        guild = await self.getguilds(request)
        guild["status"] = True
        return web.json_response(guild)
        
    async def exchange_code(self, code, redirect_uri):
            data = {
                'client_id': str(self.bot.user.id),
                'client_secret': os.getenv("TOKEN_CS"),
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirect_uri
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(f'{API_ENDPOINT}/oauth2/token', data=data) as r:
                    if r.status == 200:
                        return await r.json()
                    elif r.status == 429:
                        raise RateLimit()
                    else:
                        return None
        
    async def refresh_token(self, refresh_token):
        data = {
            'client_id': str(self.bot.user.id),
            'client_secret': os.getenv("TOKEN_CS"),
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{API_ENDPOINT}/oauth2/token', data=data) as r:
                if r.status == 200:
                    return await r.json()
                elif r.status == 429:
                    raise RateLimit()
                else:
                    return None
    
    async def revoke_token(self, token):
        data = {
            'client_id': str(self.bot.user.id),
            'client_secret': os.getenv("TOKEN_CS"),
            'token': token
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{API_ENDPOINT}/oauth2/token/revoke', data=data) as r:
                if r.status == 200:
                    return await r.json()
                elif r.status == 429:
                    raise RateLimit()
                else:
                    return None
    
    async def getdatadiscord(self, method: str, endpot: str, session: dict, *, json=None, data=None):
            refresh = False
            while True:
                if len(session.keys()) != 0 and not refresh and (session.get('token_type') is not None) and (session.get('access_token') is not None):
                    headers = {
                        "Authorization": f"{session['token_type']} {session['access_token']}"
                    }
                    async with aiohttp.ClientSession() as sr:
                        async with sr.request(method, urljoin(API_ENDPOINT, endpot), data=data, json=json, headers=headers) as r:
                            if r.status == 200:
                                return await r.json()
                            elif r.status == 429:
                                raise RateLimit()
                            else:
                                refresh = True
                else:
                    if session.get("refresh_token") != None:
                        data = await self.refresh_token(session["refresh_token"])
                        if data != None:
                            session["access_token"] = data["access_token"]
                            session["refresh_token"] = data["refresh_token"]
                            session["login"] = True
                        else:
                            raise UnAuth()
                    else:
                        raise UnAuth()
    
    def save_cache(self, request, key, data):
        request[Cache_KEY][key] = {"data": data, "last_update": int(time.time())}
        
    def get_cache(self, request, key):
        if request.query.get("cache") == "false":
            return None
        if request[Cache_KEY].get(key) is not None:
            if int(time.time()) - request[Cache_KEY][key]["last_update"] < 300:
                return request[Cache_KEY][key]["data"]
        return None
        
    async def getuser(self, request: aiohttp.web.Request):
        session = request[Authorization_KEY]
        cache_db = self.get_cache(request, "user")
        if cache_db is not None:
            return cache_db
        rdata = {}
        data = await self.getdatadiscord("GET", "users/@me", session)
        avatar_index = int(data['discriminator']) % 5 if int(data['discriminator']) != 0 else (int(data["id"]) >> 22) % 6
        avt = f"https://cdn.discordapp.com/avatars/{data['id']}/{data['avatar']}" if data['avatar'] else f"https://cdn.discordapp.com/embed/avatars/{avatar_index}.png"
        data["avatar"] = avt
        rdata["user"] = data
        self.save_cache(request, "user", rdata)
        return rdata
    
    async def getguilds(self, request: aiohttp.web.Request):
        session = request[Authorization_KEY]
        cache_db = self.get_cache(request, "guilds")
        if cache_db is not None:
            return cache_db
        rdata = {}
        data = await self.getdatadiscord("GET", "users/@me/guilds", session)
        guilds_list = {}
        for i in data:
            del i["features"]
            del i["permissions_new"]
            i["permissions"] = discord.Permissions(int(i['permissions'])).manage_guild
            i["bot_joined"] = self.bot.get_guild(int(i['id'])) is not None
            if (not i["bot_joined"]) and (not i["permissions"]):
                continue
            guilds_list[i["id"]] = i
        rdata["guilds"] = guilds_list
        self.save_cache(request, "guilds", rdata)
        return rdata  

    @web.middleware
    async def errtb(self, request: web.BaseRequest, handler):
        try:
            resp = await handler(request)
            if resp is None:
                resp = web.HTTPNoContent()
        except (web.HTTPSuccessful, web.HTTPRedirection) as e:
            e.body = None
            resp = e
        except RateLimit:
            resp = web.json_response({"status": None}, status=429)
        except UnAuth:
            request[Authorization_KEY].clear()
            if request[Authorization_KEY].get("refresh_token") is not None:
                await self.revoke_token(request[Authorization_KEY]["refresh_token"])
            resp = web.json_response({"status": False}, status=401)
        except BaseException as e:
            if isinstance(e, web.HTTPError):
                e.text = json.dumps({"status": False})
                e.content_type = "application/json"
                resp = e
            else:
                traceback.print_exc()
                resp = web.HTTPGatewayTimeout()
        resp.headers["X-Powered-By"] = "Your Mama"
        return resp
    
    @web.middleware
    async def jwt_middleware(self, request: web.BaseRequest, handler):
        fn = Fernet(os.getenv("WEB_TOKEN_ENCRYPTION").encode())
        auth_header = request.headers.get("Authorization")
        auth_ws_header = request.headers.get("Sec-Websocket-Protocol")
        session_cache = {}
        session_token = {}
        token = None
        if auth_ws_header:
            try:
                token = auth_ws_header.split(",")[0]
            except ValueError:
                pass
        if auth_header:
            try:
                type_token, token = auth_header.split(" ")
            except ValueError:
                pass
            
        if token is not None:
            try:
                raw_token = jwt.decode(token, os.getenv("JWT_TOKEN"), algorithms=["HS256"])
            except jwt.InvalidTokenError:
                return web.json_response({"status": False}, status=401)
            try:
                raw_data = raw_token["d"]
                decript_token = fn.decrypt(raw_data)
                session_token = json.loads(decript_token)
            except BaseException:
                return web.json_response({"status": False}, status=401)
            
        if "c_id" in session_token.keys():
            raw_data = await self.bot.db.get(f"s_cache:{session_token['c_id']}")
            if raw_data is not None:
                session_cache = json.loads(raw_data)
            
        request[Authorization_KEY] = session_token.copy()
        request[Cache_KEY] = session_cache.copy()
        request[Authorization_KEY].pop("c_id", None)

        try:
            resp = await handler(request)
        except web.HTTPException as e:
            resp = e
            
        old_cache = session_token.pop("c_id", None)
        cache_id = old_cache or os.urandom(16).hex()
        if (request[Authorization_KEY] != session_token and request[Authorization_KEY]):
            request[Authorization_KEY]["c_id"] = cache_id
            edata = fn.encrypt(json.dumps(request[Authorization_KEY]).encode()).decode()
            new_token = jwt.encode({"d": edata}, os.getenv("JWT_TOKEN"), algorithm="HS256")
            resp.headers["Authorization-Update"] = new_token
        
        if request[Cache_KEY] != session_cache and request[Cache_KEY]:
            edata = json.dumps(request[Cache_KEY]).encode()
            await self.bot.db.set(f"s_cache:{cache_id}", edata, ex=300)
        elif request[Cache_KEY] == session_cache and request[Cache_KEY]:
            await self.bot.db.expire(f"s_cache:{cache_id}", 300, xx=True)
        elif request[Cache_KEY] != session_cache and (not request[Cache_KEY]):
            await self.bot.db.delete(f"s_cache:{cache_id}")
        
        return resp
    
    @web.middleware
    async def cors_middleware(self, request: web.BaseRequest, handler):
        resp = web.HTTPOk()
        resp.body = None
        if request.method != "OPTIONS":
            resp = await handler(request)
        rf = request.headers.get("Origin")  
        resp.headers["Access-Control-Allow-Origin"] = "https://fantasybot.xyz"
        if rf == "https://test.fantasybot.xyz":
            resp.headers["Access-Control-Allow-Origin"] = "https://test.fantasybot.xyz"
        resp.headers["Access-Control-Allow-Credentials"] = "true"
        resp.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        resp.headers["Access-Control-Expose-Headers"] = "Content-Type, Authorization-Update"
        return resp
        
        
    async def cog_unload(self):
        print("Web Server Unload")
        await self.webapp.stop()
        await self.runner.shutdown()
        await self.runner.cleanup()
    
    @tasks.loop()
    async def web_server(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.webapp = web.TCPSite(runner=self.runner, port=3333, shutdown_timeout=0)
        await self.webapp.start()
        

async def setup(bot):
    await bot.add_cog(server(bot))
