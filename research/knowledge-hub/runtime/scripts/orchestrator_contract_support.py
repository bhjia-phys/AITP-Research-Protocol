from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Callable


def load_runtime_contract(
    *,
    load_json: Callable[[Path], dict | None],
    knowledge_root: Path,
    topic_slug: str,
) -> dict | None:
    return load_json(knowledge_root / "runtime" / "topics" / topic_slug / "runtime_protocol.generated.json")


def load_operator_checkpoint(
    *,
    load_json: Callable[[Path], dict | None],
    knowledge_root: Path,
    topic_slug: str,
) -> dict | None:
    return load_json(knowledge_root / "runtime" / "topics" / topic_slug / "operator_checkpoint.active.json")


def load_consultation_followup_selection(
    *,
    load_json: Callable[[Path], dict | None],
    knowledge_root: Path,
    topic_slug: str,
) -> dict | None:
    return load_json(
        knowledge_root
        / "runtime"
        / "topics"
        / topic_slug
        / "consultation_followup_selection.active.json"
    )


def load_selected_candidate_route_choice(
    *,
    load_json: Callable[[Path], dict | None],
    knowledge_root: Path,
    topic_slug: str,
) -> dict | None:
    return load_json(
        knowledge_root
        / "runtime"
        / "topics"
        / topic_slug
        / "selected_candidate_route_choice.active.json"
    )


def preferred_action_types_from_runtime_contract(runtime_contract: dict | None) -> list[str]:
    if not runtime_contract:
        return []
    runtime_mode = str(runtime_contract.get("runtime_mode") or "").strip()
    active_submode = str(runtime_contract.get("active_submode") or "").strip()
    transition_posture = runtime_contract.get("transition_posture") or {}
    transition_kind = str(transition_posture.get("transition_kind") or "").strip()
    triggered_by = {
        str(item).strip()
        for item in (transition_posture.get("triggered_by") or [])
        if str(item).strip()
    }
    if transition_kind == "backedge_transition" and "capability_gap_blocker" in triggered_by:
        return ["skill_discovery"]
    if transition_kind == "backedge_transition" and "non_trivial_consultation" in triggered_by:
        return ["consultation_followup"]
    if runtime_mode == "promote" or "promotion_intent" in triggered_by:
        return [
            "l2_promotion_review",
            "request_promotion",
            "approve_promotion",
            "promote_candidate",
            "auto_promote_candidate",
        ]
    if runtime_mode == "verify" or "verification_route_selection" in triggered_by:
        return [
            "select_validation_route",
            "materialize_execution_task",
            "dispatch_execution_task",
            "await_execution_result",
            "ingest_execution_result",
        ]
    if runtime_mode == "explore" and active_submode == "literature":
        return ["literature_intake_stage"]
    return []


