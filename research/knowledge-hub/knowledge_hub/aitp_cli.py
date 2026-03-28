from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .aitp_service import AITPService
from .decision_point_handler import (
    emit_decision_point,
    get_all_decision_points,
    list_pending_decision_points,
    resolve_decision_point,
)
from .decision_trace_handler import record_decision_trace
from .session_chronicle_handler import finalize_chronicle, get_latest_chronicle, start_chronicle


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


def _parse_nearby_variant(value: str) -> dict[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError(
            "nearby variants must use LABEL=RELATION:VERDICT or LABEL=RELATION:VERDICT:NOTE"
        )
    label, remainder = value.split("=", 1)
    relation, sep, verdict_note = remainder.partition(":")
    if not sep:
        raise argparse.ArgumentTypeError(
            "nearby variants must include relation and verdict separated by ':'"
        )
    verdict, _, note = verdict_note.partition(":")
    label = label.strip()
    relation = relation.strip()
    verdict = verdict.strip()
    note = note.strip()
    if not label or not relation or not verdict:
        raise argparse.ArgumentTypeError(
            "nearby variants must include label, relation, and verdict"
        )
    return {"label": label, "relation": relation, "verdict": verdict, "notes": note}


def _parse_bool_string(value: str) -> bool:
    normalized = str(value or "").strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise argparse.ArgumentTypeError("expected one of: true, false")


def _parse_json_array(value: str) -> list[Any]:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"expected a JSON array: {exc}") from exc
    if not isinstance(payload, list):
        raise argparse.ArgumentTypeError("expected a JSON array")
    return payload


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
    resume.add_argument("--load-profile", choices=["auto", "light", "full"], default="auto")
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
    formal_theory_audit.add_argument("--nearby-variant", action="append", default=[], type=_parse_nearby_variant)
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
    loop.add_argument("--load-profile", choices=["auto", "light", "full"], default="auto")
    loop.add_argument("--json", action="store_true")

    steer_topic = subparsers.add_parser(
        "steer-topic",
        help="Persist an innovation-direction update and paired control note before resuming the topic",
    )
    steer_topic.add_argument("--topic-slug", required=True)
    steer_topic.add_argument("--innovation-direction", required=True)
    steer_topic.add_argument("--decision", choices=["continue", "branch", "redirect", "stop"], default="continue")
    steer_topic.add_argument("--run-id")
    steer_topic.add_argument("--updated-by", default="aitp-cli")
    steer_topic.add_argument("--summary")
    steer_topic.add_argument("--next-question")
    steer_topic.add_argument("--target-action-id")
    steer_topic.add_argument("--target-action-summary")
    steer_topic.add_argument("--human-request")
    steer_topic.add_argument("--json", action="store_true")

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
    work.add_argument("--load-profile", choices=["auto", "light", "full"], default="auto")
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

    current_topic = subparsers.add_parser("current-topic", help="Read the current-topic routing memory")
    current_topic.add_argument("--json", action="store_true")

    emit_decision = subparsers.add_parser("emit-decision", help="Emit a durable Phase 6 decision point")
    emit_decision.add_argument("--topic-slug", required=True)
    emit_decision.add_argument("--question", required=True)
    emit_decision.add_argument("--options", required=True, type=_parse_json_array)
    emit_decision.add_argument("--blocking", required=True, type=_parse_bool_string)
    emit_decision.add_argument("--phase", choices=["clarification", "routing", "execution", "validation", "promotion"], default="routing")
    emit_decision.add_argument("--current-layer", choices=["L0", "L1", "L2", "L3", "L4"], default="L3")
    emit_decision.add_argument("--source-layer", choices=["L0", "L1", "L2", "L3", "L4"])
    emit_decision.add_argument("--target-layer", choices=["L0", "L1", "L2", "L3", "L4"])
    emit_decision.add_argument("--default-option-index", type=int)
    emit_decision.add_argument("--timeout-hint")
    emit_decision.add_argument(
        "--trigger-rule",
        choices=[
            "scope_change",
            "method_uncertainty",
            "benchmark_disagreement",
            "promotion_gate",
            "resource_choice",
            "direction_ambiguity",
            "validation_strategy",
            "gap_recovery_route",
            "formalization_bridge",
            "custom",
        ],
    )
    emit_decision.add_argument("--related-artifacts", type=_parse_json_array, default=[])
    emit_decision.add_argument("--decision-id")
    emit_decision.add_argument("--json", action="store_true")

    resolve_decision = subparsers.add_parser("resolve-decision", help="Resolve a durable Phase 6 decision point")
    resolve_decision.add_argument("--topic-slug", required=True)
    resolve_decision.add_argument("--decision-id", required=True)
    resolve_decision.add_argument("--option", required=True, type=int)
    resolve_decision.add_argument("--comment")
    resolve_decision.add_argument("--resolved-by", default="human")
    resolve_decision.add_argument("--json", action="store_true")

    list_decisions = subparsers.add_parser("list-decisions", help="List durable Phase 6 decision points")
    list_decisions.add_argument("--topic-slug", required=True)
    list_decisions.add_argument("--pending-only", action="store_true")
    list_decisions.add_argument("--json", action="store_true")

    trace_decision = subparsers.add_parser("trace-decision", help="Record a durable Phase 6 decision trace")
    trace_decision.add_argument("--topic-slug", required=True)
    trace_decision.add_argument("--summary", required=True)
    trace_decision.add_argument("--chosen", required=True)
    trace_decision.add_argument("--rationale", required=True)
    trace_decision.add_argument("--input-refs", type=_parse_json_array, default=[])
    trace_decision.add_argument("--output-refs", type=_parse_json_array, default=[])
    trace_decision.add_argument("--context")
    trace_decision.add_argument("--decision-point-ref")
    trace_decision.add_argument("--would-change-if")
    trace_decision.add_argument("--from-layer")
    trace_decision.add_argument("--to-layer")
    trace_decision.add_argument("--related-traces", type=_parse_json_array, default=[])
    trace_decision.add_argument("--json", action="store_true")

    chronicle = subparsers.add_parser("chronicle", help="Read, create, or finalize the active Phase 6 session chronicle")
    chronicle.add_argument("--topic-slug", required=True)
    chronicle.add_argument("--finalize", action="store_true")
    chronicle.add_argument("--ending-state")
    chronicle.add_argument("--next-step", action="append", default=[])
    chronicle.add_argument("--summary")
    chronicle.add_argument("--json", action="store_true")

    session_start = subparsers.add_parser(
        "session-start",
        help="Materialize AITP routing and runtime state from a natural-language session-start request",
    )
    session_topic_group = session_start.add_mutually_exclusive_group(required=False)
    session_topic_group.add_argument("--topic-slug")
    session_topic_group.add_argument("--topic")
    session_topic_group.add_argument("--current-topic", action="store_true")
    session_topic_group.add_argument("--latest-topic", action="store_true")
    session_start.add_argument("--statement")
    session_start.add_argument("--run-id")
    session_start.add_argument("--control-note")
    session_start.add_argument("--updated-by", default="aitp-session-start")
    session_start.add_argument("--skill-query", action="append", default=[])
    session_start.add_argument("--max-auto-steps", type=int, default=4)
    session_start.add_argument("--research-mode")
    session_start.add_argument("--load-profile", choices=["auto", "light", "full"], default="auto")
    session_start.add_argument("--json", action="store_true")
    session_start.add_argument("task", help="Natural-language research request to route into AITP")

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

    install = subparsers.add_parser("install-agent", help="Install AITP skills and bootstrap assets for supported agents")
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


