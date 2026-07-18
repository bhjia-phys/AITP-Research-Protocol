from __future__ import annotations

import json
from datetime import datetime, timezone


def _seed_workspace(tmp_path):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg-notes", context_id="replica", title="Replica notes")
    claim = create_claim(
        ws,
        topic_id="qg-notes",
        statement="The finite replica construction has a bounded interpretation.",
        evidence_profile="formal_derivation",
        confidence_state="hypothesis",
        active_uncertainty="analytic continuation remains open",
    )
    bind_session(
        ws,
        "session-1",
        topic_id="qg-notes",
        context_id="replica",
        runtime="codex",
        active_claim=claim.claim_id,
    )
    return ws, claim


def _semantic_request(claim_id: str, *, apply: bool = True) -> dict:
    return {
        "apply": apply,
        "event": {
            "event_id": "moment-event-1",
            "event_type": "RouteChanged",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "host": "codex",
            "host_session_id": "codex-session-1",
            "session_id": "session-1",
            "topic_id": "qg-notes",
            "subject_refs": [f"claim:{claim_id}"],
            "objective_payload": {},
            "semantic_payload": {
                "candidate_kind": "interpretation",
                "semantic_key": "finite replica boundary",
                "summary": "Preserve the finite-replica interpretation for review.",
                "payload": {"boundary": "finite replica number only"},
            },
            "source_event_id": "native-post-tool-1",
            "recursion_origin": "host_native",
        },
    }


def test_process_research_moment_decides_and_applies_one_review_gated_event(tmp_path):
    from copy import deepcopy

    import pytest

    from brain.v5.contracts import ContractError
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.record_envelope import RecordActor
    from brain.v5.research_moment_facade import process_research_moment_request

    ws, claim = _seed_workspace(tmp_path)
    payload = process_research_moment_request(
        ws,
        _semantic_request(claim.claim_id),
        actor=RecordActor(actor_type="model", actor_id="moment-test", host="pytest"),
    )

    assert payload["kind"] == "research_moment_process_result"
    assert payload["decision"]["outcome"] == "stage_semantic_candidate"
    assert payload["applied"] is True
    assert payload["receipt"]["status"] == "staged"
    assert len(payload["receipt"]["staging_refs"]) == 1
    assert payload["trust_effect"] == "none"
    assert payload["can_update_claim_trust"] is False
    assert require_valid_public_surface("research_moment_process_result", payload) == payload

    drifted = deepcopy(payload)
    drifted["state_effect"] = "read_only"
    with pytest.raises(ContractError):
        require_valid_public_surface("research_moment_process_result", drifted)


def test_decide_only_research_moment_performs_no_runtime_or_canonical_write(tmp_path):
    from brain.v5.query_index import current_canonical_watermark
    from brain.v5.record_envelope import RecordActor
    from brain.v5.research_moment_facade import process_research_moment_request

    ws, claim = _seed_workspace(tmp_path)
    before = current_canonical_watermark(ws)
    payload = process_research_moment_request(
        ws,
        _semantic_request(claim.claim_id, apply=False),
        actor=RecordActor(actor_type="model", actor_id="moment-test", host="pytest"),
    )

    assert payload["applied"] is False
    assert payload["receipt"] is None
    assert payload["state_effect"] == "read_only"
    assert current_canonical_watermark(ws) == before
    assert not (ws.root / "runtime" / "research_moments").exists()


def test_research_moment_mcp_and_file_backed_cli_share_the_same_surface(
    tmp_path, capsys
):
    from brain.v5.cli import main
    from brain.v5.mcp_research_moments import aitp_v5_process_research_moment
    from brain.v5.public_surfaces import require_valid_public_surface

    _ws, claim = _seed_workspace(tmp_path)
    request = _semantic_request(claim.claim_id, apply=False)
    mcp_payload = aitp_v5_process_research_moment(
        str(tmp_path),
        request_json=json.dumps(request),
    )
    request_path = tmp_path / "research-moment.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")

    assert main(
        [
            "--base",
            str(tmp_path),
            "research-moment",
            "process",
            "--request-json-file",
            str(request_path),
        ]
    ) == 0
    cli_payload = json.loads(capsys.readouterr().out)

    assert cli_payload == mcp_payload
    assert require_valid_public_surface("research_moment_process_result", cli_payload) == cli_payload
