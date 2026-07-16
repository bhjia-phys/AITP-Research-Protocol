from __future__ import annotations

from dataclasses import asdict, replace

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="literature-discovery-test", host="pytest")


def _setup_discovery(tmp_path):
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.proof_obligations import create_proof_obligation
    from brain.v5.recall_audit import RecallRequest, run_recall_audit
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(
        ws,
        "quantum-gravity-von-neumann",
        context_id="formal-theory",
        title="Quantum gravity and von Neumann algebras",
    )
    claim = create_claim(
        ws,
        topic_id="quantum-gravity-von-neumann",
        statement="Replica wormhole saddles require an exact source and convention comparison.",
        evidence_profile="literature_synthesis",
        confidence_state="learning",
        active_uncertainty="The semiclassical regime and operator-algebra assumptions are unclear.",
        scope="Semiclassical gravity with replica boundary conditions.",
        strongest_failure_mode="Mixing inequivalent ensemble and fixed-theory frameworks.",
    )
    obligation = create_proof_obligation(
        ws,
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        statement="Locate primary and review sources that state the replica-wormhole assumptions.",
        obligation_type="source_scope_gap",
        status="open",
        maturity_level="exploratory",
        next_action="Run a bounded literature discovery after exhaustive local recall.",
        required_evidence=["primary paper", "review with exact equation and caveat anchors"],
        failure_modes=["wrong framework", "search snippet mistaken for source support"],
    )
    bind_session(
        ws,
        "qg-session",
        topic_id=claim.topic_id,
        context_id="formal-theory",
        active_claim=claim.claim_id,
    )
    audit = run_recall_audit(
        ws,
        RecallRequest(
            session_id="qg-session",
            query_text="replica wormhole assumptions primary source review",
            normalized_intent="identify_missing_literature",
            required_families=("claims", "proof_obligations", "source_assets", "reference_locations"),
            top_k=20,
        ),
        actor=_actor(),
    )
    return (
        ws,
        claim,
        obligation,
        audit,
        pin_current_record(ws, f"proof_obligation:{obligation.obligation_id}"),
        pin_current_record(ws, f"recall_audit:{audit.audit_id}"),
    )


def _spec(
    gap_pin,
    audit_pin,
    *,
    framework="quantum_gravity",
    max_results=10,
    ttl_seconds=600,
):
    from brain.v5.literature_discovery import LiteratureDiscoverySpec

    return LiteratureDiscoverySpec(
        gap_ref=gap_pin,
        prior_audit_ref=audit_pin,
        framework=framework,
        regime="semiclassical replica saddles",
        focus_terms=("replica wormhole", "von Neumann algebra", "ensemble average"),
        required_source_types=("primary_paper", "review"),
        connector_allowlist=("quantum_gravity_literature", "qft_literature", "ima"),
        max_results=max_results,
        timeout_seconds=30,
        ttl_seconds=ttl_seconds,
    )


def test_discovery_request_requires_persisted_gap_and_recall_and_is_repeatable(tmp_path):
    from brain.v5.literature_discovery import build_literature_discovery_request
    from brain.v5.query_index import current_canonical_watermark

    ws, claim, obligation, audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    before = current_canonical_watermark(ws)

    first = build_literature_discovery_request(ws, _spec(gap_pin, audit_pin))
    second = build_literature_discovery_request(ws, _spec(gap_pin, audit_pin))

    assert first.request_id == second.request_id
    assert first.dedup_fingerprint == second.dedup_fingerprint
    assert first.topic_id == claim.topic_id
    assert first.claim_id == claim.claim_id
    assert first.gap_ref == gap_pin
    assert first.prior_audit_ref == audit_pin
    assert first.program_id == audit.program_id
    assert first.focus_set_ref == audit.focus_set_ref
    assert obligation.statement in first.normalized_query
    assert "quantum gravity" in first.normalized_query.lower()
    assert first.query_expansions
    assert first.max_results == 10
    assert first.timeout_seconds == 30
    assert first.expires_at > first.created_at
    assert first.orientation_only is True
    assert first.summary_inputs_trusted is False
    assert first.can_update_kernel_state is False
    assert first.can_update_claim_trust is False
    assert first.can_create_source_asset is False
    assert current_canonical_watermark(ws) == before


def test_discovery_request_rejects_wrong_framework_for_persisted_gap(tmp_path):
    from brain.v5.literature_discovery import build_literature_discovery_request

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)

    with pytest.raises(ValueError, match="framework.*persisted gap"):
        build_literature_discovery_request(
            ws,
            _spec(gap_pin, audit_pin, framework="condensed_matter"),
        )


def test_discovery_request_rejects_non_gap_ref_and_superseded_audit(tmp_path):
    from brain.v5.literature_discovery import build_literature_discovery_request
    from brain.v5.pinned_record_refs import pin_current_record

    ws, claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    claim_pin = pin_current_record(ws, f"claim:{claim.claim_id}")

    with pytest.raises(ValueError, match="ProofObligationRecord"):
        build_literature_discovery_request(ws, _spec(claim_pin, audit_pin))
    with pytest.raises(ValueError, match="exact current pin"):
        build_literature_discovery_request(
            ws,
            _spec(gap_pin, replace(audit_pin, content_hash="0" * 64)),
        )


