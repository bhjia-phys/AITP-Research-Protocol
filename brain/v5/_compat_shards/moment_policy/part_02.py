# Compatibility shard 2 for moment_policy.
from __future__ import annotations

def _trigger_conditions(
    *,
    decision_type: str,
    action_kind: str,
    required_now: bool,
    reason: str,
    required_before_trust_change: list[str],
) -> list[str]:
    conditions = [reason]
    if required_now:
        conditions.append("at pre_turn because required_now is true")
    else:
        conditions.append("when the host action depends on this target")
    if decision_type == "recording":
        conditions.extend(
            [
                "when an open obligation needs typed evidence or validation",
                "before final synthesis, promotion, or trust update that relies on the target claim",
            ]
        )
    if decision_type == "backtrace":
        conditions.extend(
            [
                "when source backtrace reports missing or open reconstruction components",
                "before using the target claim or source chain as support",
            ]
        )
    if decision_type == "brainstorming":
        conditions.extend(
            [
                "when a relation or exploratory path is still hypothetical or open",
                "before using the brainstormed path as claim support or validation basis",
            ]
        )
        if "original" in action_kind:
            conditions.append("before final synthesis if the local question may have drifted")
    if decision_type == "trust_boundary":
        conditions.extend(
            [
                "before any claim-trust update",
                "before trust-sensitive final output for the target claim",
            ]
        )
    if decision_type == "route":
        conditions.extend(
            [
                "when choosing, abandoning, or pivoting a nonlinear research route",
                "before route-dependent work loses the route-choice rationale",
            ]
        )
        if "checkpoint" in action_kind:
            conditions.append("before switching route when a pivot checkpoint is recorded or needed")
    if required_before_trust_change:
        conditions.append("before claim-trust changes until required_before_trust_change is satisfied")
    return _dedupe_strings(conditions)

def _recording_threshold(*, decision_type: str, required_now: bool, action_kind: str) -> str:
    if decision_type == "trust_boundary":
        return "blocking_before_claim_trust_update"
    if decision_type == "recording" and required_now:
        return "blocking_before_final_or_promotion"
    if decision_type == "backtrace" and required_now:
        return "required_before_source_dependent_support"
    if decision_type == "backtrace":
        return "recommended_before_following_source_chain"
    if decision_type == "route" and "checkpoint" in action_kind:
        return "recommended_before_route_switch"
    if decision_type == "route" and "failed" in action_kind:
        return "recommended_before_retry_or_pivot"
    if decision_type == "route":
        return "recommended_before_route_dependent_work"
    if decision_type == "brainstorming" and "original" in action_kind:
        return "recommended_before_next_local_step_or_final_synthesis"
    if decision_type == "brainstorming":
        return "recommended_before_using_hypothesis_or_exploration"
    return "recommended_when_target_becomes_action_relevant"

def _recommended_host_behavior(
    *,
    decision_type: str,
    required_now: bool,
    entrypoints: list[str],
    required_before_trust_change: list[str],
) -> list[str]:
    behavior = [
        "treat this lifecycle policy as orientation-only and verify writes against typed kernel records",
    ]
    if entrypoints:
        behavior.append("surface the declared entrypoints and payload_hints at the listed lifecycle phases")
    if required_now:
        behavior.append("treat the decision as a current-turn obligation unless an explicit blocker is recorded")
    if decision_type == "recording":
        behavior.append("call the record entrypoint before final or promotional use of the target claim")
    if decision_type == "backtrace":
        behavior.append("call the backtrace or source-record entrypoint before source-dependent actions")
    if decision_type == "brainstorming":
        behavior.append("call the brainstorming entrypoint before using the path as evidence or validation input")
    if decision_type == "route":
        behavior.append("record route choice, failed route lesson, or pivot checkpoint as process state, not evidence")
    if decision_type == "trust_boundary":
        behavior.append("at pre_final, require passed calls or explicit blockers before trust-sensitive final output")
    if required_before_trust_change:
        behavior.append("run aitp_v5_preflight_trust_update before any claim-trust mutation")
    return _dedupe_strings(behavior)

