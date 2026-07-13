"""Canonical cross-surface registry for AITP v5 runtime capabilities."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from brain.v5.capability_registry_data import (
    BRIDGE_TARGET_SPECS,
    COMPACT_MCP_NAMES,
    COMPACT_SOFT_DEPRECATION_BY_MCP,
    KERNEL_WRITE_OPERATIONS,
    MCP_ONLY_CAPABILITIES,
    OPTIONAL_MCP_CAPABILITIES,
    READ_ONLY_OPERATIONS,
    RUNTIME_WRITE_OPERATIONS,
)
from brain.v5.runtime_entrypoint_catalog import RUNTIME_ENTRYPOINTS


STATE_EFFECTS = frozenset({"read_only", "runtime_write", "kernel_write"})
COMPACT_VISIBILITIES = frozenset({"compact", "full", "hidden"})
CAPABILITY_LIFECYCLE_STATUSES = frozenset({"active", "soft_deprecated_from_compact"})


class CapabilityRegistryError(RuntimeError):
    """Raised when static capability declarations are incomplete or ambiguous."""


@dataclass(frozen=True)
class CapabilitySpec:
    operation: str
    mcp_name: str
    cli_route: str | None
    public_surface: str
    state_effect: str
    compact_visibility: str
    bridge_target: str | None = None
    lifecycle_status: str = "active"
    compatibility_window: str = ""
    compatibility_warning: str = ""
    removal_condition: str = ""


def capability_specs() -> dict[str, CapabilitySpec]:
    """Return every full and compact MCP capability with explicit effects."""

    state_effects = _catalog_state_effects()
    bridge_targets = {
        entrypoint_key: host_operation
        for host_operation, entrypoint_key, _role, _effect in BRIDGE_TARGET_SPECS
    }
    specs = {
        operation: CapabilitySpec(
            operation=operation,
            mcp_name=str(entrypoint["mcp"]),
            cli_route=str(entrypoint["cli"]),
            public_surface=str(entrypoint["surface"]),
            state_effect=state_effects[operation],
            compact_visibility=(
                "compact" if entrypoint["mcp"] in COMPACT_MCP_NAMES else "full"
            ),
            bridge_target=bridge_targets.get(operation),
            **_compatibility_metadata(str(entrypoint["mcp"])),
        )
        for operation, entrypoint in RUNTIME_ENTRYPOINTS.items()
    }
    for row in (*MCP_ONLY_CAPABILITIES, *_available_optional_capabilities()):
        operation, mcp_name, cli_route, surface, state_effect, visibility = row
        if operation in specs:
            raise CapabilityRegistryError(f"duplicate capability operation: {operation}")
        specs[operation] = CapabilitySpec(
            operation=operation,
            mcp_name=mcp_name,
            cli_route=cli_route,
            public_surface=surface,
            state_effect=state_effect,
            compact_visibility=visibility,
            **_compatibility_metadata(mcp_name),
        )
    return dict(sorted(specs.items()))


def compact_mcp_tools() -> tuple[str, ...]:
    """Return compact MCP names from the same registry used for full parity."""

    return tuple(
        spec.mcp_name
        for spec in capability_specs().values()
        if spec.compact_visibility == "compact"
    )


def capability_registry_payload() -> dict[str, Any]:
    """Return a stable JSON representation without importing live MCP modules."""

    specs = capability_specs()
    return {
        "kind": "capability_registry",
        "schema_version": "aitp.capability_registry.v1",
        "capability_count": len(specs),
        "capabilities": [asdict(spec) for spec in specs.values()],
        "state_effects": sorted(STATE_EFFECTS),
        "compact_visibilities": sorted(COMPACT_VISIBILITIES),
        "capability_lifecycle_statuses": sorted(CAPABILITY_LIFECYCLE_STATUSES),
        "truth_source": "capability_registry",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def audit_capability_registry(
    *,
    specs: Mapping[str, CapabilitySpec] | None = None,
) -> dict[str, Any]:
    """Audit catalog, MCP, public-surface, compact, and bridge parity."""

    from brain.v5 import mcp_tools
    from brain.v5.codex_facade import CODEX_SURFACE_TOOL_ALLOWLIST
    from brain.v5.public_surfaces import public_surface_names
    from brain.v5.runtime_bridge_targets import runtime_bridge_target_manifest
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    registered = dict(capability_specs() if specs is None else specs)
    entrypoints = runtime_entrypoints()
    public = set(public_surface_names())
    wrapped = {
        name
        for name, value in vars(mcp_tools).items()
        if name.startswith("aitp_v5_") and callable(value)
    }
    compact = {
        spec.mcp_name
        for spec in registered.values()
        if spec.compact_visibility == "compact"
    }
    manifest = runtime_bridge_target_manifest()
    targets = {target["entrypoint_key"]: target for target in manifest["targets"]}
    issues: list[str] = []

    _audit_specs(registered, issues)
    _audit_catalog(registered, entrypoints, issues)
    _audit_names("MCP wrapper", {spec.mcp_name for spec in registered.values()}, wrapped, issues)
    _audit_names("compact allowlist", compact, set(CODEX_SURFACE_TOOL_ALLOWLIST), issues)
    for operation, spec in registered.items():
        if spec.public_surface not in public:
            issues.append(
                f"{operation}.public_surface: unknown public surface {spec.public_surface!r}"
            )
    for operation, target in targets.items():
        spec = registered.get(operation)
        if spec is None:
            issues.append(f"{operation}: bridge target has no capability spec")
            continue
        if spec.bridge_target != target["operation"]:
            issues.append(
                f"{operation}.bridge_target: {spec.bridge_target!r} != {target['operation']!r}"
            )
        normalized = normalize_bridge_state_effect(target["state_effect"])
        if spec.state_effect != normalized:
            issues.append(
                f"{operation}.state_effect: {spec.state_effect!r} conflicts with bridge {normalized!r}"
            )
    for operation, spec in registered.items():
        if spec.bridge_target and operation not in targets:
            issues.append(f"{operation}.bridge_target: target is not in bridge manifest")

    effect_counts = Counter(spec.state_effect for spec in registered.values())
    visibility_counts = Counter(spec.compact_visibility for spec in registered.values())
    return {
        "ok": not issues,
        "kind": "capability_registry_audit",
        "schema_version": "aitp.capability_registry_audit.v1",
        "capability_count": len(registered),
        "catalog_count": len(entrypoints),
        "mcp_wrapper_count": len(wrapped),
        "public_surface_count": len(public),
        "compact_count": len(compact),
        "bridge_target_count": len(targets),
        "state_effect_counts": dict(sorted(effect_counts.items())),
        "visibility_counts": dict(sorted(visibility_counts.items())),
        "mcp_only_operations": sorted(set(registered) - set(entrypoints)),
        "issues": issues,
        "truth_source": "live_cross_surface_registry_audit",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def normalize_bridge_state_effect(value: str) -> str:
    """Normalize compatibility bridge effects to the registry's three classes."""

    mapping = {
        "read_only": "read_only",
        "preflight_only": "read_only",
        "project_skill_shim_write": "runtime_write",
        "curated_rag_manifest_write": "runtime_write",
        "typed_record_write": "kernel_write",
    }
    try:
        return mapping[value]
    except KeyError as exc:
        raise CapabilityRegistryError(f"unknown bridge state effect: {value!r}") from exc


