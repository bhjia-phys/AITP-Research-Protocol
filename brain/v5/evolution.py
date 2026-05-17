"""Background harness-evolution proposal planning."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import groupby

from brain.v5.audit import HarnessIncident
from brain.v5.ids import prefixed_id


@dataclass
class EvolutionProposal:
    proposal_id: str
    title: str
    change_direction: str
    incident_count: int
    incident_ids: list[str] = field(default_factory=list)
    target_files: list[str] = field(default_factory=list)
    required_tests: list[str] = field(default_factory=list)
    requires_regression_test: bool = True
    requires_human_review: bool = False
    approval_level: int = 2
    rationale: str = ""
    suggested_patch_type: str = ""
    status: str = "proposed"
    kind: str = "evolution_proposal"


def plan_evolution_proposals(
    incidents: list[HarnessIncident],
    *,
    repetition_threshold: int = 3,
) -> list[EvolutionProposal]:
    """Aggregate incidents into sparse, test-backed harness proposals."""

    proposals: list[EvolutionProposal] = []
    ordered = sorted(incidents, key=_group_key)
    for _, group_iter in groupby(ordered, key=_group_key):
        group = list(group_iter)
        if not _should_propose(group, repetition_threshold):
            continue
        proposals.append(_proposal_for_group(group))
    return proposals


def _should_propose(group: list[HarnessIncident], repetition_threshold: int) -> bool:
    if len(group) >= repetition_threshold:
        return True
    return any(incident.severity in {"high", "critical"} for incident in group)


def _proposal_for_group(group: list[HarnessIncident]) -> EvolutionProposal:
    first = group[0]
    target_files, required_tests = _targets_for(first)
    requires_review = _requires_human_review(group)
    approval_level = 3 if requires_review else 2
    rationale = _rationale(group, requires_review)
    title = f"{first.change_direction}: {first.violation_kind.replace('_', ' ')}"
    basis = ":".join([first.violation_kind, first.change_direction, first.suggested_harness_fix, str(len(group))])

    return EvolutionProposal(
        proposal_id=prefixed_id("proposal", basis),
        title=title,
        change_direction=first.change_direction,
        incident_count=len(group),
        incident_ids=[incident.incident_id for incident in group],
        target_files=target_files,
        required_tests=required_tests,
        requires_regression_test=True,
        requires_human_review=requires_review,
        approval_level=approval_level,
        rationale=rationale,
        suggested_patch_type=_patch_type_for(first),
    )


def _group_key(incident: HarnessIncident) -> tuple[str, str, str]:
    return (incident.violation_kind, incident.change_direction, incident.suggested_harness_fix)


def _targets_for(incident: HarnessIncident) -> tuple[list[str], list[str]]:
    text = _incident_text(incident)
    if "core protocol" in text or "promotion" in text:
        return (
            ["brain/v5/policy.py", "brain/v5/contracts.py"],
            ["tests/test_v5_policy.py", "tests/test_v5_contracts.py"],
        )
    if incident.violation_kind == "over_harnessing":
        return (
            ["brain/v5/audit.py", "brain/v5/interaction.py", "tests/test_v5_trace_audit.py"],
            ["tests/test_v5_trace_audit.py", "tests/test_v5_interaction.py"],
        )
    if "code" in text or "provenance" in text:
        return (
            ["brain/v5/policy.py", "brain/v5/risk.py", "brain/v5/code.py"],
            ["tests/test_v5_policy.py", "tests/test_v5_risk_engine.py"],
        )
    return (
        ["brain/v5/policy.py", "brain/v5/question_engine.py"],
        ["tests/test_v5_policy.py", "tests/test_v5_risk_engine.py"],
    )


def _requires_human_review(group: list[HarnessIncident]) -> bool:
    return any(incident.severity == "critical" or "core protocol" in _incident_text(incident) for incident in group)


def _rationale(group: list[HarnessIncident], requires_review: bool) -> str:
    first = group[0]
    base = (
        f"{len(group)} incident(s) show {first.violation_kind} with change direction "
        f"{first.change_direction}. Suggested fix: {first.suggested_harness_fix}."
    )
    if requires_review:
        return base + " This touches core protocol behavior, so human review is required."
    return base + " A regression test must be added before any harness patch is accepted."


def _patch_type_for(incident: HarnessIncident) -> str:
    if incident.change_direction == "loosen":
        return "friction_budget_rule"
    if "policy" in _incident_text(incident) or "promotion" in _incident_text(incident):
        return "policy_guard"
    if "question" in _incident_text(incident):
        return "dynamic_question_rule"
    return "risk_or_policy_rule"


def _incident_text(incident: HarnessIncident) -> str:
    return " ".join(
        [
            incident.violation_kind,
            incident.expected_harness_step,
            incident.observed_behavior,
            incident.suggested_harness_fix,
        ]
    ).lower()
