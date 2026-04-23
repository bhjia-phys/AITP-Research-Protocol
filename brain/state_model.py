"""Safe topic-root resolution, slug validation, and stage/posture gate model.

Centralizes path contract so brain/mcp_server.py and hooks agree on
whether topics live at <topics_root>/<slug> or <topics_root>/topics/<slug>.
Also defines the L0/L1/L3 gate evaluation logic and StageSnapshot dataclass.
"""

from __future__ import annotations

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


def topics_dir(topics_root: str | Path) -> Path:
    """Resolve the actual topics directory.

    If topics_root contains a ``topics/`` subdirectory, use it.
    Otherwise treat topics_root itself as the topics directory.
    """
    root = Path(topics_root)
    nested = root / "topics"
    return nested if nested.is_dir() else root


def validate_topic_slug(topic_slug: str) -> str:
    """Reject path-traversal, absolute, multi-component, or empty slugs."""
    slug = topic_slug.strip()
    if not slug:
        raise ValueError("topic_slug must be non-empty")
    pure = PurePath(slug)
    if pure.is_absolute():
        raise ValueError("topic_slug must be relative, got absolute path")
    if any(part in {"..", "."} for part in pure.parts):
        raise ValueError("topic_slug contains unsafe path traversal")
    if len(pure.parts) != 1:
        raise ValueError("topic_slug must be a single path component")
    return slug


def topic_root(topics_root: str | Path, topic_slug: str) -> Path:
    """Resolve the canonical directory for a single topic."""
    safe_slug = validate_topic_slug(topic_slug)
    root = topics_dir(topics_root) / safe_slug
    if not root.is_dir():
        raise FileNotFoundError(f"Topic not found: {safe_slug}")
    return root


# ---------------------------------------------------------------------------
# L0 artifact templates (frontmatter, body)
# ---------------------------------------------------------------------------

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
        "## Coverage Assessment\n\n## Gaps And Next Sources\n",
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
        ["## Search Methodology", "## Source Inventory", "## Coverage Assessment"],
    ),
]


def evaluate_l0_stage(
    parse_md: Callable[[Path], tuple[dict[str, Any], str]],
    topic_root_path: Path,
    lane: str = "unspecified",
) -> StageSnapshot:
    """Evaluate L0 gate status by checking source registry and registered sources."""
    for name, posture, fields, headings in _L0_CONTRACTS:
        path = topic_root_path / "L0" / name
        if not path.exists():
            return StageSnapshot(
                stage="L0",
                posture=posture,
                lane=lane,
                gate_status="blocked_missing_artifact",
                required_artifact_path=str(path),
                missing_requirements=[name],
                next_allowed_transition="L0",
                skill="skill-discover",
            )
        fm, body = parse_md(path)
        missing = _missing_frontmatter_keys(fm, fields) + _missing_required_headings(body, headings)
        if missing:
            return StageSnapshot(
                stage="L0",
                posture=posture,
                lane=lane,
                gate_status="blocked_missing_field",
                required_artifact_path=str(path),
                missing_requirements=missing,
                next_allowed_transition="L0",
                skill="skill-discover",
            )
        # Require at least one registered source
        src_dir = topic_root_path / "L0" / "sources"
        actual_count = len(list(src_dir.glob("*.md"))) if src_dir.is_dir() else 0
        if actual_count < 1:
            return StageSnapshot(
                stage="L0",
                posture=posture,
                lane=lane,
                gate_status="blocked_missing_field",
                required_artifact_path=str(path),
                missing_requirements=["register at least one source in L0/sources/"],
                next_allowed_transition="L0",
                skill="skill-discover",
            )

    return StageSnapshot(
        stage="L0",
        posture="discover",
        lane=lane,
        gate_status="ready",
        next_allowed_transition="L1",
        skill="skill-discover",
    )


# ---------------------------------------------------------------------------
# L1 artifact templates (frontmatter, body)
# ---------------------------------------------------------------------------

