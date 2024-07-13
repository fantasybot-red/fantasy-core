from aiohttp import web
from dataclasses import dataclass

class RateLimit(Exception):
    pass

class UnAuth(Exception):
    pass

@dataclass
class RouteData:
    method: str
    path: str
    kwargs: dict

class CustomRouteTable(web.RouteTableDef):
    def route(self, method: str, path: str, **kwargs: dict):
        def inner(handler):
            handler.__route_data__ = RouteData(method, path, kwargs)
            return handler
        return inner
    
    def setup(self, app: web.Application, class_obj):
        for k in dir(class_obj):
            var = getattr(class_obj, k)
            rdt = getattr(var, "__route_data__", None)
            if rdt is not None:
                app.router.add_route(rdt.method, rdt.path, var, **rdt.kwargs)