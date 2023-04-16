# Asynchronous XML-RPC in Python

---

The key features are:

* Asynchronous XML-RPC server based on xmlrpc.server module;
* Only standard libraries are used;
* Server with process pool for CPU-bound operations.

---

## Requirements
Python 3.7+

Only standard Python libraries

## Installation
<div class="termy">

```console
$ git clone https://github.com/krivokhizhin/aioserver.git

---> 100%
```

</div>

## Usage
- simple async XML-RPC server:

```python
# save this as server.py
import asyncio

from aioserver.xmlrpc.server import AsyncXMLRPCServer
from load import aload  # some async function

async def main():
    server = AsyncXMLRPCServer(('localhost', 6677))
    server.register_introspection_functions()
    server.register_function(aload)

asyncio.run(main())
```

```shell
$ python -m server
```
- async XML-RPC server with process pool:

```python
# save this as pool_server.py
import asyncio

from aioserver.xmlrpc.pool_server import AsyncPoolXMLRPCServer
from load import load  # some sync function

async def main():
    server = AsyncPoolXMLRPCServer(('localhost', 6677), 6)
    server.register_introspection_functions()
    server.register_function(load)

asyncio.run(main())
```

```shell
$ python -m pool_server
```