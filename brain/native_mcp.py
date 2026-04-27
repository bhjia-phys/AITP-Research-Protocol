"""
Native MCP stdio server — zero dependencies beyond Python stdlib.

Replaces FastMCP 3.x (ndjson) + claude_code_bridge.py (Content-Length converter)
with a single file that speaks MCP's native Content-Length framing directly.

The tool functions are imported from mcp_server.py — they remain unchanged.
Only the transport and JSON-RPC dispatch are replaced.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Content-Length framed stdio (MCP spec)
# ---------------------------------------------------------------------------

def _read_message() -> dict | None:
    """Read one Content-Length-prefixed JSON-RPC message from stdin."""
    header = b""
    while True:
        ch = sys.stdin.buffer.read(1)
        if not ch:
            return None
        header += ch
        if header.endswith(b"\r\n\r\n"):
            break
    content_length = 0
    for line in header.decode("utf-8").split("\r\n"):
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":", 1)[1].strip())
            break
    if content_length <= 0:
        return None
    body = sys.stdin.buffer.read(content_length)
    return json.loads(body.decode("utf-8"))


def _write_message(msg: dict) -> None:
    """Write one Content-Length-prefixed JSON-RPC message to stdout."""
    body = json.dumps(msg, ensure_ascii=False, default=str)
    encoded = body.encode("utf-8")
    header = f"Content-Length: {len(encoded)}\r\n\r\n".encode("utf-8")
    sys.stdout.buffer.write(header + encoded)
    sys.stdout.buffer.flush()


# ---------------------------------------------------------------------------
# JSON-RPC dispatch
# ---------------------------------------------------------------------------

# Ensure brain/ is importable
_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# Collect all @mcp.tool() decorated functions from mcp_server
import brain.mcp_server as _ms
_tools: dict[str, Any] = {}
for _name in dir(_ms):
    _obj = getattr(_ms, _name)
    if callable(_obj) and hasattr(_obj, "__mcp_tool__") or (
        callable(_obj) and _name.startswith("aitp_")
    ):
        _tools[_name] = _obj

# If __mcp_tool__ detection failed, collect all aitp_* callables
if len(_tools) < 10:
    _tools = {}
    for _name in dir(_ms):
        _obj = getattr(_ms, _name)
        if callable(_obj) and _name.startswith("aitp_"):
            _tools[_name] = _obj


def _build_tool_schema(func) -> dict:
    """Build a minimal JSON Schema for a tool from its signature and docstring."""
    import inspect
    sig = inspect.signature(func)
    properties = {}
    required = []
    for pname, param in sig.parameters.items():
        if pname in ("self", "cls"):
            continue
        ptype = "string"
        if param.annotation is not inspect.Parameter.empty:
            ann = param.annotation
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
        if param.default is inspect.Parameter.empty:
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

SERVER_INFO = {
    "name": "aitp-brain",
    "version": "0.6.0",
}


def _handle_request(req: dict) -> dict | None:
    """Handle a single JSON-RPC request. Returns response or None for notifications."""
    rid = req.get("id")
    method = req.get("method", "")
    params = req.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": rid,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            },
        }

    if method == "notifications/initialized":
        return None  # No response for notifications

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
        try:
            result = func(**arguments)
            # Serialize result — some tools return GateResult (dict subclass)
            if isinstance(result, dict):
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

    # Unknown method
    return {
        "jsonrpc": "2.0", "id": rid,
        "error": {"code": -32601, "message": f"Unknown method: {method}"},
    }


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    while True:
        try:
            req = _read_message()
        except Exception:
            # Log but don't crash
            print(f"READ ERROR: {traceback.format_exc()}", file=sys.stderr)
            continue
        if req is None:
            break
        try:
            resp = _handle_request(req)
        except Exception:
            resp = {
                "jsonrpc": "2.0", "id": req.get("id"),
                "error": {"code": -32603, "message": traceback.format_exc()[:500]},
            }
        if resp is not None:
            try:
                _write_message(resp)
            except Exception:
                print(f"WRITE ERROR: {traceback.format_exc()}", file=sys.stderr)


if __name__ == "__main__":
    main()