def test_discovery_request_rejects_audit_after_required_family_changes(tmp_path):
    from brain.v5.literature_discovery import build_literature_discovery_request
    from brain.v5.source_assets import register_source_asset

    ws, claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    register_source_asset(
        ws,
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        asset_type="paper",
        uri="https://example.test/new-after-audit",
        title="New metadata-only source after recall",
        metadata={
            "acquisition_state": "metadata_only",
            "shelf_eligible": False,
        },
    )

    with pytest.raises(ValueError, match="stale.*source_assets"):
        build_literature_discovery_request(ws, _spec(gap_pin, audit_pin))


def test_discovery_request_requires_recall_over_all_local_source_families(tmp_path):
    from brain.v5.literature_discovery import build_literature_discovery_request
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.recall_audit import RecallRequest, run_recall_audit

    ws, _claim, _obligation, _audit, gap_pin, _audit_pin = _setup_discovery(tmp_path)
    narrow_audit = run_recall_audit(
        ws,
        RecallRequest(
            session_id="qg-session",
            query_text="replica wormhole assumptions primary source review",
            normalized_intent="identify_missing_literature",
            required_families=("claims",),
            top_k=20,
        ),
        actor=_actor(),
    )
    narrow_pin = pin_current_record(ws, f"recall_audit:{narrow_audit.audit_id}")

    with pytest.raises(ValueError, match="recall.*required families"):
        build_literature_discovery_request(ws, _spec(gap_pin, narrow_pin))


def test_normalize_discovery_result_deduplicates_and_preserves_partial_coverage(tmp_path):
    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )
    from brain.v5.query_index import current_canonical_watermark

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    request = build_literature_discovery_request(ws, _spec(gap_pin, audit_pin))
    before = current_canonical_watermark(ws)
    connector_result = {
        "connector_results": [
            {
                "connector_id": "quantum_gravity_literature",
                "status": "ok",
                "coverage": {"query_count": 2, "pages_checked": 1},
                "results": [
                    {
                        "doi": "https://doi.org/10.1000/REPLICA.1",
                        "title": "Replica Wormholes and the Black Hole Interior",
                        "authors": ["A. Researcher", "B. Physicist"],
                        "year": 2024,
                        "uri": "https://doi.org/10.1000/REPLICA.1",
                        "framework": "quantum_gravity",
                        "source_type": "primary_paper",
                        "snippet": "Search-result orientation only.",
                        "access_disposition": "open_access",
                    },
                    {
                        "arxiv_id": "2401.00001v2",
                        "title": "Restricted Replica Review",
                        "authors": "C. Reviewer",
                        "year": "2024",
                        "uri": "https://arxiv.org/abs/2401.00001",
                        "framework": "quantum_gravity",
                        "source_type": "review",
                        "access_disposition": "license_denied",
                    },
                ],
                "errors": [],
            },
            {
                "connector_id": "qft_literature",
                "status": "partial",
                "coverage": {"query_count": 2, "pages_checked": 0},
                "results": [
                    {
                        "doi": "10.1000/replica.1",
                        "title": "Replica Wormholes and the Black Hole Interior",
                        "authors": ["A. Researcher"],
                        "year": 2024,
                        "uri": "https://example.test/duplicate",
                        "framework": "quantum_gravity",
                        "source_type": "primary_paper",
                    },
                    {
                        "doi": "10.1000/wrong.1",
                        "title": "A Lattice Condensed Matter Result",
                        "authors": ["D. Other"],
                        "year": 2023,
                        "framework": "condensed_matter",
                        "source_type": "primary_paper",
                    },
                ],
                "errors": ["second query timed out"],
            },
            {
                "connector_id": "ima",
                "status": "failed",
                "coverage": {"query_count": 1, "pages_checked": 0},
                "results": [],
                "errors": ["backend unavailable"],
            },
        ]
    }

    receipt = normalize_literature_discovery_result(request, connector_result)

    assert receipt.status == "partial"
    assert receipt.raw_result_count == 4
    assert receipt.candidate_count == 2
    assert receipt.eligible_candidate_count == 1
    assert receipt.duplicate_count == 1
    assert receipt.excluded_count == 1
    assert receipt.truncated is False
    assert len(receipt.connector_coverage) == 3
    assert {item.status for item in receipt.connector_coverage} == {"ok", "partial", "failed"}
    assert "second query timed out" in receipt.errors
    assert "backend unavailable" in receipt.errors
    primary = next(item for item in receipt.candidates if item.doi)
    restricted = next(item for item in receipt.candidates if item.arxiv_id)
    assert primary.doi == "10.1000/replica.1"
    assert primary.connector_ids == ("qft_literature", "quantum_gravity_literature")
    assert primary.snippet == "Search-result orientation only."
    assert primary.acquisition_eligible is True
    assert restricted.acquisition_eligible is False
    assert restricted.exclusion_reason == "license_denied"
    assert receipt.excluded_candidates[0].reason == "framework_mismatch"
    assert receipt.excluded_candidates[0].connector_id == "qft_literature"
    assert receipt.orientation_only is True
    assert receipt.can_create_source_asset is False
    assert receipt.can_update_claim_trust is False
    assert current_canonical_watermark(ws) == before


