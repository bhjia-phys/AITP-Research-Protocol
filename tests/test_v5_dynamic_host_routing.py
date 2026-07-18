from __future__ import annotations

import importlib.util
import importlib
from dataclasses import FrozenInstanceError
from dataclasses import replace
import json

import pytest


def test_host_route_contract_module_exists():
    assert importlib.util.find_spec("brain.v5.host_route_contracts") is not None


def test_route_contracts_expose_versioned_statuses():
    contracts = importlib.import_module("brain.v5.host_route_contracts")

    assert contracts.HOST_ROUTE_REQUEST_SCHEMA_VERSION == "aitp.host_route_request.v1"
    assert contracts.HOST_ROUTE_DECISION_SCHEMA_VERSION == "aitp.host_route_decision.v1"
    assert contracts.HOST_ROUTE_STATUSES == frozenset(
        {
            "outside_aitp",
            "selected",
            "ambiguous",
            "workspace_recovery",
            "conflict",
            "coverage_blocked",
        }
    )


def test_host_route_request_normalization_is_bounded_immutable_and_deterministic():
    from brain.v5.host_route_contracts import (
        HOST_ROUTE_REQUEST_SCHEMA_VERSION,
        HostRouteRequest,
        host_route_request_fingerprint,
        normalize_host_route_request,
    )

    request = HostRouteRequest(
        request_summary="  Continue the LibRPA screening run  ",
        host=" Codex ",
        host_session_id=" host-turn-1 ",
        project_root=" F:/AI_Workspace/Theoretical-Physics ",
        current_path=" research/librpa/run.py ",
        repo_id=" theoretical-physics ",
        branch=" main ",
        visible_files=("research/librpa/run.py", "README.md", "README.md"),
        explicit_topic_ids=("topic-b", "topic-a", "topic-a"),
        explicit_session_ids=("session-b", "session-a"),
        exact_refs=("claim:claim-b", "claim:claim-a", "claim:claim-a"),
        semantic_assessment={"research_relevant": True, "confidence": 0.9},
    )

    normalized = normalize_host_route_request(request)

    assert normalized.schema_version == HOST_ROUTE_REQUEST_SCHEMA_VERSION
    assert normalized.request_summary == "Continue the LibRPA screening run"
    assert normalized.host == "codex"
    assert normalized.host_session_id == "host-turn-1"
    assert normalized.visible_files == ("README.md", "research/librpa/run.py")
    assert normalized.explicit_topic_ids == ("topic-a", "topic-b")
    assert normalized.explicit_session_ids == ("session-a", "session-b")
    assert normalized.exact_refs == ("claim:claim-a", "claim:claim-b")
    with pytest.raises(TypeError):
        normalized.semantic_assessment["research_relevant"] = False
    with pytest.raises(FrozenInstanceError):
        normalized.host = "other"

    reordered = HostRouteRequest(
        request_summary="Continue the LibRPA screening run",
        host="codex",
        host_session_id="host-turn-1",
        project_root="F:/AI_Workspace/Theoretical-Physics",
        current_path="research/librpa/run.py",
        repo_id="theoretical-physics",
        branch="main",
        visible_files=("README.md", "research/librpa/run.py"),
        explicit_topic_ids=("topic-a", "topic-b"),
        explicit_session_ids=("session-a", "session-b"),
        exact_refs=("claim:claim-a", "claim:claim-b"),
        semantic_assessment={"confidence": 0.9, "research_relevant": True},
    )
    assert host_route_request_fingerprint(normalized) == host_route_request_fingerprint(
        reordered
    )


def test_host_route_request_rejects_hidden_pin_and_unbounded_transcript():
    from brain.v5.host_route_contracts import HostRouteRequest, normalize_host_route_request

    with pytest.raises(ValueError, match="dynamic routing cannot include a pinned session"):
        normalize_host_route_request(
            HostRouteRequest(
                request_summary="Continue the calculation",
                routing_mode="dynamic",
                pinned_session_id="session-a",
            )
        )
    with pytest.raises(TypeError):
        HostRouteRequest(
            request_summary="Continue the calculation",
            transcript="full conversation",
        )


def _strong_route_coverage(**overrides):
    from brain.v5.host_route_contracts import HostRouteCoverage

    values = {
        "checked_families": ("sessions", "topics"),
        "not_shown_families": (),
        "not_checked_families": (),
        "malformed_count": 0,
        "read_errors": (),
        "truncated": False,
        "index_status": "fresh",
        "index_generation": 7,
        "canonical_watermark": "a" * 64,
        "scope_fresh": True,
        "strong_selection_eligible": True,
    }
    values.update(overrides)
    return HostRouteCoverage(**values)


def _route_candidate(topic_id="topic-a", session_id="session-a", **overrides):
    from brain.v5.host_route_contracts import HostRouteCandidate

    values = {
        "topic_id": topic_id,
        "session_id": session_id,
        "score": 1000,
        "evidence_tier": "explicit",
        "component_scores": {"explicit_session": 1000},
        "reason_codes": ("explicit_session",),
        "exact_refs": (f"topic:{topic_id}", f"session:{session_id}"),
    }
    values.update(overrides)
    return HostRouteCandidate(**values)


