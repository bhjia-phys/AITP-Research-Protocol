"""AITP v5-only native MCP stdio server.

This entrypoint intentionally exposes only ``brain.v5.mcp_tools.aitp_v5_*``
wrappers.  Keep the legacy ``brain/native_mcp.py`` available for rollback, but
use this module when a client should talk to the typed v5 kernel only.
"""

from __future__ import annotations

import inspect
import json
import os
import sys
import tempfile
import time
import traceback
import warnings
from pathlib import Path
from typing import Any

_DIAG = Path(os.environ.get("AITP_V5_MCP_LOG", str(Path(tempfile.gettempdir()) / "aitp_v5_mcp_boot.log")))
_REPO_ROOT = Path(__file__).resolve().parents[2]
_OUTPUT_MODE = "content-length"
# Legacy compatibility aliases are disabled by default in 0.5.0.  Set
# AITP_V5_EXPOSE_COMPAT_ALIASES=1 only for migration/debug sessions that must
# discover old topic shells; current research should use aitp_v5_* typed tools.
_EXPOSE_COMPAT_ALIASES = os.environ.get("AITP_V5_EXPOSE_COMPAT_ALIASES") == "1"
_COMPAT_TOOL_NAMES = (
    {
        "aitp_list_topics",
        "aitp_get_execution_brief",
        "aitp_bootstrap_topic",
    }
    if _EXPOSE_COMPAT_ALIASES
    else set()
)

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

warnings.filterwarnings("ignore")


def _log(message: str) -> None:
    try:
        with _DIAG.open("a", encoding="utf-8") as handle:
            handle.write(f"[{time.strftime('%H:%M:%S')} pid={os.getpid()}] {message}\n")
    except Exception:
        pass


def _read_message() -> dict[str, Any] | None:
    global _OUTPUT_MODE

    first = b""
    while True:
        char = sys.stdin.buffer.read(1)
        if not char:
            return None
        if char not in b" \t\r\n":
            first = char
            break

    if first in {b"{", b"["}:
        _OUTPUT_MODE = "ndjson"
        line = first + sys.stdin.buffer.readline()
        return json.loads(line.decode("utf-8"))

    _OUTPUT_MODE = "content-length"
    header = first
    while True:
        char = sys.stdin.buffer.read(1)
        if not char:
            _log(f"EOF while reading header prefix={header[:120]!r}")
            return None
        header += char
        if header.endswith(b"\r\n\r\n") or header.endswith(b"\n\n"):
            break

    content_length = 0
    for line in header.decode("utf-8").replace("\r\n", "\n").split("\n"):
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":", 1)[1].strip())
            break
    if content_length <= 0:
        return None

    body = b""
    while len(body) < content_length:
        chunk = sys.stdin.buffer.read(content_length - len(body))
        if not chunk:
            break
        body += chunk
    return json.loads(body.decode("utf-8"))


def _write_message(message: dict[str, Any]) -> None:
    body = json.dumps(message, ensure_ascii=False, default=str).encode("utf-8")
    if _OUTPUT_MODE == "ndjson":
        sys.stdout.buffer.write(body + b"\n")
    else:
        sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8") + body)
    sys.stdout.buffer.flush()


def _annotation_schema(annotation: Any) -> dict[str, Any]:
    if annotation is inspect.Parameter.empty:
        return {"type": "string"}
    if isinstance(annotation, str):
        return _annotation_string_schema(annotation)
    origin = getattr(annotation, "__origin__", None)
    if origin is not None:
        args = getattr(annotation, "__args__", ())
        schema_types = _dedupe_schema_types([_schema_type_for_annotation(arg) for arg in args])
        return {"type": schema_types[0] if len(schema_types) == 1 else schema_types}
    return {"type": _schema_type_for_annotation(annotation)}


