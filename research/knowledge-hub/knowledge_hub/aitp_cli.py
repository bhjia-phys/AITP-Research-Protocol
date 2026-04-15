from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ._version import __version__
from .aitp_service import AITPService
from .cli_compat_handler import (
    dispatch_compat_command,
    emit_payload,
    render_cli_help,
    register_compat_commands,
    render_hello_payload,
    render_topic_next_payload,
    render_topic_status_payload,
)
from .cli_frontdoor_handler import dispatch_frontdoor_command, register_frontdoor_commands
from .cli_review_handler import dispatch_review_command, register_review_commands
from .decision_point_handler import (
    emit_decision_point,
    get_all_decision_points,
    list_pending_decision_points,
    resolve_decision_point,
)
from .decision_trace_handler import record_decision_trace
from .session_chronicle_handler import finalize_chronicle, get_latest_chronicle, start_chronicle
from .topic_replay import materialize_topic_replay_bundle
from .cli_l1_graph_handler import dispatch_l1_graph_command, register_l1_graph_commands
from .cli_l2_graph_handler import dispatch_l2_graph_command, register_l2_graph_commands
from .cli_l2_compiler_handler import dispatch_l2_compiler_command, register_l2_compiler_commands
from .cli_source_catalog_handler import dispatch_source_catalog_command, register_source_catalog_commands


def _emit(payload: dict[str, Any], as_json: bool) -> None:
    emit_payload(payload, as_json)


def _emit_text(text: str) -> None:
    print(str(text or "").rstrip())


def _read_relative_human_surface(service: AITPService, relative_path: str) -> str | None:
    target = str(relative_path or "").strip()
    if not target:
        return None
    candidate = Path(target)
    if not candidate.is_absolute():
        candidate = service.kernel_root / candidate
    if not candidate.exists():
        return None
    return candidate.read_text(encoding="utf-8")


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


