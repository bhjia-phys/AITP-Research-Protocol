from __future__ import annotations

import argparse
from typing import Any, Callable


def _parse_analytical_check(value: str) -> dict[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError(
            "analytical checks must use KIND=LABEL:STATUS or KIND=LABEL:STATUS:NOTE"
        )
    kind, remainder = value.split("=", 1)
    label, sep, status_note = remainder.partition(":")
    if not sep:
        raise argparse.ArgumentTypeError(
            "analytical checks must include label and status separated by ':'"
        )
    status, _, note = status_note.partition(":")
    kind = kind.strip()
    label = label.strip()
    status = status.strip().lower()
    note = note.strip()
    if not kind or not label or not status:
        raise argparse.ArgumentTypeError(
            "analytical checks must include kind, label, and status"
        )
    return {"kind": kind, "label": label, "status": status, "notes": note}


def register_review_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    *,
    parse_notation_binding: Callable[[str], dict[str, str]],
    parse_agent_vote: Callable[[str], dict[str, str]],
    parse_nearby_variant: Callable[[str], dict[str, str]],
) -> None:
    coverage_audit = subparsers.add_parser(
        "coverage-audit",
        help="Record theory coverage, notation, derivation, and consensus artifacts for a candidate",
    )
    coverage_audit.add_argument("--topic-slug", required=True)
    coverage_audit.add_argument("--candidate-id", required=True)
    coverage_audit.add_argument("--run-id")
    coverage_audit.add_argument("--updated-by", default="aitp-cli")
    coverage_audit.add_argument("--source-section", action="append", default=[])
    coverage_audit.add_argument("--covered-section", action="append", default=[])
    coverage_audit.add_argument("--equation-label", action="append", default=[])
    coverage_audit.add_argument("--notation-binding", action="append", default=[], type=parse_notation_binding)
    coverage_audit.add_argument("--derivation-node", action="append", default=[])
    coverage_audit.add_argument("--agent-vote", action="append", default=[], type=parse_agent_vote)
    coverage_audit.add_argument("--consensus-status", default="unanimous")
    coverage_audit.add_argument("--critical-unit-recall", type=float, default=1.0)
    coverage_audit.add_argument("--missing-anchor-count", type=int, default=0)
    coverage_audit.add_argument("--skeptic-major-gap-count", type=int, default=0)
    coverage_audit.add_argument("--supporting-regression-question-id", action="append", default=[])
    coverage_audit.add_argument("--supporting-oracle-id", action="append", default=[])
    coverage_audit.add_argument("--supporting-regression-run-id", action="append", default=[])
    coverage_audit.add_argument("--promotion-blocker", action="append", default=[])
    coverage_audit.add_argument("--followup-gap-id", action="append", default=[])
    coverage_audit.add_argument("--split-required", action="store_true")
    coverage_audit.add_argument("--cited-recovery-required", action="store_true")
    coverage_audit.add_argument("--topic-completion-status")
    coverage_audit.add_argument("--notes")
    coverage_audit.add_argument("--json", action="store_true")

    formal_theory_audit = subparsers.add_parser(
        "formal-theory-audit",
        help="Record durable faithfulness, comparator, provenance, and prerequisite-closure audits for a candidate",
    )
    formal_theory_audit.add_argument("--topic-slug", required=True)
    formal_theory_audit.add_argument("--candidate-id", required=True)
    formal_theory_audit.add_argument("--run-id")
    formal_theory_audit.add_argument("--updated-by", default="aitp-cli")
    formal_theory_audit.add_argument("--formal-theory-role", required=True)
    formal_theory_audit.add_argument("--statement-graph-role", required=True)
    formal_theory_audit.add_argument("--definition-trust-tier")
    formal_theory_audit.add_argument("--target-statement-id")
    formal_theory_audit.add_argument("--statement-graph-parent", action="append", default=[])
    formal_theory_audit.add_argument("--statement-graph-child", action="append", default=[])
    formal_theory_audit.add_argument("--informal-statement")
    formal_theory_audit.add_argument("--formal-target")
    formal_theory_audit.add_argument("--faithfulness-status", default="pending")
    formal_theory_audit.add_argument("--faithfulness-strategy")
    formal_theory_audit.add_argument("--faithfulness-notes")
    formal_theory_audit.add_argument("--comparator-audit-status", default="pending")
    formal_theory_audit.add_argument("--comparator-risk", action="append", default=[])
    formal_theory_audit.add_argument("--nearby-variant", action="append", default=[], type=parse_nearby_variant)
    formal_theory_audit.add_argument("--comparator-notes")
    formal_theory_audit.add_argument("--provenance-kind", default="generated_from_scratch")
    formal_theory_audit.add_argument("--attribution-requirement", action="append", default=[])
    formal_theory_audit.add_argument("--provenance-source", action="append", default=[])
    formal_theory_audit.add_argument("--provenance-notes")
    formal_theory_audit.add_argument("--prerequisite-closure-status", default="pending")
    formal_theory_audit.add_argument("--lean-prerequisite-id", action="append", default=[])
    formal_theory_audit.add_argument("--supporting-obligation-id", action="append", default=[])
    formal_theory_audit.add_argument("--formalization-blocker", action="append", default=[])
    formal_theory_audit.add_argument("--prerequisite-notes")
    formal_theory_audit.add_argument("--json", action="store_true")

    analytical_review = subparsers.add_parser(
        "analytical-review",
        help="Record durable analytical validation checks and their source-backed review context for a candidate",
    )
    analytical_review.add_argument("--topic-slug", required=True)
    analytical_review.add_argument("--candidate-id", required=True)
    analytical_review.add_argument("--run-id")
    analytical_review.add_argument("--updated-by", default="aitp-cli")
    analytical_review.add_argument("--check", action="append", default=[], type=_parse_analytical_check)
    analytical_review.add_argument("--source-anchor", action="append", default=[])
    analytical_review.add_argument("--assumption", action="append", default=[])
    analytical_review.add_argument("--regime-note")
    analytical_review.add_argument("--reading-depth", choices=["skim", "targeted", "deep"], default="targeted")
    analytical_review.add_argument("--summary")
    analytical_review.add_argument("--json", action="store_true")


