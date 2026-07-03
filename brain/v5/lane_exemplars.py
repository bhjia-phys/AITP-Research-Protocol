"""vNext lane-specific exemplar records and closure manifest."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from brain.v5.ids import prefixed_id
from brain.v5.markdown import write_md
from brain.v5.paths import WorkspacePaths

REQUIRED_LANES = ("toy_numeric", "semi_formal_theory", "code_backed_algorithm")
_LANES = set(REQUIRED_LANES)
_STATUSES = {"candidate", "accepted", "needs_review"}


@dataclass
class LaneExemplarRecord:
    exemplar_id: str
    topic_id: str
    lane: str
    title: str
    summary: str
    claim_id: str = ""
    run_id: str = ""
    gates_demonstrated: list[str] = field(default_factory=list)
    artifact_refs: list[str] = field(default_factory=list)
    domain_pack_refs: list[str] = field(default_factory=list)
    context_profile_refs: list[str] = field(default_factory=list)
    skill_refs: list[str] = field(default_factory=list)
    surface_refs: list[str] = field(default_factory=list)
    validation_surface_refs: list[str] = field(default_factory=list)
    workflow_steps: list[dict[str, Any]] = field(default_factory=list)
    failure_modes: list[dict[str, Any]] = field(default_factory=list)
    forbidden_uses: list[str] = field(default_factory=list)
    can_say: list[str] = field(default_factory=list)
    cannot_say: list[str] = field(default_factory=list)
    required_next_records: list[str] = field(default_factory=list)
    promotion_blockers: list[str] = field(default_factory=list)
    trust_boundary: str = ""
    source_refs: list[str] = field(default_factory=list)
    status: str = "candidate"
    summary_inputs_trusted: bool = False
    orientation_only: bool = True
    can_update_kernel_state: bool = True
    can_update_claim_trust: bool = False
    kind: str = "lane_exemplar"


def record_lane_exemplar(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    lane: str,
    title: str,
    summary: str,
    claim_id: str = "",
    run_id: str = "",
    gates_demonstrated: list[str] | None = None,
    artifact_refs: list[str] | None = None,
    domain_pack_refs: list[str] | None = None,
    context_profile_refs: list[str] | None = None,
    skill_refs: list[str] | None = None,
    surface_refs: list[str] | None = None,
    validation_surface_refs: list[str] | None = None,
    workflow_steps: list[dict[str, Any]] | None = None,
    failure_modes: list[dict[str, Any]] | None = None,
    forbidden_uses: list[str] | None = None,
    can_say: list[str] | None = None,
    cannot_say: list[str] | None = None,
    required_next_records: list[str] | None = None,
    promotion_blockers: list[str] | None = None,
    trust_boundary: str = "",
    source_refs: list[str] | None = None,
    status: str = "candidate",
) -> LaneExemplarRecord:
    """Record a vNext lane exemplar without making it scientific evidence."""

    if lane not in _LANES:
        raise ValueError(f"lane must be one of {sorted(_LANES)}")
    if status not in _STATUSES:
        raise ValueError(f"status must be one of {sorted(_STATUSES)}")
    record = LaneExemplarRecord(
        exemplar_id=prefixed_id("lane-exemplar", f"{topic_id}:{lane}:{title}", max_slug=72),
        topic_id=topic_id,
        lane=lane,
        title=title,
        summary=summary,
        claim_id=claim_id,
        run_id=run_id,
        gates_demonstrated=gates_demonstrated or [],
        artifact_refs=artifact_refs or [],
        domain_pack_refs=domain_pack_refs or [],
        context_profile_refs=context_profile_refs or [],
        skill_refs=skill_refs or [],
        surface_refs=surface_refs or [],
        validation_surface_refs=validation_surface_refs or [],
        workflow_steps=workflow_steps or [],
        failure_modes=failure_modes or [],
        forbidden_uses=forbidden_uses or [],
        can_say=can_say or [],
        cannot_say=cannot_say or [],
        required_next_records=required_next_records or [],
        promotion_blockers=promotion_blockers or [],
        trust_boundary=trust_boundary,
        source_refs=source_refs or [],
        status=status,
    )
    runtime_dir = _runtime_dir(ws, topic_id)
    runtime_dir.mkdir(parents=True, exist_ok=True)
    payload = asdict(record)
    _append_jsonl(runtime_dir / "lane_exemplars.jsonl", payload)
    write_md(
        runtime_dir / "lane_exemplars" / f"{record.exemplar_id}.md",
        payload,
        _lane_exemplar_body(record),
    )
    return record


def record_librpa_code_backed_algorithm_exemplar(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    claim_id: str = "",
    run_id: str = "",
    status: str = "accepted",
) -> LaneExemplarRecord:
    """Record the built-in LibRPA/GW code-backed algorithm exemplar."""

    return record_lane_exemplar(
        ws,
        topic_id=topic_id,
        lane="code_backed_algorithm",
        title="LibRPA/GW context-to-validation workflow",
        summary=(
            "Compile the LibRPA run context, load the gw_librpa domain pack and oh-my-librpa "
            "procedural skill, keep final/diagnostic lanes explicit, then turn tool runs into "
            "claim support only through passed validation results."
        ),
        claim_id=claim_id,
        run_id=run_id,
        gates_demonstrated=[
            "context_profile_selection",
            "domain_pack_loading",
            "lane_contract_check",
            "tool_run_provenance",
            "validation_result_gate",
            "trust_audit_before_promotion",
        ],
        artifact_refs=[
            "surface:aitp_context_pack",
            "surface:context_profile_draft",
            "surface:domain_pack_catalog:gw_librpa",
            "surface:hpc_cockpit",
            "surface:lane_contract_record",
            "surface:tool_run_record",
            "surface:validation_result_record",
        ],
        domain_pack_refs=["gw_librpa"],
        context_profile_refs=[
            "librpa_run_continuation",
            "source_reconstruction",
            "group_meeting_report",
            "closeout",
        ],
        skill_refs=[
            "oh-my-librpa",
            "oh-my-librpa-abacus-librpa",
            "oh-my-librpa-fhi-aims-qsgw",
        ],
        surface_refs=[
            "context_profile_template_catalog",
            "aitp_context_pack",
            "context_profile_draft",
            "domain_pack_catalog",
            "domain_skill_shim_manifest",
            "hpc_cockpit",
            "lane_contract_record",
            "tool_run_record",
            "validation_contract_record",
            "validation_result_record",
            "claim_trust_audit",
        ],
        validation_surface_refs=[
            "pre_tool_policy_decision",
            "validation_contract_record",
            "validation_result_record",
            "failure_mode_audit",
            "claim_trust_audit",
        ],
        workflow_steps=[
            {
                "step_id": "compile_librpa_context",
                "entrypoint": "aitp-v5 status context-pack <session-id> --task-profile librpa_run_continuation",
                "purpose": "Recover active claim, known records, domain hints, and can-say/cannot-say boundaries.",
            },
            {
                "step_id": "load_domain_experience",
                "entrypoint": "aitp-v5 domain-pack catalog",
                "purpose": "Load LibRPA/GW workflow, failure taxonomy, lane policy, artifact schema, and skill refs.",
            },
            {
                "step_id": "check_lane_contract",
                "entrypoint": "aitp-v5 status hpc-cockpit <args>",
                "purpose": "Confirm default diagnostic lane, final allowlist, supersession, and provenance gaps.",
            },
            {
                "step_id": "record_or_capture_tool_run",
                "entrypoint": "aitp-v5 tool run record <args>",
                "purpose": "Persist command, code state, lane, artifacts, scheduler/runtime state, and scientific_run_id.",
            },
            {
                "step_id": "record_validation_result",
                "entrypoint": "aitp-v5 validation result record <args>",
                "purpose": "Attach passed or partial validation before any tool-derived evidence can support a claim.",
            },
            {
                "step_id": "audit_before_promotion",
                "entrypoint": "aitp-v5 trust audit --claim <claim-id>",
                "purpose": "Check failure-mode coverage and validation links before evidence or memory promotion.",
            },
        ],
        failure_modes=[
            {
                "failure_id": "final_diagnostic_lane_mix",
                "signals": ["diagnostic label", "missing final allowlist", "assumption_plot"],
                "required_basis": ["lane_contract_record", "tool_run_record", "validation_result_record"],
            },
            {
                "failure_id": "hpc_runtime_not_science",
                "signals": ["TIME LIMIT", "OOM", "node failure", "missing expected output"],
                "required_basis": ["scheduler log", "stdout_stderr", "tool_run_record"],
            },
            {
                "failure_id": "code_state_or_recipe_gap",
                "signals": ["missing code_state_ids", "unbound recipe_id", "unversioned script"],
                "required_basis": ["code_state_record", "tool_recipe_record", "pre_tool_policy_decision"],
            },
            {
                "failure_id": "librpa_metadata_mismatch",
                "signals": ["frequency-grid mismatch", "basis-cutoff mismatch", "formula-code invariant mismatch"],
                "required_basis": ["librpa_gw_run_metadata_check", "formula_code_invariant_check"],
            },
        ],
        forbidden_uses=[
            "Treating scheduler success as scientific validation.",
            "Promoting diagnostic, unfinished, nonconverged, or contaminated-root runs as final evidence.",
            "Using generated summaries, plots, or dashboards as claim support without typed validation results.",
            "Updating claim trust directly from this exemplar or any orientation-only context pack.",
        ],
        can_say=[
            "Which typed surfaces should be consulted before continuing a LibRPA/GW run.",
            "Which failure modes and validation recipes must be checked for code-backed support.",
            "Whether a workflow record is only an exemplar or has passed validation-backed evidence links.",
        ],
        cannot_say=[
            "That a QSGW/GW physics conclusion is true.",
            "That a diagnostic lane run is eligible for final evidence.",
            "That oh-my-librpa procedural memory is itself evidence.",
        ],
        required_next_records=[
            "code_state_record",
            "lane_contract_record",
            "tool_recipe_record",
            "tool_run_record",
            "validation_contract_record",
            "validation_result_record",
            "evidence_record",
        ],
        promotion_blockers=[
            "missing passed validation_result_ids for cited tool_run_ids",
            "uncovered strongest_failure_mode",
            "missing final lane allowlist or artifact manifest",
            "summary-only or dashboard-only support",
        ],
        trust_boundary=(
            "Accepted workflow exemplar only; it can guide LibRPA/GW work but cannot validate a physics "
            "claim, update claim trust, or promote L2 memory without typed evidence and passed validation."
        ),
        source_refs=[
            "domain_pack:gw_librpa",
            "skill:oh-my-librpa",
            "docs:AITP_RESEARCH_BRAIN_ROADMAP.md#workstream-d",
            "surface:context_profile_template_catalog",
        ],
        status=status,
    )


def load_lane_exemplars(ws: WorkspacePaths, topic_id: str, *, limit: int = 6) -> dict[str, Any]:
    """Load topic-local lane exemplars for briefs and status surfaces."""

    items = [_brief_item(item) for item in _read_topic_exemplars(ws, topic_id)]
    items = items[-limit:]
    return {
        "present": bool(items),
        "items": items,
        "required_lanes": list(REQUIRED_LANES),
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }


def build_lane_exemplar_manifest(ws: WorkspacePaths) -> dict[str, Any]:
    """Return a workspace-level vNext Phase 5 lane exemplar closure manifest."""

    items = []
    topics_dir = ws.root / "topics"
    if topics_dir.exists():
        for topic_dir in sorted(path for path in topics_dir.iterdir() if path.is_dir()):
            items.extend(_read_topic_exemplars(ws, topic_dir.name))
    lane_status_counts = {lane: {} for lane in REQUIRED_LANES}
    for item in items:
        lane = str(item.get("lane") or "")
        status = str(item.get("status") or "")
        if lane in lane_status_counts and status:
            lane_status_counts[lane][status] = lane_status_counts[lane].get(status, 0) + 1
    covered_lanes = [
        lane
        for lane in REQUIRED_LANES
        if any(item.get("lane") == lane and item.get("status") == "accepted" for item in items)
    ]
    missing_lanes = [lane for lane in REQUIRED_LANES if lane not in covered_lanes]
    return {
        "kind": "lane_exemplar_manifest",
        "required_lanes": list(REQUIRED_LANES),
        "covered_lanes": covered_lanes,
        "missing_lanes": missing_lanes,
        "lane_status_counts": lane_status_counts,
        "exemplar_count": len(items),
        "items": [_brief_item(item) for item in items],
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _read_topic_exemplars(ws: WorkspacePaths, topic_id: str) -> list[dict[str, Any]]:
    path = _runtime_dir(ws, topic_id) / "lane_exemplars.jsonl"
    if not path.exists():
        return []
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            items.append(item)
    return items


def _brief_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "exemplar_id": str(item.get("exemplar_id") or ""),
        "topic_id": str(item.get("topic_id") or ""),
        "lane": str(item.get("lane") or ""),
        "title": str(item.get("title") or ""),
        "summary": str(item.get("summary") or ""),
        "claim_id": str(item.get("claim_id") or ""),
        "run_id": str(item.get("run_id") or ""),
        "gates_demonstrated": list(item.get("gates_demonstrated") or []),
        "artifact_refs": list(item.get("artifact_refs") or []),
        "domain_pack_refs": _list_values(item, "domain_pack_refs"),
        "context_profile_refs": _list_values(item, "context_profile_refs"),
        "skill_refs": _list_values(item, "skill_refs"),
        "surface_refs": _list_values(item, "surface_refs"),
        "validation_surface_refs": _list_values(item, "validation_surface_refs"),
        "workflow_steps": _list_values(item, "workflow_steps"),
        "failure_modes": _list_values(item, "failure_modes"),
        "forbidden_uses": _list_values(item, "forbidden_uses"),
        "can_say": _list_values(item, "can_say"),
        "cannot_say": _list_values(item, "cannot_say"),
        "required_next_records": _list_values(item, "required_next_records"),
        "promotion_blockers": _list_values(item, "promotion_blockers"),
        "trust_boundary": str(item.get("trust_boundary") or ""),
        "status": str(item.get("status") or ""),
        "orientation_only": True,
    }


def _lane_exemplar_body(record: LaneExemplarRecord) -> str:
    return (
        "# Lane Exemplar\n\n"
        f"Lane: {record.lane}\n\n"
        f"Title: {record.title}\n\n"
        f"Summary: {record.summary}\n\n"
        f"Trust boundary: {record.trust_boundary or 'Workflow exemplar only; not claim evidence.'}\n\n"
        "Gates demonstrated:\n"
        f"{_bullets(record.gates_demonstrated)}\n\n"
        "Artifacts:\n"
        f"{_bullets(record.artifact_refs)}\n\n"
        "Domain packs:\n"
        f"{_bullets(record.domain_pack_refs)}\n\n"
        "Context profiles:\n"
        f"{_bullets(record.context_profile_refs)}\n\n"
        "Skill refs:\n"
        f"{_bullets(record.skill_refs)}\n\n"
        "Workflow steps:\n"
        f"{_mapping_bullets(record.workflow_steps, label_key='step_id')}\n\n"
        "Failure modes:\n"
        f"{_mapping_bullets(record.failure_modes, label_key='failure_id')}\n\n"
        "Forbidden uses:\n"
        f"{_bullets(record.forbidden_uses)}\n"
    )


def _bullets(values: list[str]) -> str:
    return "\n".join(f"- {value}" for value in values) if values else "- None"


def _mapping_bullets(values: list[dict[str, Any]], *, label_key: str) -> str:
    if not values:
        return "- None"
    lines = []
    for value in values:
        if not isinstance(value, dict):
            lines.append(f"- {value}")
            continue
        label = str(value.get(label_key) or value.get("entrypoint") or value.get("purpose") or "item")
        detail = str(value.get("purpose") or value.get("signals") or value.get("required_basis") or "")
        lines.append(f"- {label}: {detail}" if detail else f"- {label}")
    return "\n".join(lines)


def _list_values(item: dict[str, Any], key: str) -> list[Any]:
    value = item.get(key)
    return list(value) if isinstance(value, list) else []


def _runtime_dir(ws: WorkspacePaths, topic_id: str) -> Path:
    return ws.topic_dir(topic_id) / "runtime"


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
