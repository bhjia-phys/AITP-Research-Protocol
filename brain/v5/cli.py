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
from brain.v5.models import TrustUpdateRequest
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.risk import assess_claim_risk
from brain.v5.summaries import read_summary_orientation, write_session_summary
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
