from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from .mode_registry import (
    PROMOTE_OPERATION_SIGNALS as _PROMOTE_ACTION_TYPES,
    VERIFY_OPERATION_SIGNALS as _VERIFY_ACTION_TYPES,
    VERIFY_TRIGGERS as _VERIFY_TRIGGERS,
)
from .mode_registry import is_valid_transition, normalize_runtime_mode as _normalize_mode

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "mode_envelope_data.json"

_DEFAULT_CONFIG: dict[str, Any] = {
    "mode_specs": {
        "explore": {
            "local_task": "Clarify the bounded research question and source basis before deeper commitment.",
            "foreground_layers": ["L0", "L1", "L3-I"],
            "required_writeback": [],
            "allowed_backedges": ["L0", "human_checkpoint"],
            "forbidden_shortcuts": ["Do not treat exploration as validation or promotion."],
            "human_checkpoint_policy": "route_change_only",
            "entry_conditions": ["A bounded question or source basis is still being clarified."],
            "exit_conditions": ["Exit once the topic has a usable idea, source basis, or explicit blocker."],
        },
        "learn": {
            "local_task": "Run the bounded L3-A <-> L4 verification loop for the active topic route.",
            "foreground_layers": ["L3", "L4"],
            "required_writeback": [],
            "allowed_backedges": ["L0", "L2", "human_checkpoint"],
            "forbidden_shortcuts": ["Do not treat style confidence as validation."],
            "human_checkpoint_policy": "when_route_changes",
            "entry_conditions": ["The topic already has a bounded question or source basis worth checking."],
            "exit_conditions": ["Exit once the verification loop yields a result, blocker, or writeback candidate."],
        },
        "implement": {
            "local_task": "Advance a bounded writeback or reusable-result route without skipping trust gates.",
            "foreground_layers": ["L3", "L4", "L2"],
            "required_writeback": [],
            "allowed_backedges": ["L0", "L3", "human_checkpoint"],
            "forbidden_shortcuts": ["Do not bypass L3-R when moving toward L2."],
            "human_checkpoint_policy": "promotion_boundary",
            "entry_conditions": ["A bounded route is mature enough to consider writeback or stable result packaging."],
            "exit_conditions": ["Exit once the writeback decision is resolved or the route demotes back to learn mode."],
        },
    },
    "literature_source_tokens": ["paper", "source", "lecture", "chapter", "literature", "reference"],
    "literature_intake_tokens": ["read", "intake", "recover", "register", "distill"],
    "literature_keep_suffixes": ["research_question.contract.md", "topic_dashboard.md"],
    "literature_defer_rules": [],
    "literature_submode_spec": {
        "local_task": "Recover and distill the bounded literature basis before broader synthesis.",
        "required_writeback": [],
        "entry_conditions": ["The current route is still source-intake heavy."],
        "exit_conditions": ["Exit once the source basis is explicit enough to support bounded L3 work."],
    },
    "mode_escalation_triggers": {
        "explore": ["direction_ambiguity", "resource_risk_limit_choice"],
        "learn": ["non_trivial_consultation", "contradiction_detected", "verification_route_selection"],
        "implement": ["promotion_intent", "decision_override_present"],
    },
    "writeback_artifact_map": {},
}


@lru_cache(maxsize=1)
def _load_config() -> dict:
    if _CONFIG_PATH.exists():
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    return dict(_DEFAULT_CONFIG)


def _mode_specs() -> dict[str, dict[str, Any]]:
    return _load_config()["mode_specs"]


def _get_mode_spec(mode: str) -> dict[str, Any]:
    return _mode_specs().get(mode, {})


def _literature_tokens() -> dict[str, tuple[str, ...]]:
    cfg = _load_config()
    return {
        "source": tuple(cfg.get("literature_source_tokens") or []),
        "intake": tuple(cfg.get("literature_intake_tokens") or []),
        "keep_suffixes": tuple(cfg.get("literature_keep_suffixes") or []),
    }


def _literature_defer_rules() -> list[tuple[str, str, str]]:
    return [
        (r["suffix"], r["trigger"], r["reason"])
        for r in _load_config().get("literature_defer_rules") or []
    ]


def _literature_submode_spec() -> dict[str, Any]:
    return _load_config().get("literature_submode_spec") or {}


def _mode_escalation_triggers() -> dict[str, set[str]]:
    return {
        mode: set(triggers)
        for mode, triggers in _load_config().get("mode_escalation_triggers", {}).items()
    }


def _writeback_artifact_map() -> dict[str, str]:
    return dict(_load_config().get("writeback_artifact_map") or {})


