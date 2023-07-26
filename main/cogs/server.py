import aiohttp
import os
import discord
import traceback
import aiohttp_session
import base64
import json
import asyncio
import mimetypes
from aiohttp import web
from unity.jsosb import Js
from urllib.parse import urljoin, quote_plus, urlparse
from discord.ext import commands, tasks
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup
from cryptography import fernet
from aiohttp_session import get_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage

jinja2page = Environment(loader=FileSystemLoader(["./website/page/"]), autoescape=True)
jinja2root = Environment(loader=FileSystemLoader(["./website/"]), autoescape=True)

def html_send(file, req:web.BaseRequest, *args, **kwargs):
    
    template = jinja2page.get_template(file)
    data = template.render(*args, **kwargs)
    
    htmlpr = BeautifulSoup(data, features="lxml")
    htmlpr.body.hidden = True
    
    bodyattrs = " ".join([f"{i[0]}=\"{i[1]}\"" for i in htmlpr.body.attrs.items()])
    outbody = str(htmlpr.body)
    htmlpr.head.hidden = True
    headattrs = " ".join([f"{i[0]}=\"{i[1]}\"" for i in htmlpr.head.attrs.items()])
    outhead = str(htmlpr.head)
    
    botdata = jinja2root.get_template("bot.html").render(url=str(req.url))
    botheadpr = BeautifulSoup(botdata, features="html.parser")
    botheadpr.head.hidden = True
    botheadout = str(botheadpr.head)
    
    template = jinja2page.get_template(os.path.join(os.path.dirname(file), "__main__.html"))
    data = template.render(headattrs=headattrs, bodyattrs=bodyattrs, body=outbody, head=outhead, bothead=botheadout)
    return web.Response(body=data, content_type="text/html")

def html_send_root(file, *args, **kwargs):
    template = jinja2root.get_template(file)
    data = template.render(*args, **kwargs)
    return web.Response(body=data, content_type="text/html")

def html_send_err(statuscode=204, bugname="", url="/"):
    template = jinja2root.get_template("err.html")
    data = template.render(statuscode=statuscode, bugname=bugname, url=url)
    return web.Response(body=data, status=statuscode, content_type="text/html")

class RateLimit(BaseException):
    pass

class UnAuth(BaseException):
    pass

