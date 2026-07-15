"""Normalize exact local or remote collector manifests into reviewable prefill."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any, Mapping

from brain.v5.compute_run_intake_contracts import (
    ComputeRunIntakeReport,
    ComputeRunIntakeRequest,
)
from brain.v5.execution_contracts import redact_execution_payload


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_TERMINAL_STATUSES = {"completed", "failed", "cancelled"}
_KNOWN_STATUSES = _TERMINAL_STATUSES | {"pending", "submitted", "running"}
_KNOWN_LANES = {"diagnostic", "exploratory", "final"}


def build_compute_run_intake(request: ComputeRunIntakeRequest) -> ComputeRunIntakeReport:
    """Build typed prefill candidates without reading remote state or writing records."""

    redaction = redact_execution_payload(request.manifest)
    manifest = redaction.payload
    source = _mapping(manifest.get("source"))
    source_uri = str(source.get("uri") or "")
    if source.get("accessible") is False:
        return ComputeRunIntakeReport(
            status="inaccessible",
            coverage="missing",
            source_uri=source_uri,
            checked_fields=tuple(_present_fields(manifest)),
            missing_fields=("source.content",),
            redacted_fields=tuple(redaction.redacted_paths),
            errors=("collector source URI was not accessible",),
        )

    collector = _mapping(manifest.get("collector"))
    run = _mapping(manifest.get("run"))
    scheduler = _mapping(run.get("scheduler"))
    executable = _mapping(run.get("executable"))
    code = _mapping(run.get("code"))
    status = str(run.get("status") or "").lower()

    required = [
        "schema_version",
        "source.kind",
        "source.uri",
        "collector.id",
        "collector.version",
        "collector.captured_at",
        "run.run_id",
        "run.tool_family",
        "run.tool_name",
        "run.status",
        "run.lane",
        "run.cwd",
        "run.code.commit_sha",
        "run.code.content_hash",
        "run.executable.path",
        "run.executable.sha256",
        "run.input_manifest",
        "run.resources",
    ]
    if str(source.get("kind") or "") == "remote" or scheduler:
        required.extend(("run.scheduler.kind", "run.scheduler.job_id"))
    if status in _TERMINAL_STATUSES or status == "running":
        required.extend(("run.completed_at", "run.exit_status", "run.output_manifest"))

    missing = tuple(sorted(path for path in required if not _has_value(manifest, path)))
    invalid = tuple(sorted(_invalid_fields(manifest)))
    errors = tuple(f"invalid collector field: {path}" for path in invalid)
    candidates = _build_candidates(
        source=source,
        collector=collector,
        run=run,
        scheduler=scheduler,
        executable=executable,
        code=code,
    )
    report_status = _report_status(status, missing, invalid)
    coverage = "complete" if not missing and not invalid else "partial"
    return ComputeRunIntakeReport(
        status=report_status,
        coverage=coverage,
        source_uri=source_uri,
        checked_fields=tuple(_present_fields(manifest)),
        missing_fields=missing,
        invalid_fields=invalid,
        redacted_fields=tuple(redaction.redacted_paths),
        errors=errors,
        candidates=candidates,
    )


def _build_candidates(
    *,
    source: Mapping[str, Any],
    collector: Mapping[str, Any],
    run: Mapping[str, Any],
    scheduler: Mapping[str, Any],
    executable: Mapping[str, Any],
    code: Mapping[str, Any],
) -> dict[str, Any]:
    run_id = str(run.get("run_id") or "")
    source_uri = str(source.get("uri") or "")
    captured_at = str(collector.get("captured_at") or "")
    executable_path = str(executable.get("path") or "")
    executable_hash = str(executable.get("sha256") or "")
    output_manifest = _list_of_mappings(run.get("output_manifest"))
    status = str(run.get("status") or "").lower()
    scheduler_job_id = str(scheduler.get("job_id") or "")

    tool_run = {
        "run_id": run_id,
        "topic_id": str(run.get("topic_id") or ""),
        "claim_id": str(run.get("claim_id") or ""),
        "recipe_id": str(run.get("recipe_id") or ""),
        "tool_family": str(run.get("tool_family") or ""),
        "tool_name": str(run.get("tool_name") or ""),
        "inputs": {"source_uri": source_uri},
        "outputs": {"collector_status": status},
        "environment": dict(_mapping(run.get("environment"))),
        "evidence_status": _evidence_status(status),
        "lane": str(run.get("lane") or "diagnostic"),
        "argv": list(run.get("argv") or []) if isinstance(run.get("argv"), list) else [],
        "cwd": str(run.get("cwd") or ""),
        "input_manifest": _list_of_mappings(run.get("input_manifest")),
        "output_manifest": output_manifest,
        "scheduler": dict(scheduler),
        "job_id": scheduler_job_id,
        "submitted_at": str(run.get("submitted_at") or ""),
        "started_at": str(run.get("started_at") or ""),
        "completed_at": str(run.get("completed_at") or ""),
        "exit_status": dict(_mapping(run.get("exit_status"))),
        "recorded_maturity": "diagnostic",
        "non_claims": [
            "collector status and scheduler metadata are process observations, not scientific evidence"
        ],
        "collector_provenance": {
            "id": str(collector.get("id") or ""),
            "version": str(collector.get("version") or ""),
            "captured_at": captured_at,
        },
    }
    artifacts = [
        {
            "artifact_id": _candidate_id("artifact", run_id, str(item.get("path") or "")),
            "topic_id": str(run.get("topic_id") or ""),
            "claim_id": str(run.get("claim_id") or ""),
            "artifact_type": str(item.get("role") or "compute_output"),
            "uri": str(item.get("uri") or _join_uri(source_uri, str(item.get("path") or ""))),
            "summary": "collector-discovered output; review required before canonical write",
            "size_bytes": _safe_nonnegative_int(item.get("size_bytes")),
            "content_hash": str(item.get("sha256") or ""),
            "hash_algorithm": "sha256" if item.get("sha256") else "",
            "captured_at": captured_at,
            "role": str(item.get("role") or "compute_output"),
            "storage_mode": "reference_only",
        }
        for item in output_manifest
    ]
    executable_hashes = (
        {executable_path: executable_hash}
        if executable_path and _SHA256.fullmatch(executable_hash)
        else {}
    )
    environment = {
        "environment_id": _candidate_id("environment", run_id, captured_at),
        "host": str(source.get("host") or ""),
        "cluster": str(source.get("cluster") or ""),
        "created_at": captured_at,
        "executable_paths": [executable_path] if executable_path else [],
        "executable_hashes": executable_hashes,
        "redacted_environment": dict(_mapping(run.get("environment"))),
        "code_identity": {
            "repo": str(code.get("repo") or ""),
            "commit_sha": str(code.get("commit_sha") or ""),
            "content_hash": str(code.get("content_hash") or ""),
        },
    }
    monitor = {
        "snapshot_id": _candidate_id("monitor", run_id, captured_at),
        "topic_id": str(run.get("topic_id") or ""),
        "claim_id": str(run.get("claim_id") or ""),
        "tool_run_id": run_id,
        "run_dir": str(run.get("cwd") or ""),
        "job_id": scheduler_job_id,
        "scheduler_state": {"status": status, **dict(scheduler)},
        "collector_id": str(collector.get("id") or ""),
        "collector_version": str(collector.get("version") or ""),
        "captured_at": captured_at,
        "remote_uri": source_uri if source.get("kind") == "remote" else "",
        "resource_usage": dict(_mapping(run.get("resources"))),
        "immutable": True,
        "orientation_only": True,
        "can_update_claim_trust": False,
    }
    validation_checklist = {
        "candidate_id": _candidate_id("validation-checklist", run_id, captured_at),
        "tool_run_id": run_id,
        "status": "not_checked",
        "required_checks": [
            "verify output bytes against the collector manifest",
            "apply an explicit validation contract",
            "review lane and applicability before any baseline acceptance",
        ],
        "creates_validation_result": False,
        "can_update_claim_trust": False,
    }
    return {
        "tool_run": tool_run,
        "artifacts": artifacts,
        "monitor_snapshot": monitor,
        "execution_environment": environment,
        "validation_checklist": validation_checklist,
    }


def _invalid_fields(manifest: Mapping[str, Any]) -> list[str]:
    fields: list[str] = []
    for path in ("source", "collector", "run"):
        value = _get(manifest, path)
        if value not in (None, "") and not isinstance(value, Mapping):
            fields.append(path)
    for path in (
        "run.code",
        "run.executable",
        "run.resources",
        "run.scheduler",
        "run.exit_status",
        "run.environment",
    ):
        value = _get(manifest, path)
        if value not in (None, "") and not isinstance(value, Mapping):
            fields.append(path)
    argv = _get(manifest, "run.argv")
    if argv not in (None, "") and not isinstance(argv, list):
        fields.append("run.argv")
    if manifest.get("schema_version") not in (None, "", "compute-run-collector/v1"):
        fields.append("schema_version")
    source_kind = _get(manifest, "source.kind")
    if source_kind and source_kind not in {"local", "remote"}:
        fields.append("source.kind")
    captured_at = _get(manifest, "collector.captured_at")
    if captured_at and not _timezone_timestamp(captured_at):
        fields.append("collector.captured_at")
    status = _get(manifest, "run.status")
    if status and str(status).lower() not in _KNOWN_STATUSES:
        fields.append("run.status")
    lane = _get(manifest, "run.lane")
    if lane and lane not in _KNOWN_LANES:
        fields.append("run.lane")
    checks = {
        "run.code.commit_sha": _COMMIT,
        "run.code.content_hash": _SHA256,
        "run.executable.sha256": _SHA256,
    }
    for path, pattern in checks.items():
        value = _get(manifest, path)
        if value and not pattern.fullmatch(str(value)):
            fields.append(path)
    for prefix in ("run.input_manifest", "run.output_manifest"):
        values = _get(manifest, prefix)
        if values not in (None, "") and not isinstance(values, list):
            fields.append(prefix)
            continue
        if isinstance(values, list):
            for index, item in enumerate(values):
                if not isinstance(item, Mapping):
                    fields.append(f"{prefix}[{index}]")
                    continue
                digest = item.get("sha256")
                if digest and not _SHA256.fullmatch(str(digest)):
                    fields.append(f"{prefix}[{index}].sha256")
                size = item.get("size_bytes")
                if size not in (None, "") and _safe_nonnegative_int(size, invalid=-1) < 0:
                    fields.append(f"{prefix}[{index}].size_bytes")
    return fields


def _timezone_timestamp(value: Any) -> bool:
    try:
        return datetime.fromisoformat(str(value)).tzinfo is not None
    except ValueError:
        return False


def _present_fields(manifest: Mapping[str, Any]) -> list[str]:
    paths: list[str] = []

    def visit(value: Any, prefix: str) -> None:
        if isinstance(value, Mapping):
            for key in sorted(value, key=str):
                visit(value[key], f"{prefix}.{key}" if prefix else str(key))
        elif isinstance(value, list):
            if value:
                paths.append(prefix)
        elif value not in (None, "", False):
            paths.append(prefix)

    visit(manifest, "")
    return sorted(paths)


def _report_status(status: str, missing: tuple[str, ...], invalid: tuple[str, ...]) -> str:
    if status in {"failed", "cancelled"}:
        return "failed"
    if status == "running" or missing or invalid:
        return "partial"
    return "complete"


def _evidence_status(status: str) -> str:
    return {
        "completed": "unreviewed",
        "running": "running",
        "pending": "submitted_pending",
        "submitted": "submitted_pending",
        "failed": "failed_runtime",
        "cancelled": "cancelled",
    }.get(status, "unreviewed")


def _has_value(manifest: Mapping[str, Any], path: str) -> bool:
    value = _get(manifest, path)
    return value not in (None, "", [], {})


def _get(manifest: Mapping[str, Any], path: str) -> Any:
    value: Any = manifest
    for part in path.split("."):
        if not isinstance(value, Mapping):
            return None
        value = value.get(part)
    return value


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    normalized = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        entry = dict(item)
        digest = str(entry.get("sha256") or "")
        entry["sha256"] = digest if _SHA256.fullmatch(digest) else ""
        if "size_bytes" in entry:
            entry["size_bytes"] = _safe_nonnegative_int(entry.get("size_bytes"))
        normalized.append(entry)
    return normalized


def _safe_nonnegative_int(value: Any, *, invalid: int = 0) -> int:
    try:
        result = int(value or 0)
    except (TypeError, ValueError):
        return invalid
    return result if result >= 0 else invalid


def _candidate_id(kind: str, *parts: str) -> str:
    digest = hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"{kind}-prefill-{digest}"


def _join_uri(root: str, path: str) -> str:
    return f"{root.rstrip('/')}/{path.lstrip('/') or ''}" if root else path
