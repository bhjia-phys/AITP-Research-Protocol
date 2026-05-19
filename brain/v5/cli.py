"""Small JSON CLI for the AITP v5 kernel."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from brain.v5.adapter_protocols import adapter_protocol_registry
from brain.v5.adapters import build_adapter_packet
from brain.v5.brief import build_execution_brief
from brain.v5.code import record_code_state
from brain.v5.evidence import record_evidence
from brain.v5.models import TrustUpdateRequest
from brain.v5.public_surfaces import describe_public_surfaces, require_valid_public_surface
from brain.v5.risk import assess_claim_risk
from brain.v5.summaries import read_summary_orientation, write_session_summary
from brain.v5.tool_executors import execute_registered_tool
from brain.v5.tools import record_tool_run, register_tool_recipe
from brain.v5.trust_updates import apply_trust_update, preflight_trust_update
from brain.v5.workspace import (
    bind_session,
    create_claim,
    create_topic,
    get_claim,
    init_workspace,
)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    payload = _dispatch(args)
    print(json.dumps(_jsonable(payload), ensure_ascii=False, sort_keys=True))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aitp-v5")
    parser.add_argument("--base", default=".", help="Workspace base directory")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("base")

    topic_parser = subparsers.add_parser("topic")
    topic_sub = topic_parser.add_subparsers(dest="topic_command", required=True)
    topic_create = topic_sub.add_parser("create")
    topic_create.add_argument("topic_id")
    topic_create.add_argument("--context", required=True, dest="context_id")
    topic_create.add_argument("--title", required=True)

    claim_parser = subparsers.add_parser("claim")
    claim_sub = claim_parser.add_subparsers(dest="claim_command", required=True)
    claim_create = claim_sub.add_parser("create")
    claim_create.add_argument("--topic", required=True, dest="topic_id")
    claim_create.add_argument("--statement", required=True)
    claim_create.add_argument("--evidence-profile", required=True)
    claim_create.add_argument("--confidence-state", default="hypothesis")
    claim_create.add_argument("--uncertainty", required=True)
    claim_create.add_argument("--recipe-id", default="")

    session_parser = subparsers.add_parser("session")
    session_sub = session_parser.add_subparsers(dest="session_command", required=True)
    session_bind = session_sub.add_parser("bind")
    session_bind.add_argument("session_id")
    session_bind.add_argument("--topic", required=True, dest="topic_id")
    session_bind.add_argument("--context", required=True, dest="context_id")
    session_bind.add_argument("--claim", default="", dest="active_claim")
    session_bind.add_argument("--interaction-profile", default="collaborator")
    session_bind.add_argument("--interaction-steering", default="")

    brief_parser = subparsers.add_parser("brief")
    brief_parser.add_argument("session_id")

    risk_parser = subparsers.add_parser("risk")
    risk_sub = risk_parser.add_subparsers(dest="risk_command", required=True)
    risk_assess = risk_sub.add_parser("assess")
    risk_assess.add_argument("claim_id")

    code_parser = subparsers.add_parser("code")
    code_sub = code_parser.add_subparsers(dest="code_command", required=True)
    code_state = code_sub.add_parser("state")
    code_state_sub = code_state.add_subparsers(dest="code_state_command", required=True)
    code_state_record = code_state_sub.add_parser("record")
    code_state_record.add_argument("--repo-id", required=True)
    code_state_record.add_argument("--upstream-remote", required=True)
    code_state_record.add_argument("--upstream-branch", required=True)
    code_state_record.add_argument("--upstream-commit", required=True)
    code_state_record.add_argument("--local-branch", required=True)
    code_state_record.add_argument("--worktree-path", required=True)
    code_state_record.add_argument("--dirty", action="store_true")
    code_state_record.add_argument("--patch-id", default="")
    code_state_record.add_argument("--diff-hash", default="")
    code_state_record.add_argument("--build-config-json", default="{}")
    code_state_record.add_argument("--runtime-environment-json", default="{}")
    code_state_record.add_argument("--linked-records-json", default="{}")
    code_state_record.add_argument("--known-divergence", default="")

    evidence_parser = subparsers.add_parser("evidence")
    evidence_sub = evidence_parser.add_subparsers(dest="evidence_command", required=True)
    evidence_record = evidence_sub.add_parser("record")
    evidence_record.add_argument("--topic", required=True, dest="topic_id")
    evidence_record.add_argument("--claim", required=True, dest="claim_id")
    evidence_record.add_argument("--type", required=True, dest="evidence_type")
    evidence_record.add_argument("--status", required=True)
    evidence_record.add_argument("--summary", required=True)
    evidence_record.add_argument("--supports-output", action="append", default=[], dest="supports_outputs")
    evidence_record.add_argument("--source-ref", action="append", default=[], dest="source_refs")
    evidence_record.add_argument("--tool-run-id", action="append", default=[], dest="tool_run_ids")
    evidence_record.add_argument("--artifact-id", action="append", default=[], dest="artifact_ids")

    tool_parser = subparsers.add_parser("tool")
    tool_sub = tool_parser.add_subparsers(dest="tool_command", required=True)
    tool_recipe = tool_sub.add_parser("recipe")
    tool_recipe_sub = tool_recipe.add_subparsers(dest="tool_recipe_command", required=True)
    tool_recipe_register = tool_recipe_sub.add_parser("register")
    tool_recipe_register.add_argument("recipe_id")
    tool_recipe_register.add_argument("--family", required=True, dest="tool_family")
    tool_recipe_register.add_argument("--name", required=True, dest="tool_name")
    tool_recipe_register.add_argument("--purpose", required=True)
    tool_recipe_register.add_argument("--required-input", action="append", default=[], dest="required_inputs")
    tool_recipe_register.add_argument("--expected-output", action="append", default=[], dest="expected_outputs")
    tool_recipe_register.add_argument("--invariant", action="append", default=[], dest="invariants")

    tool_run = tool_sub.add_parser("run")
    tool_run_sub = tool_run.add_subparsers(dest="tool_run_command", required=True)
    tool_run_record = tool_run_sub.add_parser("record")
    tool_run_record.add_argument("--recipe", required=True, dest="recipe_id")
    tool_run_record.add_argument("--family", required=True, dest="tool_family")
    tool_run_record.add_argument("--name", required=True, dest="tool_name")
    tool_run_record.add_argument("--topic", required=True, dest="topic_id")
    tool_run_record.add_argument("--claim", required=True, dest="claim_id")
    tool_run_record.add_argument("--inputs-json", default="{}")
    tool_run_record.add_argument("--outputs-json", default="{}")
    tool_run_record.add_argument("--environment-json", default="{}")
    tool_run_record.add_argument("--evidence-status", default="unreviewed")
    tool_run_record.add_argument("--code-state-id", action="append", default=[], dest="code_state_ids")
    tool_run_record.add_argument("--artifact-id", action="append", default=[], dest="artifact_ids")
    tool_run_record.add_argument("--source-ref", action="append", default=[], dest="source_refs")

    tool_execute = tool_sub.add_parser("execute")
    tool_execute.add_argument("executor_id")
    tool_execute.add_argument("--recipe", required=True, dest="recipe_id")
    tool_execute.add_argument("--topic", required=True, dest="topic_id")
    tool_execute.add_argument("--claim", required=True, dest="claim_id")
    tool_execute.add_argument("--inputs-json", required=True)
    tool_execute.add_argument("--evidence-status", default="")
    tool_execute.add_argument("--code-state-id", action="append", default=[], dest="code_state_ids")
    tool_execute.add_argument("--artifact-id", action="append", default=[], dest="artifact_ids")
    tool_execute.add_argument("--source-ref", action="append", default=[], dest="source_refs")

    summary_parser = subparsers.add_parser("summary")
    summary_sub = summary_parser.add_subparsers(dest="summary_command", required=True)
    summary_session = summary_sub.add_parser("session")
    summary_session.add_argument("session_id")
    summary_orientation = summary_sub.add_parser("orientation")
    summary_orientation.add_argument("session_id")

    adapter_parser = subparsers.add_parser("adapter")
    adapter_sub = adapter_parser.add_subparsers(dest="adapter_command", required=True)
    adapter_packet = adapter_sub.add_parser("packet")
    adapter_packet.add_argument("runtime")
    adapter_packet.add_argument("session_id")
    adapter_sub.add_parser("registry")
    adapter_sub.add_parser("public-surfaces")

    trust_parser = subparsers.add_parser("trust")
    trust_sub = trust_parser.add_subparsers(dest="trust_command", required=True)
    trust_preflight = trust_sub.add_parser("preflight")
    _add_trust_request_args(trust_preflight)
    trust_apply = trust_sub.add_parser("apply")
    _add_trust_request_args(trust_apply)

    return parser


def _dispatch(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "init":
        ws = init_workspace(Path(args.base))
        return {"ok": True, "workspace_root": str(ws.root)}

    if args.command == "adapter" and args.adapter_command == "registry":
        return {
            "ok": True,
            "adapter_protocol_registry": require_valid_public_surface(
                "adapter_protocol_registry",
                adapter_protocol_registry(),
            ),
        }

    if args.command == "adapter" and args.adapter_command == "public-surfaces":
        return {"ok": True, "public_surfaces": describe_public_surfaces()}

    ws = init_workspace(Path(args.base))

    if args.command == "topic" and args.topic_command == "create":
        topic = create_topic(ws, args.topic_id, context_id=args.context_id, title=args.title)
        return {"ok": True, **asdict(topic)}

    if args.command == "claim" and args.claim_command == "create":
        claim = create_claim(
            ws,
            topic_id=args.topic_id,
            statement=args.statement,
            evidence_profile=args.evidence_profile,
            confidence_state=args.confidence_state,
            active_uncertainty=args.uncertainty,
            recipe_id=args.recipe_id,
        )
        return {"ok": True, **asdict(claim)}

    if args.command == "session" and args.session_command == "bind":
        session = bind_session(
            ws,
            args.session_id,
            topic_id=args.topic_id,
            context_id=args.context_id,
            active_claim=args.active_claim,
            interaction_profile=args.interaction_profile,
            interaction_steering=args.interaction_steering,
        )
        return {"ok": True, **asdict(session)}

    if args.command == "brief":
        return require_valid_public_surface("execution_brief", build_execution_brief(ws, args.session_id))

    if args.command == "risk" and args.risk_command == "assess":
        claim = get_claim(ws, args.claim_id)
        risk = assess_claim_risk(claim)
        return {"ok": True, "claim_id": args.claim_id, "risk_assessment": asdict(risk)}

    if args.command == "code" and args.code_command == "state" and args.code_state_command == "record":
        state = record_code_state(
            ws,
            repo_id=args.repo_id,
            upstream_remote=args.upstream_remote,
            upstream_branch=args.upstream_branch,
            upstream_commit=args.upstream_commit,
            local_branch=args.local_branch,
            worktree_path=args.worktree_path,
            dirty=args.dirty,
            patch_id=args.patch_id,
            diff_hash=args.diff_hash,
            build_config=_json_object_arg(args.build_config_json, "--build-config-json"),
            runtime_environment=_json_object_arg(args.runtime_environment_json, "--runtime-environment-json"),
            linked_records=_json_object_arg(args.linked_records_json, "--linked-records-json"),
            known_divergence=args.known_divergence,
        )
        return {"ok": True, **require_valid_public_surface("code_state_record", {"ok": True, **asdict(state)})}

    if args.command == "evidence" and args.evidence_command == "record":
        evidence = record_evidence(
            ws,
            topic_id=args.topic_id,
            claim_id=args.claim_id,
            evidence_type=args.evidence_type,
            status=args.status,
            summary=args.summary,
            supports_outputs=args.supports_outputs,
            source_refs=args.source_refs,
            tool_run_ids=args.tool_run_ids,
            artifact_ids=args.artifact_ids,
        )
        return {"ok": True, **require_valid_public_surface("evidence_record", {"ok": True, **asdict(evidence)})}

    if args.command == "tool" and args.tool_command == "recipe" and args.tool_recipe_command == "register":
        recipe = register_tool_recipe(
            ws,
            recipe_id=args.recipe_id,
            tool_family=args.tool_family,
            tool_name=args.tool_name,
            purpose=args.purpose,
            required_inputs=args.required_inputs,
            expected_outputs=args.expected_outputs,
            invariants=args.invariants,
        )
        return {"ok": True, **require_valid_public_surface("tool_recipe_record", {"ok": True, **asdict(recipe)})}

    if args.command == "tool" and args.tool_command == "run" and args.tool_run_command == "record":
        run = record_tool_run(
            ws,
            recipe_id=args.recipe_id,
            tool_family=args.tool_family,
            tool_name=args.tool_name,
            topic_id=args.topic_id,
            claim_id=args.claim_id,
            inputs=_json_object_arg(args.inputs_json, "--inputs-json"),
            outputs=_json_object_arg(args.outputs_json, "--outputs-json"),
            environment=_json_object_arg(args.environment_json, "--environment-json"),
            evidence_status=args.evidence_status,
            code_state_ids=args.code_state_ids,
            artifact_ids=args.artifact_ids,
            source_refs=args.source_refs,
        )
        return {"ok": True, **require_valid_public_surface("tool_run_record", {"ok": True, **asdict(run)})}

    if args.command == "tool" and args.tool_command == "execute":
        run = execute_registered_tool(
            ws,
            executor_id=args.executor_id,
            recipe_id=args.recipe_id,
            topic_id=args.topic_id,
            claim_id=args.claim_id,
            inputs=_json_object_arg(args.inputs_json, "--inputs-json"),
            evidence_status=args.evidence_status,
            code_state_ids=args.code_state_ids,
            artifact_ids=args.artifact_ids,
            source_refs=args.source_refs,
        )
        return {"ok": True, **require_valid_public_surface("tool_run_record", {"ok": True, **asdict(run)})}

    if args.command == "summary" and args.summary_command == "session":
        return {
            "ok": True,
            **require_valid_public_surface(
                "session_summary_bundle",
                asdict(write_session_summary(ws, args.session_id)),
            ),
        }

    if args.command == "summary" and args.summary_command == "orientation":
        return {
            "ok": True,
            **require_valid_public_surface("summary_orientation", read_summary_orientation(ws, args.session_id)),
        }

    if args.command == "adapter" and args.adapter_command == "packet":
        return {
            "ok": True,
            **require_valid_public_surface(
                "adapter_packet",
                build_adapter_packet(ws, args.session_id, runtime=args.runtime),
            ),
        }

    if args.command == "trust" and args.trust_command == "preflight":
        request = _trust_update_request_from_args(args)
        return {
            "ok": True,
            **require_valid_public_surface("trust_update_preflight", preflight_trust_update(ws, request)),
        }

    if args.command == "trust" and args.trust_command == "apply":
        return {
            "ok": True,
            **require_valid_public_surface(
                "trust_update_apply",
                apply_trust_update(ws, _trust_update_request_from_args(args)),
            ),
        }

    raise SystemExit(f"unsupported command: {args.command}")


def _add_trust_request_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("action")
    parser.add_argument("--session", required=True, dest="session_id")
    parser.add_argument("--topic", required=True, dest="topic_id")
    parser.add_argument("--claim", required=True, dest="claim_id")
    parser.add_argument("--requested-state", default="")
    parser.add_argument("--source-kind", default="")
    parser.add_argument("--source-ref", default="")
    parser.add_argument("--evidence-ref", action="append", default=[], dest="evidence_refs")
    parser.add_argument("--code-state-id", action="append", default=[], dest="code_state_ids")
    parser.add_argument("--rationale", default="")
    parser.add_argument("--request-id", default="")


def _trust_update_request_from_args(args: argparse.Namespace) -> TrustUpdateRequest:
    request_id = args.request_id or f"trust-request-{args.session_id}-{args.claim_id}-{args.action}"
    return TrustUpdateRequest(
        request_id=request_id,
        action=args.action,
        session_id=args.session_id,
        topic_id=args.topic_id,
        claim_id=args.claim_id,
        requested_state=args.requested_state,
        source_kind=args.source_kind,
        source_ref=args.source_ref,
        evidence_refs=args.evidence_refs,
        code_state_ids=args.code_state_ids,
        rationale=args.rationale,
    )


def _json_object_arg(raw: str, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{label} must be a JSON object: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"{label} must be a JSON object")
    return payload


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
