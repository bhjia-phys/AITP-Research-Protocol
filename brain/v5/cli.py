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
from brain.v5.code import capture_code_state_from_git, record_code_state
from brain.v5.curated_rag_corpus import ingest_curated_rag_corpus
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
from brain.v5.claim_relation_map import build_claim_relation_map
from brain.v5.exploration import exploratory_record_payload, record_exploratory_record
from brain.v5.process_graph import build_process_graph_slice
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.recording_navigator import (
    build_recording_navigation_state,
    classify_recording_candidate,
    expand_recording_slot,
    verify_recording_effect,
)
from brain.v5.physics_objects import record_object_relation, record_physics_object
from brain.v5.references import record_reference_location
from brain.v5.routes import record_research_route, research_route_payload
from brain.v5.sensemaking import record_sensemaking_report
from brain.v5.source_assets import capture_source_asset_from_local_path, register_source_asset, source_asset_payload
from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
from brain.v5.memory import apply_promotion_packet, create_promotion_packet
from brain.v5.markdown import write_text_atomic
from brain.v5.risk import assess_claim_risk
from brain.v5.subagents import ingest_subagent_result
from brain.v5.tool_executors import describe_tool_executors, execute_registered_tool_result
from brain.v5.tools import (
    capture_tool_run_from_local_path,
    record_tool_run,
    register_tool_recipe,
    tool_run_payload,
)
from brain.v5.trace import persist_hook_trace_event
from brain.v5.trust_audit import audit_claim_trust
from brain.v5.trust_updates import apply_trust_update, get_trust_update_record, preflight_trust_update
from brain.v5.workspace_inventory import build_workspace_inventory, write_workspace_inventory_report
from brain.v5.workspace_migration_plan import build_workspace_migration_plan, write_workspace_migration_plan_report
from brain.v5.workspace_old_store_manifest import (
    build_workspace_old_store_manifest,
    write_workspace_old_store_manifest_report,
)
from brain.v5.workspace_file_migration_ledger import (
    build_workspace_file_migration_ledger,
    compact_workspace_file_migration_ledger,
    write_workspace_file_migration_ledger,
)
from brain.v5.workspace_migration_health import build_workspace_migration_health
from brain.v5.workspace_old_store_import import (
    apply_workspace_old_store_import_plan,
    build_workspace_old_store_import_plan,
    write_workspace_old_store_import_result,
)
from brain.v5.workspace_recovery_binding_repair import (
    apply_workspace_recovery_binding_repair,
    build_workspace_recovery_binding_repair,
    write_workspace_recovery_binding_repair,
)
from brain.v5.workspace_recovery_audit import (
    build_workspace_recovery_audit,
    compact_workspace_recovery_audit,
    write_workspace_recovery_audit,
)
from brain.v5.workspace_recording_audit import (
    build_workspace_recording_audit,
    write_workspace_recording_audit,
)
from brain.v5.workspace import (
    bind_session,
    create_claim,
    create_topic,
    get_claim,
    init_workspace,
)


