from __future__ import annotations

from typing import Any


def empty_research_judgment(
    *,
    topic_slug: str,
    run_id: str,
    updated_by: str,
) -> dict[str, Any]:
    return {
        "artifact_kind": "research_judgment",
        "topic_slug": topic_slug,
        "run_id": run_id,
        "status": "steady",
        "selected_action_id": None,
        "selected_action_summary": "No bounded action is currently selected.",
        "momentum": {
            "status": "unknown",
            "summary": "No bounded momentum signal is currently recorded.",
            "evidence_refs": [],
        },
        "stuckness": {
            "status": "none",
            "signal_count": 0,
            "latest_summary": "No durable stuckness signal is currently recorded.",
            "memory_ids": [],
            "evidence_refs": [],
        },
        "surprise": {
            "status": "none",
            "signal_count": 0,
            "latest_summary": "No durable surprise signal is currently recorded.",
            "memory_ids": [],
            "evidence_refs": [],
        },
        "guidance": [],
        "summary": "Momentum `unknown`; stuckness `none`; surprise `none`.",
        "updated_at": "",
        "updated_by": updated_by,
    }


def _topic_memory_rows(self, *, topic_slug: str, memory_kind: str) -> list[dict[str, Any]]:
    return [
        row
        for row in self._load_collaborator_memory_rows()
        if str(row.get("memory_kind") or "").strip() == memory_kind
        and self._collaborator_memory_matches_topic(row, topic_slug)
    ]


def _dedup_refs(self, refs: list[str]) -> list[str]:
    return self._dedupe_strings([str(ref).strip() for ref in refs if str(ref).strip()])


def derive_research_judgment(
    self,
    *,
    topic_slug: str,
    latest_run_id: str,
    updated_by: str,
    topic_status_explainability: dict[str, Any],
    selected_pending_action: dict[str, Any] | None,
    open_gap_summary: dict[str, Any],
    strategy_memory: dict[str, Any],
    dependency_state: dict[str, Any],
    gap_map_path: str,
) -> dict[str, Any]:
    payload = empty_research_judgment(
        topic_slug=topic_slug,
        run_id=latest_run_id,
        updated_by=updated_by,
    )
    current_route_choice = topic_status_explainability.get("current_route_choice") or {}
    active_human_need = topic_status_explainability.get("active_human_need") or {}
    last_evidence_return = topic_status_explainability.get("last_evidence_return") or {}
    selected_action_id = str((selected_pending_action or {}).get("action_id") or "").strip() or None
    selected_action_summary = (
        str((selected_pending_action or {}).get("summary") or "").strip()
        or "No bounded action is currently selected."
    )

    stuckness_rows = _topic_memory_rows(self, topic_slug=topic_slug, memory_kind="stuckness")
    surprise_rows = _topic_memory_rows(self, topic_slug=topic_slug, memory_kind="surprise")
    trajectory_rows = _topic_memory_rows(self, topic_slug=topic_slug, memory_kind="trajectory")
    collaborator_note_ref = self._relativize(self._collaborator_memory_paths()["note"])
    collaborator_json_ref = self._relativize(self._collaborator_memory_paths()["jsonl"])
    strategy_latest_ref = str(strategy_memory.get("latest_path") or "").strip()
    last_evidence_ref = str(last_evidence_return.get("path") or "").strip()

    if str(active_human_need.get("status") or "").strip() == "requested":
        momentum_status = "held"
        momentum_summary = (
            str(active_human_need.get("summary") or "").strip()
            or "Momentum is held at an active human checkpoint."
        )
        momentum_refs = _dedup_refs(
            self,
            [
                str(active_human_need.get("path") or ""),
                str(current_route_choice.get("next_action_decision_note_path") or ""),
            ],
        )
    elif str(dependency_state.get("status") or "").strip() == "dependency_blocked":
        momentum_status = "stalled"
        momentum_summary = (
            str(dependency_state.get("summary") or "").strip()
            or "Momentum is stalled by an active topic dependency."
        )
        momentum_refs = [self._relativize(self._active_topics_registry_paths()["json"])]
    elif bool(open_gap_summary.get("requires_l0_return")) or str(open_gap_summary.get("status") or "").strip() == "capability_gap":
        momentum_status = "stalled"
        momentum_summary = (
            str(open_gap_summary.get("summary") or "").strip()
            or "Momentum is stalled until the current gap surface is discharged."
        )
        momentum_refs = _dedup_refs(self, [gap_map_path])
    elif str(last_evidence_return.get("status") or "").strip() == "available":
        momentum_status = "advancing"
        momentum_summary = (
            str(last_evidence_return.get("summary") or "").strip()
            or "Momentum is advancing from a recent durable evidence return."
        )
        momentum_refs = _dedup_refs(self, [last_evidence_ref, strategy_latest_ref])
    elif selected_action_id:
        momentum_status = "queued"
        momentum_summary = f"The current bounded route is queued on `{selected_action_summary}`."
        momentum_refs = _dedup_refs(
            self,
            [
                str(current_route_choice.get("next_action_decision_note_path") or ""),
                strategy_latest_ref,
            ],
        )
    else:
        momentum_status = "unknown"
        momentum_summary = "No bounded momentum signal is currently recorded."
        momentum_refs = []

    stuckness_refs = _dedup_refs(self, [collaborator_note_ref, collaborator_json_ref, gap_map_path, strategy_latest_ref])
    if stuckness_rows:
        stuckness_status = "active"
        stuckness_summary = str(stuckness_rows[0].get("summary") or "").strip() or "A stuckness signal is active."
        stuckness_count = len(stuckness_rows)
        stuckness_ids = [str(row.get("memory_id") or "") for row in stuckness_rows if str(row.get("memory_id") or "").strip()]
    elif str(open_gap_summary.get("status") or "").strip() in {"open", "return_to_L0", "capability_gap"}:
        stuckness_status = "active"
        stuckness_summary = (
            str(open_gap_summary.get("summary") or "").strip()
            or "The current gap surface indicates bounded stuckness."
        )
        stuckness_count = 1
        stuckness_ids = []
    elif int(strategy_memory.get("harmful_count") or 0) > 0 and int(strategy_memory.get("relevant_count") or 0) > 0:
        stuckness_status = "active"
        stuckness_summary = "Relevant harmful strategy memory overlaps with the current bounded route."
        stuckness_count = 1
        stuckness_ids = []
    else:
        stuckness_status = "none"
        stuckness_summary = "No durable stuckness signal is currently recorded."
        stuckness_count = 0
        stuckness_ids = []
        stuckness_refs = []

    surprise_refs = _dedup_refs(self, [collaborator_note_ref, collaborator_json_ref])
    if surprise_rows:
        surprise_status = "active"
        surprise_summary = str(surprise_rows[0].get("summary") or "").strip() or "A surprise signal is active."
        surprise_count = len(surprise_rows)
        surprise_ids = [str(row.get("memory_id") or "") for row in surprise_rows if str(row.get("memory_id") or "").strip()]
    else:
        surprise_status = "none"
        surprise_summary = "No durable surprise signal is currently recorded."
        surprise_count = 0
        surprise_ids = []
        surprise_refs = []

    guidance = []
    if momentum_status == "held":
        guidance.append("Resolve the active human checkpoint before trusting heuristic queue selection.")
    elif momentum_status == "stalled":
        guidance.append("Do not keep the current route on autopilot; discharge the blocker or reroute explicitly.")
    if stuckness_status == "active":
        guidance.append("Read the stuckness signal before repeating the same bounded route.")
    if surprise_status == "active":
        guidance.append("Read the surprise signal before smoothing the anomaly into routine prose.")
    guidance.extend(list(strategy_memory.get("guidance") or []))
    if trajectory_rows:
        guidance.append(
            f"Latest trajectory signal: {str(trajectory_rows[0].get('summary') or '').strip() or 'review the current trajectory note.'}"
        )
    guidance = self._dedupe_strings(guidance)

    payload["selected_action_id"] = selected_action_id
    payload["selected_action_summary"] = selected_action_summary
    payload["momentum"] = {
        "status": momentum_status,
        "summary": momentum_summary,
        "evidence_refs": momentum_refs,
    }
    payload["stuckness"] = {
        "status": stuckness_status,
        "signal_count": stuckness_count,
        "latest_summary": stuckness_summary,
        "memory_ids": stuckness_ids,
        "evidence_refs": stuckness_refs,
    }
    payload["surprise"] = {
        "status": surprise_status,
        "signal_count": surprise_count,
        "latest_summary": surprise_summary,
        "memory_ids": surprise_ids,
        "evidence_refs": surprise_refs,
    }
    payload["guidance"] = guidance
    payload["status"] = (
        "signals_active"
        if stuckness_status == "active" or surprise_status == "active" or momentum_status in {"held", "stalled"}
        else "steady"
    )
    payload["summary"] = (
        f"Momentum `{momentum_status}`; stuckness `{stuckness_status}`; surprise `{surprise_status}`."
        + (f" {guidance[0]}" if guidance else "")
    )
    payload["updated_at"] = self._coalesce_string(
        str(topic_status_explainability.get("updated_at") or "").strip(),
        str((stuckness_rows[0] if stuckness_rows else {}).get("recorded_at") or "").strip(),
        str((surprise_rows[0] if surprise_rows else {}).get("recorded_at") or "").strip(),
        str((trajectory_rows[0] if trajectory_rows else {}).get("recorded_at") or "").strip(),
    )
    payload["updated_by"] = updated_by
    return payload


