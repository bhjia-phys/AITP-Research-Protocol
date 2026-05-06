"""Artifact templates, required fields, required headings for all stages.

NOTE: Pydantic runtime validation models live in brain.cli.contracts.
This module provides template constants used by state_model.py and gates.py.
"""

from __future__ import annotations

from typing import Any


# -- L0 contracts --

L0_ARTIFACT_TEMPLATES: dict[str, tuple[dict[str, Any], str]] = {
    "source_registry.md": (
        {
            "artifact_kind": "l0_source_registry",
            "stage": "L0",
            "required_fields": ["source_count", "search_status"],
            "source_count": 0,
            "search_status": "",
        },
        "# Source Registry\n\n## Search Methodology\n\n## Source Inventory\n\n"
        "## Source Roles\n\n"
        "Classify each source by its role in the research:\n"
        "- **foundational**: defines the framework (e.g. Hedin 1965 for GW)\n"
        "- **direct_dependency**: derivation directly depends on this\n"
        "- **contrast_reference**: used to validate against known limits\n"
        "- **background**: contextual but not load-bearing\n\n"
        "## Coverage Assessment\n\n"
        "Define the dimensions that matter for YOUR research question, "
        "then assess coverage for each. Do NOT fill a preset table — "
        "choose dimensions that would block your derivation if missing.\n\n"
        "### [Dimension 1 — e.g. method / regime / spatial dimension / "
        "approximation order / symmetry group]\n"
        "Currently covered:\n"
        "Missing:\n\n"
        "### [Dimension 2 — ...]\n"
        "Currently covered:\n"
        "Missing:\n\n"
        "### [Dimension N — ...]\n"
        "Currently covered:\n"
        "Missing:\n\n"
        "## Overall Verdict\n\n"
        "Which key dimensions are adequately covered? "
        "Which gaps would block derivation?\n\n"
        "## Gaps And Next Sources\n",
    ),
}

L0_SOURCE_TYPES: list[str] = [
    "paper", "preprint", "book", "dataset", "code",
    "experiment", "simulation", "lecture_notes", "reference",
]


# ---------------------------------------------------------------------------
# L0 gate evaluation
# ---------------------------------------------------------------------------

_L0_CONTRACTS: list[tuple[str, str, list[str], list[str]]] = [
    (
        "source_registry.md",
        "discover",
        ["source_count", "search_status"],
        ["## Search Methodology", "## Source Inventory", "## Coverage Assessment",
         "## Prior L2 Knowledge", "## Overall Verdict", "## Gaps And Next Sources"],
    ),
]


# -- L1 contracts + templates + intake --