def _run_phase6_command(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int | None:
    kernel_root = args.kernel_root if getattr(args, "kernel_root", None) else None

    if args.command == "emit-decision":
        layer_context = {"current_layer": args.current_layer}
        if args.source_layer:
            layer_context["source_layer"] = args.source_layer
        if args.target_layer:
            layer_context["target_layer"] = args.target_layer
        payload = emit_decision_point(
            topic_slug=args.topic_slug,
            question=args.question,
            options=args.options,
            blocking=args.blocking,
            phase=args.phase,
            layer_context=layer_context,
            default_option_index=args.default_option_index,
            timeout_hint=args.timeout_hint,
            trigger_rule=args.trigger_rule,
            related_artifacts=args.related_artifacts,
            decision_id=args.decision_id,
            kernel_root=kernel_root,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "resolve-decision":
        payload = resolve_decision_point(
            topic_slug=args.topic_slug,
            decision_id=args.decision_id,
            option_index=args.option,
            comment=args.comment,
            resolved_by=args.resolved_by,
            kernel_root=kernel_root,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "list-decisions":
        decisions = (
            list_pending_decision_points(args.topic_slug, kernel_root=kernel_root)
            if args.pending_only
            else get_all_decision_points(args.topic_slug, kernel_root=kernel_root)
        )
        _emit({"decision_points": decisions}, args.json)
        return 0

    if args.command == "trace-decision":
        layer_transition = None
        if args.from_layer or args.to_layer:
            layer_transition = {}
            if args.from_layer:
                layer_transition["from_layer"] = args.from_layer
            if args.to_layer:
                layer_transition["to_layer"] = args.to_layer
        payload = record_decision_trace(
            topic_slug=args.topic_slug,
            summary=args.summary,
            chosen=args.chosen,
            rationale=args.rationale,
            input_refs=args.input_refs,
            context=args.context,
            decision_point_ref=args.decision_point_ref,
            would_change_if=args.would_change_if,
            output_refs=args.output_refs,
            layer_transition=layer_transition,
            related_traces=args.related_traces,
            kernel_root=kernel_root,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "chronicle":
        latest = get_latest_chronicle(args.topic_slug, kernel_root=kernel_root)
        if args.finalize:
            if not args.ending_state:
                parser.error("chronicle --finalize requires --ending-state")
            if not args.summary:
                parser.error("chronicle --finalize requires --summary")
            if not args.next_step:
                parser.error("chronicle --finalize requires at least one --next-step")
            if not latest or latest.get("session_end"):
                print(f"No open chronicle found for topic '{args.topic_slug}'.")
                return 1
            payload = finalize_chronicle(
                chronicle_id=str(latest["id"]),
                ending_state=args.ending_state,
                next_steps=args.next_step,
                summary=args.summary,
                kernel_root=kernel_root,
            )
            _emit(payload, args.json)
            return 0

        if latest and not latest.get("session_end"):
            _emit({"chronicle": latest, "created": False}, args.json)
            return 0

        chronicle_id = start_chronicle(args.topic_slug, kernel_root=kernel_root)
        created = get_latest_chronicle(args.topic_slug, kernel_root=kernel_root)
        _emit({"chronicle": created, "created": True, "chronicle_id": chronicle_id}, args.json)
        return 0

    return None


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    phase6_exit = _run_phase6_command(args, parser)
    if phase6_exit is not None:
        return phase6_exit
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
        service.remember_current_topic(
            topic_slug=payload["topic_slug"],
            updated_by=args.updated_by,
            source="bootstrap",
            human_request=args.human_request or args.statement,
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
        service.remember_current_topic(
            topic_slug=payload["topic_slug"],
            updated_by=args.updated_by,
            source="resume",
            human_request=args.human_request,
        )
        payload["runtime_context"] = service.refresh_runtime_context(
            topic_slug=payload["topic_slug"],
            updated_by=args.updated_by,
            human_request=args.human_request,
            load_profile=None if args.load_profile == "auto" else args.load_profile,
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

    if args.command == "formal-theory-audit":
        payload = service.audit_formal_theory(
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
        _emit(payload, args.json)
        return 0 if payload.get("overall_status") == "ready" else 1

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
            load_profile=None if args.load_profile == "auto" else args.load_profile,
        )
        _emit(payload, args.json)
        exit_state = (payload.get("exit_audit") or {}).get("conformance_state") or {}
        return 0 if exit_state.get("overall_status") == "pass" else 1

    if args.command == "steer-topic":
        payload = service.steer_topic(
            topic_slug=args.topic_slug,
            innovation_direction=args.innovation_direction,
            decision=args.decision,
            run_id=args.run_id,
            updated_by=args.updated_by,
            summary=args.summary,
            next_question=args.next_question,
            target_action_id=args.target_action_id,
            target_action_summary=args.target_action_summary,
            human_request=args.human_request,
        )
        _emit(payload, args.json)
        return 0

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
            load_profile=None if args.load_profile == "auto" else args.load_profile,
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

    if args.command == "current-topic":
        payload = {"current_topic": service.get_current_topic_memory()}
        _emit(payload, args.json)
        return 0

    if args.command == "session-start":
        payload = service.start_chat_session(
            task=args.task,
            explicit_topic_slug=args.topic_slug,
            explicit_topic=args.topic,
            explicit_current_topic=args.current_topic,
            explicit_latest_topic=args.latest_topic,
            statement=args.statement,
            run_id=args.run_id,
            control_note=args.control_note,
            updated_by=args.updated_by,
            skill_queries=args.skill_query,
            max_auto_steps=args.max_auto_steps,
            research_mode=args.research_mode,
            load_profile=None if args.load_profile == "auto" else args.load_profile,
        )
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
