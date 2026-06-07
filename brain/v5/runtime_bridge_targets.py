"""Host-facing runtime bridge target manifest for AITP v5 entrypoints."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from brain.v5.runtime_entrypoints import runtime_entrypoints


_BRIDGE_TARGET_SPECS: tuple[tuple[str, str, str, str], ...] = (
    ("readProcessGraphSlice", "process_graph_slice", "read", "read_only"),
    ("readMomentPolicy", "host_agnostic_moment_policy", "read", "read_only"),
    ("recordExploratoryRecord", "record_exploratory_record", "write", "typed_record_write"),
    ("registerSourceAsset", "register_source_asset", "write", "typed_record_write"),
    ("captureSourceAssetAuto", "capture_source_asset_auto", "write", "typed_record_write"),
    ("recordEvidence", "record_evidence", "write", "typed_record_write"),
    ("recordToolRun", "record_tool_run", "write", "typed_record_write"),
    ("captureToolRunAuto", "capture_tool_run_auto", "write", "typed_record_write"),
    ("captureCodeStateAuto", "capture_code_state_auto", "write", "typed_record_write"),
    ("attachArtifact", "attach_artifact", "write", "typed_record_write"),
    ("attachArtifactAuto", "attach_artifact_auto", "write", "typed_record_write"),
    ("recordReferenceLocation", "record_reference_location", "write", "typed_record_write"),
    ("createProofObligation", "create_proof_obligation", "write", "typed_record_write"),
    ("createValidationContract", "create_validation_contract", "write", "typed_record_write"),
    ("recordValidationResult", "record_validation_result", "write", "typed_record_write"),
    (
        "recordSourceReconstructionReviewResult",
        "record_source_reconstruction_review_result",
        "write",
        "typed_record_write",
    ),
    ("requestHumanCheckpoint", "request_human_checkpoint", "write", "typed_record_write"),
    ("preflightTrustUpdate", "trust_preflight", "preflight", "preflight_only"),
)


def runtime_bridge_target_manifest() -> dict[str, Any]:
    """Return MCP-first host bridge targets derived from runtime_entrypoints()."""

    entrypoints = runtime_entrypoints()
    targets = [
        _target_payload(
            operation=operation,
            entrypoint_key=entrypoint_key,
            execution_role=execution_role,
            state_effect=state_effect,
            entrypoint=entrypoints[entrypoint_key],
        )
        for operation, entrypoint_key, execution_role, state_effect in _BRIDGE_TARGET_SPECS
    ]
    return {
        "kind": "runtime_bridge_target_manifest",
        "target_count": len(targets),
        "targets": targets,
        "target_groups": {
            "read": [target["operation"] for target in targets if target["execution_role"] == "read"],
            "write": [target["operation"] for target in targets if target["execution_role"] == "write"],
            "preflight": [
                target["operation"] for target in targets if target["execution_role"] == "preflight"
            ],
        },
        "excluded_entrypoints": {
            "trust_apply": "claim trust mutation remains AITP-owned and is not exposed as a host write bridge target",
        },
        "preferred_transport": "mcp",
        "fallback_transport": "cli",
        "canonical_store": ".aitp",
        "truth_source": "runtime_entrypoint_catalog",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_claim_trust": False,
    }


def runtime_bridge_target_by_operation(operation: str) -> dict[str, Any] | None:
    """Return one bridge target by host operation name."""

    for target in runtime_bridge_target_manifest()["targets"]:
        if target["operation"] == operation:
            return deepcopy(target)
    return None


def _target_payload(
    *,
    operation: str,
    entrypoint_key: str,
    execution_role: str,
    state_effect: str,
    entrypoint: dict[str, Any],
) -> dict[str, Any]:
    return {
        "operation": operation,
        "entrypoint_key": entrypoint_key,
        "mcp_tool": entrypoint["mcp"],
        "cli_fallback": entrypoint["cli"],
        "surface": entrypoint["surface"],
        "preferred_transport": "mcp",
        "fallback_transport": "cli",
        "execution_role": execution_role,
        "state_effect": state_effect,
        "canonical_store": ".aitp",
        "claim_trust_mutation": "none",
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }
