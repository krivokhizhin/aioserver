# Asynchronous XML-RPC in Python

---

The key features are:

* Asynchronous XML-RPC server based on xmlrpc.server module;
* 

---

## Requirements
Python 3.7+

Only standard Python libraries

## Installation
<div class="termy">

```console
$ git clone https://github.com/krivokhizhin/asyncxmlrpc.git

---> 100%
```

</div>

cd

python3 sync_tools/serve_forever.py
python3 serve_forever.py

python3 sync_tools/client.py 250000
python3 -m timeit 'from sync_tools.client import RpcClient;  RpcClient.start_for_timeit(250000, "localhost", 8000, 60, 100, 20)'

ps f
