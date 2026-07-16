from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace

import pytest


def _seed_workspace(tmp_path):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "target", context_id="formal-theory", title="Target topic")
    claim = create_claim(
        ws,
        topic_id="target",
        statement="The finite calculation is controlled in the stated scope.",
        evidence_profile="formal_theory",
        confidence_state="conditional",
        active_uncertainty="The asymptotic regime remains open.",
    )
    bind_session(
        ws,
        "session-1",
        topic_id="target",
        context_id="formal-theory",
        active_claim=claim.claim_id,
    )
    return ws, claim


def _request(**overrides):
    from brain.v5.context_injection_events import ContextInjectionRequest

    values = {
        "event_id": "event-1",
        "event_type": "PromptSubmit",
        "host": "codex",
        "host_session_id": "host-session-1",
        "session_id": "session-1",
        "topic_id": "target",
        "context_profile": "auto",
        "research_relevant": True,
        "host_supports_session_start": False,
        "objective_text": "Continue the finite calculation.",
        "families": ("claims",),
    }
    values.update(overrides)
    return ContextInjectionRequest(**values)


def _receipt_payload(ws, receipt):
    path = ws.base / receipt.runtime_path
    return path, json.loads(path.read_text(encoding="utf-8"))


def test_first_relevant_turn_uses_startup_budget_without_persisting_context(tmp_path):
    from brain.v5.context_injection_events import prepare_context_injection

    ws, _claim = _seed_workspace(tmp_path)
    delivered: list[str] = []

    receipt = prepare_context_injection(ws, _request(), deliver=delivered.append)

    assert receipt.logical_event_type == "ResearchTurnStart"
    assert receipt.context_profile == "startup_orientation"
    assert receipt.injection_status == "injected"
    assert receipt.max_tokens == 800
    assert receipt.max_bytes == 4000
    assert receipt.estimated_tokens <= 800
    assert receipt.byte_count <= 4000
    assert len(delivered) == 1
    assert delivered[0]
    assert receipt.content_sha256
    path, persisted = _receipt_payload(ws, receipt)
    assert path.as_posix().endswith(f"/{receipt.namespace_sha256[:2]}/{receipt.namespace_sha256}.json")
    assert persisted == asdict(receipt)
    assert "markdown" not in persisted
    assert "content" not in persisted
    assert delivered[0] not in path.read_text(encoding="utf-8")


def test_same_effective_request_is_idempotent_and_not_reinjected(tmp_path):
    from brain.v5.context_injection_events import prepare_context_injection

    ws, _claim = _seed_workspace(tmp_path)
    delivered: list[str] = []
    request = _request()

    first = prepare_context_injection(ws, request, deliver=delivered.append)
    second = prepare_context_injection(ws, request, deliver=delivered.append)

    assert second == first
    assert len(delivered) == 1


def test_prepared_receipt_can_be_delivered_exactly_once_on_replay(tmp_path):
    from brain.v5.context_injection_events import prepare_context_injection

    ws, _claim = _seed_workspace(tmp_path)
    request = _request()
    prepared = prepare_context_injection(ws, request)
    delivered: list[str] = []

    injected = prepare_context_injection(ws, request, deliver=delivered.append)
    replay = prepare_context_injection(ws, request, deliver=delivered.append)

    assert prepared.injection_status == "prepared"
    assert injected.injection_status == "injected"
    assert injected.receipt_id != prepared.receipt_id
    assert injected.previous_receipt_id
    assert replay == injected
    assert len(delivered) == 1