def compute_literature_intake_stage_signature(runtime_contract: dict | None) -> str:
    payload = runtime_contract or {}
    active_research_contract = payload.get("active_research_contract") or {}
    signature_payload = {
        "runtime_mode": str(payload.get("runtime_mode") or "").strip(),
        "active_submode": str(payload.get("active_submode") or "").strip(),
        "l1_source_intake": active_research_contract.get("l1_source_intake") or {},
        "graph_analysis_diff": ((payload.get("graph_analysis") or {}).get("diff") or {}),
    }
    encoded = json.dumps(
        signature_payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha1(encoded).hexdigest()


def topic_has_matching_literature_stage(
    *,
    knowledge_root: Path,
    topic_slug: str,
    candidate_signature: str,
) -> bool:
    if not candidate_signature:
        return False
    entries_root = knowledge_root / "canonical" / "staging" / "entries"
    if not entries_root.exists():
        return False
    for path in sorted(entries_root.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if str(payload.get("topic_slug") or "").strip() != topic_slug:
            continue
        provenance = payload.get("provenance") or {}
        if not isinstance(provenance, dict):
            continue
        if str(provenance.get("literature_stage_signature") or "").strip() == candidate_signature:
            return True
    return False


def topic_has_staged_entries(
    *,
    knowledge_root: Path,
    topic_slug: str,
) -> bool:
    entries_root = knowledge_root / "canonical" / "staging" / "entries"
    if not entries_root.exists():
        return False
    for path in sorted(entries_root.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if str(payload.get("topic_slug") or "").strip() == topic_slug:
            return True
    return False


def _parse_iso_timestamp(value: str) -> datetime | None:
    cleaned = str(value or "").strip()
    if not cleaned:
        return None
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return None


def latest_topic_local_staged_entry_updated_at(
    *,
    knowledge_root: Path,
    topic_slug: str,
) -> datetime | None:
    entries_root = knowledge_root / "canonical" / "staging" / "entries"
    if not entries_root.exists():
        return None
    latest: datetime | None = None
    for path in sorted(entries_root.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if str(payload.get("topic_slug") or "").strip() != topic_slug:
            continue
        candidate = _parse_iso_timestamp(str(payload.get("updated_at") or payload.get("created_at") or ""))
        if candidate is None:
            continue
        if latest is None or candidate > latest:
            latest = candidate
    return latest


def latest_continue_decision_updated_at(
    *,
    knowledge_root: Path,
    topic_slug: str,
) -> datetime | None:
    decisions_path = knowledge_root / "runtime" / "topics" / topic_slug / "innovation_decisions.jsonl"
    if not decisions_path.exists():
        return None
    latest: datetime | None = None
    for raw_line in decisions_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if str(payload.get("decision") or "").strip() != "continue":
            continue
        candidate = _parse_iso_timestamp(str(payload.get("updated_at") or ""))
        if candidate is None:
            continue
        if latest is None or candidate > latest:
            latest = candidate
    return latest


def count_continue_decisions_after(
    *,
    knowledge_root: Path,
    topic_slug: str,
    cutoff: datetime | None,
) -> int:
    if cutoff is None:
        return 0
    decisions_path = knowledge_root / "runtime" / "topics" / topic_slug / "innovation_decisions.jsonl"
    if not decisions_path.exists():
        return 0
    count = 0
    for raw_line in decisions_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if str(payload.get("decision") or "").strip() != "continue":
            continue
        candidate = _parse_iso_timestamp(str(payload.get("updated_at") or ""))
        if candidate is None:
            continue
        if candidate > cutoff:
            count += 1
    return count


def consultation_followup_ready_for_auto_run(
    *,
    load_json: Callable[[Path], dict | None],
    knowledge_root: Path,
    topic_slug: str,
) -> bool:
    next_action_decision = load_json(
        knowledge_root / "runtime" / "topics" / topic_slug / "next_action_decision.json"
    )
    if not next_action_decision:
        return False
    selected_action = next_action_decision.get("selected_action") or {}
    if str(selected_action.get("action_type") or "").strip() != "consultation_followup":
        return False
    latest_staged = latest_topic_local_staged_entry_updated_at(
        knowledge_root=knowledge_root,
        topic_slug=topic_slug,
    )
    continue_count = count_continue_decisions_after(
        knowledge_root=knowledge_root,
        topic_slug=topic_slug,
        cutoff=latest_staged,
    )
    return continue_count >= 2


def selected_candidate_route_choice_ready_for_materialization(
    *,
    load_json: Callable[[Path], dict | None],
    knowledge_root: Path,
    topic_slug: str,
) -> bool:
    selection_payload = load_consultation_followup_selection(
        load_json=load_json,
        knowledge_root=knowledge_root,
        topic_slug=topic_slug,
    )
    if not selection_payload or str(selection_payload.get("status") or "").strip() != "selected":
        return False
    next_action_decision = load_json(
        knowledge_root / "runtime" / "topics" / topic_slug / "next_action_decision.json"
    )
    if not next_action_decision:
        return False
    selected_action = next_action_decision.get("selected_action") or {}
    if str(selected_action.get("action_type") or "").strip() != "selected_consultation_candidate_followup":
        return False
    latest_staged = latest_topic_local_staged_entry_updated_at(
        knowledge_root=knowledge_root,
        topic_slug=topic_slug,
    )
    continue_count = count_continue_decisions_after(
        knowledge_root=knowledge_root,
        topic_slug=topic_slug,
        cutoff=latest_staged,
    )
    return continue_count >= 3


def selected_candidate_route_choice_paths(
    *,
    knowledge_root: Path,
    topic_slug: str,
) -> dict[str, Path]:
    runtime_root = knowledge_root / "runtime" / "topics" / topic_slug
    return {
        "json": runtime_root / "selected_candidate_route_choice.active.json",
        "note": runtime_root / "selected_candidate_route_choice.active.md",
    }


def derive_selected_candidate_route_choice(
    *,
    load_json: Callable[[Path], dict | None],
    knowledge_root: Path,
    topic_slug: str,
    updated_by: str,
) -> dict | None:
    selection_payload = load_consultation_followup_selection(
        load_json=load_json,
        knowledge_root=knowledge_root,
        topic_slug=topic_slug,
    )
    if not selection_payload or str(selection_payload.get("status") or "").strip() != "selected":
        return None
    selected_candidate_path = str(selection_payload.get("selected_candidate_path") or "").strip()
    if not selected_candidate_path:
        return None
    candidate_payload = load_json(knowledge_root / selected_candidate_path)
    if not candidate_payload:
        return None
    candidate_id = str(selection_payload.get("selected_candidate_id") or "").strip()
    candidate_unit_type = str(
        candidate_payload.get("candidate_unit_type") or candidate_payload.get("entry_kind") or ""
    ).strip()
    if candidate_unit_type in {"warning_note", "negative_result"}:
        chosen_action_type = "select_validation_route"
        chosen_action_summary = (
            f"Choose the first validation route for selected staged candidate `{candidate_id}` before deeper execution."
        )
        route_choice_reason = (
            "Selected staged warning-side units should first enter explicit validation-route choice."
        )
    else:
        chosen_action_type = "l2_promotion_review"
        chosen_action_summary = (
            f"Review Layer 2 promotion for selected staged candidate `{candidate_id}` before deeper execution."
        )
        route_choice_reason = (
            "Selected staged reusable units should first enter bounded Layer 2 promotion review."
        )
    return {
        "topic_slug": topic_slug,
        "run_id": str(selection_payload.get("run_id") or "").strip() or None,
        "status": "selected",
        "selected_candidate_id": candidate_id,
        "selected_candidate_path": selected_candidate_path,
        "selected_candidate_title": str(selection_payload.get("selected_candidate_title") or "").strip(),
        "selected_candidate_unit_type": candidate_unit_type,
        "chosen_action_type": chosen_action_type,
        "chosen_action_summary": chosen_action_summary,
        "route_choice_reason": route_choice_reason,
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "updated_by": updated_by,
    }


def render_selected_candidate_route_choice_markdown(payload: dict[str, Any]) -> str:
    return (
        "# Selected Candidate Route Choice\n\n"
        f"- Status: `{payload.get('status') or 'missing'}`\n"
        f"- Selected candidate: `{payload.get('selected_candidate_id') or '(missing)'}`\n"
        f"- Candidate unit type: `{payload.get('selected_candidate_unit_type') or '(missing)'}`\n"
        f"- Chosen action type: `{payload.get('chosen_action_type') or '(missing)'}`\n"
        f"- Chosen action summary: {payload.get('chosen_action_summary') or '(missing)'}\n"
        f"- Route choice reason: {payload.get('route_choice_reason') or '(missing)'}\n"
    )


def load_selected_candidate_promotion_gate(
    *,
    load_json: Callable[[Path], dict | None],
    knowledge_root: Path,
    topic_slug: str,
) -> dict | None:
    selection_payload = load_consultation_followup_selection(
        load_json=load_json,
        knowledge_root=knowledge_root,
        topic_slug=topic_slug,
    ) or {}
    route_choice_payload = load_selected_candidate_route_choice(
        load_json=load_json,
        knowledge_root=knowledge_root,
        topic_slug=topic_slug,
    ) or {}
    selected_candidate_id = str(
        route_choice_payload.get("selected_candidate_id")
        or selection_payload.get("selected_candidate_id")
        or ""
    ).strip()
    gate_payload = load_json(
        knowledge_root / "runtime" / "topics" / topic_slug / "promotion_gate.json"
    )
    if not gate_payload:
        return None
    if selected_candidate_id and str(gate_payload.get("candidate_id") or "").strip() != selected_candidate_id:
        return None
    return gate_payload


def selected_candidate_promotion_gate_ready_for_materialization(
    *,
    load_json: Callable[[Path], dict | None],
    knowledge_root: Path,
    topic_slug: str,
) -> bool:
    route_choice_payload = load_selected_candidate_route_choice(
        load_json=load_json,
        knowledge_root=knowledge_root,
        topic_slug=topic_slug,
    )
    if not route_choice_payload:
        return False
    if str(route_choice_payload.get("chosen_action_type") or "").strip() != "l2_promotion_review":
        return False
    if load_selected_candidate_promotion_gate(
        load_json=load_json,
        knowledge_root=knowledge_root,
        topic_slug=topic_slug,
    ):
        return False
    next_action_decision = load_json(
        knowledge_root / "runtime" / "topics" / topic_slug / "next_action_decision.json"
    )
    if not next_action_decision:
        return False
    selected_action = next_action_decision.get("selected_action") or {}
    if str(selected_action.get("action_type") or "").strip() != "l2_promotion_review":
        return False
    latest_staged = latest_topic_local_staged_entry_updated_at(
        knowledge_root=knowledge_root,
        topic_slug=topic_slug,
    )
    continue_count = count_continue_decisions_after(
        knowledge_root=knowledge_root,
        topic_slug=topic_slug,
        cutoff=latest_staged,
    )
    return continue_count >= 4


def selected_candidate_promotion_gate_paths(
    *,
    knowledge_root: Path,
    topic_slug: str,
) -> dict[str, Path]:
    runtime_root = knowledge_root / "runtime" / "topics" / topic_slug
    return {
        "json": runtime_root / "promotion_gate.json",
        "note": runtime_root / "promotion_gate.md",
    }


def derive_selected_candidate_promotion_gate(
    *,
    load_json: Callable[[Path], dict | None],
    knowledge_root: Path,
    topic_slug: str,
    requested_by: str,
) -> dict | None:
    route_choice_payload = load_selected_candidate_route_choice(
        load_json=load_json,
        knowledge_root=knowledge_root,
        topic_slug=topic_slug,
    )
    if not route_choice_payload:
        return None
    if str(route_choice_payload.get("chosen_action_type") or "").strip() != "l2_promotion_review":
        return None
    selected_candidate_path = str(route_choice_payload.get("selected_candidate_path") or "").strip()
    if not selected_candidate_path:
        return None
    candidate_payload = load_json(knowledge_root / selected_candidate_path)
    if not candidate_payload:
        return None
    selection_payload = load_consultation_followup_selection(
        load_json=load_json,
        knowledge_root=knowledge_root,
        topic_slug=topic_slug,
    ) or {}
    requested_at = datetime.now().astimezone().isoformat(timespec="seconds")

    def _dedupe_strings(rows: object) -> list[str]:
        ordered: list[str] = []
        seen: set[str] = set()
        if not isinstance(rows, list):
            return ordered
        for item in rows:
            cleaned = str(item or "").strip()
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            ordered.append(cleaned)
        return ordered

    candidate_id = str(
        route_choice_payload.get("selected_candidate_id")
        or selection_payload.get("selected_candidate_id")
        or candidate_payload.get("entry_id")
        or ""
    ).strip()
    candidate_type = str(
        candidate_payload.get("candidate_unit_type")
        or candidate_payload.get("entry_kind")
        or "staged_unit"
    ).strip()
    title = str(
        route_choice_payload.get("selected_candidate_title")
        or selection_payload.get("selected_candidate_title")
        or candidate_payload.get("title")
        or candidate_id
    ).strip()
    summary = str(candidate_payload.get("summary") or route_choice_payload.get("chosen_action_summary") or "").strip()
    provenance = candidate_payload.get("provenance") or {}
    return {
        "topic_slug": topic_slug,
        "run_id": str(route_choice_payload.get("run_id") or selection_payload.get("run_id") or "").strip(),
        "candidate_id": candidate_id,
        "candidate_type": candidate_type,
        "title": title,
        "summary": summary,
        "route": "selected_candidate_promotion_review",
        "status": "pending_human_approval",
        "intended_l2_targets": _dedupe_strings(candidate_payload.get("intended_l2_targets")),
        "backend_id": str(provenance.get("backend_id") or candidate_payload.get("backend_id") or "").strip(),
        "target_backend_root": str(
            provenance.get("backend_root") or candidate_payload.get("target_backend_root") or ""
        ).strip(),
        "review_mode": "human",
        "canonical_layer": "L2",
        "coverage_status": str(candidate_payload.get("coverage_status") or "not_audited"),
        "consensus_status": str(candidate_payload.get("consensus_status") or "not_requested"),
        "regression_gate_status": str(candidate_payload.get("regression_gate_status") or "not_audited"),
        "topic_completion_status": str(candidate_payload.get("topic_completion_status") or "not_assessed"),
        "source_layer": "L2_staging",
        "requested_destination_layer": "L2",
        "resolved_destination_layer": None,
        "approval_change_kind": "pending_review",
        "human_modifications": [],
        "supporting_regression_question_ids": _dedupe_strings(
            candidate_payload.get("supporting_regression_question_ids")
        ),
        "supporting_oracle_ids": _dedupe_strings(candidate_payload.get("supporting_oracle_ids")),
        "supporting_regression_run_ids": _dedupe_strings(
            candidate_payload.get("supporting_regression_run_ids")
        ),
        "runtime_schema_types": [],
        "runtime_schema_paths": {},
        "runtime_artifact_paths": {},
        "runtime_schema_context": {
            "status": "not_materialized",
            "source": "selected_candidate_route_choice",
        },
        "promotion_blockers": _dedupe_strings(candidate_payload.get("promotion_blockers")),
        "split_required": bool(candidate_payload.get("split_required")),
        "cited_recovery_required": bool(candidate_payload.get("cited_recovery_required")),
        "followup_gap_ids": _dedupe_strings(candidate_payload.get("followup_gap_ids")),
        "merge_outcome": "pending",
        "requested_by": requested_by,
        "requested_at": requested_at,
        "approved_by": None,
        "approved_at": None,
        "rejected_by": None,
        "rejected_at": None,
        "promoted_by": None,
        "promoted_at": None,
        "promoted_units": [],
        "notes": (
            "Auto-materialized from the selected staged candidate route choice so the first "
            "promotion-review gate is explicit and durable."
        ),
    }


def render_selected_candidate_promotion_gate_markdown(payload: dict[str, Any]) -> str:
    return (
        "# L2 Promotion Gate\n\n"
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`\n"
        f"- Run id: `{payload.get('run_id') or '(missing)'}`\n"
        f"- Candidate id: `{payload.get('candidate_id') or '(missing)'}`\n"
        f"- Candidate type: `{payload.get('candidate_type') or '(missing)'}`\n"
        f"- Status: `{payload.get('status') or '(missing)'}`\n"
        f"- Route: `{payload.get('route') or '(missing)'}`\n"
        f"- Requested by: `{payload.get('requested_by') or '(missing)'}` at `{payload.get('requested_at') or '(missing)'}`\n"
        f"- Review mode: `{payload.get('review_mode') or '(missing)'}`\n"
        f"- Canonical layer: `{payload.get('canonical_layer') or '(missing)'}`\n"
        f"- Source layer: `{payload.get('source_layer') or '(missing)'}`\n"
        f"- Split required: `{payload.get('split_required')}`\n"
        f"- Cited recovery required: `{payload.get('cited_recovery_required')}`\n"
        "\n"
        "## Candidate Summary\n\n"
        f"{payload.get('summary') or '(missing)'}\n\n"
        "## Promotion Blockers\n\n"
        + "".join(f"- {blocker}\n" for blocker in (payload.get("promotion_blockers") or ["(none)"]))
        + "\n"
        "## Operator Rule\n\n"
        "- L2 promotion is blocked until a human explicitly approves or rejects this gate.\n"
    )


def should_advance_past_staged_l2_review(
    *,
    knowledge_root: Path,
    topic_slug: str,
    runtime_contract: dict | None,
) -> bool:
    if not runtime_contract:
        return False
    if str(runtime_contract.get("runtime_mode") or "").strip() != "explore":
        return False
    if str(runtime_contract.get("active_submode") or "").strip() != "literature":
        return False
    latest_staged = latest_topic_local_staged_entry_updated_at(
        knowledge_root=knowledge_root,
        topic_slug=topic_slug,
    )
    if latest_staged is None:
        return False
    latest_continue = latest_continue_decision_updated_at(
        knowledge_root=knowledge_root,
        topic_slug=topic_slug,
    )
    if latest_continue is None:
        return False
    return latest_continue > latest_staged


def _queue_shaping_block_policy() -> dict[str, bool]:
    return {
        "allow_capability_append": False,
        "allow_runtime_append": False,
        "allow_closed_loop_append": False,
        "allow_literature_followup_append": False,
    }


def _active_operator_checkpoint(operator_checkpoint: dict | None) -> bool:
    if not operator_checkpoint:
        return False
    status = str(operator_checkpoint.get("status") or "").strip()
    if status in {"answered", "cancelled", "superseded"}:
        return False
    return bool(operator_checkpoint.get("active")) or status == "requested"


def queue_shaping_policy_from_contract_artifacts(
    runtime_contract: dict | None,
    operator_checkpoint: dict | None,
) -> tuple[dict[str, bool], str | None]:
    default_policy = {
        "allow_capability_append": True,
        "allow_runtime_append": True,
        "allow_closed_loop_append": True,
        "allow_literature_followup_append": True,
    }
    if _active_operator_checkpoint(operator_checkpoint):
        checkpoint_kind = str(operator_checkpoint.get("checkpoint_kind") or "human_checkpoint").strip() or "human_checkpoint"
        return (
            _queue_shaping_block_policy(),
            f"Active operator checkpoint `{checkpoint_kind}` blocks runtime-appended queue expansion until it is answered or cancelled.",
        )
    if not runtime_contract:
        return default_policy, None

    runtime_mode = str(runtime_contract.get("runtime_mode") or "").strip()
    transition_posture = runtime_contract.get("transition_posture") or {}
    transition_kind = str(transition_posture.get("transition_kind") or "").strip()
    requires_human_checkpoint = bool(transition_posture.get("requires_human_checkpoint"))
    triggered_by = {
        str(item).strip()
        for item in (transition_posture.get("triggered_by") or [])
        if str(item).strip()
    }
    if requires_human_checkpoint:
        return (
            _queue_shaping_block_policy(),
            "Runtime transition posture requires a human checkpoint before deeper queue expansion.",
        )
    if runtime_mode == "promote" or "promotion_intent" in triggered_by:
        return (
            _queue_shaping_block_policy(),
            "Promotion routing suppresses runtime-appended queue expansion in favor of explicit promotion handling.",
        )
    if transition_kind == "backedge_transition":
        allow_capability_append = "capability_gap_blocker" in triggered_by
        return (
            {
                "allow_capability_append": allow_capability_append,
                "allow_runtime_append": False,
                "allow_closed_loop_append": False,
                "allow_literature_followup_append": False,
            },
            (
                "Backedge transition keeps only explicit capability-gap recovery append behavior."
                if allow_capability_append
                else "Backedge transition suppresses runtime-appended queue expansion until the contract names a recovery lane."
            ),
        )
    return default_policy, None


def enrich_queue_meta(
    queue_meta: dict[str, Any],
    *,
    topic_slug: str,
    runtime_contract: dict | None,
    operator_checkpoint: dict | None,
    append_policy_reason: str | None,
) -> dict[str, Any]:
    enriched = dict(queue_meta)
    enriched["runtime_contract_path"] = (
        f"runtime/topics/{topic_slug}/runtime_protocol.generated.json"
        if runtime_contract is not None
        else None
    )
    enriched["operator_checkpoint_path"] = (
        f"runtime/topics/{topic_slug}/operator_checkpoint.active.json"
        if operator_checkpoint is not None
        else None
    )
    enriched["append_policy_reason"] = append_policy_reason
    return enriched


def queue_rows_from_pending_actions(
    topic_state: dict[str, Any],
    *,
    declared_contract_path: str | None,
    classify_action: Callable[[str], tuple[str, bool]],
) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    for index, summary in enumerate(topic_state.get("pending_actions", []), start=1):
        action_type, auto_runnable = classify_action(summary)
        queue.append(
            {
                "action_id": f"action:{topic_state['topic_slug']}:{index:02d}",
                "topic_slug": topic_state["topic_slug"],
                "resume_stage": topic_state["resume_stage"],
                "status": "pending",
                "action_type": action_type,
                "summary": summary,
                "auto_runnable": auto_runnable,
                "handler": None,
                "handler_args": {},
                "queue_source": "heuristic",
                "declared_contract_path": declared_contract_path,
            }
        )
    return queue


def maybe_append_skill_discovery_action(
    queue: list[dict[str, Any]],
    *,
    topic_state: dict[str, Any],
    skill_queries: list[str],
    skill_discovery_script: Path,
    queue_meta: dict[str, Any],
    queue_shaping_policy: dict[str, bool],
) -> None:
    needs_capability_review = any(
        action["action_type"] in {"backend_extension", "manual_followup"} for action in queue
    )
    has_skill_action = any(action["action_type"] == "skill_discovery" for action in queue)
    if (
        needs_capability_review
        and not has_skill_action
        and queue_meta.get("append_skill_action_if_needed", True)
        and queue_shaping_policy["allow_capability_append"]
    ):
        queue.append(
            {
                "action_id": f"action:{topic_state['topic_slug']}:{len(queue) + 1:02d}",
                "topic_slug": topic_state["topic_slug"],
                "resume_stage": topic_state["resume_stage"],
                "status": "pending",
                "action_type": "skill_discovery",
                "summary": (
                    "Review whether an external skill or adapter improvement can reduce the current "
                    "capability gap before continuing manual follow-up."
                ),
                "auto_runnable": bool(skill_queries),
                "handler": str(skill_discovery_script) if skill_queries else None,
                "handler_args": {"queries": skill_queries} if skill_queries else {},
                "queue_source": "runtime_appended",
                "declared_contract_path": queue_meta.get("declared_contract_path"),
            }
        )


def maybe_append_literature_intake_stage_action(
    queue: list[dict[str, Any]],
    *,
    topic_state: dict[str, Any],
    runtime_contract: dict | None,
    knowledge_root: Path,
    queue_meta: dict[str, Any],
    queue_shaping_policy: dict[str, bool],
) -> None:
    if not runtime_contract or not queue_shaping_policy["allow_runtime_append"]:
        return
    if str(runtime_contract.get("runtime_mode") or "").strip() != "explore":
        return
    if str(runtime_contract.get("active_submode") or "").strip() != "literature":
        return
    if any(str(row.get("action_type") or "").strip() == "literature_intake_stage" for row in queue):
        return
    candidate_signature = compute_literature_intake_stage_signature(runtime_contract)
    if topic_has_matching_literature_stage(
        knowledge_root=knowledge_root,
        topic_slug=str(topic_state.get("topic_slug") or "").strip(),
        candidate_signature=candidate_signature,
    ):
        return
    active_research_contract = runtime_contract.get("active_research_contract") or {}
    l1_source_intake = active_research_contract.get("l1_source_intake") or {}
    concept_graph = l1_source_intake.get("concept_graph") or {}
    has_graph_signal = any(
        len(concept_graph.get(key) or [])
        for key in ("nodes", "edges", "communities", "god_nodes")
    )
    if not (
        l1_source_intake.get("method_specificity_rows")
        or l1_source_intake.get("contradiction_candidates")
        or has_graph_signal
    ):
        return
    queue.insert(
        0,
        {
            "action_id": f"action:{topic_state['topic_slug']}:literature-intake-stage:01",
            "topic_slug": topic_state["topic_slug"],
            "resume_stage": topic_state["resume_stage"],
            "status": "pending",
            "action_type": "literature_intake_stage",
            "summary": "Stage bounded literature-intake units from the current L1 vault into L2 staging.",
            "auto_runnable": True,
            "handler": None,
            "handler_args": {"candidate_signature": candidate_signature},
            "queue_source": "runtime_appended",
            "declared_contract_path": queue_meta.get("declared_contract_path"),
        }
    )


def append_closed_loop_actions(
    queue: list[dict[str, Any]],
    *,
    topic_state: dict[str, Any],
    queue_meta: dict[str, Any],
    allow_runtime_appends: bool,
    queue_shaping_policy: dict[str, bool],
    closed_loop: dict[str, Any],
    advance_closed_loop_script: Path,
    execution_handoff_script: Path,
) -> None:
    if not allow_runtime_appends or not queue_shaping_policy["allow_closed_loop_append"]:
        return

    handler_args = {"run_id": topic_state.get("latest_run_id")}
    if closed_loop["next_transition"] == "select_route":
        queue.append(
            {
                "action_id": f"action:{topic_state['topic_slug']}:closed-loop-select-route",
                "topic_slug": topic_state["topic_slug"],
                "resume_stage": "L4",
                "status": "pending",
                "action_type": "select_validation_route",
                "summary": "Select exactly one validation route and persist `selected_validation_route.json`.",
                "auto_runnable": True,
                "handler": str(advance_closed_loop_script),
                "handler_args": {**handler_args, "step": "select_route"},
                "queue_source": "runtime_appended",
                "declared_contract_path": queue_meta.get("declared_contract_path"),
            }
        )
        return
    if closed_loop["next_transition"] == "materialize_task":
        queue.append(
            {
                "action_id": f"action:{topic_state['topic_slug']}:closed-loop-materialize-task",
                "topic_slug": topic_state["topic_slug"],
                "resume_stage": "L4",
                "status": "pending",
                "action_type": "materialize_execution_task",
                "summary": "Compile the selected route into `execution_task.json` and `execution_task.md` for the external execution lane.",
                "auto_runnable": True,
                "handler": str(advance_closed_loop_script),
                "handler_args": {**handler_args, "step": "materialize_task"},
                "queue_source": "runtime_appended",
                "declared_contract_path": queue_meta.get("declared_contract_path"),
            }
        )
        return
    if closed_loop["next_transition"] == "ingest_result":
        queue.append(
            {
                "action_id": f"action:{topic_state['topic_slug']}:closed-loop-ingest-result",
                "topic_slug": topic_state["topic_slug"],
                "resume_stage": "L4",
                "status": "pending",
                "action_type": "ingest_execution_result",
                "summary": "Ingest the returned execution result and write the result manifest, summary, decision ledger, and bounded literature follow-ups.",
                "auto_runnable": True,
                "handler": str(advance_closed_loop_script),
                "handler_args": {**handler_args, "step": "ingest_result"},
                "queue_source": "runtime_appended",
                "declared_contract_path": queue_meta.get("declared_contract_path"),
            }
        )
        return
    if not (closed_loop["awaiting_external_result"] and closed_loop["execution_task"]):
        return

    execution_task = closed_loop["execution_task"]
    auto_dispatch_allowed = bool(execution_task.get("auto_dispatch_allowed"))
    executor_lane = execution_task.get("executor_kind") or execution_task.get("assigned_runtime", "codex")
    queue.append(
        {
            "action_id": f"action:{topic_state['topic_slug']}:closed-loop-await-result",
            "topic_slug": topic_state["topic_slug"],
            "resume_stage": "L4",
            "status": "pending",
            "action_type": "dispatch_execution_task" if auto_dispatch_allowed else "await_execution_result",
            "summary": (
                f"Dispatch `{closed_loop['paths'].get('execution_task_path') or '(missing)'}` in the external "
                f"`{executor_lane}` lane and require "
                f"`{closed_loop['paths'].get('returned_result_path') or '(missing)'}` to be written."
                if auto_dispatch_allowed
                else (
                    f"Run `{closed_loop['paths'].get('execution_task_path') or '(missing)'}` in the external "
                    f"`{executor_lane}` lane and write "
                    f"`{closed_loop['paths'].get('returned_result_path') or '(missing)'}` using the declared result contract."
                )
            ),
            "auto_runnable": auto_dispatch_allowed,
            "handler": str(execution_handoff_script) if auto_dispatch_allowed else None,
            "handler_args": {**handler_args} if auto_dispatch_allowed else {},
            "queue_source": "runtime_appended",
            "declared_contract_path": queue_meta.get("declared_contract_path"),
        }
    )


def append_literature_followup_actions(
    queue: list[dict[str, Any]],
    *,
    topic_state: dict[str, Any],
    queue_meta: dict[str, Any],
    allow_runtime_appends: bool,
    queue_shaping_policy: dict[str, bool],
    closed_loop: dict[str, Any],
    completed_followups: set[tuple[str, str]],
    literature_followup_script: Path,
    followup_max_results: Callable[[str], int],
) -> None:
    if not allow_runtime_appends or not queue_shaping_policy["allow_literature_followup_append"]:
        return

    handler_args = {"run_id": topic_state.get("latest_run_id")}
    for index, followup in enumerate(closed_loop.get("literature_followups") or [], start=1):
        query = str(followup.get("query") or "").strip()
        target_source_type = str(followup.get("target_source_type") or "paper").strip() or "paper"
        if not query or (query, target_source_type) in completed_followups:
            continue
        priority = str(followup.get("priority") or "medium").strip() or "medium"
        auto_runnable = target_source_type in {"paper", "arxiv", "review"}
        queue.append(
            {
                "action_id": f"action:{topic_state['topic_slug']}:literature-followup:{index:02d}",
                "topic_slug": topic_state["topic_slug"],
                "resume_stage": "L3",
                "status": "pending",
                "action_type": "literature_followup_search",
                "summary": f"Search bounded {target_source_type} follow-up literature for `{query}` and register the top matches into Layer 0/1.",
                "auto_runnable": auto_runnable,
                "handler": str(literature_followup_script) if auto_runnable else None,
                "handler_args": {
                    **handler_args,
                    "query": query,
                    "priority": priority,
                    "target_source_type": target_source_type,
                    "max_results": followup_max_results(priority),
                }
                if auto_runnable
                else {},
                "queue_source": "runtime_appended",
                "declared_contract_path": queue_meta.get("declared_contract_path"),
            }
        )


def append_runtime_helper_actions(
    queue: list[dict[str, Any]],
    *,
    allow_runtime_appends: bool,
    helper_action_groups: list[list[dict[str, Any]]],
) -> None:
    if not allow_runtime_appends:
        return
    for rows in helper_action_groups:
        queue.extend(rows)


def reorder_queue_with_runtime_contract(
    queue: list[dict[str, Any]],
    runtime_contract: dict | None,
    *,
    declared_contract_used: bool,
) -> list[dict[str, Any]]:
    if declared_contract_used:
        return queue
    preferred_action_types = preferred_action_types_from_runtime_contract(runtime_contract)
    if not preferred_action_types:
        return queue
    preferred = [
        row for row in queue if str(row.get("action_type") or "").strip() in preferred_action_types
    ]
    if not preferred:
        return queue
    preferred_ids = {str(row.get("action_id") or "").strip() for row in preferred}
    trailing = [row for row in queue if str(row.get("action_id") or "").strip() not in preferred_ids]
    return preferred + trailing
