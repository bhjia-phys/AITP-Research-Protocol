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


# Domain-skill mapping: maps domain_id (from domain-manifest files) to the
# AITP skill that encodes its conventions. New domains just add an entry here.
DOMAIN_ID_TO_SKILL: dict[str, str] = {
    "abacus-librpa": "skill-librpa",
}

# Legacy slug-based fallback: used when no domain manifest is present.
# Only needed for topics created before the contract-based mechanism.
_SLUG_FALLBACK_PATTERNS: dict[str, str] = {
    "librpa": "skill-librpa",
    "crpa": "skill-librpa",
    "scrpa": "skill-librpa",
    "qsgw": "skill-librpa",
    "gw-topology": "skill-librpa",
}


def _detect_domains_from_contracts(topic_root_path: Path) -> list[str]:
    """Scan topic's contracts/ for domain manifests, return domain_ids.

    Supports two formats:
    1. contracts/domain-manifest.md — AITP native (YAML frontmatter with domain_id)
    2. contracts/domain-manifest.<domain_id>.json — multi-domain convention
    """
    contracts_dir = topic_root_path / "contracts"
    if not contracts_dir.is_dir():
        return []
    domain_ids = []

    # Format 1: domain-manifest.md (AITP native, used by aitp_bind_repo etc.)
    md_path = contracts_dir / "domain-manifest.md"
    if md_path.exists():
        text = md_path.read_text(encoding="utf-8")
        m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
        if m:
            import yaml
            try:
                fm = yaml.safe_load(m.group(1)) or {}
            except Exception:
                fm = {}
            did = fm.get("domain_id")
            if did:
                domain_ids.append(str(did))

    # Format 2: domain-manifest.<domain_id>.json (oh-my-LibRPA multi-domain)
    for manifest_path in contracts_dir.glob("domain-manifest.*.json"):
        stem = manifest_path.stem
        parts = stem.split(".", 1)
        if len(parts) == 2 and parts[0] == "domain-manifest":
            domain_ids.append(parts[1])

    # Deduplicate while preserving order
    seen = set()
    return [d for d in domain_ids if not (d in seen or seen.add(d))]


def _detect_domains_from_state(topic_root_path: Path) -> list[str]:
    """Read the 'domains' field from state.md frontmatter if present."""
    state_path = topic_root_path / "state.md"
    if not state_path.exists():
        return []
    text = state_path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return []
    import yaml
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except Exception:
        return []
    domains = fm.get("domains", [])
    if isinstance(domains, list):
        return [str(d) for d in domains]
    if isinstance(domains, str):
        return [domains]
    return []


def resolve_domain_prerequisites(topic_root_path: Path, topic_slug: str = "") -> list[str]:
    """Return domain skills that must be loaded for the given topic.

    Detection order (first match wins, all sources are merged):
    1. domain-manifest.*.json files in topic's contracts/ directory
    2. 'domains' field in state.md frontmatter
    3. Legacy slug-pattern fallback
    """
    skills = []

    # 1. Contract-based detection (robust, content-driven)
    domain_ids = _detect_domains_from_contracts(topic_root_path)
    for did in domain_ids:
        skill = DOMAIN_ID_TO_SKILL.get(did)
        if skill:
            skills.append(skill)

    # 2. State frontmatter detection
    state_domains = _detect_domains_from_state(topic_root_path)
    for did in state_domains:
        skill = DOMAIN_ID_TO_SKILL.get(did)
        if skill and skill not in skills:
            skills.append(skill)

    # 3. Legacy slug fallback
    if not skills and topic_slug:
        slug_lower = topic_slug.lower()
        for pattern, skill in _SLUG_FALLBACK_PATTERNS.items():
            if pattern in slug_lower and skill not in skills:
                skills.append(skill)

    return skills


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
    # Determine discovery mode from state.md to select the right skill
    state_fm, _ = parse_md(topic_root_path / "state.md")
    mode = state_fm.get("mode", "explore")
    # skill-deep-research is optional. Fall back to skill-discover if not deployed.
    _deep_research_skill = "skill-deep-research" if mode == "deep_research" else None
    skill = _deep_research_skill or "skill-discover"

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
                skill=skill,
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
                skill=skill,
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
                skill=skill,
            )

    return StageSnapshot(
        stage="L0",
        posture="discover",
        lane=lane,
        gate_status="ready",
        next_allowed_transition="L1",
        skill=skill,
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
            "competing_hypotheses": "",
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
        },
        "# Source TOC Map\n\n## Per-Source TOC\n\n"
        "## Coverage Summary\n\n## Deferred Sections\n\n## Extraction Notes\n",
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

