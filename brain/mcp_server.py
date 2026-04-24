"""AITP Brain MCP Server v2 — Minimal skill-driven research protocol.

Provides ~12 tools for the agent to read/write topic state.
All storage is Markdown with YAML frontmatter. No JSON, no JSONL.

Dependencies: fastmcp, pyyaml
Install: pip install fastmcp pyyaml
"""

from __future__ import annotations

import os
import re
import subprocess
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
    evaluate_l4_stage,
    evaluate_l5_stage,
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

from brain.sympy_verify import (
    check_dimensions,
    check_algebra,
    check_limit,
    validate_derivation_step,
    validate_derivation_chain,
    INFERENCE_RULES,
    INFERENCE_RULE_DESCRIPTIONS,
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

_LANE_ALIASES = {
    "code_and_materials": "code_method",
}


def _normalize_lane(lane: str) -> str:
    """Normalize lane name, resolving aliases like code_and_materials -> code_method."""
    return _LANE_ALIASES.get(lane, lane)


_SKILL_MAP = {
    "new": "skill-explore",
    "sources_registered": "skill-intake",
    "intake_done": "skill-derive",
    "candidate_ready": "skill-validate",
    "validated": "skill-promote",
    "promoted": "skill-write",
}


def _load_domain_manifest(topic_root_path: Path) -> dict[str, Any] | None:
    """Load domain-manifest.md from the topic's contracts/ directory.

    Returns the parsed frontmatter dict, or None if no manifest exists.
    Accepts manifests with either domain_id (full domain skill) or
    repo_ref (code binding only).
    """
    manifest_path = topic_root_path / "contracts" / "domain-manifest.md"
    if not manifest_path.exists():
        return None
    try:
        fm, _ = _parse_md(manifest_path)
        if "domain_id" in fm or "repo_ref" in fm:
            return fm
    except Exception:
        pass
    return None


def _domain_invariants(manifest: dict[str, Any]) -> list[dict[str, str]]:
    """Extract invariant definitions from a domain manifest."""
    return manifest.get("invariants", [])


def _domain_operations(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract operation definitions from a domain manifest."""
    return manifest.get("operations", [])

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
    manifest = _load_domain_manifest(root)
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
        "domain_skill": manifest.get("domain_id", "") if manifest else "",
        "repo_ref": manifest.get("repo_ref", {}) if manifest else {},
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
    lane = _normalize_lane(lane)
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
    # Domain-specific directories for code_method lane (PROJECT_STRUCTURE_CONVENTION)
    if lane == "code_method":
        for sub in [
            "docs/sections", "docs/figures",
            "code/patches",
            "computation/smoke_test", "computation/benchmark",
            "contracts",
            "archive/conversations", "archive/specs",
            "build/cmake",
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
def aitp_load_domain_manifest(
    topics_root: str,
    topic_slug: str,
) -> dict[str, Any]:
    """Load and return the domain manifest for a topic, if one exists.

    Reads contracts/domain-manifest.md. Returns the manifest frontmatter with
    domain_id, target_codes, operations, invariants, repo_ref, etc., or an
    empty dict if no domain skill is registered for this topic.
    """
    root = _topic_root(topics_root, topic_slug)
    manifest = _load_domain_manifest(root)
    if manifest is None:
        return {"message": "No domain manifest found. Place contracts/domain-manifest.md to register a domain skill."}
    return manifest


@mcp.tool()
def aitp_bind_repo(
    topics_root: str,
    topic_slug: str,
    repo_path: str,
    branch_prefix: str = "feat",
    base_branch: str = "",
) -> dict[str, Any]:
    """Bind a topic to a local git repo for code development.

    Creates a feature branch in the repo and writes a repo_ref into
    contracts/domain-manifest.json. After binding, the agent reads/writes
    code directly in the repo rather than copying files into the topic.

    Args:
        topics_root: Root directory for topics.
        topic_slug: Topic identifier.
        repo_path: Absolute path to the local git repository.
        branch_prefix: Prefix for the feature branch (default "feat").
            Use "fix" for bug fixes, "experiment" for exploratory work.
        base_branch: Branch to create from. Defaults to current HEAD.
    """
    import json as _json

    root = _topic_root(topics_root, topic_slug)
    repo = Path(repo_path)
    if not repo.is_dir():
        return {"message": f"Repo path does not exist: {repo}"}
    if not (repo / ".git").exists():
        return {"message": f"Not a git repository: {repo}"}

    branch_name = f"{branch_prefix}/{topic_slug}"

    try:
        if base_branch:
            subprocess.run(
                ["git", "checkout", "-b", branch_name, base_branch],
                cwd=str(repo), capture_output=True, text=True, check=True,
            )
        else:
            current = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(repo), capture_output=True, text=True, check=True,
            ).stdout.strip()
            if current == branch_name:
                pass  # already on the right branch
            else:
                subprocess.run(
                    ["git", "checkout", "-b", branch_name],
                    cwd=str(repo), capture_output=True, text=True, check=True,
                )
    except subprocess.CalledProcessError as e:
        return {"message": f"Git error: {e.stderr.strip()}"}

    base_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo), capture_output=True, text=True, check=True,
    ).stdout.strip()[:12]

    contracts_dir = root / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = contracts_dir / "domain-manifest.md"

    if manifest_path.exists():
        fm, body = _parse_md(manifest_path)
    else:
        fm, body = {}, "# Domain Manifest\n"

    fm["repo_ref"] = {
        "local_path": str(repo),
        "branch": branch_name,
        "base_commit": base_commit,
    }

    _write_md(manifest_path, fm, body)

    _append_to_topic_log(
        root,
        f"bound repo: {repo} branch={branch_name} base={base_commit}",
    )

    return {
        "message": f"Bound topic {topic_slug} to {repo} on branch {branch_name}",
        "repo_path": str(repo),
        "branch": branch_name,
        "base_commit": base_commit,
    }


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
    _auto_refresh_flow_notebook(root, state_fm)
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
# L3 idea branching — multiple approaches explored in parallel
# ---------------------------------------------------------------------------

_IDEA_STATUSES = {"active", "failed", "succeeded", "abandoned", "superseded"}


@mcp.tool()
def aitp_submit_idea(
    topics_root: str,
    topic_slug: str,
    idea_slug: str,
    title: str,
    approach: str,
    derivation: str = "",
    outcome: str = "active",
    lessons_learned: str = "",
    inspired_by: list[str] | None = None,
    supersedes: list[str] | None = None,
) -> dict[str, Any]:
    """Record a new derivation approach or idea attempt in L3.

    Research is branching — you may have multiple ideas for how to derive
    a result. Each idea gets its own record. Failed ideas are kept visible
    because their lessons may help other approaches succeed.

    Args:
        idea_slug: Short identifier, e.g. 'algebraic-method', 'path-integral-attempt'
        title: Human-readable name
        approach: Description of the approach/method
        derivation: Key derivation steps (optional, can be filled progressively)
        outcome: active | failed | succeeded | abandoned | superseded
        lessons_learned: What was learned, even from failure
        inspired_by: List of idea slugs that inspired this one
        supersedes: List of idea slugs this one replaces

    Returns:
        Dict with confirmation and popup gate.
    """
    root = _topic_root(topics_root, topic_slug)
    slug = _slugify(idea_slug)
    ideas_dir = root / "L3" / "ideas"
    ideas_dir.mkdir(parents=True, exist_ok=True)
    idea_path = ideas_dir / f"{slug}.md"

    is_update = idea_path.exists()
    if is_update:
        existing_fm, _ = _parse_md(idea_path)

    fm = {
        "idea_slug": slug,
        "title": title,
        "status": outcome if outcome in _IDEA_STATUSES else "active",
        "approach": approach,
        "created_at": _now() if not is_update else existing_fm.get("created_at", _now()),
        "updated_at": _now(),
    }
    if inspired_by:
        fm["inspired_by"] = inspired_by
    if supersedes:
        fm["supersedes"] = supersedes
    if lessons_learned:
        fm["lessons_learned"] = lessons_learned

    body = (
        f"# {title}\n\n"
        f"## Approach\n{approach}\n\n"
        f"## Derivation\n{derivation or '(To be filled as work progresses)'}\n\n"
        f"## Outcome\n{outcome}\n\n"
        f"## Lessons Learned\n{lessons_learned or '(To be filled)'}\n"
    )

    _write_md(idea_path, fm, body)

    # Append to cross-idea log
    log_path = ideas_dir / "_log.md"
    if not log_path.exists():
        _write_md(log_path, {
            "kind": "ideas_log",
            "topic_slug": topic_slug,
            "created_at": _now(),
        }, "# Ideas Log\n\n## Timeline\n")
    _, log_body = _parse_md(log_path)
    action = "updated" if is_update else "created"
    log_body += f"\n- {_now()}: {action} idea `{slug}` — **{title}** (status: {outcome})"
    _write_md(log_path, {"kind": "ideas_log", "updated_at": _now()}, log_body)

    # If superseding other ideas, update them
    if supersedes:
        for sup_slug in supersedes:
            sup_path = ideas_dir / f"{_slugify(sup_slug)}.md"
            if sup_path.exists():
                sup_fm, sup_body = _parse_md(sup_path)
                sup_fm["status"] = "superseded"
                sup_fm["superseded_by"] = slug
                sup_fm["updated_at"] = _now()
                _write_md(sup_path, sup_fm, sup_body)

    # Auto-refresh flow notebook to include ideas section
    state_fm, _ = _parse_md(root / "state.md")
    _auto_refresh_flow_notebook(root, state_fm)

    msg = f"Idea '{slug}' {action} (status: {outcome})."
    if outcome == "failed":
        msg += " Failed approaches are valuable — their lessons will be preserved."

    return _GateResult({
        "message": msg,
        "popup_gate": {
            "question": f"Idea '{title}': continue exploring or switch approach?",
            "header": "Idea",
            "options": [
                {"label": "Continue this idea", "description": "Keep working on this approach. Fill derivation steps progressively."},
                {"label": "Create another idea", "description": "Record a different approach. Multiple ideas can be explored in parallel."},
                {"label": "Mark failed", "description": "This approach didn't work. Record lessons and keep visible for other ideas."},
            ],
        },
        "idea_slug": slug,
        "is_update": is_update,
    })


@mcp.tool()
def aitp_list_ideas(
    topics_root: str,
    topic_slug: str,
    status_filter: str = "",
) -> dict[str, Any]:
    """List all L3 ideas with their status and key findings.

    Args:
        status_filter: optional filter — active, failed, succeeded, abandoned, superseded
    """
    root = _topic_root(topics_root, topic_slug)
    ideas_dir = root / "L3" / "ideas"
    if not ideas_dir.is_dir():
        return {"ideas": [], "count": 0, "message": "No ideas recorded yet."}

    ideas = []
    for ip in sorted(ideas_dir.glob("*.md")):
        if ip.stem.startswith("_"):
            continue  # Skip _log.md
        fm, body = _parse_md(ip)
        if status_filter and fm.get("status") != status_filter:
            continue
        ideas.append({
            "slug": fm.get("idea_slug", ip.stem),
            "title": fm.get("title", ip.stem),
            "status": fm.get("status", "active"),
            "approach": (fm.get("approach", "") or "")[:150],
            "lessons_learned": (fm.get("lessons_learned", "") or "")[:200],
            "superseded_by": fm.get("superseded_by", ""),
            "inspired_by": fm.get("inspired_by", []),
            "supersedes": fm.get("supersedes", []),
            "created_at": fm.get("created_at", ""),
            "updated_at": fm.get("updated_at", ""),
        })

    # Sort: active first, then succeeded, then failed, then others
    def _sort_key(i):
        order = {"active": 0, "succeeded": 1, "failed": 2, "superseded": 3, "abandoned": 4}
        return (order.get(i["status"], 5), i["slug"])

    ideas.sort(key=_sort_key)

    return {
        "ideas": ideas,
        "count": len(ideas),
        "by_status": {
            s: sum(1 for i in ideas if i["status"] == s)
            for s in _IDEA_STATUSES
        },
        "log_path": str(ideas_dir / "_log.md"),
    }


@mcp.tool()
def aitp_promote_idea_to_candidate(
    topics_root: str,
    topic_slug: str,
    idea_slug: str,
    candidate_title: str = "",
    candidate_claim: str = "",
) -> dict[str, Any]:
    """Promote a successful L3 idea to a full candidate for L4 validation.

    Copies the idea's approach and derivation into a new candidate file.
    The idea is marked as 'succeeded' and linked to the candidate.

    Args:
        idea_slug: The idea to promote
        candidate_title: Title for the candidate (defaults to idea title)
        candidate_claim: The claim statement (extracted from derivation if empty)
    """
    root = _topic_root(topics_root, topic_slug)
    slug = _slugify(idea_slug)
    ideas_dir = root / "L3" / "ideas"
    idea_path = ideas_dir / f"{slug}.md"

    if not idea_path.exists():
        return {"message": f"Idea '{slug}' not found. Use aitp_submit_idea first."}

    fm, body = _parse_md(idea_path)
    if fm.get("status") not in ("active", "succeeded"):
        return {
            "message": (
                f"Idea '{slug}' has status '{fm.get('status')}', "
                f"not 'active' or 'succeeded'. Only viable ideas can be promoted."
            ),
        }

    # Create candidate from idea
    title = candidate_title or fm.get("title", slug)
    claim = candidate_claim or f"Derived via approach: {fm.get('approach', '')}"

    # Extract derivation from idea body
    derivation = ""
    if "## Derivation" in body:
        derivation = body.split("## Derivation", 1)[1].strip()
        if "## Outcome" in derivation:
            derivation = derivation.split("## Outcome")[0].strip()

    # Use aitp_submit_candidate's logic inline
    cand_dir = root / "L3" / "candidates"
    cand_dir.mkdir(parents=True, exist_ok=True)
    cand_path = cand_dir / f"{slug}.md"

    state_fm, _ = _parse_md(root / "state.md")
    l3_mode = state_fm.get("l3_mode", "research")

    cand_fm = {
        "candidate_id": slug,
        "title": title,
        "claim": claim,
        "status": "submitted",
        "mode": "candidate",
        "candidate_type": "research_claim",
        "l3_mode": l3_mode,
        "source_idea": slug,
        "depends_on": [],
        "created_at": _now(),
        "updated_at": _now(),
    }
    cand_body = (
        f"# {title}\n\n"
        f"## Claim\n{claim}\n\n"
        f"## Evidence\nDerived via idea `{slug}`:\n\n{derivation[:2000]}\n\n"
        f"## Assumptions\nExtracted from idea approach.\n\n"
        f"## Validation Criteria\nTo be validated via L4 review.\n"
    )
    _write_md(cand_path, cand_fm, cand_body)

    # Update idea
    fm["status"] = "succeeded"
    fm["promoted_to_candidate"] = slug
    fm["promoted_at"] = _now()
    fm["updated_at"] = _now()
    _write_md(idea_path, fm, body)

    _auto_refresh_flow_notebook(root, state_fm)

    return _GateResult({
        "message": f"Idea '{slug}' promoted to candidate '{slug}'. L4 validation can now begin.",
        "idea_slug": slug,
        "candidate_id": slug,
        "popup_gate": {
            "question": f"Idea '{title}' promoted. Validate via L4 review now?",
            "header": "Promote Idea",
            "options": [
                {"label": "Validate now", "description": "Submit this candidate for L4 adversarial review."},
                {"label": "Promote other ideas", "description": "Check other ideas first before validating."},
            ],
        },
    })


# ---------------------------------------------------------------------------
# Promotion gate lifecycle
# ---------------------------------------------------------------------------

_PROMOTION_TRANSITIONS = {
    "submitted": "validated",
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
        except OSError as e:
            _append_to_topic_log(
                root,
                f"promoted {slug} to L2 but graph node creation failed: {e}",
            )
            return f"Promoted {slug} to global L2 (v{fm['version']}). WARNING: graph node not created — {e}"

    _append_to_topic_log(root, f"promoted {slug} to global L2 (v{fm['version']})")
    state_fm, _ = _parse_md(root / "state.md")
    _auto_refresh_flow_notebook(root, state_fm)
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

    if stage == "L4":
        snapshot = evaluate_l4_stage(_parse_md, root, lane=fm.get("lane", "unspecified"))
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
                else ["submit L4 review for unreviewed candidates"]
            ),
            "immediate_blocked_work": ["L5 writing", "L2 promotion (until validated)"],
            "_agent_behavior_reminder": _AGENT_BEHAVIOR_REMINDER,
        }

    if stage == "L5":
        snapshot = evaluate_l5_stage(_parse_md, root, lane=fm.get("lane", "unspecified"))
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
                else ["draft paper sections from L5_writing scaffolds"]
            ),
            "immediate_blocked_work": ["L3 derivation (use retreat_to_l3 if gaps found)"],
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

    _auto_refresh_flow_notebook(root, fm)

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
    devils_advocate: str = "",
    verification_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    r"""Submit an L4 review with one of the six validation outcomes. Returns popup gate.

    ADVERSARIAL REVIEW (v3): You are NOT certifying your own work. You are
    attempting to falsify the claim. A "pass" means the claim survived your
    best attempts to break it.

    EVIDENCE REQUIREMENTS BY LANE:
    - toy_numeric / code_method: evidence_scripts + evidence_outputs REQUIRED for pass.
      Every data point must have a data_provenance entry.
    - formal_theory: outcome="pass" REQUIRES check_results with at minimum:
        dimensional_consistency, symmetry_compatibility, limiting_case_check,
        correspondence_check — OR verification_evidence from SymPy verification tools.
      Each check must describe what was verified and the outcome.

    devils_advocate: REQUIRED for "pass". State at least one specific way the
      claim could still be wrong despite passing all checks. This is the
      adversarial collaborator's duty — no claim is beyond doubt.

    verification_evidence: Optional dict with results from SymPy verification
      tools (aitp_verify_dimensions, aitp_verify_algebra, etc.).
      Format: {"tool": "aitp_verify_dimensions", "result": {...}}

    data_provenance: list of dicts, each with keys:
      - data_point: what was measured/computed
      - script: path to the script that produced it
      - executed_at: ISO timestamp of execution
      - method: brief description of how it was computed

    Example pass review:
      aitp_submit_l4_review(td, "qho", "energy-spectrum", "pass",
        check_results={
          "dimensional_consistency": "pass: [H] = [\hbar\omega] = energy",
          "symmetry_compatibility": "pass: H commutes with parity",
          "limiting_case_check": "pass: classical HO recovered as n→∞",
          "correspondence_check": "pass: matches known result E_n=(n+1/2)\hbar\omega",
        },
        devils_advocate="The derivation assumes the potential is exactly harmonic. "
                        "Anharmonic corrections would shift the spectrum.",
        verification_evidence={"tool": "aitp_verify_dimensions", "result": {"pass": True}},
      )
    """
    if outcome not in L4_OUTCOMES:
        return {"message": f"Invalid outcome '{outcome}'. Valid: {L4_OUTCOMES}"}

    root = _topic_root(topics_root, topic_slug)
    slug = _slugify(candidate_id)

    # Lane-aware evidence requirement
    state_fm, _ = _parse_md(root / "state.md")
    lane = state_fm.get("lane", "")

    # ---- Adversarial evidence enforcement ----

    if outcome == "pass":
        # Check devil's advocate
        if not devils_advocate.strip():
            return {
                "message": (
                    "BLOCKED: Adversarial review requires devils_advocate for pass outcomes. "
                    "State at least one specific way the claim could still be wrong — "
                    "what assumptions could break? What regime boundaries are untested? "
                    "What measurement would falsify this claim?"
                ),
            }

        # toy_numeric / code_method: must have evidence scripts + outputs
        if lane in ("toy_numeric", "code_method"):
            if not evidence_scripts or not evidence_outputs:
                return {
                    "message": (
                        f"BLOCKED: Lane '{lane}' requires evidence_scripts and evidence_outputs "
                        f"for L4 pass reviews. Execute validation scripts, record outputs, "
                        f"and re-submit."
                    ),
                }

        # formal_theory: must have check_results OR verification_evidence
        if lane == "formal_theory":
            has_check_results = bool(check_results and any(
                k in check_results for k in PHYSICS_CHECK_FIELDS
            ))
            has_verification = bool(verification_evidence)
            if not has_check_results and not has_verification:
                return {
                    "message": (
                        f"BLOCKED: Lane 'formal_theory' requires evidence for L4 pass. "
                        f"Provide either:\n"
                        f"1. check_results with at least one physics check from "
                        f"{sorted(PHYSICS_CHECK_FIELDS)}, OR\n"
                        f"2. verification_evidence from SymPy verification tools "
                        f"(aitp_verify_dimensions, aitp_verify_algebra, aitp_verify_derivation_step).\n"
                        f"Python cannot certify physics — you must provide the evidence."
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
    if devils_advocate:
        fm["devils_advocate"] = devils_advocate
    if verification_evidence:
        fm["verification_evidence"] = verification_evidence

    body = (
        f"# Review: {slug}\n\n"
        f"## Outcome\n{outcome}\n\n"
        f"## Notes\n{notes}\n\n"
    )
    if devils_advocate:
        body += f"## Devil's Advocate\n{devils_advocate}\n\n"
    if verification_evidence:
        body += (
            "## SymPy Verification Evidence\n"
            f"Tool: {verification_evidence.get('tool', 'unknown')}\n\n"
            f"```\n{verification_evidence.get('result', {})}\n```\n\n"
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
            # Reset status if previously validated — new review invalidates old result
            if cand_fm.get("status") in ("validated", "partial_validated"):
                cand_fm["status"] = "submitted"
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
    _auto_refresh_flow_notebook(root, state_fm)
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
def aitp_verify_dimensions(
    expression: str,
    variable_dimensions: dict,  # JSON object mapping variable → dimension name
) -> dict[str, Any]:
    """Verify dimensional consistency of a physics equation using SymPy.

    Checks that every term on the RHS has the same physical dimension as the LHS.
    This is a pure symbolic check — no LLM judgment involved.

    Args:
        expression: A physics equation, e.g. "E = m * c**2"
        variable_dimensions: Map of each variable to its dimension name.
            Supported dimensions: mass, length, time, charge, temperature,
            energy, momentum, velocity, acceleration, force, action, frequency,
            angular_momentum, pressure, power, density, electric_field,
            magnetic_field, electric_potential, wavefunction, cross_section,
            entropy, heat_capacity, dimensionless, and others.

    Example:
        aitp_verify_dimensions("E = m * c**2", {"E": "energy", "m": "mass", "c": "velocity"})
        → pass=True, rhs_dimensions=["mass * length^2 / time^2"]

        aitp_verify_dimensions("E = m * c", {"E": "energy", "m": "mass", "c": "velocity"})
        → pass=False, rhs_dimensions=["mass * length / time"]
    """
    return check_dimensions(expression, variable_dimensions)


@mcp.tool()
def aitp_verify_algebra(
    lhs: str,
    rhs: str,
    assumptions: dict | None = None,
) -> dict[str, Any]:
    """Verify an algebraic identity using SymPy symbolic simplification.

    Checks whether lhs - rhs simplifies to zero. Use for commutators,
    operator identities, and analytic simplifications.

    Args:
        lhs: Left-hand side in SymPy-compatible syntax, e.g. "a*a_dag - a_dag*a"
        rhs: Right-hand side, e.g. "1"
        assumptions: Optional dict mapping symbols to definitions.
            e.g., {"N": "a_dag * a"}

    Example:
        aitp_verify_algebra("(x + y)**2", "x**2 + 2*x*y + y**2")
        → pass=True

        aitp_verify_algebra("exp(I*pi)", "-1")
        → pass=True
    """
    return check_algebra(lhs, rhs, assumptions)


@mcp.tool()
def aitp_verify_limit(
    expression: str,
    limit_var: str,
    limit_value: str,
    expected: str,
    assumptions: dict | None = None,
) -> dict[str, Any]:
    r"""Verify that an expression reduces to the expected form in a given limit.

    Essential for correspondence-principle checks: does the quantum result
    reduce to the classical result when \hbar → 0? Does the relativistic
    expression reduce to Newtonian when v/c → 0?

    Args:
        expression: The expression to check, e.g. "(n + 1/2) * hbar * omega"
        limit_var: Variable approaching the limit, e.g. "n", "hbar", "v"
        limit_value: Limit value, "0", "oo" (infinity), or an expression
        expected: Expected limiting form, e.g. "n * hbar * omega"
        assumptions: Optional symbol definitions

    Example:
        aitp_verify_limit(
            "sqrt(1 - v**2/c**2)", "v", "0", "1"
        )
        → pass=True (Lorentz factor → 1 in non-relativistic limit)

        aitp_verify_limit(
            "(n + 1/2)*hbar*omega", "n", "oo",
            "n*hbar*omega"
        )
        → pass=True (quantum → classical equipartition)
    """
    return check_limit(expression, limit_var, limit_value, expected, assumptions)


@mcp.tool()
def aitp_list_inference_rules() -> dict[str, Any]:
    """List all available physics inference rules for derivation step verification.

    Each rule has a generic SymPy-based validator. Use these when recording
    derivation steps in the L3 analysis subplane.
    """
    return {
        "rules": [
            {"name": r, "description": INFERENCE_RULE_DESCRIPTIONS.get(r, "")}
            for r in INFERENCE_RULES
        ],
        "usage": (
            "Record each derivation step with: rule, input_expr, output_expr, argument. "
            "Then verify with aitp_verify_derivation_step."
        ),
    }


@mcp.tool()
def aitp_verify_derivation_step(
    rule: str,
    input_expr: str,
    output_expr: str,
    argument: str = "",
    assumptions: dict | None = None,
) -> dict[str, Any]:
    """Verify a single derivation step using the specified inference rule.

    Each rule has a generic SymPy-based validator that checks whether the
    output correctly follows from the input using this rule — independent
    of the specific equation content.

    Args:
        rule: One of the inference rules from aitp_list_inference_rules()
        input_expr: The expression before the operation (SymPy-compatible)
        output_expr: The expression after the operation (SymPy-compatible)
        argument: Rule-specific argument:
            - multiply_both_sides / divide_both_sides: the factor
            - substitute: "old=new" or "old->new"
            - differentiate / integrate: the variable
            - take_limit: "var->value" (e.g. "n->oo", "hbar->0")
            - series_expand: "var,order" or "var,point,order"
            - apply_identity: the identity expression or "A=B"
        assumptions: Optional dict of symbol definitions

    Example:
        aitp_verify_derivation_step("substitute", "x**2 + y", "x**2 + 2*x + 1",
                                     "y=2*x+1")
        → pass=True

        aitp_verify_derivation_step("differentiate", "x**2", "2*x", "x")
        → pass=True (d(x^2)/dx = 2x correct)

        aitp_verify_derivation_step("differentiate", "x**2", "3*x", "x")
        → pass=False (d(x^2)/dx ≠ 3x)
    """
    return validate_derivation_step(rule, input_expr, output_expr, argument, assumptions)


@mcp.tool()
def aitp_verify_derivation_chain(
    steps: list[dict],
    assumptions: dict | None = None,
) -> dict[str, Any]:
    """Verify an entire derivation chain step by step.

    Each step is a dict with keys: rule, input_expr, output_expr, argument (optional).
    The first step may omit input_expr (treated as initial expression).

    Returns per-step results with overall pass/fail and a summary.

    Example:
        aitp_verify_derivation_chain([
            {"rule": "multiply_both_sides", "input_expr": "E = m*c**2",
             "output_expr": "E/c**2 = m", "argument": "1/c**2"},
            {"rule": "substitute", "output_expr": "m = E/c**2",
             "argument": "m=E/c**2"},
        ])
        → pass=True (both steps verified)

    Use this at the end of L3 analysis to validate the full derivation.
    """
    return validate_derivation_chain(steps, assumptions)


@mcp.tool()
def aitp_switch_lane(
    topics_root: str,
    topic_slug: str,
    new_lane: str,
    reason: str = "",
) -> dict[str, Any]:
    """Switch the research lane for an active topic. Records old/new lane and reason.

    new_lane: formal_theory | toy_numeric | code_method | code_and_materials | unspecified
    Valid transitions: any lane to any other lane. Common patterns:
      - formal_theory → toy_numeric: analytical derivation hit a dead end
      - toy_numeric → code_method: need production-quality computation
      - code_method → formal_theory: numerical results suggest a clean analytical form
    Note: code_and_materials is an alias for code_method and is normalized automatically.
    """
    resolved = _normalize_lane(new_lane)
    valid_lanes = {"formal_theory", "toy_numeric", "code_method", "unspecified"}
    if resolved not in valid_lanes:
        return {"message": f"Invalid lane '{new_lane}'. Valid: {sorted(valid_lanes)}"}

    root = _topic_root(topics_root, topic_slug)
    state_path = root / "state.md"
    fm, body = _parse_md(state_path)

    old_lane = fm.get("lane", "unspecified")
    if old_lane == resolved:
        return {"message": f"Topic is already on lane '{new_lane}'. No change needed."}

    fm["lane"] = resolved
    fm["previous_lane"] = old_lane
    fm["lane_switch_reason"] = reason
    fm["lane_switched_at"] = _now()
    fm["updated_at"] = _now()
    _write_md(state_path, fm, body)
    _append_to_topic_log(root, f"switched lane: {old_lane} -> {resolved} ({reason})")

    return {
        "message": f"Switched lane from '{old_lane}' to '{resolved}'.",
        "old_lane": old_lane,
        "new_lane": resolved,
        "requested_lane": new_lane,
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


@mcp.tool()
def aitp_query_l2_index(
    topics_root: str,
    domain_filter: str = "",
) -> dict[str, Any]:
    """Query the L2 knowledge base index — progressive disclosure entry point.

    Returns a domain taxonomy tree with per-domain summaries and node counts.
    Use this FIRST when starting a new topic to discover what L2 already knows.
    Then drill down with aitp_query_l2_graph for specific nodes.

    If domain_filter is given, returns only that domain with full node listings.
    Otherwise returns all domains with summary-level detail.
    """
    global_l2 = _global_l2_path(topics_root)
    nodes_dir = global_l2 / "graph" / "nodes"
    if not nodes_dir.is_dir():
        return {"domains": {}, "total_nodes": 0, "message": "L2 graph is empty — no validated knowledge yet."}

    # Scan all nodes and group by domain
    domains: dict[str, dict[str, Any]] = {}
    for node_path in sorted(nodes_dir.glob("*.md")):
        fm, body = _parse_md(node_path)
        domain = str(fm.get("domain", "")).strip()
        if not domain:
            domain = "uncategorized"

        if domain not in domains:
            domains[domain] = {
                "node_count": 0,
                "by_type": {},
                "nodes": [],
            }

        node_info = {
            "node_id": fm.get("node_id", node_path.stem),
            "title": fm.get("title", node_path.stem),
            "type": fm.get("type", "concept"),
            "trust_basis": fm.get("trust_basis", "source_grounded"),
            "regime_of_validity": fm.get("regime_of_validity", ""),
            "mathematical_expression": fm.get("mathematical_expression", ""),
            "physical_meaning": (fm.get("physical_meaning", "") or "")[:200],
        }

        domains[domain]["node_count"] += 1
        ntype = node_info["type"]
        domains[domain]["by_type"][ntype] = domains[domain]["by_type"].get(ntype, 0) + 1
        domains[domain]["nodes"].append(node_info)

    # Build progressive-disclosure response
    domain_summaries: dict[str, Any] = {}
    for domain_name, data in domains.items():
        summary = {
            "node_count": data["node_count"],
            "by_type": data["by_type"],
            "key_results": [
                n["title"] for n in data["nodes"]
                if n["type"] in ("result", "theorem")
                and n["trust_basis"] in ("validated", "independently_verified")
            ][:5],
            "established_concepts": [
                n["title"] for n in data["nodes"]
                if n["type"] == "concept"
            ][:5],
            "open_questions": [
                n["title"] for n in data["nodes"]
                if n["type"] == "open_question"
            ],
        }

        if domain_filter and domain_name != domain_filter:
            continue

        domain_summaries[domain_name] = summary

    if domain_filter:
        return {
            "domain": domain_filter,
            "summary": domain_summaries.get(domain_filter, {}),
            "nodes": domains.get(domain_filter, {}).get("nodes", []),
            "total_nodes_in_domain": domains.get(domain_filter, {}).get("node_count", 0),
        }

    return {
        "domains": domain_summaries,
        "domain_list": sorted(domains.keys()),
        "total_domains": len(domains),
        "total_nodes": sum(d["node_count"] for d in domains.values()),
        "hint": "Use aitp_query_l2_graph to drill into specific nodes.",
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
    domain: str = "",
) -> str:
    """Create a node in the L2 knowledge graph.

    node_type: concept | theorem | technique | derivation_chain | result | approximation | open_question | regime_boundary
    domain: e.g. 'electronic-structure', 'quantum-many-body', 'qft', 'condensed-matter'
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
        "domain": domain,
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
    domain: str | None = None,
) -> str:
    """Update fields of an existing L2 graph node.
    Set domain to categorize within the L2 index taxonomy."""
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
    if domain is not None:
        fm["domain"] = domain
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

    # Verify both nodes exist — refuse to create dangling edges
    from_slug = _slugify(from_node)
    to_slug = _slugify(to_node)
    from_path = global_l2 / "graph" / "nodes" / f"{from_slug}.md"
    to_path = global_l2 / "graph" / "nodes" / f"{to_slug}.md"
    missing = []
    if not from_path.exists():
        missing.append(f"from_node '{from_slug}'")
    if not to_path.exists():
        missing.append(f"to_node '{to_slug}'")
    if missing:
        return (
            f"Cannot create edge: node(s) not found in L2 graph: {', '.join(missing)}. "
            f"Create the missing node(s) with aitp_create_l2_node first."
        )

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
    return f"Created L2 edge {slug} ({from_slug} --[{edge_type}]--> {to_slug})"


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
def _build_flow_notebook_content(
    root: Path, title: str, question: str, lane: str
) -> str:
    """Build flow_notebook.tex content from all L3 subplane artifacts.

    Reads every subplane active artifact, every candidate, and every L4 review,
    then consolidates into a structured LaTeX document.
    """
    def _read_section(path: Path) -> str:
        if not path.exists():
            return ""
        _, body = _parse_md(path)
        return body

    def _esc(text: str) -> str:
        """Minimal LaTeX escaping."""
        return (text
                .replace("\\", "\\textbackslash ")
                .replace("&", "\\&")
                .replace("%", "\\%")
                .replace("$", "\\$")
                .replace("#", "\\#")
                .replace("_", "\\_")
                .replace("{", "\\{")
                .replace("}", "\\}")
                .replace("^", "\\^{}")
                .replace("~", "\\textasciitilde "))

    def _inline_math_safe(text: str) -> str:
        """Keep $...$ and $$...$$ math blocks intact, escape the rest."""
        # Simple approach: split on $, escape odd segments
        parts = text.split("$")
        result = []
        for i, part in enumerate(parts):
            if i % 2 == 0:
                result.append(_esc(part))
            else:
                result.append(f"${part}$")
        return "".join(result)

    # Determine L3 mode
    fm_state, _ = _parse_md(root / "state.md")
    l3_mode = fm_state.get("l3_mode", "research")

    # Collect subplane artifacts
    subplanes = []
    if l3_mode == "research":
        from brain.state_model import L3_SUBPLANES, L3_ACTIVE_ARTIFACT_NAMES
        sp_names = L3_SUBPLANES
        art_names = L3_ACTIVE_ARTIFACT_NAMES
    else:
        from brain.state_model import STUDY_L3_SUBPLANES, STUDY_L3_ACTIVE_ARTIFACT_NAMES
        sp_names = STUDY_L3_SUBPLANES
        art_names = STUDY_L3_ACTIVE_ARTIFACT_NAMES

    for sp in sp_names:
        art_name = art_names.get(sp, f"active_{sp}.md")
        path = root / "L3" / sp / art_name
        if path.exists():
            fm, body = _parse_md(path)
            subplanes.append({
                "name": sp,
                "frontmatter": fm,
                "body": body,
            })

    # Collect candidates
    cand_dir = root / "L3" / "candidates"
    candidates = []
    if cand_dir.is_dir():
        for cp in sorted(cand_dir.glob("*.md")):
            fm, body = _parse_md(cp)
            if fm.get("status") in ("validated", "approved_for_promotion", "promoted", ""):
                candidates.append({"slug": cp.stem, "fm": fm, "body": body})

    # Collect L4 reviews
    review_dir = root / "L4" / "reviews"
    reviews = []
    if review_dir.is_dir():
        for rp in sorted(review_dir.glob("*.md")):
            fm, body = _parse_md(rp)
            reviews.append({"slug": rp.stem, "fm": fm, "body": body})

    # Build LaTeX document
    tex = []
    tex.append(r"\documentclass[11pt,a4paper]{article}")
    tex.append(r"\usepackage[utf8]{inputenc}")
    tex.append(r"\usepackage[T1]{fontenc}")
    tex.append(r"\usepackage{amsmath,amssymb,amsfonts}")
    tex.append(r"\usepackage{physics}")
    tex.append(r"\usepackage{hyperref}")
    tex.append(r"\usepackage[margin=2.5cm]{geometry}")
    tex.append(r"\usepackage{enumitem}")
    tex.append("")
    tex.append(r"\title{Flow Notebook: " + _esc(title) + "}")
    tex.append(r"\author{AITP Protocol v3}")
    tex.append(r"\date{\today}")
    tex.append("")
    tex.append(r"\begin{document}")
    tex.append(r"\maketitle")
    tex.append("")

    # ---- 1. Abstract / Synthesis ----
    tex.append(r"\section{Research Summary}")
    tex.append("")
    synopsis_written = False
    for sp in subplanes:
        if sp["name"] in ("distillation", "synthesis"):
            text = _inline_math_safe(sp["body"].strip())
            if text:
                tex.append(r"\subsection*{Synthesis}")
                tex.append("")
                for line in text.split("\n"):
                    if line.startswith("#"):
                        tex.append(r"\subsection*{" + _esc(line.lstrip("# ")) + "}")
                    elif line.strip():
                        tex.append(_esc(line))
                    tex.append("")
                synopsis_written = True

    if not synopsis_written and candidates:
        tex.append(r"\subsection*{Key Claims}")
        tex.append(r"\begin{itemize}")
        for c in candidates[:5]:
            claim = c["fm"].get("claim", "")[:300]
            tex.append(r"\item " + _inline_math_safe(claim))
        tex.append(r"\end{itemize}")

    # ---- 2. Question & Scope ----
    tex.append(r"\section{Research Question}")
    tex.append("")
    qc_path = root / "L1" / "question_contract.md"
    if qc_path.exists():
        fm_qc, body_qc = _parse_md(qc_path)
        bounded = fm_qc.get("bounded_question", question)
        scope = fm_qc.get("scope_boundaries", "")
        tex.append(r"\textbf{Bounded Question:} " + _inline_math_safe(bounded))
        tex.append("")
        if scope:
            tex.append(r"\textbf{Scope:} " + _esc(scope))
            tex.append("")

    # ---- 3. Source Basis ----
    tex.append(r"\section{Source Basis}")
    tex.append("")
    sb_path = root / "L1" / "source_basis.md"
    if sb_path.exists():
        _, body_sb = _parse_md(sb_path)
        tex.append(_inline_math_safe(body_sb[:2000]))
        tex.append("")

    # ---- 4. Conventions ----
    cs_path = root / "L1" / "convention_snapshot.md"
    if cs_path.exists():
        tex.append(r"\section{Conventions \& Notation}")
        tex.append("")
        _, body_cs = _parse_md(cs_path)
        tex.append(_inline_math_safe(body_cs[:1000]))
        tex.append("")

    # ---- 5. Derivation ----
    tex.append(r"\section{Derivation}")
    tex.append("")
    derivation_sps = [sp for sp in subplanes if sp["name"] in ("analysis", "step_derive", "result_integration")]
    if derivation_sps:
        for sp in derivation_sps:
            tex.append(r"\subsection*{" + sp["name"].replace("_", " ").title() + "}")
            tex.append("")
            text = _inline_math_safe(sp["body"].strip())
            for line in text.split("\n"):
                if line.startswith("## "):
                    tex.append(r"\subsubsection*{" + _esc(line[3:]) + "}")
                elif line.strip():
                    tex.append(_esc(line))
                tex.append("")
    else:
        tex.append(r"(No structured derivation recorded. See subplane artifacts.)")
        tex.append("")

    # ---- 5.5 Ideas Explored ----
    ideas_dir = root / "L3" / "ideas"
    if ideas_dir.is_dir():
        ideas_list = sorted(
            [ip for ip in ideas_dir.glob("*.md") if not ip.stem.startswith("_")],
            key=lambda p: p.stat().st_mtime, reverse=True,
        )
        if ideas_list:
            tex.append(r"\section{Ideas Explored}")
            tex.append(r"\label{sec:ideas}")
            tex.append("")
            tex.append(
                r"Multiple derivation approaches were explored. "
                r"Failed approaches are preserved — their lessons informed "
                r"successful routes. Cross-references link related ideas."
            )
            tex.append("")
            for ip in ideas_list:
                fm_i, body_i = _parse_md(ip)
                status = fm_i.get("status", "active")
                status_cmd = {
                    "succeeded": r"\textbf{[SUCCEEDED — promoted to candidate]}",
                    "failed": r"\textbf{[FAILED — lessons preserved]}",
                    "active": r"\textbf{[IN PROGRESS]}",
                    "abandoned": r"\textbf{[ABANDONED]}",
                    "superseded": r"\textbf{[SUPERSEDED]}",
                }.get(status, "")

                tex.append(r"\subsection*{" + _esc(fm_i.get("title", ip.stem)) + "}")
                tex.append(r"\textbf{Status:} " + status_cmd)
                tex.append("")

                # Approach
                approach = (fm_i.get("approach", "") or "").strip()
                if approach:
                    tex.append(r"\textbf{Approach:}")
                    tex.append("")
                    tex.append(_inline_math_safe(approach))
                    tex.append("")

                # Derivation — extract from body
                if body_i:
                    deriv_text = body_i
                    # Skip sections we handle separately
                    for skip_hdr in ["## Approach", "## Outcome", "## Lessons Learned"]:
                        if skip_hdr in deriv_text:
                            deriv_text = deriv_text.split(skip_hdr, 1)[0]
                    deriv_text = deriv_text.strip()
                    # Remove leading "# Title" line
                    if deriv_text.startswith("# "):
                        deriv_text = deriv_text.split("\n", 1)[1] if "\n" in deriv_text else ""
                    deriv_text = deriv_text.strip()
                    if deriv_text:
                        tex.append(r"\textbf{Derivation:}")
                        tex.append("")
                        tex.append(_inline_math_safe(deriv_text[:2000]))
                        tex.append("")

                # Lessons learned
                lessons = (fm_i.get("lessons_learned", "") or "").strip()
                if lessons:
                    tex.append(r"\textbf{Lessons Learned:}")
                    tex.append("")
                    tex.append(_inline_math_safe(lessons))
                    tex.append("")

                # Cross-references
                refs = []
                if fm_i.get("inspired_by"):
                    refs.append("Inspired by: " + ", ".join(fm_i["inspired_by"]))
                if fm_i.get("supersedes"):
                    refs.append("Supersedes: " + ", ".join(fm_i["supersedes"]))
                if fm_i.get("superseded_by"):
                    refs.append(r"\textbf{Superseded by:} " + fm_i["superseded_by"])
                if fm_i.get("promoted_to_candidate"):
                    refs.append(r"\textbf{Promoted to candidate:} " + fm_i["promoted_to_candidate"])
                if refs:
                    tex.append(r"\textbf{Connections:}")
                    tex.append("")
                    for ref in refs:
                        tex.append(r"\quad • " + _esc(ref))
                    tex.append("")

                # Timestamps
                created = fm_i.get("created_at", "")
                updated = fm_i.get("updated_at", "")
                if created or updated:
                    tex.append(r"\textit{Created: " + _esc(created[:19]) + "}")
                    if updated and updated != created:
                        tex.append(r" \textit{— Updated: " + _esc(updated[:19]) + "}")
                    tex.append("")

                tex.append(r"\hrulefill")
                tex.append("")

    # ---- 6. Results ----
    tex.append(r"\section{Results}")
    tex.append("")
    if candidates:
        for i, c in enumerate(candidates, 1):
            title = c["fm"].get("title", c["slug"])
            claim = c["fm"].get("claim", "")
            ctype = c["fm"].get("candidate_type", "research_claim")
            regime = c["fm"].get("regime_of_validity", "")
            tex.append(r"\subsection*{Result " + str(i) + r": " + _esc(title) + "}")
            tex.append("")
            tex.append(r"\textbf{Type:} " + _esc(ctype))
            tex.append("")
            tex.append(r"\textbf{Claim:} " + _inline_math_safe(claim))
            tex.append("")
            if regime:
                tex.append(r"\textbf{Regime of Validity:} " + _esc(regime))
                tex.append("")
    else:
        tex.append(r"(No candidates submitted.)")
        tex.append("")

    # ---- 7. Gap Audit / Limitations ----
    tex.append(r"\section{Assumptions, Gaps \& Limitations}")
    tex.append("")
    gap_sps = [sp for sp in subplanes if sp["name"] in ("gap_audit", "planning", "ideation")]
    gap_written = False
    for sp in gap_sps:
        text = _inline_math_safe(sp["body"].strip())
        if text:
            tex.append(r"\subsection*{" + sp["name"].replace("_", " ").title() + "}")
            tex.append("")
            for line in text.split("\n"):
                if line.strip():
                    tex.append(_esc(line))
                    tex.append("")
            gap_written = True
    if not gap_written:
        tex.append(r"(No formal gap audit recorded.)")
        tex.append("")

    # ---- 8. Validation ----
    tex.append(r"\section{Validation}")
    tex.append("")
    if reviews:
        for r in reviews:
            outcome = r["fm"].get("outcome", "unknown")
            notes = r["fm"].get("notes", "")
            tex.append(r"\subsection*{" + _esc(r["slug"]) + r" — " + _esc(outcome) + "}")
            tex.append("")
            if notes:
                tex.append(_inline_math_safe(notes[:500]))
                tex.append("")
    else:
        tex.append(r"(No L4 reviews submitted.)")
        tex.append("")

    # ---- 9. Open Questions ----
    tex.append(r"\section{Open Questions \& Future Work}")
    tex.append("")
    oq_candidates = [c for c in candidates if c["fm"].get("candidate_type") == "open_question"]
    if oq_candidates:
        tex.append(r"\begin{itemize}")
        for c in oq_candidates:
            tex.append(r"\item " + _inline_math_safe(c["fm"].get("claim", c["slug"])[:300]))
        tex.append(r"\end{itemize}")
    else:
        tex.append(r"(No open questions formally recorded.)")
        tex.append("")

    tex.append("")
    tex.append(r"\end{document}")

    return "\n".join(tex)


def _auto_refresh_flow_notebook(root: Path, fm: dict) -> None:
    """Silently regenerate flow_notebook.tex. Never blocks — errors are ignored."""
    try:
        title = str(fm.get("title", ""))
        question = ""  # extracted from body if needed
        lane = str(fm.get("lane", "unspecified"))
        tex_content = _build_flow_notebook_content(root, title, question, lane)
        tex_dir = root / "L3" / "tex"
        tex_dir.mkdir(parents=True, exist_ok=True)
        _write_md(tex_dir / "flow_notebook.tex", {
            "artifact_kind": "l3_flow_notebook",
            "stage": "L3",
            "generated_at": _now(),
            "topic_slug": fm.get("topic_slug", ""),
        }, tex_content)
    except Exception:
        pass  # Never block normal operations


@mcp.tool()
def aitp_generate_flow_notebook(
    topics_root: str,
    topic_slug: str,
) -> dict[str, Any]:
    """Generate flow_notebook.tex from all L3 subplane artifacts, candidates, and reviews.

    Reads every subplane active artifact, every candidate, and every L4 review,
    then consolidates into a structured LaTeX document at L3/tex/flow_notebook.tex.
    This is the readable research record — a physicist can understand the full
    derivation, results, and validation from this single document.

    Call this before advance_to_l5, or at any point during L3/L4 to snapshot progress.
    """
    root = _topic_root(topics_root, topic_slug)
    fm, _ = _parse_md(root / "state.md")

    title = str(fm.get("title", topic_slug))
    question = ""  # extracted from body if available
    lane = str(fm.get("lane", "unspecified"))

    tex_content = _build_flow_notebook_content(root, title, question, lane)

    # Write to L3/tex/
    tex_dir = root / "L3" / "tex"
    tex_dir.mkdir(parents=True, exist_ok=True)
    tex_path = tex_dir / "flow_notebook.tex"
    _write_md(tex_path, {
        "artifact_kind": "l3_flow_notebook",
        "stage": "L3",
        "generated_at": _now(),
        "topic_slug": topic_slug,
    }, tex_content)

    _append_to_topic_log(root, "generated flow_notebook.tex")

    return {
        "message": f"flow_notebook.tex generated at L3/tex/flow_notebook.tex",
        "path": str(tex_path),
        "size_bytes": len(tex_content),
        "sections_included": [
            "Research Summary",
            "Research Question",
            "Source Basis",
            "Conventions & Notation",
            "Derivation",
            "Results",
            "Assumptions, Gaps & Limitations",
            "Validation",
            "Open Questions & Future Work",
        ],
    }


def aitp_advance_to_l5(topics_root: str, topic_slug: str) -> dict[str, Any]:
    """Transition from L4 to L5 writing. Returns popup gate.

    Auto-generates flow_notebook.tex before advancing if it doesn't exist."""
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
