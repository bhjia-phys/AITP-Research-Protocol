"""Batch checkpoint support for low-interruption research bursts."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from brain.v5.closeout_completeness import build_record_completeness_audit
from brain.v5.ids import prefixed_id
from brain.v5.models import QuietCheckpointBatchRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.recovery_session import recover_session_binding_for_read
from brain.v5.research_state import attach_artifact
from brain.v5.run_iterations import record_run_iteration
from brain.v5.sensemaking import record_sensemaking_report
from brain.v5.source_assets import register_source_asset, source_asset_payload
from brain.v5.store import write_record
from brain.v5.tools import record_tool_run


def preview_quiet_checkpoint_batch(
    ws: WorkspacePaths,
    session_id: str,
    *,
    claim_id: str = "",
    run_id: str = "",
    summary: str,
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    changed_files: list[str] | None = None,
    generated_artifacts: list[dict[str, Any]] | None = None,
    validation_commands: list[str] | None = None,
    durable_observations: list[str] | None = None,
    claim_boundary: dict[str, Any] | None = None,
    next_blockers: list[str] | None = None,
    artifact_specs: list[dict[str, Any]] | None = None,
    source_specs: list[dict[str, Any]] | None = None,
    tool_run_specs: list[dict[str, Any]] | None = None,
    sensemaking_summary: str = "",
    source_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Preview a checkpoint batch without writing records."""

    focus = _focus(ws, session_id, claim_id=claim_id)
    checkpoint_id = _checkpoint_id(focus["topic_id"], session_id, summary)
    run_id = run_id or checkpoint_id
    artifact_specs = _dict_list(artifact_specs)
    source_specs = _dict_list(source_specs)
    tool_run_specs = _dict_list(tool_run_specs)
    planned = _planned_writes(
        checkpoint_id=checkpoint_id,
        run_id=run_id,
        artifact_specs=artifact_specs,
        source_specs=source_specs,
        tool_run_specs=tool_run_specs,
        sensemaking_summary=sensemaking_summary,
    )
    inputs_list = _str_list(inputs)
    outputs_list = _str_list(outputs)
    changed_files_list = _str_list(changed_files)
    generated_artifacts_list = artifact_specs or _dict_list(generated_artifacts)
    audit_generated_artifacts_list = _dict_list(generated_artifacts)
    if artifact_specs:
        audit_generated_artifacts_list = artifact_specs + audit_generated_artifacts_list
    else:
        audit_generated_artifacts_list = generated_artifacts_list
    validation_commands_list = _str_list(validation_commands)
    durable_observations_list = _str_list(durable_observations)
    claim_boundary_map = claim_boundary or {}
    next_blockers_list = _str_list(next_blockers)
    source_refs_list = _str_list(source_refs)
    audit = build_record_completeness_audit(
        topic_id=focus["topic_id"],
        claim_id=focus["claim_id"],
        run_id=run_id,
        summary=summary,
        inputs=inputs_list,
        outputs=outputs_list,
        changed_files=changed_files_list,
        generated_artifacts=audit_generated_artifacts_list,
        validation_commands=validation_commands_list,
        claim_boundary=claim_boundary_map,
        next_blockers=next_blockers_list,
        artifact_specs=artifact_specs,
        source_specs=source_specs,
        tool_run_specs=tool_run_specs,
        planned_typed_writes=planned,
        closeout_surface="quiet_checkpoint",
        write_executed=False,
    )
    return {
        "ok": True,
        "kind": "quiet_checkpoint_preview",
        "checkpoint_id": checkpoint_id,
        "topic_id": focus["topic_id"],
        "session_id": focus["session_id"],
        "requested_session_id": focus["requested_session_id"],
        "claim_id": focus["claim_id"],
        "run_id": run_id,
        "summary": summary,
        "inputs": inputs_list,
        "outputs": outputs_list,
        "changed_files": changed_files_list,
        "generated_artifacts": generated_artifacts_list,
        "validation_commands": validation_commands_list,
        "durable_observations": durable_observations_list,
        "claim_boundary": claim_boundary_map,
        "next_blockers": next_blockers_list,
        "planned_typed_writes": planned,
        "source_refs": source_refs_list,
        "record_completeness_audit": audit,
        "status": "preview_only",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def apply_quiet_checkpoint_batch(
    ws: WorkspacePaths,
    session_id: str,
    *,
    claim_id: str = "",
    run_id: str = "",
    summary: str,
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    changed_files: list[str] | None = None,
    generated_artifacts: list[dict[str, Any]] | None = None,
    validation_commands: list[str] | None = None,
    durable_observations: list[str] | None = None,
    claim_boundary: dict[str, Any] | None = None,
    next_blockers: list[str] | None = None,
    artifact_specs: list[dict[str, Any]] | None = None,
    source_specs: list[dict[str, Any]] | None = None,
    tool_run_specs: list[dict[str, Any]] | None = None,
    sensemaking_summary: str = "",
    source_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Apply a checkpoint batch through existing typed write functions."""

    preview = preview_quiet_checkpoint_batch(
        ws,
        session_id,
        claim_id=claim_id,
        run_id=run_id,
        summary=summary,
        inputs=inputs,
        outputs=outputs,
        changed_files=changed_files,
        generated_artifacts=generated_artifacts,
        validation_commands=validation_commands,
        durable_observations=durable_observations,
        claim_boundary=claim_boundary,
        next_blockers=next_blockers,
        artifact_specs=artifact_specs,
        source_specs=source_specs,
        tool_run_specs=tool_run_specs,
        sensemaking_summary=sensemaking_summary,
        source_refs=source_refs,
    )
    written_refs: list[str] = []
    topic_id = preview["topic_id"]
    focus_claim_id = preview["claim_id"]
    checkpoint_id = preview["checkpoint_id"]
    run_id = preview["run_id"]
    all_source_refs = list(preview["source_refs"])

    record_run_iteration(
        ws,
        topic_id=topic_id,
        run_id=run_id,
        iteration_id=checkpoint_id,
        plan_summary=summary,
        deliverables=preview["outputs"] + preview["changed_files"] + [str(item.get("uri") or item.get("path") or "") for item in preview["generated_artifacts"]],
        checks=preview["validation_commands"],
        stop_rules=_checkpoint_stop_rules(preview["claim_boundary"], preview["next_blockers"]),
        l4_return_summary="Quiet checkpoint batch recorded without trust promotion.",
        l3_synthesis_summary="; ".join(preview["durable_observations"]),
        decision="Preserve research burst as typed records; use evidence/validation/trust gates separately.",
        status="synthesized",
        claim_id=focus_claim_id,
        source_refs=all_source_refs,
    )

    for spec in _dict_list(artifact_specs):
        artifact = attach_artifact(
            ws,
            topic_id=topic_id,
            claim_id=focus_claim_id,
            artifact_type=str(spec.get("artifact_type") or spec.get("type") or "generated_artifact"),
            uri=str(spec.get("uri") or spec.get("path") or ""),
            summary=str(spec.get("summary") or summary),
            size_bytes=int(spec.get("size_bytes") or 0),
            metadata=_dict(spec.get("metadata")),
        )
        written_refs.append(f"artifact:{artifact.artifact_id}")

    for spec in _dict_list(source_specs):
        asset = register_source_asset(
            ws,
            topic_id=topic_id,
            claim_id=focus_claim_id,
            asset_type=str(spec.get("asset_type") or spec.get("type") or "note"),
            uri=str(spec.get("uri") or ""),
            title=str(spec.get("title") or spec.get("label") or "quiet checkpoint source"),
            label=str(spec.get("label") or ""),
            source_kind=str(spec.get("source_kind") or "quiet_checkpoint"),
            summary=str(spec.get("summary") or summary),
            source_refs=_str_list(spec.get("source_refs")) + all_source_refs,
            artifact_ids=_str_list(spec.get("artifact_ids")),
            code_state_ids=_str_list(spec.get("code_state_ids")),
            reference_location_ids=_str_list(spec.get("reference_location_ids")),
            derived_from=_str_list(spec.get("derived_from")),
            metadata=_dict(spec.get("metadata")),
            linked_records=_dict(spec.get("linked_records")),
        )
        payload = source_asset_payload(asset)
        written_refs.append(f"source_asset:{payload['asset_id']}")

    for spec in _dict_list(tool_run_specs):
        run = record_tool_run(
            ws,
            recipe_id=str(spec.get("recipe_id") or "quiet-checkpoint-tool-run"),
            tool_family=str(spec.get("tool_family") or spec.get("family") or "research_burst"),
            tool_name=str(spec.get("tool_name") or spec.get("name") or "quiet_checkpoint"),
            topic_id=topic_id,
            claim_id=focus_claim_id,
            inputs=_dict(spec.get("inputs")),
            outputs=_dict(spec.get("outputs")),
            environment=_dict(spec.get("environment")),
            evidence_status=str(spec.get("evidence_status") or "unreviewed"),
            code_state_ids=_str_list(spec.get("code_state_ids")),
            artifact_ids=_str_list(spec.get("artifact_ids")),
            source_refs=_str_list(spec.get("source_refs")) + all_source_refs,
        )
        written_refs.append(f"tool_run:{run.run_id}")

    if sensemaking_summary:
        report = record_sensemaking_report(
            ws,
            topic_id=topic_id,
            claim_id=focus_claim_id,
            title=f"Quiet checkpoint synthesis: {checkpoint_id}",
            summary=sensemaking_summary,
            open_questions=preview["next_blockers"],
            next_actions=["route evidence/validation/trust updates through explicit gates"],
        )
        written_refs.append(f"sensemaking_report:{report.report_id}")

    written_refs.append(f"quiet_checkpoint:{checkpoint_id}")
    audit_generated_artifacts = list(preview["generated_artifacts"])
    for item in _dict_list(generated_artifacts):
        if item not in audit_generated_artifacts:
            audit_generated_artifacts.append(item)
    audit = build_record_completeness_audit(
        topic_id=topic_id,
        claim_id=focus_claim_id,
        run_id=run_id,
        summary=summary,
        inputs=preview["inputs"],
        outputs=preview["outputs"],
        changed_files=preview["changed_files"],
        generated_artifacts=audit_generated_artifacts,
        validation_commands=preview["validation_commands"],
        claim_boundary=preview["claim_boundary"],
        next_blockers=preview["next_blockers"],
        artifact_specs=_dict_list(artifact_specs),
        source_specs=_dict_list(source_specs),
        tool_run_specs=_dict_list(tool_run_specs),
        written_refs=written_refs,
        planned_typed_writes=preview["planned_typed_writes"],
        closeout_surface="quiet_checkpoint",
        write_executed=True,
    )
    record = QuietCheckpointBatchRecord(
        checkpoint_id=checkpoint_id,
        topic_id=topic_id,
        session_id=preview["session_id"],
        claim_id=focus_claim_id,
        run_id=run_id,
        summary=summary,
        inputs=preview["inputs"],
        outputs=preview["outputs"],
        changed_files=preview["changed_files"],
        generated_artifacts=preview["generated_artifacts"],
        validation_commands=preview["validation_commands"],
        durable_observations=preview["durable_observations"],
        claim_boundary=preview["claim_boundary"],
        next_blockers=preview["next_blockers"],
        planned_typed_writes=preview["planned_typed_writes"],
        written_refs=written_refs,
        source_refs=all_source_refs,
        record_completeness_audit=audit,
    )
    write_record(
        ws.registry_dir("quiet_checkpoints") / f"{checkpoint_id}.md",
        record,
        body=_checkpoint_body(record),
    )
    return {"ok": True, **asdict(record)}


def _focus(ws: WorkspacePaths, session_id: str, *, claim_id: str) -> dict[str, str]:
    recovered = recover_session_binding_for_read(ws, session_id)
    session = recovered.session
    return {
        "requested_session_id": recovered.requested_session_id,
        "session_id": session.session_id,
        "topic_id": session.topic_id,
        "claim_id": claim_id or session.active_claim,
    }


def _checkpoint_id(topic_id: str, session_id: str, summary: str) -> str:
    return prefixed_id("quiet-checkpoint", f"{topic_id}:{session_id}:{summary}", max_slug=80)


def _planned_writes(
    *,
    checkpoint_id: str,
    run_id: str,
    artifact_specs: list[dict[str, Any]],
    source_specs: list[dict[str, Any]],
    tool_run_specs: list[dict[str, Any]],
    sensemaking_summary: str,
) -> list[dict[str, Any]]:
    planned = [
        {
            "record_type": "run_iteration_record",
            "action": "record_run_iteration",
            "reason": "preserve burst-level plan/checks/observations",
            "expected_ref": f"run_iteration:{run_id}:{checkpoint_id}",
        },
        {
            "record_type": "quiet_checkpoint_batch",
            "action": "record_quiet_checkpoint_batch",
            "reason": "preserve batch envelope and written refs",
            "expected_ref": f"quiet_checkpoint:{checkpoint_id}",
        },
    ]
    planned.extend(
        {
            "record_type": "artifact_record",
            "action": "attach_artifact",
            "reason": "capture generated artifact pointer",
            "expected_uri": str(spec.get("uri") or spec.get("path") or ""),
        }
        for spec in artifact_specs
    )
    planned.extend(
        {
            "record_type": "source_asset_record",
            "action": "register_source_asset",
            "reason": "capture source/provenance asset",
            "expected_uri": str(spec.get("uri") or ""),
        }
        for spec in source_specs
    )
    planned.extend(
        {
            "record_type": "tool_run_record",
            "action": "record_tool_run",
            "reason": "capture command or validation transcript as unreviewed tool run",
            "expected_tool": str(spec.get("tool_name") or spec.get("name") or "quiet_checkpoint"),
        }
        for spec in tool_run_specs
    )
    if sensemaking_summary:
        planned.append(
            {
                "record_type": "sensemaking_report_record",
                "action": "record_sensemaking_report",
                "reason": "capture burst synthesis without validation authority",
                "expected_ref": "sensemaking_report:<generated>",
            }
        )
    return planned


def _checkpoint_stop_rules(claim_boundary: dict[str, Any], next_blockers: list[str]) -> list[str]:
    stop_rules = _str_list(claim_boundary.get("cannot_say")) + _str_list(claim_boundary.get("non_claims"))
    stop_rules.extend(next_blockers)
    return stop_rules


def _checkpoint_body(record: QuietCheckpointBatchRecord) -> str:
    observations = "\n".join(f"- {item}" for item in record.durable_observations) or "- None"
    blockers = "\n".join(f"- {item}" for item in record.next_blockers) or "- None"
    refs = "\n".join(f"- {item}" for item in record.written_refs) or "- None"
    audit = record.record_completeness_audit or {}
    missing = "\n".join(f"- {item}" for item in audit.get("missing_recommended_slots", [])) or "- None"
    audit_summary = str(audit.get("summary") or "No completeness audit recorded.")
    return (
        f"# Quiet Checkpoint {record.checkpoint_id}\n\n"
        f"{record.summary}\n\n"
        "## Durable Observations\n\n"
        f"{observations}\n\n"
        "## Next Blockers\n\n"
        f"{blockers}\n\n"
        "## Written Refs\n\n"
        f"{refs}\n\n"
        "## Record Completeness Audit\n\n"
        f"{audit_summary}\n\n"
        "### Missing Recommended Slots\n\n"
        f"{missing}\n"
    )


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _dict_list(values: Any) -> list[dict[str, Any]]:
    if not values:
        return []
    return [dict(value) for value in values if isinstance(value, dict)]


def _str_list(values: Any) -> list[str]:
    if not values:
        return []
    if isinstance(values, str):
        values = [values]
    return [str(value).strip() for value in values if str(value).strip()]
