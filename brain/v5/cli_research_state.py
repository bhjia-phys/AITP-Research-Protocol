"""CLI wiring for conservative research-state records."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.research_state import (
    attach_artifact,
    attach_artifact_from_local_path,
    classify_research_event,
    create_proof_obligation,
    record_bounded_numerical_evidence,
    register_source,
    update_claim_status,
    update_proof_obligation,
)


def add_research_state_parser(sp) -> None:
    parser = sp.add_parser("research-state")
    sub = parser.add_subparsers(dest="research_state_command", required=True)

    src = sub.add_parser("register-source")
    src.add_argument("--topic", required=True, dest="topic_id")
    src.add_argument("--claim", default="", dest="claim_id")
    src.add_argument("--uri", required=True)
    src.add_argument("--label", required=True)
    src.add_argument("--connector", default="manual", dest="connector_id")
    src.add_argument("--type", default="source", dest="location_type")
    src.add_argument("--external-id", default="")
    src.add_argument("--summary", default="")
    src.add_argument("--source-ref", default="")
    src.add_argument("--metadata-json", default="{}")

    art = sub.add_parser("attach-artifact")
    art.add_argument("--topic", required=True, dest="topic_id")
    art.add_argument("--claim", required=True, dest="claim_id")
    art.add_argument("--type", required=True, dest="artifact_type")
    art.add_argument("--uri", required=True)
    art.add_argument("--summary", required=True)
    art.add_argument("--size-bytes", default=0)
    art.add_argument("--metadata-json", default="{}")
    auta = sub.add_parser("attach-artifact-auto")
    auta.add_argument("--path", required=True)
    auta.add_argument("--topic", required=True, dest="topic_id")
    auta.add_argument("--claim", required=True, dest="claim_id")
    auta.add_argument("--type", required=True, dest="artifact_type")
    auta.add_argument("--summary", required=True)
    auta.add_argument("--metadata-json", default="{}")

    status = sub.add_parser("update-claim-status")
    status.add_argument("--topic", required=True, dest="topic_id")
    status.add_argument("--claim", required=True, dest="claim_id")
    status.add_argument("--maturity-level", required=True)
    status.add_argument("--claim-status", required=True)
    status.add_argument("--scope", required=True)
    status.add_argument("--risk", required=True)
    status.add_argument("--next-action", required=True)
    status.add_argument("--assumption", action="append", default=[], dest="assumptions")
    status.add_argument("--open-gap", action="append", default=[], dest="open_gaps")
    status.add_argument("--source-ref", action="append", default=[], dest="source_refs")
    status.add_argument("--evidence-ref", action="append", default=[], dest="evidence_refs")
    status.add_argument("--artifact-id", action="append", default=[], dest="artifact_ids")

    obligation = sub.add_parser("create-proof-obligation")
    obligation.add_argument("--topic", required=True, dest="topic_id")
    obligation.add_argument("--claim", required=True, dest="claim_id")
    obligation.add_argument("--statement", required=True)
    obligation.add_argument("--type", required=True, dest="obligation_type")
    obligation.add_argument("--status", required=True)
    obligation.add_argument("--maturity-level", required=True)
    obligation.add_argument("--next-action", required=True)
    obligation.add_argument("--required-evidence", action="append", default=[], dest="required_evidence")
    obligation.add_argument("--proof-strategy", action="append", default=[], dest="proof_strategy")
    obligation.add_argument("--failure-mode", action="append", default=[], dest="failure_modes")
    obligation.add_argument("--source-ref", action="append", default=[], dest="source_refs")
    obligation.add_argument("--evidence-ref", action="append", default=[], dest="evidence_refs")
    obligation.add_argument("--artifact-id", action="append", default=[], dest="artifact_ids")

    obligation_update = sub.add_parser("update-proof-obligation")
    obligation_update.add_argument("obligation_id")
    obligation_update.add_argument("--topic", default="", dest="topic_id")
    obligation_update.add_argument("--claim", default="", dest="claim_id")
    obligation_update.add_argument("--statement", default="")
    obligation_update.add_argument("--type", default="", dest="obligation_type")
    obligation_update.add_argument("--status", default="")
    obligation_update.add_argument("--maturity-level", default="")
    obligation_update.add_argument("--next-action", default="")
    obligation_update.add_argument("--required-evidence", action="append", default=None, dest="required_evidence")
    obligation_update.add_argument("--proof-strategy", action="append", default=None, dest="proof_strategy")
    obligation_update.add_argument("--failure-mode", action="append", default=None, dest="failure_modes")
    obligation_update.add_argument("--source-ref", action="append", default=None, dest="source_refs")
    obligation_update.add_argument("--evidence-ref", action="append", default=None, dest="evidence_refs")
    obligation_update.add_argument("--artifact-id", action="append", default=None, dest="artifact_ids")
    obligation_update.add_argument("--replace-lists", action="store_true")

    event = sub.add_parser("classify-event")
    event.add_argument("--topic", required=True, dest="topic_id")
    event.add_argument("--claim", default="", dest="claim_id")
    event.add_argument("--summary", required=True, dest="event_summary")
    event.add_argument("--event-kind", default="")
    event.add_argument("--source-uri", default="")

    bounded = sub.add_parser("bounded-evidence")
    bounded.add_argument("--topic", required=True, dest="topic_id")
    bounded.add_argument("--claim", required=True, dest="claim_id")
    bounded.add_argument("--artifact-uri", required=True)
    bounded.add_argument("--artifact-summary", required=True)
    bounded.add_argument("--artifact-type", default="result_json")
    bounded.add_argument("--evidence-type", default="bounded_numerical_evidence")
    bounded.add_argument("--status", default="supports")
    bounded.add_argument("--supports-output", action="append", default=[], dest="supports_outputs")
    bounded.add_argument("--scope", required=True)
    bounded.add_argument("--recipe", default="fisherd-bounded-numerical-audit", dest="recipe_id")
    bounded.add_argument("--tool-family", default="remote_numerics")
    bounded.add_argument("--tool-name", default="fisherd")
    bounded.add_argument("--command", default="", dest="run_command")
    bounded.add_argument("--machine", default="")
    bounded.add_argument("--remote-root", default="")
    bounded.add_argument("--inputs-json", default="{}")
    bounded.add_argument("--outputs-json", default="{}")
    bounded.add_argument("--environment-json", default="{}")
    bounded.add_argument("--source-ref", action="append", default=[], dest="source_refs")
    bounded.add_argument("--assumption", action="append", default=[], dest="assumptions")
    bounded.add_argument("--open-gap", action="append", default=[], dest="open_gaps")
    bounded.add_argument("--next-action", default="human_review_before_trust_update")


def dispatch_research_state_command(args, ws) -> dict:
    if args.research_state_command == "register-source":
        record = register_source(
            ws,
            topic_id=args.topic_id,
            claim_id=args.claim_id,
            uri=args.uri,
            label=args.label,
            connector_id=args.connector_id,
            location_type=args.location_type,
            external_id=args.external_id,
            summary=args.summary,
            source_ref=args.source_ref,
            metadata=_j(args.metadata_json),
        )
        return {"ok": True, **require_valid_public_surface("reference_location_record", {"ok": True, **asdict(record)})}
    if args.research_state_command == "attach-artifact":
        record = attach_artifact(
            ws,
            topic_id=args.topic_id,
            claim_id=args.claim_id,
            artifact_type=args.artifact_type,
            uri=args.uri,
            summary=args.summary,
            size_bytes=args.size_bytes,
            metadata=_j(args.metadata_json),
        )
        return {"ok": True, **require_valid_public_surface("artifact_record", {"ok": True, **asdict(record)})}
    if args.research_state_command == "attach-artifact-auto":
        record = attach_artifact_from_local_path(
            ws,
            path=args.path,
            topic_id=args.topic_id,
            claim_id=args.claim_id,
            artifact_type=args.artifact_type,
            summary=args.summary,
            metadata=_j(args.metadata_json),
        )
        return {"ok": True, **require_valid_public_surface("artifact_record", {"ok": True, **asdict(record)})}
    if args.research_state_command == "update-claim-status":
        record = update_claim_status(
            ws,
            topic_id=args.topic_id,
            claim_id=args.claim_id,
            maturity_level=args.maturity_level,
            claim_status=args.claim_status,
            scope=args.scope,
            risk=args.risk,
            next_action=args.next_action,
            assumptions=args.assumptions,
            open_gaps=args.open_gaps,
            source_refs=args.source_refs,
            evidence_refs=args.evidence_refs,
            artifact_ids=args.artifact_ids,
        )
        return {"ok": True, **require_valid_public_surface("claim_status_record", {"ok": True, **asdict(record)})}
    if args.research_state_command == "create-proof-obligation":
        record = create_proof_obligation(
            ws,
            topic_id=args.topic_id,
            claim_id=args.claim_id,
            statement=args.statement,
            obligation_type=args.obligation_type,
            status=args.status,
            maturity_level=args.maturity_level,
            next_action=args.next_action,
            required_evidence=args.required_evidence,
            proof_strategy=args.proof_strategy,
            failure_modes=args.failure_modes,
            source_refs=args.source_refs,
            evidence_refs=args.evidence_refs,
            artifact_ids=args.artifact_ids,
        )
        return {"ok": True, **require_valid_public_surface("proof_obligation_record", {"ok": True, **asdict(record)})}
    if args.research_state_command == "update-proof-obligation":
        record = update_proof_obligation(
            ws,
            obligation_id=args.obligation_id,
            topic_id=args.topic_id,
            claim_id=args.claim_id,
            statement=args.statement,
            obligation_type=args.obligation_type,
            status=args.status,
            maturity_level=args.maturity_level,
            next_action=args.next_action,
            required_evidence=args.required_evidence,
            proof_strategy=args.proof_strategy,
            failure_modes=args.failure_modes,
            source_refs=args.source_refs,
            evidence_refs=args.evidence_refs,
            artifact_ids=args.artifact_ids,
            replace_lists=args.replace_lists,
        )
        return {"ok": True, **require_valid_public_surface("proof_obligation_record", {"ok": True, **asdict(record)})}
    if args.research_state_command == "classify-event":
        payload = classify_research_event(
            topic_id=args.topic_id,
            claim_id=args.claim_id,
            event_summary=args.event_summary,
            event_kind=args.event_kind,
            source_uri=args.source_uri,
        )
        return require_valid_public_surface("research_event_classification", payload)
    if args.research_state_command == "bounded-evidence":
        payload = record_bounded_numerical_evidence(
            ws,
            topic_id=args.topic_id,
            claim_id=args.claim_id,
            artifact_uri=args.artifact_uri,
            artifact_summary=args.artifact_summary,
            artifact_type=args.artifact_type,
            evidence_type=args.evidence_type,
            status=args.status,
            supports_outputs=args.supports_outputs,
            scope=args.scope,
            recipe_id=args.recipe_id,
            tool_family=args.tool_family,
            tool_name=args.tool_name,
            command=args.run_command,
            machine=args.machine,
            remote_root=args.remote_root,
            inputs=_j(args.inputs_json),
            outputs=_j(args.outputs_json),
            environment=_j(args.environment_json),
            source_refs=args.source_refs,
            assumptions=args.assumptions,
            open_gaps=args.open_gaps,
            next_action=args.next_action,
        )
        return require_valid_public_surface("bounded_numerical_evidence_bundle", payload)
    raise SystemExit(f"unsupported research-state command: {args.research_state_command}")


def _j(raw: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("expected a JSON object")
    return payload
