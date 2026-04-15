from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .l1_source_intake_support import (
    coalesce_l1_source_intake,
    derive_l1_conflict_intake,
    empty_l1_source_intake,
    l1_assumption_depth_summary_lines,
    l1_contradiction_summary_lines,
    l1_context_lines,
    l1_interpretation_focus_lines,
    l1_notation_tension_lines,
    l1_open_ambiguity_lines,
    l1_reading_depth_limit_lines,
    normalize_l1_source_intake,
    render_source_intelligence_markdown,
    source_intelligence_paths,
    source_intelligence_payload,
)
from .l1_vault_support import materialize_l1_vault
from .collaborator_profile_support import materialize_collaborator_profile_surface
from .mode_learning_support import materialize_mode_learning_surface
from .research_taste_support import (
    dashboard_research_taste_lines,
)
from .scratchpad_support import materialize_scratchpad_surface, scratchpad_dashboard_lines
from .topic_dashboard_surface_support import finalize_topic_shell_outputs, materialize_research_state_surfaces
from .research_trajectory_support import materialize_research_trajectory_surface
from .research_judgment_runtime_support import (
    dashboard_research_judgment_lines,
)
from .runtime_read_path_support import normalize_competing_hypotheses
from .runtime_projection_handler import write_topic_skill_projection
from .graph_analysis_tools import (
    build_graph_analysis_surface,
    graph_analysis_paths,
    render_graph_analysis_markdown,
    write_graph_analysis_history,
)
from .validation_review_service import analytical_cross_check_markdown_lines
from .topic_truth_root_support import compatibility_projection_path
def _read_json(path: Path) -> dict[str, Any] | None:
    target = path
    if not target.exists():
        compatibility_path = compatibility_projection_path(path)
        if compatibility_path is None or not compatibility_path.exists():
            return None
        target = compatibility_path
    return json.loads(target.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    target = path
    if not target.exists():
        compatibility_path = compatibility_projection_path(path)
        if compatibility_path is None or not compatibility_path.exists():
            return []
        target = compatibility_path
    rows: list[dict[str, Any]] = []
    for raw_line in target.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, ensure_ascii=True, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    compatibility_path = compatibility_projection_path(path)
    if compatibility_path is not None and compatibility_path != path:
        compatibility_path.parent.mkdir(parents=True, exist_ok=True)
        compatibility_path.write_text(rendered, encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    compatibility_path = compatibility_projection_path(path)
    if compatibility_path is not None and compatibility_path != path:
        compatibility_path.parent.mkdir(parents=True, exist_ok=True)
        compatibility_path.write_text(text, encoding="utf-8")


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-+", "-", lowered).strip("-")
    return lowered or "aitp-topic"


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _checkpoint_option_set(checkpoint_kind: str | None) -> tuple[list[dict[str, str]], int | None]:
    normalized = str(checkpoint_kind or "").strip()
    if normalized == "scope_ambiguity":
        return (
            [
                {
                    "key": "clarify_now",
                    "label": "Clarify now",
                    "description": "Fill the missing topic-intent fields before deeper execution continues.",
                },
                {
                    "key": "continue_with_deferred_fields",
                    "label": "Continue with deferred fields",
                    "description": "Proceed honestly with clarification deferred and visible in the topic state.",
                },
                {
                    "key": "branch_new_topic",
                    "label": "Branch new topic",
                    "description": "Split the current vague direction into a separate topic branch first.",
                },
            ],
            0,
        )
    if normalized == "promotion_approval":
        return (
            [
                {
                    "key": "approve_for_l2",
                    "label": "Approve for L2",
                    "description": "Allow reusable-knowledge writeback to proceed.",
                },
                {
                    "key": "reject_for_now",
                    "label": "Reject for now",
                    "description": "Keep the candidate out of L2 until the trust boundary is stronger.",
                },
                {
                    "key": "narrow_before_writeback",
                    "label": "Narrow before writeback",
                    "description": "Reduce scope and tighten the candidate before promotion is reconsidered.",
                },
            ],
            2,
        )
    if normalized == "execution_lane_confirmation":
        return (
            [
                {
                    "key": "stay_local",
                    "label": "Stay local",
                    "description": "Keep the next execution step in the current local lane.",
                },
                {
                    "key": "use_external_runtime",
                    "label": "Use external runtime",
                    "description": "Dispatch the next execution step to the planned external runtime or server lane.",
                },
                {
                    "key": "narrow_before_dispatch",
                    "label": "Narrow before dispatch",
                    "description": "Reduce cost or scope before any execution lane is confirmed.",
                },
            ],
            0,
        )
    if normalized == "contradiction_adjudication":
        return (
            [
                {
                    "key": "split_regimes",
                    "label": "Split regimes",
                    "description": "Treat the conflict as a regime split rather than one flattened result.",
                },
                {
                    "key": "downgrade_claim",
                    "label": "Downgrade claim",
                    "description": "Keep the route but weaken the current candidate claim.",
                },
                {
                    "key": "return_to_L0",
                    "label": "Return to L0",
                    "description": "Go back to source recovery before further interpretation.",
                },
            ],
            0,
        )
    if normalized == "benchmark_or_validation_route_choice":
        return (
            [
                {
                    "key": "benchmark_first",
                    "label": "Benchmark first",
                    "description": "Use the smallest honest benchmark route before deeper execution.",
                },
                {
                    "key": "execution_backed_validation",
                    "label": "Execution-backed validation",
                    "description": "Advance directly into the prepared execution-backed validation lane.",
                },
                {
                    "key": "pause_and_clarify_route",
                    "label": "Clarify route",
                    "description": "Pause and refine the validation route before choosing one lane.",
                },
            ],
            0,
        )
    if normalized == "resource_risk_limit_choice":
        return (
            [
                {
                    "key": "keep_small_and_safe",
                    "label": "Keep small and safe",
                    "description": "Stay within the smallest cost and risk envelope.",
                },
                {
                    "key": "allow_broader_budget",
                    "label": "Allow broader budget",
                    "description": "Permit a larger execution budget or system-size envelope.",
                },
                {
                    "key": "pause_until_limit_defined",
                    "label": "Pause for limit",
                    "description": "Do not expand until the budget or risk boundary is explicit.",
                },
            ],
            0,
        )
    if normalized == "novelty_direction_choice":
        return (
            [
                {
                    "key": "keep_current_branch",
                    "label": "Keep current branch",
                    "description": "Continue with the current novelty direction.",
                },
                {
                    "key": "redirect_novelty_target",
                    "label": "Redirect novelty",
                    "description": "Change the novelty target but keep the same topic branch.",
                },
                {
                    "key": "branch_new_direction",
                    "label": "Branch direction",
                    "description": "Fork the new novelty direction into a separate branch.",
                },
            ],
            0,
        )
    if normalized == "stop_continue_branch_redirect_decision":
        return (
            [
                {
                    "key": "continue",
                    "label": "Continue",
                    "description": "Keep the current topic moving on the active bounded route.",
                },
                {
                    "key": "branch",
                    "label": "Branch",
                    "description": "Split the next route into a new topic branch.",
                },
                {
                    "key": "redirect",
                    "label": "Redirect",
                    "description": "Change the active route inside the current topic.",
                },
                {
                    "key": "stop",
                    "label": "Stop",
                    "description": "Pause or stop the topic until explicitly resumed.",
                },
            ],
            0,
        )
    return ([], None)


def derive_open_gap_summary(
    self,
    *,
    topic_slug: str,
    candidate_rows: list[dict[str, Any]],
    pending_actions: list[dict[str, Any]],
    selected_pending_action: dict[str, Any] | None,
) -> dict[str, Any]:
    blockers: list[str] = []
    followup_gap_ids: list[str] = []
    followup_gap_writeback_rows = self._load_followup_gap_writeback_rows(topic_slug)
    capability_gap_active = any(
        str(row.get("action_type") or "").strip() == "skill_discovery" for row in pending_actions
    )
    for row in candidate_rows:
        candidate_id = str(row.get("candidate_id") or "").strip() or "candidate"
        for blocker in row.get("promotion_blockers") or []:
            text = str(blocker).strip()
            if text:
                blockers.append(f"{candidate_id}: {text}")
        if _as_bool(row.get("split_required")):
            blockers.append(f"{candidate_id}: split into narrower units before promotion.")
        if _as_bool(row.get("cited_recovery_required")):
            blockers.append(
                f"{candidate_id}: return to L0 to recover cited definitions, derivations, or prior-work context."
            )
        followup_gap_ids.extend(list(row.get("followup_gap_ids") or []))
    for row in followup_gap_writeback_rows:
        child_topic_slug = str(row.get("child_topic_slug") or "").strip() or "followup-child"
        return_status = str(row.get("return_status") or "").strip() or "returned_with_gap"
        summary = str(row.get("summary") or "").strip()
        blockers.append(
            f"{child_topic_slug}: unresolved child follow-up returned as `{return_status}` and still requires parent gap writeback."
        )
        if summary:
            blockers.append(f"{child_topic_slug}: {summary}")
        followup_gap_ids.extend(list(row.get("parent_gap_ids") or []))

    selected_action_type = str((selected_pending_action or {}).get("action_type") or "").strip()
    selected_action_summary = str((selected_pending_action or {}).get("summary") or "").strip().lower()
    requires_l0_return = any(
        needle in selected_action_summary
        for needle in ("source", "reference", "prior work", "background", "literature", "citation")
    ) or selected_action_type == "l0_source_expansion"
    requires_l0_return = requires_l0_return or any(
        "return to l0" in blocker.lower() or "prior-work" in blocker.lower() or "cited" in blocker.lower()
        for blocker in blockers
    )
    requires_l0_return = requires_l0_return or bool(followup_gap_writeback_rows)

    gap_items = self._dedupe_strings(blockers + [str(value) for value in followup_gap_ids if str(value).strip()])
    if requires_l0_return:
        status = "return_to_L0"
        summary = "Understanding or prior-work gaps are active. Recover sources through L0 before smoothing the topic in prose."
    elif gap_items:
        status = "open"
        summary = "Open gap packets or blockers remain. Keep them explicit and do not silently merge them into the narrative."
    elif capability_gap_active:
        status = "capability_gap"
        summary = "The main blocker is a capability/workflow gap. Resolve it explicitly through the runtime queue."
    else:
        status = "clear"
        summary = "No explicit gap packet is currently open."

    return {
        "topic_slug": topic_slug,
        "status": status,
        "gap_count": len(gap_items),
        "blockers": self._dedupe_strings(blockers),
        "followup_gap_ids": self._dedupe_strings(followup_gap_ids),
        "followup_gap_writeback_count": len(followup_gap_writeback_rows),
        "followup_gap_writeback_child_topics": self._dedupe_strings(
            [str(row.get("child_topic_slug") or "").strip() for row in followup_gap_writeback_rows if str(row.get("child_topic_slug") or "").strip()]
        ),
        "pending_action_summaries": self._dedupe_strings(
            [str(row.get("summary") or "").strip() for row in pending_actions if str(row.get("summary") or "").strip()]
        ),
        "requires_l0_return": requires_l0_return,
        "capability_gap_active": capability_gap_active,
        "summary": summary,
    }

def derive_idea_packet(
    self,
    *,
    topic_slug: str,
    updated_by: str,
    human_request: str | None,
    topic_state: dict[str, Any],
    interaction_state: dict[str, Any],
    existing_idea_packet: dict[str, Any],
    existing_research: dict[str, Any],
    existing_validation: dict[str, Any],
    research_contract: dict[str, Any],
    validation_contract: dict[str, Any],
    selected_pending_action: dict[str, Any] | None,
) -> dict[str, Any]:
    source_rows = _read_jsonl(self._l0_root(topic_slug) / "source_index.jsonl")
    request_text = (
        str(human_request or "").strip()
        or str(interaction_state.get("human_request") or "").strip()
    )
    actionable_request = self._request_looks_actionable(request_text)

    # 从 source 中蒸馏信息（新增功能）
    distilled = self._distill_from_sources(source_rows or [], topic_slug)

    distilled_initial_idea = str(distilled.get("distilled_initial_idea") or "").strip()
    distilled_novelty_target = str(distilled.get("distilled_novelty_target") or "").strip()
    distilled_first_validation_route = str(
        distilled.get("distilled_first_validation_route") or ""
    ).strip()
    initial_idea = self._coalesce_string(
        existing_idea_packet.get("initial_idea"),
        str(existing_research.get("question") or "").strip(),
        distilled_initial_idea,
        request_text,
    )
    novelty_target = self._coalesce_string(
        existing_idea_packet.get("novelty_target"),
        distilled_novelty_target,
    )
    non_goals = self._coalesce_list(
        existing_idea_packet.get("non_goals"),
        list(existing_research.get("non_goals") or []),
    )
    first_validation_route = self._coalesce_string(
        existing_idea_packet.get("first_validation_route"),
        str(existing_validation.get("verification_focus") or "").strip()
        or str(validation_contract.get("verification_focus") or "").strip()
        or distilled_first_validation_route
        or str((selected_pending_action or {}).get("summary") or "").strip()
        or "Define the first bounded validation route before deeper execution.",
    )
    initial_evidence_bar = self._coalesce_string(
        existing_idea_packet.get("initial_evidence_bar"),
        str(existing_validation.get("acceptance_rule") or "").strip()
        or str(validation_contract.get("acceptance_rule") or "").strip()
        or "Require a durable first validation artifact before advancing the topic.",
    )

    missing_fields: list[str] = []
    if not initial_idea:
        missing_fields.append("initial_idea")
    if not novelty_target:
        missing_fields.append("novelty_target")
    if not non_goals:
        missing_fields.append("non_goals")
    if not first_validation_route:
        missing_fields.append("first_validation_route")
    if not initial_evidence_bar:
        missing_fields.append("initial_evidence_bar")

    execution_context_signals: list[str] = []
    if str(topic_state.get("latest_run_id") or "").strip():
        execution_context_signals.append("latest_run_id")
    if source_rows and (
        distilled_initial_idea
        or distilled_novelty_target
        or distilled_first_validation_route
    ):
        execution_context_signals.append("l0_sources")
    if str((selected_pending_action or {}).get("action_id") or "").strip():
        execution_context_signals.append("selected_action")
    explicit_shell_context = bool(
        str(existing_research.get("question") or "").strip()
        or list(existing_research.get("scope") or [])
        or list(existing_research.get("deliverables") or [])
        or str(existing_validation.get("verification_focus") or "").strip()
        or list(existing_validation.get("required_checks") or [])
    )
    if explicit_shell_context:
        execution_context_signals.append("existing_shell_contracts")

    existing_status = str(existing_idea_packet.get("status") or "").strip()
    fully_clarified_packet = bool(
        initial_idea
        and novelty_target
        and non_goals
        and first_validation_route
        and initial_evidence_bar
    )
    if existing_status == "deferred":
        status = existing_status
    elif execution_context_signals:
        status = "approved_for_execution"
    elif fully_clarified_packet:
        status = "approved_for_execution"
    elif initial_idea and first_validation_route and initial_evidence_bar and actionable_request:
        status = "approved_for_execution"
    else:
        status = "needs_clarification"

    status_reason = (
        "Approved for execution because durable topic context already exists."
        if status == "approved_for_execution" and execution_context_signals
        else (
            "Approved for execution because the idea packet now specifies a novelty target, first validation route, and evidence bar."
            if status == "approved_for_execution" and fully_clarified_packet
            else (
                "Approved for execution because the request already specifies a concrete initial lane and evidence bar."
                if status == "approved_for_execution"
                else "Needs clarification because the topic is not yet specific enough to justify substantive execution."
            )
        )
    )

    clarification_questions: list[str] = []
    if status == "needs_clarification":
        if not actionable_request:
            clarification_questions.append(
                "Should AITP first do scoped problem definition, literature scoping, benchmark reproduction, or derivation planning?"
            )
        if "initial_idea" in missing_fields:
            clarification_questions.append(
                "What is the idea in one sentence, including the physical object, regime, and intended question?"
            )
        if "novelty_target" in missing_fields:
            clarification_questions.append(
                "What exact novelty target should count as success beyond routine reproduction or literature summary?"
            )
        if "non_goals" in missing_fields:
            clarification_questions.append(
                "What should this topic explicitly not try to solve in the first lane?"
            )
        if "first_validation_route" in missing_fields:
            clarification_questions.append(
                "What is the first validation lane: literature scoping, analytic derivation, benchmark reproduction, or numerical pilot?"
            )
        if "initial_evidence_bar" in missing_fields:
            clarification_questions.append(
                "What minimum evidence bar should justify continuing beyond the first bounded step?"
            )

    return {
        "topic_slug": topic_slug,
        "status": status,
        "status_reason": status_reason,
        "initial_idea": initial_idea,
        "novelty_target": novelty_target,
        "non_goals": non_goals,
        "first_validation_route": first_validation_route,
        "initial_evidence_bar": initial_evidence_bar,
        "missing_fields": self._dedupe_strings(missing_fields),
        "clarification_questions": self._dedupe_strings(clarification_questions),
        "execution_context_signals": self._dedupe_strings(execution_context_signals),
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }

def derive_operator_checkpoint(
    self,
    *,
    topic_slug: str,
    updated_by: str,
    existing_checkpoint: dict[str, Any],
    idea_packet: dict[str, Any],
    research_contract: dict[str, Any],
    validation_contract: dict[str, Any],
    promotion_gate: dict[str, Any],
    selected_pending_action: dict[str, Any] | None,
    decision_surface: dict[str, Any],
    dashboard_path: Path,
    idea_packet_paths: dict[str, Path],
    research_paths: dict[str, Path],
    validation_paths: dict[str, Path],
    execution_task: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    selected_action_id = str((selected_pending_action or {}).get("action_id") or "").strip()
    selected_action_type = str((selected_pending_action or {}).get("action_type") or "").strip()
    selected_action_summary = str((selected_pending_action or {}).get("summary") or "").strip()
    selected_action_summary_lower = selected_action_summary.lower()
    promotion_status = str(promotion_gate.get("status") or "not_requested").strip()
    control_note_path = str(decision_surface.get("control_note_path") or "").strip()
    execution_task_payload = dict(execution_task or {})
    execution_task_note_path = self._normalize_artifact_path(self._runtime_root(topic_slug) / "execution_task.md")
    execution_task_needs_human_confirm = bool(execution_task_payload.get("needs_human_confirm"))
    execution_task_auto_dispatch_allowed = bool(execution_task_payload.get("auto_dispatch_allowed"))
    checkpoint_kind: str | None = None
    question = ""
    required_response = ""
    blocker_summary: list[str] = []
    evidence_refs: list[str] = []
    response_channels: list[str] = []

    if str(idea_packet.get("status") or "").strip() == "needs_clarification":
        checkpoint_kind = "scope_ambiguity"
        question = "AITP needs the initial topic intent clarified before substantive execution can continue."
        required_response = (
            "Fill the idea packet with a novelty target, non-goals, first validation route, and initial evidence bar."
        )
        blocker_summary = list(idea_packet.get("clarification_questions") or []) or [
            "Complete the missing intent fields in the idea packet."
        ]
        evidence_refs = [
            self._relativize(idea_packet_paths["note"]),
            self._relativize(research_paths["note"]),
            self._relativize(validation_paths["note"]),
        ]
        response_channels = [
            self._relativize(idea_packet_paths["note"]),
            self._relativize(research_paths["note"]),
            self._relativize(validation_paths["note"]),
        ]
    elif promotion_status in {"requested", "pending_human_approval"}:
        checkpoint_kind = "promotion_approval"
        candidate_id = str(promotion_gate.get("candidate_id") or "").strip() or "(missing)"
        backend_id = str(promotion_gate.get("backend_id") or "").strip() or "(missing)"
        question = f"Is `{candidate_id}` ready to save as reusable knowledge in `{backend_id}`?"
        required_response = (
            "Say whether this is ready to save as reusable knowledge, should be rejected, "
            "or should be narrowed before writeback continues."
        )
        blocker_summary = self._dedupe_strings(
            list(promotion_gate.get("promotion_blockers") or [])
            or ["A reusable-knowledge decision is waiting for an explicit human response."]
        )
        evidence_refs = self._dedupe_strings(
            [
                self._relativize(self._promotion_gate_paths(topic_slug)["json"]),
                self._relativize(self._promotion_gate_paths(topic_slug)["note"]),
                self._relativize(dashboard_path),
            ]
        )
        response_channels = [
            self._relativize(self._promotion_gate_paths(topic_slug)["note"]),
            self._relativize(dashboard_path),
        ]
    elif (
        selected_action_type in {"dispatch_execution_task", "await_execution_result"}
        and execution_task_payload
        and (execution_task_needs_human_confirm or not execution_task_auto_dispatch_allowed)
    ):
        checkpoint_kind = "execution_lane_confirmation"
        question = "AITP has prepared an L4 execution plan and needs the operator to confirm the execution lane before dispatch."
        required_response = (
            "Confirm whether this should stay local, use an external runtime/server lane, switch to Lean/formal work, or be narrowed to a cheaper chosen approach."
        )
        blocker_summary = self._dedupe_strings(
            [
                selected_action_summary or "Execution dispatch is waiting for operator confirmation.",
                (
                    f"Planned runtime `{execution_task_payload.get('assigned_runtime') or '(missing)'}`, "
                    f"executor `{execution_task_payload.get('executor_kind') or '(missing)'}`, "
                    f"surface `{execution_task_payload.get('surface') or '(missing)'}`."
                ),
                "Do not dispatch the execution task until the lane, runtime target, and resource boundary are confirmed.",
            ]
        )
        evidence_refs = self._dedupe_strings(
            [
                self._normalize_artifact_path(execution_task_note_path) or "",
                self._relativize(validation_paths["note"]),
                self._relativize(dashboard_path),
            ]
        )
        response_channels = self._dedupe_strings(
            [
                self._normalize_artifact_path(execution_task_note_path) or "",
                self._relativize(validation_paths["note"]),
                self._relativize(dashboard_path),
            ]
        )
    elif any(needle in selected_action_summary_lower for needle in ("contradiction", "conflict", "regime mismatch")):
        checkpoint_kind = "contradiction_adjudication"
        question = "AITP found a contradiction-style blocker and needs the operator to choose how to judge this."
        required_response = "Choose whether to split regimes, downgrade the claim, or restart from source intake."
        blocker_summary = [
            selected_action_summary or "An unresolved contradiction/regime conflict is active.",
            "Do not let the queue guess how to judge this without an explicit operator choice.",
        ]
        evidence_refs = [
            self._relativize(self._gap_map_path(topic_slug)),
            self._relativize(validation_paths["note"]),
            self._relativize(dashboard_path),
        ]
        response_channels = [
            self._relativize(self._gap_map_path(topic_slug)),
            self._relativize(validation_paths["note"]),
        ]
    elif (
        selected_action_type in {"select_validation_route"}
        or any(
            needle in selected_action_summary_lower
            for needle in ("validation route", "verification route", "benchmark", "selected route")
        )
    ):
        checkpoint_kind = "benchmark_or_validation_route_choice"
        question = "AITP needs an operator decision on the next benchmark or validation lane."
        required_response = "Choose the initial benchmark/validation route that should govern the next bounded step."
        blocker_summary = [
            selected_action_summary or "Validation-route choice remains unresolved.",
            "The active validation contract needs an explicit route choice before deeper execution.",
        ]
        evidence_refs = [
            self._relativize(validation_paths["note"]),
            self._relativize(dashboard_path),
        ]
        response_channels = [self._relativize(validation_paths["note"])]
    elif any(
        needle in selected_action_summary_lower
        for needle in ("resource limit", "risk limit", "compute budget", "system size", "larger-system", "budget")
    ):
        checkpoint_kind = "resource_risk_limit_choice"
        question = "AITP needs an operator decision on the acceptable resource or risk limit for the next lane."
        required_response = "State the permitted budget, system-size ceiling, or risk boundary before the next step expands."
        blocker_summary = [
            selected_action_summary or "The next lane requires an explicit resource/risk limit.",
        ]
        evidence_refs = [
            self._relativize(dashboard_path),
            self._relativize(validation_paths["note"]),
        ]
        response_channels = [self._relativize(dashboard_path)]
    elif any(
        needle in selected_action_summary_lower
        for needle in ("innovation direction", "novelty direction", "direction choice", "focus direction")
    ):
        checkpoint_kind = "novelty_direction_choice"
        question = "AITP needs an operator decision on the novelty direction before continuing."
        required_response = "Clarify which innovation target should dominate the current topic branch."
        blocker_summary = [
            selected_action_summary or "The current novelty direction remains ambiguous.",
        ]
        evidence_refs = [
            self._relativize(research_paths["note"]),
            self._relativize(dashboard_path),
        ]
        if control_note_path:
            evidence_refs.append(self._normalize_artifact_path(control_note_path) or control_note_path)
        response_channels = self._dedupe_strings(
            [self._normalize_artifact_path(control_note_path) or "", self._relativize(research_paths["note"])]
        )
    elif any(
        needle in selected_action_summary_lower
        for needle in ("continue or branch", "branch or redirect", "redirect decision", "stop or continue")
    ):
        checkpoint_kind = "stop_continue_branch_redirect_decision"
        question = "AITP needs an explicit stop/continue/branch/redirect decision from the operator."
        required_response = "Record whether the topic should continue, pause, branch, stop, or redirect."
        blocker_summary = [selected_action_summary or "The loop is waiting for an explicit operator steering decision."]
        evidence_refs = self._dedupe_strings(
            [self._normalize_artifact_path(control_note_path) or "", self._relativize(dashboard_path)]
        )
        response_channels = self._dedupe_strings([self._normalize_artifact_path(control_note_path) or ""])

    now = _now_iso()
    existing_status = str(existing_checkpoint.get("status") or "").strip()
    existing_id = str(existing_checkpoint.get("checkpoint_id") or "").strip()
    existing_fingerprint = str(existing_checkpoint.get("trigger_fingerprint") or "").strip()

    if checkpoint_kind is None:
        payload = dict(existing_checkpoint or {})
        payload.setdefault("checkpoint_id", f"checkpoint:{topic_slug}:none")
        payload["topic_slug"] = topic_slug
        payload["run_id"] = str(existing_checkpoint.get("run_id") or "")
        payload["checkpoint_kind"] = None
        payload["status"] = "cancelled"
        payload["active"] = False
        payload["trigger_fingerprint"] = ""
        payload["question"] = "No active operator checkpoint is currently blocking execution."
        payload["required_response"] = "No operator response is currently required."
        payload["response_channels"] = []
        payload["blocker_summary"] = []
        payload["evidence_refs"] = []
        payload["options"] = []
        payload["default_option_index"] = None
        payload["selected_action_id"] = selected_action_id or None
        payload["selected_action_summary"] = selected_action_summary or None
        payload["answer"] = payload.get("answer")
        payload["requested_at"] = payload.get("requested_at")
        payload["requested_by"] = payload.get("requested_by")
        payload["answered_at"] = payload.get("answered_at")
        payload["answered_by"] = payload.get("answered_by")
        payload["updated_at"] = now if existing_status in {"requested", "answered"} else payload.get("updated_at") or now
        payload["updated_by"] = updated_by
        return payload, None

    checkpoint_id = f"checkpoint:{topic_slug}:{_slugify(checkpoint_kind)}"
    trigger_fingerprint = "|".join(
        [
            checkpoint_kind,
            selected_action_id,
            promotion_status,
            ",".join(self._dedupe_strings(list(idea_packet.get("missing_fields") or []))),
            selected_action_summary,
        ]
    )
    payload = {
        "checkpoint_id": checkpoint_id,
        "topic_slug": topic_slug,
        "run_id": str(research_contract.get("run_id") or ""),
        "checkpoint_kind": checkpoint_kind,
        "status": "requested",
        "active": True,
        "trigger_fingerprint": trigger_fingerprint,
        "question": question,
        "required_response": required_response,
        "response_channels": self._dedupe_strings(response_channels),
        "blocker_summary": self._dedupe_strings(blocker_summary),
        "evidence_refs": self._dedupe_strings(evidence_refs),
        "options": _checkpoint_option_set(checkpoint_kind)[0],
        "default_option_index": _checkpoint_option_set(checkpoint_kind)[1],
        "selected_action_id": selected_action_id or None,
        "selected_action_summary": selected_action_summary or None,
        "answer": None,
        "requested_at": now,
        "requested_by": updated_by,
        "answered_at": None,
        "answered_by": None,
        "updated_at": now,
        "updated_by": updated_by,
    }
    superseded_payload: dict[str, Any] | None = None
    if existing_id == checkpoint_id and existing_fingerprint == trigger_fingerprint:
        if existing_status in {"requested", "answered"}:
            payload["status"] = existing_status
            payload["active"] = existing_status == "requested"
            payload["answer"] = existing_checkpoint.get("answer")
            payload["requested_at"] = existing_checkpoint.get("requested_at") or now
            payload["requested_by"] = existing_checkpoint.get("requested_by") or updated_by
            payload["answered_at"] = existing_checkpoint.get("answered_at")
            payload["answered_by"] = existing_checkpoint.get("answered_by")
            payload["updated_at"] = existing_checkpoint.get("updated_at") or now
            payload["updated_by"] = existing_checkpoint.get("updated_by") or updated_by
    elif existing_status in {"requested", "answered"} and existing_id and existing_id != checkpoint_id:
        superseded_payload = dict(existing_checkpoint)
        superseded_payload["status"] = "superseded"
        superseded_payload["active"] = False
        superseded_payload["updated_at"] = now
        superseded_payload["updated_by"] = updated_by
    return payload, superseded_payload

def render_topic_dashboard_markdown(
    self,
    *,
    topic_slug: str,
    topic_state: dict[str, Any],
    source_intelligence: dict[str, Any],
    graph_analysis: dict[str, Any],
    runtime_focus: dict[str, Any],
    selected_pending_action: dict[str, Any] | None,
    pending_actions: list[dict[str, Any]],
    idea_packet: dict[str, Any],
    operator_checkpoint: dict[str, Any],
    topic_status_explainability: dict[str, Any],
    research_contract: dict[str, Any],
    validation_contract: dict[str, Any],
    validation_review_bundle: dict[str, Any],
    promotion_readiness: dict[str, Any],
    open_gap_summary: dict[str, Any],
    strategy_memory: dict[str, Any],
    statement_compilation: dict[str, Any],
    topic_skill_projection: dict[str, Any],
    topic_completion: dict[str, Any],
    lean_bridge: dict[str, Any],
    dependency_state: dict[str, Any],
) -> str:
    selected_action_summary = str(runtime_focus.get("next_action_summary") or "").strip()
    if not selected_action_summary:
        selected_action_summary = str((selected_pending_action or {}).get("summary") or "").strip() or "(none)"
    l0_source_handoff = runtime_focus.get("l0_source_handoff") or {}
    current_route_choice = topic_status_explainability.get("current_route_choice") or {}
    last_evidence_return = topic_status_explainability.get("last_evidence_return") or {}
    active_human_need = topic_status_explainability.get("active_human_need") or {}
    research_judgment = topic_status_explainability.get("research_judgment") or {}
    research_taste = topic_status_explainability.get("research_taste") or {}
    scratchpad = topic_status_explainability.get("scratchpad") or {}
    blocker_summary = runtime_focus.get("blocker_summary") or topic_status_explainability.get("blocker_summary") or []
    l1_source_intake = research_contract.get("l1_source_intake") or {}
    lines = [
        "# Topic dashboard",
        "",
        f"- Topic slug: `{topic_slug}`",
        f"- Title: `{research_contract.get('title') or self._topic_display_title(topic_slug)}`",
        f"- Resume stage: `{runtime_focus.get('resume_stage') or topic_state.get('resume_stage') or '(missing)'}`",
        f"- Last materialized stage: `{runtime_focus.get('last_materialized_stage') or topic_state.get('last_materialized_stage') or '(missing)'}`",
        f"- Latest run id: `{topic_state.get('latest_run_id') or '(missing)'}`",
        f"- Research mode: `{research_contract.get('research_mode') or topic_state.get('research_mode') or '(missing)'}`",
        f"- Current bounded action: `{selected_action_summary}`",
        f"- Pending action count: `{len(pending_actions)}`",
        "",
        "## Active question",
        "",
        research_contract.get("question") or "(missing)",
        "",
        "## Why this topic is here",
        "",
        runtime_focus.get("why_this_topic_is_here")
        or topic_status_explainability.get("why_this_topic_is_here")
        or "(missing)",
        "",
        "## Current status",
        "",
        f"- Idea packet: `{idea_packet.get('status') or '(missing)'}`",
        f"- Operator checkpoint: `{operator_checkpoint.get('status') or '(missing)'}`",
        f"- Research contract: `{research_contract.get('status') or '(missing)'}`",
        f"- Validation contract: `{validation_contract.get('status') or '(missing)'}`",
        f"- Validation review bundle: `{validation_review_bundle.get('status') or '(missing)'}`",
        f"- Promotion readiness: `{promotion_readiness.get('status') or '(missing)'}`",
        f"- Gap status: `{open_gap_summary.get('status') or '(missing)'}`",
        f"- Dependencies: `{runtime_focus.get('dependency_status') or dependency_state.get('status') or '(missing)'}`",
        f"- Topic completion: `{topic_completion.get('status') or '(missing)'}`",
        f"- Statement compilation: `{statement_compilation.get('status') or '(missing)'}`",
        f"- Lean bridge: `{lean_bridge.get('status') or '(missing)'}`",
        "",
        "## Dependencies",
        "",
        f"- Status: `{runtime_focus.get('dependency_status') or dependency_state.get('status') or '(missing)'}`",
        f"- Blocked by: `{', '.join(dependency_state.get('blocked_by') or []) or '(none)'}`",
        "",
        f"{runtime_focus.get('dependency_summary') or dependency_state.get('summary') or '(none)'}",
        "",
        "## Idea packet summary",
        "",
        f"- Gate status: `{idea_packet.get('status') or '(missing)'}`",
        f"- First validation route: {idea_packet.get('first_validation_route') or '(missing)'}",
        f"- Initial evidence bar: {idea_packet.get('initial_evidence_bar') or '(missing)'}",
        f"- Missing fields: `{', '.join(idea_packet.get('missing_fields') or []) or '(none)'}`",
        "",
        idea_packet.get("status_reason") or "(missing)",
        "",
        "## Active operator checkpoint",
        "",
        f"- Status: `{operator_checkpoint.get('status') or '(missing)'}`",
        f"- Kind: `{operator_checkpoint.get('checkpoint_kind') or '(none)'}`",
        f"- Open next: `{operator_checkpoint.get('note_path') or '(missing)'}`",
        "",
        operator_checkpoint.get("question") or "(none)",
        "",
        "## Current route choice",
        "",
        f"- Decision source: `{current_route_choice.get('decision_source') or '(missing)'}`",
        f"- Queue source: `{current_route_choice.get('queue_source') or '(missing)'}`",
        f"- Selected action id: `{current_route_choice.get('selected_action_id') or '(none)'}`",
        f"- Selected action type: `{current_route_choice.get('selected_action_type') or '(none)'}`",
        f"- Selected action auto-runnable: `{str(bool(current_route_choice.get('selected_action_auto_runnable'))).lower()}`",
        f"- Next-action decision note: `{current_route_choice.get('next_action_decision_note_path') or '(missing)'}`",
        f"- Selected validation route: `{current_route_choice.get('selected_validation_route_path') or '(missing)'}`",
        "",
        f"{current_route_choice.get('selected_action_summary') or '(none)'}",
        "",
        *dashboard_research_judgment_lines(research_judgment),
        *dashboard_research_taste_lines(research_taste),
        *scratchpad_dashboard_lines(scratchpad),
        "## Last evidence return",
        "",
        f"- Status: `{last_evidence_return.get('status') or '(missing)'}`",
        f"- Kind: `{runtime_focus.get('last_evidence_kind') or last_evidence_return.get('kind') or '(missing)'}`",
        f"- Record id: `{last_evidence_return.get('record_id') or '(none)'}`",
        f"- Recorded at: `{last_evidence_return.get('recorded_at') or '(unknown)'}`",
        f"- Path: `{last_evidence_return.get('path') or '(missing)'}`",
        "",
        f"{runtime_focus.get('last_evidence_summary') or last_evidence_return.get('summary') or '(none)'}",
        "",
        "## Active human need",
        "",
        f"- Status: `{runtime_focus.get('human_need_status') or active_human_need.get('status') or '(missing)'}`",
        f"- Kind: `{runtime_focus.get('human_need_kind') or active_human_need.get('kind') or '(missing)'}`",
        f"- Path: `{active_human_need.get('path') or '(missing)'}`",
        "",
        f"{runtime_focus.get('human_need_summary') or active_human_need.get('summary') or '(none)'}",
        "",
        "## Source intelligence",
        "",
        f"- Canonical source ids: `{', '.join(source_intelligence.get('canonical_source_ids') or []) or '(none)'}`",
        f"- Citation edge count: `{len(source_intelligence.get('citation_edges') or [])}`",
        f"- Neighbor signal count: `{source_intelligence.get('neighbor_signal_count') or 0}`",
        f"- Cross-topic matches: `{source_intelligence.get('cross_topic_match_count') or 0}`",
        "",
        source_intelligence.get("summary") or "(missing)",
        "",
        "## Graph analysis",
        "",
        f"- Connection count: `{((graph_analysis.get('summary') or {}).get('connection_count') or 0)}`",
        f"- Question count: `{((graph_analysis.get('summary') or {}).get('question_count') or 0)}`",
        f"- History length: `{((graph_analysis.get('summary') or {}).get('history_length') or 0)}`",
        f"- Note path: `{graph_analysis.get('note_path') or '(missing)'}`",
        "",
        "## L1 intake honesty",
        "",
    ]
    if l0_source_handoff:
        lines[730:730] = [
            "## L0 source handoff",
            "",
            f"- Status: `{l0_source_handoff.get('status') or '(missing)'}`",
            f"- Summary: {l0_source_handoff.get('summary') or '(missing)'}",
            f"- Primary lane: `{l0_source_handoff.get('primary_path') or '(missing)'}`",
            f"- Use when: {l0_source_handoff.get('primary_when') or '(missing)'}",
            "",
            "### Alternate entries",
            "",
        ] + [
            f"- `{row.get('path') or '(missing)'}`: {row.get('when') or '(missing)'}"
            if isinstance(row, dict)
            else f"- {row}"
            for row in (l0_source_handoff.get("alternate_entries") or ["(none)"])
        ] + [
            "",
        ]
    for item in graph_analysis.get("connections") or ["(none)"]:
        if item == (graph_analysis.get("connections") or [None])[0]:
            lines.extend(["### Graph connections", ""])
        if isinstance(item, dict):
            lines.append(
                f"- `{item.get('kind') or '(missing)'}` `{item.get('bridge_label') or '(missing)'}`: "
                f"{item.get('detail') or '(missing)'}"
            )
        else:
            lines.append(f"- {item}")
    for item in graph_analysis.get("questions") or ["(none)"]:
        if item == (graph_analysis.get("questions") or [None])[0]:
            lines.extend(["", "### Graph question seeds", ""])
        if isinstance(item, dict):
            lines.append(
                f"- `{item.get('question_type') or '(missing)'}` `{item.get('bridge_label') or '(missing)'}`: "
                f"{item.get('question') or '(missing)'}"
            )
        else:
            lines.append(f"- {item}")
    diff = graph_analysis.get("diff") or {}
    lines.extend(
        [
            "",
            "### Graph diff",
            "",
            f"- Added nodes: `{((diff.get('added') or {}).get('node_count') or 0)}`",
            f"- Removed nodes: `{((diff.get('removed') or {}).get('node_count') or 0)}`",
            f"- Added labels: `{', '.join((diff.get('added') or {}).get('node_labels') or []) or '(none)'}`",
            f"- Removed labels: `{', '.join((diff.get('removed') or {}).get('node_labels') or []) or '(none)'}`",
            "",
        ]
    )
    for item in l1_assumption_depth_summary_lines(l1_source_intake) or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "### Reading-depth limits", ""])
    for item in l1_reading_depth_limit_lines(l1_source_intake) or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "### Contradiction candidates", ""])
    for item in l1_contradiction_summary_lines(l1_source_intake) or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "### Notation-alignment tension", ""])
    for item in l1_notation_tension_lines(l1_source_intake) or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## Validation review bundle",
        "",
        f"- Status: `{validation_review_bundle.get('status') or '(missing)'}`",
        f"- Primary kind: `{validation_review_bundle.get('primary_review_kind') or '(missing)'}`",
        f"- Note path: `{validation_review_bundle.get('note_path') or '(missing)'}`",
        "",
        f"{validation_review_bundle.get('summary') or '(missing)'}",
        "",
        "## Blocker summary",
        "",
    ])
    lines.extend(analytical_cross_check_markdown_lines(validation_review_bundle.get("analytical_cross_check_surface") or {}))
    if validation_review_bundle.get("analytical_cross_check_surface"):
        lines.append("")
    for item in blocker_summary or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## Promotion readiness summary",
        "",
        promotion_readiness.get("summary") or "(missing)",
        "",
        "## Open gap summary",
        "",
        open_gap_summary.get("summary") or "(missing)",
        "",
        "## Strategy memory",
        "",
        f"- Status: `{strategy_memory.get('status') or '(missing)'}`",
        f"- Lane: `{strategy_memory.get('lane') or '(missing)'}`",
        f"- Row count: `{strategy_memory.get('row_count') or 0}`",
        f"- Relevant count: `{strategy_memory.get('relevant_count') or 0}`",
        f"- Latest path: `{strategy_memory.get('latest_path') or '(none)'}`",
        "",
        strategy_memory.get("summary") or "(missing)",
        "",
        "## Topic skill projection",
        "",
        f"- Status: `{topic_skill_projection.get('status') or '(missing)'}`",
        f"- Projection id: `{topic_skill_projection.get('id') or '(missing)'}`",
        f"- Projection note: `{topic_skill_projection.get('note_path') or '(missing)'}`",
        f"- Intended L2 target: `{topic_skill_projection.get('intended_l2_target') or '(none)'}`",
        "",
        topic_skill_projection.get("summary") or "(missing)",
        "",
        "## Topic completion summary",
        "",
        topic_completion.get("summary") or "(missing)",
        "",
        "## Statement compilation summary",
        "",
        statement_compilation.get("summary") or "(missing)",
        "",
        "## Lean bridge summary",
        "",
        lean_bridge.get("summary") or "(missing)",
        "",
    ])
    for item in strategy_memory.get("guidance") or []:
        if item == (strategy_memory.get("guidance") or [None])[0]:
            lines.extend(["## Strategy guidance", ""])
        lines.append(f"- {item}")
    for item in topic_skill_projection.get("required_first_routes") or []:
        if item == (topic_skill_projection.get("required_first_routes") or [None])[0]:
            lines.extend(["", "## Projection route guidance", ""])
        lines.append(f"- {item}")
    if source_intelligence.get("source_neighbors"):
        lines.extend(["", "## Source neighbors", ""])
        for row in source_intelligence.get("source_neighbors") or []:
            lines.append(f"- `{row.get('source_id') or '(missing)'}` ~ `{row.get('neighbor_source_id') or '(missing)'}` via `{row.get('relation_kind') or '(missing)'}`")
    fidelity_summary = source_intelligence.get("fidelity_summary") or {}
    lines.extend(["", "## Source fidelity", "", f"- Strongest=`{fidelity_summary.get('strongest_tier') or 'unknown'}`; Weakest=`{fidelity_summary.get('weakest_tier') or 'unknown'}`; Counts=`{', '.join(f'{key}={value}' for key, value in (fidelity_summary.get('counts_by_tier') or {}).items()) or '(none)'}`"])
    lines.extend([
        "",
        "## Immediate next actions",
        "",
    ])
    for row in pending_actions[:8] or [{"summary": "(none)"}]:
        lines.append(
            f"- [{str(row.get('action_type') or 'unknown')}] {str(row.get('summary') or '(missing)')}"
        )
    lines.extend(
        [
            "",
            "## Operating rule",
            "",
            "- If a definition, proof dependency, or prior-work comparison is missing, return to L0 and persist the recovery artifacts before continuing.",
            "- Keep the research and validation contracts synchronized with any scope change.",
        ]
    )
    return "\n".join(lines) + "\n"

