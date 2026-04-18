from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .l2_graph import materialize_canonical_index
from .l2_staging import stage_provisional_l2_entry
from .runtime_path_support import resolve_runtime_reference_path
from .topic_truth_root_support import compatibility_projection_path


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, Any] | None:
    target = path
    if not target.exists():
        compatibility = compatibility_projection_path(path)
        if compatibility is None or not compatibility.exists():
            return None
        target = compatibility
    return json.loads(target.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, ensure_ascii=True, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    compatibility = compatibility_projection_path(path)
    if compatibility is not None and compatibility != path:
        compatibility.parent.mkdir(parents=True, exist_ok=True)
        compatibility.write_text(rendered, encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    compatibility = compatibility_projection_path(path)
    if compatibility is not None and compatibility != path:
        compatibility.parent.mkdir(parents=True, exist_ok=True)
        compatibility.write_text(text, encoding="utf-8")


def iteration_run_root(service: Any, *, topic_slug: str, run_id: str) -> Path:
    return service._feedback_run_root(topic_slug, run_id)


def iteration_journal_paths(service: Any, *, topic_slug: str, run_id: str) -> dict[str, Path]:
    run_root = iteration_run_root(service, topic_slug=topic_slug, run_id=run_id)
    return {
        "run_root": run_root,
        "journal_json": run_root / "iteration_journal.json",
        "journal_note": run_root / "iteration_journal.md",
        "iterations_root": run_root / "iterations",
    }


def iteration_paths(
    service: Any,
    *,
    topic_slug: str,
    run_id: str,
    iteration_id: str,
) -> dict[str, Path]:
    journal_paths = iteration_journal_paths(service, topic_slug=topic_slug, run_id=run_id)
    root = journal_paths["iterations_root"] / iteration_id
    return {
        "root": root,
        "plan_json": root / "plan.contract.json",
        "plan_note": root / "plan.md",
        "return_json": root / "l4_return.json",
        "return_note": root / "l4_return.md",
        "synthesis_json": root / "l3_synthesis.json",
        "synthesis_note": root / "l3_synthesis.md",
    }


def _resolve_execution_task_path(
    service: Any,
    *,
    topic_slug: str,
    run_id: str,
    selected_action_id: str,
) -> Path | None:
    runtime_task = service._runtime_root(topic_slug) / "execution_task.json"
    if runtime_task.exists():
        runtime_payload = _read_json(runtime_task) or {}
        runtime_source_action_id = str(runtime_payload.get("source_action_id") or "").strip()
        if not selected_action_id or runtime_source_action_id == selected_action_id:
            return runtime_task
    execution_tasks_dir = service._minimum_l4_package_paths(topic_slug, run_id)["execution_tasks_dir"]
    if execution_tasks_dir.exists():
        matching_paths: list[Path] = []
        for task_path in sorted(execution_tasks_dir.glob("*.json")):
            payload = _read_json(task_path) or {}
            if str(payload.get("source_action_id") or "").strip() == selected_action_id:
                matching_paths.append(task_path)
        if matching_paths:
            return matching_paths[-1]
    return service._first_existing_validation_task_path(execution_tasks_dir)


def _resolve_returned_result_path(
    service: Any,
    *,
    topic_slug: str,
    run_id: str,
    topic_state: dict[str, Any],
) -> Path | None:
    pointer = str((topic_state.get("pointers") or {}).get("returned_execution_result_path") or "").strip()
    if pointer:
        resolved = resolve_runtime_reference_path(
            pointer,
            kernel_root=service.kernel_root,
            repo_root=service.repo_root,
        )
        if resolved is not None and resolved.exists():
            return resolved
    fallback = service._validation_run_root(topic_slug, run_id) / "returned_execution_result.json"
    if fallback.exists():
        return fallback
    return None


def _next_iteration_id(existing_ids: list[str]) -> str:
    return f"iteration-{len(existing_ids) + 1:03d}"


def _current_iteration_id(
    service: Any,
    *,
    topic_slug: str,
    run_id: str,
    selected_action_id: str,
    execution_task_ref: str,
) -> tuple[str, list[str], bool]:
    paths = iteration_journal_paths(service, topic_slug=topic_slug, run_id=run_id)
    payload = _read_json(paths["journal_json"]) or {}
    iteration_ids = [str(item).strip() for item in (payload.get("iteration_ids") or []) if str(item).strip()]
    current_iteration_id = str(payload.get("current_iteration_id") or "").strip()
    if not current_iteration_id:
        current_iteration_id = iteration_ids[-1] if iteration_ids else "iteration-001"
    if not iteration_ids:
        iteration_ids = [current_iteration_id]

    current_paths = iteration_paths(
        service,
        topic_slug=topic_slug,
        run_id=run_id,
        iteration_id=current_iteration_id,
    )
    current_plan = _read_json(current_paths["plan_json"]) or {}
    current_synthesis = _read_json(current_paths["synthesis_json"]) or {}
    current_plan_action_id = str(current_plan.get("selected_action_id") or "").strip()
    current_plan_execution_task_path = str(current_plan.get("execution_task_path") or "").strip()
    synthesis_status = str(current_synthesis.get("status") or "").strip()

    action_changed = bool(selected_action_id and selected_action_id != current_plan_action_id)
    execution_changed = bool(
        execution_task_ref
        and current_plan_execution_task_path
        and execution_task_ref != current_plan_execution_task_path
    )
    created_new = False
    if synthesis_status == "summarized" and (action_changed or execution_changed):
        current_iteration_id = _next_iteration_id(iteration_ids)
        iteration_ids.append(current_iteration_id)
        created_new = True
    elif current_iteration_id not in iteration_ids:
        iteration_ids.append(current_iteration_id)
    return current_iteration_id, iteration_ids, created_new


def _plan_status(execution_task_payload: dict[str, Any] | None, returned_result_payload: dict[str, Any] | None) -> str:
    if returned_result_payload is not None:
        return "returned"
    if execution_task_payload:
        return str(execution_task_payload.get("status") or "planned").strip() or "planned"
    return "draft"


def _synthesis_decision(
    *,
    returned_result_payload: dict[str, Any] | None,
    promotion_readiness: dict[str, Any],
) -> tuple[str, str, str]:
    if returned_result_payload is None:
        return ("pending", "pending_l4_return", "none")

    result_status = str(returned_result_payload.get("status") or "").strip().lower()
    if result_status in {"success", "passed", "complete", "completed", "ready"}:
        return ("summarized", "ready_for_staging_review", "review_for_staging")
    if result_status == "partial":
        return ("summarized", "continue_iteration", "defer")
    if str(promotion_readiness.get("status") or "").strip().lower() == "ready":
        return ("summarized", "ready_for_staging_review", "review_for_staging")
    return ("summarized", "blocked", "none")


def _maybe_stage_iteration_result(
    service: Any,
    *,
    topic_slug: str,
    run_id: str,
    iteration_id: str,
    updated_by: str,
    selected_action_id: str,
    selected_action_summary: str,
    returned_result_payload: dict[str, Any] | None,
    returned_result_ref: str,
    validation_review_bundle_path: str,
    synthesis_summary: str,
    next_step_summary: str,
    journal_paths: dict[str, Path],
    current_paths: dict[str, Path],
) -> dict[str, Any]:
    if returned_result_payload is None:
        return {}

    title = f"{topic_slug} {run_id} {iteration_id} provisional iteration result"
    source_artifact_paths = service._dedupe_strings(
        [
            returned_result_ref,
            service._relativize(current_paths["plan_note"]),
            service._relativize(current_paths["return_note"]),
            service._relativize(current_paths["synthesis_note"]),
            service._relativize(journal_paths["journal_note"]),
            validation_review_bundle_path,
        ]
    )
    notes_lines = [
        f"Run id: {run_id}",
        f"Iteration id: {iteration_id}",
        f"Selected action id: {selected_action_id or '(missing)'}",
        f"Selected action summary: {selected_action_summary or '(missing)'}",
        f"Returned result id: {str(returned_result_payload.get('result_id') or '').strip() or '(missing)'}",
        f"Returned result status: {str(returned_result_payload.get('status') or '').strip() or '(missing)'}",
        "",
        "Synthesis summary:",
        synthesis_summary or "(missing)",
        "",
        "Next step summary:",
        next_step_summary or "(missing)",
    ]
    staged = stage_provisional_l2_entry(
        service.kernel_root,
        topic_slug=topic_slug,
        entry_kind="iteration_result",
        title=title,
        summary=synthesis_summary or str(returned_result_payload.get("summary") or "").strip() or title,
        source_artifact_paths=source_artifact_paths,
        notes="\n".join(notes_lines).strip(),
        staged_by=updated_by,
    )
    entry = dict(staged["entry"])
    return {
        "entry_id": str(entry.get("entry_id") or ""),
        "topic_slug": str(entry.get("topic_slug") or ""),
        "entry_kind": str(entry.get("entry_kind") or ""),
        "status": str(entry.get("status") or ""),
        "title": str(entry.get("title") or ""),
        "summary": str(entry.get("summary") or ""),
        "path": str(entry.get("path") or ""),
        "note_path": str(entry.get("note_path") or ""),
        "workspace_staging_manifest_path": service._relativize(Path(staged["manifest_json_path"])),
        "workspace_staging_manifest_note_path": service._relativize(Path(staged["manifest_markdown_path"])),
    }


def _reuse_unit_ids(context: dict[str, Any] | None) -> list[str]:
    if not context:
        return []
    ids: list[str] = []
    seen: set[str] = set()
    for key in ("canonical_hits", "staged_hits"):
        for row in context.get(key) or []:
            unit_id = str(row.get("id") or "").strip()
            if unit_id and unit_id not in seen:
                seen.add(unit_id)
                ids.append(unit_id)
    return ids


def _canonical_unit_paths_by_id(service: Any) -> dict[str, Path]:
    index_path = service.kernel_root / "canonical" / "index.jsonl"
    mapping: dict[str, Path] = {}
    if not index_path.exists():
        return mapping
    for raw_line in index_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        row = json.loads(line)
        unit_id = str(row.get("id") or row.get("unit_id") or "").strip()
        path_ref = str(row.get("path") or "").strip()
        if unit_id and path_ref:
            mapping[unit_id] = service.kernel_root.joinpath(*path_ref.split("/"))
    return mapping


def _record_canonical_reuse_receipts(
    service: Any,
    *,
    receipt_refs: list[str] | str,
    idea_reuse_context: dict[str, Any] | None,
    plan_reuse_context: dict[str, Any] | None,
    unit_ids: list[str] | None = None,
) -> None:
    normalized_receipt_refs = [
        str(item).strip()
        for item in (
            [receipt_refs] if isinstance(receipt_refs, str) else list(receipt_refs or [])
        )
        if str(item).strip()
    ]
    if not normalized_receipt_refs:
        return
    touched = False
    seen_paths: set[str] = set()
    canonical_paths_by_id = _canonical_unit_paths_by_id(service)

    def _visit_path(unit_path: Path) -> None:
        nonlocal touched
        payload = _read_json(unit_path)
        if payload is None:
            return
        reuse_receipts = [str(item).strip() for item in (payload.get("reuse_receipts") or []) if str(item).strip()]
        updated_receipts = [*reuse_receipts]
        for receipt_ref in normalized_receipt_refs:
            if receipt_ref not in updated_receipts:
                updated_receipts.append(receipt_ref)
        if updated_receipts == reuse_receipts:
            return
        payload["reuse_receipts"] = updated_receipts
        _write_json(unit_path, payload)
        touched = True

    for context in (idea_reuse_context or {}, plan_reuse_context or {}):
        for row in context.get("canonical_hits") or []:
            path_ref = str(row.get("path") or "").strip()
            if not path_ref or path_ref in seen_paths:
                continue
            seen_paths.add(path_ref)
            _visit_path(service.kernel_root.joinpath(*path_ref.split("/")))
    for unit_id in unit_ids or []:
        normalized_unit_id = str(unit_id or "").strip()
        unit_path = canonical_paths_by_id.get(normalized_unit_id)
        if unit_path is None:
            continue
        path_ref = service._relativize(unit_path)
        if path_ref in seen_paths:
            continue
        seen_paths.add(path_ref)
        _visit_path(unit_path)
    if touched:
        materialize_canonical_index(service.kernel_root)


def _render_plan_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Iteration Plan",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Run id: `{payload.get('run_id') or '(missing)'}`",
        f"- Iteration id: `{payload.get('iteration_id') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Selected action id: `{payload.get('selected_action_id') or '(missing)'}`",
        f"- Selected action type: `{payload.get('selected_action_type') or '(missing)'}`",
        f"- Assigned runtime: `{payload.get('assigned_runtime') or '(missing)'}`",
        f"- Executor kind: `{payload.get('executor_kind') or '(missing)'}`",
        f"- Surface: `{payload.get('surface') or '(missing)'}`",
        f"- Execution task: `{payload.get('execution_task_path') or '(missing)'}`",
        f"- Resource context: `{payload.get('resource_context_path') or '(missing)'}`",
        f"- Idea reuse context: `{payload.get('idea_reuse_context_path') or '(missing)'}`",
        f"- Plan reuse context: `{payload.get('plan_reuse_context_path') or '(missing)'}`",
        f"- Server ref: `{payload.get('server_ref') or '(none)'}`",
        f"- Environment ref: `{payload.get('environment_ref') or '(none)'}`",
        "",
        "## Objective",
        "",
        f"- {payload.get('selected_action_summary') or payload.get('verification_focus') or '(missing)'}",
        "",
        "## Machine-facing validation inputs",
        "",
        f"- Research contract: `{payload.get('research_question_contract_path') or '(missing)'}`",
        f"- Validation contract: `{payload.get('validation_contract_path') or '(missing)'}`",
        f"- Validation review bundle: `{payload.get('validation_review_bundle_path') or '(missing)'}`",
        "",
        "## Execution details",
        "",
        f"- Where to run: `{payload.get('where_to_run') or '(missing)'}`",
        f"- Reasoning profile: `{payload.get('reasoning_profile') or '(missing)'}`",
        "",
        "## Reuse basis",
        "",
        f"- Idea reuse note: `{payload.get('idea_reuse_note_path') or '(missing)'}`",
        f"- Plan reuse note: `{payload.get('plan_reuse_note_path') or '(missing)'}`",
        "",
        "### Idea-basis unit ids",
        "",
    ]
    for item in payload.get("idea_reuse_unit_ids") or []:
        lines.append(f"- `{item}`")
    if not (payload.get("idea_reuse_unit_ids") or []):
        lines.append("- `(none declared)`")
    lines.extend(["", "### Plan-basis unit ids", ""])
    for item in payload.get("plan_reuse_unit_ids") or []:
        lines.append(f"- `{item}`")
    if not (payload.get("plan_reuse_unit_ids") or []):
        lines.append("- `(none declared)`")
    lines.extend(["", "### Reuse supporting refs", ""])
    for item in payload.get("reuse_supporting_refs") or []:
        lines.append(f"- `{item}`")
    if not (payload.get("reuse_supporting_refs") or []):
        lines.append("- `(none declared)`")
    lines.extend([
        "",
        "## Allowed input artifacts",
        "",
    ])
    for item in payload.get("allowed_input_artifacts") or []:
        lines.append(f"- `{item}`")
    if not (payload.get("allowed_input_artifacts") or []):
        lines.append("- `(none declared)`")
    lines.extend(["", "## Planned outputs", ""])
    for item in payload.get("planned_outputs") or []:
        lines.append(f"- `{item}`")
    if not (payload.get("planned_outputs") or []):
        lines.append("- `(none declared)`")
    lines.extend(["", "## Pass conditions", ""])
    for item in payload.get("pass_conditions") or []:
        lines.append(f"- {item}")
    if not (payload.get("pass_conditions") or []):
        lines.append("- `(none declared)`")
    lines.extend(["", "## Failure signals", ""])
    for item in payload.get("failure_signals") or []:
        lines.append(f"- {item}")
    if not (payload.get("failure_signals") or []):
        lines.append("- `(none declared)`")
    lines.extend(["", "## Reproducibility requirements", ""])
    for item in payload.get("reproducibility_requirements") or []:
        lines.append(f"- {item}")
    if not (payload.get("reproducibility_requirements") or []):
        lines.append("- `(none declared)`")
    lines.extend(["", "## Tool refs", ""])
    for item in payload.get("tool_refs") or []:
        lines.append(f"- `{item}`")
    if not (payload.get("tool_refs") or []):
        lines.append("- `(none declared)`")
    lines.append("")
    return "\n".join(lines)


def _render_l4_return_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# L4 Return",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Run id: `{payload.get('run_id') or '(missing)'}`",
        f"- Iteration id: `{payload.get('iteration_id') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Execution task: `{payload.get('execution_task_path') or '(missing)'}`",
        f"- Validation review bundle: `{payload.get('validation_review_bundle_path') or '(missing)'}`",
        f"- Returned execution result: `{payload.get('returned_execution_result_path') or '(missing)'}`",
        "",
        "## Result summary",
        "",
        f"- Result status: `{payload.get('returned_result_status') or 'pending'}`",
        f"- Result id: `{payload.get('returned_result_id') or '(missing)'}`",
        "",
        payload.get("returned_result_summary") or "Await the first durable L4 return artifact for this iteration.",
        "",
    ]
    return "\n".join(lines)