def _moment_summary(decision: dict[str, Any]) -> dict[str, Any]:
    summary = {
        "moment": decision["moment"],
        "reason": decision["reason"],
        "target_type": decision["target_type"],
        "target_id": decision["target_id"],
        "decision_type": decision["decision_type"],
        "required_now": decision["required_now"],
        "trust_boundary": decision["trust_boundary"],
    }
    if decision["missing_components"]:
        summary["missing_components"] = list(decision["missing_components"])
    return summary

def _dedupe_decisions(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for item in items:
        key = (item["moment"], item["decision_type"], item["target_type"], item["target_id"])
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result

def _dedupe_strings(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        value = str(item)
        if value and value not in result:
            result.append(value)
    return result

def _payload_hints(
    *,
    action_kind: str,
    target_type: str,
    target_id: str,
    topic_id: str,
    claim_id: str,
    session_id: str,
    target_record: dict[str, Any],
    record_entrypoints: list[str],
    exploration_entrypoints: list[str],
    trust_entrypoints: list[str],
) -> list[dict[str, Any]]:
    hints: list[dict[str, Any]] = []
    for entrypoint in [*record_entrypoints, *exploration_entrypoints, *trust_entrypoints]:
        hint = _payload_hint(
            entrypoint=entrypoint,
            action_kind=action_kind,
            target_type=target_type,
            target_id=target_id,
            topic_id=topic_id,
            claim_id=claim_id,
            session_id=session_id,
            target_record=target_record,
        )
        if hint is not None:
            hints.append(with_draft_schema(hint))
    return hints

def _payload_hint(
    *,
    entrypoint: str,
    action_kind: str,
    target_type: str,
    target_id: str,
    topic_id: str,
    claim_id: str,
    session_id: str,
    target_record: dict[str, Any],
) -> dict[str, Any] | None:
    base = {
        "entrypoint": entrypoint,
        "action_kind": action_kind,
        "target_type": target_type,
        "target_id": target_id,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }
    if entrypoint == "aitp_v5_record_evidence":
        return {
            **base,
            "record_action": "record_evidence",
            "required_fields": ["topic_id", "claim_id", "evidence_type", "status", "summary"],
            "draft": _clean_mapping(
                {
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "evidence_type": _evidence_type_for_target(target_type, action_kind),
                    "status": "supports",
                    "summary": _placeholder("source-grounded evidence summary"),
                    "supports_outputs": _supports_outputs(target_record),
                    "source_refs": _source_refs(target_record),
                }
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
                    "status": "located",
                    "summary": _placeholder("orientation-only source pointer summary"),
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
                    "asset_type": "paper",
                    "uri": _placeholder("source URI"),
                    "title": _placeholder("source title"),
                    "source_kind": "literature",
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
                    "asset_type": "",
                    "title": "",
                    "source_kind": "local_file_auto",
                    "summary": _placeholder("orientation-only local source capture summary"),
                }
            ),
        }
    if entrypoint == "aitp_v5_record_exploratory_record":
        return {
            **base,
            "record_action": "record_exploratory_record",
            "required_fields": ["topic_id", "exploration_type", "title", "focal_question", "summary"],
            "draft": _clean_mapping(
                {
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "session_id": session_id,
                    "exploration_type": _exploration_type_for_action(action_kind),
                    "title": _exploration_title(action_kind),
                    "focal_question": _placeholder("local question to record"),
                    "summary": _placeholder("orientation-only exploration summary"),
                    "original_question": target_record.get("original_question", ""),
                    "local_question": target_record.get("local_question", ""),
                    "object_ids": list(target_record.get("object_ids") or []),
                    "relation_ids": list(target_record.get("relation_ids") or []),
                    "source_refs": _source_refs(target_record),
                    "reasoning_moves": _reasoning_moves(action_kind, target_record),
                    "backtrace_targets": _backtrace_targets(target_record),
                    "relation_path_questions": _relation_path_questions(action_kind, target_record),
                    "definition_boundary_questions": _definition_boundary_questions(action_kind, target_record),
                    "derivation_backtrace_questions": _derivation_backtrace_questions(action_kind, target_record),
                    "source_dependency_questions": _source_dependency_questions(action_kind, target_record),
                    "original_question_guard": _original_question_guard(target_record),
                    "candidate_paths": list(target_record.get("candidate_paths") or []),
                    "unresolved_points": list(target_record.get("unresolved_points") or []),
                    "next_actions": list(target_record.get("next_actions") or []),
                }
            ),
        }
    if entrypoint == "aitp_v5_record_research_route":
        return {
            **base,
            "record_action": "record_research_route",
            "required_fields": ["topic_id", "title", "route_type", "status", "rationale"],
            "draft": _clean_mapping(
                {
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "session_id": session_id,
                    "title": target_record.get("title") or _placeholder("route title"),
                    "route_type": target_record.get("route_type") or "steering_route",
                    "status": target_record.get("status") or "live",
                    "rationale": target_record.get("rationale") or _placeholder("route-choice rationale"),
                    "current_question": target_record.get("current_question", ""),
                    "next_action": target_record.get("next_action", ""),
                    "failure_modes": list(target_record.get("failure_modes") or []),
                    "source_refs": _source_refs(target_record),
                    "evidence_refs": _string_list(target_record.get("evidence_refs")),
                    "artifact_ids": _string_list(target_record.get("artifact_ids")),
                    "parent_route_ids": _string_list(target_record.get("parent_route_ids")),
                    "checkpoint_ids": _string_list(target_record.get("checkpoint_ids")),
                    "exploratory_record_ids": _string_list(target_record.get("exploratory_record_ids")),
                    "object_ids": _string_list(target_record.get("object_ids")),
                    "relation_ids": _string_list(target_record.get("relation_ids")),
                    "decision_rationale": target_record.get("decision_rationale", ""),
                    "pivot_reason": target_record.get("pivot_reason", ""),
                }
            ),
        }
    if entrypoint == "aitp_v5_request_human_checkpoint":
        return {
            **base,
            "record_action": "request_human_checkpoint",
            "required_fields": ["topic_id", "claim_id", "reason", "requested_by"],
            "draft": _clean_mapping(
                {
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "reason": target_record.get("pivot_reason")
                    or target_record.get("decision_rationale")
                    or _placeholder("route switch checkpoint reason"),
                    "requested_by": "route_policy",
                    "options": ["continue_route", "switch_route", "pause_for_review"],
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
                    "contract_id": _placeholder("validation contract id"),
                    "tool_run_id": _placeholder("tool run id"),
                    "status": "partial",
                    "summary": _placeholder("validation result summary"),
                    "checked_outputs": _supports_outputs(target_record),
                }
            ),
        }
    if entrypoint == "aitp_v5_preflight_trust_update":
        return {
            **base,
            "record_action": "preflight_trust_update",
            "required_fields": ["action", "session_id", "topic_id", "claim_id"],
            "draft": _clean_mapping(
                {
                    "action": "change_claim_confidence",
                    "session_id": session_id,
                    "topic_id": topic_id,
                    "claim_id": claim_id or (target_id if target_type == "claim" else ""),
                    "requested_state": _placeholder("requested claim confidence state"),
                    "source_kind": _preflight_source_kind(action_kind, target_type),
                    "source_ref": _source_ref_for_target(target_type, target_id),
                    "evidence_refs": _source_refs(target_record),
                    "code_state_ids": _string_list(target_record.get("code_state_ids")),
                    "rationale": _preflight_rationale(action_kind, target_type, target_id),
                }
            ),
        }
    return None

def _evidence_type_for_target(target_type: str, action_kind: str) -> str:
    if target_type == "proof_obligation":
        return "proof_obligation_resolution"
    if "source" in action_kind or "backtrace" in action_kind:
        return "source_reconstruction"
    return "process_record"

def _preflight_source_kind(action_kind: str, target_type: str) -> str:
    if "source" in action_kind or "backtrace" in action_kind:
        return "source_record"
    if "relation" in action_kind or target_type == "object_relation":
        return "theory_reasoning_record"
    if target_type == "proof_obligation":
        return "proof_obligation_record"
    if target_type == "research_route":
        return "route_record"
    return "typed_record"

def _preflight_rationale(action_kind: str, target_type: str, target_id: str) -> str:
    return (
        f"Run AITP trust preflight before using {target_type}:{target_id} "
        f"for action {action_kind} as a claim-trust change or trust-sensitive final conclusion."
    )

def _exploration_type_for_action(action_kind: str) -> str:
    if "relation_path" in action_kind:
        return "relation_path_brainstorm"
    if "source" in action_kind or "backtrace" in action_kind:
        return "backtrace_step"
    if "original" in action_kind:
        return "question_decomposition"
    return "steering_checkpoint"

def _exploration_title(action_kind: str) -> str:
    if "relation_path" in action_kind:
        return "Record relation-path brainstorm"
    if "source" in action_kind or "backtrace" in action_kind:
        return "Record source backtrace step"
    if "original" in action_kind:
        return "Record original-question drift check"
    return "Record research steering checkpoint"

def _supports_outputs(record: dict[str, Any]) -> list[str]:
    for key in ("required_evidence", "missing_components"):
        values = record.get(key)
        if isinstance(values, list):
            return [str(value) for value in values if str(value)]
    return []

def _source_refs(record: dict[str, Any]) -> list[str]:
    values = record.get("source_refs")
    if isinstance(values, list):
        return [str(value) for value in values if str(value)]
    return []

def _source_ref_for_target(target_type: str, target_id: str) -> str:
    return f"{target_type}:{target_id}" if target_type and target_id else ""

def _reasoning_moves(action_kind: str, record: dict[str, Any]) -> list[str]:
    values = _string_list(record.get("reasoning_moves"))
    if values:
        return values
    if "relation_path" in action_kind:
        return ["why-question decomposition", "relation-path brainstorming"]
    if "source" in action_kind or "backtrace" in action_kind:
        return ["source dependency backtrace", "bidirectional definition backtrace"]
    if "original" in action_kind:
        return ["original-question continuity check"]
    return ["local research steering checkpoint"]

def _backtrace_targets(record: dict[str, Any]) -> list[str]:
    values = _string_list(record.get("backtrace_targets"))
    if values:
        return values
    targets = [
        *[f"object:{value}" for value in _string_list([record.get("subject_id"), record.get("object_id")])],
        *[f"object:{value}" for value in _string_list(record.get("object_ids"))],
        *[f"relation:{value}" for value in _string_list([record.get("relation_id")])],
        *[f"relation:{value}" for value in _string_list(record.get("relation_ids"))],
        *[f"source:{value}" for value in _source_refs(record)],
    ]
    return _dedupe_strings(targets)

def _relation_path_questions(action_kind: str, record: dict[str, Any]) -> list[str]:
    values = _string_list(record.get("relation_path_questions"))
    if values:
        return values
    if "relation_path" not in action_kind:
        return []
    local_question = str(record.get("local_question") or "")
    if local_question:
        return [local_question]
    return ["Which intermediate physical objects or definitions could connect the two sides?"]

def _definition_boundary_questions(action_kind: str, record: dict[str, Any]) -> list[str]:
    values = _string_list(record.get("definition_boundary_questions"))
    if values:
        return values
    if "source" in action_kind or "backtrace" in action_kind or "relation_path" in action_kind:
        return ["Which definitions, assumptions, or convention boundaries must be traced on both sides?"]
    return []
