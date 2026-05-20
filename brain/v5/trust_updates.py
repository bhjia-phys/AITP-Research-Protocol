"""Trust-changing action preflight for AITP v5."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace

from brain.v5.models import ClaimRecord, CodeStateRecord, TrustUpdateRequest
from brain.v5.paths import WorkspacePaths
from brain.v5.policy import evaluate_policy
from brain.v5.store import list_records, write_record
from brain.v5.workspace import get_claim

_SUMMARY_SOURCE_KINDS = {
    "derived_summary",
    "summary_orientation",
    "task_plan",
    "findings",
    "progress",
}


def preflight_trust_update(ws: WorkspacePaths, request: TrustUpdateRequest) -> dict:
    """Check whether a trust-changing request may mutate kernel state.

    The preflight returns a typed policy payload only. It does not update the
    claim, confidence state, evidence ledger, validation state, or L2 memory.
    """

    claim = get_claim(ws, request.claim_id)
    code_states = _resolve_code_states(ws, claim, request.code_state_ids)
    source_kind = request.source_kind.strip().lower()
    decision = evaluate_policy(
        action=request.action,
        claim=claim,
        code_states=code_states,
        evidence_refs=request.evidence_refs,
        context={
            "source_kind": source_kind,
            "source_ref": request.source_ref,
            "orientation_only": source_kind in _SUMMARY_SOURCE_KINDS,
        },
    )
    policy_reasons = [asdict(reason) for reason in decision.reasons]
    code_state_ids = [state.code_state_id for state in code_states]
    proof = _preflight_proof(
        request,
        allowed=decision.allowed,
        policy_reasons=policy_reasons,
        required_actions=decision.required_actions,
        code_state_ids=code_state_ids,
    )
    return {
        "kind": "trust_update_preflight",
        "request": asdict(request),
        "request_id": request.request_id,
        "action": request.action,
        "session_id": request.session_id,
        "topic_id": request.topic_id,
        "claim_id": request.claim_id,
        "requested_state": request.requested_state,
        "allowed": decision.allowed,
        "mutation_allowed_after_preflight": decision.allowed,
        "policy_reasons": policy_reasons,
        "required_actions": decision.required_actions,
        "evidence_refs": list(request.evidence_refs),
        "code_state_ids": code_state_ids,
        "preflight_token": proof["token"],
        "preflight_proof": proof,
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
    }


def apply_trust_update(ws: WorkspacePaths, request: TrustUpdateRequest) -> dict:
    """Apply a trust-changing update only after policy preflight allows it."""

    preflight = preflight_trust_update(ws, request)
    claim = get_claim(ws, request.claim_id)
    if not preflight["allowed"]:
        return _apply_payload(
            request,
            preflight=preflight,
            applied=False,
            previous_state=claim.confidence_state,
            new_state=claim.confidence_state,
            required_actions=preflight["required_actions"],
        )
    if request.preflight_token != preflight["preflight_token"]:
        return _apply_payload(
            request,
            preflight=preflight,
            applied=False,
            previous_state=claim.confidence_state,
            new_state=claim.confidence_state,
            required_actions=["pass_matching_preflight_token"],
        )
    if request.action != "change_claim_confidence":
        return _apply_payload(
            request,
            preflight=preflight,
            applied=False,
            previous_state=claim.confidence_state,
            new_state=claim.confidence_state,
            required_actions=["unsupported_trust_update_action"],
        )
    if not request.requested_state:
        return _apply_payload(
            request,
            preflight=preflight,
            applied=False,
            previous_state=claim.confidence_state,
            new_state=claim.confidence_state,
            required_actions=["set_requested_state"],
        )

    updated = replace(claim, confidence_state=request.requested_state)
    _write_claim(ws, updated)
    return _apply_payload(
        request,
        preflight=preflight,
        applied=True,
        previous_state=claim.confidence_state,
        new_state=updated.confidence_state,
        required_actions=[],
    )


def _resolve_code_states(
    ws: WorkspacePaths,
    claim: ClaimRecord,
    requested_ids: list[str],
) -> list[CodeStateRecord]:
    states = list_records(ws.registry_dir("code_states"), CodeStateRecord)
    if requested_ids:
        wanted = set(requested_ids)
        return [state for state in states if state.code_state_id in wanted]
    return [state for state in states if _record_links_to_claim(state.linked_records, claim.claim_id)]


def _write_claim(ws: WorkspacePaths, claim: ClaimRecord) -> None:
    body = f"# Claim\n\n{claim.statement}\n"
    write_record(ws.registry_dir("claims") / f"{claim.claim_id}.md", claim, body=body)
    write_record(ws.topic_dir(claim.topic_id) / "claims" / "ledger" / f"{claim.claim_id}.md", claim, body=body)


def _apply_payload(
    request: TrustUpdateRequest,
    *,
    preflight: dict,
    applied: bool,
    previous_state: str,
    new_state: str,
    required_actions: list[str],
) -> dict:
    return {
        "kind": "trust_update_apply",
        "request": asdict(request),
        "request_id": request.request_id,
        "action": request.action,
        "session_id": request.session_id,
        "topic_id": request.topic_id,
        "claim_id": request.claim_id,
        "applied": applied,
        "previous_state": previous_state,
        "new_state": new_state,
        "required_actions": list(required_actions),
        "preflight": preflight,
        "preflight_token": request.preflight_token,
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    }


def _record_links_to_claim(linked_records: dict, claim_id: str) -> bool:
    for value in linked_records.values():
        if value == claim_id:
            return True
        if isinstance(value, list) and claim_id in value:
            return True
    return False


def _preflight_proof(
    request: TrustUpdateRequest,
    *,
    allowed: bool,
    policy_reasons: list[dict],
    required_actions: list[str],
    code_state_ids: list[str],
) -> dict:
    request_digest = _digest(_request_token_payload(request, code_state_ids))
    policy_digest = _digest({
        "allowed": allowed,
        "policy_reasons": policy_reasons,
        "required_actions": list(required_actions),
    })
    token_seed = f"{request_digest}|{policy_digest}"
    token = "trust-preflight-" + hashlib.sha256(token_seed.encode("utf-8")).hexdigest()[:24]
    return {
        "token": token,
        "request_id": request.request_id,
        "request_digest": request_digest,
        "policy_digest": policy_digest,
        "source": "trust_update_preflight",
    }


def _request_token_payload(request: TrustUpdateRequest, code_state_ids: list[str]) -> dict:
    payload = asdict(request)
    payload["preflight_token"] = ""
    payload["source_kind"] = payload["source_kind"].strip().lower()
    payload["code_state_ids"] = list(code_state_ids)
    return payload


def _digest(payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()
