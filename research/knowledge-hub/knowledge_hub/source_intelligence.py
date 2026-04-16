from __future__ import annotations

import hashlib
import re
from typing import Any

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "with",
}

ARXIV_RE = re.compile(r"\b(?:arxiv:)?(?P<id>\d{4}\.\d{4,5}(?:v\d+)?)\b", re.IGNORECASE)
DOI_RE = re.compile(r"\b10\.\d{4,9}/[^\s<>{}\[\]|\"']+", re.IGNORECASE)

REGIME_PATTERNS = (
    "strong coupling",
    "weak coupling",
    "continuum limit",
    "perturbative",
    "non-relativistic",
    "relativistic",
    "finite temperature",
    "zero temperature",
)

ASSUMPTION_PATTERNS = (
    re.compile(r"\bassum(?:e|es|ed|ing)\s+(?P<clause>[^.;,\n]+)", re.IGNORECASE),
    re.compile(r"\bunder the assumption(?:s)?\s+(?:that\s+)?(?P<clause>[^.;,\n]+)", re.IGNORECASE),
)

NOTATION_PATTERNS = (
    re.compile(r"\b(?P<symbol>[A-Za-z][A-Za-z0-9_-]*)\s+(?:denotes|represents|labels|means)\s+(?P<meaning>[^.;,\n]+)", re.IGNORECASE),
    re.compile(r"\b(?P<symbol>[A-Za-z][A-Za-z0-9_-]*)\s+for\s+(?P<meaning>[^.;,\n]+)", re.IGNORECASE),
)

CONTRADICTION_PAIRS = (
    ("non-relativistic", "relativistic"),
    ("strong coupling", "weak coupling"),
    ("zero temperature", "finite temperature"),
)

FIDELITY_RANK = {
    "peer_reviewed": 4,
    "preprint": 3,
    "local_note": 2,
    "web": 1,
    "unknown": 0,
}
RELEVANCE_RANK = {
    "canonical": 4,
    "must_read": 3,
    "strongly_relevant": 2,
    "useful": 1,
    "irrelevant": 0,
}
RELEVANCE_TIERS = tuple(RELEVANCE_RANK.keys())
ROLE_LABEL_KEYWORDS = {
    "foundational": ("foundational", "foundation", "seminal", "classic"),
    "key_result": ("key result", "main result", "we show", "we prove", "we derive"),
    "modern_reference": ("modern", "recent", "state of the art", "current"),
    "review": ("review", "survey", "overview"),
    "technical_tool": ("algorithm", "implementation", "workflow", "tool", "benchmark", "solver"),
    "limitation": ("limitation", "limitations", "open problem", "future work", "failure"),
    "application_connection": ("application", "applied", "experiment", "phenomenology"),
}

METHOD_SPECIFICITY_RULES = (
    ("formal_derivation", "high", ("we derive", "derivation", "theorem", "lemma", "proof obligation", "we prove", "proof")),
    (
        "numerical_benchmark",
        "high",
        ("benchmark", "exact diagonalization", "simulation", "numerically", "monte carlo", "finite-size scaling"),
    ),
    (
        "implementation_workflow",
        "high",
        ("implementation", "algorithm", "workflow", "pipeline", "code path", "script", "solver"),
    ),
    ("survey_overview", "low", ("survey", "overview", "review", "perspective", "introduction")),
)


