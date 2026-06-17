"""
Native MCP stdio server — zero dependencies beyond Python stdlib.

Replaces FastMCP 3.x (ndjson) + claude_code_bridge.py (Content-Length converter)
with a single file that speaks both newline-delimited JSON and MCP's native
Content-Length framing. Codex CLI/App uses newline-delimited local stdio, while
Claude-style clients use Content-Length.

The tool functions are imported from mcp_server.py — they remain unchanged.
Only the transport and JSON-RPC dispatch are replaced.
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
import warnings
from pathlib import Path
from typing import Any

_DIAG = Path(__file__).resolve().parent / "_mcp_boot.log"
_FRAMING_MODE = "headers"

# Suppress any stderr warnings before importing mcp_server (which triggers
# fastmcp -> requests, which emits RequestsDependencyWarning on stderr).
# Claude Code treats early stderr output as a startup failure.
warnings.filterwarnings("ignore")

def _log(msg):
    try:
        with open(_DIAG, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')} pid={os.getpid()}] {msg}\n")
    except Exception:
        pass

_log(f"BOOT python={sys.executable} cwd={Path.cwd()}")


# ---------------------------------------------------------------------------
# Stdio framing
# ---------------------------------------------------------------------------

def _read_message() -> dict | None:
    """Read one JSON-RPC message from stdin.

    Codex CLI currently speaks newline-delimited JSON for local stdio MCP,
    while other clients use Content-Length framing. Support both and mirror the
    first frame type when writing responses.
    """
    global _FRAMING_MODE

    first = sys.stdin.buffer.read(1)
    if not first:
        return None
    while first in b" \t\r\n":
        first = sys.stdin.buffer.read(1)
        if not first:
            return None

    if first == b"{":
        _FRAMING_MODE = "lines"
        line = first + sys.stdin.buffer.readline()
        return json.loads(line.decode("utf-8"))

    _FRAMING_MODE = "headers"
    header = first
    while True:
        ch = sys.stdin.buffer.read(1)
        if not ch:
            return None
        header += ch
        if header.endswith(b"\r\n\r\n") or header.endswith(b"\n\n"):
            break
    content_length = 0
    for line in header.decode("utf-8").replace("\r\n", "\n").split("\n"):
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":", 1)[1].strip())
            break
    if content_length <= 0:
        return None
    # Loop to handle partial reads from pipes (Windows especially)
    body = b""
    while len(body) < content_length:
        chunk = sys.stdin.buffer.read(content_length - len(body))
        if not chunk:
            break
        body += chunk
    return json.loads(body.decode("utf-8"))


def _write_message(msg: dict) -> None:
    """Write one JSON-RPC message using the active stdin framing mode."""
    body = json.dumps(msg, ensure_ascii=False, default=str)
    encoded = body.encode("utf-8")
    if _FRAMING_MODE == "lines":
        sys.stdout.buffer.write(encoded + b"\n")
        sys.stdout.buffer.flush()
        return
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
_log("importing brain.mcp_server ...")
import brain.mcp_server as _ms
_log(f"imported, found tools")
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
        is_optional = False
        if param.annotation is not inspect.Parameter.empty:
            ann = param.annotation
            # Unwrap Optional / Union with None
            origin = getattr(ann, "__origin__", None)
            if origin is not None:
                args = getattr(ann, "__args__", ())
                non_none = [a for a in args if a is not type(None)]
                if len(args) > len(non_none):
                    is_optional = True  # None was in the union
                if non_none:
                    ann = non_none[0]
            elif hasattr(ann, "__union_params__"):
                # Python 3.9 Union backport
                pass
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
    # Strip leading whitespace from each line of the docstring
    lines = doc.split("\n")
    if len(lines) > 1:
        doc = lines[0] + "\n" + "\n".join(l.lstrip() for l in lines[1:])
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
    "name": "aitp-brain-legacy",
    "version": "0.5.0",
}


def _handle_request(req: dict) -> dict | None:
    """Handle a single JSON-RPC request. Returns response or None for notifications."""
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
        return None  # No response for notifications

    if method == "tools/list":
        return {
            "jsonrpc": "2.0", "id": rid,
            "result": {"tools": TOOL_SCHEMAS},
        }

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        _log(f"tools/call: {tool_name}")
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
            tb = traceback.format_exc()
            _log(f"tools/call ERROR: {tb[:300]}")
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
    _log("main() entered")
    while True:
        try:
            req = _read_message()
            _log(f"got: {req.get('method','?') if req else 'EOF'}")
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