def render_research_judgment_markdown(payload: dict[str, Any]) -> str:
    momentum = payload.get("momentum") or {}
    stuckness = payload.get("stuckness") or {}
    surprise = payload.get("surprise") or {}
    lines = [
        "# Research judgment",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Run id: `{payload.get('run_id') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Selected action id: `{payload.get('selected_action_id') or '(none)'}`",
        f"- Selected action summary: {payload.get('selected_action_summary') or '(missing)'}",
        "",
        payload.get("summary") or "(missing)",
        "",
        "## Momentum",
        "",
        f"- Status: `{momentum.get('status') or '(missing)'}`",
        f"- Evidence refs: `{', '.join(momentum.get('evidence_refs') or []) or '(none)'}`",
        "",
        momentum.get("summary") or "(missing)",
        "",
        "## Stuckness",
        "",
        f"- Status: `{stuckness.get('status') or '(missing)'}`",
        f"- Signal count: `{stuckness.get('signal_count') or 0}`",
        f"- Memory ids: `{', '.join(stuckness.get('memory_ids') or []) or '(none)'}`",
        f"- Evidence refs: `{', '.join(stuckness.get('evidence_refs') or []) or '(none)'}`",
        "",
        stuckness.get("latest_summary") or "(missing)",
        "",
        "## Surprise",
        "",
        f"- Status: `{surprise.get('status') or '(missing)'}`",
        f"- Signal count: `{surprise.get('signal_count') or 0}`",
        f"- Memory ids: `{', '.join(surprise.get('memory_ids') or []) or '(none)'}`",
        f"- Evidence refs: `{', '.join(surprise.get('evidence_refs') or []) or '(none)'}`",
        "",
        surprise.get("latest_summary") or "(missing)",
        "",
        "## Guidance",
        "",
    ]
    for row in payload.get("guidance") or ["(none)"]:
        lines.append(f"- {row}")
    return "\n".join(lines) + "\n"