def test_callback_failure_is_delivery_uncertain_until_host_acknowledges_retry(tmp_path):
    from brain.v5.context_injection_events import (
        ContextInjectionDeliveryUncertainError,
        acknowledge_context_injection_delivery,
        context_injection_receipt_path,
        prepare_context_injection,
    )

    ws, _claim = _seed_workspace(tmp_path)
    request = _request()
    effects: list[str] = []

    def uncertain_delivery(content):
        effects.append(content)
        raise RuntimeError("host failed after accepting content")

    with pytest.raises(RuntimeError, match="host failed"):
        prepare_context_injection(ws, request, deliver=uncertain_delivery)
    path = context_injection_receipt_path(ws, request, "startup_orientation")
    started = json.loads(path.read_text(encoding="utf-8"))
    assert started["injection_status"] == "delivery_started"
    assert started["delivery_attempt_id"]

    with pytest.raises(ContextInjectionDeliveryUncertainError):
        prepare_context_injection(ws, request, deliver=effects.append)
    assert len(effects) == 1

    prepared = acknowledge_context_injection_delivery(
        ws,
        request,
        delivery_attempt_id=started["delivery_attempt_id"],
        delivered=False,
    )
    completed = prepare_context_injection(ws, request, deliver=effects.append)

    assert prepared.injection_status == "prepared"
    assert completed.injection_status == "injected"
    assert len(effects) == 2


def test_concurrent_replay_delivers_once_and_returns_one_receipt(tmp_path):
    from brain.v5.context_injection_events import prepare_context_injection

    ws, _claim = _seed_workspace(tmp_path)
    delivered: list[str] = []
    request = _request()

    with ThreadPoolExecutor(max_workers=8) as pool:
        receipts = list(
            pool.map(
                lambda _index: prepare_context_injection(
                    ws,
                    request,
                    deliver=delivered.append,
                ),
                range(8),
            )
        )

    assert len({receipt.receipt_id for receipt in receipts}) == 1
    assert len(delivered) == 1


def test_setup_and_greetings_do_not_consume_first_research_turn(tmp_path):
    from brain.v5.context_injection_events import prepare_context_injection

    ws, _claim = _seed_workspace(tmp_path)
    ignored = prepare_context_injection(
        ws,
        _request(
            event_id="setup-1",
            research_relevant=False,
            objective_text="Configure the plugin.",
        ),
    )
    first = prepare_context_injection(ws, _request(event_id="research-1"))
    second = prepare_context_injection(ws, _request(event_id="research-2"))

    assert ignored.injection_status == "ignored_not_research_relevant"
    assert ignored.context_profile == "none"
    assert ignored.byte_count == 0
    assert first.context_profile == "startup_orientation"
    assert first.logical_event_type == "ResearchTurnStart"
    assert second.context_profile == "normal_research"
    assert second.logical_event_type == "PromptSubmit"


def test_native_session_start_uses_startup_then_prompt_uses_normal(tmp_path):
    from brain.v5.context_injection_events import prepare_context_injection

    ws, _claim = _seed_workspace(tmp_path)
    started = prepare_context_injection(
        ws,
        _request(
            event_id="session-start",
            event_type="SessionStart",
            host_supports_session_start=True,
            context_profile="startup_orientation",
        ),
    )
    continued = prepare_context_injection(
        ws,
        _request(
            event_id="prompt-1",
            host_supports_session_start=True,
            context_profile="normal_research",
        ),
    )

    assert started.context_profile == "startup_orientation"
    assert started.logical_event_type == "SessionStart"
    assert continued.context_profile == "normal_research"


@pytest.mark.parametrize(
    ("profile", "tokens", "bytes_limit"),
    [
        ("startup_orientation", 801, 4000),
        ("startup_orientation", 800, 4001),
        ("normal_research", 1501, 7500),
        ("normal_research", 1500, 7501),
    ],
)
def test_host_cannot_raise_named_profile_budgets(tmp_path, profile, tokens, bytes_limit):
    from brain.v5.context_injection_events import prepare_context_injection

    ws, _claim = _seed_workspace(tmp_path)
    event_type = "SessionStart" if profile == "startup_orientation" else "PromptSubmit"
    supports_start = True

    with pytest.raises(ValueError, match="profile budget"):
        prepare_context_injection(
            ws,
            _request(
                event_type=event_type,
                host_supports_session_start=supports_start,
                context_profile=profile,
                max_tokens=tokens,
                max_bytes=bytes_limit,
            ),
        )


