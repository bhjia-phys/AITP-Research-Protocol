"""Tool recipe and tool-run records for AITP v5."""

from __future__ import annotations

import hashlib
import mimetypes
from contextlib import nullcontext
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dataclasses import asdict

from brain.v5.models import ToolRecipeRecord, ToolRunRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository
from brain.v5.tool_run_transitions import (
    create_or_merge_tool_run as _create_or_merge_tool_run,
    merge_tool_run_links as _merge_tool_run_links,
    require_acyclic_supersession as _require_acyclic_supersession,
    require_available_successor as _require_available_successor,
    select_tool_run_id as _select_tool_run_id,
    tool_run_identity as _tool_run_identity,
    tool_run_revision_basis as _tool_run_revision_basis,
    tool_run_v1_id as _tool_run_v1_id,
)


_TOOL_RUN_LANES = frozenset({"final", "diagnostic", "exploratory"})


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
    _repository(ws, actor_id="register_tool_recipe").write(
        "tool_recipes",
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
    attempts of one scientific run. ``supersedes`` becomes an immutable,
    hash-protected forward edge on the new attempt. The prior attempt is never
    patched; read models derive the reverse edge. ``lane`` marks the run
    ``final``/``diagnostic``/``exploratory`` and defaults to ``diagnostic`` so
    an unmarked run can never be mistaken for final evidence.
    """

    if lane not in _TOOL_RUN_LANES:
        raise ValueError(f"lane must be one of {sorted(_TOOL_RUN_LANES)}")
    repository = _repository(ws, actor_id="record_tool_run")
    transition_lock = (
        repository.lock_record("tool_runs", supersedes)
        if supersedes
        else nullcontext()
    )
    with transition_lock:
        effective_scientific_run_id = scientific_run_id
        legacy_v1_candidates: list[str] = []
        if supersedes:
            old_record, _, _ = _tool_run_revision_basis(repository, supersedes)
            if old_record.topic_id != topic_id or old_record.claim_id != claim_id:
                raise ValueError(
                    "superseding tool runs must belong to the same topic and claim"
                )
            if (
                scientific_run_id
                and old_record.scientific_run_id
                and scientific_run_id != old_record.scientific_run_id
            ):
                raise ValueError(
                    "superseding tool run scientific_run_id must match the prior run"
                )
            if not effective_scientific_run_id:
                effective_scientific_run_id = old_record.scientific_run_id

        v1_run_id = _tool_run_v1_id(
            recipe_id=recipe_id,
            tool_family=tool_family,
            tool_name=tool_name,
            topic_id=topic_id,
            claim_id=claim_id,
            inputs=inputs or {},
            outputs=outputs or {},
            environment=environment or {},
            evidence_status=evidence_status,
            source_refs=source_refs or [],
            scientific_run_id=effective_scientific_run_id,
            supersedes_run_id=supersedes,
            lane=lane,
        )
        if supersedes and effective_scientific_run_id:
            legacy_v1_candidates.append(
                _tool_run_v1_id(
                    recipe_id=recipe_id,
                    tool_family=tool_family,
                    tool_name=tool_name,
                    topic_id=topic_id,
                    claim_id=claim_id,
                    inputs=inputs or {},
                    outputs=outputs or {},
                    environment=environment or {},
                    evidence_status=evidence_status,
                    source_refs=source_refs or [],
                    scientific_run_id="",
                    supersedes_run_id=supersedes,
                    lane=lane,
                )
            )

        identity = _tool_run_identity(
            recipe_id=recipe_id,
            tool_family=tool_family,
            tool_name=tool_name,
            topic_id=topic_id,
            claim_id=claim_id,
            inputs=inputs or {},
            outputs=outputs or {},
            environment=environment or {},
            evidence_status=evidence_status,
            source_refs=source_refs or [],
            scientific_run_id=effective_scientific_run_id,
            supersedes_run_id=supersedes,
            lane=lane,
        )
        run_id = _select_tool_run_id(
            repository,
            v1_run_id=v1_run_id,
            identity=identity,
            legacy_v1_candidates=legacy_v1_candidates,
        )
        if supersedes:
            _require_acyclic_supersession(
                repository,
                supersedes,
                run_id,
                topic_id=topic_id,
                claim_id=claim_id,
                scientific_run_id=effective_scientific_run_id,
            )
            _require_available_successor(repository, supersedes, run_id)

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
            scientific_run_id=effective_scientific_run_id,
            supersedes_run_id=supersedes,
            lane=lane,
        )
        record = _create_or_merge_tool_run(
            repository,
            record,
            body=f"# Tool Run\n\nRecipe: `{recipe_id}`\n\nTool: `{tool_family}:{tool_name}`\n",
        )
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

    repository = _repository(ws, actor_id="link_code_state_to_run")
    return _merge_tool_run_links(
        repository,
        run_id=run_id,
        code_state_ids=[code_state_id],
    )


def link_artifact_to_run(
    ws: WorkspacePaths, *, run_id: str, artifact_id: str
) -> ToolRunRecord:
    """Back-link an artifact/source_asset id to an existing tool run (idempotent)."""

    repository = _repository(ws, actor_id="link_artifact_to_run")
    return _merge_tool_run_links(
        repository,
        run_id=run_id,
        artifact_ids=[artifact_id],
    )


def tool_run_payload(
    record: ToolRunRecord,
    *,
    include_ok: bool = True,
) -> dict[str, Any]:
    payload = asdict(record)
    # One-release public compatibility alias. Canonical records use only the
    # unambiguous forward-edge field and never persist this legacy string key.
    payload["supersedes"] = record.supersedes_run_id
    return {"ok": True, **payload} if include_ok else payload


def _repository(ws: WorkspacePaths, *, actor_id: str) -> RecordRepository:
    return RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id=actor_id, host="aitp"),
    )


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