def test_normalize_discovery_result_enforces_global_budget(tmp_path):
    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    request = build_literature_discovery_request(
        ws,
        _spec(gap_pin, audit_pin, max_results=2),
    )
    results = [
        {
            "doi": f"10.1000/result.{index}",
            "title": f"Replica result {index}",
            "authors": ["A. Author"],
            "year": 2024,
            "framework": "quantum_gravity",
            "source_type": "primary_paper",
            "access_disposition": "open_access",
        }
        for index in range(4)
    ]

    receipt = normalize_literature_discovery_result(
        request,
        {
            "connector_results": [
                {
                    "connector_id": "quantum_gravity_literature",
                    "status": "ok",
                    "coverage": {"query_count": 1},
                    "results": results,
                    "errors": [],
                }
            ]
        },
    )

    assert receipt.raw_result_count == 4
    assert receipt.candidate_count == 2
    assert receipt.truncated is True
    assert receipt.budget_dropped_count == 2


def test_normalize_discovery_result_rejects_expired_or_unallowed_connector(tmp_path):
    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    request = build_literature_discovery_request(ws, _spec(gap_pin, audit_pin))

    with pytest.raises(ValueError, match="expired"):
        normalize_literature_discovery_result(
            replace(
                request,
                created_at="1999-01-01T00:00:00+00:00",
                expires_at="1999-01-01T00:10:00+00:00",
            ),
            {"connector_results": []},
        )
    receipt = normalize_literature_discovery_result(
        request,
        {
            "connector_results": [
                {
                    "connector_id": "not-allowed",
                    "status": "ok",
                    "coverage": {},
                    "results": [],
                    "errors": [],
                }
            ]
        },
    )
    assert receipt.status == "failed"
    assert receipt.candidate_count == 0
    assert any("not-allowed" in error for error in receipt.errors)


def test_discovery_receipt_reports_missing_requested_connectors(tmp_path):
    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    request = build_literature_discovery_request(ws, _spec(gap_pin, audit_pin))

    receipt = normalize_literature_discovery_result(
        request,
        {
            "connector_results": [
                {
                    "connector_id": "quantum_gravity_literature",
                    "status": "ok",
                    "coverage": {"query_count": 1},
                    "results": [
                        {
                            "doi": "10.1000/partial-coverage.1",
                            "title": "One connector returned a candidate",
                            "authors": ["A. Author"],
                            "year": 2024,
                            "framework": "quantum_gravity",
                            "source_type": "primary_paper",
                            "access_disposition": "open_access",
                        }
                    ],
                    "errors": [],
                }
            ]
        },
    )

    assert receipt.status == "partial"
    assert {item.connector_id for item in receipt.connector_coverage} == set(
        request.connector_allowlist
    )
    missing = [item for item in receipt.connector_coverage if item.status == "failed"]
    assert {item.connector_id for item in missing} == {"ima", "qft_literature"}
    assert all("did not return" in item.errors[0] for item in missing)


def test_complete_discovery_receipt_cannot_claim_global_absence(tmp_path):
    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    spec = replace(
        _spec(gap_pin, audit_pin),
        connector_allowlist=("quantum_gravity_literature",),
    )
    request = build_literature_discovery_request(ws, spec)
    receipt = normalize_literature_discovery_result(
        request,
        {
            "connector_results": [
                {
                    "connector_id": "quantum_gravity_literature",
                    "status": "ok",
                    "coverage": {"query_count": 1},
                    "results": [],
                    "errors": [],
                }
            ]
        },
    )

    assert receipt.status == "complete"
    assert receipt.candidate_count == 0
    assert receipt.can_claim_no_result is False
    assert receipt.orientation_only is True