def _workspace_path_arg(value: str, workspace_root: str | Path | None) -> str:
    """Resolve workspace command paths without depending on the process cwd."""

    if not value:
        return ""
    path = Path(value)
    if path.is_absolute() or not workspace_root:
        return str(path)
    return str(Path(workspace_root) / path)


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

    wp = sp.add_parser("workspace"); wps = wp.add_subparsers(dest="workspace_command", required=True)
    wi = wps.add_parser("inventory")
    wi.add_argument("--workspace-root", default="")
    wi.add_argument("--write-json", default="")
    wi.add_argument("--write-report", default="")
    wmp = wps.add_parser("migration-plan")
    wmp.add_argument("--workspace-root", default="")
    wmp.add_argument("--inventory-json", default="")
    wmp.add_argument("--write-json", default="")
    wmp.add_argument("--write-report", default="")
    wos = wps.add_parser("old-store-manifest")
    wos.add_argument("--workspace-root", default="")
    wos.add_argument("--write-json", default="")
    wos.add_argument("--write-report", default="")
    wfl = wps.add_parser("file-migration-ledger")
    wfl.add_argument("--workspace-root", default="")
    wfl.add_argument("--migration-plan-json", default="")
    wfl.add_argument("--old-store-manifest-json", default="")
    wfl.add_argument("--legacy-accounting-dir", default="")
    wfl.add_argument("--write-json", default="")
    wfl.add_argument("--write-report", default="")
    wfl.add_argument("--compact", action="store_true")
    wmh = wps.add_parser("migration-health")
    wmh.add_argument("--sample-limit", type=int, default=5)
    wosi = wps.add_parser("old-store-import")
    wosi.add_argument("--workspace-root", default="")
    wosi.add_argument("--old-store-manifest-json", default="")
    wosi.add_argument("--topic", action="append", default=[], dest="topics")
    wosi.add_argument("--apply", action="store_true")
    wosi.add_argument("--write-json", default="")
    wosi.add_argument("--write-report", default="")
    wrbr = wps.add_parser("recovery-binding-repair")
    wrbr.add_argument("--topic", action="append", default=[], dest="topics")
    wrbr.add_argument("--apply", action="store_true")
    wrbr.add_argument("--write-json", default="")
    wrbr.add_argument("--write-report", default="")
    wra = wps.add_parser("recovery-audit")
    wra.add_argument("--migration-plan-json", default="")
    wra.add_argument("--topic", action="append", default=[], dest="topics")
    wra.add_argument("--write-json", default="")
    wra.add_argument("--write-report", default="")
    wra.add_argument("--compact", action="store_true")
    wrec = wps.add_parser("recording-audit")
    wrec.add_argument("--migration-plan-json", default="")
    wrec.add_argument("--topic", action="append", default=[], dest="topics")
    wrec.add_argument("--write-json", default="")
    wrec.add_argument("--write-report", default="")
    wrec.add_argument("--limit", type=int, default=40)

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
    sp.add_parser("relation-map").add_argument("session_id")

    ap = sp.add_parser("asset"); aps = ap.add_subparsers(dest="asset_command", required=True)
    ar = aps.add_parser("register")
    ar.add_argument("--topic", required=True, dest="topic_id")
    ar.add_argument("--type", required=True, dest="asset_type")
    ar.add_argument("--uri", required=True)
    ar.add_argument("--title", required=True)
    ar.add_argument("--claim", default="", dest="claim_id")
    ar.add_argument("--label", default="")
    ar.add_argument("--content-hash", default="")
    ar.add_argument("--hash-algorithm", default="")
    ar.add_argument("--version-anchor-json", default="{}")
    ar.add_argument("--acquired-at", default="")
    ar.add_argument("--source-kind", default="manual")
    ar.add_argument("--summary", default="")
    ar.add_argument("--source-ref", action="append", default=[], dest="source_refs")
    ar.add_argument("--artifact-id", action="append", default=[], dest="artifact_ids")
    ar.add_argument("--code-state-id", action="append", default=[], dest="code_state_ids")
    ar.add_argument("--reference-location-id", action="append", default=[], dest="reference_location_ids")
    ar.add_argument("--derived-from", action="append", default=[], dest="derived_from")
    ar.add_argument("--metadata-json", default="{}")
    ar.add_argument("--linked-records-json", default="{}")
    aa = aps.add_parser("capture-auto")
    aa.add_argument("--path", required=True)
    aa.add_argument("--topic", required=True, dest="topic_id")
    aa.add_argument("--claim", default="", dest="claim_id")
    aa.add_argument("--type", default="", dest="asset_type")
    aa.add_argument("--title", default="")
    aa.add_argument("--label", default="")
    aa.add_argument("--version-anchor-json", default="{}")
    aa.add_argument("--acquired-at", default="")
    aa.add_argument("--source-kind", default="local_file_auto")
    aa.add_argument("--summary", default="")
    aa.add_argument("--source-ref", action="append", default=[], dest="source_refs")
    aa.add_argument("--artifact-id", action="append", default=[], dest="artifact_ids")
    aa.add_argument("--code-state-id", action="append", default=[], dest="code_state_ids")
    aa.add_argument("--reference-location-id", action="append", default=[], dest="reference_location_ids")
    aa.add_argument("--derived-from", action="append", default=[], dest="derived_from")
    aa.add_argument("--metadata-json", default="{}")
    aa.add_argument("--linked-records-json", default="{}")

    gp = sp.add_parser("graph"); gs = gp.add_subparsers(dest="graph_command", required=True)
    sl = gs.add_parser("slice"); sl.add_argument("session_id")
    sl.add_argument("--claim", default="", dest="claim_id"); sl.add_argument("--limit", type=int, default=80)
    mp = gs.add_parser("moment-policy"); mp.add_argument("session_id")
    mp.add_argument("--claim", default="", dest="claim_id"); mp.add_argument("--limit", type=int, default=80)

    recp = sp.add_parser("recording"); recs = recp.add_subparsers(dest="recording_command", required=True)
    rcc = recs.add_parser("classify-candidate")
    rcc.add_argument("--session", default="", dest="session_id")
    rcc.add_argument("--event-type", required=True)
    rcc.add_argument("--summary", default="")
    rcc.add_argument("--topic", default="", dest="topic_id")
    rcc.add_argument("--claim", default="", dest="claim_id")
    rcc.add_argument("--touched-ref", action="append", default=[], dest="touched_refs")
    rcc.add_argument("--produced-artifact", action="append", default=[], dest="produced_artifacts")
    rcc.add_argument("--tool-call-id", default="")
    rcc.add_argument("--risk-hint", default="")
    rcc.add_argument("--payload-json", default="{}")
    rns = recs.add_parser("navigation-state")
    rns.add_argument("session_id")
    rns.add_argument("--claim", default="", dest="claim_id")
    rns.add_argument("--limit", type=int, default=40)
    res = recs.add_parser("expand-slot")
    res.add_argument("session_id")
    res.add_argument("--slot", required=True)
    res.add_argument("--claim", default="", dest="claim_id")
    res.add_argument("--candidate-json", default="{}")
    rev = recs.add_parser("verify-effect")
    rev.add_argument("session_id")
    rev.add_argument("--claim", default="", dest="claim_id")
    rev.add_argument("--expected-ref", action="append", default=[], dest="expected_refs")
    rev.add_argument("--before-node-id", action="append", default=[], dest="before_node_ids")
    rev.add_argument("--before-edge-id", action="append", default=[], dest="before_edge_ids")
    rev.add_argument("--limit", type=int, default=80)

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
    csa = css.add_parser("auto")
    csa.add_argument("--worktree-path", required=True)
    csa.add_argument("--repo-id", default="")
    csa.add_argument("--topic", default="", dest="topic_id")
    csa.add_argument("--claim", default="", dest="claim_id")
    csa.add_argument("--session", default="", dest="session_id")
    csa.add_argument("--build-config-json", default="{}")
    csa.add_argument("--runtime-environment-json", default="{}")
    csa.add_argument("--linked-records-json", default="{}")
    csa.add_argument("--known-divergence", default="")
    csa.add_argument("--write-patch-artifact", action="store_true")

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
    tra = trus.add_parser("capture-auto")
    tra.add_argument("--path", required=True)
    tra.add_argument("--recipe", required=True, dest="recipe_id")
    tra.add_argument("--family", required=True, dest="tool_family")
    tra.add_argument("--name", required=True, dest="tool_name")
    tra.add_argument("--topic", required=True, dest="topic_id")
    tra.add_argument("--claim", required=True, dest="claim_id")
    tra.add_argument("--inputs-json", default="{}")
    tra.add_argument("--outputs-json", default="{}")
    tra.add_argument("--environment-json", default="{}")
    tra.add_argument("--evidence-status", default="unreviewed")
    tra.add_argument("--code-state-id", action="append", default=[], dest="code_state_ids")
    tra.add_argument("--artifact-id", action="append", default=[], dest="artifact_ids")
    tra.add_argument("--source-ref", action="append", default=[], dest="source_refs")
    tra.add_argument("--summary", default="")
    tra.add_argument("--max-preview-chars", type=int, default=1200)

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

    crp = sp.add_parser("curated-rag"); crs = crp.add_subparsers(dest="curated_rag_command", required=True)
    cri = crs.add_parser("ingest")
    cri.add_argument("--path", action="append", required=True, dest="paths")
    cri.add_argument("--corpus-id", default="")
    cri.add_argument("--tag", action="append", default=[], dest="tags")
    cri.add_argument("--domain-hint", action="append", default=[], dest="domain_hints")
    cri.add_argument("--topic-hint", action="append", default=[], dest="topic_hints")
    cri.add_argument("--language", default="en")
    cri.add_argument("--priority", default="medium")
    cri.add_argument("--chunk-token-limit", type=int, default=220)
    cri.add_argument("--title-prefix", default="")
    cri.add_argument("--asset-type", default="")
    cri.add_argument("--no-rebuild-index", action="store_true")

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

    ex_p = sp.add_parser("exploration"); ex_s = ex_p.add_subparsers(dest="exploration_command", required=True)
    er = ex_s.add_parser("record")
    er.add_argument("--topic", required=True, dest="topic_id")
    er.add_argument("--claim", default="", dest="claim_id")
    er.add_argument("--session", default="", dest="session_id")
    er.add_argument("--type", required=True, dest="exploration_type")
    er.add_argument("--title", required=True)
    er.add_argument("--focal-question", required=True)
    er.add_argument("--summary", required=True)
    er.add_argument("--original-question", default="")
    er.add_argument("--local-question", default="")
    er.add_argument("--status", default="open")
    er.add_argument("--object-id", action="append", default=[], dest="object_ids")
    er.add_argument("--relation-id", action="append", default=[], dest="relation_ids")
    er.add_argument("--source-ref", action="append", default=[], dest="source_refs")
    er.add_argument("--artifact-id", action="append", default=[], dest="artifact_ids")
    er.add_argument("--parent-record-id", action="append", default=[], dest="parent_record_ids")
    er.add_argument("--derived-record-id", action="append", default=[], dest="derived_record_ids")
    er.add_argument("--reasoning-move", action="append", default=[], dest="reasoning_moves")
    er.add_argument("--backtrace-target", action="append", default=[], dest="backtrace_targets")
    er.add_argument("--candidate-path", action="append", default=[], dest="candidate_paths")
    er.add_argument("--relation-path-question", action="append", default=[], dest="relation_path_questions")
    er.add_argument("--definition-boundary-question", action="append", default=[], dest="definition_boundary_questions")
    er.add_argument("--derivation-backtrace-question", action="append", default=[], dest="derivation_backtrace_questions")
    er.add_argument("--source-dependency-question", action="append", default=[], dest="source_dependency_questions")
    er.add_argument("--original-question-guard", action="append", default=[], dest="original_question_guard")
    er.add_argument("--unresolved-point", action="append", default=[], dest="unresolved_points")
    er.add_argument("--next-action", action="append", default=[], dest="next_actions")
    er.add_argument("--human-steering", default="")
    er.add_argument("--metadata-json", default="{}")

    rt_p = sp.add_parser("route"); rt_s = rt_p.add_subparsers(dest="route_command", required=True)
    rtr = rt_s.add_parser("record")
    rtr.add_argument("--topic", required=True, dest="topic_id")
    rtr.add_argument("--claim", default="", dest="claim_id")
    rtr.add_argument("--session", default="", dest="session_id")
    rtr.add_argument("--type", required=True, dest="route_type")
    rtr.add_argument("--status", required=True)
    rtr.add_argument("--title", required=True)
    rtr.add_argument("--rationale", required=True)
    rtr.add_argument("--current-question", default="")
    rtr.add_argument("--next-action", default="")
    rtr.add_argument("--failure-mode", action="append", default=[], dest="failure_modes")
    rtr.add_argument("--source-ref", action="append", default=[], dest="source_refs")
    rtr.add_argument("--evidence-ref", action="append", default=[], dest="evidence_refs")
    rtr.add_argument("--artifact-id", action="append", default=[], dest="artifact_ids")
    rtr.add_argument("--parent-route-id", action="append", default=[], dest="parent_route_ids")
    rtr.add_argument("--checkpoint-id", action="append", default=[], dest="checkpoint_ids")
    rtr.add_argument("--exploratory-record-id", action="append", default=[], dest="exploratory_record_ids")
    rtr.add_argument("--object-id", action="append", default=[], dest="object_ids")
    rtr.add_argument("--relation-id", action="append", default=[], dest="relation_ids")
    rtr.add_argument("--decision-rationale", default="")
    rtr.add_argument("--pivot-reason", default="")
    rtr.add_argument("--metadata-json", default="{}")

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
    if args.command == "adapter" and args.adapter_command in {
        "registry",
        "public-surfaces",
        "bridge-targets",
        "bridge-acceptance",
        "payload-profiles",
        "record-gate-audit",
        "smoke-coverage",
    }:
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
    if args.command == "relation-map":
        return require_valid_public_surface("claim_relation_map", build_claim_relation_map(ws, args.session_id))
    if args.command == "asset" and args.asset_command == "register":
        asset = register_source_asset(
            ws,
            topic_id=args.topic_id,
            claim_id=args.claim_id,
            asset_type=args.asset_type,
            uri=args.uri,
            title=args.title,
            label=args.label,
            content_hash=args.content_hash,
            hash_algorithm=args.hash_algorithm,
            version_anchor=_j(args.version_anchor_json),
            acquired_at=args.acquired_at,
            source_kind=args.source_kind,
            summary=args.summary,
            source_refs=args.source_refs,
            artifact_ids=args.artifact_ids,
            code_state_ids=args.code_state_ids,
            reference_location_ids=args.reference_location_ids,
            derived_from=args.derived_from,
            metadata=_j(args.metadata_json),
            linked_records=_j(args.linked_records_json),
        )
        return require_valid_public_surface("source_asset_record", source_asset_payload(asset))
    if args.command == "asset" and args.asset_command == "capture-auto":
        asset = capture_source_asset_from_local_path(
            ws,
            path=args.path,
            topic_id=args.topic_id,
            claim_id=args.claim_id,
            asset_type=args.asset_type,
            title=args.title,
            label=args.label,
            version_anchor=_j(args.version_anchor_json),
            acquired_at=args.acquired_at,
            source_kind=args.source_kind,
            summary=args.summary,
            source_refs=args.source_refs,
            artifact_ids=args.artifact_ids,
            code_state_ids=args.code_state_ids,
            reference_location_ids=args.reference_location_ids,
            derived_from=args.derived_from,
            metadata=_j(args.metadata_json),
            linked_records=_j(args.linked_records_json),
        )
        return require_valid_public_surface("source_asset_record", source_asset_payload(asset))
    if args.command == "graph" and args.graph_command == "slice":
        return require_valid_public_surface(
            "process_graph_slice",
            build_process_graph_slice(ws, args.session_id, claim_id=args.claim_id, limit=args.limit),
        )
    if args.command == "graph" and args.graph_command == "moment-policy":
        graph = build_process_graph_slice(ws, args.session_id, claim_id=args.claim_id, limit=args.limit)
        return require_valid_public_surface("host_agnostic_moment_policy", graph["moment_policy"])
    if args.command == "recording" and args.recording_command == "classify-candidate":
        return require_valid_public_surface(
            "recording_candidate_classification",
            classify_recording_candidate(
                ws,
                session_id=args.session_id,
                event_type=args.event_type,
                summary=args.summary,
                topic_id=args.topic_id,
                claim_id=args.claim_id,
                touched_refs=args.touched_refs,
                produced_artifacts=args.produced_artifacts,
                tool_call_id=args.tool_call_id,
                risk_hint=args.risk_hint,
                payload=_j(args.payload_json),
            ),
        )
    if args.command == "recording" and args.recording_command == "navigation-state":
        return require_valid_public_surface(
            "recording_navigation_state",
            build_recording_navigation_state(ws, args.session_id, claim_id=args.claim_id, limit=args.limit),
        )
    if args.command == "recording" and args.recording_command == "expand-slot":
        return require_valid_public_surface(
            "recording_slot_expansion",
            expand_recording_slot(ws, args.session_id, args.slot, claim_id=args.claim_id, candidate=_j(args.candidate_json)),
        )
    if args.command == "recording" and args.recording_command == "verify-effect":
        return require_valid_public_surface(
            "recording_effect_verification",
            verify_recording_effect(
                ws,
                args.session_id,
                expected_refs=args.expected_refs,
                before_node_ids=args.before_node_ids,
                before_edge_ids=args.before_edge_ids,
                claim_id=args.claim_id,
                limit=args.limit,
            ),
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

    if args.command == "code" and args.code_command == "state" and args.code_state_command == "auto":
        st = capture_code_state_from_git(
            ws,
            worktree_path=args.worktree_path,
            repo_id=args.repo_id,
            topic_id=args.topic_id,
            claim_id=args.claim_id,
            session_id=args.session_id,
            build_config=_j(args.build_config_json),
            runtime_environment=_j(args.runtime_environment_json),
            linked_records=_j(args.linked_records_json),
            known_divergence=args.known_divergence,
            write_patch_artifact=args.write_patch_artifact,
        )
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

    if args.command == "tool" and args.tool_command == "run" and args.tool_run_command == "capture-auto":
        rn = capture_tool_run_from_local_path(
            ws,
            path=args.path,
            recipe_id=args.recipe_id,
            tool_family=args.tool_family,
            tool_name=args.tool_name,
            topic_id=args.topic_id,
            claim_id=args.claim_id,
            inputs=_j(args.inputs_json),
            outputs=_j(args.outputs_json),
            environment=_j(args.environment_json),
            evidence_status=args.evidence_status,
            code_state_ids=args.code_state_ids,
            artifact_ids=args.artifact_ids,
            source_refs=args.source_refs,
            summary=args.summary,
            max_preview_chars=args.max_preview_chars,
        )
        return require_valid_public_surface("tool_run_record", tool_run_payload(rn))

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

    if args.command == "curated-rag" and args.curated_rag_command == "ingest":
        return require_valid_public_surface(
            "curated_rag_ingest_result",
            ingest_curated_rag_corpus(
                ws,
                paths=args.paths,
                corpus_id=args.corpus_id,
                tags=args.tags,
                domain_hints=args.domain_hints,
                topic_hints=args.topic_hints,
                language=args.language,
                priority=args.priority,
                chunk_token_limit=args.chunk_token_limit,
                title_prefix=args.title_prefix,
                asset_type=args.asset_type,
                rebuild_index=not args.no_rebuild_index,
            ),
        )

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

    if args.command == "workspace" and args.workspace_command == "inventory":
        workspace_root = args.workspace_root or None
        write_json = _workspace_path_arg(args.write_json, workspace_root)
        write_report = _workspace_path_arg(args.write_report, workspace_root)
        payload = build_workspace_inventory(
            ws,
            workspace_root=workspace_root,
        )
        if write_json:
            write_text_atomic(write_json, json.dumps(_jsonable(payload), ensure_ascii=False, sort_keys=True, indent=2))
            payload = {**payload, "json_path": write_json}
        if write_report:
            payload = {
                **payload,
                "report_path": str(write_workspace_inventory_report(payload, write_report)),
            }
        return payload

    if args.command == "workspace" and args.workspace_command == "migration-plan":
        workspace_root = args.workspace_root or None
        inventory_json = _workspace_path_arg(args.inventory_json, workspace_root)
        write_json = _workspace_path_arg(args.write_json, workspace_root)
        write_report = _workspace_path_arg(args.write_report, workspace_root)
        payload = build_workspace_migration_plan(
            ws,
            workspace_root=workspace_root,
            inventory_path=inventory_json or None,
        )
        if write_json:
            write_text_atomic(write_json, json.dumps(_jsonable(payload), ensure_ascii=False, sort_keys=True, indent=2))
            payload = {**payload, "json_path": write_json}
        if write_report:
            payload = {
                **payload,
                "report_path": str(write_workspace_migration_plan_report(payload, write_report)),
            }
        return payload

    if args.command == "workspace" and args.workspace_command == "old-store-manifest":
        workspace_root = args.workspace_root or None
        write_json = _workspace_path_arg(args.write_json, workspace_root)
        write_report = _workspace_path_arg(args.write_report, workspace_root)
        payload = build_workspace_old_store_manifest(
            ws,
            workspace_root=workspace_root,
        )
        if write_json:
            write_text_atomic(write_json, json.dumps(_jsonable(payload), ensure_ascii=False, sort_keys=True, indent=2))
            payload = {**payload, "json_path": write_json}
        if write_report:
            payload = {
                **payload,
                "report_path": str(write_workspace_old_store_manifest_report(payload, write_report)),
            }
        return payload

    if args.command == "workspace" and args.workspace_command == "file-migration-ledger":
        workspace_root = args.workspace_root or None
        migration_plan_json = _workspace_path_arg(args.migration_plan_json, workspace_root)
        old_store_manifest_json = _workspace_path_arg(args.old_store_manifest_json, workspace_root)
        legacy_accounting_dir = _workspace_path_arg(args.legacy_accounting_dir, workspace_root)
        write_json = _workspace_path_arg(args.write_json, workspace_root)
        write_report = _workspace_path_arg(args.write_report, workspace_root)
        payload = build_workspace_file_migration_ledger(
            ws,
            workspace_root=workspace_root,
            migration_plan_path=migration_plan_json or None,
            old_store_manifest_path=old_store_manifest_json or None,
            legacy_accounting_dir=legacy_accounting_dir or None,
        )
        if write_json or write_report:
            payload = write_workspace_file_migration_ledger(
                payload,
                json_path=write_json or None,
                report_path=write_report or None,
            )
        if args.compact:
            return require_valid_public_surface(
                "workspace_file_migration_ledger_progress",
                compact_workspace_file_migration_ledger(payload),
            )
        return require_valid_public_surface("workspace_file_migration_ledger", payload)

    if args.command == "workspace" and args.workspace_command == "migration-health":
        return require_valid_public_surface(
            "workspace_migration_health",
            build_workspace_migration_health(ws, sample_limit=args.sample_limit),
        )

    if args.command == "workspace" and args.workspace_command == "old-store-import":
        workspace_root = args.workspace_root or None
        old_store_manifest_json = _workspace_path_arg(args.old_store_manifest_json, workspace_root)
        write_json = _workspace_path_arg(args.write_json, workspace_root)
        write_report = _workspace_path_arg(args.write_report, workspace_root)
        payload = build_workspace_old_store_import_plan(
            ws,
            workspace_root=workspace_root,
            old_store_manifest_path=old_store_manifest_json or None,
            topics=args.topics,
        )
        if args.apply:
            payload = apply_workspace_old_store_import_plan(payload)
        if write_json or write_report:
            payload = write_workspace_old_store_import_result(
                payload,
                json_path=write_json or None,
                report_path=write_report or None,
            )
        return require_valid_public_surface("workspace_old_store_import_result", payload)

    if args.command == "workspace" and args.workspace_command == "recovery-binding-repair":
        payload = build_workspace_recovery_binding_repair(
            ws,
            topics=args.topics,
        )
        if args.apply:
            payload = apply_workspace_recovery_binding_repair(payload, ws)
        if args.write_json or args.write_report:
            payload = write_workspace_recovery_binding_repair(
                payload,
                json_path=args.write_json or None,
                report_path=args.write_report or None,
            )
        return require_valid_public_surface("workspace_recovery_binding_repair", payload)

    if args.command == "workspace" and args.workspace_command == "recovery-audit":
        payload = build_workspace_recovery_audit(
            ws,
            migration_plan_path=args.migration_plan_json or None,
            topics=args.topics,
        )
        if args.write_json or args.write_report:
            payload = write_workspace_recovery_audit(
                payload,
                json_path=args.write_json or None,
                report_path=args.write_report or None,
            )
        if args.compact:
            return require_valid_public_surface(
                "workspace_recovery_audit_progress",
                compact_workspace_recovery_audit(payload),
            )
        return require_valid_public_surface("workspace_recovery_audit", payload)

    if args.command == "workspace" and args.workspace_command == "recording-audit":
        payload = build_workspace_recording_audit(
            ws,
            migration_plan_path=args.migration_plan_json or None,
            topics=args.topics,
            limit=args.limit,
        )
        if args.write_json or args.write_report:
            payload = write_workspace_recording_audit(
                payload,
                json_path=args.write_json or None,
                report_path=args.write_report or None,
            )
        return require_valid_public_surface("workspace_recording_audit", payload)

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

    if args.command == "exploration" and args.exploration_command == "record":
        rec = record_exploratory_record(
            ws,
            topic_id=args.topic_id,
            claim_id=args.claim_id,
            session_id=args.session_id,
            exploration_type=args.exploration_type,
            title=args.title,
            focal_question=args.focal_question,
            summary=args.summary,
            original_question=args.original_question,
            local_question=args.local_question,
            status=args.status,
            object_ids=args.object_ids,
            relation_ids=args.relation_ids,
            source_refs=args.source_refs,
            artifact_ids=args.artifact_ids,
            parent_record_ids=args.parent_record_ids,
            derived_record_ids=args.derived_record_ids,
            reasoning_moves=args.reasoning_moves,
            backtrace_targets=args.backtrace_targets,
            candidate_paths=args.candidate_paths,
            relation_path_questions=args.relation_path_questions,
            definition_boundary_questions=args.definition_boundary_questions,
            derivation_backtrace_questions=args.derivation_backtrace_questions,
            source_dependency_questions=args.source_dependency_questions,
            original_question_guard=args.original_question_guard,
            unresolved_points=args.unresolved_points,
            next_actions=args.next_actions,
            human_steering=args.human_steering,
            metadata=_j(args.metadata_json),
        )
        return require_valid_public_surface("exploratory_record", exploratory_record_payload(rec))

    if args.command == "route" and args.route_command == "record":
        route = record_research_route(
            ws,
            topic_id=args.topic_id,
            claim_id=args.claim_id,
            session_id=args.session_id,
            title=args.title,
            route_type=args.route_type,
            status=args.status,
            rationale=args.rationale,
            current_question=args.current_question,
            next_action=args.next_action,
            failure_modes=args.failure_modes,
            source_refs=args.source_refs,
            evidence_refs=args.evidence_refs,
            artifact_ids=args.artifact_ids,
            parent_route_ids=args.parent_route_ids,
            checkpoint_ids=args.checkpoint_ids,
            exploratory_record_ids=args.exploratory_record_ids,
            object_ids=args.object_ids,
            relation_ids=args.relation_ids,
            decision_rationale=args.decision_rationale,
            pivot_reason=args.pivot_reason,
            metadata=_j(args.metadata_json),
        )
        return require_valid_public_surface("research_route_record", research_route_payload(route))

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
