from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from closed_loop_v1 import compute_closed_loop_status


def derive_surface_roots(topic_state: dict[str, Any]) -> dict[str, str]:
    topic_slug = topic_state["topic_slug"]
    pointers = topic_state["pointers"]
    feedback_status_path = pointers.get("feedback_status_path")
    feedback_run_root = feedback_status_path.rsplit("/", 1)[0] if feedback_status_path else f"topics/{topic_slug}/L3"
    promotion_decision_path = pointers.get("promotion_decision_path")
    validation_run_root = promotion_decision_path.rsplit("/", 1)[0] if promotion_decision_path else f"topics/{topic_slug}/L4"
    return {
        "L0": f"topics/{topic_slug}/L0",
        "L1": f"topics/{topic_slug}/L1",
        "L2": "canonical",
        "L3": feedback_run_root,
        "L4_execution": validation_run_root,
        "L4_control": pointers.get("control_note_path") or "(missing)",
        "L3_action_contract": pointers.get("next_actions_contract_path") or "(missing)",
        "runtime": f"topics/{topic_slug}/runtime",
    }


def build_interaction_state(
    topic_state: dict[str, Any],
    queue: list[dict[str, Any]],
    queue_meta: dict[str, Any],
    human_request: str,
    topic_runtime_root: Path,
    knowledge_root: Path,
    *,
    action_queue_contract_generated_filename: str,
    action_queue_contract_generated_note_filename: str,
    deferred_buffer_note_filename: str,
    followup_subtopics_note_filename: str,
    deferred_buffer_filename: str,
    followup_subtopics_filename: str,
    now_iso: Callable[[], str],
    load_json: Callable[[Path], dict[str, Any] | None],
) -> dict[str, Any]:
    pointers = topic_state["pointers"]
    surfaces = derive_surface_roots(topic_state)
    surfaces["runtime_unfinished"] = f"topics/{topic_state['topic_slug']}/runtime/unfinished_work.md"
    surfaces["runtime_decision"] = f"topics/{topic_state['topic_slug']}/runtime/next_action_decision.md"
    surfaces["runtime_queue_contract"] = (
        f"topics/{topic_state['topic_slug']}/runtime/{action_queue_contract_generated_note_filename}"
    )
    surfaces["runtime_promotion_gate"] = f"topics/{topic_state['topic_slug']}/runtime/promotion_gate.md"
    surfaces["runtime_deferred_buffer"] = f"topics/{topic_state['topic_slug']}/runtime/{deferred_buffer_note_filename}"
    surfaces["runtime_followup_subtopics"] = f"topics/{topic_state['topic_slug']}/runtime/{followup_subtopics_note_filename}"
    capability_artifacts = [
        str(path)
        for filename in ("skill_discovery.json", "skill_recommendations.md")
        for path in [topic_runtime_root / filename]
        if path.exists()
    ]
    closed_loop = compute_closed_loop_status(
        knowledge_root,
        topic_state["topic_slug"],
        topic_state.get("latest_run_id"),
    )
    surfaces["runtime_followup_gaps"] = (
        closed_loop["paths"].get("followup_gap_writeback_note_path")
        or f"topics/{topic_state['topic_slug']}/runtime/(followup-gap-writeback-missing)"
    )
    decision_payload = load_json(topic_runtime_root / "next_action_decision.json") or {}
    unfinished_payload = load_json(topic_runtime_root / "unfinished_work.json") or {}
    return {
        "topic_slug": topic_state["topic_slug"],
        "updated_at": now_iso(),
        "updated_by": topic_state.get("updated_by", "codex"),
        "human_request": human_request,
        "resume_stage": topic_state["resume_stage"],
        "last_materialized_stage": topic_state["last_materialized_stage"],
        "autonomy_policy": {
            "mode": "persistent_research_loop",
            "termination_conditions": [
                "validated reusable output enters Layer 2",
                "a durable deferred or rejected conclusion is recorded",
                "a hard blocker requires human intervention",
            ],
            "self_modification_allowed_targets": [
                "research/knowledge-hub/runtime",
                "research/knowledge-hub/validation",
                "research/adapters/openclaw",
                "skills-shared",
            ],
            "self_modification_rule": (
                "Capability upgrades must leave durable files on disk and must be reported in the "
                "final output or handoff note."
            ),
        },
        "delivery_contract": {
            "possible_final_layers": ["L1", "L2", "L3", "L4"],
            "rule": (
                "Outputs land in the highest justified layer, not automatically in Layer 2. "
                "Final reporting must name exact artifact paths and explain the layer choice."
            ),
        },
        "human_edit_surfaces": [
            {"surface": "L0", "path": surfaces["L0"], "role": "source substrate"},
            {"surface": "L1", "path": surfaces["L1"], "role": "provisional intake"},
            {"surface": "L2", "path": surfaces["L2"], "role": "canonical reusable memory"},
            {"surface": "L3", "path": surfaces["L3"], "role": "exploratory research run"},
            {"surface": "L3_action_contract", "path": surfaces["L3_action_contract"], "role": "declared L3 action contract when present"},
            {"surface": "L4_execution", "path": surfaces["L4_execution"], "role": "execution-backed validation"},
            {"surface": "L4_control", "path": surfaces["L4_control"], "role": "human-readable adjudication"},
            {"surface": "runtime", "path": surfaces["runtime"], "role": "resume and operator visibility"},
            {"surface": "runtime_unfinished", "path": surfaces["runtime_unfinished"], "role": "human-readable unfinished-work index"},
            {"surface": "runtime_decision", "path": surfaces["runtime_decision"], "role": "human-readable next-action decision"},
            {"surface": "runtime_queue_contract", "path": surfaces["runtime_queue_contract"], "role": "generated action-contract snapshot for editing"},
            {"surface": "runtime_promotion_gate", "path": surfaces["runtime_promotion_gate"], "role": "human approval gate for L2 promotion"},
            {"surface": "runtime_deferred_buffer", "path": surfaces["runtime_deferred_buffer"], "role": "deferred candidate parking and reactivation buffer"},
            {"surface": "runtime_followup_subtopics", "path": surfaces["runtime_followup_subtopics"], "role": "parent-child lineage for cited-literature subtopics"},
            {"surface": "runtime_followup_gaps", "path": surfaces["runtime_followup_gaps"], "role": "structured unresolved gap ledger from closed-loop result ingest"},
            {"surface": "runtime_trajectory", "path": closed_loop["paths"].get("trajectory_note_path") or f"topics/{topic_state['topic_slug']}/runtime/(trajectory-log-missing)", "role": "human-readable execution trajectory after result ingest"},
            {"surface": "runtime_failure_classification", "path": closed_loop["paths"].get("failure_classification_note_path") or f"topics/{topic_state['topic_slug']}/runtime/(failure-classification-missing)", "role": "human-readable failure classification after result ingest"},
        ],
        "capability_adaptation": {
            "protocol_path": "research/adapters/openclaw/SKILL_ADAPTATION_PROTOCOL.md",
            "discovery_script": "research/adapters/openclaw/scripts/discover_external_skills.py",
            "auto_install_allowed": False,
            "recommended_when_action_types_present": ["backend_extension", "manual_followup", "skill_discovery"],
            "discovery_artifacts": capability_artifacts,
        },
        "conformance": {
            "protocol_path": "research/knowledge-hub/AGENT_CONFORMANCE_PROTOCOL.md",
            "audit_script": "research/knowledge-hub/runtime/scripts/audit_topic_conformance.py",
        },
        "closed_loop": {
            "selected_route_path": closed_loop["paths"].get("selected_route_path"),
            "execution_task_path": closed_loop["paths"].get("execution_task_path"),
            "returned_result_path": closed_loop["paths"].get("returned_result_path"),
            "result_manifest_path": closed_loop["paths"].get("result_manifest_path"),
            "trajectory_log_path": closed_loop["paths"].get("trajectory_log_path"),
            "trajectory_note_path": closed_loop["paths"].get("trajectory_note_path"),
            "failure_classification_path": closed_loop["paths"].get("failure_classification_path"),
            "failure_classification_note_path": closed_loop["paths"].get("failure_classification_note_path"),
            "decision_ledger_path": closed_loop["paths"].get("decision_ledger_path"),
            "literature_followup_path": closed_loop["paths"].get("literature_followup_path"),
            "followup_gap_writeback_path": closed_loop["paths"].get("followup_gap_writeback_path"),
            "followup_gap_writeback_note_path": closed_loop["paths"].get("followup_gap_writeback_note_path"),
            "next_transition": closed_loop.get("next_transition"),
            "next_transition_reason": closed_loop.get("next_transition_reason"),
            "selected_route_id": (closed_loop.get("selected_route") or {}).get("route_id"),
            "task_id": (closed_loop.get("execution_task") or {}).get("task_id"),
            "result_id": (closed_loop.get("result_manifest") or {}).get("result_id"),
            "latest_decision": (closed_loop.get("latest_decision") or {}).get("decision"),
            "literature_followup_count": len(closed_loop.get("literature_followups") or []),
            "followup_gap_count": len(closed_loop.get("followup_gaps") or []),
            "research_mode": topic_state.get("research_mode"),
            "executor_kind": topic_state.get("active_executor_kind"),
            "reasoning_profile": topic_state.get("active_reasoning_profile"),
            "failure_severity": (closed_loop.get("failure_classification") or {}).get("severity"),
            "deferred_buffer_path": f"topics/{topic_state['topic_slug']}/runtime/{deferred_buffer_filename}",
            "followup_subtopics_path": f"topics/{topic_state['topic_slug']}/runtime/{followup_subtopics_filename}",
        },
        "decision_surface": {
            "unfinished_work_path": f"topics/{topic_state['topic_slug']}/runtime/unfinished_work.json",
            "unfinished_work_note_path": f"topics/{topic_state['topic_slug']}/runtime/unfinished_work.md",
            "next_action_decision_path": f"topics/{topic_state['topic_slug']}/runtime/next_action_decision.json",
            "next_action_decision_note_path": f"topics/{topic_state['topic_slug']}/runtime/next_action_decision.md",
            "decision_contract_path": pointers.get("next_action_decision_contract_path"),
            "decision_mode": decision_payload.get("decision_mode"),
            "decision_source": decision_payload.get("decision_source"),
            "decision_contract_status": decision_payload.get("decision_contract_status"),
            "decision_basis": decision_payload.get("decision_basis"),
            "selected_action_id": (decision_payload.get("selected_action") or {}).get("action_id"),
            "selected_action_type": (decision_payload.get("selected_action") or {}).get("action_type"),
            "selected_action_auto_runnable": bool((decision_payload.get("selected_action") or {}).get("auto_runnable")),
            "reason": decision_payload.get("reason"),
            "control_note_path": (decision_payload.get("control_note") or {}).get("path"),
            "control_note_status": (decision_payload.get("control_note") or {}).get("steering_status"),
            "pending_count": unfinished_payload.get("pending_count"),
            "manual_pending_count": unfinished_payload.get("manual_pending_count"),
            "auto_pending_count": unfinished_payload.get("auto_pending_count"),
        },
        "action_queue_surface": {
            "queue_source": queue_meta.get("queue_source") or "heuristic",
            "declared_contract_path": queue_meta.get("declared_contract_path"),
            "declared_contract_used": bool(queue_meta.get("declared_contract_used")),
            "declared_contract_valid": bool(queue_meta.get("declared_contract_valid")),
            "generated_contract_path": f"topics/{topic_state['topic_slug']}/runtime/{action_queue_contract_generated_filename}",
            "generated_contract_note_path": f"topics/{topic_state['topic_slug']}/runtime/{action_queue_contract_generated_note_filename}",
            "policy_note": queue_meta.get("policy_note"),
        },
        "pending_actions": queue,
    }


