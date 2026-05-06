"""Stage gate evaluation functions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from brain.state import StageSnapshot, L3_ACTIVITIES, L3_ACTIVITY_ARTIFACT_NAMES, L3_ACTIVITY_REQUIRED_HEADINGS, L3_ACTIVITY_TEMPLATES, L3_ACTIVITY_SKILL_MAP, PHYSICS_CHECK_FIELDS, _LANE_PHYSICS_CHECK_FIELDS
from brain.contracts import _L0_CONTRACTS, _L1_INTENSITY_CONTRACTS, _L1_CONTRACTS
from brain.checks import _missing_frontmatter_keys, _missing_required_headings, _check_heading_content, _check_question_semantic_validity, _extract_domain_rules
from brain.physicist import _check_physicist_l2_lookup, _check_physicist_correspondence, _check_physicist_anomalies
from brain.domains import _detect_domains_from_contracts, _detect_domains_from_state, resolve_domain_prerequisites, DOMAIN_ID_TO_SKILL, _SLUG_FALLBACK_PATTERNS


# -- L0 gate --

def evaluate_l0_stage(
    parse_md: Callable[[Path], tuple[dict[str, Any], str]],
    topic_root_path: Path,
    lane: str = "unspecified",
) -> StageSnapshot:
    """Evaluate L0 gate status by checking source registry and registered sources."""
    state_fm, _ = parse_md(topic_root_path / "state.md")
    skill = "skill-discover"

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
        # Content check: ## Prior L2 Knowledge — must state what L2 already knows
        if not _check_heading_content(body, "## Prior L2 Knowledge", min_chars=50):
            return StageSnapshot(
                stage="L0", posture=posture, lane=lane,
                gate_status="blocked_missing_field",
                required_artifact_path=str(path),
                missing_requirements=[
                    "## Prior L2 Knowledge must record what L2 already knows about this topic "
                    "(even if the answer is 'no prior knowledge exists')"
                ],
                next_allowed_transition="L0", skill=skill,
            )

        # Content check: ## Overall Verdict must have substantive content
        if not _check_heading_content(body, "## Overall Verdict", min_chars=200):
            return StageSnapshot(
                stage="L0",
                posture=posture,
                lane=lane,
                gate_status="blocked_missing_field",
                required_artifact_path=str(path),
                missing_requirements=[
                    "## Overall Verdict has insufficient content (need >= 200 chars of substantive assessment)"
                ],
                next_allowed_transition="L0",
                skill=skill,
            )
        # Require at least one registered source (new dir structure or legacy .md)
        src_dir = topic_root_path / "L0" / "sources"
        actual_count = 0
        if src_dir.is_dir():
            for item in src_dir.iterdir():
                if item.is_dir() and (item / "source.md").exists():
                    actual_count += 1
                elif item.is_file() and item.suffix == ".md":
                    actual_count += 1
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


# -- L1 gate --

def evaluate_l1_stage(
    parse_md: Callable[[Path], tuple[dict[str, Any], str]],
    topic_root_path: Path,
    lane: str = "unspecified",
    research_intensity: str = "",
) -> StageSnapshot:
    """Evaluate L1 gate status. Respects research_intensity for contract selection.

    If research_intensity is not explicitly passed, it is read from state.md.
    Falls back to "standard" if not found.
    """
    # Resolve research_intensity: explicit arg > state.md > default
    if not research_intensity:
        try:
            state_path = topic_root_path / "state.md"
            if state_path.exists():
                state_fm, _ = parse_md(state_path)
                research_intensity = str(
                    state_fm.get("research_intensity", "standard")
                ).strip() or "standard"
        except Exception:
            research_intensity = "standard"
    if research_intensity not in ("quick", "standard", "full"):
        research_intensity = "standard"
    # Select contracts based on research intensity
    if research_intensity == "full":
        contracts = _L1_CONTRACTS
    elif research_intensity in _L1_INTENSITY_CONTRACTS:
        contracts = _L1_INTENSITY_CONTRACTS[research_intensity]
    else:
        contracts = _L1_INTENSITY_CONTRACTS["standard"]

    for name, posture, fields, headings in contracts:
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

    # Question semantic validity: check the question is genuinely well-posed.
    # Competing hypotheses and non-success conditions are only required for
    # standard/full intensity; quick mode skips them.
    question_path = topic_root_path / "L1" / "question_contract.md"
    if question_path.exists():
        q_fm, q_body = parse_md(question_path)
        sem_issues = _check_question_semantic_validity(q_fm, q_body, research_intensity)
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
                research_intensity=research_intensity,
            )

    # Coverage gate: only for standard/full intensity.
    if research_intensity in ("standard", "full"):
        toc_path = topic_root_path / "L1" / "source_toc_map.md"
        if toc_path.exists():
            toc_fm, toc_body = parse_md(toc_path)
            total = int(toc_fm.get("total_sections", 0))
            if total == 0:
                return StageSnapshot(
                    stage="L1",
                    posture="read",
                    lane=lane,
                    gate_status="blocked_coverage_incomplete",
                    required_artifact_path=str(toc_path),
                    missing_requirements=[
                        "No sections parsed in source_toc_map (total_sections=0). "
                        "Call aitp_parse_source_toc for each source to register "
                        "its section structure before advancing to L3."
                    ],
                    next_allowed_transition="L1",
                    skill="skill-read",
                    research_intensity=research_intensity,
                )
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
                    research_intensity=research_intensity,
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
                    research_intensity=research_intensity,
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
                        research_intensity=research_intensity,
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
                        research_intensity=research_intensity,
                    )

    # L2 cross-reference check: question_contract must reference prior L2 knowledge
    qc_path = topic_root_path / "L1" / "question_contract.md"
    if qc_path.exists():
        _, qc_body = parse_md(qc_path)
        if "## L2 Cross-Reference" not in qc_body:
            return StageSnapshot(
                stage="L1",
                posture="frame",
                lane=lane,
                gate_status="blocked_missing_field",
                required_artifact_path=str(qc_path),
                missing_requirements=["## L2 Cross-Reference — must record what L2 already knows about this question"],
                next_allowed_transition="L1",
                skill="skill-frame",
                research_intensity=research_intensity,
            )

    # L0→L1 traceability: each L1 artifact must cite which L0 sources it draws from.
    # Read actual L0 source IDs and verify that at least source_basis and
    # derivation_anchor_map have source_refs pointing to real L0 sources.
    l0_sources_dir = topic_root_path / "L0" / "sources"
    actual_l0_ids: set[str] = set()
    if l0_sources_dir.is_dir():
        for d in l0_sources_dir.iterdir():
            if d.is_dir():
                actual_l0_ids.add(d.name)
    if actual_l0_ids:
        traceability_gaps: list[str] = []
        for art_name in ["source_basis.md", "derivation_anchor_map.md",
                          "convention_snapshot.md", "contradiction_register.md"]:
            art_path = topic_root_path / "L1" / art_name
            if not art_path.exists():
                continue
            fm, _ = parse_md(art_path)
            refs = fm.get("source_refs", [])
            if not isinstance(refs, list):
                refs = []
            matched = [r for r in refs if r in actual_l0_ids]
            if not matched:
                traceability_gaps.append(
                    f"{art_name}: source_refs={refs} does not reference any known "
                    f"L0 source {sorted(actual_l0_ids)}"
                )
        if traceability_gaps:
            return StageSnapshot(
                stage="L1",
                posture="frame",
                lane=lane,
                gate_status="blocked_missing_field",
                required_artifact_path=str(topic_root_path / "L1"),
                missing_requirements=traceability_gaps,
                next_allowed_transition="L1",
                skill="skill-frame",
                research_intensity=research_intensity,
            )

    # Auto-generate L1/INDEX.md on gate ready (non-blocking)
    try:
        from brain.flow_notebook import generate_l1_index
        index_content = generate_l1_index(topic_root_path)
        index_path = topic_root_path / "L1" / "INDEX.md"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(index_content, encoding="utf-8")
    except Exception:
        pass  # Index is derivative — never block gate advancement

    return StageSnapshot(
        stage="L1",
        posture="frame",
        lane=lane,
        gate_status="ready",
        next_allowed_transition="L3",
        skill="skill-frame",
        research_intensity=research_intensity,
    )


# -- L3 gate --

# -- L3 cross-activity prerequisite DAG --
# Each downstream activity requires upstream artifacts to have real
# content, not just template scaffolding. The DAG edges are:
#
#   plan ──→ derive ──→ integrate ──→ distill
#                │           ↗
#                ├──────────┘
#                ▼
#           gap-audit ──────────────┘
#
# Activity entry is always allowed (flexible workspace), but the gate
# reports blocked_incomplete when prerequisite content is missing,
# and candidate submission is hard-blocked by cmd_candidate_submit().

def _check_l3_cross_activity_prerequisites(
    parse_md, topic_root_path: Path, current_activity: str,
) -> list[str]:
    """Check that prerequisite upstream activities have real content.

    Returns list of human-readable issue strings. Empty list = all clear.
    """
    issues: list[str] = []
    l3_dir = topic_root_path / "L3"

    def _artifact_has_section(activity: str, heading: str, min_chars: int = 50) -> bool:
        name = L3_ACTIVITY_ARTIFACT_NAMES.get(activity, f"active_{activity}.md")
        path = l3_dir / activity / name
        if not path.exists():
            return False
        _, body = parse_md(path)
        return _check_heading_content(body, heading, min_chars=min_chars)

    def _artifact_path(activity: str) -> Path:
        name = L3_ACTIVITY_ARTIFACT_NAMES.get(activity, f"active_{activity}.md")
        return l3_dir / activity / name

    def _artifact_body(activity: str) -> str:
        path = _artifact_path(activity)
        if not path.exists():
            return ""
        _, body = parse_md(path)
        return body

    # --- derive requires plan ---
    if current_activity in ("derive",):
        if not _artifact_has_section("plan", "## Derivation Route", min_chars=50):
            issues.append(
                "Plan artifact has empty or missing '## Derivation Route'. "
                "Without a derivation route, derivation lacks strategic direction."
            )

    # --- gap-audit requires derive ---
    if current_activity in ("gap-audit",):
        if not _artifact_has_section("derive", "## Derivation Chains", min_chars=50):
            issues.append(
                "Derive artifact has empty or missing '## Derivation Chains'. "
                "Gap audit requires derivation content to audit."
            )

    # --- integrate requires derive AND gap-audit ---
    if current_activity in ("integrate",):
        if not _artifact_has_section("derive", "## Derivation Chains", min_chars=50):
            issues.append(
                "Derive artifact has empty or missing '## Derivation Chains'. "
                "Integration requires derivation content to integrate."
            )
        if not _artifact_has_section("gap-audit", "## Correspondence Check", min_chars=30):
            issues.append(
                "Gap-audit '## Correspondence Check' is empty or missing. "
                "Integration without correspondence checks risks accepting "
                "results that fail known limits."
            )

    # --- distill requires integrate AND gap-audit ---
    if current_activity in ("distill",):
        if not _artifact_has_section("integrate", "## Findings", min_chars=50):
            issues.append(
                "Integrate '## Findings' is empty or missing. "
                "Distillation requires findings to distill."
            )
        if not _artifact_has_section("gap-audit", "## Correspondence Check", min_chars=30):
            issues.append(
                "Gap-audit '## Correspondence Check' is empty or missing. "
                "Distillation without correspondence checks risks promoting "
                "results that fail known limits."
            )

    # --- blocked_incomplete: derive work done but zero candidates ---
    if current_activity in ("integrate", "distill"):
        cand_dir = l3_dir / "candidates"
        candidates = list(cand_dir.glob("*.md")) if cand_dir.is_dir() else []
        if not candidates and _artifact_has_section("derive", "## Derivation Chains", min_chars=80):
            issues.append(
                "Derivation work appears complete but no candidates have been "
                "submitted. Create a candidate via 'aitp derive pack' before "
                "proceeding to L4."
            )

    return issues


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

    # Derivation steps check (was dead code — now wired in v1.0):
    # Verify derivation steps exist and are traceable when activity is derive-related
    derivation_count = 0
    steps_dir = topic_root_path / "L2" / "graph" / "steps"
    if steps_dir.exists():
        derivation_count = len(list(steps_dir.glob("*.md")))

    # Cross-activity prerequisite check:
    # Flexible workspace allows entering any activity, but the gate reports
    # blocked_incomplete when upstream artifacts lack real content.
    cross_issues = _check_l3_cross_activity_prerequisites(
        parse_md, topic_root_path, current_activity,
    )
    if cross_issues:
        return StageSnapshot(
            stage="L3", posture="derive", lane=lane,
            gate_status="blocked_incomplete",
            required_artifact_path="",
            missing_requirements=cross_issues,
            next_allowed_transition="",
            skill=skill,
            l3_subplane=current_activity, l3_mode="",
        )

    # Build domain constraints from domain manifest + domain skill
    domain_constraints = {}
    domain_manifest_path = topic_root_path / "contracts" / "domain-manifest.md"
    if domain_manifest_path.exists():
        dm_fm, _ = parse_md(domain_manifest_path)
        domain_id = str(dm_fm.get("domain_id", "")).strip()
        if domain_id:
            # Check legacy slug patterns
            skill_name = DOMAIN_ID_TO_SKILL.get(domain_id)
            if not skill_name:
                for pattern, s in _SLUG_FALLBACK_PATTERNS.items():
                    if pattern in domain_id:
                        skill_name = s
                        break
            if skill_name:
                skill_path = Path(__file__).parent.parent / "skills" / f"{skill_name}.md"
                if skill_path.exists():
                    domain_constraints = _extract_domain_rules(skill_path, parse_md)

    return StageSnapshot(
        stage="L3", posture="derive", lane=lane,
        gate_status="ready",
        next_allowed_transition="L4",
        skill=skill,
        l3_subplane=current_activity, l3_mode="",
        domain_constraints=domain_constraints,
    )


# -- L4 gate --

def _load_manifest(topic_root_path: Path) -> dict[str, Any] | None:
    """Load domain-manifest from topic's contracts/ directory. Supports .md and .json."""
    # Try .md format first
    manifest_path = topic_root_path / "contracts" / "domain-manifest.md"
    if manifest_path.exists():
        try:
            text = manifest_path.read_text(encoding="utf-8")
            if text.startswith("---"):
                end = text.find("---", 3)
                if end != -1:
                    import yaml
                    data = yaml.safe_load(text[3:end])
                    if data and ("domain_id" in data or "repo_ref" in data):
                        return data
        except Exception:
            pass
    # Try .json format (multi-domain convention)
    contracts_dir = topic_root_path / "contracts"
    if contracts_dir.is_dir():
        for jp in sorted(contracts_dir.glob("domain-manifest.*.json")):
            try:
                import json
                data = json.loads(jp.read_text(encoding="utf-8"))
                if isinstance(data, dict) and ("domain_id" in data or "repo_ref" in data):
                    return data
            except Exception:
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

    # Outcome-based routing: check review outcomes for differentiated handling
    stuck_candidates = []
    timeout_candidates = []
    fail_candidates = []
    for cand_path in submitted:
        slug = cand_path.stem
        review_path = review_dir / f"{slug}.md"
        if review_path.exists():
            rfm, _ = parse_md(review_path)
            outcome = str(rfm.get("outcome", "")).strip()
            if outcome == "stuck":
                stuck_candidates.append(slug)
            elif outcome == "timeout":
                timeout_candidates.append(slug)
            elif outcome == "fail":
                fail_candidates.append(slug)

    if stuck_candidates:
        return StageSnapshot(
            stage="L4", posture="verify", lane=lane,
            gate_status="blocked_stuck",
            required_artifact_path=str(review_dir / stuck_candidates[0]),
            missing_requirements=[
                f"Candidate {c} validation is STUCK. Options: "
                f"(a) switch lane via aitp_switch_lane, "
                f"(b) retreat to L1 and reframe, "
                f"(c) narrow the claim scope."
                for c in stuck_candidates
            ],
            next_allowed_transition="L1",
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

    # Adversarial counterargument check: pass reviews must challenge at least one claim
    for cand_path in submitted:
        slug = cand_path.stem
        review_path = review_dir / f"{slug}.md"
        if review_path.exists():
            rfm, rev_body = parse_md(review_path)
            # Only require counterargument for pass outcomes
            if rfm.get("outcome") == "pass":
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

    # Physics check completeness: every review must cover the required check fields.
    # formal_theory lane requires all 8; other lanes require the original 5.
    _base_checks = PHYSICS_CHECK_FIELDS[:5]
    _required_checks = _LANE_PHYSICS_CHECK_FIELDS.get(lane, _base_checks)
    for cand_path in submitted:
        slug = cand_path.stem
        review_path = review_dir / f"{slug}.md"
        if review_path.exists():
            rfm, _ = parse_md(review_path)
            check_results = rfm.get("check_results", {})
            if isinstance(check_results, dict):
                missing_checks = [
                    f for f in _required_checks
                    if f not in check_results or not str(check_results[f]).strip()
                ]
            else:
                missing_checks = list(_required_checks)
            if missing_checks:
                return StageSnapshot(
                    stage="L4", posture="verify", lane=lane,
                    gate_status="blocked_missing_field",
                    required_artifact_path=str(review_path),
                    missing_requirements=[
                        f"L4 review for {slug} missing physics check: {mc}"
                        for mc in missing_checks
                    ],
                    next_allowed_transition="L3",
                    skill="skill-validate",
                )

    # Domain invariant checks (if domain manifest exists with invariants)
    manifest = _load_manifest(topic_root_path)
    if manifest:
        invariants = manifest.get("invariants", [])
        if invariants:  # Only require invariant checks when invariants are declared
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

    # AI Physicist L2 Lookup (was dead code — now wired in v1.0):
    # Check that reviews reference L2 knowledge relevant to the claims
    l2_warnings = []
    for cand_path in submitted:
        slug = cand_path.stem
        review_path = review_dir / f"{slug}.md"
        if review_path.exists():
            rf, rb = parse_md(review_path)
            try:
                lookup = _check_physicist_l2_lookup(review_path, parse_md, topic_root_path)
            except Exception:
                lookup = True, ""
            if not lookup[0]:
                l2_warnings.append(f"{slug}: {lookup[1]}")

    # AI Physicist Check: every review must contain a correspondence/limit check
    # with at least one concrete physical limit named
    for cand_path in submitted:
        slug = cand_path.stem
        review_path = review_dir / f"{slug}.md"
        if review_path.exists():
            _, rev_body = parse_md(review_path)
            correspondence_issues = _check_physicist_correspondence(rev_body, lane)
            if correspondence_issues:
                return StageSnapshot(
                    stage="L4", posture="verify", lane=lane,
                    gate_status="blocked_missing_field",
                    required_artifact_path=str(review_path),
                    missing_requirements=[
                        f"L4 review for {slug}: {issue}" for issue in correspondence_issues
                    ],
                    next_allowed_transition="L3",
                    skill="skill-validate",
                )
            anomaly_issues = _check_physicist_anomalies(rev_body)
            if anomaly_issues:
                return StageSnapshot(
                    stage="L4", posture="verify", lane=lane,
                    gate_status="blocked_missing_field",
                    required_artifact_path=str(review_path),
                    missing_requirements=[
                        f"L4 review for {slug}: {issue}" for issue in anomaly_issues
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
