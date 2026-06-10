"""Read-only lookup helpers for canonical typed record references."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from brain.v5.models import (
    ArtifactRecord,
    ClaimRecord,
    CodeStateRecord,
    EvidenceRecord,
    ExploratoryRecord,
    HumanCheckpointRecord,
    MemoryEntryRecord,
    PhysicsObjectRecord,
    ProofObligationRecord,
    ReferenceLocationRecord,
    ResearchRouteRecord,
    ResearchRunEventRecord,
    ResearchRunRecord,
    SessionBinding,
    SourceAssetRecord,
    ToolRecipeRecord,
    ToolRunRecord,
    TopicRecord,
    ValidationContractRecord,
    ValidationResultRecord,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.store import read_record


_RecordSpec = tuple[str, str, str, type[Any], str, str, bool]

_RECORD_SPECS: dict[str, _RecordSpec] = {
    "artifact": ("artifacts", "artifact_id", "artifact_record", ArtifactRecord, "typed_record", "registry/artifacts", False),
    "claim": ("claims", "claim_id", "claim_record", ClaimRecord, "typed_record", "registry/claims", False),
    "code_state": ("code_states", "code_state_id", "code_state_record", CodeStateRecord, "typed_record", "registry/code_states", False),
    "evidence": ("evidence", "evidence_id", "evidence_record", EvidenceRecord, "typed_record", "registry/evidence", False),
    "exploratory_record": (
        "exploratory_records",
        "record_id",
        "exploratory_record",
        ExploratoryRecord,
        "typed_record",
        "registry/exploratory_records",
        False,
    ),
    "human_checkpoint": (
        "checkpoints",
        "checkpoint_id",
        "human_checkpoint_record",
        HumanCheckpointRecord,
        "typed_record",
        "registry/checkpoints",
        False,
    ),
    "memory_entry": (
        "memory_entries",
        "entry_id",
        "memory_entry_record",
        MemoryEntryRecord,
        "typed_record",
        "memory/l2/entries",
        False,
    ),
    "physics_object": (
        "physics_objects",
        "object_id",
        "physics_object_record",
        PhysicsObjectRecord,
        "typed_record",
        "registry/physics_objects",
        False,
    ),
    "proof_obligation": (
        "proof_obligations",
        "obligation_id",
        "proof_obligation_record",
        ProofObligationRecord,
        "typed_record",
        "registry/proof_obligations",
        False,
    ),
    "reference_location": (
        "reference_locations",
        "location_id",
        "reference_location_record",
        ReferenceLocationRecord,
        "orientation_only_record",
        "registry/reference_locations",
        False,
    ),
    "research_route": (
        "routes",
        "route_id",
        "research_route_record",
        ResearchRouteRecord,
        "orientation_only_record",
        "registry/routes",
        False,
    ),
    "research_run": (
        "research_runs",
        "run_id",
        "research_run_record",
        ResearchRunRecord,
        "process_record",
        "registry/research_runs",
        False,
    ),
    "research_run_event": (
        "research_run_events",
        "event_id",
        "research_run_event_record",
        ResearchRunEventRecord,
        "process_event_record",
        "registry/research_run_events",
        False,
    ),
    "session": (
        "",
        "session_id",
        "session_binding",
        SessionBinding,
        "runtime_binding",
        "runtime/sessions",
        True,
    ),
    "source_asset": (
        "source_assets",
        "asset_id",
        "source_asset_record",
        SourceAssetRecord,
        "orientation_only_record",
        "registry/source_assets",
        False,
    ),
    "tool_recipe": (
        "tool_recipes",
        "recipe_id",
        "tool_recipe_record",
        ToolRecipeRecord,
        "typed_record",
        "registry/tool_recipes",
        False,
    ),
    "tool_run": ("tool_runs", "run_id", "tool_run_record", ToolRunRecord, "typed_record", "registry/tool_runs", False),
    "topic": ("", "topic_id", "topic_record", TopicRecord, "typed_record", "topics/<topic_id>/topic.md", True),
    "validation_contract": (
        "validation_contracts",
        "contract_id",
        "validation_contract_record",
        ValidationContractRecord,
        "typed_record",
        "registry/validation_contracts",
        False,
    ),
    "validation_result": (
        "validation_results",
        "result_id",
        "validation_result_record",
        ValidationResultRecord,
        "typed_record",
        "registry/validation_results",
        False,
    ),
}

_ALIASES = {
    "aitp": "",
    "asset": "source_asset",
    "source-asset": "source_asset",
    "source_asset_record": "source_asset",
    "reference-location": "reference_location",
    "reference_location_record": "reference_location",
    "ref_location": "reference_location",
    "evidence_record": "evidence",
    "artifact_record": "artifact",
    "tool-run": "tool_run",
    "tool_run_record": "tool_run",
    "validation-contract": "validation_contract",
    "validation_contract_record": "validation_contract",
    "validation-result": "validation_result",
    "validation_result_record": "validation_result",
    "code-state": "code_state",
    "code_state_record": "code_state",
    "route": "research_route",
    "research-route": "research_route",
    "research_route_record": "research_route",
    "research-run": "research_run",
    "research_run_record": "research_run",
    "research-event": "research_run_event",
    "research-run-event": "research_run_event",
    "research_run_event_record": "research_run_event",
    "checkpoint": "human_checkpoint",
    "human_checkpoint_record": "human_checkpoint",
    "proof-obligation": "proof_obligation",
    "proof_obligation_record": "proof_obligation",
    "object": "physics_object",
    "physics-object": "physics_object",
    "physics_object_record": "physics_object",
    "memory": "memory_entry",
    "memory-entry": "memory_entry",
    "memory_entry_record": "memory_entry",
    "claim_record": "claim",
    "topic_record": "topic",
}

_MISSING_REF_SUGGESTIONS: dict[str, tuple[str, str, str, str]] = {
    "reference_location": (
        "recordReferenceLocation",
        "record_reference_location",
        "reference_location_record",
        "record a normal AITP reference location before using this ref as source context",
    ),
    "source_asset": (
        "registerSourceAsset",
        "register_source_asset",
        "source_asset_record",
        "register or auto-capture a normal AITP source asset before using this ref as source context",
    ),
}


def lookup_record_refs(ws: WorkspacePaths, refs: list[str]) -> dict[str, Any]:
    """Return read-only typed-store existence checks for canonical record refs."""

    clean_refs = [str(ref).strip() for ref in refs if str(ref).strip()]
    results = [_lookup_record_ref(ws, ref) for ref in clean_refs]
    found_count = sum(1 for item in results if item["status"] == "found")
    return {
        "kind": "record_ref_lookup",
        "lookup_scope": "typed_record_existence_only",
        "lookup_count": len(results),
        "found_count": found_count,
        "missing_count": sum(1 for item in results if item["status"] == "not_found"),
        "unsupported_count": sum(1 for item in results if item["status"] == "unsupported_kind"),
        "malformed_count": sum(1 for item in results if item["status"] == "malformed_ref"),
        "refs": results,
        "supported_ref_kinds": sorted(_RECORD_SPECS),
        "read_surface_effect": "record_existence_check_only",
        "records_validation_result": False,
        "source_support_result": False,
        "evidence_created": False,
        "validation_created": False,
        "claim_trust_mutation": "none",
        "can_update_claim_trust": False,
        "summary_inputs_trusted": False,
        "orientation_only": True,
    }


def _lookup_record_ref(ws: WorkspacePaths, ref: str) -> dict[str, Any]:
    parsed = _parse_ref(ref)
    if parsed is None:
        return _base_result(ref, status="malformed_ref", diagnostic="expected '<kind>:<record_id>' or 'aitp:<kind>:<record_id>'")

    ref_kind, record_id = parsed
    spec = _RECORD_SPECS.get(ref_kind)
    if spec is None:
        result = _base_result(ref, ref_kind=ref_kind, record_id=record_id, status="unsupported_kind")
        result["diagnostic"] = "ref kind is not supported by this read-only lookup surface"
        return result

    family, id_field, surface, cls, record_role, store_scope, _custom_path = spec
    path = _record_path(ws, ref_kind, family, record_id)
    result = _base_result(
        ref,
        ref_kind=ref_kind,
        record_id=record_id,
        status="not_found",
        id_field=id_field,
        surface=surface,
        record_role=record_role,
        store_scope=store_scope,
    )
    if not path.exists():
        _add_missing_ref_suggestion(result, ref_kind)
        return result

    try:
        record = read_record(path, cls)
    except (TypeError, ValueError):
        result["diagnostic"] = "record file exists but does not satisfy its typed record shape"
        return result

    actual_id = getattr(record, id_field, "")
    if actual_id != record_id:
        result["diagnostic"] = "record file exists but record id field does not match requested ref"
        return result

    record_payload = asdict(record) if is_dataclass(record) else dict(record)
    result.update(
        {
            "status": "found",
            "record_confirmed": True,
            "topic_id": str(record_payload.get("topic_id") or ""),
            "claim_id": str(record_payload.get("claim_id") or ""),
            "record_kind": str(record_payload.get("kind") or ""),
            "orientation_only_record": bool(record_payload.get("orientation_only", False)),
            "can_update_record_claim_trust": False,
            "diagnostic": "record exists in typed store",
        }
    )
    return result


def _add_missing_ref_suggestion(result: dict[str, Any], ref_kind: str) -> None:
    suggestion = _MISSING_REF_SUGGESTIONS.get(ref_kind)
    if suggestion is None:
        return
    operation, entrypoint, surface, reason = suggestion
    result.update(
        {
            "suggested_next_operation": operation,
            "suggested_next_entrypoint": entrypoint,
            "suggested_next_surface": surface,
            "suggested_next_reason": reason,
        }
    )


def _parse_ref(ref: str) -> tuple[str, str] | None:
    parts = [part.strip() for part in ref.split(":")]
    if len(parts) == 3 and parts[0] == "aitp":
        _, raw_kind, record_id = parts
    elif len(parts) == 2:
        raw_kind, record_id = parts
    else:
        return None
    if not raw_kind or not record_id:
        return None
    kind = _ALIASES.get(raw_kind, raw_kind).replace("-", "_")
    return kind, record_id


def _record_path(ws: WorkspacePaths, ref_kind: str, family: str, record_id: str) -> Path:
    if ref_kind == "session":
        return ws.session_path(record_id)
    if ref_kind == "topic":
        return ws.topic_dir(record_id) / "topic.md"
    if ref_kind == "memory_entry":
        return ws.root / "memory" / "l2" / "entries" / f"{record_id}.md"
    return ws.registry_dir(family) / f"{record_id}.md"


def _base_result(
    ref: str,
    *,
    status: str,
    ref_kind: str = "",
    record_id: str = "",
    id_field: str = "",
    surface: str = "",
    record_role: str = "",
    store_scope: str = "",
    diagnostic: str = "",
) -> dict[str, Any]:
    return {
        "ref": ref,
        "ref_kind": ref_kind,
        "record_id": record_id,
        "id_field": id_field,
        "surface": surface,
        "record_role": record_role,
        "store_scope": store_scope,
        "status": status,
        "record_confirmed": False,
        "topic_id": "",
        "claim_id": "",
        "record_kind": "",
        "orientation_only_record": False,
        "can_update_record_claim_trust": False,
        "read_surface_effect": "record_existence_check_only",
        "records_validation_result": False,
        "source_support_result": False,
        "claim_trust_mutation": "none",
        "can_update_claim_trust": False,
        "suggested_next_operation": "",
        "suggested_next_entrypoint": "",
        "suggested_next_surface": "",
        "suggested_next_reason": "",
        "diagnostic": diagnostic,
    }
