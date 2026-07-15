"""Trust-neutral routing for grounded knowledge, insight, and procedural Skill candidates."""

from __future__ import annotations

from dataclasses import dataclass

from brain.v5.physics_knowledge_models import INSIGHT_KINDS


GROUNDED_KINDS = frozenset({"definition", "formula", "convention", "relation", "derivation"})
PROCEDURAL_KINDS = frozenset({"procedural_workflow"})


@dataclass(frozen=True)
class KnowledgeCandidate:
    candidate_id: str
    content_kinds: tuple[str, ...]
    statement: str
    source_refs: tuple[str, ...] = ()
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