def light_profile_primary_reads(
    *,
    topic_dashboard_path: str,
    research_question_contract_note_path: str,
) -> list[dict[str, str]]:
    return [
        {"path": topic_dashboard_path, "reason": "Primary human runtime surface for the current topic. Read this first for the bounded status, next action, and blockers."},
        {"path": research_question_contract_note_path, "reason": "Active research question, scope, and deliverables for ordinary topic work."},
    ]


def decision_override_read(control_note_path: str) -> dict[str, str]:
    return {"path": control_note_path, "reason": "Human steering or a declared decision override is active. Read this before trusting heuristic queue flow."}


def _detect_literature_intake_intent(*texts: str | None) -> bool:
    tokens = _literature_tokens()
    normalized = " ".join(str(text or "").strip().lower() for text in texts if str(text or "").strip())
    if not normalized:
        return False
    return any(token in normalized for token in tokens["source"]) and any(
        token in normalized for token in tokens["intake"]
    )


def _load_recorded_mode(
    topic_slug: str | None,
    classification_type: str,
) -> str | None:
    if not topic_slug:
        return None
    from .aitp_service import AITPService, read_jsonl
    svc = AITPService()
    path = svc._classification_contract_path(topic_slug)
    rows = read_jsonl(path)
    typed = [r for r in rows if r.get("classification_type") == classification_type]
    return typed[-1].get("value") if typed else None


def _select_active_submode(
    *,
    runtime_mode: str,
    selected_action_type: str,
    selected_action_summary: str,
    human_request: str | None,
    active_triggers: set[str],
    recorded_submode: str | None = None,
) -> str | None:
    if recorded_submode:
        return recorded_submode
    if runtime_mode in ("learn", "implement") and bool(active_triggers & _VERIFY_TRIGGERS):
        return "derivation" if "derivation" in selected_action_summary.lower() else "numerical"
    lowered_summary = selected_action_summary.lower()
    if runtime_mode == "explore" and "l2 staging manifest" in lowered_summary:
        return "literature"
    if runtime_mode == "explore" and _detect_literature_intake_intent(
        selected_action_type,
        selected_action_summary,
        human_request,
    ):
        return "literature"
    if runtime_mode == "implement":
        lowered = selected_action_summary.lower()
        if any(t in lowered for t in ("code", "implement", "algorithm")):
            return "code"
        if any(t in lowered for t in ("formal", "proof", "lean")):
            return "formal"
        if any(t in lowered for t in ("numerical", "experiment", "benchmark")):
            return "experimental"
    return None


def _select_runtime_mode(
    *,
    resume_stage: str | None,
    idea_packet_status: str,
    operator_checkpoint_status: str,
    selected_action_type: str,
    selected_action_summary: str,
    active_triggers: set[str],
    current_mode: str | None = None,
    recorded_mode: str | None = None,
) -> str:
    if recorded_mode:
        candidate = recorded_mode
    else:
        lowered_summary = selected_action_summary.lower()
        candidate = "explore"

        if selected_action_type in _PROMOTE_ACTION_TYPES or any(token in lowered_summary for token in ("promot", "writeback")):
            candidate = "implement"
        elif (
            resume_stage == "L4"
            or selected_action_type in _VERIFY_ACTION_TYPES
            or bool(active_triggers & _VERIFY_TRIGGERS)
            or any(token in lowered_summary for token in ("validation", "verification", "proof", "derivation", "selected route"))
        ):
            candidate = "learn"
        elif idea_packet_status == "needs_clarification" or operator_checkpoint_status == "requested":
            candidate = "explore"
        elif any(token in lowered_summary for token in ("novel", "new idea", "conjecture", "hypothesis")):
            candidate = "implement"
        else:
            candidate = "explore"

    if current_mode is not None:
        normalized_current = _normalize_mode(current_mode)
        normalized_candidate = _normalize_mode(candidate)
        if not is_valid_transition(normalized_current, normalized_candidate):
            return normalized_current

    return candidate


