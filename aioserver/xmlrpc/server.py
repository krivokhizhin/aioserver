import inspect
import traceback

from xmlrpc.client import Fault, dumps, loads, gzip_encode
from xmlrpc.server import SimpleXMLRPCDispatcher, SimpleXMLRPCRequestHandler, resolve_dotted_attribute

from ..streamserver import AsyncStreamServer
from ..http.server import AsyncBaseHTTPRequestHandler


class AsyncXMLRPCDispatcher(SimpleXMLRPCDispatcher):
    
    async def _async_marshaled_dispatch(self, data, dispatch_method = None, path = None):
        """Dispatches an XML-RPC method from marshalled (XML) data."""
        try:
            params, method = loads(data, use_builtin_types=self.use_builtin_types)

            # generate response
            if dispatch_method is not None:
                response = await dispatch_method(method, params)
            else:
                response = await self._async_dispatch(method, params)
            # wrap response in a singleton tuple
            response = (response,)
            response = dumps(response, methodresponse=1,
                             allow_none=self.allow_none, encoding=self.encoding)
        except Fault as fault:
            response = dumps(fault, allow_none=self.allow_none,
                             encoding=self.encoding)
        except BaseException as exc:
            response = dumps(
                Fault(1, "%s:%s" % (type(exc), exc)),
                encoding=self.encoding, allow_none=self.allow_none,
                )

        return response.encode(self.encoding, 'xmlcharrefreplace')

    async def _async_dispatch(self, method, params):
        """Dispatches the XML-RPC method."""
        try:
            # call the matching registered function
            func = self.funcs[method]
        except KeyError:
            pass
        else:
            if func is not None:
                return await self.call_func(func, *params)
            raise Exception('method "%s" is not supported' % method)

        if self.instance is not None:
            if hasattr(self.instance, '_async_dispatch'):
                # call the `_async_dispatch` method on the instance
                return await self.instance._async_dispatch(method, params)

            # call the instance's method directly
            try:
                func = resolve_dotted_attribute(
                    self.instance,
                    method,
                    self.allow_dotted_names
                )
            except AttributeError:
                pass
            else:
                if func is not None:
                    return await self.call_func(func, *params)

        raise Exception('method "%s" is not supported' % method)

    def has_not_async_function(self) -> bool:
        return not all(map(inspect.iscoroutinefunction, self.funcs))


class AsyncXMLRPCRequestHandler(AsyncBaseHTTPRequestHandler, SimpleXMLRPCRequestHandler):

    async def async_do_POST(self):
        """Handles the HTTP POST request."""
        # Check that the path is legal
        if not self.is_rpc_path_valid():
            self.report_404()
            return

        try:
            # Get arguments by reading body of request.
            # We read this in chunks to avoid straining
            # socket.read(); around the 10 or 15Mb mark, some platforms
            # begin to have problems (bug #792570).
            max_chunk_size = 10*1024*1024
            size_remaining = int(self.headers["content-length"])
            L = []
            while size_remaining:
                chunk_size = min(size_remaining, max_chunk_size)
                chunk = await self.rfile.read(chunk_size)
                if not chunk:
                    break
                L.append(chunk)
                size_remaining -= len(L[-1])
            data = b''.join(L)

            data = self.decode_request_content(data)
            if data is None:
                return #response has been sent

            # In previous versions of SimpleXMLRPCServer, _dispatch
            # could be overridden in this class, instead of in
            # SimpleXMLRPCDispatcher. To maintain backwards compatibility,
            # check to see if a subclass implements _dispatch and dispatch
            # using that method if present.
            response = await self.server._async_marshaled_dispatch(
                    data, getattr(self, '_async_dispatch', None), self.path
                )
        except Exception as e: # This should only happen if the module is buggy
            # internal error, report as HTTP server error
            self.send_response(500)

            # Send information about the exception if requested
            if hasattr(self.server, '_send_traceback_header') and \
                    self.server._send_traceback_header:
                self.send_header("X-exception", str(e))
                trace = traceback.format_exc()
                trace = str(trace.encode('ASCII', 'backslashreplace'), 'ASCII')
                self.send_header("X-traceback", trace)

            self.send_header("Content-length", "0")
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/xml")
            if self.encode_threshold is not None:
                if len(response) > self.encode_threshold:
                    q = self.accept_encodings().get("gzip", 0)
                    if q:
                        try:
                            response = gzip_encode(response)
                            self.send_header("Content-Encoding", "gzip")
                        except NotImplementedError:
                            pass
            self.send_header("Content-length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)


class AsyncXMLRPCServer(AsyncXMLRPCDispatcher, AsyncStreamServer):

    def __init__(self, addr, asyncRequestHandlerClass=AsyncXMLRPCRequestHandler,
                 logRequests=True, allow_none=False, encoding=None,
                 use_builtin_types=False):
        AsyncStreamServer.__init__(self, addr, asyncRequestHandlerClass)
        self.logRequests = logRequests
        AsyncXMLRPCDispatcher.__init__(self, allow_none, encoding, use_builtin_types)

    async def call_func(self, method, *args, **kwargs):
        if inspect.iscoroutinefunction(method):
            return await method(*args, **kwargs)
        elif not hasattr(self, 'loop'):
            return method(*args, **kwargs)
        