def _parse_human_modification(value: str) -> dict[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError(
            "human modifications must use FIELD=CHANGE:REASON"
        )
    field, change_reason = value.split("=", 1)
    change, sep, reason = change_reason.partition(":")
    field = field.strip()
    change = change.strip()
    reason = reason.strip()
    if not field or not change or not sep or not reason:
        raise argparse.ArgumentTypeError(
            "human modifications must include field, change, and reason"
        )
    return {"field": field, "change": change, "reason": reason}


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
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

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

    hello = subparsers.add_parser("hello", help="Run the first AITP onboarding step for one demo topic")
    hello.add_argument("--topic", default="Demo topic")
    hello.add_argument("--question", default="What is the first bounded question?")
    hello.add_argument("--mode", choices=["formal_theory", "toy_numeric", "code_method"], default="formal_theory")
    hello.add_argument("--updated-by", default="aitp-cli")
    hello.add_argument("--arxiv-id", action="append", default=[])
    hello.add_argument("--local-note-path", action="append", default=[])
    hello.add_argument("--json", action="store_true")

    help_cmd = subparsers.add_parser("help", help="Show the human-oriented AITP command guide")
    help_cmd.add_argument("--all", action="store_true")

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

    paired_backend_audit = subparsers.add_parser(
        "paired-backend-audit",
        help="Audit paired-backend alignment, drift semantics, and backend debt state",
    )
    paired_backend_audit.add_argument("--topic-slug", required=True)
    paired_backend_audit.add_argument("--backend-id", default="backend:theoretical-physics-knowledge-network")
    paired_backend_audit.add_argument("--updated-by", default="aitp-cli")
    paired_backend_audit.add_argument("--json", action="store_true")

    h_plane_audit = subparsers.add_parser(
        "h-plane-audit",
        help="Audit unified H-plane steering, checkpoint, registry, and approval state",
    )
    h_plane_audit.add_argument("--topic-slug", required=True)
    h_plane_audit.add_argument("--updated-by", default="aitp-cli")
    h_plane_audit.add_argument("--json", action="store_true")

    register_review_commands(
        subparsers,
        parse_notation_binding=_parse_notation_binding,
        parse_agent_vote=_parse_agent_vote,
        parse_nearby_variant=_parse_nearby_variant,
    )

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
    steer_input = steer_topic.add_mutually_exclusive_group(required=True)
    steer_input.add_argument("--innovation-direction")
    steer_input.add_argument("--text")
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
    status.add_argument("--verbose", action="store_true")
    status.add_argument("--full", action="store_true")
    status.add_argument("--json", action="store_true")

    interaction = subparsers.add_parser("interaction", help="Show the active human-interaction packet for one topic")
    interaction.add_argument("--topic-slug", required=True)
    interaction.add_argument("--updated-by", default="aitp-cli")
    interaction.add_argument("--json", action="store_true")

    resolve_checkpoint = subparsers.add_parser(
        "resolve-checkpoint",
        help="Resolve the active operator checkpoint for one topic",
    )
    resolve_checkpoint.add_argument("--topic-slug", required=True)
    resolve_checkpoint.add_argument("--option", required=True, type=int)
    resolve_checkpoint.add_argument("--comment")
    resolve_checkpoint.add_argument("--resolved-by", default="human")
    resolve_checkpoint.add_argument("--json", action="store_true")

    layer_graph = subparsers.add_parser(
        "layer-graph",
        help="Materialize and inspect the iterative topic layer graph for the current topic",
    )
    layer_graph.add_argument("--topic-slug", required=True)
    layer_graph.add_argument("--updated-by", default="aitp-cli")
    layer_graph.add_argument("--json", action="store_true")

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
    verify.add_argument("--mode", choices=["proof", "comparison", "numeric", "analytical", "topic-completion"], required=True)
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

    statement_compilation = subparsers.add_parser(
        "statement-compilation",
        help="Compile bounded theory statements into declaration skeletons and proof-repair plans",
    )
    statement_compilation.add_argument("--topic-slug", required=True)
    statement_compilation.add_argument("--run-id")
    statement_compilation.add_argument("--candidate-id")
    statement_compilation.add_argument("--updated-by", default="aitp-cli")
    statement_compilation.add_argument("--json", action="store_true")

    state = subparsers.add_parser("state", help="Read topic runtime state")
    state.add_argument("--topic-slug", required=True)
    state.add_argument("--json", action="store_true")

    topics = subparsers.add_parser("topics", help="List active topics from the multi-topic registry")
    topics.add_argument("--updated-by", default="aitp-cli")
    topics.add_argument("--json", action="store_true")

    current_topic = subparsers.add_parser("current-topic", help="Read the current-topic routing memory")
    current_topic.add_argument("--json", action="store_true")

    collaborator_memory = subparsers.add_parser(
        "collaborator-memory",
        help="Read runtime-side collaborator memory without mixing it into canonical scientific memory",
    )
    collaborator_memory.add_argument("--topic-slug")
    collaborator_memory.add_argument("--limit", type=int, default=10)
    collaborator_memory.add_argument("--json", action="store_true")

    replay_topic = subparsers.add_parser("replay-topic", help="Build a human-readable replay bundle for one topic")
    replay_topic.add_argument("--topic-slug", required=True)
    replay_topic.add_argument("--json", action="store_true")

    register_l2_graph_commands(subparsers)
    register_l1_graph_commands(subparsers)
    register_source_catalog_commands(subparsers)

    focus_topic = subparsers.add_parser("focus-topic", help="Move registry focus to a specific topic")
    focus_topic.add_argument("--topic-slug", required=True)
    focus_topic.add_argument("--updated-by", default="aitp-cli")
    focus_topic.add_argument("--human-request")
    focus_topic.add_argument("--json", action="store_true")

    pause_topic = subparsers.add_parser("pause-topic", help="Pause a topic in the active-topics registry")
    pause_topic.add_argument("--topic-slug", required=True)
    pause_topic.add_argument("--updated-by", default="aitp-cli")
    pause_topic.add_argument("--human-request")
    pause_topic.add_argument("--json", action="store_true")

    resume_topic = subparsers.add_parser("resume-topic", help="Resume a paused topic in the active-topics registry")
    resume_topic.add_argument("--topic-slug", required=True)
    resume_topic.add_argument("--updated-by", default="aitp-cli")
    resume_topic.add_argument("--human-request")
    resume_topic.add_argument("--json", action="store_true")

    block_topic = subparsers.add_parser("block-topic", help="Declare that one topic is blocked by another topic")
    block_topic.add_argument("--topic-slug", required=True)
    block_topic.add_argument("--blocked-by", required=True)
    block_topic.add_argument("--reason", required=True)
    block_topic.add_argument("--updated-by", default="aitp-cli")
    block_topic.add_argument("--human-request")
    block_topic.add_argument("--json", action="store_true")

    unblock_topic = subparsers.add_parser("unblock-topic", help="Clear one dependency from a topic")
    unblock_topic.add_argument("--topic-slug", required=True)
    unblock_topic.add_argument("--blocked-by", required=True)
    unblock_topic.add_argument("--updated-by", default="aitp-cli")
    unblock_topic.add_argument("--human-request")
    unblock_topic.add_argument("--json", action="store_true")

    clear_topic_dependencies = subparsers.add_parser("clear-topic-dependencies", help="Clear all dependencies from a topic")
    clear_topic_dependencies.add_argument("--topic-slug", required=True)
    clear_topic_dependencies.add_argument("--updated-by", default="aitp-cli")
    clear_topic_dependencies.add_argument("--human-request")
    clear_topic_dependencies.add_argument("--json", action="store_true")

    prune_compat_surfaces = subparsers.add_parser(
        "prune-compat-surfaces",
        help="Remove compatibility-only runtime surfaces once primary surfaces exist",
    )
    prune_compat_surfaces.add_argument("--topic-slug", required=True)
    prune_compat_surfaces.add_argument("--updated-by", default="aitp-cli")
    prune_compat_surfaces.add_argument("--json", action="store_true")

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
    approve_promotion.add_argument("--human-modification", action="append", default=[], type=_parse_human_modification)
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

    register_compat_commands(subparsers)
    register_frontdoor_commands(subparsers)
    register_l2_compiler_commands(subparsers)

    return parser


def _service_from_args(args: argparse.Namespace) -> AITPService:
    kwargs: dict[str, Any] = {}
    if args.kernel_root:
        kwargs["kernel_root"] = args.kernel_root
    if args.repo_root:
        kwargs["repo_root"] = args.repo_root
    return AITPService(**kwargs)


def _emit_cli_error(args: argparse.Namespace, message: str) -> int:
    cleaned = str(message or "").rstrip()
    if getattr(args, "json", False):
        _emit({"status": "error", "error": cleaned}, True)
    else:
        print(cleaned, file=sys.stderr)
    return 1


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
    try:
        return _main_with_args(parser, args)
    except (RuntimeError, FileNotFoundError, ValueError) as exc:
        return _emit_cli_error(args, str(exc))


def _main_with_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    if args.command == "help":
        _emit_text(render_cli_help(parser, show_all=args.all))
        return 0
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

    if args.command == "hello":
        payload = service.hello_topic(
            topic=args.topic,
            question=args.question,
            mode=args.mode,
            updated_by=args.updated_by,
            arxiv_ids=args.arxiv_id,
            local_note_paths=args.local_note_path,
        )
        if args.json:
            _emit(payload, True)
        else:
            _emit_text(render_hello_payload(payload))
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

    if args.command == "paired-backend-audit":
        payload = service.paired_backend_audit(
            topic_slug=args.topic_slug,
            backend_id=args.backend_id,
            updated_by=args.updated_by,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "h-plane-audit":
        payload = service.h_plane_audit(
            topic_slug=args.topic_slug,
            updated_by=args.updated_by,
        )
        _emit(payload, args.json)
        return 0

    review_payload = dispatch_review_command(args, service)
    if review_payload is not None:
        payload = review_payload
        _emit(payload, args.json)
        if args.command == "coverage-audit":
            return 0 if payload.get("coverage_status") == "pass" else 1
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
        if args.text:
            payload = service.steer_topic_from_text(
                topic_slug=args.topic_slug,
                text=args.text,
                run_id=args.run_id,
                updated_by=args.updated_by,
                topic_state=None,
                control_note=None,
            )
        else:
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
        if args.json:
            _emit(payload, True)
        elif args.full:
            dashboard_path = str((((payload.get("primary_runtime_surfaces") or {}).get("primary") or {}).get("runtime_human")) or "").strip()
            rendered = _read_relative_human_surface(service, dashboard_path)
            if rendered is None:
                _emit_text(render_topic_status_payload(payload))
            else:
                _emit_text(rendered)
        elif args.verbose:
            _emit_text(render_topic_status_payload(payload, tier="verbose"))
        else:
            _emit_text(render_topic_status_payload(payload))
        return 0

    if args.command == "interaction":
        payload = service.topic_interaction(
            topic_slug=args.topic_slug,
            updated_by=args.updated_by,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "resolve-checkpoint":
        payload = service.resolve_operator_checkpoint(
            topic_slug=args.topic_slug,
            option_index=args.option,
            comment=args.comment,
            resolved_by=args.resolved_by,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "layer-graph":
        payload = service.topic_layer_graph(
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
        if args.json:
            _emit(payload, True)
        else:
            _emit_text(render_topic_next_payload(payload))
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

    if args.command == "statement-compilation":
        payload = service.prepare_statement_compilation(
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

    if args.command == "topics":
        payload = service.list_active_topics(updated_by=args.updated_by)
        _emit(payload, args.json)
        return 0

    if args.command == "current-topic":
        payload = {"current_topic": service.get_current_topic_memory()}
        _emit(payload, args.json)
        return 0

    if args.command == "collaborator-memory":
        payload = service.get_collaborator_memory(
            topic_slug=args.topic_slug,
            limit=args.limit,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "replay-topic":
        payload = materialize_topic_replay_bundle(service.kernel_root, args.topic_slug)
        _emit(payload, args.json)
        return 0

    l1_graph_payload = dispatch_l1_graph_command(args, service)
    if l1_graph_payload is not None:
        _emit(l1_graph_payload, args.json)
        return 0

    l2_graph_payload = dispatch_l2_graph_command(args, service)
    if l2_graph_payload is not None:
        _emit(l2_graph_payload, args.json)
        return 0

    source_catalog_payload = dispatch_source_catalog_command(args, service)
    if source_catalog_payload is not None:
        _emit(source_catalog_payload, args.json)
        return 0

    l2_compiler_payload = dispatch_l2_compiler_command(args, service)
    if l2_compiler_payload is not None:
        _emit(l2_compiler_payload, args.json)
        return 0

    if args.command == "focus-topic":
        payload = service.focus_topic(
            topic_slug=args.topic_slug,
            updated_by=args.updated_by,
            human_request=args.human_request,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "pause-topic":
        payload = service.pause_topic(
            topic_slug=args.topic_slug,
            updated_by=args.updated_by,
            human_request=args.human_request,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "resume-topic":
        payload = service.resume_topic(
            topic_slug=args.topic_slug,
            updated_by=args.updated_by,
            human_request=args.human_request,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "block-topic":
        payload = service.set_topic_dependency(
            topic_slug=args.topic_slug,
            blocked_by_topic_slug=args.blocked_by,
            reason=args.reason,
            updated_by=args.updated_by,
            human_request=args.human_request,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "unblock-topic":
        payload = service.clear_topic_dependency(
            topic_slug=args.topic_slug,
            blocked_by_topic_slug=args.blocked_by,
            updated_by=args.updated_by,
            human_request=args.human_request,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "clear-topic-dependencies":
        payload = service.clear_all_topic_dependencies(
            topic_slug=args.topic_slug,
            updated_by=args.updated_by,
            human_request=args.human_request,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "prune-compat-surfaces":
        payload = service.prune_compat_surfaces(
            topic_slug=args.topic_slug,
            updated_by=args.updated_by,
        )
        _emit(payload, args.json)
        return 0

    compat_payload = dispatch_compat_command(args, service, parser)
    if compat_payload is not None:
        _emit(compat_payload, args.json)
        return 0

    frontdoor_payload = dispatch_frontdoor_command(args, service)
    if frontdoor_payload is not None:
        _emit(frontdoor_payload, args.json)
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
            human_modifications=args.human_modification,
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

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