def test_discovery_receipt_binds_request_instance_and_freezes_coverage(tmp_path):
    import json
    from datetime import UTC, datetime, timedelta

    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )
    from brain.v5.literature_discovery_contracts import (
        literature_discovery_request_integrity,
    )

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    first = build_literature_discovery_request(ws, _spec(gap_pin, audit_pin))
    shifted_at = datetime.now(UTC) + timedelta(seconds=1)
    second = replace(
        first,
        created_at=shifted_at.isoformat(),
        expires_at=(shifted_at + timedelta(seconds=first.ttl_seconds)).isoformat(),
        request_integrity_hash=literature_discovery_request_integrity(
            dedup_fingerprint=first.dedup_fingerprint,
            created_at=shifted_at.isoformat(),
            expires_at=(shifted_at + timedelta(seconds=first.ttl_seconds)).isoformat(),
        ),
    )
    result = {
        "connector_results": [
            {
                "connector_id": "quantum_gravity_literature",
                "status": "ok",
                "coverage": {"queries": ["replica wormhole"]},
                "results": [],
                "errors": [],
            }
        ]
    }
    first_receipt = normalize_literature_discovery_result(
        first,
        result,
    )
    second_receipt = normalize_literature_discovery_result(
        second,
        result,
    )

    assert first.request_id == second.request_id
    assert first_receipt.receipt_id != second_receipt.receipt_id
    assert first_receipt.request_integrity_hash == first.request_integrity_hash
    for item in first_receipt.connector_coverage:
        with pytest.raises(TypeError):
            item.coverage["new"] = True
    coverage = next(
        item.coverage
        for item in first_receipt.connector_coverage
        if item.connector_id == "quantum_gravity_literature"
    )
    with pytest.raises(TypeError):
        coverage["queries"].append("mutated")
    json.dumps(asdict(first_receipt))


def test_discovery_requires_nonempty_coverage_and_enforces_execution_timeout(tmp_path):
    from datetime import UTC, datetime, timedelta

    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )
    from brain.v5.literature_discovery_contracts import (
        literature_discovery_request_integrity,
    )

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    spec = replace(
        _spec(gap_pin, audit_pin),
        connector_allowlist=("quantum_gravity_literature",),
    )
    request = build_literature_discovery_request(ws, spec)
    empty_coverage = normalize_literature_discovery_result(
        request,
        {
            "connector_results": [
                {
                    "connector_id": "quantum_gravity_literature",
                    "status": "ok",
                    "coverage": {},
                    "results": [],
                    "errors": [],
                }
            ]
        },
    )
    assert empty_coverage.status == "failed"
    assert any("coverage must describe" in error for error in empty_coverage.errors)

    zero_queries = normalize_literature_discovery_result(
        request,
        {
            "connector_results": [
                {
                    "connector_id": "quantum_gravity_literature",
                    "status": "ok",
                    "coverage": {"query_count": 0},
                    "results": [],
                    "errors": [],
                }
            ]
        },
    )
    assert zero_queries.status == "failed"
    assert any("positive query_count" in error for error in zero_queries.errors)

    created_at = datetime.now(UTC) - timedelta(seconds=request.timeout_seconds + 1)
    expires_at = created_at + timedelta(seconds=request.ttl_seconds)
    stale_execution = replace(
        request,
        created_at=created_at.isoformat(),
        expires_at=expires_at.isoformat(),
        request_integrity_hash=literature_discovery_request_integrity(
            dedup_fingerprint=request.dedup_fingerprint,
            created_at=created_at.isoformat(),
            expires_at=expires_at.isoformat(),
        ),
    )
    with pytest.raises(ValueError, match="execution timeout"):
        normalize_literature_discovery_result(stale_execution, {"connector_results": []})


def test_discovery_request_revalidates_host_boundary_fields(tmp_path):
    from brain.v5.literature_discovery import build_literature_discovery_request
    from brain.v5.literature_discovery_contracts import validate_literature_discovery_request

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    request = build_literature_discovery_request(ws, _spec(gap_pin, audit_pin))

    with pytest.raises(ValueError, match="program_id"):
        validate_literature_discovery_request(replace(request, program_id=None))
    with pytest.raises(ValueError, match="unsupported source type"):
        validate_literature_discovery_request(
            replace(request, required_source_types=("social_media",))
        )
    with pytest.raises(ValueError, match="unknown connector"):
        validate_literature_discovery_request(
            replace(request, connector_allowlist=("arbitrary-host-tool",))
        )
    with pytest.raises(ValueError, match="fingerprint"):
        validate_literature_discovery_request(
            replace(request, topic_id="foreign-topic")
        )


def test_discovery_request_binds_ttl_and_instance_timestamps(tmp_path):
    from datetime import UTC, datetime, timedelta

    from brain.v5.literature_discovery import build_literature_discovery_request
    from brain.v5.literature_discovery_contracts import validate_literature_discovery_request

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    short = build_literature_discovery_request(
        ws,
        _spec(gap_pin, audit_pin, ttl_seconds=600),
    )
    long = build_literature_discovery_request(
        ws,
        _spec(gap_pin, audit_pin, ttl_seconds=1200),
    )
    assert short.request_id != long.request_id

    future = datetime.now(UTC) + timedelta(days=1)
    with pytest.raises(ValueError, match="integrity|timestamp|future"):
        validate_literature_discovery_request(
            replace(
                short,
                created_at=future.isoformat(),
                expires_at=(future + timedelta(seconds=600)).isoformat(),
            )
        )


