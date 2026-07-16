"""Conservative formula normalization and retrieval."""

from __future__ import annotations

import re
import math
from typing import Any, Mapping

from brain.v5.knowledge_retrieval import (
    KnowledgeComponentResult,
    KnowledgeQuery,
    _component_result,
    _candidate_limit,
    _eligible_items,
    _hit,
)
from brain.v5.knowledge_snapshot import KnowledgeSnapshot


DEFAULT_FORMULA_POLICY = {
    "version": "formula-normalization.v1",
    "exact_weight": 8.0,
    "token_weight": 2.0,
}
_TOKEN_RE = re.compile(r"\\?[A-Za-z]+(?:_[A-Za-z0-9{}]+|\^[A-Za-z0-9{}]+)*|[-+*/=()]|\d+(?:\.\d+)?")


def normalize_formula(
    expression: str,
    *,
    dummy_symbols: Mapping[str, str] | None = None,
    commutative_product_safe: bool = False,
) -> str:
    """Normalize harmless syntax while preserving sign, order, and indices."""

    value = str(expression or "").strip()
    for left, right in (("\\(", "\\)"), ("\\[", "\\]"), ("$", "$")):
        if value.startswith(left) and value.endswith(right):
            value = value[len(left) : len(value) - len(right)]
    value = value.replace("\\left", "").replace("\\right", "")
    value = value.replace("\\cdot", "*").replace("\\,", "")
    value = re.sub(r"\\([A-Za-z]+)", r"\1", value)
    substitutions = dict(dummy_symbols or {})
    if substitutions:
        for source, target in sorted(
            substitutions.items(),
            key=lambda item: (-len(item[0]), item[0]),
        ):
            value = re.sub(
                rf"(?<![A-Za-z0-9]){re.escape(source)}(?![A-Za-z0-9])",
                target,
                value,
            )
    value = re.sub(r"\s+", "", value)
    if commutative_product_safe and _safe_product(value):
        left, separator, right = value.partition("=")
        target = right if separator else left
        factors = sorted(part for part in target.split("*") if part)
        normalized = "*".join(factors)
        value = f"{left}={normalized}" if separator else normalized
    return value


def search_formula(
    snapshot: KnowledgeSnapshot,
    query: KnowledgeQuery,
    policy: Mapping[str, Any] | None = None,
) -> KnowledgeComponentResult:
    selected = _formula_policy(policy)
    if not query.formula.strip():
        return _component_result(
            component="formula",
            version=str(selected["version"]),
            status="absent",
            snapshot=snapshot,
            hits=(),
            coverage={
                "reason": "query_has_no_formula",
                "checked_items": 0,
                "projection_source": "bounded_snapshot_formula_fields",
                "sidecar_status": "not_configured",
            },
            policy=selected,
        )
    eligible, excluded = _eligible_items(snapshot, query)
    dummy_symbols = dict(query.formula_dummy_symbols)
    normalized_query = normalize_formula(
        query.formula,
        dummy_symbols=dummy_symbols,
        commutative_product_safe=query.formula_commutative_product_safe,
    )
    query_tokens = set(_formula_tokens(normalized_query))
    scored = []
    for item, lane in eligible:
        for original in item.fields.get("formula", ()):
            normalized = normalize_formula(
                original,
                dummy_symbols=dummy_symbols,
                commutative_product_safe=query.formula_commutative_product_safe,
            )
            candidate_tokens = set(_formula_tokens(normalized))
            exact = normalized == normalized_query
            overlap = len(query_tokens.intersection(candidate_tokens)) / len(query_tokens.union(candidate_tokens)) if query_tokens or candidate_tokens else 0.0
            score = (float(selected["exact_weight"]) if exact else 0.0) + float(selected["token_weight"]) * overlap
            if score > 0:
                scored.append((round(score, 12), item, lane, original, normalized, exact, overlap))
    best: dict[str, tuple] = {}
    for row in scored:
        prior = best.get(row[1].record_ref)
        if prior is None or row[0] > prior[0]:
            best[row[1].record_ref] = row
    ordered = sorted(best.values(), key=lambda row: (-row[0], row[1].record_ref))
    hits = tuple(
        _hit(
            item,
            component="formula",
            rank=index,
            score=score,
            lane=lane,
            field_scores={"formula_exact": float(exact), "formula_token_overlap": round(overlap, 12)},
            anchors={
                "original_formula": original,
                "normalized_formula": normalized,
                "query_normalized_formula": normalized_query,
                "dummy_symbols": dummy_symbols,
                "commutative_product_safe": query.formula_commutative_product_safe,
            },
        )
        for index, (score, item, lane, original, normalized, exact, overlap) in enumerate(
            ordered[: _candidate_limit(query)], start=1
        )
    )
    return _component_result(
        component="formula",
        version=str(selected["version"]),
        status="available",
        snapshot=snapshot,
        hits=hits,
        coverage={
            **excluded,
            "checked_items": len(eligible),
            "candidate_formula_count": len(scored),
            "returned_items": len(hits),
            "truncated": len(ordered) > len(hits),
            "projection_source": "bounded_snapshot_formula_fields",
            "sidecar_status": "not_configured",
        },
        policy=selected,
    )


def _formula_tokens(value: str) -> tuple[str, ...]:
    return tuple(match.group(0) for match in _TOKEN_RE.finditer(value))


def _formula_policy(policy: Mapping[str, Any] | None) -> dict[str, Any]:
    selected = {**DEFAULT_FORMULA_POLICY, **dict(policy or {})}
    if selected["version"] != DEFAULT_FORMULA_POLICY["version"]:
        raise ValueError("unsupported formula policy version")
    exact_weight = float(selected["exact_weight"])
    token_weight = float(selected["token_weight"])
    if (
        not math.isfinite(exact_weight)
        or not math.isfinite(token_weight)
        or exact_weight < 0
        or token_weight < 0
        or exact_weight + token_weight <= 0
    ):
        raise ValueError("formula policy weights must be finite and non-negative")
    return {
        **selected,
        "exact_weight": exact_weight,
        "token_weight": token_weight,
    }


def _safe_product(value: str) -> bool:
    target = value.partition("=")[2] if "=" in value else value
    return bool("*" in target and not any(token in target for token in ("+", "-", "/", "(", ")")))


__all__ = ["DEFAULT_FORMULA_POLICY", "normalize_formula", "search_formula"]
