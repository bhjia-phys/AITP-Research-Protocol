"""Explicit routing-mode contracts shared by hook installers and runners."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


HOOK_ROUTING_MODES = frozenset({"dynamic", "pinned", "pinned_compat"})


@dataclass(frozen=True)
class HookRoutingMode:
    routing_mode: str
    pinned_session_id: str
    legacy_pinned: bool
    migration_required: bool

    def __post_init__(self) -> None:
        if self.routing_mode not in HOOK_ROUTING_MODES:
            raise ValueError("unsupported hook routing mode")
        if self.routing_mode == "dynamic" and self.pinned_session_id:
            raise ValueError("dynamic routing cannot carry a session pin")
        if self.routing_mode != "dynamic" and not self.pinned_session_id:
            raise ValueError("pinned hook routing requires a session pin")
        if self.legacy_pinned != (self.routing_mode == "pinned_compat"):
            raise ValueError("legacy_pinned must identify pinned_compat")
        if self.migration_required != self.legacy_pinned:
            raise ValueError("only legacy pinned routing requires migration")


def normalize_hook_routing_mode(
    routing_mode: object,
    session_id: object,
    *,
    legacy_positional: bool = False,
) -> HookRoutingMode:
    """Normalize one CLI or installer request without inferring a hidden pin."""

    mode = _text(routing_mode, "routing_mode").casefold().replace("-", "_")
    session = _text(session_id, "session_id")
    if mode == "pinned_compat":
        raise ValueError("pinned_compat is reserved for legacy positional sessions")
    if mode and mode not in {"dynamic", "pinned"}:
        raise ValueError(f"unsupported hook routing mode: {mode}")
    if legacy_positional:
        if mode:
            raise ValueError("legacy positional session cannot be combined with routing mode")
        if not session:
            raise ValueError("legacy positional routing requires a session pin")
        return HookRoutingMode("pinned_compat", session, True, True)
    if not mode:
        if session:
            raise ValueError("session pin requires explicit pinned routing")
        mode = "dynamic"
    if mode == "dynamic":
        if session:
            raise ValueError("dynamic routing does not accept a session pin")
        return HookRoutingMode("dynamic", "", False, False)
    if not session:
        raise ValueError("pinned routing requires a session pin")
    return HookRoutingMode("pinned", session, False, False)


def hook_routing_metadata(
    routing: HookRoutingMode,
    *,
    project_root: str | Path,
    topics_root: str | Path,
) -> dict[str, object]:
    if not isinstance(routing, HookRoutingMode):
        raise TypeError("routing must be a HookRoutingMode")
    return {
        "routing_mode": routing.routing_mode,
        "pinned_session_id": routing.pinned_session_id,
        "project_root": _absolute_path(project_root, "project_root"),
        "topics_root": _absolute_path(topics_root, "topics_root"),
        "legacy_pinned": routing.legacy_pinned,
        "migration_required": routing.migration_required,
        "runtime_metadata_only": True,
    }


def hook_routing_cli_args(routing: HookRoutingMode) -> list[str]:
    if not isinstance(routing, HookRoutingMode):
        raise TypeError("routing must be a HookRoutingMode")
    argv = ["--routing-mode", routing.routing_mode]
    if routing.pinned_session_id:
        argv.extend(["--session-id", routing.pinned_session_id])
    return argv


def resolve_installer_hook_routing(
    routing: HookRoutingMode | None,
    *,
    session_id: str = "",
) -> HookRoutingMode:
    if routing is not None:
        if not isinstance(routing, HookRoutingMode):
            raise TypeError("routing must be a HookRoutingMode")
        if session_id and session_id != routing.pinned_session_id:
            raise ValueError("installer session_id conflicts with routing selection")
        return routing
    return normalize_hook_routing_mode(
        "",
        session_id,
        legacy_positional=bool(session_id),
    )


def _text(value: object, label: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    text = value.strip()
    if len(text.encode("utf-8")) > 4096:
        raise ValueError(f"{label} is too large")
    return text


def _absolute_path(value: str | Path, label: str) -> str:
    if not isinstance(value, (str, Path)):
        raise TypeError(f"{label} must be a path")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{label} must be a non-empty path")
    return str(Path(text).expanduser().resolve(strict=False))


__all__ = [
    "HOOK_ROUTING_MODES",
    "HookRoutingMode",
    "hook_routing_cli_args",
    "hook_routing_metadata",
    "normalize_hook_routing_mode",
    "resolve_installer_hook_routing",
]
