#!/usr/bin/env python3
"""Bootstrap or resume an AITP topic and materialize an executable action queue."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from closed_loop_v1 import compute_closed_loop_status
from interaction_surface_support import (
    build_agent_brief as render_agent_brief,
    build_interaction_state as materialize_interaction_state,
    build_operator_console as render_operator_console,
    derive_surface_roots as derive_interaction_surface_roots,
)
from orchestrator_contract_support import (
    append_closed_loop_actions,
    consultation_followup_ready_for_auto_run,
    derive_post_promotion_followup,
    derive_post_promotion_blocker_route_choice,
    derive_selected_candidate_promotion_gate,
    derive_selected_candidate_route_choice,
    load_consultation_followup_selection,
    load_post_promotion_blocker_route_choice,
    load_post_promotion_followup,
    load_selected_candidate_promotion_gate,
    post_promotion_formalization_followup_action,
    post_promotion_proof_repair_review_action,
    load_selected_candidate_route_choice,
    append_literature_followup_actions,
    append_runtime_helper_actions,
    compute_literature_intake_stage_signature,
    enrich_queue_meta,
    load_operator_checkpoint,
    load_runtime_contract,
    maybe_append_literature_intake_stage_action,
    maybe_append_skill_discovery_action,
    queue_rows_from_pending_actions,
    queue_shaping_policy_from_contract_artifacts,
    reorder_queue_with_runtime_contract,
    render_post_promotion_blocker_route_choice_markdown,
    render_post_promotion_followup_markdown,
    render_selected_candidate_promotion_gate_markdown,
    render_selected_candidate_route_choice_markdown,
    post_promotion_blocker_route_choice_paths,
    post_promotion_blocker_route_choice_ready_for_materialization,
    post_promotion_followup_paths,
    post_promotion_followup_ready_for_materialization,
    selected_candidate_promotion_gate_paths,
    selected_candidate_promotion_gate_ready_for_materialization,
    should_advance_past_staged_l2_review,
    selected_candidate_route_choice_paths,
    selected_candidate_route_choice_ready_for_materialization,
    topic_has_staged_entries,
)

NEXT_ACTIONS_CONTRACT_FILENAME = "next_actions.contract.json"
ACTION_QUEUE_CONTRACT_GENERATED_FILENAME = "action_queue_contract.generated.json"
ACTION_QUEUE_CONTRACT_GENERATED_NOTE_FILENAME = "action_queue_contract.generated.md"
CANDIDATE_SPLIT_CONTRACT_FILENAME = "candidate_split.contract.json"
DEFERRED_BUFFER_FILENAME = "deferred_candidates.json"
DEFERRED_BUFFER_NOTE_FILENAME = "deferred_candidates.md"
FOLLOWUP_SUBTOPICS_FILENAME = "followup_subtopics.jsonl"
FOLLOWUP_SUBTOPICS_NOTE_FILENAME = "followup_subtopics.md"
TOPIC_COMPLETION_FILENAME = "topic_completion.json"
LEAN_BRIDGE_ACTIVE_FILENAME = "lean_bridge.active.json"


def _synthesize_fallback_summary(
    topic_slug: str,
    topic_state: dict,
    knowledge_root: Path,
    fallback_kind: str,
) -> str:
    rc_path = knowledge_root / "topics" / topic_slug / "runtime" / "research_question.contract.json"
    rc = load_json(rc_path) or {}
    question = str(rc.get("question") or "").strip()
    source_index_path = knowledge_root / "topics" / topic_slug / "L0" / "source_index.jsonl"
    source_rows = read_jsonl(source_index_path) or []
    has_sources = bool(source_rows)
    has_question = bool(question)
    has_run = bool(topic_state.get("latest_run_id") or topic_state.get("resume_stage"))

    if not has_question and not has_sources and not has_run:
        return f"Initialize the research workspace for topic `{topic_slug}`."

    stop = {"the", "a", "an", "is", "are", "was", "were", "be", "to", "of", "in", "for", "on", "with", "at", "by", "from", "that", "this", "and", "or", "but", "not", "if", "it", "its", "do", "does", "did", "will", "would", "could", "should", "may", "might", "shall", "can", "have", "has", "had", "been", "being"}
    words = [w for w in question.split() if w.lower().strip(".,;:!?") not in stop] if question else [topic_slug]
    phrase = " ".join(words[:6]) if words else topic_slug

    if fallback_kind == "post_promotion":
        if has_question:
            return (
                f"Confirm the promoted reusable outcome for the bounded question on "
                f"{phrase} before opening another bounded route."
            )
        return "Confirm the promoted Layer 2 outcome before opening another bounded route."

    if fallback_kind == "l1_vault":
        if has_question:
            return (
                f"Review the L2 staging manifest and compiled source basis for the bounded question on "
                f"{phrase} before continuing interpretation."
            )
        return "Review the L2 staging manifest and compiled source basis before continuing."

    if has_question and has_sources:
        return (
            f"Recover the source basis interpretation for the bounded question on "
            f"{phrase} before continuing execution."
        )
    if has_question:
        return f"Bootstrap the research workflow for the bounded question on {phrase} before continuing."
    if has_sources:
        return f"Register the source basis for `{topic_slug}` and formulate the bounded research question."
    return f"Resume the research workflow for `{topic_slug}`."


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "aitp-topic"


def write_json(path: Path, payload: dict) -> None:
    rendered = json.dumps(payload, ensure_ascii=True, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    compatibility_path = compatibility_projection_path(path)
    if compatibility_path is not None and compatibility_path != path:
        compatibility_path.parent.mkdir(parents=True, exist_ok=True)
        compatibility_path.write_text(rendered, encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    rendered = "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows)
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
    return None


def load_json(path: Path) -> dict | None:
    target = path
    if not target.exists():
        compatibility_path = compatibility_projection_path(path)
        if compatibility_path is None or not compatibility_path.exists():
            return None
        target = compatibility_path
    return json.loads(target.read_text(encoding="utf-8"))


def python_command() -> list[str]:
    executable = str(getattr(sys, "executable", "") or "").strip()
    if executable:
        return [executable]

    for candidate in ("python3", "python"):
        resolved = shutil.which(candidate)
        if resolved:
            return [resolved]

    launcher = shutil.which("py")
    if launcher:
        return [launcher, "-3"]

    return ["python"]


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


def as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def relative_path(path: Path | None, root: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def ensure_topic_shell(knowledge_root: Path, topic_slug: str, statement: str | None, topic_title: str | None = None) -> None:
    created_at = now_iso()
    title = str(topic_title or "").strip() or topic_slug.replace("-", " ").title()

    layer0_topic = knowledge_root / "topics" / topic_slug / "L0" / "topic.json"
    if not layer0_topic.exists():
        write_json(
            layer0_topic,
            {
                "topic_slug": topic_slug,
                "title": title,
                "status": "source_active",
                "created_at": created_at,
            },
        )

    intake_topic = knowledge_root / "topics" / topic_slug / "L1" / "topic.json"
    if not intake_topic.exists():
        write_json(
            intake_topic,
            {
                "topic_slug": topic_slug,
                "title": title,
                "status": "intake_active",
                "created_at": created_at,
            },
        )

    intake_status = knowledge_root / "topics" / topic_slug / "L1" / "status.json"
    if not intake_status.exists():
        write_json(
            intake_status,
            {"stage": "L1_active", "next_stage": "L1", "last_updated": created_at},
        )

    if statement:
        latest_run_root = knowledge_root / "topics" / topic_slug / "L3" / "runs"
        run_id = datetime.now().astimezone().strftime("%Y-%m-%d-%H%M%S-bootstrap")
        run_root = latest_run_root / run_id
        if not run_root.exists():
            write_json(
                run_root / "topic.json",
                {
                    "topic_slug": topic_slug,
                    "run_id": run_id,
                    "question": statement,
                    "created_at": created_at,
                },
            )
            write_json(
                run_root / "status.json",
                {"stage": "candidate_shaping", "last_updated": created_at},
            )
            write_text(
                run_root / "next_actions.md",
                "# Next actions\n\n1. Start with source-layer/scripts/discover_and_register.py when you have a topic query; if you already know the arXiv id, use source-layer/scripts/register_arxiv_source.py and intake/ARXIV_FIRST_SOURCE_INTAKE.md.\n",
            )


def _load_recorded_action_classification(
    classification_contract_path: Path | str | None,
) -> str | None:
    if not classification_contract_path:
        return None
    path = Path(classification_contract_path)
    if not path.exists():
        return None
    rows: list[dict] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    action_rows = [r for r in rows if r.get("classification_type") == "action_type"]
    if action_rows:
        return action_rows[-1].get("value")
    return None


def classify_action(
    summary: str,
    *,
    pre_classified_type: str | None = None,
    classification_contract_path: str | None = None,
) -> tuple[str, bool]:
    if pre_classified_type:
        auto_types = {
            "apply_candidate_split_contract",
            "reactivate_deferred_candidate",
            "spawn_followup_subtopics",
            "assess_topic_completion",
            "prepare_lean_bridge",
            "auto_promote_candidate",
        }
        return pre_classified_type, pre_classified_type in auto_types

    recorded = _load_recorded_action_classification(classification_contract_path)
    if recorded:
        auto_types = {
            "apply_candidate_split_contract",
            "reactivate_deferred_candidate",
            "spawn_followup_subtopics",
            "assess_topic_completion",
            "prepare_lean_bridge",
            "auto_promote_candidate",
        }
        return recorded, recorded in auto_types

    lowered = summary.lower()
    if "baseline" in lowered or "reproduc" in lowered:
        return "baseline_reproduction", False
    if "atomic" in lowered or "dependency graph" in lowered or "decompos" in lowered:
        return "atomic_understanding", False
    if "split contract" in lowered or "split candidate" in lowered:
        return "apply_candidate_split_contract", True
    if "reactivate deferred" in lowered or "reactivate parked" in lowered:
        return "reactivate_deferred_candidate", True
    if "follow-up subtopic" in lowered or "followup subtopic" in lowered:
        return "spawn_followup_subtopics", True
    if "topic-completion" in lowered or "topic completion" in lowered:
        return "assess_topic_completion", True
    if "lean bridge" in lowered or "formalization ready" in lowered or "lean-ready" in lowered:
        return "prepare_lean_bridge", True
    if "auto-promote" in lowered or "l2_auto" in lowered:
        return "auto_promote_candidate", True
    if "conformance" in lowered:
        return "conformance_audit", False
    if "skill" in lowered or "tooling" in lowered or "workflow" in lowered:
        return "skill_discovery", False
    if "layer 0 callback" in lowered or "reference" in lowered or "source" in lowered:
        return "l0_source_expansion", False
    if (
        "numerical backend" in lowered
        or "backend" in lowered
        or "resolve parity" in lowered
        or "translation sectors" in lowered
    ):
        return "backend_extension", False
    if lowered.startswith("re-run") or "re-run" in lowered or "rerun" in lowered:
        return "l4_revalidation", False
    if "claim_card" in lowered or "method" in lowered or "layer 2" in lowered:
        return "l2_promotion_review", False
    return "manual_followup", False


def completed_literature_followups(knowledge_root: Path, topic_slug: str, run_id: str | None) -> set[tuple[str, str]]:
    if not run_id:
        return set()
    receipts_path = (
        knowledge_root / "topics" / topic_slug / "L4" / "runs" / run_id / "literature_followup_receipts.jsonl"
    )
    completed: set[tuple[str, str]] = set()
    for row in read_jsonl(receipts_path):
        query = str(row.get("query") or "").strip()
        target_source_type = str(row.get("target_source_type") or "paper").strip() or "paper"
        if not query:
            continue
        if row.get("status") in {"completed", "no_matches"}:
            completed.add((query, target_source_type))
    return completed


def followup_max_results(priority: str) -> int:
    if priority == "high":
        return 3
    if priority == "low":
        return 1
    return 2


def load_runtime_policy(knowledge_root: Path) -> dict:
    return load_json(knowledge_root / "runtime" / "closed_loop_policies.json") or {}


def fingerprint_payload(payload: dict) -> str:
    serialized = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(serialized.encode("utf-8")).hexdigest()


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


def pending_split_contract_action(knowledge_root: Path, topic_state: dict, queue_meta: dict) -> list[dict]:
    policy = (load_runtime_policy(knowledge_root).get("candidate_split_policy") or {})
    if not policy.get("enabled") or not policy.get("auto_apply_contracts", True):
        return []
    run_id = str(topic_state.get("latest_run_id") or "").strip()
    if not run_id:
        return []
    contract_path = (
        knowledge_root
        / "feedback"
        / "topics"
        / topic_state["topic_slug"]
        / "runs"
        / run_id
        / str(policy.get("contract_filename") or CANDIDATE_SPLIT_CONTRACT_FILENAME)
    )
    contract_payload = load_json(contract_path)
    if contract_payload is None:
        return []
    receipts_path = (
        knowledge_root
        / "feedback"
        / "topics"
        / topic_state["topic_slug"]
        / "runs"
        / run_id
        / str(policy.get("receipt_filename") or "candidate_split_receipts.jsonl")
    )
    receipt_rows = read_jsonl(receipts_path)
    pending_sources: list[str] = []
    for split_payload in contract_payload.get("splits") or []:
        source_candidate_id = str(split_payload.get("source_candidate_id") or "").strip()
        if not source_candidate_id:
            continue
        fingerprint = fingerprint_payload(split_payload)
        already_applied = any(
            str(row.get("source_candidate_id") or "") == source_candidate_id
            and str(row.get("fingerprint") or "") == fingerprint
            for row in receipt_rows
        )
        if not already_applied:
            pending_sources.append(source_candidate_id)
    if not pending_sources:
        return []
    return [
        {
            "action_id": f"action:{topic_state['topic_slug']}:apply-split-contract",
            "topic_slug": topic_state["topic_slug"],
            "resume_stage": "L3",
            "status": "pending",
            "action_type": "apply_candidate_split_contract",
            "summary": (
                "Apply the declared candidate split contract so wide or mixed candidates are decomposed "
                "and unresolved fragments move into the deferred buffer."
            ),
            "auto_runnable": True,
            "handler": None,
            "handler_args": {"run_id": run_id},
            "queue_source": "runtime_appended",
            "declared_contract_path": queue_meta.get("declared_contract_path"),
        }
    ]


def auto_promotion_actions(knowledge_root: Path, topic_state: dict, queue_meta: dict) -> list[dict]:
    policy = (load_runtime_policy(knowledge_root).get("auto_promotion_policy") or {})
    if not policy.get("enabled"):
        return []
    run_id = str(topic_state.get("latest_run_id") or "").strip()
    if not run_id:
        return []
    candidate_rows = read_jsonl(
        knowledge_root / "topics" / topic_state["topic_slug"] / "L3" / "runs" / run_id / "candidate_ledger.jsonl"
    )
    allowed_statuses = {
        str(value).strip()
        for value in (policy.get("trigger_candidate_statuses") or [])
        if str(value).strip()
    }
    allowed_types = {
        str(value).strip()
        for value in (policy.get("theory_formal_candidate_types") or [])
        if str(value).strip()
    }
    promotion_gate = load_json(knowledge_root / "topics" / topic_state["topic_slug"] / "runtime" / "promotion_gate.json") or {}
    actions: list[dict] = []
    for row in candidate_rows:
        candidate_id = str(row.get("candidate_id") or "").strip()
        candidate_type = str(row.get("candidate_type") or "").strip()
        status = str(row.get("status") or "").strip()
        if not candidate_id or not candidate_type:
            continue
        if allowed_statuses and status not in allowed_statuses:
            continue
        if allowed_types and candidate_type not in allowed_types:
            continue
        if status in {"promoted", "auto_promoted", "split_into_children", "deferred_buffered"}:
            continue
        if (
            str(promotion_gate.get("candidate_id") or "") == candidate_id
            and str(promotion_gate.get("status") or "") in {"approved", "promoted"}
        ):
            continue
        packet_root = (
            knowledge_root
            / "topics"
            / topic_state["topic_slug"]
            / "L4"
            / "runs"
            / run_id
            / "theory-packets"
            / slugify(candidate_id)
        )
        coverage_payload = load_json(packet_root / "coverage_ledger.json") or {}
        consensus_payload = load_json(packet_root / "agent_consensus.json") or {}
        regression_payload = load_json(packet_root / "regression_gate.json") or {}
        if str(coverage_payload.get("status") or "") != "pass":
            continue
        if str(consensus_payload.get("status") or "") != "ready":
            continue
        if policy.get("require_regression_gate_pass", True) and str(regression_payload.get("status") or "") != "pass":
            continue
        if policy.get("block_when_split_required", True) and (
            as_bool(row.get("split_required")) or as_bool(regression_payload.get("split_required"))
        ):
            continue
        if policy.get("block_when_promotion_blockers_present", True) and (
            list(row.get("promotion_blockers") or []) or list(regression_payload.get("promotion_blockers") or [])
        ):
            continue
        if policy.get("block_when_cited_recovery_required", True) and (
            as_bool(row.get("cited_recovery_required")) or as_bool(regression_payload.get("cited_recovery_required"))
        ):
            continue
        actions.append(
            {
                "action_id": f"action:{topic_state['topic_slug']}:auto-promote:{slugify(candidate_id)}",
                "topic_slug": topic_state["topic_slug"],
                "resume_stage": "L4",
                "status": "pending",
                "action_type": "auto_promote_candidate",
                "summary": (
                    f"Auto-promote theory-formal candidate `{candidate_id}` into `L2_auto` "
                    "after its coverage and consensus gates have passed."
                ),
                "auto_runnable": True,
                "handler": None,
                "handler_args": {
                    "run_id": run_id,
                    "candidate_id": candidate_id,
                    "backend_id": str(policy.get("default_backend_id") or ""),
                },
                "queue_source": "runtime_appended",
                "declared_contract_path": queue_meta.get("declared_contract_path"),
            }
        )
    return actions


def followup_subtopic_actions(knowledge_root: Path, topic_state: dict, queue_meta: dict) -> list[dict]:
    policy = (load_runtime_policy(knowledge_root).get("followup_subtopic_policy") or {})
    if not policy.get("enabled"):
        return []
    run_id = str(topic_state.get("latest_run_id") or "").strip()
    if not run_id:
        return []
    receipts_path = (
        knowledge_root / "topics" / topic_state["topic_slug"] / "L4" / "runs" / run_id / "literature_followup_receipts.jsonl"
    )
    existing_rows = read_jsonl(knowledge_root / "topics" / topic_state["topic_slug"] / "runtime" / FOLLOWUP_SUBTOPICS_FILENAME)
    existing_keys = {
        (str(row.get("query") or ""), str(row.get("arxiv_id") or ""))
        for row in existing_rows
    }
    allowed_source_types = {
        str(value).strip()
        for value in (policy.get("spawn_target_source_types") or [])
        if str(value).strip()
    }
    bounded_gap_required = bool(policy.get("bounded_gap_required"))
    max_subtopics = int(policy.get("max_subtopics_per_receipt") or 2)
    actions: list[dict] = []
    for receipt in read_jsonl(receipts_path):
        target_source_type = str(receipt.get("target_source_type") or "paper").strip() or "paper"
        if allowed_source_types and target_source_type not in allowed_source_types:
            continue
        if str(receipt.get("status") or "") != "completed":
            continue
        if bounded_gap_required and not (
            list(receipt.get("parent_gap_ids") or [])
            or list(receipt.get("parent_followup_task_ids") or [])
            or str(receipt.get("parent_followup_task_id") or "").strip()
            or list(receipt.get("reentry_targets") or [])
            or list(receipt.get("supporting_regression_question_ids") or [])
        ):
            continue
        match_count = 0
        for match in list(receipt.get("matches") or [])[:max_subtopics]:
            arxiv_id = str(match.get("arxiv_id") or "").strip()
            if not arxiv_id:
                continue
            if (str(receipt.get("query") or ""), arxiv_id) in existing_keys:
                continue
            match_count += 1
        if match_count == 0:
            continue
        actions.append(
            {
                "action_id": f"action:{topic_state['topic_slug']}:spawn-followup:{slugify(str(receipt.get('query') or 'followup'))}",
                "topic_slug": topic_state["topic_slug"],
                "resume_stage": "L0",
                "status": "pending",
                "action_type": "spawn_followup_subtopics",
                "summary": (
                    f"Spawn independent follow-up subtopics for `{receipt.get('query') or '(missing)'}` "
                    "so cited-literature gaps re-enter AITP through fresh L0/L1 topic shells."
                ),
                "auto_runnable": True,
                "handler": None,
                "handler_args": {
                    "run_id": run_id,
                    "query": str(receipt.get("query") or ""),
                    "receipt_id": str(receipt.get("receipt_id") or ""),
                },
                "queue_source": "runtime_appended",
                "declared_contract_path": queue_meta.get("declared_contract_path"),
            }
        )
    return actions


def followup_reintegration_actions(knowledge_root: Path, topic_state: dict, queue_meta: dict) -> list[dict]:
    policy = (load_runtime_policy(knowledge_root).get("followup_subtopic_policy") or {})
    if not policy.get("enabled"):
        return []
    run_id = str(topic_state.get("latest_run_id") or "").strip()
    if not run_id:
        return []
    unresolved_statuses = {
        str(value).strip()
        for value in (policy.get("unresolved_return_statuses") or [])
        if str(value).strip()
    }
    actions: list[dict] = []
    for row in read_jsonl(knowledge_root / "topics" / topic_state["topic_slug"] / "runtime" / FOLLOWUP_SUBTOPICS_FILENAME):
        child_topic_slug = str(row.get("child_topic_slug") or "").strip()
        if not child_topic_slug:
            continue
        if str(row.get("status") or "").strip() == "reintegrated":
            continue
        return_packet_path = str(row.get("return_packet_path") or "").strip()
        if not return_packet_path:
            continue
        packet_path = Path(return_packet_path).expanduser()
        if not packet_path.is_absolute():
            packet_path = knowledge_root / packet_path
        return_packet = load_json(packet_path)
        if return_packet is None:
            continue
        return_status = str(return_packet.get("return_status") or "").strip()
        if not return_status or return_status == "pending_reentry":
            continue
        summary_suffix = (
            "with unresolved gap writeback"
            if return_status in unresolved_statuses and return_status != "pending_reentry"
            else "and refresh the parent completion state"
        )
        actions.append(
            {
                "action_id": f"action:{topic_state['topic_slug']}:reintegrate-followup:{slugify(child_topic_slug)}",
                "topic_slug": topic_state["topic_slug"],
                "resume_stage": "L3",
                "status": "pending",
                "action_type": "reintegrate_followup_subtopic",
                "summary": (
                    f"Reintegrate returned child follow-up topic `{child_topic_slug}` back into the parent topic "
                    f"{summary_suffix}."
                ),
                "auto_runnable": True,
                "handler": None,
                "handler_args": {
                    "run_id": run_id,
                    "child_topic_slug": child_topic_slug,
                },
                "queue_source": "runtime_appended",
                "declared_contract_path": queue_meta.get("declared_contract_path"),
            }
        )
    return actions


def topic_completion_actions(knowledge_root: Path, topic_state: dict, queue_meta: dict) -> list[dict]:
    policy = (load_runtime_policy(knowledge_root).get("topic_completion_policy") or {})
    if policy.get("enabled") is False:
        return []
    run_id = str(topic_state.get("latest_run_id") or "").strip()
    if not run_id:
        return []
    topic_slug = topic_state["topic_slug"]
    candidate_rows = read_jsonl(
        knowledge_root / "topics" / topic_slug / "L3" / "runs" / run_id / "candidate_ledger.jsonl"
    )
    followup_rows = read_jsonl(knowledge_root / "topics" / topic_slug / "runtime" / FOLLOWUP_SUBTOPICS_FILENAME)
    promotion_gate = load_json(knowledge_root / "topics" / topic_slug / "runtime" / "promotion_gate.json") or {}
    gate_status = str(promotion_gate.get("status") or "").strip()
    if not candidate_rows and not followup_rows and gate_status != "promoted":
        return []
    completion_payload = load_json(knowledge_root / "topics" / topic_slug / "runtime" / TOPIC_COMPLETION_FILENAME) or {}
    candidate_count_value = completion_payload.get("candidate_count")
    followup_count_value = completion_payload.get("followup_subtopic_count")
    candidate_count_matches = (
        candidate_count_value is not None and int(candidate_count_value) == len(candidate_rows)
    )
    followup_count_matches = (
        followup_count_value is not None and int(followup_count_value) == len(followup_rows)
    )
    needs_refresh = (
        str(completion_payload.get("run_id") or "") != run_id
        or not candidate_count_matches
        or not followup_count_matches
        or (gate_status == "promoted" and str(completion_payload.get("status") or "") != "promoted")
    )
    if not needs_refresh:
        return []
    return [
        {
            "action_id": f"action:{topic_slug}:topic-completion",
            "topic_slug": topic_slug,
            "resume_stage": "L4",
            "status": "pending",
            "action_type": "assess_topic_completion",
            "summary": "Refresh the topic-completion gate over regression support, blocker clearance, and child follow-up debt.",
            "auto_runnable": True,
            "handler": None,
            "handler_args": {"run_id": run_id},
            "queue_source": "runtime_appended",
            "declared_contract_path": queue_meta.get("declared_contract_path"),
        }
    ]


def prune_obsolete_actions(knowledge_root: Path, topic_state: dict, queue: list[dict]) -> list[dict]:
    topic_slug = topic_state["topic_slug"]
    runtime_root = knowledge_root / "topics" / topic_slug / "runtime"
    promotion_gate = load_json(runtime_root / "promotion_gate.json") or {}
    gate_status = str(promotion_gate.get("status") or "").strip()
    completion_payload = load_json(runtime_root / TOPIC_COMPLETION_FILENAME) or {}
    completion_status = str(completion_payload.get("status") or "").strip()
    latest_run_id = str(topic_state.get("latest_run_id") or "").strip()
    source_count = int(topic_state.get("source_count") or 0)

    filtered: list[dict] = []
    for row in queue:
        action_type = str(row.get("action_type") or "").strip()
        action_summary = str(row.get("summary") or "").strip().lower()
        queue_source = str(row.get("queue_source") or "").strip()
        handler_args = row.get("handler_args") or {}
        action_run_id = str(handler_args.get("run_id") or "").strip()

        if (
            source_count > 0
            and action_type == "l0_source_expansion"
            and "discover_and_register.py" in action_summary
            and "register_arxiv_source.py" in action_summary
        ):
            continue

        if gate_status == "promoted":
            if action_type == "auto_promote_candidate":
                continue
            if action_type in {
                "l2_promotion_review",
                "request_promotion",
                "approve_promotion",
                "promote_candidate",
            }:
                continue
            if action_type == "assess_topic_completion" and queue_source == "heuristic" and not handler_args:
                continue
            if (
                completion_status == "promoted"
                and action_type == "assess_topic_completion"
                and action_run_id
                and action_run_id == latest_run_id
            ):
                continue

        filtered.append(row)
    return filtered


def lean_bridge_actions(knowledge_root: Path, topic_state: dict, queue_meta: dict) -> list[dict]:
    policy = (load_runtime_policy(knowledge_root).get("lean_bridge_policy") or {})
    if policy.get("enabled") is False:
        return []
    run_id = str(topic_state.get("latest_run_id") or "").strip()
    if not run_id:
        return []
    topic_slug = topic_state["topic_slug"]
    allowed_types = {
        str(value).strip()
        for value in (policy.get("trigger_candidate_types") or [])
        if str(value).strip()
    }
    candidate_rows = read_jsonl(
        knowledge_root / "topics" / topic_slug / "L3" / "runs" / run_id / "candidate_ledger.jsonl"
    )
    target_candidates = []
    for row in candidate_rows:
        candidate_id = str(row.get("candidate_id") or "").strip()
        candidate_type = str(row.get("candidate_type") or "").strip()
        if not candidate_id:
            continue
        if allowed_types and candidate_type not in allowed_types:
            continue
        target_candidates.append(candidate_id)
    if not target_candidates:
        return []
    active_payload = load_json(knowledge_root / "topics" / topic_slug / "runtime" / LEAN_BRIDGE_ACTIVE_FILENAME) or {}
    packet_candidate_ids = {
        str(row.get("candidate_id") or "").strip()
        for row in (active_payload.get("packets") or [])
        if str(row.get("candidate_id") or "").strip()
    }
    needs_refresh = (
        str(active_payload.get("run_id") or "") != run_id
        or not set(target_candidates).issubset(packet_candidate_ids)
    )
    if not needs_refresh:
        return []
    return [
        {
            "action_id": f"action:{topic_slug}:lean-bridge",
            "topic_slug": topic_slug,
            "resume_stage": "L4",
            "status": "pending",
            "action_type": "prepare_lean_bridge",
            "summary": "Refresh Lean bridge packets and proof-state sidecars for the active bounded formal candidates.",
            "auto_runnable": True,
            "handler": None,
            "handler_args": {"run_id": run_id},
            "queue_source": "runtime_appended",
            "declared_contract_path": queue_meta.get("declared_contract_path"),
        }
    ]


def deferred_reactivation_actions(knowledge_root: Path, topic_state: dict, queue_meta: dict) -> list[dict]:
    policy = (load_runtime_policy(knowledge_root).get("deferred_buffer_policy") or {})
    if not policy.get("enabled") or not policy.get("auto_reactivate", True):
        return []
    run_id = str(topic_state.get("latest_run_id") or "").strip()
    if not run_id:
        return []
    deferred_buffer = load_json(
        knowledge_root / "topics" / topic_state["topic_slug"] / "runtime" / DEFERRED_BUFFER_FILENAME
    ) or {}
    source_rows = read_jsonl(knowledge_root / "topics" / topic_state["topic_slug"] / "L0" / "source_index.jsonl")
    source_ids = {
        str(row.get("source_id") or "").strip()
        for row in source_rows
        if str(row.get("source_id") or "").strip()
    }
    source_text = " ".join(
        [
            str(row.get("title") or "")
            for row in source_rows
        ]
        + [
            str(row.get("summary") or "")
            for row in source_rows
        ]
    ).lower()
    child_topics = {
        str(row.get("child_topic_slug") or "").strip()
        for row in read_jsonl(knowledge_root / "topics" / topic_state["topic_slug"] / "runtime" / FOLLOWUP_SUBTOPICS_FILENAME)
        if str(row.get("child_topic_slug") or "").strip()
    }
    actions: list[dict] = []
    for entry in deferred_buffer.get("entries") or []:
        entry_id = str(entry.get("entry_id") or "").strip()
        if not entry_id or str(entry.get("status") or "") != "buffered":
            continue
        if not (entry.get("reactivation_candidate") or {}):
            continue
        if not buffer_entry_ready_for_reactivation(entry, source_ids, source_text, child_topics):
            continue
        actions.append(
            {
                "action_id": f"action:{topic_state['topic_slug']}:reactivate:{slugify(entry_id)}",
                "topic_slug": topic_state["topic_slug"],
                "resume_stage": "L3",
                "status": "pending",
                "action_type": "reactivate_deferred_candidate",
                "summary": (
                    f"Reactivate deferred entry `{entry_id}` because its declared source or subtopic triggers are now satisfied."
                ),
                "auto_runnable": True,
                "handler": None,
                "handler_args": {"run_id": run_id, "entry_id": entry_id},
                "queue_source": "runtime_appended",
                "declared_contract_path": queue_meta.get("declared_contract_path"),
            }
        )
    return actions


def load_declared_action_contract(topic_state: dict, knowledge_root: Path) -> dict | None:
    next_actions_rel = str(((topic_state.get("pointers") or {}).get("next_actions_path") or "")).strip()
    if not next_actions_rel:
        return None
    next_actions_path = knowledge_root / next_actions_rel
    contract_path = next_actions_path.parent / NEXT_ACTIONS_CONTRACT_FILENAME
    payload = load_json(contract_path)
    if payload is None:
        return None
    return {
        "path": contract_path,
        "relpath": relative_path(contract_path, knowledge_root),
        "payload": payload,
    }


def declared_actions_from_contract(
    topic_state: dict,
    declared_contract: dict | None,
    knowledge_root: Path | None = None,
) -> tuple[list[dict], dict]:
    if declared_contract is None:
        return [], {
            "queue_source": "heuristic",
            "declared_contract_path": None,
            "declared_contract_used": False,
            "declared_contract_valid": False,
        }

    payload = declared_contract["payload"]
    rows = payload.get("actions")
    if not isinstance(rows, list):
        return [], {
            "queue_source": "heuristic",
            "declared_contract_path": declared_contract["relpath"],
            "declared_contract_used": False,
            "declared_contract_valid": False,
            "fallback_reason": "Declared action contract is missing an `actions` list.",
        }

    queue: list[dict] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        if row.get("enabled") is False:
            continue
        summary = str(row.get("summary") or "").strip()
        if not summary:
            continue
        action_type = str(row.get("action_type") or "").strip()
        derived_action_type, derived_auto_runnable = classify_action(
            summary,
            classification_contract_path=str(
                knowledge_root / "topics" / topic_state["topic_slug"] / "runtime" / "classification_contract.jsonl"
            ) if knowledge_root else None,
        )
        if not action_type:
            action_type = derived_action_type
        auto_runnable = row.get("auto_runnable")
        if auto_runnable is None:
            auto_runnable = derived_auto_runnable
        handler = row.get("handler")
        handler_args = row.get("handler_args")
        queue.append(
            {
                "action_id": str(row.get("action_id") or f"action:{topic_state['topic_slug']}:{index:02d}"),
                "topic_slug": topic_state["topic_slug"],
                "resume_stage": str(row.get("resume_stage") or topic_state["resume_stage"]),
                "status": "pending",
                "action_type": action_type,
                "summary": summary,
                "auto_runnable": bool(auto_runnable),
                "handler": str(handler) if handler else None,
                "handler_args": handler_args if isinstance(handler_args, dict) else {},
                "queue_source": "declared_contract",
                "declared_contract_path": declared_contract["relpath"],
            }
        )

    return queue, {
        "queue_source": "declared_contract" if queue else "heuristic",
        "declared_contract_path": declared_contract["relpath"],
        "declared_contract_used": bool(queue),
        "declared_contract_valid": bool(queue),
        "append_runtime_actions": bool(payload.get("append_runtime_actions", True)),
        "append_skill_action_if_needed": bool(payload.get("append_skill_action_if_needed", True)),
        "policy_note": str(payload.get("policy_note") or "").strip() or None,
    }


def build_action_queue_contract_snapshot(
    topic_state: dict,
    queue: list[dict],
    queue_meta: dict,
    knowledge_root: Path,
) -> dict:
    return {
        "contract_version": 1,
        "topic_slug": topic_state["topic_slug"],
        "run_id": topic_state.get("latest_run_id"),
        "updated_at": now_iso(),
        "updated_by": topic_state.get("updated_by", "codex"),
        "queue_source": queue_meta.get("queue_source") or "heuristic",
        "declared_contract_path": queue_meta.get("declared_contract_path"),
        "declared_contract_used": bool(queue_meta.get("declared_contract_used")),
        "declared_contract_valid": bool(queue_meta.get("declared_contract_valid")),
        "runtime_contract_path": queue_meta.get("runtime_contract_path"),
        "operator_checkpoint_path": queue_meta.get("operator_checkpoint_path"),
        "append_policy_reason": queue_meta.get("append_policy_reason"),
        "policy_note": queue_meta.get("policy_note"),
        "actions": [
            {
                "action_id": row.get("action_id"),
                "resume_stage": row.get("resume_stage"),
                "action_type": row.get("action_type"),
                "summary": row.get("summary"),
                "auto_runnable": bool(row.get("auto_runnable")),
                "handler": row.get("handler"),
                "handler_args": row.get("handler_args") or {},
                "queue_source": row.get("queue_source") or queue_meta.get("queue_source") or "heuristic",
                "declared_contract_path": row.get("declared_contract_path"),
            }
            for row in queue
        ],
        "authoring_hint": (
            "To override heuristic queue synthesis, write a durable `next_actions.contract.json` "
            "next to the current `next_actions.md` and keep the human explanation in markdown."
        ),
    }


def build_action_queue_contract_markdown(payload: dict) -> str:
    lines = [
        "# Action queue contract snapshot",
        "",
        f"- Topic slug: `{payload['topic_slug']}`",
        f"- Run id: `{payload.get('run_id') or '(none)'}`",
        f"- Updated at: `{payload['updated_at']}`",
        f"- Updated by: `{payload['updated_by']}`",
        f"- Queue source: `{payload.get('queue_source') or 'heuristic'}`",
        f"- Declared contract path: `{payload.get('declared_contract_path') or '(missing)'}`",
        f"- Declared contract used: `{str(bool(payload.get('declared_contract_used'))).lower()}`",
        f"- Runtime contract path: `{payload.get('runtime_contract_path') or '(missing)'}`",
        f"- Operator checkpoint path: `{payload.get('operator_checkpoint_path') or '(missing)'}`",
        f"- Append policy reason: {payload.get('append_policy_reason') or '(default policy)' }",
        "",
        "## Actions",
        "",
    ]
    for index, row in enumerate(payload.get("actions") or [], start=1):
        lines.append(
            f"{index}. [{row['action_type']}] {row['summary']} "
            f"(auto_runnable={str(bool(row['auto_runnable'])).lower()}, handler={row.get('handler') or '(manual)'})"
        )
    if not (payload.get("actions") or []):
        lines.append("- No actions were materialized.")
    lines.extend(
        [
            "",
            "## Authoring hint",
            "",
            f"- {payload['authoring_hint']}",
        ]
    )
    return "\n".join(lines) + "\n"


def materialize_action_queue(
    topic_state: dict,
    skill_queries: list[str],
    skill_discovery_script: Path,
    advance_closed_loop_script: Path,
    execution_handoff_script: Path,
    literature_followup_script: Path,
    knowledge_root: Path,
) -> tuple[list[dict], dict]:
    runtime_contract = load_runtime_contract(
        load_json=load_json,
        knowledge_root=knowledge_root,
        topic_slug=topic_state["topic_slug"],
    )
    operator_checkpoint = load_operator_checkpoint(
        load_json=load_json,
        knowledge_root=knowledge_root,
        topic_slug=topic_state["topic_slug"],
    )
    queue_shaping_policy, append_policy_reason = queue_shaping_policy_from_contract_artifacts(
        runtime_contract,
        operator_checkpoint,
    )
    declared_contract = load_declared_action_contract(topic_state, knowledge_root)
    queue, queue_meta = declared_actions_from_contract(topic_state, declared_contract, knowledge_root=knowledge_root)
    queue_meta = enrich_queue_meta(
        queue_meta,
        topic_slug=topic_state["topic_slug"],
        runtime_contract=runtime_contract,
        operator_checkpoint=operator_checkpoint,
        append_policy_reason=append_policy_reason,
    )
    allow_runtime_appends = bool(queue_meta.get("append_runtime_actions", True)) and queue_shaping_policy["allow_runtime_append"]
    if not queue:
        queue = queue_rows_from_pending_actions(
            topic_state,
            declared_contract_path=queue_meta.get("declared_contract_path"),
            classify_action=classify_action,
        )

    if allow_runtime_appends:
        queue.extend(pending_split_contract_action(knowledge_root, topic_state, queue_meta))

    maybe_append_skill_discovery_action(
        queue,
        topic_state=topic_state,
        skill_queries=skill_queries,
        skill_discovery_script=skill_discovery_script,
        queue_meta=queue_meta,
        queue_shaping_policy=queue_shaping_policy,
    )
    maybe_append_literature_intake_stage_action(
        queue,
        topic_state=topic_state,
        runtime_contract=runtime_contract,
        knowledge_root=knowledge_root,
        queue_meta=queue_meta,
        queue_shaping_policy=queue_shaping_policy,
    )

    closed_loop = compute_closed_loop_status(
        knowledge_root,
        topic_state["topic_slug"],
        topic_state.get("latest_run_id"),
        queue_rows=queue,
    )
    append_closed_loop_actions(
        queue,
        topic_state=topic_state,
        queue_meta=queue_meta,
        allow_runtime_appends=allow_runtime_appends,
        queue_shaping_policy=queue_shaping_policy,
        closed_loop=closed_loop,
        advance_closed_loop_script=advance_closed_loop_script,
        execution_handoff_script=execution_handoff_script,
    )
    completed_followups: set[tuple[str, str]] = set()
    if allow_runtime_appends and queue_shaping_policy["allow_literature_followup_append"]:
        completed_followups = completed_literature_followups(
            knowledge_root,
            topic_state["topic_slug"],
            topic_state.get("latest_run_id"),
        )
    append_literature_followup_actions(
        queue,
        topic_state=topic_state,
        queue_meta=queue_meta,
        allow_runtime_appends=allow_runtime_appends,
        queue_shaping_policy=queue_shaping_policy,
        closed_loop=closed_loop,
        completed_followups=completed_followups,
        literature_followup_script=literature_followup_script,
        followup_max_results=followup_max_results,
    )

    if allow_runtime_appends:
        append_runtime_helper_actions(
            queue,
            allow_runtime_appends=allow_runtime_appends,
            helper_action_groups=[
                followup_subtopic_actions(knowledge_root, topic_state, queue_meta),
                followup_reintegration_actions(knowledge_root, topic_state, queue_meta),
                topic_completion_actions(knowledge_root, topic_state, queue_meta),
                lean_bridge_actions(knowledge_root, topic_state, queue_meta),
                deferred_reactivation_actions(knowledge_root, topic_state, queue_meta),
                auto_promotion_actions(knowledge_root, topic_state, queue_meta),
            ],
        )
    queue = prune_obsolete_actions(knowledge_root, topic_state, queue)
    queue = reorder_queue_with_runtime_contract(
        queue,
        runtime_contract,
        declared_contract_used=bool(queue_meta.get("declared_contract_used")),
    )

    if not queue and int(topic_state.get("source_count") or 0) > 0:
        selection_payload = load_consultation_followup_selection(
            load_json=load_json,
            knowledge_root=knowledge_root,
            topic_slug=str(topic_state.get("topic_slug") or "").strip(),
        )
        if (
            isinstance(selection_payload, dict)
            and str(selection_payload.get("status") or "").strip() == "selected"
        ):
            route_choice_payload = load_selected_candidate_route_choice(
                load_json=load_json,
                knowledge_root=knowledge_root,
                topic_slug=str(topic_state.get("topic_slug") or "").strip(),
            )
            if route_choice_payload is None and selected_candidate_route_choice_ready_for_materialization(
                load_json=load_json,
                knowledge_root=knowledge_root,
                topic_slug=str(topic_state.get("topic_slug") or "").strip(),
            ):
                route_choice_payload = derive_selected_candidate_route_choice(
                    load_json=load_json,
                    knowledge_root=knowledge_root,
                    topic_slug=str(topic_state.get("topic_slug") or "").strip(),
                    updated_by=str(topic_state.get("updated_by") or "codex"),
                )
                if isinstance(route_choice_payload, dict):
                    queue_meta["selected_candidate_route_choice_payload"] = route_choice_payload
            if isinstance(route_choice_payload, dict):
                promotion_gate_payload = load_selected_candidate_promotion_gate(
                    load_json=load_json,
                    knowledge_root=knowledge_root,
                    topic_slug=str(topic_state.get("topic_slug") or "").strip(),
                )
                if promotion_gate_payload is None and selected_candidate_promotion_gate_ready_for_materialization(
                    load_json=load_json,
                    knowledge_root=knowledge_root,
                    topic_slug=str(topic_state.get("topic_slug") or "").strip(),
                ):
                    promotion_gate_payload = derive_selected_candidate_promotion_gate(
                        load_json=load_json,
                        knowledge_root=knowledge_root,
                        topic_slug=str(topic_state.get("topic_slug") or "").strip(),
                        requested_by=str(topic_state.get("updated_by") or "codex"),
                    )
                    if isinstance(promotion_gate_payload, dict):
                        queue_meta["selected_candidate_promotion_gate_payload"] = promotion_gate_payload
                if isinstance(promotion_gate_payload, dict):
                    gate_status = str(promotion_gate_payload.get("status") or "").strip()
                    if gate_status == "pending_human_approval":
                        queue.append(
                            {
                                "action_id": f"action:{topic_state['topic_slug']}:selected-candidate-promotion-gate",
                                "topic_slug": topic_state["topic_slug"],
                                "resume_stage": topic_state["resume_stage"],
                                "status": "pending",
                                "action_type": "approve_promotion",
                                "summary": (
                                    "Review the pending promotion gate for the selected staged candidate "
                                    f"`{str(promotion_gate_payload.get('candidate_id') or '').strip()}` "
                                    "before any Layer 2 writeback."
                                ),
                                "auto_runnable": False,
                                "handler": None,
                                "handler_args": {
                                    "run_id": topic_state.get("latest_run_id"),
                                    "candidate_id": str(
                                        promotion_gate_payload.get("candidate_id") or ""
                                    ).strip(),
                                    "candidate_path": str(
                                        route_choice_payload.get("selected_candidate_path") or ""
                                    ).strip(),
                                },
                                "queue_source": queue_meta.get("queue_source") or "runtime_appended",
                                "declared_contract_path": queue_meta.get("declared_contract_path"),
                            }
                        )
                        return queue, queue_meta
                    if gate_status == "approved":
                        queue.append(
                            {
                                "action_id": f"action:{topic_state['topic_slug']}:selected-candidate-promotion-approved",
                                "topic_slug": topic_state["topic_slug"],
                                "resume_stage": topic_state["resume_stage"],
                                "status": "pending",
                                "action_type": "promote_candidate",
                                "summary": (
                                    "Promote the selected staged candidate "
                                    f"`{str(promotion_gate_payload.get('candidate_id') or '').strip()}` "
                                    "into Layer 2 using the approved promotion gate."
                                ),
                                "auto_runnable": False,
                                "handler": None,
                                "handler_args": {
                                    "run_id": topic_state.get("latest_run_id"),
                                    "candidate_id": str(
                                        promotion_gate_payload.get("candidate_id") or ""
                                    ).strip(),
                                    "candidate_path": str(
                                        route_choice_payload.get("selected_candidate_path") or ""
                                    ).strip(),
                                },
                                "queue_source": queue_meta.get("queue_source") or "runtime_appended",
                                "declared_contract_path": queue_meta.get("declared_contract_path"),
                            }
                        )
                        return queue, queue_meta
                    if gate_status == "promoted":
                        run_id = str(topic_state.get("latest_run_id") or "").strip()
                        candidate_rows = (
                            read_jsonl(
                                knowledge_root
                                / "topics"
                                / topic_state["topic_slug"]
                                / "L3"
                                / "runs"
                                / run_id
                                / "candidate_ledger.jsonl"
                            )
                            if run_id
                            else []
                        )
                        followup_rows = read_jsonl(
                            knowledge_root
                            / "topics"
                            / topic_state["topic_slug"]
                            / "runtime"
                            / FOLLOWUP_SUBTOPICS_FILENAME
                        )
                        completion_payload = load_json(
                            knowledge_root
                            / "topics"
                            / topic_state["topic_slug"]
                            / "runtime"
                            / TOPIC_COMPLETION_FILENAME
                        ) or {}
                        candidate_count_value = completion_payload.get("candidate_count")
                        followup_count_value = completion_payload.get("followup_subtopic_count")
                        candidate_count_matches = (
                            candidate_count_value is not None and int(candidate_count_value) == len(candidate_rows)
                        )
                        followup_count_matches = (
                            followup_count_value is not None and int(followup_count_value) == len(followup_rows)
                        )
                        completion_stale = (
                            str(completion_payload.get("run_id") or "") != run_id
                            or not candidate_count_matches
                            or not followup_count_matches
                            or str(completion_payload.get("status") or "") != "promoted"
                        )
                        post_promotion_followup = load_post_promotion_followup(
                            load_json=load_json,
                            knowledge_root=knowledge_root,
                            topic_slug=str(topic_state.get("topic_slug") or "").strip(),
                        )
                        if post_promotion_followup is None and post_promotion_followup_ready_for_materialization(
                            load_json=load_json,
                            knowledge_root=knowledge_root,
                            topic_slug=str(topic_state.get("topic_slug") or "").strip(),
                        ):
                            post_promotion_followup = derive_post_promotion_followup(
                                load_json=load_json,
                                knowledge_root=knowledge_root,
                                topic_slug=str(topic_state.get("topic_slug") or "").strip(),
                                updated_by=str(topic_state.get("updated_by") or "codex"),
                            )
                            if isinstance(post_promotion_followup, dict):
                                queue_meta["post_promotion_followup_payload"] = post_promotion_followup
                        if completion_stale:
                            queue.append(
                                {
                                    "action_id": f"action:{topic_state['topic_slug']}:selected-candidate-post-promotion",
                                    "topic_slug": topic_state["topic_slug"],
                                    "resume_stage": "L4",
                                    "status": "pending",
                                    "action_type": "assess_topic_completion",
                                    "summary": (
                                        "Refresh topic-completion state after the selected staged candidate "
                                        "has already been written back into Layer 2."
                                    ),
                                    "auto_runnable": True,
                                    "handler": None,
                                    "handler_args": {
                                        "run_id": topic_state.get("latest_run_id"),
                                    },
                                    "queue_source": queue_meta.get("queue_source") or "runtime_appended",
                                    "declared_contract_path": queue_meta.get("declared_contract_path"),
                                }
                            )
                        elif isinstance(post_promotion_followup, dict):
                            blocker_route_choice_payload = load_post_promotion_blocker_route_choice(
                                load_json=load_json,
                                knowledge_root=knowledge_root,
                                topic_slug=str(topic_state.get("topic_slug") or "").strip(),
                            )
                            if blocker_route_choice_payload is None and post_promotion_blocker_route_choice_ready_for_materialization(
                                load_json=load_json,
                                knowledge_root=knowledge_root,
                                topic_slug=str(topic_state.get("topic_slug") or "").strip(),
                            ):
                                blocker_route_choice_payload = derive_post_promotion_blocker_route_choice(
                                    load_json=load_json,
                                    knowledge_root=knowledge_root,
                                    topic_slug=str(topic_state.get("topic_slug") or "").strip(),
                                    updated_by=str(topic_state.get("updated_by") or "codex"),
                                )
                                if isinstance(blocker_route_choice_payload, dict):
                                    queue_meta["post_promotion_blocker_route_choice_payload"] = blocker_route_choice_payload
                            if isinstance(blocker_route_choice_payload, dict):
                                queue.append(
                                    {
                                        "action_id": f"action:{topic_state['topic_slug']}:post-promotion-blocker-route-choice",
                                        "topic_slug": topic_state["topic_slug"],
                                        "resume_stage": "L4",
                                        "status": "pending",
                                        "action_type": str(
                                            blocker_route_choice_payload.get("chosen_action_type") or ""
                                        ).strip(),
                                        "summary": str(
                                            blocker_route_choice_payload.get("chosen_action_summary") or ""
                                        ).strip(),
                                        "auto_runnable": False,
                                        "handler": None,
                                        "handler_args": {
                                            "run_id": topic_state.get("latest_run_id"),
                                            "candidate_id": str(
                                                blocker_route_choice_payload.get("candidate_id") or ""
                                            ).strip(),
                                        },
                                        "queue_source": queue_meta.get("queue_source") or "runtime_appended",
                                        "declared_contract_path": queue_meta.get("declared_contract_path"),
                                    }
                                )
                                return queue, queue_meta
                            queue.append(
                                {
                                    "action_id": f"action:{topic_state['topic_slug']}:post-promotion-followup",
                                    "topic_slug": topic_state["topic_slug"],
                                    "resume_stage": "L4",
                                    "status": "pending",
                                    "action_type": str(
                                        post_promotion_followup.get("chosen_action_type") or ""
                                    ).strip(),
                                    "summary": str(
                                        post_promotion_followup.get("chosen_action_summary") or ""
                                    ).strip(),
                                    "auto_runnable": False,
                                    "handler": None,
                                    "handler_args": {
                                        "run_id": topic_state.get("latest_run_id"),
                                        "candidate_id": str(
                                            post_promotion_followup.get("candidate_id") or ""
                                        ).strip(),
                                    },
                                    "queue_source": queue_meta.get("queue_source") or "runtime_appended",
                                    "declared_contract_path": queue_meta.get("declared_contract_path"),
                                }
                            )
                        else:
                            proof_repair_review = post_promotion_proof_repair_review_action(
                                load_json=load_json,
                                knowledge_root=knowledge_root,
                                topic_slug=topic_state["topic_slug"],
                                topic_state=topic_state,
                                queue_meta=queue_meta,
                            )
                            if proof_repair_review is not None:
                                queue.append(proof_repair_review)
                                return queue, queue_meta
                            post_promotion_followup = post_promotion_formalization_followup_action(
                                load_json=load_json,
                                knowledge_root=knowledge_root,
                                topic_slug=topic_state["topic_slug"],
                                topic_state=topic_state,
                                queue_meta=queue_meta,
                            )
                            if post_promotion_followup is not None:
                                queue.append(post_promotion_followup)
                                return queue, queue_meta
                            queue.append(
                                {
                                    "action_id": f"action:{topic_state['topic_slug']}:post-promotion-inspect",
                                    "topic_slug": topic_state["topic_slug"],
                                    "resume_stage": "L4",
                                    "status": "pending",
                                    "action_type": "inspect_resume_state",
                                    "summary": _synthesize_fallback_summary(
                                        topic_state["topic_slug"],
                                        topic_state,
                                        knowledge_root,
                                        "post_promotion",
                                    ),
                                    "auto_runnable": False,
                                    "handler": None,
                                    "handler_args": {},
                                    "queue_source": queue_meta.get("queue_source") or "runtime_appended",
                                    "declared_contract_path": queue_meta.get("declared_contract_path"),
                                }
                            )
                        return queue, queue_meta
                queue.append(
                    {
                        "action_id": f"action:{topic_state['topic_slug']}:selected-candidate-route-choice",
                        "topic_slug": topic_state["topic_slug"],
                        "resume_stage": topic_state["resume_stage"],
                        "status": "pending",
                        "action_type": str(route_choice_payload.get("chosen_action_type") or "").strip(),
                        "summary": str(route_choice_payload.get("chosen_action_summary") or "").strip(),
                        "auto_runnable": False,
                        "handler": None,
                        "handler_args": {
                            "run_id": topic_state.get("latest_run_id"),
                            "candidate_id": str(route_choice_payload.get("selected_candidate_id") or "").strip(),
                            "candidate_path": str(route_choice_payload.get("selected_candidate_path") or "").strip(),
                        },
                        "queue_source": queue_meta.get("queue_source") or "runtime_appended",
                        "declared_contract_path": queue_meta.get("declared_contract_path"),
                    }
                )
                return queue, queue_meta
            selected_candidate_id = str(
                selection_payload.get("selected_candidate_id") or ""
            ).strip()
            selected_candidate_path = str(
                selection_payload.get("selected_candidate_path") or ""
            ).strip()
            queue.append(
                {
                    "action_id": f"action:{topic_state['topic_slug']}:selected-consultation-candidate",
                    "topic_slug": topic_state["topic_slug"],
                    "resume_stage": topic_state["resume_stage"],
                    "status": "pending",
                    "action_type": "selected_consultation_candidate_followup",
                    "summary": (
                        f"Review the selected staged candidate `{selected_candidate_id}` "
                        "and decide whether to split, validate, or promote it before deeper execution."
                    ),
                    "auto_runnable": False,
                    "handler": None,
                    "handler_args": {
                        "run_id": topic_state.get("latest_run_id"),
                        "candidate_id": selected_candidate_id,
                        "candidate_path": selected_candidate_path,
                    },
                    "queue_source": queue_meta.get("queue_source") or "runtime_appended",
                    "declared_contract_path": queue_meta.get("declared_contract_path"),
                }
            )
            return queue, queue_meta
        if should_advance_past_staged_l2_review(
            knowledge_root=knowledge_root,
            topic_slug=str(topic_state.get("topic_slug") or "").strip(),
            runtime_contract=runtime_contract,
        ):
            consultation_auto_runnable = consultation_followup_ready_for_auto_run(
                load_json=load_json,
                knowledge_root=knowledge_root,
                topic_slug=str(topic_state.get("topic_slug") or "").strip(),
            )
            queue.append(
                {
                    "action_id": f"action:{topic_state['topic_slug']}:consult-staged-l2",
                    "topic_slug": topic_state["topic_slug"],
                    "resume_stage": topic_state["resume_stage"],
                    "status": "pending",
                    "action_type": "consultation_followup",
                    "summary": "Consult the topic-local staged L2 memory and choose one bounded candidate before deeper execution.",
                    "auto_runnable": consultation_auto_runnable,
                    "handler": None,
                    "handler_args": {"run_id": topic_state.get("latest_run_id")},
                    "queue_source": queue_meta.get("queue_source") or "runtime_appended",
                    "declared_contract_path": queue_meta.get("declared_contract_path"),
                }
            )
            return queue, queue_meta
        fallback_summary = _synthesize_fallback_summary(
            topic_state["topic_slug"],
            topic_state,
            knowledge_root,
            "l1_vault",
        )
        queue.append(
            {
                "action_id": f"action:{topic_state['topic_slug']}:inspect-l1-vault",
                "topic_slug": topic_state["topic_slug"],
                "resume_stage": topic_state["resume_stage"],
                "status": "pending",
                "action_type": "inspect_resume_state",
                "summary": fallback_summary,
                "auto_runnable": False,
                "handler": None,
                "handler_args": {},
                "queue_source": queue_meta.get("queue_source") or "runtime_appended",
                "declared_contract_path": queue_meta.get("declared_contract_path"),
            }
        )

    if not queue:
        queue.append(
            {
                "action_id": f"action:{topic_state['topic_slug']}:01",
                "topic_slug": topic_state["topic_slug"],
                "resume_stage": topic_state["resume_stage"],
                "status": "pending",
                "action_type": "inspect_resume_state",
                "summary": _synthesize_fallback_summary(
                    topic_state["topic_slug"],
                    topic_state,
                    knowledge_root,
                    "empty_queue",
                ),
                "auto_runnable": False,
                "handler": None,
                "handler_args": {},
                "queue_source": queue_meta.get("queue_source") or "heuristic",
                "declared_contract_path": queue_meta.get("declared_contract_path"),
            }
        )
    return queue, queue_meta


def derive_surface_roots(topic_state: dict) -> dict[str, str]:
    return derive_interaction_surface_roots(topic_state)


def build_interaction_state(
    topic_state: dict,
    queue: list[dict],
    queue_meta: dict,
    human_request: str,
    topic_runtime_root: Path,
    knowledge_root: Path,
) -> dict:
    return materialize_interaction_state(
        topic_state,
        queue,
        queue_meta,
        human_request,
        topic_runtime_root,
        knowledge_root,
        action_queue_contract_generated_filename=ACTION_QUEUE_CONTRACT_GENERATED_FILENAME,
        action_queue_contract_generated_note_filename=ACTION_QUEUE_CONTRACT_GENERATED_NOTE_FILENAME,
        deferred_buffer_note_filename=DEFERRED_BUFFER_NOTE_FILENAME,
        followup_subtopics_note_filename=FOLLOWUP_SUBTOPICS_NOTE_FILENAME,
        deferred_buffer_filename=DEFERRED_BUFFER_FILENAME,
        followup_subtopics_filename=FOLLOWUP_SUBTOPICS_FILENAME,
        now_iso=now_iso,
        load_json=load_json,
    )


def build_operator_console(topic_state: dict, interaction_state: dict, queue: list[dict]) -> str:
    return render_operator_console(topic_state, interaction_state, queue)


def build_agent_brief(topic_state: dict, queue: list[dict], interaction_state: dict) -> str:
    return render_agent_brief(topic_state, queue, interaction_state)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--knowledge-root")
    parser.add_argument("--repo-root")
    parser.add_argument("--topic-slug")
    parser.add_argument("--topic")
    parser.add_argument("--statement")
    parser.add_argument("--run-id")
    parser.add_argument("--control-note")
    parser.add_argument("--research-mode")
    parser.add_argument("--updated-by", default="codex")
    parser.add_argument("--arxiv-id", action="append", default=[])
    parser.add_argument("--local-note-path", action="append", default=[])
    parser.add_argument("--skill-query", action="append", default=[])
    parser.add_argument("--human-request")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    topic_slug = args.topic_slug or (slugify(args.topic) if args.topic else None)
    if not topic_slug:
        raise SystemExit("Provide --topic-slug or --topic.")

    knowledge_root = (
        Path(args.knowledge_root).expanduser().resolve()
        if args.knowledge_root
        else Path(__file__).resolve().parents[2]
    )
    research_root = (
        Path(args.repo_root).expanduser().resolve() / "research"
        if args.repo_root
        else knowledge_root.parent
    )
    ensure_topic_shell(knowledge_root, topic_slug, args.statement, args.topic)

    register_arxiv = knowledge_root / "source-layer" / "scripts" / "register_arxiv_source.py"
    register_local = knowledge_root / "source-layer" / "scripts" / "register_local_note_source.py"
    sync_script = knowledge_root / "runtime" / "scripts" / "sync_topic_state.py"
    skill_discovery_script = (
        research_root / "adapters" / "openclaw" / "scripts" / "discover_external_skills.py"
    )
    advance_closed_loop_script = knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py"
    execution_handoff_script = (
        research_root / "adapters" / "openclaw" / "scripts" / "dispatch_execution_task.py"
    )
    literature_followup_script = knowledge_root / "runtime" / "scripts" / "run_literature_followup.py"
    decision_script = knowledge_root / "runtime" / "scripts" / "decide_next_action.py"
    conformance_audit_script = knowledge_root / "runtime" / "scripts" / "audit_topic_conformance.py"
    py = python_command()

    for arxiv_id in args.arxiv_id:
        subprocess.run(
            [
                *py,
                str(register_arxiv),
                "--topic-slug",
                topic_slug,
                "--arxiv-id",
                arxiv_id,
                "--registered-by",
                args.updated_by,
                "--download-source",
            ],
            check=True,
            stdin=subprocess.DEVNULL,
        )

    for local_note_path in args.local_note_path:
        subprocess.run(
            [
                *py,
                str(register_local),
                "--topic-slug",
                topic_slug,
                "--path",
                local_note_path,
                "--registered-by",
                args.updated_by,
            ],
            check=True,
            stdin=subprocess.DEVNULL,
        )

    sync_cmd = [
        *py,
        str(sync_script),
        "--topic-slug",
        topic_slug,
        "--updated-by",
        args.updated_by,
    ]
    if args.run_id:
        sync_cmd.extend(["--run-id", args.run_id])
    if args.control_note:
        sync_cmd.extend(["--control-note", args.control_note])
    if args.research_mode:
        sync_cmd.extend(["--research-mode", args.research_mode])
    subprocess.run(sync_cmd, check=True, stdin=subprocess.DEVNULL)

    topic_runtime_root = knowledge_root / "topics" / topic_slug / "runtime"
    topic_state = load_json(topic_runtime_root / "topic_state.json")
    if topic_state is None:
        raise SystemExit(f"Runtime state missing for topic {topic_slug}")

    if args.skill_query:
        skill_cmd = [
            *py,
            str(skill_discovery_script),
            "--topic-slug",
            topic_slug,
            "--updated-by",
            args.updated_by,
        ]
        for query in args.skill_query:
            skill_cmd.extend(["--query", query])
        subprocess.run(skill_cmd, check=True, stdin=subprocess.DEVNULL)

    action_queue, queue_meta = materialize_action_queue(
        topic_state,
        args.skill_query,
        skill_discovery_script,
        advance_closed_loop_script,
        execution_handoff_script,
        literature_followup_script,
        knowledge_root,
    )
    route_choice_payload = queue_meta.get("selected_candidate_route_choice_payload")
    if isinstance(route_choice_payload, dict):
        route_choice_paths = selected_candidate_route_choice_paths(
            knowledge_root=knowledge_root,
            topic_slug=topic_slug,
        )
        write_json(route_choice_paths["json"], route_choice_payload)
        write_text(
            route_choice_paths["note"],
            render_selected_candidate_route_choice_markdown(route_choice_payload),
        )
    promotion_gate_payload = queue_meta.get("selected_candidate_promotion_gate_payload")
    if isinstance(promotion_gate_payload, dict):
        promotion_gate_paths = selected_candidate_promotion_gate_paths(
            knowledge_root=knowledge_root,
            topic_slug=topic_slug,
        )
        write_json(promotion_gate_paths["json"], promotion_gate_payload)
        write_text(
            promotion_gate_paths["note"],
            render_selected_candidate_promotion_gate_markdown(promotion_gate_payload),
        )
    post_promotion_followup_payload = queue_meta.get("post_promotion_followup_payload")
    if isinstance(post_promotion_followup_payload, dict):
        followup_paths = post_promotion_followup_paths(
            knowledge_root=knowledge_root,
            topic_slug=topic_slug,
        )
        write_json(followup_paths["json"], post_promotion_followup_payload)
        write_text(
            followup_paths["note"],
            render_post_promotion_followup_markdown(post_promotion_followup_payload),
        )
    blocker_route_choice_payload = queue_meta.get("post_promotion_blocker_route_choice_payload")
    if isinstance(blocker_route_choice_payload, dict):
        blocker_paths = post_promotion_blocker_route_choice_paths(
            knowledge_root=knowledge_root,
            topic_slug=topic_slug,
        )
        write_json(blocker_paths["json"], blocker_route_choice_payload)
        write_text(
            blocker_paths["note"],
            render_post_promotion_blocker_route_choice_markdown(blocker_route_choice_payload),
        )
    write_jsonl(topic_runtime_root / "action_queue.jsonl", action_queue)
    queue_contract_snapshot = build_action_queue_contract_snapshot(
        topic_state,
        action_queue,
        queue_meta,
        knowledge_root,
    )
    write_json(
        topic_runtime_root / ACTION_QUEUE_CONTRACT_GENERATED_FILENAME,
        queue_contract_snapshot,
    )
    write_text(
        topic_runtime_root / ACTION_QUEUE_CONTRACT_GENERATED_NOTE_FILENAME,
        build_action_queue_contract_markdown(queue_contract_snapshot),
    )
    subprocess.run(
        [
            *py,
            str(decision_script),
            "--topic-slug",
            topic_slug,
            "--updated-by",
            args.updated_by,
        ],
        check=True,
        stdin=subprocess.DEVNULL,
    )
    subprocess.run(sync_cmd, check=True, stdin=subprocess.DEVNULL)
    topic_state = load_json(topic_runtime_root / "topic_state.json")
    if topic_state is None:
        raise SystemExit(f"Runtime state missing for topic {topic_slug} after decision refresh")
    human_request = args.human_request or args.statement or topic_state.get("summary") or f"Resume {topic_slug}."
    interaction_state = build_interaction_state(
        topic_state,
        action_queue,
        queue_meta,
        human_request,
        topic_runtime_root,
        knowledge_root,
    )
    write_json(topic_runtime_root / "interaction_state.json", interaction_state)
    write_text(topic_runtime_root / "operator_console.md", build_operator_console(topic_state, interaction_state, action_queue))
    write_text(topic_runtime_root / "agent_brief.md", build_agent_brief(topic_state, action_queue, interaction_state))
    subprocess.run(
        [
            *py,
            str(conformance_audit_script),
            "--topic-slug",
            topic_slug,
            "--phase",
            "entry",
            "--updated-by",
            args.updated_by,
        ],
        check=True,
        stdin=subprocess.DEVNULL,
    )

    print(f"Orchestrated topic {topic_slug}")
    print(f"- topic_state: {topic_runtime_root / 'topic_state.json'}")
    print(f"- action_queue: {topic_runtime_root / 'action_queue.jsonl'}")
    print(f"- agent_brief: {topic_runtime_root / 'agent_brief.md'}")
    print(f"- interaction_state: {topic_runtime_root / 'interaction_state.json'}")
    print(f"- operator_console: {topic_runtime_root / 'operator_console.md'}")
    print(f"- conformance_state: {topic_runtime_root / 'conformance_state.json'}")
    print(f"- conformance_report: {topic_runtime_root / 'conformance_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
