# Compatibility shard 1 for cli.
from __future__ import annotations

import argparse

import json

import sys

from dataclasses import asdict, is_dataclass

from pathlib import Path

from typing import Any

from brain.v5.brief import build_execution_brief

from brain.v5.cli_adapters import add_adapter_parser, dispatch_adapter_command

from brain.v5.cli_authorities import add_authority_parser, dispatch_authority_command

from brain.v5.cli_context import add_context_parser, dispatch_context_command

from brain.v5.cli_domain_packs import add_domain_pack_parser, dispatch_domain_pack_command

from brain.v5.cli_memory import add_memory_parser, dispatch_memory_command

from brain.v5.cli_summaries import add_summary_parser, dispatch_summary_command

from brain.v5.cli_source import add_source_parser, dispatch_source_command

from brain.v5.code import capture_code_state_from_git, record_code_state

from brain.v5.curated_rag_corpus import (
    curated_rag_corpus,
    draft_curated_rag_promotion,
    ingest_curated_rag_corpus,
    read_curated_rag_chunk,
    search_curated_rag_corpus,
)

from brain.v5.evidence import record_evidence

from brain.v5.knowledge_connectors import describe_knowledge_connectors

from brain.v5.knowledge_connector_bindings import bind_knowledge_connector, list_knowledge_connector_bindings

from brain.v5.cli_legacy import add_legacy_parser, dispatch_legacy_command

from brain.v5.cli_interaction import add_interaction_parser, dispatch_interaction_command

from brain.v5.cli_literature import add_literature_parser, dispatch_literature_command

from brain.v5.models import TrustUpdateRequest

from brain.v5.cli_policy import add_policy_parser, dispatch_policy_command

from brain.v5.cli_query import add_query_parser, dispatch_query_command

from brain.v5.cli_record_lifecycle import (
    cmd_record_audit_routing,
    cmd_record_lifecycle,
    cmd_record_rehome,
    cmd_record_supersede,
)

from brain.v5.cli_research_state import add_research_state_parser, dispatch_research_state_command

from brain.v5.cli_validation import add_validation_parser, dispatch_validation_command

from brain.v5.cli_vnext import VNEXT_COMMANDS, add_vnext_parsers, dispatch_vnext_command

from brain.v5.cli_goal import add_goal_parser, dispatch_goal_command

from brain.v5.cli_harness_feedback import add_harness_feedback_parser, dispatch_harness_feedback_command

from brain.v5.claim_relation_map import build_claim_relation_map

from brain.v5.exploration import exploratory_record_payload, record_exploratory_record

from brain.v5.process_graph import build_process_graph_slice

from brain.v5.public_surfaces import require_valid_public_surface

from brain.v5.quiet_checkpoint import apply_quiet_checkpoint_batch, preview_quiet_checkpoint_batch

from brain.v5.research_timeline import build_research_timeline

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

from brain.v5.source_assets import (
    acquire_arxiv_source_asset,
    acquire_pdf_source_asset,
    capture_source_asset_from_local_path,
    register_source_asset,
    source_asset_payload,
)

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
    _add_parser_section_01(sp)
    _add_parser_section_02(sp)
    _add_parser_section_03(sp)
    _add_parser_section_04(sp)
    return parser