def compute_topic_completion_payload(
    self,
    *,
    topic_slug: str,
    run_id: str | None,
    candidate_rows: list[dict[str, Any]],
    updated_by: str,
) -> dict[str, Any]:
    followup_rows = self._load_followup_subtopic_rows(topic_slug)
    reintegration_rows = self._load_followup_reintegration_rows(topic_slug)
    promotion_gate = self._load_promotion_gate(topic_slug) or {}
    gate_status = str(promotion_gate.get("status") or "").strip()
    policy = self._load_runtime_policy().get("followup_subtopic_policy") or {}
    unresolved_statuses = {
        str(value).strip()
        for value in (policy.get("unresolved_return_statuses") or [])
        if str(value).strip()
    }
    unresolved_statuses.discard("pending_reentry")

    regression_question_ids: list[str] = []
    oracle_ids: list[str] = []
    regression_run_ids: list[str] = []
    promotion_ready_candidate_ids: list[str] = []
    blocked_candidate_ids: list[str] = []
    open_gap_ids: list[str] = []
    blockers: list[str] = []
    candidate_ids: list[str] = []

    for row in candidate_rows:
        candidate_id = str(row.get("candidate_id") or "").strip()
        if candidate_id:
            candidate_ids.append(candidate_id)
        regression_question_ids.extend(list(row.get("supporting_regression_question_ids") or []))
        oracle_ids.extend(list(row.get("supporting_oracle_ids") or []))
        regression_run_ids.extend(list(row.get("supporting_regression_run_ids") or []))
        open_gap_ids.extend(list(row.get("followup_gap_ids") or []))
        open_gap_ids.extend(list(row.get("parent_gap_ids") or []))
        if str(row.get("topic_completion_status") or "") == "promotion-ready":
            promotion_ready_candidate_ids.append(candidate_id)
        if (
            list(row.get("promotion_blockers") or [])
            or _as_bool(row.get("split_required"))
            or _as_bool(row.get("cited_recovery_required"))
        ):
            blocked_candidate_ids.append(candidate_id)
        for blocker in row.get("promotion_blockers") or []:
            text = str(blocker).strip()
            if text:
                blockers.append(f"{candidate_id or 'candidate'}: {text}")
        if _as_bool(row.get("split_required")):
            blockers.append(f"{candidate_id or 'candidate'}: split required before promotion.")
        if _as_bool(row.get("cited_recovery_required")):
            blockers.append(
                f"{candidate_id or 'candidate'}: cited-source or prior-work recovery must return through L0."
            )

    reintegrated_children = {
        str(row.get("child_topic_slug") or "").strip()
        for row in reintegration_rows
        if str(row.get("child_topic_slug") or "").strip()
    }
    unresolved_followup_child_topics: list[str] = []
    returned_with_gap_child_topics: list[str] = []
    for row in followup_rows:
        child_topic_slug = str(row.get("child_topic_slug") or "").strip()
        if not child_topic_slug:
            continue
        return_packet_path = str(row.get("return_packet_path") or "").strip()
        return_packet = _read_json(Path(return_packet_path)) if return_packet_path else None
        return_status = str((return_packet or {}).get("return_status") or row.get("status") or "").strip()
        if child_topic_slug in reintegrated_children or str(row.get("status") or "") == "reintegrated":
            continue
        if return_status in unresolved_statuses or str(row.get("status") or "") == "returned_with_gap":
            returned_with_gap_child_topics.append(child_topic_slug)
            blockers.append(f"{child_topic_slug}: returned from follow-up with unresolved gaps.")
            continue
        if return_status in {"spawned", "pending_reentry", ""} or str(row.get("status") or "") == "spawned":
            unresolved_followup_child_topics.append(child_topic_slug)
            blockers.append(f"{child_topic_slug}: follow-up child topic not yet reintegrated.")

    regression_question_ids = self._dedupe_strings(regression_question_ids)
    oracle_ids = self._dedupe_strings(oracle_ids)
    regression_run_ids = self._dedupe_strings(regression_run_ids)
    promotion_ready_candidate_ids = self._dedupe_strings(promotion_ready_candidate_ids)
    blocked_candidate_ids = self._dedupe_strings(blocked_candidate_ids)
    open_gap_ids = self._dedupe_strings(open_gap_ids)
    blockers = self._dedupe_strings(blockers)
    candidate_ids = self._dedupe_strings(candidate_ids)

    regression_manifest_status = "empty"
    if regression_question_ids and oracle_ids and regression_run_ids:
        regression_manifest_status = "ready"
    elif regression_question_ids or oracle_ids or regression_run_ids:
        regression_manifest_status = "partial"

    gate_checks = self._completion_gate_checks(
        regression_question_ids=regression_question_ids,
        oracle_ids=oracle_ids,
        regression_run_ids=regression_run_ids,
        promotion_ready_candidate_ids=promotion_ready_candidate_ids,
        blocked_candidate_ids=blocked_candidate_ids,
        unresolved_followup_child_topics=unresolved_followup_child_topics,
        returned_with_gap_child_topics=returned_with_gap_child_topics,
    )

    if not candidate_rows and not followup_rows:
        status = "not_assessed"
        summary = "No candidate or follow-up completion surface exists yet."
    elif gate_status == "promoted" and candidate_rows:
        status = "promoted"
        summary = "At least one regression-backed candidate has already been promoted through the active gate."
    elif blockers or unresolved_followup_child_topics or returned_with_gap_child_topics:
        status = "promotion-blocked"
        summary = "Topic completion is blocked by explicit candidate blockers or unreintegrated follow-up returns."
    elif promotion_ready_candidate_ids and regression_question_ids and oracle_ids and regression_run_ids:
        status = "promotion-ready"
        summary = "The topic has regression-backed candidates and no unresolved follow-up return debt."
    elif regression_question_ids and oracle_ids and regression_run_ids:
        status = "regression-stable"
        summary = "Regression-backed topic surfaces exist, but promotion readiness is not yet fully established."
    elif regression_question_ids and oracle_ids:
        status = "regression-seeded"
        summary = "Question/oracle surfaces exist, but recent regression run support is still incomplete."
    else:
        status = "gap-aware"
        summary = "The topic can name its blockers, but regression-governed completion is not established."

    return {
        "$schema": "https://aitp.local/schemas/topic-completion.schema.json",
        "completion_version": 1,
        "topic_slug": topic_slug,
        "run_id": run_id or "",
        "status": status,
        "candidate_count": len(candidate_rows),
        "followup_subtopic_count": len(followup_rows),
        "reintegrated_followup_count": len(reintegrated_children),
        "unresolved_followup_child_topics": self._dedupe_strings(unresolved_followup_child_topics),
        "returned_with_gap_child_topics": self._dedupe_strings(returned_with_gap_child_topics),
        "regression_manifest": {
            "status": regression_manifest_status,
            "candidate_ids": candidate_ids,
            "regression_question_ids": regression_question_ids,
            "oracle_ids": oracle_ids,
            "regression_run_ids": regression_run_ids,
            "candidate_count": len(candidate_ids),
            "question_count": len(regression_question_ids),
            "oracle_count": len(oracle_ids),
            "run_count": len(regression_run_ids),
        },
        "completion_gate_checks": gate_checks,
        "promotion_ready_candidate_ids": promotion_ready_candidate_ids,
        "blocked_candidate_ids": blocked_candidate_ids,
        "regression_question_ids": regression_question_ids,
        "oracle_ids": oracle_ids,
        "regression_run_ids": regression_run_ids,
        "open_gap_ids": open_gap_ids,
        "blockers": blockers,
        "summary": summary,
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }

