"""Colab 橋接：讓 Claude 不靠 Claude Code 的 MCP 工具清單刷新，也能操作瀏覽器裡的 Colab。

為什麼有這支（2026-10-10 家裡用筆電）：
colab-mcp 連上 Colab 網頁後會發「工具清單變了」通知，Claude Code 本該重新抓清單、拿到新增／執行儲存格的工具。
今天兩次連上都沒重抓（伺服器 log 有 connection open、之後沒有 ListToolsRequest），工具一直只有 1 個。
這支自己開一份 colab-mcp、自己 list_tools，再開本機 HTTP 讓 Claude 用指令呼叫，繞過那個刷新。

用法：
  # 1) 背景啟動（會自動開一個 Colab Scratchpad 分頁，請在那個分頁換 A100 並連線）
  uv run --with fastmcp==2.14.5 python scripts/colab_bridge.py serve
  # 2) 另一個命令列呼叫
  uv run --with fastmcp==2.14.5 python scripts/colab_bridge.py status
  uv run --with fastmcp==2.14.5 python scripts/colab_bridge.py tools
  uv run --with fastmcp==2.14.5 python scripts/colab_bridge.py call <工具名> '<JSON 參數>'
  uv run --with fastmcp==2.14.5 python scripts/colab_bridge.py call <工具名> @args.json   # 參數放檔案（中文、換行不用跳脫）

連線開在最後點過的 Chrome 視窗（sunnyboychu 那個才有 Pro／A100），見記憶 colab-mcp-account-and-tab。
"""
import asyncio
import json
import sys
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 8765
COLAB_MCP = ["uvx", "git+https://github.com/googlecolab/colab-mcp"]


def dump(x):
    if hasattr(x, "model_dump"):
        return x.model_dump(mode="json")
    if isinstance(x, (list, tuple)):
        return [dump(i) for i in x]
    return x


class Bridge:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.client = None
        self.connected = False

    async def start(self):
        from fastmcp import Client
        from fastmcp.client.transports import StdioTransport
        self.client = Client(StdioTransport(command=COLAB_MCP[0], args=COLAB_MCP[1:]), timeout=600)
        await self.client.__aenter__()
        await self.connect()

    async def connect(self):
        # 只叫一次：沒連上時每叫一次就多開一個分頁；要再試走 /reconnect（由人決定）
        r = await self.client.call_tool("open_colab_browser_connection", {}, raise_on_error=False)
        self.connected = bool(getattr(r, "data", None)) or "true" in json.dumps(dump(r.content))
        print(f"[bridge] 連線：{self.connected}", flush=True)
        names = [t.name for t in await self.client.list_tools()]
        print(f"[bridge] 工具 {len(names)} 個：{names}", flush=True)
        return names

    def run(self, coro, timeout=900):
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result(timeout)


B = Bridge()


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def reply(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        try:
            if self.path == "/status":
                return self.reply(200, {"connected": B.connected})
            if self.path == "/tools":
                ts = B.run(B.client.list_tools())
                return self.reply(200, [{"name": t.name, "description": t.description, "input": t.inputSchema} for t in ts])
            if self.path == "/reconnect":
                return self.reply(200, {"tools": B.run(B.connect())})
            self.reply(404, {"error": "unknown path"})
        except Exception as e:
            self.reply(500, {"error": repr(e)})

    def do_POST(self):
        try:
            req = json.loads(self.rfile.read(int(self.headers["Content-Length"])).decode("utf-8"))
            r = B.run(B.client.call_tool(req["name"], req.get("arguments", {}), raise_on_error=False))
            self.reply(200, {"is_error": getattr(r, "is_error", False), "content": dump(r.content),
                             "data": dump(getattr(r, "structured_content", None))})
        except Exception as e:
            self.reply(500, {"error": repr(e)})


def serve():
    threading.Thread(target=B.loop.run_forever, daemon=True).start()
    B.run(B.start(), timeout=300)
    print(f"[bridge] HTTP 127.0.0.1:{PORT} 就緒", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()


def http(path, data=None, timeout=900):
    r = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}",
                               data=json.dumps(data, ensure_ascii=False).encode("utf-8") if data is not None else None,
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=timeout) as f:
        return json.loads(f.read().decode("utf-8"))


def main():
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "serve":
        return serve()
    if cmd in ("status", "tools", "reconnect"):
        out = http("/" + cmd)
    elif cmd == "exec":  # 在筆記本最後加一格程式碼並執行，印出輸出：exec '<程式碼>' 或 exec @code.py
        arg = sys.argv[2]
        code = Path(arg[1:]).read_text(encoding="utf-8") if arg.startswith("@") else arg
        cells = http("/", {"name": "get_cells", "arguments": {}})
        n = len(json.loads(cells["content"][0]["text"]).get("cells", [])) if cells.get("content") else 0
        http("/", {"name": "add_code_cell", "arguments": {"cellIndex": n, "language": "python", "code": code}})
        # add_code_cell 回傳的 id 欄位名不固定，直接讀回第 n 格最可靠
        cid = json.loads(http("/", {"name": "get_cells", "arguments": {}})["content"][0]["text"])["cells"][n]["id"]
        out = http("/", {"name": "run_code_cell", "arguments": {"cellId": cid}}, timeout=3600)
        for c in out.get("content") or []:
            print(c.get("text", c))
        return
    elif cmd == "call":
        arg = sys.argv[3] if len(sys.argv) > 3 else "{}"
        args = json.loads(Path(arg[1:]).read_text(encoding="utf-8") if arg.startswith("@") else arg)
        out = http("/", {"name": sys.argv[2], "arguments": args})
    else:
        sys.exit(f"不認得的指令 {cmd}")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