# ---------------------------------------------------------------------------
# L1 gate evaluation
# ---------------------------------------------------------------------------

def _missing_frontmatter_keys(frontmatter: dict[str, object], required: list[str]) -> list[str]:
    return [key for key in required if not str(frontmatter.get(key, "")).strip()]


def _missing_required_headings(body: str, headings: list[str]) -> list[str]:
    return [h for h in headings if h not in body]


_QUESTION_STEMS = [
    "what", "how does", "why", "under what conditions",
    "derive", "compute", "estimate", "prove", "calculate",
    "determine", "predict", "explain", "compare", "evaluate",
]


def _check_question_semantic_validity(
    fm: dict[str, object], body: str
) -> list[str]:
    """Check that the bounded question is structurally well-posed.

    Returns a list of missing requirements (empty = valid).
    Checks are structural, not qualitative — we don't judge whether it's
    a "good" question, only whether it has the necessary form.
    """
    issues: list[str] = []
    question = str(fm.get("bounded_question", "")).strip().lower()
    scope = str(fm.get("scope_boundaries", "")).strip().lower()
    targets = str(fm.get("target_quantities", "")).strip()

    if question:
        has_stem = any(stem in question for stem in _QUESTION_STEMS)
        if not has_stem:
            issues.append(
                "bounded_question must contain a question stem "
                "(e.g. 'what is', 'derive', 'compute', 'estimate', 'determine'). "
                f"Got: '{str(fm.get('bounded_question', ''))[:100]}'"
            )

    if not scope or "not" not in scope:
        issues.append(
            "scope_boundaries must identify at least one explicit exclusion "
            "(e.g. 'This question does NOT ask about...'). "
            "Without boundaries the question is unbounded."
        )

    if not targets:
        issues.append(
            "target_quantities must name at least one physically measurable "
            "or calculable quantity with units or dimensionless characterization."
        )

    # Competing hypotheses check
    competing = str(fm.get("competing_hypotheses", "")).strip()
    if not competing:
        issues.append(
            "competing_hypotheses must name at least one alternative hypothesis "
            "or prior explanation. State what other answers exist and why they "
            "might be wrong. This prevents tunnel vision."
        )

    # Non-Success Conditions check
    if "## Non-Success Conditions" in body:
        nsc_start = body.index("## Non-Success Conditions")
        nsc_end = body.find("##", nsc_start + 1)
        nsc_section = body[nsc_start:nsc_end] if nsc_end > 0 else body[nsc_start:]
        nsc_content = nsc_section.split("\n", 1)[1].strip() if "\n" in nsc_section else ""
        if not nsc_content or len(nsc_content) < 20:
            issues.append(
                "## Non-Success Conditions must describe at least one specific "
                "failure mode (not generic text). Describe what would falsify "
                "or invalidate the expected answer."
            )

    return issues


