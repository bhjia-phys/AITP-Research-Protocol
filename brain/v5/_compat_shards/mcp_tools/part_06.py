# Compatibility shard 6 for mcp_tools.
from __future__ import annotations

def aitp_v5_apply_quiet_checkpoint_batch(
    base: str,
    *,
    session_id: str,
    claim_id: str = "",
    run_id: str = "",
    summary: str,
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    changed_files: list[str] | None = None,
    generated_artifacts: list[dict] | None = None,
    validation_commands: list[str] | None = None,
    durable_observations: list[str] | None = None,
    claim_boundary: dict | None = None,
    next_blockers: list[str] | None = None,
    artifact_specs: list[dict] | None = None,
    source_specs: list[dict] | None = None,
    tool_run_specs: list[dict] | None = None,
    sensemaking_summary: str = "",
    source_refs: list[str] | None = None,
) -> dict:
    """Apply a research-burst checkpoint batch without updating claim trust."""

    return require_valid_public_surface(
        "quiet_checkpoint_batch",
        apply_quiet_checkpoint_batch(
            _ws(base),
            session_id,
            claim_id=claim_id,
            run_id=run_id,
            summary=summary,
            inputs=inputs,
            outputs=outputs,
            changed_files=changed_files,
            generated_artifacts=generated_artifacts,
            validation_commands=validation_commands,
            durable_observations=durable_observations,
            claim_boundary=claim_boundary,
            next_blockers=next_blockers,
            artifact_specs=artifact_specs,
            source_specs=source_specs,
            tool_run_specs=tool_run_specs,
            sensemaking_summary=sensemaking_summary,
            source_refs=source_refs,
        ),
    )

def aitp_v5_create_promotion_packet(
    base: str, *, topic_id: str, claim_id: str, proposed_memory_kind: str = "scoped_claim",
    scope: str = "", evidence_refs: list[str] | None = None, non_claims: list[str] | None = None,
    known_failure_modes: list[str] | None = None, validation_result_ids: list[str] | None = None,
    failure_mode_review_checkpoint_id: str = "", failure_mode_review_result_id: str = "",
) -> dict:
    pkt = create_promotion_packet(_ws(base), topic_id=topic_id, claim_id=claim_id,
        proposed_memory_kind=proposed_memory_kind, scope=scope, evidence_refs=evidence_refs,
        validation_result_ids=validation_result_ids, non_claims=non_claims,
        known_failure_modes=known_failure_modes, failure_mode_review_checkpoint_id=failure_mode_review_checkpoint_id, failure_mode_review_result_id=failure_mode_review_result_id)
    return require_valid_public_surface("promotion_packet_record", {"ok": True, **asdict(pkt)})

def aitp_v5_apply_promotion_packet(
    base: str, *, packet_id: str, checkpoint_id: str,
) -> dict:
    entry = apply_promotion_packet(_ws(base), packet_id=packet_id, checkpoint_id=checkpoint_id)
    return require_valid_public_surface("memory_entry_record", {"ok": True, **asdict(entry)})

def aitp_v5_preflight_trust_update(
    base: str, *, action: str, session_id: str, topic_id: str, claim_id: str,
    requested_state: str = "", source_kind: str = "", source_ref: str = "",
    evidence_refs: list[str] | None = None, code_state_ids: list[str] | None = None,
    rationale: str = "", request_id: str = "", preflight_token: str = "",
) -> dict:
    return {"ok": True, **require_valid_public_surface("trust_update_preflight",
        preflight_trust_update(_ws(base), _trust_request(locals())))}

def aitp_v5_apply_trust_update(
    base: str, *, action: str, session_id: str, topic_id: str, claim_id: str,
    requested_state: str = "", source_kind: str = "", source_ref: str = "",
    evidence_refs: list[str] | None = None, code_state_ids: list[str] | None = None,
    rationale: str = "", request_id: str = "", preflight_token: str = "",
) -> dict:
    return {"ok": True, **require_valid_public_surface("trust_update_apply",
        apply_trust_update(_ws(base), _trust_request(locals())))}

def aitp_v5_get_trust_update_record(base: str, *, update_id: str) -> dict:
    record = get_trust_update_record(_ws(base), update_id)
    return require_valid_public_surface("trust_update_record", {"ok": True, **asdict(record)})

def _trust_request(ns: dict) -> TrustUpdateRequest:
    rid = ns.get("request_id") or f"trust-request-{ns['session_id']}-{ns['claim_id']}-{ns['action']}"
    return TrustUpdateRequest(request_id=rid, action=ns["action"], session_id=ns["session_id"],
        topic_id=ns["topic_id"], claim_id=ns["claim_id"], requested_state=ns.get("requested_state", ""),
        source_kind=ns.get("source_kind", ""), source_ref=ns.get("source_ref", ""),
        evidence_refs=ns.get("evidence_refs") or [], code_state_ids=ns.get("code_state_ids") or [],
        rationale=ns.get("rationale", ""), preflight_token=ns.get("preflight_token", ""))

def _linked_code_states(ws, claim_id: str) -> list[CodeStateRecord]:
    states = list_records(ws.registry_dir("code_states"), CodeStateRecord)
    return [s for s in states if _record_links_to_claim(s.linked_records, claim_id)]

def _record_links_to_claim(linked_records: dict, claim_id: str) -> bool:
    for value in linked_records.values():
        if value == claim_id or (isinstance(value, list) and claim_id in value):
            return True
    return False
