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
    evaluate_l1_stage,
    evaluate_l3_stage,
    L1_ARTIFACT_TEMPLATES,
    L3_ARTIFACT_TEMPLATES,
    L3_ACTIVE_ARTIFACT_NAMES,
    L3_SKILL_MAP,
    L3_SUBPLANES,
    L3_ALLOWED_TRANSITIONS,
    L4_OUTCOMES,
    PHYSICS_CHECK_FIELDS,
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
        "gate_status": snapshot.gate_status,
        "mode": fm.get("mode", "explore"),
        "layer": fm.get("layer", "L1"),
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
) -> str:
    """Create a new topic directory structure with state.md and L1 scaffolds."""
    safe_slug = validate_topic_slug(topic_slug)
    base = topics_dir(topics_root)
    root = base / safe_slug
    if root.exists():
        return f"Topic {safe_slug} already exists."
    root.mkdir(parents=True)
    for sub in [
        "L0/sources", "L1/intake", "L3/candidates",
        "L4/reviews", "L4/scripts", "L4/outputs",
        "L5_writing/figures", "L5_writing/tables", "runtime",
    ]:
        (root / sub).mkdir(parents=True)
    # Write L1 artifact scaffolds
    for rel_name, (artifact_fm, artifact_body) in L1_ARTIFACT_TEMPLATES.items():
        _write_md(root / "L1" / rel_name, artifact_fm, artifact_body)
    # Runtime surfaces: topic index and log
    _write_md(root / "runtime" / "index.md", {
        "topic_slug": safe_slug, "kind": "topic_index", "created_at": _now(),
    }, (
        f"# Topic Index: {title}\n\n"
        "## Source Basis\n- L0/sources/\n- L1/source_basis.md\n\n"
        "## Research Notebook\n- L3/ subplane active artifacts\n\n"
        "## Validation\n- L4/reviews/\n\n"
        "## Reusable Results\n- global L2/ (cross-topic)\n\n"
        "## Writing\n- L3/tex/flow_notebook.tex\n- L5_writing/\n"
    ))
    _write_md(root / "runtime" / "log.md", {
        "topic_slug": safe_slug, "kind": "topic_log", "created_at": _now(),
    }, f"# Topic Log: {title}\n\n## Events\n\n- {_now()} topic bootstrapped\n")
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
        "mode": "explore",
        "layer": "L1",
        "stage": "L1",
        "posture": "read",
        "lane": lane,
        "gate_status": "blocked_missing_field",
        "created_at": _now(),
        "updated_at": _now(),
        "sources_count": 0,
        "candidates_count": 0,
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
def aitp_record_derivation(
    topics_root: str,
    topic_slug: str,
    derivation_id: str,
    kind: str,
    title: str,
    status: str = "in_progress",
    source: str = "",
    content: str = "",
) -> str:
    """Append a derivation record to L3/derivations.md."""
    root = _topic_root(topics_root, topic_slug)
    deriv_path = root / "L3" / "derivations.md"
    section = (
        f"\n## {title}\n\n"
        f"- id: {derivation_id}\n"
        f"- kind: {kind}\n"
        f"- status: {status}\n"
        f"- source: {source}\n"
        f"- recorded: {_now()}\n\n"
        f"{content}\n"
    )
    _append_section(deriv_path, section)
    return f"Recorded derivation {derivation_id}"


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
) -> dict[str, Any]:
    """Submit a candidate finding. Creates L3/candidates/<id>.md. Returns popup gate for confirmation."""
    root = _topic_root(topics_root, topic_slug)
    slug = _slugify(candidate_id)
    path = root / "L3" / "candidates" / f"{slug}.md"
    fm = {
        "candidate_id": slug,
        "title": title,
        "claim": claim,
        "status": "submitted",
        "mode": "candidate",
        "created_at": _now(),
        "updated_at": _now(),
    }
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
    """Move a validated candidate to pending_approval for human review. Returns popup gate."""
    root = _topic_root(topics_root, topic_slug)
    slug = _slugify(candidate_id)
    cand_path = root / "L3" / "candidates" / f"{slug}.md"
    if not cand_path.exists():
        return _GateResult({"message": f"Candidate {slug} not found."})
    fm, body = _parse_md(cand_path)
    current = fm.get("status", "")
    if current != "validated":
        return _GateResult({"message": f"Candidate {slug} status is '{current}', not 'validated'. Cannot request promotion."})
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
        fm["status"] = "validated"
        fm["rejection_reason"] = reason
    else:
        return f"Unknown decision '{decision}'. Use 'approve' or 'reject'."
    _write_md(cand_path, fm, body)
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
        return f"Candidate {slug} is not approved_for_promotion (status: {fm.get('status')}). Use aitp_request_promotion then aitp_resolve_promotion_gate first."

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
    if "version" not in fm:
        fm["version"] = 1

    _write_md(cand_path, fm, body)
    _write_md(l2_path, fm, body)

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
def aitp_get_skill_context(topics_root: str, topic_slug: str) -> dict[str, Any]:
    """Determine which skill to inject based on current topic status."""
    root = _topic_root(topics_root, topic_slug)
    fm, _ = _parse_md(root / "state.md")
    status = _infer_status(fm, root)
    skill_name = _SKILL_MAP.get(status, "skill-continuous")
    return {
        "topic_slug": topic_slug,
        "status": status,
        "mode": fm.get("mode", "explore"),
        "skill": skill_name,
        "message": f"Topic is in '{status}' state. Inject '{skill_name}'.",
    }