def _catalog_state_effects() -> dict[str, str]:
    groups = {
        "read_only": READ_ONLY_OPERATIONS,
        "runtime_write": RUNTIME_WRITE_OPERATIONS,
        "kernel_write": KERNEL_WRITE_OPERATIONS,
    }
    seen: set[str] = set()
    effects: dict[str, str] = {}
    for effect, operations in groups.items():
        overlap = seen.intersection(operations)
        if overlap:
            raise CapabilityRegistryError(
                f"operations have conflicting state effects: {sorted(overlap)}"
            )
        seen.update(operations)
        effects.update({operation: effect for operation in operations})
    catalog = set(RUNTIME_ENTRYPOINTS)
    if seen != catalog:
        raise CapabilityRegistryError(
            "catalog state classification drift: "
            f"missing={sorted(catalog - seen)}, unknown={sorted(seen - catalog)}"
        )
    return effects


def _available_optional_capabilities() -> tuple[tuple[Any, ...], ...]:
    from brain.v5 import mcp_tools

    return tuple(
        row
        for row in OPTIONAL_MCP_CAPABILITIES
        if callable(getattr(mcp_tools, row[1], None))
    )


def _audit_specs(specs: Mapping[str, CapabilitySpec], issues: list[str]) -> None:
    mcp_counts = Counter(spec.mcp_name for spec in specs.values())
    for operation, spec in specs.items():
        if operation != spec.operation:
            issues.append(f"{operation}.operation: key and declared operation differ")
        if spec.state_effect not in STATE_EFFECTS:
            issues.append(f"{operation}.state_effect: invalid {spec.state_effect!r}")
        if spec.compact_visibility not in COMPACT_VISIBILITIES:
            issues.append(
                f"{operation}.compact_visibility: invalid {spec.compact_visibility!r}"
            )
        if spec.lifecycle_status not in CAPABILITY_LIFECYCLE_STATUSES:
            issues.append(
                f"{operation}.lifecycle_status: invalid {spec.lifecycle_status!r}"
            )
        if spec.lifecycle_status == "soft_deprecated_from_compact":
            if spec.compact_visibility != "full":
                issues.append(
                    f"{operation}.compact_visibility: soft-deprecated compact route must be full"
                )
            if not spec.compatibility_window:
                issues.append(f"{operation}.compatibility_window: must be non-empty")
            if not spec.compatibility_warning:
                issues.append(f"{operation}.compatibility_warning: must be non-empty")
            if not spec.removal_condition:
                issues.append(f"{operation}.removal_condition: must be non-empty")
        if not spec.mcp_name:
            issues.append(f"{operation}.mcp_name: must be non-empty")
        if not spec.public_surface:
            issues.append(f"{operation}.public_surface: must be non-empty")
        if spec.cli_route is not None and not spec.cli_route.startswith("aitp-v5 "):
            issues.append(f"{operation}.cli_route: must be an aitp-v5 command or null")
    for name, count in mcp_counts.items():
        if count != 1:
            issues.append(f"mcp_name {name!r}: declared by {count} capabilities")


