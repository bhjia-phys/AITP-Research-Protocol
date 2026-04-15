from __future__ import annotations

from typing import Any

_MODE_SPECS: dict[str, dict[str, Any]] = {
    "discussion": {
        "local_task": "Clarify direction, shrink ambiguity, and keep the topic inside an honest early-layer envelope.",
        "foreground_layers": ["L0", "L1", "L3"],
        "allowed_backedges": ["L1 -> L0", "L1/L3 -> L2"],
        "required_writeback": ["idea_packet", "operator_checkpoint", "research_question_contract"],
        "forbidden_shortcuts": [
            "Do not treat discussion as validation.",
            "Do not preload heavy L4 or promotion context without a declared trigger.",
        ],
        "human_checkpoint_policy": "Ask only when the ambiguity materially changes route choice or topic direction.",
        "entry_conditions": ["Intent clarification, scope ambiguity, or an unresolved operator checkpoint is active."],
        "exit_conditions": ["Exit when the question is bounded enough for candidate formation or the human redirects the route."],
    },
    "explore": {
        "local_task": "Form or refine a bounded candidate without pretending it is already validated.",
        "foreground_layers": ["L1", "L3"],
        "allowed_backedges": ["L3 -> L0", "L3 -> L2"],
        "required_writeback": ["candidate_packets", "route_choice_notes", "source_recovery_notes"],
        "forbidden_shortcuts": [
            "Do not treat local plausibility as validation.",
            "Do not widen mandatory context beyond the current chosen approach.",
        ],
        "human_checkpoint_policy": "Ask only at real route changes, cost changes, or novelty-definition changes.",
        "entry_conditions": ["A bounded research question exists and work is still forming or refining the candidate route."],
        "exit_conditions": ["Exit when the candidate is concrete enough for L4 validation or when an honest backedge is required."],
    },
    "verify": {
        "local_task": "Validate, adjudicate, or inspect proof/execution obligations for the current bounded candidate.",
        "foreground_layers": ["L4"],
        "allowed_backedges": ["L4 -> L0", "L4 -> L2"],
        "required_writeback": ["validation_result_artifacts", "contradiction_artifacts", "decision_or_route_updates"],
        "forbidden_shortcuts": [
            "Do not let style confidence count as validation.",
            "Do not keep iterating locally after a real L0/L2 blocker is known.",
        ],
        "human_checkpoint_policy": "Ask when the execution lane, resource commitment, or the question of how to judge this is materially open.",
        "entry_conditions": ["Current work is in explicit validation, proof review, or route-selection review."],
        "exit_conditions": ["Exit when validation completes, blocks honestly to L0/L2/human, or hands off to promotion."],
    },
    "promote": {
        "local_task": "Inspect gate state and decide whether L4-backed material may cross the L4 -> L2 boundary.",
        "foreground_layers": ["L4", "L2"],
        "allowed_backedges": ["promote -> L4", "promote -> L0", "promote -> L2"],
        "required_writeback": ["promotion_gate", "promotion_decision", "backend_receipt"],
        "forbidden_shortcuts": [
            "Do not treat consultation as promotion.",
            "Do not treat maturity vibes as gate satisfaction.",
        ],
        "human_checkpoint_policy": "Human checkpoints remain legitimate for writeback and expensive trust moves.",
        "entry_conditions": ["The current action is explicitly reviewing or executing Layer 2 writeback."],
        "exit_conditions": ["Exit when gate review completes or the candidate is rejected back to L4/L0 work."],
    },
}