def test_host_may_request_smaller_profile_budgets(tmp_path):
    from brain.v5.context_injection_events import prepare_context_injection

    ws, _claim = _seed_workspace(tmp_path)
    receipt = prepare_context_injection(
        ws,
        _request(max_tokens=320, max_bytes=1800),
    )

    assert receipt.max_tokens == 320
    assert receipt.max_bytes == 1800
    assert receipt.estimated_tokens <= 320
    assert receipt.byte_count <= 1800


def test_explicit_profile_cannot_override_lifecycle_semantics(tmp_path):
    from brain.v5.context_injection_events import prepare_context_injection

    ws, _claim = _seed_workspace(tmp_path)

    with pytest.raises(ValueError, match="lifecycle-selected profile"):
        prepare_context_injection(
            ws,
            _request(context_profile="normal_research"),
        )


def test_namespace_separates_workspace_host_topic_focus_profile_and_event(tmp_path):
    from brain.v5.context_injection_events import context_injection_receipt_path

    ws_a, _claim = _seed_workspace(tmp_path / "a")
    ws_b, _claim_b = _seed_workspace(tmp_path / "b")
    base = _request()
    cases = [
        (ws_a, base, "startup_orientation"),
        (ws_b, base, "startup_orientation"),
        (ws_a, replace(base, host="claude-code"), "startup_orientation"),
        (ws_a, replace(base, topic_id="other"), "startup_orientation"),
        (ws_a, replace(base, focus_set_ref="focus_set:focus-a"), "startup_orientation"),
        (ws_a, base, "normal_research"),
        (ws_a, replace(base, event_id="event-2"), "startup_orientation"),
    ]

    paths = [context_injection_receipt_path(ws, request, profile) for ws, request, profile in cases]

    assert len(set(paths)) == len(paths)
    for path, (_ws, request, _profile) in zip(paths, cases, strict=True):
        rendered = path.as_posix()
        assert request.host not in rendered
        assert request.host_session_id not in rendered
        assert request.event_id not in rendered


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("host", "../codex", "safe logical identifier"),
        ("event_id", r"folder\\event", "safe logical identifier"),
        ("session_id", "C:/absolute", "safe logical identifier"),
        ("topic_id", "CON", "reserved filesystem name"),
        ("host", "cafe\u0301", "NFC-normalized"),
        ("event_id", "x" * 257, "at most 256 UTF-8 bytes"),
        ("focus_set_ref", "focus_set:../escape", "safe logical identifier"),
    ],
)
def test_request_rejects_path_like_ambiguous_and_unnormalized_identifiers(field, value, message):
    values = {field: value}
    with pytest.raises(ValueError, match=message):
        _request(**values)


