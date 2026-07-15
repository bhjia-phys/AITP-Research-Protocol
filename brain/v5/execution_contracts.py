"""Redaction and shape contracts for reproducible execution records."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlsplit, urlunsplit


_SENSITIVE_KEY = re.compile(
    r"(^|[_-])(token|password|passwd|secret|credential|api[_-]?key|access[_-]?key|private[_-]?key)($|[_-])",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RedactionPolicy:
    environment_allowlist: tuple[str, ...] = ()
    sensitive_argv_positions: tuple[int, ...] = ()
    replacement: str = "[REDACTED]"


@dataclass(frozen=True)
class RedactionResult:
    payload: dict[str, Any]
    redacted_paths: tuple[str, ...]
    omitted_paths: tuple[str, ...]
    can_update_claim_trust: bool = False


def redact_execution_payload(
    payload: Mapping[str, Any],
    policy: RedactionPolicy | None = None,
) -> RedactionResult:
    """Return a detached execution payload with secrets removed."""

    active = policy or RedactionPolicy()
    redacted: list[str] = []
    omitted: list[str] = []
    result = _redact_value(dict(payload), active, "", redacted)
    environment = result.get("environment")
    if isinstance(environment, dict) and active.environment_allowlist:
        allowed = set(active.environment_allowlist)
        for key in list(environment):
            if key not in allowed:
                environment.pop(key)
                omitted.append(f"environment.{key}")
    argv = result.get("argv")
    if isinstance(argv, list):
        for position in active.sensitive_argv_positions:
            if 0 <= position < len(argv):
                argv[position] = active.replacement
                redacted.append(f"argv[{position}]")
    return RedactionResult(
        payload=result,
        redacted_paths=tuple(sorted(set(redacted))),
        omitted_paths=tuple(sorted(set(omitted))),
    )


def _redact_value(
    value: Any,
    policy: RedactionPolicy,
    path: str,
    redacted: list[str],
) -> Any:
    if isinstance(value, Mapping):
        result = {}
        for raw_key, item in value.items():
            key = str(raw_key)
            child_path = f"{path}.{key}" if path else key
            if _SENSITIVE_KEY.search(key):
                result[key] = policy.replacement
                redacted.append(child_path)
            else:
                result[key] = _redact_value(item, policy, child_path, redacted)
        return result
    if isinstance(value, (list, tuple)):
        return [
            _redact_value(item, policy, f"{path}[{index}]", redacted)
            for index, item in enumerate(value)
        ]
    if isinstance(value, str) and "://" in value:
        parsed = urlsplit(value)
        if parsed.username is not None or parsed.password is not None:
            host = parsed.hostname or ""
            if parsed.port is not None:
                host = f"{host}:{parsed.port}"
            redacted.append(path)
            return urlunsplit((parsed.scheme, host, parsed.path, parsed.query, parsed.fragment))
    return value