def filter_escalation_triggers_for_mode(
    *,
    runtime_mode: str,
    escalation_triggers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    allowed = _mode_escalation_triggers().get(str(runtime_mode or "").strip())
    if not allowed:
        return [dict(row) for row in escalation_triggers]

    filtered: list[dict[str, Any]] = []
    for row in escalation_triggers:
        copied = dict(row)
        trigger = str(copied.get("trigger") or "").strip()
        if bool(copied.get("active")) and trigger not in allowed:
            copied["active"] = False
        filtered.append(copied)
    return filtered


def _transition_posture(
    *,
    runtime_mode: str,
    active_triggers: set[str],
    operator_checkpoint_status: str,
) -> dict[str, Any]:
    if runtime_mode == "implement" and "promotion_intent" in active_triggers:
        return {
            "transition_kind": "forward_transition",
            "transition_reason": "L4-validated material is ready for the L4 -> L2 promotion pipeline.",
            "allowed_targets": ["L2", "L4", "L0"],
            "triggered_by": ["promotion_intent"],
            "requires_human_checkpoint": True,
            "human_checkpoint_reason": "Layer 2 writeback remains an explicit trust boundary.",
        }
    if "non_trivial_consultation" in active_triggers:
        return {
            "transition_kind": "backedge_transition",
            "transition_reason": "Current work needs L2 consultation before further local continuation is honest.",
            "allowed_targets": ["L2"],
            "triggered_by": ["non_trivial_consultation"],
            "requires_human_checkpoint": False,
            "human_checkpoint_reason": None,
        }
    if "capability_gap_blocker" in active_triggers:
        return {
            "transition_kind": "backedge_transition",
            "transition_reason": "A missing capability or workflow is the honest blocker for the next step.",
            "allowed_targets": ["L0", "human_checkpoint"],
            "triggered_by": ["capability_gap_blocker"],
            "requires_human_checkpoint": True,
            "human_checkpoint_reason": "Capability gaps often require operator choice about tooling, lane, or resource commitment.",
        }
    if "contradiction_detected" in active_triggers:
        return {
            "transition_kind": "backedge_transition",
            "transition_reason": "The current validation posture exposes contradiction or regime mismatch that may require earlier-layer recovery.",
            "allowed_targets": ["L0", "L2", "human_checkpoint"],
            "triggered_by": ["contradiction_detected"],
            "requires_human_checkpoint": False,
            "human_checkpoint_reason": None,
        }
    requires_human_checkpoint = operator_checkpoint_status == "requested"
    return {
        "transition_kind": "boundary_hold",
        "transition_reason": f"Current work remains inside the `{runtime_mode}` envelope until a declared trigger or completed artifact changes the layer boundary.",
        "allowed_targets": list(_get_mode_spec(runtime_mode).get("foreground_layers", [])),
        "triggered_by": sorted(active_triggers),
        "requires_human_checkpoint": requires_human_checkpoint,
        "human_checkpoint_reason": "An active operator checkpoint is unresolved." if requires_human_checkpoint else None,
    }


def build_runtime_mode_contract(
    *,
    resume_stage: str | None,
    load_profile: str,
    idea_packet_status: str,
    operator_checkpoint_status: str,
    selected_action_type: str,
    selected_action_summary: str,
    must_read_now: list[dict[str, str]],
    may_defer_until_trigger: list[dict[str, str]],
    escalation_triggers: list[dict[str, Any]],
    human_request: str | None = None,
    current_mode: str | None = None,
    topic_slug: str | None = None,
) -> dict[str, Any]:
    recorded_mode = _load_recorded_mode(topic_slug, "runtime_mode")
    recorded_submode = _load_recorded_mode(topic_slug, "active_submode")
    active_triggers = {
        str(row.get("trigger") or "").strip()
        for row in escalation_triggers
        if row.get("active") and str(row.get("trigger") or "").strip()
    }
    runtime_mode = _select_runtime_mode(
        resume_stage=resume_stage,
        idea_packet_status=idea_packet_status,
        operator_checkpoint_status=operator_checkpoint_status,
        selected_action_type=selected_action_type,
        selected_action_summary=selected_action_summary,
        active_triggers=active_triggers,
        current_mode=current_mode,
        recorded_mode=recorded_mode,
    )
    active_submode = _select_active_submode(
        runtime_mode=runtime_mode,
        selected_action_type=selected_action_type,
        selected_action_summary=selected_action_summary,
        human_request=human_request,
        active_triggers=active_triggers,
        recorded_submode=recorded_submode,
    )
    mode_spec = _get_mode_spec(runtime_mode)
    transition_posture = _transition_posture(
        runtime_mode=runtime_mode,
        active_triggers=active_triggers,
        operator_checkpoint_status=operator_checkpoint_status,
    )
    local_task = str(mode_spec["local_task"])
    required_writeback = list(mode_spec["required_writeback"])
    entry_conditions = list(mode_spec["entry_conditions"])
    if active_submode:
        if active_submode in ("derivation", "numerical"):
            entry_conditions.append("A bounded L3-L4 loop is active and each failed pass can produce explicit feedback.")
        elif active_submode in ("code", "formal", "experimental"):
            entry_conditions.append("An active implement submode is driving the L3-I -> L3-P -> L3-A pipeline.")
        elif active_submode == "literature":
            lit_spec = _literature_submode_spec()
            local_task = str(lit_spec["local_task"])
            required_writeback = list(lit_spec["required_writeback"])
            entry_conditions.extend(lit_spec["entry_conditions"])
    exit_conditions = list(mode_spec["exit_conditions"])
    if active_submode == "literature":
        exit_conditions.extend(_literature_submode_spec().get("exit_conditions") or [])
    if transition_posture["transition_kind"] == "backedge_transition":
        exit_conditions.append("Current work should exit locally once the declared backedge has been materialized.")
    topic_has_ideas = idea_packet_status not in ("", "needs_clarification", "missing")
    topic_has_sources = bool(must_read_now) or bool(may_defer_until_trigger)
    topic_has_verified_results = bool(active_triggers & {"validation_passed", "promotion_ready"})
    topic_has_novel_conclusions = any(
        token in selected_action_summary.lower()
        for token in ("novel", "conclusion", "result")
    )
    transition_validation = validate_mode_transition_conditions(
        from_mode=current_mode or runtime_mode,
        to_mode=runtime_mode,
        topic_has_ideas=topic_has_ideas,
        topic_has_sources=topic_has_sources,
        topic_has_verified_results=topic_has_verified_results,
        topic_has_novel_conclusions=topic_has_novel_conclusions,
    )
    return {
        "runtime_mode": runtime_mode,
        "active_submode": active_submode,
        "mode_envelope": {
            "mode": runtime_mode,
            "active_submode": active_submode,
            "load_profile": load_profile,
            "local_task": local_task,
            "foreground_layers": list(mode_spec["foreground_layers"]),
            "minimum_mandatory_context": must_read_now,
            "deferred_context": may_defer_until_trigger,
            "allowed_backedges": list(mode_spec["allowed_backedges"]),
            "required_writeback": required_writeback,
            "forbidden_shortcuts": list(mode_spec["forbidden_shortcuts"]),
            "human_checkpoint_policy": mode_spec["human_checkpoint_policy"],
            "entry_conditions": entry_conditions,
            "exit_conditions": exit_conditions,
        },
        "transition_posture": transition_posture,
        "transition_validation": transition_validation,
    }


def runtime_mode_payload_fragment(**kwargs: Any) -> dict[str, Any]:
    mode_contract = build_runtime_mode_contract(**kwargs)
    return {
        "runtime_mode": mode_contract["runtime_mode"],
        "active_submode": mode_contract["active_submode"],
        "mode_envelope": mode_contract["mode_envelope"],
        "transition_posture": mode_contract["transition_posture"],
        "transition_validation": mode_contract["transition_validation"],
    }


def check_forbidden_shortcuts(
    *,
    runtime_mode: str,
    action_type: str,
    action_summary: str,
) -> dict[str, Any]:
    """Check whether an action violates the current mode's forbidden_shortcuts.

    Returns a dict with 'allowed' (bool) and optional 'reason' (str).
    """
    mode_spec = _get_mode_spec(runtime_mode)
    if not mode_spec:
        return {"allowed": True}

    lowered_summary = action_summary.lower()

    violations: list[str] = []
    if runtime_mode == "explore":
        # "Do not form formal candidates in explore mode."
        if action_type in ("promote_candidate", "auto_promote_candidate", "request_promotion"):
            violations.append("Explore mode forbids candidate promotion actions.")
        # "Do not execute L4 validation or L2 promotion."
        if action_type in ("dispatch_execution_task", "materialize_execution_task"):
            if any(t in lowered_summary for t in ("validation", "verification", "execution")):
                violations.append("Explore mode forbids L4 validation execution.")
    elif runtime_mode == "learn":
        # "L4 results must return through L3-R, never directly to L2."
        if action_type == "promote_candidate" and "l2" in lowered_summary and "l3" not in lowered_summary:
            violations.append("Learn mode requires L4 results to return through L3-R, not directly to L2.")
        # "Do not let style confidence count as validation."
        if "style confidence" in lowered_summary or "style_confidence" in lowered_summary:
            violations.append("Learn mode forbids treating style confidence as validation.")
    elif runtime_mode == "implement":
        # "L4 results must return through L3-R, never directly to L2."
        if action_type == "promote_candidate" and "bypass" in lowered_summary:
            violations.append("Implement mode forbids bypassing L3-R for promotion.")
        # "New conclusions stay in L3 for human review before L2 promotion."
        if "auto-promote" in lowered_summary and "conclusion" in lowered_summary:
            violations.append("Implement mode requires human review before promoting new conclusions.")

    if violations:
        return {"allowed": False, "reason": "; ".join(violations)}
    return {"allowed": True}


def check_layer_permission(
    *,
    runtime_mode: str,
    target_layer: str,
) -> dict[str, Any]:
    """Check whether an action targeting *target_layer* is permitted in the current mode.

    Returns a dict with 'allowed' (bool) and optional 'reason' (str).
    """
    mode_spec = _get_mode_spec(runtime_mode)
    if not mode_spec:
        return {"allowed": True}

    normalized = target_layer.strip().upper()
    if not normalized.startswith("L"):
        return {"allowed": True}

    prefix = normalized.split("-")[0]
    foreground = {str(layer).strip().upper().split("-")[0] for layer in mode_spec.get("foreground_layers") or []}
    if prefix not in foreground:
        return {
            "allowed": False,
            "reason": f"{runtime_mode} mode does not permit work in {normalized} (foreground: {', '.join(sorted(foreground))}).",
        }
    return {"allowed": True}


def verify_required_writeback(
    *,
    runtime_mode: str,
    kernel_root: Path,
    topic_slug: str,
) -> dict[str, Any]:
    """Check whether required_writeback artifacts exist for the current mode.

    Returns a dict with 'all_satisfied' (bool) and per-item status.
    """
    mode_spec = _get_mode_spec(runtime_mode)
    if not mode_spec:
        return {"all_satisfied": True, "items": [], "missing": []}

    required = [str(r).strip() for r in mode_spec.get("required_writeback") or []]
    items: list[dict[str, Any]] = []
    missing: list[str] = []

    for key in required:
        pattern = _writeback_artifact_map().get(key, "")
        path_str = pattern.format(slug=topic_slug) if "{slug}" in pattern else pattern
        resolved = kernel_root / path_str
        satisfied = resolved.exists() if path_str else True
        items.append({"key": key, "path": path_str, "satisfied": satisfied})
        if not satisfied:
            missing.append(key)

    return {
        "all_satisfied": len(missing) == 0,
        "items": items,
        "missing": missing,
        "mode": runtime_mode,
    }


def validate_mode_transition_conditions(
    *,
    from_mode: str,
    to_mode: str,
    topic_has_ideas: bool = False,
    topic_has_sources: bool = False,
    topic_has_verified_results: bool = False,
    topic_has_novel_conclusions: bool = False,
) -> dict[str, Any]:
    """Validate entry/exit conditions for a mode transition.

    Returns a dict with 'valid' (bool), 'exit_met', 'entry_met', and 'warnings'.
    """
    from_spec = _get_mode_spec(from_mode)
    to_spec = _get_mode_spec(to_mode)
    warnings: list[str] = []

    # Check exit conditions of the source mode
    exit_met = True
    if from_spec:
        exit_conds = [str(c).lower() for c in from_spec.get("exit_conditions") or []]
        if from_mode == "explore":
            if not topic_has_ideas and not topic_has_sources:
                exit_met = False
                warnings.append("Explore exit: no ideas recorded or sources identified yet.")
        elif from_mode == "learn":
            if not topic_has_verified_results:
                warnings.append("Learn exit: no verified results or identified gap yet.")
        elif from_mode == "implement":
            if not topic_has_novel_conclusions:
                warnings.append("Implement exit: no novel conclusion recorded yet.")

    # Check entry conditions of the target mode
    entry_met = True
    if to_spec:
        entry_conds = [str(c).lower() for c in to_spec.get("entry_conditions") or []]
        if to_mode == "learn":
            if not topic_has_ideas and not topic_has_sources:
                entry_met = False
                warnings.append("Learn entry: at least one idea or source should be identified.")
        elif to_mode == "implement":
            if not topic_has_ideas:
                entry_met = False
                warnings.append("Implement entry: a concrete idea should be ready for execution.")

    return {
        "valid": exit_met and entry_met,
        "exit_met": exit_met,
        "entry_met": entry_met,
        "warnings": warnings,
    }


def runtime_mode_markdown_lines(payload: dict[str, Any]) -> list[str]:
    runtime_mode = str(payload.get("runtime_mode") or "explore")
    active_submode = payload.get("active_submode")
    mode_envelope = payload.get("mode_envelope") or {}
    transition_posture = payload.get("transition_posture") or {}
    return [
        f"- Runtime mode: `{runtime_mode}`",
        f"- Active submode: `{active_submode or '(none)'}`",
        "",
        "## Mode envelope",
        "",
        f"- Local task: `{mode_envelope.get('local_task') or '(missing)'}`",
        f"- Foreground layers: `{', '.join(mode_envelope.get('foreground_layers') or []) or '(missing)'}`",
        f"- Human checkpoint policy: `{mode_envelope.get('human_checkpoint_policy') or '(missing)'}`",
        "",
        "## Transition posture",
        "",
        f"- Kind: `{transition_posture.get('transition_kind') or '(missing)'}`",
        f"- Allowed targets: `{', '.join(transition_posture.get('allowed_targets') or []) or '(none)'}`",
        f"- Reason: `{transition_posture.get('transition_reason') or '(missing)'}`",
    ]


def _append_path_reason(rows: list[dict[str, str]], *, path: str | None, reason: str) -> None:
    normalized = str(path or "").strip()
    if not normalized:
        return
    if any(str(row.get("path") or "").strip() == normalized for row in rows):
        return
    rows.append({"path": normalized, "reason": reason})


def _append_deferred_surface(
    rows: list[dict[str, str]],
    *,
    path: str | None,
    trigger: str,
    reason: str,
) -> None:
    normalized = str(path or "").strip()
    if not normalized:
        return
    for row in rows:
        if str(row.get("path") or "").strip() == normalized:
            return
    rows.append({"path": normalized, "trigger": trigger, "reason": reason})


def _literature_wiki_paths(l1_vault: dict[str, Any]) -> list[str]:
    wiki = l1_vault.get("wiki") or {}
    page_paths = [str(item) for item in (wiki.get("page_paths") or [])]
    if page_paths:
        return page_paths
    fallback = [
        str(wiki.get("home_page_path") or ""),
        "topics/{topic_slug}/L1/vault/wiki/source-intake.md",
        "topics/{topic_slug}/L1/vault/wiki/open-questions.md",
        "topics/{topic_slug}/L1/vault/wiki/runtime-bridge.md",
    ]
    topic_slug = str(l1_vault.get("topic_slug") or "").strip()
    return [item.format(topic_slug=topic_slug) for item in fallback if item]


def _surface_reason(
    path: str | None,
    *surface_groups: list[dict[str, Any]],
    fallback: str,
) -> str:
    normalized = str(path or "").strip()
    if not normalized:
        return fallback
    for group in surface_groups:
        for row in group:
            if str(row.get("path") or "").strip() == normalized:
                reason = str(row.get("reason") or "").strip()
                if reason:
                    return reason
    return fallback


def _refocus_by_rules(
    *,
    runtime_mode_payload: dict[str, Any],
    must_read_now: list[dict[str, str]],
    may_defer_until_trigger: list[dict[str, str]],
    prioritized_paths: list[tuple[str | None, str]],
    deferred_rules: list[tuple[str | None, str, str]],
) -> dict[str, Any]:
    focused_reads: list[dict[str, str]] = []
    deferred_reads = list(may_defer_until_trigger)
    deferred_by_path = {
        str(row.get("path") or "").strip(): row
        for row in deferred_reads
        if str(row.get("path") or "").strip()
    }
    deferred_paths = {
        path
        for path, _, _ in deferred_rules
        if str(path or "").strip()
    }

    for row in must_read_now:
        path = str(row.get("path") or "").strip()
        reason = str(row.get("reason") or "").strip()
        if not path:
            continue
        if path in deferred_paths:
            continue
        _append_path_reason(focused_reads, path=path, reason=reason or "Current runtime surface.")

    for path, reason in prioritized_paths:
        _append_path_reason(
            focused_reads,
            path=path,
            reason=_surface_reason(path, must_read_now, may_defer_until_trigger, fallback=reason),
        )

    for path, trigger, reason in deferred_rules:
        normalized = str(path or "").strip()
        if not normalized:
            continue
        existing = deferred_by_path.get(normalized)
        _append_deferred_surface(
            deferred_reads,
            path=normalized,
            trigger=str((existing or {}).get("trigger") or trigger),
            reason=str((existing or {}).get("reason") or reason),
        )

    updated_payload = {
        **runtime_mode_payload,
        "mode_envelope": {
            **(runtime_mode_payload.get("mode_envelope") or {}),
            "minimum_mandatory_context": focused_reads,
            "deferred_context": deferred_reads,
        },
    }
    return {
        "runtime_mode_payload": updated_payload,
        "must_read_now": focused_reads,
        "may_defer_until_trigger": deferred_reads,
    }


def refocus_context_for_active_submode(
    *,
    runtime_mode_payload: dict[str, Any],
    must_read_now: list[dict[str, str]],
    may_defer_until_trigger: list[dict[str, str]],
    l1_vault: dict[str, Any],
    canonical_index_path: str | None,
    workspace_staging_manifest_path: str | None,
    validation_contract_path: str | None = None,
    validation_review_bundle_path: str | None = None,
    promotion_readiness_path: str | None = None,
    promotion_gate_path: str | None = None,
) -> dict[str, Any]:
    if str(runtime_mode_payload.get("active_submode") or "") != "literature":
        return {
            "runtime_mode_payload": runtime_mode_payload,
            "must_read_now": must_read_now,
            "may_defer_until_trigger": may_defer_until_trigger,
        }

    focused_reads: list[dict[str, str]] = []
    deferred_reads = list(may_defer_until_trigger)
    for row in must_read_now:
        path = str(row.get("path") or "").strip()
        reason = str(row.get("reason") or "").strip()
        matched_defer = False
        for suffix, trigger, deferred_reason in _literature_defer_rules():
            if path.endswith(suffix):
                _append_deferred_surface(
                    deferred_reads,
                    path=path,
                    trigger=trigger,
                    reason=deferred_reason,
                )
                matched_defer = True
                break
        if matched_defer:
            continue
        if path.endswith(tuple(t for t in _literature_tokens()["keep_suffixes"])):
            _append_path_reason(focused_reads, path=path, reason=reason or "Keep this runtime control surface visible.")

    for wiki_path in _literature_wiki_paths(l1_vault):
        _append_path_reason(
            focused_reads,
            path=wiki_path,
            reason="Current L1 vault wiki page for literature-intake extraction and bounded source distillation.",
        )
    _append_path_reason(
        focused_reads,
        path=workspace_staging_manifest_path,
        reason="Current staging manifest for duplicate checks and fast-path L2 writeback visibility.",
    )
    _append_path_reason(
        focused_reads,
        path=canonical_index_path,
        reason="Current canonical L2 index for checking whether the source-backed knowledge already exists.",
    )
    _append_deferred_surface(
        deferred_reads,
        path=validation_review_bundle_path,
        trigger="verification_route_selection",
        reason="Validation review is deferred while the current route is still literature-intake staging.",
    )
    _append_deferred_surface(
        deferred_reads,
        path=validation_contract_path,
        trigger="verification_route_selection",
        reason="Validation contracts become mandatory only after literature staging yields a candidate worth checking.",
    )
    _append_deferred_surface(
        deferred_reads,
        path=promotion_readiness_path,
        trigger="promotion_intent",
        reason="Promotion-readiness review is deferred while the current route is still literature-intake staging.",
    )
    _append_deferred_surface(
        deferred_reads,
        path=promotion_gate_path,
        trigger="promotion_intent",
        reason="Promotion-gate review is deferred while the current route is still literature-intake staging.",
    )

    updated_payload = {
        **runtime_mode_payload,
        "mode_envelope": {
            **(runtime_mode_payload.get("mode_envelope") or {}),
            "minimum_mandatory_context": focused_reads,
            "deferred_context": deferred_reads,
        },
    }
    return {
        "runtime_mode_payload": updated_payload,
        "must_read_now": focused_reads,
        "may_defer_until_trigger": deferred_reads,
    }


def refocus_context_for_runtime_mode(
    *,
    runtime_mode_payload: dict[str, Any],
    must_read_now: list[dict[str, str]],
    may_defer_until_trigger: list[dict[str, str]],
    topic_dashboard_path: str | None = None,
    research_question_contract_note_path: str | None = None,
    control_note_path: str | None = None,
    topic_synopsis_path: str | None = None,
    idea_packet_path: str | None = None,
    operator_checkpoint_path: str | None = None,
    validation_contract_path: str | None = None,
    validation_review_bundle_path: str | None = None,
    promotion_readiness_path: str | None = None,
    promotion_gate_path: str | None = None,
    topic_completion_path: str | None = None,
    verification_route_paths: list[str] | None = None,
    l1_vault: dict[str, Any] | None = None,
    canonical_index_path: str | None = None,
    workspace_staging_manifest_path: str | None = None,
) -> dict[str, Any]:
    if str(runtime_mode_payload.get("active_submode") or "") == "literature":
        return refocus_context_for_active_submode(
            runtime_mode_payload=runtime_mode_payload,
            must_read_now=must_read_now,
            may_defer_until_trigger=may_defer_until_trigger,
            l1_vault=l1_vault or {},
            canonical_index_path=canonical_index_path,
            workspace_staging_manifest_path=workspace_staging_manifest_path,
            validation_contract_path=validation_contract_path,
            validation_review_bundle_path=validation_review_bundle_path,
            promotion_readiness_path=promotion_readiness_path,
            promotion_gate_path=promotion_gate_path,
        )

    runtime_mode = str(runtime_mode_payload.get("runtime_mode") or "").strip()
    verification_route_rows = [
        (path, "Current selected validation route or execution-handoff surface for explicit verification work.")
        for path in (verification_route_paths or [])
        if str(path or "").strip()
    ]
    shared_primary_rows = [
        (topic_dashboard_path, "Primary human runtime surface for the current topic."),
            (research_question_contract_note_path, "Active research question, scope, and chosen approach contract."),
    ]

    if runtime_mode == "explore":
        prioritized_paths = list(shared_primary_rows)
        if str((runtime_mode_payload.get("mode_envelope") or {}).get("load_profile") or "") == "full":
            prioritized_paths.extend(
                [
                    (idea_packet_path, "Current idea packet for L3-I ideation."),
                    (operator_checkpoint_path, "Active operator checkpoint before deeper execution."),
                    (control_note_path, "Current human steering note for this topic."),
                    (topic_synopsis_path, "Machine synopsis for the current bounded candidate route and queue state."),
                ]
            )
        deferred_rules = [
            (
                validation_review_bundle_path,
                "verification_route_selection",
                "Validation review stays deferred while the route is still exploratory.",
            ),
            (
                validation_contract_path,
                "verification_route_selection",
                "Validation-contract details stay deferred while the route is still exploratory.",
            ),
            (
                promotion_readiness_path,
                "promotion_intent",
                "Promotion-readiness review is deferred until the route becomes a writeback candidate.",
            ),
            (
                promotion_gate_path,
                "promotion_intent",
                "Promotion-gate review is deferred until the route becomes a writeback candidate.",
            ),
            (
                topic_completion_path,
                "verification_route_selection",
                "Topic-completion review is deferred until the route exits exploration and enters learn mode.",
            ),
        ]
        return _refocus_by_rules(
            runtime_mode_payload=runtime_mode_payload,
            must_read_now=must_read_now,
            may_defer_until_trigger=may_defer_until_trigger,
            prioritized_paths=prioritized_paths,
            deferred_rules=deferred_rules,
        )

    if runtime_mode == "learn":
        prioritized_paths = [
            *shared_primary_rows,
            (validation_review_bundle_path, "Primary L4 review surface for the active L3-A <-> L4 loop."),
            (validation_contract_path, "Current validation route, required checks, and failure modes for this topic."),
            *verification_route_rows,
            (topic_completion_path, "Topic-completion support surface for remaining blockers and regression debt."),
        ]
        deferred_rules = [
            (
                control_note_path,
                "decision_override_present",
                "Human steering history is deferred unless a decision override becomes the current blocker.",
            ),
            (
                topic_synopsis_path,
                "runtime_truth_audit",
                "Machine synopsis details are deferred until a runtime-truth audit is needed.",
            ),
            (
                promotion_readiness_path,
                "promotion_intent",
                "Promotion-readiness review stays deferred until verification yields a writeback candidate.",
            ),
            (
                promotion_gate_path,
                "promotion_intent",
                "Promotion-gate review stays deferred until verification yields a writeback candidate.",
            ),
        ]
        return _refocus_by_rules(
            runtime_mode_payload=runtime_mode_payload,
            must_read_now=must_read_now,
            may_defer_until_trigger=may_defer_until_trigger,
            prioritized_paths=prioritized_paths,
            deferred_rules=deferred_rules,
        )

    if runtime_mode == "implement":
        prioritized_paths = [
            *shared_primary_rows,
            (idea_packet_path, "Active L3-I idea driving the implementation pipeline."),
            (promotion_readiness_path, "Promotion blockers, ready candidates, and gate posture for the current writeback decision."),
            (promotion_gate_path, "Current promotion gate, backend target, and writeback receipt surface."),
            (validation_review_bundle_path, "Supporting L4 review surface behind the current writeback decision."),
            (topic_completion_path, "Topic-completion support surface for remaining regression debt before writeback."),
        ]
        deferred_rules = [
            (
                control_note_path,
                "decision_override_present",
                "Human steering history is deferred unless a decision override becomes active.",
            ),
            (
                topic_synopsis_path,
                "runtime_truth_audit",
                "Machine synopsis details are deferred unless gate debugging requires a runtime-truth audit.",
            ),
            (
                validation_contract_path,
                "verification_route_selection",
                "Low-level validation-route details are deferred unless gate review falls back into fresh verification work.",
            ),
        ]
        return _refocus_by_rules(
            runtime_mode_payload=runtime_mode_payload,
            must_read_now=must_read_now,
            may_defer_until_trigger=may_defer_until_trigger,
            prioritized_paths=prioritized_paths,
            deferred_rules=deferred_rules,
        )

    return {
        "runtime_mode_payload": runtime_mode_payload,
        "must_read_now": must_read_now,
        "may_defer_until_trigger": may_defer_until_trigger,
    }


def dedupe_surface_entries(surfaces: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    for surface in surfaces:
        key = f"{surface['surface']}::{surface['path']}"
        if key not in seen:
            seen.add(key)
            deduped.append(surface)
    return deduped