def test_receipt_path_rejects_runtime_symlink_escape(tmp_path):
    from brain.v5.context_injection_events import context_injection_receipt_path

    ws, _claim = _seed_workspace(tmp_path / "workspace")
    root = ws.root / "runtime" / "context_injections"
    outside = tmp_path / "outside"
    outside.mkdir()
    if root.exists():
        root.rmdir()
    try:
        os.symlink(outside, root, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlinks are unavailable")

    with pytest.raises(ValueError, match="escapes AITP runtime"):
        context_injection_receipt_path(ws, _request(), "startup_orientation")


def test_receipt_captures_effective_lineage_scope_tokens_refs_and_no_trust(tmp_path):
    from brain.v5.context_injection_events import prepare_context_injection

    ws, claim = _seed_workspace(tmp_path)
    claim_ref = f"claim:{claim.claim_id}"
    receipt = prepare_context_injection(ws, _request(exact_refs=(claim_ref,)))

    assert receipt.base_index_generation >= 1
    assert receipt.base_index_content_hash
    assert receipt.delta_generation >= 0
    assert receipt.canonical_watermark
    assert "claims" in receipt.selected_family_state_tokens
    assert "claims" in receipt.selected_family_content_tokens
    assert claim_ref in receipt.exact_refs
    assert claim_ref in receipt.selected_record_refs
    assert receipt.checked_scope["primary_topic_id"] == "target"
    assert receipt.checked_scope["checked_families"]
    assert receipt.trust_effect == "none"
    assert receipt.can_update_kernel_state is False
    assert receipt.can_update_claim_trust is False
    assert receipt.summary_inputs_trusted is False


def test_changed_selected_family_token_creates_new_receipt_and_preserves_history(tmp_path):
    from brain.v5.context_injection_events import prepare_context_injection
    from brain.v5.workspace import create_claim

    ws, _claim = _seed_workspace(tmp_path)
    request = _request()
    first = prepare_context_injection(ws, request)
    create_claim(
        ws,
        topic_id="target",
        statement="A second selected-family statement changes the effective scope token.",
        evidence_profile="formal_theory",
        confidence_state="open",
        active_uncertainty="It is not yet connected to the active derivation.",
    )

    second = prepare_context_injection(ws, request)

    assert second.receipt_id != first.receipt_id
    assert second.selected_family_content_tokens["claims"] != first.selected_family_content_tokens["claims"]
    assert second.previous_receipt_id == first.receipt_id
    history_path = ws.root / "runtime" / "context_injections" / "history" / first.receipt_id.split(":")[-1][:2] / f"{first.receipt_id.split(':')[-1]}.json"
    assert json.loads(history_path.read_text(encoding="utf-8")) == asdict(first)


def test_content_cycle_uses_unique_receipt_instances_and_preserves_every_revision(tmp_path):
    from brain.v5.context_injection_events import prepare_context_injection

    ws, _claim = _seed_workspace(tmp_path)
    requests = [
        _request(objective_text="Inspect assumption A."),
        _request(objective_text="Inspect assumption B."),
        _request(objective_text="Inspect assumption A."),
        _request(objective_text="Inspect assumption C."),
    ]

    receipts = [prepare_context_injection(ws, request) for request in requests]

    assert len({receipt.receipt_id for receipt in receipts}) == 4
    assert receipts[0].content_fingerprint == receipts[2].content_fingerprint
    assert [receipt.receipt_revision for receipt in receipts] == [1, 2, 3, 4]
    for receipt in receipts[:-1]:
        digest = receipt.receipt_id.rsplit(":", 1)[-1]
        history = ws.root / "runtime" / "context_injections" / "history" / digest[:2] / f"{digest}.json"
        assert json.loads(history.read_text(encoding="utf-8"))["receipt_id"] == receipt.receipt_id


def test_ignored_content_cycle_uses_the_same_monotonic_history_contract(tmp_path):
    from brain.v5.context_injection_events import prepare_context_injection

    ws, _claim = _seed_workspace(tmp_path)
    requests = [
        _request(research_relevant=False, objective_text="Setup A."),
        _request(research_relevant=False, objective_text="Setup B."),
        _request(research_relevant=False, objective_text="Setup A."),
        _request(research_relevant=False, objective_text="Setup C."),
    ]

    receipts = [prepare_context_injection(ws, request) for request in requests]

    assert len({receipt.receipt_id for receipt in receipts}) == 4
    assert receipts[0].content_fingerprint == receipts[2].content_fingerprint
    assert [receipt.receipt_revision for receipt in receipts] == [1, 2, 3, 4]
    assert all(receipt.injection_status == "ignored_not_research_relevant" for receipt in receipts)


def test_unrelated_process_family_write_does_not_reinject(tmp_path):
    from brain.v5.context_injection_events import prepare_context_injection
    from brain.v5.query_index import current_canonical_watermark
    from brain.v5.tools import record_tool_run

    ws, claim = _seed_workspace(tmp_path)
    delivered: list[str] = []
    request = _request()
    first = prepare_context_injection(ws, request, deliver=delivered.append)
    before_watermark = current_canonical_watermark(ws)
    record_tool_run(
        ws,
        recipe_id="diagnostic-recipe",
        tool_family="local",
        tool_name="diagnostic",
        topic_id="target",
        claim_id=claim.claim_id,
        inputs={"step": 1},
        outputs={"status": "observed"},
        evidence_status="unreviewed",
        lane="diagnostic",
    )
    after_watermark = current_canonical_watermark(ws)

    second = prepare_context_injection(ws, request, deliver=delivered.append)

    assert after_watermark != before_watermark
    assert second == first
    assert len(delivered) == 1


def test_changed_context_content_creates_new_receipt_even_with_same_event(tmp_path):
    from brain.v5.context_injection_events import prepare_context_injection

    ws, _claim = _seed_workspace(tmp_path)
    first = prepare_context_injection(ws, _request(objective_text="Inspect assumption A."))
    second = prepare_context_injection(ws, _request(objective_text="Inspect assumption B."))

    assert second.receipt_id != first.receipt_id
    assert second.content_sha256 != first.content_sha256
    assert second.previous_receipt_id == first.receipt_id


def test_corrupt_existing_receipt_fails_closed(tmp_path):
    from brain.v5.context_injection_events import (
        ContextInjectionError,
        context_injection_receipt_path,
        prepare_context_injection,
    )

    ws, _claim = _seed_workspace(tmp_path)
    receipt = prepare_context_injection(ws, _request())
    path = context_injection_receipt_path(ws, _request(), receipt.context_profile)
    path.write_text('{"corrupt": true}\n', encoding="utf-8")

    with pytest.raises(ContextInjectionError, match="existing context injection receipt"):
        prepare_context_injection(ws, _request())
    assert path.read_text(encoding="utf-8") == '{"corrupt": true}\n'


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda payload: payload.update(runtime_path="../../escape.json"), "runtime_path"),
        (lambda payload: payload.update(base_index_generation=999), "payload SHA-256"),
        (lambda payload: payload.pop("max_tokens"), "field set"),
        (lambda payload: payload.update(context_text="full secret context"), "field set"),
    ],
)
def test_legal_shape_receipt_tampering_fails_closed(tmp_path, mutation, message):
    from brain.v5.context_injection_events import ContextInjectionError, prepare_context_injection

    ws, _claim = _seed_workspace(tmp_path)
    request = _request()
    receipt = prepare_context_injection(ws, request)
    path, payload = _receipt_payload(ws, receipt)
    mutation(payload)
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ContextInjectionError, match=message):
        prepare_context_injection(ws, request)