def test_discovery_spec_rejects_oversized_request_metadata(tmp_path):
    from brain.v5.literature_discovery_contracts import validate_literature_discovery_spec

    _ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    spec = _spec(gap_pin, audit_pin)

    invalid = (
        (replace(spec, regime="r" * 501), "regime.*500"),
        (replace(spec, focus_terms=tuple(f"term-{index}" for index in range(33))), "focus_terms.*32"),
        (replace(spec, focus_terms=("f" * 201,)), "focus_terms.*200"),
        (
            replace(spec, required_source_types=("primary_paper",) * 9),
            "required_source_types.*8",
        ),
        (
            replace(spec, connector_allowlist=("qft_literature",) * 17),
            "connector_allowlist.*16",
        ),
    )
    for candidate, message in invalid:
        with pytest.raises(ValueError, match=message):
            validate_literature_discovery_spec(candidate)


def test_discovery_request_rejects_oversized_query_metadata(tmp_path):
    from brain.v5.literature_discovery import build_literature_discovery_request
    from brain.v5.literature_discovery_contracts import validate_literature_discovery_request

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    request = build_literature_discovery_request(ws, _spec(gap_pin, audit_pin))

    invalid = (
        (replace(request, normalized_query="q" * 2001), "normalized_query.*2000"),
        (replace(request, query_expansions=("one", "two", "three", "four")), "query_expansions.*3"),
        (replace(request, query_expansions=("q" * 2001,)), "query_expansions.*2000"),
        (replace(request, regime="r" * 501), "regime.*500"),
        (
            replace(request, focus_terms=tuple(f"term-{index}" for index in range(33))),
            "focus_terms.*32",
        ),
    )
    for candidate, message in invalid:
        with pytest.raises(ValueError, match=message):
            validate_literature_discovery_request(candidate)


def test_normalize_discovery_result_rejects_tampered_request_budget(tmp_path):
    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    request = build_literature_discovery_request(ws, _spec(gap_pin, audit_pin))

    with pytest.raises(ValueError, match="max_results|fingerprint"):
        normalize_literature_discovery_result(
            replace(request, max_results=10_000),
            {"connector_results": []},
        )


def test_discovery_candidate_with_unchecked_access_requires_acquisition_review(tmp_path):
    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    request = build_literature_discovery_request(ws, _spec(gap_pin, audit_pin))
    receipt = normalize_literature_discovery_result(
        request,
        {
            "connector_results": [
                {
                    "connector_id": "quantum_gravity_literature",
                    "status": "ok",
                    "coverage": {"query_count": 1},
                    "results": [
                        {
                            "doi": "10.1000/unverified.1",
                            "title": "Unverified access candidate",
                            "authors": ["A. Author"],
                            "year": 2024,
                            "framework": "quantum_gravity",
                            "source_type": "primary_paper",
                        }
                    ],
                    "errors": [],
                }
            ]
        },
    )

    assert receipt.candidate_count == 1
    assert receipt.eligible_candidate_count == 0
    assert receipt.candidates[0].acquisition_eligible is False
    assert receipt.candidates[0].exclusion_reason == "access_not_verified"


def test_discovery_title_only_candidate_cannot_enter_acquisition(tmp_path):
    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    request = build_literature_discovery_request(ws, _spec(gap_pin, audit_pin))
    receipt = normalize_literature_discovery_result(
        request,
        {
            "connector_results": [
                {
                    "connector_id": "quantum_gravity_literature",
                    "status": "ok",
                    "coverage": {"query_count": 1},
                    "results": [
                        {
                            "title": "A title-only literature lead",
                            "authors": ["A. Author"],
                            "year": 2024,
                            "framework": "quantum_gravity",
                            "source_type": "primary_paper",
                            "access_disposition": "open_access",
                        }
                    ],
                    "errors": [],
                }
            ]
        },
    )

    assert receipt.candidate_count == 1
    assert receipt.eligible_candidate_count == 0
    assert receipt.candidates[0].dedup_key.startswith("title:")
    assert receipt.candidates[0].acquisition_eligible is False
    assert receipt.candidates[0].exclusion_reason == "stable_locator_not_verified"


def test_discovery_public_records_are_serializable(tmp_path):
    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    request = build_literature_discovery_request(ws, _spec(gap_pin, audit_pin))
    receipt = normalize_literature_discovery_result(
        request,
        {"connector_results": []},
    )

    assert asdict(request)["gap_ref"]["record_ref"].startswith("proof_obligation:")
    assert asdict(receipt)["request_id"] == request.request_id


def test_discovery_rejects_oversized_connector_result_without_iterating_it(tmp_path):
    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    request = build_literature_discovery_request(ws, _spec(gap_pin, audit_pin))
    oversized = [
        {
            "doi": f"10.1000/oversized.{index}",
            "title": f"Oversized result {index}",
            "framework": "quantum_gravity",
            "source_type": "primary_paper",
        }
        for index in range(1001)
    ]

    receipt = normalize_literature_discovery_result(
        request,
        {
            "connector_results": [
                {
                    "connector_id": "quantum_gravity_literature",
                    "status": "ok",
                    "coverage": {"query_count": 1},
                    "results": oversized,
                    "errors": [],
                }
            ]
        },
    )

    observed = next(
        item
        for item in receipt.connector_coverage
        if item.connector_id == "quantum_gravity_literature"
    )
    assert observed.status == "failed"
    assert observed.raw_result_count == 1001
    assert receipt.candidate_count == 0
    assert any("result budget" in error for error in receipt.errors)