L1_ARTIFACT_TEMPLATES: dict[str, tuple[dict[str, Any], str]] = {
    "question_contract.md": (
        {
            "artifact_kind": "l1_question_contract",
            "stage": "L1",
            "required_fields": ["bounded_question", "scope_boundaries", "target_quantities"],
            "bounded_question": "",
            "scope_boundaries": "",
            "target_quantities": "",
        },
        "# Question Contract\n\n## Bounded Question\n\n## Scope Boundaries\n\n"
        "## Target Quantities Or Claims\n\n## Non-Success Conditions\n\n## Uncertainty Markers\n",
    ),
    "source_basis.md": (
        {
            "artifact_kind": "l1_source_basis",
            "stage": "L1",
            "required_fields": ["core_sources", "peripheral_sources"],
            "core_sources": "",
            "peripheral_sources": "",
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
        },
        "# Convention Snapshot\n\n## Notation Choices\n\n## Unit Conventions\n\n"
        "## Sign Conventions\n\n## Metric Or Coordinate Conventions\n\n## Unresolved Tensions\n",
    ),
    "derivation_anchor_map.md": (
        {
            "artifact_kind": "l1_derivation_anchor_map",
            "stage": "L1",
            "required_fields": ["starting_anchors"],
            "starting_anchors": "",
        },
        "# Derivation Anchor Map\n\n## Source Anchors\n\n## Missing Steps\n\n"
        "## Candidate Starting Points\n",
    ),
    "contradiction_register.md": (
        {
            "artifact_kind": "l1_contradiction_register",
            "stage": "L1",
            "required_fields": ["blocking_contradictions"],
            "blocking_contradictions": "",
        },
        "# Contradiction Register\n\n## Unresolved Source Conflicts\n\n"
        "## Regime Mismatches\n\n## Notation Collisions\n\n## Blocking Status\n",
    ),
}


# ---------------------------------------------------------------------------
# L1 gate evaluation
# ---------------------------------------------------------------------------

def _missing_frontmatter_keys(frontmatter: dict[str, object], required: list[str]) -> list[str]:
    return [key for key in required if not str(frontmatter.get(key, "")).strip()]


def _missing_required_headings(body: str, headings: list[str]) -> list[str]:
    return [h for h in headings if h not in body]


_L1_CONTRACTS: list[tuple[str, str, list[str], list[str]]] = [
    (
        "question_contract.md",
        "read",
        ["bounded_question", "scope_boundaries", "target_quantities"],
        ["## Bounded Question", "## Scope Boundaries", "## Target Quantities Or Claims"],
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
        ["## Notation Choices", "## Unit Conventions", "## Unresolved Tensions"],
    ),
    (
        "derivation_anchor_map.md",
        "frame",
        ["starting_anchors"],
        ["## Source Anchors", "## Candidate Starting Points"],
    ),
    (
        "contradiction_register.md",
        "frame",
        ["blocking_contradictions"],
        ["## Unresolved Source Conflicts", "## Blocking Status"],
    ),
]


def evaluate_l1_stage(
    parse_md: Callable[[Path], tuple[dict[str, Any], str]],
    topic_root_path: Path,
    lane: str = "unspecified",
) -> StageSnapshot:
    """Evaluate L1 gate status by checking all required artifacts."""
    for name, posture, fields, headings in _L1_CONTRACTS:
        path = topic_root_path / "L1" / name
        if not path.exists():
            return StageSnapshot(
                stage="L1",
                posture=posture,
                lane=lane,
                gate_status="blocked_missing_artifact",
                required_artifact_path=str(path),
                missing_requirements=[name],
                next_allowed_transition="L1",
                skill=f"skill-{posture}",
            )
        fm, body = parse_md(path)
        missing = _missing_frontmatter_keys(fm, fields) + _missing_required_headings(body, headings)
        if missing:
            return StageSnapshot(
                stage="L1",
                posture=posture,
                lane=lane,
                gate_status="blocked_missing_field",
                required_artifact_path=str(path),
                missing_requirements=missing,
                next_allowed_transition="L1",
                skill=f"skill-{posture}",
            )

    return StageSnapshot(
        stage="L1",
        posture="frame",
        lane=lane,
        gate_status="ready",
        next_allowed_transition="L3",
        skill="skill-frame",
    )


# ---------------------------------------------------------------------------
# L3 subplanes
# ---------------------------------------------------------------------------

L3_SUBPLANES = ["ideation", "planning", "analysis", "result_integration", "distillation"]

L3_ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "ideation": ["planning"],
    "planning": ["analysis", "ideation"],
    "analysis": ["result_integration", "ideation", "planning"],
    "result_integration": ["distillation", "analysis"],
    "distillation": ["result_integration"],
}

