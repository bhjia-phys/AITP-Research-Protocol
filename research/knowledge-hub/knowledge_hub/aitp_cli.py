from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .aitp_service import AITPService


def _emit(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _parse_notation_binding(value: str) -> dict[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("notation bindings must use SYMBOL=MEANING")
    symbol, meaning = value.split("=", 1)
    symbol = symbol.strip()
    meaning = meaning.strip()
    if not symbol or not meaning:
        raise argparse.ArgumentTypeError("notation bindings must include both symbol and meaning")
    return {"symbol": symbol, "meaning": meaning}


def _parse_agent_vote(value: str) -> dict[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("agent votes must use ROLE=VERDICT or ROLE=VERDICT:NOTE")
    role, verdict_note = value.split("=", 1)
    role = role.strip()
    verdict, _, note = verdict_note.partition(":")
    verdict = verdict.strip()
    note = note.strip()
    if not role or not verdict:
        raise argparse.ArgumentTypeError("agent votes must include both role and verdict")
    return {"role": role, "verdict": verdict, "notes": note}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AITP kernel CLI")
    parser.add_argument("--kernel-root", type=Path)
    parser.add_argument("--repo-root", type=Path)

    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap = subparsers.add_parser("bootstrap", help="Bootstrap or update an AITP topic")
    bootstrap.add_argument("--topic")
    bootstrap.add_argument("--topic-slug")
    bootstrap.add_argument("--statement")
    bootstrap.add_argument("--run-id")
    bootstrap.add_argument("--control-note")
    bootstrap.add_argument("--updated-by", default="aitp-cli")
    bootstrap.add_argument("--arxiv-id", action="append", default=[])
    bootstrap.add_argument("--local-note-path", action="append", default=[])
    bootstrap.add_argument("--skill-query", action="append", default=[])
    bootstrap.add_argument("--human-request")
    bootstrap.add_argument("--json", action="store_true")

    new_topic = subparsers.add_parser("new-topic", help="Create a topic shell around an explicit research question")
    new_topic.add_argument("--topic", required=True)
    new_topic.add_argument("--question", required=True)
    new_topic.add_argument("--mode", choices=["formal_theory", "toy_numeric", "code_method"])
    new_topic.add_argument("--run-id")
    new_topic.add_argument("--control-note")
    new_topic.add_argument("--updated-by", default="aitp-cli")
    new_topic.add_argument("--arxiv-id", action="append", default=[])
    new_topic.add_argument("--local-note-path", action="append", default=[])
    new_topic.add_argument("--skill-query", action="append", default=[])
    new_topic.add_argument("--human-request")
    new_topic.add_argument("--json", action="store_true")

    resume = subparsers.add_parser("resume", help="Resume an existing AITP topic")
    resume.add_argument("--topic-slug", required=True)
    resume.add_argument("--run-id")
    resume.add_argument("--control-note")
    resume.add_argument("--updated-by", default="aitp-cli")
    resume.add_argument("--arxiv-id", action="append", default=[])
    resume.add_argument("--local-note-path", action="append", default=[])
    resume.add_argument("--skill-query", action="append", default=[])
    resume.add_argument("--human-request")
    resume.add_argument("--json", action="store_true")

    audit = subparsers.add_parser("audit", help="Run the AITP conformance audit")
    audit.add_argument("--topic-slug", required=True)
    audit.add_argument("--phase", choices=["entry", "exit"], default="entry")
    audit.add_argument("--updated-by", default="aitp-cli")
    audit.add_argument("--json", action="store_true")

    ci_check = subparsers.add_parser("ci-check", help="CI-friendly alias for the AITP conformance audit")
    ci_check.add_argument("--topic-slug", required=True)
    ci_check.add_argument("--phase", choices=["entry", "exit"], default="exit")
    ci_check.add_argument("--updated-by", default="aitp-cli")
    ci_check.add_argument("--json", action="store_true")

    baseline = subparsers.add_parser("baseline", help="Scaffold baseline-reproduction artifacts")
    baseline.add_argument("--topic-slug", required=True)
    baseline.add_argument("--run-id", required=True)
    baseline.add_argument("--title", required=True)
    baseline.add_argument("--reference", required=True)
    baseline.add_argument("--agreement-criterion", required=True)
    baseline.add_argument("--baseline-kind", default="public_example")
    baseline.add_argument("--updated-by", default="aitp-cli")
    baseline.add_argument("--notes")
    baseline.add_argument("--json", action="store_true")

    atomize = subparsers.add_parser("atomize", help="Scaffold atomic-understanding artifacts")
    atomize.add_argument("--topic-slug", required=True)
    atomize.add_argument("--run-id", required=True)
    atomize.add_argument("--method-title", required=True)
    atomize.add_argument("--updated-by", default="aitp-cli")
    atomize.add_argument("--scope-note")
    atomize.add_argument("--json", action="store_true")

    operation_init = subparsers.add_parser("operation-init", help="Register a reusable operation for trust tracking")
    operation_init.add_argument("--topic-slug", required=True)
    operation_init.add_argument("--run-id")
    operation_init.add_argument("--title", required=True)
    operation_init.add_argument("--kind", required=True)
    operation_init.add_argument("--updated-by", default="aitp-cli")
    operation_init.add_argument("--summary")
    operation_init.add_argument("--notes")
    operation_init.add_argument("--reference", action="append", default=[])
    operation_init.add_argument("--source-path", action="append", default=[])
    operation_init.add_argument("--baseline-required", action="store_true")
    operation_init.add_argument("--no-baseline-required", action="store_true")
    operation_init.add_argument("--atomic-required", action="store_true")
    operation_init.add_argument("--no-atomic-required", action="store_true")
    operation_init.add_argument("--json", action="store_true")

    operation_update = subparsers.add_parser("operation-update", help="Update operation trust status or artifacts")
    operation_update.add_argument("--topic-slug", required=True)
    operation_update.add_argument("--run-id")
    operation_update.add_argument("--operation", required=True)
    operation_update.add_argument("--updated-by", default="aitp-cli")
    operation_update.add_argument("--summary")
    operation_update.add_argument("--notes")
    operation_update.add_argument("--baseline-status")
    operation_update.add_argument("--atomic-status")
    operation_update.add_argument("--reference", action="append", default=[])
    operation_update.add_argument("--source-path", action="append", default=[])
    operation_update.add_argument("--artifact-path", action="append", default=[])
    operation_update.add_argument("--json", action="store_true")

    trust_audit = subparsers.add_parser("trust-audit", help="Audit operation trust for a validation run")
    trust_audit.add_argument("--topic-slug", required=True)
    trust_audit.add_argument("--run-id")
    trust_audit.add_argument("--updated-by", default="aitp-cli")
    trust_audit.add_argument("--json", action="store_true")

    capability_audit = subparsers.add_parser("capability-audit", help="Audit runtime/operator capability state")
    capability_audit.add_argument("--topic-slug", required=True)
    capability_audit.add_argument("--updated-by", default="aitp-cli")
    capability_audit.add_argument("--json", action="store_true")

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
    coverage_audit.add_argument("--notation-binding", action="append", default=[], type=_parse_notation_binding)
    coverage_audit.add_argument("--derivation-node", action="append", default=[])
    coverage_audit.add_argument("--agent-vote", action="append", default=[], type=_parse_agent_vote)
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

    loop = subparsers.add_parser("loop", help="Run the safe AITP auto-continue loop")
    loop.add_argument("--topic")
    loop.add_argument("--topic-slug")
    loop.add_argument("--statement")
    loop.add_argument("--run-id")
    loop.add_argument("--control-note")
    loop.add_argument("--updated-by", default="aitp-cli")
    loop.add_argument("--skill-query", action="append", default=[])
    loop.add_argument("--human-request")
    loop.add_argument("--max-auto-steps", type=int, default=4)
    loop.add_argument("--json", action="store_true")

    status = subparsers.add_parser("status", help="Show topic shell status and active research contract")
    status.add_argument("--topic-slug", required=True)
    status.add_argument("--updated-by", default="aitp-cli")
    status.add_argument("--json", action="store_true")

    next_cmd = subparsers.add_parser("next", help="Show the next bounded action and mandatory read set")
    next_cmd.add_argument("--topic-slug", required=True)
    next_cmd.add_argument("--updated-by", default="aitp-cli")
    next_cmd.add_argument("--json", action="store_true")

    work = subparsers.add_parser("work", help="Unified shell around bounded bootstrap and loop execution")
    work.add_argument("--topic")
    work.add_argument("--topic-slug")
    work.add_argument("--question")
    work.add_argument("--mode", choices=["formal_theory", "toy_numeric", "code_method"])
    work.add_argument("--run-id")
    work.add_argument("--control-note")
    work.add_argument("--updated-by", default="aitp-cli")
    work.add_argument("--skill-query", action="append", default=[])
    work.add_argument("--human-request")
    work.add_argument("--max-auto-steps", type=int, default=1)
    work.add_argument("--json", action="store_true")

    verify = subparsers.add_parser("verify", help="Prepare a validation contract for a bounded verification mode")
    verify.add_argument("--topic-slug", required=True)
    verify.add_argument("--mode", choices=["proof", "comparison", "numeric", "topic-completion"], required=True)
    verify.add_argument("--updated-by", default="aitp-cli")
    verify.add_argument("--json", action="store_true")

    complete_topic = subparsers.add_parser("complete-topic", help="Assess topic-completion status against regression and follow-up debt")
    complete_topic.add_argument("--topic-slug", required=True)
    complete_topic.add_argument("--run-id")
    complete_topic.add_argument("--updated-by", default="aitp-cli")
    complete_topic.add_argument("--json", action="store_true")

    reintegrate_followup = subparsers.add_parser(
        "reintegrate-followup",
        help="Reintegrate a child follow-up topic back into its parent topic",
    )
    reintegrate_followup.add_argument("--topic-slug", required=True)
    reintegrate_followup.add_argument("--child-topic-slug", required=True)
    reintegrate_followup.add_argument("--run-id")
    reintegrate_followup.add_argument("--updated-by", default="aitp-cli")
    reintegrate_followup.add_argument("--json", action="store_true")

    update_followup_return = subparsers.add_parser(
        "update-followup-return",
        help="Update a child topic follow-up return packet before parent reintegration",
    )
    update_followup_return.add_argument("--topic-slug", required=True)
    update_followup_return.add_argument("--run-id")
    update_followup_return.add_argument(
        "--return-status",
        required=True,
        choices=[
            "pending_reentry",
            "recovered_units",
            "resolved_gap_update",
            "returned_with_gap",
            "returned_unresolved",
        ],
    )
    update_followup_return.add_argument(
        "--accepted-return-shape",
        choices=["recovered_units", "resolved_gap_update", "still_unresolved_packet"],
    )
    update_followup_return.add_argument("--return-summary")
    update_followup_return.add_argument("--child-topic-summary")
    update_followup_return.add_argument("--return-artifact-path", action="append", default=[])
    update_followup_return.add_argument("--updated-by", default="aitp-cli")
    update_followup_return.add_argument("--json", action="store_true")

    lean_bridge = subparsers.add_parser("lean-bridge", help="Materialize Lean-ready bridge packets for a topic")
    lean_bridge.add_argument("--topic-slug", required=True)
    lean_bridge.add_argument("--run-id")
    lean_bridge.add_argument("--candidate-id")
    lean_bridge.add_argument("--updated-by", default="aitp-cli")
    lean_bridge.add_argument("--json", action="store_true")

    state = subparsers.add_parser("state", help="Read topic runtime state")
    state.add_argument("--topic-slug", required=True)
    state.add_argument("--json", action="store_true")

    request_promotion = subparsers.add_parser("request-promotion", help="Request human approval before Layer 2 promotion")
    request_promotion.add_argument("--topic-slug", required=True)
    request_promotion.add_argument("--candidate-id", required=True)
    request_promotion.add_argument("--run-id")
    request_promotion.add_argument("--route", default="L3->L4->L2")
    request_promotion.add_argument("--backend-id")
    request_promotion.add_argument("--target-backend-root")
    request_promotion.add_argument("--updated-by", default="aitp-cli")
    request_promotion.add_argument("--notes")
    request_promotion.add_argument("--json", action="store_true")

    approve_promotion = subparsers.add_parser("approve-promotion", help="Approve a pending Layer 2 promotion request")
    approve_promotion.add_argument("--topic-slug", required=True)
    approve_promotion.add_argument("--candidate-id", required=True)
    approve_promotion.add_argument("--run-id")
    approve_promotion.add_argument("--updated-by", default="aitp-cli")
    approve_promotion.add_argument("--notes")
    approve_promotion.add_argument("--json", action="store_true")

    reject_promotion = subparsers.add_parser("reject-promotion", help="Reject a pending Layer 2 promotion request")
    reject_promotion.add_argument("--topic-slug", required=True)
    reject_promotion.add_argument("--candidate-id", required=True)
    reject_promotion.add_argument("--run-id")
    reject_promotion.add_argument("--updated-by", default="aitp-cli")
    reject_promotion.add_argument("--notes")
    reject_promotion.add_argument("--json", action="store_true")

    promote = subparsers.add_parser("promote", help="Promote an approved candidate into the configured Layer 2 backend")
    promote.add_argument("--topic-slug", required=True)
    promote.add_argument("--candidate-id", required=True)
    promote.add_argument("--run-id")
    promote.add_argument("--backend-id")
    promote.add_argument("--target-backend-root")
    promote.add_argument("--domain")
    promote.add_argument("--subdomain")
    promote.add_argument("--source-id")
    promote.add_argument("--source-section")
    promote.add_argument("--source-section-title")
    promote.add_argument("--updated-by", default="aitp-cli")
    promote.add_argument("--notes")
    promote.add_argument("--json", action="store_true")

    auto_promote = subparsers.add_parser(
        "auto-promote",
        help="Auto-promote a theory candidate into L2_auto after coverage and consensus gates pass",
    )
    auto_promote.add_argument("--topic-slug", required=True)
    auto_promote.add_argument("--candidate-id", required=True)
    auto_promote.add_argument("--run-id")
    auto_promote.add_argument("--backend-id")
    auto_promote.add_argument("--target-backend-root")
    auto_promote.add_argument("--domain")
    auto_promote.add_argument("--subdomain")
    auto_promote.add_argument("--source-id")
    auto_promote.add_argument("--source-section")
    auto_promote.add_argument("--source-section-title")
    auto_promote.add_argument("--updated-by", default="aitp-cli")
    auto_promote.add_argument("--notes")
    auto_promote.add_argument("--json", action="store_true")

    install = subparsers.add_parser("install-agent", help="Install AITP wrappers for supported agents")
    install.add_argument("--agent", choices=["codex", "openclaw", "opencode", "claude-code", "all"], required=True)
    install.add_argument("--scope", choices=["user", "project"], default="user")
    install.add_argument("--target-root")
    install.add_argument("--no-force", action="store_true")
    install.add_argument("--no-mcp", action="store_true")
    install.add_argument("--json", action="store_true")

    doctor = subparsers.add_parser("doctor", help="Show AITP CLI install status")
    doctor.add_argument("--json", action="store_true")

    return parser


def _service_from_args(args: argparse.Namespace) -> AITPService:
    kwargs: dict[str, Any] = {}
    if args.kernel_root:
        kwargs["kernel_root"] = args.kernel_root
    if args.repo_root:
        kwargs["repo_root"] = args.repo_root
    return AITPService(**kwargs)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    service = _service_from_args(args)

    if args.command == "bootstrap":
        payload = service.orchestrate(
            topic_slug=args.topic_slug,
            topic=args.topic,
            statement=args.statement,
            run_id=args.run_id,
            control_note=args.control_note,
            updated_by=args.updated_by,
            arxiv_ids=args.arxiv_id,
            local_note_paths=args.local_note_path,
            skill_queries=args.skill_query,
            human_request=args.human_request,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "new-topic":
        payload = service.new_topic(
            topic=args.topic,
            question=args.question,
            mode=args.mode,
            run_id=args.run_id,
            control_note=args.control_note,
            updated_by=args.updated_by,
            arxiv_ids=args.arxiv_id,
            local_note_paths=args.local_note_path,
            skill_queries=args.skill_query,
            human_request=args.human_request,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "resume":
        payload = service.orchestrate(
            topic_slug=args.topic_slug,
            run_id=args.run_id,
            control_note=args.control_note,
            updated_by=args.updated_by,
            arxiv_ids=args.arxiv_id,
            local_note_paths=args.local_note_path,
            skill_queries=args.skill_query,
            human_request=args.human_request,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "audit":
        payload = service.audit(topic_slug=args.topic_slug, phase=args.phase, updated_by=args.updated_by)
        _emit(payload, args.json)
        state = payload.get("conformance_state") or {}
        return 0 if state.get("overall_status") == "pass" else 1

    if args.command == "ci-check":
        payload = service.audit(topic_slug=args.topic_slug, phase=args.phase, updated_by=args.updated_by)
        _emit(payload, args.json)
        state = payload.get("conformance_state") or {}
        return 0 if state.get("overall_status") == "pass" else 1

    if args.command == "baseline":
        payload = service.scaffold_baseline(
            topic_slug=args.topic_slug,
            run_id=args.run_id,
            title=args.title,
            reference=args.reference,
            agreement_criterion=args.agreement_criterion,
            baseline_kind=args.baseline_kind,
            updated_by=args.updated_by,
            notes=args.notes,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "atomize":
        payload = service.scaffold_atomic_understanding(
            topic_slug=args.topic_slug,
            run_id=args.run_id,
            method_title=args.method_title,
            updated_by=args.updated_by,
            scope_note=args.scope_note,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "operation-init":
        baseline_required = None
        if args.baseline_required:
            baseline_required = True
        if args.no_baseline_required:
            baseline_required = False

        atomic_required = None
        if args.atomic_required:
            atomic_required = True
        if args.no_atomic_required:
            atomic_required = False

        payload = service.scaffold_operation(
            topic_slug=args.topic_slug,
            run_id=args.run_id,
            title=args.title,
            kind=args.kind,
            updated_by=args.updated_by,
            summary=args.summary,
            notes=args.notes,
            baseline_required=baseline_required,
            atomic_understanding_required=atomic_required,
            references=args.reference,
            source_paths=args.source_path,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "operation-update":
        payload = service.update_operation(
            topic_slug=args.topic_slug,
            run_id=args.run_id,
            operation=args.operation,
            updated_by=args.updated_by,
            summary=args.summary,
            notes=args.notes,
            baseline_status=args.baseline_status,
            atomic_understanding_status=args.atomic_status,
            references=args.reference,
            source_paths=args.source_path,
            artifact_paths=args.artifact_path,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "trust-audit":
        payload = service.audit_operation_trust(
            topic_slug=args.topic_slug,
            run_id=args.run_id,
            updated_by=args.updated_by,
        )
        _emit(payload, args.json)
        return 0 if payload.get("overall_status") == "pass" else 1

    if args.command == "capability-audit":
        payload = service.capability_audit(
            topic_slug=args.topic_slug,
            updated_by=args.updated_by,
        )
        _emit(payload, args.json)
        return 0 if payload.get("overall_status") == "ready" else 1

    if args.command == "coverage-audit":
        payload = service.audit_theory_coverage(
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
        _emit(payload, args.json)
        return 0 if payload.get("coverage_status") == "pass" else 1

    if args.command == "loop":
        payload = service.run_topic_loop(
            topic_slug=args.topic_slug,
            topic=args.topic,
            statement=args.statement,
            run_id=args.run_id,
            control_note=args.control_note,
            updated_by=args.updated_by,
            human_request=args.human_request,
            skill_queries=args.skill_query,
            max_auto_steps=args.max_auto_steps,
        )
        _emit(payload, args.json)
        exit_state = (payload.get("exit_audit") or {}).get("conformance_state") or {}
        return 0 if exit_state.get("overall_status") == "pass" else 1

    if args.command == "status":
        payload = service.topic_status(
            topic_slug=args.topic_slug,
            updated_by=args.updated_by,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "next":
        payload = service.topic_next(
            topic_slug=args.topic_slug,
            updated_by=args.updated_by,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "work":
        payload = service.work_topic(
            topic=args.topic,
            topic_slug=args.topic_slug,
            question=args.question,
            mode=args.mode,
            run_id=args.run_id,
            control_note=args.control_note,
            updated_by=args.updated_by,
            skill_queries=args.skill_query,
            human_request=args.human_request,
            max_auto_steps=args.max_auto_steps,
        )
        _emit(payload, args.json)
        if "exit_audit" in payload:
            exit_state = (payload.get("exit_audit") or {}).get("conformance_state") or {}
            return 0 if exit_state.get("overall_status") == "pass" else 1
        return 0

    if args.command == "verify":
        payload = service.prepare_verification(
            topic_slug=args.topic_slug,
            mode=args.mode,
            updated_by=args.updated_by,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "complete-topic":
        payload = service.assess_topic_completion(
            topic_slug=args.topic_slug,
            run_id=args.run_id,
            updated_by=args.updated_by,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "reintegrate-followup":
        payload = service.reintegrate_followup_subtopic(
            topic_slug=args.topic_slug,
            child_topic_slug=args.child_topic_slug,
            run_id=args.run_id,
            updated_by=args.updated_by,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "update-followup-return":
        payload = service.update_followup_return_packet(
            topic_slug=args.topic_slug,
            run_id=args.run_id,
            return_status=args.return_status,
            accepted_return_shape=args.accepted_return_shape,
            return_summary=args.return_summary,
            child_topic_summary=args.child_topic_summary,
            return_artifact_paths=args.return_artifact_path,
            updated_by=args.updated_by,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "lean-bridge":
        payload = service.prepare_lean_bridge(
            topic_slug=args.topic_slug,
            run_id=args.run_id,
            candidate_id=args.candidate_id,
            updated_by=args.updated_by,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "state":
        payload = {"topic_state": service.get_runtime_state(args.topic_slug)}
        _emit(payload, args.json)
        return 0

    if args.command == "request-promotion":
        payload = service.request_promotion(
            topic_slug=args.topic_slug,
            candidate_id=args.candidate_id,
            run_id=args.run_id,
            route=args.route,
            backend_id=args.backend_id,
            target_backend_root=args.target_backend_root,
            requested_by=args.updated_by,
            notes=args.notes,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "approve-promotion":
        payload = service.approve_promotion(
            topic_slug=args.topic_slug,
            candidate_id=args.candidate_id,
            run_id=args.run_id,
            approved_by=args.updated_by,
            notes=args.notes,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "reject-promotion":
        payload = service.reject_promotion(
            topic_slug=args.topic_slug,
            candidate_id=args.candidate_id,
            run_id=args.run_id,
            rejected_by=args.updated_by,
            notes=args.notes,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "promote":
        payload = service.promote_candidate(
            topic_slug=args.topic_slug,
            candidate_id=args.candidate_id,
            run_id=args.run_id,
            promoted_by=args.updated_by,
            backend_id=args.backend_id,
            target_backend_root=args.target_backend_root,
            domain=args.domain,
            subdomain=args.subdomain,
            source_id=args.source_id,
            source_section=args.source_section,
            source_section_title=args.source_section_title,
            notes=args.notes,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "auto-promote":
        payload = service.auto_promote_candidate(
            topic_slug=args.topic_slug,
            candidate_id=args.candidate_id,
            run_id=args.run_id,
            promoted_by=args.updated_by,
            backend_id=args.backend_id,
            target_backend_root=args.target_backend_root,
            domain=args.domain,
            subdomain=args.subdomain,
            source_id=args.source_id,
            source_section=args.source_section,
            source_section_title=args.source_section_title,
            notes=args.notes,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "install-agent":
        payload = service.install_agent(
            agent=args.agent,
            scope=args.scope,
            target_root=args.target_root,
            force=not args.no_force,
            install_mcp=not args.no_mcp,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "doctor":
        payload = service.ensure_cli_installed()
        _emit(payload, args.json)
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
