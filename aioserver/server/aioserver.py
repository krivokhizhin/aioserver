import asyncio
import sys

from asyncio import StreamReader, StreamWriter


class AsyncStreamServer:

    def __init__(self, server_address, AsyncRequestHandlerClass) -> None:
        self.server_address = server_address
        self.AsyncRequestHandlerClass = AsyncRequestHandlerClass

    async def serve_forever(self):
        """Start accepting connections."""
        server = await asyncio.start_server(self._handle_stream, *self.server_address)

        async with server:
            await server.serve_forever()

    async def _handle_stream(self, reader: StreamReader, writer: StreamWriter):
        """Handle new client stream."""
        if await self.verify_stream(reader, writer):
            try:
                await self.process_stream(reader, writer)
            except Exception:
                await self.handle_error(writer)
                await self.shutdown_stream(reader, writer)
            except:
                await self.shutdown_stream(reader, writer)
                raise
        else:
            await self.shutdown_stream(reader, writer)

    async def verify_stream(self, reader: StreamReader, writer: StreamWriter) -> bool:
        """Verify the stream.  May be overridden.

        Return True if we should proceed with this stream.
        """
        return True
    
    async def process_stream(self, reader: StreamReader, writer: StreamWriter):
        """Call finish_stream.  May be overridden."""
        await self.finish_stream(reader, writer)
        await self.shutdown_stream(reader, writer)
    
    async def finish_stream(self, reader: StreamReader, writer: StreamWriter):
        """Finish one stream by instantiating AsyncRequestHandlerClass."""
        await self.AsyncRequestHandlerClass(reader, writer, self)
    
    async def handle_error(self, writer: StreamWriter):
        """Handle an error gracefully.  May be overridden.

        The default is to print a traceback and continue.
        """
        print('-'*40, file=sys.stderr)
        print('Exception occurred during processing of stream from',
            writer.get_extra_info('sockname'), file=sys.stderr)
        import traceback
        traceback.print_exc()
        print('-'*40, file=sys.stderr)
    
    async def shutdown_stream(self, reader: StreamReader, writer: StreamWriter):
        """Called to shutdown and close an individual stream."""
        await self.close_stream(writer)
    
    async def close_stream(self, writer: StreamWriter):
        """Called to clean up an individual stream."""
        writer.close()
        await writer.wait_closed()

class AsyncStreamRequestHandler:

    async def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        await instance.__init__(*args, **kwargs)
        return instance

    async def __init__(self, reader: StreamReader, writer: StreamWriter, server):
        self.reader = reader
        self.writer = writer
        self.client_address = writer.get_extra_info('sockname')
        self.server = server

        await self.setup()
        try:
            await self.async_handle()
        finally:
            await self.async_finish()

    async def setup(self):
        self.rfile = self.reader
        self.wfile = self.writer

    async def async_handle(self):
        pass

    async def async_finish(self):
        if not self.wfile.is_closing():
            await self.wfile.drain()