def test_discovery_normalization_is_independent_of_result_order(tmp_path):
    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    request = build_literature_discovery_request(ws, _spec(gap_pin, audit_pin))
    first = {
        "doi": "10.1000/order.1",
        "title": "Zeta title",
        "authors": ["Z. Author"],
        "framework": "quantum_gravity",
        "source_type": "primary_paper",
        "access_disposition": "not_checked",
    }
    second = {
        "doi": "10.1000/order.1",
        "title": "Alpha title",
        "authors": ["A. Author"],
        "framework": "quantum_gravity",
        "source_type": "primary_paper",
        "access_disposition": "open_access",
    }

    def normalize(results):
        return normalize_literature_discovery_result(
            request,
            {
                "connector_results": [
                    {
                        "connector_id": "quantum_gravity_literature",
                        "status": "ok",
                        "coverage": {"query_count": 1},
                        "results": results,
                        "errors": [],
                    }
                ]
            },
        )

    forward = normalize([first, second])
    reverse = normalize([second, first])

    assert forward.receipt_id == reverse.receipt_id
    assert forward.candidates == reverse.candidates
    assert forward.excluded_candidates == reverse.excluded_candidates
    assert forward.connector_coverage == reverse.connector_coverage
    assert forward.errors == reverse.errors


def test_discovery_fails_closed_for_malformed_mapping_uri_and_identifiers(tmp_path):
    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )

    class ExplodingMapping(dict):
        def get(self, *_args, **_kwargs):
            raise RuntimeError("host mapping exploded")

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    request = build_literature_discovery_request(ws, _spec(gap_pin, audit_pin))

    with pytest.raises(TypeError, match="plain JSON object"):
        normalize_literature_discovery_result(
            request,
            ExplodingMapping(connector_results=[]),
        )

    receipt = normalize_literature_discovery_result(
        request,
        {
            "connector_results": [
                {
                    "connector_id": "quantum_gravity_literature",
                    "status": "ok",
                    "coverage": {},
                    "results": [
                        {
                            "title": "Malformed URI candidate",
                            "uri": "https://[invalid-host",
                            "framework": "quantum_gravity",
                            "source_type": "primary_paper",
                        },
                        {
                            "title": "Pseudo DOI candidate",
                            "doi": "javascript:alert(1)",
                            "framework": "quantum_gravity",
                            "source_type": "primary_paper",
                        },
                        {
                            "title": "Pseudo arXiv candidate",
                            "arxiv_id": "javascript:alert(2)",
                            "framework": "quantum_gravity",
                            "source_type": "review",
                        },
                    ],
                    "errors": [],
                }
            ]
        },
    )

    assert receipt.candidate_count == 0
    assert {item.reason for item in receipt.excluded_candidates} == {
        "invalid_identifier",
        "unsafe_uri_scheme",
    }


def test_discovery_normalizer_rejects_non_request_before_reading_expiry():
    from brain.v5.literature_discovery import normalize_literature_discovery_result

    with pytest.raises(TypeError, match="request must be LiteratureDiscoveryRequest"):
        normalize_literature_discovery_result(object(), {})


def test_discovery_normalizer_rejects_non_plain_host_lists(tmp_path):
    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )

    class ExplodingList(list):
        def __len__(self):
            raise RuntimeError("host list length exploded")

        def __getitem__(self, _key):
            raise RuntimeError("host list indexing exploded")

        def __iter__(self):
            raise RuntimeError("host list iteration exploded")

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    request = build_literature_discovery_request(ws, _spec(gap_pin, audit_pin))

    with pytest.raises(ValueError, match="connector_results.*plain JSON list"):
        normalize_literature_discovery_result(
            request,
            {"connector_results": ExplodingList()},
        )

    receipt = normalize_literature_discovery_result(
        request,
        {
            "connector_results": [
                {
                    "connector_id": "quantum_gravity_literature",
                    "status": "ok",
                    "coverage": {},
                    "results": ExplodingList(),
                    "errors": [],
                }
            ]
        },
    )
    assert receipt.status == "failed"
    assert any("results must be a plain JSON list" in error for error in receipt.errors)


