#!/usr/bin/env python3
"""Launch AITP v5 MCP, or a first-run setup MCP when configuration is missing."""

from __future__ import annotations

import inspect
import json
import os
import runpy
import sys
from pathlib import Path
from typing import Any


CONFIG_PATH = Path.home() / ".aitp" / "codex-plugin-config.json"
INSTALL_RECORD_PATH = Path.home() / ".aitp" / "install-record.json"


def main() -> None:
    plugin_root = Path(__file__).resolve().parents[1]
    install_record = _read_json(INSTALL_RECORD_PATH)
    config = _read_json(CONFIG_PATH)
    repo_root = _resolve_repo_root(plugin_root, config, install_record)

    if repo_root is None:
        _run_setup_server(plugin_root, config, install_record)
        return

    topics_root = _resolve_topics_root(config, install_record)
    os.environ.setdefault("AITP_TOPICS_ROOT", str(topics_root))
    topics_root.mkdir(parents=True, exist_ok=True)

    entrypoint = repo_root / "brain" / "v5" / "native_mcp.py"
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    os.chdir(repo_root)
    sys.argv = [str(entrypoint)]
    runpy.run_path(str(entrypoint), run_name="__main__")


def _read_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_config(repo_root: Path, topics_root: Path) -> dict[str, str]:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "repo_root": str(repo_root.resolve()),
        "topics_root": str(topics_root.expanduser().resolve()),
    }
    CONFIG_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def _resolve_repo_root(plugin_root: Path, config: dict, install_record: dict) -> Path | None:
    candidates: list[Path] = []

    env_repo = os.environ.get("AITP_REPO_ROOT", "").strip()
    if env_repo:
        candidates.append(Path(env_repo).expanduser())

    config_repo = str(config.get("repo_root", "")).strip()
    if config_repo:
        candidates.append(Path(config_repo).expanduser())

    for install in install_record.get("installs", {}).values():
        repo_value = install.get("variables", {}).get("REPO_ROOT", "")
        if repo_value:
            candidates.append(Path(repo_value).expanduser())

    candidates.extend(
        [
            plugin_root / "vendor" / "AITP-Research-Protocol",
            Path.cwd(),
            *Path.cwd().parents,
        ]
    )

    for candidate in candidates:
        repo = _normalize_repo_candidate(candidate)
        if repo and _is_aitp_repo(repo):
            return repo.resolve()
    return None


def _normalize_repo_candidate(candidate: Path) -> Path | None:
    candidate = candidate.expanduser()
    if candidate.name == "native_mcp.py":
        return candidate.parents[2]
    return candidate


def _is_aitp_repo(path: Path) -> bool:
    return (path / "brain" / "v5" / "native_mcp.py").is_file()


def _resolve_topics_root(config: dict, install_record: dict) -> Path:
    env_topics = os.environ.get("AITP_TOPICS_ROOT", "").strip()
    if env_topics:
        return Path(env_topics).expanduser()

    config_topics = str(config.get("topics_root", "")).strip()
    if config_topics:
        return Path(config_topics).expanduser()

    for install in install_record.get("installs", {}).values():
        topics_value = install.get("variables", {}).get("TOPICS_ROOT", "")
        if topics_value:
            return Path(topics_value).expanduser()

    return Path.home() / ".aitp" / "topics"