def _generate_physics_next_action(
    parse_md: Callable[[Path], tuple[dict[str, Any], str]],
    topic_root_path: Path,
    stage: str,
    gate_status: str,
) -> str:
    """Generate a physics-contentful next action prompt.

    When gate is ready, produce a prompt grounded in the topic's question
    contract and domain context. When blocked, describe what needs fixing.
    """
    if gate_status != "ready":
        return ""

    question_path = topic_root_path / "L1" / "question_contract.md"
    if not question_path.exists():
        return ""

    q_fm, _ = parse_md(question_path)
    question = str(q_fm.get("bounded_question", "")).strip()
    scope = str(q_fm.get("scope_boundaries", "")).strip()
    targets = str(q_fm.get("target_quantities", "")).strip()

    if not question:
        return ""

    parts = [f"Your question: {question}"]
    if targets:
        parts.append(f"Key observable: {targets}")
    if scope:
        parts.append(f"Explicitly excluded: {scope}")
    parts.append(
        "Proceed to the next stage, or refine the question first if "
        "the scope or target still feels vague."
    )
    return "\n".join(parts)


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

    # Question semantic validity: check the question is genuinely well-posed
    question_path = topic_root_path / "L1" / "question_contract.md"
    if question_path.exists():
        q_fm, q_body = parse_md(question_path)
        sem_issues = _check_question_semantic_validity(q_fm, q_body)
        if sem_issues:
            return StageSnapshot(
                stage="L1",
                posture="read",
                lane=lane,
                gate_status="blocked_missing_field",
                required_artifact_path=str(question_path),
                missing_requirements=sem_issues,
                next_allowed_transition="L1",
                skill="skill-read",
            )

    # Coverage gate: source_toc_map must indicate full extraction or explicit deferrals
    toc_path = topic_root_path / "L1" / "source_toc_map.md"
    if toc_path.exists():
        toc_fm, toc_body = parse_md(toc_path)
        cov = str(toc_fm.get("coverage_status", "")).strip().lower()
        if cov not in ("complete", "partial_with_deferrals"):
            return StageSnapshot(
                stage="L1",
                posture="read",
                lane=lane,
                gate_status="blocked_coverage_incomplete",
                required_artifact_path=str(toc_path),
                missing_requirements=[
                    "coverage_status must be 'complete' or 'partial_with_deferrals' "
                    f"(got '{cov or '(empty)'}'). Extract or defer all source sections."
                ],
                next_allowed_transition="L1",
                skill="skill-read",
            )
        # If partial_with_deferrals, require at least one deferred section documented
        if cov == "partial_with_deferrals" and "## Deferred Sections" not in toc_body:
            return StageSnapshot(
                stage="L1",
                posture="read",
                lane=lane,
                gate_status="blocked_coverage_incomplete",
                required_artifact_path=str(toc_path),
                missing_requirements=[
                    "coverage_status is 'partial_with_deferrals' but ## Deferred Sections "
                    "heading is missing. Document which sections are deferred and why."
                ],
                next_allowed_transition="L1",
                skill="skill-read",
            )
        # Intake quality audit: extracted sections must have non-trivial intake notes
        intake_dir = topic_root_path / "L1" / "intake"
        if intake_dir.is_dir():
            extracted = toc_body.count("— status: extracted")
            intake_notes = list(intake_dir.rglob("*.md"))
            if extracted > 0 and len(intake_notes) < extracted:
                return StageSnapshot(
                    stage="L1",
                    posture="read",
                    lane=lane,
                    gate_status="blocked_coverage_incomplete",
                    required_artifact_path=str(intake_dir),
                    missing_requirements=[
                        f"{extracted} sections marked extracted but only "
                        f"{len(intake_notes)} intake notes found under L1/intake/. "
                        "Create an intake note for each extracted section via "
                        "aitp_write_section_intake."
                    ],
                    next_allowed_transition="L1",
                    skill="skill-read",
                )
            # Check that intake notes for extracted sections have completeness_confidence
            low_confidence = []
            for note_path in intake_notes:
                nfm, _ = parse_md(note_path)
                conf = str(nfm.get("completeness_confidence", "")).strip().lower()
                if conf == "low":
                    low_confidence.append(note_path.stem)
            if low_confidence:
                return StageSnapshot(
                    stage="L1",
                    posture="read",
                    lane=lane,
                    gate_status="blocked_coverage_incomplete",
                    required_artifact_path=str(intake_dir),
                    missing_requirements=[
                        f"Low completeness_confidence in intake notes: "
                        f"{', '.join(low_confidence[:5])}. "
                        "Re-read these sections or explicitly defer them."
                    ],
                    next_allowed_transition="L1",
                    skill="skill-read",
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

# ---------------------------------------------------------------------------
# L3 flexible workspace — no forced mode or subplane sequence
# ---------------------------------------------------------------------------

L3_ACTIVITIES = [
    "ideate", "plan", "derive", "trace-derivation",
    "gap-audit", "connect", "integrate", "distill",
]

L3_ACTIVITY_TEMPLATES: dict[str, tuple[str, dict[str, Any], str]] = {
    "ideate": (
        "ideate",
        {"artifact_kind": "l3_active_idea", "activity": "ideate",
         "required_fields": ["idea_statement", "motivation"],
         "idea_statement": "", "motivation": ""},
        "# Active Idea\n\n## Idea Statement\n\n## Motivation\n\n"
        "## Prior Work (L2 Check)\n\n## Risk Assessment\n",
    ),
    "plan": (
        "plan",
        {"artifact_kind": "l3_active_plan", "activity": "plan",
         "required_fields": ["plan_statement", "derivation_route"],
         "plan_statement": "", "derivation_route": ""},
        "# Active Plan\n\n## Plan Statement\n\n## Derivation Route\n\n"
        "## Tool And Knowledge Requirements\n\n## Risk Assessment\n",
    ),
    "derive": (
        "derive",
        {"artifact_kind": "l3_active_derivation", "activity": "derive",
         "required_fields": ["derivation_count", "all_steps_justified"],
         "derivation_count": 0, "all_steps_justified": ""},
        "# Active Derivation\n\n## Derivation Chains\n\n"
        "## Step-by-Step Trace\n\n## Feynman Self-Check\n\n## Unresolved Steps\n",
    ),
    "trace-derivation": (
        "trace-derivation",
        {"artifact_kind": "l3_active_trace", "activity": "trace-derivation",
         "required_fields": ["source_id", "derivation_count"],
         "source_id": "", "derivation_count": 0},
        "# Active Trace\n\n## Source Reference\n\n## Derivation Chains\n\n"
        "## Step-by-Step Trace\n\n## Justification Gaps\n",
    ),
    "gap-audit": (
        "gap-audit",
        {"artifact_kind": "l3_active_gaps", "activity": "gap-audit",
         "required_fields": ["gap_count", "blocking_gaps"],
         "gap_count": 0, "blocking_gaps": ""},
        "# Active Gap Audit\n\n## Unstated Assumptions\n\n"
        "## Approximation Regimes\n\n## Correspondence Check\n\n"
        "## Prerequisite Gaps\n\n## Severity Assessment\n",
    ),
    "connect": (
        "connect",
        {"artifact_kind": "l3_active_connect", "activity": "connect",
         "required_fields": ["connection_summary"],
         "connection_summary": ""},
        "# Active Connection\n\n## Concepts Being Connected\n\n"
        "## Proposed Edges\n\n## Evidence\n\n## Trust Assessment\n",
    ),
    "integrate": (
        "integrate",
        {"artifact_kind": "l3_active_integration", "activity": "integrate",
         "required_fields": ["integration_statement", "findings"],
         "integration_statement": "", "findings": ""},
        "# Active Integration\n\n## Integration Statement\n\n## Findings\n\n"
        "## Consistency Checks\n\n## Gaps Remaining\n",
    ),
    "distill": (
        "distill",
        {"artifact_kind": "l3_active_distillation", "activity": "distill",
         "required_fields": ["distilled_claim", "evidence_summary"],
         "distilled_claim": "", "evidence_summary": ""},
        "# Active Distillation\n\n## Distilled Claim\n\n## Evidence Summary\n\n"
        "## Confidence Level\n\n## Open Questions\n",
    ),
}

L3_ACTIVITY_ARTIFACT_NAMES: dict[str, str] = {
    "ideate": "active_idea.md",
    "plan": "active_plan.md",
    "derive": "active_derivation.md",
    "trace-derivation": "active_trace.md",
    "gap-audit": "active_gaps.md",
    "connect": "active_connect.md",
    "integrate": "active_integration.md",
    "distill": "active_distillation.md",
}

# Backwards-compat aliases for flow notebook and legacy tools.
L3_SUBPLANES = L3_ACTIVITIES
L3_ACTIVE_ARTIFACT_NAMES = L3_ACTIVITY_ARTIFACT_NAMES
STUDY_L3_SUBPLANES = ["source_decompose", "step_derive", "gap_audit", "synthesis"]
STUDY_L3_ACTIVE_ARTIFACT_NAMES = {
    "source_decompose": "active_decomposition.md",
    "step_derive": "active_derivation.md",
    "gap_audit": "active_gaps.md",
    "synthesis": "active_synthesis.md",
}

L3_ACTIVITY_SKILL_MAP: dict[str, str] = {
    "ideate": "skill-l3-ideate",
    "plan": "skill-l3-plan",
    "derive": "skill-l3-analyze",
    "trace-derivation": "skill-l3-step-derive",
    "gap-audit": "skill-l3-gap-audit",
    "connect": "skill-l3-analyze",
    "integrate": "skill-l3-integrate",
    "distill": "skill-l3-distill",
}

L3_ACTIVITY_REQUIRED_HEADINGS: dict[str, list[str]] = {
    "ideate": ["## Idea Statement", "## Motivation"],
    "plan": ["## Plan Statement", "## Derivation Route"],
    "derive": ["## Derivation Chains", "## Step-by-Step Trace"],
    "trace-derivation": ["## Source Reference", "## Derivation Chains"],
    "gap-audit": ["## Unstated Assumptions", "## Correspondence Check"],
    "connect": ["## Concepts Being Connected", "## Proposed Edges"],
    "integrate": ["## Integration Statement", "## Findings"],
    "distill": ["## Distilled Claim", "## Evidence Summary"],
}

STUDY_CANDIDATE_TYPES = [
    "atomic_concept", "derivation_chain", "correspondence_link",
    "regime_boundary", "open_question",
]


def evaluate_l3_stage(
    parse_md: Callable[[Path], tuple[dict[str, Any], str]],
    topic_root_path: Path,
    lane: str = "unspecified",
) -> StageSnapshot:
    """Evaluate L3 gate status. L3 is a flexible workspace — any activity
    can be entered at any time. The gate checks that the current activity's
    artifact exists and is filled."""
    state_fm, _ = parse_md(topic_root_path / "state.md")
    current_activity = str(state_fm.get("l3_activity", "")).strip() or "ideate"

    if current_activity not in L3_ACTIVITIES:
        return StageSnapshot(
            stage="L3", posture="derive", lane=lane,
            gate_status="blocked_missing_artifact",
            required_artifact_path="",
            missing_requirements=[f"unknown activity '{current_activity}'. Valid: {L3_ACTIVITIES}"],
            next_allowed_transition="", skill="skill-l3-ideate",
            l3_subplane=current_activity, l3_mode="",
        )

    artifact_name = L3_ACTIVITY_ARTIFACT_NAMES.get(current_activity, f"active_{current_activity}.md")
    artifact_path = topic_root_path / "L3" / current_activity / artifact_name
    skill = L3_ACTIVITY_SKILL_MAP.get(current_activity, "skill-l3-ideate")

    template_info = L3_ACTIVITY_TEMPLATES.get(current_activity)
    if template_info is None:
        return StageSnapshot(
            stage="L3", posture="derive", lane=lane,
            gate_status="blocked_missing_artifact",
            required_artifact_path=str(artifact_path),
            missing_requirements=[f"no template for activity '{current_activity}'"],
            next_allowed_transition="", skill=skill,
            l3_subplane=current_activity, l3_mode="",
        )

    _, template_fm, _ = template_info
    req_fields = [f for f in template_fm.get("required_fields", [])]
    req_headings = L3_ACTIVITY_REQUIRED_HEADINGS.get(current_activity, [])

    if not artifact_path.exists():
        return StageSnapshot(
            stage="L3", posture="derive", lane=lane,
            gate_status="blocked_missing_artifact",
            required_artifact_path=str(artifact_path),
            missing_requirements=[artifact_name],
            next_allowed_transition="",
            skill=skill,
            l3_subplane=current_activity, l3_mode="",
        )

    fm, body = parse_md(artifact_path)
    missing = (
        _missing_frontmatter_keys(fm, req_fields)
        + _missing_required_headings(body, req_headings)
    )
    if missing:
        return StageSnapshot(
            stage="L3", posture="derive", lane=lane,
            gate_status="blocked_missing_field",
            required_artifact_path=str(artifact_path),
            missing_requirements=missing,
            next_allowed_transition="",
            skill=skill,
            l3_subplane=current_activity, l3_mode="",
        )

    # L3 is ready when at least one activity artifact is complete.
    # Any activity can lead to L4 — there is no "last subplane".
    return StageSnapshot(
        stage="L3", posture="derive", lane=lane,
        gate_status="ready",
        next_allowed_transition="L4",
        skill=skill,
        l3_subplane=current_activity, l3_mode="",
    )


# ---------------------------------------------------------------------------
# L2 knowledge graph constants
# ---------------------------------------------------------------------------

L2_NODE_TYPES = [
    # Core knowledge types
    "concept", "theorem", "technique", "derivation_chain",
    "result", "approximation", "open_question", "regime_boundary",
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
    "depends_on_steps": [],
    "depends_on_nodes": [],
    "approximation": "",
    "regime_condition": "",
    "source_ref": "",
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
]


def _load_manifest(topic_root_path: Path) -> dict[str, Any] | None:
    """Load domain-manifest.md from topic's contracts/ directory."""
    manifest_path = topic_root_path / "contracts" / "domain-manifest.md"
    if not manifest_path.exists():
        return None
    try:
        text = manifest_path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            return None
        end = text.find("---", 3)
        if end == -1:
            return None
        import yaml
        data = yaml.safe_load(text[3:end])
        if data and ("domain_id" in data or "repo_ref" in data):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def evaluate_l4_stage(
    parse_md: Callable[[Path], tuple[dict[str, Any], str]],
    topic_root_path: Path,
    lane: str = "unspecified",
) -> StageSnapshot:
    """Evaluate L4 gate status by checking candidates and reviews (v3).

    L4 is entered when the agent has completed the L3 subplane cycle and
    begins validating candidates. Gate checks:
    - At least one candidate submitted
    - At least one L4 review filed for each candidate being promoted
    - Domain invariants checked (if domain-manifest.json exists)
    """
    cand_dir = topic_root_path / "L3" / "candidates"
    review_dir = topic_root_path / "L4" / "reviews"

    submitted = list(cand_dir.glob("*.md")) if cand_dir.is_dir() else []
    if not submitted:
        return StageSnapshot(
            stage="L4", posture="verify", lane=lane,
            gate_status="blocked_missing_artifact",
            required_artifact_path=str(cand_dir),
            missing_requirements=["at least one submitted candidate"],
            next_allowed_transition="L3",
            skill="skill-validate",
        )

    # Check which submitted candidates have reviews
    unreviewed = []
    for cand_path in submitted:
        slug = cand_path.stem
        review_path = review_dir / f"{slug}.md"
        if not review_path.exists():
            unreviewed.append(slug)

    if unreviewed:
        return StageSnapshot(
            stage="L4", posture="verify", lane=lane,
            gate_status="blocked_missing_artifact",
            required_artifact_path=str(review_dir / unreviewed[0]),
            missing_requirements=[f"L4 review for {u}" for u in unreviewed],
            next_allowed_transition="L3",
            skill="skill-validate",
        )

    # Check if any candidate is validated
    validated = []
    for cand_path in submitted:
        fm, _ = parse_md(cand_path)
        if fm.get("status") == "validated":
            validated.append(cand_path.stem)

    if not validated:
        return StageSnapshot(
            stage="L4", posture="verify", lane=lane,
            gate_status="blocked_missing_field",
            required_artifact_path=str(submitted[0]),
            missing_requirements=["at least one validated candidate"],
            next_allowed_transition="L3",
            skill="skill-validate",
        )

    # Adversarial counterargument check: every review must challenge at least one claim
    for cand_path in submitted:
        slug = cand_path.stem
        review_path = review_dir / f"{slug}.md"
        if review_path.exists():
            _, rev_body = parse_md(review_path)
            has_counter = (
                "## Counterargument" in rev_body
                or "## Limitations Identified" in rev_body
                or "## Devil's Advocate" in rev_body
            )
            if not has_counter:
                return StageSnapshot(
                    stage="L4", posture="verify", lane=lane,
                    gate_status="blocked_missing_field",
                    required_artifact_path=str(review_path),
                    missing_requirements=[
                        f"L4 review for {slug} must include a counterargument: "
                        "## Counterargument, ## Limitations Identified, or "
                        "## Devil's Advocate section that challenges at least "
                        "one specific claim from the candidate."
                    ],
                    next_allowed_transition="L3",
                    skill="skill-validate",
                )

    # Domain invariant checks (if domain manifest exists)
    manifest = _load_manifest(topic_root_path)
    if manifest:
        invariants = manifest.get("invariants", [])
        invariant_results_path = topic_root_path / "L4" / "invariant-checks.md"
        if not invariant_results_path.exists():
            invariant_ids = [inv.get("id", "unknown") for inv in invariants]
            return StageSnapshot(
                stage="L4", posture="verify", lane=lane,
                gate_status="blocked_missing_artifact",
                required_artifact_path=str(invariant_results_path),
                missing_requirements=[f"domain invariant check: {iid}" for iid in invariant_ids],
                next_allowed_transition="L3",
                skill="skill-validate",
            )
        inv_fm, inv_body = parse_md(invariant_results_path)
        unchecked = []
        for inv in invariants:
            inv_id = inv.get("id", "")
            if inv_id and inv_id not in inv_body:
                unchecked.append(inv_id)
        if unchecked:
            return StageSnapshot(
                stage="L4", posture="verify", lane=lane,
                gate_status="blocked_missing_field",
                required_artifact_path=str(invariant_results_path),
                missing_requirements=[f"domain invariant result for: {uid}" for uid in unchecked],
                next_allowed_transition="L3",
                skill="skill-validate",
            )

    # Contradiction detection: scan reviews for contradiction outcomes.
    # Contradiction with known results is the highest-value signal in L4.
    conflicts = []
    for cand_path in submitted:
        slug = cand_path.stem
        review_path = review_dir / f"{slug}.md"
        if review_path.exists():
            rfm, _ = parse_md(review_path)
            if rfm.get("outcome") == "contradiction":
                conflicts.append(slug)
    if conflicts:
        return StageSnapshot(
            stage="L4", posture="verify", lane=lane,
            gate_status="blocked_contradiction",
            required_artifact_path=str(review_dir / conflicts[0]),
            missing_requirements=[
                f"Review for {c} reports CONTRADICTION with known results. "
                f"Resolve: (a) new physics found, (b) error in derivation, "
                f"or (c) regime mismatch between claimed and actual validity."
                for c in conflicts
            ],
            next_allowed_transition="L3",
            skill="skill-validate",
        )

    return StageSnapshot(
        stage="L4", posture="verify", lane=lane,
        gate_status="ready",
        next_allowed_transition="L2",
        skill="skill-promote",
    )


def evaluate_l5_stage(
    parse_md: Callable[[Path], tuple[dict[str, Any], str]],
    topic_root_path: Path,
    lane: str = "unspecified",
) -> StageSnapshot:
    """Evaluate L5 gate status by checking writing scaffolds and promoted candidates.

    Gate checks:
    - L5_writing scaffolds exist (outline.md, claim_evidence_map.md, limitations.md)
    - At least one candidate promoted to global L2
    """
    l5_dir = topic_root_path / "L5_writing"
    if not l5_dir.is_dir():
        return StageSnapshot(
            stage="L5", posture="write", lane=lane,
            gate_status="blocked_missing_artifact",
            required_artifact_path=str(l5_dir),
            missing_requirements=["L5_writing directory"],
            next_allowed_transition="L4",
            skill="skill-write",
        )

    required = ["outline.md", "claim_evidence_map.md", "limitations.md"]
    for name in required:
        path = l5_dir / name
        if not path.exists():
            return StageSnapshot(
                stage="L5", posture="write", lane=lane,
                gate_status="blocked_missing_artifact",
                required_artifact_path=str(path),
                missing_requirements=[name],
                next_allowed_transition="",
                skill="skill-write",
            )

    return StageSnapshot(
        stage="L5", posture="write", lane=lane,
        gate_status="ready",
        next_allowed_transition="L2",
        skill="skill-write",
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
    # L3 study mode — literature understanding subplanes
    ("L3_study", "source_decompose"): [
        ("arxiv-latex-mcp", "Read paper sections for decomposition", "A"),
        ("knowledge-hub", "Check existing L2 concepts for overlap", "C"),
    ],
    ("L3_study", "step_derive"): [
        ("arxiv-latex-mcp", "Reference derivation steps from source", "A"),
        ("jupyter-mcp-server", "Symbolic verification of derivation steps (SymPy)", "A"),
        ("knowledge-hub", "Query prerequisite concepts from L2", "A"),
    ],
    ("L3_study", "gap_audit"): [
        ("arxiv-latex-mcp", "Cross-check claims against source", "A"),
        ("knowledge-hub", "Check L2 for correspondence targets", "C"),
    ],
    ("L3_study", "synthesis"): [
        ("knowledge-hub", "Write synthesized knowledge to L2", "C"),
        ("arxiv-latex-mcp", "Final verification against source", "A"),
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


# ---------------------------------------------------------------------------
# Semantic search — physics concept aliases and token-aware matching
# ---------------------------------------------------------------------------

PHYSICS_CONCEPT_ALIASES: dict[str, list[str]] = {
    # Many-body methods
    "rpa": ["random phase approximation"],
    "random phase approximation": ["rpa"],
    "crpa": ["canonical random phase approximation"],
    "canonical random phase approximation": ["crpa"],
    "scrpa": ["self-consistent random phase approximation", "sc-rpa"],
    "self-consistent random phase approximation": ["scrpa", "sc-rpa"],
    "gw": ["g0w0", "gw approximation"],
    "g0w0": ["gw"],
    "qsGW": ["quasiparticle self-consistent gw", "qs-gw"],
    "quasiparticle self-consistent gw": ["qsGW", "qs-gw"],
    "bse": ["bethe-salpeter equation"],
    "bethe-salpeter equation": ["bse"],
    # Density functional
    "dft": ["density functional theory"],
    "density functional theory": ["dft"],
    "lda": ["local density approximation"],
    "local density approximation": ["lda"],
    "gga": ["generalized gradient approximation"],
    "generalized gradient approximation": ["gga"],
    "tddft": ["time-dependent density functional theory"],
    "time-dependent density functional theory": ["tddft"],
    # Quantum field theory
    "qft": ["quantum field theory"],
    "quantum field theory": ["qft"],
    "qed": ["quantum electrodynamics"],
    "quantum electrodynamics": ["qed"],
    "qcd": ["quantum chromodynamics"],
    "quantum chromodynamics": ["qcd"],
    "eft": ["effective field theory"],
    "effective field theory": ["eft"],
    "rg": ["renormalization group"],
    "renormalization group": ["rg"],
    "frg": ["functional renormalization group"],
    "functional renormalization group": ["frg"],
    "dmrg": ["density matrix renormalization group"],
    "density matrix renormalization group": ["dmrg"],
    # Condensed matter
    "sc": ["self-consistent", "superconducting"],
    "bcs": ["bardeen-cooper-schrieffer"],
    "hubbard model": ["hubbard hamiltonian"],
    "heisenberg model": ["heisenberg hamiltonian"],
    "ising model": ["ising hamiltonian"],
    "ssh": ["su-schrieffer-heeger"],
    # Quantum information
    "vm": ["von neumann"],
    "mipt": ["measurement-induced phase transition"],
    "measurement-induced phase transition": ["mipt"],
    "lqg": ["loop quantum gravity"],
    "loop quantum gravity": ["lqg"],
    "entanglement entropy": ["von neumann entropy", "ee"],
    # Green's functions
    "gf": ["green's function", "green function"],
    "green's function": ["gf", "green function", "propagator"],
    "propagator": ["green's function", "gf"],
    "self-energy": ["self energy"],
    "dyson equation": ["dyson's equation"],
    # Geometry / topology
    "berry phase": ["geometric phase", "berry connection"],
    "chern number": ["chern invariant", "tknn invariant"],
    "chern insulator": ["quantum anomalous hall"],
    # Computational
    "vasp": ["vienna ab initio simulation package"],
    "qe": ["quantum espresso"],
    "wannier": ["wannier90", "maximally localized wannier functions"],
    "lcao": ["linear combination of atomic orbitals"],
    "paw": ["projector augmented wave"],
}

LATEX_NORM_RE = re.compile(r'\s+')


def normalize_latex(expr: str) -> str:
    """Normalize a LaTeX expression for comparison: collapse whitespace, unify braces."""
    if not expr:
        return ""
    s = expr.strip()
    s = s.replace('\\left', '').replace('\\right', '')
    s = s.replace('{', ' ').replace('}', ' ')
    s = s.replace('[', ' ').replace(']', ' ')
    s = s.replace('(', ' ').replace(')', ' ')
    s = ' '.join(s.split())
    return s.lower()


_ALIAS_LOOKUP: dict[str, list[str]] = {}
for _abbr, _expansions in PHYSICS_CONCEPT_ALIASES.items():
    _key = _abbr.lower()
    if _key not in _ALIAS_LOOKUP:
        _ALIAS_LOOKUP[_key] = []
    _ALIAS_LOOKUP[_key].extend(e.lower() for e in _expansions)


def tokenize_for_search(text: str) -> set[str]:
    """Split text into searchable tokens including concept expansions."""
    if not text:
        return set()
    tokens = set()
    # Split on common delimiters
    for part in re.split(r'[\s,;:.!?()\[\]{}]+', text.lower()):
        part = part.strip('"\'`-_=+*&^%$#@!~<>/\\|')
        if part and len(part) >= 2:
            tokens.add(part)
            # Add alias expansions
            if part in _ALIAS_LOOKUP:
                for alias in _ALIAS_LOOKUP[part]:
                    tokens.add(alias)
                    # Also add individual words from multi-word aliases
                    for alias_word in alias.split():
                        if len(alias_word) >= 2:
                            tokens.add(alias_word)
    # Also add multi-word phrase as single token
    text_lower = text.lower().strip()
    if ' ' in text_lower:
        tokens.add(text_lower)
    return tokens


def semantic_score(query: str, content_fields: list[str]) -> float:
    """Compute relevance score between query and content using token overlap.

    Returns 0.0-1.0 where 1.0 is perfect match.
    Query tokens are matched against each content field; matches in shorter
    fields (like title) are weighted higher than matches in long body text.
    """
    if not query:
        return 0.0
    query_tokens = tokenize_for_search(query)
    if not query_tokens:
        return 0.0

    best_score = 0.0
    for field_text in content_fields:
        if not field_text:
            continue
        field_tokens = tokenize_for_search(field_text)
        if not field_tokens:
            continue
        overlap = query_tokens & field_tokens
        if not overlap:
            continue
        # Jaccard-like: |intersection| / |query|
        recall = len(overlap) / len(query_tokens)
        # Precision: how much of the field matched
        precision = len(overlap) / len(field_tokens)
        # F1-like score
        if recall + precision > 0:
            score = 2 * recall * precision / (recall + precision)
        else:
            score = 0.0
        # Bonus for exact phrase match
        query_lower = query.lower().strip()
        if query_lower in field_text.lower():
            score = max(score, 0.85)
        # Bonus for normalized LaTeX match
        if '$' in query and '$' in field_text:
            q_latex = normalize_latex(query)
            f_latex = normalize_latex(field_text)
            if q_latex and f_latex and q_latex in f_latex:
                score = max(score, 0.9)
        best_score = max(best_score, score)

    return best_score