def test_selected_route_decision_is_bounded_exact_and_trust_neutral():
    from brain.v5.host_route_contracts import (
        HOST_ROUTE_DECISION_SCHEMA_VERSION,
        HostRouteDecision,
        route_decision_payload,
    )

    candidate = _route_candidate()
    decision = HostRouteDecision(
        status="selected",
        request_fingerprint="b" * 64,
        candidates=(candidate,),
        coverage=_strong_route_coverage(),
        selected_topic_id="topic-a",
        selected_session_id="session-a",
        reason_codes=("unique_explicit_session",),
        recommended_next_operation="enter_selected_session",
    )

    payload = route_decision_payload(decision)

    assert payload["schema_version"] == HOST_ROUTE_DECISION_SCHEMA_VERSION
    assert payload["status"] == "selected"
    assert payload["selected_topic_id"] == "topic-a"
    assert payload["selected_session_id"] == "session-a"
    assert len(payload["candidates"]) == 1
    assert payload["coverage"]["strong_selection_eligible"] is True
    assert payload["orientation_only"] is True
    assert payload["summary_inputs_trusted"] is False
    assert payload["canonical_write_allowed"] is False
    assert payload["can_update_kernel_state"] is False
    assert payload["can_update_claim_trust"] is False
    assert payload["trust_effect"] == "none"
    assert "request_summary" not in payload

    with pytest.raises(ValueError, match="canonical_write_allowed must be false"):
        replace(decision, canonical_write_allowed=True)


def test_selected_route_requires_strong_coverage_and_matching_candidate():
    from brain.v5.host_route_contracts import HostRouteDecision

    candidate = _route_candidate()
    blocked = _strong_route_coverage(
        read_errors=("sessions index read failed",),
        strong_selection_eligible=False,
    )
    with pytest.raises(ValueError, match="selected routes require strong coverage"):
        HostRouteDecision(
            status="selected",
            request_fingerprint="c" * 64,
            candidates=(candidate,),
            coverage=blocked,
            selected_topic_id="topic-a",
            selected_session_id="session-a",
            reason_codes=("candidate_not_verified",),
            recommended_next_operation="repair_coverage",
        )

    with pytest.raises(ValueError, match="selected route must match a primary candidate"):
        HostRouteDecision(
            status="selected",
            request_fingerprint="d" * 64,
            candidates=(candidate,),
            coverage=_strong_route_coverage(),
            selected_topic_id="topic-b",
            selected_session_id="session-b",
            reason_codes=("candidate_mismatch",),
            recommended_next_operation="enter_selected_session",
        )


def test_route_decision_preserves_ambiguity_and_limits_candidate_cards():
    from brain.v5.host_route_contracts import HostRouteDecision

    candidates = tuple(
        _route_candidate(f"topic-{index}", f"session-{index}", score=1000 - index)
        for index in range(4)
    )
    with pytest.raises(ValueError, match="at most 3 candidates"):
        HostRouteDecision(
            status="ambiguous",
            request_fingerprint="e" * 64,
            candidates=candidates,
            coverage=_strong_route_coverage(),
            reason_codes=("multiple_primary_candidates",),
            recommended_next_operation="choose_candidate",
        )

    ambiguous = HostRouteDecision(
        status="ambiguous",
        request_fingerprint="f" * 64,
        candidates=candidates[:2],
        coverage=_strong_route_coverage(),
        reason_codes=("multiple_primary_candidates",),
        recommended_next_operation="choose_candidate",
    )
    assert ambiguous.selected_topic_id == ""
    assert ambiguous.selected_session_id == ""
    assert ambiguous.canonical_write_allowed is False


def test_supporting_route_candidate_requires_target_revalidation():
    with pytest.raises(ValueError, match="supporting candidates require target revalidation"):
        _route_candidate(
            "topic-b",
            "session-b",
            evidence_tier="supporting_scope",
            supporting_only=True,
            requires_target_revalidation=False,
        )


def test_route_decision_payload_round_trip_rejects_authority_tampering():
    from brain.v5.host_route_contracts import (
        HostRouteDecision,
        host_route_decision_from_payload,
        route_decision_payload,
        validate_host_route_decision_payload,
    )

    decision = HostRouteDecision(
        status="selected",
        request_fingerprint="1" * 64,
        candidates=(_route_candidate(),),
        coverage=_strong_route_coverage(),
        selected_topic_id="topic-a",
        selected_session_id="session-a",
        reason_codes=("unique_explicit_session",),
        recommended_next_operation="enter_selected_session",
    )
    payload = json.loads(json.dumps(route_decision_payload(decision)))

    assert validate_host_route_decision_payload(payload) == ()
    assert host_route_decision_from_payload(payload) == decision

    payload["canonical_write_allowed"] = True
    issues = validate_host_route_decision_payload(payload)
    assert any("canonical_write_allowed must be false" in issue for issue in issues)
    with pytest.raises(ValueError, match="canonical_write_allowed must be false"):
        host_route_decision_from_payload(payload)
