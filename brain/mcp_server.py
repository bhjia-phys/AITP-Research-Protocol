"""AITP Brain MCP Server v2 — Minimal skill-driven research protocol.

Provides ~12 tools for the agent to read/write topic state.
All storage is Markdown with YAML frontmatter. No JSON, no JSONL.

Dependencies: fastmcp, pyyaml
Install: pip install fastmcp pyyaml
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

# Ensure the parent directory is on sys.path so `brain` is importable
# regardless of cwd when launched as an MCP stdio server.
_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from fastmcp import FastMCP

from brain.state_model import (
    topic_root as resolve_topic_root,
    topics_dir,
    validate_topic_slug,
    evaluate_l0_stage,
    evaluate_l1_stage,
    evaluate_l3_stage,
    _get_l3_config,
    L0_ARTIFACT_TEMPLATES,
    L1_ARTIFACT_TEMPLATES,
    L3_ARTIFACT_TEMPLATES,
    L3_ACTIVE_ARTIFACT_NAMES,
    L3_SKILL_MAP,
    L3_SUBPLANES,
    L3_ALLOWED_TRANSITIONS,
    L4_OUTCOMES,
    PHYSICS_CHECK_FIELDS,
    STUDY_L3_SUBPLANES,
    STUDY_L3_ARTIFACT_TEMPLATES,
    STUDY_L3_ACTIVE_ARTIFACT_NAMES,
    STUDY_L3_SKILL_MAP,
    STUDY_L3_ALLOWED_TRANSITIONS,
    STUDY_CANDIDATE_TYPES,
    L2_NODE_TYPES,
    L2_EDGE_TYPES,
    L2_TOWER_TEMPLATE,
    TRUST_EVOLUTION,
    semantic_score,
    normalize_latex,
    tokenize_for_search,
)

mcp = FastMCP("aitp-brain")


class _GateResult(dict):
    """Dict subclass that stringifies to its 'message' value.

    Backwards-compatible: ``assertIn("foo", result)`` checks the message,
    while ``result["popup_gate"]`` returns the popup dict.
    """

    def __str__(self) -> str:
        return str(self.get("message", ""))

    def __contains__(self, item) -> bool:
        if isinstance(item, str):
            if super().__contains__(item):
                return True
            return item in str(self)
        return super().__contains__(item)

    def lower(self) -> str:
        return str(self).lower()


# ---------------------------------------------------------------------------
# Helpers — Markdown + YAML frontmatter I/O
# ---------------------------------------------------------------------------

_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)

_AGENT_BEHAVIOR_REMINDER = (
    "Python is storage+search only. You are the physicist. "
    "Assess your own work before advancing — the skill file asks Socratic questions, "
    "not compliance checklists. Evidence before claims. "
    "Derivations before conclusions. Limits before generalizations. "
    "Check compute_target before ANY code, SymPy, Lean, or numerical work "
    "— route heavy computation to the declared target (local/fisher/lean-remote)."
)


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _topic_root(topics_root: str, topic_slug: str) -> Path:
    return resolve_topic_root(topics_root, topic_slug)


def _parse_md(path: Path) -> tuple[dict[str, Any], str]:
    if not path.exists():
        return {}, ""
    text = path.read_text(encoding="utf-8")
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    import yaml
    fm = yaml.safe_load(m.group(1)) or {}
    return fm, m.group(2)


def _atomic_write_text(path: Path, text: str) -> None:
    """Write text to file atomically via temp-file-and-replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _render_md(fm: dict[str, Any], body: str) -> str:
    import yaml
    frontmatter = yaml.dump(fm, default_flow_style=False, allow_unicode=True).strip()
    return f"---\n{frontmatter}\n---\n{body}\n"


def _write_md(path: Path, fm: dict[str, Any], body: str) -> None:
    _atomic_write_text(path, _render_md(fm, body))


