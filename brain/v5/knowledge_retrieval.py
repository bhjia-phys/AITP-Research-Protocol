"""Deterministic fielded lexical retrieval over one knowledge snapshot."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
from typing import Any, Mapping, Sequence

from brain.v5.knowledge_snapshot import KnowledgeSnapshot, KnowledgeSnapshotItem
from brain.v5.knowledge_retrieval_metrics import evaluate_ranked_refs
from brain.v5.query_index_documents import lexical_terms
from brain.v5.source_shelf_storage import hash_json


DEFAULT_LEXICAL_POLICY = {
    "version": "fielded-bm25.v1",
    "k1": 1.2,
    "b": 0.75,
    "field_weights": {
        "canonical_name": 4.0,
        "aliases": 3.0,
        "formula": 4.0,
        "framework": 2.5,
        "regime": 2.5,
        "assumptions": 1.5,
        "non_claims": 1.0,
        "source_anchors": 1.0,
        "relation": 2.0,
        "statement": 2.5,
        "passage_text": 1.0,
    },
}


@dataclass(frozen=True)
class KnowledgeQuery:
    text: str
    topic_id: str
    framework: str = ""
    regime: str = ""
    conventions: tuple[str, ...] = ()
    formula: str = ""
    formula_dummy_symbols: tuple[tuple[str, str], ...] = ()
    formula_commutative_product_safe: bool = False
    intent: str = "default"
    program_id: str = ""
    seed_refs: tuple[str, ...] = ()
    include_discovery: bool = False
    revalidation_decision_refs: tuple[Any, ...] = ()
    max_results: int = 8
    page_offset: int = 0
    graph_depth: int = 2
    deterministic: bool = True

    def __post_init__(self) -> None:
        if not self.text.strip() and not self.formula.strip() and not self.seed_refs:
            raise ValueError("knowledge query requires text, formula, or seed refs")
        if not self.topic_id.strip():
            raise ValueError("knowledge query topic_id is required")
        if self.intent not in {"default", "comparison", "dependency", "insight"}:
            raise ValueError("knowledge query intent is unsupported")
        if isinstance(self.max_results, bool) or not 1 <= self.max_results <= 100:
            raise ValueError("knowledge query max_results must be in [1, 100]")
        if (
            isinstance(self.page_offset, bool)
            or not isinstance(self.page_offset, int)
            or not 0 <= self.page_offset <= 10000
        ):
            raise ValueError("knowledge query page_offset must be in [0, 10000]")
        if isinstance(self.graph_depth, bool) or not 0 <= self.graph_depth <= 3:
            raise ValueError("knowledge query graph_depth must be in [0, 3]")
        if not isinstance(self.formula_commutative_product_safe, bool):
            raise TypeError("formula commutative-product declaration must be boolean")
        dummy_sources: set[str] = set()
        for mapping in self.formula_dummy_symbols:
            if (
                not isinstance(mapping, tuple)
                or len(mapping) != 2
                or not all(isinstance(value, str) and value.strip() for value in mapping)
            ):
                raise TypeError("formula dummy symbols must be non-empty string pairs")
            if mapping[0] in dummy_sources:
                raise ValueError("formula dummy symbol sources must be unique")
            dummy_sources.add(mapping[0])
        if self.revalidation_decision_refs:
            from brain.v5.pinned_record_refs import PinnedRecordRef

            for value in self.revalidation_decision_refs:
                if isinstance(value, PinnedRecordRef):
                    pinned = value
                elif isinstance(value, Mapping):
                    pinned = PinnedRecordRef(
                        record_ref=str(value.get("record_ref") or ""),
                        content_hash=str(value.get("content_hash") or ""),
                        revision=value.get("revision"),
                    )
                else:
                    raise TypeError(
                        "knowledge query revalidation decisions must be exact pinned refs"
                    )
                if not pinned.record_ref.startswith("scope_revalidation_decision:"):
                    raise ValueError(
                        "knowledge query revalidation decision ref has the wrong kind"
                    )


@dataclass(frozen=True)
class KnowledgeRetrievalHit:
    record_ref: str
    component: str
    rank: int
    score: float
    lane: str
    topic_id: str
    family: str
    field_scores: dict[str, float] = field(default_factory=dict)
    anchors: dict[str, Any] = field(default_factory=dict)
    path: tuple[str, ...] = ()
    exact_expansion_refs: tuple[str, ...] = ()
    orientation_only: bool = True
    can_update_claim_trust: bool = False


@dataclass(frozen=True)
class KnowledgeComponentResult:
    component: str
    version: str
    status: str
    snapshot_hash: str
    component_hash: str
    hits: tuple[KnowledgeRetrievalHit, ...]
    coverage: dict[str, Any]
    deterministic: bool = True
    errors: tuple[str, ...] = ()
    can_update_claim_trust: bool = False


@dataclass(frozen=True)
class KnowledgeRetrievalCoverage:
    snapshot_compatible: bool
    complete: bool
    component_statuses: dict[str, str]
    checked_scope: dict[str, Any]
    excluded_scope: dict[str, int]
    pagination: dict[str, Any]
    errors: tuple[str, ...] = ()
    truncated: bool = False


@dataclass(frozen=True)
class KnowledgeRetrievalResult:
    query: KnowledgeQuery
    hits: tuple[KnowledgeRetrievalHit, ...]
    coverage: KnowledgeRetrievalCoverage
    result_hash: str
    deterministic: bool
    can_claim_no_result: bool
    can_update_claim_trust: bool = False


def search_fielded_lexical(
    snapshot: KnowledgeSnapshot,
    query: KnowledgeQuery,
    policy: Mapping[str, Any] | None = None,
) -> KnowledgeComponentResult:
    """Run deterministic fielded BM25 and expose every field contribution."""

    selected_policy = _lexical_policy(policy)
    eligible, excluded = _eligible_items(snapshot, query)
    query_terms = lexical_terms(f"{query.text} {query.formula}")
    weighted_fields = dict(selected_policy["field_weights"])
    corpus = [(_item_fields(item), item, lane) for item, lane in eligible]
    field_corpora = {
        field_name: tuple(
            _terms(fields.get(field_name, ()))
            for fields, _item, _lane in corpus
        )
        for field_name in weighted_fields
    }
    corpus_statistics = {
        field_name: {
            "document_count": len(documents),
            "nonempty_document_count": sum(bool(document) for document in documents),
            "average_document_length": round(
                sum(len(document) for document in documents) / len(documents),
                12,
            )
            if documents
            else 0.0,
            "query_document_frequency": {
                term: sum(term in document for document in documents)
                for term in query_terms
            },
        }
        for field_name, documents in field_corpora.items()
    }
    scores: list[tuple[float, KnowledgeSnapshotItem, str, dict[str, float]]] = []
    for fields, item, lane in corpus:
        contributions: dict[str, float] = {}
        for field_name, weight in weighted_fields.items():
            values = fields.get(field_name, ())
            tokens = _terms(values)
            if not tokens or not query_terms:
                continue
            score = _bm25_field(
                tokens,
                query_terms,
                corpus_size=corpus_statistics[field_name]["document_count"],
                average_length=corpus_statistics[field_name][
                    "average_document_length"
                ],
                document_frequencies=corpus_statistics[field_name][
                    "query_document_frequency"
                ],
                k1=float(selected_policy["k1"]),
                b=float(selected_policy["b"]),
            )
            if score > 0:
                contributions[field_name] = round(score * float(weight), 12)
        total = round(sum(contributions.values()), 12)
        if total > 0:
            scores.append((total, item, lane, contributions))
    scores.sort(key=lambda row: (-row[0], row[1].record_ref))
    hits = tuple(
        _hit(
            item,
            component="lexical",
            rank=index,
            score=score,
            lane=lane,
            field_scores=contributions,
        )
        for index, (score, item, lane, contributions) in enumerate(
            scores[: _candidate_limit(query)], start=1
        )
    )
    coverage = {
        **excluded,
        "checked_items": len(snapshot.items),
        "eligible_items": len(eligible),
        "matched_items": len(scores),
        "returned_items": len(hits),
        "truncated": len(scores) > len(hits),
        "query_terms": list(query_terms),
        "selected_fields": list(weighted_fields),
        "corpus_statistics": corpus_statistics,
        "tie_handling": "score_desc_then_record_ref",
    }
    return _component_result(
        component="lexical",
        version=str(selected_policy["version"]),
        status="available",
        snapshot=snapshot,
        hits=hits,
        coverage=coverage,
        policy=selected_policy,
    )


def _eligible_items(
    snapshot: KnowledgeSnapshot,
    query: KnowledgeQuery,
) -> tuple[list[tuple[KnowledgeSnapshotItem, str]], dict[str, int]]:
    eligible: list[tuple[KnowledgeSnapshotItem, str]] = []
    excluded = {
        "foreign_topic_excluded": 0,
        "foreign_insight_excluded": 0,
        "wrong_framework_excluded": 0,
        "wrong_regime_excluded": 0,
        "convention_mismatch_excluded": 0,
        "insight_lane_excluded": 0,
        "inactive_excluded": 0,
    }
    for item in snapshot.items:
        if item.lifecycle_status not in {"", "active", "established"}:
            excluded["inactive_excluded"] += 1
            continue
        lane = item.lane
        if item.topic_id != query.topic_id:
            if item.lane == "insight":
                excluded["foreign_insight_excluded"] += 1
                continue
            if (
                query.program_id
                and item.program_id
                and _norm(item.program_id) == _norm(query.program_id)
            ):
                lane = "shared"
            elif not query.include_discovery:
                excluded["foreign_topic_excluded"] += 1
                continue
            else:
                lane = "discovery"
        if item.lane == "insight" and query.intent not in {"insight", "comparison"}:
            excluded["insight_lane_excluded"] += 1
            continue
        mismatch = ""
        if query.framework and item.framework and _norm(query.framework) != _norm(item.framework):
            mismatch = "wrong_framework_excluded"
        elif query.regime and item.regime and _norm(query.regime) != _norm(item.regime):
            mismatch = "wrong_regime_excluded"
        elif query.conventions and item.conventions and not set(map(_norm, query.conventions)) <= set(map(_norm, item.conventions)):
            mismatch = "convention_mismatch_excluded"
        if mismatch:
            if query.intent == "comparison":
                lane = "comparison"
            else:
                excluded[mismatch] += 1
                continue
        eligible.append((item, lane))
    return eligible, excluded


def _item_fields(item: KnowledgeSnapshotItem) -> dict[str, tuple[str, ...]]:
    return {
        **item.fields,
        "framework": (item.framework,) if item.framework else (),
        "regime": (item.regime,) if item.regime else (),
    }


def _bm25_field(
    document: tuple[str, ...],
    query_terms: tuple[str, ...],
    *,
    corpus_size: int,
    average_length: float,
    document_frequencies: Mapping[str, int],
    k1: float,
    b: float,
) -> float:
    if not corpus_size:
        return 0.0
    length = len(document)
    average = average_length or 1.0
    score = 0.0
    for term in query_terms:
        frequency = document.count(term)
        if not frequency:
            continue
        document_frequency = int(document_frequencies.get(term, 0))
        inverse = math.log(
            1.0
            + (corpus_size - document_frequency + 0.5)
            / (document_frequency + 0.5)
        )
        denominator = frequency + k1 * (1.0 - b + b * length / average)
        score += inverse * frequency * (k1 + 1.0) / denominator
    return score


def _hit(
    item: KnowledgeSnapshotItem,
    *,
    component: str,
    rank: int,
    score: float,
    lane: str,
    field_scores: Mapping[str, float] | None = None,
    anchors: Mapping[str, Any] | None = None,
    path: Sequence[str] = (),
) -> KnowledgeRetrievalHit:
    return KnowledgeRetrievalHit(
        record_ref=item.record_ref,
        component=component,
        rank=rank,
        score=round(float(score), 12),
        lane=lane,
        topic_id=item.topic_id,
        family=item.family,
        field_scores=dict(field_scores or {}),
        anchors=dict(anchors or {}),
        path=tuple(path),
        exact_expansion_refs=(item.record_ref,),
        orientation_only=lane != "grounded",
    )


def _component_result(
    *,
    component: str,
    version: str,
    status: str,
    snapshot: KnowledgeSnapshot,
    hits: Sequence[KnowledgeRetrievalHit],
    coverage: Mapping[str, Any],
    policy: Mapping[str, Any],
    deterministic: bool = True,
    errors: Sequence[str] = (),
) -> KnowledgeComponentResult:
    lineage_errors = list(snapshot.lineage.errors)
    if not snapshot.lineage.scope_fresh:
        lineage_errors.append("knowledge snapshot scope is not fresh")
    if not snapshot.lineage.scope_content_verified:
        lineage_errors.append("knowledge snapshot scope content is not verified")
    merged_errors = tuple(dict.fromkeys([*errors, *lineage_errors]))
    merged_coverage = {
        **dict(coverage),
        "snapshot_scope_fresh": snapshot.lineage.scope_fresh,
        "snapshot_scope_content_verified": snapshot.lineage.scope_content_verified,
        "snapshot_dirty_families": list(snapshot.lineage.dirty_families),
        "snapshot_errors": list(snapshot.lineage.errors),
        "query_index_generation": snapshot.lineage.query_index_generation,
        "query_index_delta_generation": snapshot.lineage.query_index_delta_generation,
        "query_index_content_hash": snapshot.lineage.query_index_content_hash,
        "selected_family_state_tokens": dict(snapshot.lineage.selected_family_state_tokens),
        "selected_family_content_watermarks": dict(
            snapshot.lineage.selected_family_content_watermarks
        ),
        "source_shelf_generation": snapshot.lineage.source_shelf_generation,
        "source_shelf_passages_hash": snapshot.lineage.source_shelf_passages_hash,
    }
    basis = {
        "component": component,
        "version": version,
        "status": status,
        "snapshot_hash": snapshot.lineage.snapshot_hash,
        "hits": [asdict(hit) for hit in hits],
        "coverage": merged_coverage,
        "policy": dict(policy),
        "deterministic": deterministic,
        "errors": list(merged_errors),
    }
    return KnowledgeComponentResult(
        component=component,
        version=version,
        status=status,
        snapshot_hash=snapshot.lineage.snapshot_hash,
        component_hash=hash_json(basis),
        hits=tuple(hits),
        coverage=merged_coverage,
        deterministic=deterministic,
        errors=merged_errors,
    )


def _lexical_policy(policy: Mapping[str, Any] | None) -> dict[str, Any]:
    selected = {**DEFAULT_LEXICAL_POLICY, **dict(policy or {})}
    selected["field_weights"] = {
        **DEFAULT_LEXICAL_POLICY["field_weights"],
        **dict((policy or {}).get("field_weights") or {}),
    }
    if selected["version"] != DEFAULT_LEXICAL_POLICY["version"]:
        raise ValueError("unsupported lexical policy version")
    k1 = float(selected["k1"])
    b = float(selected["b"])
    weights = [float(value) for value in selected["field_weights"].values()]
    if (
        not math.isfinite(k1)
        or not math.isfinite(b)
        or k1 <= 0
        or not 0 <= b <= 1
        or not weights
        or any(not math.isfinite(value) or value < 0 for value in weights)
        or not any(value > 0 for value in weights)
    ):
        raise ValueError("BM25 policy parameters are invalid")
    selected["k1"] = k1
    selected["b"] = b
    selected["field_weights"] = {
        str(key): float(value) for key, value in selected["field_weights"].items()
    }
    return selected


def _terms(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(term for value in values for term in lexical_terms(value))


def _norm(value: str) -> str:
    return " ".join(str(value).strip().lower().split())


def _candidate_limit(query: KnowledgeQuery) -> int:
    return query.page_offset + query.max_results


__all__ = [
    "DEFAULT_LEXICAL_POLICY",
    "KnowledgeComponentResult",
    "KnowledgeQuery",
    "KnowledgeRetrievalCoverage",
    "KnowledgeRetrievalHit",
    "KnowledgeRetrievalResult",
    "evaluate_ranked_refs",
    "search_fielded_lexical",
]
