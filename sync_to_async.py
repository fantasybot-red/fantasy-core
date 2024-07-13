import typing
import asyncio 
import functools
import concurrent.futures

pool = concurrent.futures.ThreadPoolExecutor()

def run(func: typing.Callable) -> typing.Coroutine:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(pool, func, *args, **kwargs)
        return result
    return wrapper


async def run_blocking(func: typing.Callable, *args, **kwargs) -> typing.Any:
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(pool, func, *args, **kwargs)
    return result