L3_ARTIFACT_TEMPLATES: dict[str, tuple[str, dict[str, Any], str]] = {
    # (subplane, frontmatter, body)
    "ideation": (
        "ideation",
        {
            "artifact_kind": "l3_active_idea",
            "subplane": "ideation",
            "required_fields": ["idea_statement", "motivation"],
            "idea_statement": "",
            "motivation": "",
        },
        "# Active Idea\n\n## Idea Statement\n\n## Motivation\n\n"
        "## Prior Work\n\n## Risk Assessment\n",
    ),
    "planning": (
        "planning",
        {
            "artifact_kind": "l3_active_plan",
            "subplane": "planning",
            "required_fields": ["plan_statement", "derivation_route"],
            "plan_statement": "",
            "derivation_route": "",
        },
        "# Active Plan\n\n## Plan Statement\n\n## Derivation Route\n\n"
        "## Expected Outcomes\n\n## Milestones\n",
    ),
    "analysis": (
        "analysis",
        {
            "artifact_kind": "l3_active_analysis",
            "subplane": "analysis",
            "required_fields": ["analysis_statement", "method"],
            "analysis_statement": "",
            "method": "",
        },
        "# Active Analysis\n\n## Analysis Statement\n\n## Method\n\n"
        "## Results So Far\n\n## Anomalies\n",
    ),
    "result_integration": (
        "result_integration",
        {
            "artifact_kind": "l3_active_integration",
            "subplane": "result_integration",
            "required_fields": ["integration_statement", "findings"],
            "integration_statement": "",
            "findings": "",
        },
        "# Active Integration\n\n## Integration Statement\n\n## Findings\n\n"
        "## Consistency Checks\n\n## Gaps Remaining\n",
    ),
    "distillation": (
        "distillation",
        {
            "artifact_kind": "l3_active_distillation",
            "subplane": "distillation",
            "required_fields": ["distilled_claim", "evidence_summary"],
            "distilled_claim": "",
            "evidence_summary": "",
        },
        "# Active Distillation\n\n## Distilled Claim\n\n## Evidence Summary\n\n"
        "## Confidence Level\n\n## Open Questions\n",
    ),
}

L3_ACTIVE_ARTIFACT_NAMES: dict[str, str] = {
    "ideation": "active_idea.md",
    "planning": "active_plan.md",
    "analysis": "active_analysis.md",
    "result_integration": "active_integration.md",
    "distillation": "active_distillation.md",
}

L3_SKILL_MAP: dict[str, str] = {
    "ideation": "skill-l3-ideate",
    "planning": "skill-l3-plan",
    "analysis": "skill-l3-analyze",
    "result_integration": "skill-l3-integrate",
    "distillation": "skill-l3-distill",
}

L3_REQUIRED_HEADINGS: dict[str, list[str]] = {
    "ideation": ["## Idea Statement", "## Motivation"],
    "planning": ["## Plan Statement", "## Derivation Route"],
    "analysis": ["## Analysis Statement", "## Method"],
    "result_integration": ["## Integration Statement", "## Findings"],
    "distillation": ["## Distilled Claim", "## Evidence Summary"],
}


def evaluate_l3_stage(
    parse_md: Callable[[Path], tuple[dict[str, Any], str]],
    topic_root_path: Path,
    lane: str = "unspecified",
) -> StageSnapshot:
    """Evaluate L3 gate status by checking active subplane artifacts."""
    state_fm, _ = parse_md(topic_root_path / "state.md")
    current_subplane = str(state_fm.get("l3_subplane", "")).strip() or "ideation"

    artifact_name = L3_ACTIVE_ARTIFACT_NAMES.get(current_subplane, "active_idea.md")
    artifact_path = topic_root_path / "L3" / current_subplane / artifact_name
    skill = L3_SKILL_MAP.get(current_subplane, "skill-l3-ideate")

    template_info = L3_ARTIFACT_TEMPLATES.get(current_subplane)
    if template_info is None:
        return StageSnapshot(
            stage="L3", posture="derive", lane=lane,
            gate_status="blocked_missing_artifact",
            required_artifact_path=str(artifact_path),
            missing_requirements=[f"unknown subplane '{current_subplane}'"],
            next_allowed_transition="", skill=skill,
            l3_subplane=current_subplane,
        )

    _, template_fm, _ = template_info
    required_fields = [f for f in template_fm.get("required_fields", [])
                       if not current_subplane.startswith("_")]
    required_headings = L3_REQUIRED_HEADINGS.get(current_subplane, [])

    if not artifact_path.exists():
        return StageSnapshot(
            stage="L3", posture="derive", lane=lane,
            gate_status="blocked_missing_artifact",
            required_artifact_path=str(artifact_path),
            missing_requirements=[artifact_name],
            next_allowed_transition="",
            skill=skill,
            l3_subplane=current_subplane,
        )

    fm, body = parse_md(artifact_path)
    missing = (
        _missing_frontmatter_keys(fm, required_fields)
        + _missing_required_headings(body, required_headings)
    )
    if missing:
        return StageSnapshot(
            stage="L3", posture="derive", lane=lane,
            gate_status="blocked_missing_field",
            required_artifact_path=str(artifact_path),
            missing_requirements=missing,
            next_allowed_transition="",
            skill=skill,
            l3_subplane=current_subplane,
        )

    # Current subplane is complete; check if this is the last one
    if current_subplane == "distillation":
        return StageSnapshot(
            stage="L3", posture="derive", lane=lane,
            gate_status="ready",
            next_allowed_transition="L4",
            skill=skill,
            l3_subplane=current_subplane,
        )
    return StageSnapshot(
        stage="L3", posture="derive", lane=lane,
        gate_status="ready",
        next_allowed_transition=",".join(L3_ALLOWED_TRANSITIONS.get(current_subplane, [])),
        skill=skill,
        l3_subplane=current_subplane,
    )


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
]