class SetupMcpServer:
    def __init__(self, plugin_root: Path, config: dict, install_record: dict) -> None:
        self.plugin_root = plugin_root
        self.config = config
        self.install_record = install_record
        self.output_mode = "content-length"
        self.tools = {
            "aitp_config_status": self.aitp_config_status,
            "aitp_configure": self.aitp_configure,
            "aitp_suggest_config": self.aitp_suggest_config,
        }
        self.tool_schemas = [
            self._build_tool_schema(name, func) for name, func in sorted(self.tools.items())
        ]

    def aitp_config_status(self) -> dict:
        """Show whether the AITP Codex plugin is configured."""

        repo_root = _resolve_repo_root(self.plugin_root, self.config, self.install_record)
        topics_root = _resolve_topics_root(self.config, self.install_record)
        return {
            "configured": repo_root is not None,
            "mode": "setup" if repo_root is None else "ready",
            "config_path": str(CONFIG_PATH),
            "repo_root": str(repo_root) if repo_root else "",
            "topics_root": str(topics_root),
            "needs_user_input": repo_root is None,
            "next_step": (
                "Ask the user for the local AITP-Research-Protocol checkout path, "
                "or ask whether Codex should clone it into a chosen folder."
                if repo_root is None
                else "Restart the MCP server or open a new Codex thread to load full AITP tools."
            ),
        }

    def aitp_suggest_config(self) -> dict:
        """Suggest first-run AITP plugin configuration choices."""

        default_topics = Path.home() / ".aitp" / "topics"
        candidates = []
        env_repo = os.environ.get("AITP_REPO_ROOT", "").strip()
        if env_repo:
            candidates.append(env_repo)
        for install in self.install_record.get("installs", {}).values():
            repo_value = install.get("variables", {}).get("REPO_ROOT", "")
            if repo_value and repo_value not in candidates:
                candidates.append(repo_value)
        vendor = self.plugin_root / "vendor" / "AITP-Research-Protocol"
        if str(vendor) not in candidates:
            candidates.append(str(vendor))
        return {
            "repo_root_candidates": candidates,
            "default_topics_root": str(default_topics),
            "recommended_question": (
                "Where is your local AITP-Research-Protocol checkout, and where "
                "should AITP store topic records?"
            ),
            "setup_call": "aitp_configure(repo_root=<path>, topics_root=<path>)",
        }

    def aitp_configure(self, repo_root: str, topics_root: str = "") -> dict:
        """Persist the AITP repo path and topics root for this Codex plugin."""

        repo = Path(repo_root).expanduser()
        if not _is_aitp_repo(repo):
            return {
                "ok": False,
                "error": "repo_root must point to an AITP-Research-Protocol checkout containing brain/v5/native_mcp.py",
                "repo_root": str(repo),
            }
        topics = Path(topics_root).expanduser() if str(topics_root or "").strip() else Path.home() / ".aitp" / "topics"
        topics.mkdir(parents=True, exist_ok=True)
        payload = _write_config(repo, topics)
        self.config = payload
        return {
            "ok": True,
            "config_path": str(CONFIG_PATH),
            "repo_root": payload["repo_root"],
            "topics_root": payload["topics_root"],
            "next_step": "Restart the MCP server or open a new Codex thread so full AITP v5 tools load.",
        }

    def serve(self) -> None:
        while True:
            request = self._read_message()
            if request is None:
                break
            response = self._handle_request(request)
            if response is not None:
                self._write_message(response)

    def _handle_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
        request_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": params.get("protocolVersion", "2025-06-18"),
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "aitp-config-setup", "version": "0.1.0"},
                },
            }
        if method == "ping":
            return {"jsonrpc": "2.0", "id": request_id, "result": {}}
        if method == "notifications/initialized":
            return None
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": self.tool_schemas}}
        if method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            func = self.tools.get(tool_name)
            if func is None:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
                }
            try:
                result = func(**arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]},
                }
            except Exception as exc:
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

    def _read_message(self) -> dict[str, Any] | None:
        first = b""
        while True:
            char = sys.stdin.buffer.read(1)
            if not char:
                return None
            if char not in b" \t\r\n":
                first = char
                break

        if first in {b"{", b"["}:
            self.output_mode = "ndjson"
            return json.loads((first + sys.stdin.buffer.readline()).decode("utf-8"))

        self.output_mode = "content-length"
        header = first
        while True:
            char = sys.stdin.buffer.read(1)
            if not char:
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
        body = sys.stdin.buffer.read(content_length)
        return json.loads(body.decode("utf-8"))

    def _write_message(self, message: dict[str, Any]) -> None:
        body = json.dumps(message, ensure_ascii=False, default=str).encode("utf-8")
        if self.output_mode == "ndjson":
            sys.stdout.buffer.write(body + b"\n")
        else:
            sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8") + body)
        sys.stdout.buffer.flush()

    def _build_tool_schema(self, name: str, func: Any) -> dict[str, Any]:
        signature = inspect.signature(func)
        properties = {}
        required = []
        for param_name, param in signature.parameters.items():
            properties[param_name] = {"type": "string"}
            if param.default is inspect.Parameter.empty:
                required.append(param_name)
        return {
            "name": name,
            "description": (func.__doc__ or f"AITP setup tool: {name}").strip().splitlines()[0],
            "inputSchema": {"type": "object", "properties": properties, "required": required},
        }


def _run_setup_server(plugin_root: Path, config: dict, install_record: dict) -> None:
    SetupMcpServer(plugin_root, config, install_record).serve()


if __name__ == "__main__":
    main()
