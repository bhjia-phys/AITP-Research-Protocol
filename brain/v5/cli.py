"""Small JSON CLI for the AITP v5 kernel."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from brain.v5.brief import build_execution_brief
from brain.v5.cli_adapters import add_adapter_parser, dispatch_adapter_command
from brain.v5.cli_memory import add_memory_parser, dispatch_memory_command
from brain.v5.cli_summaries import add_summary_parser, dispatch_summary_command
from brain.v5.cli_source import add_source_parser, dispatch_source_command
from brain.v5.code import record_code_state
from brain.v5.evidence import record_evidence
from brain.v5.knowledge_connectors import describe_knowledge_connectors
from brain.v5.cli_legacy import add_legacy_parser, dispatch_legacy_command
from brain.v5.cli_interaction import add_interaction_parser, dispatch_interaction_command
from brain.v5.cli_literature import add_literature_parser, dispatch_literature_command
from brain.v5.models import TrustUpdateRequest
from brain.v5.cli_policy import add_policy_parser, dispatch_policy_command
from brain.v5.cli_research_state import add_research_state_parser, dispatch_research_state_command
from brain.v5.cli_validation import add_validation_parser, dispatch_validation_command
from brain.v5.cli_vnext import VNEXT_COMMANDS, add_vnext_parsers, dispatch_vnext_command
from brain.v5.cli_goal import add_goal_parser, dispatch_goal_command
from brain.v5.process_graph import build_process_graph_slice
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.physics_objects import record_object_relation, record_physics_object
from brain.v5.references import record_reference_location
from brain.v5.sensemaking import record_sensemaking_report
from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
from brain.v5.memory import apply_promotion_packet, create_promotion_packet
from brain.v5.risk import assess_claim_risk
from brain.v5.subagents import ingest_subagent_result
from brain.v5.tool_executors import describe_tool_executors, execute_registered_tool_result
from brain.v5.tools import record_tool_run, register_tool_recipe
from brain.v5.trace import persist_hook_trace_event
from brain.v5.trust_audit import audit_claim_trust
from brain.v5.trust_updates import apply_trust_update, get_trust_update_record, preflight_trust_update
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
    print(json.dumps(_jsonable(payload), ensure_ascii=True, sort_keys=True))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aitp-v5", description="AITP v5 kernel CLI")
    parser.add_argument("--base", default=".")
    sp = parser.add_subparsers(dest="command", required=True)

    sp.add_parser("init").add_argument("base")

    tp = sp.add_parser("topic"); ts = tp.add_subparsers(dest="topic_command", required=True)
    tc = ts.add_parser("create"); tc.add_argument("topic_id")
    tc.add_argument("--context", required=True, dest="context_id"); tc.add_argument("--title", required=True)

    cl_p = sp.add_parser("claim"); cl_s = cl_p.add_subparsers(dest="claim_command", required=True)
    cc = cl_s.add_parser("create")
    cc.add_argument("--topic", required=True, dest="topic_id"); cc.add_argument("--statement", required=True)
    cc.add_argument("--evidence-profile", required=True)
    cc.add_argument("--confidence-state", default="hypothesis"); cc.add_argument("--uncertainty", required=True)
    cc.add_argument("--recipe-id", default="")

    se_p = sp.add_parser("session"); se_s = se_p.add_subparsers(dest="session_command", required=True)
    sb = se_s.add_parser("bind"); sb.add_argument("session_id")
    sb.add_argument("--topic", required=True, dest="topic_id"); sb.add_argument("--context", required=True, dest="context_id")
    sb.add_argument("--claim", default="", dest="active_claim")
    sb.add_argument("--interaction-profile", default="collaborator"); sb.add_argument("--interaction-steering", default="")

    sp.add_parser("brief").add_argument("session_id")

    gp = sp.add_parser("graph"); gs = gp.add_subparsers(dest="graph_command", required=True)
    sl = gs.add_parser("slice"); sl.add_argument("session_id")
    sl.add_argument("--claim", default="", dest="claim_id"); sl.add_argument("--limit", type=int, default=80)

    rp = sp.add_parser("risk"); rs = rp.add_subparsers(dest="risk_command", required=True)
    rs.add_parser("assess").add_argument("claim_id")

    cp = sp.add_parser("code"); cs = cp.add_subparsers(dest="code_command", required=True)
    cst = cs.add_parser("state"); css = cst.add_subparsers(dest="code_state_command", required=True)
    csr = css.add_parser("record")
    csr.add_argument("--repo-id", required=True)
    csr.add_argument("--upstream-remote", required=True); csr.add_argument("--upstream-branch", required=True)
    csr.add_argument("--upstream-commit", required=True); csr.add_argument("--local-branch", required=True)
    csr.add_argument("--worktree-path", required=True); csr.add_argument("--dirty", action="store_true")
    csr.add_argument("--patch-id", default=""); csr.add_argument("--diff-hash", default="")
    csr.add_argument("--build-config-json", default="{}"); csr.add_argument("--runtime-environment-json", default="{}")
    csr.add_argument("--linked-records-json", default="{}"); csr.add_argument("--known-divergence", default="")

    ep = sp.add_parser("evidence"); es = ep.add_subparsers(dest="evidence_command", required=True)
    evr = es.add_parser("record")
    evr.add_argument("--topic", required=True, dest="topic_id"); evr.add_argument("--claim", required=True, dest="claim_id")
    evr.add_argument("--type", required=True, dest="evidence_type"); evr.add_argument("--status", required=True)
    evr.add_argument("--summary", required=True)
    evr.add_argument("--supports-output", action="append", default=[], dest="supports_outputs")
    evr.add_argument("--source-ref", action="append", default=[], dest="source_refs")
    evr.add_argument("--tool-run-id", action="append", default=[], dest="tool_run_ids")
    evr.add_argument("--validation-result-id", action="append", default=[], dest="validation_result_ids")
    evr.add_argument("--artifact-id", action="append", default=[], dest="artifact_ids")

    tlp = sp.add_parser("tool"); tls = tlp.add_subparsers(dest="tool_command", required=True)
    tls.add_parser("executors")
    trp = tls.add_parser("recipe"); trs = trp.add_subparsers(dest="tool_recipe_command", required=True)
    tr = trs.add_parser("register"); tr.add_argument("recipe_id")
    tr.add_argument("--family", required=True, dest="tool_family"); tr.add_argument("--name", required=True, dest="tool_name")
    tr.add_argument("--purpose", required=True)
    tr.add_argument("--required-input", action="append", default=[], dest="required_inputs")
    tr.add_argument("--expected-output", action="append", default=[], dest="expected_outputs")
    tr.add_argument("--invariant", action="append", default=[], dest="invariants")

    trun = tls.add_parser("run"); trus = trun.add_subparsers(dest="tool_run_command", required=True)
    trr = trus.add_parser("record")
    trr.add_argument("--recipe", required=True, dest="recipe_id")
    trr.add_argument("--family", required=True, dest="tool_family"); trr.add_argument("--name", required=True, dest="tool_name")
    trr.add_argument("--topic", required=True, dest="topic_id"); trr.add_argument("--claim", required=True, dest="claim_id")
    trr.add_argument("--inputs-json", default="{}"); trr.add_argument("--outputs-json", default="{}")
    trr.add_argument("--environment-json", default="{}"); trr.add_argument("--evidence-status", default="unreviewed")
    trr.add_argument("--code-state-id", action="append", default=[], dest="code_state_ids")
    trr.add_argument("--artifact-id", action="append", default=[], dest="artifact_ids")
    trr.add_argument("--source-ref", action="append", default=[], dest="source_refs")

    te = tls.add_parser("execute"); te.add_argument("executor_id")
    te.add_argument("--recipe", required=True, dest="recipe_id")
    te.add_argument("--topic", required=True, dest="topic_id"); te.add_argument("--claim", required=True, dest="claim_id")
    te.add_argument("--inputs-json", required=True)
    te.add_argument("--evidence-status", default=""); te.add_argument("--evidence-type", default="tool_run")
    te.add_argument("--evidence-summary", default="")
    te.add_argument("--code-state-id", action="append", default=[], dest="code_state_ids")
    te.add_argument("--artifact-id", action="append", default=[], dest="artifact_ids")
    te.add_argument("--source-ref", action="append", default=[], dest="source_refs")
    te.add_argument("--supports-output", action="append", default=[], dest="supports_outputs")

    kp = sp.add_parser("knowledge"); ks = kp.add_subparsers(dest="knowledge_command", required=True)
    ks.add_parser("connectors")

    trcp = sp.add_parser("trace"); trcs = trcp.add_subparsers(dest="trace_command", required=True)
    the = trcs.add_parser("hook-event"); thes = the.add_subparsers(dest="trace_hook_event_command", required=True)
    thp = thes.add_parser("persist"); thp.add_argument("--payload-json", required=True)

    rfp = sp.add_parser("reference"); rfs = rfp.add_subparsers(dest="reference_command", required=True)
    rfl = rfs.add_parser("location"); rls = rfl.add_subparsers(dest="reference_location_command", required=True)
    rlr = rls.add_parser("record")
    rlr.add_argument("--topic", required=True, dest="topic_id"); rlr.add_argument("--claim", default="", dest="claim_id")
    rlr.add_argument("--connector", required=True, dest="connector_id")
    rlr.add_argument("--type", required=True, dest="location_type")
    rlr.add_argument("--uri", required=True); rlr.add_argument("--label", required=True)
    rlr.add_argument("--source-ref", default=""); rlr.add_argument("--external-id", default="")
    rlr.add_argument("--status", default="located"); rlr.add_argument("--summary", default="")
    rlr.add_argument("--metadata-json", default="{}"); rlr.add_argument("--linked-records-json", default="{}")

    add_legacy_parser(sp)
    add_interaction_parser(sp)
    add_literature_parser(sp)
    add_vnext_parsers(sp)
    add_goal_parser(sp)

    add_summary_parser(sp)
    add_source_parser(sp)

    add_adapter_parser(sp)

    op = sp.add_parser("object"); ops = op.add_subparsers(dest="object_command", required=True)
    orr = ops.add_parser("record")
    orr.add_argument("--topic", required=True, dest="topic_id")
    orr.add_argument("--type", required=True, dest="object_type"); orr.add_argument("--name", required=True)
    orr.add_argument("--definition", required=True); orr.add_argument("--notation", default="")
    orr.add_argument("--assumption", action="append", default=[], dest="assumptions")
    orr.add_argument("--source-ref", action="append", default=[], dest="source_refs")
    orr.add_argument("--metadata-json", default="{}"); orr.add_argument("--linked-records-json", default="{}")
    orr.add_argument("--status", default="active")

    rlp = sp.add_parser("relation"); rls2 = rlp.add_subparsers(dest="relation_command", required=True)
    rr = rls2.add_parser("record")
    rr.add_argument("--topic", required=True, dest="topic_id"); rr.add_argument("--type", required=True, dest="relation_type")
    rr.add_argument("--subject", required=True, dest="subject_id"); rr.add_argument("--object", required=True, dest="object_id")
    rr.add_argument("--statement", required=True); rr.add_argument("--claim", default="", dest="claim_id")
    rr.add_argument("--assumption", action="append", default=[], dest="assumptions")
    rr.add_argument("--failure-mode", action="append", default=[], dest="failure_modes")
    rr.add_argument("--source-ref", action="append", default=[], dest="source_refs")
    rr.add_argument("--evidence-ref", action="append", default=[], dest="evidence_refs")
    rr.add_argument("--status", default="hypothesis")

    sg_p = sp.add_parser("sensemaking"); sg_s = sg_p.add_subparsers(dest="sensemaking_command", required=True)
    sr = sg_s.add_parser("report")
    sr.add_argument("--topic", required=True, dest="topic_id"); sr.add_argument("--claim", required=True, dest="claim_id")
    sr.add_argument("--title", required=True); sr.add_argument("--summary", required=True)
    sr.add_argument("--object-id", action="append", default=[], dest="object_ids")
    sr.add_argument("--relation-id", action="append", default=[], dest="relation_ids")
    sr.add_argument("--evidence-ref", action="append", default=[], dest="evidence_refs")
    sr.add_argument("--open-question", action="append", default=[], dest="open_questions")
    sr.add_argument("--next-action", action="append", default=[], dest="next_actions")

    sap = sp.add_parser("subagent"); sas = sap.add_subparsers(dest="subagent_command", required=True)
    sai = sas.add_parser("ingest-result")
    sai.add_argument("--topic", required=True, dest="topic_id")
    sai.add_argument("--packet-json", required=True)
    sai.add_argument("--result-json", required=True)

    chk_p = sp.add_parser("checkpoint"); chk_s = chk_p.add_subparsers(dest="checkpoint_command", required=True)
    chk_r = chk_s.add_parser("request")
    chk_r.add_argument("--topic", required=True, dest="topic_id"); chk_r.add_argument("--claim", required=True, dest="claim_id")
    chk_r.add_argument("--reason", required=True); chk_r.add_argument("--requested-by", required=True)
    chk_r.add_argument("--option", action="append", default=[], dest="options")
    chk_d = chk_s.add_parser("decide")
    chk_d.add_argument("checkpoint_id"); chk_d.add_argument("--decision", required=True)
    chk_d.add_argument("--rationale", required=True); chk_d.add_argument("--decided-by", required=True)

    pp = sp.add_parser("promotion"); pps = pp.add_subparsers(dest="promotion_command", required=True)
    pkt = pps.add_parser("packet"); pkts = pkt.add_subparsers(dest="promotion_packet_command", required=True)
    pc = pkts.add_parser("create")
    pc.add_argument("--topic", required=True, dest="topic_id"); pc.add_argument("--claim", required=True, dest="claim_id")
    pc.add_argument("--proposed-kind", default="scoped_claim", dest="proposed_memory_kind")
    pc.add_argument("--scope", required=True)
    pc.add_argument("--evidence-ref", action="append", default=[], dest="evidence_refs")
    pc.add_argument("--validation-result-id", action="append", default=[], dest="validation_result_ids")
    pc.add_argument("--non-claim", action="append", default=[], dest="non_claims")
    pc.add_argument("--failure-mode", action="append", default=[], dest="known_failure_modes"); pc.add_argument("--failure-mode-review-checkpoint", default="", dest="failure_mode_review_checkpoint_id"); pc.add_argument("--failure-mode-review-result", default="", dest="failure_mode_review_result_id")
    pa = pkts.add_parser("apply")
    pa.add_argument("packet_id")
    pa.add_argument("--checkpoint", required=True, dest="checkpoint_id")

    tp2 = sp.add_parser("trust"); ts2 = tp2.add_subparsers(dest="trust_command", required=True)
    _add_trust_request_args(ts2.add_parser("preflight")); _add_trust_request_args(ts2.add_parser("apply"))
    ta = ts2.add_parser("audit"); ta.add_argument("--claim", required=True, dest="claim_id")
    tur = ts2.add_parser("update-record"); tur.add_argument("update_id")

    add_policy_parser(sp)

    add_validation_parser(sp)

    add_memory_parser(sp)
    add_research_state_parser(sp)

    return parser


def _dispatch(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "init":
        return {"ok": True, "workspace_root": str(init_workspace(Path(args.base)).root)}
    if args.command == "adapter" and args.adapter_command in {"registry", "public-surfaces", "record-gate-audit", "smoke-coverage"}:
        return dispatch_adapter_command(args, None)

    ws = init_workspace(Path(args.base))

    if args.command == "policy":
        return dispatch_policy_command(args, ws)

    if args.command == "topic" and args.topic_command == "create":
        return {"ok": True, **asdict(create_topic(ws, args.topic_id, context_id=args.context_id, title=args.title))}
    if args.command == "claim" and args.claim_command == "create":
        return {"ok": True, **asdict(create_claim(ws, topic_id=args.topic_id, statement=args.statement,
            evidence_profile=args.evidence_profile, confidence_state=args.confidence_state,
            active_uncertainty=args.uncertainty, recipe_id=args.recipe_id))}
    if args.command == "session" and args.session_command == "bind":
        return {"ok": True, **asdict(bind_session(ws, args.session_id, topic_id=args.topic_id,
            context_id=args.context_id, active_claim=args.active_claim,
            interaction_profile=args.interaction_profile, interaction_steering=args.interaction_steering))}
    if args.command == "brief":
        return require_valid_public_surface("execution_brief", build_execution_brief(ws, args.session_id))
    if args.command == "graph" and args.graph_command == "slice":
        return require_valid_public_surface(
            "process_graph_slice",
            build_process_graph_slice(ws, args.session_id, claim_id=args.claim_id, limit=args.limit),
        )
    if args.command == "risk" and args.risk_command == "assess":
        return {"ok": True, "claim_id": args.claim_id, "risk_assessment": asdict(assess_claim_risk(get_claim(ws, args.claim_id)))}

    if args.command == "code" and args.code_command == "state" and args.code_state_command == "record":
        st = record_code_state(ws, repo_id=args.repo_id, upstream_remote=args.upstream_remote,
            upstream_branch=args.upstream_branch, upstream_commit=args.upstream_commit,
            local_branch=args.local_branch, worktree_path=args.worktree_path, dirty=args.dirty,
            patch_id=args.patch_id, diff_hash=args.diff_hash,
            build_config=_j(args.build_config_json), runtime_environment=_j(args.runtime_environment_json),
            linked_records=_j(args.linked_records_json), known_divergence=args.known_divergence)
        return {"ok": True, **require_valid_public_surface("code_state_record", {"ok": True, **asdict(st)})}

    if args.command == "evidence" and args.evidence_command == "record":
        ev = record_evidence(ws, topic_id=args.topic_id, claim_id=args.claim_id,
            evidence_type=args.evidence_type, status=args.status, summary=args.summary,
            supports_outputs=args.supports_outputs, source_refs=args.source_refs,
            tool_run_ids=args.tool_run_ids, validation_result_ids=args.validation_result_ids,
            artifact_ids=args.artifact_ids)
        return {"ok": True, **require_valid_public_surface("evidence_record", {"ok": True, **asdict(ev)})}

    if args.command == "tool" and args.tool_command == "recipe" and args.tool_recipe_command == "register":
        rc = register_tool_recipe(ws, recipe_id=args.recipe_id, tool_family=args.tool_family,
            tool_name=args.tool_name, purpose=args.purpose, required_inputs=args.required_inputs,
            expected_outputs=args.expected_outputs, invariants=args.invariants)
        return {"ok": True, **require_valid_public_surface("tool_recipe_record", {"ok": True, **asdict(rc)})}

    if args.command == "tool" and args.tool_command == "run" and args.tool_run_command == "record":
        rn = record_tool_run(ws, recipe_id=args.recipe_id, tool_family=args.tool_family,
            tool_name=args.tool_name, topic_id=args.topic_id, claim_id=args.claim_id,
            inputs=_j(args.inputs_json), outputs=_j(args.outputs_json),
            environment=_j(args.environment_json), evidence_status=args.evidence_status,
            code_state_ids=args.code_state_ids, artifact_ids=args.artifact_ids, source_refs=args.source_refs)
        return {"ok": True, **require_valid_public_surface("tool_run_record", {"ok": True, **asdict(rn)})}

    if args.command == "tool" and args.tool_command == "executors":
        return require_valid_public_surface("tool_executor_catalog", describe_tool_executors())

    if args.command == "tool" and args.tool_command == "execute":
        r = execute_registered_tool_result(ws, executor_id=args.executor_id, recipe_id=args.recipe_id,
            topic_id=args.topic_id, claim_id=args.claim_id, inputs=_j(args.inputs_json),
            evidence_status=args.evidence_status, code_state_ids=args.code_state_ids,
            artifact_ids=args.artifact_ids, source_refs=args.source_refs,
            supports_outputs=args.supports_outputs, evidence_type=args.evidence_type,
            evidence_summary=args.evidence_summary)
        p = {"ok": True, **asdict(r.run)}
        if r.evidence is not None:
            p["evidence_id"] = r.evidence.evidence_id
            p["evidence"] = require_valid_public_surface("evidence_record", {"ok": True, **asdict(r.evidence)})
        return {"ok": True, **require_valid_public_surface("tool_run_record", p)}

    if args.command == "knowledge" and args.knowledge_command == "connectors":
        return require_valid_public_surface("knowledge_connector_catalog", describe_knowledge_connectors())

    if args.command == "trace" and args.trace_command == "hook-event" and args.trace_hook_event_command == "persist":
        return require_valid_public_surface("hook_trace_event_record", persist_hook_trace_event(ws, _j(args.payload_json)))

    if args.command == "reference" and args.reference_command == "location" and args.reference_location_command == "record":
        loc = record_reference_location(ws, topic_id=args.topic_id, claim_id=args.claim_id,
            connector_id=args.connector_id, location_type=args.location_type, uri=args.uri, label=args.label,
            source_ref=args.source_ref, external_id=args.external_id, status=args.status, summary=args.summary,
            metadata=_j(args.metadata_json), linked_records=_j(args.linked_records_json))
        return {"ok": True, **require_valid_public_surface("reference_location_record", {"ok": True, **asdict(loc)})}

    if args.command == "legacy":
        return dispatch_legacy_command(args, ws)
    if args.command == "interaction":
        return dispatch_interaction_command(args, ws)
    if args.command == "literature":
        return dispatch_literature_command(args, ws)
    if args.command in VNEXT_COMMANDS:
        return dispatch_vnext_command(args, ws)
    if args.command == "goal":
        return dispatch_goal_command(args, ws)

    if args.command == "summary":
        return dispatch_summary_command(args, ws)
    if args.command == "source":
        return dispatch_source_command(args, ws)
    if args.command == "adapter":
        return dispatch_adapter_command(args, ws)

    if args.command == "trust":
        if args.trust_command == "audit":
            return require_valid_public_surface("claim_trust_audit", audit_claim_trust(ws, claim_id=args.claim_id))
        if args.trust_command == "update-record":
            record = get_trust_update_record(ws, args.update_id)
            return require_valid_public_surface("trust_update_record", {"ok": True, **asdict(record)})
        req = _trust_update_request_from_args(args)
        if args.trust_command == "preflight":
            return {"ok": True, **require_valid_public_surface("trust_update_preflight", preflight_trust_update(ws, req))}
        return {"ok": True, **require_valid_public_surface("trust_update_apply", apply_trust_update(ws, req))}

    if args.command == "validation":
        return dispatch_validation_command(args, ws)

    if args.command == "memory":
        return dispatch_memory_command(args, ws)

    if args.command == "research-state":
        return dispatch_research_state_command(args, ws)

    if args.command == "object" and args.object_command == "record":
        obj = record_physics_object(ws, topic_id=args.topic_id, object_type=args.object_type,
            name=args.name, definition=args.definition, notation=args.notation, assumptions=args.assumptions,
            source_refs=args.source_refs, metadata=_j(args.metadata_json),
            linked_records=_j(args.linked_records_json), status=args.status)
        return {"ok": True, **require_valid_public_surface("physics_object_record", {"ok": True, **asdict(obj)})}

    if args.command == "relation" and args.relation_command == "record":
        rel = record_object_relation(ws, topic_id=args.topic_id, relation_type=args.relation_type,
            subject_id=args.subject_id, object_id=args.object_id, statement=args.statement,
            claim_id=args.claim_id, assumptions=args.assumptions, failure_modes=args.failure_modes,
            source_refs=args.source_refs, evidence_refs=args.evidence_refs, status=args.status)
        return {"ok": True, **require_valid_public_surface("object_relation_record", {"ok": True, **asdict(rel)})}

    if args.command == "sensemaking" and args.sensemaking_command == "report":
        rpt = record_sensemaking_report(ws, topic_id=args.topic_id, claim_id=args.claim_id,
            title=args.title, summary=args.summary, object_ids=args.object_ids,
            relation_ids=args.relation_ids, evidence_refs=args.evidence_refs,
            open_questions=args.open_questions, next_actions=args.next_actions)
        return {"ok": True, **require_valid_public_surface("sensemaking_report_record", {"ok": True, **asdict(rpt)})}

    if args.command == "subagent" and args.subagent_command == "ingest-result":
        result = ingest_subagent_result(
            ws,
            _j(args.packet_json),
            topic_id=args.topic_id,
            result_payload=_j(args.result_json),
        )
        return _subagent_ingestion_payload(result)

    if args.command == "checkpoint" and args.checkpoint_command == "request":
        chk = request_human_checkpoint(ws, topic_id=args.topic_id, claim_id=args.claim_id,
            reason=args.reason, requested_by=args.requested_by, options=args.options)
        return {"ok": True, **require_valid_public_surface("human_checkpoint_record", {"ok": True, **asdict(chk)})}

    if args.command == "checkpoint" and args.checkpoint_command == "decide":
        dec = decide_human_checkpoint(ws, checkpoint_id=args.checkpoint_id,
            decision=args.decision, rationale=args.rationale, decided_by=args.decided_by)
        return {"ok": True, **require_valid_public_surface("human_checkpoint_record", {"ok": True, **asdict(dec)})}

    if args.command == "promotion" and args.promotion_command == "packet" and args.promotion_packet_command == "create":
        pkt = create_promotion_packet(ws, topic_id=args.topic_id, claim_id=args.claim_id,
            proposed_memory_kind=args.proposed_memory_kind, scope=args.scope,
            evidence_refs=args.evidence_refs, validation_result_ids=args.validation_result_ids,
            non_claims=args.non_claims,
            known_failure_modes=args.known_failure_modes, failure_mode_review_checkpoint_id=args.failure_mode_review_checkpoint_id, failure_mode_review_result_id=args.failure_mode_review_result_id)
        return {"ok": True, **require_valid_public_surface("promotion_packet_record", {"ok": True, **asdict(pkt)})}

    if args.command == "promotion" and args.promotion_command == "packet" and args.promotion_packet_command == "apply":
        entry = apply_promotion_packet(ws, packet_id=args.packet_id, checkpoint_id=args.checkpoint_id)
        return {"ok": True, **require_valid_public_surface("memory_entry_record", {"ok": True, **asdict(entry)})}

    raise SystemExit(f"unsupported command: {args.command}")


def _add_trust_request_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("action"); p.add_argument("--session", required=True, dest="session_id")
    p.add_argument("--topic", required=True, dest="topic_id"); p.add_argument("--claim", required=True, dest="claim_id")
    p.add_argument("--requested-state", default=""); p.add_argument("--source-kind", default="")
    p.add_argument("--source-ref", default="")
    p.add_argument("--evidence-ref", action="append", default=[], dest="evidence_refs")
    p.add_argument("--code-state-id", action="append", default=[], dest="code_state_ids")
    p.add_argument("--preflight-token", default="")
    p.add_argument("--rationale", default=""); p.add_argument("--request-id", default="")


def _trust_update_request_from_args(args: argparse.Namespace) -> TrustUpdateRequest:
    return TrustUpdateRequest(
        request_id=args.request_id or f"trust-request-{args.session_id}-{args.claim_id}-{args.action}",
        action=args.action, session_id=args.session_id, topic_id=args.topic_id, claim_id=args.claim_id,
        requested_state=args.requested_state, source_kind=args.source_kind, source_ref=args.source_ref,
        evidence_refs=args.evidence_refs, code_state_ids=args.code_state_ids, rationale=args.rationale,
        preflight_token=args.preflight_token,
    )


def _j(raw: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("expected a JSON object")
    return payload


def _subagent_ingestion_payload(result) -> dict[str, Any]:
    payload = result.to_payload()
    payload["evidence"] = require_valid_public_surface("evidence_record", {"ok": True, **payload["evidence"]})
    payload["proposal"] = require_valid_public_surface("sensemaking_report_record", {"ok": True, **payload["proposal"]})
    return {"ok": True, **payload}


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
