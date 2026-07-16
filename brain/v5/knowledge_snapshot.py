"""Lineage-bound read-only snapshots for physics knowledge retrieval."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
import json
from typing import Any, Iterable, Mapping, Sequence

from brain.v5.paths import WorkspacePaths
from brain.v5.query_index_snapshot import (
    load_effective_query_index,
    scoped_index_freshness,
    scoped_index_orientation,
)
from brain.v5.source_shelf_storage import hash_json
from brain.v5.knowledge_snapshot_edges import (
    link_types as _link_types,
    record_link_types as _record_link_types,
    record_links as _record_links,
)


DEFAULT_KNOWLEDGE_FAMILIES = (
    "code_states",
    "derivation_chains",
    "derivation_reviews",
    "derivation_steps",
    "insights",
    "object_relations",
    "physics_assertions",
    "physics_objects",
    "proof_obligations",
    "reference_locations",
    "source_assets",
)


@dataclass(frozen=True)
class KnowledgeSnapshotLineage:
    query_index_generation: int
    query_index_delta_generation: int
    query_index_content_hash: str
    selected_family_state_tokens: dict[str, str]
    selected_family_content_watermarks: dict[str, str]
    source_shelf_generation: str = ""
    source_shelf_passages_hash: str = ""
    source_shelf_topic_id: str = ""
    excluded_unscoped_counts: dict[str, int] = field(default_factory=dict)
    freshness_mode: str = "strong"
    scope_fresh: bool = False
    scope_content_verified: bool = False
    dirty_families: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    snapshot_hash: str = ""

    def __post_init__(self) -> None:
        for value, label in (
            (self.query_index_generation, "query index generation"),
            (self.query_index_delta_generation, "query index delta generation"),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"knowledge snapshot {label} must be non-negative")
        if not _digest(self.query_index_content_hash):
            raise ValueError("knowledge snapshot query index content hash is invalid")
        state_keys = set(self.selected_family_state_tokens)
        content_keys = set(self.selected_family_content_watermarks)
        if state_keys != content_keys:
            raise ValueError("knowledge snapshot selected-family lineage keys must match")
        for mapping in (
            self.selected_family_state_tokens,
            self.selected_family_content_watermarks,
        ):
            if any(not key.strip() or not _digest(value) for key, value in mapping.items()):
                raise ValueError("knowledge snapshot family lineage digest is invalid")
        shelf_values = (
            self.source_shelf_generation,
            self.source_shelf_passages_hash,
            self.source_shelf_topic_id,
        )
        if any(shelf_values) and not (
            _digest(self.source_shelf_generation)
            and _digest(self.source_shelf_passages_hash)
            and self.source_shelf_topic_id.strip()
        ):
            raise ValueError("knowledge snapshot source shelf lineage is incomplete")
        if not isinstance(self.scope_fresh, bool) or not isinstance(
            self.scope_content_verified, bool
        ):
            raise TypeError("knowledge snapshot freshness flags must be boolean")
        if any(
            not isinstance(family, str)
            or not family.strip()
            or isinstance(count, bool)
            or not isinstance(count, int)
            or count < 1
            for family, count in self.excluded_unscoped_counts.items()
        ):
            raise ValueError("knowledge snapshot unscoped counts are invalid")
        if self.freshness_mode not in {"orientation", "strong"}:
            raise ValueError("knowledge snapshot freshness mode is invalid")
        if self.snapshot_hash and not _digest(self.snapshot_hash):
            raise ValueError("knowledge snapshot hash is invalid")


@dataclass(frozen=True)
class KnowledgeSnapshotItem:
    record_ref: str
    record_hash: str
    revision: int
    family: str
    topic_id: str
    program_id: str
    lane: str
    framework: str
    regime: str
    conventions: tuple[str, ...]
    fields: dict[str, tuple[str, ...]]
    links: tuple[str, ...]
    link_types: dict[str, tuple[str, ...]] = field(default_factory=dict)
    lifecycle_status: str = "active"
    review_status: str = ""
    orientation_only: bool = True


@dataclass(frozen=True)
class KnowledgeSnapshot:
    items: tuple[KnowledgeSnapshotItem, ...]
    lineage: KnowledgeSnapshotLineage
    can_update_claim_trust: bool = False


def knowledge_snapshot_from_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    lineage: KnowledgeSnapshotLineage,
) -> KnowledgeSnapshot:
    """Build a deterministic immutable snapshot from already bounded rows."""

    items = tuple(sorted((_item_from_row(row) for row in rows), key=lambda item: item.record_ref))
    refs = [item.record_ref for item in items]
    if len(refs) != len(set(refs)):
        raise ValueError("knowledge snapshot record refs must be unique")
    basis = {
        "lineage": {
            key: value
            for key, value in asdict(lineage).items()
            if key != "snapshot_hash"
        },
        "items": [asdict(item) for item in items],
    }
    snapshot_hash = hash_json(basis)
    if lineage.snapshot_hash and lineage.snapshot_hash != snapshot_hash:
        raise ValueError("knowledge snapshot lineage hash disagrees with rows")
    return KnowledgeSnapshot(
        items=items,
        lineage=replace(lineage, snapshot_hash=snapshot_hash),
    )


def build_knowledge_snapshot(
    ws: WorkspacePaths,
    *,
    selected_families: Iterable[str] = DEFAULT_KNOWLEDGE_FAMILIES,
    source_shelf_generation: str = "",
    source_shelf_topic_id: str = "",
    freshness_mode: str = "strong",
) -> KnowledgeSnapshot:
    """Bind canonical query-index rows and one optional exact source shelf."""

    if freshness_mode not in {"orientation", "strong"}:
        raise ValueError("knowledge snapshot freshness_mode is unsupported")
    families = tuple(sorted(set(selected_families)))
    snapshot = load_effective_query_index(ws, allow_cached=True)
    freshness = (
        scoped_index_orientation(ws, snapshot, families)
        if freshness_mode == "orientation"
        else scoped_index_freshness(ws, snapshot, families)
    )
    projected_rows = [
        _row_from_index_document(document)
        for document in snapshot.documents
        if document.get("family") in families
    ]
    rows = []
    excluded_unscoped_counts: dict[str, int] = {}
    for row in projected_rows:
        if str(row.get("topic_id") or "").strip():
            rows.append(row)
            continue
        family = str(row.get("family") or "unknown")
        excluded_unscoped_counts[family] = excluded_unscoped_counts.get(family, 0) + 1
    errors = list(snapshot.read_errors)
    errors.extend(freshness.diagnostics)
    if excluded_unscoped_counts:
        detail = ", ".join(
            f"{family}={count}"
            for family, count in sorted(excluded_unscoped_counts.items())
        )
        errors.append(f"excluded unscoped knowledge rows: {detail}")
    for family in families:
        malformed = int(snapshot.malformed_family_counts.get(family, 0))
        if malformed:
            errors.append(f"{family} has {malformed} malformed indexed record(s)")

    shelf_generation = ""
    shelf_passages_hash = ""
    shelf_topic = ""
    if source_shelf_generation:
        if not source_shelf_topic_id:
            raise ValueError("source_shelf_topic_id is required with a generation")
        from brain.v5.curated_rag_corpus import curated_rag_corpus

        catalog = curated_rag_corpus(
            ws,
            source_shelf_generation=source_shelf_generation,
            topic_id=source_shelf_topic_id,
        )
        policy = catalog["index_policy"]
        shelf_generation = policy["source_shelf_generation"]
        shelf_passages_hash = policy["source_shelf_passages_hash"]
        shelf_topic = policy["source_shelf_topic_id"]
        rows.extend(_rows_from_source_shelf(catalog))
        if policy.get("source_shelf_incomplete_coverage"):
            errors.append("source shelf coverage is incomplete")
    elif source_shelf_topic_id:
        raise ValueError("source_shelf_generation is required with a shelf topic")

    manifest = snapshot.manifest
    lineage = KnowledgeSnapshotLineage(
        query_index_generation=int(manifest.generation),
        query_index_delta_generation=int(snapshot.delta_generation),
        query_index_content_hash=str(manifest.content_hash),
        selected_family_state_tokens={
            family: snapshot.family_state_tokens.get(family, "") for family in families
        },
        selected_family_content_watermarks={
            family: snapshot.family_content_watermarks.get(family, "") for family in families
        },
        source_shelf_generation=shelf_generation,
        source_shelf_passages_hash=shelf_passages_hash,
        source_shelf_topic_id=shelf_topic,
        excluded_unscoped_counts=dict(sorted(excluded_unscoped_counts.items())),
        freshness_mode=freshness_mode,
        scope_fresh=freshness.scope_fresh,
        scope_content_verified=freshness.scope_content_verified,
        dirty_families=tuple(freshness.dirty_families),
        errors=tuple(dict.fromkeys(errors)),
    )
    return knowledge_snapshot_from_rows(rows, lineage=lineage)


def _item_from_row(row: Mapping[str, Any]) -> KnowledgeSnapshotItem:
    required = ("record_ref", "record_hash", "family", "topic_id", "lane")
    for key in required:
        if not isinstance(row.get(key), str) or not str(row[key]).strip():
            raise ValueError(f"knowledge snapshot row {key} must be non-empty")
    record_hash = str(row["record_hash"])
    if not _digest(record_hash):
        raise ValueError("knowledge snapshot record_hash must be a sha256 digest")
    revision = row.get("revision", 1)
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        raise ValueError("knowledge snapshot revision must be positive")
    fields = {
        str(key): _strings(value)
        for key, value in dict(row.get("fields") or {}).items()
        if _strings(value)
    }
    lane = str(row["lane"])
    if lane not in {"grounded", "insight", "orientation", "source"}:
        raise ValueError(f"unsupported knowledge snapshot lane: {lane}")
    links = _strings(row.get("links"))
    link_types = _link_types(row.get("link_types"), links)
    return KnowledgeSnapshotItem(
        record_ref=str(row["record_ref"]),
        record_hash=record_hash.lower(),
        revision=revision,
        family=str(row["family"]),
        topic_id=str(row["topic_id"]),
        program_id=str(row.get("program_id") or ""),
        lane=lane,
        framework=str(row.get("framework") or ""),
        regime=str(row.get("regime") or ""),
        conventions=_strings(row.get("conventions")),
        fields=fields,
        links=links,
        link_types=link_types,
        lifecycle_status=str(row.get("lifecycle_status") or "active"),
        review_status=str(row.get("review_status") or ""),
        orientation_only=lane != "grounded",
    )


def _row_from_index_document(document: Mapping[str, Any]) -> dict[str, Any]:
    frontmatter, body = _decode_search_text(str(document.get("search_text") or ""))
    family = str(document.get("family") or "")
    linked_records = (
        frontmatter.get("linked_records")
        if isinstance(frontmatter.get("linked_records"), Mapping)
        else {}
    )
    return {
        "record_ref": str(document.get("record_ref") or ""),
        "record_hash": str(document.get("record_content_hash") or ""),
        "revision": _positive_int(frontmatter.get("revision"), 1),
        "family": family,
        "topic_id": str(
            document.get("topic_id")
            or frontmatter.get("topic_id")
            or linked_records.get("topic_id")
            or ""
        ),
        "program_id": str(document.get("program_id") or frontmatter.get("program_id") or ""),
        "lane": _knowledge_lane(family, frontmatter),
        "framework": str(frontmatter.get("framework") or ""),
        "regime": str(frontmatter.get("regime") or ""),
        "conventions": _strings(frontmatter.get("conventions")),
        "fields": _retrieval_fields(frontmatter, body),
        "links": _record_links(frontmatter),
        "link_types": _record_link_types(frontmatter),
        "lifecycle_status": str(document.get("lifecycle_status") or "active"),
        "review_status": str(frontmatter.get("review_status") or ""),
    }


def _rows_from_source_shelf(catalog: Mapping[str, Any]) -> list[dict[str, Any]]:
    documents = {item["document_id"]: item for item in catalog.get("documents", [])}
    rows = []
    for chunk in catalog.get("chunks", []):
        anchor = chunk["anchor"]
        document = documents[chunk["document_id"]]
        passage_ref = str(anchor["source_passage_id"])
        rows.append(
            {
                "record_ref": passage_ref,
                "record_hash": str(anchor["text_hash"]),
                "revision": 1,
                "family": "source_shelf_passages",
                "topic_id": catalog["index_policy"]["source_shelf_topic_id"],
                "program_id": "",
                "lane": "source",
                "framework": "",
                "regime": "",
                "conventions": [],
                "fields": {
                    "canonical_name": [document["title"]],
                    "passage_text": [chunk["text"]],
                    "statement": [chunk["summary"]],
                    "source_asset_ref": [anchor["source_asset_ref"]],
                    "source_anchors": list(anchor["source_location_refs"]),
                    "anchor_kinds": list(anchor["anchor_kinds"]),
                    "anchor_labels": list(anchor["anchor_labels"]),
                },
                "links": [anchor["source_asset_ref"], *anchor["source_location_refs"]],
            }
        )
    return rows


def _decode_search_text(value: str) -> tuple[dict[str, Any], str]:
    try:
        frontmatter, end = json.JSONDecoder().raw_decode(value)
    except (json.JSONDecodeError, TypeError):
        return {}, value
    return (frontmatter if isinstance(frontmatter, dict) else {}), value[end:].strip()


def _retrieval_fields(frontmatter: Mapping[str, Any], body: str) -> dict[str, list[str]]:
    metadata = frontmatter.get("metadata") if isinstance(frontmatter.get("metadata"), dict) else {}
    return {
        "canonical_name": _values(frontmatter, "canonical_name", "name", "title"),
        "aliases": _values(frontmatter, "aliases"),
        "formula": _values(
            frontmatter,
            "expression",
            "notation",
            "input_expression",
            "output_expression",
            "value",
        ),
        "assumptions": _values(frontmatter, "assumptions", "conditions", "unresolved_conditions"),
        "non_claims": _values(frontmatter, "non_claims", "failure_modes", "falsifiers"),
        "speculation": _values(frontmatter, "speculation_level", "insight_kind"),
        "source_anchors": _values(
            frontmatter,
            "source_refs",
            "source_asset_refs",
            "source_location_refs",
            "source_anchor_refs",
        ),
        "relation": _values(frontmatter, "relation_type", "statement"),
        "statement": _values(frontmatter, "statement", "definition", "target", "summary"),
        "passage_text": [body] if body else [],
        "code": _values(metadata, "module", "function", "parameter", "output"),
    }


def _knowledge_lane(family: str, frontmatter: Mapping[str, Any]) -> str:
    if family == "insights":
        return "insight"
    if family == "physics_assertions":
        grounded = (
            frontmatter.get("review_status") == "reviewed"
            and bool(frontmatter.get("source_asset_refs"))
            and bool(frontmatter.get("source_location_refs"))
        )
        return "grounded" if grounded else "orientation"
    if family == "object_relations":
        return "grounded" if frontmatter.get("review_status") == "reviewed" else "orientation"
    if family == "physics_objects":
        grounded = (
            frontmatter.get("knowledge_role") == "grounded_knowledge"
            and frontmatter.get("review_status") == "reviewed"
        )
        return "grounded" if grounded else "orientation"
    if family == "derivation_reviews" and frontmatter.get("decision") == "passed":
        return "grounded"
    return "orientation"


def _values(mapping: Mapping[str, Any], *keys: str) -> list[str]:
    values: list[str] = []
    for key in keys:
        values.extend(_strings(mapping.get(key)))
    return list(dict.fromkeys(values))


def _strings(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value.strip() else ()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(str(item) for item in value if isinstance(item, (str, int, float)) and str(item).strip())
    if value not in (None, ""):
        return (str(value),)
    return ()


def _positive_int(value: Any, default: int) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else default


def _digest(value: str) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value.lower())
    )


__all__ = [
    "DEFAULT_KNOWLEDGE_FAMILIES",
    "KnowledgeSnapshot",
    "KnowledgeSnapshotItem",
    "KnowledgeSnapshotLineage",
    "build_knowledge_snapshot",
    "knowledge_snapshot_from_rows",
]
