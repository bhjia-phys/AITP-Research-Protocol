"""Shared type for built-in and workspace domain packs."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DomainPackRecord:
    pack_id: str
    domain: str
    description: str
    suggested_question_intents: list[str] = field(default_factory=list)
    risk_signals: list[str] = field(default_factory=list)
    workflow_graph: dict = field(default_factory=dict)
    failure_taxonomy: list[dict] = field(default_factory=list)
    lane_policy: dict = field(default_factory=dict)
    artifact_schema: dict = field(default_factory=dict)
    hpc_interpretation: dict = field(default_factory=dict)
    context_profile_refs: list[str] = field(default_factory=list)
    tool_recipes: list[str] = field(default_factory=list)
    tool_executor_recommendations: list[dict] = field(default_factory=list)
    skill_refs: list[dict] = field(default_factory=list)
    manifest_refs: list[dict] = field(default_factory=list)
    integration_boundary: str = (
        "Domain packs and external skills are orientation and execution guidance only; "
        "typed kernel records remain the authority for evidence, validation, memory, and trust."
    )
    trust_card_templates: list[str] = field(default_factory=list)
    truth_standard_policy: str = "global_only"
    kind: str = "domain_pack"
