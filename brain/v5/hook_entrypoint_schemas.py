"""Shared schemas for runtime hook entrypoint metadata."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


_PRE_TOOL_POLICY_INPUT_SCHEMA = {
    "required": ["session_id", "action", "claim_id", "risk_level"],
    "optional": [
        "evidence_refs",
        "code_state_ids",
        "validation_contract_ids",
        "source_kind",
        "source_ref",
        "orientation_only",
        "human_checkpoint_id",
    ],
    "risk_levels": ["fluid", "guided", "rigorous", "adversarial"],
    "truth_source": "typed_records",
    "summary_inputs_trusted": False,
}

_PRE_TOOL_EVENT_PLATFORM_SCHEMA = {
    "required": ["runtime", "session_id"],
    "hook_field": "hook_name_or_lifecycle_event",
    "tool_name_fields": ["tool_name", "tool.name"],
    "tool_input_fields": ["tool_input", "tool.input"],
    "tool_input_optional": [
        "claim_id",
        "evidence_refs",
        "code_state_ids",
        "validation_contract_ids",
        "packet",
        "source_kind",
        "source_ref",
        "orientation_only",
        "risk_level",
        "human_checkpoint_id",
        "checkpoint_id",
    ],
    "truth_source": "platform_event_for_routing_only",
    "summary_inputs_trusted": False,
}


def pre_tool_policy_input_schema() -> dict[str, Any]:
    return deepcopy(_PRE_TOOL_POLICY_INPUT_SCHEMA)


def pre_tool_event_platform_schema() -> dict[str, Any]:
    return deepcopy(_PRE_TOOL_EVENT_PLATFORM_SCHEMA)
