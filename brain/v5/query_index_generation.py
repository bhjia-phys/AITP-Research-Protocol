"""Immutable component generations for the disposable query index."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from brain.v5.markdown import write_text_atomic
from brain.v5.paths import WorkspacePaths


def next_generation_number(ws: WorkspacePaths, published_generation: int) -> int:
    """Reserve after both the root generation and any unpublished directories."""

    generations_dir = ws.root / "indexes" / "generations"
    observed = [max(0, int(published_generation))]
    if generations_dir.exists():
        for path in generations_dir.iterdir():
            if path.is_dir() and path.name.isdigit():
                observed.append(int(path.name))
    return max(observed) + 1


def generation_component_files(generation: int) -> dict[str, str]:
    prefix = f"generations/{generation:016d}"
    return {
        "document_file": f"{prefix}/record_documents.json",
        "lexical_file": f"{prefix}/lexical_index.json",
        "issues_file": f"{prefix}/issues.json",
        "generation_manifest_file": f"{prefix}/manifest.json",
    }


def write_immutable_generation(
    ws: WorkspacePaths,
    *,
    manifest_payload: dict[str, Any],
    document_text: str,
    lexical_text: str,
    issues_text: str,
) -> None:
    """Write one unpublished generation and reject path reuse."""

    generation_manifest = ws.root / "indexes" / Path(
        str(manifest_payload["generation_manifest_file"])
    )
    generation_dir = generation_manifest.parent
    if generation_dir.exists():
        raise FileExistsError(f"query index generation already exists: {generation_dir}")
    write_text_atomic(
        ws.root / "indexes" / Path(str(manifest_payload["document_file"])),
        document_text,
    )
    write_text_atomic(
        ws.root / "indexes" / Path(str(manifest_payload["lexical_file"])),
        lexical_text,
    )
    write_text_atomic(
        ws.root / "indexes" / Path(str(manifest_payload["issues_file"])),
        issues_text,
    )
    write_text_atomic(
        generation_manifest,
        json.dumps(manifest_payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
    )


def load_generation_descriptor(ws: WorkspacePaths, relative_path: str) -> dict[str, Any]:
    return json.loads(
        (ws.root / "indexes" / Path(relative_path)).read_text(encoding="utf-8")
    )
