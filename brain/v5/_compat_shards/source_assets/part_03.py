# Compatibility shard 3 for source_assets.
from __future__ import annotations

def _duplicate_hash_diagnostics(
    ws: WorkspacePaths,
    *,
    asset_id: str,
    content_hash: str,
    hash_algorithm: str,
) -> dict[str, Any]:
    duplicates = [
        record.asset_id
        for record in list_records(ws.registry_dir("source_assets"), SourceAssetRecord)
        if record.asset_id != asset_id
        and record.content_hash == content_hash
        and (record.hash_algorithm or "unknown") == hash_algorithm
    ]
    return {
        "hash": content_hash,
        "hash_algorithm": hash_algorithm,
        "duplicate_hash": bool(duplicates),
        "duplicate_asset_ids": duplicates,
        "diagnostic_scope": "registry/source_assets",
    }