_PROMOTE_ACTION_TYPES = {
    "request_promotion",
    "approve_promotion",
    "promote_candidate",
    "auto_promote_candidate",
}
_VERIFY_ACTION_TYPES = {
    "select_validation_route",
    "materialize_execution_task",
    "dispatch_execution_task",
    "ingest_execution_result",
    "prepare_lean_bridge",
    "review_proof_repair_plan",
}
_VERIFY_TRIGGERS = {"verification_route_selection", "proof_completion_review", "contradiction_detected"}
_LITERATURE_SOURCE_TOKENS = ("literature", "paper", "source", "arxiv", "pdf")
_LITERATURE_INTAKE_TOKENS = ("read", "extract", "intake", "note", "notes", "summar")
_LITERATURE_KEEP_SUFFIXES = (
    "topic_dashboard.md",
    "research_question.contract.md",
    "control_note.md",
    "idea_packet.md",
    "operator_checkpoint.active.md",
    "graph_analysis.md",
    "topic_synopsis.json",
)
_LITERATURE_DEFER_RULES = (
    (
        "validation_review_bundle.active.md",
        "verification_route_selection",
        "Validation review details are only mandatory once the work leaves literature intake and enters explicit verification.",
    ),
    (
        "validation_contract.active.md",
        "verification_route_selection",
        "Validation-route details are deferred until the work leaves literature intake and enters explicit verification.",
    ),
    (
        "promotion_readiness.json",
        "promotion_intent",
        "Promotion-readiness details are deferred until the work leaves literature intake and approaches writeback.",
    ),
    (
        "promotion_gate.md",
        "promotion_intent",
        "Promotion-gate review is deferred during literature-intake staging.",
    ),
    (
        "topic_completion.json",
        "verification_route_selection",
        "Topic-completion review is deferred while the work is still source-intake staging.",
    ),
    (
        "topic_completion.md",
        "verification_route_selection",
        "Topic-completion review is deferred while the work is still source-intake staging.",
    ),
)
_LITERATURE_SUBMODE_SPEC = {
    "local_task": "Read a source, extract reusable knowledge units, and stage them into L2 without full formal-theory audit.",
    "required_writeback": [
        "l2_staging_entries_with_literature_intake_fast_path",
        "l1_vault_wiki_pages_for_current_source",
    ],
    "entry_conditions": [
        "The current request is source-intake or paper-reading work rather than benchmark execution or proof discharge.",
        "The topic needs reusable literature knowledge staged before a deeper validation route exists.",
    ],
    "exit_conditions": [
        "Exit when the current source has yielded its bounded staged knowledge units.",
        "Exit when the human redirects the route away from literature intake.",
    ],
}
_MODE_ESCALATION_TRIGGERS = {
    "discussion": {
        "decision_override_present",
    },
    "explore": {
        "non_trivial_consultation",
        "capability_gap_blocker",
        "trust_missing",
    },
    "verify": {
        "verification_route_selection",
        "proof_completion_review",
        "contradiction_detected",
    },
    "promote": {
        "promotion_intent",
        "decision_override_present",
    },
}


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
    normalized = " ".join(str(text or "").strip().lower() for text in texts if str(text or "").strip())
    if not normalized:
        return False
    return any(token in normalized for token in _LITERATURE_SOURCE_TOKENS) and any(
        token in normalized for token in _LITERATURE_INTAKE_TOKENS
    )


def _select_active_submode(
    *,
    runtime_mode: str,
    selected_action_type: str,
    selected_action_summary: str,
    human_request: str | None,
    active_triggers: set[str],
) -> str | None:
    if runtime_mode == "verify" and bool(active_triggers & _VERIFY_TRIGGERS):
        return "iterative_verify"
    lowered_summary = selected_action_summary.lower()
    if runtime_mode == "explore" and "l2 staging manifest" in lowered_summary:
        return "literature"
    if runtime_mode == "explore" and _detect_literature_intake_intent(
        selected_action_type,
        selected_action_summary,
        human_request,
    ):
        return "literature"
    return None


def _select_runtime_mode(
    *,
    resume_stage: str | None,
    idea_packet_status: str,
    operator_checkpoint_status: str,
    selected_action_type: str,
    selected_action_summary: str,
    active_triggers: set[str],
) -> str:
    lowered_summary = selected_action_summary.lower()
    if idea_packet_status == "needs_clarification" or operator_checkpoint_status == "requested":
        return "discussion"
    if selected_action_type in _PROMOTE_ACTION_TYPES or any(token in lowered_summary for token in ("promot", "writeback")):
        return "promote"
    if (
        resume_stage == "L4"
        or selected_action_type in _VERIFY_ACTION_TYPES
        or bool(active_triggers & _VERIFY_TRIGGERS)
        or any(token in lowered_summary for token in ("validation", "verification", "proof", "derivation", "selected route"))
    ):
        return "verify"
    return "explore"