def _audit_catalog(
    specs: Mapping[str, CapabilitySpec],
    entrypoints: Mapping[str, Mapping[str, Any]],
    issues: list[str],
) -> None:
    for operation, entrypoint in entrypoints.items():
        spec = specs.get(operation)
        if spec is None:
            issues.append(f"{operation}: runtime catalog operation is unregistered")
            continue
        expected = (entrypoint.get("mcp"), entrypoint.get("cli"), entrypoint.get("surface"))
        actual = (spec.mcp_name, spec.cli_route, spec.public_surface)
        if actual != expected:
            issues.append(f"{operation}: registry/catalog route mismatch")


def _compatibility_metadata(mcp_name: str) -> dict[str, str]:
    row = COMPACT_SOFT_DEPRECATION_BY_MCP.get(mcp_name)
    if row is None:
        return {}
    return {
        "lifecycle_status": row["lifecycle_status"],
        "compatibility_window": row["compatibility_window"],
        "compatibility_warning": row["warning"],
        "removal_condition": row["removal_condition"],
    }


def _audit_names(label: str, registered: set[str], live: set[str], issues: list[str]) -> None:
    for name in sorted(registered - live):
        issues.append(f"{label}: registered but unavailable: {name}")
    for name in sorted(live - registered):
        issues.append(f"{label}: available but unregistered: {name}")
