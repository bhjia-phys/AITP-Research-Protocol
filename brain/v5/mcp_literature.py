"""MCP wrappers for literature intake assistant surfaces."""

from __future__ import annotations

from pathlib import Path

from brain.v5.literature_comparison_draft import build_literature_comparison_draft
from brain.v5.literature_corpus_extraction_artifact import build_literature_corpus_extraction_artifact
from brain.v5.literature_extraction_report import build_literature_extraction_report
from brain.v5.literature_intake import record_literature_candidate, suggest_literature_intake
from brain.v5.literature_reading_route import build_literature_reading_route
from brain.v5.literature_source_extraction import build_literature_source_extraction_candidates
from brain.v5.literature_source_set_readiness import build_literature_source_set_readiness
from brain.v5.literature_source_review_handoff import build_literature_source_review_handoff
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import init_workspace


def aitp_v5_suggest_literature_intake(
    base: str,
    *,
    session_id: str,
    uri: str,
    label: str,
    external_id: str = "",
    short_summary: str = "",
    detected_relevance: str = "",
    optional_claim_id: str = "",
    scoped_output: str = "",
    asset_type: str = "",
) -> dict:
    return require_valid_public_surface(
        "literature_intake_suggestion",
        suggest_literature_intake(
            init_workspace(Path(base)),
            session_id=session_id,
            uri=uri,
            label=label,
            external_id=external_id,
            short_summary=short_summary,
            detected_relevance=detected_relevance,
            optional_claim_id=optional_claim_id,
            scoped_output=scoped_output,
            asset_type=asset_type,
        ),
    )


def aitp_v5_record_literature_candidate(
    base: str,
    *,
    session_id: str,
    uri: str,
    label: str,
    external_id: str = "",
    short_summary: str = "",
    detected_relevance: str = "",
    optional_claim_id: str = "",
    scoped_output: str = "",
    asset_type: str = "",
) -> dict:
    return require_valid_public_surface(
        "literature_intake_record_result",
        record_literature_candidate(
            init_workspace(Path(base)),
            session_id=session_id,
            uri=uri,
            label=label,
            external_id=external_id,
            short_summary=short_summary,
            detected_relevance=detected_relevance,
            optional_claim_id=optional_claim_id,
            scoped_output=scoped_output,
            asset_type=asset_type,
        ),
    )


def aitp_v5_build_literature_source_review_handoff(
    base: str,
    *,
    session_id: str,
    uri: str,
    label: str,
    external_id: str = "",
    short_summary: str = "",
    detected_relevance: str = "",
    optional_claim_id: str = "",
    scoped_output: str = "",
    reviewed_refs: list[str] | None = None,
) -> dict:
    return require_valid_public_surface(
        "literature_source_review_handoff",
        build_literature_source_review_handoff(
            init_workspace(Path(base)),
            session_id=session_id,
            uri=uri,
            label=label,
            external_id=external_id,
            short_summary=short_summary,
            detected_relevance=detected_relevance,
            optional_claim_id=optional_claim_id,
            scoped_output=scoped_output,
            reviewed_refs=reviewed_refs or [],
        ),
    )


def aitp_v5_build_literature_comparison_draft(
    base: str,
    *,
    session_id: str,
    comparison_question: str,
    source_refs: list[str],
    dimensions: list[str] | None = None,
    optional_claim_id: str = "",
    rationale: str = "",
) -> dict:
    return require_valid_public_surface(
        "literature_comparison_draft",
        build_literature_comparison_draft(
            init_workspace(Path(base)),
            session_id=session_id,
            comparison_question=comparison_question,
            source_refs=source_refs,
            dimensions=dimensions or [],
            optional_claim_id=optional_claim_id,
            rationale=rationale,
        ),
    )


def aitp_v5_build_literature_reading_route(
    base: str,
    *,
    session_id: str,
    reading_question: str,
    source_refs: list[str],
    route_type: str = "auto",
    focus_terms: list[str] | None = None,
    optional_claim_id: str = "",
    rationale: str = "",
) -> dict:
    return require_valid_public_surface(
        "literature_reading_route",
        build_literature_reading_route(
            init_workspace(Path(base)),
            session_id=session_id,
            reading_question=reading_question,
            source_refs=source_refs,
            route_type=route_type,
            focus_terms=focus_terms or [],
            optional_claim_id=optional_claim_id,
            rationale=rationale,
        ),
    )


def aitp_v5_build_literature_source_extraction_candidates(
    base: str,
    *,
    session_id: str,
    source_refs: list[str],
    focus_terms: list[str] | None = None,
    extraction_modes: list[str] | None = None,
    optional_claim_id: str = "",
    rationale: str = "",
) -> dict:
    return require_valid_public_surface(
        "literature_source_extraction_candidates",
        build_literature_source_extraction_candidates(
            init_workspace(Path(base)),
            session_id=session_id,
            source_refs=source_refs,
            focus_terms=focus_terms or [],
            extraction_modes=extraction_modes or [],
            optional_claim_id=optional_claim_id,
            rationale=rationale,
        ),
    )


def aitp_v5_build_literature_extraction_report(
    base: str,
    *,
    session_id: str,
    source_refs: list[str],
    report_profile: str = "paper_learning",
    focus_terms: list[str] | None = None,
    optional_claim_id: str = "",
) -> dict:
    return require_valid_public_surface(
        "literature_extraction_report",
        build_literature_extraction_report(
            init_workspace(Path(base)),
            session_id=session_id,
            source_refs=source_refs,
            report_profile=report_profile,
            focus_terms=focus_terms or [],
            optional_claim_id=optional_claim_id,
        ),
    )


def aitp_v5_build_literature_corpus_extraction_artifact(
    base: str,
    *,
    session_id: str,
    chunk_ids: list[str],
    reference_location_ids: list[str],
    report_profile: str = "paper_learning",
    focus_terms: list[str] | None = None,
    optional_claim_id: str = "",
    artifact_intent: str = "corpus_backed_extraction_report",
) -> dict:
    return require_valid_public_surface(
        "literature_corpus_extraction_artifact",
        build_literature_corpus_extraction_artifact(
            init_workspace(Path(base)),
            session_id=session_id,
            chunk_ids=chunk_ids,
            reference_location_ids=reference_location_ids,
            report_profile=report_profile,
            focus_terms=focus_terms or [],
            optional_claim_id=optional_claim_id,
            artifact_intent=artifact_intent,
        ),
    )


def aitp_v5_build_literature_source_set_readiness(
    base: str,
    *,
    session_id: str,
    source_refs: list[str],
    optional_claim_id: str = "",
    readiness_scope: str = "source_set_learning",
) -> dict:
    return require_valid_public_surface(
        "literature_source_set_readiness",
        build_literature_source_set_readiness(
            init_workspace(Path(base)),
            session_id=session_id,
            source_refs=source_refs,
            optional_claim_id=optional_claim_id,
            readiness_scope=readiness_scope,
        ),
    )