def evaluate_l4_stage(
    parse_md: Callable[[Path], tuple[dict[str, Any], str]],
    topic_root_path: Path,
    lane: str = "unspecified",
) -> StageSnapshot:
    """Evaluate L4 gate status by checking validation contract and review."""
    contract_path = topic_root_path / "L4" / "validation_contract.md"
    if not contract_path.exists():
        return StageSnapshot(
            stage="L4", posture="verify", lane=lane,
            gate_status="blocked_missing_artifact",
            required_artifact_path=str(contract_path),
            missing_requirements=["validation_contract.md"],
            next_allowed_transition="",
            skill="skill-l4-validate",
        )

    fm, body = parse_md(contract_path)
    if not str(fm.get("candidate_id", "")).strip():
        return StageSnapshot(
            stage="L4", posture="verify", lane=lane,
            gate_status="blocked_missing_field",
            required_artifact_path=str(contract_path),
            missing_requirements=["candidate_id"],
            next_allowed_transition="",
            skill="skill-l4-validate",
        )

    return StageSnapshot(
        stage="L4", posture="verify", lane=lane,
        gate_status="ready",
        next_allowed_transition="L3,L5,L2",
        skill="skill-l4-validate",
    )


def evaluate_l5_stage(
    parse_md: Callable[[Path], tuple[dict[str, Any], str]],
    topic_root_path: Path,
    lane: str = "unspecified",
) -> StageSnapshot:
    """Evaluate L5 gate status by checking provenance artifacts."""
    required = ["outline.md", "claim_evidence_map.md", "limitations.md"]
    for name in required:
        path = topic_root_path / "L5_writing" / name
        if not path.exists():
            return StageSnapshot(
                stage="L5", posture="write", lane=lane,
                gate_status="blocked_missing_artifact",
                required_artifact_path=str(path),
                missing_requirements=[name],
                next_allowed_transition="",
                skill="skill-l5-write",
            )
        fm, body = parse_md(path)
        # Check that outline has at least some content beyond template
        if "## Claims" in body and body.count("\n") < 8:
            return StageSnapshot(
                stage="L5", posture="write", lane=lane,
                gate_status="blocked_missing_field",
                required_artifact_path=str(path),
                missing_requirements=[f"{name} body content"],
                next_allowed_transition="",
                skill="skill-l5-write",
            )

    return StageSnapshot(
        stage="L5", posture="write", lane=lane,
        gate_status="ready",
        next_allowed_transition="L2",
        skill="skill-l5-write",
    )


# ---------------------------------------------------------------------------
# Progressive-disclosure tool catalog
# ---------------------------------------------------------------------------
# Integration patterns (A/B/C) control how the agent interacts with each tool:
#
#   A = Catalog-only     — list in menu, agent loads on demand via ToolSearch
#   B = Skill reference  — catalog + explicit invoke instruction in AITP skill
#   C = Workflow absorbed — already embedded in AITP skill, catalog is FYI only
#
# Each entry: (tool_name, one_line_desc, integration_pattern)
#
# Pattern A: Tool is optional reference. Missing it doesn't break results.
# Pattern B: Tool should be invoked at specific subplane checkpoints.
#            The AITP skill file references it with an invoke instruction.
# Pattern C: Tool's workflow is already part of the AITP skill's mandatory
#            steps. Catalog entry is informational only.