@pytest.mark.parametrize("failure_write", [2, 3])
def test_receipt_replay_repairs_interrupted_first_turn_state(
    tmp_path,
    monkeypatch,
    failure_write,
):
    import brain.v5.context_injection_storage as storage
    from brain.v5.context_injection_events import prepare_context_injection

    ws, _claim = _seed_workspace(tmp_path)
    request = _request(event_id=f"first-{failure_write}")
    original = storage.write_text_atomic
    calls = 0
    failed = False

    def fail_once(path, text):
        nonlocal calls, failed
        calls += 1
        if calls == failure_write and not failed:
            failed = True
            raise OSError(f"failpoint write {failure_write}")
        return original(path, text)

    monkeypatch.setattr(storage, "write_text_atomic", fail_once)
    with pytest.raises(OSError, match="failpoint"):
        prepare_context_injection(ws, request)
    monkeypatch.setattr(storage, "write_text_atomic", original)

    repaired = prepare_context_injection(ws, request)
    continued = prepare_context_injection(ws, _request(event_id=f"next-{failure_write}"))

    assert repaired.context_profile == "startup_orientation"
    assert continued.context_profile == "normal_research"


def test_shared_hook_protocol_validates_receipt_without_granting_trust(tmp_path):
    from brain.v5.context_injection_events import prepare_context_injection
    from brain.v5.hook_protocol_contracts import (
        context_injection_protocol,
        require_valid_context_injection_receipt,
    )

    ws, _claim = _seed_workspace(tmp_path)
    receipt = prepare_context_injection(ws, _request())
    protocol = context_injection_protocol()

    assert protocol["entrypoint"] == "brain.v5.context_injection_events.prepare_context_injection"
    assert protocol["acknowledgement_entrypoint"] == (
        "brain.v5.context_injection_events.acknowledge_context_injection_delivery"
    )
    assert protocol["profiles"] == {
        "startup_orientation": {"max_tokens": 800, "max_bytes": 4000},
        "normal_research": {"max_tokens": 1500, "max_bytes": 7500},
    }
    assert protocol["first_relevant_turn_fallback"] is True
    assert protocol["receipt_contains_full_context"] is False
    assert protocol["delivery_statuses"] == [
        "prepared",
        "delivery_started",
        "injected",
        "ignored_not_research_relevant",
    ]
    assert protocol["uncertain_delivery_requires_acknowledgement"] is True
    assert protocol["can_update_claim_trust"] is False
    assert require_valid_context_injection_receipt(asdict(receipt)) == asdict(receipt)