def _append_section(path: Path, section: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if existing and not existing.endswith("\n"):
        existing += "\n"
    _atomic_write_text(path, existing + section + "\n")


def _slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-") or "untitled"


# ---------------------------------------------------------------------------
# Skill injection logic
# ---------------------------------------------------------------------------

_SKILL_MAP = {
    "new": "skill-explore",
    "sources_registered": "skill-intake",
    "intake_done": "skill-derive",
    "candidate_ready": "skill-validate",
    "validated": "skill-promote",
    "promoted": "skill-write",
}

_VALID_STATUSES = set(_SKILL_MAP.keys()) | {"complete", "blocked"}


def _infer_status(fm: dict[str, Any], topic_root: Path) -> str:
    explicit = str(fm.get("status") or "").strip()
    if explicit and explicit in _VALID_STATUSES:
        return explicit
    src_dir = topic_root / "L0" / "sources"
    intake_dir = topic_root / "L1" / "intake"
    cand_dir = topic_root / "L3" / "candidates"
    if src_dir.is_dir() and list(src_dir.glob("*.md")):
        if intake_dir.is_dir() and list(intake_dir.glob("*.md")):
            if cand_dir.is_dir() and list(cand_dir.glob("*.md")):
                return "candidate_ready"
            return "intake_done"
        return "sources_registered"
    return "new"


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def aitp_list_topics(topics_root: str) -> list[dict[str, Any]]:
    """List all topics under topics_root with their stage, title, and question.

    Use this BEFORE aitp_get_status when you need to discover which topic
    matches the user's research request.
    """
    root = Path(topics_root)
    if not root.is_dir():
        return []
    results = []
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        state_file = d / "state.md"
        if not state_file.exists():
            continue
        fm, body = _parse_md(state_file)
        results.append({
            "topic_slug": d.name,
            "title": fm.get("title", d.name),
            "stage": fm.get("stage", "unknown"),
            "lane": fm.get("lane", ""),
            "question": fm.get("question", ""),
        })
    return results


@mcp.tool()
def aitp_health_check(topics_root: str) -> dict[str, Any]:
    """Return aggregated health status of ALL topics.

    Returns counts by stage, gate status, lane, and per-topic details
    including blocked reasons, candidate counts, source counts, and
    last-updated timestamps. Use as a single dashboard call before
    diving into individual topics.
    """
    root = topics_dir(topics_root)
    if not root.is_dir():
        return {"error": f"Topics directory not found: {root}", "topics": [], "summary": {}}

    topics_list: list[dict[str, Any]] = []
    summary: dict[str, Any] = {
        "total_topics": 0,
        "by_stage": {},
        "by_gate_status": {},
        "by_lane": {},
        "blocked_count": 0,
        "ready_count": 0,
        "total_candidates": 0,
        "total_sources": 0,
    }

    for topic_dir in sorted(root.iterdir()):
        if not topic_dir.is_dir():
            continue
        state_path = topic_dir / "state.md"
        if not state_path.exists():
            continue
        slug = topic_dir.name

        fm, _ = _parse_md(state_path)
        stage = str(fm.get("stage", "L0")).strip() or "L0"
        lane = str(fm.get("lane", "unspecified")).strip() or "unspecified"

        # Live gate evaluation: gate_status from state.md may be stale
        try:
            if stage == "L3":
                snap = evaluate_l3_stage(_parse_md, topic_dir, lane=lane)
            elif stage == "L0":
                snap = evaluate_l0_stage(_parse_md, topic_dir, lane=lane)
            else:
                snap = evaluate_l1_stage(_parse_md, topic_dir, lane=lane)
            gate = snap.gate_status
            posture = snap.posture
            l3_subplane = snap.l3_subplane or ""
            l3_mode = snap.l3_mode or ""
            missing = snap.missing_requirements
        except Exception as exc:
            gate = "error"
            posture = "unknown"
            l3_subplane = ""
            l3_mode = ""
            missing = [f"evaluation error: {exc}"]

        # Source and candidate counts
        src_dir = topic_dir / "L0" / "sources"
        src_count = len(list(src_dir.glob("*.md"))) if src_dir.is_dir() else 0
        cand_dir = topic_dir / "L3" / "candidates"
        cand_count = len(list(cand_dir.glob("*.md"))) if cand_dir.is_dir() else 0

        entry = {
            "topic_slug": slug,
            "title": fm.get("title", slug),
            "stage": stage,
            "posture": posture,
            "lane": lane,
            "gate_status": gate,
            "l3_subplane": l3_subplane,
            "l3_mode": l3_mode,
            "missing_requirements": missing,
            "sources_count": src_count,
            "candidates_count": cand_count,
            "last_updated": str(fm.get("updated_at", "")),
        }
        topics_list.append(entry)

        # Aggregate
        summary["total_topics"] += 1
        summary["by_stage"][stage] = summary["by_stage"].get(stage, 0) + 1
        summary["by_gate_status"][gate] = summary["by_gate_status"].get(gate, 0) + 1
        summary["by_lane"][lane] = summary["by_lane"].get(lane, 0) + 1
        summary["total_sources"] += src_count
        summary["total_candidates"] += cand_count
        if gate.startswith("blocked"):
            summary["blocked_count"] += 1
        elif gate == "ready":
            summary["ready_count"] += 1

    return {
        "summary": summary,
        "topics": topics_list,
        "topics_root": str(root),
        "checked_at": _now(),
    }


@mcp.tool()
def aitp_get_status(topics_root: str, topic_slug: str) -> dict[str, Any]:
    """Read topic state and return current status, stage, posture, and gate."""
    root = _topic_root(topics_root, topic_slug)
    fm, body = _parse_md(root / "state.md")
    status = _infer_status(fm, root)
    snapshot = evaluate_l1_stage(_parse_md, root, lane=fm.get("lane", "unspecified"))
    src_dir = root / "L0" / "sources"
    cand_dir = root / "L3" / "candidates"
    global_l2 = _global_l2_path(topics_root)
    return {
        "topic_slug": topic_slug,
        "status": status,
        "stage": fm.get("stage", snapshot.stage),
        "posture": fm.get("posture", snapshot.posture),
        "lane": fm.get("lane", snapshot.lane),
        "compute_target": str(fm.get("compute", "local")),
        "gate_status": snapshot.gate_status,
        "mode": fm.get("mode", "explore"),
        "layer": fm.get("layer", "L1"),
        "l3_mode": fm.get("l3_mode", "research"),
        "title": fm.get("title", topic_slug),
        "required_artifact_path": snapshot.required_artifact_path,
        "missing_requirements": snapshot.missing_requirements,
        "sources_count": len(list(src_dir.glob("*.md"))) if src_dir.is_dir() else 0,
        "candidates_count": len(list(cand_dir.glob("*.md"))) if cand_dir.is_dir() else 0,
        "l2_count": len(list(global_l2.glob("*.md"))) if global_l2.is_dir() else 0,
        "updated_at": fm.get("updated_at", ""),
    }


@mcp.tool()
def aitp_update_status(
    topics_root: str,
    topic_slug: str,
    status: str | None = None,
    mode: str | None = None,
    layer: str | None = None,
) -> str:
    """Update topic state.md frontmatter fields."""
    root = _topic_root(topics_root, topic_slug)
    state_path = root / "state.md"
    fm, body = _parse_md(state_path)
    if status:
        fm["status"] = status
    if mode:
        fm["mode"] = mode
    if layer:
        fm["layer"] = layer
    fm["updated_at"] = _now()
    _write_md(state_path, fm, body)
    return f"Updated {topic_slug}: status={fm.get('status')}, mode={fm.get('mode')}, layer={fm.get('layer')}"


@mcp.tool()
def aitp_bootstrap_topic(
    topics_root: str,
    topic_slug: str,
    title: str,
    question: str,
    lane: str = "unspecified",
    mode: str = "explore",
) -> str:
    """Create a new topic directory structure with state.md and L0/L1 scaffolds."""
    safe_slug = validate_topic_slug(topic_slug)
    base = topics_dir(topics_root)
    root = base / safe_slug
    if root.exists():
        return f"Topic {safe_slug} already exists."
    root.mkdir(parents=True)
    for sub in [
        "L0/sources", "L1/intake", "L3/candidates",
        "L4/reviews", "L4/scripts", "L4/outputs", "L4/outputs/figures",
        "L5_writing/figures", "L5_writing/tables", "runtime",
    ]:
        (root / sub).mkdir(parents=True)
    # Write L0 artifact scaffolds
    for rel_name, (artifact_fm, artifact_body) in L0_ARTIFACT_TEMPLATES.items():
        _write_md(root / "L0" / rel_name, artifact_fm, artifact_body)
    # Write L1 artifact scaffolds
    for rel_name, (artifact_fm, artifact_body) in L1_ARTIFACT_TEMPLATES.items():
        _write_md(root / "L1" / rel_name, artifact_fm, artifact_body)
    # Runtime surfaces: topic index and log
    _write_md(root / "runtime" / "index.md", {
        "topic_slug": safe_slug, "kind": "topic_index", "created_at": _now(),
    }, (
        f"# Topic Index: {title}\n\n"
        "## Source Discovery\n- L0/sources/\n- L0/source_registry.md\n\n"
        "## Source Basis\n- L1/source_basis.md\n\n"
        "## Research Notebook\n- L3/ subplane active artifacts\n\n"
        "## Validation\n- L4/reviews/\n\n"
        "## Reusable Results\n- global L2/ (cross-topic)\n\n"
        "## Writing\n- L3/tex/flow_notebook.tex\n- L5_writing/\n"
    ))
    _write_md(root / "runtime" / "log.md", {
        "topic_slug": safe_slug, "kind": "topic_log", "created_at": _now(),
    }, f"# Topic Log: {title}\n\n## Events\n\n- {_now()} topic bootstrapped\n")
    _write_md(root / "runtime" / "sessions.md", {
        "kind": "session_log", "topic_slug": safe_slug, "created_at": _now(),
    }, f"# Session Log: {title}\n\n## Sessions\n")
    # Global L2 surfaces
    global_l2 = base.parent / "L2" if base.name == "topics" else Path(topics_root).parent / "L2"
    global_l2.mkdir(parents=True, exist_ok=True)
    if not (global_l2 / "index.md").exists():
        _write_md(global_l2 / "index.md", {
            "kind": "global_l2_index", "created_at": _now(),
        }, (
            "# Global L2 Index\n\n"
            "## Family\n\n## Regime\n\n"
            "## Warning And Negative Results\n\n## Cross-Topic Bridges\n"
        ))
    if not (global_l2 / "log.md").exists():
        _write_md(global_l2 / "log.md", {
            "kind": "global_l2_log", "created_at": _now(),
        }, "# Global L2 Log\n\n## Events\n")
    fm = {
        "topic_slug": safe_slug,
        "title": title,
        "status": "new",
        "mode": mode,
        "layer": "L0",
        "stage": "L0",
        "posture": "discover",
        "lane": lane,
        "compute": "local",
        "gate_status": "blocked_missing_field",
        "created_at": _now(),
        "updated_at": _now(),
        "sources_count": 0,
        "candidates_count": 0,
        "l4_cycle_count": 0,
        "research_loop_active": False,
        "research_loop_max_cycles": 0,
        "l3_mode": "research",
    }
    body = f"# {title}\n\n## Research Question\n{question}\n"
    _write_md(root / "state.md", fm, body)
    return f"Bootstrapped topic {safe_slug} at {root}"


@mcp.tool()
def aitp_register_source(
    topics_root: str,
    topic_slug: str,
    source_id: str,
    source_type: str = "paper",
    title: str = "",
    arxiv_id: str = "",
    fidelity: str = "arxiv_preprint",
    notes: str = "",
) -> str:
    """Register a source in L0. Creates a Markdown file with frontmatter."""
    root = _topic_root(topics_root, topic_slug)
    slug = _slugify(source_id)
    path = root / "L0" / "sources" / f"{slug}.md"
    if path.exists():
        return f"Source {slug} already registered."
    fm = {
        "source_id": slug,
        "type": source_type,
        "title": title or source_id,
        "arxiv_id": arxiv_id,
        "fidelity": fidelity,
        "registered": _now(),
    }
    body = f"# {title or source_id}\n\n{notes}\n" if notes else f"# {title or source_id}\n"
    _write_md(path, fm, body)
    # Update sources_count in state.md
    state_path = root / "state.md"
    sfm, sbody = _parse_md(state_path)
    sfm["sources_count"] = int(sfm.get("sources_count", 0)) + 1
    sfm["updated_at"] = _now()
    _write_md(state_path, sfm, sbody)
    return f"Registered source {slug}"


@mcp.tool()
def aitp_list_sources(topics_root: str, topic_slug: str) -> list[dict[str, Any]]:
    """List all registered sources for a topic."""
    root = _topic_root(topics_root, topic_slug)
    src_dir = root / "L0" / "sources"
    if not src_dir.is_dir():
        return []
    results = []
    for path in sorted(src_dir.glob("*.md")):
        fm, _ = _parse_md(path)
        results.append({"source_id": fm.get("source_id", path.stem), "title": fm.get("title", ""), "type": fm.get("type", ""), "arxiv_id": fm.get("arxiv_id", "")})
    return results


@mcp.tool()
def aitp_submit_candidate(
    topics_root: str,
    topic_slug: str,
    candidate_id: str,
    title: str,
    claim: str,
    evidence: str = "",
    assumptions: str = "",
    validation_criteria: str = "",
    depends_on: list[str] | None = None,
    candidate_type: str = "research_claim",
    regime_of_validity: str = "",
) -> dict[str, Any]:
    """Submit a candidate finding. Creates L3/candidates/<id>.md. Returns popup gate for confirmation.

    depends_on: list of candidate_ids that this candidate builds upon.
    candidate_type: type of candidate — research modes produce research_claim (default),
        study modes produce atomic_concept, derivation_chain, correspondence_link,
        regime_boundary, or open_question.
    regime_of_validity: physical regime where this candidate applies (required for study candidates).
    """
    root = _topic_root(topics_root, topic_slug)
    slug = _slugify(candidate_id)
    path = root / "L3" / "candidates" / f"{slug}.md"

    # Determine l3_mode from state
    state_fm, _ = _parse_md(root / "state.md")
    l3_mode = state_fm.get("l3_mode", "research")
    if candidate_type == "research_claim" and l3_mode == "study":
        candidate_type = "atomic_concept"

    fm = {
        "candidate_id": slug,
        "title": title,
        "claim": claim,
        "status": "submitted",
        "mode": "candidate",
        "candidate_type": candidate_type,
        "l3_mode": l3_mode,
        "depends_on": depends_on or [],
        "created_at": _now(),
        "updated_at": _now(),
    }
    if regime_of_validity:
        fm["regime_of_validity"] = regime_of_validity
    body = (
        f"# {title}\n\n"
        f"## Claim\n{claim}\n\n"
        f"## Evidence\n{evidence}\n\n"
        f"## Assumptions\n{assumptions}\n\n"
        f"## Validation Criteria\n{validation_criteria}\n"
    )
    _write_md(path, fm, body)
    return _GateResult({
        "message": f"Submitted candidate {slug}",
        "popup_gate": {
            "question": f"Submit candidate '{title}' ({slug}) for validation?",
            "header": "Submit",
            "options": [
                {"label": "Submit", "description": "Proceed with submission and move to L4 validation."},
                {"label": "Revise", "description": "Go back and refine the candidate before submitting."},
            ],
        },
    })


# ---------------------------------------------------------------------------
# Promotion gate lifecycle
# ---------------------------------------------------------------------------

_PROMOTION_TRANSITIONS = {
    "submitted": "pending_validation",
    "pending_validation": "validated",
    "validated": "pending_approval",
    "pending_approval": "approved_for_promotion",
    "approved_for_promotion": "promoted",
}


@mcp.tool()
def aitp_request_promotion(
    topics_root: str,
    topic_slug: str,
    candidate_id: str,
) -> dict[str, Any]:
    """Move a validated candidate to pending_approval for human review. Returns popup gate.

    Requires candidate status='validated' (i.e., L4 review with outcome='pass' has been submitted).
    Also verifies that an L4 pass review exists for this candidate.
    """
    root = _topic_root(topics_root, topic_slug)
    slug = _slugify(candidate_id)
    cand_path = root / "L3" / "candidates" / f"{slug}.md"
    if not cand_path.exists():
        return _GateResult({"message": f"Candidate {slug} not found."})
    fm, body = _parse_md(cand_path)
    current = fm.get("status", "")
    if current != "validated":
        return _GateResult({"message": f"Candidate {slug} status is '{current}', not 'validated'. Cannot request promotion."})

    # Verify L4 pass review exists
    review_path = root / "L4" / "reviews" / f"{slug}.md"
    if not review_path.exists():
        return _GateResult({
            "message": f"No L4 review found for {slug}. Submit aitp_submit_l4_review with outcome='pass' first.",
        })
    rev_fm, _ = _parse_md(review_path)
    if rev_fm.get("outcome") != "pass":
        return _GateResult({
            "message": f"L4 review for {slug} has outcome='{rev_fm.get('outcome')}', not 'pass'. Cannot promote.",
        })
    fm["status"] = "pending_approval"
    fm["promotion_requested_at"] = _now()
    _write_md(cand_path, fm, body)
    cand_title = fm.get("title", slug)
    return _GateResult({
        "message": f"Candidate {slug} moved to pending_approval. Awaiting human decision.",
        "popup_gate": {
            "question": f"Request promotion of '{cand_title}' ({slug}) to global knowledge base?",
            "header": "Promote",
            "options": [
                {"label": "Approve promotion", "description": "Promote this candidate to the global L2 knowledge base."},
                {"label": "Reject", "description": "Send back for further work. Provide a reason."},
            ],
        },
    })


@mcp.tool()
def aitp_resolve_promotion_gate(
    topics_root: str,
    topic_slug: str,
    candidate_id: str,
    decision: str,
    reason: str = "",
) -> str:
    """Resolve a pending_approval candidate: approve or reject."""
    root = _topic_root(topics_root, topic_slug)
    slug = _slugify(candidate_id)
    cand_path = root / "L3" / "candidates" / f"{slug}.md"
    if not cand_path.exists():
        return f"Candidate {slug} not found."
    fm, body = _parse_md(cand_path)
    if fm.get("status") != "pending_approval":
        return f"Candidate {slug} is not pending_approval (status: {fm.get('status')})."
    if decision == "approve":
        fm["status"] = "approved_for_promotion"
        fm["approved_at"] = _now()
        fm["approval_reason"] = reason
    elif decision == "reject":
        fm["status"] = "rejected_from_promotion"
        fm["rejection_reason"] = reason
        fm["rejected_at"] = _now()
    else:
        return f"Unknown decision '{decision}'. Use 'approve' or 'reject'."
    _write_md(cand_path, fm, body)

    if decision == "reject":
        _append_to_topic_log(root, f"promotion rejected for {slug}: {reason}")
        return (
            f"Candidate {slug} promotion rejected. "
            f"The agent should call aitp_retreat_to_l3 to return to L3/analysis "
            f"and address the rejection reason before re-submitting."
        )
    return f"Candidate {slug} resolved: {decision}."


@mcp.tool()
def aitp_promote_candidate(
    topics_root: str,
    topic_slug: str,
    candidate_id: str,
    comment: str = "",
    trust_basis: str = "validated",
    trust_scope: str = "bounded_reusable",
) -> str:
    """Promote an approved candidate to global L2 with conflict/version handling."""
    root = _topic_root(topics_root, topic_slug)
    slug = _slugify(candidate_id)
    cand_path = root / "L3" / "candidates" / f"{slug}.md"
    if not cand_path.exists():
        return f"Candidate {slug} not found."
    fm, body = _parse_md(cand_path)
    if fm.get("status") != "approved_for_promotion":
        return _GateResult({
            "message": (
                f"Candidate {slug} is not approved_for_promotion (status: {fm.get('status')}). "
                f"Use aitp_request_promotion then aitp_resolve_promotion_gate(approve) first."
            ),
        })

    global_l2 = _global_l2_path(topics_root)
    global_l2.mkdir(parents=True, exist_ok=True)
    l2_path = global_l2 / f"{slug}.md"

    new_claim = str(fm.get("claim", "")).strip()

    if l2_path.exists():
        existing_fm, _ = _parse_md(l2_path)
        existing_claim = str(existing_fm.get("claim", "")).strip()
        if existing_claim and existing_claim != new_claim and new_claim:
            # Conflict: different claims for same unit
            conflict_path = global_l2 / "conflicts" / f"{slug}.md"
            conflict_path.parent.mkdir(parents=True, exist_ok=True)
            _write_md(conflict_path, {
                "kind": "conflict", "candidate_id": slug,
                "existing_claim": existing_claim, "new_claim": new_claim,
                "detected_at": _now(),
            }, f"# Conflict: {slug}\n\nExisting: {existing_claim}\n\nNew: {new_claim}\n")
            return f"Conflict detected for {slug}. Written to L2/conflicts/. Resolve before promoting."

        # Same or compatible claim: version bump
        existing_version = int(existing_fm.get("version", 1))
        fm["version"] = existing_version + 1
        fm["previous_version_promoted_at"] = existing_fm.get("promoted_at", "")

    fm["status"] = "promoted"
    fm["promoted_at"] = _now()
    fm["promotion_comment"] = comment
    fm["trust_basis"] = trust_basis
    fm["trust_scope"] = trust_scope
    if fm.get("candidate_type"):
        fm["candidate_type"] = fm.get("candidate_type", "research_claim")
    if fm.get("regime_of_validity"):
        fm["regime_of_validity"] = fm.get("regime_of_validity", "")
    if "version" not in fm:
        fm["version"] = 1

    _write_md(cand_path, fm, body)
    _write_md(l2_path, fm, body)

    # Also create a graph node if the candidate has a type and regime
    cand_type = fm.get("candidate_type", "research_claim")
    regime = fm.get("regime_of_validity", "")

    # Map study candidate types to L2 node types
    _STUDY_TO_L2_NODE_TYPE = {
        "atomic_concept": "concept",
        "derivation_chain": "derivation_chain",
        "correspondence_link": "regime_boundary",
        "regime_boundary": "regime_boundary",
        "open_question": "open_question",
    }
    mapped_type = _STUDY_TO_L2_NODE_TYPE.get(cand_type, cand_type)
    if cand_type != "research_claim" and mapped_type in L2_NODE_TYPES:
        try:
            _ensure_l2_graph_dirs(topics_root)
            global_l2 = _global_l2_path(topics_root)
            node_path = global_l2 / "graph" / "nodes" / f"{slug}.md"
            node_fm = {
                "node_id": slug,
                "type": mapped_type,
                "title": fm.get("title", slug),
                "regime_of_validity": regime,
                "trust_basis": trust_basis,
                "trust_scope": trust_scope,
                "version": 1,
                "source_candidate": slug,
                "source_topic": topic_slug,
                "mathematical_expression": "",
                "created_at": _now(),
                "updated_at": _now(),
            }
            node_body = (
                f"# {fm.get('title', slug)}\n\n"
                f"## Physical Meaning\n{fm.get('claim', '')}\n\n"
                f"## Mathematical Expression\n\n"
                f"## Regime and Limits\n{regime}\n\n"
                f"## Open Questions\n"
            )
            _write_md(node_path, node_fm, node_body)
        except Exception:
            pass  # Non-fatal: graph node creation is best-effort

    _append_to_topic_log(root, f"promoted {slug} to global L2 (v{fm['version']})")
    return f"Promoted {slug} to global L2 (v{fm['version']})."


@mcp.tool()
def aitp_list_candidates(topics_root: str, topic_slug: str) -> list[dict[str, Any]]:
    """List all candidates for a topic."""
    root = _topic_root(topics_root, topic_slug)
    cand_dir = root / "L3" / "candidates"
    if not cand_dir.is_dir():
        return []
    results = []
    for path in sorted(cand_dir.glob("*.md")):
        fm, _ = _parse_md(path)
        results.append({"candidate_id": fm.get("candidate_id", path.stem), "title": fm.get("title", ""), "status": fm.get("status", "")})
    return results


@mcp.tool()
def aitp_get_execution_brief(topics_root: str, topic_slug: str) -> dict[str, Any]:
    """Return a stage/posture execution brief with gate status and missing requirements."""
    root = _topic_root(topics_root, topic_slug)
    fm, _ = _parse_md(root / "state.md")
    stage = str(fm.get("stage", "L0"))

    if stage == "L3":
        snapshot = evaluate_l3_stage(_parse_md, root, lane=fm.get("lane", "unspecified"))
        return {
            "topic_slug": topic_slug,
            "stage": snapshot.stage,
            "posture": snapshot.posture,
            "lane": snapshot.lane,
            "compute_target": str(fm.get("compute", "local")),
            "gate_status": snapshot.gate_status,
            "required_artifact_path": snapshot.required_artifact_path,
            "missing_requirements": snapshot.missing_requirements,
            "next_allowed_transition": snapshot.next_allowed_transition,
            "skill": snapshot.skill,
            "l3_subplane": snapshot.l3_subplane,
            "l3_mode": snapshot.l3_mode,
            "immediate_allowed_work": (
                [f"edit {snapshot.required_artifact_path}"]
                if snapshot.required_artifact_path
                else [f"advance from {snapshot.l3_subplane}"]
            ),
            "immediate_blocked_work": ["L4 validation", "L2 promotion"],
            "_agent_behavior_reminder": _AGENT_BEHAVIOR_REMINDER,
        }

    if stage == "L0":
        snapshot = evaluate_l0_stage(_parse_md, root, lane=fm.get("lane", "unspecified"))
        return {
            "topic_slug": topic_slug,
            "stage": snapshot.stage,
            "posture": snapshot.posture,
            "lane": snapshot.lane,
            "compute_target": str(fm.get("compute", "local")),
            "gate_status": snapshot.gate_status,
            "required_artifact_path": snapshot.required_artifact_path,
            "missing_requirements": snapshot.missing_requirements,
            "next_allowed_transition": snapshot.next_allowed_transition,
            "skill": snapshot.skill,
            "l3_subplane": snapshot.l3_subplane,
            "immediate_allowed_work": (
                [f"edit {snapshot.required_artifact_path}"]
                if snapshot.required_artifact_path
                else ["advance to L1 (reading and framing)"]
            ),
            "immediate_blocked_work": ["L1 framing", "L3 derivation", "L4 validation", "L2 promotion"],
            "_agent_behavior_reminder": _AGENT_BEHAVIOR_REMINDER,
        }

    snapshot = evaluate_l1_stage(_parse_md, root, lane=fm.get("lane", "unspecified"))
    return {
        "topic_slug": topic_slug,
        "stage": snapshot.stage,
        "posture": snapshot.posture,
        "lane": snapshot.lane,
        "compute_target": str(fm.get("compute", "local")),
        "gate_status": snapshot.gate_status,
        "required_artifact_path": snapshot.required_artifact_path,
        "missing_requirements": snapshot.missing_requirements,
        "next_allowed_transition": snapshot.next_allowed_transition,
        "skill": snapshot.skill,
        "l3_subplane": snapshot.l3_subplane,
        "immediate_allowed_work": (
            [f"edit {snapshot.required_artifact_path}"]
            if snapshot.required_artifact_path
            else ["prepare transition to L3"]
        ),
        "immediate_blocked_work": ["L3 derivation", "L4 validation", "L2 promotion"],
        "_agent_behavior_reminder": _AGENT_BEHAVIOR_REMINDER,
    }


@mcp.tool()
def aitp_session_resume(
    topics_root: str,
    topic_slug: str,
) -> dict[str, Any]:
    """Get a resumption context for a topic after a session break.

    Returns current state, recent log entries (last 10 events), and the
    execution brief so the agent can pick up where it left off without
    re-reading every artifact.
    """
    root = _topic_root(topics_root, topic_slug)
    fm, body = _parse_md(root / "state.md")

    # Read last N log entries
    log_path = root / "runtime" / "log.md"
    recent_events: list[str] = []
    if log_path.exists():
        log_text = log_path.read_text(encoding="utf-8")
        lines = [l.strip() for l in log_text.splitlines() if l.strip().startswith("- ")]
        recent_events = lines[-10:]

    # Get execution brief inline
    stage = str(fm.get("stage", "L0"))
    if stage == "L3":
        snapshot = evaluate_l3_stage(_parse_md, root, lane=fm.get("lane", "unspecified"))
    elif stage == "L0":
        snapshot = evaluate_l0_stage(_parse_md, root, lane=fm.get("lane", "unspecified"))
    else:
        snapshot = evaluate_l1_stage(_parse_md, root, lane=fm.get("lane", "unspecified"))

    # Summarize what was last worked on
    last_subplane = fm.get("l3_subplane", "")
    l3_mode = fm.get("l3_mode", "research")
    summary_parts = [
        f"Topic '{fm.get('title', topic_slug)}' is at stage={stage}",
    ]
    if last_subplane:
        summary_parts.append(f"L3 subplane={last_subplane} (mode={l3_mode})")
        summary_parts.append(f"L3 subplane={last_subplane}")
    if snapshot.gate_status != "ready":
        summary_parts.append(f"gated by: {snapshot.missing_requirements}")
    if recent_events:
        summary_parts.append(f"last activity: {recent_events[-1]}")

    return {
        "topic_slug": topic_slug,
        "stage": stage,
        "posture": fm.get("posture", snapshot.posture),
        "lane": fm.get("lane", ""),
        "l3_mode": l3_mode,
        "l3_subplane": last_subplane,
        "gate_status": snapshot.gate_status,
        "skill": snapshot.skill,
        "required_artifact_path": snapshot.required_artifact_path,
        "missing_requirements": snapshot.missing_requirements,
        "recent_events": recent_events,
        "resume_summary": ". ".join(summary_parts) + ".",
        "instruction": (
            f"Resume by reading skill '{snapshot.skill}' and continuing "
            f"from where the last session left off."
        ),
    }


# ---------------------------------------------------------------------------
# L0 <-> L1 transition tools
# ---------------------------------------------------------------------------


@mcp.tool()
def aitp_advance_to_l1(topics_root: str, topic_slug: str) -> dict[str, Any]:
    """Transition a topic from L0 (discover, ready) to L1 (read). Returns popup gate."""
    root = _topic_root(topics_root, topic_slug)
    l0_snapshot = evaluate_l0_stage(_parse_md, root)
    if l0_snapshot.gate_status != "ready":
        return _GateResult({"message": f"L0 gate is not ready (status: {l0_snapshot.gate_status}). Register sources and fill source_registry.md first."})

    state_path = root / "state.md"
    fm, body = _parse_md(state_path)
    fm["stage"] = "L1"
    fm["posture"] = "read"
    fm["layer"] = "L1"
    fm["updated_at"] = _now()
    _write_md(state_path, fm, body)
    _append_to_topic_log(root, "advanced from L0 to L1")
    return _GateResult({
        "message": "Advanced to L1 (reading and framing). Begin reading registered sources and filling L1 artifacts.",
        "popup_gate": {
            "question": "Source discovery complete. Begin reading and framing?",
            "header": "L0->L1",
            "options": [
                {"label": "Start reading", "description": "Proceed to L1. Read registered sources and fill source_basis.md."},
                {"label": "Register more sources", "description": "Go back and add more sources to L0 before reading."},
            ],
        },
    })


@mcp.tool()
def aitp_retreat_to_l0(topics_root: str, topic_slug: str, reason: str = "") -> _GateResult:
    """Retreat from L1 back to L0 for more source discovery. L1 work is preserved.

    Use when reading reveals missing sources, wrong coverage, or need for additional materials.
    """
    root = _topic_root(topics_root, topic_slug)
    state_path = root / "state.md"
    fm, body = _parse_md(state_path)
    current_stage = fm.get("stage", "L0")
    if current_stage not in ("L1", "L3"):
        return _GateResult({"message": f"Cannot retreat to L0: topic is at {current_stage}."})

    fm["stage"] = "L0"
    fm["posture"] = "discover"
    fm["layer"] = "L0"
    fm["retreated_from"] = current_stage
    fm["retreat_reason"] = reason
    fm["updated_at"] = _now()
    _write_md(state_path, fm, body)
    _append_to_topic_log(root, f"retreated from {current_stage} to L0: {reason}")
    return _GateResult({
        "message": f"Retreated to L0 from {current_stage}. All artifacts preserved. Register more sources or update the registry.",
        "popup_gate": {
            "question": "Retreated to L0 for more source discovery. What do you need to do?",
            "header": f"{current_stage}→L0",
            "options": [
                {"label": "Register sources", "description": "Add new sources (papers, datasets, code, etc.) to L0/sources/."},
                {"label": "Update registry", "description": "Edit L0/source_registry.md with new search methodology or coverage assessment."},
                {"label": "Go back", "description": f"Return to {current_stage} without changes (used register_source separately)."},
            ],
        },
    })


# ---------------------------------------------------------------------------
# L3 subplane tools
# ---------------------------------------------------------------------------


@mcp.tool()
def aitp_advance_to_l3(
    topics_root: str,
    topic_slug: str,
    l3_mode: str = "research",
) -> dict[str, Any]:
    """Transition a topic from L1 (ready) to L3. Returns popup gate.

    l3_mode: research | study
    - research (default): start at ideation subplane for original derivation
    - study: start at source_decompose for literature understanding
    """
    root = _topic_root(topics_root, topic_slug)
    l1_snapshot = evaluate_l1_stage(_parse_md, root)
    if l1_snapshot.gate_status != "ready":
        return _GateResult({"message": f"L1 gate is not ready (status: {l1_snapshot.gate_status}). Fill missing artifacts first."})

    if l3_mode not in ("research", "study"):
        return _GateResult({"message": f"Invalid l3_mode '{l3_mode}'. Use 'research' or 'study'."})

    (
        subplanes,
        _,
        templates,
        artifact_names,
        _,
        _,
        entry_subplane,
    ) = _get_l3_config(l3_mode)

    state_path = root / "state.md"
    fm, body = _parse_md(state_path)
    fm["stage"] = "L3"
    fm["posture"] = "derive"
    fm["l3_mode"] = l3_mode
    fm["l3_subplane"] = entry_subplane
    fm["updated_at"] = _now()
    _write_md(state_path, fm, body)

    # Create L3 subplane directories and scaffolds
    for subplane in subplanes:
        (root / "L3" / subplane).mkdir(parents=True, exist_ok=True)
        _, template_fm, template_body = templates[subplane]
        artifact_path = root / "L3" / subplane / artifact_names[subplane]
        if not artifact_path.exists():
            _write_md(artifact_path, template_fm, template_body)

    (root / "L3" / "tex").mkdir(parents=True, exist_ok=True)
    return _GateResult({
        "message": f"Advanced to L3 {entry_subplane} (mode: {l3_mode}).",
        "popup_gate": {
            "question": f"L1 complete. Start L3 in {l3_mode} mode ({entry_subplane})?",
            "header": "L1->L3",
            "options": [
                {"label": "Start", "description": f"Proceed to L3 {l3_mode} mode, starting at {entry_subplane}."},
                {"label": "Review L1 first", "description": "Go back and review L1 artifacts before advancing."},
            ],
        },
    })


@mcp.tool()
def aitp_advance_l3_subplane(
    topics_root: str, topic_slug: str, target_subplane: str,
) -> str:
    """Advance the L3 subplane. Only allows valid forward transitions and backedges.

    Transition rules depend on l3_mode:
    - research: ideation -> planning -> analysis -> result_integration -> distillation
    - study: source_decompose -> step_derive -> gap_audit -> synthesis
    """
    root = _topic_root(topics_root, topic_slug)
    state_path = root / "state.md"
    fm, body = _parse_md(state_path)
    l3_mode = str(fm.get("l3_mode", "research")).strip() or "research"

    (
        subplanes,
        allowed_transitions,
        _,
        _,
        skill_map,
        _,
        _,
    ) = _get_l3_config(l3_mode)

    if target_subplane not in subplanes:
        return f"Unknown subplane '{target_subplane}' for mode '{l3_mode}'. Valid: {subplanes}"

    current = fm.get("l3_subplane", subplanes[0])
    allowed = allowed_transitions.get(current, [])
    if target_subplane not in allowed:
        return (
            f"Transition from '{current}' to '{target_subplane}' is not allowed "
            f"in {l3_mode} mode. Allowed targets: {allowed}"
        )

    fm["l3_subplane"] = target_subplane
    fm["updated_at"] = _now()
    _write_md(state_path, fm, body)

    skill = skill_map.get(target_subplane, skill_map.get(subplanes[0], "skill-l3-ideate"))
    return f"Advanced to L3/{target_subplane} (mode: {l3_mode}). Follow {skill}."


@mcp.tool()
def aitp_retreat_to_l1(topics_root: str, topic_slug: str, reason: str = "") -> _GateResult:
    """Retreat from L3 back to L1 for re-reading or re-framing. L3 work is preserved.

    Use when analysis reveals insufficient sources, wrong framing, or missing assumptions.
    """
    root = _topic_root(topics_root, topic_slug)
    state_path = root / "state.md"
    fm, body = _parse_md(state_path)
    current_stage = fm.get("stage", "L1")
    if current_stage != "L3":
        return _GateResult({"message": f"Cannot retreat: topic is at {current_stage}, not L3."})

    fm["stage"] = "L1"
    fm["posture"] = "read"
    fm["retreated_from_l3"] = True
    fm["retreat_reason"] = reason
    fm["updated_at"] = _now()
    _write_md(state_path, fm, body)
    _append_to_topic_log(root, f"retreated from L3 to L1: {reason}")
    return _GateResult({
        "message": f"Retreated to L1. L3 artifacts preserved. Register more sources or revise framing.",
        "popup_gate": {
            "question": "Retreated to L1 for re-reading/framing. What do you need to do?",
            "header": "L3→L1",
            "options": [
                {"label": "Register sources", "description": "Add new literature sources to L0 before re-framing."},
                {"label": "Revise framing", "description": "Edit the research question or formal frame based on new insight."},
                {"label": "Resume L3", "description": "Go back to L3 without changes (used register_source separately)."},
            ],
        },
    })


# ---------------------------------------------------------------------------
# L3 mode switching (research <-> study)
# ---------------------------------------------------------------------------


@mcp.tool()
def aitp_switch_l3_mode(
    topics_root: str,
    topic_slug: str,
    new_mode: str,
    reason: str = "",
) -> dict[str, Any]:
    """Switch between L3 research mode and study mode.

    new_mode: research | study
    - research: original derivation (ideation -> planning -> analysis -> result_integration -> distillation)
    - study: literature understanding (source_decompose -> step_derive -> gap_audit -> synthesis)

    Switching preserves current subplane state and resets to the entry subplane
    of the new mode. Use when:
    - research -> study: L3 derivation reveals knowledge gaps needing literature study
    - study -> research: literature study yields new research directions
    """
    valid_modes = {"research", "study"}
    if new_mode not in valid_modes:
        return {"message": f"Invalid mode '{new_mode}'. Valid: {sorted(valid_modes)}"}

    root = _topic_root(topics_root, topic_slug)
    state_path = root / "state.md"
    fm, body = _parse_md(state_path)

    if fm.get("stage") not in ("L3", "L1"):
        return _GateResult({
            "message": f"Cannot switch L3 mode: topic is at {fm.get('stage')}, not L3/L1.",
        })

    old_mode = fm.get("l3_mode", "research")
    if old_mode == new_mode:
        return {"message": f"Already in '{new_mode}' mode. No change needed."}

    # Determine entry subplane for new mode
    _, _, _, _, _, _, entry_subplane = _get_l3_config(new_mode)

    fm["l3_mode"] = new_mode
    fm["previous_l3_mode"] = old_mode
    fm["l3_mode_switch_reason"] = reason
    fm["l3_mode_switched_at"] = _now()
    if fm.get("stage") == "L3":
        fm["l3_subplane"] = entry_subplane
    fm["updated_at"] = _now()
    _write_md(state_path, fm, body)

    if fm.get("stage") == "L3":
        # Create subplane directories and scaffolds for new mode
        subplanes, _, templates, artifact_names, _, _, _ = _get_l3_config(new_mode)
        for subplane in subplanes:
            (root / "L3" / subplane).mkdir(parents=True, exist_ok=True)
            _, template_fm, template_body = templates[subplane]
            artifact_path = root / "L3" / subplane / artifact_names[subplane]
            if not artifact_path.exists():
                _write_md(artifact_path, template_fm, template_body)

    _append_to_topic_log(root, f"switched L3 mode: {old_mode} -> {new_mode} ({reason})")

    mode_desc = {
        "research": "ideation -> planning -> analysis -> result_integration -> distillation",
        "study": "source_decompose -> step_derive -> gap_audit -> synthesis",
    }
    return _GateResult({
        "message": (
            f"Switched L3 mode from '{old_mode}' to '{new_mode}'. "
            f"New subplane flow: {mode_desc[new_mode]}. "
            f"Entry subplane: {entry_subplane}."
        ),
        "old_mode": old_mode,
        "new_mode": new_mode,
        "entry_subplane": entry_subplane,
    })


# ---------------------------------------------------------------------------
# Flow TeX
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# L4 physics adjudication
# ---------------------------------------------------------------------------


@mcp.tool()
def aitp_submit_l4_review(
    topics_root: str,
    topic_slug: str,
    candidate_id: str,
    outcome: str,
    notes: str = "",
    check_results: dict[str, str] | None = None,
    evidence_scripts: list[str] | None = None,
    evidence_outputs: list[str] | None = None,
    execution_environment: str = "",
    data_provenance: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Submit an L4 review with one of the six validation outcomes. Returns popup gate.

    EVIDENCE REQUIREMENTS BY LANE:
    - toy_numeric / code_method: evidence_scripts and evidence_outputs are REQUIRED for 'pass'.
      Every data point must have a data_provenance entry tracing it to a specific script execution.
    - formal_theory: check_results dict is the primary evidence carrier. Required entries:
      dimensional_consistency, symmetry_compatibility, limiting_case_check, correspondence_check.
      evidence_scripts/outputs are optional but recommended for automated symbolic checks (SymPy).
      The check_results values should describe WHAT was verified and the outcome (e.g., "pass: all
      terms have units of energy; RHS and LHS match under ℏ=c=1").

    data_provenance: list of dicts, each with keys:
      - data_point: what was measured/computed
      - script: path to the script that produced it
      - executed_at: ISO timestamp of execution
      - method: brief description of how it was computed
    """
    if outcome not in L4_OUTCOMES:
        return {"message": f"Invalid outcome '{outcome}'. Valid: {L4_OUTCOMES}"}

    root = _topic_root(topics_root, topic_slug)
    slug = _slugify(candidate_id)

    # Lane-aware evidence requirement
    state_fm, _ = _parse_md(root / "state.md")
    lane = state_fm.get("lane", "")
    needs_evidence = lane in ("toy_numeric", "code_method")

    if needs_evidence and outcome == "pass":
        if not evidence_scripts or not evidence_outputs:
            return {
                "message": (
                    f"BLOCKED: Lane '{lane}' requires evidence_scripts and evidence_outputs "
                    f"for L4 pass reviews. You must:\n"
                    f"1. Write validation scripts and save them (e.g., L4/scripts/)\n"
                    f"2. Execute them on the target machine specified in the plan\n"
                    f"3. Record output paths (e.g., L4/outputs/)\n"
                    f"4. Re-submit with evidence_scripts=[...] and evidence_outputs=[...]"
                ),
            }

    (root / "L4" / "reviews").mkdir(parents=True, exist_ok=True)
    cycle = int(state_fm.get("l4_cycle_count", 0)) + 1
    # Versioned review: cand-1_v1.md, cand-1_v2.md, etc. Also overwrite latest.
    version_tag = f"_v{cycle}"
    review_path_versioned = root / "L4" / "reviews" / f"{slug}{version_tag}.md"
    review_path = root / "L4" / "reviews" / f"{slug}.md"

    fm = {
        "artifact_kind": "l4_review",
        "stage": "L4",
        "candidate_id": slug,
        "outcome": outcome,
        "l4_cycle": cycle,
        "reviewed_at": _now(),
    }
    if check_results:
        fm["check_results"] = check_results
    if evidence_scripts:
        fm["evidence_scripts"] = evidence_scripts
    if evidence_outputs:
        fm["evidence_outputs"] = evidence_outputs
    if execution_environment:
        fm["execution_environment"] = execution_environment
    if data_provenance:
        fm["data_provenance"] = data_provenance

    body = (
        f"# Review: {slug}\n\n"
        f"## Outcome\n{outcome}\n\n"
        f"## Notes\n{notes}\n\n"
    )
    if execution_environment:
        body += f"## Execution Environment\n{execution_environment}\n\n"
    if evidence_scripts:
        body += "## Evidence Scripts\n" + "\n".join(f"- `{s}`" for s in evidence_scripts) + "\n\n"
    if evidence_outputs:
        body += "## Evidence Outputs\n" + "\n".join(f"- `{o}`" for o in evidence_outputs) + "\n\n"
    body += "## Check Results\n"
    if check_results:
        for check, result in check_results.items():
            body += f"- {check}: {result}\n"
    else:
        body += "No individual check results recorded.\n"
    if data_provenance:
        body += "\n## Data Provenance\n"
        for entry in data_provenance:
            body += (
                f"- **{entry.get('data_point', '?')}**\n"
                f"  - Script: `{entry.get('script', '?')}`\n"
                f"  - Executed: {entry.get('executed_at', '?')}\n"
                f"  - Method: {entry.get('method', '?')}\n"
            )

    _write_md(review_path, fm, body)
    _write_md(review_path_versioned, fm, body)  # Preserve history across cycles
    _append_to_topic_log(root, f"L4 review (cycle {cycle}): {slug} -> {outcome}")

    # Update candidate status based on L4 outcome
    cand_path = root / "L3" / "candidates" / f"{slug}.md"
    if cand_path.exists():
        cand_fm, cand_body = _parse_md(cand_path)
        if outcome == "pass":
            cand_fm["status"] = "validated"
            cand_fm["validated_at"] = _now()
        elif outcome == "partial_pass":
            cand_fm["status"] = "partial_validated"
            cand_fm["l4_notes"] = notes
        elif outcome in ("fail", "contradiction", "stuck", "timeout"):
            cand_fm["l4_outcome"] = outcome
            cand_fm["l4_notes"] = notes
        _write_md(cand_path, cand_fm, cand_body)

    result: dict[str, Any] = {"message": f"L4 review submitted for {slug}: {outcome} (cycle {cycle})."}
    result["l4_cycle"] = cycle

    if outcome != "pass":
        result["popup_gate"] = {
            "question": f"L4 review outcome was '{outcome}' (not pass). How to proceed?",
            "header": "L4 Review",
            "options": [
                {"label": "Revise candidate", "description": "Return to L3 and revise the candidate based on review findings."},
                {"label": "Re-validate", "description": "Re-run validation with adjusted criteria."},
                {"label": "Abandon candidate", "description": "Discard this candidate and try a different approach."},
            ],
        }
    return _GateResult(result)


# ---------------------------------------------------------------------------
# Topic lifecycle
# ---------------------------------------------------------------------------


@mcp.tool()
def aitp_archive_topic(
    topics_root: str,
    topic_slug: str,
    reason: str = "",
    reason_category: str = "abandoned",
) -> dict[str, Any]:
    """Archive a topic, marking it as abandoned or paused. Preserves all artifacts.

    reason_category: abandoned | paused | superseded | merged_into_another
    Returns a popup gate for confirmation.
    """
    valid_categories = {"abandoned", "paused", "superseded", "merged_into_another"}
    if reason_category not in valid_categories:
        return {"message": f"Invalid reason_category '{reason_category}'. Valid: {sorted(valid_categories)}"}

    root = _topic_root(topics_root, topic_slug)
    state_path = root / "state.md"
    fm, body = _parse_md(state_path)

    if fm.get("stage") == "archived":
        return {"message": f"Topic {topic_slug} is already archived."}

    old_stage = fm.get("stage", "unknown")
    fm["stage"] = "archived"
    fm["previous_stage"] = old_stage
    fm["archive_reason"] = reason
    fm["archive_category"] = reason_category
    fm["archived_at"] = _now()
    fm["updated_at"] = _now()
    _write_md(state_path, fm, body)
    _append_to_topic_log(root, f"archived ({reason_category}): {reason}")

    return _GateResult({
        "message": f"Topic {topic_slug} archived ({reason_category}). All artifacts preserved.",
        "popup_gate": {
            "question": f"Archive topic '{fm.get('title', topic_slug)}' as {reason_category}?",
            "header": "Archive",
            "options": [
                {"label": "Confirm archive", "description": f"Mark as {reason_category}. Artifacts preserved for future reference."},
                {"label": "Cancel", "description": "Keep the topic active and continue working."},
            ],
        },
    })


@mcp.tool()
def aitp_restore_topic(
    topics_root: str,
    topic_slug: str,
) -> str:
    """Restore an archived topic to its previous stage."""
    root = _topic_root(topics_root, topic_slug)
    state_path = root / "state.md"
    fm, body = _parse_md(state_path)

    if fm.get("stage") != "archived":
        return f"Topic {topic_slug} is not archived (stage: {fm.get('stage')})."

    previous = fm.pop("previous_stage", "L1")
    fm["stage"] = previous
    fm.pop("archived_at", None)
    fm.pop("archive_reason", None)
    fm.pop("archive_category", None)
    fm["updated_at"] = _now()
    _write_md(state_path, fm, body)
    _append_to_topic_log(root, f"restored from archive to {previous}")
    return f"Topic {topic_slug} restored to stage {previous}."


@mcp.tool()
def aitp_switch_lane(
    topics_root: str,
    topic_slug: str,
    new_lane: str,
    reason: str = "",
) -> dict[str, Any]:
    """Switch the research lane for an active topic. Records old/new lane and reason.

    new_lane: formal_theory | toy_numeric | code_method | unspecified
    Valid transitions: any lane to any other lane. Common patterns:
      - formal_theory → toy_numeric: analytical derivation hit a dead end
      - toy_numeric → code_method: need production-quality computation
      - code_method → formal_theory: numerical results suggest a clean analytical form
    """
    valid_lanes = {"formal_theory", "toy_numeric", "code_method", "unspecified"}
    if new_lane not in valid_lanes:
        return {"message": f"Invalid lane '{new_lane}'. Valid: {sorted(valid_lanes)}"}

    root = _topic_root(topics_root, topic_slug)
    state_path = root / "state.md"
    fm, body = _parse_md(state_path)

    old_lane = fm.get("lane", "unspecified")
    if old_lane == new_lane:
        return {"message": f"Topic is already on lane '{new_lane}'. No change needed."}

    fm["lane"] = new_lane
    fm["previous_lane"] = old_lane
    fm["lane_switch_reason"] = reason
    fm["lane_switched_at"] = _now()
    fm["updated_at"] = _now()
    _write_md(state_path, fm, body)
    _append_to_topic_log(root, f"switched lane: {old_lane} -> {new_lane} ({reason})")

    return {
        "message": f"Switched lane from '{old_lane}' to '{new_lane}'.",
        "old_lane": old_lane,
        "new_lane": new_lane,
        "note": "L4 evidence requirements change with lane. Review validation contract.",
    }


@mcp.tool()
def aitp_set_compute_target(
    topics_root: str,
    topic_slug: str,
    target: str,
) -> dict[str, Any]:
    """Set the compute target for a topic. Agents MUST check this before
    running any code, numerical computation, SymPy, Lean, or heavy I/O.

    Valid targets:
      - local: this machine, lightweight only (small SymPy, quick checks)
      - fisher: Fisher server via ssh-mcp (numerical diagonalization, QSGW, LibRPA)
      - lean-remote: remote Lean server via lean-lsp-mcp (mathlib compilation)

    The compute target is returned by aitp_get_execution_brief and
    aitp_get_status so agents always know where to execute.
    """
    valid_targets = {"local", "fisher", "lean-remote"}
    if target not in valid_targets:
        return {
            "message": f"Invalid compute target '{target}'. Valid: {sorted(valid_targets)}",
            "valid_targets": sorted(valid_targets),
        }

    root = _topic_root(topics_root, topic_slug)
    state_path = root / "state.md"
    fm, body = _parse_md(state_path)

    old_target = fm.get("compute", "local")
    fm["compute"] = target
    fm["compute_set_at"] = _now()
    fm["updated_at"] = _now()
    _write_md(state_path, fm, body)
    _append_to_topic_log(
        root,
        f"compute target: {old_target} -> {target}",
    )

    return {
        "message": f"Compute target set to '{target}' (was '{old_target}').",
        "old_target": old_target,
        "new_target": target,
        "note": (
            "Agents must route all computation, numerical work, SymPy, "
            "and Lean compilation to this target. Do NOT execute heavy "
            "workloads on the wrong machine."
        ),
    }


@mcp.tool()
def aitp_fork_topic(
    topics_root: str,
    parent_slug: str,
    child_slug: str,
    title: str,
    question: str,
    copy_l1_artifacts: bool = True,
    reason: str = "",
) -> str:
    """Fork a new topic from a side-discovery in an existing topic.

    Creates a new topic with optional L1 artifact copies from the parent.
    Links parent and child in both topics' runtime logs.
    """
    safe_child = validate_topic_slug(child_slug)
    base = topics_dir(topics_root)
    child_root = base / safe_child

    if child_root.exists():
        return f"Topic {safe_child} already exists."

    parent_root = _topic_root(topics_root, parent_slug)
    parent_fm, _ = _parse_md(parent_root / "state.md")

    # Bootstrap child with same lane as parent
    result = aitp_bootstrap_topic(
        topics_root, safe_child, title, question,
        lane=parent_fm.get("lane", "unspecified"),
    )

    child_root = base / safe_child

    # Copy L1 artifacts if requested
    if copy_l1_artifacts:
        for artifact_name in L1_ARTIFACT_TEMPLATES:
            src = parent_root / "L1" / artifact_name
            dst = child_root / "L1" / artifact_name
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                _atomic_write_text(dst, src.read_text(encoding="utf-8"))

    # Record provenance
    state_path = child_root / "state.md"
    fm, body = _parse_md(state_path)
    fm["forked_from"] = parent_slug
    fm["fork_reason"] = reason
    fm["forked_at"] = _now()
    _write_md(state_path, fm, body)

    _append_to_topic_log(child_root, f"forked from {parent_slug}: {reason}")
    _append_to_topic_log(parent_root, f"forked child topic {safe_child}: {reason}")

    return result + f" Forked from {parent_slug}."


# ---------------------------------------------------------------------------
# Knowledge-base operations
# ---------------------------------------------------------------------------


def _append_to_topic_log(root: Path, event: str) -> None:
    """Append a dated event to the topic runtime log."""
    log_path = root / "runtime" / "log.md"
    if log_path.exists():
        existing = log_path.read_text(encoding="utf-8")
    else:
        existing = f"# Topic Log\n\n## Events\n"
    if not existing.endswith("\n"):
        existing += "\n"
    _atomic_write_text(log_path, existing + f"- {_now()} {event}\n")


def _global_l2_path(topics_root: str) -> Path:
    base = topics_dir(topics_root)
    return base.parent / "L2" if base.name == "topics" else Path(topics_root).parent / "L2"


@mcp.tool()
def aitp_query_l2(
    topics_root: str,
    query: str = "",
) -> dict[str, Any]:
    """Query the global L2 knowledge base (cross-topic validated claims).

    Returns all promoted candidates with their claims, trust basis, scope,
    and any conflicts. Optionally filter by query substring match on claim text.
    Use this when starting a new topic to check existing validated knowledge.
    """
    global_l2 = _global_l2_path(topics_root)
    if not global_l2.is_dir():
        return {"message": "Global L2 directory not found.", "results": [], "count": 0}

    results = []
    conflicts = []
    conflict_dir = global_l2 / "conflicts"
    if conflict_dir.is_dir():
        for cp in sorted(conflict_dir.glob("*.md")):
            cfm, _ = _parse_md(cp)
            conflicts.append({
                "candidate_id": cfm.get("candidate_id", cp.stem),
                "existing_claim": cfm.get("existing_claim", ""),
                "new_claim": cfm.get("new_claim", ""),
            })

    for l2_path in sorted(global_l2.glob("*.md")):
        if l2_path.parent.name == "conflicts":
            continue
        fm, body = _parse_md(l2_path)
        claim_text = str(fm.get("claim", ""))
        title = str(fm.get("title", ""))
        if query:
            score = semantic_score(query, [title, claim_text, body])
            if score < 0.15:
                continue
        else:
            score = 1.0
        results.append({
            "candidate_id": fm.get("candidate_id", l2_path.stem),
            "title": title,
            "claim": claim_text,
            "trust_basis": fm.get("trust_basis", ""),
            "trust_scope": fm.get("trust_scope", ""),
            "version": fm.get("version", 1),
            "promoted_at": fm.get("promoted_at", ""),
            "relevance": round(score, 3),
        })

    results.sort(key=lambda r: r.get("relevance", 0.0), reverse=True)
    return {
        "results": results,
        "conflicts": conflicts,
        "count": len(results),
        "authority_level": "L2_validated_reusable",
    }


# ---------------------------------------------------------------------------
# L2 knowledge graph operations
# ---------------------------------------------------------------------------


def _ensure_l2_graph_dirs(topics_root: str) -> Path:
    """Ensure L2/graph/ directories exist and return the graph root."""
    global_l2 = _global_l2_path(topics_root)
    for sub in ["graph/nodes", "graph/edges", "graph/towers"]:
        (global_l2 / sub).mkdir(parents=True, exist_ok=True)
    return global_l2


@mcp.tool()
def aitp_create_l2_node(
    topics_root: str,
    node_id: str,
    node_type: str,
    title: str,
    physical_meaning: str = "",
    mathematical_expression: str = "",
    regime_of_validity: str = "",
    tower: str = "",
    aliases: list[str] | None = None,
    units: str = "",
    source_candidate: str = "",
    energy_scale: str = "",
) -> str:
    """Create a node in the L2 knowledge graph.

    node_type: concept | theorem | technique | derivation_chain | result | approximation | open_question | regime_boundary
    """
    if node_type not in L2_NODE_TYPES:
        return f"Invalid node_type '{node_type}'. Valid: {L2_NODE_TYPES}"

    global_l2 = _ensure_l2_graph_dirs(topics_root)
    slug = _slugify(node_id)
    node_path = global_l2 / "graph" / "nodes" / f"{slug}.md"

    # Check for existing node (merge scenario)
    existing_fm: dict[str, Any] = {}
    if node_path.exists():
        existing_fm, _ = _parse_md(node_path)
        existing_version = int(existing_fm.get("version", 1))
    else:
        existing_version = 0

    fm: dict[str, Any] = {
        "node_id": slug,
        "type": node_type,
        "title": title,
        "regime_of_validity": regime_of_validity,
        "tower": tower,
        "trust_basis": "source_grounded",
        "trust_scope": "single_source",
        "version": existing_version + 1,
        "aliases": aliases or [],
        "units": units,
        "mathematical_expression": mathematical_expression,
        "energy_scale": energy_scale,
        "created_at": existing_fm.get("created_at", _now()),
        "updated_at": _now(),
    }
    if source_candidate:
        fm["source_candidate"] = source_candidate
    # Preserve higher trust level if merging
    if existing_fm:
        trust_order = ["source_grounded", "multi_source_confirmed", "validated", "independently_verified"]
        old_idx = trust_order.index(existing_fm.get("trust_basis", "source_grounded")) if existing_fm.get("trust_basis") in trust_order else 0
        new_idx = trust_order.index(fm["trust_basis"])
        if old_idx > new_idx:
            fm["trust_basis"] = existing_fm["trust_basis"]
            fm["trust_scope"] = existing_fm.get("trust_scope", fm["trust_scope"])

    body = (
        f"# {title}\n\n"
        f"## Physical Meaning\n{physical_meaning}\n\n"
        f"## Mathematical Expression\n{mathematical_expression}\n\n"
        f"## Regime and Limits\n\n"
        f"## Derivation Chain\n\n"
        f"## Open Questions\n"
    )
    _write_md(node_path, fm, body)
    return f"Created L2 graph node {slug} (type={node_type}, v{fm['version']})"


@mcp.tool()
def aitp_update_l2_node(
    topics_root: str,
    node_id: str,
    physical_meaning: str | None = None,
    mathematical_expression: str | None = None,
    regime_of_validity: str | None = None,
    tower: str | None = None,
    aliases: list[str] | None = None,
    trust_level: str | None = None,
) -> str:
    """Update fields of an existing L2 graph node."""
    global_l2 = _global_l2_path(topics_root)
    slug = _slugify(node_id)
    node_path = global_l2 / "graph" / "nodes" / f"{slug}.md"
    if not node_path.exists():
        return f"Node {slug} not found. Use aitp_create_l2_node first."

    fm, body = _parse_md(node_path)
    if physical_meaning is not None:
        fm["physical_meaning"] = physical_meaning
    if mathematical_expression is not None:
        fm["mathematical_expression"] = mathematical_expression
    if regime_of_validity is not None:
        fm["regime_of_validity"] = regime_of_validity
    if tower is not None:
        fm["tower"] = tower
    if aliases is not None:
        fm["aliases"] = aliases
    if trust_level and trust_level in TRUST_EVOLUTION:
        fm.update(TRUST_EVOLUTION[trust_level])
    fm["updated_at"] = _now()
    fm["version"] = int(fm.get("version", 1)) + 1
    _write_md(node_path, fm, body)
    return f"Updated L2 node {slug} (v{fm['version']})"


@mcp.tool()
def aitp_create_l2_edge(
    topics_root: str,
    edge_id: str,
    from_node: str,
    to_node: str,
    edge_type: str,
    regime_condition: str = "",
    evidence: str = "",
    correspondence_verified: bool = False,
) -> str:
    """Create a typed edge between two L2 graph nodes.

    edge_type: limits_to | derives_from | uses | assumes | matches_onto | decouples_at |
               emerges_from | specializes | generalizes | approximates | component_of |
               equivalent_to | contradicts | refines | motivates | proven_by
    """
    if edge_type not in L2_EDGE_TYPES:
        return f"Invalid edge_type '{edge_type}'. Valid: {L2_EDGE_TYPES}"

    global_l2 = _ensure_l2_graph_dirs(topics_root)
    slug = _slugify(edge_id)
    edge_path = global_l2 / "graph" / "edges" / f"{slug}.md"

    # Verify both nodes exist
    from_slug = _slugify(from_node)
    to_slug = _slugify(to_node)
    from_path = global_l2 / "graph" / "nodes" / f"{from_slug}.md"
    to_path = global_l2 / "graph" / "nodes" / f"{to_slug}.md"
    warnings = []
    if not from_path.exists():
        warnings.append(f"Warning: from_node '{from_slug}' not found in L2 graph")
    if not to_path.exists():
        warnings.append(f"Warning: to_node '{to_slug}' not found in L2 graph")

    fm: dict[str, Any] = {
        "edge_id": slug,
        "from_node": from_slug,
        "to_node": to_slug,
        "type": edge_type,
        "regime_condition": regime_condition,
        "correspondence_verified": correspondence_verified,
        "evidence": evidence,
        "created_at": _now(),
    }

    body = (
        f"# Edge: {from_slug} --[{edge_type}]--> {to_slug}\n\n"
        f"## Regime Condition\n{regime_condition}\n\n"
        f"## Evidence\n{evidence}\n\n"
        f"## Verification\n{'Verified' if correspondence_verified else 'Not yet verified'}\n"
    )
    _write_md(edge_path, fm, body)
    msg = f"Created L2 edge {slug} ({from_slug} --[{edge_type}]--> {to_slug})"
    if warnings:
        msg += ". " + "; ".join(warnings)
    return msg


@mcp.tool()
def aitp_query_l2_graph(
    topics_root: str,
    query: str = "",
    node_type: str = "",
    tower: str = "",
    from_node: str = "",
    edge_type: str = "",
) -> dict[str, Any]:
    """Query the L2 knowledge graph with dual-level retrieval.

    Low-level: match specific nodes by type, tower, or query substring.
    High-level: find all edges from a node to explore relationships.
    """
    global_l2 = _global_l2_path(topics_root)
    nodes_dir = global_l2 / "graph" / "nodes"
    edges_dir = global_l2 / "graph" / "edges"

    if not nodes_dir.is_dir():
        return {"message": "L2 graph not initialized.", "nodes": [], "edges": []}

    # Node search (low-level)
    nodes = []
    for np in sorted(nodes_dir.glob("*.md")):
        fm, body = _parse_md(np)
        if node_type and fm.get("type") != node_type:
            continue
        if tower and fm.get("tower") != tower:
            continue
        if query:
            q_fields = [
                str(fm.get("title", "")),
                str(fm.get("physical_meaning", "")),
                str(fm.get("mathematical_expression", "")),
                str(fm.get("aliases", [])),
                body,
            ]
            score = semantic_score(query, q_fields)
            if score < 0.15:
                continue
        else:
            score = 1.0
        nodes.append({
            "node_id": fm.get("node_id", np.stem),
            "title": fm.get("title", ""),
            "type": fm.get("type", ""),
            "tower": fm.get("tower", ""),
            "regime_of_validity": fm.get("regime_of_validity", ""),
            "trust_basis": fm.get("trust_basis", ""),
            "trust_scope": fm.get("trust_scope", ""),
            "version": fm.get("version", 1),
            "mathematical_expression": fm.get("mathematical_expression", ""),
            "relevance": round(score, 3),
        })

    # Edge search (high-level from a specific node)
    edges = []
    if edges_dir.is_dir():
        for ep in sorted(edges_dir.glob("*.md")):
            fm, _ = _parse_md(ep)
            if edge_type and fm.get("type") != edge_type:
                continue
            if from_node:
                fn = _slugify(from_node)
                if fm.get("from_node") != fn and fm.get("to_node") != fn:
                    continue
            edges.append({
                "edge_id": fm.get("edge_id", ep.stem),
                "from_node": fm.get("from_node", ""),
                "to_node": fm.get("to_node", ""),
                "type": fm.get("type", ""),
                "regime_condition": fm.get("regime_condition", ""),
                "correspondence_verified": fm.get("correspondence_verified", False),
            })

    nodes.sort(key=lambda n: n.get("relevance", 0.0), reverse=True)
    return {
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "authority_level": "L2_graph",
    }


@mcp.tool()
def aitp_merge_subgraph_delta(
    topics_root: str,
    topic_slug: str,
    nodes: list[dict[str, str]] | None = None,
    edges: list[dict[str, str]] | None = None,
    missing_prerequisites: list[str] | None = None,
) -> dict[str, Any]:
    """Merge a subgraph delta from study mode into the L2 knowledge graph.

    nodes: list of {node_id, type, title, physical_meaning, mathematical_expression, regime_of_validity, tower}
    edges: list of {edge_id, from_node, to_node, type, regime_condition, evidence}
    missing_prerequisites: list of node_ids that should exist but don't yet
    """
    global_l2 = _ensure_l2_graph_dirs(topics_root)
    root = _topic_root(topics_root, topic_slug)
    results = {"nodes_created": 0, "nodes_updated": 0, "edges_created": 0, "conflicts": [], "missing": []}

    if nodes:
        for nd in nodes:
            nid = _slugify(nd.get("node_id", ""))
            if not nid:
                continue
            node_path = global_l2 / "graph" / "nodes" / f"{nid}.md"
            if node_path.exists():
                # Merge: bump version, potentially upgrade trust
                existing_fm, _ = _parse_md(node_path)
                existing_fm["version"] = int(existing_fm.get("version", 1)) + 1
                existing_fm["updated_at"] = _now()
                # Check for title conflict (different concept, same slug)
                if nd.get("title") and existing_fm.get("title") != nd.get("title"):
                    results["conflicts"].append({
                        "node_id": nid,
                        "existing_title": existing_fm.get("title", ""),
                        "new_title": nd.get("title", ""),
                    })
                _write_md(node_path, existing_fm, _parse_md(node_path)[1])
                results["nodes_updated"] += 1
            else:
                # Create new
                nd_type = nd.get("type", "concept")
                if nd_type not in L2_NODE_TYPES:
                    nd_type = "concept"
                fm = {
                    "node_id": nid,
                    "type": nd_type,
                    "title": nd.get("title", nid),
                    "regime_of_validity": nd.get("regime_of_validity", ""),
                    "tower": nd.get("tower", ""),
                    "trust_basis": "source_grounded",
                    "trust_scope": "single_source",
                    "version": 1,
                    "mathematical_expression": nd.get("mathematical_expression", ""),
                    "source_topic": topic_slug,
                    "created_at": _now(),
                    "updated_at": _now(),
                }
                body = (
                    f"# {nd.get('title', nid)}\n\n"
                    f"## Physical Meaning\n{nd.get('physical_meaning', '')}\n\n"
                    f"## Mathematical Expression\n{nd.get('mathematical_expression', '')}\n\n"
                    f"## Regime and Limits\n{nd.get('regime_of_validity', '')}\n\n"
                    f"## Open Questions\n"
                )
                _write_md(node_path, fm, body)
                results["nodes_created"] += 1

    if edges:
        for ed in edges:
            eid = _slugify(ed.get("edge_id", ""))
            if not eid:
                continue
            edge_path = global_l2 / "graph" / "edges" / f"{eid}.md"
            if edge_path.exists():
                continue  # Don't overwrite edges
            ed_type = ed.get("type", "uses")
            if ed_type not in L2_EDGE_TYPES:
                ed_type = "uses"
            fm = {
                "edge_id": eid,
                "from_node": _slugify(ed.get("from_node", "")),
                "to_node": _slugify(ed.get("to_node", "")),
                "type": ed_type,
                "regime_condition": ed.get("regime_condition", ""),
                "evidence": ed.get("evidence", ""),
                "correspondence_verified": False,
                "source_topic": topic_slug,
                "created_at": _now(),
            }
            body = (
                f"# Edge: {fm['from_node']} --[{ed_type}]--> {fm['to_node']}\n\n"
                f"## Regime Condition\n{fm['regime_condition']}\n\n"
                f"## Evidence\n{fm['evidence']}\n"
            )
            _write_md(edge_path, fm, body)
            results["edges_created"] += 1

    if missing_prerequisites:
        for mp in missing_prerequisites:
            mp_slug = _slugify(mp)
            mp_path = global_l2 / "graph" / "nodes" / f"{mp_slug}.md"
            if not mp_path.exists():
                results["missing"].append(mp_slug)

    _append_to_topic_log(
        root,
        f"L2 graph merge: {results['nodes_created']} created, "
        f"{results['nodes_updated']} updated, {results['edges_created']} edges, "
        f"{len(results['conflicts'])} conflicts, {len(results['missing'])} missing",
    )
    return results


# ---------------------------------------------------------------------------
# Quality assurance tools (study mode)
# ---------------------------------------------------------------------------


@mcp.tool()
def aitp_create_l2_tower(
    topics_root: str,
    tower_id: str,
    name: str,
    energy_range: str,
    layers: list[dict[str, str]] | None = None,
) -> str:
    """Define an EFT tower in the L2 knowledge graph.

    layers: list of {id, energy_scale, theories (comma-separated node_ids)}
    """
    global_l2 = _ensure_l2_graph_dirs(topics_root)
    slug = _slugify(tower_id)
    tower_path = global_l2 / "graph" / "towers" / f"{slug}.md"

    fm = {
        "kind": "l2_tower",
        "tower_id": slug,
        "name": name,
        "energy_range": energy_range,
        "layers": layers or [],
        "created_at": _now(),
        "updated_at": _now(),
    }

    layer_lines = []
    for layer in (layers or []):
        layer_lines.append(
            f"### {layer.get('id', 'unknown')}\n"
            f"- Energy scale: {layer.get('energy_scale', '')}\n"
            f"- Theories: {layer.get('theories', '')}\n"
        )

    body = (
        f"# {name}\n\n"
        f"Energy range: {energy_range}\n\n"
        f"## Layers\n\n{''.join(layer_lines) if layer_lines else 'No layers defined yet.'}\n\n"
        f"## Correspondence Links\n\n"
        f"## Open Boundaries\n"
    )
    _write_md(tower_path, fm, body)
    return f"Created EFT tower {slug}: {name}"


# ---------------------------------------------------------------------------
# L5 writing
# ---------------------------------------------------------------------------

_L5_ARTIFACTS = {
    "outline.md":
        "# Writing Outline\n\n## Title\n\n## Claims\n\n## Structure\n\n"
        "## Target Audience\n\n## Key Equations\n",
    "claim_evidence_map.md":
        "# Claim-Evidence Map\n\n## Claims\n\n## Evidence Links\n\n"
        "## Provenance Chain\n\n## Confidence Per Claim\n",
    "equation_provenance.md":
        "# Equation Provenance\n\n## Equations\n\n## Source Classification\n\n"
        "## Derivation Chain\n\n## Verification Status\n",
    "figure_provenance.md":
        "# Figure Provenance\n\n## Figures\n\n## Source Data\n\n"
        "## Reproducibility Notes\n",
    "limitations.md":
        "# Limitations\n\n## Non-Claims\n\n## Unresolved Issues\n\n"
        "## Regime Boundaries\n\n## Negative Results\n",
}


@mcp.tool()
def aitp_advance_to_l5(topics_root: str, topic_slug: str) -> dict[str, Any]:
    """Transition from L4 to L5 writing. Returns popup gate."""
    root = _topic_root(topics_root, topic_slug)
    state_path = root / "state.md"
    fm, body = _parse_md(state_path)
    fm["stage"] = "L5"
    fm["posture"] = "write"
    fm["updated_at"] = _now()
    _write_md(state_path, fm, body)

    # Create L5 scaffolds
    l5_dir = root / "L5_writing"
    l5_dir.mkdir(parents=True, exist_ok=True)
    for name, content in _L5_ARTIFACTS.items():
        path = l5_dir / name
        if not path.exists():
            _write_md(path, {
                "artifact_kind": f"l5_{name.replace('.', '_')}",
                "stage": "L5",
                "created_at": _now(),
            }, content)

    _append_to_topic_log(root, "advanced to L5 writing")
    return _GateResult({
        "message": "Advanced to L5 writing. Fill provenance artifacts before drafting.",
        "popup_gate": {
            "question": "Ready to start the L5 writing phase?",
            "header": "L4->L5",
            "options": [
                {"label": "Start writing", "description": "Proceed to L5 writing. Draft the paper from validated results."},
                {"label": "Review first", "description": "Review the flow notebook and validation results before writing."},
            ],
        },
    })


# ---------------------------------------------------------------------------
# Visualization tools (Phase 4)
# ---------------------------------------------------------------------------


@mcp.tool()
def aitp_visualize_eft_tower(
    topics_root: str,
    tower_id: str,
) -> dict[str, Any]:
    """Render an EFT tower as a structured ASCII diagram with energy axis, nodes, and correspondence links.

    Returns a dict with 'ascii' (text diagram) and 'metadata' (layer/node counts).
    """
    global_l2 = _global_l2_path(topics_root)
    tower_path = global_l2 / "graph" / "towers" / f"{_slugify(tower_id)}.md"
    if not tower_path.exists():
        return {"error": f"Tower '{tower_id}' not found."}

    fm, body = _parse_md(tower_path)
    layers = fm.get("layers", [])
    if not layers:
        return {"ascii": f"# {fm.get('name', tower_id)}\n\n(no layers defined)", "metadata": {"layer_count": 0}}

    # Build node lookup for titles
    nodes_dir = global_l2 / "graph" / "nodes"
    node_titles = {}
    if nodes_dir.exists():
        for np in nodes_dir.glob("*.md"):
            nfm, _ = _parse_md(np)
            node_titles[np.stem] = nfm.get("title", np.stem)

    # Build correspondence edges for this tower's nodes
    edges_dir = global_l2 / "graph" / "edges"
    corr_edges = []
    tower_node_ids = set()
    for layer in layers:
        theories = layer.get("theories", "")
        for t in theories.split(","):
            t = t.strip()
            if t:
                tower_node_ids.add(_slugify(t))

    if edges_dir.exists():
        for ep in edges_dir.glob("*.md"):
            efm, _ = _parse_md(ep)
            if efm.get("type") in ("limits_to", "matches_onto", "emerges_from"):
                fn = efm.get("from_node", "")
                tn = efm.get("to_node", "")
                if fn in tower_node_ids or tn in tower_node_ids:
                    corr_edges.append({
                        "from": fn,
                        "to": tn,
                        "type": efm.get("type", ""),
                        "condition": efm.get("regime_condition", ""),
                        "verified": efm.get("correspondence_verified", False),
                    })

    # Render ASCII tower
    lines = []
    lines.append(f"# {fm.get('name', tower_id)}")
    lines.append(f"# Energy range: {fm.get('energy_range', '?')}")
    lines.append("")
    lines.append("  Energy")
    lines.append("    ^")

    for i, layer in enumerate(reversed(layers)):
        lid = layer.get("id", f"layer-{i}")
        escale = layer.get("energy_scale", "?")
        theories = layer.get("theories", "")
        theory_list = [t.strip() for t in theories.split(",") if t.strip()]
        theory_names = [node_titles.get(_slugify(t), t) for t in theory_list]

        # Find correspondence edges involving this layer's nodes
        layer_edges = []
        for e in corr_edges:
            for t in theory_list:
                if _slugify(t) in (e["from"], e["to"]):
                    layer_edges.append(e)

        if i == 0 and len(layers) > 1:
            lines.append("    |")
        lines.append(f"    +-- [{escale}]  {lid}")
        for tn in theory_names:
            lines.append(f"    |   |  - {tn}")
        for e in layer_edges:
            arrow = "-->" if e["type"] == "limits_to" else "<--" if e["type"] == "emerges_from" else "==>"
            v_mark = " [verified]" if e.get("verified") else " [unverified]"
            partner = e["to"] if e["from"] in {_slugify(t) for t in theory_list} else e["from"]
            lines.append(f"    |   |  {arrow} {partner}{v_mark}")
        lines.append("    |")

    lines.append("    v")
    lines.append("  (IR limit)")
    lines.append("")

    # Correspondence summary
    if corr_edges:
        lines.append("## Correspondence Links")
        for e in corr_edges:
            v = "OK" if e.get("verified") else "!!"
            lines.append(f"  [{v}] {e['from']} --[{e['type']}]--> {e['to']}")
            if e.get("condition"):
                lines.append(f"       when: {e['condition']}")
        lines.append("")

    return {
        "ascii": "\n".join(lines),
        "metadata": {
            "tower_id": _slugify(tower_id),
            "layer_count": len(layers),
            "node_count": len(tower_node_ids),
            "correspondence_count": len(corr_edges),
            "unverified_count": sum(1 for e in corr_edges if not e.get("verified")),
        },
    }


@mcp.tool()
def aitp_visualize_derivation_chain(
    topics_root: str,
    node_id: str,
) -> dict[str, Any]:
    """Render a derivation chain as a step-by-step ASCII diagram with justifications and dependencies.

    Reads a derivation_chain node and traces connected edges to build a visual chain.
    """
    global_l2 = _global_l2_path(topics_root)
    node_path = global_l2 / "graph" / "nodes" / f"{_slugify(node_id)}.md"
    if not node_path.exists():
        return {"error": f"Node '{node_id}' not found."}

    fm, body = _parse_md(node_path)
    if fm.get("type") != "derivation_chain":
        return {"error": f"Node '{node_id}' is type '{fm.get('type')}', not 'derivation_chain'."}

    # Parse body for step information
    # Expected sections: ## Step-by-Step Trace or inline steps
    steps = []
    lines = body.split("\n")
    step_idx = 0
    in_steps = False
    current_step = None

    for line in lines:
        if "## Step-by-Step" in line or "## Steps" in line:
            in_steps = True
            continue
        if in_steps and line.startswith("## "):
            in_steps = False
            if current_step:
                steps.append(current_step)
                current_step = None
            continue
        if in_steps and line.strip().startswith("- ") or line.strip().startswith("* "):
            if current_step:
                steps.append(current_step)
            step_idx += 1
            current_step = {"step_id": f"S{step_idx}", "text": line.strip()[2:], "depends_on": [], "justification": ""}
        elif in_steps and current_step and line.strip():
            current_step["text"] += " " + line.strip()
    if current_step:
        steps.append(current_step)

    # Find connected nodes via edges
    edges_dir = global_l2 / "graph" / "edges"
    incoming = []
    outgoing = []
    slug = _slugify(node_id)
    if edges_dir.exists():
        for ep in edges_dir.glob("*.md"):
            efm, _ = _parse_md(ep)
            if efm.get("from_node") == slug:
                outgoing.append({"to": efm.get("to_node", ""), "type": efm.get("type", "")})
            elif efm.get("to_node") == slug:
                incoming.append({"from": efm.get("from_node", ""), "type": efm.get("type", "")})

    # Build node title lookup
    nodes_dir = global_l2 / "graph" / "nodes"
    node_titles = {}
    if nodes_dir.exists():
        for np in nodes_dir.glob("*.md"):
            nfm, _ = _parse_md(np)
            node_titles[np.stem] = nfm.get("title", np.stem)

    # Render ASCII
    out = []
    out.append(f"# Derivation Chain: {fm.get('title', node_id)}")
    out.append(f"Regime: {fm.get('regime_of_validity', 'unspecified')}")
    out.append(f"Trust: {fm.get('trust_basis', 'unknown')}")
    out.append("")

    if incoming:
        out.append("## Prerequisites")
        for inc in incoming:
            out.append(f"  <-- [{inc['type']}] {node_titles.get(inc['from'], inc['from'])}")
        out.append("")

    if steps:
        out.append("## Steps")
        for step in steps:
            out.append(f"  [{step['step_id']}] {step['text']}")
            if step.get("justification"):
                out.append(f"       just: {step['justification']}")
            if step.get("depends_on"):
                out.append(f"       deps: {', '.join(step['depends_on'])}")
            out.append("       |")
        out.append("       v")
    else:
        out.append("## Steps (from body text)")
        for line in body.split("\n"):
            if line.strip():
                out.append(f"  {line}")
        out.append("")

    if outgoing:
        out.append("## Results")
        for og in outgoing:
            out.append(f"  --> [{og['type']}] {node_titles.get(og['to'], og['to'])}")
        out.append("")

    return {
        "ascii": "\n".join(out),
        "metadata": {
            "node_id": slug,
            "step_count": len(steps),
            "incoming_edges": len(incoming),
            "outgoing_edges": len(outgoing),
        },
    }


@mcp.tool()
def aitp_visualize_knowledge_graph(
    topics_root: str,
    center_node: str = "",
    max_depth: int = 2,
    node_type: str = "",
) -> dict[str, Any]:
    """Render a local subgraph of the L2 knowledge graph as an ASCII diagram.

    Shows nodes, edges, trust levels, conflicts, and missing prerequisites.
    If center_node is given, shows its neighborhood up to max_depth.
    If node_type is given, filters to that type.
    """
    global_l2 = _global_l2_path(topics_root)
    nodes_dir = global_l2 / "graph" / "nodes"
    edges_dir = global_l2 / "graph" / "edges"
    conflicts_dir = global_l2 / "conflicts"

    if not nodes_dir.exists() or not any(nodes_dir.iterdir()):
        return {"ascii": "(empty graph)", "metadata": {"node_count": 0, "edge_count": 0}}

    # Load all nodes
    all_nodes = {}
    for np in nodes_dir.glob("*.md"):
        nfm, _ = _parse_md(np)
        nid = np.stem
        all_nodes[nid] = {
            "id": nid,
            "type": nfm.get("type", "unknown"),
            "title": nfm.get("title", nid),
            "trust": nfm.get("trust_basis", ""),
            "regime": nfm.get("regime_of_validity", ""),
            "version": nfm.get("version", 1),
        }

    # Filter by type if requested
    if node_type:
        all_nodes = {k: v for k, v in all_nodes.items() if v["type"] == node_type}

    # Load all edges
    all_edges = []
    if edges_dir.exists():
        for ep in edges_dir.glob("*.md"):
            efm, _ = _parse_md(ep)
            all_edges.append({
                "id": ep.stem,
                "from": efm.get("from_node", ""),
                "to": efm.get("to_node", ""),
                "type": efm.get("type", ""),
                "verified": efm.get("correspondence_verified", False),
            })

    # Determine visible subgraph
    if center_node:
        center = _slugify(center_node)
        visible = {center}
        frontier = {center}
        for _ in range(max_depth):
            next_frontier = set()
            for nid in frontier:
                for e in all_edges:
                    if e["from"] == nid and e["to"] in all_nodes:
                        next_frontier.add(e["to"])
                    if e["to"] == nid and e["from"] in all_nodes:
                        next_frontier.add(e["from"])
            visible |= next_frontier
            frontier = next_frontier
        nodes = {k: v for k, v in all_nodes.items() if k in visible}
        edges = [e for e in all_edges if e["from"] in visible and e["to"] in visible]
    else:
        nodes = all_nodes
        edges = all_edges

    # Load conflicts
    conflicts = []
    if conflicts_dir.exists():
        for cp in conflicts_dir.glob("*.md"):
            cfm, _ = _parse_md(cp)
            conflicts.append({
                "id": cp.stem,
                "nodes": cfm.get("involved_nodes", []),
                "description": cfm.get("description", ""),
                "resolved": cfm.get("resolved", False),
            })

    # Find nodes without limits_to edges (potential correspondence gaps)
    result_nodes = {nid for nid, n in nodes.items() if n["type"] in ("result", "approximation")}
    nodes_with_limits = set()
    for e in edges:
        if e["type"] == "limits_to":
            nodes_with_limits.add(e["from"])
    missing_correspondence = result_nodes - nodes_with_limits

    # Type icons
    type_icon = {
        "concept": "[C]", "theorem": "[T]", "technique": "[X]",
        "derivation_chain": "[D]", "result": "[R]", "approximation": "[A]",
        "open_question": "[?]", "regime_boundary": "[B]",
    }

    # Trust markers
    trust_mark = {
        "source_grounded": ".", "multi_source_confirmed": "+",
        "validated": "*", "independently_verified": "**",
    }

    # Render ASCII
    out = []
    out.append("# L2 Knowledge Graph")
    out.append(f"# {len(nodes)} nodes, {len(edges)} edges, {len(conflicts)} conflicts")
    out.append("")

    # Nodes by type
    by_type = {}
    for nid, n in nodes.items():
        by_type.setdefault(n["type"], []).append(n)
    for ntype in sorted(by_type.keys()):
        icon = type_icon.get(ntype, "[?]")
        out.append(f"## {icon} {ntype} ({len(by_type[ntype])})")
        for n in sorted(by_type[ntype], key=lambda x: x["id"]):
            tm = trust_mark.get(n["trust"], " ")
            gap_mark = " !" if n["id"] in missing_correspondence else ""
            out.append(f"  {icon} {tm} {n['id']}: {n['title']}{gap_mark}")
        out.append("")

    # Edges by type
    if edges:
        out.append("## Edges")
        edge_by_type = {}
        for e in edges:
            edge_by_type.setdefault(e["type"], []).append(e)
        for etype in sorted(edge_by_type.keys()):
            out.append(f"### {etype} ({len(edge_by_type[etype])})")
            for e in edge_by_type[etype]:
                v = " [v]" if e.get("verified") else ""
                out.append(f"  {e['from']} --[{etype}]--> {e['to']}{v}")
        out.append("")

    # Conflicts
    if conflicts:
        out.append("## Conflicts")
        for c in conflicts:
            status = "RESOLVED" if c.get("resolved") else "OPEN"
            out.append(f"  [{status}] {c.get('id', '?')}: {c.get('description', '')}")
        out.append("")

    # Missing correspondence
    if missing_correspondence:
        out.append("## Missing Correspondence (no limits_to edge)")
        for nid in sorted(missing_correspondence):
            out.append(f"  !! {nid}: {nodes[nid]['title']}")
        out.append("")

    return {
        "ascii": "\n".join(out),
        "metadata": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "conflict_count": len(conflicts),
            "missing_correspondence": len(missing_correspondence),
            "type_counts": {t: len(ns) for t, ns in by_type.items()},
        },
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
