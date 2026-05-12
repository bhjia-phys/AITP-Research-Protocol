"""Safe topic-root resolution, slug validation, and stage/posture gate model.

Centralizes path contract so brain/mcp_server.py and hooks agree on
whether topics live at <topics_root>/<slug> or <topics_root>/topics/<slug>.
Also defines the L0/L1/L3 gate evaluation logic and StageSnapshot dataclass.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path, PurePath
from typing import Any, Callable


@dataclass(frozen=True)
class StageSnapshot:
    stage: str
    posture: str
    lane: str
    gate_status: str
    required_artifact_path: str = ""
    missing_requirements: list[str] = field(default_factory=list)
    next_allowed_transition: str = ""
    skill: str = "skill-continuous"
    l3_subplane: str = ""
    l3_mode: str = ""
    domain_prerequisites: list[str] = field(default_factory=list)
    domain_constraints: dict = field(default_factory=dict)
    l4_background_status: str = ""
    research_intensity: str = "standard"
    interaction_level: str = "collaborative"
    # Memory layer fields (v1.0)
    memory_gate_enabled: bool = False
    memory_status: str = "not_evaluated"
    memory_summary: str = ""
    # Retreat tracking (v1.1)
    retreated_from: str = ""
    retreated_to: str = ""
    retreat_reason: str = ""
    retreated_at: str = ""
    retreat_count: int = 0
    # L1 freshness tracking (v1.2)
    l1_feedback_status: str = ""  # "" = not evaluated, "has_feedback" or "missing"
    # Entry profile for L3 routing (v4.2)
    entry_profile: str = ""  # learn_paper | explore_idea | continue_work | l4_return


# -- Re-exported from state_model for backward compat --

L3_ACTIVITIES = [
    "ideate", "plan", "derive", "trace-derivation",
    "diagnose", "gap-audit", "integrate", "connect", "distill",
]

L3_ACTIVITY_TEMPLATES: dict[str, tuple[str, dict[str, Any], str]] = {
    "ideate": (
        "ideate",
        {"artifact_kind": "l3_active_idea", "activity": "ideate",
         "required_fields": ["idea_statement", "motivation"],
         "idea_statement": "", "motivation": "",
         "completion_status": "draft"},
        "# Active Idea\n\n## Idea Statement\n\n## Motivation\n\n"
        "## Prior Work (L2 Check)\n\n## Risk Assessment\n",
    ),
    "plan": (
        "plan",
        {"artifact_kind": "l3_active_plan", "activity": "plan",
         "required_fields": ["plan_statement", "derivation_route"],
         "plan_statement": "", "derivation_route": "",
         "completion_status": "draft"},
        "# Active Plan\n\n## Plan Statement\n\n## Derivation Route\n\n"
        "## Tool And Knowledge Requirements\n\n## Risk Assessment\n",
    ),
    "derive": (
        "derive",
        {"artifact_kind": "l3_active_derivation", "activity": "derive",
         "required_fields": ["derivation_count", "all_steps_justified"],
         "derivation_count": 0, "all_steps_justified": "",
         "completion_status": "draft"},
        "# Active Derivation\n\n## Derivation Chains\n\n"
        "## Step-by-Step Trace\n\n## Attempted Routes (Dead Ends)\n\n"
        "## Dead Ends / Negative Results\n\n"
        "## Feynman Self-Check\n\n## Unresolved Steps\n",
    ),
    "trace-derivation": (
        "trace-derivation",
        {"artifact_kind": "l3_active_trace", "activity": "trace-derivation",
         "required_fields": ["source_id", "derivation_count"],
         "source_id": "", "derivation_count": 0,
         "completion_status": "draft"},
        "# Active Trace\n\n## Source Reference\n\n## Derivation Chains\n\n"
        "## Step-by-Step Trace\n\n## Justification Gaps\n",
    ),
    "gap-audit": (
        "gap-audit",
        {"artifact_kind": "l3_active_gaps", "activity": "gap-audit",
         "required_fields": ["gap_count", "blocking_gaps"],
         "gap_count": 0, "blocking_gaps": "",
         "completion_status": "draft"},
        "# Active Gap Audit\n\n## Unstated Assumptions\n\n"
        "## Approximation Regimes\n\n## Correspondence Check\n\n"
        "## Prerequisite Gaps\n\n## Severity Assessment\n",
    ),
    "integrate": (
        "integrate",
        {"artifact_kind": "l3_active_integration", "activity": "integrate",
         "required_fields": ["integration_statement", "findings"],
         "integration_statement": "", "findings": "",
         "completion_status": "draft"},
        "# Active Integration\n\n## Integration Statement\n\n## Findings\n\n"
        "## Consistency Checks\n\n## Gaps Remaining\n",
    ),
    "diagnose": (
        "diagnose",
        {"artifact_kind": "l3_active_diagnosis", "activity": "diagnose",
         "required_fields": ["anomaly_description", "hypothesis_count"],
         "anomaly_description": "", "hypothesis_count": 0,
         "completion_status": "draft"},
        "# Active Diagnosis\n\n## Anomaly Description\n\n"
        "## Hypothesis Stack\n\n## Tests Executed\n\n"
        "## Excluded Hypotheses\n\n## Resolution\n",
    ),
    "connect": (
        "connect",
        {"artifact_kind": "l3_active_connect", "activity": "connect",
         "required_fields": ["nodes_created", "edges_created"],
         "nodes_created": "", "edges_created": "",
         "completion_status": "draft"},
        "# Active Connection\n\n## Concepts Being Connected\n\n"
        "## Proposed Edges\n\n## Evidence\n\n"
        "## Trust Assessment\n\n## Discovered Candidates\n",
    ),
    "distill": (
        "distill",
        {"artifact_kind": "l3_active_distillation", "activity": "distill",
         "required_fields": ["distilled_claim", "evidence_summary"],
         "distilled_claim": "", "evidence_summary": "",
         "completion_status": "draft"},
        "# Active Distillation\n\n## Distilled Claim\n\n## Evidence Summary\n\n"
        "## Confidence Level\n\n## Open Questions\n",
    ),
}

L3_ACTIVITY_ARTIFACT_NAMES: dict[str, str] = {
    "ideate": "active_idea.md",
    "plan": "active_plan.md",
    "derive": "active_derivation.md",
    "trace-derivation": "active_trace.md",
    "diagnose": "active_diagnosis.md",
    "gap-audit": "active_gaps.md",
    "integrate": "active_integration.md",
    "connect": "active_connect.md",
    "distill": "active_distillation.md",
}

# Backwards-compat aliases for flow notebook and legacy tools.
L3_SUBPLANES = L3_ACTIVITIES
L3_ACTIVE_ARTIFACT_NAMES = L3_ACTIVITY_ARTIFACT_NAMES
# Study mode merged into flexible workspace in v4.0; entry_profile (v4.2)
# replaces l3_mode for routing. Kept as empty for backward compat.
STUDY_L3_SUBPLANES: list[str] = []
STUDY_L3_ACTIVE_ARTIFACT_NAMES: dict[str, str] = {}

L3_ACTIVITY_SKILL_MAP: dict[str, str] = {
    "ideate": "skill-l3-ideate",
    "plan": "skill-l3-plan",
    "derive": "skill-l3-analyze",
    "trace-derivation": "skill-l3-analyze",
    "diagnose": "skill-l3-diagnose",
    "gap-audit": "skill-l3-gap-audit",
    "integrate": "skill-l3-integrate",
    "connect": "skill-l3-connect",
    "distill": "skill-l3-distill",
}

# Backwards-compat: old name for L3_ACTIVITY_TEMPLATES
L3_ARTIFACT_TEMPLATES = L3_ACTIVITY_TEMPLATES

def _get_l3_config() -> dict:
    """Deprecated — returns activity config for test compat."""
    return {
        'activities': L3_ACTIVITIES,
        'skill_map': L3_ACTIVITY_SKILL_MAP,
        'artifact_names': L3_ACTIVITY_ARTIFACT_NAMES,
    }

L3_ACTIVITY_REQUIRED_HEADINGS: dict[str, list[str]] = {
    "ideate": ["## Idea Statement", "## Motivation"],
    "plan": ["## Plan Statement", "## Derivation Route"],
    "derive": ["## Derivation Chains", "## Step-by-Step Trace"],
    "trace-derivation": ["## Source Reference", "## Derivation Chains"],
    "diagnose": ["## Anomaly Description", "## Hypothesis Stack"],
    "gap-audit": ["## Unstated Assumptions", "## Correspondence Check"],
    "integrate": ["## Integration Statement", "## Findings"],
    "connect": ["## Concepts Being Connected", "## Proposed Edges"],
    "distill": ["## Distilled Claim", "## Evidence Summary"],
}

STUDY_CANDIDATE_TYPES = [
    "atomic_concept", "derivation_chain", "correspondence_link",
    "regime_boundary", "open_question",
]

CANDIDATE_TYPES = STUDY_CANDIDATE_TYPES + ["research_claim", "negative_result"]

_ARTIFACT_COMPLETION_STATUSES = {"draft", "complete"}


# ---------------------------------------------------------------------------
# L2 knowledge graph constants
# ---------------------------------------------------------------------------

L2_NODE_TYPES = [
    # Core knowledge types
    "concept", "theorem", "technique", "derivation_chain",
    "result", "approximation", "open_question", "regime_boundary",
    "negative_result",      # a claim that was tested and failed — equal value to positive
    # Fine-grained types (from LAYER2_OBJECT_FAMILIES)
    "definition",           # definition_card
    "equation",             # equation_card
    "assumption_card",      # assumption_card — what must be true for a result
    "notation",             # notation_card — symbol conventions
    "proof_fragment",       # proof_fragment — partial proof steps
    "example",              # example_card — illustrative cases
    "caveat",               # caveat_card — warnings, limitations
    "diagram",              # diagram — figures as evidence attachments
]

L2_EDGE_TYPES = [
    # Core physics
    "limits_to", "specializes", "generalizes", "approximates",
    # Logical dependency
    "derives_from", "proven_by", "assumes", "uses",
    # Structural
    "component_of", "equivalent_to", "contradicts",
    # EFT tower
    "matches_onto", "decouples_at", "emerges_from",
    # Research
    "refines", "motivates",
    # Falsification
    "falsifies",            # a negative result / experiment that rules out a claim
    # Physics-specific relations
    "dual_to",              # Kramers-Wannier, AdS/CFT bulk/boundary
    "conjugate_to",         # Fourier conjugate, Legendre conjugate
    "perturbative_in",      # expansion in a small parameter
    "superseded_by",        # old result replaced by newer one
    "invariant_under",      # quantity invariant under a symmetry group
]

# Suggested domains for L2 node categorisation. These are hints, not a closed enum.
# Any domain string is valid — new domains are auto-registered on first use.
# The list below provides labels, descriptions, and typical energy scales for
# common physics domains. Extend freely as research expands.
DOMAIN_TAXONOMY: dict[str, dict[str, Any]] = {
    "electronic-structure": {
        "label": "Electronic Structure",
        "energy_scales": ["eV", "Hartree"],
    },
    "quantum-many-body": {
        "label": "Quantum Many-Body Theory",
        "energy_scales": ["eV", "meV", "K"],
    },
    "qft": {
        "label": "Quantum Field Theory",
        "energy_scales": ["GeV", "TeV", "Planck"],
    },
    "condensed-matter": {
        "label": "Condensed Matter Physics",
        "energy_scales": ["meV", "eV", "K"],
    },
    "quantum-gravity": {
        "label": "Quantum Gravity",
        "energy_scales": ["Planck"],
    },
    "generalized-symmetries": {
        "label": "Generalized Symmetries",
        "energy_scales": [],
    },
    "quantum-information": {
        "label": "Quantum Information",
        "energy_scales": [],
    },
    "statistical-mechanics": {
        "label": "Statistical Mechanics",
        "energy_scales": ["K", "eV"],
    },
    "aitp-protocol": {
        "label": "AITP Protocol (Internal)",
        "energy_scales": [],
    },
}

# Domains are open — any string is valid. New domains register on first use.
# VALID_DOMAINS exists for backwards compat but is NOT used for validation.
def _is_valid_domain(domain: str) -> bool:
    return bool(domain.strip())

VALID_DOMAINS = frozenset(DOMAIN_TAXONOMY.keys())

# Fields excluded from L2 query output to prevent context bloat.
# Source provenance is stored for auditing but hidden from consumers.
L2_QUERY_HIDDEN_FIELDS = frozenset({
    "source_candidate", "source_ref", "source_topic",
    "created_at", "promoted_at", "promotion_comment",
    "previous_version_promoted_at", "aliases",
})

DIAGRAM_TEMPLATE: dict[str, Any] = {
    "kind": "l2_diagram",
    "diagram_id": "",
    "title": "",
    "what_it_shows": "",
    "related_nodes": [],
    "related_edges": [],
    "source_ref": "",
    "source_file": "",
}

JUSTIFICATION_TYPES = [
    "definition", "theorem", "approximation", "physical_principle",
    "algebraic_identity", "limit", "assumption",
    "conjecture",           # widely used but not proven
    "gap",                  # explicitly marked unfilled step
    "numerical_evidence",   # supported by computation but no analytic proof
]

STEP_TEMPLATE: dict[str, Any] = {
    "kind": "l2_derivation_step",
    "step_id": "",
    "chain_id": "",
    "order": 0,
    "input_expr": "",
    "output_expr": "",
    "transform": "",
    "justification_type": "",
    "justification_detail": "",
    "rigor_level": "",          # rigorous | heuristic | handwaving | conjectured
    "gap_marker": "",           # non-empty = this step is an acknowledged gap
    "depends_on_steps": [],
    "depends_on_nodes": [],
    "approximation": "",
    "regime_condition": "",
    "source_ref": "",
    "code_ref": "",             # code location: "file:line", "function_name"
    "paper_ref": "",            # paper equation/section reference
    "fidelity_assessment": "",  # "faithful" | "approximate" | "deviates" | "unverifiable"
}

L2_TOWER_TEMPLATE: tuple[dict[str, Any], str] = (
    {
        "kind": "l2_tower",
        "name": "",
        "energy_range": "",
        "layers": [],
        "correspondence_links": [],
    },
    "# EFT Tower\n\n## Layers\n\n## Correspondence Links\n\n## Open Boundaries\n",
)

L2_CORRESPONDENCE_TEMPLATE: tuple[dict[str, Any], str] = (
    {
        "kind": "l2_correspondence",
        "from_theory": "",
        "to_theory": "",
        "limit_condition": "",
        "verified": False,
        "verified_by": "",
    },
    "# Correspondence Link\n\n## Limit Condition\n\n## Verification\n\n## Notes\n",
)

STUDY_L4_CHECKS = [
    "coverage_check",
    "feynman_self_test",
    "correspondence_check",
    "derivation_step_completeness",
    "regime_annotation",
    "l2_edge_completeness",
]

TRUST_EVOLUTION = {
    "source_grounded": {"trust_basis": "source_grounded", "trust_scope": "single_source"},
    "multi_source_confirmed": {"trust_basis": "multi_source_confirmed", "trust_scope": "bounded_reusable"},
    "validated": {"trust_basis": "validated", "trust_scope": "broad_reusable"},
    "independently_verified": {"trust_basis": "independently_verified", "trust_scope": "broad_reusable"},
}


# ---------------------------------------------------------------------------
# L4 adjudication constants
# ---------------------------------------------------------------------------

L4_OUTCOMES = ["pass", "partial_pass", "fail", "contradiction", "stuck", "timeout"]

PHYSICS_CHECK_FIELDS = [
    "dimensional_consistency",
    "symmetry_compatibility",
    "limiting_case_check",
    "conservation_check",
    "correspondence_check",
    "approximation_validity_check",
    "unitarity_check",
    "causality_check",
    "scale_separation_check",
    "regularization_independence",
]

# Lane-dependent required check fields.
# formal_theory requires all 10 physics checks.
# code_method and toy_numeric require the first 8 (all except
# unitarity/causality — includes scale_separation and
# regularization_independence which are critical for finite-size
# and EFT workflows).
_LANE_PHYSICS_CHECK_FIELDS: dict[str, list[str]] = {
    "formal_theory": PHYSICS_CHECK_FIELDS,
    "code_method": PHYSICS_CHECK_FIELDS[:8],
    "toy_numeric": PHYSICS_CHECK_FIELDS[:8],
}

CROSS_DOMAIN_CHECK_FIELDS = [
    "structural_isomorphism_check",
    "regime_translation_check",
    "counterexample_search",
    "multi_observer_triangulation",
]

