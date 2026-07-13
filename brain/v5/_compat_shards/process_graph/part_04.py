# Compatibility shard 4 for process_graph.
from __future__ import annotations

def _provenance_payload_hint(
    *,
    entrypoint: str,
    gap_type: str,
    provenance_kind: str,
    reason: str,
    topic_id: str,
    claim_id: str,
    target_type: str,
    target_id: str,
    target_record: dict[str, Any],
) -> dict[str, Any] | None:
    base = {
        "entrypoint": entrypoint,
        "action_kind": "capture_provenance_gap",
        "target_type": target_type,
        "target_id": target_id,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
        **_provenance_lifecycle(
            entrypoint=entrypoint,
            gap_type=gap_type,
            reason=reason,
            claim_id=claim_id,
            target_type=target_type,
            target_id=target_id,
        ),
    }
    if entrypoint == "aitp_v5_record_reference_location":
        return {
            **base,
            "record_action": "record_reference_location",
            "required_fields": ["topic_id", "connector_id", "location_type", "uri", "label"],
            "draft": _clean_mapping(
                {
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "connector_id": _placeholder("connector id"),
                    "location_type": "paper_section",
                    "uri": _placeholder("source URI"),
                    "label": _placeholder("source label"),
                    "source_ref": _source_ref_for_target(target_type, target_id),
                    "status": "located",
                    "summary": reason,
                    "linked_records": _linked_records(target_type, target_id, claim_id),
                }
            ),
        }
    if entrypoint == "aitp_v5_register_source_asset":
        return {
            **base,
            "record_action": "register_source_asset",
            "required_fields": ["topic_id", "asset_type", "uri", "title"],
            "draft": _clean_mapping(
                {
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "asset_type": target_record.get("asset_type") or "paper",
                    "uri": target_record.get("uri") or _placeholder("source URI"),
                    "title": target_record.get("title") or target_record.get("label") or _placeholder("source title"),
                    "label": target_record.get("label") or "",
                    "content_hash": target_record.get("content_hash") or _placeholder("content hash if known"),
                    "hash_algorithm": target_record.get("hash_algorithm") or "sha256",
                    "version_anchor": target_record.get("version_anchor") or {},
                    "source_kind": target_record.get("source_kind") or "literature",
                    "summary": reason,
                    "source_refs": _string_list(target_record.get("source_refs")),
                    "artifact_ids": _string_list(target_record.get("artifact_ids")),
                    "code_state_ids": _string_list(target_record.get("code_state_ids")),
                    "reference_location_ids": _string_list(target_record.get("reference_location_ids")),
                    "linked_records": _linked_records(target_type, target_id, claim_id),
                }
            ),
        }
    if entrypoint == "aitp_v5_capture_source_asset_auto":
        return {
            **base,
            "record_action": "capture_source_asset_auto",
            "required_fields": ["path", "topic_id"],
            "draft": _clean_mapping(
                {
                    "path": _placeholder("local source file path"),
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "asset_type": target_record.get("asset_type") or "",
                    "title": target_record.get("title") or target_record.get("label") or "",
                    "label": target_record.get("label") or "",
                    "version_anchor": target_record.get("version_anchor") or {},
                    "source_kind": target_record.get("source_kind") or "local_file_auto",
                    "summary": reason,
                    "source_refs": _string_list(target_record.get("source_refs")),
                    "artifact_ids": _string_list(target_record.get("artifact_ids")),
                    "code_state_ids": _string_list(target_record.get("code_state_ids")),
                    "reference_location_ids": _string_list(target_record.get("reference_location_ids")),
                    "linked_records": _linked_records(target_type, target_id, claim_id),
                }
            ),
        }
    if entrypoint in {"aitp_v5_capture_code_state_auto", "aitp_v5_record_code_state"}:
        return {
            **base,
            "record_action": "capture_code_state_auto",
            "required_fields": ["worktree_path"],
            "draft": _clean_mapping(
                {
                    "worktree_path": _placeholder("local worktree path"),
                    "repo_id": target_record.get("recipe_id") or target_record.get("tool_name") or _placeholder("repo id"),
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "linked_records": _linked_records(target_type, target_id, claim_id),
                    "known_divergence": reason,
                    "write_patch_artifact": True,
                }
            ),
        }
    if entrypoint == "aitp_v5_record_tool_run":
        return {
            **base,
            "record_action": "record_tool_run",
            "required_fields": ["recipe_id", "tool_family", "tool_name", "topic_id", "claim_id"],
            "draft": _clean_mapping(
                {
                    "recipe_id": target_record.get("recipe_id") or _placeholder("tool recipe id"),
                    "tool_family": target_record.get("tool_family") or _tool_family_for_gap(provenance_kind, gap_type),
                    "tool_name": target_record.get("tool_name") or _placeholder("tool name"),
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "inputs": target_record.get("inputs") or {},
                    "outputs": target_record.get("outputs") or {},
                    "environment": target_record.get("environment") or {},
                    "evidence_status": target_record.get("evidence_status") or "unreviewed",
                    "code_state_ids": _string_list(target_record.get("code_state_ids")),
                    "artifact_ids": _string_list(target_record.get("artifact_ids")),
                    "source_refs": _source_refs_for_record(target_record, target_type, target_id),
                }
            ),
        }
    if entrypoint == "aitp_v5_capture_tool_run_auto":
        return {
            **base,
            "record_action": "capture_tool_run_auto",
            "required_fields": [
                "path",
                "recipe_id",
                "tool_family",
                "tool_name",
                "topic_id",
                "claim_id",
            ],
            "draft": _clean_mapping(
                {
                    "path": _placeholder("local tool transcript or result file path"),
                    "recipe_id": target_record.get("recipe_id") or _placeholder("tool recipe id"),
                    "tool_family": target_record.get("tool_family") or _tool_family_for_gap(provenance_kind, gap_type),
                    "tool_name": target_record.get("tool_name") or _placeholder("tool name"),
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "inputs": target_record.get("inputs") or {},
                    "outputs": target_record.get("outputs") or {},
                    "environment": target_record.get("environment") or {},
                    "evidence_status": target_record.get("evidence_status") or "unreviewed",
                    "code_state_ids": _string_list(target_record.get("code_state_ids")),
                    "artifact_ids": _string_list(target_record.get("artifact_ids")),
                    "source_refs": _source_refs_for_record(target_record, target_type, target_id),
                    "summary": reason,
                }
            ),
        }
    if entrypoint == "aitp_v5_create_validation_contract":
        return {
            **base,
            "record_action": "create_validation_contract",
            "required_fields": ["topic_id", "claim_id", "required_checks", "failure_modes", "required_evidence_outputs"],
            "draft": _clean_mapping(
                {
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "required_checks": _validation_required_checks(gap_type),
                    "failure_modes": _validation_failure_modes(gap_type),
                    "required_evidence_outputs": _validation_required_outputs(target_record, gap_type),
                    "tool_recipe_ids": _string_list(target_record.get("tool_recipe_ids")),
                    "executor_ids": _string_list(target_record.get("executor_ids")),
                    "validator_role": "adversarial_reviewer",
                }
            ),
        }
    if entrypoint == "aitp_v5_record_validation_result":
        return {
            **base,
            "record_action": "record_validation_result",
            "required_fields": ["topic_id", "claim_id", "contract_id", "tool_run_id", "status", "summary"],
            "draft": _clean_mapping(
                {
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "contract_id": target_record.get("contract_id") or _placeholder("validation contract id"),
                    "tool_run_id": target_record.get("tool_run_id") or _placeholder("tool run id"),
                    "status": target_record.get("status") or "partial",
                    "summary": target_record.get("summary") or reason,
                    "checked_outputs": _string_list(target_record.get("checked_outputs")),
                    "covered_failure_modes": _string_list(target_record.get("covered_failure_modes")),
                    "failure_modes_observed": _string_list(target_record.get("failure_modes_observed")),
                    "evidence_refs": _string_list(target_record.get("evidence_refs")),
                    "artifact_ids": _string_list(target_record.get("artifact_ids")),
                }
            ),
        }
    if entrypoint == "aitp_v5_attach_artifact":
        return {
            **base,
            "record_action": "attach_artifact",
            "required_fields": ["topic_id", "claim_id", "artifact_type", "uri", "summary"],
            "draft": _clean_mapping(
                {
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "artifact_type": _artifact_type_for_gap(gap_type),
                    "uri": _placeholder("artifact URI"),
                    "summary": reason,
                    "metadata": {
                        "target_type": target_type,
                        "target_id": target_id,
                        "provenance_kind": provenance_kind,
                    },
                }
            ),
        }
    if entrypoint == "aitp_v5_attach_artifact_auto":
        return {
            **base,
            "record_action": "attach_artifact_auto",
            "required_fields": ["path", "topic_id", "claim_id", "artifact_type", "summary"],
            "draft": _clean_mapping(
                {
                    "path": _placeholder("local artifact file path"),
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "artifact_type": _artifact_type_for_gap(gap_type),
                    "summary": reason,
                    "metadata": {
                        "target_type": target_type,
                        "target_id": target_id,
                        "provenance_kind": provenance_kind,
                    },
                }
            ),
        }
    return None