def test_discovery_normalizer_contains_hostile_nested_containers(tmp_path):
    from collections.abc import Mapping

    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )

    class ExplodingCoverage(Mapping):
        def __getitem__(self, _key):
            raise RuntimeError("coverage read exploded")

        def __iter__(self):
            raise RuntimeError("coverage iteration exploded")

        def __len__(self):
            raise RuntimeError("coverage length exploded")

        def __eq__(self, _other):
            raise RuntimeError("coverage equality exploded")

    class ExplodingAuthors(list):
        def __getitem__(self, _key):
            raise RuntimeError("authors indexing exploded")

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    spec = replace(
        _spec(gap_pin, audit_pin),
        connector_allowlist=("quantum_gravity_literature",),
    )
    request = build_literature_discovery_request(ws, spec)
    receipt = normalize_literature_discovery_result(
        request,
        {
            "connector_results": [
                {
                    "connector_id": "quantum_gravity_literature",
                    "status": "ok",
                    "coverage": ExplodingCoverage(),
                    "results": [
                        {
                            "doi": "10.1000/nested-host.1",
                            "title": "Nested hostile metadata",
                            "authors": ExplodingAuthors(),
                            "framework": "quantum_gravity",
                            "source_type": "primary_paper",
                            "access_disposition": "open_access",
                        }
                    ],
                    "errors": [],
                }
            ]
        },
    )

    assert receipt.candidate_count == 1
    assert receipt.candidates[0].authors == ()
    assert receipt.connector_coverage[0].coverage == {}
    assert "coverage must contain only JSON-compatible values" in receipt.errors


def test_discovery_normalizer_rejects_host_scalar_subclasses(tmp_path):
    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )

    class ExplodingString(str):
        def __getitem__(self, _key):
            raise RuntimeError("string slicing exploded")

    class ExplodingYear:
        def __int__(self):
            raise RuntimeError("year conversion exploded")

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    spec = replace(
        _spec(gap_pin, audit_pin),
        connector_allowlist=("quantum_gravity_literature",),
    )
    request = build_literature_discovery_request(ws, spec)
    receipt = normalize_literature_discovery_result(
        request,
        {
            "connector_results": [
                {
                    "connector_id": "quantum_gravity_literature",
                    "status": "ok",
                    "coverage": {"query_count": 1},
                    "results": [
                        {
                            "doi": "10.1000/host-scalar.1",
                            "title": "Safe title",
                            "year": ExplodingYear(),
                            "framework": "quantum_gravity",
                            "source_type": "primary_paper",
                        },
                        {
                            "doi": "10.1000/host-scalar.2",
                            "title": ExplodingString("host string"),
                            "framework": "quantum_gravity",
                            "source_type": "primary_paper",
                        },
                    ],
                    "errors": [ExplodingString("host diagnostic")],
                }
            ]
        },
    )

    assert receipt.candidate_count == 1
    assert receipt.candidates[0].year is None
    assert receipt.excluded_count == 1
    assert receipt.excluded_candidates[0].reason == "invalid_candidate"


def test_discovery_reports_oversized_connector_diagnostics_as_dropped(tmp_path):
    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    spec = replace(
        _spec(gap_pin, audit_pin),
        connector_allowlist=("quantum_gravity_literature",),
    )
    request = build_literature_discovery_request(ws, spec)
    errors = [f"connector diagnostic {index}" for index in range(205)]

    receipt = normalize_literature_discovery_result(
        request,
        {
            "connector_results": [
                {
                    "connector_id": "quantum_gravity_literature",
                    "status": "partial",
                    "coverage": {},
                    "results": [],
                    "errors": errors,
                }
            ]
        },
    )

    assert receipt.diagnostic_dropped_count == 205
    assert receipt.truncated is True
    assert any("error budget exceeded" in error for error in receipt.errors)


def test_discovery_candidate_rejects_unsafe_uri_scheme(tmp_path):
    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    request = build_literature_discovery_request(ws, _spec(gap_pin, audit_pin))

    receipt = normalize_literature_discovery_result(
        request,
        {
            "connector_results": [
                {
                    "connector_id": "quantum_gravity_literature",
                    "status": "ok",
                    "coverage": {"query_count": 1},
                    "results": [
                        {
                            "doi": "10.1000/unsafe-uri.1",
                            "title": "Unsafe external location",
                            "authors": ["A. Author"],
                            "year": 2024,
                            "uri": "javascript:alert(document.domain)",
                            "framework": "quantum_gravity",
                            "source_type": "primary_paper",
                            "access_disposition": "open_access",
                        }
                    ],
                    "errors": [],
                }
            ]
        },
    )

    assert receipt.candidate_count == 0
    assert receipt.eligible_candidate_count == 0
    assert receipt.excluded_candidates[0].reason == "unsafe_uri_scheme"


