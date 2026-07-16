'Runtime hook protocol contracts for AITP v5 adapter packets.'

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/hook_protocol_contracts/part_01.py",
    "_compat_shards/hook_protocol_contracts/part_02.py",
    ),
)
del _load_module_shards


def context_injection_protocol() -> dict:
    """Return the host-neutral, trust-neutral context injection contract."""

    from brain.v5.context_injection_events import CONTEXT_INJECTION_PROFILE_BUDGETS

    return {
        "entrypoint": "brain.v5.context_injection_events.prepare_context_injection",
        "acknowledgement_entrypoint": (
            "brain.v5.context_injection_events.acknowledge_context_injection_delivery"
        ),
        "profiles": {
            profile: dict(budget)
            for profile, budget in CONTEXT_INJECTION_PROFILE_BUDGETS.items()
        },
        "first_relevant_turn_fallback": True,
        "receipt_contains_full_context": False,
        "delivery_statuses": [
            "prepared",
            "delivery_started",
            "injected",
            "ignored_not_research_relevant",
        ],
        "uncertain_delivery_requires_acknowledgement": True,
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def validate_context_injection_receipt(
    payload: dict,
    *,
    path: str = "context_injection_receipt",
):
    """Validate the shared runtime receipt without granting trust authority."""

    from brain.v5.context_injection_events import (
        validate_context_injection_receipt_payload,
    )
    from brain.v5.contracts import ContractResult

    result = ContractResult()
    try:
        errors = validate_context_injection_receipt_payload(payload)
    except Exception:  # noqa: BLE001 - malformed host input must fail closed.
        result.add(path, "receipt validation failed safely")
        return result
    for error in errors:
        result.add(path, error)
    return result


def require_valid_context_injection_receipt(payload: dict) -> dict:
    """Return a valid context injection receipt or raise ContractError."""

    from brain.v5.contracts import ContractError

    result = validate_context_injection_receipt(payload)
    if not result.ok:
        raise ContractError(result)
    return payload
