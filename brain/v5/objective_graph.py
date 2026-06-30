"""Read-only objective/work-package projection for quiet research sessions."""

from __future__ import annotations

from typing import Any

from brain.v5.brief import build_execution_brief
from brain.v5.claim_relation_map import build_claim_relation_map
from brain.v5.models import (
    ArtifactRecord,
    ClaimRecord,
    ClaimStatusRecord,
    ProofObligationRecord,
    ResearchRouteRecord,
    ResearchRunRecord,
    TopicRecord,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.recovery_session import recover_session_binding_for_read
from brain.v5.store import list_valid_records, read_record


def build_objective_graph(ws: WorkspacePaths, session_id: str) -> dict[str, Any]:
    """Build an orientation-only objective/work-package view from typed records."""

    recovered = recover_session_binding_for_read(ws, session_id)
    session = recovered.session
    topic = _read_topic(ws, session.topic_id)
    claims = _topic_claims(ws, session.topic_id)
    artifacts = _topic_artifacts(ws, session.topic_id)
    routes = _topic_routes(ws, session.topic_id)
    runs = _topic_runs(ws, session.topic_id)
    statuses = _topic_claim_statuses(ws, session.topic_id)
    obligations = _topic_proof_obligations(ws, session.topic_id)

    work_packages = _work_packages(
        active_claim_id=session.active_claim,
        active_route_id=session.active_route,
        claims=claims,
        artifacts=artifacts,
        routes=routes,
        runs=runs,
        statuses=statuses,
        obligations=obligations,
    )
    active_work_packages = [
        package
        for package in work_packages
        if package["work_package_id"] in _active_work_package_ids(work_packages)
    ]

    payload = {
        "ok": True,
        "kind": "objective_graph",
        "topic_id": session.topic_id,
        "session_id": session.session_id,
        "requested_session_id": recovered.requested_session_id,
        "recovery_selection_source": recovered.recovery_selection_source,
        "current_objective": {
            "objective_id": f"objective-{session.topic_id}",
            "title": topic.title if topic else session.topic_id,
            "source": "topic_record",
            "status": "active",
        },
        "active_work_packages": active_work_packages,
        "work_packages": work_packages,
        "claims": [_claim_payload(claim) for claim in claims],
        "artifacts": [_artifact_payload(artifact) for artifact in artifacts],
        "deliverables": _deliverables(artifacts),
        "blockers": _blockers(statuses, obligations),
        "source_records": {
            "session": [session.session_id],
            "claims": [claim.claim_id for claim in claims],
            "routes": [route.route_id for route in routes],
            "research_runs": [run.run_id for run in runs],
            "artifacts": [artifact.artifact_id for artifact in artifacts],
            "claim_statuses": [status.status_id for status in statuses],
            "proof_obligations": [obligation.obligation_id for obligation in obligations],
        },
        "truth_source": False,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    payload["markdown"] = _render_objective_graph_markdown(payload)
    return payload


def build_compact_brief(
    ws: WorkspacePaths,
    session_id: str,
    *,
    max_lines: int = 40,
    objective_text: str = "",
    user_goal: str = "",
) -> dict[str, Any]:
    """Build a short orientation-only brief that preserves trust boundaries."""

    objective_graph = build_objective_graph(ws, session_id)
    full_brief = build_execution_brief(ws, session_id)
    if objective_text or user_goal:
        relation_map = build_claim_relation_map(
            ws,
            session_id,
            objective_text=objective_text,
            user_goal=user_goal,
        )
    else:
        relation_map = full_brief.get("claim_relation_map") or build_claim_relation_map(ws, session_id)
    conclusion = relation_map.get("current_conclusion") or {}
    focus_reconciliation = relation_map.get("active_claim_focus_reconciliation") or {}
    drift_detected = bool(relation_map.get("not_authoritative_for_current_goal_if_rebind_needed"))
    warnings = list(relation_map.get("warnings") or [])
    active_package = _first(objective_graph.get("active_work_packages") or [])
    relevant_claim_ids = list(active_package.get("claim_ids") or []) if active_package else []
    relevant_claims = [
        claim
        for claim in objective_graph.get("claims", [])
        if not relevant_claim_ids or claim.get("claim_id") in relevant_claim_ids
    ][:5]
    artifacts = [
        artifact
        for artifact in objective_graph.get("artifacts", [])
        if not relevant_claim_ids or artifact.get("claim_id") in relevant_claim_ids
    ][:5]
    next_actions = _limit_strings(
        list(relation_map.get("next_valid_actions") or [])
        + [str(item.get("action") or "") for item in full_brief.get("next_action_candidates", [])],
        limit=6,
    )
    blockers = _limit_strings(list(relation_map.get("current_blockers") or []), limit=6)
    can_say = _limit_strings(list(conclusion.get("can_say") or []), limit=6)
    cannot_say = _limit_strings(list(conclusion.get("cannot_say") or []), limit=6)
    if drift_detected:
        drift_warning = "active_claim_focus_drift_detected: active claim relation map is scoped to the old active claim and may be stale for the current goal"
        blockers = _limit_strings([drift_warning] + blockers, limit=6)
        cannot_say = _limit_strings(
            ["cannot treat active-claim-only relation map as authoritative for the current goal until keep/rebind/split is chosen"]
            + cannot_say,
            limit=6,
        )
        next_actions = _limit_strings(
            [
                "choose active-claim focus option: keep current claim, confirm rebind, split claim/work package, or continue read-only stale"
            ]
            + next_actions,
            limit=6,
        )

    payload = {
        "ok": True,
        "kind": "compact_execution_brief",
        "session_id": str(objective_graph.get("session_id") or ""),
        "topic_id": str(objective_graph.get("topic_id") or ""),
        "current_objective": objective_graph.get("current_objective") or {},
        "active_work_package": active_package or {},
        "relevant_claims": relevant_claims,
        "can_say": can_say,
        "cannot_say": cannot_say,
        "blockers": blockers,
        "next_valid_actions": next_actions,
        "recent_relevant_artifacts": artifacts,
        "relation_map_scope": str(relation_map.get("relation_map_scope") or "active_claim_only"),
        "not_authoritative_for_current_goal_if_rebind_needed": drift_detected,
        "warnings": warnings,
        "active_claim_focus_reconciliation": focus_reconciliation,
        "expand": {
            "full_execution_brief_cli": f"aitp-v5 brief {session_id}",
            "full_relation_map_cli": f"aitp-v5 relation-map {session_id}",
            "objective_graph_cli": f"aitp-v5 status objective-graph {session_id}",
            "mcp_full_execution_brief": "aitp_v5_get_execution_brief",
            "mcp_full_relation_map": "aitp_v5_get_claim_relation_map",
            "mcp_objective_graph": "aitp_v5_get_objective_graph",
        },
        "source_records": {
            "objective_graph": "derived",
            "execution_brief": f"execution_brief:{session_id}",
            "claim_relation_map": f"claim_relation_map:{session_id}",
            "active_claim_focus_reconciliation": "derived",
        },
        "truth_source": False,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    line_limit = max(1, min(max_lines, 40))
    payload["lines"] = _compact_lines(payload)[:line_limit]
    payload["line_count"] = len(payload["lines"])
    payload["markdown"] = "\n".join(payload["lines"]) + "\n"
    return payload


def _read_topic(ws: WorkspacePaths, topic_id: str) -> TopicRecord | None:
    try:
        return read_record(ws.topic_dir(topic_id) / "topic.md", TopicRecord)
    except (FileNotFoundError, TypeError, ValueError):
        return None


def _topic_claims(ws: WorkspacePaths, topic_id: str) -> list[ClaimRecord]:
    return [
        claim
        for claim in list_valid_records(ws.registry_dir("claims"), ClaimRecord)
        if claim.topic_id == topic_id and getattr(claim, "lifecycle_status", "active") == "active"
    ]


def _topic_artifacts(ws: WorkspacePaths, topic_id: str) -> list[ArtifactRecord]:
    return [
        artifact
        for artifact in list_valid_records(ws.registry_dir("artifacts"), ArtifactRecord)
        if artifact.topic_id == topic_id
    ]


def _topic_routes(ws: WorkspacePaths, topic_id: str) -> list[ResearchRouteRecord]:
    return [
        route
        for route in list_valid_records(ws.registry_dir("routes"), ResearchRouteRecord)
        if route.topic_id == topic_id
    ]


def _topic_runs(ws: WorkspacePaths, topic_id: str) -> list[ResearchRunRecord]:
    return [
        run
        for run in list_valid_records(ws.registry_dir("research_runs"), ResearchRunRecord)
        if run.topic_id == topic_id
    ]


def _topic_claim_statuses(ws: WorkspacePaths, topic_id: str) -> list[ClaimStatusRecord]:
    return [
        status
        for status in list_valid_records(ws.registry_dir("claim_statuses"), ClaimStatusRecord)
        if status.topic_id == topic_id
    ]


def _topic_proof_obligations(ws: WorkspacePaths, topic_id: str) -> list[ProofObligationRecord]:
    return [
        obligation
        for obligation in list_valid_records(ws.registry_dir("proof_obligations"), ProofObligationRecord)
        if obligation.topic_id == topic_id
    ]


def _work_packages(
    *,
    active_claim_id: str,
    active_route_id: str,
    claims: list[ClaimRecord],
    artifacts: list[ArtifactRecord],
    routes: list[ResearchRouteRecord],
    runs: list[ResearchRunRecord],
    statuses: list[ClaimStatusRecord],
    obligations: list[ProofObligationRecord],
) -> list[dict[str, Any]]:
    packages: list[dict[str, Any]] = []
    seen: set[str] = set()
    for route in routes:
        package = _route_package(route, artifacts, runs, statuses, obligations, active_route_id)
        packages.append(package)
        seen.update(package["claim_ids"])
    for claim in claims:
        if claim.claim_id in seen and claim.claim_id != active_claim_id:
            continue
        packages.append(_claim_package(claim, artifacts, runs, statuses, obligations, active_claim_id))
    return packages


def _route_package(
    route: ResearchRouteRecord,
    artifacts: list[ArtifactRecord],
    runs: list[ResearchRunRecord],
    statuses: list[ClaimStatusRecord],
    obligations: list[ProofObligationRecord],
    active_route_id: str,
) -> dict[str, Any]:
    claim_ids = [route.claim_id] if route.claim_id else []
    return {
        "work_package_id": f"wp-route-{route.route_id}",
        "title": route.title,
        "status": "active" if route.route_id == active_route_id else route.status,
        "route_id": route.route_id,
        "claim_ids": claim_ids,
        "artifact_ids": _artifact_ids_for_claims(artifacts, claim_ids),
        "research_run_ids": [run.run_id for run in runs if run.claim_id in claim_ids],
        "blockers": _claim_blockers(statuses, obligations, claim_ids),
        "next_action": route.next_action,
        "source": "research_route",
    }


def _claim_package(
    claim: ClaimRecord,
    artifacts: list[ArtifactRecord],
    runs: list[ResearchRunRecord],
    statuses: list[ClaimStatusRecord],
    obligations: list[ProofObligationRecord],
    active_claim_id: str,
) -> dict[str, Any]:
    claim_ids = [claim.claim_id]
    return {
        "work_package_id": f"wp-claim-{claim.claim_id}",
        "title": _excerpt(claim.statement, limit=96),
        "status": "active" if claim.claim_id == active_claim_id else "available",
        "route_id": "",
        "claim_ids": claim_ids,
        "artifact_ids": _artifact_ids_for_claims(artifacts, claim_ids),
        "research_run_ids": [run.run_id for run in runs if run.claim_id == claim.claim_id],
        "blockers": _claim_blockers(statuses, obligations, claim_ids),
        "next_action": _first_nonempty([status.next_action for status in statuses if status.claim_id == claim.claim_id]),
        "source": "claim_record",
    }


def _active_work_package_ids(packages: list[dict[str, Any]]) -> set[str]:
    active = {package["work_package_id"] for package in packages if package.get("status") == "active"}
    if active:
        return active
    return {packages[0]["work_package_id"]} if packages else set()


def _artifact_ids_for_claims(artifacts: list[ArtifactRecord], claim_ids: list[str]) -> list[str]:
    return [artifact.artifact_id for artifact in artifacts if artifact.claim_id in claim_ids]


def _claim_blockers(
    statuses: list[ClaimStatusRecord],
    obligations: list[ProofObligationRecord],
    claim_ids: list[str],
) -> list[str]:
    blockers: list[str] = []
    for status in statuses:
        if status.claim_id in claim_ids:
            blockers.extend(status.open_gaps)
            if status.next_action:
                blockers.append(status.next_action)
    for obligation in obligations:
        if obligation.claim_id in claim_ids and obligation.status.lower() in {"open", "pending", "blocked", "incomplete"}:
            blockers.append(obligation.statement)
    return _limit_strings(blockers, limit=8)


def _blockers(statuses: list[ClaimStatusRecord], obligations: list[ProofObligationRecord]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for status in statuses:
        for gap in status.open_gaps:
            out.append({"record_kind": "claim_status", "record_id": status.status_id, "claim_id": status.claim_id, "summary": gap})
    for obligation in obligations:
        if obligation.status.lower() in {"open", "pending", "blocked", "incomplete"}:
            out.append({
                "record_kind": "proof_obligation",
                "record_id": obligation.obligation_id,
                "claim_id": obligation.claim_id,
                "summary": obligation.statement,
            })
    return out


def _claim_payload(claim: ClaimRecord) -> dict[str, Any]:
    return {
        "claim_id": claim.claim_id,
        "statement": claim.statement,
        "confidence_state": claim.confidence_state,
        "evidence_profile": claim.evidence_profile,
        "scope": claim.scope,
        "non_claims": claim.non_claims,
        "strongest_failure_mode": claim.strongest_failure_mode,
    }


def _artifact_payload(artifact: ArtifactRecord) -> dict[str, Any]:
    return {
        "artifact_id": artifact.artifact_id,
        "claim_id": artifact.claim_id,
        "artifact_type": artifact.artifact_type,
        "uri": artifact.uri,
        "summary": artifact.summary,
    }


def _deliverables(artifacts: list[ArtifactRecord]) -> list[dict[str, Any]]:
    deliverable_markers = ("paper", "note", "report", "draft", "manuscript")
    return [
        {
            "deliverable_id": artifact.artifact_id,
            "artifact_id": artifact.artifact_id,
            "kind": artifact.artifact_type,
            "summary": artifact.summary,
            "status": "artifact_recorded",
        }
        for artifact in artifacts
        if any(marker in f"{artifact.artifact_type} {artifact.summary}".lower() for marker in deliverable_markers)
    ]


def _compact_lines(payload: dict[str, Any]) -> list[str]:
    objective = payload.get("current_objective") or {}
    package = payload.get("active_work_package") or {}
    lines = [
        f"Current objective: {objective.get('title') or payload.get('topic_id')}",
        f"Active work package: {package.get('title') or 'none'}",
    ]
    if payload.get("not_authoritative_for_current_goal_if_rebind_needed"):
        reconciliation = payload.get("active_claim_focus_reconciliation") or {}
        lines.extend(
            [
                "Warning: active_claim_focus_drift_detected.",
                "Relation map scope: active_claim_only; confirm keep/rebind/split before using it as current-goal context.",
                "Candidate sibling claims:",
            ]
        )
        candidates = list(reconciliation.get("candidate_sibling_claims") or [])[:3]
        if candidates:
            lines.extend(
                f"- {candidate.get('claim_id')}: {_excerpt(candidate.get('statement_excerpt') or '', limit=110)}"
                for candidate in candidates
            )
        else:
            lines.append("- none")
    lines.append("Relevant claims:")
    lines.extend(f"- {claim.get('claim_id')}: {_excerpt(claim.get('statement') or '', limit=120)}" for claim in payload.get("relevant_claims", []))
    lines.append("Can say:")
    lines.extend(f"- {item}" for item in payload.get("can_say", []))
    lines.append("Cannot say:")
    lines.extend(f"- {item}" for item in payload.get("cannot_say", []))
    lines.append("Blockers:")
    lines.extend(f"- {item}" for item in payload.get("blockers", []))
    lines.append("Next valid actions:")
    lines.extend(f"- {item}" for item in payload.get("next_valid_actions", []))
    lines.append("Recent relevant artifacts:")
    lines.extend(
        f"- {artifact.get('artifact_id')}: {_excerpt(artifact.get('summary') or artifact.get('uri') or '', limit=100)}"
        for artifact in payload.get("recent_relevant_artifacts", [])
    )
    lines.append("Expand: use full execution brief or full relation map explicitly.")
    return lines


def _render_objective_graph_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Objective Graph: {payload['topic_id']}",
        "",
        f"- Current objective: {payload['current_objective'].get('title', '')}",
        f"- Active work packages: {len(payload.get('active_work_packages') or [])}",
        f"- Claims: {len(payload.get('claims') or [])}",
        f"- Artifacts: {len(payload.get('artifacts') or [])}",
        f"- Blockers: {len(payload.get('blockers') or [])}",
    ]
    return "\n".join(lines) + "\n"


def _first(items: list[Any]) -> Any:
    return items[0] if items else None


def _first_nonempty(items: list[str]) -> str:
    for item in items:
        if item:
            return item
    return ""


def _limit_strings(items: list[str], *, limit: int) -> list[str]:
    out: list[str] = []
    for item in items:
        text = str(item or "").strip()
        if text and text not in out:
            out.append(text)
        if len(out) >= limit:
            break
    return out


def _excerpt(value: str, *, limit: int) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."
