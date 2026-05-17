from __future__ import annotations


def test_trace_logger_appends_jsonl_events(tmp_path):
    from brain.v5.trace import TraceEvent, append_trace_event, read_trace_events

    trace_path = tmp_path / "trace.jsonl"
    append_trace_event(
        trace_path,
        TraceEvent(
            event_id="event-1",
            session_id="s1",
            topic_id="fqhe",
            event_type="brief_built",
            risk_level="fluid",
            payload={"max_questions": 1},
        ),
    )
    append_trace_event(
        trace_path,
        TraceEvent(
            event_id="event-2",
            session_id="s1",
            topic_id="fqhe",
            event_type="question_asked",
            risk_level="fluid",
            payload={"question_id": "q1"},
        ),
    )

    events = read_trace_events(trace_path)

    assert [event.event_id for event in events] == ["event-1", "event-2"]
    assert events[0].payload == {"max_questions": 1}


def test_audit_detects_underthinking_when_rigorous_action_lacks_evidence():
    from brain.v5.audit import audit_trace_events
    from brain.v5.trace import TraceEvent

    incidents = audit_trace_events(
        [
            TraceEvent(
                event_id="event-1",
                session_id="s1",
                topic_id="librpa-gw",
                claim_id="claim-1",
                event_type="brief_built",
                risk_level="rigorous",
                payload={"required_outputs": ["evidence_or_provenance"]},
            ),
            TraceEvent(
                event_id="event-2",
                session_id="s1",
                topic_id="librpa-gw",
                claim_id="claim-1",
                event_type="action_completed",
                risk_level="rigorous",
                payload={"action": "accept_code_method_result", "outputs": []},
            ),
        ]
    )

    assert len(incidents) == 1
    assert incidents[0].violation_kind == "under_thinking"
    assert incidents[0].change_direction == "tighten"
    assert incidents[0].severity == "high"
    assert "evidence_or_provenance" in incidents[0].suggested_harness_fix


def test_audit_detects_overharnessing_when_fluid_mode_asks_too_many_questions():
    from brain.v5.audit import audit_trace_events
    from brain.v5.trace import TraceEvent

    events = [
        TraceEvent(
            event_id="event-1",
            session_id="s1",
            topic_id="fqhe",
            event_type="brief_built",
            risk_level="fluid",
            payload={"max_questions": 1},
        )
    ]
    for index in range(3):
        events.append(
            TraceEvent(
                event_id=f"event-q{index}",
                session_id="s1",
                topic_id="fqhe",
                event_type="question_asked",
                risk_level="fluid",
                payload={"question_id": f"q{index}"},
            )
        )

    incidents = audit_trace_events(events)

    assert len(incidents) == 1
    assert incidents[0].violation_kind == "over_harnessing"
    assert incidents[0].change_direction == "loosen"
    assert "fluid" in incidents[0].observed_behavior
