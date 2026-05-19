"""Shared validation entrypoints for public AITP v5 surfaces."""

from __future__ import annotations

from typing import Any, Callable

_PUBLIC_SURFACE_NAMES = (
    "adapter_packet",
    "adapter_protocol_registry",
    "code_state_record",
    "evidence_record",
    "execution_brief",
    "session_summary_bundle",
    "summary_orientation",
    "tool_recipe_record",
    "tool_run_record",
    "trust_update_apply",
    "trust_update_preflight",
)
_PUBLIC_SURFACE_VALIDATOR_REF = "brain.v5.public_surfaces.require_valid_public_surface"
_PUBLIC_SURFACE_PURPOSES = {
    "adapter_packet": "runtime adapter packet carrying brief, summary orientation, and trust protocol metadata",
    "adapter_protocol_registry": "auditable registry metadata for adapter protocol fields and validator surfaces",
    "code_state_record": "contracted code-state provenance record for code-dependent physics results",
    "evidence_record": "contracted evidence write result linked to a claim and required outputs",
    "execution_brief": "typed kernel brief for current focus, risk, evidence coverage, and next actions",
    "session_summary_bundle": "orientation-only summary files regenerated from typed kernel records",
    "summary_orientation": "read-only summary view with explicit truth-source protections",
    "tool_recipe_record": "contracted reusable tool recipe record with inputs, outputs, and invariants",
    "tool_run_record": "contracted tool-run provenance record linked to claims, code states, and artifacts",
    "trust_update_apply": "contracted result of a trust-changing mutation after preflight",
    "trust_update_preflight": "contracted preflight gate for trust-changing actions",
}


def public_surface_names() -> tuple[str, ...]:
    """Return the names of public payload surfaces with contract gates."""

    return _PUBLIC_SURFACE_NAMES


def public_surface_validator_ref() -> str:
    """Return the stable import path for validating public payload surfaces."""

    return _PUBLIC_SURFACE_VALIDATOR_REF


def describe_public_surfaces() -> dict[str, Any]:
    """Return an auditable description of public surface contract coverage."""

    return {
        "kind": "public_surface_contracts",
        "validator": public_surface_validator_ref(),
        "surface_names": list(public_surface_names()),
        "surfaces": [
            {
                "name": name,
                "validator": public_surface_validator_ref(),
                "purpose": _PUBLIC_SURFACE_PURPOSES[name],
            }
            for name in public_surface_names()
        ],
        "truth_source": "contract_registry",
        "summary_inputs_trusted": False,
    }


def require_valid_public_surface(surface_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Validate a public payload by stable surface name."""

    validator = _validators().get(surface_name)
    if validator is None:
        raise ValueError(f"unknown public surface: {surface_name}")
    return validator(payload)


def _validators() -> dict[str, Callable[[dict[str, Any]], dict[str, Any]]]:
    from brain.v5.contracts import (
        require_valid_adapter_packet,
        require_valid_adapter_protocol_registry,
        require_valid_code_state_record,
        require_valid_evidence_record,
        require_valid_execution_brief,
        require_valid_session_summary_bundle,
        require_valid_summary_orientation,
        require_valid_tool_recipe_record,
        require_valid_tool_run_record,
        require_valid_trust_update_apply,
        require_valid_trust_update_preflight,
    )

    return {
        "adapter_packet": require_valid_adapter_packet,
        "adapter_protocol_registry": require_valid_adapter_protocol_registry,
        "code_state_record": require_valid_code_state_record,
        "evidence_record": require_valid_evidence_record,
        "execution_brief": require_valid_execution_brief,
        "session_summary_bundle": require_valid_session_summary_bundle,
        "summary_orientation": require_valid_summary_orientation,
        "tool_recipe_record": require_valid_tool_recipe_record,
        "tool_run_record": require_valid_tool_run_record,
        "trust_update_apply": require_valid_trust_update_apply,
        "trust_update_preflight": require_valid_trust_update_preflight,
    }