def _provenance_lifecycle(
    *,
    entrypoint: str,
    gap_type: str,
    reason: str,
    claim_id: str,
    target_type: str,
    target_id: str,
) -> dict[str, Any]:
    return {
        "lifecycle_phases": ["pre_action"],
        "trigger_conditions": [
            reason,
            "before using the target as evidence, validation input, benchmark basis, memory promotion input, or checked conclusion",
        ],
        "recording_threshold": "recommended_before_provenance_dependent_reuse",
        "trust_boundary_inputs": {
            "target_refs": [f"{target_type}:{target_id}"],
            "claim_id": claim_id,
            "entrypoints": [entrypoint],
            "required_before_trust_change": [],
            "requires_preflight": False,
            "final_gate_required": False,
        },
        "recommended_host_behavior": [
            "surface this provenance payload hint as an orientation-only AITP write draft",
            f"call {entrypoint} only after replacing placeholders with real typed provenance",
        ],
    }

def _linked_records(target_type: str, target_id: str, claim_id: str) -> dict[str, str]:
    result = {"target_type": target_type, "target_id": target_id}
    if claim_id:
        result["claim_id"] = claim_id
    return result

def _source_ref_for_target(target_type: str, target_id: str) -> str:
    return f"{target_type}:{target_id}" if target_type and target_id else ""