def test_discovery_rejects_overlong_identity_and_whitespace_uri(tmp_path):
    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    spec = replace(
        _spec(gap_pin, audit_pin),
        connector_allowlist=("quantum_gravity_literature",),
    )
    request = build_literature_discovery_request(ws, spec)
    receipt = normalize_literature_discovery_result(
        request,
        {
            "connector_results": [
                {
                    "connector_id": "quantum_gravity_literature",
                    "status": "ok",
                    "coverage": {"query_count": 1},
                    "results": [
                        {
                            "doi": "10.1000/" + "a" * 400,
                            "title": "Overlong DOI",
                            "framework": "quantum_gravity",
                            "source_type": "primary_paper",
                        },
                        {
                            "uri": "https://exa mple.com/paper",
                            "title": "Whitespace host",
                            "framework": "quantum_gravity",
                            "source_type": "primary_paper",
                            "access_disposition": "open_access",
                        },
                        {
                            "uri": "https://example.test/" + "p" * 2100,
                            "title": "Overlong URI",
                            "framework": "quantum_gravity",
                            "source_type": "primary_paper",
                        },
                    ],
                    "errors": [],
                }
            ]
        },
    )

    assert receipt.candidate_count == 0
    assert receipt.eligible_candidate_count == 0
    assert {item.reason for item in receipt.excluded_candidates} == {
        "invalid_identifier",
        "invalid_location",
        "unsafe_uri_scheme",
    }


def test_discovery_uri_dedup_preserves_case_sensitive_path(tmp_path):
    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    spec = replace(
        _spec(gap_pin, audit_pin),
        connector_allowlist=("quantum_gravity_literature",),
    )
    request = build_literature_discovery_request(ws, spec)
    base = {
        "title": "Case-sensitive URI candidate",
        "framework": "quantum_gravity",
        "source_type": "primary_paper",
        "access_disposition": "open_access",
    }
    receipt = normalize_literature_discovery_result(
        request,
        {
            "connector_results": [
                {
                    "connector_id": "quantum_gravity_literature",
                    "status": "ok",
                    "coverage": {"query_count": 1},
                    "results": [
                        {**base, "uri": "https://EXAMPLE.test/Paper"},
                        {**base, "uri": "https://example.test/paper"},
                    ],
                    "errors": [],
                }
            ]
        },
    )

    assert receipt.candidate_count == 2
    assert receipt.duplicate_count == 0
    assert {item.dedup_key for item in receipt.candidates} == {
        "uri:https://example.test/Paper",
        "uri:https://example.test/paper",
    }


def test_discovery_normalizes_non_json_connector_coverage_without_crashing(tmp_path):
    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    request = build_literature_discovery_request(ws, _spec(gap_pin, audit_pin))

    receipt = normalize_literature_discovery_result(
        request,
        {
            "connector_results": [
                {
                    "connector_id": "quantum_gravity_literature",
                    "status": "ok",
                    "coverage": {"pages": {1, 2}},
                    "results": [],
                    "errors": [],
                }
            ]
        },
    )

    assert receipt.connector_coverage[0].coverage == {}
    assert "coverage must contain only JSON-compatible values" in receipt.errors
    assert asdict(receipt)["request_id"] == request.request_id


@pytest.mark.parametrize(
    "coverage",
    (
        {"huge_integer": 1 << 100_000},
        {"k" * 501: 1},
        {f"key-{index}": index for index in range(1001)},
    ),
)
def test_discovery_rejects_coverage_outside_structural_scalar_budgets(
    tmp_path,
    coverage,
):
    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    request = build_literature_discovery_request(ws, _spec(gap_pin, audit_pin))
    receipt = normalize_literature_discovery_result(
        request,
        {
            "connector_results": [
                {
                    "connector_id": "quantum_gravity_literature",
                    "status": "ok",
                    "coverage": coverage,
                    "results": [],
                    "errors": [],
                }
            ]
        },
    )

    observed = next(
        item
        for item in receipt.connector_coverage
        if item.connector_id == "quantum_gravity_literature"
    )
    assert observed.coverage == {}
    assert "coverage must contain only JSON-compatible values" in receipt.errors


def test_discovery_materializes_nested_connector_coverage_as_plain_json(tmp_path):
    from types import MappingProxyType

    from brain.v5.literature_discovery import (
        build_literature_discovery_request,
        normalize_literature_discovery_result,
    )

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    request = build_literature_discovery_request(ws, _spec(gap_pin, audit_pin))

    receipt = normalize_literature_discovery_result(
        request,
        {
            "connector_results": [
                {
                    "connector_id": "quantum_gravity_literature",
                    "status": "ok",
                    "coverage": {
                        "queries": MappingProxyType({"pages": [1, 2]})
                    },
                    "results": [],
                    "errors": [],
                }
            ]
        },
    )

    observed = next(
        item
        for item in receipt.connector_coverage
        if item.connector_id == "quantum_gravity_literature"
    )
    assert observed.coverage == {
        "queries": {"pages": [1, 2]}
    }
    assert not any("JSON-compatible" in error for error in receipt.errors)
    assert asdict(receipt)["request_id"] == request.request_id


def test_discovery_request_reports_bounded_lifetime_error(tmp_path):
    from brain.v5.literature_discovery import build_literature_discovery_request
    from brain.v5.literature_discovery_contracts import validate_literature_discovery_request

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    request = build_literature_discovery_request(ws, _spec(gap_pin, audit_pin))

    with pytest.raises(ValueError, match="between 60 and 3600 seconds"):
        validate_literature_discovery_request(
            replace(request, expires_at="2999-01-01T00:00:00+00:00")
        )