def test_receipt_contract_rejects_claim_trust_authority(tmp_path):
    from brain.v5.context_injection_events import prepare_context_injection
    from brain.v5.contracts import ContractError
    from brain.v5.hook_protocol_contracts import require_valid_context_injection_receipt

    ws, _claim = _seed_workspace(tmp_path)
    payload = asdict(prepare_context_injection(ws, _request()))
    payload["can_update_claim_trust"] = True

    with pytest.raises(ContractError):
        require_valid_context_injection_receipt(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("max_tokens", "800"),
        ("base_index_generation", "1"),
        ("estimated_tokens", float("nan")),
        ("checked_scope", {"unjsonable": {"value"}}),
        ("context_profile", []),
        ("context_profile", {}),
        ("injection_status", []),
        ("injection_status", {}),
    ],
)
def test_public_receipt_validator_returns_contract_errors_for_malformed_types(
    tmp_path,
    field,
    value,
):
    from brain.v5.context_injection_events import prepare_context_injection
    from brain.v5.hook_protocol_contracts import validate_context_injection_receipt

    ws, _claim = _seed_workspace(tmp_path)
    payload = asdict(prepare_context_injection(ws, _request()))
    payload[field] = value

    result = validate_context_injection_receipt(payload)

    assert result.ok is False
    assert result.issues


def test_public_receipt_validator_handles_mixed_type_unknown_keys(tmp_path):
    from brain.v5.context_injection_events import prepare_context_injection
    from brain.v5.hook_protocol_contracts import validate_context_injection_receipt

    ws, _claim = _seed_workspace(tmp_path)
    payload = asdict(prepare_context_injection(ws, _request()))
    payload[1] = "unexpected"
    payload["unexpected"] = "unexpected"

    result = validate_context_injection_receipt(payload)

    assert result.ok is False
    assert result.issues


def test_public_receipt_validator_fails_closed_if_validator_raises(monkeypatch):
    import brain.v5.context_injection_events as context_injection_events
    from brain.v5.hook_protocol_contracts import validate_context_injection_receipt

    def fail_validation(_payload):
        raise RuntimeError("validator failure")

    monkeypatch.setattr(
        context_injection_events,
        "validate_context_injection_receipt_payload",
        fail_validation,
    )

    result = validate_context_injection_receipt({})

    assert result.ok is False
    assert result.issues[0].message == "receipt validation failed safely"
