from __future__ import annotations


def test_repeated_incidents_aggregate_into_one_proposal():
    from brain.v5.audit import HarnessIncident
    from brain.v5.evolution import plan_evolution_proposals

    incidents = [
        HarnessIncident(
            incident_id=f"incident-{index}",
            session_id=f"s{index}",
            topic_id="fqhe",
            claim_id="claim-fqhe",
            violation_kind="over_harnessing",
            severity="medium",
            expected_harness_step="ask at most 1 question in fluid mode",
            observed_behavior="fluid mode asked 3 questions",
            evidence_ref=f"trace_event:event-{index}",
            suggested_harness_fix="loosen fluid interaction so extra questions are deferred",
            change_direction="loosen",
        )
        for index in range(3)
    ]

    proposals = plan_evolution_proposals(incidents)

    assert len(proposals) == 1
    assert proposals[0].change_direction == "loosen"
    assert proposals[0].incident_count == 3
    assert proposals[0].requires_regression_test is True
    assert "tests/test_v5_trace_audit.py" in proposals[0].target_files


def test_high_severity_incident_generates_proposal_without_repetition():
    from brain.v5.audit import HarnessIncident
    from brain.v5.evolution import plan_evolution_proposals

    incident = HarnessIncident(
        incident_id="incident-code-provenance",
        session_id="s1",
        topic_id="librpa-gw",
        claim_id="claim-code",
        violation_kind="under_thinking",
        severity="high",
        expected_harness_step="produce evidence_or_provenance",
        observed_behavior="rigorous action completed without evidence_or_provenance",
        evidence_ref="trace_event:event-1",
        suggested_harness_fix="tighten policy so evidence_or_provenance is required",
        change_direction="tighten",
    )

    proposals = plan_evolution_proposals([incident])

    assert len(proposals) == 1
    assert proposals[0].requires_human_review is False
    assert proposals[0].required_tests
    assert proposals[0].approval_level == 2


def test_core_protocol_change_requires_human_review():
    from brain.v5.audit import HarnessIncident
    from brain.v5.evolution import plan_evolution_proposals

    incident = HarnessIncident(
        incident_id="incident-core-policy",
        session_id="s1",
        topic_id="global",
        claim_id="",
        violation_kind="under_thinking",
        severity="critical",
        expected_harness_step="block unsafe promotion",
        observed_behavior="core protocol allowed promotion without evidence",
        evidence_ref="trace_event:event-1",
        suggested_harness_fix="modify core protocol promotion policy",
        change_direction="tighten",
    )

    proposals = plan_evolution_proposals([incident])

    assert len(proposals) == 1
    assert proposals[0].requires_human_review is True
    assert proposals[0].approval_level == 3
    assert "core protocol" in proposals[0].rationale.lower()
