"""Trust-neutral routing for grounded knowledge, insight, and procedural Skill candidates."""

from __future__ import annotations

from dataclasses import dataclass

from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version, pin_current_record
from brain.v5.physics_knowledge_models import INSIGHT_KINDS


GROUNDED_KINDS = frozenset({"definition", "formula", "convention", "relation", "derivation"})
PROCEDURAL_KINDS = frozenset({"procedural_workflow"})


@dataclass(frozen=True)
class KnowledgeCandidate:
    candidate_id: str
    content_kinds: tuple[str, ...]
    statement: str
    topic_id: str = ""
    source_refs: tuple[str, ...] = ()
    grounding_pins: tuple[PinnedRecordRef, ...] = ()
    framework: str = ""
    regime: str = ""
    conventions: tuple[str, ...] = ()
    procedural_steps: tuple[str, ...] = ()
    validation_refs: tuple[str, ...] = ()
    applicability_boundary: str = ""


@dataclass(frozen=True)
class CandidateRoute:
    lane: str
    target_lanes: tuple[str, ...]
    split_required: bool
    eligible_for_skill: bool
    requires_human_review: bool = True
    evidence_role: str = "forbidden"
    can_update_claim_trust: bool = False


@dataclass(frozen=True)
class CandidateDiagnostics:
    candidate_id: str
    lane: str
    eligible_for_grounded_review: bool
    missing_requirements: tuple[str, ...]
    errors: tuple[str, ...]
    checked_refs: tuple[str, ...]
    writes_records: bool = False
    can_update_claim_trust: bool = False


def route_knowledge_candidate(candidate: KnowledgeCandidate) -> CandidateRoute:
    kinds = frozenset(candidate.content_kinds)
    if not kinds:
        raise ValueError("knowledge candidate requires at least one content kind")
    unknown = kinds.difference(GROUNDED_KINDS, INSIGHT_KINDS, PROCEDURAL_KINDS)
    if unknown:
        raise ValueError(f"unsupported knowledge candidate kinds: {sorted(unknown)}")
    lanes = []
    if kinds.intersection(GROUNDED_KINDS):
        lanes.append("grounded_knowledge")
    if kinds.intersection(INSIGHT_KINDS):
        lanes.append("speculative_insight")
    if kinds.intersection(PROCEDURAL_KINDS):
        lanes.append("procedural_skill")
    if len(lanes) > 1:
        return CandidateRoute(
            lane="mixed_split_required",
            target_lanes=tuple(lanes),
            split_required=True,
            eligible_for_skill=False,
        )
    lane = lanes[0]
    eligible = bool(
        lane == "procedural_skill"
        and candidate.procedural_steps
        and candidate.validation_refs
        and candidate.applicability_boundary.strip()
    )
    return CandidateRoute(
        lane=lane,
        target_lanes=(lane,),
        split_required=False,
        eligible_for_skill=eligible,
    )


def diagnose_knowledge_candidate(
    ws: WorkspacePaths,
    candidate: KnowledgeCandidate,
) -> CandidateDiagnostics:
    route = route_knowledge_candidate(candidate)
    asset_refs: list[str] = []
    locations = []
    checked: list[str] = []
    errors: list[str] = []
    for pin in candidate.grounding_pins:
        checked.append(pin.record_ref)
        try:
            if pin_current_record(ws, pin.record_ref) != pin:
                errors.append(f"stale_grounding_pin:{pin.record_ref}")
                continue
            version = get_record_version(ws, pin)
        except (ValueError, RuntimeError):
            errors.append(f"unresolved_grounding_pin:{pin.record_ref}")
            continue
        topic_id = str(getattr(version.record, "topic_id", "") or "")
        if candidate.topic_id and topic_id and topic_id != candidate.topic_id:
            errors.append(f"grounding_scope_mismatch:{pin.record_ref}")
        if pin.record_ref.startswith("source_asset:"):
            asset_refs.append(pin.record_ref)
        elif pin.record_ref.startswith("reference_location:"):
            locations.append(version.record)
    missing = []
    if not asset_refs:
        missing.append("exact_source_asset_pin")
    if not locations:
        missing.append("exact_source_location_pin")
    if route.lane == "grounded_knowledge" and not candidate.framework.strip():
        missing.append("framework")
    if route.lane == "grounded_knowledge" and not candidate.regime.strip():
        missing.append("regime")
    if asset_refs and any(location.source_ref not in asset_refs for location in locations):
        errors.append("source_location_asset_mismatch")
    eligible = bool(
        route.lane == "grounded_knowledge" and not missing and not errors
    )
    return CandidateDiagnostics(
        candidate_id=candidate.candidate_id,
        lane=route.lane,
        eligible_for_grounded_review=eligible,
        missing_requirements=tuple(missing),
        errors=tuple(errors),
        checked_refs=tuple(checked),
    )