def build_operator_console(topic_state: dict[str, Any], interaction_state: dict[str, Any], queue: list[dict[str, Any]]) -> str:
    decision_surface = interaction_state.get("decision_surface") or {}
    queue_surface = interaction_state.get("action_queue_surface") or {}
    promotion_gate = topic_state.get("promotion_gate") or {}
    status_explainability = topic_state.get("status_explainability") or {}
    current_route_choice = status_explainability.get("current_route_choice") or {}
    last_evidence_return = status_explainability.get("last_evidence_return") or {}
    active_human_need = status_explainability.get("active_human_need") or {}
    selected_action_id = str(decision_surface.get("selected_action_id") or "")
    selected_action = next((action for action in queue if str(action.get("action_id") or "") == selected_action_id), queue[0] if queue else None)
    selected_summary = str((selected_action or {}).get("summary") or "(no pending action)")
    selected_type = str((selected_action or {}).get("action_type") or "(none)")
    selected_auto = str(bool((selected_action or {}).get("auto_runnable"))).lower()
    trigger_rows = [
        ("decision_override_present", (decision_surface.get("control_note_status") or "missing") != "missing" or (decision_surface.get("decision_contract_status") or "missing") != "missing", "Open the decision contract or control note before trusting heuristic queue selection."),
        ("promotion_intent", str(promotion_gate.get("status") or "not_requested") in {"requested", "approved"}, "Open the promotion gate before any writeback-facing work."),
        ("capability_gap_blocker", any(str(action.get("action_type") or "") == "skill_discovery" for action in queue), "Open capability/discovery surfaces only when the blocker is a real workflow gap."),
    ]
    open_next = decision_surface.get("next_action_decision_note_path") or queue_surface.get("generated_contract_note_path") or "(missing)"
    lines = [
        "# AITP operator console", "", "## Immediate execution contract", "",
        f"- Topic slug: `{interaction_state['topic_slug']}`",
        f"- Human request: `{interaction_state['human_request']}`",
        f"- Resume stage: `{interaction_state['resume_stage']}`",
        f"- Last materialized stage: `{interaction_state['last_materialized_stage']}`",
        f"- Current bounded action: `{selected_summary}`",
        f"- Selected action type: `{selected_type}`",
        f"- Selected action auto-runnable: `{selected_auto}`",
        f"- Open next: `{open_next}`", "",
        "### Do now", "",
        f"- Continue bounded `{interaction_state['resume_stage']}` work on the selected action instead of expanding the whole protocol surface at once.",
        "- Use declared decision and queue artifacts before heuristic interpretation.",
        "- Keep final reporting honest about exact artifact paths and chosen layer.", "",
        "### Do not do yet", "",
        "- Do not treat consultation as promotion or perform writeback without the gate surfaces.",
        "- Do not claim heavy execution happened unless returned execution artifacts exist.",
        "- Do not replace declared control notes or decision contracts with ad hoc queue guesses.", "",
        "### Escalate when", "",
    ]
    for name, active, note in trigger_rows:
        lines.append(f"- `{name}` status=`{'active' if active else 'inactive'}`: {note}")
    if status_explainability:
        lines.extend(["", "## Topic explainability", "",
            f"- Why here: {status_explainability.get('why_this_topic_is_here') or '(missing)'}",
            f"- Current route: {current_route_choice.get('next_action_summary') or '(none)'}",
            f"- Last evidence: {last_evidence_return.get('summary') or '(none)'}",
            f"- Human need: {active_human_need.get('summary') or '(none)'}"])
    lines.extend(["", "## Active loops", "",
        "1. Research loop: use L0/L1/L2/L3/L4 according to the current epistemic state.",
        "2. Capability loop: if a missing workflow or backend is the blocker, run controlled skill discovery before declaring failure.",
        "3. Delivery loop: final output may land in L1, L2, L3, or L4, but it must always report exact artifact paths and the reason for that layer choice.", "",
        "## Deferred surfaces and human edit areas", ""])
    for surface in interaction_state["human_edit_surfaces"]:
        lines.append(f"- [{surface['surface']}] `{surface['path']}` {surface['role']}")
    lines.extend(["", "## Pending actions", ""])
    for index, action in enumerate(queue, start=1):
        handler = action["handler"] or "(manual)"
        lines.append(f"{index}. [{action['action_type']}] {action['summary']} (auto_runnable={str(action['auto_runnable']).lower()}, handler={handler})")
    lines.extend(["", "## Decision surface", "",
        f"- Mode: `{decision_surface.get('decision_mode') or '(missing)'}`",
        f"- Source: `{decision_surface.get('decision_source') or '(missing)'}`",
        f"- Basis: `{decision_surface.get('decision_basis') or '(missing)'}`",
        f"- Selected action: `{decision_surface.get('selected_action_id') or '(none)'}`",
        f"- Selected type: `{decision_surface.get('selected_action_type') or '(none)'}`",
        f"- Selected action auto-runnable: `{str(bool(decision_surface.get('selected_action_auto_runnable'))).lower()}`",
        f"- Pending counts: total=`{decision_surface.get('pending_count', '(missing)')}`, manual=`{decision_surface.get('manual_pending_count', '(missing)')}`, auto=`{decision_surface.get('auto_pending_count', '(missing)')}`",
        f"- Reason: {decision_surface.get('reason') or '(missing)'}",
        f"- Control note: `{decision_surface.get('control_note_path') or '(missing)'}` status=`{decision_surface.get('control_note_status') or 'missing'}`",
        f"- Innovation direction: `{topic_state.get('pointers', {}).get('innovation_direction_path') or '(missing)'}`",
        f"- Innovation decisions: `{topic_state.get('pointers', {}).get('innovation_decisions_path') or '(missing)'}`",
        f"- Decision contract: `{decision_surface.get('decision_contract_path') or '(missing)'}` status=`{decision_surface.get('decision_contract_status') or 'missing'}`", "",
        "## Decision artifacts", "",
        f"- Unfinished work JSON: `{decision_surface.get('unfinished_work_path') or '(missing)'}`",
        f"- Unfinished work note: `{decision_surface.get('unfinished_work_note_path') or '(missing)'}`",
        f"- Next-action decision JSON: `{decision_surface.get('next_action_decision_path') or '(missing)'}`",
        f"- Next-action decision note: `{decision_surface.get('next_action_decision_note_path') or '(missing)'}`", "",
        "## Action queue source", "",
        f"- Queue source: `{queue_surface.get('queue_source') or '(missing)'}`",
        f"- Declared L3 contract: `{queue_surface.get('declared_contract_path') or '(missing)'}`",
        f"- Declared contract used: `{str(bool(queue_surface.get('declared_contract_used'))).lower()}`",
        f"- Generated contract JSON: `{queue_surface.get('generated_contract_path') or '(missing)'}`",
        f"- Generated contract note: `{queue_surface.get('generated_contract_note_path') or '(missing)'}`", "",
        "## L2 promotion gate", "",
        f"- Status: `{promotion_gate.get('status') or 'not_requested'}`",
        f"- Candidate id: `{promotion_gate.get('candidate_id') or '(missing)'}`",
        f"- Candidate type: `{promotion_gate.get('candidate_type') or '(missing)'}`",
        f"- Backend id: `{promotion_gate.get('backend_id') or '(missing)'}`",
        f"- Target backend root: `{promotion_gate.get('target_backend_root') or '(missing)'}`",
        f"- Gate JSON: `{topic_state.get('pointers', {}).get('promotion_gate_path') or '(missing)'}`",
        f"- Gate note: `{topic_state.get('pointers', {}).get('promotion_gate_note_path') or '(missing)'}`"])
    capability = interaction_state["capability_adaptation"]
    lines.extend(["", "## Capability adaptation", "",
        f"- Protocol: `{capability['protocol_path']}`",
        f"- Discovery script: `{capability['discovery_script']}`",
        f"- Auto install allowed: `{str(capability['auto_install_allowed']).lower()}`"])
    discovery_artifacts = capability["discovery_artifacts"]
    if discovery_artifacts:
        lines.append("- Discovery artifacts:")
        for artifact in discovery_artifacts:
            lines.append(f"  - `{artifact}`")
    else:
        lines.append("- Discovery artifacts: `(none yet)`")
    lines.extend(["", "## Delivery rule", "", f"- {interaction_state['delivery_contract']['rule']}", ""])
    return "\n".join(lines)


