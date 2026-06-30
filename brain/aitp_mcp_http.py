"""
AITP MCP server over HTTP (Streamable HTTP transport).

Replaces the stdio native_mcp.py approach with a local HTTP server,
bypassing Windows pipe communication issues entirely.

Usage:
    python brain/aitp_mcp_http.py [--port PORT] [--host HOST]

Claude Code config:
    {"type": "http", "url": "http://127.0.0.1:PORT/mcp"}
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
import uuid
import warnings
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

_PORT = int(os.environ.get("AITP_MCP_HTTP_PORT", "9876"))
_HOST = os.environ.get("AITP_MCP_HTTP_HOST", "127.0.0.1")

# Suppress warnings before importing mcp_server
warnings.filterwarnings("ignore")

# Ensure brain/ is importable
_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# Import tool definitions (same as native_mcp.py)
print(f"[aitp-http] Importing brain.mcp_server ...", file=sys.stderr)
_t0 = time.time()
import brain.mcp_server as _ms
print(f"[aitp-http] Imported in {time.time() - _t0:.1f}s", file=sys.stderr)

# Collect tools (same logic as native_mcp.py)
_tools: dict[str, Any] = {}
for _name in dir(_ms):
    _obj = getattr(_ms, _name)
    if callable(_obj) and hasattr(_obj, "__mcp_tool__") or (
        callable(_obj) and _name.startswith("aitp_")
    ):
        _tools[_name] = _obj

if len(_tools) < 10:
    _tools = {}
    for _name in dir(_ms):
        _obj = getattr(_ms, _name)
        if callable(_obj) and _name.startswith("aitp_"):
            _tools[_name] = _obj

# Tool schema building (same as native_mcp.py)
def _build_tool_schema(func) -> dict:
    import inspect
    sig = inspect.signature(func)
    properties = {}
    required = []
    for pname, param in sig.parameters.items():
        if pname in ("self", "cls"):
            continue
        ptype = "string"
        is_optional = False
        if param.annotation is not inspect.Parameter.empty:
            ann = param.annotation
            origin = getattr(ann, "__origin__", None)
            if origin is not None:
                args = getattr(ann, "__args__", ())
                non_none = [a for a in args if a is not type(None)]
                if len(args) > len(non_none):
                    is_optional = True
                if non_none:
                    ann = non_none[0]
            if ann is int:
                ptype = "integer"
            elif ann is float:
                ptype = "number"
            elif ann is bool:
                ptype = "boolean"
            elif ann is dict or str(ann).startswith("dict"):
                ptype = "object"
            elif ann is list or str(ann).startswith("list"):
                ptype = "array"
        properties[pname] = {"type": ptype}
        if param.default is inspect.Parameter.empty and not is_optional:
            required.append(pname)

    doc = (func.__doc__ or "").strip()
    return {
        "name": func.__name__,
        "description": doc[:500] if doc else f"AITP tool: {func.__name__}",
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }

TOOL_SCHEMAS: list[dict] = []
for _tname, _tfunc in sorted(_tools.items()):
    try:
        TOOL_SCHEMAS.append(_build_tool_schema(_tfunc))
    except Exception:
        TOOL_SCHEMAS.append({
            "name": _tname,
            "description": f"AITP tool: {_tname}",
            "inputSchema": {"type": "object", "properties": {}, "required": []},
        })

SERVER_INFO = {"name": "aitp-brain-legacy-http", "version": "1.0.0"}
_sessions: dict[str, str] = {}  # session_id -> created_at


def handle_request(req: dict) -> dict | None:
    rid = req.get("id")
    method = req.get("method", "")
    params = req.get("params", {})

    if method == "initialize":
        client_version = params.get("protocolVersion", "2025-06-18")
        return {
            "jsonrpc": "2.0", "id": rid,
            "result": {
                "protocolVersion": client_version,
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            },
        }

    if method == "ping":
        return {"jsonrpc": "2.0", "id": rid, "result": {}}

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        return {
            "jsonrpc": "2.0", "id": rid,
            "result": {"tools": TOOL_SCHEMAS},
        }

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        func = _tools.get(tool_name)
        if func is None:
            return {
                "jsonrpc": "2.0", "id": rid,
                "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
            }
        if (
            getattr(_ms, "is_legacy_write_tool", lambda _name: False)(tool_name)
            and not getattr(_ms, "_legacy_writes_enabled", lambda: False)()
        ):
            payload = getattr(_ms, "legacy_write_blocked_payload")(tool_name)
            return {
                "jsonrpc": "2.0", "id": rid,
                "error": {
                    "code": -32050,
                    "message": payload["message"],
                    "data": payload,
                },
            }
        try:
            result = func(**arguments)
            if result is None:
                text = ""
            elif isinstance(result, dict):
                text = json.dumps(result, ensure_ascii=False, default=str)
            else:
                text = str(result)
            return {
                "jsonrpc": "2.0", "id": rid,
                "result": {"content": [{"type": "text", "text": text}]},
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0", "id": rid,
                "error": {"code": -32603, "message": f"{type(e).__name__}: {e}"},
            }

    return {
        "jsonrpc": "2.0", "id": rid,
        "error": {"code": -32601, "message": f"Unknown method: {method}"},
    }


class MCPHandler(BaseHTTPRequestHandler):
    """HTTP handler for MCP JSON-RPC requests."""

    def do_GET(self):
        """Health check endpoint."""
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok", "server": "aitp-brain",
                "version": SERVER_INFO["version"], "tools": len(TOOL_SCHEMAS),
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """MCP JSON-RPC endpoint."""
        if self.path != "/mcp":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            req = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        # Session management
        session_id = self.headers.get("Mcp-Session-Id", "")
        new_session_id = None

        if req.get("method") == "initialize":
            new_session_id = uuid.uuid4().hex[:16]
            _sessions[new_session_id] = time.strftime("%Y-%m-%dT%H:%M:%S")

        resp = handle_request(req)

        if resp is None:
            # Notification — return 202 Accepted
            self.send_response(202)
            self.end_headers()
            return

        resp_body = json.dumps(resp, ensure_ascii=False, default=str)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        if new_session_id:
            self.send_header("Mcp-Session-Id", new_session_id)
        self.send_header("Content-Length", str(len(resp_body.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(resp_body.encode("utf-8"))

    def do_DELETE(self):
        """Session cleanup."""
        session_id = self.headers.get("Mcp-Session-Id", "")
        _sessions.pop(session_id, None)
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        """Log to stderr."""
        print(f"[aitp-http] {args[0]}", file=sys.stderr)


def main():
    server = HTTPServer((_HOST, _PORT), MCPHandler)
    print(f"[aitp-http] AITP MCP HTTP server on http://{_HOST}:{_PORT}/mcp", file=sys.stderr)
    print(f"[aitp-http] {len(TOOL_SCHEMAS)} tools loaded", file=sys.stderr)
    print(f"[aitp-http] Health check: http://{_HOST}:{_PORT}/health", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[aitp-http] Shutting down", file=sys.stderr)
        server.shutdown()


if __name__ == "__main__":
    main()