L1_ARTIFACT_TEMPLATES: dict[str, tuple[dict[str, Any], str]] = {
    "question_contract.md": (
        {
            "artifact_kind": "l1_question_contract",
            "stage": "L1",
            "required_fields": ["bounded_question", "scope_boundaries", "target_quantities"],
            "bounded_question": "",
            "scope_boundaries": "",
            "target_quantities": "",
            "competing_hypotheses": "",
            "source_refs": [],
        },
        "# Question Contract\n\n## Bounded Question\n\n## Competing Hypotheses\n\n"
        "## Scope Boundaries\n\n## Forbidden Proxies\n\n"
        "## Target Quantities Or Claims\n\n## Deliverables\n\n"
        "## Acceptance Criteria\n\n## Non-Success Conditions\n\n## Uncertainty Markers\n",
    ),
    "source_basis.md": (
        {
            "artifact_kind": "l1_source_basis",
            "stage": "L1",
            "required_fields": ["core_sources", "peripheral_sources"],
            "core_sources": "",
            "peripheral_sources": "",
            "source_refs": [],
        },
        "# Source Basis\n\n## Core Sources\n\n## Peripheral Sources\n\n"
        "## Source Roles\n\n## Reading Depth\n\n## Why Each Source Matters\n",
    ),
    "convention_snapshot.md": (
        {
            "artifact_kind": "l1_convention_snapshot",
            "stage": "L1",
            "required_fields": ["notation_choices", "unit_conventions"],
            "notation_choices": "",
            "unit_conventions": "",
            "source_refs": [],
        },
        "# Convention Snapshot\n\n## Notation Choices\n\n## Unit Conventions\n\n"
        "## Sign Conventions\n\n## Metric Or Coordinate Conventions\n\n"
        "## Categorized Assumptions\n\n"
        "Group by category — each has different failure modes:\n"
        "- **Mathematical assumptions**: topology, dimensionality, symmetry group, "
        "completeness, convergence properties\n"
        "- **Physical assumptions**: energy regime, coupling limits, boundary conditions, "
        "equilibrium vs non-equilibrium, thermodynamic limit\n"
        "- **Notational assumptions**: sign conventions, normalization choices, "
        "index ranges, Fourier convention (factors of 2π)\n\n"
        "## Canonical Notation\n\n"
        "When sources disagree on notation, choose ONE canonical convention "
        "for this topic. Record the chosen notation and justify why it was "
        "selected over alternatives. This is the notation L3 derivations "
        "should adopt unless there is a physics reason to switch.\n\n"
        "## Unresolved Tensions\n\n"
        "## L3 Discoveries\n\n"
        "Appended during L3 derivation as new conventions, sign choices, "
        "or normalization factors are discovered that were not captured "
        "at L1 framing time. Each entry should include the derivation "
        "context and source equation.\n",
    ),
    "derivation_anchor_map.md": (
        {
            "artifact_kind": "l1_derivation_anchor_map",
            "stage": "L1",
            "required_fields": ["starting_anchors", "anchor_count"],
            "starting_anchors": "",
            "anchor_count": 0,
            "source_refs": [],
        },
        "# Derivation Anchor Map\n\n"
        "## Source Anchors\n\n"
        "Record each anchor with:\n"
        "- **Section pointer** — exact source section/location where the derivation lives\n"
        "- **Derivation type** — `derived_in_full` | `stated_with_sketch` | "
        "`handwaved` (\"it can be shown that...\")\n"
        "- **Depends on** — which prior equations or results within the source does it use?\n"
        "- **Feeds into** — which downstream results depend on it?\n"
        "- **Assumptions used** — which assumptions (by category: "
        "mathematical/physical/notational) does the derivation invoke?\n\n"
        "## Dependency Graph\n\n"
        "Sketch the equation dependency graph across all sources.\n\n"
        "## Missing Steps\n\n"
        "Which steps are skipped or unclear? What would a self-contained "
        "derivation need to fill in?\n\n"
        "## Candidate Starting Points\n\n"
        "Which anchors are the strongest entry points for L3 derivation?\n",
    ),
    "contradiction_register.md": (
        {
            "artifact_kind": "l1_contradiction_register",
            "stage": "L1",
            "required_fields": ["blocking_contradictions"],
            "blocking_contradictions": "",
            "source_refs": [],
        },
        "# Contradiction Register\n\n## Unresolved Source Conflicts\n\n"
        "## Internal Inconsistencies\n\n"
        "Flag places where a single source contradicts itself or where the "
        "argument chain has a gap. Every physicist knows the weakest step in "
        "their own derivation — record it here.\n\n"
        "## Regime Mismatches\n\n## Notation Collisions\n\n## Blocking Status\n",
    ),
    "source_toc_map.md": (
        {
            "artifact_kind": "l1_source_toc_map",
            "stage": "L1",
            "required_fields": ["sources_with_toc", "total_sections", "coverage_status"],
            "sources_with_toc": "",
            "total_sections": 0,
            "coverage_status": "",
            "source_refs": [],
        },
        "# Source TOC Map\n\n"
        "## Per-Source TOC\n\n"
        "*(Use aitp_parse_source_toc to register each source's section structure.)*\n\n"
        "## Coverage Summary\n\n## Deferred Sections\n\n## Extraction Notes\n",
    ),
    "source_cross_map.md": (
        {
            "artifact_kind": "l1_source_cross_map",
            "stage": "L1",
            "required_fields": [],
            "cross_references": [],
            "source_refs": [],
        },
        "# Source Cross Map\n\n"
        "## Cross-Source Dependencies\n\n"
        "Record how sources depend on each other:\n"
        "- Source A uses results from Source B → A depends_on B\n"
        "- Source A provides foundation for Source B → A feeds_into B\n"
        "- Source A contradicts Source B → A conflicts_with B\n\n"
        "## Equation Lineage\n\n"
        "Trace key equations across sources. When the same equation appears "
        "in multiple sources, record the original source and all references.\n\n"
        "## Unresolved Cross-References\n",
    ),
}


