#!/usr/bin/env python3
"""Minimal closed-loop helpers for AITP runtime v1."""

from __future__ import annotations

import copy
import json
import re
from datetime import datetime
from pathlib import Path

from closed_loop_policy import (
    closed_loop_policy_path_ref,
    load_closed_loop_policy,
    result_ingest_policy,
    route_selection_policy,
)
from research_mode_profiles import resolve_task_research_profile

ROUTE_SELECTION_POLICY = route_selection_policy()
RESULT_INGEST_POLICY = result_ingest_policy()
FULL_CLOSED_LOOP_POLICY = load_closed_loop_policy()

VALID_RESULT_STATUSES = set(RESULT_INGEST_POLICY.get("valid_result_statuses") or ["success", "failed", "partial"])
VALID_DECISIONS = set(RESULT_INGEST_POLICY.get("valid_decisions") or ["keep", "revise", "discard", "defer"])
SYSTEM_ACTION_TYPES = {
    "select_validation_route",
    "materialize_execution_task",
    "ingest_execution_result",
    "await_execution_result",
}
STOPWORDS = set(ROUTE_SELECTION_POLICY.get("stopwords") or [])
MIN_ROUTE_TOKEN_OVERLAP = int(ROUTE_SELECTION_POLICY.get("min_route_token_overlap") or 2)
MIN_ROUTE_SCORE = int(ROUTE_SELECTION_POLICY.get("min_route_score") or 140)
NON_EXECUTION_PREFIXES = tuple(ROUTE_SELECTION_POLICY.get("non_execution_prefixes") or [])
EXECUTION_HINTS = tuple(ROUTE_SELECTION_POLICY.get("execution_hints") or [])
RERUN_HINTS = tuple(ROUTE_SELECTION_POLICY.get("rerun_hints") or ["re-run", "rerun", "run again", "repeat"])
DEFAULT_FAILURE_SIGNALS = [
    str(item).strip()
    for item in (ROUTE_SELECTION_POLICY.get("default_failure_signals") or [])
    if str(item).strip()
]
SELECTION_REASON_TEMPLATES = dict(ROUTE_SELECTION_POLICY.get("selection_reason_templates") or {})
DECISION_RULES = list(RESULT_INGEST_POLICY.get("decision_rules") or [])
CANDIDATE_STATUS_BY_DECISION = dict(RESULT_INGEST_POLICY.get("candidate_status_by_decision") or {})
FOLLOWUP_POLICY = dict(RESULT_INGEST_POLICY.get("followup_policy") or {})
FAILURE_CLASSIFICATION_POLICY = dict(RESULT_INGEST_POLICY.get("failure_classification") or {})
FOLLOWUP_GAP_POLICY = dict(FULL_CLOSED_LOOP_POLICY.get("followup_gap_policy") or {})
VALID_FOLLOWUP_GAP_KINDS = {
    str(item).strip()
    for item in (FOLLOWUP_GAP_POLICY.get("allowed_gap_kinds") or [])
    if str(item).strip()
}
RETURN_TO_STAGE_BY_GAP_KIND = {
    str(key).strip(): str(value).strip()
    for key, value in (FOLLOWUP_GAP_POLICY.get("return_to_stage_by_kind") or {}).items()
    if str(key).strip() and str(value).strip()
}
DEFAULT_GAP_PRIORITY_BY_STAGE = {
    str(key).strip(): str(value).strip()
    for key, value in (FOLLOWUP_GAP_POLICY.get("default_priority_by_stage") or {}).items()
    if str(key).strip() and str(value).strip()
}
DEFAULT_FOLLOWUP_GAP_STATUS = str(FOLLOWUP_GAP_POLICY.get("default_status") or "open")
DEFAULT_FOLLOWUP_GAP_TARGET_SOURCE_TYPE = str(
    FOLLOWUP_GAP_POLICY.get("default_target_source_type") or "paper"
)


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def compatibility_projection_path(path: Path) -> Path | None:
    resolved = path.expanduser().resolve()
    parts = resolved.parts
    if "runtime" in parts and "topics" in parts:
        runtime_index = parts.index("runtime")
        if runtime_index + 2 < len(parts) and parts[runtime_index + 1] == "topics":
            kernel_root = Path(parts[0]).joinpath(*parts[1:runtime_index])
            topic_slug = parts[runtime_index + 2]
            remainder = parts[runtime_index + 3 :]
            return kernel_root / "topics" / topic_slug / "runtime" / Path(*remainder)
    if "feedback" in parts and "topics" in parts:
        feedback_index = parts.index("feedback")
        if feedback_index + 2 < len(parts) and parts[feedback_index + 1] == "topics":
            kernel_root = Path(parts[0]).joinpath(*parts[1:feedback_index])
            topic_slug = parts[feedback_index + 2]
            remainder = parts[feedback_index + 3 :]
            return kernel_root / "topics" / topic_slug / "L3" / Path(*remainder)
    if "validation" in parts and "topics" in parts:
        validation_index = parts.index("validation")
        if validation_index + 2 < len(parts) and parts[validation_index + 1] == "topics":
            kernel_root = Path(parts[0]).joinpath(*parts[1:validation_index])
            topic_slug = parts[validation_index + 2]
            remainder = parts[validation_index + 3 :]
            return kernel_root / "topics" / topic_slug / "L4" / Path(*remainder)
    if "source-layer" in parts and "topics" in parts:
        source_index = parts.index("source-layer")
        if source_index + 2 < len(parts) and parts[source_index + 1] == "topics":
            kernel_root = Path(parts[0]).joinpath(*parts[1:source_index])
            topic_slug = parts[source_index + 2]
            remainder = parts[source_index + 3 :]
            return kernel_root / "topics" / topic_slug / "L0" / Path(*remainder)
    if "intake" in parts and "topics" in parts:
        intake_index = parts.index("intake")
        if intake_index + 2 < len(parts) and parts[intake_index + 1] == "topics":
            kernel_root = Path(parts[0]).joinpath(*parts[1:intake_index])
            topic_slug = parts[intake_index + 2]
            remainder = parts[intake_index + 3 :]
            return kernel_root / "topics" / topic_slug / "L1" / Path(*remainder)
    if "consultation" in parts and "topics" in parts:
        consultation_index = parts.index("consultation")
        if consultation_index + 2 < len(parts) and parts[consultation_index + 1] == "topics":
            kernel_root = Path(parts[0]).joinpath(*parts[1:consultation_index])
            topic_slug = parts[consultation_index + 2]
            remainder = parts[consultation_index + 3 :]
            return kernel_root / "topics" / topic_slug / "consultation" / Path(*remainder)
    if "topics" in parts:
        topics_index = parts.index("topics")
        if topics_index + 3 < len(parts):
            kernel_root = Path(parts[0]).joinpath(*parts[1:topics_index])
            topic_slug = parts[topics_index + 1]
            surface = parts[topics_index + 2]
            remainder = parts[topics_index + 3 :]
            if surface == "runtime":
                return kernel_root / "runtime" / "topics" / topic_slug / Path(*remainder)
            if surface == "L3":
                return kernel_root / "feedback" / "topics" / topic_slug / Path(*remainder)
            if surface == "L4":
                return kernel_root / "validation" / "topics" / topic_slug / Path(*remainder)
            if surface == "L0":
                return kernel_root / "source-layer" / "topics" / topic_slug / Path(*remainder)
            if surface == "L1":
                return kernel_root / "intake" / "topics" / topic_slug / Path(*remainder)
            if surface == "consultation":
                return kernel_root / "consultation" / "topics" / topic_slug / Path(*remainder)
    return None


def read_json(path: Path) -> dict | None:
    target = path
    if not target.exists():
        compatibility_path = compatibility_projection_path(path)
        if compatibility_path is None or not compatibility_path.exists():
            return None
        target = compatibility_path
    return json.loads(target.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    target = path
    if not target.exists():
        compatibility_path = compatibility_projection_path(path)
        if compatibility_path is None or not compatibility_path.exists():
            return []
        target = compatibility_path
    rows: list[dict] = []
    for raw_line in target.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict | list) -> None:
    rendered = json.dumps(payload, ensure_ascii=True, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    compatibility_path = compatibility_projection_path(path)
    if compatibility_path is not None and compatibility_path != path:
        compatibility_path.parent.mkdir(parents=True, exist_ok=True)
        compatibility_path.write_text(rendered, encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    compatibility_path = compatibility_projection_path(path)
    if compatibility_path is not None and compatibility_path != path:
        compatibility_path.parent.mkdir(parents=True, exist_ok=True)
        compatibility_path.write_text(text, encoding="utf-8")


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=True) + "\n")
    compatibility_path = compatibility_projection_path(path)
    if compatibility_path is not None and compatibility_path != path:
        compatibility_path.parent.mkdir(parents=True, exist_ok=True)
        with compatibility_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def write_jsonl_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in rows)
    path.write_text(text, encoding="utf-8")
    compatibility_path = compatibility_projection_path(path)
    if compatibility_path is not None and compatibility_path != path:
        compatibility_path.parent.mkdir(parents=True, exist_ok=True)
        compatibility_path.write_text(text, encoding="utf-8")


