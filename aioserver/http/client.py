import email.parser

from asyncio import StreamReader
from http.client import LineTooLong, HTTPException, HTTPMessage

_MAXLINE = 65536
_MAXHEADERS = 100
    
async def async_http_parse_headers(reader: StreamReader, _class=HTTPMessage):
    headers = []
    while True:
        line = await reader.readline()
        if len(line) > _MAXLINE:
            raise LineTooLong("header line")
        headers.append(line)
        if len(headers) > _MAXHEADERS:
            raise HTTPException("got more than %d headers" % _MAXHEADERS)
        if line in (b'\r\n', b'\n', b''):
            break
    hstring = b''.join(headers).decode('iso-8859-1')
    return email.parser.Parser(_class=_class).parsestr(hstring)
