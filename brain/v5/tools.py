"""Tool recipe and tool-run records for AITP v5."""

from __future__ import annotations

import hashlib
import mimetypes
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dataclasses import asdict

from brain.v5.ids import prefixed_id, short_hash
from brain.v5.markdown import read_md
from brain.v5.models import ToolRecipeRecord, ToolRunRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import read_record, write_record


def register_tool_recipe(
    ws: WorkspacePaths,
    *,
    recipe_id: str,
    tool_family: str,
    tool_name: str,
    purpose: str,
    required_inputs: list[str] | None = None,
    expected_outputs: list[str] | None = None,
    invariants: list[str] | None = None,
) -> ToolRecipeRecord:
    """Register a reusable recipe for a formal, numerical, code, or domain tool."""

    record = ToolRecipeRecord(
        recipe_id=recipe_id,
        tool_family=tool_family,
        tool_name=tool_name,
        purpose=purpose,
        required_inputs=required_inputs or [],
        expected_outputs=expected_outputs or [],
        invariants=invariants or [],
    )
    write_record(
        ws.registry_dir("tool_recipes") / f"{recipe_id}.md",
        record,
        body=f"# Tool Recipe\n\n{purpose}\n",
    )
    return record


def record_tool_run(
    ws: WorkspacePaths,
    *,
    recipe_id: str,
    tool_family: str,
    tool_name: str,
    topic_id: str,
    claim_id: str,
    inputs: dict | None = None,
    outputs: dict | None = None,
    environment: dict | None = None,
    evidence_status: str = "unreviewed",
    code_state_ids: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    source_refs: list[str] | None = None,
    scientific_run_id: str = "",
    supersedes: str = "",
    lane: str = "diagnostic",
) -> ToolRunRecord:
    """Record one tool execution as auditable evidence input.

    HPC job attempts reuse this same record. ``scientific_run_id`` groups the
    attempts of one scientific run; ``supersedes`` points at the prior attempt
    being replaced and back-fills that record's ``superseded_by``; ``lane``
    marks the run ``final``/``diagnostic``/``exploratory`` and defaults to
    ``diagnostic`` so an unmarked run can never be mistaken for final evidence.
    """

    run_basis = ":".join(
        [
            recipe_id,
            tool_family,
            tool_name,
            topic_id,
            claim_id,
            short_hash(str(inputs or {}), 8),
            short_hash(str(outputs or {}), 8),
        ]
    )
    run_id = prefixed_id("tool-run", run_basis, max_slug=72)

    inherited_run_id = scientific_run_id
    backfill: tuple[Path, ToolRunRecord, str] | None = None
    if supersedes:
        old_path = ws.registry_dir("tool_runs") / f"{supersedes}.md"
        if not old_path.exists():
            raise ValueError(f"superseded tool run not found: {supersedes}")
        old_record = read_record(old_path, ToolRunRecord)
        _, old_body = read_md(old_path)
        old_record.superseded_by = run_id
        backfill = (old_path, old_record, old_body)
        if not inherited_run_id and old_record.scientific_run_id:
            inherited_run_id = old_record.scientific_run_id

    record = ToolRunRecord(
        run_id=run_id,
        recipe_id=recipe_id,
        tool_family=tool_family,
        tool_name=tool_name,
        topic_id=topic_id,
        claim_id=claim_id,
        inputs=inputs or {},
        outputs=outputs or {},
        environment=environment or {},
        evidence_status=evidence_status,
        code_state_ids=code_state_ids or [],
        artifact_ids=artifact_ids or [],
        source_refs=source_refs or [],
        scientific_run_id=inherited_run_id,
        supersedes=supersedes,
        lane=lane,
    )
    write_record(
        ws.registry_dir("tool_runs") / f"{run_id}.md",
        record,
        body=f"# Tool Run\n\nRecipe: `{recipe_id}`\n\nTool: `{tool_family}:{tool_name}`\n",
    )
    if backfill is not None:
        old_path, old_record, old_body = backfill
        write_record(old_path, old_record, body=old_body)
    return record