def dispatch_review_command(args: argparse.Namespace, service: Any) -> dict[str, Any] | None:
    if args.command == "coverage-audit":
        return service.audit_theory_coverage(
            topic_slug=args.topic_slug,
            candidate_id=args.candidate_id,
            run_id=args.run_id,
            updated_by=args.updated_by,
            source_sections=args.source_section,
            covered_sections=args.covered_section,
            equation_labels=args.equation_label,
            notation_bindings=args.notation_binding,
            derivation_nodes=args.derivation_node,
            agent_votes=args.agent_vote,
            consensus_status=args.consensus_status,
            critical_unit_recall=args.critical_unit_recall,
            missing_anchor_count=args.missing_anchor_count,
            skeptic_major_gap_count=args.skeptic_major_gap_count,
            supporting_regression_question_ids=args.supporting_regression_question_id,
            supporting_oracle_ids=args.supporting_oracle_id,
            supporting_regression_run_ids=args.supporting_regression_run_id,
            promotion_blockers=args.promotion_blocker,
            split_required=args.split_required,
            cited_recovery_required=args.cited_recovery_required,
            followup_gap_ids=args.followup_gap_id,
            topic_completion_status=args.topic_completion_status,
            notes=args.notes,
        )
    if args.command == "formal-theory-audit":
        return service.audit_formal_theory(
            topic_slug=args.topic_slug,
            candidate_id=args.candidate_id,
            run_id=args.run_id,
            updated_by=args.updated_by,
            formal_theory_role=args.formal_theory_role,
            statement_graph_role=args.statement_graph_role,
            definition_trust_tier=args.definition_trust_tier,
            target_statement_id=args.target_statement_id,
            statement_graph_parents=args.statement_graph_parent,
            statement_graph_children=args.statement_graph_child,
            informal_statement=args.informal_statement,
            formal_target=args.formal_target,
            faithfulness_status=args.faithfulness_status,
            faithfulness_strategy=args.faithfulness_strategy,
            faithfulness_notes=args.faithfulness_notes,
            comparator_audit_status=args.comparator_audit_status,
            comparator_risks=args.comparator_risk,
            nearby_variants=args.nearby_variant,
            comparator_notes=args.comparator_notes,
            provenance_kind=args.provenance_kind,
            attribution_requirements=args.attribution_requirement,
            provenance_sources=args.provenance_source,
            provenance_notes=args.provenance_notes,
            prerequisite_closure_status=args.prerequisite_closure_status,
            lean_prerequisite_ids=args.lean_prerequisite_id,
            supporting_obligation_ids=args.supporting_obligation_id,
            formalization_blockers=args.formalization_blocker,
            prerequisite_notes=args.prerequisite_notes,
        )
    if args.command == "analytical-review":
        return service.audit_analytical_review(
            topic_slug=args.topic_slug,
            candidate_id=args.candidate_id,
            run_id=args.run_id,
            updated_by=args.updated_by,
            checks=args.check,
            source_anchors=args.source_anchor,
            assumption_refs=args.assumption,
            regime_note=args.regime_note,
            reading_depth=args.reading_depth,
            summary=args.summary,
        )
    return None
