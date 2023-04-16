import asyncio
import inspect

from asyncio.events import AbstractEventLoop
from concurrent.futures import ProcessPoolExecutor
from functools import partial

from .server import AsyncXMLRPCServer


class AsyncPoolXMLRPCServer(AsyncXMLRPCServer):

    def __init__(self, addr, max_workers: int, *args, **kwargs):
        super().__init__(addr, *args, **kwargs)

        self.max_workers = max_workers

    async def serve_forever(self):

        if self.max_workers > 0 and self.has_not_async_function():
            self.executor = ProcessPoolExecutor(self.max_workers)
            self.loop: AbstractEventLoop = asyncio.get_running_loop()

        await super().serve_forever()

        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False, cancel_futures=True)

    async def call_func(self, method, *args, **kwargs):
        if inspect.iscoroutinefunction(method):
            return await method(*args, **kwargs)
        elif not hasattr(self, 'loop'):
            return method(*args, **kwargs)
            
        call_method = partial(method, *args, **kwargs)
        return await self.loop.run_in_executor(self.executor, call_method)