def build_agent_brief(topic_state: dict[str, Any], queue: list[dict[str, Any]], interaction_state: dict[str, Any]) -> str:
    pointers = topic_state["pointers"]
    backend_bridges = topic_state.get("backend_bridges") or []
    promotion_gate = topic_state.get("promotion_gate") or {}
    decision_surface = interaction_state.get("decision_surface") or {}
    queue_surface = interaction_state.get("action_queue_surface") or {}
    research_mode_profile = topic_state.get("research_mode_profile") or {}
    selected_action_id = str(decision_surface.get("selected_action_id") or "")
    selected_action = next((action for action in queue if str(action.get("action_id") or "") == selected_action_id), queue[0] if queue else None)
    selected_summary = str((selected_action or {}).get("summary") or "(no pending action)")
    trigger_rows = [
        ("decision_override_present", (decision_surface.get("control_note_status") or "missing") != "missing" or (decision_surface.get("decision_contract_status") or "missing") != "missing", "Open control-note or decision-contract artifacts before trusting heuristic routing."),
        ("promotion_intent", str(promotion_gate.get("status") or "not_requested") in {"requested", "approved"}, "Open promotion-gate artifacts before any writeback-facing work."),
        ("non_trivial_consultation", "consult" in selected_summary.lower() or "memory" in selected_summary.lower(), "Open consultation artifacts when L2 memory materially changes terminology, candidate shape, or route choice."),
        ("capability_gap_blocker", any(str(action.get("action_type") or "") == "skill_discovery" for action in queue), "Open capability surfaces only when the blocker is a real missing workflow or backend."),
    ]
    lines = [
        "# AITP agent brief", "", "## Immediate execution contract", "",
        f"- Topic slug: `{topic_state['topic_slug']}`",
        f"- Resume stage: `{topic_state['resume_stage']}`",
        f"- Last materialized stage: `{topic_state['last_materialized_stage']}`",
        f"- Current bounded action: `{selected_summary}`",
        f"- Open next: `topics/{topic_state['topic_slug']}/runtime/operator_console.md`",
        f"- Source count: `{topic_state.get('source_count', 0)}`",
        f"- Latest run id: `{topic_state.get('latest_run_id') or '(none)'}`",
        f"- Research mode: `{topic_state.get('research_mode') or '(missing)'}`",
        f"- Executor kind: `{topic_state.get('active_executor_kind') or '(missing)'}`",
        f"- Reasoning profile: `{topic_state.get('active_reasoning_profile') or '(missing)'}`", "",
        "### Do now", "",
        f"- Continue bounded `{topic_state['resume_stage']}` work on the selected action instead of reopening the whole protocol stack.",
        "- Read exact deeper surfaces only when the named trigger below becomes active.",
        "- Keep outputs in the highest justified layer and report exact artifact paths.", "",
        "### Do not do yet", "",
        "- Do not promote or auto-promote material without the promotion gate and the required supporting artifacts.",
        "- Do not treat consultation lookup as if it already justifies Layer 2 writeback.",
        "- Do not bypass conformance, control notes, or declared contracts with ad hoc browsing.", "",
        "### Escalate when", "",
    ]
    for name, active, note in trigger_rows:
        lines.append(f"- `{name}` status=`{'active' if active else 'inactive'}`: {note}")
    lines.extend(["", "## Deferred surfaces and exact pointers", "",
        f"- Layer 0 source index: `{pointers.get('l0_source_index_path') or '(missing)'}`",
        f"- Intake status: `{pointers.get('intake_status_path') or '(missing)'}`",
        f"- Feedback status: `{pointers.get('feedback_status_path') or '(missing)'}`",
        f"- Promotion decision: `{pointers.get('promotion_decision_path') or '(missing)'}`",
        f"- Promotion gate: `{pointers.get('promotion_gate_path') or '(missing)'}`",
        f"- Promotion gate note: `{pointers.get('promotion_gate_note_path') or '(missing)'}`",
        f"- Consultation index: `{pointers.get('consultation_index_path') or '(missing)'}`",
        f"- Innovation direction: `{pointers.get('innovation_direction_path') or '(missing)'}`",
        f"- Innovation decisions: `{pointers.get('innovation_decisions_path') or '(missing)'}`",
        f"- Interaction state: `topics/{topic_state['topic_slug']}/runtime/interaction_state.json`",
        f"- Operator console: `topics/{topic_state['topic_slug']}/runtime/operator_console.md`",
        f"- Conformance state: `topics/{topic_state['topic_slug']}/runtime/conformance_state.json`",
        f"- Conformance report: `topics/{topic_state['topic_slug']}/runtime/conformance_report.md`",
        f"- Selected route: `{interaction_state.get('closed_loop', {}).get('selected_route_path') or '(missing)'}`",
        f"- Execution task: `{interaction_state.get('closed_loop', {}).get('execution_task_path') or '(missing)'}`",
        f"- Returned result contract: `{interaction_state.get('closed_loop', {}).get('returned_result_path') or '(missing)'}`",
        f"- Trajectory log: `{interaction_state.get('closed_loop', {}).get('trajectory_log_path') or '(missing)'}`",
        f"- Failure classification: `{interaction_state.get('closed_loop', {}).get('failure_classification_path') or '(missing)'}`",
        f"- Capability protocol: `research/adapters/openclaw/SKILL_ADAPTATION_PROTOCOL.md`",
        f"- Conformance protocol: `research/knowledge-hub/AGENT_CONFORMANCE_PROTOCOL.md`",
        f"- Unfinished work: `{decision_surface.get('unfinished_work_path') or '(missing)'}`",
        f"- Next-action decision: `{decision_surface.get('next_action_decision_path') or '(missing)'}`",
        f"- Decision source: `{decision_surface.get('decision_source') or '(missing)'}`",
        f"- Decision mode: `{decision_surface.get('decision_mode') or '(missing)'}`",
        f"- Selected action: `{decision_surface.get('selected_action_id') or '(none)'}`",
        f"- Queue source: `{queue_surface.get('queue_source') or '(missing)'}`",
        f"- Declared L3 action contract: `{queue_surface.get('declared_contract_path') or '(missing)'}`", "",
        "## Research-mode governance", "",
        f"- Profile path: `{research_mode_profile.get('profile_path') or '(missing)'}`",
        f"- Profile label: `{research_mode_profile.get('label') or '(missing)'}`", "",
        "### Reproducibility expectations", ""])
    for item in research_mode_profile.get("reproducibility_expectations") or ["No explicit reproducibility expectation recorded."]:
        lines.append(f"- {item}")
    lines.extend(["", "### Human-readable notes", ""])
    for item in research_mode_profile.get("note_expectations") or ["No explicit note expectation recorded."]:
        lines.append(f"- {item}")
    lines.extend(["", "## L2 backend bridge snapshot", ""])
    if backend_bridges:
        for bridge in backend_bridges:
            lines.extend([
                f"- `{bridge.get('backend_id') or '(missing)'}` title=`{bridge.get('title') or '(missing)'}` type=`{bridge.get('backend_type') or '(missing)'}` status=`{bridge.get('status') or '(missing)'}` card_status=`{bridge.get('card_status') or '(missing)'}` sources=`{bridge.get('source_count', 0)}`",
                f"  card_path=`{bridge.get('card_path') or '(missing)'}`",
                f"  backend_root=`{bridge.get('backend_root') or '(missing)'}`",
                f"  artifact_kinds=`{', '.join(bridge.get('artifact_kinds') or []) or '(missing)'}`",
                f"  canonical_targets=`{', '.join(bridge.get('canonical_targets') or []) or '(missing)'}`",
                f"  l0_registration_script=`{bridge.get('l0_registration_script') or '(missing)'}`",
            ])
    else:
        lines.append("- None registered.")
    lines.extend(["", "## L2 promotion gate", "",
        f"- Status: `{promotion_gate.get('status') or 'not_requested'}`",
        f"- Candidate id: `{promotion_gate.get('candidate_id') or '(missing)'}`",
        f"- Candidate type: `{promotion_gate.get('candidate_type') or '(missing)'}`",
        f"- Backend id: `{promotion_gate.get('backend_id') or '(missing)'}`",
        f"- Target backend root: `{promotion_gate.get('target_backend_root') or '(missing)'}`",
        f"- Approved by: `{promotion_gate.get('approved_by') or '(pending)'}`",
        f"- Promoted units: `{', '.join(promotion_gate.get('promoted_units') or []) or '(none)'}`", "",
        "## Action queue", ""])
    for index, action in enumerate(queue, start=1):
        lines.append(f"{index}. [{action['action_type']}] {action['summary']} (auto_runnable={str(action['auto_runnable']).lower()})")
    return "\n".join(lines) + "\n"