def _add_parser_section_01(sp):
    sp.add_parser("init").add_argument("base")
    wp = sp.add_parser("workspace")
    wps = wp.add_subparsers(dest="workspace_command", required=True)
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
    tp = sp.add_parser("topic")
    ts = tp.add_subparsers(dest="topic_command", required=True)
    tc = ts.add_parser("create")
    tc.add_argument("topic_id")
    tc.add_argument("--context", required=True, dest="context_id")
    tc.add_argument("--title", required=True)
    cl_p = sp.add_parser("claim")
    cl_s = cl_p.add_subparsers(dest="claim_command", required=True)
    cc = cl_s.add_parser("create")
    cc.add_argument("--topic", required=True, dest="topic_id")
    cc.add_argument("--statement", required=True)
    cc.add_argument("--evidence-profile", required=True)
    cc.add_argument("--confidence-state", default="hypothesis")
    cc.add_argument("--uncertainty", required=True)
    cc.add_argument("--recipe-id", default="")
    se_p = sp.add_parser("session")
    se_s = se_p.add_subparsers(dest="session_command", required=True)
    sb = se_s.add_parser("bind")
    sb.add_argument("session_id")
    sb.add_argument("--topic", required=True, dest="topic_id")
    sb.add_argument("--context", required=True, dest="context_id")
    sb.add_argument("--claim", default="", dest="active_claim")
    sb.add_argument("--interaction-profile", default="collaborator")
    sb.add_argument("--interaction-steering", default="")
    sp.add_parser("brief").add_argument("session_id")
    sp.add_parser("relation-map").add_argument("session_id")
    timeline_p = sp.add_parser("timeline")
    timeline_p.add_argument("session_id")
    timeline_p.add_argument("--claim", default="", dest="claim_id")
    timeline_p.add_argument("--limit", type=int, default=80)
    ap = sp.add_parser("asset")
    aps = ap.add_subparsers(dest="asset_command", required=True)
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
    aa.add_argument("--copy-to-store", action="store_true")
    aa.add_argument("--force-refresh", action="store_true")
    apdf = aps.add_parser("acquire-pdf")
    apdf.add_argument("--topic", required=True, dest="topic_id")
    apdf.add_argument("--url", required=True)
    apdf.add_argument("--title", required=True)
    apdf.add_argument("--claim", default="", dest="claim_id")
    apdf.add_argument("--type", default="paper", dest="asset_type")
    apdf.add_argument("--label", default="")
    apdf.add_argument("--timeout", type=int, default=120, dest="timeout_seconds")
    apdf.add_argument("--max-bytes", type=int, default=200 * 1024 * 1024, dest="max_bytes")
    apdf.add_argument("--force-refresh", action="store_true")
    apdf.add_argument("--version-anchor-json", default="{}")
    apdf.add_argument("--acquired-at", default="")
    apdf.add_argument("--source-kind", default="literature_pdf")
    apdf.add_argument("--summary", default="")
    apdf.add_argument("--source-ref", action="append", default=[], dest="source_refs")
    apdf.add_argument("--artifact-id", action="append", default=[], dest="artifact_ids")
    apdf.add_argument("--code-state-id", action="append", default=[], dest="code_state_ids")
    apdf.add_argument("--reference-location-id", action="append", default=[], dest="reference_location_ids")
    apdf.add_argument("--derived-from", action="append", default=[], dest="derived_from")
    apdf.add_argument("--metadata-json", default="{}")
    apdf.add_argument("--linked-records-json", default="{}")
    aarxiv = aps.add_parser("acquire-arxiv")
    aarxiv.add_argument("--topic", required=True, dest="topic_id")
    aarxiv.add_argument("--arxiv-id", required=True)
    aarxiv.add_argument("--title", default="")
    aarxiv.add_argument("--claim", default="", dest="claim_id")
    aarxiv.add_argument("--version", default="")
    aarxiv.add_argument("--label", default="")
    aarxiv.add_argument("--timeout", type=int, default=120, dest="timeout_seconds")
    aarxiv.add_argument("--max-bytes", type=int, default=200 * 1024 * 1024, dest="max_bytes")
    aarxiv.add_argument("--force-refresh", action="store_true")
    aarxiv.add_argument("--version-anchor-json", default="{}")
    aarxiv.add_argument("--source-kind", default="arxiv_pdf")
    aarxiv.add_argument("--summary", default="")
    aarxiv.add_argument("--source-ref", action="append", default=[], dest="source_refs")
    aarxiv.add_argument("--artifact-id", action="append", default=[], dest="artifact_ids")
    aarxiv.add_argument("--code-state-id", action="append", default=[], dest="code_state_ids")
    aarxiv.add_argument("--reference-location-id", action="append", default=[], dest="reference_location_ids")
    aarxiv.add_argument("--derived-from", action="append", default=[], dest="derived_from")
    aarxiv.add_argument("--metadata-json", default="{}")
    aarxiv.add_argument("--linked-records-json", default="{}")
