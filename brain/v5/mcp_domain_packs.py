"""MCP wrappers for read-only domain-pack catalog surfaces."""

from __future__ import annotations

from brain.v5.domain_packs import describe_domain_packs
from brain.v5.models import ClaimRecord
from brain.v5.public_surfaces import require_valid_public_surface


def aitp_v5_list_domain_packs() -> dict:
    """Return the read-only AITP v5 domain-pack catalog."""

    return require_valid_public_surface("domain_pack_catalog", describe_domain_packs())


def aitp_v5_suggest_domain_packs_for_claim(
    *,
    statement: str,
    topic_id: str = "ad_hoc",
    evidence_profile: str = "unknown",
    confidence_state: str = "hypothesis",
    active_uncertainty: str = "ad_hoc_domain_pack_suggestion",
    scope: str = "",
    strongest_failure_mode: str = "",
) -> dict:
    """Suggest read-only domain packs from a claim-like text packet."""

    claim = ClaimRecord(
        claim_id="ad-hoc-domain-pack-suggestion",
        topic_id=topic_id or "ad_hoc",
        statement=statement,
        evidence_profile=evidence_profile or "unknown",
        confidence_state=confidence_state or "hypothesis",
        active_uncertainty=active_uncertainty or "ad_hoc_domain_pack_suggestion",
        scope=scope,
        strongest_failure_mode=strongest_failure_mode,
    )
    return require_valid_public_surface(
        "domain_pack_catalog",
        describe_domain_packs(claim=claim, selection_scope="suggested_for_claim"),
    )