def ensure_topic_shell_surfaces(
    self,
    *,
    topic_slug: str,
    updated_by: str,
    human_request: str | None = None,
    topic_state: dict[str, Any] | None = None,
    interaction_state: dict[str, Any] | None = None,
    promotion_gate: dict[str, Any] | None = None,
    queue_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    runtime_root = self._ensure_runtime_root(topic_slug)
    resolved_topic_state = dict(topic_state or _read_json(runtime_root / "topic_state.json") or {})
    resolved_interaction_state = dict(
        interaction_state or _read_json(runtime_root / "interaction_state.json") or {}
    )
    resolved_queue_rows = list(queue_rows or _read_jsonl(runtime_root / "action_queue.jsonl"))
    resolved_promotion_gate = dict(promotion_gate or self._load_promotion_gate(topic_slug) or {})
    decision_surface = resolved_interaction_state.get("decision_surface") or {}
    pending_actions, selected_pending_action = self._pending_action_context(
        resolved_queue_rows,
        decision_surface,
    )
    latest_run_id = str(resolved_topic_state.get("latest_run_id") or "").strip()
    candidate_rows = self._candidate_rows_for_run(topic_slug, latest_run_id)
    promotion_readiness = self._derive_promotion_readiness(
        topic_slug=topic_slug,
        latest_run_id=latest_run_id,
        promotion_gate=resolved_promotion_gate,
        candidate_rows=candidate_rows,
    )
    open_gap_summary = self._derive_open_gap_summary(
        topic_slug=topic_slug,
        candidate_rows=candidate_rows,
        pending_actions=pending_actions,
        selected_pending_action=selected_pending_action,
    )
    topic_completion = self.assess_topic_completion(
        topic_slug=topic_slug,
        run_id=latest_run_id or None,
        updated_by=updated_by,
        refresh_runtime_bundle=False,
    )
    dependency_state = self._topic_dependency_state(topic_slug)
    statement_compilation = self.prepare_statement_compilation(
        topic_slug=topic_slug,
        run_id=latest_run_id or None,
        updated_by=updated_by,
        refresh_runtime_bundle=False,
    )
    lean_bridge = self.prepare_lean_bridge(
        topic_slug=topic_slug,
        run_id=latest_run_id or None,
        updated_by=updated_by,
        refresh_runtime_bundle=False,
    )
    followup_reintegration_paths = self._write_followup_reintegration_rows(
        topic_slug,
        self._load_followup_reintegration_rows(topic_slug),
    )
    followup_gap_writeback_paths = self._write_followup_gap_writeback_rows(
        topic_slug,
        self._load_followup_gap_writeback_rows(topic_slug),
    )

    research_paths = self._research_question_contract_paths(topic_slug)
    validation_paths = self._validation_contract_paths(topic_slug)
    idea_packet_paths = self._idea_packet_paths(topic_slug)
    operator_checkpoint_paths = self._operator_checkpoint_paths(topic_slug)
    topic_skill_projection_paths = self._topic_skill_projection_paths(topic_slug)
    dashboard_path = self._topic_dashboard_path(topic_slug)
    readiness_path = self._promotion_readiness_path(topic_slug)
    validation_review_bundle_paths = self._validation_review_bundle_paths(topic_slug)
    gap_map_path = self._gap_map_path(topic_slug)
    source_intelligence_artifact_paths = source_intelligence_paths(runtime_root)
    graph_analysis_artifact_paths = graph_analysis_paths(runtime_root)

    existing_research = _read_json(research_paths["json"]) or {}
    existing_validation = _read_json(validation_paths["json"]) or {}
    existing_idea_packet = _read_json(idea_packet_paths["json"]) or {}
    existing_operator_checkpoint = _read_json(operator_checkpoint_paths["json"]) or {}
    existing_execution_task = _read_json(runtime_root / "execution_task.json") or {}
    source_rows = _read_jsonl(self._l0_root(topic_slug) / "source_index.jsonl")
    source_intelligence = source_intelligence_payload(
        kernel_root=self.kernel_root,
        topic_slug=topic_slug,
        source_rows=source_rows,
    )
    source_intelligence_json_ref = self._relativize(source_intelligence_artifact_paths["json"])
    source_intelligence_note_ref = self._relativize(source_intelligence_artifact_paths["note"])
    source_intelligence_surface = {
        **source_intelligence,
        "path": source_intelligence_json_ref,
        "note_path": source_intelligence_note_ref,
    }
    distilled = self._distill_from_sources(source_rows or [], topic_slug)
    distilled_initial_idea = str(distilled.get("distilled_initial_idea") or "").strip()
    distilled_first_validation_route = str(
        distilled.get("distilled_first_validation_route") or ""
    ).strip()
    distilled_l1_source_intake = normalize_l1_source_intake(distilled.get("distilled_l1_source_intake"))

    research_mode = str(
        resolved_topic_state.get("research_mode")
        or existing_research.get("research_mode")
        or self._template_mode_to_research_mode(existing_research.get("template_mode"))
        or "exploratory_general"
    ).strip()
    template_mode = str(
        existing_research.get("template_mode")
        or self._research_mode_to_template_mode(research_mode)
    ).strip()
    validation_mode = str(
        existing_validation.get("validation_mode")
        or self._validation_mode_for_modes(template_mode=template_mode, research_mode=research_mode)
    ).strip()
    title = self._coalesce_string(
        existing_research.get("title"),
        self._topic_display_title(topic_slug),
    )
    selected_action_summary = str((selected_pending_action or {}).get("summary") or "").strip()
    active_question = self._coalesce_string(
        existing_research.get("question"),
        distilled_initial_idea,
        human_request
        or str(resolved_interaction_state.get("human_request") or "").strip()
        or f"Clarify, validate, and persist the bounded theoretical-physics question for {title}.",
    )

    context_defaults = self._dedupe_strings(
        [
            f"Human request: {human_request or resolved_interaction_state.get('human_request') or active_question}",
            f"Resume stage: {resolved_topic_state.get('resume_stage') or 'uninitialized'}",
            f"Latest run id: {latest_run_id or 'missing'}",
            f"Selected action: {selected_action_summary or 'none'}",
        ]
        + l1_context_lines(distilled_l1_source_intake)
    )
    target_claim_defaults = self._dedupe_strings(
        [str(row.get("candidate_id") or "").strip() for row in candidate_rows if str(row.get("candidate_id") or "").strip()]
        or [str((selected_pending_action or {}).get("action_id") or "").strip()]
    )
    deliverable_defaults = [
        "Persist the active research question, validation route, and bounded next action as durable runtime artifacts.",
        "Write derivation/proof or execution evidence into the appropriate AITP layer before claiming completion.",
        "Produce Layer-appropriate outputs that can later be promoted into durable L2 knowledge when justified.",
    ]
    acceptance_defaults = [
        "The question, scope, deliverables, and acceptance checks remain synchronized with the runtime state.",
        "Missing definitions, cited derivations, or prior-work comparisons trigger a durable return to L0 instead of a prose-only bridge.",
        "Proof or validation claims cite concrete L3/L4 artifacts rather than memory or style confidence.",
    ]
    forbidden_proxy_defaults = [
        "Do not treat polished prose, hidden assumptions, or memory-only agreement as proof.",
        "Do not silently widen scope without updating this contract.",
        "Do not skip a restart from source intake when the blocker is really a missing source, citation chain, or prior-work comparison.",
    ]
    uncertainty_defaults = open_gap_summary["blockers"] or [
        "Mark unresolved notation, source, or regime gaps explicitly before continuing."
    ]
    research_status_default = "blocked" if open_gap_summary["requires_l0_return"] else "active"
    l1_source_intake = coalesce_l1_source_intake(
        existing_research.get("l1_source_intake"),
        distilled_l1_source_intake,
    )
    l1_source_intake.update(
        derive_l1_conflict_intake(
            source_rows=source_rows,
            l1_source_intake=l1_source_intake,
        )
    )
    previous_graph_analysis = _read_json(graph_analysis_artifact_paths["json"]) or {}
    graph_analysis = build_graph_analysis_surface(
        topic_slug=topic_slug,
        l1_source_intake=l1_source_intake,
        previous_payload=previous_graph_analysis,
        updated_by=updated_by,
    )
    graph_analysis_surface = {
        **graph_analysis,
        "path": self._relativize(graph_analysis_artifact_paths["json"]),
        "note_path": self._relativize(graph_analysis_artifact_paths["note"]),
        "history_path": self._relativize(graph_analysis_artifact_paths["history"]),
    }
    research_contract = {
        "contract_version": 1,
        "question_id": self._coalesce_string(
            existing_research.get("question_id"),
            f"research_question:{topic_slug}",
        ),
        "title": title,
        "topic_slug": topic_slug,
        "status": self._coalesce_string(existing_research.get("status"), research_status_default),
        "template_mode": template_mode,
        "research_mode": research_mode,
        "question": active_question,
        "scope": self._coalesce_list(
            existing_research.get("scope"),
            [
                f"Keep work bounded to topic `{topic_slug}` and the currently selected action.",
                "Make derivation dependencies, notation, and validation obligations explicit.",
            ]
            + ([f"Current bounded action: {selected_action_summary}"] if selected_action_summary else []),
        ),
        "assumptions": self._coalesce_list(
            existing_research.get("assumptions"),
            [str(row.get("assumption") or "").strip() for row in l1_source_intake.get("assumption_rows") or []]
            +
            [
                "Only persisted AITP artifacts count as research progress.",
                "Missing cited derivations or prior-work context must be recovered through L0 rather than guessed.",
            ],
        ),
        "non_goals": self._coalesce_list(
            existing_research.get("non_goals"),
            [
                "Do not treat the runtime shell as a generic project manager.",
                "Do not claim theory completion without layer-addressable derivation or validation evidence.",
            ],
        ),
        "context_intake": self._coalesce_list(existing_research.get("context_intake"), context_defaults),
        "l1_source_intake": l1_source_intake,
        "source_basis_refs": self._coalesce_list(
            existing_research.get("source_basis_refs"),
            self._research_source_basis_refs(topic_slug=topic_slug, source_rows=source_rows),
        ),
        "interpretation_focus": self._coalesce_list(
            existing_research.get("interpretation_focus"),
            self._research_interpretation_focus_defaults(
                active_question=active_question,
                first_validation_route=distilled_first_validation_route,
                research_mode=research_mode,
                selected_action_summary=selected_action_summary,
            )
            + l1_interpretation_focus_lines(l1_source_intake),
        ),
        "open_ambiguities": self._coalesce_list(
            existing_research.get("open_ambiguities"),
            self._research_open_ambiguities_defaults(
                existing_idea_packet=existing_idea_packet,
                open_gap_summary=open_gap_summary,
            )
            + l1_open_ambiguity_lines(l1_source_intake),
        ),
        "competing_hypotheses": normalize_competing_hypotheses(
            existing_research.get("competing_hypotheses") or [],
            topic_slug=topic_slug,
        ),
        "formalism_and_notation": self._coalesce_list(
            existing_research.get("formalism_and_notation"),
            [
                f"Research mode `{research_mode}` governs the default level of derivation detail.",
                "Notation bindings must be persisted explicitly when symbols or conventions are non-trivial.",
            ],
        ),
        "observables": self._coalesce_list(
            existing_research.get("observables"),
            [
                "Declared candidate ids, bounded claims, and validation outcomes.",
                "Promotion readiness, gap honesty, and whether the topic must return to L0.",
            ],
        ),
        "target_claims": self._coalesce_list(existing_research.get("target_claims"), target_claim_defaults),
        "deliverables": self._coalesce_list(existing_research.get("deliverables"), deliverable_defaults),
        "acceptance_tests": self._coalesce_list(
            existing_research.get("acceptance_tests"),
            acceptance_defaults,
        ),
        "forbidden_proxies": self._coalesce_list(
            existing_research.get("forbidden_proxies"),
            forbidden_proxy_defaults,
        ),
        "uncertainty_markers": self._coalesce_list(
            existing_research.get("uncertainty_markers"),
            uncertainty_defaults,
        ),
        "target_layers": self._coalesce_list(
            existing_research.get("target_layers"),
            ["L1", "L3", "L4", "L2"],
        ),
    }
    l1_vault = materialize_l1_vault(
        kernel_root=self.kernel_root,
        topic_slug=topic_slug,
        title=title,
        research_contract=research_contract,
        source_rows=source_rows,
        source_intelligence=source_intelligence_surface,
        research_contract_json_path=research_paths["json"],
        research_contract_note_path=research_paths["note"],
        control_note_path=self._control_note_path(topic_slug),
        operator_console_path=runtime_root / "operator_console.md",
        topic_dashboard_path=dashboard_path,
        updated_by=updated_by,
        relativize=self._relativize,
    )
    research_contract["l1_vault"] = l1_vault["payload"]

    artifact_defaults = [
        self._relativize(runtime_root / "runtime_protocol.generated.md"),
        self._relativize(runtime_root / "action_queue.jsonl"),
        self._relativize(research_paths["note"]),
        self._relativize(dashboard_path),
        self._relativize(Path(l1_vault["path"])),
        self._relativize(Path(l1_vault["note_path"])),
    ]
    if (runtime_root / "conformance_report.md").exists():
        artifact_defaults.append(self._relativize(runtime_root / "conformance_report.md"))
    if (runtime_root / "capability_report.md").exists():
        artifact_defaults.append(self._relativize(runtime_root / "capability_report.md"))
    if self._promotion_gate_paths(topic_slug)["json"].exists():
        artifact_defaults.append(self._relativize(self._promotion_gate_paths(topic_slug)["json"]))

    validation_status_default = "deferred" if open_gap_summary["requires_l0_return"] else "planned"
    validation_contract = {
        "contract_version": 1,
        "validation_id": self._coalesce_string(
            existing_validation.get("validation_id"),
            f"validation:{topic_slug}:active",
        ),
        "topic_slug": topic_slug,
        "status": self._coalesce_string(existing_validation.get("status"), validation_status_default),
        "template_mode": template_mode,
        "verification_focus": self._coalesce_string(
            existing_validation.get("verification_focus"),
            distilled_first_validation_route,
            selected_action_summary or promotion_readiness["summary"],
        ),
        "validation_mode": validation_mode,
        "target_claim_ids": self._coalesce_list(
            existing_validation.get("target_claim_ids"),
            target_claim_defaults,
        ),
        "acceptance_rule": self._coalesce_string(
            existing_validation.get("acceptance_rule"),
            "Accept only when the declared claims are supported by persisted derivation or execution artifacts and all active L0-recovery blockers are discharged.",
        ),
        "rejection_rule": self._coalesce_string(
            existing_validation.get("rejection_rule"),
            "Reject whenever missing anchors, missing executed evidence, unresolved cited-source gaps, or contract drift remain active.",
        ),
        "required_checks": self._coalesce_list(
            existing_validation.get("required_checks"),
            [
                "Check that the research question, scope, and selected action still match the runtime state.",
                "Check that source-backed assumptions and regimes are not being treated as settled beyond their recorded reading depth.",
                "Check that proof, derivation, or execution evidence is persisted in the declared layer.",
                "If prior-work or cited-source gaps remain, return to L0 before advancing the claim.",
            ],
        ),
        "oracle_artifacts": self._coalesce_list(
            existing_validation.get("oracle_artifacts"),
            artifact_defaults,
        ),
        "executed_evidence": self._coalesce_list(
            existing_validation.get("executed_evidence"),
            [],
        ),
        "confidence_cap": self._coalesce_string(
            existing_validation.get("confidence_cap"),
            "medium" if open_gap_summary["status"] != "clear" else "high",
        ),
        "gap_followups": self._coalesce_list(
            existing_validation.get("gap_followups"),
            open_gap_summary["blockers"] + open_gap_summary["followup_gap_ids"],
        ),
        "failure_modes": self._coalesce_list(
            existing_validation.get("failure_modes"),
            [
                "Proof steps remain implicit or depend on unstated notation.",
                "Executed validation is claimed but no durable evidence path exists.",
                "A cited derivation or prior-work dependency was glossed over instead of recovered through L0.",
            ],
        ),
        "artifacts": self._coalesce_list(
            existing_validation.get("artifacts"),
            artifact_defaults,
        ),
    }
    validation_review_bundle = self._derive_validation_review_bundle(
        topic_slug=topic_slug,
        latest_run_id=latest_run_id,
        updated_by=updated_by,
        validation_contract=validation_contract,
        promotion_readiness=promotion_readiness,
        open_gap_summary=open_gap_summary,
        topic_completion=topic_completion,
        candidate_rows=candidate_rows,
        promotion_gate=resolved_promotion_gate,
    )
    validation_review_bundle_json_ref = self._relativize(validation_review_bundle_paths["json"])
    validation_review_bundle_note_ref = self._relativize(validation_review_bundle_paths["note"])
    validation_contract["primary_review_bundle_path"] = validation_review_bundle_json_ref
    validation_contract["review_focus"] = self._coalesce_string(
        existing_validation.get("review_focus"),
        validation_review_bundle.get("summary"),
    )
    validation_contract["open_review_questions"] = self._coalesce_list(
        existing_validation.get("open_review_questions"),
        list(validation_review_bundle.get("blockers") or []),
    )
    validation_contract["oracle_artifacts"] = self._dedupe_strings(
        [validation_review_bundle_note_ref, *list(validation_contract.get("oracle_artifacts") or [])]
    )
    validation_contract["artifacts"] = self._dedupe_strings(
        [validation_review_bundle_note_ref, *list(validation_contract.get("artifacts") or [])]
    )
    strategy_memory = self._derive_strategy_memory_summary(
        topic_slug=topic_slug,
        latest_run_id=latest_run_id or None,
        selected_pending_action=selected_pending_action,
        research_contract=research_contract,
        validation_contract=validation_contract,
    )
    collaborator_profile_paths, collaborator_profile = materialize_collaborator_profile_surface(
        self,
        runtime_root=runtime_root,
        topic_slug=topic_slug,
        updated_by=updated_by,
    )
    research_trajectory_paths, research_trajectory = materialize_research_trajectory_surface(self, runtime_root=runtime_root, topic_slug=topic_slug, updated_by=updated_by)
    mode_learning_paths, mode_learning = materialize_mode_learning_surface(self, runtime_root=runtime_root, topic_slug=topic_slug, updated_by=updated_by)
    topic_skill_projection = self._derive_topic_skill_projection(
        topic_slug=topic_slug,
        updated_by=updated_by,
        topic_state=resolved_topic_state,
        research_contract=research_contract,
        validation_contract=validation_contract,
        selected_pending_action=selected_pending_action,
        strategy_memory=strategy_memory,
        topic_completion=topic_completion,
        open_gap_summary=open_gap_summary,
        candidate_rows=candidate_rows,
    )
    topic_skill_projection_written = write_topic_skill_projection(
        topic_slug,
        topic_skill_projection,
        kernel_root=self.kernel_root,
    )
    _write_text(
        topic_skill_projection_paths["note"],
        self._render_topic_skill_projection_markdown(topic_skill_projection),
    )
    topic_skill_projection_surface = {
        **topic_skill_projection_written["topic_skill_projection"],
        "path": self._relativize(Path(topic_skill_projection_written["path"])),
        "note_path": self._relativize(topic_skill_projection_paths["note"]),
    }
    topic_skill_projection_candidate = self._sync_topic_skill_projection_candidate(
        topic_slug=topic_slug,
        run_id=latest_run_id or None,
        projection=topic_skill_projection_surface,
        updated_by=updated_by,
    )
    idea_packet = self._derive_idea_packet(
        topic_slug=topic_slug,
        updated_by=updated_by,
        human_request=human_request,
        topic_state=resolved_topic_state,
        interaction_state=resolved_interaction_state,
        existing_idea_packet=existing_idea_packet,
        existing_research=existing_research,
        existing_validation=existing_validation,
        research_contract=research_contract,
        validation_contract=validation_contract,
        selected_pending_action=selected_pending_action,
    )
    operator_checkpoint, superseded_checkpoint = self._derive_operator_checkpoint(
        topic_slug=topic_slug,
        updated_by=updated_by,
        existing_checkpoint=existing_operator_checkpoint,
        idea_packet=idea_packet,
        research_contract=research_contract,
        validation_contract=validation_contract,
        promotion_gate=resolved_promotion_gate,
        selected_pending_action=selected_pending_action,
        decision_surface=decision_surface,
        dashboard_path=dashboard_path,
        idea_packet_paths=idea_packet_paths,
        research_paths=research_paths,
        validation_paths=validation_paths,
        execution_task=existing_execution_task,
    )

    _write_json(research_paths["json"], research_contract)
    _write_text(research_paths["note"], self._render_research_question_contract_markdown(research_contract))
    _write_json(source_intelligence_artifact_paths["json"], source_intelligence_surface)
    _write_text(source_intelligence_artifact_paths["note"], render_source_intelligence_markdown(source_intelligence_surface))
    _write_json(graph_analysis_artifact_paths["json"], graph_analysis_surface)
    _write_text(graph_analysis_artifact_paths["note"], render_graph_analysis_markdown(graph_analysis_surface))
    write_graph_analysis_history(graph_analysis_artifact_paths["history"], payload=graph_analysis_surface)
    _write_json(validation_paths["json"], validation_contract)
    _write_text(validation_paths["note"], self._render_validation_contract_markdown(validation_contract))
    _write_json(validation_review_bundle_paths["json"], validation_review_bundle)
    _write_text(
        validation_review_bundle_paths["note"],
        self._render_validation_review_bundle_markdown(validation_review_bundle),
    )
    _write_json(idea_packet_paths["json"], idea_packet)
    _write_text(idea_packet_paths["note"], self._render_idea_packet_markdown(idea_packet))
    operator_checkpoint_paths_written = self._write_operator_checkpoint(
        topic_slug=topic_slug,
        payload=operator_checkpoint,
        superseded_payload=superseded_checkpoint,
    )
    operator_checkpoint_surface = {
        **operator_checkpoint,
        "path": self._relativize(Path(operator_checkpoint_paths_written["operator_checkpoint_path"])),
        "note_path": self._relativize(Path(operator_checkpoint_paths_written["operator_checkpoint_note_path"])),
        "ledger_path": self._relativize(Path(operator_checkpoint_paths_written["operator_checkpoint_ledger_path"])),
    }
    topic_status_explainability = self._derive_topic_status_explainability(
        topic_slug=topic_slug,
        topic_state=resolved_topic_state,
        interaction_state=resolved_interaction_state,
        selected_pending_action=selected_pending_action,
        idea_packet=idea_packet,
        operator_checkpoint=operator_checkpoint_surface,
        open_gap_summary=open_gap_summary,
        validation_contract=validation_contract,
    )
    research_judgment_paths, research_judgment, research_taste_paths, research_taste = materialize_research_state_surfaces(
        self,
        runtime_root=runtime_root,
        topic_slug=topic_slug,
        latest_run_id=latest_run_id,
        updated_by=updated_by,
        topic_status_explainability=topic_status_explainability,
        selected_pending_action=selected_pending_action,
        open_gap_summary=open_gap_summary,
        strategy_memory=strategy_memory,
        dependency_state=dependency_state,
        gap_map_path=gap_map_path,
    )
    scratchpad_paths, scratchpad = materialize_scratchpad_surface(self, runtime_root=runtime_root, topic_slug=topic_slug, updated_by=updated_by)
    topic_status_explainability["scratchpad"] = scratchpad
    runtime_focus = self._topic_synopsis_runtime_focus(topic_state=resolved_topic_state, topic_status_explainability=topic_status_explainability, dependency_state=dependency_state, promotion_readiness=promotion_readiness)
    topic_state_path = runtime_root / "topic_state.json"
    if topic_state_path.exists() and resolved_topic_state:
        resolved_topic_state = {**dict(resolved_topic_state), "status_explainability": topic_status_explainability}
        _write_json(topic_state_path, resolved_topic_state)
    finalize_topic_shell_outputs(
        self,
        dashboard_path=dashboard_path,
        topic_slug=topic_slug,
        topic_state=resolved_topic_state,
        source_intelligence=source_intelligence_surface,
        graph_analysis=graph_analysis_surface,
        runtime_focus=runtime_focus,
        selected_pending_action=selected_pending_action,
        pending_actions=pending_actions,
        idea_packet=idea_packet,
        operator_checkpoint=operator_checkpoint_surface,
        topic_status_explainability=topic_status_explainability,
        research_contract=research_contract,
        validation_contract=validation_contract,
        validation_review_bundle={
            **validation_review_bundle,
            "path": validation_review_bundle_json_ref,
            "note_path": validation_review_bundle_note_ref,
        },
        promotion_readiness=promotion_readiness,
        readiness_path=readiness_path,
        open_gap_summary=open_gap_summary,
        gap_map_path=gap_map_path,
        strategy_memory=strategy_memory,
        statement_compilation=statement_compilation,
        topic_skill_projection=topic_skill_projection_surface,
        topic_completion=topic_completion,
        lean_bridge=lean_bridge,
        dependency_state=dependency_state,
    )
    return {
        "research_question_contract_path": str(research_paths["json"]),
        "research_question_contract_note_path": str(research_paths["note"]),
        "l1_vault_path": str(l1_vault["path"]),
        "l1_vault_note_path": str(l1_vault["note_path"]),
        "l1_vault_raw_manifest_path": str(l1_vault["raw_manifest_path"]),
        "l1_vault_raw_manifest_note_path": str(l1_vault["raw_manifest_note_path"]),
        "l1_vault_wiki_home_path": str(l1_vault["wiki_home_path"]),
        "l1_vault_wiki_schema_path": str(l1_vault["wiki_schema_path"]),
        "l1_vault_wiki_source_intake_path": str(l1_vault["wiki_source_intake_path"]),
        "l1_vault_wiki_open_questions_path": str(l1_vault["wiki_open_questions_path"]),
        "l1_vault_wiki_runtime_bridge_path": str(l1_vault["wiki_runtime_bridge_path"]),
        "l1_vault_output_digest_path": str(l1_vault["output_digest_path"]),
        "l1_vault_output_digest_note_path": str(l1_vault["output_digest_note_path"]),
        "l1_vault_flowback_log_path": str(l1_vault["flowback_log_path"]),
        "l1_vault_flowback_note_path": str(l1_vault["flowback_note_path"]),
        "validation_contract_path": str(validation_paths["json"]),
        "validation_contract_note_path": str(validation_paths["note"]),
        "validation_review_bundle_path": str(validation_review_bundle_paths["json"]),
        "validation_review_bundle_note_path": str(validation_review_bundle_paths["note"]),
        "collaborator_profile_path": str(collaborator_profile_paths["json"]),
        "collaborator_profile_note_path": str(collaborator_profile_paths["note"]),
        "research_trajectory_path": str(research_trajectory_paths["json"]),
        "research_trajectory_note_path": str(research_trajectory_paths["note"]),
        "mode_learning_path": str(mode_learning_paths["json"]),
        "mode_learning_note_path": str(mode_learning_paths["note"]),
        "research_judgment_path": str(research_judgment_paths["json"]),
        "research_judgment_note_path": str(research_judgment_paths["note"]),
        "research_taste_path": str(research_taste_paths["json"]),
        "research_taste_note_path": str(research_taste_paths["note"]),
        "research_taste_entries_path": str(research_taste_paths["entries"]),
        "scratchpad_path": str(scratchpad_paths["json"]),
        "scratchpad_note_path": str(scratchpad_paths["note"]),
        "scratchpad_entries_path": str(scratchpad_paths["entries"]),
        "idea_packet_path": str(idea_packet_paths["json"]),
        "idea_packet_note_path": str(idea_packet_paths["note"]),
        "operator_checkpoint_path": operator_checkpoint_paths_written["operator_checkpoint_path"],
        "operator_checkpoint_note_path": operator_checkpoint_paths_written["operator_checkpoint_note_path"],
        "operator_checkpoint_ledger_path": operator_checkpoint_paths_written["operator_checkpoint_ledger_path"],
        "topic_dashboard_path": str(dashboard_path),
        "source_intelligence_path": str(source_intelligence_artifact_paths["json"]),
        "source_intelligence_note_path": str(source_intelligence_artifact_paths["note"]),
        "graph_analysis_path": str(graph_analysis_artifact_paths["json"]),
        "graph_analysis_note_path": str(graph_analysis_artifact_paths["note"]),
        "graph_analysis_history_path": str(graph_analysis_artifact_paths["history"]),
        "topic_skill_projection_path": str(topic_skill_projection_paths["json"]),
        "topic_skill_projection_note_path": str(topic_skill_projection_paths["note"]),
        "promotion_readiness_path": str(readiness_path),
        "gap_map_path": str(gap_map_path),
        "topic_completion_path": topic_completion["topic_completion_path"],
        "topic_completion_note_path": topic_completion["topic_completion_note_path"],
        "statement_compilation_path": statement_compilation["statement_compilation_path"],
        "statement_compilation_note_path": statement_compilation["statement_compilation_note_path"],
        "lean_bridge_path": lean_bridge["lean_bridge_path"],
        "lean_bridge_note_path": lean_bridge["lean_bridge_note_path"],
        "followup_reintegration_path": followup_reintegration_paths["followup_reintegration_path"],
        "followup_reintegration_note_path": followup_reintegration_paths["followup_reintegration_note_path"],
        "followup_gap_writeback_path": followup_gap_writeback_paths["followup_gap_writeback_path"],
        "followup_gap_writeback_note_path": followup_gap_writeback_paths["followup_gap_writeback_note_path"],
        "research_question_contract": research_contract,
        "l1_vault": l1_vault["payload"],
        "source_intelligence": source_intelligence_surface,
        "graph_analysis": graph_analysis_surface,
        "validation_contract": validation_contract,
        "validation_review_bundle": {
            **validation_review_bundle,
            "path": validation_review_bundle_json_ref,
            "note_path": validation_review_bundle_note_ref,
        },
        "collaborator_profile": collaborator_profile,
        "research_trajectory": research_trajectory,
        "mode_learning": mode_learning,
        "research_judgment": research_judgment,
        "research_taste": research_taste,
        "scratchpad": scratchpad,
        "idea_packet": idea_packet,
        "operator_checkpoint": operator_checkpoint_surface,
        "topic_state_explainability": topic_status_explainability,
        "runtime_focus": runtime_focus,
        "promotion_readiness": promotion_readiness,
        "open_gap_summary": open_gap_summary,
        "dependency_state": dependency_state,
        "strategy_memory": strategy_memory,
        "statement_compilation": statement_compilation,
        "topic_skill_projection": topic_skill_projection_surface,
        "topic_skill_projection_candidate": topic_skill_projection_candidate,
        "topic_completion": topic_completion,
        "lean_bridge": lean_bridge,
    }