def filter_escalation_triggers_for_mode(
    *,
    runtime_mode: str,
    escalation_triggers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    allowed = _MODE_ESCALATION_TRIGGERS.get(str(runtime_mode or "").strip())
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
    if runtime_mode == "promote":
        return {
            "transition_kind": "forward_transition",
            "transition_reason": "The current bounded task is explicitly reviewing or executing the L4 -> L2 boundary.",
            "allowed_targets": ["L2", "L4", "L0"],
            "triggered_by": ["promotion_intent"] if "promotion_intent" in active_triggers else [],
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
        "allowed_targets": list(_MODE_SPECS[runtime_mode]["foreground_layers"]),
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
) -> dict[str, Any]:
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
    )
    active_submode = _select_active_submode(
        runtime_mode=runtime_mode,
        selected_action_type=selected_action_type,
        selected_action_summary=selected_action_summary,
        human_request=human_request,
        active_triggers=active_triggers,
    )
    mode_spec = _MODE_SPECS[runtime_mode]
    transition_posture = _transition_posture(
        runtime_mode=runtime_mode,
        active_triggers=active_triggers,
        operator_checkpoint_status=operator_checkpoint_status,
    )
    local_task = str(mode_spec["local_task"])
    required_writeback = list(mode_spec["required_writeback"])
    entry_conditions = list(mode_spec["entry_conditions"])
    if active_submode:
        if active_submode == "iterative_verify":
            entry_conditions.append("A bounded L3-L4 loop is active and each failed pass can produce explicit feedback.")
        elif active_submode == "literature":
            local_task = str(_LITERATURE_SUBMODE_SPEC["local_task"])
            required_writeback = list(_LITERATURE_SUBMODE_SPEC["required_writeback"])
            entry_conditions.extend(_LITERATURE_SUBMODE_SPEC["entry_conditions"])
    exit_conditions = list(mode_spec["exit_conditions"])
    if active_submode == "literature":
        exit_conditions.extend(_LITERATURE_SUBMODE_SPEC["exit_conditions"])
    if transition_posture["transition_kind"] == "backedge_transition":
        exit_conditions.append("Current work should exit locally once the declared backedge has been materialized.")
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
    }


def runtime_mode_payload_fragment(**kwargs: Any) -> dict[str, Any]:
    mode_contract = build_runtime_mode_contract(**kwargs)
    return {
        "runtime_mode": mode_contract["runtime_mode"],
        "active_submode": mode_contract["active_submode"],
        "mode_envelope": mode_contract["mode_envelope"],
        "transition_posture": mode_contract["transition_posture"],
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
        for suffix, trigger, deferred_reason in _LITERATURE_DEFER_RULES:
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
        if path.endswith(_LITERATURE_KEEP_SUFFIXES):
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

    if runtime_mode == "discussion":
        prioritized_paths = [
            (idea_packet_path, "Clarify the current idea packet before deeper execution."),
            (operator_checkpoint_path, "Resolve the active operator checkpoint before deeper execution."),
            *shared_primary_rows,
            (control_note_path, "Current human steering note for this topic."),
        ]
        deferred_rules = [
            (
                validation_review_bundle_path,
                "verification_route_selection",
                "Validation review details stay deferred until the work enters explicit verification.",
            ),
            (
                validation_contract_path,
                "verification_route_selection",
                "Validation-route details stay deferred until the work enters explicit verification.",
            ),
            (
                promotion_readiness_path,
                "promotion_intent",
                "Promotion-readiness review is deferred while the route is still being clarified.",
            ),
            (
                promotion_gate_path,
                "promotion_intent",
                "Promotion-gate review is deferred while the route is still being clarified.",
            ),
            (
                topic_completion_path,
                "verification_route_selection",
                "Topic-completion review is deferred while the route remains in early discussion.",
            ),
        ]
        return _refocus_by_rules(
            runtime_mode_payload=runtime_mode_payload,
            must_read_now=must_read_now,
            may_defer_until_trigger=may_defer_until_trigger,
            prioritized_paths=prioritized_paths,
            deferred_rules=deferred_rules,
        )

    if runtime_mode == "explore":
        prioritized_paths = list(shared_primary_rows)
        if str((runtime_mode_payload.get("mode_envelope") or {}).get("load_profile") or "") == "full":
            prioritized_paths.extend(
                [
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
                "Topic-completion review is deferred until the route exits exploration and enters verification.",
            ),
        ]
        return _refocus_by_rules(
            runtime_mode_payload=runtime_mode_payload,
            must_read_now=must_read_now,
            may_defer_until_trigger=may_defer_until_trigger,
            prioritized_paths=prioritized_paths,
            deferred_rules=deferred_rules,
        )

    if runtime_mode == "verify":
        prioritized_paths = [
            *shared_primary_rows,
            (validation_review_bundle_path, "Primary L4 review surface for the active verification lane."),
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

    if runtime_mode == "promote":
        prioritized_paths = [
            *shared_primary_rows,
            (promotion_readiness_path, "Promotion blockers, ready candidates, and gate posture for the current writeback decision."),
            (promotion_gate_path, "Current promotion gate, backend target, and writeback receipt surface."),
            (validation_review_bundle_path, "Supporting L4 review surface behind the current writeback decision."),
            (topic_completion_path, "Topic-completion support surface for remaining regression debt before writeback."),
        ]
        deferred_rules = [
            (
                control_note_path,
                "decision_override_present",
                "Human steering history is deferred unless a decision override becomes active during gate review.",
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
