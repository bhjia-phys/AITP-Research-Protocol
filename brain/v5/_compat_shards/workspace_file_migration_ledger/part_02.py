# Compatibility shard 2 for workspace_file_migration_ledger.
from __future__ import annotations

def _old_store_file_fate(
    *,
    category: str,
    family: str,
    topic_action: str,
    has_topic: bool,
) -> tuple[str, str, bool, str, str]:
    if category in {"registry_record", "memory_entry"}:
        target = "canonical_memory/l2/entries" if category == "memory_entry" else (
            f"canonical_registry/{family}" if family else "canonical_registry"
        )
        if topic_action in {"root_store_import_review_required", "repair_canonical_topic_shell_and_merge_required"}:
            return (
                "typed_import_candidate",
                "import_review_required",
                True,
                "root/nested typed record is not yet represented in the canonical topic graph",
                target,
            )
        if topic_action == "duplicate_store_review_required":
            return (
                "typed_import_candidate",
                "duplicate_review_required",
                True,
                "root-local typed record must be diffed against canonical records before import or archive",
                target,
            )
        return (
            "semantic_review_basis",
            "semantic_review_required",
            True,
            "typed record belongs to a topic that still has legacy/canonical semantic-review work",
            target,
        )
    if category in {"topic_shell", "runtime_session"}:
        return (
            "archive_reference",
            "archive_decision_required",
            True,
            "topic shell or runtime session must be explicitly archived or promoted before old-store retirement",
            "archive_manifest",
        )
    if category in {"derived_surface", "migration_artifact", "runtime_artifact", "store_metadata"}:
        return (
            "archive_reference",
            "archive_decision_required" if has_topic else "archive_accounted",
            bool(has_topic),
            "noncanonical store support file is preserved by hash manifest",
            "archive_manifest",
        )
    return (
        "archive_reference",
        "archive_decision_required",
        True,
        "unclassified old-store file requires an explicit archive/import decision",
        "archive_manifest",
    )

def _legacy_accounting_payload(path: str | Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    root = Path(path)
    file_manifest = _load_json(root / "file_manifest.json")
    summary_path = root / "migration_summary.json"
    summary = _load_json(summary_path) if summary_path.exists() else {}
    return {
        "migration_dir": str(root),
        "legacy_root": str(summary.get("legacy_root") or ""),
        "expected_file_count": len(file_manifest),
        "files": file_manifest,
    }

def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def _top_values(items: list[dict[str, Any]], key: str, *, limit: int = 12) -> list[str]:
    counts = Counter(str(item.get(key) or "_unassigned") for item in items)
    return [value for value, _count in counts.most_common(limit)]

def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")
