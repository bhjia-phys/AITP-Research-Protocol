from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


_BRAIN_BACKEND_ID = "backend:theoretical-physics-brain"


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _load_backend_card(kernel_root: Path, backend_id: str) -> tuple[Path | None, dict[str, Any] | None]:
    index_path = kernel_root / "canonical" / "backends" / "backend_index.jsonl"
    if index_path.exists():
        for raw_line in index_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            row = json.loads(line)
            if str(row.get("backend_id") or "").strip() != backend_id:
                continue
            card_path = str(row.get("card_path") or "").strip()
            if not card_path:
                continue
            candidate = Path(card_path)
            if not candidate.is_absolute():
                candidate = kernel_root / card_path
            payload = _read_json(candidate)
            if payload is not None:
                return candidate.resolve(), payload

    for candidate in sorted((kernel_root / "canonical" / "backends").rglob("*.json")):
        payload = _read_json(candidate)
        if payload is None:
            continue
        if str(payload.get("backend_id") or "").strip() == backend_id:
            return candidate.resolve(), payload
    return None, None


def _resolve_brain_root(
    *,
    kernel_root: Path,
    repo_root: Path,
    target_root: str | None,
) -> tuple[Path, Path | None, dict[str, Any] | None]:
    if target_root:
        return Path(target_root).expanduser().resolve(), None, None

    env_override = os.environ.get("AITP_THEORETICAL_PHYSICS_BRAIN_ROOT")
    if env_override and env_override.strip():
        return Path(env_override).expanduser().resolve(), None, None

    card_path, card_payload = _load_backend_card(kernel_root, _BRAIN_BACKEND_ID)
    if card_payload:
        for root_path in card_payload.get("root_paths") or []:
            candidate = str(root_path).strip()
            if not candidate or candidate.startswith("__"):
                continue
            return Path(candidate).expanduser().resolve(), card_path, card_payload

    fallback = repo_root / "obsidian-markdown" / "01 Theoretical Physics"
    if fallback.exists():
        return fallback.resolve(), None, None

    raise FileNotFoundError(
        "Unable to resolve theoretical-physics brain root. Pass target_root, set "
        "AITP_THEORETICAL_PHYSICS_BRAIN_ROOT, or configure the backend card root_paths."
    )


def _concept_graph_export_root(kernel_root: Path, topic_slug: str) -> Path:
    return kernel_root / "topics" / topic_slug / "L1" / "vault" / "wiki" / "concept-graph"


def sync_concept_graph_export_to_theoretical_physics_brain(
    *,
    kernel_root: Path,
    repo_root: Path,
    topic_slug: str,
    updated_by: str,
    target_root: str | None = None,
) -> dict[str, Any]:
    resolved_kernel_root = kernel_root.expanduser().resolve()
    resolved_repo_root = repo_root.expanduser().resolve()
    source_root = _concept_graph_export_root(resolved_kernel_root, topic_slug)
    manifest_path = source_root / "manifest.json"
    manifest_payload = _read_json(manifest_path)
    if manifest_payload is None:
        raise FileNotFoundError(f"Concept-graph export manifest missing: {manifest_path}")

    brain_root, card_path, card_payload = _resolve_brain_root(
        kernel_root=resolved_kernel_root,
        repo_root=resolved_repo_root,
        target_root=target_root,
    )
    target_export_root = brain_root / "90 AITP Imports" / "concept-graphs" / topic_slug
    if target_export_root.exists():
        shutil.rmtree(target_export_root)
    shutil.copytree(source_root, target_export_root)

    mirrored_files = [path for path in target_export_root.rglob("*") if path.is_file()]
    receipt_payload = {
        "kind": "theoretical_physics_brain_concept_graph_sync_receipt",
        "topic_slug": topic_slug,
        "backend_id": _BRAIN_BACKEND_ID,
        "backend_root": str(brain_root),
        "backend_card_path": str(card_path) if card_path else "",
        "source_export_root": str(source_root),
        "target_root": str(target_export_root),
        "source_manifest_path": str(manifest_path),
        "mirrored_manifest_path": str(target_export_root / "manifest.json"),
        "summary": {
            "mirrored_file_count": len(mirrored_files),
            "node_note_count": int(((manifest_payload.get("summary") or {}).get("node_note_count")) or 0),
            "community_folder_count": int(((manifest_payload.get("summary") or {}).get("community_folder_count")) or 0),
        },
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }
    receipt_path = source_root / "theoretical_physics_brain_sync.receipt.json"
    _write_json(receipt_path, receipt_payload)
    return {
        **receipt_payload,
        "receipt_path": str(receipt_path),
        "backend_card_payload": card_payload or {},
    }