def relative_to_root(path: Path | None, root: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def ensure_string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if not isinstance(value, list):
        return []
    cleaned: list[str] = []
    for item in value:
        if item is None:
            continue
        text = str(item).strip()
        if text:
            cleaned.append(text)
    return cleaned


def ensure_dict_list(value: object) -> list[dict]:
    if not isinstance(value, list):
        return []
    rows: list[dict] = []
    for item in value:
        if isinstance(item, dict):
            rows.append(item)
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


def first_non_empty_text(*values: object) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-+", "-", lowered).strip("-")
    return lowered or "aitp-closed-loop"


def derive_run_id(topic_state: dict) -> str | None:
    run_id = topic_state.get("latest_run_id")
    if run_id:
        return str(run_id)

    pointers = topic_state.get("pointers") or {}
    for key in ("feedback_status_path", "promotion_decision_path", "next_actions_path"):
        raw_path = pointers.get(key)
        if not raw_path:
            continue
        match = re.search(r"/runs/([^/]+)/", str(raw_path))
        if match:
            return match.group(1)
    return None


def build_paths(knowledge_root: Path, topic_slug: str, run_id: str | None) -> dict[str, Path | None]:
    runtime_root = knowledge_root / "topics" / topic_slug / "runtime"
    validation_run_root = (
        knowledge_root / "topics" / topic_slug / "L4" / "runs" / run_id if run_id else None
    )
    feedback_run_root = (
        knowledge_root / "topics" / topic_slug / "L3" / "runs" / run_id if run_id else None
    )
    result_manifest_path = validation_run_root / "results" / "result_manifest.json" if validation_run_root else None

    return {
        "runtime_root": runtime_root,
        "selected_route_path": runtime_root / "selected_validation_route.json",
        "execution_task_path": runtime_root / "execution_task.json",
        "execution_task_md_path": runtime_root / "execution_task.md",
        "queue_path": runtime_root / "action_queue.jsonl",
        "validation_run_root": validation_run_root,
        "feedback_run_root": feedback_run_root,
        "execution_notes_dir": validation_run_root / "execution_notes" if validation_run_root else None,
        "returned_result_path": validation_run_root / "returned_execution_result.json" if validation_run_root else None,
        "result_manifest_path": result_manifest_path,
        "result_summary_path": validation_run_root / "result_summary.md" if validation_run_root else None,
        "decision_ledger_path": validation_run_root / "decision_ledger.jsonl" if validation_run_root else None,
        "trajectory_log_path": validation_run_root / "results" / "trajectory_log.jsonl" if validation_run_root else None,
        "trajectory_note_path": validation_run_root / "results" / "trajectory_log.md" if validation_run_root else None,
        "failure_classification_path": (
            validation_run_root / "results" / "failure_classification.json" if validation_run_root else None
        ),
        "failure_classification_note_path": (
            validation_run_root / "results" / "failure_classification.md" if validation_run_root else None
        ),
        "literature_followup_path": (
            validation_run_root / "literature_followup_queries.json" if validation_run_root else None
        ),
        "literature_followup_receipts_path": (
            validation_run_root / "literature_followup_receipts.jsonl" if validation_run_root else None
        ),
        "followup_gap_writeback_path": (
            validation_run_root / "followup_gap_writeback.json" if validation_run_root else None
        ),
        "followup_gap_writeback_note_path": (
            validation_run_root / "followup_gap_writeback.md" if validation_run_root else None
        ),
        "feedback_status_path": feedback_run_root / "status.json" if feedback_run_root else None,
        "feedback_next_actions_path": feedback_run_root / "next_actions.md" if feedback_run_root else None,
        "execution_tasks_dir": validation_run_root / "execution-tasks" if validation_run_root else None,
        "execution_result_template_path": knowledge_root / "validation" / "templates" / "execution-result.template.json",
    }


def tokenize(text: str) -> set[str]:
    tokens = set(re.findall(r"[a-z0-9]+", text.lower()))
    return {token for token in tokens if len(token) > 2 and token not in STOPWORDS}


def extract_backtick_items(text: str) -> list[str]:
    return unique_list([item.strip() for item in re.findall(r"`([^`]+)`", text) if item.strip()])


def resolve_artifact_ref(ref: str, knowledge_root: Path, validation_run_root: Path | None) -> str:
    cleaned = ref.strip()
    if not cleaned:
        return cleaned
    if cleaned.startswith((
        "topics/",
        "validation/",
        "feedback/",
        "runtime/",
        "source-layer/",
        "intake/",
        "canonical/",
        "consultation/",
    )):
        return cleaned
    if validation_run_root is not None and cleaned.startswith(("execution-tasks/", "results/", "configs/")):
        return relative_to_root(validation_run_root / cleaned, knowledge_root) or cleaned
    return cleaned


def canonicalize_artifact_ref(ref: str) -> str:
    cleaned = str(ref or "").strip()
    if not cleaned:
        return cleaned
    cleaned = cleaned.removeprefix("./")
    for prefix in ("research/knowledge-hub/", "knowledge-hub/"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break
    return cleaned


def normalize_followup_query_rows(
    value: object,
    *,
    default_reason: str,
    default_priority: str,
    default_target_source_type: str,
    result_id: str,
) -> list[dict]:
    normalized: list[dict] = []
    if not isinstance(value, list):
        return normalized
    for item in value:
        if isinstance(item, str):
            query = item.strip()
            if not query:
                continue
            normalized.append(
                {
                    "query": query,
                    "reason": default_reason,
                    "priority": default_priority,
                    "target_source_type": default_target_source_type,
                    "triggered_by_result_id": result_id,
                }
            )
            continue
        if not isinstance(item, dict):
            continue
        query = str(item.get("query") or "").strip()
        if not query:
            continue
        normalized.append(
            {
                "query": query,
                "reason": str(item.get("reason") or default_reason),
                "priority": str(item.get("priority") or default_priority),
                "target_source_type": str(item.get("target_source_type") or default_target_source_type),
                "triggered_by_result_id": result_id,
            }
        )
    return normalized


def build_declared_literature_followups(
    returned_result: dict,
    decision: dict,
    route: dict,
    task_payload: dict,
    result_id: str,
) -> list[dict]:
    explicit = returned_result.get("literature_followup_queries") or returned_result.get("followup_queries")
    default_target_source_type = str(FOLLOWUP_POLICY.get("default_target_source_type") or "paper")
    default_priority = str(FOLLOWUP_POLICY.get("default_priority") or "medium")
    max_queries = int(FOLLOWUP_POLICY.get("max_queries") or 3)
    normalized = normalize_followup_query_rows(
        explicit,
        default_reason=str(returned_result.get("decision_reason") or decision["reason"]),
        default_priority=default_priority,
        default_target_source_type=default_target_source_type,
        result_id=result_id,
    )
    if normalized:
        return normalized[:max_queries]

    needs_followup = any(
        bool(returned_result.get(flag))
        for flag in (FOLLOWUP_POLICY.get("trigger_flags") or [])
    ) or decision["decision"] in set(FOLLOWUP_POLICY.get("trigger_decisions") or [])
    if not needs_followup:
        return []

    base_terms = " ".join(
        unique_list(
            [
                task_payload.get("task_id", ""),
                route.get("route_type", ""),
                route.get("objective", ""),
            ]
        )
    )
    queries = [
        {
            "query": f"{base_terms} {FOLLOWUP_POLICY.get('baseline_query_suffix') or 'limitation baseline comparison'}".strip(),
            "reason": decision["reason"],
            "priority": (
                str(FOLLOWUP_POLICY.get("baseline_gap_priority") or default_priority)
                if returned_result.get("missing_baseline_support")
                else default_priority
            ),
            "target_source_type": default_target_source_type,
            "triggered_by_result_id": result_id,
        }
    ]
    if returned_result.get("contradiction_detected"):
        queries.append(
            {
                "query": f"{base_terms} {FOLLOWUP_POLICY.get('contradiction_query_suffix') or 'contradiction sector dependence'}".strip(),
                "reason": str(
                    FOLLOWUP_POLICY.get("contradiction_reason")
                    or "Returned result flagged a contradiction or mismatch that needs literature context."
                ),
                "priority": str(FOLLOWUP_POLICY.get("baseline_gap_priority") or default_priority),
                "target_source_type": default_target_source_type,
                "triggered_by_result_id": result_id,
            }
        )
    return queries[:max_queries]


def default_reopen_conditions(gap_kind: str, return_to_stage: str) -> list[str]:
    if return_to_stage == "L0":
        return ["Reopen after ingesting a new source that explicitly addresses the missing result."]
    if return_to_stage == "L1":
        return ["Reopen after the missing definition or notation is restated and anchored in provisional intake notes."]
    if return_to_stage == "L4_formalization":
        return ["Reopen after the mathematical formalization blocker is decomposed into explicit proof obligations."]
    if gap_kind == "missing_derivation_step":
        return ["Reopen after the omitted derivation step is written as a bounded derivation-step or proof-fragment note."]
    return ["Reopen after the missing local support is added to the current Layer 3 branch."]


def default_gap_title(gap_kind: str, route: dict, task_payload: dict, index: int) -> str:
    objective = first_non_empty_text(route.get("objective"), task_payload.get("summary"), f"gap {index}")
    return f"{gap_kind.replace('_', ' ')} for {objective}"


def normalize_followup_gap_entries(
    *,
    returned_result: dict,
    decision: dict,
    route: dict,
    task_payload: dict,
    result_id: str,
    paths: dict[str, Path | None],
    knowledge_root: Path,
) -> list[dict]:
    if not FOLLOWUP_GAP_POLICY.get("enabled", True):
        return []

    explicit_rows = ensure_dict_list(returned_result.get("followup_gap_writeback"))
    default_queries = build_declared_literature_followups(returned_result, decision, route, task_payload, result_id)
    rows_to_normalize = explicit_rows
    if not rows_to_normalize and default_queries:
        rows_to_normalize = [
            {
                "gap_kind": "cross_paper_dependency",
                "title": f"Bounded literature recovery for {first_non_empty_text(route.get('objective'), task_payload.get('task_id'), 'current route')}",
                "summary": (
                    "The returned result still depends on external literature or comparison work before the current "
                    "route can be treated as complete."
                ),
                "blocker_reason": str(returned_result.get("decision_reason") or decision["reason"]),
                "suggested_queries": default_queries,
                "theorem_family_ids": [],
                "affected_unit_ids": [],
            }
        ]

    normalized: list[dict] = []
    max_queries = int(FOLLOWUP_POLICY.get("max_queries") or 3)
    for index, item in enumerate(rows_to_normalize, start=1):
        gap_kind = str(item.get("gap_kind") or item.get("kind") or "").strip()
        if not gap_kind or gap_kind not in VALID_FOLLOWUP_GAP_KINDS:
            raise SystemExit(
                f"Invalid followup_gap_writeback entry {index}: gap_kind must be one of {sorted(VALID_FOLLOWUP_GAP_KINDS)}."
            )
        return_to_stage = str(item.get("return_to_stage") or RETURN_TO_STAGE_BY_GAP_KIND.get(gap_kind) or "L3").strip()
        if return_to_stage not in {"L0", "L1", "L3", "L4_formalization"}:
            raise SystemExit(
                f"Invalid followup_gap_writeback entry {index}: unsupported return_to_stage `{return_to_stage}`."
            )
        summary = str(item.get("summary") or "").strip()
        blocker_reason = str(item.get("blocker_reason") or item.get("reason") or "").strip()
        if not summary or not blocker_reason:
            raise SystemExit(
                f"Invalid followup_gap_writeback entry {index}: both `summary` and `blocker_reason` are required."
            )
        title = str(item.get("title") or default_gap_title(gap_kind, route, task_payload, index)).strip()
        theorem_family_ids = unique_list(ensure_string_list(item.get("theorem_family_ids")))
        affected_unit_ids = unique_list(ensure_string_list(item.get("affected_unit_ids")))
        evidence_refs = unique_list(
            [
                canonicalize_artifact_ref(ref)
                for ref in ensure_string_list(item.get("evidence_refs"))
                if canonicalize_artifact_ref(ref)
            ]
            + [
                ref
                for ref in (
                    relative_to_root(paths["returned_result_path"], knowledge_root),
                    relative_to_root(paths["result_manifest_path"], knowledge_root),
                    relative_to_root(paths["execution_task_path"], knowledge_root),
                    relative_to_root(paths["selected_route_path"], knowledge_root),
                )
                if ref
            ]
        )
        default_priority = str(
            DEFAULT_GAP_PRIORITY_BY_STAGE.get(return_to_stage)
            or FOLLOWUP_POLICY.get("default_priority")
            or "medium"
        )
        suggested_queries = normalize_followup_query_rows(
            item.get("suggested_queries") or item.get("literature_followup_queries"),
            default_reason=blocker_reason,
            default_priority=default_priority,
            default_target_source_type=str(item.get("target_source_type") or DEFAULT_FOLLOWUP_GAP_TARGET_SOURCE_TYPE),
            result_id=result_id,
        )
        if return_to_stage == "L0" and not suggested_queries:
            query_terms = unique_list(
                theorem_family_ids
                + affected_unit_ids
                + [
                    title,
                    summary,
                    str(route.get("objective") or ""),
                ]
            )
            query = " ".join(term for term in query_terms if term).strip()
            if query:
                suggested_queries = [
                    {
                        "query": query,
                        "reason": blocker_reason,
                        "priority": default_priority,
                        "target_source_type": str(
                            item.get("target_source_type") or DEFAULT_FOLLOWUP_GAP_TARGET_SOURCE_TYPE
                        ),
                        "triggered_by_result_id": result_id,
                    }
                ]
        gap_slug = slugify(f"{route.get('route_id') or 'route'}-{index}-{title}")
        normalized.append(
            {
                "gap_id": str(item.get("gap_id") or f"followup_gap:{gap_slug}"),
                "gap_kind": gap_kind,
                "title": title,
                "summary": summary,
                "blocker_reason": blocker_reason,
                "parent_route_id": str(route.get("route_id") or ""),
                "parent_task_id": str(task_payload.get("task_id") or ""),
                "parent_candidate_id": str(item.get("parent_candidate_id") or task_payload.get("candidate_id") or ""),
                "parent_unit_id": str(item.get("parent_unit_id") or ""),
                "theorem_family_ids": theorem_family_ids,
                "affected_unit_ids": affected_unit_ids,
                "evidence_refs": evidence_refs,
                "return_to_stage": return_to_stage,
                "reopen_conditions": unique_list(
                    ensure_string_list(item.get("reopen_conditions")) or default_reopen_conditions(gap_kind, return_to_stage)
                ),
                "status": str(item.get("status") or DEFAULT_FOLLOWUP_GAP_STATUS or "open"),
                "suggested_queries": suggested_queries[:max_queries],
                "notes": str(item.get("notes") or "").strip(),
            }
        )
    return normalized


def persist_followup_gap_writeback(
    *,
    knowledge_root: Path,
    paths: dict[str, Path | None],
    topic_slug: str,
    run_id: str,
    result_id: str,
    updated_by: str,
    gaps: list[dict],
) -> dict | None:
    if not gaps or paths["followup_gap_writeback_path"] is None or paths["followup_gap_writeback_note_path"] is None:
        return None
    payload = {
        "gap_writeback_version": 1,
        "topic_slug": topic_slug,
        "run_id": run_id,
        "result_id": result_id,
        "updated_at": now_iso(),
        "updated_by": updated_by,
        "gaps": gaps,
    }
    write_json(paths["followup_gap_writeback_path"], payload)
    lines = [
        "# Follow-up gap writeback",
        "",
        f"- Topic slug: `{topic_slug}`",
        f"- Run id: `{run_id}`",
        f"- Result id: `{result_id}`",
        f"- Updated by: `{updated_by}`",
        f"- Gap count: `{len(gaps)}`",
        "",
    ]
    for index, gap in enumerate(gaps, start=1):
        lines.extend(
            [
                f"## {index}. {gap['title']}",
                "",
                f"- Gap id: `{gap['gap_id']}`",
                f"- Gap kind: `{gap['gap_kind']}`",
                f"- Return to stage: `{gap['return_to_stage']}`",
                f"- Status: `{gap['status']}`",
                f"- Parent route id: `{gap['parent_route_id']}`",
                f"- Parent task id: `{gap['parent_task_id']}`",
                f"- Parent candidate id: `{gap.get('parent_candidate_id') or '(none)'}`",
                f"- Parent unit id: `{gap.get('parent_unit_id') or '(none)'}`",
                f"- Theorem families: `{', '.join(gap.get('theorem_family_ids') or []) or '(none)'}`",
                f"- Affected units: `{', '.join(gap.get('affected_unit_ids') or []) or '(none)'}`",
                "",
                "### Why it blocks",
                "",
                f"- {gap['blocker_reason']}",
                "",
                "### Summary",
                "",
                f"- {gap['summary']}",
                "",
                "### Reopen conditions",
                "",
            ]
        )
        for item in gap.get("reopen_conditions") or ["No explicit reopen condition recorded."]:
            lines.append(f"- {item}")
        lines.extend(["", "### Evidence refs", ""])
        for item in gap.get("evidence_refs") or ["(none)"]:
            lines.append(f"- `{item}`" if item != "(none)" else f"- {item}")
        lines.extend(["", "### Suggested Layer-0 queries", ""])
        for query in gap.get("suggested_queries") or []:
            lines.append(
                f"- `{query['query']}` priority=`{query['priority']}` target=`{query['target_source_type']}` reason=`{query['reason']}`"
            )
        if not (gap.get("suggested_queries") or []):
            lines.append("- None.")
        if gap.get("notes"):
            lines.extend(["", "### Notes", "", f"- {gap['notes']}"])
        lines.append("")
    write_text(paths["followup_gap_writeback_note_path"], "\n".join(lines) + "\n")
    return {
        "path": relative_to_root(paths["followup_gap_writeback_path"], knowledge_root),
        "note_path": relative_to_root(paths["followup_gap_writeback_note_path"], knowledge_root),
        "gap_count": len(gaps),
    }


def task_priority(status: str | None) -> int:
    if status == "planned":
        return 100
    if status == "blocked":
        return 90
    if status == "failed":
        return 80
    if status == "running":
        return 70
    if status == "completed":
        return 10
    return 50


def condition_matches(context: dict[str, bool], token: str) -> bool:
    return bool(context.get(token, False))


def highest_severity(severities: list[str], default: str = "info") -> str:
    severity_rank = FAILURE_CLASSIFICATION_POLICY.get("severity_rank") or {}
    best = default
    best_rank = int(severity_rank.get(default, 0))
    for severity in severities:
        rank = int(severity_rank.get(severity, 0))
        if rank > best_rank:
            best = severity
            best_rank = rank
    return best


def load_execution_task_candidates(paths: dict[str, Path | None], knowledge_root: Path) -> list[dict]:
    execution_tasks_dir = paths["execution_tasks_dir"]
    if execution_tasks_dir is None:
        return []
    if not execution_tasks_dir.exists():
        compatibility_dir = compatibility_projection_path(execution_tasks_dir)
        if compatibility_dir is None or not compatibility_dir.exists():
            return []
        execution_tasks_dir = compatibility_dir

    candidates: list[dict] = []
    for task_path in sorted(execution_tasks_dir.glob("*.json")):
        payload = read_json(task_path)
        if payload is None:
            continue
        candidates.append(
            {
                "path": task_path,
                "relpath": relative_to_root(task_path, knowledge_root),
                "payload": payload,
                "status": payload.get("status", "planned"),
            }
        )
    candidates.sort(
        key=lambda item: (
            -task_priority(item["status"]),
            item["payload"].get("task_id", ""),
        )
    )
    return candidates


def action_requests_rerun(summary: str) -> bool:
    lowered = summary.lower()
    return any(marker in lowered for marker in RERUN_HINTS)


def action_invites_execution(summary: str) -> bool:
    lowered = summary.lower().strip()
    if lowered.startswith(NON_EXECUTION_PREFIXES):
        return False
    return any(marker in lowered for marker in EXECUTION_HINTS)


def action_matches_task(summary: str, task_candidate: dict) -> dict:
    payload = task_candidate["payload"]
    task_path = Path(task_candidate["path"])
    explicit_refs = extract_backtick_items(summary)
    score = 0
    explicit_match = False

    for ref in explicit_refs:
        if ref.endswith(task_path.name) or ref.endswith(payload.get("task_id", "")):
            score += 1000
            explicit_match = True

    action_tokens = tokenize(summary)
    anchor_tokens = tokenize(" ".join([payload.get("task_id", ""), task_path.stem]))
    task_tokens = tokenize(
        " ".join(
            [
                payload.get("task_id", ""),
                payload.get("summary", ""),
                task_path.stem,
            ]
        )
    )
    anchor_overlap = len(action_tokens & anchor_tokens)
    token_overlap = len(action_tokens & task_tokens)
    score += 40 * anchor_overlap
    score += 25 * token_overlap
    score += task_priority(payload.get("status"))
    return {
        "score": score,
        "anchor_overlap": anchor_overlap,
        "token_overlap": token_overlap,
        "explicit_match": explicit_match,
    }


def choose_route_candidate(
    knowledge_root: Path,
    topic_state: dict,
    queue_rows: list[dict] | None = None,
) -> dict | None:
    topic_slug = topic_state["topic_slug"]
    run_id = derive_run_id(topic_state)
    paths = build_paths(knowledge_root, topic_slug, run_id)
    if queue_rows is None:
        queue_rows = read_jsonl(paths["queue_path"])  # type: ignore[arg-type]
    manual_actions = [
        row
        for row in queue_rows
        if row.get("status") == "pending"
        and row.get("action_type") not in SYSTEM_ACTION_TYPES
        and row.get("action_type") not in {"skill_discovery", "inspect_resume_state"}
    ]
    task_candidates = load_execution_task_candidates(paths, knowledge_root)

    best_action: dict | None = None
    best_task: dict | None = None
    best_match: dict | None = None
    best_score = -1

    for action in manual_actions:
        summary = str(action.get("summary", ""))
        if not action_invites_execution(summary):
            continue
        rerun_requested = action_requests_rerun(summary)
        for task_candidate in task_candidates:
            if task_candidate["status"] == "completed" and not rerun_requested:
                continue
            match = action_matches_task(summary, task_candidate)
            if not match["explicit_match"] and match["anchor_overlap"] < MIN_ROUTE_TOKEN_OVERLAP:
                continue
            if match["score"] > best_score:
                best_score = match["score"]
                best_action = action
                best_task = task_candidate
                best_match = match

    if best_task is None:
        return None
    if best_match is None:
        return None
    if not best_match["explicit_match"] and best_match["score"] < MIN_ROUTE_SCORE:
        return None

    source_summary = str((best_action or {}).get("summary") or "No pending action summary was available.")
    task_payload = copy.deepcopy((best_task or {}).get("payload") or {})
    validation_run_root = paths["validation_run_root"]
    input_artifacts = ensure_string_list(task_payload.get("input_artifacts"))
    if not input_artifacts:
        input_artifacts = [
            resolve_artifact_ref(ref, knowledge_root, validation_run_root)  # type: ignore[arg-type]
            for ref in extract_backtick_items(source_summary)
        ]
    expected_outputs = ensure_string_list(task_payload.get("planned_outputs"))
    failure_signals = ensure_string_list(task_payload.get("failure_signals"))
    if not failure_signals:
        failure_signals = list(DEFAULT_FAILURE_SIGNALS)

    action_suffix = (best_action or {}).get("action_id") or (task_payload.get("task_id") or "route")
    route_id = f"route:{topic_slug}:{slugify(str(action_suffix).split(':')[-1])}"
    route_type = task_payload.get("surface") or (best_action or {}).get("action_type") or "manual_followup"
    research_profile = resolve_task_research_profile(
        task_payload=task_payload,
        classification_contract_path=str(
            knowledge_root / "topics" / topic_slug / "runtime" / "classification_contract.jsonl"
        ),
    )

    selection_reason = (
        SELECTION_REASON_TEMPLATES.get("fallback")
        or "Selected the strongest executable validation lane from the current pending actions."
    )
    if best_match["explicit_match"]:
        selection_reason = (
            SELECTION_REASON_TEMPLATES.get("explicit_match")
            or "Selected the explicitly referenced execution-task record from the current pending actions."
        )
    elif best_task is not None:
        selection_reason = (
            SELECTION_REASON_TEMPLATES.get("score_match")
            or "Selected the highest-scoring pending action against an existing non-completed execution-task record."
        )

    explicit_human_confirm = task_payload.get("needs_human_confirm")
    if explicit_human_confirm is None:
        needs_human_confirm = True
    else:
        needs_human_confirm = bool(explicit_human_confirm)
    allow_web_search = bool(task_payload.get("allow_web_search")) if best_task is not None else False

    return {
        "route_id": route_id,
        "route_type": route_type,
        "objective": source_summary,
        "source_action_id": (best_action or {}).get("action_id"),
        "source_action_summary": source_summary,
        "source_execution_task_path": (
            relative_to_root(best_task["path"], knowledge_root) if best_task is not None else None
        ),
        "run_id": run_id,
        "input_artifacts": unique_list(input_artifacts),
        "expected_outputs": unique_list(expected_outputs),
        "success_criterion": ensure_string_list(task_payload.get("pass_conditions")) or [source_summary],
        "failure_signals": failure_signals,
        "needs_human_confirm": needs_human_confirm,
        "allow_web_search": allow_web_search,
        "selected_at": now_iso(),
        "selected_by": topic_state.get("updated_by") or "codex",
        "assigned_runtime": task_payload.get("assigned_runtime") or "codex",
        "validation_note": task_payload.get("validation_note"),
        "candidate_id": task_payload.get("candidate_id"),
        "surface": task_payload.get("surface"),
        "selection_reason": selection_reason,
        "expected_result_artifact": relative_to_root(paths["returned_result_path"], knowledge_root),
        "candidate_score": best_match["score"],
        "closed_loop_policy_path": closed_loop_policy_path_ref(),
        "research_mode": task_payload.get("research_mode") or research_profile["research_mode"],
        "research_mode_profile_path": research_profile["profile"].get("profile_path"),
        "executor_kind": task_payload.get("executor_kind") or research_profile["executor_kind"],
        "reasoning_profile": task_payload.get("reasoning_profile") or research_profile["reasoning_profile"],
    }


def compute_closed_loop_status(
    knowledge_root: Path,
    topic_slug: str,
    run_id: str | None,
    queue_rows: list[dict] | None = None,
) -> dict:
    paths = build_paths(knowledge_root, topic_slug, run_id)
    selected_route = read_json(paths["selected_route_path"])  # type: ignore[arg-type]
    execution_task = read_json(paths["execution_task_path"])  # type: ignore[arg-type]
    returned_result = read_json(paths["returned_result_path"]) if paths["returned_result_path"] else None
    result_manifest = read_json(paths["result_manifest_path"]) if paths["result_manifest_path"] else None
    trajectory_rows = read_jsonl(paths["trajectory_log_path"]) if paths["trajectory_log_path"] else []
    failure_classification = (
        read_json(paths["failure_classification_path"]) if paths["failure_classification_path"] else None
    )
    decision_rows = read_jsonl(paths["decision_ledger_path"]) if paths["decision_ledger_path"] else []
    literature_followups = read_json(paths["literature_followup_path"]) if paths["literature_followup_path"] else None
    followup_gap_writeback = (
        read_json(paths["followup_gap_writeback_path"]) if paths["followup_gap_writeback_path"] else None
    )
    latest_decision = decision_rows[-1] if decision_rows else None
    route_candidate = None

    next_transition = None
    next_transition_reason = "No further closed-loop transition is currently ready."
    awaiting_external_result = False

    if returned_result is not None and result_manifest is None:
        next_transition = "ingest_result"
        next_transition_reason = "A returned execution result exists and has not yet been ingested into durable writeback artifacts."
    elif selected_route is None:
        route_candidate = choose_route_candidate(
            knowledge_root,
            {
                "topic_slug": topic_slug,
                "latest_run_id": run_id,
            },
            queue_rows=queue_rows,
        )
        if route_candidate is not None:
            next_transition = "select_route"
            next_transition_reason = "A matched non-completed execution route is available from the current topic state."
        else:
            next_transition_reason = (
                "No executable validation route can be selected from the current topic state without a new or updated execution-task record."
            )
    elif execution_task is None or execution_task.get("route_id") != selected_route.get("route_id"):
        next_transition = "materialize_task"
        next_transition_reason = "A route is selected but no concrete execution handoff task has been materialized yet."
    elif execution_task is not None and returned_result is None:
        awaiting_external_result = True
        next_transition_reason = "Execution task is ready; waiting for an external executor to write the returned result artifact."

    return {
        "paths": {key: relative_to_root(value, knowledge_root) for key, value in paths.items()},
        "selected_route": selected_route,
        "execution_task": execution_task,
        "returned_result": returned_result,
        "result_manifest": result_manifest,
        "trajectory_log": trajectory_rows,
        "failure_classification": failure_classification,
        "latest_decision": latest_decision,
        "literature_followups": literature_followups if isinstance(literature_followups, list) else [],
        "followup_gap_writeback": followup_gap_writeback,
        "followup_gaps": list((followup_gap_writeback or {}).get("gaps") or []),
        "route_candidate": route_candidate,
        "next_transition": next_transition,
        "next_transition_reason": next_transition_reason,
        "awaiting_external_result": awaiting_external_result,
    }


def materialize_execution_task(knowledge_root: Path, topic_state: dict, updated_by: str) -> dict:
    topic_slug = topic_state["topic_slug"]
    run_id = derive_run_id(topic_state)
    paths = build_paths(knowledge_root, topic_slug, run_id)
    selected_route = read_json(paths["selected_route_path"])  # type: ignore[arg-type]
    if selected_route is None:
        raise SystemExit("Cannot materialize execution_task.json without selected_validation_route.json")

    source_task_payload = None
    source_task_path = selected_route.get("source_execution_task_path")
    if source_task_path:
        source_task_payload = read_json(knowledge_root / str(source_task_path))

    task_id = None
    if source_task_payload is not None:
        task_id = source_task_payload.get("task_id")
    if not task_id:
        task_id = slugify(selected_route.get("route_id", topic_slug).split(":")[-1])

    validation_note = None
    if source_task_payload is not None:
        validation_note = source_task_payload.get("validation_note")
    validation_note = validation_note or selected_route.get("validation_note") or "(missing)"

    candidate_id = None
    if source_task_payload is not None:
        candidate_id = source_task_payload.get("candidate_id")
    candidate_id = candidate_id or selected_route.get("candidate_id") or f"candidate:{slugify(topic_slug)}-closed-loop-v1"

    research_profile = resolve_task_research_profile(
        explicit_mode=topic_state.get("research_mode"),
        task_payload=source_task_payload or {},
        route=selected_route,
        existing_topic_state=topic_state,
        classification_contract_path=str(
            knowledge_root / "topics" / topic_slug / "runtime" / "classification_contract.jsonl"
        ),
    )

    surface = None
    if source_task_payload is not None:
        surface = source_task_payload.get("surface")
    surface = surface or selected_route.get("surface") or research_profile["profile"].get("default_surface") or "coding"
    if surface not in {"numerical", "symbolic", "formal", "coding", "human_review"}:
        surface = "coding"

    executor_kind = (
        (source_task_payload or {}).get("executor_kind")
        or selected_route.get("executor_kind")
        or research_profile["executor_kind"]
    )
    assigned_runtime = (
        (source_task_payload or {}).get("assigned_runtime")
        or selected_route.get("assigned_runtime")
        or research_profile["assigned_runtime"]
    )
    reasoning_profile = (
        (source_task_payload or {}).get("reasoning_profile")
        or selected_route.get("reasoning_profile")
        or research_profile["reasoning_profile"]
    )

    task_payload = {
        "task_id": task_id,
        "validation_note": validation_note,
        "candidate_id": candidate_id,
        "research_mode": research_profile["research_mode"],
        "research_mode_profile_path": research_profile["profile"].get("profile_path"),
        "closed_loop_policy_path": closed_loop_policy_path_ref(),
        "surface": surface,
        "status": "planned",
        "input_artifacts": ensure_string_list(
            (source_task_payload or {}).get("input_artifacts")
        )
        or ensure_string_list(selected_route.get("input_artifacts")),
        "planned_outputs": ensure_string_list(
            (source_task_payload or {}).get("planned_outputs")
        )
        or ensure_string_list(selected_route.get("expected_outputs")),
        "pass_conditions": ensure_string_list(
            (source_task_payload or {}).get("pass_conditions")
        )
        or ensure_string_list(selected_route.get("success_criterion")),
        "failure_signals": ensure_string_list(
            (source_task_payload or {}).get("failure_signals")
        )
        or ensure_string_list(selected_route.get("failure_signals")),
        "assigned_runtime": assigned_runtime,
        "executor_kind": executor_kind,
        "reasoning_profile": reasoning_profile,
        "reproducibility_requirements": ensure_string_list(
            (source_task_payload or {}).get("reproducibility_requirements")
        )
        or research_profile["reproducibility_expectations"],
        "required_human_notes": ensure_string_list((source_task_payload or {}).get("required_human_notes"))
        or research_profile["note_expectations"],
        "result_artifacts": [],
        "summary": (source_task_payload or {}).get("summary")
        or selected_route.get("objective")
        or f"Execute route {selected_route['route_id']}",
        "run_id": selected_route.get("run_id"),
        "route_id": selected_route["route_id"],
        "source_action_id": selected_route.get("source_action_id"),
        "source_execution_task_path": selected_route.get("source_execution_task_path"),
        "workspace_root": knowledge_root.parent.name,
        "where_to_run": knowledge_root.parent.name,
        "allowed_input_artifacts": ensure_string_list(selected_route.get("input_artifacts")),
        "result_writeback_path": relative_to_root(paths["returned_result_path"], knowledge_root),
        "result_template_path": relative_to_root(paths["execution_result_template_path"], knowledge_root),
        "execution_notes_dir": relative_to_root(paths["execution_notes_dir"], knowledge_root),
        "trajectory_log_path": relative_to_root(paths["trajectory_log_path"], knowledge_root),
        "trajectory_note_path": relative_to_root(paths["trajectory_note_path"], knowledge_root),
        "failure_classification_path": relative_to_root(paths["failure_classification_path"], knowledge_root),
        "failure_classification_note_path": relative_to_root(paths["failure_classification_note_path"], knowledge_root),
        "needs_human_confirm": bool(selected_route.get("needs_human_confirm", True)),
        "auto_dispatch_allowed": not bool(selected_route.get("needs_human_confirm", True)),
        "allow_web_search": bool(selected_route.get("allow_web_search", False)),
        "materialized_at": now_iso(),
        "materialized_by": updated_by,
        "human_summary": selected_route.get("objective") or "(missing)",
    }
    write_json(paths["execution_task_path"], task_payload)  # type: ignore[arg-type]

    markdown = [
        "# Closed-loop execution task",
        "",
        f"- Topic slug: `{topic_slug}`",
        f"- Run id: `{run_id or '(missing)'}`",
        f"- Route id: `{selected_route['route_id']}`",
        f"- Task id: `{task_payload['task_id']}`",
        f"- Research mode: `{task_payload['research_mode']}`",
        f"- Research-mode profile: `{task_payload['research_mode_profile_path']}`",
        f"- Closed-loop policy: `{task_payload['closed_loop_policy_path']}`",
        f"- Assigned runtime: `{task_payload['assigned_runtime']}`",
        f"- Executor kind: `{task_payload['executor_kind']}`",
        f"- Reasoning profile: `{task_payload['reasoning_profile']}`",
        f"- Surface: `{task_payload['surface']}`",
        f"- Needs human confirm: `{str(task_payload['needs_human_confirm']).lower()}`",
        f"- Auto dispatch allowed: `{str(task_payload['auto_dispatch_allowed']).lower()}`",
        f"- Allow web search: `{str(task_payload['allow_web_search']).lower()}`",
        f"- Return result artifact: `{task_payload['result_writeback_path']}`",
        f"- Result template: `{task_payload['result_template_path']}`",
        f"- Execution notes dir: `{task_payload['execution_notes_dir'] or '(missing)'}`",
        f"- Trajectory log: `{task_payload['trajectory_log_path'] or '(missing)'}`",
        f"- Failure classification: `{task_payload['failure_classification_path'] or '(missing)'}`",
        "",
        "## Summary",
        "",
        f"- {task_payload['human_summary']}",
        "",
        "## Approval gate",
        "",
        (
            "- Human confirmation is required before dispatch because this execution lane was inferred from the current route and has not yet been explicitly approved in durable task artifacts."
            if task_payload["needs_human_confirm"]
            else "- This execution lane is already marked as explicitly approved for automatic dispatch."
        ),
        "",
        "## Allowed input artifacts",
        "",
    ]
    for artifact in task_payload["allowed_input_artifacts"]:
        markdown.append(f"- `{artifact}`")
    if not task_payload["allowed_input_artifacts"]:
        markdown.append("- `(none declared)`")

    markdown.extend(["", "## Expected outputs", ""])
    for artifact in task_payload["planned_outputs"]:
        markdown.append(f"- `{artifact}`")
    if not task_payload["planned_outputs"]:
        markdown.append("- `(none declared)`")

    markdown.extend(["", "## Pass conditions", ""])
    for condition in task_payload["pass_conditions"]:
        markdown.append(f"- {condition}")

    markdown.extend(["", "## Failure signals", ""])
    for signal in task_payload["failure_signals"]:
        markdown.append(f"- {signal}")

    markdown.extend(["", "## Reproducibility requirements", ""])
    for requirement in task_payload["reproducibility_requirements"]:
        markdown.append(f"- {requirement}")
    if not task_payload["reproducibility_requirements"]:
        markdown.append("- `(none declared)`")

    markdown.extend(["", "## Required human-readable notes", ""])
    for requirement in task_payload["required_human_notes"]:
        markdown.append(f"- {requirement}")
    if not task_payload["required_human_notes"]:
        markdown.append("- `(none declared)`")

    markdown.extend(
        [
            "",
            "## Truthfulness guardrail",
            "",
            "- Do not mark success unless the returned execution result artifact really exists.",
            "- If using a fixture-backed or placeholder result, label it explicitly as non-scientific.",
            "",
        ]
    )
    write_text(paths["execution_task_md_path"], "\n".join(markdown))  # type: ignore[arg-type]
    return task_payload


def normalize_artifact_paths(
    knowledge_root: Path,
    artifact_refs: list[str],
) -> tuple[list[str], list[str]]:
    existing: list[str] = []
    missing: list[str] = []
    for artifact in artifact_refs:
        canonical_ref = canonicalize_artifact_ref(artifact)
        artifact_path = (
            knowledge_root / canonical_ref
            if canonical_ref.startswith(
                (
                    "topics/",
                    "validation/",
                    "feedback/",
                    "runtime/",
                    "source-layer/",
                    "intake/",
                    "canonical/",
                    "consultation/",
                )
            )
            else None
        )
        compatibility_path = compatibility_projection_path(artifact_path) if artifact_path is not None else None
        if artifact_path is not None and (
            artifact_path.exists() or (compatibility_path is not None and compatibility_path.exists())
        ):
            existing.append(canonical_ref)
        elif artifact_path is None:
            existing.append(canonical_ref)
        else:
            missing.append(canonical_ref)
    return existing, missing


def build_trajectory_events(
    task_payload: dict,
    returned_result: dict,
    manifest: dict,
    missing_artifacts: list[str],
    task_contract_mismatch: bool,
) -> list[dict]:
    provided_events = ensure_dict_list(returned_result.get("trajectory_events"))
    if provided_events:
        normalized: list[dict] = []
        for index, event in enumerate(provided_events, start=1):
            normalized.append(
                {
                    "event_index": index,
                    "event_type": str(event.get("event_type") or event.get("stage") or "executor_event"),
                    "status": str(event.get("status") or manifest["status"] or "partial"),
                    "message": str(event.get("message") or event.get("summary") or "").strip()
                    or "Executor reported a trajectory event.",
                    "recorded_at": str(event.get("recorded_at") or event.get("timestamp") or now_iso()),
                    "artifacts": unique_list(
                        [canonicalize_artifact_ref(ref) for ref in ensure_string_list(event.get("artifacts"))]
                    ),
                }
            )
        return normalized

    events = [
        {
            "event_index": 1,
            "event_type": "task_materialized",
            "status": "planned",
            "message": str(task_payload.get("human_summary") or task_payload.get("summary") or "Execution task materialized."),
            "recorded_at": str(task_payload.get("materialized_at") or now_iso()),
            "artifacts": unique_list(ensure_string_list(task_payload.get("allowed_input_artifacts"))),
        },
        {
            "event_index": 2,
            "event_type": "executor_report",
            "status": str(returned_result.get("status") or manifest["status"] or "partial"),
            "message": str(
                returned_result.get("what_actually_ran")
                or returned_result.get("summary")
                or "The executor returned a bounded execution report."
            ),
            "recorded_at": str(returned_result.get("created_at") or now_iso()),
            "artifacts": unique_list(
                [canonicalize_artifact_ref(ref) for ref in ensure_string_list(returned_result.get("artifacts"))]
            ),
        },
    ]
    if task_contract_mismatch:
        events.append(
            {
                "event_index": len(events) + 1,
                "event_type": "task_contract_mismatch",
                "status": "partial",
                "message": (
                    f"Returned result task_id `{returned_result.get('task_id')}` did not match "
                    f"expected `{task_payload.get('task_id')}`."
                ),
                "recorded_at": now_iso(),
                "artifacts": [],
            }
        )
    if missing_artifacts:
        events.append(
            {
                "event_index": len(events) + 1,
                "event_type": "missing_artifacts",
                "status": "partial",
                "message": f"Declared artifacts missing during ingest: {', '.join(missing_artifacts)}",
                "recorded_at": now_iso(),
                "artifacts": [],
            }
        )
    events.append(
        {
            "event_index": len(events) + 1,
            "event_type": "ingest_summary",
            "status": manifest["status"],
            "message": (
                f"Ingest classified the execution as `{manifest['status']}` with "
                f"{len(manifest.get('artifacts') or [])} verified artifact(s)."
            ),
            "recorded_at": now_iso(),
            "artifacts": unique_list(ensure_string_list(manifest.get("artifacts"))),
        }
    )
    return events


def persist_trajectory_log(
    knowledge_root: Path,
    paths: dict[str, Path | None],
    topic_slug: str,
    run_id: str | None,
    task_payload: dict,
    returned_result: dict,
    manifest: dict,
    missing_artifacts: list[str],
    task_contract_mismatch: bool,
) -> dict:
    rows = build_trajectory_events(task_payload, returned_result, manifest, missing_artifacts, task_contract_mismatch)
    trajectory_id = f"trajectory:{slugify(task_payload['task_id'])}:{slugify(returned_result['result_id'])}"
    log_rows: list[dict] = []
    for row in rows:
        log_rows.append(
            {
                "trajectory_id": trajectory_id,
                "topic_slug": topic_slug,
                "run_id": run_id,
                "route_id": manifest.get("route_id"),
                "task_id": task_payload.get("task_id"),
                "result_id": returned_result.get("result_id"),
                "research_mode": task_payload.get("research_mode"),
                "executor_kind": task_payload.get("executor_kind"),
                "reasoning_profile": task_payload.get("reasoning_profile"),
                **row,
            }
        )

    write_jsonl_rows(paths["trajectory_log_path"], log_rows)  # type: ignore[arg-type]

    lines = [
        "# Execution trajectory log",
        "",
        f"- Topic slug: `{topic_slug}`",
        f"- Run id: `{run_id or '(missing)'}`",
        f"- Route id: `{manifest.get('route_id') or '(missing)'}`",
        f"- Task id: `{task_payload.get('task_id') or '(missing)'}`",
        f"- Result id: `{returned_result.get('result_id') or '(missing)'}`",
        f"- Research mode: `{task_payload.get('research_mode') or '(missing)'}`",
        f"- Executor kind: `{task_payload.get('executor_kind') or '(missing)'}`",
        f"- Reasoning profile: `{task_payload.get('reasoning_profile') or '(missing)'}`",
        "",
        "## Events",
        "",
    ]
    for row in log_rows:
        lines.append(
            f"{row['event_index']}. [{row['status']}] `{row['event_type']}` {row['message']}"
        )
    write_text(paths["trajectory_note_path"], "\n".join(lines) + "\n")  # type: ignore[arg-type]

    return {
        "trajectory_id": trajectory_id,
        "event_count": len(log_rows),
        "path": relative_to_root(paths["trajectory_log_path"], knowledge_root),
        "note_path": relative_to_root(paths["trajectory_note_path"], knowledge_root),
    }


def classify_failure(
    returned_result: dict,
    manifest: dict,
    task_payload: dict,
    missing_artifacts: list[str],
    task_contract_mismatch: bool,
) -> dict:
    triggered_signals = unique_list(ensure_string_list(returned_result.get("failure_signals_triggered")))
    if missing_artifacts:
        triggered_signals.append("Declared output artifacts were missing during ingest.")
    if task_contract_mismatch:
        triggered_signals.append("Returned result task_id did not match the declared execution task.")
    triggered_signals = unique_list(triggered_signals)

    context = {
        "manifest.fixture_backed": bool(manifest.get("fixture_backed")),
        "manifest.non_scientific": bool(manifest.get("non_scientific")),
        "manifest.executor_reported_status=failed": str(manifest.get("executor_reported_status") or "") == "failed",
        "manifest.status=failed": str(manifest.get("status") or "") == "failed",
        "manifest.status=partial": str(manifest.get("status") or "") == "partial",
        "missing_artifacts_present": bool(missing_artifacts),
        "task_contract_mismatch": bool(task_contract_mismatch),
        "contradiction_detected": bool(returned_result.get("contradiction_detected")),
        "missing_baseline_support": bool(returned_result.get("missing_baseline_support")),
        "inconclusive": bool(returned_result.get("inconclusive")),
    }

    categories: list[str] = []
    matched_severities: list[str] = []
    for rule in FAILURE_CLASSIFICATION_POLICY.get("category_rules") or []:
        conditions = [str(item).strip() for item in (rule.get("when_any_true") or []) if str(item).strip()]
        if conditions and not any(condition_matches(context, token) for token in conditions):
            continue
        category_id = str(rule.get("id") or "").strip()
        if category_id:
            categories.append(category_id)
        severity = str(rule.get("severity") or "").strip()
        if severity:
            matched_severities.append(severity)
    if not categories:
        categories.append(
            str(FAILURE_CLASSIFICATION_POLICY.get("default_category") or "success_without_detected_failure")
        )

    severity = highest_severity(
        matched_severities,
        default=str(FAILURE_CLASSIFICATION_POLICY.get("default_severity") or "info"),
    )
    summary = str(
        (FAILURE_CLASSIFICATION_POLICY.get("summary_by_severity") or {}).get(
            severity,
            "Failure classification summary unavailable.",
        )
    )

    return {
        "classification_id": (
            f"failure-classification:{slugify(task_payload['task_id'])}:{slugify(returned_result['result_id'])}"
        ),
        "recorded_at": now_iso(),
        "manifest_status": manifest.get("status"),
        "executor_reported_status": manifest.get("executor_reported_status"),
        "research_mode": task_payload.get("research_mode"),
        "executor_kind": task_payload.get("executor_kind"),
        "reasoning_profile": task_payload.get("reasoning_profile"),
        "severity": severity,
        "categories": categories,
        "closed_loop_policy_path": closed_loop_policy_path_ref(),
        "triggered_failure_signals": triggered_signals,
        "declared_failure_signals": ensure_string_list(task_payload.get("failure_signals")),
        "missing_artifacts": missing_artifacts,
        "summary": summary,
    }


def persist_failure_classification(
    knowledge_root: Path,
    paths: dict[str, Path | None],
    topic_slug: str,
    run_id: str | None,
    task_payload: dict,
    manifest: dict,
    classification: dict,
) -> dict:
    payload = {
        "topic_slug": topic_slug,
        "run_id": run_id,
        "route_id": manifest.get("route_id"),
        "task_id": task_payload.get("task_id"),
        "result_id": manifest.get("result_id"),
        **classification,
    }
    write_json(paths["failure_classification_path"], payload)  # type: ignore[arg-type]

    lines = [
        "# Failure classification",
        "",
        f"- Topic slug: `{topic_slug}`",
        f"- Run id: `{run_id or '(missing)'}`",
        f"- Route id: `{manifest.get('route_id') or '(missing)'}`",
        f"- Task id: `{task_payload.get('task_id') or '(missing)'}`",
        f"- Result id: `{manifest.get('result_id') or '(missing)'}`",
        f"- Severity: `{payload['severity']}`",
        f"- Research mode: `{payload['research_mode'] or '(missing)'}`",
        f"- Executor kind: `{payload['executor_kind'] or '(missing)'}`",
        f"- Reasoning profile: `{payload['reasoning_profile'] or '(missing)'}`",
        "",
        "## Categories",
        "",
    ]
    for category in payload["categories"]:
        lines.append(f"- `{category}`")
    lines.extend(["", "## Triggered failure signals", ""])
    for signal in payload["triggered_failure_signals"] or ["No explicit failure signal was triggered."]:
        lines.append(f"- {signal}")
    lines.extend(["", "## Summary", "", f"- {payload['summary']}"])
    write_text(paths["failure_classification_note_path"], "\n".join(lines) + "\n")  # type: ignore[arg-type]

    return {
        "path": relative_to_root(paths["failure_classification_path"], knowledge_root),
        "note_path": relative_to_root(paths["failure_classification_note_path"], knowledge_root),
        "severity": payload["severity"],
        "categories": payload["categories"],
    }


def build_literature_followups(
    followup_gaps: list[dict],
    returned_result: dict,
    decision: dict,
    route: dict,
    task_payload: dict,
    result_id: str,
) -> list[dict]:
    max_queries = int(FOLLOWUP_POLICY.get("max_queries") or 3)
    normalized: list[dict] = []
    for gap in followup_gaps:
        if str(gap.get("return_to_stage") or "") != "L0":
            continue
        for query in gap.get("suggested_queries") or []:
            normalized.append(
                {
                    "query": str(query.get("query") or "").strip(),
                    "reason": str(query.get("reason") or gap.get("blocker_reason") or decision["reason"]),
                    "priority": str(query.get("priority") or FOLLOWUP_POLICY.get("default_priority") or "medium"),
                    "target_source_type": str(
                        query.get("target_source_type") or DEFAULT_FOLLOWUP_GAP_TARGET_SOURCE_TYPE
                    ),
                    "triggered_by_result_id": result_id,
                    "triggered_by_gap_id": str(gap.get("gap_id") or ""),
                    "gap_kind": str(gap.get("gap_kind") or ""),
                }
            )
    deduped: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        key = (row["query"], row["target_source_type"])
        if not row["query"] or key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    if deduped:
        return deduped[:max_queries]
    return build_declared_literature_followups(returned_result, decision, route, task_payload, result_id)


def infer_decision(returned_result: dict, manifest_status: str, route: dict, task_payload: dict, updated_by: str) -> dict:
    requested_decision = str(returned_result.get("recommended_decision") or "").strip().lower()
    decision = requested_decision if requested_decision in VALID_DECISIONS else None
    reason = str(returned_result.get("decision_reason") or "").strip()
    confidence = 0.25
    matched_rule_id = None

    if decision is None:
        for rule in DECISION_RULES:
            manifest_statuses = {str(item).strip() for item in (rule.get("manifest_status_in") or []) if str(item).strip()}
            if manifest_statuses and manifest_status not in manifest_statuses:
                continue
            trigger_flags = [str(item).strip() for item in (rule.get("when_any_true") or []) if str(item).strip()]
            if trigger_flags and not any(bool(returned_result.get(flag)) for flag in trigger_flags):
                continue
            candidate = str(rule.get("decision") or "").strip().lower()
            if candidate not in VALID_DECISIONS:
                continue
            decision = candidate
            reason = reason or str(rule.get("reason") or "").strip()
            confidence = float(rule.get("confidence") or confidence)
            matched_rule_id = str(rule.get("id") or "").strip() or None
            break
        if decision is None:
            decision = "keep"
            reason = reason or "Returned result met the declared task contract without immediate contradiction."
    else:
        for rule in DECISION_RULES:
            if str(rule.get("decision") or "").strip().lower() == decision:
                confidence = float(rule.get("confidence") or confidence)
                matched_rule_id = str(rule.get("id") or "").strip() or None
                break

    object_type = "route"
    object_ref = route["route_id"]
    if task_payload.get("candidate_id"):
        object_type = "candidate"
        object_ref = task_payload["candidate_id"]

    timestamp = now_iso()
    return {
        "decision_id": f"decision:{slugify(route['route_id'])}:{slugify(timestamp)}",
        "result_id": returned_result.get("result_id"),
        "object_type": object_type,
        "object_ref": object_ref,
        "decision": decision,
        "reason": reason,
        "confidence": confidence,
        "matched_policy_rule_id": matched_rule_id,
        "closed_loop_policy_path": closed_loop_policy_path_ref(),
        "made_by": updated_by,
        "timestamp": timestamp,
    }


def build_next_actions(
    manifest_relpath: str,
    result_summary_relpath: str,
    followup_relpath: str | None,
    followup_gap_relpath: str | None,
    decision: dict,
    returned_result: dict,
) -> list[str]:
    explicit = ensure_string_list(returned_result.get("next_actions"))
    if explicit:
        return explicit

    actions = [
        f"Review `{result_summary_relpath}` before promoting or reusing the current validation route.",
    ]
    if decision["decision"] in {"revise", "defer"}:
        actions.append(
            f"Treat `{manifest_relpath}` as a bounded execution writeback, not as a sufficient scientific conclusion by itself."
        )
    if followup_relpath:
        actions.append(
            f"Run the bounded literature follow-up list in `{followup_relpath}` before strengthening the current claim."
        )
    if followup_gap_relpath:
        actions.append(
            f"Review `{followup_gap_relpath}` and resolve each open gap according to its declared return-to-stage before strengthening the current claim."
        )
    if returned_result.get("fixture_backed") or returned_result.get("non_scientific"):
        actions.append(
            "Replace the fixture-backed control result with a real execution result before any scientific keep/promote decision is attempted."
        )
    return actions


def ingest_execution_result(knowledge_root: Path, topic_state: dict, updated_by: str) -> dict:
    topic_slug = topic_state["topic_slug"]
    run_id = derive_run_id(topic_state)
    paths = build_paths(knowledge_root, topic_slug, run_id)
    selected_route = read_json(paths["selected_route_path"])  # type: ignore[arg-type]
    if selected_route is None:
        raise SystemExit("Cannot ingest execution result without selected_validation_route.json")

    task_payload = read_json(paths["execution_task_path"])  # type: ignore[arg-type]
    if task_payload is None:
        raise SystemExit("Cannot ingest execution result without execution_task.json")

    returned_result = read_json(paths["returned_result_path"]) if paths["returned_result_path"] else None
    if returned_result is None:
        raise SystemExit("Returned execution result artifact is missing.")

    returned_result.setdefault(
        "result_id",
        f"result:{slugify(task_payload['task_id'])}:{slugify(now_iso())}",
    )
    returned_result.setdefault("created_at", now_iso())
    returned_result.setdefault("produced_by", updated_by)
    returned_result.setdefault("research_mode", task_payload.get("research_mode"))
    returned_result.setdefault("executor_kind", task_payload.get("executor_kind"))
    returned_result.setdefault("reasoning_profile", task_payload.get("reasoning_profile"))

    reported_status = str(returned_result.get("status") or "partial").lower()
    manifest_status = reported_status if reported_status in VALID_RESULT_STATUSES else "partial"
    declared_artifacts = unique_list(ensure_string_list(returned_result.get("artifacts")))
    existing_artifacts, missing_artifacts = normalize_artifact_paths(knowledge_root, declared_artifacts)
    task_contract_mismatch = bool(
        returned_result.get("task_id") and returned_result.get("task_id") != task_payload["task_id"]
    )
    if manifest_status == "success" and missing_artifacts:
        manifest_status = "partial"
    if task_contract_mismatch:
        manifest_status = "partial"
        missing_artifacts.append(
            f"task_id mismatch: expected {task_payload['task_id']} but got {returned_result.get('task_id')}"
        )

    manifest = {
        "result_id": returned_result["result_id"],
        "route_id": selected_route["route_id"],
        "task_id": task_payload["task_id"],
        "status": manifest_status,
        "artifacts": existing_artifacts,
        "metrics": returned_result.get("metrics") or {},
        "logs": ensure_string_list(returned_result.get("logs")),
        "produced_by": returned_result.get("produced_by") or updated_by,
        "created_at": returned_result["created_at"],
        "notes": returned_result.get("notes"),
        "executor_reported_status": reported_status,
        "source_result_path": relative_to_root(paths["returned_result_path"], knowledge_root),
        "missing_artifacts": missing_artifacts,
        "fixture_backed": bool(returned_result.get("fixture_backed")),
        "non_scientific": bool(returned_result.get("non_scientific")),
        "research_mode": returned_result.get("research_mode") or task_payload.get("research_mode"),
        "executor_kind": returned_result.get("executor_kind") or task_payload.get("executor_kind"),
        "reasoning_profile": returned_result.get("reasoning_profile") or task_payload.get("reasoning_profile"),
        "required_human_notes": ensure_string_list(task_payload.get("required_human_notes")),
        "reproducibility_requirements": ensure_string_list(task_payload.get("reproducibility_requirements")),
        "closed_loop_policy_path": closed_loop_policy_path_ref(),
        "trajectory_log_path": relative_to_root(paths["trajectory_log_path"], knowledge_root),
        "failure_classification_path": relative_to_root(paths["failure_classification_path"], knowledge_root),
    }
    write_json(paths["result_manifest_path"], manifest)  # type: ignore[arg-type]

    trajectory = persist_trajectory_log(
        knowledge_root=knowledge_root,
        paths=paths,
        topic_slug=topic_slug,
        run_id=run_id,
        task_payload=task_payload,
        returned_result=returned_result,
        manifest=manifest,
        missing_artifacts=missing_artifacts,
        task_contract_mismatch=task_contract_mismatch,
    )
    failure_classification = classify_failure(
        returned_result=returned_result,
        manifest=manifest,
        task_payload=task_payload,
        missing_artifacts=missing_artifacts,
        task_contract_mismatch=task_contract_mismatch,
    )
    failure_summary = persist_failure_classification(
        knowledge_root=knowledge_root,
        paths=paths,
        topic_slug=topic_slug,
        run_id=run_id,
        task_payload=task_payload,
        manifest=manifest,
        classification=failure_classification,
    )

    decision = infer_decision(returned_result, manifest_status, selected_route, task_payload, updated_by)
    decision["result_id"] = returned_result["result_id"]
    append_jsonl(paths["decision_ledger_path"], decision)  # type: ignore[arg-type]

    followup_gaps = normalize_followup_gap_entries(
        returned_result=returned_result,
        decision=decision,
        route=selected_route,
        task_payload=task_payload,
        result_id=returned_result["result_id"],
        paths=paths,
        knowledge_root=knowledge_root,
    )
    followup_gap_writeback = persist_followup_gap_writeback(
        knowledge_root=knowledge_root,
        paths=paths,
        topic_slug=topic_slug,
        run_id=run_id or "(missing)",
        result_id=returned_result["result_id"],
        updated_by=updated_by,
        gaps=followup_gaps,
    )
    followups = build_literature_followups(
        followup_gaps,
        returned_result,
        decision,
        selected_route,
        task_payload,
        returned_result["result_id"],
    )
    write_json(paths["literature_followup_path"], followups)  # type: ignore[arg-type]

    result_summary_lines = [
        "# Closed-loop result summary",
        "",
        f"- Topic slug: `{topic_slug}`",
        f"- Run id: `{run_id or '(missing)'}`",
        f"- Route id: `{selected_route['route_id']}`",
        f"- Task id: `{task_payload['task_id']}`",
        f"- Result id: `{returned_result['result_id']}`",
        f"- Status: `{manifest_status}`",
        f"- Produced by: `{manifest['produced_by']}`",
        f"- Research mode: `{manifest.get('research_mode') or '(missing)'}`",
        f"- Executor kind: `{manifest.get('executor_kind') or '(missing)'}`",
        f"- Reasoning profile: `{manifest.get('reasoning_profile') or '(missing)'}`",
        f"- Closed-loop policy: `{manifest.get('closed_loop_policy_path') or '(missing)'}`",
        f"- Fixture backed: `{str(manifest['fixture_backed']).lower()}`",
        f"- Non-scientific: `{str(manifest['non_scientific']).lower()}`",
        f"- Trajectory log: `{trajectory.get('path') or '(missing)'}`",
        f"- Failure classification: `{failure_summary.get('path') or '(missing)'}`",
        "",
        "## What was attempted",
        "",
        f"- {returned_result.get('what_was_attempted') or task_payload.get('summary') or selected_route.get('objective')}",
        "",
        "## What actually ran",
        "",
        f"- {returned_result.get('what_actually_ran') or returned_result.get('summary') or 'The external executor did not provide additional detail.'}",
        "",
        "## Key outputs",
        "",
    ]
    for artifact in existing_artifacts:
        result_summary_lines.append(f"- `{artifact}`")
    if not existing_artifacts:
        result_summary_lines.append("- `(no durable output artifacts were confirmed beyond the returned result record)`")
    metrics = returned_result.get("metrics") or {}
    if metrics:
        result_summary_lines.extend(["", "## Metrics", ""])
        for key in sorted(metrics):
            result_summary_lines.append(f"- `{key}`: `{metrics[key]}`")
    result_summary_lines.extend(["", "## Governance surfaces", ""])
    result_summary_lines.append(f"- Trajectory log note: `{trajectory.get('note_path') or '(missing)'}`")
    result_summary_lines.append(f"- Failure classification note: `{failure_summary.get('note_path') or '(missing)'}`")
    result_summary_lines.append(
        f"- Follow-up gap writeback: `{(followup_gap_writeback or {}).get('note_path') or '(none)'}`"
    )
    limitations = ensure_string_list(returned_result.get("limitations"))
    if missing_artifacts:
        limitations.append(f"Missing declared artifacts: {', '.join(missing_artifacts)}")
    if manifest["fixture_backed"]:
        limitations.append("This was a fixture-backed control-path result, not a scientific execution claim.")
    result_summary_lines.extend(["", "## Known limitations", ""])
    for limitation in unique_list(limitations) or ["No explicit limitations were provided."]:
        result_summary_lines.append(f"- {limitation}")
    non_conclusions = ensure_string_list(returned_result.get("non_conclusions"))
    if not non_conclusions:
        non_conclusions = [
            "This writeback does not by itself justify a new scientific promotion or canonical claim.",
        ]
    result_summary_lines.extend(["", "## What this does not justify", ""])
    for item in non_conclusions:
        result_summary_lines.append(f"- {item}")
    write_text(paths["result_summary_path"], "\n".join(result_summary_lines) + "\n")  # type: ignore[arg-type]

    feedback_status = read_json(paths["feedback_status_path"]) if paths["feedback_status_path"] else {}
    if feedback_status is None:
        feedback_status = {}
    feedback_status["stage"] = "closed_loop_result_ingested"
    feedback_status["candidate_status"] = CANDIDATE_STATUS_BY_DECISION.get(
        decision["decision"],
        decision["decision"],
    )
    feedback_status["last_updated"] = now_iso()
    feedback_status["last_result_id"] = returned_result["result_id"]
    feedback_status["last_closed_loop_decision_id"] = decision["decision_id"]
    feedback_status["last_result_manifest_path"] = relative_to_root(paths["result_manifest_path"], knowledge_root)
    feedback_status["last_trajectory_log_path"] = trajectory.get("path")
    feedback_status["last_failure_classification_path"] = failure_summary.get("path")
    feedback_status["last_followup_gap_writeback_path"] = (followup_gap_writeback or {}).get("path")
    feedback_status["open_followup_gap_count"] = len(followup_gaps)
    write_json(paths["feedback_status_path"], feedback_status)  # type: ignore[arg-type]

    next_actions = build_next_actions(
        manifest_relpath=relative_to_root(paths["result_manifest_path"], knowledge_root) or "(missing)",
        result_summary_relpath=relative_to_root(paths["result_summary_path"], knowledge_root) or "(missing)",
        followup_relpath=relative_to_root(paths["literature_followup_path"], knowledge_root),
        followup_gap_relpath=(followup_gap_writeback or {}).get("note_path"),
        decision=decision,
        returned_result=returned_result,
    )
    next_actions_lines = ["# Next actions", ""]
    for index, action in enumerate(next_actions, start=1):
        next_actions_lines.append(f"{index}. {action}")
    write_text(paths["feedback_next_actions_path"], "\n".join(next_actions_lines) + "\n")  # type: ignore[arg-type]

    try:
        _notebook_path = knowledge_root / "topics" / topic_slug / "L3"
        if _notebook_path.exists():
            import sys as _sys
            _hub_parent = str(knowledge_root / "knowledge_hub")
            if _hub_parent not in _sys.path:
                _sys.path.insert(0, _hub_parent)
            from knowledge_hub.research_notebook_support import append_notebook_entry as _ane
            _ane(
                _notebook_path,
                kind="closed_loop_result",
                title=f"Result: {manifest_status}",
                status=manifest_status,
                run_id=run_id or "",
                body=str(returned_result.get("what_was_attempted") or ""),
                details={
                    "result_id": returned_result["result_id"],
                    "task_id": task_payload["task_id"],
                    "decision": decision.get("decision", ""),
                    "route_id": selected_route.get("route_id", ""),
                },
            )
    except Exception:
        pass

    return {
        "manifest": manifest,
        "trajectory": trajectory,
        "failure_classification": failure_classification,
        "decision": decision,
        "followups": followups,
        "followup_gap_writeback": followup_gap_writeback,
        "followup_gaps": followup_gaps,
    }


def select_validation_route(knowledge_root: Path, topic_state: dict, updated_by: str) -> dict:
    selected_route = choose_route_candidate(knowledge_root, topic_state)
    if selected_route is None:
        raise SystemExit("No executable validation route could be selected from the current topic state.")
    selected_route["selected_by"] = updated_by
    topic_slug = topic_state["topic_slug"]
    run_id = derive_run_id(topic_state)
    paths = build_paths(knowledge_root, topic_slug, run_id)
    write_json(paths["selected_route_path"], selected_route)  # type: ignore[arg-type]
    return selected_route
