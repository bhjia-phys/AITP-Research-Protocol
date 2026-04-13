from __future__ import annotations

from typing import Any


VALID_MCP_PROFILES = ("full", "review", "skeptic")
READ_ONLY_MCP_PROFILES = frozenset({"review", "skeptic"})
MCP_PROFILE_SERVER_NAMES = {
    "full": "aitp",
    "review": "aitp-review",
    "skeptic": "aitp-skeptic",
}


def normalize_mcp_profile(profile: str | None) -> str:
    resolved = str(profile or "full").strip().lower()
    if not resolved:
        return "full"
    if resolved not in VALID_MCP_PROFILES:
        raise ValueError(
            f"Unsupported MCP profile: {profile}. Expected one of: {', '.join(VALID_MCP_PROFILES)}"
        )
    return resolved


def is_read_only_mcp_profile(profile: str | None) -> bool:
    return normalize_mcp_profile(profile) in READ_ONLY_MCP_PROFILES


def server_name_for_mcp_profile(profile: str | None) -> str:
    return MCP_PROFILE_SERVER_NAMES[normalize_mcp_profile(profile)]


def profile_instructions(profile: str | None) -> str:
    resolved = normalize_mcp_profile(profile)
    if resolved == "review":
        return (
            "AITP review-agent MCP tools. This profile is mechanically read-only: "
            "inspect runtime state and tool manifests, but do not mutate topic artifacts."
        )
    if resolved == "skeptic":
        return (
            "AITP skeptic-agent MCP tools. This profile is mechanically read-only: "
            "inspect runtime state and tool manifests while remaining unable to mutate topic artifacts."
        )
    return (
        "AITP kernel tools for orchestrating topic runs, reading runtime state, "
        "scaffolding trust gates, auditing conformance, and installing agent wrappers."
    )


def tool_allowed_in_profile(tool_name: str, access_mode: str, profile: str | None) -> bool:
    del tool_name
    resolved_profile = normalize_mcp_profile(profile)
    normalized_access = str(access_mode).strip().lower()
    if normalized_access not in {"read", "write"}:
        raise ValueError(f"Unsupported MCP tool access mode: {access_mode}")
    if resolved_profile == "full":
        return True
    return normalized_access == "read"


def build_profile_tool_manifest(profile: str | None, tool_access_map: dict[str, str]) -> dict[str, Any]:
    resolved_profile = normalize_mcp_profile(profile)
    normalized_access = {
        str(name): str(access).strip().lower()
        for name, access in tool_access_map.items()
    }
    allowed_tools = sorted(
        name
        for name, access in normalized_access.items()
        if tool_allowed_in_profile(name, access, resolved_profile)
    )
    blocked_tools = sorted(set(normalized_access) - set(allowed_tools))
    return {
        "profile": resolved_profile,
        "server_name": server_name_for_mcp_profile(resolved_profile),
        "read_only": is_read_only_mcp_profile(resolved_profile),
        "allowed_tools": allowed_tools,
        "blocked_tools": blocked_tools,
        "tool_access": dict(sorted(normalized_access.items())),
    }