class server(commands.Cog):
    app = web.Application(debug=True)
    routes = web.RouteTableDef()
    
    def __init__(self, bot: discord.AutoShardedClient):
        self.bot = bot

        API_ENDPOINT = 'https://discord.com/api/v10'
        REDIRECT_URI = "https://fantasybot.tech/login"

        async def exchange_code(code):
            data = {
                'client_id': str(bot.user.id),
                'client_secret': os.getenv("TOKEN_CS"),
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': REDIRECT_URI
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(f'{API_ENDPOINT}/oauth2/token', data=data) as r:
                    if r.status == 200:
                        return await r.json()
                    elif r.status == 429:
                        raise RateLimit()
                    else:
                        return None

        async def refresh_token(refresh_token):
            data = {
                'client_id': str(bot.user.id),
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
        
        async def getdatadiscord(method: str, endpot: str, session: aiohttp_session.Session, *, json=None, data=None):
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
                            data = await refresh_token(session["refresh_token"])
                            if data != None:
                                session["access_token"] = data["access_token"]
                                session["refresh_token"] = data["refresh_token"]
                                session["login"] = True
                            else:
                                raise UnAuth()
                        else:
                            raise UnAuth()
            
        
        async def getuser(session, cache=True):
            if (session.get("user") is None) or (not cache):
                data = await getdatadiscord("GET", "users/@me", session)
                avt = f"https://cdn.discordapp.com/avatars/{data['id']}/{data['avatar']}" if data['avatar'] else f"https://cdn.discordapp.com/embed/avatars/{int(data['discriminator']) % 5}.png"
                data["avatar"] = avt
                session["user"] = data
            else:
                data = session["user"]
            return data
        
        # routes
        
        @self.routes.post('/api/dep')
        async def dep(request: web.BaseRequest):
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
        
        @self.routes.get('/')
        async def index(request: web.BaseRequest):
            return html_send("root-main/index.html", request)
                
        @self.routes.get('/tos')
        async def tos(request: web.BaseRequest):
            return html_send("root-main/tos.html", request)
            
        @self.routes.get('/pp')
        async def policy(request: web.BaseRequest):
            return html_send("dash-main/privacy-policy.html", request)
        
        @self.routes.get('/premium')
        async def premium(request: web.BaseRequest):
            return html_send("root-main/premium.html", request, temp="dash.html")
            
        @self.routes.get('/favicon.ico')
        async def favicon(request: web.BaseRequest):
            return web.FileResponse("./website/favicon.ico")

        @self.routes.get('/support')
        async def supporturl(request: web.BaseRequest):
            return web.HTTPFound('https://discord.gg/tJSDj6bc3s')
            
        @self.routes.get('/invite')
        async def invite(request: web.BaseRequest):
            return web.HTTPFound(discord.utils.oauth_url(931353470353674291, permissions=discord.Permissions.all()))
            
        @self.routes.get('/robots.txt')
        async def robots(request: web.BaseRequest):
            return web.FileResponse("./website/robots.txt")
        
        # dash
         
        @self.routes.view("/login")
        async def login(request: aiohttp.web.Request):
            session = await get_session(request)
            code = request.query.get("code")
            rurl = request.query.get("u")
            if rurl:
              try:
                    rurl = urlparse(rurl).path
              except BaseException:
                    rurl = None
            state = request.query.get("state")
            if state:
                try:
                    state = base64.urlsafe_b64decode(state.encode('ascii')).decode('ascii')
                    state = urlparse(state).path
                except BaseException:
                    state = None
            if not session.get("login"):
                if code != None:
                    data = await exchange_code(code)
                    if data:
                        session["access_token"] = data["access_token"]
                        session["refresh_token"] = data["refresh_token"]
                        session["token_type"] = data["token_type"]
                        session["login"] = True
                        return web.HTTPFound("/dash") if not state else web.HTTPFound(state)
                stateurl = ""
                if rurl:
                    bs64 = base64.urlsafe_b64encode(rurl.encode('ascii')).decode('ascii')
                    stateurl = f"&state={quote_plus(bs64)}"
                return web.HTTPFound(f"https://discord.com/oauth2/authorize?client_id=931353470353674291&redirect_uri=https://fantasybot.tech/login&response_type=code&scope=identify&prompt=none{stateurl}")
            return web.HTTPFound("/dash") if not rurl else web.HTTPFound(rurl)
        
        @self.routes.view("/api/login")
        async def api_login(request: aiohttp.web.Request):
            session = await get_session(request)
            if session.get("login"):
                if not request.cookies.get("sid"):
                    await getuser(session, False)
                return web.json_response({"status": True})
            return web.json_response({"status": False}, status=401)

        @self.routes.view("/api/@me")
        async def api_me(request: aiohttp.web.Request):
            session = await get_session(request)
            if session.get("login"):
                if not request.cookies.get("sid"):
                    data = await getuser(session, False)
                    return web.json_response(data)
                else:
                    data = await getuser(session)
                    return web.json_response(data)
            return web.json_response({"status": False}, status=401)
        
        @self.routes.view("/api/@me/guilds")
        async def api_me_guilds(request: aiohttp.web.Request):
            session = await get_session(request)
            if session.get("login"):
                user = await getuser(session)
                user = self.bot.get_user(int(user["id"]))
                data = []
                if user:
                    data = [{"id": i.id, "name": i.name, "icon": (i.icon.url if i.icon else None)} for i in user.mutual_guilds if i.get_member(user.id).guild_permissions.manage_guild]
                return web.json_response(data)
            return web.json_response({"status": False}, status=401)
        
        @self.routes.view("/dash")
        async def dash(request: aiohttp.web.Request):
            return html_send("dash-main/dash.html", request)
        
        @self.routes.view("/logout")
        async def logout(request: aiohttp.web.Request):
            session = await get_session(request)
            resp = web.HTTPFound("/")
            if session.get("login"):
                resp.del_cookie("Session_Token")
            return resp

        self.web_server.start()
    
    @web.middleware
    async def javascript_osb(self, request: web.BaseRequest, handler):
        resp = await handler(request)
        if type(resp) is web.FileResponse:
            ct, encoding = mimetypes.guess_type(str(resp._path))
            print(ct)
            with open(resp._path, "r") as f:
                jsencode = Js.obfuscate(f.read())
            resp = web.Response(body=jsencode, content_type=ct)
        return resp
    
    @web.middleware
    async def errtb(self, request: web.BaseRequest, handler):
        try:
            resp = await handler(request)
            if resp is None:
                resp = web.HTTPNoContent()
        except web.HTTPError as e:
            resp = html_send_err(statuscode=e.status_code, bugname=e.reason, url=str(request.url))
        except web.HTTPSuccessful as e:
            resp = e
        except web.HTTPRedirection as e:
            resp = e
        except RateLimit:
            resp = html_send_err(statuscode=429, bugname="You Got Rate Limit", url=str(request.url))
        except UnAuth:
            session = await get_session(request)
            session.clear()
            if request.path.startswith("/api/"):
                resp = web.json_response({"status": False}, status=401)
            else:
                resp = web.HTTPFound(location=f"/login?u={quote_plus(request.path_qs)}")
        except BaseException:
            traceback.print_exc()
            resp = html_send_err(statuscode=500, bugname="Internal Server Error", url=str(request.url))
        return resp
        
    async def cog_unload(self):
        await self.webapp.stop()
    
    @tasks.loop()
    async def web_server(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        self.webapp = web.TCPSite(runner=runner, port=3333)  #nosec
        await self.webapp.start()

    @web_server.before_loop
    async def web_server_before_loop(self):
        self.routes.static("/js/", "./website/jscdn")
        self.routes.static("/assets/", "./website/assets")
        self.app.add_routes(self.routes)
        key = os.getenv("WEB_KEY")
        f = fernet.Fernet(key.encode("utf8"))
        s = EncryptedCookieStorage(f, cookie_name="Session_Token", httponly=False, max_age=34560000)
        self.app.middlewares.append(aiohttp_session.session_middleware(s))
        self.app.middlewares.append(self.javascript_osb)
        self.app.middlewares.append(self.errtb)
        

async def setup(bot):
    await bot.add_cog(server(bot))