TOOL_CATALOG: dict[tuple[str, str], list[tuple[str, str, str]]] = {
    # L0 — source discovery and registration
    ("L0", "discover"): [
        ("arxiv-latex-mcp", "Read paper sections and abstracts from arXiv", "A"),
        ("paper-search-mcp", "Multi-source paper search (arXiv, PubMed, Semantic Scholar, etc.)", "B"),
        ("knowledge-hub", "Query existing knowledge base for related sources", "C"),
    ],
    # L1 — reading and framing
    ("L1", "read"): [
        ("arxiv-latex-mcp", "Read paper sections and abstracts from arXiv", "A"),
        ("paper-search-mcp", "Multi-source paper search (arXiv, PubMed, Semantic Scholar, etc.)", "A"),
        ("knowledge-hub", "Query existing knowledge base for related sources", "C"),
    ],
    ("L1", "frame"): [
        ("arxiv-latex-mcp", "Read paper sections and abstracts from arXiv", "A"),
        ("paper-search-mcp", "Search for related papers across multiple databases", "A"),
        ("knowledge-hub", "Query existing knowledge base for related sources", "C"),
    ],
    # L3 — derivation subplanes
    ("L3", "ideation"): [
        ("scientific-brainstorming", "Physics brainstorming and idea exploration", "B"),
        ("arxiv-latex-mcp", "Check related papers and formulas", "A"),
        ("paper-search-mcp", "Search for related work to avoid duplication", "A"),
        ("knowledge-hub", "Query validated knowledge from L2", "A"),
        ("jupyter-mcp-server", "Quick feasibility estimates during ideation", "A"),
    ],
    ("L3", "planning"): [
        ("arxiv-latex-mcp", "Check related papers and formulas", "A"),
        ("knowledge-hub", "Query validated knowledge from L2", "A"),
        ("ssh-mcp", "Connect to Fisher server for compute-heavy tasks", "A"),
        ("jupyter-mcp-server", "Run numerical experiments (toy_numeric/code_method lanes)", "C"),
    ],
    ("L3", "analysis"): [
        ("arxiv-latex-mcp", "Reference papers during computation", "A"),
        ("knowledge-hub", "Query validated knowledge from L2", "A"),
        ("jupyter-mcp-server", "Run numerical experiments and analysis", "C"),
        ("ssh-mcp", "Connect to Fisher server for remote computation", "A"),
        ("mcp-server-chart", "Generate scientific charts and visualizations", "A"),
    ],
    ("L3", "result_integration"): [
        ("arxiv-latex-mcp", "Cross-check findings against papers", "A"),
        ("knowledge-hub", "Compare against validated L2 knowledge", "A"),
        ("mcp-server-chart", "Generate comparison charts", "A"),
    ],
    ("L3", "distillation"): [
        ("arxiv-latex-mcp", "Verify distilled claims against literature", "A"),
        ("knowledge-hub", "Check if claim duplicates existing L2 knowledge", "A"),
    ],
    # L4 — validation
    ("L4", "validate"): [
        ("jupyter-mcp-server", "Run independent validation scripts", "C"),
        ("ssh-mcp", "Run validation on Fisher server", "A"),
        ("arxiv-latex-mcp", "Check claims against published results", "A"),
        ("knowledge-hub", "Compare against validated L2 knowledge", "A"),
        ("mcp-server-chart", "Generate validation comparison charts", "A"),
    ],
    # L2 — promotion
    ("L2", "promote"): [
        ("knowledge-hub", "Store validated knowledge to L2", "C"),
    ],
    # L5 — writing
    ("L5", "write"): [
        ("arxiv-latex-mcp", "Reference paper formatting and structure", "A"),
        ("scientific-writing", "Academic writing guidance and structure", "B"),
        ("mcp-server-chart", "Generate publication-quality charts", "A"),
    ],
}

# Pattern B tools that should be explicitly invoked at specific subplanes.
# Key: tool_name, Value: list of (stage, subplane, invoke_instruction)
PATTERN_B_INSTRUCTIONS: dict[str, list[tuple[str, str, str]]] = {
    "paper-search-mcp": [
        ("L0", "discover",
         "Invoke 'paper-search-mcp' to systematically search for relevant sources "
         "during the discovery phase."),
    ],
    "scientific-brainstorming": [
        ("L3", "ideation",
         "Invoke skill 'scientific-brainstorming' BEFORE discussion round 1 "
         "to structure the idea exploration workflow."),
    ],
    "scientific-writing": [
        ("L5", "write",
         "Invoke skill 'scientific-writing' at the start of L5 to follow "
         "the academic writing structure and methodology."),
    ],
}


def get_tool_catalog(stage: str, posture_or_subplane: str) -> list[tuple[str, str, str]]:
    """Return the tool catalog for the given stage and posture/subplane."""
    return TOOL_CATALOG.get((stage, posture_or_subplane), [])


def get_pattern_b_instructions(stage: str, subplane: str) -> list[tuple[str, str]]:
    """Return Pattern B invoke instructions for the current stage/subplane."""
    result = []
    for tool_name, entries in PATTERN_B_INSTRUCTIONS.items():
        for s, sp, instruction in entries:
            if s == stage and sp == subplane:
                result.append((tool_name, instruction))
    return result