def _source_refs_for_record(record: dict[str, Any], target_type: str, target_id: str) -> list[str]:
    refs = _string_list(record.get("source_refs"))
    target_ref = _source_ref_for_target(target_type, target_id)
    if target_ref and target_ref not in refs:
        refs.append(target_ref)
    return refs

def _tool_family_for_gap(provenance_kind: str, gap_type: str) -> str:
    if "benchmark" in gap_type:
        return "benchmark"
    if provenance_kind == "code":
        return "code"
    return "research_tool"

def _validation_required_checks(gap_type: str) -> list[str]:
    if "code" in gap_type or "benchmark" in gap_type or "validation_contract" in gap_type:
        return ["reproduce command/run provenance", "check expected outputs", "capture artifact or log"]
    return ["check required outputs", "check source/provenance basis"]

def _validation_failure_modes(gap_type: str) -> list[str]:
    if "code" in gap_type or "benchmark" in gap_type or "validation_contract" in gap_type:
        return ["uncaptured code state", "missing benchmark artifact", "unreviewed tool output"]
    return ["missing evidence output", "unreviewed validation basis"]

def _validation_required_outputs(record: dict[str, Any], gap_type: str) -> list[str]:
    checked = _string_list(record.get("checked_outputs"))
    if checked:
        return checked
    if "benchmark" in gap_type:
        return ["benchmark result artifact", "tool-run transcript"]
    return ["typed evidence output"]

def _artifact_type_for_gap(gap_type: str) -> str:
    if "benchmark" in gap_type:
        return "benchmark_log"
    if "validation" in gap_type:
        return "validation_artifact"
    return "provenance_artifact"

def _placeholder(label: str) -> str:
    return f"<{label}>"

def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]

def _clean_mapping(value: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in value.items():
        if item is None or item == "" or item == [] or item == {}:
            continue
        result[key] = item
    return result

def _linked_code_state_ids_for_claim(records: list[CodeStateRecord], claim_ids: set[str]) -> set[str]:
    result = set()
    for record in records:
        if _mapping_links_any(record.linked_records, claim_ids):
            result.add(record.code_state_id)
    return result

def _mapping_links_any(value: Any, targets: set[str]) -> bool:
    if isinstance(value, dict):
        return any(_mapping_links_any(item, targets) for item in value.values())
    if isinstance(value, list):
        return any(_mapping_links_any(item, targets) for item in value)
    return isinstance(value, str) and value in targets

def _record_payload(record: Any) -> dict[str, Any]:
    if is_dataclass(record):
        return asdict(record)
    return dict(record)

def _node_id(node_type: str, record_id: str) -> str:
    return f"{node_type}:{record_id}"

def _reference_lookup(records: list[ReferenceLocationRecord]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for record in records:
        for value in (
            record.location_id,
            f"reference_location:{record.location_id}",
            f"reference-location:{record.location_id}",
            record.source_ref,
            record.uri,
            record.label,
        ):
            if value:
                lookup[value] = record.location_id
    return lookup

def _source_asset_lookup(records: list[SourceAssetRecord]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for record in records:
        for value in (
            record.asset_id,
            f"source_asset:{record.asset_id}",
            f"source-asset:{record.asset_id}",
            record.uri,
            record.title,
            record.label,
            *record.source_refs,
        ):
            if value:
                lookup[value] = record.asset_id
    return lookup

def _closed(status: str) -> bool:
    return status.strip().lower().replace("-", "_") in _CLOSED_OBLIGATION_STATUSES

def _obligation_slice(record: ProofObligationRecord) -> dict[str, Any]:
    suggested_moments = _suggested_moments_for_obligation(record)
    return {
        "obligation_id": record.obligation_id,
        "topic_id": record.topic_id,
        "claim_id": record.claim_id,
        "status": record.status,
        "obligation_type": record.obligation_type,
        "statement": record.statement,
        "severity": _obligation_severity(record),
        "target_node_id": f"proof_obligation:{record.obligation_id}",
        "suggested_moments": suggested_moments,
        "source_refs": list(record.source_refs),
        "trust_boundary": "before_final_or_promotion" if record.human_gate_required else "before_validation",
        "next_action": record.next_action,
        "required_evidence": list(record.required_evidence),
    }
