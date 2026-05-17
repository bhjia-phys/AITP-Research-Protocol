"""Harness audit rules for under-thinking and over-harnessing."""

from __future__ import annotations

from dataclasses import dataclass

from brain.v5.ids import prefixed_id
from brain.v5.trace import TraceEvent


@dataclass
class HarnessIncident:
    incident_id: str
    session_id: str
    topic_id: str
    claim_id: str
    violation_kind: str
    severity: str
    expected_harness_step: str
    observed_behavior: str
    evidence_ref: str
    suggested_harness_fix: str
    change_direction: str
    kind: str = "harness_incident"


def audit_trace_events(events: list[TraceEvent]) -> list[HarnessIncident]:
    """Scan a lightweight trace for harness failures."""

    incidents: list[HarnessIncident] = []
    incidents.extend(_detect_underthinking(events))
    incidents.extend(_detect_over_harnessing(events))
    return incidents


def _detect_underthinking(events: list[TraceEvent]) -> list[HarnessIncident]:
    incidents: list[HarnessIncident] = []
    required_by_focus: dict[tuple[str, str, str], set[str]] = {}

    for event in events:
        focus = _focus_key(event)
        if event.event_type == "brief_built":
            required = event.payload.get("required_outputs") or []
            required_by_focus[focus] = set(required)
            continue

        if event.event_type != "action_completed":
            continue
        if event.risk_level not in {"rigorous", "adversarial"}:
            continue

        required = required_by_focus.get(focus, set(event.payload.get("required_outputs") or []))
        outputs = set(event.payload.get("outputs") or [])
        missing = sorted(required - outputs)
        critical_missing = [item for item in missing if item in {"evidence_or_provenance", "counterargument_or_falsification_path"}]
        if not critical_missing:
            continue

        incidents.append(
            HarnessIncident(
                incident_id=_incident_id("under-thinking", event, ",".join(critical_missing)),
                session_id=event.session_id,
                topic_id=event.topic_id,
                claim_id=event.claim_id,
                violation_kind="under_thinking",
                severity="high",
                expected_harness_step=f"produce required outputs: {', '.join(critical_missing)}",
                observed_behavior=f"{event.risk_level} action completed without {', '.join(critical_missing)}",
                evidence_ref=f"trace_event:{event.event_id}",
                suggested_harness_fix=(
                    "tighten policy or question generation so "
                    f"{', '.join(critical_missing)} is required before accepting the action"
                ),
                change_direction="tighten",
            )
        )

    return incidents


def _detect_over_harnessing(events: list[TraceEvent]) -> list[HarnessIncident]:
    incidents: list[HarnessIncident] = []
    max_questions_by_session: dict[tuple[str, str], int] = {}
    question_events: dict[tuple[str, str], list[TraceEvent]] = {}

    for event in events:
        session_key = (event.session_id, event.topic_id)
        if event.event_type == "brief_built" and event.risk_level == "fluid":
            max_questions = event.payload.get("max_questions")
            if isinstance(max_questions, int):
                max_questions_by_session[session_key] = max_questions
        elif event.event_type == "question_asked" and event.risk_level == "fluid":
            question_events.setdefault(session_key, []).append(event)

    for session_key, questions in question_events.items():
        max_questions = max_questions_by_session.get(session_key)
        if max_questions is None or len(questions) <= max_questions:
            continue

        first = questions[0]
        incidents.append(
            HarnessIncident(
                incident_id=_incident_id("over-harnessing", first, str(len(questions))),
                session_id=first.session_id,
                topic_id=first.topic_id,
                claim_id=first.claim_id,
                violation_kind="over_harnessing",
                severity="medium",
                expected_harness_step=f"ask at most {max_questions} question(s) in fluid mode",
                observed_behavior=f"fluid mode asked {len(questions)} questions",
                evidence_ref=",".join(f"trace_event:{event.event_id}" for event in questions),
                suggested_harness_fix="loosen fluid interaction so extra questions are deferred to session summary",
                change_direction="loosen",
            )
        )

    return incidents


def _focus_key(event: TraceEvent) -> tuple[str, str, str]:
    return (event.session_id, event.topic_id, event.claim_id)


def _incident_id(prefix: str, event: TraceEvent, detail: str) -> str:
    return prefixed_id("incident", f"{prefix}:{event.session_id}:{event.topic_id}:{event.claim_id}:{event.event_id}:{detail}")