_AGENT_BEHAVIOR_REMINDER = (
    "BEHAVIORAL RULE: When you need to ask the user ANY question "
    "(clarification, direction choice, scope check), you MUST use the AskUserQuestion tool. "
    "Steps: (1) Call ToolSearch(query='select:AskUserQuestion', max_results=1). "
    "(2) Call AskUserQuestion(questions=[{...}]). "
    "NEVER type questions as plain text. NEVER list options in markdown."
)


@mcp.tool()
def aitp_get_execution_brief(topics_root: str, topic_slug: str) -> dict[str, Any]:
    """Return a stage/posture execution brief with gate status and missing requirements."""
    root = _topic_root(topics_root, topic_slug)
    fm, _ = _parse_md(root / "state.md")
    stage = str(fm.get("stage", "L1"))

    if stage == "L3":
        snapshot = evaluate_l3_stage(_parse_md, root, lane=fm.get("lane", "unspecified"))
        return {
            "topic_slug": topic_slug,
            "stage": snapshot.stage,
            "posture": snapshot.posture,
            "lane": snapshot.lane,
            "gate_status": snapshot.gate_status,
            "required_artifact_path": snapshot.required_artifact_path,
            "missing_requirements": snapshot.missing_requirements,
            "next_allowed_transition": snapshot.next_allowed_transition,
            "skill": snapshot.skill,
            "l3_subplane": snapshot.l3_subplane,
            "immediate_allowed_work": (
                [f"edit {snapshot.required_artifact_path}"]
                if snapshot.required_artifact_path
                else [f"advance from {snapshot.l3_subplane}"]
            ),
            "immediate_blocked_work": ["L4 validation", "L2 promotion"],
            "_agent_behavior_reminder": _AGENT_BEHAVIOR_REMINDER,
        }

    snapshot = evaluate_l1_stage(_parse_md, root, lane=fm.get("lane", "unspecified"))
    return {
        "topic_slug": topic_slug,
        "stage": snapshot.stage,
        "posture": snapshot.posture,
        "lane": snapshot.lane,
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


# ---------------------------------------------------------------------------
# L3 subplane tools
# ---------------------------------------------------------------------------


@mcp.tool()
def aitp_advance_to_l3(topics_root: str, topic_slug: str) -> dict[str, Any]:
    """Transition a topic from L1 (ready) to L3, starting at ideation subplane. Returns popup gate."""
    root = _topic_root(topics_root, topic_slug)
    l1_snapshot = evaluate_l1_stage(_parse_md, root)
    if l1_snapshot.gate_status != "ready":
        return _GateResult({"message": f"L1 gate is not ready (status: {l1_snapshot.gate_status}). Fill missing artifacts first."})

    state_path = root / "state.md"
    fm, body = _parse_md(state_path)
    fm["stage"] = "L3"
    fm["posture"] = "derive"
    fm["l3_subplane"] = "ideation"
    fm["updated_at"] = _now()
    _write_md(state_path, fm, body)

    # Create L3 subplane directories and scaffolds
    for subplane in L3_SUBPLANES:
        (root / "L3" / subplane).mkdir(parents=True, exist_ok=True)
        _, template_fm, template_body = L3_ARTIFACT_TEMPLATES[subplane]
        artifact_name = L3_ACTIVE_ARTIFACT_NAMES[subplane]
        artifact_path = root / "L3" / subplane / artifact_name
        if not artifact_path.exists():
            _write_md(artifact_path, template_fm, template_body)

    (root / "L3" / "tex").mkdir(parents=True, exist_ok=True)
    return _GateResult({
        "message": f"Advanced to L3 ideation. Create L3/ideation/active_idea.md to proceed.",
        "popup_gate": {
            "question": "L1 reading and framing complete. Start L3 derivation (ideation)?",
            "header": "L1->L3",
            "options": [
                {"label": "Start derivation", "description": "Proceed to L3 ideation and begin generating candidate ideas."},
                {"label": "Review L1 first", "description": "Go back and review L1 artifacts before advancing."},
            ],
        },
    })


@mcp.tool()
def aitp_advance_l3_subplane(
    topics_root: str, topic_slug: str, target_subplane: str,
) -> str:
    """Advance the L3 subplane. Only allows valid forward transitions and backedges."""
    if target_subplane not in L3_SUBPLANES:
        return f"Unknown subplane '{target_subplane}'. Valid: {L3_SUBPLANES}"

    root = _topic_root(topics_root, topic_slug)
    state_path = root / "state.md"
    fm, body = _parse_md(state_path)
    current = fm.get("l3_subplane", "ideation")

    allowed = L3_ALLOWED_TRANSITIONS.get(current, [])
    if target_subplane not in allowed:
        return (
            f"Transition from '{current}' to '{target_subplane}' is not allowed. "
            f"Allowed targets: {allowed}"
        )

    fm["l3_subplane"] = target_subplane
    fm["updated_at"] = _now()
    _write_md(state_path, fm, body)

    skill = L3_SKILL_MAP.get(target_subplane, "skill-l3-ideate")
    return f"Advanced to L3/{target_subplane}. Follow {skill}."


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
# Flow TeX
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# L4 physics adjudication
# ---------------------------------------------------------------------------


@mcp.tool()
def aitp_create_validation_contract(
    topics_root: str,
    topic_slug: str,
    candidate_id: str,
    mandatory_checks: list[str] | None = None,
    validation_route: str = "",
    failure_conditions: str = "",
) -> str:
    """Create an L4 validation contract for a candidate."""
    root = _topic_root(topics_root, topic_slug)
    slug = _slugify(candidate_id)
    checks = mandatory_checks or ["dimensional_consistency"]
    fm = {
        "artifact_kind": "l4_validation_contract",
        "stage": "L4",
        "candidate_id": slug,
        "validation_route": validation_route,
        "mandatory_checks": checks,
        "failure_conditions": failure_conditions,
        "created_at": _now(),
    }
    body = (
        f"# Validation Contract: {slug}\n\n"
        f"## Validation Route\n{validation_route}\n\n"
        f"## Mandatory Checks\n" + "\n".join(f"- {c}" for c in checks) + "\n\n"
        f"## Failure Conditions\n{failure_conditions}\n"
    )
    (root / "L4").mkdir(parents=True, exist_ok=True)
    _write_md(root / "L4" / "validation_contract.md", fm, body)
    return f"Created validation contract for {slug} with {len(checks)} checks."


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

    For toy_numeric / code_method lanes, evidence_scripts and evidence_outputs are REQUIRED.
    For formal_theory lane, they are optional (analytical checks suffice).

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
    review_path = root / "L4" / "reviews" / f"{slug}.md"

    fm = {
        "artifact_kind": "l4_review",
        "stage": "L4",
        "candidate_id": slug,
        "outcome": outcome,
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
    _append_to_topic_log(root, f"L4 review: {slug} -> {outcome}")

    result: dict[str, Any] = {"message": f"L4 review submitted for {slug}: {outcome}."}
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


@mcp.tool()
def aitp_return_to_l3_from_l4(
    topics_root: str,
    topic_slug: str,
    reason: str = "post_l4_analysis",
) -> dict[str, Any]:
    """After L4 pass, return to L3 for post-validation analysis. Mandatory step.

    L4 pass does NOT advance to L5 directly. It returns to L3 analysis so the
    agent can: (1) analyze validation findings, (2) update flow_notebook.tex,
    (3) ask the human whether to persist, continue iterating, or advance.

    reason: why returning (post_l4_analysis | post_l4_revision | post_l4_extension)
    """
    root = _topic_root(topics_root, topic_slug)
    state_path = root / "state.md"
    fm, body = _parse_md(state_path)
    current_stage = fm.get("stage", "")

    if current_stage not in ("L3", "L4"):
        return _GateResult({"message": f"Cannot return to L3: topic is at {current_stage}."})

    fm["stage"] = "L3"
    fm["posture"] = "derive"
    fm["l3_subplane"] = "analysis"
    fm["l4_return_reason"] = reason
    fm["updated_at"] = _now()
    _write_md(state_path, fm, body)
    _append_to_topic_log(root, f"returned from L4 to L3 analysis: {reason}")

    return _GateResult({
        "message": (
            f"Returned to L3 analysis from L4. You MUST:\n"
            f"1. Analyze the L4 validation results\n"
            f"2. Update flow_notebook.tex with L4 findings\n"
            f"3. Ask the human: persist/advance or continue iterating?\n"
            f"4. If iterating: plan → analyze → integrate → distill → L4 again"
        ),
    })


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
def aitp_ingest_knowledge(
    topics_root: str,
    topic_slug: str,
    source_id: str,
    source_type: str = "paper",
    title: str = "",
    arxiv_id: str = "",
    role: str = "peripheral",
    notes: str = "",
) -> str:
    """Ingest a source: register in L0, note role, append to topic log."""
    root = _topic_root(topics_root, topic_slug)
    slug = _slugify(source_id)
    src_path = root / "L0" / "sources" / f"{slug}.md"
    fm = {
        "source_id": slug,
        "type": source_type,
        "title": title or source_id,
        "arxiv_id": arxiv_id,
        "role": role,
        "fidelity": "arxiv_preprint",
        "registered": _now(),
    }
    body = f"# {title or source_id}\n\n{notes}\n" if notes else f"# {title or source_id}\n"
    _write_md(src_path, fm, body)
    _append_to_topic_log(root, f"ingest source {slug} (role: {role})")
    return f"Ingested source {slug} into L0 with role {role}."


@mcp.tool()
def aitp_query_knowledge(
    topics_root: str,
    topic_slug: str,
    question: str,
) -> dict[str, Any]:
    """Query the layered knowledge base. Returns a layer-aware answer packet."""
    root = _topic_root(topics_root, topic_slug)

    # Determine highest available layer with content
    basis_layer = "L1"
    artifact_refs = []
    regime_notes = []

    # Check L0/L1 sources
    src_dir = root / "L0" / "sources"
    if src_dir.is_dir():
        for p in src_dir.glob("*.md"):
            fm, _ = _parse_md(p)
            artifact_refs.append(f"L0/{p.name}")
            if fm.get("role") == "core":
                regime_notes.append(f"Core source: {fm.get('title', p.stem)}")

    # Check L1 artifacts
    for name in ["question_contract.md", "source_basis.md", "convention_snapshot.md"]:
        if (root / "L1" / name).exists():
            artifact_refs.append(f"L1/{name}")

    # Check L3
    state_fm, _ = _parse_md(root / "state.md")
    if str(state_fm.get("stage", "")) == "L3":
        basis_layer = "L3"
        for sp in L3_SUBPLANES:
            artifact_name = L3_ACTIVE_ARTIFACT_NAMES[sp]
            sp_path = root / "L3" / sp / artifact_name
            if sp_path.exists():
                artifact_refs.append(f"L3/{sp}/{artifact_name}")

    # Check L4
    rev_dir = root / "L4" / "reviews"
    if rev_dir.is_dir() and list(rev_dir.glob("*.md")):
        basis_layer = "L4"

    # Build answer from L1 question contract
    answer = ""
    q_fm, q_body = _parse_md(root / "L1" / "question_contract.md")
    if q_fm.get("bounded_question"):
        answer = str(q_fm["bounded_question"])
    if q_fm.get("scope_boundaries"):
        regime_notes.append(f"Scope: {q_fm['scope_boundaries']}")

    authority_warning = (
        f"This answer is grounded at {basis_layer}. "
        f"Do not treat it as stronger than {basis_layer} authority."
    )

    return {
        "question": question,
        "answer": answer or "No bounded question defined yet.",
        "basis_layer": basis_layer,
        "artifact_refs": artifact_refs,
        "regime_notes": regime_notes,
        "authority_warning": authority_warning,
    }


@mcp.tool()
def aitp_lint_knowledge(
    topics_root: str,
    topic_slug: str,
) -> list[dict[str, str]]:
    """Lint the knowledge base for structural and scientific hygiene."""
    root = _topic_root(topics_root, topic_slug)
    findings: list[dict[str, str]] = []

    # Check contradiction register for unresolved entries
    cr_path = root / "L1" / "contradiction_register.md"
    if cr_path.exists():
        cr_fm, _ = _parse_md(cr_path)
        blocking = str(cr_fm.get("blocking_contradictions", "")).strip()
        if not blocking:
            findings.append({
                "severity": "warning",
                "kind": "unresolved_contradiction",
                "artifact_path": str(cr_path),
                "message": "Contradiction register has no blocking_contradictions value.",
            })

    # Check global L2 promoted units for regime and non-claims
    l2_dir = _global_l2_path(topics_root)
    if l2_dir.is_dir():
        for l2_path in sorted(l2_dir.glob("*.md")):
            l2_fm, l2_body = _parse_md(l2_path)
            has_regime = "## Regime" in l2_body or "regime" in str(l2_fm.get("regime", ""))
            if not has_regime:
                findings.append({
                    "severity": "warning",
                    "kind": "missing_regime",
                    "artifact_path": str(l2_path),
                    "message": f"Promoted unit {l2_path.name} lacks regime specification.",
                })
            has_nonclaims = "## Non-Success" in l2_body or "non_success" in str(l2_fm.get("non_success", ""))
            if not has_nonclaims:
                findings.append({
                    "severity": "warning",
                    "kind": "missing_nonclaims",
                    "artifact_path": str(l2_path),
                    "message": f"Promoted unit {l2_path.name} lacks non-claims or failure modes.",
                })

    # Check for orphaned L2 units without provenance
    if l2_dir.is_dir():
        for l2_path in sorted(l2_dir.glob("*.md")):
            l2_fm, _ = _parse_md(l2_path)
            if not l2_fm.get("candidate_id") and not l2_fm.get("promoted_at"):
                findings.append({
                    "severity": "error",
                    "kind": "broken_provenance",
                    "artifact_path": str(l2_path),
                    "message": f"L2 unit {l2_path.name} has no provenance link.",
                })

    # Log lint run
    _append_to_topic_log(
        root,
        f"lint run: {len(findings)} findings ({sum(1 for f in findings if f['severity'] == 'error')} errors)",
    )
    return findings


@mcp.tool()
def aitp_writeback_query_result(
    topics_root: str,
    topic_slug: str,
    basis_layer: str,
    content: str,
    note_id: str,
) -> str:
    """Write back a query result to the appropriate layer. L2 requires promotion gate."""
    if basis_layer == "L2":
        return (
            "L2 writeback not allowed directly. Use aitp_submit_candidate + "
            "aitp_request_promotion + aitp_resolve_promotion_gate + aitp_promote_candidate."
        )

    root = _topic_root(topics_root, topic_slug)
    slug = _slugify(note_id)

    if basis_layer == "L1":
        note_path = root / "L1" / f"{slug}.md"
        _write_md(note_path, {
            "artifact_kind": "l1_note", "stage": "L1", "created_at": _now(),
        }, f"# Query Writeback: {slug}\n\n{content}\n")
        _append_to_topic_log(root, f"writeback L1 note {slug}")
        return f"Written L1/{slug}.md"

    if basis_layer == "L3":
        note_path = root / "L3" / f"{slug}.md"
        _write_md(note_path, {
            "artifact_kind": "l3_note", "stage": "L3", "created_at": _now(),
        }, f"# Query Writeback: {slug}\n\n{content}\n")
        _append_to_topic_log(root, f"writeback L3 note {slug}")
        return f"Written L3/{slug}.md"

    if basis_layer == "L4":
        note_path = root / "L4" / "reviews" / f"{slug}.md"
        _write_md(note_path, {
            "artifact_kind": "l4_note", "stage": "L4", "created_at": _now(),
        }, f"# Query Writeback: {slug}\n\n{content}\n")
        _append_to_topic_log(root, f"writeback L4 note {slug}")
        return f"Written L4/reviews/{slug}.md"

    return f"Unknown basis_layer '{basis_layer}'. Use L1, L3, or L4."


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
    """Transition from L4 to L5 writing. Requires flow_notebook.tex. Returns popup gate."""
    root = _topic_root(topics_root, topic_slug)
    tex_path = root / "L3" / "tex" / "flow_notebook.tex"
    if not tex_path.exists():
        return _GateResult({
            "message": (
                f"Blocked: flow_notebook.tex not found at {tex_path}. "
                f"The agent must generate and compile the flow notebook during L3 distillation "
                f"before advancing to L5."
            ),
        })

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
        "message": f"Advanced to L5 writing. Fill provenance artifacts before drafting.",
        "popup_gate": {
            "question": "Validation passed. Start the L5 writing phase?",
            "header": "L4->L5",
            "options": [
                {"label": "Start writing", "description": "Proceed to L5 writing. Fill provenance files and draft the paper."},
                {"label": "Review first", "description": "Review the flow notebook and validation results before writing."},
            ],
        },
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
