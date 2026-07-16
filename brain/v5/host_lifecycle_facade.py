"""Read-only characterization of currently installed host lifecycle capabilities."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


HOST_LIFECYCLE_CAPABILITY_SCHEMA_VERSION = "host_lifecycle_capability_matrix/v1"


@dataclass(frozen=True)
class HostLifecycleEventCapability:
    """One installed automatic host event and its current observable contract."""

    logical_event: str
    native_event: str
    installation_kind: str
    output_contract: str
    trace_contract: str
    failure_contract: str
    timeout_contract: str


@dataclass(frozen=True)
class HostLifecycleCapability:
    """Read-only lifecycle boundary for a real host configuration owner."""

    host: str
    owner_paths: tuple[str, ...]
    automatic_events: tuple[HostLifecycleEventCapability, ...]
    unsupported_events: tuple[str, ...]
    fallback_operations: Mapping[str, str]
    legacy_injection_conflicts: tuple[str, ...] = ()

    def event(self, logical_event: str) -> HostLifecycleEventCapability:
        """Return the installed automatic event for a later normalizer or report."""

        for event in self.automatic_events:
            if event.logical_event == logical_event:
                return event
        raise ValueError(f"host {self.host!r} has no installed automatic event {logical_event!r}")


@dataclass(frozen=True)
class HostLifecycleCapabilityMatrix:
    """Versioned immutable matrix suitable for later normalization and readiness work."""

    schema_version: str
    hosts: Mapping[str, HostLifecycleCapability]


def _event(
    logical_event: str,
    native_event: str,
    installation_kind: str,
    output_contract: str,
    trace_contract: str,
    failure_contract: str,
    timeout_contract: str = "no_owner_timeout",
) -> HostLifecycleEventCapability:
    return HostLifecycleEventCapability(
        logical_event=logical_event,
        native_event=native_event,
        installation_kind=installation_kind,
        output_contract=output_contract,
        trace_contract=trace_contract,
        failure_contract=failure_contract,
        timeout_contract=timeout_contract,
    )


def _profile(
    host: str,
    owner_paths: tuple[str, ...],
    automatic_events: tuple[HostLifecycleEventCapability, ...],
    unsupported_events: tuple[str, ...],
    fallback_operations: dict[str, str],
    legacy_injection_conflicts: tuple[str, ...] = (),
) -> HostLifecycleCapability:
    return HostLifecycleCapability(
        host=host,
        owner_paths=owner_paths,
        automatic_events=automatic_events,
        unsupported_events=unsupported_events,
        fallback_operations=MappingProxyType(dict(fallback_operations)),
        legacy_injection_conflicts=legacy_injection_conflicts,
    )


_CLAUDE_EVENTS = (
    _event(
        "session_start",
        "SessionStart",
        "native_installed_hook",
        "suppressed_continue_with_compact_workspace_refresh",
        "no_trace_event",
        "hook_failure_propagates_to_host",
    ),
    _event(
        "pre_tool",
        "PreToolUse",
        "native_installed_hook",
        "hook_decision_payload",
        "no_trace_event",
        "hook_failure_propagates_to_host",
    ),
    _event(
        "post_tool",
        "PostToolUse",
        "native_installed_hook",
        "suppressed_continue_with_hook_trace_event_record",
        "append_hook_trace_event",
        "hook_failure_propagates_to_host",
    ),
)

_KIMI_EVENTS = (
    _event(
        "session_start",
        "SessionStart",
        "native_installed_hook",
        "suppressed_continue_with_compact_workspace_refresh",
        "no_trace_event",
        "hook_failure_propagates_to_host",
    ),
    _event(
        "pre_tool",
        "PreToolUse",
        "native_installed_hook",
        "hook_decision_payload",
        "no_trace_event",
        "hook_failure_propagates_to_host",
    ),
    _event(
        "post_tool",
        "PostToolUse",
        "native_installed_hook",
        "suppressed_continue_with_hook_trace_event_record",
        "append_hook_trace_event",
        "hook_failure_propagates_to_host",
    ),
)

_CODEX_EVENTS = (
    _event(
        "pre_tool",
        "PreToolUse",
        "native_installed_hook",
        "pre_tool_policy_decision",
        "no_trace_event",
        "hook_failure_propagates_to_host",
    ),
    _event(
        "post_tool",
        "PostToolUse",
        "native_installed_hook",
        "hook_trace_event_record",
        "append_hook_trace_event",
        "hook_failure_propagates_to_host",
    ),
)

_OPENCODE_EVENTS = (
    _event(
        "pre_tool",
        "tool.execute.before",
        "native_installed_plugin_hook",
        "pre_tool_policy_decision_for_blocking",
        "no_trace_event",
        "nonzero_or_block_throws_to_host",
    ),
    _event(
        "post_tool",
        "tool.execute.after",
        "native_installed_plugin_hook",
        "no_host_output",
        "append_hook_trace_event",
        "failure_is_logged_and_suppressed",
    ),
)


_HOSTS = MappingProxyType(
    {
        "claude_code": _profile(
            "claude_code",
            (
                "hooks/aitp_v5_claude_hook.py",
                "brain/v5/hook_install_templates.py",
            ),
            _CLAUDE_EVENTS,
            ("prompt_submit", "session_end"),
            {"closeout": "apply_session_closeout"},
        ),
        "kimi_code": _profile(
            "kimi_code",
            (
                "hooks/aitp_v5_kimi_hook.py",
                "brain/v5/hook_kimi_install.py",
            ),
            _KIMI_EVENTS,
            ("prompt_submit", "session_end"),
            {"closeout": "apply_session_closeout"},
        ),
        "codex": _profile(
            "codex",
            (
                "brain/v5/hook_codex_install.py",
                "brain/v5/codex_facade.py",
            ),
            _CODEX_EVENTS,
            ("session_start", "prompt_submit", "session_end"),
            {
                "first_research_prompt": "aitp_v5_codex_enter",
                "closeout": "aitp_v5_codex_closeout",
            },
        ),
        "opencode": _profile(
            "opencode",
            (
                "deploy/templates/opencode/aitp-plugin.js",
                "brain/v5/hook_opencode_install.py",
            ),
            _OPENCODE_EVENTS,
            ("session_start", "prompt_submit", "session_end"),
            {"closeout": "apply_session_closeout"},
            (
                "experimental.chat.system.transform: stale full-skill injection; "
                "not a lifecycle start capability",
            ),
        ),
    }
)

_MATRIX = HostLifecycleCapabilityMatrix(
    schema_version=HOST_LIFECYCLE_CAPABILITY_SCHEMA_VERSION,
    hosts=_HOSTS,
)


def host_lifecycle_capability_matrix() -> HostLifecycleCapabilityMatrix:
    """Return the static matrix without probing, dispatching, or writing host state."""

    return _MATRIX


def host_lifecycle_capability(host: str) -> HostLifecycleCapability:
    """Return one host profile, failing closed for an uncharacterized host."""

    try:
        return _MATRIX.hosts[host]
    except KeyError as exc:
        raise ValueError(f"unsupported host: {host!r}") from exc


__all__ = [
    "HOST_LIFECYCLE_CAPABILITY_SCHEMA_VERSION",
    "HostLifecycleCapability",
    "HostLifecycleCapabilityMatrix",
    "HostLifecycleEventCapability",
    "host_lifecycle_capability",
    "host_lifecycle_capability_matrix",
]
