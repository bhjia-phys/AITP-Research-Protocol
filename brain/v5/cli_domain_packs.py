"""CLI handlers for read-only domain-pack catalog surfaces."""

from __future__ import annotations

from brain.v5.domain_packs import describe_domain_packs
from brain.v5.models import ClaimRecord
from brain.v5.public_surfaces import require_valid_public_surface


def add_domain_pack_parser(sp) -> None:
    domain = sp.add_parser("domain-pack")
    ds = domain.add_subparsers(dest="domain_pack_command", required=True)
    ds.add_parser("catalog")
    suggest = ds.add_parser("suggest")
    suggest.add_argument("--topic", default="ad_hoc", dest="topic_id")
    suggest.add_argument("--statement", required=True)
    suggest.add_argument("--evidence-profile", default="unknown")
    suggest.add_argument("--confidence-state", default="hypothesis")
    suggest.add_argument("--uncertainty", default="ad_hoc_domain_pack_suggestion")
    suggest.add_argument("--scope", default="")
    suggest.add_argument("--failure-mode", default="", dest="strongest_failure_mode")


def dispatch_domain_pack_command(args, _ws) -> dict:
    if args.domain_pack_command == "catalog":
        return require_valid_public_surface("domain_pack_catalog", describe_domain_packs())
    if args.domain_pack_command == "suggest":
        claim = ClaimRecord(
            claim_id="ad-hoc-domain-pack-suggestion",
            topic_id=args.topic_id or "ad_hoc",
            statement=args.statement,
            evidence_profile=args.evidence_profile or "unknown",
            confidence_state=args.confidence_state or "hypothesis",
            active_uncertainty=args.uncertainty or "ad_hoc_domain_pack_suggestion",
            scope=args.scope,
            strongest_failure_mode=args.strongest_failure_mode,
        )
        return require_valid_public_surface(
            "domain_pack_catalog",
            describe_domain_packs(claim=claim, selection_scope="suggested_for_claim"),
        )
    raise SystemExit(f"unsupported domain-pack command: {args.domain_pack_command}")