def _render_l3_synthesis_markdown(payload: dict[str, Any]) -> str:
    staging_entry = payload.get("staging_entry") or {}
    lines = [
        "# L3 Synthesis",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Run id: `{payload.get('run_id') or '(missing)'}`",
        f"- Iteration id: `{payload.get('iteration_id') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Conclusion status: `{payload.get('conclusion_status') or '(missing)'}`",
        f"- Staging decision: `{payload.get('staging_decision') or '(missing)'}`",
        f"- Promotion readiness: `{payload.get('promotion_readiness_status') or '(missing)'}`",
        f"- Staging entry: `{staging_entry.get('entry_id') or '(none)'}`",
        "",
        "## Synthesis summary",
        "",
        payload.get("synthesis_summary") or "(missing)",
        "",
        "## Next step",
        "",
        payload.get("next_step_summary") or "(missing)",
        "",
    ]
    if staging_entry:
        lines.extend(
            [
                "## Provisional staging",
                "",
                f"- Entry id: `{staging_entry.get('entry_id') or '(missing)'}`",
                f"- Entry note: `{staging_entry.get('note_path') or '(missing)'}`",
                f"- Workspace staging manifest: `{payload.get('workspace_staging_manifest_path') or '(missing)'}`",
                "",
            ]
        )
    return "\n".join(lines)


