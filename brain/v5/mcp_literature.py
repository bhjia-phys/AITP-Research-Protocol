"""MCP wrappers for literature intake assistant surfaces."""

from __future__ import annotations

from pathlib import Path

from brain.v5.literature_comparison_draft import build_literature_comparison_draft
from brain.v5.literature_intake import record_literature_candidate, suggest_literature_intake
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
