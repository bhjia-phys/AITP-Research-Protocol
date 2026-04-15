#!/usr/bin/env python3
"""Materialize unfinished-work and next-action decision artifacts for one topic."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

UNFINISHED_WORK_FILENAME = "unfinished_work.json"
UNFINISHED_WORK_NOTE_FILENAME = "unfinished_work.md"
NEXT_ACTION_DECISION_FILENAME = "next_action_decision.json"
NEXT_ACTION_DECISION_NOTE_FILENAME = "next_action_decision.md"
NEXT_ACTION_DECISION_CONTRACT_FILENAME = "next_action_decision.contract.json"

SYSTEM_BLOCKING_ACTION_TYPES = {
    "select_validation_route",
    "materialize_execution_task",
    "dispatch_execution_task",
    "ingest_execution_result",
}

ACTIVE_CONTROL_DIRECTIVES = {"follow_control_note", "human_redirect"}
STOP_CONTROL_DIRECTIVES = {"no_action", "stop", "pause"}
RUNTIME_POINTER_KEYS = (
    "next_actions_path",
    "control_note_path",
    "promotion_decision_path",
    "selected_validation_route_path",
    "execution_task_path",
    "result_manifest_path",
    "trajectory_log_path",
    "failure_classification_path",
    "decision_ledger_path",
    "literature_followup_queries_path",
)
TOKEN_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "into",
    "from",
    "than",
    "then",
    "when",
    "what",
    "which",
    "before",
    "after",
    "because",
    "rather",
    "current",
    "existing",
    "follow",
    "control",
    "bundle",
    "result",
    "results",
    "action",
    "actions",
    "work",
}


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
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def ensure_string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        cleaned = value.strip()
        return [cleaned] if cleaned else []
    if not isinstance(value, list):
        return []
    rows: list[str] = []
    for item in value:
        cleaned = str(item or "").strip()
        if cleaned:
            rows.append(cleaned)
    return rows


def unique_list(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def tokenize(text: str) -> set[str]:
    tokens = set(re.findall(r"[a-z0-9]+", text.lower()))
    return {token for token in tokens if len(token) > 2 and token not in TOKEN_STOPWORDS}


def extract_backtick_refs(text: str) -> list[str]:
    return unique_list([item.strip() for item in re.findall(r"`([^`]+)`", text) if item.strip()])


def first_markdown_heading(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or None
    return None


def first_summary_line(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith(("- ", "* ")):
            return stripped[2:].strip() or None
        if re.match(r"^\d+\.\s+", stripped):
            return re.sub(r"^\d+\.\s+", "", stripped).strip() or None
        return stripped
    return None


def parse_scalar(value: str) -> object:
    cleaned = value.strip()
    lowered = cleaned.lower()
    if lowered in {"true", "yes"}:
        return True
    if lowered in {"false", "no"}:
        return False
    if lowered in {"null", "none"}:
        return None
    if cleaned.startswith('"') and cleaned.endswith('"') and len(cleaned) >= 2:
        return cleaned[1:-1]
    if cleaned.startswith("'") and cleaned.endswith("'") and len(cleaned) >= 2:
        return cleaned[1:-1]
    return cleaned


def parse_frontmatter(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    metadata: dict[str, object] = {}
    current_list_key: str | None = None
    body_start = 0
    for index in range(1, len(lines)):
        line = lines[index]
        stripped = line.strip()
        if stripped == "---":
            body_start = index + 1
            break
        if not stripped:
            continue
        if current_list_key and stripped.startswith("- "):
            assert isinstance(metadata[current_list_key], list)
            metadata[current_list_key].append(stripped[2:].strip())
            continue
        if ":" not in line:
            current_list_key = None
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if not key:
            current_list_key = None
            continue
        if raw_value == "":
            metadata[key] = []
            current_list_key = key
        else:
            metadata[key] = parse_scalar(raw_value)
            current_list_key = None

    if body_start == 0:
        return {}, text
    return metadata, "\n".join(lines[body_start:])


def relative_path(path: Path | None, root: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def resolve_note_path(raw_path: str | None, knowledge_root: Path, topic_runtime_root: Path) -> Path | None:
    if not raw_path:
        return None
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    for prefix in (knowledge_root, knowledge_root.parent, topic_runtime_root):
        resolved = prefix / candidate
        if resolved.exists():
            return resolved
    return knowledge_root / candidate


def load_decision_contract(topic_runtime_root: Path) -> dict | None:
    return read_json(topic_runtime_root / NEXT_ACTION_DECISION_CONTRACT_FILENAME)


def normalize_control_directive(raw_value: object) -> str | None:
    value = str(raw_value or "").strip().lower()
    if not value:
        return None
    aliases = {
        "redirect": "human_redirect",
        "human_redirect": "human_redirect",
        "follow_control_note": "follow_control_note",
        "follow": "follow_control_note",
        "continue_unfinished": "continue_unfinished",
        "pause": "pause",
        "stop": "stop",
        "no_action": "no_action",
    }
    return aliases.get(value, value)


def inspect_control_note(
    raw_path: str | None,
    knowledge_root: Path,
    topic_runtime_root: Path,
) -> dict:
    if not raw_path:
        return {
            "path": None,
            "exists": False,
            "status": "missing",
            "steering_status": "missing",
            "directive": None,
            "allow_override_unfinished": False,
            "allow_override_decision_contract": False,
            "target_action_id": None,
            "target_action_summary": None,
            "target_artifacts": [],
            "stop_conditions": [],
            "evidence_refs": [],
            "summary": "No control note is currently attached to this topic.",
            "title": None,
            "parse_mode": "missing",
        }

    note_path = resolve_note_path(raw_path, knowledge_root, topic_runtime_root)
    if note_path is None or not note_path.exists():
        return {
            "path": raw_path,
            "exists": False,
            "status": "missing",
            "steering_status": "missing",
            "directive": None,
            "allow_override_unfinished": False,
            "allow_override_decision_contract": False,
            "target_action_id": None,
            "target_action_summary": None,
            "target_artifacts": [],
            "stop_conditions": [],
            "evidence_refs": [],
            "summary": f"Configured control note is missing: {raw_path}",
            "title": None,
            "parse_mode": "missing",
        }

    metadata: dict[str, object] = {}
    body_text = ""
    parse_mode = "markdown"
    if note_path.suffix.lower() == ".json":
        metadata = read_json(note_path) or {}
        body_text = json.dumps(metadata, ensure_ascii=True, indent=2)
        parse_mode = "json"
    else:
        raw_text = note_path.read_text(encoding="utf-8")
        metadata, body_text = parse_frontmatter(raw_text)
        parse_mode = "frontmatter" if metadata else "markdown"

    directive = normalize_control_directive(
        metadata.get("directive") or metadata.get("mode") or metadata.get("intent")
    )
    allow_override = bool(metadata.get("allow_override_unfinished", False))
    allow_override_decision_contract = bool(
        metadata.get("allow_override_decision_contract", False)
    )
    if directive in ACTIVE_CONTROL_DIRECTIVES:
        allow_override = True

    title = str(metadata.get("title") or first_markdown_heading(body_text) or note_path.stem)
    summary = str(metadata.get("summary") or first_summary_line(body_text) or title)
    target_artifacts = ensure_string_list(metadata.get("target_artifacts") or metadata.get("artifacts"))
    evidence_refs = unique_list(
        target_artifacts
        + ensure_string_list(metadata.get("evidence_refs"))
        + extract_backtick_refs(body_text)
    )
    steering_status = "advisory"
    if directive in ACTIVE_CONTROL_DIRECTIVES and allow_override:
        steering_status = "active_redirect"
    elif directive in STOP_CONTROL_DIRECTIVES:
        steering_status = "stop"

    return {
        "path": relative_path(note_path, knowledge_root),
        "exists": True,
        "status": "present",
        "steering_status": steering_status,
        "directive": directive,
        "allow_override_unfinished": allow_override,
        "allow_override_decision_contract": allow_override_decision_contract,
        "target_action_id": str(metadata.get("target_action_id") or "").strip() or None,
        "target_action_summary": str(metadata.get("target_action_summary") or metadata.get("target_action") or "").strip()
        or None,
        "target_artifacts": target_artifacts,
        "stop_conditions": ensure_string_list(metadata.get("stop_conditions")),
        "evidence_refs": evidence_refs,
        "summary": summary,
        "title": title,
        "parse_mode": parse_mode,
    }


def action_evidence_refs(row: dict) -> list[str]:
    return extract_backtick_refs(str(row.get("summary") or ""))


def is_system_blocker(row: dict) -> bool:
    return str(row.get("action_type") or "") in SYSTEM_BLOCKING_ACTION_TYPES


def build_pending_item(index: int, row: dict) -> dict:
    return {
        "queue_rank": index + 1,
        "action_id": row.get("action_id"),
        "action_type": row.get("action_type"),
        "resume_stage": row.get("resume_stage"),
        "status": row.get("status"),
        "summary": row.get("summary"),
        "auto_runnable": bool(row.get("auto_runnable")),
        "handler": row.get("handler"),
        "handler_args": row.get("handler_args") or {},
        "system_blocker": is_system_blocker(row),
        "evidence_refs": action_evidence_refs(row),
    }


def policy_ranked_pending(pending_rows: list[dict]) -> list[dict]:
    blocking = [row for row in pending_rows if is_system_blocker(row)]
    if blocking:
        non_blocking = [row for row in pending_rows if not is_system_blocker(row)]
        return blocking + non_blocking
    return list(pending_rows)


def action_match_score(row: dict, control_note: dict) -> int:
    score = 0
    action_id = str(row.get("action_id") or "")
    summary = str(row.get("summary") or "")
    if control_note.get("target_action_id") and action_id == control_note["target_action_id"]:
        score += 1000

    target_summary = str(control_note.get("target_action_summary") or "").strip().lower()
    lowered_summary = summary.lower()
    if target_summary:
        if target_summary == lowered_summary:
            score += 500
        elif target_summary in lowered_summary or lowered_summary in target_summary:
            score += 250
        score += 20 * len(tokenize(target_summary) & tokenize(lowered_summary))

    action_refs = set(action_evidence_refs(row))
    target_artifacts = set(ensure_string_list(control_note.get("target_artifacts")))
    score += 100 * len(action_refs & target_artifacts)

    if control_note.get("summary"):
        score += 5 * len(tokenize(str(control_note["summary"])) & tokenize(summary))
    return score


def match_control_note_action(pending_rows: list[dict], control_note: dict) -> tuple[dict | None, str | None]:
    best_row: dict | None = None
    best_score = 0
    for row in pending_rows:
        score = action_match_score(row, control_note)
        if score > best_score:
            best_row = row
            best_score = score
    if best_row is None or best_score <= 0:
        return None, None
    if control_note.get("target_action_id") and best_score >= 1000:
        return best_row, "control_note.target_action_id"
    if control_note.get("target_artifacts") and best_score >= 100:
        return best_row, "control_note.target_artifacts"
    return best_row, "control_note.text_match"


def runtime_state_refs(topic_state: dict) -> list[str]:
    pointers = topic_state.get("pointers") or {}
    refs = [str(pointers.get(key) or "").strip() for key in RUNTIME_POINTER_KEYS]
    refs = [ref for ref in refs if ref]
    return unique_list(refs)


def load_runtime_contract(topic_runtime_root: Path) -> dict | None:
    return read_json(topic_runtime_root / "runtime_protocol.generated.json")


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


def policy_ranked_pending(pending_rows: list[dict], runtime_contract: dict | None = None) -> list[dict]:
    blocking = [row for row in pending_rows if is_system_blocker(row)]
    non_blocking = [row for row in pending_rows if not is_system_blocker(row)]
    preferred_action_types = preferred_action_types_from_runtime_contract(runtime_contract)
    if preferred_action_types:
        preferred = [
            row for row in non_blocking if str(row.get("action_type") or "").strip() in preferred_action_types
        ]
        if preferred:
            preferred_ids = {str(row.get("action_id") or "").strip() for row in preferred}
            trailing = [
                row for row in non_blocking if str(row.get("action_id") or "").strip() not in preferred_ids
            ]
            return blocking + preferred + trailing
    if blocking:
        return blocking + non_blocking
    return list(pending_rows)


def build_unfinished_work(topic_state: dict, queue_rows: list[dict], control_note: dict, runtime_contract: dict | None = None) -> dict:
    pending_rows = [row for row in queue_rows if row.get("status") == "pending"]
    ordered_pending = policy_ranked_pending(pending_rows, runtime_contract=runtime_contract)
    pending_items = [build_pending_item(index, row) for index, row in enumerate(ordered_pending)]
    auto_pending = [item for item in pending_items if item["auto_runnable"]]
    manual_pending = [item for item in pending_items if not item["auto_runnable"]]
    blockers = [item for item in pending_items if item["system_blocker"]]

    note_surfaces = []
    pointers = topic_state.get("pointers") or {}
    for key, label in (
        ("next_actions_path", "L3 next-actions note"),
        ("next_actions_contract_path", "L3 next-actions contract"),
        ("control_note_path", "L4 control note"),
    ):
        raw_path = str(pointers.get(key) or "").strip()
        if raw_path:
            note_surfaces.append({"label": label, "path": raw_path})

    payload = {
        "topic_slug": topic_state["topic_slug"],
        "updated_at": now_iso(),
        "updated_by": topic_state.get("updated_by", "codex"),
        "policy": {
            "default_mode": "unfinished_first",
            "system_blockers_precede_research_queue": True,
            "chat_redirect_requires_persisted_artifact": True,
            "human_override_surface": "control_note",
        },
        "resume_stage": topic_state.get("resume_stage"),
        "latest_run_id": topic_state.get("latest_run_id"),
        "control_note": {
            "path": control_note.get("path"),
            "status": control_note.get("status"),
            "steering_status": control_note.get("steering_status"),
            "directive": control_note.get("directive"),
            "allow_override_decision_contract": bool(
                control_note.get("allow_override_decision_contract")
            ),
            "summary": control_note.get("summary"),
        },
        "pending_count": len(pending_items),
        "auto_pending_count": len(auto_pending),
        "manual_pending_count": len(manual_pending),
        "system_blocker_count": len(blockers),
        "queue_head_action_id": pending_items[0]["action_id"] if pending_items else None,
        "ordered_pending_actions": pending_items,
        "runtime_state_refs": runtime_state_refs(topic_state),
        "human_note_surfaces": note_surfaces,
        "closed_loop": topic_state.get("closed_loop") or {},
    }
    preferred_action_types = preferred_action_types_from_runtime_contract(runtime_contract)
    if preferred_action_types:
        payload["policy"]["runtime_contract_preferred_action_types"] = preferred_action_types
    return payload


def select_default_action(pending_rows: list[dict], runtime_contract: dict | None = None) -> tuple[dict | None, str | None]:
    if not pending_rows:
        return None, None
    ordered = policy_ranked_pending(pending_rows, runtime_contract=runtime_contract)
    selected = ordered[0]
    preferred_action_types = preferred_action_types_from_runtime_contract(runtime_contract)
    if preferred_action_types and str(selected.get("action_type") or "").strip() in preferred_action_types:
        return selected, f"runtime_contract_preferred:{str(selected.get('action_type') or '').strip()}"
    if is_system_blocker(selected):
        return selected, "unfinished_runtime_blocker"
    return selected, "unfinished_queue_head"


def decision_action_payload(row: dict | None) -> dict | None:
    if row is None:
        return None
    return {
        "action_id": row.get("action_id"),
        "action_type": row.get("action_type"),
        "resume_stage": row.get("resume_stage"),
        "status": row.get("status"),
        "summary": row.get("summary"),
        "auto_runnable": bool(row.get("auto_runnable")),
        "handler": row.get("handler"),
        "handler_args": row.get("handler_args") or {},
        "system_blocker": is_system_blocker(row),
        "evidence_refs": action_evidence_refs(row),
    }


def apply_decision_contract(pending_rows: list[dict], contract_payload: dict | None) -> dict | None:
    if not contract_payload:
        return None

    decision_mode = str(contract_payload.get("decision_mode") or "").strip() or "declared_contract"
    reason = str(contract_payload.get("reason") or "").strip() or "Using an explicit next-action decision contract."
    selected_action_id = str(
        contract_payload.get("selected_action_id")
        or ((contract_payload.get("selected_action") or {}).get("action_id") if isinstance(contract_payload.get("selected_action"), dict) else "")
        or ""
    ).strip()
    pending_map = {str(row.get("action_id") or "").strip(): row for row in pending_rows}

    if not selected_action_id:
        if decision_mode in {"no_action", "pause", "stop"}:
            return {
                "decision_source": "declared_contract",
                "decision_mode": "no_action",
                "decision_basis": "decision_contract",
                "reason": reason,
                "requires_human_intervention": bool(
                    contract_payload.get("requires_human_intervention", False)
                ),
                "selected_action": None,
                "auto_dispatch_allowed": False,
                "evidence_refs": unique_list(ensure_string_list(contract_payload.get("evidence_refs"))),
                "decision_contract_status": "valid",
            }
        return {
            "decision_source": "declared_contract",
            "decision_mode": "no_action",
            "decision_basis": "invalid_decision_contract",
            "reason": (
                "The explicit next-action decision contract is missing `selected_action_id`. "
                "Fix the contract or remove it before continuing."
            ),
            "requires_human_intervention": True,
            "selected_action": None,
            "auto_dispatch_allowed": False,
            "evidence_refs": unique_list(ensure_string_list(contract_payload.get("evidence_refs"))),
            "decision_contract_status": "invalid",
        }

    selected_row = pending_map.get(selected_action_id)
    if selected_row is None:
        return {
            "decision_source": "declared_contract",
            "decision_mode": "no_action",
            "decision_basis": "invalid_decision_contract",
            "reason": (
                f"The explicit next-action decision contract selected `{selected_action_id}`, "
                "but that action is not currently pending."
            ),
            "requires_human_intervention": True,
            "selected_action": None,
            "auto_dispatch_allowed": False,
            "evidence_refs": unique_list(
                ensure_string_list(contract_payload.get("evidence_refs")) + [selected_action_id]
            ),
            "decision_contract_status": "invalid",
        }

    selected_action = decision_action_payload(selected_row)
    auto_dispatch_allowed = bool(contract_payload.get("auto_dispatch_allowed", selected_action["auto_runnable"]))
    auto_dispatch_allowed = auto_dispatch_allowed and bool(selected_action["auto_runnable"])
    requires_human_intervention = bool(
        contract_payload.get("requires_human_intervention", not auto_dispatch_allowed)
    )
    return {
        "decision_source": "declared_contract",
        "decision_mode": decision_mode,
        "decision_basis": "decision_contract",
        "reason": reason,
        "requires_human_intervention": requires_human_intervention,
        "selected_action": selected_action,
        "auto_dispatch_allowed": auto_dispatch_allowed,
        "evidence_refs": unique_list(
            ensure_string_list(contract_payload.get("evidence_refs")) + action_evidence_refs(selected_row)
        ),
        "decision_contract_status": "valid",
    }


def build_next_action_decision(topic_state: dict, queue_rows: list[dict], control_note: dict, runtime_contract: dict | None = None) -> dict:
    pending_rows = [row for row in queue_rows if row.get("status") == "pending"]
    decision_contract = load_decision_contract(
        Path(__file__).resolve().parents[1] / "topics" / topic_state["topic_slug"]
    )
    directive = control_note.get("directive")
    if (
        decision_contract
        and directive in ACTIVE_CONTROL_DIRECTIVES
        and control_note.get("allow_override_unfinished")
        and control_note.get("allow_override_decision_contract")
    ):
        matched_row, match_basis = match_control_note_action(pending_rows, control_note)
        if matched_row is None:
            return {
                "topic_slug": topic_state["topic_slug"],
                "updated_at": now_iso(),
                "updated_by": topic_state.get("updated_by", "codex"),
                "policy": {
                    "default_mode": "unfinished_first",
                    "chat_redirect_requires_persisted_artifact": True,
                    "human_override_surface": "control_note",
                    "control_note_override_requires_explicit_directive": True,
                    "declared_decision_contract_path": f"topics/{topic_state['topic_slug']}/runtime/{NEXT_ACTION_DECISION_CONTRACT_FILENAME}",
                },
                "control_note": control_note,
                "decision_source": "control_note",
                "decision_contract_status": "override_requested_unmatched",
                "decision_mode": "no_action",
                "decision_basis": "control_note_override_unmatched",
                "reason": (
                    "The control note explicitly requests overriding the declared decision contract, "
                    "but no pending queue action matches the persisted redirect. Update the queue or "
                    "the control note before continuing."
                ),
                "requires_human_intervention": True,
                "selected_action": None,
                "auto_dispatch_allowed": False,
                "evidence_refs": unique_list(
                    ensure_string_list(control_note.get("evidence_refs")) + runtime_state_refs(topic_state)
                ),
            }
        return {
            "topic_slug": topic_state["topic_slug"],
            "updated_at": now_iso(),
            "updated_by": topic_state.get("updated_by", "codex"),
            "policy": {
                "default_mode": "unfinished_first",
                "chat_redirect_requires_persisted_artifact": True,
                "human_override_surface": "control_note",
                "control_note_override_requires_explicit_directive": True,
                "declared_decision_contract_path": f"topics/{topic_state['topic_slug']}/runtime/{NEXT_ACTION_DECISION_CONTRACT_FILENAME}",
            },
            "control_note": control_note,
            "decision_source": "control_note",
            "decision_contract_status": "overridden_by_control_note",
            "decision_mode": "human_redirect",
            "decision_basis": f"control_note_contract_override:{match_basis}",
            "reason": (
                "The control note explicitly authorizes overriding the declared decision contract, "
                "so the loop follows the persisted redirect instead of the frozen decision."
            ),
            "requires_human_intervention": not bool(matched_row.get("auto_runnable")),
            "selected_action": decision_action_payload(matched_row),
            "auto_dispatch_allowed": bool(matched_row.get("auto_runnable")),
            "evidence_refs": unique_list(
                ensure_string_list(control_note.get("evidence_refs"))
                + action_evidence_refs(matched_row)
                + runtime_state_refs(topic_state)
            ),
        }
    contract_decision = apply_decision_contract(pending_rows, decision_contract)
    if contract_decision is not None:
        selected_action = contract_decision["selected_action"]
        return {
            "topic_slug": topic_state["topic_slug"],
            "updated_at": now_iso(),
            "updated_by": topic_state.get("updated_by", "codex"),
            "policy": {
                "default_mode": "unfinished_first",
                "chat_redirect_requires_persisted_artifact": True,
                "human_override_surface": "control_note",
                "control_note_override_requires_explicit_directive": True,
                "declared_decision_contract_path": f"topics/{topic_state['topic_slug']}/runtime/{NEXT_ACTION_DECISION_CONTRACT_FILENAME}",
            },
            "control_note": control_note,
            "decision_source": contract_decision["decision_source"],
            "decision_contract_status": contract_decision["decision_contract_status"],
            "decision_mode": contract_decision["decision_mode"],
            "decision_basis": contract_decision["decision_basis"],
            "reason": contract_decision["reason"],
            "requires_human_intervention": contract_decision["requires_human_intervention"],
            "selected_action": selected_action,
            "auto_dispatch_allowed": bool(contract_decision["auto_dispatch_allowed"]),
            "evidence_refs": unique_list(contract_decision["evidence_refs"] + runtime_state_refs(topic_state)),
        }

    default_row, default_basis = select_default_action(pending_rows, runtime_contract=runtime_contract)
    selected_row = default_row
    decision_mode = "continue_unfinished" if default_row is not None else "no_action"
    decision_source = "heuristic"
    decision_contract_status = "missing"
    decision_basis = default_basis
    reason = (
        "No active control note override exists, so the loop continues with the highest-priority unfinished work."
        if default_row is not None
        else "No pending actions remain, so there is nothing to dispatch."
    )
    requires_human_intervention = default_row is not None and not bool(default_row.get("auto_runnable"))
    evidence_refs = []
    if default_row is not None:
        evidence_refs.extend(action_evidence_refs(default_row))

    if directive in STOP_CONTROL_DIRECTIVES:
        selected_row = None
        decision_mode = "no_action"
        decision_basis = "control_note_stop"
        requires_human_intervention = False
        reason = (
            "The attached control note requests that the loop stop or pause automatic continuation "
            "until the stated stop conditions are cleared."
        )
        evidence_refs = ensure_string_list(control_note.get("evidence_refs"))
    elif directive in ACTIVE_CONTROL_DIRECTIVES and control_note.get("allow_override_unfinished"):
        matched_row, match_basis = match_control_note_action(pending_rows, control_note)
        if matched_row is None:
            selected_row = None
            decision_mode = "no_action"
            decision_source = "heuristic"
            decision_basis = "control_note_unmatched"
            requires_human_intervention = True
            reason = (
                "The control note requests a redirect, but no pending queue action matches it. "
                "Persist the redirect into `next_actions.md` or `action_queue.jsonl` before continuing."
            )
            evidence_refs = ensure_string_list(control_note.get("evidence_refs"))
        else:
            selected_row = matched_row
            decision_mode = (
                "follow_control_note"
                if default_row is None or matched_row.get("action_id") == default_row.get("action_id")
                else "human_redirect"
            )
            decision_source = "control_note"
            decision_basis = match_basis
            requires_human_intervention = not bool(matched_row.get("auto_runnable"))
            reason = (
                "The control note provides an explicit persisted redirect, so it overrides the default unfinished-first order."
            )
            evidence_refs = unique_list(
                ensure_string_list(control_note.get("evidence_refs")) + action_evidence_refs(matched_row)
            )

    selected_action = decision_action_payload(selected_row)
    return {
        "topic_slug": topic_state["topic_slug"],
        "updated_at": now_iso(),
        "updated_by": topic_state.get("updated_by", "codex"),
        "policy": {
            "default_mode": "unfinished_first",
            "chat_redirect_requires_persisted_artifact": True,
            "human_override_surface": "control_note",
            "control_note_override_requires_explicit_directive": True,
            "declared_decision_contract_path": f"topics/{topic_state['topic_slug']}/runtime/{NEXT_ACTION_DECISION_CONTRACT_FILENAME}",
        },
        "control_note": control_note,
        "decision_source": decision_source,
        "decision_contract_status": decision_contract_status,
        "decision_mode": decision_mode,
        "decision_basis": decision_basis,
        "reason": reason,
        "requires_human_intervention": requires_human_intervention,
        "selected_action": selected_action,
        "auto_dispatch_allowed": bool(selected_action and selected_action.get("auto_runnable")),
        "evidence_refs": unique_list(evidence_refs + runtime_state_refs(topic_state)),
    }


def build_unfinished_work_markdown(payload: dict) -> str:
    lines = [
        "# Unfinished work",
        "",
        f"- Topic slug: `{payload['topic_slug']}`",
        f"- Updated at: `{payload['updated_at']}`",
        f"- Updated by: `{payload['updated_by']}`",
        f"- Resume stage: `{payload.get('resume_stage') or '(missing)'}`",
        f"- Latest run id: `{payload.get('latest_run_id') or '(none)'}`",
        "",
        "## Policy",
        "",
        f"- Default mode: `{payload['policy']['default_mode']}`",
        "- Rule: unfinished work is resumed before new speculative branches are opened.",
        "- Rule: chat-only redirects do not count until they are persisted into a durable steering artifact.",
        "- Rule: active runtime blockers are surfaced ahead of ordinary research queue items.",
        "",
        "## Control note",
        "",
        f"- Path: `{payload['control_note'].get('path') or '(missing)'}`",
        f"- Status: `{payload['control_note'].get('steering_status') or payload['control_note'].get('status') or 'missing'}`",
        f"- Allow decision-contract override: `{str(bool(payload['control_note'].get('allow_override_decision_contract'))).lower()}`",
        f"- Summary: {payload['control_note'].get('summary') or '(none)' }",
        "",
        "## Pending counts",
        "",
        f"- Total pending: `{payload['pending_count']}`",
        f"- Manual pending: `{payload['manual_pending_count']}`",
        f"- Auto-runnable pending: `{payload['auto_pending_count']}`",
        f"- Runtime blockers: `{payload['system_blocker_count']}`",
        "",
        "## Ordered unfinished actions",
        "",
    ]
    if payload["ordered_pending_actions"]:
        for item in payload["ordered_pending_actions"]:
            lines.append(
                f"{item['queue_rank']}. [{item['action_type']}] {item['summary']} "
                f"(auto_runnable={str(item['auto_runnable']).lower()}, system_blocker={str(item['system_blocker']).lower()})"
            )
    else:
        lines.append("- No pending actions remain.")

    lines.extend(
        [
            "",
            "## Human note surfaces",
            "",
        ]
    )
    if payload["human_note_surfaces"]:
        for surface in payload["human_note_surfaces"]:
            lines.append(f"- {surface['label']}: `{surface['path']}`")
    else:
        lines.append("- No layer-local note surface is currently registered.")

    lines.extend(
        [
            "",
            "## Runtime state refs",
            "",
        ]
    )
    if payload["runtime_state_refs"]:
        for ref in payload["runtime_state_refs"]:
            lines.append(f"- `{ref}`")
    else:
        lines.append("- None recorded.")
    return "\n".join(lines) + "\n"


def build_next_action_markdown(payload: dict) -> str:
    selected = payload.get("selected_action")
    lines = [
        "# Next action decision",
        "",
        f"- Topic slug: `{payload['topic_slug']}`",
        f"- Updated at: `{payload['updated_at']}`",
        f"- Updated by: `{payload['updated_by']}`",
        f"- Decision mode: `{payload['decision_mode']}`",
        f"- Decision source: `{payload.get('decision_source') or '(missing)'}`",
        f"- Decision basis: `{payload.get('decision_basis') or '(missing)'}`",
        f"- Auto dispatch allowed: `{str(payload['auto_dispatch_allowed']).lower()}`",
        f"- Requires human intervention: `{str(payload['requires_human_intervention']).lower()}`",
        "",
        "## Why this was selected",
        "",
        f"- {payload['reason']}",
        "",
        "## Control note state",
        "",
        f"- Path: `{payload['control_note'].get('path') or '(missing)'}`",
        f"- Steering status: `{payload['control_note'].get('steering_status') or payload['control_note'].get('status') or 'missing'}`",
        f"- Directive: `{payload['control_note'].get('directive') or '(none)'}`",
        f"- Allow decision-contract override: `{str(bool(payload['control_note'].get('allow_override_decision_contract'))).lower()}`",
        f"- Summary: {payload['control_note'].get('summary') or '(none)' }",
        f"- Decision contract status: `{payload.get('decision_contract_status') or 'missing'}`",
        f"- Decision contract path: `{payload.get('policy', {}).get('declared_decision_contract_path') or '(missing)'}`",
        "",
        "## Selected action",
        "",
    ]
    if selected:
        lines.extend(
            [
                f"- Action id: `{selected['action_id']}`",
                f"- Action type: `{selected['action_type']}`",
                f"- Resume stage: `{selected.get('resume_stage') or '(missing)'}`",
                f"- Summary: {selected['summary']}",
                f"- Handler: `{selected.get('handler') or '(manual)'}`",
            ]
        )
    else:
        lines.append("- No action is currently selected.")

    lines.extend(
        [
            "",
            "## Evidence refs",
            "",
        ]
    )
    if payload["evidence_refs"]:
        for ref in payload["evidence_refs"]:
            lines.append(f"- `{ref}`")
    else:
        lines.append("- None recorded.")
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic-slug", required=True)
    parser.add_argument("--control-note")
    parser.add_argument("--updated-by", default="codex")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    knowledge_root = Path(__file__).resolve().parents[2]
    topic_runtime_root = knowledge_root / "runtime" / "topics" / args.topic_slug
    topic_state = read_json(topic_runtime_root / "topic_state.json")
    if topic_state is None:
        raise SystemExit(f"Runtime topic state is missing for {args.topic_slug}")

    queue_rows = read_jsonl(topic_runtime_root / "action_queue.jsonl")
    pointers = topic_state.get("pointers") or {}
    control_note_raw = args.control_note or pointers.get("control_note_path")
    control_note = inspect_control_note(control_note_raw, knowledge_root, topic_runtime_root)

    updated_by = args.updated_by
    topic_state["updated_by"] = updated_by
    runtime_contract = load_runtime_contract(topic_runtime_root)
    unfinished_work = build_unfinished_work(topic_state, queue_rows, control_note, runtime_contract)
    unfinished_work["updated_by"] = updated_by
    next_action = build_next_action_decision(topic_state, queue_rows, control_note, runtime_contract)
    next_action["updated_by"] = updated_by

    write_json(topic_runtime_root / UNFINISHED_WORK_FILENAME, unfinished_work)
    write_text(topic_runtime_root / UNFINISHED_WORK_NOTE_FILENAME, build_unfinished_work_markdown(unfinished_work))
    write_json(topic_runtime_root / NEXT_ACTION_DECISION_FILENAME, next_action)
    write_text(topic_runtime_root / NEXT_ACTION_DECISION_NOTE_FILENAME, build_next_action_markdown(next_action))

    print(f"Materialized decision surfaces for {args.topic_slug}")
    print(f"- unfinished_work: {topic_runtime_root / UNFINISHED_WORK_FILENAME}")
    print(f"- next_action_decision: {topic_runtime_root / NEXT_ACTION_DECISION_FILENAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