def capture_tool_run_from_local_path(
    ws: WorkspacePaths,
    *,
    path: str,
    recipe_id: str,
    tool_family: str,
    tool_name: str,
    topic_id: str,
    claim_id: str,
    inputs: dict[str, Any] | None = None,
    outputs: dict[str, Any] | None = None,
    environment: dict[str, Any] | None = None,
    evidence_status: str = "unreviewed",
    code_state_ids: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    source_refs: list[str] | None = None,
    scientific_run_id: str = "",
    supersedes: str = "",
    lane: str = "diagnostic",
    summary: str = "",
    max_preview_chars: int = 1200,
) -> ToolRunRecord:
    """Inspect a local transcript/result file and record tool-run provenance."""

    local_path = Path(path).expanduser()
    if not local_path.exists():
        raise FileNotFoundError(f"tool-run transcript path does not exist: {path}")
    if not local_path.is_file():
        raise ValueError(f"tool-run transcript path must be a file: {path}")

    resolved = local_path.resolve()
    stat = resolved.stat()
    captured_at = datetime.now(UTC).isoformat()
    mtime_utc = datetime.fromtimestamp(stat.st_mtime, UTC).isoformat()
    content_hash = _sha256(resolved)
    mime_type, _ = mimetypes.guess_type(str(resolved))
    preview = _text_preview(resolved, max_preview_chars=max_preview_chars)

    enriched_outputs = dict(outputs or {})
    enriched_outputs.setdefault("transcript_uri", f"file://{resolved}")
    enriched_outputs.setdefault("transcript_sha256", content_hash)
    enriched_outputs.setdefault("transcript_hash_algorithm", "sha256")
    enriched_outputs.setdefault("transcript_size_bytes", stat.st_size)
    enriched_outputs.setdefault("transcript_mtime_utc", mtime_utc)
    enriched_outputs.setdefault("transcript_mime_type", mime_type or "")
    enriched_outputs.setdefault("transcript_preview", preview["preview"])
    enriched_outputs.setdefault("transcript_preview_truncated", preview["truncated"])
    if summary:
        enriched_outputs.setdefault("summary", summary)

    enriched_environment = dict(environment or {})
    enriched_environment.setdefault("capture_tool", "aitp_v5_capture_tool_run_auto")
    enriched_environment.setdefault("captured_at", captured_at)
    enriched_environment.setdefault("local_path", str(resolved))
    enriched_environment.setdefault("file_name", resolved.name)
    enriched_environment.setdefault("content_hash_basis", "local transcript/result file bytes")
    enriched_environment.setdefault("summary_inputs_trusted", False)
    enriched_environment.setdefault("can_update_claim_trust", False)

    run = record_tool_run(
        ws,
        recipe_id=recipe_id,
        tool_family=tool_family,
        tool_name=tool_name,
        topic_id=topic_id,
        claim_id=claim_id,
        inputs=inputs,
        outputs=enriched_outputs,
        environment=enriched_environment,
        evidence_status=evidence_status,
        code_state_ids=code_state_ids,
        artifact_ids=artifact_ids,
        source_refs=source_refs,
        scientific_run_id=scientific_run_id,
        supersedes=supersedes,
        lane=lane,
    )
    return run


def link_code_state_to_run(
    ws: WorkspacePaths, *, run_id: str, code_state_id: str
) -> ToolRunRecord:
    """Back-link a code_state to an existing tool run (idempotent).

    Fills the ``code_state_ids`` gap left when a run was recorded before its
    code provenance was resolved (the common case for HPC runs whose commit was
    only pinned later). Preserves the run body.
    """

    path = ws.registry_dir("tool_runs") / f"{run_id}.md"
    if not path.exists():
        raise ValueError(f"tool run not found: {run_id}")
    record = read_record(path, ToolRunRecord)
    if code_state_id in record.code_state_ids:
        return record
    _, body = read_md(path)
    record.code_state_ids = [*record.code_state_ids, code_state_id]
    write_record(path, record, body=body)
    return record


def link_artifact_to_run(
    ws: WorkspacePaths, *, run_id: str, artifact_id: str
) -> ToolRunRecord:
    """Back-link an artifact/source_asset id to an existing tool run (idempotent)."""

    path = ws.registry_dir("tool_runs") / f"{run_id}.md"
    if not path.exists():
        raise ValueError(f"tool run not found: {run_id}")
    record = read_record(path, ToolRunRecord)
    if artifact_id in record.artifact_ids:
        return record
    _, body = read_md(path)
    record.artifact_ids = [*record.artifact_ids, artifact_id]
    write_record(path, record, body=body)
    return record


def tool_run_payload(record: ToolRunRecord) -> dict[str, Any]:
    return {"ok": True, **asdict(record)}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _text_preview(path: Path, *, max_preview_chars: int) -> dict[str, Any]:
    limit = max(0, int(max_preview_chars or 0))
    if limit == 0:
        return {"preview": "", "truncated": path.stat().st_size > 0}
    read_limit = max(32, limit * 4 + 4)
    with path.open("rb") as handle:
        data = handle.read(read_limit)
    text = data.decode("utf-8", errors="replace")
    preview = text[:limit]
    truncated = path.stat().st_size > len(data) or len(text) > len(preview)
    return {"preview": preview, "truncated": truncated}
