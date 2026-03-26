#!/usr/bin/env python3
"""Sync a topic-level runtime resume state from existing layer artifacts."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

from closed_loop_v1 import compute_closed_loop_status
from research_mode_profiles import resolve_task_research_profile


VALID_RESUME_STAGES = {"L0", "L1", "L2", "L3", "L4"}
NEXT_ACTIONS_CONTRACT_FILENAME = "next_actions.contract.json"
NEXT_ACTION_DECISION_CONTRACT_FILENAME = "next_action_decision.contract.json"
NEXT_ACTION_DECISION_CONTRACT_NOTE_FILENAME = "next_action_decision.contract.md"
ACTION_QUEUE_CONTRACT_GENERATED_FILENAME = "action_queue_contract.generated.json"
ACTION_QUEUE_CONTRACT_GENERATED_NOTE_FILENAME = "action_queue_contract.generated.md"
DEFERRED_BUFFER_FILENAME = "deferred_candidates.json"
DEFERRED_BUFFER_NOTE_FILENAME = "deferred_candidates.md"
FOLLOWUP_SUBTOPICS_FILENAME = "followup_subtopics.jsonl"
FOLLOWUP_SUBTOPICS_NOTE_FILENAME = "followup_subtopics.md"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows)
    path.write_text(text, encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_next_actions(path: Path) -> list[str]:
    if not path.exists():
        return []
    actions: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        numbered_match = re.match(r"^\d+\.\s+(.*)$", line)
        if numbered_match:
            actions.append(numbered_match.group(1).strip())
            continue
        if line.startswith(("- ", "* ")):
            actions.append(line[2:].strip())
    return actions


def load_next_actions_contract(path: Path | None) -> dict | None:
    if path is None:
        return None
    contract_path = path.parent / NEXT_ACTIONS_CONTRACT_FILENAME
    if not contract_path.exists():
        return None
    return read_json(contract_path)


def parse_contract_actions(contract: dict | None) -> list[str]:
    if not contract:
        return []
    rows = contract.get("actions")
    if not isinstance(rows, list):
        return []
    actions: list[str] = []
    for row in rows:
        if not isinstance(row, dict) or row.get("enabled") is False:
            continue
        summary = str(row.get("summary") or "").strip()
        if summary:
            actions.append(summary)
    return actions


def buffer_entry_ready_for_reactivation(entry: dict, source_ids: set[str], source_text: str, child_topics: set[str]) -> bool:
    conditions = entry.get("reactivation_conditions") or {}
    source_rules = {
        str(value).strip()
        for value in (conditions.get("source_ids_any") or [])
        if str(value).strip()
    }
    if source_rules and source_ids.intersection(source_rules):
        return True
    text_rules = [
        str(value).strip().lower()
        for value in (conditions.get("text_contains_any") or [])
        if str(value).strip()
    ]
    if text_rules and any(rule in source_text for rule in text_rules):
        return True
    child_topic_rules = {
        str(value).strip()
        for value in (conditions.get("child_topics_any") or [])
        if str(value).strip()
    }
    if child_topic_rules and child_topics.intersection(child_topic_rules):
        return True
    return not source_rules and not text_rules and not child_topic_rules


def latest_run_id(runs_root: Path) -> str | None:
    if not runs_root.exists():
        return None
    run_names = sorted(path.name for path in runs_root.iterdir() if path.is_dir())
    return run_names[-1] if run_names else None


def relative_path(path: Path | None, root: Path) -> str | None:
    if path is None or not path.exists():
        return None
    return path.relative_to(root).as_posix()


def resolve_card_path(path_value: str | None, knowledge_root: Path) -> Path | None:
    if not path_value or not str(path_value).strip():
        return None
    candidate = Path(str(path_value).strip()).expanduser()
    if not candidate.is_absolute():
        candidate = knowledge_root / candidate
    resolved = candidate.resolve()
    return resolved if resolved.exists() else None


def load_backend_registry_rows(knowledge_root: Path) -> list[dict]:
    return read_jsonl(knowledge_root / "canonical" / "backends" / "backend_index.jsonl")


def scan_backend_cards(knowledge_root: Path) -> dict[str, Path]:
    backend_root = knowledge_root / "canonical" / "backends"
    discovered: dict[str, Path] = {}
    for card_path in backend_root.rglob("*.json"):
        if card_path.name == "backend.template.json":
            continue
        if "examples" in card_path.parts:
            continue
        payload = read_json(card_path)
        backend_id = str((payload or {}).get("backend_id") or "").strip()
        if backend_id and backend_id not in discovered:
            discovered[backend_id] = card_path.resolve()
    return discovered


def build_backend_bridges(l0_source_rows: list[dict], knowledge_root: Path) -> list[dict]:
    grouped_rows: dict[str, list[dict]] = {}
    for row in l0_source_rows:
        provenance = row.get("provenance") or {}
        backend_id = str(provenance.get("backend_id") or "").strip()
        if backend_id:
            grouped_rows.setdefault(backend_id, []).append(row)

    if not grouped_rows:
        return []

    registry_rows = load_backend_registry_rows(knowledge_root)
    registry_by_id = {
        str(row.get("backend_id") or "").strip(): row
        for row in registry_rows
        if str(row.get("backend_id") or "").strip()
    }
    scanned_cards = scan_backend_cards(knowledge_root)
    bridges: list[dict] = []

    for backend_id in sorted(grouped_rows):
        rows = grouped_rows[backend_id]
        provenance = rows[0].get("provenance") or {}
        registry_row = registry_by_id.get(backend_id) or {}

        explicit_card_path = resolve_card_path(str(provenance.get("backend_card_path") or ""), knowledge_root)
        registry_card_path = resolve_card_path(str(registry_row.get("card_path") or ""), knowledge_root)
        scanned_card_path = scanned_cards.get(backend_id)
        card_path = explicit_card_path or registry_card_path or scanned_card_path
        card_payload = read_json(card_path) if card_path is not None else None

        artifact_kinds = sorted(
            {
                str((row.get("provenance") or {}).get("backend_artifact_kind") or "").strip()
                for row in rows
                if str((row.get("provenance") or {}).get("backend_artifact_kind") or "").strip()
            }
        )
        source_ids = [
            str(row.get("source_id") or "").strip()
            for row in rows
            if str(row.get("source_id") or "").strip()
        ]
        backend_root = str(
            provenance.get("backend_root")
            or ((card_payload or {}).get("root_paths") or [None])[0]
            or ""
        ).strip()

        bridges.append(
            {
                "backend_id": backend_id,
                "title": str((card_payload or {}).get("title") or registry_row.get("title") or backend_id),
                "backend_type": str(
                    (card_payload or {}).get("backend_type")
                    or registry_row.get("backend_type")
                    or "(missing)"
                ),
                "status": str((card_payload or {}).get("status") or registry_row.get("status") or "(missing)"),
                "card_path": relative_path(card_path, knowledge_root)
                if card_path is not None and str(card_path).startswith(str(knowledge_root))
                else (str(card_path) if card_path is not None else str(provenance.get("backend_card_path") or "") or None),
                "card_status": "present" if card_payload else "missing",
                "backend_root": backend_root or "(missing)",
                "artifact_granularity": str((card_payload or {}).get("artifact_granularity") or "(missing)"),
                "artifact_kinds": artifact_kinds,
                "canonical_targets": list(
                    (card_payload or {}).get("canonical_targets")
                    or registry_row.get("canonical_targets")
                    or []
                ),
                "retrieval_hints": list((card_payload or {}).get("retrieval_hints") or []),
                "l0_registration_script": str(
                    ((card_payload or {}).get("l0_registration") or {}).get("script") or "(missing)"
                ),
                "source_count": len(source_ids),
                "source_ids": source_ids,
            }
        )
    return bridges


def infer_resume_state(
    intake_status: dict | None,
    feedback_status: dict | None,
    latest_decision: dict | None,
    closed_loop_decision: dict | None,
) -> tuple[str, str, str]:
    if latest_decision:
        verdict = latest_decision.get("verdict", "unknown")
        fallback_targets = latest_decision.get("fallback_targets") or []
        if verdict in {"accepted", "promoted"}:
            return "L2", "L4", "Latest validation promoted material into Layer 2."
        if verdict in {"deferred", "rejected", "needs_revision"}:
            if fallback_targets:
                first_target = fallback_targets[0]
                if str(first_target).startswith("feedback/"):
                    return (
                        "L3",
                        "L4",
                        f"Latest Layer 4 verdict is {verdict}; resume exploratory work in Layer 3.",
                    )
                if str(first_target).startswith("intake/"):
                    return (
                        "L1",
                        "L4",
                        f"Latest Layer 4 verdict is {verdict}; resume source-bound work in Layer 1.",
                    )
            return "L4", "L4", f"Latest Layer 4 verdict is {verdict}; inspect the validation record."

    if closed_loop_decision:
        decision = closed_loop_decision.get("decision", "unknown")
        if decision == "keep":
            return "L4", "L4", "Latest closed-loop decision kept the route; inspect the Layer 4 writeback before any promotion."
        if decision in {"revise", "discard", "defer"}:
            return "L3", "L4", f"Latest closed-loop decision is {decision}; resume exploratory work in Layer 3."
        return "L4", "L4", "A Layer 4 closed-loop decision exists; inspect the validation writeback."

    if feedback_status:
        return "L3", "L3", "A Layer 3 run exists without a later decision artifact."

    if intake_status:
        next_stage = intake_status.get("next_stage")
        if next_stage in VALID_RESUME_STAGES:
            return next_stage, "L1", f"Layer 1 status points next to {next_stage}."
        return "L1", "L1", "Only Layer 1 intake artifacts are currently materialized."

    return "L0", "L0", "No layer artifacts were found for this topic."


def build_resume_markdown(state: dict) -> str:
    pointers = state["pointers"]
    layer_status = state["layer_status"]
    backend_bridges = state.get("backend_bridges") or []
    promotion_gate = state.get("promotion_gate") or {}
    closed_loop = state.get("closed_loop") or {}
    research_mode_profile = state.get("research_mode_profile") or {}
    lines = [
        "# Topic runtime resume",
        "",
        f"- Topic slug: `{state['topic_slug']}`",
        f"- Updated at: `{state['updated_at']}`",
        f"- Updated by: `{state['updated_by']}`",
        f"- Last materialized stage: `{state['last_materialized_stage']}`",
        f"- Resume stage: `{state['resume_stage']}`",
        f"- Latest run id: `{state['latest_run_id'] or '(none)'}`",
        f"- Research mode: `{state.get('research_mode') or '(missing)'}`",
        f"- Active executor kind: `{state.get('active_executor_kind') or '(missing)'}`",
        f"- Active reasoning profile: `{state.get('active_reasoning_profile') or '(missing)'}`",
        "",
        "## Resume reason",
        "",
        f"- {state['resume_reason']}",
        "",
        "## Research-mode governance",
        "",
        f"- Profile path: `{research_mode_profile.get('profile_path') or '(missing)'}`",
        f"- Label: `{research_mode_profile.get('label') or '(missing)'}`",
        f"- Description: {research_mode_profile.get('description') or '(missing)'}",
        "",
        "### Reproducibility expectations",
        "",
    ]
    for item in research_mode_profile.get("reproducibility_expectations") or ["No explicit reproducibility expectation recorded."]:
        lines.append(f"- {item}")
    lines.extend(["", "### Human-readable notes", ""])
    for item in research_mode_profile.get("note_expectations") or ["No explicit note expectation recorded."]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Layer snapshot",
            "",
            f"- L0: `{layer_status['L0']['status']}` ({state['source_count']} sources)",
            f"- L1: `{layer_status['L1']['status']}`",
            f"- L3: `{layer_status['L3']['status']}`",
            f"- L4: `{layer_status['L4']['status']}`",
            f"- Closed loop: `{closed_loop.get('status', 'missing')}`",
            "",
            "## L0 backend bridges",
            "",
        ]
    )
    if backend_bridges:
        for bridge in backend_bridges:
            lines.extend(
                [
                    f"- `{bridge.get('backend_id') or '(missing)'}` title=`{bridge.get('title') or '(missing)'}` "
                    f"type=`{bridge.get('backend_type') or '(missing)'}` status=`{bridge.get('status') or '(missing)'}` "
                    f"card_status=`{bridge.get('card_status') or '(missing)'}` sources=`{bridge.get('source_count', 0)}`",
                    f"  card_path=`{bridge.get('card_path') or '(missing)'}`",
                    f"  backend_root=`{bridge.get('backend_root') or '(missing)'}`",
                    f"  artifact_granularity=`{bridge.get('artifact_granularity') or '(missing)'}`",
                    f"  artifact_kinds=`{', '.join(bridge.get('artifact_kinds') or []) or '(missing)'}`",
                    f"  canonical_targets=`{', '.join(bridge.get('canonical_targets') or []) or '(missing)'}`",
                    f"  l0_registration_script=`{bridge.get('l0_registration_script') or '(missing)'}`",
                ]
            )
    else:
        lines.append("- None registered.")

    lines.extend(
        [
            "",
            "## L2 promotion gate",
            "",
            f"- Status: `{promotion_gate.get('status') or 'not_requested'}`",
            f"- Candidate id: `{promotion_gate.get('candidate_id') or '(missing)'}`",
            f"- Candidate type: `{promotion_gate.get('candidate_type') or '(missing)'}`",
            f"- Backend id: `{promotion_gate.get('backend_id') or '(missing)'}`",
            f"- Target backend root: `{promotion_gate.get('target_backend_root') or '(missing)'}`",
            f"- Review mode: `{promotion_gate.get('review_mode') or '(missing)'}`",
            f"- Canonical layer: `{promotion_gate.get('canonical_layer') or '(missing)'}`",
            f"- Coverage status: `{promotion_gate.get('coverage_status') or '(missing)'}`",
            f"- Consensus status: `{promotion_gate.get('consensus_status') or '(missing)'}`",
            f"- Merge outcome: `{promotion_gate.get('merge_outcome') or '(missing)'}`",
            f"- Gate JSON: `{pointers.get('promotion_gate_path') or '(missing)'}`",
            f"- Gate note: `{pointers.get('promotion_gate_note_path') or '(missing)'}`",
            "",
            "## Closed-loop state",
            "",
            f"- Selected route: `{closed_loop.get('selected_route_id') or '(missing)'}`",
            f"- Execution task: `{closed_loop.get('task_id') or '(missing)'}`",
            f"- Result manifest: `{closed_loop.get('result_id') or '(missing)'}`",
            f"- Latest decision: `{closed_loop.get('latest_decision') or '(missing)'}`",
            f"- Literature follow-ups: `{closed_loop.get('literature_followup_count', 0)}`",
            f"- Follow-up gaps: `{closed_loop.get('followup_gap_count', 0)}`",
            f"- Deferred candidates: `{state.get('deferred_candidate_count', 0)}`",
            f"- Reactivatable deferred entries: `{state.get('reactivable_deferred_count', 0)}`",
            f"- Follow-up subtopics: `{state.get('followup_subtopic_count', 0)}`",
            "",
            "## Pending actions",
            "",
        ]
    )
    if state["pending_actions"]:
        for index, action in enumerate(state["pending_actions"], start=1):
            lines.append(f"{index}. {action}")
    else:
        lines.append("- None recorded.")

    lines.extend(
        [
            "",
            "## Key pointers",
            "",
            f"- L0 source index: `{pointers['l0_source_index_path'] or '(missing)'}`",
            f"- Intake status: `{pointers['intake_status_path'] or '(missing)'}`",
            f"- Feedback status: `{pointers['feedback_status_path'] or '(missing)'}`",
            f"- Next actions: `{pointers['next_actions_path'] or '(missing)'}`",
            f"- Next-actions contract: `{pointers.get('next_actions_contract_path') or '(missing)'}`",
            f"- Promotion decision: `{pointers['promotion_decision_path'] or '(missing)'}`",
            f"- Consultation index: `{pointers['consultation_index_path'] or '(missing)'}`",
            f"- L4 control note: `{pointers['control_note_path'] or '(missing)'}`",
            f"- Innovation direction: `{pointers.get('innovation_direction_path') or '(missing)'}`",
            f"- Innovation decisions: `{pointers.get('innovation_decisions_path') or '(missing)'}`",
            f"- Unfinished work index: `{pointers.get('unfinished_work_path') or '(missing)'}`",
            f"- Unfinished work note: `{pointers.get('unfinished_work_note_path') or '(missing)'}`",
            f"- Next-action decision: `{pointers.get('next_action_decision_path') or '(missing)'}`",
            f"- Next-action decision note: `{pointers.get('next_action_decision_note_path') or '(missing)'}`",
            f"- Next-action decision contract: `{pointers.get('next_action_decision_contract_path') or '(missing)'}`",
            f"- Next-action decision contract note: `{pointers.get('next_action_decision_contract_note_path') or '(missing)'}`",
            f"- Generated queue-contract snapshot: `{pointers.get('action_queue_contract_generated_path') or '(missing)'}`",
            f"- Generated queue-contract note: `{pointers.get('action_queue_contract_generated_note_path') or '(missing)'}`",
            f"- Selected validation route: `{pointers.get('selected_validation_route_path') or '(missing)'}`",
            f"- Execution task: `{pointers.get('execution_task_path') or '(missing)'}`",
            f"- Execution notes: `{pointers.get('execution_notes_path') or '(missing)'}`",
            f"- Returned execution result: `{pointers.get('returned_execution_result_path') or '(missing)'}`",
            f"- Result manifest: `{pointers.get('result_manifest_path') or '(missing)'}`",
            f"- Trajectory log: `{pointers.get('trajectory_log_path') or '(missing)'}`",
            f"- Trajectory note: `{pointers.get('trajectory_note_path') or '(missing)'}`",
            f"- Failure classification: `{pointers.get('failure_classification_path') or '(missing)'}`",
            f"- Failure classification note: `{pointers.get('failure_classification_note_path') or '(missing)'}`",
            f"- Decision ledger: `{pointers.get('decision_ledger_path') or '(missing)'}`",
            f"- Literature follow-ups: `{pointers.get('literature_followup_queries_path') or '(missing)'}`",
            f"- Literature follow-up receipts: `{pointers.get('literature_followup_receipts_path') or '(missing)'}`",
            f"- Follow-up gap writeback: `{pointers.get('followup_gap_writeback_path') or '(missing)'}`",
            f"- Follow-up gap writeback note: `{pointers.get('followup_gap_writeback_note_path') or '(missing)'}`",
            f"- Deferred buffer: `{pointers.get('deferred_buffer_path') or '(missing)'}`",
            f"- Deferred buffer note: `{pointers.get('deferred_buffer_note_path') or '(missing)'}`",
            f"- Follow-up subtopics: `{pointers.get('followup_subtopics_path') or '(missing)'}`",
            f"- Follow-up subtopics note: `{pointers.get('followup_subtopics_note_path') or '(missing)'}`",
            "",
            "## Summary",
            "",
            f"- {state['summary']}",
            "",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic-slug", required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--control-note")
    parser.add_argument("--research-mode")
    parser.add_argument("--updated-by", default="codex")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    knowledge_root = Path(__file__).resolve().parents[2]
    runtime_root = knowledge_root / "runtime"
    topic_slug = args.topic_slug
    topic_runtime_root = runtime_root / "topics" / topic_slug
    existing_topic_state = read_json(topic_runtime_root / "topic_state.json") or {}
    existing_pointers = existing_topic_state.get("pointers") or {}

    source_layer_topic_root = knowledge_root / "source-layer" / "topics" / topic_slug
    intake_topic_root = knowledge_root / "intake" / "topics" / topic_slug
    feedback_runs_root = knowledge_root / "feedback" / "topics" / topic_slug / "runs"
    validation_runs_root = knowledge_root / "validation" / "topics" / topic_slug / "runs"
    consultation_root = knowledge_root / "consultation" / "topics" / topic_slug

    detected_run_id = args.run_id
    if not detected_run_id:
        detected_run_id = latest_run_id(validation_runs_root) or latest_run_id(feedback_runs_root)

    l0_source_index_path = source_layer_topic_root / "source_index.jsonl"
    intake_status_path = intake_topic_root / "status.json"
    feedback_status_path = (
        feedback_runs_root / detected_run_id / "status.json" if detected_run_id else None
    )
    next_actions_path = (
        feedback_runs_root / detected_run_id / "next_actions.md" if detected_run_id else None
    )
    promotion_decisions_path = (
        validation_runs_root / detected_run_id / "promotion_decisions.jsonl"
        if detected_run_id
        else None
    )
    consultation_index_path = consultation_root / "consultation_index.jsonl"

    l0_source_rows = read_jsonl(l0_source_index_path)
    intake_status = read_json(intake_status_path)
    feedback_status = read_json(feedback_status_path) if feedback_status_path else None
    promotion_rows = read_jsonl(promotion_decisions_path) if promotion_decisions_path else []
    latest_decision = promotion_rows[-1] if promotion_rows else None
    consultation_rows = read_jsonl(consultation_index_path)
    backend_bridges = build_backend_bridges(l0_source_rows, knowledge_root)
    promotion_gate_path = topic_runtime_root / "promotion_gate.json"
    promotion_gate_note_path = topic_runtime_root / "promotion_gate.md"
    deferred_buffer_path = topic_runtime_root / DEFERRED_BUFFER_FILENAME
    deferred_buffer_note_path = topic_runtime_root / DEFERRED_BUFFER_NOTE_FILENAME
    followup_subtopics_path = topic_runtime_root / FOLLOWUP_SUBTOPICS_FILENAME
    followup_subtopics_note_path = topic_runtime_root / FOLLOWUP_SUBTOPICS_NOTE_FILENAME
    promotion_gate = read_json(promotion_gate_path) or {}
    deferred_buffer = read_json(deferred_buffer_path) or {}
    followup_subtopics = read_jsonl(followup_subtopics_path)
    next_actions_contract = load_next_actions_contract(next_actions_path)
    pending_actions = parse_contract_actions(next_actions_contract)
    if not pending_actions and next_actions_path:
        pending_actions = parse_next_actions(next_actions_path)
    closed_loop = compute_closed_loop_status(knowledge_root, topic_slug, detected_run_id)
    closed_loop_task = closed_loop.get("execution_task") or {}
    closed_loop_route = closed_loop.get("selected_route") or {}
    latest_closed_loop_decision = closed_loop.get("latest_decision")
    research_profile = resolve_task_research_profile(
        explicit_mode=args.research_mode,
        task_payload=closed_loop_task,
        route=closed_loop_route,
        existing_topic_state=existing_topic_state,
    )
    research_mode = research_profile["research_mode"]
    active_executor_kind = str(
        closed_loop_task.get("executor_kind")
        or closed_loop_route.get("executor_kind")
        or research_profile["executor_kind"]
    )
    active_reasoning_profile = str(
        closed_loop_task.get("reasoning_profile")
        or closed_loop_route.get("reasoning_profile")
        or research_profile["reasoning_profile"]
    )
    latest_trajectory_log_ref = closed_loop["paths"].get("trajectory_log_path")
    latest_failure_classification_ref = closed_loop["paths"].get("failure_classification_path")
    source_ids = {
        str(row.get("source_id") or "").strip()
        for row in l0_source_rows
        if str(row.get("source_id") or "").strip()
    }
    source_text = " ".join(
        [
            str(row.get("title") or "")
            for row in l0_source_rows
        ]
        + [
            str(row.get("summary") or "")
            for row in l0_source_rows
        ]
    ).lower()
    child_topic_slugs = {
        str(row.get("child_topic_slug") or "").strip()
        for row in followup_subtopics
        if str(row.get("child_topic_slug") or "").strip()
    }
    reactivatable_deferred_count = sum(
        1
        for entry in (deferred_buffer.get("entries") or [])
        if str(entry.get("status") or "") == "buffered"
        and buffer_entry_ready_for_reactivation(entry, source_ids, source_text, child_topic_slugs)
    )

    resume_stage, last_materialized_stage, resume_reason = infer_resume_state(
        intake_status=intake_status,
        feedback_status=feedback_status,
        latest_decision=latest_decision,
        closed_loop_decision=latest_closed_loop_decision,
    )

    l1_status = "missing"
    if intake_status:
        l1_status = intake_status.get("stage", "present")

    l3_status = "missing"
    if feedback_status:
        candidate_status = feedback_status.get("candidate_status")
        l3_status = candidate_status or feedback_status.get("stage", "present")

    l4_status = "missing"
    if latest_decision:
        l4_status = latest_decision.get("verdict", "present")
    elif latest_closed_loop_decision:
        l4_status = latest_closed_loop_decision.get("decision", "present")
    elif closed_loop.get("result_manifest"):
        l4_status = closed_loop["result_manifest"].get("status", "present")

    control_note_rel = args.control_note
    if control_note_rel:
        control_note_rel = str(Path(control_note_rel))
    else:
        control_note_rel = str(existing_pointers.get("control_note_path") or "").strip() or None
    innovation_direction_rel = str(existing_pointers.get("innovation_direction_path") or "").strip() or None
    innovation_decisions_rel = str(existing_pointers.get("innovation_decisions_path") or "").strip() or None

    unfinished_work_path = topic_runtime_root / "unfinished_work.json"
    unfinished_work_note_path = topic_runtime_root / "unfinished_work.md"
    next_action_decision_path = topic_runtime_root / "next_action_decision.json"
    next_action_decision_note_path = topic_runtime_root / "next_action_decision.md"
    next_action_decision_contract_path = topic_runtime_root / NEXT_ACTION_DECISION_CONTRACT_FILENAME
    next_action_decision_contract_note_path = topic_runtime_root / NEXT_ACTION_DECISION_CONTRACT_NOTE_FILENAME
    action_queue_contract_generated_path = topic_runtime_root / ACTION_QUEUE_CONTRACT_GENERATED_FILENAME
    action_queue_contract_generated_note_path = topic_runtime_root / ACTION_QUEUE_CONTRACT_GENERATED_NOTE_FILENAME

    summary_parts = []
    if intake_status:
        summary_parts.append(f"L1={intake_status.get('stage', 'present')}")
    if feedback_status:
        summary_parts.append(f"L3={feedback_status.get('candidate_status') or feedback_status.get('stage', 'present')}")
    if latest_decision:
        summary_parts.append(f"L4={latest_decision.get('verdict', 'present')}")
    elif latest_closed_loop_decision:
        summary_parts.append(f"L4={latest_closed_loop_decision.get('decision', 'present')}")
    if closed_loop.get("selected_route"):
        summary_parts.append(f"closed_loop={closed_loop['selected_route'].get('route_id')}")
    if backend_bridges:
        summary_parts.append(f"backends={len(backend_bridges)}")
    if promotion_gate:
        summary_parts.append(f"promotion_gate={promotion_gate.get('status', 'unknown')}")
    if deferred_buffer.get("entries"):
        summary_parts.append(f"deferred={len(deferred_buffer.get('entries') or [])}")
    if followup_subtopics:
        summary_parts.append(f"followup_subtopics={len(followup_subtopics)}")
    if closed_loop.get("followup_gaps"):
        summary_parts.append(f"followup_gaps={len(closed_loop.get('followup_gaps') or [])}")
    summary_parts.append(f"mode={research_mode}")
    summary_parts.append(f"executor={active_executor_kind}")
    summary = (
        f"Resume at {resume_stage}; "
        + ", ".join(summary_parts)
        + (f"; next action count={len(pending_actions)}" if pending_actions else "")
    ).strip()

    topic_state = {
        "topic_slug": topic_slug,
        "updated_at": now_iso(),
        "updated_by": args.updated_by,
        "latest_run_id": detected_run_id,
        "last_materialized_stage": last_materialized_stage,
        "resume_stage": resume_stage,
        "resume_reason": resume_reason,
        "research_mode": research_mode,
        "research_mode_profile": {
            "profile_path": research_profile["profile"].get("profile_path"),
            "label": research_profile["profile"].get("label"),
            "description": research_profile["profile"].get("description"),
            "reproducibility_expectations": research_profile["reproducibility_expectations"],
            "note_expectations": research_profile["note_expectations"],
        },
        "active_executor_kind": active_executor_kind,
        "active_reasoning_profile": active_reasoning_profile,
        "latest_trajectory_log_ref": latest_trajectory_log_ref,
        "latest_failure_classification_ref": latest_failure_classification_ref,
        "pending_actions": pending_actions,
        "consultation_count": len(consultation_rows),
        "source_count": len(l0_source_rows),
        "backend_bridge_count": len(backend_bridges),
        "backend_bridges": backend_bridges,
        "deferred_candidate_count": len(deferred_buffer.get("entries") or []),
        "reactivable_deferred_count": reactivatable_deferred_count,
        "followup_subtopic_count": len(followup_subtopics),
        "followup_gap_count": len(closed_loop.get("followup_gaps") or []),
        "promotion_gate": {
            "status": str(promotion_gate.get("status") or "not_requested"),
            "candidate_id": str(promotion_gate.get("candidate_id") or ""),
            "candidate_type": str(promotion_gate.get("candidate_type") or ""),
            "backend_id": str(promotion_gate.get("backend_id") or ""),
            "target_backend_root": str(promotion_gate.get("target_backend_root") or ""),
            "review_mode": str(promotion_gate.get("review_mode") or ""),
            "canonical_layer": str(promotion_gate.get("canonical_layer") or ""),
            "coverage_status": str(promotion_gate.get("coverage_status") or ""),
            "consensus_status": str(promotion_gate.get("consensus_status") or ""),
            "merge_outcome": str(promotion_gate.get("merge_outcome") or ""),
            "approved_by": str(promotion_gate.get("approved_by") or ""),
            "promoted_units": list(promotion_gate.get("promoted_units") or []),
        },
        "layer_status": {
            "L0": {
                "status": "present" if l0_source_rows else "missing",
                "source_count": len(l0_source_rows),
                "backend_bridge_count": len(backend_bridges),
            },
            "L1": {
                "status": l1_status,
                "next_stage": intake_status.get("next_stage") if intake_status else None,
                "last_updated": intake_status.get("last_updated") if intake_status else None,
            },
            "L3": {
                "status": l3_status,
                "last_updated": feedback_status.get("last_updated") if feedback_status else None,
            },
            "L4": {
                "status": l4_status,
                "decision_id": latest_decision.get("decision_id") if latest_decision else None,
                "decided_at": latest_decision.get("decided_at") if latest_decision else None,
            },
        },
        "pointers": {
            "l0_source_index_path": relative_path(l0_source_index_path, knowledge_root),
            "intake_status_path": relative_path(intake_status_path, knowledge_root),
            "feedback_status_path": relative_path(feedback_status_path, knowledge_root),
            "next_actions_path": relative_path(next_actions_path, knowledge_root),
            "next_actions_contract_path": relative_path(
                next_actions_path.parent / NEXT_ACTIONS_CONTRACT_FILENAME if next_actions_path else None,
                knowledge_root,
            ),
            "promotion_decision_path": relative_path(promotion_decisions_path, knowledge_root),
            "promotion_gate_path": relative_path(promotion_gate_path, knowledge_root),
            "promotion_gate_note_path": relative_path(promotion_gate_note_path, knowledge_root),
            "deferred_buffer_path": relative_path(deferred_buffer_path, knowledge_root),
            "deferred_buffer_note_path": relative_path(deferred_buffer_note_path, knowledge_root),
            "followup_subtopics_path": relative_path(followup_subtopics_path, knowledge_root),
            "followup_subtopics_note_path": relative_path(followup_subtopics_note_path, knowledge_root),
            "consultation_index_path": relative_path(consultation_index_path, knowledge_root),
            "control_note_path": control_note_rel,
            "innovation_direction_path": innovation_direction_rel,
            "innovation_decisions_path": innovation_decisions_rel,
            "unfinished_work_path": relative_path(unfinished_work_path, knowledge_root),
            "unfinished_work_note_path": relative_path(unfinished_work_note_path, knowledge_root),
            "next_action_decision_path": relative_path(next_action_decision_path, knowledge_root),
            "next_action_decision_note_path": relative_path(next_action_decision_note_path, knowledge_root),
            "next_action_decision_contract_path": relative_path(
                next_action_decision_contract_path,
                knowledge_root,
            ),
            "next_action_decision_contract_note_path": relative_path(
                next_action_decision_contract_note_path,
                knowledge_root,
            ),
            "action_queue_contract_generated_path": relative_path(
                action_queue_contract_generated_path,
                knowledge_root,
            ),
            "action_queue_contract_generated_note_path": relative_path(
                action_queue_contract_generated_note_path,
                knowledge_root,
            ),
            "selected_validation_route_path": relative_path(
                (knowledge_root / closed_loop["paths"]["selected_route_path"])
                if closed_loop["paths"].get("selected_route_path")
                else None,
                knowledge_root,
            ),
            "execution_task_path": relative_path(
                (knowledge_root / closed_loop["paths"]["execution_task_path"])
                if closed_loop["paths"].get("execution_task_path")
                else None,
                knowledge_root,
            ),
            "execution_notes_path": closed_loop["paths"].get("execution_notes_dir"),
            "returned_execution_result_path": closed_loop["paths"].get("returned_result_path"),
            "result_manifest_path": closed_loop["paths"].get("result_manifest_path"),
            "trajectory_log_path": latest_trajectory_log_ref,
            "trajectory_note_path": closed_loop["paths"].get("trajectory_note_path"),
            "failure_classification_path": latest_failure_classification_ref,
            "failure_classification_note_path": closed_loop["paths"].get("failure_classification_note_path"),
            "decision_ledger_path": closed_loop["paths"].get("decision_ledger_path"),
            "literature_followup_queries_path": closed_loop["paths"].get("literature_followup_path"),
            "literature_followup_receipts_path": closed_loop["paths"].get("literature_followup_receipts_path"),
            "followup_gap_writeback_path": closed_loop["paths"].get("followup_gap_writeback_path"),
            "followup_gap_writeback_note_path": closed_loop["paths"].get("followup_gap_writeback_note_path"),
        },
        "closed_loop": {
            "status": (closed_loop.get("latest_decision") or {}).get("decision")
            or (closed_loop.get("result_manifest") or {}).get("status")
            or ("awaiting_result" if closed_loop.get("awaiting_external_result") else "missing"),
            "selected_route_id": (closed_loop.get("selected_route") or {}).get("route_id"),
            "task_id": (closed_loop.get("execution_task") or {}).get("task_id"),
            "result_id": (closed_loop.get("result_manifest") or {}).get("result_id"),
            "latest_decision": (closed_loop.get("latest_decision") or {}).get("decision"),
            "literature_followup_count": len(closed_loop.get("literature_followups") or []),
            "followup_gap_count": len(closed_loop.get("followup_gaps") or []),
            "next_transition": closed_loop.get("next_transition"),
            "research_mode": research_mode,
            "executor_kind": active_executor_kind,
            "reasoning_profile": active_reasoning_profile,
            "trajectory_event_count": len(closed_loop.get("trajectory_log") or []),
            "failure_severity": (closed_loop.get("failure_classification") or {}).get("severity"),
        },
        "summary": summary,
    }

    topic_state_path = topic_runtime_root / "topic_state.json"
    resume_path = topic_runtime_root / "resume.md"
    index_path = runtime_root / "topic_index.jsonl"

    write_json(topic_state_path, topic_state)
    write_text(resume_path, build_resume_markdown(topic_state))

    index_rows = [row for row in read_jsonl(index_path) if row.get("topic_slug") != topic_slug]
    index_rows.append(
        {
            "topic_slug": topic_slug,
            "latest_run_id": detected_run_id,
            "last_materialized_stage": last_materialized_stage,
            "resume_stage": resume_stage,
            "updated_at": topic_state["updated_at"],
            "updated_by": args.updated_by,
            "research_mode": research_mode,
            "active_executor_kind": active_executor_kind,
            "backend_bridge_count": len(backend_bridges),
            "state_path": topic_state_path.relative_to(knowledge_root).as_posix(),
            "resume_path": resume_path.relative_to(knowledge_root).as_posix(),
            "summary": summary,
        }
    )
    write_jsonl(index_path, index_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