def _render_iteration_journal_markdown(payload: dict[str, Any]) -> str:
    latest_staging_entry = payload.get("latest_staging_entry") or {}
    lines = [
        "# Iteration Journal",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Run id: `{payload.get('run_id') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Current iteration: `{payload.get('current_iteration_id') or '(missing)'}`",
        f"- Latest conclusion: `{payload.get('latest_conclusion_status') or '(missing)'}`",
        f"- Latest staging decision: `{payload.get('latest_staging_decision') or '(missing)'}`",
        f"- Latest staged entry: `{latest_staging_entry.get('entry_id') or '(none)'}`",
        "",
        "## Iterations",
        "",
    ]
    for row in payload.get("iterations") or []:
        lines.extend(
            [
                f"- `{row.get('iteration_id') or '(missing)'}`",
                f"  - plan: `{row.get('plan_note_path') or '(missing)'}`",
                f"  - L4 return: `{row.get('l4_return_note_path') or '(missing)'}`",
                f"  - L3 synthesis: `{row.get('l3_synthesis_note_path') or '(missing)'}`",
                f"  - conclusion: `{row.get('conclusion_status') or '(missing)'}`",
                f"  - staged entry: `{row.get('staging_entry_note_path') or '(none)'}`",
            ]
        )
    if not (payload.get("iterations") or []):
        lines.append("- `(none)`")
    lines.extend(
        [
            "",
            "## Current pointers",
            "",
            f"- Current plan contract: `{(payload.get('latest_paths') or {}).get('current_plan_path') or '(missing)'}`",
            f"- Current L4 return: `{(payload.get('latest_paths') or {}).get('current_return_path') or '(missing)'}`",
            f"- Current L3 synthesis: `{(payload.get('latest_paths') or {}).get('current_synthesis_path') or '(missing)'}`",
            f"- Workspace staging manifest: `{payload.get('workspace_staging_manifest_path') or '(missing)'}`",
            "",
        ]
    )
    return "\n".join(lines)


def materialize_iteration_journal(
    service: Any,
    *,
    topic_slug: str,
    run_id: str | None,
    updated_by: str,
    topic_state: dict[str, Any],
    selected_pending_action: dict[str, Any] | None,
    research_contract: dict[str, Any],
    validation_contract: dict[str, Any],
    validation_review_bundle: dict[str, Any],
    promotion_readiness: dict[str, Any],
    idea_reuse_context: dict[str, Any] | None = None,
    plan_reuse_context: dict[str, Any] | None = None,
    execution_resource_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not run_id:
        return {}

    selected_action_id = str((selected_pending_action or {}).get("action_id") or "").strip()
    selected_action_type = str((selected_pending_action or {}).get("action_type") or "").strip()
    selected_action_summary = str((selected_pending_action or {}).get("summary") or "").strip()

    execution_task_path = _resolve_execution_task_path(
        service,
        topic_slug=topic_slug,
        run_id=run_id,
        selected_action_id=selected_action_id,
    )
    execution_task_ref = service._relativize(execution_task_path) if execution_task_path else ""
    execution_task_payload = _read_json(execution_task_path) if execution_task_path else None
    returned_result_path = _resolve_returned_result_path(
        service,
        topic_slug=topic_slug,
        run_id=run_id,
        topic_state=topic_state,
    )
    returned_result_ref = service._relativize(returned_result_path) if returned_result_path else ""
    returned_result_payload = _read_json(returned_result_path) if returned_result_path else None

    current_iteration_id, iteration_ids, created_new = _current_iteration_id(
        service,
        topic_slug=topic_slug,
        run_id=run_id,
        selected_action_id=selected_action_id,
        execution_task_ref=execution_task_ref,
    )
    journal_paths = iteration_journal_paths(service, topic_slug=topic_slug, run_id=run_id)
    current_paths = iteration_paths(
        service,
        topic_slug=topic_slug,
        run_id=run_id,
        iteration_id=current_iteration_id,
    )
    existing_current_plan = _read_json(current_paths["plan_json"]) or {}
    existing_current_plan_execution_task_path = str(existing_current_plan.get("execution_task_path") or "").strip()
    plan_is_newer_than_return = bool(
        returned_result_path is not None
        and returned_result_path.exists()
        and current_paths["plan_json"].exists()
        and current_paths["plan_json"].stat().st_mtime > returned_result_path.stat().st_mtime
    )
    stale_return_for_current = bool(
        returned_result_payload is not None
        and (
            (
                execution_task_ref
                and existing_current_plan_execution_task_path
                and execution_task_ref != existing_current_plan_execution_task_path
            )
            or plan_is_newer_than_return
        )
    )
    if created_new or stale_return_for_current:
        returned_result_ref = ""
        returned_result_payload = None

    idea_reuse_unit_ids = _reuse_unit_ids(idea_reuse_context)
    plan_reuse_unit_ids = _reuse_unit_ids(plan_reuse_context)
    plan_payload = {
        "contract_version": 1,
        "topic_slug": topic_slug,
        "run_id": run_id,
        "iteration_id": current_iteration_id,
        "status": _plan_status(execution_task_payload, returned_result_payload),
        "selected_action_id": selected_action_id,
        "selected_action_type": selected_action_type,
        "selected_action_summary": selected_action_summary,
        "verification_focus": str(validation_contract.get("verification_focus") or "").strip(),
        "research_question_contract_path": service._relativize(service._research_question_contract_paths(topic_slug)["note"]),
        "validation_contract_path": service._relativize(service._validation_contract_paths(topic_slug)["note"]),
        "validation_review_bundle_path": str(validation_review_bundle.get("note_path") or ""),
        "execution_task_path": execution_task_ref,
        "assigned_runtime": str((execution_task_payload or {}).get("assigned_runtime") or "codex"),
        "executor_kind": str((execution_task_payload or {}).get("executor_kind") or "codex_cli"),
        "surface": str((execution_task_payload or {}).get("surface") or "human_review"),
        "reasoning_profile": str((execution_task_payload or {}).get("reasoning_profile") or ""),
        "where_to_run": str((execution_task_payload or {}).get("where_to_run") or service.kernel_root.name),
        "resource_context_path": str((execution_resource_context or {}).get("path") or ""),
        "idea_reuse_context_path": str((idea_reuse_context or {}).get("path") or ""),
        "idea_reuse_note_path": str((idea_reuse_context or {}).get("note_path") or ""),
        "idea_reuse_unit_ids": idea_reuse_unit_ids,
        "plan_reuse_context_path": str((plan_reuse_context or {}).get("path") or ""),
        "plan_reuse_note_path": str((plan_reuse_context or {}).get("note_path") or ""),
        "plan_reuse_unit_ids": plan_reuse_unit_ids,
        "reuse_supporting_refs": list(
            dict.fromkeys(
                [
                    str(item).strip()
                    for item in (
                        list((idea_reuse_context or {}).get("supporting_refs") or [])
                        + list((plan_reuse_context or {}).get("supporting_refs") or [])
                    )
                    if str(item).strip()
                ]
            )
        ),
        "server_ref": str((execution_resource_context or {}).get("recommended_server", {}).get("capability_id") or ""),
        "environment_ref": str((execution_resource_context or {}).get("recommended_environment", {}).get("capability_id") or ""),
        "tool_refs": list((execution_resource_context or {}).get("recommended_tool_ids") or []),
        "allowed_input_artifacts": list((execution_task_payload or {}).get("allowed_input_artifacts") or []),
        "planned_outputs": list((execution_task_payload or {}).get("planned_outputs") or []),
        "pass_conditions": list((execution_task_payload or {}).get("pass_conditions") or validation_contract.get("required_checks") or []),
        "failure_signals": list((execution_task_payload or {}).get("failure_signals") or validation_contract.get("failure_modes") or []),
        "reproducibility_requirements": list((execution_task_payload or {}).get("reproducibility_requirements") or []),
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }
    _write_json(current_paths["plan_json"], plan_payload)
    _write_text(current_paths["plan_note"], _render_plan_markdown(plan_payload) + "\n")
    _record_canonical_reuse_receipts(
        service,
        receipt_refs=service._relativize(current_paths["plan_json"]),
        idea_reuse_context=idea_reuse_context,
        plan_reuse_context=plan_reuse_context,
    )

    l4_return_payload = {
        "contract_version": 1,
        "topic_slug": topic_slug,
        "run_id": run_id,
        "iteration_id": current_iteration_id,
        "status": "returned" if returned_result_payload is not None else "pending",
        "execution_task_path": execution_task_ref,
        "validation_review_bundle_path": str(validation_review_bundle.get("note_path") or ""),
        "returned_execution_result_path": returned_result_ref,
        "returned_result_id": str((returned_result_payload or {}).get("result_id") or ""),
        "returned_result_status": str((returned_result_payload or {}).get("status") or ""),
        "returned_result_summary": str((returned_result_payload or {}).get("summary") or ""),
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }
    _write_json(current_paths["return_json"], l4_return_payload)
    _write_text(current_paths["return_note"], _render_l4_return_markdown(l4_return_payload) + "\n")

    synthesis_status, conclusion_status, staging_decision = _synthesis_decision(
        returned_result_payload=returned_result_payload,
        promotion_readiness=promotion_readiness,
    )
    if returned_result_payload is None:
        synthesis_summary = "Await the first durable L4 return before summarizing this iteration."
        next_step_summary = "Do not stage or conclude the run yet. Wait for the returned execution artifact."
    elif conclusion_status == "ready_for_staging_review":
        synthesis_summary = "The current returned result is strong enough to review for provisional staging."
        next_step_summary = "Review the returned result and candidate state for honest provisional staging or promotion routing."
    elif conclusion_status == "continue_iteration":
        synthesis_summary = str((returned_result_payload or {}).get("summary") or "").strip() or "The current return is partial and still leaves bounded work open."
        next_step_summary = "Plan another bounded L3 iteration before attempting staging."
    else:
        synthesis_summary = str((returned_result_payload or {}).get("summary") or "").strip() or "The current return does not justify immediate staging."
        next_step_summary = "Resolve the blocking validation issues before another staging or promotion decision."

    staging_entry: dict[str, Any] = {}
    workspace_staging_manifest_path = ""
    workspace_staging_manifest_note_path = ""
    if conclusion_status == "ready_for_staging_review":
        staging_entry = _maybe_stage_iteration_result(
            service,
            topic_slug=topic_slug,
            run_id=run_id,
            iteration_id=current_iteration_id,
            updated_by=updated_by,
            selected_action_id=selected_action_id,
            selected_action_summary=selected_action_summary,
            returned_result_payload=returned_result_payload,
            returned_result_ref=returned_result_ref,
            validation_review_bundle_path=str(validation_review_bundle.get("note_path") or ""),
            synthesis_summary=synthesis_summary,
            next_step_summary=next_step_summary,
            journal_paths=journal_paths,
            current_paths=current_paths,
        )
        if staging_entry:
            staging_decision = "staged_provisionally"
            workspace_staging_manifest_path = str(staging_entry.get("workspace_staging_manifest_path") or "")
            workspace_staging_manifest_note_path = str(staging_entry.get("workspace_staging_manifest_note_path") or "")

    synthesis_payload = {
        "contract_version": 1,
        "topic_slug": topic_slug,
        "run_id": run_id,
        "iteration_id": current_iteration_id,
        "status": synthesis_status,
        "conclusion_status": conclusion_status,
        "staging_decision": staging_decision,
        "promotion_readiness_status": str(promotion_readiness.get("status") or ""),
        "returned_execution_result_path": returned_result_ref,
        "validation_review_bundle_path": str(validation_review_bundle.get("note_path") or ""),
        "synthesis_summary": synthesis_summary,
        "next_step_summary": next_step_summary,
        "staging_entry": {
            key: value
            for key, value in staging_entry.items()
            if key not in {"workspace_staging_manifest_path", "workspace_staging_manifest_note_path"}
        },
        "workspace_staging_manifest_path": workspace_staging_manifest_path,
        "workspace_staging_manifest_note_path": workspace_staging_manifest_note_path,
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }
    _write_json(current_paths["synthesis_json"], synthesis_payload)
    _write_text(current_paths["synthesis_note"], _render_l3_synthesis_markdown(synthesis_payload) + "\n")
    if staging_entry:
        _record_canonical_reuse_receipts(
            service,
            receipt_refs=[
                service._relativize(current_paths["synthesis_json"]),
                str(staging_entry.get("path") or "").strip(),
                workspace_staging_manifest_path,
            ],
            idea_reuse_context=idea_reuse_context,
            plan_reuse_context=plan_reuse_context,
            unit_ids=[
                str(item).strip()
                for item in (
                    list(existing_current_plan.get("idea_reuse_unit_ids") or [])
                    + list(existing_current_plan.get("plan_reuse_unit_ids") or [])
                )
                if str(item).strip()
            ],
        )

    iterations: list[dict[str, Any]] = []
    for iteration_id in iteration_ids:
        paths = iteration_paths(service, topic_slug=topic_slug, run_id=run_id, iteration_id=iteration_id)
        synth = _read_json(paths["synthesis_json"]) or {}
        iterations.append(
            {
                "iteration_id": iteration_id,
                "plan_note_path": service._relativize(paths["plan_note"]),
                "l4_return_note_path": service._relativize(paths["return_note"]),
                "l3_synthesis_note_path": service._relativize(paths["synthesis_note"]),
                "conclusion_status": str(synth.get("conclusion_status") or ""),
                "staging_entry_id": str(((synth.get("staging_entry") or {}).get("entry_id")) or ""),
                "staging_entry_note_path": str(((synth.get("staging_entry") or {}).get("note_path")) or ""),
            }
        )

    journal_payload = {
        "contract_version": 1,
        "topic_slug": topic_slug,
        "run_id": run_id,
        "status": "awaiting_human_review" if conclusion_status == "ready_for_staging_review" else "iterating",
        "current_iteration_id": current_iteration_id,
        "iteration_ids": iteration_ids,
        "latest_conclusion_status": conclusion_status,
        "latest_staging_decision": staging_decision,
        "latest_staging_entry": synthesis_payload.get("staging_entry") or {},
        "workspace_staging_manifest_path": workspace_staging_manifest_path,
        "workspace_staging_manifest_note_path": workspace_staging_manifest_note_path,
        "iterations": iterations,
        "latest_paths": {
            "journal_note_path": service._relativize(journal_paths["journal_note"]),
            "current_plan_path": service._relativize(current_paths["plan_json"]),
            "current_return_path": service._relativize(current_paths["return_json"]),
            "current_synthesis_path": service._relativize(current_paths["synthesis_json"]),
        },
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }
    _write_json(journal_paths["journal_json"], journal_payload)
    _write_text(journal_paths["journal_note"], _render_iteration_journal_markdown(journal_payload) + "\n")
    try:
        from .research_notebook_support import append_notebook_entry
        l3_root = service._l3_root(topic_slug)
        append_notebook_entry(
            l3_root,
            kind="iteration_journal",
            title=f"Iteration {current_iteration_id}",
            status=str(conclusion_status or "in_progress"),
            run_id=run_id or "",
            body=str(journal_payload.get("latest_staging_entry", {}).get("summary") or ""),
            details={
                "iteration_id": current_iteration_id,
                "total_iterations": len(iteration_ids),
                "staging_decision": str(staging_decision or ""),
            },
        )
    except Exception:
        pass
    return {
        **journal_payload,
        "path": service._relativize(journal_paths["journal_json"]),
        "note_path": service._relativize(journal_paths["journal_note"]),
    }