L1_INTAKE_TEMPLATE: tuple[dict[str, Any], str] = (
    {
        "artifact_kind": "l1_section_intake",
        "stage": "L1",
        "required_fields": ["source_id", "section_id", "extraction_status", "completeness_confidence"],
        "source_id": "",
        "section_id": "",
        "section_title": "",
        "extraction_status": "skimming",
        "completeness_confidence": "",
        "source_ref": "",
        "source_file": "",
        "regime": "",
        "validity_conditions": "",
        "figure_refs": "",
    },
    "# Section Intake\n\n## Section Summary (skim)\n\n"
    "## Key Concepts\n\n## Equations Found\n\n"
    "## Physical Claims\n\n"
    "Record each claim with its argument role and authority level:\n\n"
    "Argument role:\n"
    "- **physical_principle** — follows from conservation, symmetry, causality, etc.\n"
    "- **algebraic_identity** — purely mathematical manipulation\n"
    "- **assumption** — invoked without proof; may be justified elsewhere or deferred\n"
    "- **approximation** — a controlled limit (e.g. weak coupling, large-N, low-T)\n"
    "- **conjecture** — not yet proven; may be speculative\n\n"
    "Authority level (per claim, not blanket):\n"
    "- **source_grounded** — directly extracted from the source with "
    "sentence-level evidence\n"
    "- **provisional** — agent interpretation or synthesis of multiple "
    "source statements\n"
    "- **tentative** — speculative connection; needs L3 derivation to confirm\n\n"
    "## Argument Structure\n\n"
    "How do the claims connect? Record the section's logical flow:\n"
    "- Claim A establishes → Claim B uses A to derive → Claim C generalizes B\n"
    "- Which claims are load-bearing for downstream sections?\n\n"
    "## Figures & Diagrams\n\n"
    "Record each figure that conveys physics content. For each figure:\n"
    "- Figure number and label from source\n"
    "- What it shows (phase diagram, Feynman diagram, band structure, "
    "energy landscape, schematic, data plot, etc.)\n"
    "- Which equations/concepts it illustrates\n"
    "- Whether it's essential for understanding the argument\n"
    "- Link to L2 diagram node if already created\n\n"
    "## Regime & Validity\n\n"
    "What physical regime do these results live in? "
    "What conditions must hold for them to be valid?\n"
    "Record any claimed limiting behavior (e.g. \"reduces to X in the T→0 limit\").\n\n"
    "## Prerequisites\n\n## Cross-References\n\n## Completeness Self-Assessment\n",
)


_L1_CONTRACTS: list[tuple[str, str, list[str], list[str]]] = [
    (
        "question_contract.md",
        "read",
        ["bounded_question", "scope_boundaries", "target_quantities"],
        ["## Bounded Question", "## Competing Hypotheses", "## Scope Boundaries", "## Target Quantities Or Claims"],
    ),
    (
        "source_basis.md",
        "read",
        ["core_sources", "peripheral_sources"],
        ["## Core Sources", "## Peripheral Sources", "## Why Each Source Matters"],
    ),
    (
        "convention_snapshot.md",
        "frame",
        ["notation_choices", "unit_conventions"],
        ["## Notation Choices", "## Unit Conventions", "## Categorized Assumptions", "## Unresolved Tensions"],
    ),
    (
        "derivation_anchor_map.md",
        "frame",
        ["starting_anchors", "anchor_count"],
        ["## Source Anchors", "## Dependency Graph", "## Candidate Starting Points"],
    ),
    (
        "contradiction_register.md",
        "frame",
        ["blocking_contradictions"],
        ["## Unresolved Source Conflicts", "## Internal Inconsistencies", "## Blocking Status"],
    ),
    (
        "source_toc_map.md",
        "read",
        ["sources_with_toc", "total_sections", "coverage_status"],
        ["## Per-Source TOC", "## Coverage Summary"],
    ),
    (
        "source_cross_map.md",
        "frame",
        [],
        ["## Cross-Source Dependencies"],
    ),
]


# Research intensity → which L1 contracts are mandatory.
# quick: question_contract only. standard: question_contract + source_basis
#   + source_toc_map. full: all 6 artifacts.
_L1_INTENSITY_CONTRACTS: dict[str, list[tuple[str, str, list[str], list[str]]]] = {
    "quick": [
        ("question_contract.md", "read",
         ["bounded_question", "scope_boundaries", "target_quantities"],
         ["## Bounded Question", "## Competing Hypotheses",
          "## Scope Boundaries", "## Target Quantities Or Claims"]),
    ],
    "standard": [
        ("question_contract.md", "read",
         ["bounded_question", "scope_boundaries", "target_quantities"],
         ["## Bounded Question", "## Competing Hypotheses",
          "## Scope Boundaries", "## Target Quantities Or Claims"]),
        ("source_basis.md", "read",
         ["core_sources", "peripheral_sources"],
         ["## Core Sources", "## Peripheral Sources", "## Why Each Source Matters"]),
        ("source_toc_map.md", "read",
         ["sources_with_toc", "total_sections", "coverage_status"],
         ["## Per-Source TOC", "## Coverage Summary"]),
    ],
}



# -- Stage config --

INTERACTION_LEVELS = ["collaborative", "direct", "silent"]

# Validation depth for L4 reviews.
# abbreviated: dimensional_consistency + one-sentence devils_advocate.
# full: all 5 physics checks + 5-dimension devils_advocate.
VALIDATION_DEPTHS = ["abbreviated", "full"]

# L3 activities from which a candidate can be submitted directly to L4
# without completing the full 5-subplane sequence.
_DIRECT_SUBMIT_ACTIVITIES = {"distill", "derive", "integrate"}

