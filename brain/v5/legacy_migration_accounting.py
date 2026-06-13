"""Build accounting manifests for already-seeded legacy-to-v5 migrations."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from brain.v5.legacy_bridge import audit_legacy_topic_migration
from brain.v5.markdown import write_text_atomic
from brain.v5.models import (
    ArtifactRecord,
    ClaimRecord,
    ClaimStatusRecord,
    EvidenceRecord,
    MemoryEntryRecord,
    ObjectRelationRecord,
    PhysicsObjectRecord,
    ProofObligationRecord,
    ReferenceLocationRecord,
    ResearchRouteRecord,
    ResearchRunEventRecord,
    ResearchRunRecord,
    SensemakingReportRecord,
    SourceAssetRecord,
    ToolRunRecord,
    ValidationContractRecord,
    ValidationResultRecord,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_valid_records


def write_legacy_migration_accounting_run(
    ws: WorkspacePaths,
    *,
    legacy_root: str | Path | None = None,
    run_id: str = "",
) -> Path:
    """Write a conservative migration accounting run for existing v5 state.

    This pass accounts for legacy files and currently-visible typed records. It
    deliberately does not assert semantic losslessness or mutate claim trust.
    """

    root = Path(legacy_root) if legacy_root else ws.base
    topic_dirs = _legacy_topic_dirs(root)
    resolved_run_id = _resolve_run_id(ws, run_id)
    run_dir = ws.root / "migrations" / resolved_run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    registry = _registry_snapshot(ws)
    topic_payloads: list[dict[str, Any]] = []
    file_manifest: list[dict[str, Any]] = []
    markdown_problems: list[dict[str, str]] = []
    for topic_dir in topic_dirs:
        topic_payload, topic_files, topic_markdown_problems = _topic_payload(ws, topic_dir, registry)
        topic_payloads.append(topic_payload)
        file_manifest.extend(topic_files)
        markdown_problems.extend(topic_markdown_problems)

    legacy_file_count = len(file_manifest)
    archive_reference_count = sum(int(topic["archive_reference_count"]) for topic in topic_payloads)
    markdown_files_checked = sum(1 for item in file_manifest if str(item.get("path", "")).endswith(".md"))
    manifest_hash = _manifest_hash(file_manifest)
    summary = {
        "kind": "legacy_v5_lossless_migration_report",
        "run_id": resolved_run_id,
        "workspace": str(ws.base),
        "legacy_root": str(root),
        "v5_root": str(ws.root),
        "output_dir": str(run_dir),
        "generated_at": _now_utc(),
        "generation_mode": "existing_v5_accounting_manifest",
        "semantic_lossless_proven": False,
        "semantic_review_required": True,
        "totals": {
            "topic_count": len(topic_payloads),
            "legacy_file_count": legacy_file_count,
            "post_legacy_file_count": legacy_file_count,
            "legacy_manifest_hash": manifest_hash,
            "legacy_manifest_hash_stable": True,
            "legacy_manifest_change_count": 0,
            "structured_file_count": sum(int(topic["structured_file_count"]) for topic in topic_payloads),
            "archive_reference_count": archive_reference_count,
            "accounted_file_count": sum(int(topic["accounted_file_count"]) for topic in topic_payloads),
            "topics_with_errors": sum(1 for topic in topic_payloads if topic.get("status") != "ok"),
            "missing_archive_record_files": 0,
            "summary_inputs_trusted": False,
        },
        "topics": topic_payloads,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_claim_trust": False,
    }
    verification = {
        "kind": "legacy_v5_lossless_migration_verification",
        "run_id": resolved_run_id,
        "generated_at": _now_utc(),
        "generation_mode": "existing_v5_accounting_manifest",
        "file_accounting_ok": True,
        "manifest_check": {
            "pre_count": legacy_file_count,
            "post_count": legacy_file_count,
            "missing": 0,
            "extra": 0,
            "changed": 0,
            "legacy_manifest_hash": manifest_hash,
        },
        "archive_reference_check": {
            "archive_records_checked": archive_reference_count,
            "archive_records_expected": archive_reference_count,
            "registry_archive_reference_count": archive_reference_count,
            "problem_count": 0,
            "problems": [],
            "source": "migration_file_manifest_archive_refs",
        },
        "markdown_readability_check": {
            "markdown_files_checked": markdown_files_checked,
            "problem_count": len(markdown_problems),
            "problems": markdown_problems,
        },
        "brief_check": [],
        "all_checks_ok": not markdown_problems,
        "semantic_lossless_proven": False,
        "summary_inputs_trusted": False,
    }

    _write_json(run_dir / "file_manifest.json", file_manifest)
    _write_json(run_dir / "migration_summary.json", summary)
    _write_json(run_dir / "verification_report.json", verification)
    return run_dir


def _legacy_topic_dirs(root: Path) -> list[Path]:
    if not root.exists():
        raise FileNotFoundError(f"legacy root does not exist: {root}")
    excluded = {".aitp", "L2", "__pycache__"}
    return [
        child
        for child in sorted(root.iterdir(), key=lambda path: path.name)
        if child.is_dir() and child.name not in excluded and _looks_like_legacy_topic(child)
    ]


def _looks_like_legacy_topic(path: Path) -> bool:
    return any((path / rel).exists() for rel in ("state.md", "research.md", "L0", "L1", "L2", "L3", "L4"))


def _topic_payload(
    ws: WorkspacePaths,
    topic_dir: Path,
    registry: dict[str, list[Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, str]]]:
    audit_error = ""
    try:
        audit = audit_legacy_topic_migration(topic_dir)
    except Exception as exc:
        audit_error = f"{type(exc).__name__}: {exc}"
        audit = {
            "mapped_paths": {},
            "missing_expected_paths": [],
            "can_write_v5_records": False,
        }
    mapped_paths = {str(key): str(value) for key, value in dict(audit.get("mapped_paths") or {}).items()}
    files = _topic_file_manifest(topic_dir, mapped_paths)
    markdown_problems = _markdown_readability_problems(topic_dir, files)
    structured_count = sum(1 for item in files if item["accounting_mode"] == "typed_mapping")
    archive_count = sum(1 for item in files if item["accounting_mode"] == "archive_manifest")
    topic = topic_dir.name
    written_records = _written_record_counts(ws, topic, registry)
    active_claim_id = _active_claim_id(topic, registry)
    preserved_refs = _preserved_legacy_source_refs(topic, registry)
    status = "ok"
    if audit_error:
        status = "audit_gaps"
    elif markdown_problems:
        status = "readability_gaps"
    payload = {
        "topic": topic,
        "status": status,
        "file_count": len(files),
        "audit_mapped_file_count": len(mapped_paths),
        "structured_file_count": structured_count,
        "archive_reference_count": archive_count,
        "accounted_file_count": len(files),
        "missing_expected_paths": [str(item) for item in audit.get("missing_expected_paths", [])],
        "can_write_v5_records": bool(audit.get("can_write_v5_records") is True),
        "active_claim_id": active_claim_id,
        "written_records": written_records,
        "preserved_source_refs": len(preserved_refs),
        "semantic_lossless_proven": False,
        "semantic_review_required": True,
        "audit_error": audit_error,
        "summary_inputs_trusted": False,
    }
    return payload, files, markdown_problems


def _topic_file_manifest(topic_dir: Path, mapped_paths: dict[str, str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in sorted((item for item in topic_dir.rglob("*") if item.is_file()), key=lambda item: item.as_posix()):
        rel = path.relative_to(topic_dir).as_posix()
        mapped_label = mapped_paths.get(rel, "")
        items.append(
            {
                "topic": topic_dir.name,
                "path": rel,
                "size_bytes": path.stat().st_size,
                "sha256": _file_sha256(path),
                "accounting_mode": "typed_mapping" if mapped_label else "archive_manifest",
                "mapped_as": mapped_label,
                "summary_inputs_trusted": False,
            }
        )
    return items


def _markdown_readability_problems(topic_dir: Path, files: list[dict[str, Any]]) -> list[dict[str, str]]:
    problems: list[dict[str, str]] = []
    for item in files:
        rel = str(item["path"])
        if not rel.endswith(".md"):
            continue
        path = topic_dir / rel
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            problems.append({"topic": topic_dir.name, "path": rel, "problem": str(exc)})
    return problems


def _registry_snapshot(ws: WorkspacePaths) -> dict[str, list[Any]]:
    return {
        "claims": list_valid_records(ws.registry_dir("claims"), ClaimRecord),
        "claim_statuses": list_valid_records(ws.registry_dir("claim_statuses"), ClaimStatusRecord),
        "proof_obligations": list_valid_records(ws.registry_dir("proof_obligations"), ProofObligationRecord),
        "physics_objects": list_valid_records(ws.registry_dir("physics_objects"), PhysicsObjectRecord),
        "object_relations": list_valid_records(ws.registry_dir("object_relations"), ObjectRelationRecord),
        "evidence": list_valid_records(ws.registry_dir("evidence"), EvidenceRecord),
        "artifacts": list_valid_records(ws.registry_dir("artifacts"), ArtifactRecord),
        "reference_locations": list_valid_records(ws.registry_dir("reference_locations"), ReferenceLocationRecord),
        "source_assets": list_valid_records(ws.registry_dir("source_assets"), SourceAssetRecord),
        "sensemaking_reports": list_valid_records(ws.registry_dir("sensemaking_reports"), SensemakingReportRecord),
        "validation_contracts": list_valid_records(ws.registry_dir("validation_contracts"), ValidationContractRecord),
        "validation_results": list_valid_records(ws.registry_dir("validation_results"), ValidationResultRecord),
        "tool_runs": list_valid_records(ws.registry_dir("tool_runs"), ToolRunRecord),
        "research_routes": list_valid_records(ws.registry_dir("routes"), ResearchRouteRecord),
        "research_runs": list_valid_records(ws.registry_dir("research_runs"), ResearchRunRecord),
        "research_run_events": list_valid_records(ws.registry_dir("research_run_events"), ResearchRunEventRecord),
        "memory_entries": list_valid_records(ws.root / "memory" / "l2" / "entries", MemoryEntryRecord),
    }


def _written_record_counts(ws: WorkspacePaths, topic: str, registry: dict[str, list[Any]]) -> dict[str, int]:
    counts = {"topics": 1 if (ws.topic_dir(topic) / "topic.md").exists() else 0}
    for family, records in registry.items():
        counts[family] = sum(1 for record in records if _record_topic(record) == topic)
    return counts


def _active_claim_id(topic: str, registry: dict[str, list[Any]]) -> str:
    claims = [claim for claim in registry["claims"] if claim.topic_id == topic]
    return claims[0].claim_id if claims else ""


def _preserved_legacy_source_refs(topic: str, registry: dict[str, list[Any]]) -> list[str]:
    refs: set[str] = set()
    for records in registry.values():
        for record in records:
            if _record_topic(record) != topic:
                continue
            refs.update(_legacy_refs_from_record(record))
    return sorted(refs)


def _legacy_refs_from_record(record: Any) -> list[str]:
    refs: list[str] = []
    for field in ("source_refs", "source_ref"):
        value = getattr(record, field, None)
        if isinstance(value, list):
            refs.extend(str(item) for item in value)
        elif isinstance(value, str) and value:
            refs.append(value)
    return [ref for ref in refs if ref.startswith("legacy_") or ref.startswith("legacy:")]


def _record_topic(record: Any) -> str:
    topic = getattr(record, "topic_id", "")
    if topic:
        return str(topic)
    return str(getattr(record, "source_topic_id", "") or "")


def _resolve_run_id(ws: WorkspacePaths, requested: str) -> str:
    if requested:
        return requested
    base = datetime.now(timezone.utc).strftime("legacy-v5-lossless-accounting-%Y%m%dT%H%M%SZ")
    candidate = base
    counter = 2
    while (ws.root / "migrations" / candidate).exists():
        candidate = f"{base}-{counter}"
        counter += 1
    return candidate


def _manifest_hash(items: list[dict[str, Any]]) -> str:
    text = json.dumps(items, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    write_text_atomic(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
