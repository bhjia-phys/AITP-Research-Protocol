"""Minimal MCP server — just to test if Claude Code spawns the process."""
import os
import sys
import json
from pathlib import Path

# Write PID to file immediately to prove we started
LOG = Path(os.environ.get("AITP_MCP_DIAG_LOG", str(Path(__file__).with_name("_mcp_diag.log"))))
with open(LOG, "a", encoding="utf-8") as f:
    f.write(f"STARTED pid={os.getpid()} executable={sys.executable} cwd={Path.cwd()}\n")

def read_msg():
    header = b""
    while True:
        ch = sys.stdin.buffer.read(1)
        if not ch: return None
        header += ch
        if header.endswith(b"\r\n\r\n"): break
    cl = 0
    for line in header.decode("utf-8").split("\r\n"):
        if line.lower().startswith("content-length:"):
            cl = int(line.split(":", 1)[1].strip())
    if cl <= 0: return None
    body = b""
    while len(body) < cl:
        chunk = sys.stdin.buffer.read(cl - len(body))
        if not chunk: break
        body += chunk
    return json.loads(body.decode("utf-8"))

def write_msg(msg):
    body = json.dumps(msg, ensure_ascii=False)
    enc = body.encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(enc)}\r\n\r\n".encode() + enc)
    sys.stdout.buffer.flush()

def main():
    while True:
        req = read_msg()
        if req is None: break
        method = req.get("method", "")
        rid = req.get("id")
        params = req.get("params", {})

        if method == "initialize":
            write_msg({
                "jsonrpc": "2.0", "id": rid,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "aitp-minimal", "version": "0.5.0"},
                }
            })
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            write_msg({
                "jsonrpc": "2.0", "id": rid,
                "result": {"tools": [{
                    "name": "aitp_ping",
                    "description": "Ping test tool — returns pong",
                    "inputSchema": {"type": "object", "properties": {}, "required": []}
                }]}
            })
        elif method == "tools/call":
            write_msg({
                "jsonrpc": "2.0", "id": rid,
                "result": {"content": [{"type": "text", "text": "pong"}]}
            })

if __name__ == "__main__":
    main()