def _slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-+", "-", lowered).strip("-")
    return lowered or "source"


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = str(value or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def normalize_role_labels(values: list[Any] | None) -> list[str]:
    normalized: list[str] = []
    for value in values or []:
        token = str(value or "").strip().lower()
        if token:
            normalized.append(token)
    return _dedupe_strings(normalized)


def _valid_relevance_tier(value: Any) -> str:
    candidate = str(value or "").strip().lower()
    return candidate if candidate in RELEVANCE_RANK else ""


def infer_source_relevance(
    *,
    source_type: str,
    title: str,
    summary: str,
    provenance: dict[str, Any] | None,
    canonical_source_id: str,
    explicit_relevance_tier: str | None = None,
    explicit_role_labels: list[Any] | None = None,
) -> tuple[str, str, list[str]]:
    provenance = provenance or {}
    text = " ".join(
        [
            str(title or "").strip().lower(),
            str(summary or "").strip().lower(),
        ]
    )
    role_labels = normalize_role_labels(
        list(explicit_role_labels or [])
        or list(provenance.get("role_labels") or [])
    )
    for label, keywords in ROLE_LABEL_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            role_labels = _dedupe_strings([*role_labels, label])

    explicit_tier = _valid_relevance_tier(explicit_relevance_tier or provenance.get("relevance_tier"))
    if explicit_tier:
        return explicit_tier, "explicit_source_metadata", role_labels

    lower_source_type = str(source_type or "").strip().lower()
    if "review" in role_labels:
        return "must_read", "review_keyword", role_labels
    if any(keyword in text for keyword in ("foundational", "seminal", "classic")):
        return "canonical", "foundational_keyword", role_labels
    if lower_source_type in {"paper", "pdf"}:
        return "strongly_relevant", "formal_source_default", role_labels
    if lower_source_type == "local_note":
        return "useful", "local_note_default", role_labels
    if lower_source_type in {"url", "web_page", "video", "transcript", "conversation"}:
        return "useful", "supplementary_source_default", role_labels
    if canonical_source_id.startswith("source_identity:doi:") or canonical_source_id.startswith("source_identity:arxiv:"):
        return "strongly_relevant", "canonical_identity_default", role_labels
    return "useful", "topic_local_default", role_labels


def normalize_arxiv_id(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    raw = raw.rsplit("/", 1)[-1]
    raw = raw.lower().removeprefix("arxiv:")
    return re.sub(r"v\d+$", "", raw)


def normalize_doi(value: str) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return ""
    raw = raw.removeprefix("https://doi.org/")
    raw = raw.removeprefix("http://doi.org/")
    raw = raw.rstrip(").,;")
    return raw


def derive_canonical_source_id(
    *,
    source_type: str,
    title: str,
    summary: str,
    provenance: dict[str, Any] | None,
    locator: dict[str, Any] | None,
) -> str:
    provenance = provenance or {}
    locator = locator or {}

    doi = normalize_doi(
        provenance.get("doi")
        or provenance.get("journal_url")
        or provenance.get("source_url")
    )
    if doi.startswith("10."):
        return f"source_identity:doi:{_slugify(doi)}"

    arxiv_id = normalize_arxiv_id(
        provenance.get("arxiv_id")
        or provenance.get("versioned_id")
        or provenance.get("abs_url")
    )
    if arxiv_id:
        return f"source_identity:arxiv:{_slugify(arxiv_id)}"

    backend_id = str(provenance.get("backend_id") or "").strip()
    backend_relative_path = str(locator.get("backend_relative_path") or "").strip()
    if backend_id and backend_relative_path:
        fingerprint = hashlib.sha1(f"{backend_id}::{backend_relative_path}".encode("utf-8")).hexdigest()[:16]
        return f"source_identity:backend:{fingerprint}"

    absolute_path = str(provenance.get("absolute_path") or "").strip()
    if absolute_path:
        fingerprint = hashlib.sha1(absolute_path.encode("utf-8")).hexdigest()[:16]
        return f"source_identity:file:{fingerprint}"

    fingerprint = hashlib.sha1(
        f"{source_type}::{title.strip().lower()}::{summary.strip().lower()}".encode("utf-8")
    ).hexdigest()[:16]
    return f"source_identity:content:{fingerprint}"


def extract_reference_ids(*, text: str, provenance: dict[str, Any] | None = None) -> list[str]:
    provenance = provenance or {}
    combined = " ".join(
        [
            str(text or ""),
            str(provenance.get("doi") or ""),
            str(provenance.get("references") or ""),
        ]
    )
    refs: list[str] = []
    refs.extend(f"arxiv:{_slugify(normalize_arxiv_id(match.group('id')))}" for match in ARXIV_RE.finditer(combined))
    refs.extend(f"doi:{_slugify(normalize_doi(match.group(0)))}" for match in DOI_RE.finditer(combined))

    explicit_refs = provenance.get("references") or []
    if isinstance(explicit_refs, list):
        for value in explicit_refs:
            normalized = str(value or "").strip()
            if not normalized:
                continue
            lower = normalized.lower()
            if lower.startswith("doi:"):
                refs.append(f"doi:{_slugify(lower.split(':', 1)[1])}")
            elif lower.startswith("arxiv:"):
                refs.append(f"arxiv:{_slugify(lower.split(':', 1)[1])}")
            else:
                refs.append(normalized)

    normalized_refs: list[str] = []
    for ref in refs:
        token = str(ref or "").strip()
        if not token:
            continue
        if token.startswith("doi:") or token.startswith("arxiv:"):
            normalized_refs.append(token)
        elif "/" in token or token.startswith("10."):
            normalized_refs.append(f"doi:{_slugify(token)}")
        else:
            normalized_refs.append(token)
    return _dedupe_strings(normalized_refs)


def extract_neighbor_terms(*, title: str, summary: str, limit: int = 12) -> list[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", f"{title} {summary}".lower())
    filtered = [token for token in tokens if token not in STOPWORDS]
    ordered = _dedupe_strings(filtered)
    return ordered[:limit]


def detect_assumptions(*, text: str) -> list[str]:
    assumptions: list[str] = []
    for pattern in ASSUMPTION_PATTERNS:
        for match in pattern.finditer(text):
            clause = re.sub(r"\s+", " ", str(match.group("clause") or "").strip())
            if clause:
                assumptions.append(clause)
    return _dedupe_strings(assumptions)


def detect_regimes(*, text: str) -> list[str]:
    lowered = text.lower()
    return [phrase for phrase in REGIME_PATTERNS if phrase in lowered]


def infer_method_specificity(*, text: str, source_type: str) -> tuple[str, str, str]:
    lowered = str(text or "").lower()
    for family, tier, needles in METHOD_SPECIFICITY_RULES:
        for needle in needles:
            if needle in lowered:
                return family, tier, needle

    normalized_source_type = str(source_type or "").strip().lower()
    if normalized_source_type in {"benchmark", "code", "implementation", "numerical", "experiment"}:
        return "numerical_benchmark", "medium", normalized_source_type
    if normalized_source_type in {"thesis", "paper", "article", "book", "lecture", "derivation"}:
        return "unspecified_method", "low", normalized_source_type or "source_type"
    return "unspecified_method", "low", normalized_source_type or "summary"


def infer_reading_depth_label(
    *,
    source_type: str,
    provenance: dict[str, Any] | None,
    locator: dict[str, Any] | None,
) -> str:
    provenance = provenance or {}
    locator = locator or {}
    if source_type == "local_note":
        return "full_read"
    if str(locator.get("extracted_source_dir") or "").strip() or str(locator.get("downloaded_source_bundle") or "").strip():
        return "full_read"
    if str(provenance.get("pdf_url") or "").strip() or str(provenance.get("abs_url") or "").strip():
        return "abstract_only"
    return "skim"


def detect_notation_candidates(*, text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for pattern in NOTATION_PATTERNS:
        for match in pattern.finditer(text):
            symbol = re.sub(r"\s+", " ", str(match.group("symbol") or "").strip())
            meaning = re.sub(r"\s+", " ", str(match.group("meaning") or "").strip())
            key = (symbol.lower(), meaning.lower())
            if not symbol or not meaning or key in seen:
                continue
            seen.add(key)
            rows.append({"symbol": symbol, "meaning": meaning})
    return rows


def detect_contradiction_candidates(
    *,
    existing_rows: list[dict[str, Any]],
    assumptions: list[str],
    regimes: list[str],
) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    incoming_assumptions = [str(item).strip() for item in assumptions if str(item).strip()]
    incoming_regimes = [str(item).strip() for item in regimes if str(item).strip()]
    incoming_rows = [("assumption", row) for row in incoming_assumptions] + [
        ("regime", row) for row in incoming_regimes
    ]
    for row in existing_rows:
        existing_assumptions = [str(item).strip() for item in (row.get("assumptions") or []) if str(item).strip()]
        existing_regimes = [str(item).strip() for item in (row.get("regimes") or []) if str(item).strip()]
        existing_rows_with_kind = [("assumption", item) for item in existing_assumptions] + [
            ("regime", item) for item in existing_regimes
        ]
        for left, right in CONTRADICTION_PAIRS:
            for incoming_kind, incoming_value in incoming_rows:
                incoming_text = incoming_value.lower()
                if left not in incoming_text and right not in incoming_text:
                    continue
                for existing_kind, existing_value in existing_rows_with_kind:
                    existing_text = existing_value.lower()
                    if left in incoming_text and right in existing_text:
                        source_basis = incoming_value
                        against_basis = existing_value
                        detail = f"{left} vs {right}"
                    elif right in incoming_text and left in existing_text:
                        source_basis = incoming_value
                        against_basis = existing_value
                        detail = f"{right} vs {left}"
                    else:
                        continue
                    kind = "regime_mismatch" if "regime" in {incoming_kind, existing_kind} else "assumption_conflict"
                    key = (
                        str(row.get("source_id") or ""),
                        detail,
                        incoming_kind,
                        incoming_value.lower(),
                        existing_value.lower(),
                    )
                    if key in seen:
                        continue
                    seen.add(key)
                    candidates.append(
                        {
                            "kind": kind,
                            "against_source_id": str(row.get("source_id") or ""),
                            "detail": detail,
                            "comparison_basis": "regime_rows"
                            if "regime" in {incoming_kind, existing_kind}
                            else "assumption_rows",
                            "source_basis_type": incoming_kind,
                            "source_basis_summary": source_basis,
                            "against_basis_type": existing_kind,
                            "against_basis_summary": against_basis,
                        }
                    )
    return candidates


def detect_notation_tension_candidates(
    *,
    existing_rows: list[dict[str, Any]],
    notation_candidates: list[dict[str, str]],
) -> list[dict[str, str]]:
    tensions: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in existing_rows:
        for existing_binding in list(row.get("notation_candidates") or []):
            existing_symbol = str(existing_binding.get("symbol") or "").strip()
            existing_meaning = str(existing_binding.get("meaning") or "").strip().lower()
            if not existing_symbol or not existing_meaning:
                continue
            for incoming_binding in notation_candidates:
                incoming_symbol = str(incoming_binding.get("symbol") or "").strip()
                incoming_meaning = str(incoming_binding.get("meaning") or "").strip().lower()
                if not incoming_symbol or not incoming_meaning:
                    continue
                if incoming_meaning != existing_meaning or incoming_symbol.lower() == existing_symbol.lower():
                    continue
                key = (existing_meaning, existing_symbol.lower(), incoming_symbol.lower())
                if key in seen:
                    continue
                seen.add(key)
                tensions.append(
                    {
                        "meaning": existing_meaning,
                        "existing_symbol": existing_symbol,
                        "incoming_symbol": incoming_symbol,
                        "against_source_id": str(row.get("source_id") or ""),
                    }
                )
    return tensions


def infer_source_fidelity(
    *,
    source_type: str,
    provenance: dict[str, Any] | None,
    canonical_source_id: str,
) -> tuple[str, str]:
    provenance = provenance or {}
    canonical_source_id = str(canonical_source_id or "").strip()
    lower_source_type = str(source_type or "").strip().lower()
    abs_url = str(provenance.get("abs_url") or "").strip().lower()
    source_url = str(provenance.get("source_url") or "").strip().lower()
    if canonical_source_id.startswith("source_identity:doi:") or normalize_doi(str(provenance.get("doi") or "")):
        return "peer_reviewed", "canonical_doi_identity"
    if canonical_source_id.startswith("source_identity:arxiv:") or "arxiv.org" in abs_url or "arxiv.org" in source_url:
        return "preprint", "arxiv_identity"
    if lower_source_type == "local_note":
        return "local_note", "local_note_source"
    if lower_source_type in {"web", "website", "blog", "web_note"}:
        return "web", "web_source"
    return "unknown", "source_type_only"


def build_source_intelligence(
    *,
    topic_slug: str,
    source_rows: list[dict[str, Any]],
    global_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    canonical_source_ids = _dedupe_strings(
        [
            str(row.get("canonical_source_id") or "").strip()
            or derive_canonical_source_id(
                source_type=str(row.get("source_type") or ""),
                title=str(row.get("title") or ""),
                summary=str(row.get("summary") or ""),
                provenance=row.get("provenance") or {},
                locator=row.get("locator") or {},
            )
            for row in source_rows
        ]
    )

    citation_edges: list[dict[str, Any]] = []
    source_neighbors: list[dict[str, Any]] = []
    fidelity_rows: list[dict[str, str]] = []
    relevance_rows: list[dict[str, Any]] = []
    seen_neighbor_keys: set[tuple[str, str, str]] = set()

    local_rows: list[dict[str, Any]] = []
    for row in source_rows:
        local_rows.append(
            {
                **row,
                "canonical_source_id": str(row.get("canonical_source_id") or "").strip()
                or derive_canonical_source_id(
                    source_type=str(row.get("source_type") or ""),
                    title=str(row.get("title") or ""),
                    summary=str(row.get("summary") or ""),
                    provenance=row.get("provenance") or {},
                    locator=row.get("locator") or {},
                ),
                "references": _dedupe_strings(list(row.get("references") or [])),
                "neighbor_terms": extract_neighbor_terms(
                    title=str(row.get("title") or ""),
                    summary=str(row.get("summary") or ""),
                ),
            }
        )
    for row in local_rows:
        fidelity_tier, fidelity_basis = infer_source_fidelity(
            source_type=str(row.get("source_type") or ""),
            provenance=row.get("provenance") if isinstance(row.get("provenance"), dict) else {},
            canonical_source_id=str(row.get("canonical_source_id") or ""),
        )
        fidelity_rows.append(
            {
                "source_id": str(row.get("source_id") or ""),
                "canonical_source_id": str(row.get("canonical_source_id") or ""),
                "source_type": str(row.get("source_type") or ""),
                "fidelity_tier": fidelity_tier,
                "fidelity_basis": fidelity_basis,
            }
        )
        relevance_tier, relevance_basis, role_labels = infer_source_relevance(
            source_type=str(row.get("source_type") or ""),
            title=str(row.get("title") or ""),
            summary=str(row.get("summary") or ""),
            provenance=row.get("provenance") if isinstance(row.get("provenance"), dict) else {},
            canonical_source_id=str(row.get("canonical_source_id") or ""),
            explicit_relevance_tier=str(row.get("relevance_tier") or ""),
            explicit_role_labels=row.get("role_labels") if isinstance(row.get("role_labels"), list) else [],
        )
        relevance_rows.append(
            {
                "source_id": str(row.get("source_id") or ""),
                "canonical_source_id": str(row.get("canonical_source_id") or ""),
                "source_type": str(row.get("source_type") or ""),
                "relevance_tier": relevance_tier,
                "relevance_basis": relevance_basis,
                "role_labels": role_labels,
            }
        )

    local_source_ids = {str(row.get("source_id") or "").strip() for row in local_rows}

    for row in local_rows:
        source_id = str(row.get("source_id") or "").strip()
        canonical_id = str(row.get("canonical_source_id") or "").strip()
        references = list(row.get("references") or [])
        for target_ref in references:
            citation_edges.append(
                {
                    "source_id": source_id,
                    "target_ref": target_ref,
                    "target_source_id": None,
                    "relation": "cites",
                }
            )

        local_terms = set(row.get("neighbor_terms") or [])
        local_refs = set(references)
        for global_row in global_rows:
            neighbor_source_id = str(global_row.get("source_id") or "").strip()
            if not neighbor_source_id or neighbor_source_id == source_id:
                continue
            neighbor_topic_slug = str(global_row.get("topic_slug") or "").strip()
            neighbor_canonical_id = str(global_row.get("canonical_source_id") or "").strip()
            neighbor_refs = set(global_row.get("references") or [])
            neighbor_terms = set(global_row.get("neighbor_terms") or [])
            relation_kind = ""
            if canonical_id and canonical_id == neighbor_canonical_id:
                relation_kind = "shared_identity"
            elif local_refs and neighbor_refs and local_refs.intersection(neighbor_refs):
                relation_kind = "shared_reference"
            elif local_terms and neighbor_terms and len(local_terms.intersection(neighbor_terms)) >= 2:
                relation_kind = "keyword_overlap"
            if not relation_kind:
                continue
            key = (source_id, neighbor_source_id, relation_kind)
            if key in seen_neighbor_keys:
                continue
            seen_neighbor_keys.add(key)
            source_neighbors.append(
                {
                    "source_id": source_id,
                    "neighbor_source_id": neighbor_source_id,
                    "neighbor_topic_slug": neighbor_topic_slug,
                    "neighbor_canonical_source_id": neighbor_canonical_id or None,
                    "relation_kind": relation_kind,
                    "shared_reference_count": len(local_refs.intersection(neighbor_refs)),
                    "shared_term_count": len(local_terms.intersection(neighbor_terms)),
                    "cross_topic": bool(neighbor_topic_slug and neighbor_topic_slug != topic_slug),
                }
            )

    source_neighbors.sort(
        key=lambda row: (
            {"shared_identity": 0, "shared_reference": 1, "keyword_overlap": 2}.get(
                str(row.get("relation_kind") or ""),
                9,
            ),
            str(row.get("neighbor_topic_slug") or ""),
            str(row.get("neighbor_source_id") or ""),
        )
    )
    citation_edges.sort(key=lambda row: (str(row.get("source_id") or ""), str(row.get("target_ref") or "")))

    cross_topic_match_count = len(
        {
            str(row.get("neighbor_source_id") or "")
            for row in source_neighbors
            if row.get("cross_topic")
        }
    )
    counts_by_tier: dict[str, int] = {}
    for row in fidelity_rows:
        tier = str(row.get("fidelity_tier") or "unknown")
        counts_by_tier[tier] = counts_by_tier.get(tier, 0) + 1
    tiers_present = [tier for tier, count in counts_by_tier.items() if count > 0]
    strongest_tier = max(tiers_present, key=lambda item: (FIDELITY_RANK.get(item, -1), item), default="unknown")
    weakest_tier = min(tiers_present, key=lambda item: (FIDELITY_RANK.get(item, 99), item), default="unknown")
    counts_by_tier = dict(
        sorted(counts_by_tier.items(), key=lambda item: (-FIDELITY_RANK.get(item[0], -1), item[0]))
    )
    relevance_counts_by_tier: dict[str, int] = {}
    role_label_counts: dict[str, int] = {}
    for row in relevance_rows:
        tier = str(row.get("relevance_tier") or "useful")
        relevance_counts_by_tier[tier] = relevance_counts_by_tier.get(tier, 0) + 1
        for label in row.get("role_labels") or []:
            normalized_label = str(label or "").strip().lower()
            if normalized_label:
                role_label_counts[normalized_label] = role_label_counts.get(normalized_label, 0) + 1
    relevance_tiers_present = [tier for tier, count in relevance_counts_by_tier.items() if count > 0]
    strongest_relevance_tier = max(
        relevance_tiers_present,
        key=lambda item: (RELEVANCE_RANK.get(item, -1), item),
        default="irrelevant",
    )
    weakest_relevance_tier = min(
        relevance_tiers_present,
        key=lambda item: (RELEVANCE_RANK.get(item, 99), item),
        default="irrelevant",
    )
    relevance_counts_by_tier = dict(
        sorted(relevance_counts_by_tier.items(), key=lambda item: (-RELEVANCE_RANK.get(item[0], -1), item[0]))
    )
    role_label_counts = dict(sorted(role_label_counts.items(), key=lambda item: (-item[1], item[0])))

    return {
        "canonical_source_ids": canonical_source_ids,
        "cross_topic_match_count": cross_topic_match_count,
        "fidelity_rows": fidelity_rows,
        "fidelity_summary": {
            "source_count": len(fidelity_rows),
            "counts_by_tier": counts_by_tier,
            "strongest_tier": strongest_tier,
            "weakest_tier": weakest_tier,
        },
        "relevance_rows": relevance_rows,
        "relevance_summary": {
            "source_count": len(relevance_rows),
            "counts_by_tier": relevance_counts_by_tier,
            "strongest_tier": strongest_relevance_tier,
            "weakest_tier": weakest_relevance_tier,
            "role_label_counts": role_label_counts,
        },
        "citation_edges": citation_edges,
        "source_neighbors": source_neighbors,
        "neighbor_signal_count": len(source_neighbors),
    }
