"""Strict v2 writers for recipes and reproducible tool runs."""

from __future__ import annotations

from dataclasses import replace

from brain.v5.execution_contracts import RedactionPolicy, redact_execution_payload
from brain.v5.execution_scope_policy import assess_execution_scope
from brain.v5.models import (
    CodePatchManifestRecord,
    CodeStateRecord,
    ExecutionEnvironmentRecord,
    ToolRecipeRecord,
    ToolRunRecord,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository, WritePolicy, WriteResult


_RUN_MATURITIES = {"diagnostic", "reproducible_candidate", "superseded"}


def record_code_state_v2(
    ws: WorkspacePaths,
    record: CodeStateRecord,
    *,
    actor: RecordActor,
    strict_reproducibility: bool = True,
) -> WriteResult:
    if not record.upstream_commit or (
        strict_reproducibility and len(record.upstream_commit) != 40
    ):
        raise ValueError("code state requires an exact 40-character commit")
    if record.dirty and strict_reproducibility:
        if not (record.patch_manifest_ref and record.patch_manifest_hash and record.patch_manifest_revision):
            raise ValueError("dirty v2 code state requires an exact patch manifest")
        patch = get_record_version(
            ws,
            PinnedRecordRef(
                record.patch_manifest_ref,
                record.patch_manifest_hash,
                record.patch_manifest_revision,
            ),
        ).record
        if not isinstance(patch, CodePatchManifestRecord) or not patch.coverage_complete:
            raise ValueError("dirty v2 code state patch manifest is incomplete")
    return RecordRepository(ws, actor=actor).write(
        "code_states",
        record,
        body=f"# Code State\n\nRepository: `{record.repo_id}`\n\nCommit: `{record.upstream_commit}`\n",
    )


def record_tool_recipe_compat(
    ws: WorkspacePaths,
    record: ToolRecipeRecord,
    *,
    actor: RecordActor,
) -> WriteResult:
    return RecordRepository(ws, actor=actor).write(
        "tool_recipes",
        record,
        body=f"# Tool Recipe\n\n{record.purpose}\n",
    )


def write_tool_run_compat(
    repository: RecordRepository,
    record: ToolRunRecord,
    *,
    body: str,
    policy: WritePolicy | None = None,
) -> WriteResult:
    """Compatibility persistence seam used by legacy identity transitions."""

    return repository.write("tool_runs", record, body=body, policy=policy)


def record_tool_recipe_v2(
    ws: WorkspacePaths,
    record: ToolRecipeRecord,
    *,
    actor: RecordActor,
) -> WriteResult:
    if not record.recipe_id or not record.tool_family or not record.tool_name:
        raise ValueError("v2 tool recipe identity fields must be non-empty")
    if not record.recipe_version or record.recipe_version == "v1-compat":
        raise ValueError("v2 tool recipe requires an explicit recipe version")
    return RecordRepository(ws, actor=actor).write(
        "tool_recipes",
        record,
        body=f"# Tool Recipe\n\n{record.purpose}\n",
    )


def record_tool_run_v2(
    ws: WorkspacePaths,
    record: ToolRunRecord,
    *,
    actor: RecordActor,
    redaction_policy: RedactionPolicy | None = None,
) -> WriteResult:
    if record.recorded_maturity == "accepted_baseline":
        raise ValueError("accepted_baseline may only be projected by an execution baseline")
    if record.recorded_maturity not in _RUN_MATURITIES:
        raise ValueError("unsupported ToolRun recorded_maturity")
    pins = _core_pins(record)
    if record.recorded_maturity == "reproducible_candidate":
        _validate_reproducible_core(ws, record, pins)
    redaction = redact_execution_payload(
        {"argv": record.argv, "environment": record.environment},
        redaction_policy,
    )
    stored = replace(
        record,
        argv=redaction.payload["argv"],
        environment=redaction.payload["environment"],
    )
    return RecordRepository(ws, actor=actor).write(
        "tool_runs",
        stored,
        body=(
            "# Tool Run\n\n"
            f"Recipe: `{stored.recipe_id}`\n\n"
            f"Maturity: `{stored.recorded_maturity}`\n"
        ),
    )


def _core_pins(record: ToolRunRecord) -> tuple[PinnedRecordRef, ...]:
    fields = (
        ("recipe", record.recipe_ref, record.recipe_hash, record.recipe_revision),
        ("code state", record.code_state_ref, record.code_state_hash, record.code_state_revision),
        ("environment", record.environment_ref, record.environment_hash, record.environment_revision),
    )
    pins = []
    for label, ref, content_hash, revision in fields:
        if not ref or not content_hash or not revision:
            if record.recorded_maturity == "reproducible_candidate":
                raise ValueError(f"reproducible candidate requires exact {label} ref")
            continue
        pins.append(PinnedRecordRef(ref, content_hash, revision))
    return tuple(pins)


def _validate_reproducible_core(
    ws: WorkspacePaths,
    record: ToolRunRecord,
    pins: tuple[PinnedRecordRef, ...],
) -> None:
    versions = [get_record_version(ws, pin).record for pin in pins]
    if not isinstance(versions[0], ToolRecipeRecord):
        raise ValueError("exact recipe ref does not resolve to a tool recipe")
    if versions[0].recipe_id != record.recipe_id:
        raise ValueError("exact recipe ref does not match run recipe_id")
    if not isinstance(versions[1], CodeStateRecord):
        raise ValueError("exact code state ref does not resolve to a code state")
    if not isinstance(versions[2], ExecutionEnvironmentRecord):
        raise ValueError("exact environment ref does not resolve to an execution environment")
    scope = assess_execution_scope(
        ws,
        operation="record_tool_run_v2",
        consumer_scope=(f"topic:{record.topic_id}", f"claim:{record.claim_id}"),
        dependency_refs=pins,
    )
    if scope.decision != "allowed":
        raise ValueError(f"tool run dependency scope is not allowed: {scope.decision}")
