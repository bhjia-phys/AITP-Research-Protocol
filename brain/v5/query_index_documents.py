"""Deterministic query-index documents, lexical terms, and stable hashes."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from brain.v5.legacy_record_materialization import materialize_record_class
from brain.v5.paths import WorkspacePaths


_LATIN_TOKEN_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.+-]*")
_CJK_TOKEN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")
_CONTEXT_SUMMARY_FIELDS = (
    "active_uncertainty",
    "artifact_type",
    "claim_status",
    "confidence_state",
    "created_at",
    "event_type",
    "evidence_status",
    "failure_modes",
    "lifecycle_status",
    "maturity_level",
    "next_action",
    "objective",
    "outputs",
    "phase",
    "pivot_reason",
    "research_question",
    "risk",
    "scope",
    "statement",
    "summary",
    "superseded_by",
    "supersedes_run_id",
    "timestamp",
    "tool_family",
    "tool_name",
    "updated_at",
    "validation_status",
)


def _document_row(ws, spec, frontmatter, body, envelope, path):
    topic_id = str(frontmatter.get("topic_id") or frontmatter.get("topic") or "")
    lifecycle = str(frontmatter.get("lifecycle_status") or frontmatter.get("status") or "")
    searchable = json.dumps(_json_safe(frontmatter), ensure_ascii=False, sort_keys=True)
    return {
        "record_ref": f"{spec.ref_kind}:{envelope.record_id}",
        "record_id": envelope.record_id,
        "family": envelope.record_family,
        "kind": str(frontmatter.get("kind") or ""),
        "topic_id": topic_id,
        "claim_id": str(frontmatter.get("claim_id") or ""),
        "session_id": envelope.session_id,
        "program_id": envelope.program_id,
        "scope_refs": list(envelope.scope_refs),
        "source_record_refs": list(envelope.source_record_refs),
        "status": str(frontmatter.get("status") or ""),
        "lifecycle_status": lifecycle,
        "title": str(frontmatter.get("title") or frontmatter.get("statement") or ""),
        "record_content_hash": envelope.content_hash,
        "typed_materialization_status": _typed_materialization_status(frontmatter, spec),
        "relative_path": _relative_path(ws, path),
        "summary_fields": {
            key: _json_safe(frontmatter[key])
            for key in _CONTEXT_SUMMARY_FIELDS
            if key in frontmatter and frontmatter[key] not in (None, "", [], {})
        },
        "search_text": f"{searchable}\n{body}".strip(),
    }


def _project_tool_run_supersession(documents: list[dict[str, Any]]) -> None:
    successors: dict[str, list[str]] = {}
    for document in documents:
        if document.get("family") != "tool_runs":
            continue
        summary = document.get("summary_fields") or {}
        prior_id = str(summary.get("supersedes_run_id") or "").strip()
        if prior_id:
            successors.setdefault(prior_id, []).append(str(document.get("record_id") or ""))
    for document in documents:
        if document.get("family") != "tool_runs":
            continue
        successor_ids = sorted(item for item in successors.get(document.get("record_id"), []) if item)
        if successor_ids:
            document["summary_fields"]["superseded_by"] = successor_ids[0]


def _lexical_index(documents):
    postings: dict[str, set[int]] = {}
    for row in documents:
        for term in lexical_terms(row["search_text"]):
            postings.setdefault(term, set()).add(row["doc_id"])
    return {term: sorted(refs) for term, refs in sorted(postings.items())}


def lexical_terms(text: str) -> tuple[str, ...]:
    """Tokenize Latin identifiers and bounded CJK n-grams deterministically."""

    lowered = str(text or "").lower()
    latin_tokens = set(_LATIN_TOKEN_RE.findall(lowered))
    terms = set(latin_tokens)
    for token in latin_tokens:
        terms.update(part for part in re.split(r"[._+\-]+", token) if len(part) >= 2)
    for match in _CJK_TOKEN_RE.findall(lowered):
        sequence = match[:128]
        terms.add(sequence)
        for width in range(2, min(4, len(sequence)) + 1):
            terms.update(
                sequence[index : index + width]
                for index in range(len(sequence) - width + 1)
            )
    return tuple(sorted(term for term in terms if term))


def _typed_materialization_status(frontmatter, spec) -> str:
    if spec.record_class is None:
        return "not_applicable"
    try:
        materialize_record_class(
            frontmatter,
            spec.record_class,
            id_field=spec.id_field,
            legacy_id_fields=spec.legacy_id_fields,
        )
    except (TypeError, ValueError):
        return "unavailable"
    return "ready"


def _relative_path(ws: WorkspacePaths, path: Path) -> str:
    return path.relative_to(ws.root).as_posix()


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_safe(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _hash_json(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