def _annotation_string_schema(annotation: str) -> dict[str, Any]:
    text = annotation.replace("typing.", "").strip()
    if "|" in text:
        schema_types = _dedupe_schema_types(
            [_schema_type_for_annotation(part.strip()) for part in text.split("|")]
        )
        return {"type": schema_types[0] if len(schema_types) == 1 else schema_types}
    return {"type": _schema_type_for_annotation(text)}


def _schema_type_for_annotation(annotation: Any) -> str:
    if annotation is type(None):
        return "null"
    if isinstance(annotation, str):
        text = annotation.strip()
        if text in {"None", "NoneType", "null"}:
            return "null"
        if text in {"int", "builtins.int"}:
            return "integer"
        if text in {"float", "builtins.float"}:
            return "number"
        if text in {"bool", "builtins.bool"}:
            return "boolean"
        if text in {"Any", "typing.Any"} or text.startswith("dict"):
            return "object"
        if text.startswith("list"):
            return "array"
        return "string"
    if annotation is int:
        return "integer"
    if annotation is float:
        return "number"
    if annotation is bool:
        return "boolean"
    if annotation in {dict, Any} or str(annotation).startswith("dict"):
        return "object"
    if annotation is list or str(annotation).startswith("list"):
        return "array"
    return "string"


def _dedupe_schema_types(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        if value not in out:
            out.append(value)
    return out


def _build_tool_schema(name: str, func: Any) -> dict[str, Any]:
    signature = inspect.signature(func)
    properties: dict[str, Any] = {}
    required: list[str] = []
    for param_name, param in signature.parameters.items():
        if param_name in {"self", "cls"}:
            continue
        annotation = param.annotation
        properties[param_name] = _annotation_schema(annotation)
        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    doc = (func.__doc__ or f"AITP v5 tool: {name}").strip()
    lines = doc.splitlines()
    description = lines[0] if lines else f"AITP v5 tool: {name}"
    return {
        "name": name,
        "description": description[:500],
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }


def _load_tools() -> dict[str, Any]:
    _log(f"BOOT python={sys.executable} cwd={Path.cwd()}")
    _log("importing brain.v5.mcp_tools ...")
    from brain.v5 import mcp_tools

    tools = {
        name: getattr(mcp_tools, name)
        for name in dir(mcp_tools)
        if (name.startswith("aitp_v5_") or name in _COMPAT_TOOL_NAMES)
        and callable(getattr(mcp_tools, name))
    }
    _log(f"loaded {len(tools)} v5 tools")
    return tools


_TOOLS = _load_tools()
_TOOL_SCHEMAS = [_build_tool_schema(name, func) for name, func in sorted(_TOOLS.items())]
from brain.v5 import __version__ as _AITP_VERSION

_SERVER_INFO = {"name": "aitp-v5-brain", "version": _AITP_VERSION}


def _handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    request_id = request.get("id")
    method = request.get("method", "")
    params = request.get("params", {})

    if method == "initialize":
        protocol_version = params.get("protocolVersion", "2025-06-18")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": protocol_version,
                "capabilities": {"tools": {}},
                "serverInfo": _SERVER_INFO,
            },
        }

    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": _TOOL_SCHEMAS}}

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        func = _TOOLS.get(tool_name)
        if func is None:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
            }
        try:
            result = func(**arguments)
            text = "" if result is None else json.dumps(result, ensure_ascii=False, default=str)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": text}]},
            }
        except Exception as exc:
            _log(f"tools/call ERROR: {traceback.format_exc()[:500]}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": f"{type(exc).__name__}: {exc}"},
            }

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"Unknown method: {method}"},
    }


def main() -> None:
    _log("main() entered")
    while True:
        try:
            request = _read_message()
        except Exception:
            _log(f"READ ERROR: {traceback.format_exc()[:500]}")
            continue
        if request is None:
            _log("EOF")
            break
        _log(f"got: {request.get('method', '?')}")
        response = _handle_request(request)
        if response is not None:
            _write_message(response)


if __name__ == "__main__":
    main()
