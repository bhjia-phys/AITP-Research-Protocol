"""QSGW/LibRPA lightweight research-cockpit surfaces.

The cockpit is a topic-local orientation surface. It summarizes final vs
diagnostic lane boundaries, report/script artifacts, and typed-record coverage
without creating evidence or changing claim trust.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from brain.v5.lane_exemplars import load_lane_exemplars
from brain.v5.models import (
    EvidenceRecord,
    ReferenceLocationRecord,
    SensemakingReportRecord,
    ToolRunRecord,
    ValidationContractRecord,
)
from brain.v5.operator_checkpoint import load_operator_checkpoint
from brain.v5.output_stability import load_final_output_profile
from brain.v5.paths import WorkspacePaths
from brain.v5.store import read_record

DEFAULT_QSGW_TOPIC_ID = "qsgw-headwing-update-librpa"
_MANIFEST_VERSION = "qsgw-research-cockpit-v1"
_DEFAULT_REPORTS_REL = Path("research") / "librpa" / "reports"
_DEFAULT_SCRIPTS_REL = Path("research") / "librpa" / "scripts"
_ARTIFACT_SUFFIXES = {".csv", ".json", ".md", ".pdf", ".png", ".svg", ".tsv", ".txt"}
_SCRIPT_SUFFIXES = {".ipynb", ".md", ".ps1", ".py", ".sh"}
_LANE_MANIFEST_GLOB = "*lane_manifest_current.json"
_AITP_INTAKE_GLOB = "*aitp_intake_current.jsonl"
_REMOTE_ROOT_RE = re.compile(r"/data/home/[^\s,'\")\]]+")

_FORBIDDEN_ROOTS = [
    {
        "root": "/data/home/df_iopcas_bhj/ai-runs/mgo-qsgw-k999-headonly-kconv-20260523-1135",
        "status": "forbidden",
        "reason": "known contaminated MgO root; must never feed final or diagnostic updates except as a negative provenance example",
    }
]
_PREFERRED_ROOTS = [
    {
        "root": "/data/home/df_iopcas_bhj/ai-runs/mgo-qsgw-k999-headonly-kconv-20260523-1210-nohardlink",
        "status": "preferred_clean_root",
        "reason": "clean MgO head-only root with no-hardlink provenance",
    }
]


def write_qsgw_cockpit_surfaces(
    ws: WorkspacePaths,
    *,
    topic_id: str = DEFAULT_QSGW_TOPIC_ID,
    reports_dir: str | Path | None = None,
    scripts_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Write topic-local cockpit files and return the contracted bundle."""

    manifest = build_qsgw_cockpit_manifest(
        ws,
        topic_id=topic_id,
        reports_dir=reports_dir,
        scripts_dir=scripts_dir,
    )
    runtime_dir = ws.topic_dir(topic_id) / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "manifest": str(runtime_dir / "qsgw_cockpit_manifest.json"),
        "dashboard_dry_run": str(runtime_dir / "qsgw_cockpit_dashboard.md"),
        "plot_guard": str(runtime_dir / "qsgw_plot_guard.generated.md"),
    }
    _write_json(Path(files["manifest"]), manifest)
    Path(files["dashboard_dry_run"]).write_text(_render_dashboard(manifest), encoding="utf-8")
    Path(files["plot_guard"]).write_text(_render_plot_guard(manifest), encoding="utf-8")
    return {
        "kind": "qsgw_cockpit_bundle",
        "topic_id": topic_id,
        "files": files,
        "manifest": manifest,
        "source_records": _source_records(manifest),
        "derived_from": "typed_records_and_report_artifact_scan",
        "truth_source": False,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def build_qsgw_cockpit_manifest(
    ws: WorkspacePaths,
    *,
    topic_id: str = DEFAULT_QSGW_TOPIC_ID,
    reports_dir: str | Path | None = None,
    scripts_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Build a conservative QSGW/LibRPA lane manifest from local files."""

    reports_root = _resolve_workspace_path(ws, reports_dir, default=_DEFAULT_REPORTS_REL)
    scripts_root = _resolve_workspace_path(ws, scripts_dir, default=_DEFAULT_SCRIPTS_REL)
    current_records = _current_record_summary(ws, topic_id)
    observed_roots = sorted(
        set(current_records["observed_remote_roots"])
        | set(_scan_text_roots(reports_root, suffixes={".json", ".md", ".txt", ".tsv"}, limit=60))
    )
    report_artifacts = _scan_artifacts(reports_root, suffixes=_ARTIFACT_SUFFIXES, limit=80)
    script_artifacts = _scan_artifacts(scripts_root, suffixes=_SCRIPT_SUFFIXES, limit=80)
    downstream_intake = _downstream_intake(reports_root)
    lane_manifest = _lane_manifest(ws, topic_id, current_records, observed_roots)
    plot_guard = _plot_guard()
    refresh_intake = _refresh_intake(downstream_intake)
    next_actions = _next_actions(lane_manifest, report_artifacts, script_artifacts, downstream_intake)
    return {
        "kind": "qsgw_cockpit_manifest",
        "manifest_version": _MANIFEST_VERSION,
        "topic_id": topic_id,
        "lane_manifest": lane_manifest,
        "current_records": current_records,
        "report_artifacts": report_artifacts,
        "script_artifacts": script_artifacts,
        "downstream_intake": downstream_intake,
        "plot_guard": plot_guard,
        "refresh_intake": refresh_intake,
        "typed_record_templates": _typed_record_templates(topic_id),
        "dashboard": _dashboard_summary(current_records, report_artifacts, script_artifacts, downstream_intake),
        "next_actions": next_actions,
        "trust_update_forbidden": True,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def compact_qsgw_cockpit_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a small host-friendly cockpit projection."""

    manifest = payload.get("manifest") if isinstance(payload.get("manifest"), dict) else {}
    records = manifest.get("current_records") if isinstance(manifest.get("current_records"), dict) else {}
    evidence_counts = records.get("evidence_counts_by_lane") if isinstance(records.get("evidence_counts_by_lane"), dict) else {}
    lane_manifest = manifest.get("lane_manifest") if isinstance(manifest.get("lane_manifest"), dict) else {}
    plot_guard = manifest.get("plot_guard") if isinstance(manifest.get("plot_guard"), dict) else {}
    downstream_intake = manifest.get("downstream_intake") if isinstance(manifest.get("downstream_intake"), dict) else {}
    return {
        "kind": "qsgw_cockpit_bundle_progress",
        "source_surface": "qsgw_cockpit_bundle",
        "topic_id": str(payload.get("topic_id") or manifest.get("topic_id") or ""),
        "files": dict(payload.get("files") or {}),
        "lane_status": str(lane_manifest.get("status") or ""),
        "final_evidence_candidates": int(evidence_counts.get("final", 0) or 0),
        "diagnostic_evidence_candidates": int(evidence_counts.get("diagnostic", 0) or 0),
        "unclassified_evidence_candidates": int(evidence_counts.get("unclassified", 0) or 0),
        "forbidden_roots": [item["root"] for item in lane_manifest.get("forbidden_roots", []) if isinstance(item, dict) and item.get("root")],
        "final_plot_guard_required": bool(plot_guard.get("final_lane", {}).get("requires_explicit_allowlist", False)),
        "diagnostic_label_required": bool(plot_guard.get("diagnostic_lane", {}).get("requires_explicit_profile", False)),
        "downstream_lane_manifests": int(downstream_intake.get("lane_manifest_count", 0) or 0),
        "downstream_intake_jsonl": int(downstream_intake.get("intake_jsonl_count", 0) or 0),
        "downstream_intake_records": int(downstream_intake.get("intake_record_count", 0) or 0),
        "downstream_intake_all_guarded": bool(downstream_intake.get("all_intake_rows_guarded", False)),
        "downstream_result_intake_candidates": bool(downstream_intake.get("has_result_intake_candidates", False)),
        "next_actions": [item.get("action", "") for item in manifest.get("next_actions", []) if isinstance(item, dict)],
        "trust_update_forbidden": True,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _current_record_summary(ws: WorkspacePaths, topic_id: str) -> dict[str, Any]:
    evidence, evidence_errors = _safe_records(ws, "evidence", EvidenceRecord)
    tool_runs, tool_errors = _safe_records(ws, "tool_runs", ToolRunRecord)
    references, reference_errors = _safe_records(ws, "reference_locations", ReferenceLocationRecord)
    validation_contracts, validation_errors = _safe_records(ws, "validation_contracts", ValidationContractRecord)
    sensemaking_reports, sensemaking_errors = _safe_records(ws, "sensemaking_reports", SensemakingReportRecord)

    topic_evidence = [record for record in evidence if record.topic_id == topic_id]
    topic_tool_runs = [record for record in tool_runs if record.topic_id == topic_id]
    topic_references = [record for record in references if record.topic_id == topic_id]
    topic_validation = [record for record in validation_contracts if record.topic_id == topic_id]
    topic_sensemaking = [record for record in sensemaking_reports if record.topic_id == topic_id]

    evidence_items = [_evidence_item(record) for record in topic_evidence]
    evidence_counts = {"final": 0, "diagnostic": 0, "unclassified": 0}
    for item in evidence_items:
        evidence_counts[item["lane"]] += 1

    all_payloads = (
        [_record_payload(record) for record in topic_evidence]
        + [_record_payload(record) for record in topic_tool_runs]
        + [_record_payload(record) for record in topic_references]
        + [_record_payload(record) for record in topic_validation]
        + [_record_payload(record) for record in topic_sensemaking]
    )
    return {
        "final_output_profile": load_final_output_profile(ws, topic_id),
        "lane_exemplars": load_lane_exemplars(ws, topic_id),
        "operator_checkpoint": load_operator_checkpoint(ws, topic_id),
        "evidence_counts_by_lane": evidence_counts,
        "evidence_items": _limited(evidence_items, limit=20),
        "tool_run_count": len(topic_tool_runs),
        "tool_runs": _limited([_tool_run_item(record) for record in topic_tool_runs], limit=12),
        "reference_location_count": len(topic_references),
        "reference_locations": _limited([_reference_item(record) for record in topic_references], limit=12),
        "validation_contract_count": len(topic_validation),
        "validation_contracts": _limited([_validation_item(record) for record in topic_validation], limit=12),
        "sensemaking_report_count": len(topic_sensemaking),
        "sensemaking_reports": _limited([_sensemaking_item(record) for record in topic_sensemaking], limit=12),
        "observed_remote_roots": sorted(_roots_from_payloads(all_payloads)),
        "read_errors": evidence_errors + tool_errors + reference_errors + validation_errors + sensemaking_errors,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }


def _lane_manifest(
    ws: WorkspacePaths,
    topic_id: str,
    current_records: dict[str, Any],
    observed_roots: list[str],
) -> dict[str, Any]:
    topic_present = (ws.topic_dir(topic_id) / "topic.md").exists()
    profile = current_records.get("final_output_profile") or {}
    evidence_counts = current_records.get("evidence_counts_by_lane") or {}
    if profile.get("present") or any(evidence_counts.values()):
        status = "ready_for_cockpit_dry_run"
    elif topic_present:
        status = "needs_lane_records"
    else:
        status = "topic_missing"
    return {
        "status": status,
        "topic_present": topic_present,
        "final_lane": {
            "purpose": "paper/final comparison only",
            "requires": [
                "usable_for_final=True provenance",
                "finished=True for G0W0 baselines",
                "physically reasonable non-negative gap rows",
                "clean or explicitly accepted remote root",
                "explicit claim scope and validation contract before trust changes",
            ],
            "forbids": [
                "nonconverged rows as final conclusions",
                "negative-gap or noiter rows as final conclusions",
                "iter20 human assumptions unless separately validated",
                "diagnostic plots overwriting final-only outputs",
            ],
        },
        "diagnostic_lane": {
            "purpose": "trend finding, group-meeting diagnostics, and failure-mode localization",
            "allowed_when_labeled": [
                "iter20 assumptions",
                "nonconverged-but-flat trends",
                "gap-history and band diagnostics",
                "nonfinal roots used only to explain failure modes",
            ],
            "forbids": [
                "claim confidence promotion",
                "final comparison table updates",
                "silent reuse by final plotting scripts",
            ],
        },
        "forbidden_roots": list(_FORBIDDEN_ROOTS),
        "preferred_roots": list(_PREFERRED_ROOTS),
        "observed_remote_roots": observed_roots,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }


def _plot_guard() -> dict[str, Any]:
    return {
        "final_lane": {
            "requires_explicit_allowlist": True,
            "required_row_fields": [
                "lane=final",
                "usable_for_final=True",
                "finished=True when method=G0W0",
                "physical_valid=True",
                "contamination_status=clean",
            ],
            "forbidden_markers": [
                "diagnostic",
                "human_assumption",
                "iter20_assumption",
                "nonconverged",
                "negative_gap",
                "noiter",
                "contaminated_root",
            ],
            "overwrite_policy": "must not overwrite strict final-only plots unless the input manifest hash changes and final guards pass",
        },
        "diagnostic_lane": {
            "requires_explicit_profile": True,
            "required_output_label": "diagnostic",
            "allowed_markers": ["human_assumption", "iter20_assumption", "nonconverged_but_flat", "gap_history", "band_diagnostic"],
            "overwrite_policy": "must write to diagnostic-named outputs and leave final-only artifacts untouched",
        },
        "trust_boundary": "plot guards route artifacts; they do not validate claims or update trust",
    }


def _refresh_intake(downstream_intake: dict[str, Any] | None = None) -> dict[str, Any]:
    downstream_intake = downstream_intake or {}
    return {
        "recommended_outputs": [
            "research/librpa/reports/qsgw_status_manifest.json",
            "research/librpa/reports/aitp_intake.jsonl",
        ],
        "observed_outputs": {
            "lane_manifests": downstream_intake.get("lane_manifests", []),
            "intake_jsonl": downstream_intake.get("intake_jsonl", []),
            "intake_record_count": downstream_intake.get("intake_record_count", 0),
            "all_intake_rows_guarded": downstream_intake.get("all_intake_rows_guarded", False),
        },
        "jsonl_record_kinds": [
            "qsgw_kpoint_status_candidate",
            "tool_run_candidate",
            "final_evidence_candidate",
            "diagnostic_evidence_candidate",
        ],
        "rules": [
            "refresh scripts may emit AITP-ready candidates, not trust updates",
            "every final candidate must carry usable_for_final and clean-root provenance",
            "diagnostic candidates must name the assumption or failure mode they illustrate",
            "manual or policy preflight remains required before any claim confidence change",
        ],
    }


def _typed_record_templates(topic_id: str) -> dict[str, Any]:
    return {
        "final_evidence": {
            "entrypoint": "aitp-v5 evidence record",
            "topic_id": topic_id,
            "required_fields": ["claim_id", "evidence_type", "status", "summary", "supports_outputs", "source_refs"],
            "lane_rules": ["status should be supports/mixed only after scoped validation", "must cite final-usable manifest or TSV hash"],
        },
        "diagnostic_evidence": {
            "entrypoint": "aitp-v5 evidence record",
            "topic_id": topic_id,
            "required_fields": ["claim_id", "evidence_type", "status", "summary", "supports_outputs", "source_refs"],
            "lane_rules": ["status is usually mixed or inconclusive", "summary must name diagnostic scope and non-claim boundary"],
        },
        "tool_run": {
            "entrypoint": "aitp-v5 tool run record",
            "topic_id": topic_id,
            "required_fields": ["recipe_id", "tool_family", "tool_name", "claim_id", "inputs", "outputs"],
            "lane_rules": ["record refresh/plot provenance and input hashes; do not imply evidence validity by itself"],
        },
        "reference_location": {
            "entrypoint": "aitp-v5 reference location record",
            "topic_id": topic_id,
            "required_fields": ["connector_id", "location_type", "uri", "label"],
            "lane_rules": ["orientation-only; never changes confidence"],
        },
        "validation_contract": {
            "entrypoint": "aitp-v5 validation contract create",
            "topic_id": topic_id,
            "required_fields": ["claim_id", "required_checks", "failure_modes", "required_evidence_outputs"],
            "lane_rules": ["required before rigorous/adversarial trust-relevant tool execution"],
        },
        "sensemaking_report": {
            "entrypoint": "aitp-v5 sensemaking report",
            "topic_id": topic_id,
            "required_fields": ["claim_id", "title", "summary", "open_questions", "next_actions"],
            "lane_rules": ["capture prior-art or scope changes without treating them as validation"],
        },
    }


def _dashboard_summary(
    current_records: dict[str, Any],
    report_artifacts: dict[str, Any],
    script_artifacts: dict[str, Any],
    downstream_intake: dict[str, Any],
) -> dict[str, Any]:
    evidence_counts = current_records.get("evidence_counts_by_lane") or {}
    report_counts = report_artifacts.get("counts_by_lane") or {}
    script_roles = script_artifacts.get("counts_by_role") or {}
    return {
        "final_lane_status": "has_candidates_needs_guarded_review" if evidence_counts.get("final") else "guard_configured_no_final_candidate",
        "diagnostic_lane_status": "has_diagnostic_candidates" if evidence_counts.get("diagnostic") else "diagnostic_guard_configured",
        "record_counts": {
            "evidence_final": evidence_counts.get("final", 0),
            "evidence_diagnostic": evidence_counts.get("diagnostic", 0),
            "evidence_unclassified": evidence_counts.get("unclassified", 0),
            "tool_runs": current_records.get("tool_run_count", 0),
            "references": current_records.get("reference_location_count", 0),
            "validation_contracts": current_records.get("validation_contract_count", 0),
            "sensemaking_reports": current_records.get("sensemaking_report_count", 0),
        },
        "artifact_counts": {
            "reports_final_named": report_counts.get("final", 0),
            "reports_diagnostic_named": report_counts.get("diagnostic", 0),
            "reports_unclassified": report_counts.get("unclassified", 0),
            "refresh_scripts": script_roles.get("refresh", 0),
            "plot_scripts": script_roles.get("plot", 0),
            "downstream_lane_manifests": downstream_intake.get("lane_manifest_count", 0),
            "downstream_intake_jsonl": downstream_intake.get("intake_jsonl_count", 0),
            "downstream_intake_records": downstream_intake.get("intake_record_count", 0),
        },
        "blocking_notes": [
            "legacy semantic review backlog remains a separate blocking backlog",
            "cockpit artifacts are orientation-only and cannot update claim trust",
        ],
    }


def _next_actions(
    lane_manifest: dict[str, Any],
    report_artifacts: dict[str, Any],
    script_artifacts: dict[str, Any],
    downstream_intake: dict[str, Any],
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    if not downstream_intake.get("lane_manifest_count"):
        actions.append(
            {
                "action": "materialize_final_diagnostic_lane_manifest",
                "why": "future agents need a local allowlist boundary before reading reports as final or diagnostic",
            }
        )
    actions.append(
        {
            "action": "add_plot_guard_to_final_scripts",
            "why": "final plots should fail closed unless inputs are final-usable and clean",
        }
    )
    if not downstream_intake.get("intake_jsonl_count"):
        actions.append(
            {
                "action": "emit_refresh_aitp_intake_jsonl",
                "why": "monitoring should produce reviewable candidates without manual bookkeeping",
            }
        )
    elif not downstream_intake.get("has_result_intake_candidates"):
        actions.append(
            {
                "action": "extend_refresh_monitor_to_emit_result_intake_jsonl",
                "why": "audit intake exists, but completed/diagnostic result rows still need the same guarded JSONL shape",
            }
        )
    actions.append(
        {
            "action": "review_dashboard_dry_run_before_claim_updates",
            "why": "dashboard can guide work, but trust updates still require preflight and human checkpoints",
        }
    )
    if lane_manifest.get("status") == "topic_missing":
        actions.insert(0, {"action": "bind_or_create_qsgw_topic", "why": "cockpit is most useful once the topic exists"})
    if not report_artifacts.get("present"):
        actions.append({"action": "point_reports_dir_at_research_librpa_reports", "why": "no report artifacts were found"})
    if not script_artifacts.get("present"):
        actions.append({"action": "point_scripts_dir_at_research_librpa_scripts", "why": "no refresh or plot scripts were found"})
    return actions


def _downstream_intake(reports_root: Path) -> dict[str, Any]:
    lane_manifests = _scan_lane_manifests(reports_root)
    intake_files = _scan_intake_jsonl(reports_root)
    intake_record_count = sum(int(item.get("record_count", 0) or 0) for item in intake_files)
    all_guarded = bool(intake_files) and all(bool(item.get("all_rows_guarded", False)) for item in intake_files)
    return {
        "root": str(reports_root),
        "present": reports_root.exists(),
        "lane_manifest_count": len(lane_manifests),
        "intake_jsonl_count": len(intake_files),
        "intake_record_count": intake_record_count,
        "all_intake_rows_guarded": all_guarded,
        "has_result_intake_candidates": any(bool(item.get("has_result_candidates", False)) for item in intake_files),
        "lane_manifests": lane_manifests,
        "intake_jsonl": intake_files,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }


def _scan_lane_manifests(reports_root: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if not reports_root.exists():
        return items
    for path in sorted(reports_root.glob(_LANE_MANIFEST_GLOB), key=lambda p: p.name.lower()):
        payload, error = _read_json(path)
        item: dict[str, Any] = {
            "path": str(path),
            "relative_path": path.name,
            "readable": error is None,
            "error": error,
            "trust_update_forbidden": True,
            "claim_confidence_update_allowed": False,
        }
        if isinstance(payload, dict):
            counts = payload.get("counts") if isinstance(payload.get("counts"), dict) else {}
            final_allowlist = payload.get("final_allowlist") if isinstance(payload.get("final_allowlist"), list) else []
            diagnostic_candidates = (
                payload.get("diagnostic_candidates") if isinstance(payload.get("diagnostic_candidates"), list) else []
            )
            item.update(
                {
                    "kind": payload.get("kind", ""),
                    "topic_id": payload.get("topic_id", ""),
                    "counts": counts,
                    "final_allowlist_count": len(final_allowlist),
                    "diagnostic_candidate_count": len(diagnostic_candidates),
                    "trust_update_forbidden": bool(payload.get("trust_update_forbidden", True)),
                    "claim_confidence_update_allowed": bool(payload.get("claim_confidence_update_allowed", False)),
                }
            )
        items.append(item)
    return items


def _scan_intake_jsonl(reports_root: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if not reports_root.exists():
        return items
    for path in sorted(reports_root.glob(_AITP_INTAKE_GLOB), key=lambda p: p.name.lower()):
        records, errors = _read_jsonl(path)
        record_kinds = sorted({str(record.get("record_kind") or "") for record in records if isinstance(record, dict)})
        all_guarded = bool(records) and all(_intake_record_is_guarded(record) for record in records)
        items.append(
            {
                "path": str(path),
                "relative_path": path.name,
                "record_count": len(records),
                "record_kinds": record_kinds,
                "read_errors": errors,
                "all_rows_guarded": all_guarded,
                "has_final_usable_rows": any(bool(record.get("usable_for_final", False)) for record in records),
                "has_result_candidates": any(_is_result_candidate(record) for record in records),
                "summary_inputs_trusted": False,
                "can_update_claim_trust": False,
            }
        )
    return items


def _intake_record_is_guarded(record: dict[str, Any]) -> bool:
    plot_guard = record.get("plot_guard") if isinstance(record.get("plot_guard"), dict) else {}
    return (
        bool(record.get("trust_update_forbidden", False))
        and not bool(record.get("usable_for_final", False))
        and not bool(plot_guard.get("allowed_in_final_plot", False))
    )


def _is_result_candidate(record: dict[str, Any]) -> bool:
    kind = str(record.get("record_kind") or "")
    if kind in {"qsgw_kpoint_status_candidate", "final_evidence_candidate", "diagnostic_evidence_candidate"}:
        return True
    raw = record.get("raw_row") if isinstance(record.get("raw_row"), dict) else {}
    keys = set(str(key).lower() for key in raw)
    return bool({"gap_ev", "finished", "converged", "usable_for_final"} & keys)


def _read_json(path: Path) -> tuple[Any, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, json.JSONDecodeError) as exc:
        return None, str(exc)


def _read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return records, [str(exc)]
    for index, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {index}: {exc}")
            continue
        if isinstance(payload, dict):
            records.append(payload)
        else:
            errors.append(f"line {index}: expected object")
    return records, errors


def _scan_artifacts(root: Path, *, suffixes: set[str], limit: int) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    if root.exists():
        for path in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: str(p).lower()):
            if path.suffix.lower() not in suffixes:
                continue
            item = _artifact_item(root, path)
            items.append(item)
            if len(items) >= limit:
                break
    return {
        "root": str(root),
        "present": root.exists(),
        "item_count": len(items),
        "items": items,
        "counts_by_lane": _counts(items, "lane"),
        "counts_by_role": _counts(items, "role"),
        "summary_inputs_trusted": False,
    }


def _artifact_item(root: Path, path: Path) -> dict[str, Any]:
    rel = str(path.relative_to(root)).replace("\\", "/")
    name = path.name.lower()
    lane = _classify_lane([rel, name])
    role = "refresh" if "refresh" in name or "status" in name or "monitor" in name else "plot" if "plot" in name or "figure" in name or "fig" in name else "report"
    return {
        "path": str(path),
        "relative_path": rel,
        "suffix": path.suffix.lower(),
        "lane": lane,
        "role": role,
        "size_bytes": path.stat().st_size,
    }


def _scan_text_roots(root: Path, *, suffixes: set[str], limit: int) -> list[str]:
    roots: set[str] = set()
    if not root.exists():
        return []
    scanned = 0
    for path in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: str(p).lower()):
        if path.suffix.lower() not in suffixes:
            continue
        scanned += 1
        if scanned > limit:
            break
        try:
            roots.update(_REMOTE_ROOT_RE.findall(path.read_text(encoding="utf-8", errors="ignore")))
        except OSError:
            continue
    return sorted(roots)


def _evidence_item(record: EvidenceRecord) -> dict[str, Any]:
    lane = _classify_lane([record.evidence_type, record.status, record.summary, *record.supports_outputs, *record.source_refs])
    return {
        "evidence_id": record.evidence_id,
        "claim_id": record.claim_id,
        "evidence_type": record.evidence_type,
        "status": record.status,
        "lane": lane,
        "supports_outputs": list(record.supports_outputs),
        "source_refs": list(record.source_refs),
        "summary_excerpt": _excerpt(record.summary),
    }


def _tool_run_item(record: ToolRunRecord) -> dict[str, Any]:
    lane = _classify_lane([record.recipe_id, record.tool_name, record.evidence_status, json.dumps(record.outputs, sort_keys=True)])
    return {
        "run_id": record.run_id,
        "recipe_id": record.recipe_id,
        "tool_name": record.tool_name,
        "claim_id": record.claim_id,
        "evidence_status": record.evidence_status,
        "lane": lane,
    }


def _reference_item(record: ReferenceLocationRecord) -> dict[str, Any]:
    return {
        "location_id": record.location_id,
        "claim_id": record.claim_id,
        "location_type": record.location_type,
        "uri": record.uri,
        "label": record.label,
        "orientation_only": True,
    }


def _validation_item(record: ValidationContractRecord) -> dict[str, Any]:
    return {
        "contract_id": record.contract_id,
        "claim_id": record.claim_id,
        "status": record.status,
        "required_evidence_outputs": list(record.required_evidence_outputs),
        "failure_modes": list(record.failure_modes),
    }


def _sensemaking_item(record: SensemakingReportRecord) -> dict[str, Any]:
    return {
        "report_id": record.report_id,
        "claim_id": record.claim_id,
        "title": record.title,
        "validation_status": record.validation_status,
        "summary_excerpt": _excerpt(record.summary),
    }


def _classify_lane(values: list[str]) -> str:
    text = " ".join(str(value).lower() for value in values if value)
    diagnostic_markers = (
        "diagnostic",
        "nonfinal",
        "non-final",
        "iter20",
        "human_assumption",
        "human-assumption",
        "assumption",
        "nonconverged",
        "noiter",
        "negative-gap",
        "negative_gap",
        "gap-history",
        "trend",
        "pilot",
    )
    final_markers = (
        "usable_for_final",
        "final-usable",
        "final_usable",
        "final_lane",
        "final-only",
        "final_only",
        "paper_claim",
        "paper-claim",
        "final_comparison",
        "final-comparison",
    )
    if any(marker in text for marker in diagnostic_markers):
        return "diagnostic"
    if any(marker in text for marker in final_markers):
        return "final"
    return "unclassified"


def _source_records(manifest: dict[str, Any]) -> dict[str, list[str]]:
    records = manifest.get("current_records") if isinstance(manifest.get("current_records"), dict) else {}
    evidence = records.get("evidence_items") if isinstance(records.get("evidence_items"), list) else []
    tool_runs = records.get("tool_runs") if isinstance(records.get("tool_runs"), list) else []
    refs = records.get("reference_locations") if isinstance(records.get("reference_locations"), list) else []
    validations = records.get("validation_contracts") if isinstance(records.get("validation_contracts"), list) else []
    sensemaking = records.get("sensemaking_reports") if isinstance(records.get("sensemaking_reports"), list) else []
    return {
        "topics": [str(manifest.get("topic_id") or "")],
        "evidence": [str(item.get("evidence_id")) for item in evidence if isinstance(item, dict) and item.get("evidence_id")],
        "tool_runs": [str(item.get("run_id")) for item in tool_runs if isinstance(item, dict) and item.get("run_id")],
        "reference_locations": [str(item.get("location_id")) for item in refs if isinstance(item, dict) and item.get("location_id")],
        "validation_contracts": [str(item.get("contract_id")) for item in validations if isinstance(item, dict) and item.get("contract_id")],
        "sensemaking_reports": [str(item.get("report_id")) for item in sensemaking if isinstance(item, dict) and item.get("report_id")],
    }


def _safe_records(ws: WorkspacePaths, family: str, cls: type) -> tuple[list[Any], list[dict[str, str]]]:
    records: list[Any] = []
    errors: list[dict[str, str]] = []
    root = ws.registry_dir(family)
    if not root.exists():
        return records, errors
    for path in sorted(root.glob("*.md")):
        try:
            records.append(read_record(path, cls))
        except Exception as exc:  # pragma: no cover - defensive against dirty research workspaces
            errors.append({"path": str(path), "error": str(exc)})
    return records, errors


def _record_payload(record: Any) -> dict[str, Any]:
    if is_dataclass(record):
        return asdict(record)
    return dict(record)


def _roots_from_payloads(payloads: list[dict[str, Any]]) -> set[str]:
    roots: set[str] = set()
    for payload in payloads:
        roots.update(_REMOTE_ROOT_RE.findall(json.dumps(payload, ensure_ascii=False, sort_keys=True)))
    return roots


def _resolve_workspace_path(ws: WorkspacePaths, value: str | Path | None, *, default: Path) -> Path:
    if value is None or str(value) == "":
        return ws.base / default
    path = Path(value)
    if path.is_absolute():
        return path
    return ws.base / path


def _counts(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key) or "unclassified")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _limited(items: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    return items[-limit:] if len(items) > limit else items


def _excerpt(text: str, *, limit: int = 220) -> str:
    clean = " ".join(str(text).split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3] + "..."


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _render_dashboard(manifest: dict[str, Any]) -> str:
    lane = manifest["lane_manifest"]
    records = manifest["current_records"]
    dashboard = manifest["dashboard"]
    counts = dashboard["record_counts"]
    artifacts = dashboard["artifact_counts"]
    next_action_lines = [f"{item['action']}: {item['why']}" for item in manifest["next_actions"]]
    return (
        "# QSGW Research Cockpit\n\n"
        f"Topic: `{manifest['topic_id']}`\n\n"
        f"Manifest version: `{manifest['manifest_version']}`\n\n"
        f"Lane status: `{lane['status']}`\n\n"
        "## Current Counts\n\n"
        f"- Final evidence candidates: {counts['evidence_final']}\n"
        f"- Diagnostic evidence candidates: {counts['evidence_diagnostic']}\n"
        f"- Unclassified evidence candidates: {counts['evidence_unclassified']}\n"
        f"- Tool runs: {counts['tool_runs']}\n"
        f"- Reference locations: {counts['references']}\n"
        f"- Validation contracts: {counts['validation_contracts']}\n"
        f"- Sensemaking reports: {counts['sensemaking_reports']}\n\n"
        "## Artifact Scan\n\n"
        f"- Final-named reports: {artifacts['reports_final_named']}\n"
        f"- Diagnostic-named reports: {artifacts['reports_diagnostic_named']}\n"
        f"- Refresh scripts: {artifacts['refresh_scripts']}\n"
        f"- Plot scripts: {artifacts['plot_scripts']}\n\n"
        "## Forbidden Roots\n\n"
        f"{_bullets(item['root'] for item in lane['forbidden_roots'])}\n\n"
        "## Observed Remote Roots\n\n"
        f"{_bullets(records.get('observed_remote_roots') or [])}\n\n"
        "## Next Actions\n\n"
        f"{_bullets(next_action_lines)}\n\n"
        "This dashboard is orientation-only. Do not update claim trust or promote diagnostic outputs from it.\n"
    )


def _render_plot_guard(manifest: dict[str, Any]) -> str:
    guard = manifest["plot_guard"]
    final = guard["final_lane"]
    diagnostic = guard["diagnostic_lane"]
    return (
        "# QSGW Plot Guard\n\n"
        "## Final Lane\n\n"
        "Required row fields:\n"
        f"{_bullets(final['required_row_fields'])}\n\n"
        "Forbidden markers:\n"
        f"{_bullets(final['forbidden_markers'])}\n\n"
        f"Overwrite policy: {final['overwrite_policy']}\n\n"
        "## Diagnostic Lane\n\n"
        f"Required output label: `{diagnostic['required_output_label']}`\n\n"
        "Allowed markers:\n"
        f"{_bullets(diagnostic['allowed_markers'])}\n\n"
        f"Overwrite policy: {diagnostic['overwrite_policy']}\n\n"
        f"Trust boundary: {guard['trust_boundary']}\n"
    )


def _bullets(values: Any) -> str:
    items = [str(value) for value in values if str(value)]
    return "\n".join(f"- {value}" for value in items) if items else "- None"
