#!/usr/bin/env python3
"""Bootstrap or resume an AITP topic and materialize an executable action queue."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

from closed_loop_v1 import compute_closed_loop_status

NEXT_ACTIONS_CONTRACT_FILENAME = "next_actions.contract.json"
ACTION_QUEUE_CONTRACT_GENERATED_FILENAME = "action_queue_contract.generated.json"
ACTION_QUEUE_CONTRACT_GENERATED_NOTE_FILENAME = "action_queue_contract.generated.md"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "aitp-topic"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict | None:
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


def relative_path(path: Path | None, root: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def ensure_topic_shell(knowledge_root: Path, topic_slug: str, statement: str | None) -> None:
    created_at = now_iso()
    title = topic_slug.replace("-", " ").title()

    layer0_topic = knowledge_root / "source-layer" / "topics" / topic_slug / "topic.json"
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

    intake_topic = knowledge_root / "intake" / "topics" / topic_slug / "topic.json"
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

    intake_status = knowledge_root / "intake" / "topics" / topic_slug / "status.json"
    if not intake_status.exists():
        write_json(
            intake_status,
            {"stage": "L1_active", "next_stage": "L1", "last_updated": created_at},
        )

    if statement:
        latest_run_root = knowledge_root / "feedback" / "topics" / topic_slug / "runs"
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
                "# Next actions\n\n1. Convert the topic statement into explicit source and candidate artifacts.\n",
            )


def classify_action(summary: str) -> tuple[str, bool]:
    lowered = summary.lower()
    if "baseline" in lowered or "reproduc" in lowered:
        return "baseline_reproduction", False
    if "atomic" in lowered or "dependency graph" in lowered or "decompos" in lowered:
        return "atomic_understanding", False
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
        knowledge_root / "validation" / "topics" / topic_slug / "runs" / run_id / "literature_followup_receipts.jsonl"
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


def declared_actions_from_contract(topic_state: dict, declared_contract: dict | None) -> tuple[list[dict], dict]:
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
        derived_action_type, derived_auto_runnable = classify_action(summary)
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
    declared_contract = load_declared_action_contract(topic_state, knowledge_root)
    queue, queue_meta = declared_actions_from_contract(topic_state, declared_contract)
    if not queue:
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
                    "declared_contract_path": queue_meta.get("declared_contract_path"),
                }
            )

    needs_capability_review = any(
        action["action_type"] in {"backend_extension", "manual_followup"} for action in queue
    )
    has_skill_action = any(action["action_type"] == "skill_discovery" for action in queue)
    if needs_capability_review and not has_skill_action and queue_meta.get("append_skill_action_if_needed", True):
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

    closed_loop = compute_closed_loop_status(
        knowledge_root,
        topic_state["topic_slug"],
        topic_state.get("latest_run_id"),
        queue_rows=queue,
    )
    handler_args = {"run_id": topic_state.get("latest_run_id")}

    if queue_meta.get("append_runtime_actions", True) and closed_loop["next_transition"] == "select_route":
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
    elif queue_meta.get("append_runtime_actions", True) and closed_loop["next_transition"] == "materialize_task":
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
    elif queue_meta.get("append_runtime_actions", True) and closed_loop["next_transition"] == "ingest_result":
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
    elif queue_meta.get("append_runtime_actions", True) and closed_loop["awaiting_external_result"] and closed_loop["execution_task"]:
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

    completed_followups = completed_literature_followups(
        knowledge_root,
        topic_state["topic_slug"],
        topic_state.get("latest_run_id"),
    )
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

    if not queue:
        queue.append(
            {
                "action_id": f"action:{topic_state['topic_slug']}:01",
                "topic_slug": topic_state["topic_slug"],
                "resume_stage": topic_state["resume_stage"],
                "status": "pending",
                "action_type": "inspect_resume_state",
                "summary": "No explicit pending actions were found; inspect the runtime resume state.",
                "auto_runnable": False,
                "handler": None,
                "handler_args": {},
                "queue_source": queue_meta.get("queue_source") or "heuristic",
                "declared_contract_path": queue_meta.get("declared_contract_path"),
            }
        )
    return queue, queue_meta


def derive_surface_roots(topic_state: dict) -> dict[str, str]:
    topic_slug = topic_state["topic_slug"]
    pointers = topic_state["pointers"]

    feedback_status_path = pointers.get("feedback_status_path")
    feedback_run_root = feedback_status_path.rsplit("/", 1)[0] if feedback_status_path else f"feedback/topics/{topic_slug}"

    promotion_decision_path = pointers.get("promotion_decision_path")
    validation_run_root = (
        promotion_decision_path.rsplit("/", 1)[0]
        if promotion_decision_path
        else f"validation/topics/{topic_slug}"
    )

    return {
        "L0": f"source-layer/topics/{topic_slug}",
        "L1": f"intake/topics/{topic_slug}",
        "L2": "canonical",
        "L3": feedback_run_root,
        "L4_execution": validation_run_root,
        "L4_control": pointers.get("control_note_path") or "(missing)",
        "L3_action_contract": pointers.get("next_actions_contract_path") or "(missing)",
        "runtime": f"runtime/topics/{topic_slug}",
    }


def build_interaction_state(
    topic_state: dict,
    queue: list[dict],
    queue_meta: dict,
    human_request: str,
    topic_runtime_root: Path,
    knowledge_root: Path,
) -> dict:
    pointers = topic_state["pointers"]
    surfaces = derive_surface_roots(topic_state)
    surfaces["runtime_unfinished"] = f"runtime/topics/{topic_state['topic_slug']}/unfinished_work.md"
    surfaces["runtime_decision"] = f"runtime/topics/{topic_state['topic_slug']}/next_action_decision.md"
    surfaces["runtime_queue_contract"] = (
        f"runtime/topics/{topic_state['topic_slug']}/{ACTION_QUEUE_CONTRACT_GENERATED_NOTE_FILENAME}"
    )
    capability_artifacts = []
    for filename in ("skill_discovery.json", "skill_recommendations.md"):
        artifact_path = topic_runtime_root / filename
        if artifact_path.exists():
            capability_artifacts.append(str(artifact_path))

    closed_loop = compute_closed_loop_status(
        knowledge_root,
        topic_state["topic_slug"],
        topic_state.get("latest_run_id"),
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
            {
                "surface": "L3_action_contract",
                "path": surfaces["L3_action_contract"],
                "role": "declared L3 action contract when present",
            },
            {"surface": "L4_execution", "path": surfaces["L4_execution"], "role": "execution-backed validation"},
            {"surface": "L4_control", "path": surfaces["L4_control"], "role": "human-readable adjudication"},
            {"surface": "runtime", "path": surfaces["runtime"], "role": "resume and operator visibility"},
            {
                "surface": "runtime_unfinished",
                "path": surfaces["runtime_unfinished"],
                "role": "human-readable unfinished-work index",
            },
            {
                "surface": "runtime_decision",
                "path": surfaces["runtime_decision"],
                "role": "human-readable next-action decision",
            },
            {
                "surface": "runtime_queue_contract",
                "path": surfaces["runtime_queue_contract"],
                "role": "generated action-contract snapshot for editing",
            },
            {
                "surface": "runtime_trajectory",
                "path": closed_loop["paths"].get("trajectory_note_path")
                or f"runtime/topics/{topic_state['topic_slug']}/(trajectory-log-missing)",
                "role": "human-readable execution trajectory after result ingest",
            },
            {
                "surface": "runtime_failure_classification",
                "path": closed_loop["paths"].get("failure_classification_note_path")
                or f"runtime/topics/{topic_state['topic_slug']}/(failure-classification-missing)",
                "role": "human-readable failure classification after result ingest",
            },
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
            "next_transition": closed_loop.get("next_transition"),
            "next_transition_reason": closed_loop.get("next_transition_reason"),
            "selected_route_id": (closed_loop.get("selected_route") or {}).get("route_id"),
            "task_id": (closed_loop.get("execution_task") or {}).get("task_id"),
            "result_id": (closed_loop.get("result_manifest") or {}).get("result_id"),
            "latest_decision": (closed_loop.get("latest_decision") or {}).get("decision"),
            "literature_followup_count": len(closed_loop.get("literature_followups") or []),
            "research_mode": topic_state.get("research_mode"),
            "executor_kind": topic_state.get("active_executor_kind"),
            "reasoning_profile": topic_state.get("active_reasoning_profile"),
            "failure_severity": (closed_loop.get("failure_classification") or {}).get("severity"),
        },
        "decision_surface": {
            "unfinished_work_path": f"runtime/topics/{topic_state['topic_slug']}/unfinished_work.json",
            "unfinished_work_note_path": f"runtime/topics/{topic_state['topic_slug']}/unfinished_work.md",
            "next_action_decision_path": f"runtime/topics/{topic_state['topic_slug']}/next_action_decision.json",
            "next_action_decision_note_path": f"runtime/topics/{topic_state['topic_slug']}/next_action_decision.md",
            "decision_contract_path": pointers.get("next_action_decision_contract_path"),
            "decision_mode": decision_payload.get("decision_mode"),
            "decision_source": decision_payload.get("decision_source"),
            "decision_contract_status": decision_payload.get("decision_contract_status"),
            "decision_basis": decision_payload.get("decision_basis"),
            "selected_action_id": (decision_payload.get("selected_action") or {}).get("action_id"),
            "selected_action_type": (decision_payload.get("selected_action") or {}).get("action_type"),
            "selected_action_auto_runnable": bool(
                (decision_payload.get("selected_action") or {}).get("auto_runnable")
            ),
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
            "generated_contract_path": (
                f"runtime/topics/{topic_state['topic_slug']}/{ACTION_QUEUE_CONTRACT_GENERATED_FILENAME}"
            ),
            "generated_contract_note_path": (
                f"runtime/topics/{topic_state['topic_slug']}/{ACTION_QUEUE_CONTRACT_GENERATED_NOTE_FILENAME}"
            ),
            "policy_note": queue_meta.get("policy_note"),
        },
        "pending_actions": queue,
    }


def build_operator_console(interaction_state: dict, queue: list[dict]) -> str:
    lines = [
        "# AITP operator console",
        "",
        f"- Topic slug: `{interaction_state['topic_slug']}`",
        f"- Human request: `{interaction_state['human_request']}`",
        f"- Resume stage: `{interaction_state['resume_stage']}`",
        f"- Last materialized stage: `{interaction_state['last_materialized_stage']}`",
        "",
        "## Active loops",
        "",
        "1. Research loop: use L0/L1/L2/L3/L4 according to the current epistemic state.",
        "2. Capability loop: if a missing workflow or backend is the blocker, run controlled skill discovery before declaring failure.",
        "3. Delivery loop: final output may land in L1, L2, L3, or L4, but it must always report exact artifact paths and the reason for that layer choice.",
        "",
        "## Human edit surfaces",
        "",
    ]

    for surface in interaction_state["human_edit_surfaces"]:
        lines.append(f"- [{surface['surface']}] `{surface['path']}` {surface['role']}")

    lines.extend(
        [
            "",
            "## Pending actions",
            "",
        ]
    )

    for index, action in enumerate(queue, start=1):
        handler = action["handler"] or "(manual)"
        lines.append(
            f"{index}. [{action['action_type']}] {action['summary']} "
            f"(auto_runnable={str(action['auto_runnable']).lower()}, handler={handler})"
        )

    decision_surface = interaction_state.get("decision_surface") or {}
    queue_surface = interaction_state.get("action_queue_surface") or {}
    lines.extend(
        [
            "",
            "## Decision surface",
            "",
            f"- Mode: `{decision_surface.get('decision_mode') or '(missing)'}`",
            f"- Source: `{decision_surface.get('decision_source') or '(missing)'}`",
            f"- Basis: `{decision_surface.get('decision_basis') or '(missing)'}`",
            f"- Selected action: `{decision_surface.get('selected_action_id') or '(none)'}`",
            f"- Selected type: `{decision_surface.get('selected_action_type') or '(none)'}`",
            f"- Selected action auto-runnable: `{str(bool(decision_surface.get('selected_action_auto_runnable'))).lower()}`",
            f"- Pending counts: total=`{decision_surface.get('pending_count', '(missing)')}`, "
            f"manual=`{decision_surface.get('manual_pending_count', '(missing)')}`, "
            f"auto=`{decision_surface.get('auto_pending_count', '(missing)')}`",
            f"- Reason: {decision_surface.get('reason') or '(missing)'}",
            f"- Control note: `{decision_surface.get('control_note_path') or '(missing)'}` "
            f"status=`{decision_surface.get('control_note_status') or 'missing'}`",
            f"- Decision contract: `{decision_surface.get('decision_contract_path') or '(missing)'}` "
            f"status=`{decision_surface.get('decision_contract_status') or 'missing'}`",
            "",
            "## Decision artifacts",
            "",
            f"- Unfinished work JSON: `{decision_surface.get('unfinished_work_path') or '(missing)'}`",
            f"- Unfinished work note: `{decision_surface.get('unfinished_work_note_path') or '(missing)'}`",
            f"- Next-action decision JSON: `{decision_surface.get('next_action_decision_path') or '(missing)'}`",
            f"- Next-action decision note: `{decision_surface.get('next_action_decision_note_path') or '(missing)'}`",
            "",
            "## Action queue source",
            "",
            f"- Queue source: `{queue_surface.get('queue_source') or '(missing)'}`",
            f"- Declared L3 contract: `{queue_surface.get('declared_contract_path') or '(missing)'}`",
            f"- Declared contract used: `{str(bool(queue_surface.get('declared_contract_used'))).lower()}`",
            f"- Generated contract JSON: `{queue_surface.get('generated_contract_path') or '(missing)'}`",
            f"- Generated contract note: `{queue_surface.get('generated_contract_note_path') or '(missing)'}`",
        ]
    )

    capability = interaction_state["capability_adaptation"]
    lines.extend(
        [
            "",
            "## Capability adaptation",
            "",
            f"- Protocol: `{capability['protocol_path']}`",
            f"- Discovery script: `{capability['discovery_script']}`",
            f"- Auto install allowed: `{str(capability['auto_install_allowed']).lower()}`",
        ]
    )

    discovery_artifacts = capability["discovery_artifacts"]
    if discovery_artifacts:
        lines.append("- Discovery artifacts:")
        for artifact in discovery_artifacts:
            lines.append(f"  - `{artifact}`")
    else:
        lines.append("- Discovery artifacts: `(none yet)`")

    lines.extend(
        [
            "",
            "## Delivery rule",
            "",
            f"- {interaction_state['delivery_contract']['rule']}",
            "",
        ]
    )
    return "\n".join(lines)


def build_agent_brief(topic_state: dict, queue: list[dict], interaction_state: dict) -> str:
    pointers = topic_state["pointers"]
    backend_bridges = topic_state.get("backend_bridges") or []
    decision_surface = interaction_state.get("decision_surface") or {}
    queue_surface = interaction_state.get("action_queue_surface") or {}
    research_mode_profile = topic_state.get("research_mode_profile") or {}
    lines = [
        "# AITP agent brief",
        "",
        f"- Topic slug: `{topic_state['topic_slug']}`",
        f"- Resume stage: `{topic_state['resume_stage']}`",
        f"- Last materialized stage: `{topic_state['last_materialized_stage']}`",
        f"- Source count: `{topic_state.get('source_count', 0)}`",
        f"- Latest run id: `{topic_state.get('latest_run_id') or '(none)'}`",
        f"- Research mode: `{topic_state.get('research_mode') or '(missing)'}`",
        f"- Executor kind: `{topic_state.get('active_executor_kind') or '(missing)'}`",
        f"- Reasoning profile: `{topic_state.get('active_reasoning_profile') or '(missing)'}`",
        "",
        "## Primary pointers",
        "",
        f"- Layer 0 source index: `{pointers.get('l0_source_index_path') or '(missing)'}`",
        f"- Intake status: `{pointers.get('intake_status_path') or '(missing)'}`",
        f"- Feedback status: `{pointers.get('feedback_status_path') or '(missing)'}`",
        f"- Promotion decision: `{pointers.get('promotion_decision_path') or '(missing)'}`",
        f"- Consultation index: `{pointers.get('consultation_index_path') or '(missing)'}`",
        f"- Interaction state: `runtime/topics/{topic_state['topic_slug']}/interaction_state.json`",
        f"- Operator console: `runtime/topics/{topic_state['topic_slug']}/operator_console.md`",
        f"- Conformance state: `runtime/topics/{topic_state['topic_slug']}/conformance_state.json`",
        f"- Conformance report: `runtime/topics/{topic_state['topic_slug']}/conformance_report.md`",
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
        f"- Declared L3 action contract: `{queue_surface.get('declared_contract_path') or '(missing)'}`",
        "",
        "## Research-mode governance",
        "",
        f"- Profile path: `{research_mode_profile.get('profile_path') or '(missing)'}`",
        f"- Profile label: `{research_mode_profile.get('label') or '(missing)'}`",
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
            "## L2 backend bridge snapshot",
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
            "## Action queue",
            "",
        ]
    )
    for index, action in enumerate(queue, start=1):
        lines.append(
            f"{index}. [{action['action_type']}] {action['summary']} (auto_runnable={str(action['auto_runnable']).lower()})"
        )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
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

    knowledge_root = Path(__file__).resolve().parents[2]
    research_root = knowledge_root.parent
    ensure_topic_shell(knowledge_root, topic_slug, args.statement)

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

    for arxiv_id in args.arxiv_id:
        subprocess.run(
            [
                "python3",
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
        )

    for local_note_path in args.local_note_path:
        subprocess.run(
            [
                "python3",
                str(register_local),
                "--topic-slug",
                topic_slug,
                "--path",
                local_note_path,
                "--registered-by",
                args.updated_by,
            ],
            check=True,
        )

    sync_cmd = [
        "python3",
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
    subprocess.run(sync_cmd, check=True)

    topic_runtime_root = knowledge_root / "runtime" / "topics" / topic_slug
    topic_state = load_json(topic_runtime_root / "topic_state.json")
    if topic_state is None:
        raise SystemExit(f"Runtime state missing for topic {topic_slug}")

    if args.skill_query:
        skill_cmd = [
            "python3",
            str(skill_discovery_script),
            "--topic-slug",
            topic_slug,
            "--updated-by",
            args.updated_by,
        ]
        for query in args.skill_query:
            skill_cmd.extend(["--query", query])
        subprocess.run(skill_cmd, check=True)

    action_queue, queue_meta = materialize_action_queue(
        topic_state,
        args.skill_query,
        skill_discovery_script,
        advance_closed_loop_script,
        execution_handoff_script,
        literature_followup_script,
        knowledge_root,
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
            "python3",
            str(decision_script),
            "--topic-slug",
            topic_slug,
            "--updated-by",
            args.updated_by,
        ],
        check=True,
    )
    subprocess.run(sync_cmd, check=True)
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
    write_text(topic_runtime_root / "operator_console.md", build_operator_console(interaction_state, action_queue))
    write_text(topic_runtime_root / "agent_brief.md", build_agent_brief(topic_state, action_queue, interaction_state))
    subprocess.run(
        [
            "python3",
            str(conformance_audit_script),
            "--topic-slug",
            topic_slug,
            "--phase",
            "entry",
            "--updated-by",
            args.updated_by,
        ],
        check=True,
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
