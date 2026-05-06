"""AITP Brain MCP Server v2  --  Minimal skill-driven research protocol.

Provides ~55 tools for the agent to read/write topic state.
All storage is Markdown with YAML frontmatter. No JSON, no JSONL.

Dependencies: fastmcp, pyyaml
Install: pip install fastmcp pyyaml

DISPATCH STATUS (C6+H4 migration — 7/11 tools dispatched):
  Dispatched (MCP→CLI):
    - aitp_register_source       → source add        (with extra-metadata enrichment)
    - aitp_create_l2_edge        → l2 edge-create    (full dispatch)
    - aitp_submit_candidate      → candidate submit  (core dispatch + _GateResult popup)
    - aitp_switch_l3_activity    → switch-activity   (normal case; L4→L3 bg job MCP-only)
    - aitp_write_section_intake  → source extract    (core write; TOC update MCP-only)
    - aitp_request_promotion     → promote           (preflight dispatch + _GateResult popup)
    - aitp_gate_override         → gate override     (direct dispatch)

  MCP-native (global L2 direct write — no CLI equivalent by design):
    - aitp_bootstrap_topic       — creates global L2 surfaces
    - aitp_promote_candidate     — writes to global L2 graph
    - aitp_create_l2_node        — writes to global L2/nodes/
    - aitp_merge_subgraph_delta  — bulk merge to global L2
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
    resolve_domain_prerequisites,
    L0_ARTIFACT_TEMPLATES,
    L1_ARTIFACT_TEMPLATES,
    L3_ACTIVITIES,
    L3_ACTIVITY_TEMPLATES,
    L3_ACTIVITY_ARTIFACT_NAMES,
    L3_ACTIVITY_SKILL_MAP,
    L4_OUTCOMES,
    PHYSICS_CHECK_FIELDS,
    L2_NODE_TYPES,
    L2_EDGE_TYPES,
    L2_TOWER_TEMPLATE,
    TRUST_EVOLUTION,
    semantic_score,
    normalize_latex,
    tokenize_for_search,
    _generate_physics_next_action,
    _check_question_semantic_validity,
    DOMAIN_TAXONOMY,
    VALID_DOMAINS,
    L2_QUERY_HIDDEN_FIELDS,
    DIAGRAM_TEMPLATE,
    JUSTIFICATION_TYPES,
    STEP_TEMPLATE,
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

from brain.cli.decorators import require_stage, with_preflight

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
# Helpers  --  Markdown + YAML frontmatter I/O
# ---------------------------------------------------------------------------

_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)

_AGENT_BEHAVIOR_REMINDER = (
    "Python is storage+search only. You are the physicist. "
    "Assess your own work before advancing  --  the skill file asks Socratic questions, "
    "not compliance checklists. Evidence before claims. "
    "Derivations before conclusions. Limits before generalizations. "
    "Check compute_target before ANY code, SymPy, Lean, or numerical work "
    " --  route heavy computation to the declared target (local/fisher/lean-remote). "
    "If domain_prerequisites is non-empty, load those skills BEFORE the stage skill. "
"If l4_background_status is 'submitted' or 'running', a validation job is executing "
"on HPC — you can switch to L3 for ideation/planning while waiting, then call "
"aitp_l4_check_results when the job completes."
)


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _get_protocol_version() -> str:
    """Read protocol version from package.json, fall back to '0.0.0'."""
    try:
        pkg_path = Path(__file__).resolve().parent.parent / "package.json"
        if pkg_path.exists():
            import json
            return json.loads(pkg_path.read_text(encoding="utf-8")).get("version", "0.0.0")
    except Exception:
        pass
    return "0.0.0"


def _topic_root(topics_root: str, topic_slug: str) -> Path:
    from brain.cli.state import resolve_topic_root as _resolve
    return _resolve(topics_root, topic_slug)


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
    "promoted": "skill-promote",
}


def _load_domain_manifest(topic_root_path: Path) -> dict[str, Any] | None:
    """Load domain-manifest from the topic's contracts/ directory.

    Returns the parsed frontmatter dict, or None if no manifest exists.
    Supports both .md (frontmatter) and .json formats.
    Accepts manifests with either domain_id (full domain skill) or
    repo_ref (code binding only).
    """
    # Try .md format first
    manifest_path = topic_root_path / "contracts" / "domain-manifest.md"
    if manifest_path.exists():
        try:
            fm, _ = _parse_md(manifest_path)
            if "domain_id" in fm or "repo_ref" in fm:
                return fm
        except Exception:
            pass
    # Try .json format (multi-domain convention)
    for jp in sorted((topic_root_path / "contracts").glob("domain-manifest.*.json")) if (topic_root_path / "contracts").is_dir() else []:
        try:
            import json
            data = json.loads(jp.read_text(encoding="utf-8"))
            if isinstance(data, dict) and ("domain_id" in data or "repo_ref" in data):
                return data
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
    root = topics_dir(topics_root)
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
            elif stage == "L4":
                snap = evaluate_l4_stage(_parse_md, topic_dir, lane=lane)
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
            "protocol_version": str(fm.get("protocol_version", "0.0.0")),
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

    # Protocol version compatibility check
    server_version = _get_protocol_version()
    version_warnings: list[dict[str, Any]] = []
    for entry in topics_list:
        pv = entry.get("protocol_version", "0.0.0")
        if pv and pv != "0.0.0" and pv != server_version:
            version_warnings.append({
                "topic_slug": entry["topic_slug"],
                "topic_protocol_version": pv,
                "server_version": server_version,
                "action": (
                    "Topic was created with a different AITP version. "
                    "State is forward-compatible but verify gate status is correct."
                ),
            })

    return {
        "summary": summary,
        "topics": topics_list,
        "topics_root": str(root),
        "checked_at": _now(),
        "server_version": server_version,
        "version_warnings": version_warnings,
    }


@mcp.tool()
def aitp_get_status(topics_root: str, topic_slug: str) -> dict[str, Any]:
    """Read topic state and return current status, stage, posture, and gate."""
    root = _topic_root(topics_root, topic_slug)
    fm, body = _parse_md(root / "state.md")
    status = _infer_status(fm, root)
    stage = str(fm.get("stage", "L1")).strip() or "L1"
    lane = str(fm.get("lane", "unspecified")).strip() or "unspecified"

    if stage == "L3":
        snapshot = evaluate_l3_stage(_parse_md, root, lane=lane)
    elif stage == "L4":
        snapshot = evaluate_l4_stage(_parse_md, root, lane=lane)
    elif stage == "L0":
        snapshot = evaluate_l0_stage(_parse_md, root, lane=lane)
    else:
        snapshot = evaluate_l1_stage(_parse_md, root, lane=lane)
    src_dir = root / "L0" / "sources"
    cand_dir = root / "L3" / "candidates"
    global_l2 = _global_l2_path(topics_root)
    domain_prereqs = resolve_domain_prerequisites(root, topic_slug)
    return {
        "topic_slug": topic_slug,
        "status": status,
        "stage": fm.get("stage", snapshot.stage),
        "posture": fm.get("posture", snapshot.posture),
        "lane": fm.get("lane", snapshot.lane),
        "research_intensity": str(fm.get("research_intensity", "standard")).strip() or "standard",
        "interaction_level": str(fm.get("interaction_level", "collaborative")).strip() or "collaborative",
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
        "l2_count": (
            (len(list(global_l2.glob("*.md"))) if global_l2.is_dir() else 0)
            + (len(list((global_l2 / "entries").glob("*.md"))) - 1 if (global_l2 / "entries").is_dir() else 0)
            + (len(list((global_l2 / "graph" / "nodes").glob("*.md"))) if (global_l2 / "graph" / "nodes").is_dir() else 0)
        ),
        "domain_prerequisites": domain_prereqs,
        "repo_ref": {},
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
@require_stage
# MCP-native: global L2 direct write — creates global L2 surfaces, no CLI equivalent
def aitp_bootstrap_topic(
    topics_root: str,
    topic_slug: str,
    title: str,
    question: str,
    lane: str = "unspecified",
    mode: str = "explore",
    research_intensity: str = "standard",
    interaction_level: str = "collaborative",
) -> str:
    """Create a new topic directory structure with state.md and L0/L1 scaffolds.

    research_intensity: "quick" (minimal L1 — just question_contract),
      "standard" (question + source_basis + toc_map),
      "full" (all 6 L1 artifacts + full L4 review).
    interaction_level: "collaborative" (full popup gates),
      "direct" (popup only for gate transitions),
      "silent" (no popups except promotion rejection).
    """
    lane = _normalize_lane(lane)
    if research_intensity not in ("quick", "standard", "full"):
        research_intensity = "standard"
    if interaction_level not in ("collaborative", "direct", "silent"):
        interaction_level = "collaborative"
    safe_slug = validate_topic_slug(topic_slug)
    base = topics_dir(topics_root)
    root = base / safe_slug
    if root.exists():
        return f"Topic {safe_slug} already exists."
    root.mkdir(parents=True)
    for sub in [
        "L0/sources", "L1/intake", "L3/candidates",
        "L4/reviews", "L4/scripts", "L4/outputs", "L4/outputs/figures",
        "runtime",
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
    # Write L1 artifact scaffolds — always write all for forward compat,
    # but intensity controls which are checked by the gate.
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
        "## Writing\n- flow_notebook.tex (topic root)\n"
    ))
    _write_md(root / "runtime" / "log.md", {
        "topic_slug": safe_slug, "kind": "topic_log", "created_at": _now(),
    }, f"# Topic Log: {title}\n\n## Events\n\n- {_now()} topic bootstrapped\n")
    _write_md(root / "runtime" / "sessions.md", {
        "kind": "session_log", "topic_slug": safe_slug, "created_at": _now(),
    }, f"# Session Log: {title}\n\n## Sessions\n")
    # Global L2 surfaces — full v5 faceted layout
    global_l2 = _ensure_l2_graph_dirs(str(base))
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
        "research_intensity": research_intensity,
        "interaction_level": interaction_level,
        "l3_activity": "ideate",
        "protocol_version": _get_protocol_version(),
    }
    # Note: `layer` and `l3_mode` are v3 legacy fields NOT written at bootstrap.
    # `layer` is set by retreat/advance ops when needed.
    # `l3_mode` is set by aitp_switch_l3_mode for research vs study distinction.
    # `l3_activity` starts at "ideate" — the default L3 subplane activity.
    body = f"# {title}\n\n## Research Question\n{question}\n"
    _write_md(root / "state.md", fm, body)
    return (
        f"Bootstrapped topic '{safe_slug}' at {root}\n"
        f"  research_intensity: {research_intensity}\n"
        f"  interaction_level: {interaction_level}\n"
        f"  lane: {lane}"
    )


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
@require_stage
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

    # Auto-detect domain_id from slug patterns if not already set
    if not fm.get("domain_id"):
        slug_lower = topic_slug.lower()
        if any(p in slug_lower for p in ("librpa", "crpa", "scrpa", "qsgw", "gw-topology")):
            fm["domain_id"] = "oh-my-librpa"

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


# dispatch: aitp source add
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
    physical_system: str = "",
    method_category: str = "",
    regime: str = "",
    source_role: str = "direct_dependency",
    epistemic_tier: str = "",
    source_url: str = "",
    source_path: str = "",
    clone_repo: str = "",
    repo_branch: str = "",
    repo_commit: str = "",
) -> str:
    """Register a source in L0. Creates per-source directory.

    All sources are peer-level in L0/sources/<source_id>/:
      source.md   — pure metadata
      notes.md    — initial reading notes template
      original/   — preserved original files (papers, code, user derivations)

    Source types:
      paper:       arXiv tarball, user PDF/md/tex → original/
      code:        .cpp/.h/.py files → original/
      repo:        git clone entire repository into source dir
      derivation:  user's own derivation PDF/md → original/

    Args:
        source_url: Download URL (arxiv e-print, raw file)
        source_path: Local file/directory to copy into original/
        clone_repo: Git URL — clones entire repo into source directory
        repo_branch: Branch name for clone
        repo_commit: Commit hash to record
    """
    from brain.cli._dispatch_helpers import dispatch
    from brain.cli.commands.source import cmd_source_add

    result = dispatch(cmd_source_add,
        topic=topic_slug, id=source_id, title=title or source_id,
        type=source_type, role=source_role, notes=notes,
        url=source_url, path=source_path,
        repo=clone_repo, branch=repo_branch, commit=repo_commit,
        success_msg=f"Registered source {_slugify(source_id)}")

    # Enrich with extra metadata fields
    if arxiv_id or fidelity != "arxiv_preprint" or physical_system or method_category or regime or epistemic_tier:
        root = _topic_root(topics_root, topic_slug)
        slug = _slugify(source_id)
        # New directory structure: L0/sources/<slug>/source.md
        source_dir = root / "L0" / "sources" / slug
        path = source_dir / "source.md"
        # Fall back to legacy flat file
        if not path.exists():
            path = root / "L0" / "sources" / f"{slug}.md"
        if path.exists():
            fm, body = _parse_md(path)
            if arxiv_id: fm["arxiv_id"] = arxiv_id
            if fidelity != "arxiv_preprint": fm["fidelity"] = fidelity
            if physical_system: fm["physical_system"] = physical_system
            if method_category: fm["method_category"] = method_category
            if regime: fm["regime"] = regime
            if epistemic_tier: fm["epistemic_tier"] = epistemic_tier
            if repo_commit: fm["commit"] = repo_commit
            _write_md(path, fm, body)

    return result


@mcp.tool()
def aitp_list_sources(topics_root: str, topic_slug: str) -> list[dict[str, Any]]:
    """List all registered sources for a topic."""
    root = _topic_root(topics_root, topic_slug)
    src_dir = root / "L0" / "sources"
    if not src_dir.is_dir():
        return []
    results = []
    seen: set[str] = set()
    # New directory structure: L0/sources/<slug>/source.md
    for d in sorted(src_dir.iterdir()):
        if d.is_dir():
            sf = d / "source.md"
            if sf.exists():
                fm, _ = _parse_md(sf)
                sid = fm.get("source_id", d.name)
                seen.add(sid)
                results.append({
                    "source_id": sid,
                    "title": fm.get("title", ""),
                    "type": fm.get("type", ""),
                    "arxiv_id": fm.get("arxiv_id", ""),
                    "original_files": fm.get("original_files", []),
                })
    # Legacy flat files: L0/sources/<slug>.md
    for path in sorted(src_dir.glob("*.md")):
        fm, _ = _parse_md(path)
        sid = fm.get("source_id", path.stem)
        if sid not in seen:
            seen.add(sid)
            results.append({
                "source_id": sid,
                "title": fm.get("title", ""),
                "type": fm.get("type", ""),
                "arxiv_id": fm.get("arxiv_id", ""),
                "original_files": [],
            })
    return results


@mcp.tool()
@require_stage
def aitp_parse_source_toc(
    topics_root: str,
    topic_slug: str,
    source_id: str,
    toc_entries: list[dict[str, str]],
    toc_confidence: str = "medium",
) -> str:
    """Parse and record a source's table of contents into the L1 source_toc_map.

    Call this after accessing a source (via arxiv-latex-mcp, web reader, etc.)
    to mechanically register every section/chapter. Each entry should correspond
    to the smallest identifiable unit in the source's structure.

    toc_entries: list of dicts, each with:
      - "section_id": slug for the section (e.g. "sec2-1")
      - "title": section title as in the source
      - "depth": heading depth as string, e.g. "1" for chapter, "2" for subsection
      - "page_range": optional, e.g. "3-5"
    toc_confidence: high (from machine-parsed TOC, e.g. arxiv-latex-mcp sections),
      medium (AI-extracted from well-structured PDF), low (AI-guessed from
      unstructured text). Defaults to "medium".
    """
    root = _topic_root(topics_root, topic_slug)
    toc_path = root / "L1" / "source_toc_map.md"

    if not toc_path.exists():
        return "L1/source_toc_map.md not found. Bootstrap the topic first."

    fm, body = _parse_md(toc_path)

    # Build section table entries
    section_lines = []
    for entry in toc_entries:
        sid = entry.get("section_id", "unknown")
        title = entry.get("title", "Untitled")
        depth = entry.get("depth", "1")
        page_range = entry.get("page_range", "")
        indent = "  " * (int(depth) - 1) if depth.isdigit() else ""
        page_info = f" (pp. {page_range})" if page_range else ""
        section_lines.append(
            f"{indent}- [{sid}] {title}{page_info}  --  status: pending"
        )

    # Append to ## Per-Source TOC
    confidence_note = f" (TOC confidence: {toc_confidence})"
    source_block = (
        f"\n### {source_id}{confidence_note}\n\n"
        + "\n".join(section_lines)
        + "\n"
    )

    if "## Per-Source TOC" in body:
        body = body.replace("## Per-Source TOC\n", "## Per-Source TOC\n" + source_block + "\n", 1)
    else:
        body += source_block

    # Update frontmatter counters
    new_section_count = len(toc_entries)
    total = int(fm.get("total_sections", 0)) + new_section_count
    fm["total_sections"] = total

    # Update sources_with_toc
    existing_sources = str(fm.get("sources_with_toc", ""))
    if existing_sources:
        fm["sources_with_toc"] = f"{existing_sources}, {source_id}"
    else:
        fm["sources_with_toc"] = source_id

    # Reset coverage_status since new sections are pending
    fm["coverage_status"] = ""

    _write_md(toc_path, fm, body)
    _append_to_topic_log(root, f"parsed TOC for source {source_id}: {new_section_count} sections")
    return f"Recorded {new_section_count} sections for {source_id}. Total sections: {total}. Mark sections as extracted/deferred using aitp_update_section_status."


@mcp.tool()
def aitp_update_section_status(
    topics_root: str,
    topic_slug: str,
    source_id: str,
    section_id: str,
    new_status: str,
    extraction_note: str = "",
) -> str:
    """Update the reading status of a specific section in the source_toc_map.

    new_status: pending | skimming | extracted | deferred
    extraction_note: brief note about what was extracted, or reason for deferral.
    """
    valid_statuses = {"pending", "skimming", "extracted", "deferred"}
    if new_status not in valid_statuses:
        return f"Invalid status '{new_status}'. Valid: {sorted(valid_statuses)}"

    root = _topic_root(topics_root, topic_slug)
    toc_path = root / "L1" / "source_toc_map.md"
    if not toc_path.exists():
        return "L1/source_toc_map.md not found."

    fm, body = _parse_md(toc_path)

    # Find and replace the section's status line
    old_pattern = f"[{section_id}]"
    lines = body.split("\n")
    found = False
    import re as _re_section
    for i, line in enumerate(lines):
        if old_pattern in line and source_id in body[:body.index(line) + len(line)]:
            # Replace status
            lines[i] = _re_section.sub(r" --  status: \w+", f" --  status: {new_status}", line)
            if extraction_note:
                lines[i] += f"\n  > {extraction_note}"
            # Link to intake note if it exists
            intake_note_path = f"L1/intake/{_slugify(source_id)}/{_slugify(section_id)}.md"
            if (root / intake_note_path).exists() and "→ intake:" not in lines[i]:
                lines[i] = lines[i].rstrip() + f"  → intake: {intake_note_path}"
            found = True
            break

    # Also check under the correct ### source_id block
    if not found:
        in_source_block = False
        for i, line in enumerate(lines):
            if line.strip().startswith(f"### {source_id}"):
                in_source_block = True
                continue
            if line.startswith("### ") and in_source_block:
                break
            if in_source_block and old_pattern in line:
                import re as _re_section2
                lines[i] = _re_section2.sub(r" --  status: \w+", f" --  status: {new_status}", line)
                if extraction_note:
                    lines[i] += f"\n  > {extraction_note}"
                # Link to intake note if it exists
                intake_note_path = f"L1/intake/{_slugify(source_id)}/{_slugify(section_id)}.md"
                if (root / intake_note_path).exists() and "→ intake:" not in lines[i]:
                    lines[i] = lines[i].rstrip() + f"  → intake: {intake_note_path}"
                found = True
                break

    if not found:
        return f"Section [{section_id}] not found under source {source_id}."

    body = "\n".join(lines)

    # Recompute coverage
    total = int(fm.get("total_sections", 0))
    done = body.count(" --  status: extracted")
    deferred = body.count(" --  status: deferred")
    pending = total - done - deferred

    if pending <= 0:
        if deferred > 0:
            fm["coverage_status"] = "partial_with_deferrals"
            # Ensure ## Deferred Sections is populated
            if "## Deferred Sections" in body and body.count("## Deferred Sections") > 0:
                deferred_lines = [l for l in lines if " --  status: deferred" in l]
                deferred_summary = "\n".join(f"- {l.strip()}" for l in deferred_lines)
                body = body.replace(
                    "## Deferred Sections\n",
                    f"## Deferred Sections\n{deferred_summary}\n\n",
                    1,
                )
        else:
            fm["coverage_status"] = "complete"
    else:
        fm["coverage_status"] = ""

    _write_md(toc_path, fm, body)
    _append_to_topic_log(
        root,
        f"section {source_id}/{section_id} -> {new_status} "
        f"(extracted: {done}/{total}, deferred: {deferred})",
    )
    return (
        f"Updated {source_id}/{section_id} to {new_status}. "
        f"Coverage: {done} extracted, {deferred} deferred, {pending} pending out of {total}."
    )


@mcp.tool()
@require_stage
def aitp_batch_extract_section(
    topics_root: str,
    topic_slug: str,
    source_id: str,
    section_id: str,
    section_title: str = "",
    summary: str = "",
    key_concepts: str = "",
    completeness_confidence: str = "medium",
    concepts: list[dict[str, str]] | None = None,
    edges: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Extract a section in one call: intake note + L2 nodes + L2 edges + status update.

    Replaces 5 separate MCP calls for the common "finish reading a section" workflow.

    concepts: list of {concept_id, title, domain, physical_meaning, expression}
        Each entry creates an L2 concept node. source_ref is auto-set to
        {source_id}/{section_id}.
    edges: list of {from_node, to_node, edge_type}
        Each entry creates an L2 edge. from_node should be one of the
        concept_ids just created, or an existing L2 node.
    """
    results = {
        "intake": "", "nodes_created": 0, "edges_created": 0,
        "status": "", "suggestions": [],
    }

    # 1. Write intake note
    results["intake"] = aitp_write_section_intake(
        topics_root=topics_root, topic_slug=topic_slug,
        source_id=source_id, section_id=section_id,
        section_title=section_title, summary=summary,
        key_concepts=key_concepts,
        completeness_confidence=completeness_confidence,
    )

    # 2. Create L2 nodes for discovered concepts
    concept_ids = []
    if concepts:
        for c in concepts:
            cid = c.get("concept_id", "")
            if not cid:
                continue
            source_ref = f"{source_id}/{section_id}"
            r = aitp_create_l2_node(
                topics_root=topics_root, node_id=cid,
                node_type=c.get("node_type", "concept"),
                title=c.get("title", cid),
                domain=c.get("domain", ""),
                physical_meaning=c.get("physical_meaning", ""),
                mathematical_expression=c.get("expression", ""),
                source_ref=source_ref,
            )
            concept_ids.append(cid)
            results["nodes_created"] += 1

    # 3. Auto-suggest related existing L2 concepts
    if concept_ids:
        suggestions = _suggest_related_concepts(
            topics_root, concept_ids[0], concept_ids
        )
        if suggestions:
            results["suggestions"] = suggestions

    # 4. Create L2 edges
    if edges:
        for e in edges:
            eid = f"{e.get('from_node', '')}--{e.get('to_node', '')}"
            source_ref = f"{source_id}/{section_id}"
            r = aitp_create_l2_edge(
                topics_root=topics_root, edge_id=eid,
                from_node=e.get("from_node", ""),
                to_node=e.get("to_node", ""),
                edge_type=e.get("edge_type", "uses"),
                source_ref=source_ref,
            )
            results["edges_created"] += 1

    # 5. Update section status
    results["status"] = aitp_update_section_status(
        topics_root=topics_root, topic_slug=topic_slug,
        source_id=source_id, section_id=section_id,
        new_status="extracted",
    )

    return results


def _suggest_related_concepts(
    topics_root: str,
    query_title: str,
    exclude_ids: list[str],
    query_meaning: str = "",
) -> list[dict[str, Any]]:
    """Find existing L2 concepts semantically similar using TF-IDF vectors."""
    global_l2 = _global_l2_path(topics_root)
    nodes_dir = global_l2 / "graph" / "nodes"
    if not nodes_dir.is_dir():
        return []

    # Collect all existing nodes with embeddings
    candidates = []
    existing_texts = []
    exclude = set(exclude_ids)
    for np in nodes_dir.glob("*.md"):
        nid = np.stem
        if nid in exclude:
            continue
        fm, _ = _parse_md(np)
        candidates.append({
            "node_id": nid,
            "title": fm.get("title", nid),
            "domain": fm.get("domain", ""),
            "type": fm.get("type", ""),
            "_embedding": fm.get("_embedding", ""),
        })
        existing_texts.append(
            fm.get("title", nid) + " " + (fm.get("physical_meaning", "") or "")
        )

    if not candidates:
        return []

    try:
        from brain.l2_embedding import embed_concept, find_similar
        query_vec = embed_concept(query_title, query_meaning, existing_texts)
        return find_similar(query_vec, candidates, top_k=5, threshold=0.1)
    except Exception:
        # Fallback to token overlap if embedding fails
        suggestions = []
        query_tokens = set(query_title.lower().replace("-", " ").split())
        for c in candidates:
            title_tokens = set(c["title"].lower().split())
            overlap = query_tokens & title_tokens
            if len(overlap) >= 2 or query_title.lower() in c["title"].lower():
                suggestions.append({
                    "node_id": c["node_id"],
                    "title": c["title"],
                    "domain": c["domain"],
                    "type": c["type"],
                    "similarity": round(len(overlap) / len(query_tokens), 2) if query_tokens else 0,
                })
        suggestions.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        return suggestions[:5]


@mcp.tool()
@require_stage
# dispatch: source extract — core write dispatched to CLI; TOC update + log MCP-only
def aitp_write_section_intake(
    topics_root: str,
    topic_slug: str,
    source_id: str,
    section_id: str,
    section_title: str = "",
    summary: str = "",
    key_concepts: str = "",
    equations_found: str = "",
    physical_claims: str = "",
    prerequisites: str = "",
    completeness_confidence: str = "",
    cross_references: str = "",
    source_file: str = "",
) -> str:
    """Write a structured per-section intake note after reading a source.

    Creates L1/intake/{source_id}/{section_id}.md with frontmatter and body.
    Also updates the TOC map entry with a link to this intake note.

    For paper sources: section_id = chapter/section slug (e.g. "sec2-1")
    For repo sources: section_id = file path slug (e.g. "task-qsgw-band-0-cpp"),
      and source_file = the actual file path within the repo
      (e.g. "driver/task_qsgw_band_0.cpp").

    completeness_confidence: high | medium | low  --  honest self-assessment.
    """
    root = _topic_root(topics_root, topic_slug)

    # Compose rich body from structured MCP fields
    body_parts = [f"# {section_title or section_id}"]
    if summary:
        body_parts.append(f"\n## Section Summary (skim)\n\n{summary}")
    if key_concepts:
        body_parts.append(f"\n## Key Concepts\n\n{key_concepts}")
    if equations_found:
        body_parts.append(f"\n## Equations Found\n\n{equations_found}")
    if physical_claims:
        body_parts.append(f"\n## Physical Claims\n\n{physical_claims}")
    if prerequisites:
        body_parts.append(f"\n## Prerequisites\n\n{prerequisites}")
    if cross_references:
        body_parts.append(f"\n## Cross-References\n\n{cross_references}")
    if completeness_confidence:
        body_parts.append(
            f"\n## Completeness Self-Assessment\n\n"
            f"Confidence: **{completeness_confidence}**\n"
        )
    composed_body = "\n".join(body_parts)

    # Dispatch core write to CLI (already nests by source: L1/intake/{source}/{section}.md)
    from brain.cli._dispatch_helpers import dispatch
    from brain.cli.commands.reading import cmd_source_extract

    os.environ["AITP_TOPICS_ROOT"] = topics_root
    result = dispatch(cmd_source_extract,
        topic=topic_slug, source=source_id, section=section_id,
        content=composed_body, confidence=completeness_confidence or "medium",
        source_file=source_file,
        success_msg=f"Intake written: L1/intake/{_slugify(source_id)}/{_slugify(section_id)}.md")

    status = "extracted" if completeness_confidence in ("high", "medium") else "skimming"

    # TOC map update (MCP-only — richer than CLI currently handles)
    toc_path = root / "L1" / "source_toc_map.md"
    if toc_path.exists():
        t_fm, t_body = _parse_md(toc_path)
        old_marker = f"[{section_id}]"
        intake_link = f"L1/intake/{_slugify(source_id)}/{_slugify(section_id)}.md"
        lines = t_body.split("\n")
        for i, line in enumerate(lines):
            if old_marker in line:
                if "→ intake:" not in line:
                    lines[i] = line.rstrip() + f"  → intake: {intake_link}"
                break
        t_body = "\n".join(lines)
        _write_md(toc_path, t_fm, t_body)

    _append_to_topic_log(
        root,
        f"intake written for {source_id}/{section_id} "
        f"(confidence: {completeness_confidence or 'unset'})",
    )
    return (
        f"{result} Status: {status}, confidence: {completeness_confidence or 'unset'}."
    )


# dispatch: partial — core file creation differs from CLI (MCP creates candidate directly,
# CLI requires pre-existing file from derive_pack). Preflight dispatched to CLI.
@mcp.tool()
# dispatch: candidate submit — core validation dispatched to CLI; _GateResult popup MCP-only
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
    candidate_type: type of candidate  --  research modes produce research_claim (default),
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

    source_refs_list = depends_on or []

    fm = {
        "candidate_id": slug,
        "title": title,
        "claim": claim,
        "claim_statement": claim,      # CLI/contract compat (min_length=20 enforced by Pydantic)
        "status": "submitted",
        "mode": "candidate",
        "candidate_type": candidate_type,
        "l3_mode": l3_mode,
        "derivation_chain_id": "default",
        "source_refs": source_refs_list,
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

    # Dispatch to CLI for preflight + contract validation + stage transition
    from brain.cli._dispatch_helpers import dispatch
    from brain.cli.commands.l3_workflow import cmd_candidate_submit

    os.environ["AITP_TOPICS_ROOT"] = topics_root
    result = dispatch(cmd_candidate_submit,
        topic=topic_slug, candidate_id=slug, type=candidate_type,
        chain="default",
        success_msg=f"Submitted candidate {slug}")

    if "CLI command failed" in result:
        return result

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
# L3 idea branching  --  multiple approaches explored in parallel
# ---------------------------------------------------------------------------

_IDEA_STATUSES = {"active", "failed", "succeeded", "abandoned", "superseded"}


@mcp.tool()
@require_stage
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

    Research is branching  --  you may have multiple ideas for how to derive
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
    log_body += f"\n- {_now()}: {action} idea `{slug}`  --  **{title}** (status: {outcome})"
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

    msg = f"Idea '{slug}' {action} (status: {outcome})."
    if outcome == "failed":
        msg += " Failed approaches are valuable  --  their lessons will be preserved."

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
        status_filter: optional filter  --  active, failed, succeeded, abandoned, superseded
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
@require_stage
def aitp_promote_idea_to_candidate(
    topics_root: str,
    topic_slug: str,
    idea_slug: str,
    candidate_title: str = "",
    candidate_claim: str = "",
    derivation_summary: str = "",
    evidence: str = "",
    regime_of_validity: str = "",
) -> dict[str, Any]:
    """Promote a successful L3 idea to a full candidate for L4 validation.

    Copies the idea's approach and derivation into a new candidate file.
    The idea is marked as 'succeeded' and linked to the candidate.

    Args:
        idea_slug: The idea to promote
        candidate_title: Title for the candidate (defaults to idea title)
        candidate_claim: The claim statement (extracted from derivation if empty)
        derivation_summary: Summary of derivation from idea to claim
        evidence: Evidence supporting the claim
        regime_of_validity: Applicable scope/regime for the claim
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
    claim = candidate_claim or fm.get("idea_statement", "") or f"Derived via approach: {fm.get('approach', '')}"

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
        "derivation_summary": derivation_summary,
        "evidence": evidence,
        "regime_of_validity": regime_of_validity,
        "status": "submitted",
        "mode": "candidate",
        "candidate_type": "research_claim",
        "l3_mode": l3_mode,
        "promoted_from_idea": slug,
        "source_idea": slug,
        "depends_on": [],
        "created_at": _now(),
        "updated_at": _now(),
    }
    cand_body = (
        f"# {title}\n\n"
        f"## Claim\n{claim}\n\n"
        f"## Derivation Summary\n{derivation_summary or derivation[:2000]}\n\n"
        f"## Evidence\n{evidence or f'Derived via idea `{slug}`:\\n\\n' + derivation[:2000]}\n\n"
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
@with_preflight("promote")
@require_stage
# dispatch: promote — preflight dispatched to CLI; _GateResult popup MCP-only
def aitp_request_promotion(
    topics_root: str,
    topic_slug: str,
    candidate_id: str,
) -> dict[str, Any]:
    """Move a validated candidate to pending_approval for human review. Returns popup gate.

    Requires candidate status='validated' (i.e., L4 review with outcome='pass' has been submitted).
    Also verifies that an L4 pass review exists for this candidate.
    Refuses promotion if the topic has not reached L4 stage (L1->L2 bypass guard).
    """
    root = _topic_root(topics_root, topic_slug)

    # Dispatch preflight to CLI (contract validation, source coverage, etc.)
    from brain.cli.preflight import run_preflight
    os.environ["AITP_TOPICS_ROOT"] = topics_root
    preflight_failures = run_preflight("promote", root, candidate_id=candidate_id)
    if preflight_failures:
        return _GateResult({
            "message": f"Preflight blocked promotion: {'; '.join(preflight_failures[:3])}",
        })

    # L1->L2 bypass guard: topic must be at L4 or L2 stage
    state_fm, _ = _parse_md(root / "state.md")
    current_stage = str(state_fm.get("stage", "")).strip()
    if current_stage not in ("L4", "L2", "promotion"):
        return _GateResult({
            "message": (
                f"Promotion blocked: topic is at stage {current_stage or 'L0'}, "
                f"not L4. Candidates must pass through the full L0->L1->L3->L4 "
                f"pipeline before promotion to L2. Continue derivation and "
                f"validation first."
            ),
        })

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
@require_stage
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
            f"Address the rejection reason, then re-submit via aitp_submit_candidate "
            f"with the same candidate_id to restart the validation cycle."
        )
    return f"Candidate {slug} resolved: {decision}."


# MCP-native: writes to global L2 graph — promoted candidate → global L2 surface
@mcp.tool()
@with_preflight("promote")
@require_stage
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
            # Classify the conflict type
            def _classify_conflict(existing: str, new: str) -> str:
                """Heuristic classification of conflict type."""
                existing_lower = existing.lower()
                new_lower = new.lower()
                # Same result but different regime → regime_mismatch
                regime_words = {"regime", "coupling", "temperature", "limit", "thermal", "2d", "3d",
                               "weak", "strong", "low-t", "high-t", "finite", "zero-t"}
                if any(w in existing_lower for w in regime_words) and \
                   any(w in new_lower for w in regime_words):
                    # Check if the core claim is similar but regime differs
                    return "regime_mismatch"
                # Direct contradiction → physical_contradiction
                contradiction_words = {"not", "fails", "cannot", "does not", "never", "contradicts"}
                if any(w in existing_lower for w in contradiction_words) or \
                   any(w in new_lower for w in contradiction_words):
                    return "physical_contradiction"
                # Different notation → notation_collision
                notation_markers = {"sign", "convention", "normalization", "metric", "units",
                                   "factor of", "hbar", "c=1", "g=1", "(-+++)", "(+---)"}
                if any(w in existing_lower for w in notation_markers) and \
                   any(w in new_lower for w in notation_markers):
                    return "notation_collision"
                # New claim extends or replaces old → supersedes
                extend_words = {"extends", "generalizes", "supersedes", "beyond", "all-order"}
                if any(w in new_lower for w in extend_words):
                    return "supersedes"
                # Default: same topic but different conclusion
                return "physical_contradiction"

            conflict_type = _classify_conflict(existing_claim, new_claim)
            conflict_path = global_l2 / "conflicts" / f"{slug}.md"
            conflict_path.parent.mkdir(parents=True, exist_ok=True)
            conflict_fm = {
                "kind": "conflict",
                "candidate_id": slug,
                "conflict_type": conflict_type,
                "existing_claim": existing_claim,
                "new_claim": new_claim,
                "detected_at": _now(),
            }
            resolution_hints = {
                "physical_contradiction": "One claim must be wrong — re-validate both against independent sources.",
                "regime_mismatch": "Claims may both be correct in different regimes — define regime boundaries explicitly.",
                "notation_collision": "Likely a convention difference — canonicalise notation and re-compare.",
                "supersedes": "New claim extends old — verify the extension is valid, then version-bump.",
            }
            conflict_body = (
                f"# Conflict: {slug}\n\n"
                f"Type: **{conflict_type}**\n\n"
                f"Existing: {existing_claim}\n\nNew: {new_claim}\n\n"
                f"## Suggested Resolution\n{resolution_hints.get(conflict_type, 'Manual review required.')}\n"
            )
            _write_md(conflict_path, conflict_fm, conflict_body)
            return f"Conflict ({conflict_type}) detected for {slug}. Written to L2/conflicts/. Resolve before promoting."

        # Same or compatible claim: version bump
        existing_version = int(existing_fm.get("version", 1))
        fm["version"] = existing_version + 1
        fm["previous_version_promoted_at"] = existing_fm.get("promoted_at", "")

    fm["status"] = "promoted"
    fm["promoted_at"] = _now()
    fm["promotion_comment"] = comment
    fm["trust_basis"] = trust_basis
    fm["trust_scope"] = trust_scope
    fm["l2_path"] = str(l2_path)
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

    # Map candidate types to L2 node types
    _CANDIDATE_TO_L2_NODE_TYPE = {
        "atomic_concept": "concept",
        "derivation_chain": "derivation_chain",
        "correspondence_link": "regime_boundary",
        "regime_boundary": "regime_boundary",
        "open_question": "open_question",
        "research_claim": "result",
    }
    mapped_type = _CANDIDATE_TO_L2_NODE_TYPE.get(cand_type, cand_type)
    if mapped_type in L2_NODE_TYPES:
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
            return f"Promoted {slug} to global L2 (v{fm['version']}). WARNING: graph node not created  --  {e}"

    _append_to_topic_log(root, f"promoted {slug} to global L2 (v{fm['version']})")

    # Clear research loop on successful promotion
    sf, sb = _parse_md(root / "state.md")
    sf["research_loop_active"] = False
    sf["updated_at"] = _now()
    _write_md(root / "state.md", sf, sb)

    # EFT tower auto-matching: check if this result naturally fits into
    # existing EFT towers based on energy scale or regime proximity.
    eft_hints: list[str] = []
    try:
        reg = str(fm.get("regime_of_validity", ""))
        energy = str(fm.get("energy_scale", ""))
        if reg or energy:
            towers_dir = global_l2 / "graph" / "towers"
            if towers_dir.is_dir():
                for tp in sorted(towers_dir.glob("*.md")):
                    tfm, _ = _parse_md(tp)
                    tower_range = str(tfm.get("energy_range", "")).lower()
                    reg_lower = reg.lower()
                    energy_lower = energy.lower()
                    # Check regime keyword overlap
                    regime_overlap = any(
                        kw in tower_range or kw in str(tfm.get("name", "")).lower()
                        for kw in reg_lower.split()
                        if len(kw) > 3
                    )
                    # Check energy scale overlap
                    energy_overlap = (
                        energy_lower
                        and (energy_lower in tower_range or tower_range in energy_lower)
                    )
                    if regime_overlap or energy_overlap:
                        eft_hints.append(
                            f"EFT tower '{tfm.get('name', tp.stem)}' "
                            f"({tower_range}) may match. "
                            f"Consider aitp_create_l2_edge(edge_type='matches_onto') "
                            f"to link this result to the tower."
                        )

        if eft_hints:
            _append_to_topic_log(
                root,
                f"EFT auto-match for {slug}: {len(eft_hints)} candidate tower(s)",
            )
    except Exception:
        pass  # EFT matching is advisory only — never block promotion

    # Create/update a v5 faceted entry for this promoted claim
    try:
        entries_dir = global_l2 / "entries"
        entries_dir.mkdir(parents=True, exist_ok=True)
        entry_path = entries_dir / f"{slug}.md"

        # Map trust_basis to entry status
        trust_to_status = {
            "validated": "verified",
            "independently_verified": "verified",
            "multi_source_confirmed": "consistent",
            "source_grounded": "unverified",
        }
        entry_status = trust_to_status.get(trust_basis, "unverified")

        entry_fm: dict[str, Any] = {
            "entry_id": slug,
            "role": "claim",
            "title": fm.get("title", slug),
            "lane": [fm.get("lane", _normalize_lane("code_method"))],
            "status": entry_status,
            "regime": fm.get("regime_of_validity", ""),
            "claim_type": mapped_type if mapped_type in ("theorem", "result", "approximation",
                          "negative_result", "definition", "equation") else "result",
            "statement": fm.get("claim", ""),
            "observable": fm.get("observable", ""),
            "evidence_type": "code_derived" if _normalize_lane(fm.get("lane", "code_method")) == "code_method" else "analytic_proof",
            "source_ref": f"topic:{topic_slug}/candidate:{slug}",
            "updated": _now(),
            "version": 1,
            "created_at": _now(),
        }
        entry_body = (
            f"# {fm.get('title', slug)}\n\n"
            f"**Claim:** {fm.get('claim', '')}\n\n"
            f"**Trust:** {trust_basis} (promoted from topic:{topic_slug})\n\n"
            f"## Relationships\n"
            f"- promoted_from: topic:{topic_slug}\n"
        )
        if entry_path.exists():
            existing_entry_fm, _ = _parse_md(entry_path)
            entry_fm["version"] = int(existing_entry_fm.get("version", 1)) + 1
        _write_md(entry_path, entry_fm, entry_body)
        _rebuild_entry_index(global_l2)
        _append_to_topic_log(root, f"created L2 entry {slug} from promoted candidate")
    except Exception as e:
        _append_to_topic_log(root, f"entry creation for {slug} failed: {e}")
        # Don't block promotion — entry creation is additive

    return (
        f"Promoted {slug} to global L2 (v{fm['version']})."
        + (f"\n\nEFT tower matches:\n" + "\n".join(f"  - {h}" for h in eft_hints)
           if eft_hints else "")
    )


@mcp.tool()
@require_stage
def aitp_fast_track_claim(
    topics_root: str,
    topic_slug: str,
    claim: str,
    evidence_summary: str,
    source_ref: str,
    regime_of_validity: str = "",
    node_type: str = "result",
    domain: str = "",
) -> _GateResult:
    """Fast-track a claim from L3 distillation directly to L2 promotion.

    For claims already validated by literature or simple enough that formal
    L4 adversarial review is disproportionate. Creates candidate with
    source_grounded trust and returns a popup gate for human approval.

    The human MUST approve before the claim enters L2. This prevents
    unvalidated claims from poisoning the global knowledge graph.

    Trust basis is set to "source_grounded" (not "validated") to reflect
    the abbreviated path. Use aitp_fast_track_claim for:
    - Textbook or well-established results you're reproducing
    - Claims directly traceable to a peer-reviewed source
    - Simple correspondences or regime boundaries

    Do NOT use for novel claims requiring adversarial validation.
    """
    # Require non-empty source_ref
    if not source_ref or not source_ref.strip():
        return _GateResult({
            "message": "Fast-track requires a non-empty source_ref. "
                       "Provide the source that validates this claim."
        })
    # Require non-empty evidence_summary
    if not evidence_summary or not evidence_summary.strip():
        return _GateResult({
            "message": "Fast-track requires a non-empty evidence_summary. "
                       "Describe why this claim is already validated."
        })

    root = _topic_root(topics_root, topic_slug)
    slug = _slugify(claim)[:60]
    candidate_id = f"fast-{slug}"

    # Verify source_ref resolves to a registered L0 source
    sources_dir = root / "L0" / "sources"
    registered_sources = set()
    if sources_dir.exists():
        for sf in sources_dir.glob("*.md"):
            sf_fm, _ = _parse_md(sf)
            if sf_fm.get("source_id"):
                registered_sources.add(sf_fm["source_id"])
    source_id = source_ref.split(":")[0].strip() if ":" in source_ref else source_ref.strip()
    if registered_sources and source_id not in registered_sources:
        return _GateResult({
            "message": f"source_ref '{source_id}' does not match any registered L0 source. "
                       f"Register the source first with aitp source add."
        })

    # Write candidate — status "submitted" (not "approved_for_promotion")
    # Fast-tracked claims still go through the normal promotion gate
    cand_fm = {
        "candidate_id": candidate_id,
        "claim": claim,
        "evidence": evidence_summary,
        "source_ref": source_ref,
        "regime_of_validity": regime_of_validity,
        "candidate_type": node_type if node_type in L2_NODE_TYPES else "result",
        "status": "submitted",
        "confidence": "source_grounded",
        "fast_tracked": True,
        "created_at": _now(),
        "domain": domain,
    }
    cand_body = (
        f"# Fast-Track Claim: {claim[:80]}\n\n"
        f"**Claim:** {claim}\n\n"
        f"**Evidence:** {evidence_summary}\n\n"
        f"**Source:** {source_ref}\n\n"
        f"**Regime:** {regime_of_validity or '(unspecified)'}\n\n"
        f"## Fast-Track Justification\n"
        f"This claim was fast-tracked because it is either:\n"
        f"- Already validated in peer-reviewed literature, or\n"
        f"- A simple correspondence/regime boundary, or\n"
        f"- A concept definition directly traceable to source\n\n"
        f"Trust basis: source_grounded (not validated — no L4 review)\n"
    )
    cand_path = root / "L3" / "candidates" / f"{candidate_id}.md"
    _write_md(cand_path, cand_fm, cand_body)

    # Update state counters
    state_fm, state_body = _parse_md(root / "state.md")
    state_fm["candidates_count"] = state_fm.get("candidates_count", 0) + 1
    _write_md(root / "state.md", state_fm, state_body)

    _append_to_topic_log(root, f"fast-track claim '{claim[:80]}' awaiting approval ({candidate_id})")

    return _GateResult({
        "message": (
            f"Fast-track candidate created: '{claim[:80]}'\n"
            f"  candidate_id: {candidate_id}\n"
            f"  trust_basis: source_grounded (abbreviated path)\n"
            f"  regime: {regime_of_validity or '(unspecified)'}\n\n"
            f"HUMAN APPROVAL REQUIRED before L2 promotion."
        ),
        "popup_gate": {
            "question": (
                f"Fast-track claim for L2 promotion:\n\n"
                f"Claim: {claim}\n"
                f"Evidence: {evidence_summary}\n"
                f"Source: {source_ref}\n"
                f"Regime: {regime_of_validity or '(unspecified)'}\n\n"
                f"This skips L4 adversarial review. Approve?"
            ),
            "header": "Fast-Track Approval",
            "options": [
                {"label": "Approve", "description": "Promote to L2 with source_grounded trust"},
                {"label": "Send to L4", "description": "Require full adversarial validation first"},
                {"label": "Reject", "description": "Do not promote this claim"},
            ],
            "multiSelect": False,
        },
        "candidate_id": slug,
        "pending_approval": True,
    })


@mcp.tool()
def aitp_resolve_conflict(
    topics_root: str,
    topic_slug: str,
    conflict_id: str,
    resolution: str,
) -> dict[str, Any]:
    """Resolve an L2 conflict with a structured decision.

    Args:
        conflict_id: The conflict file slug (without .md)
        resolution: One of "accept_new", "accept_existing", "mark_regime_dependent", "defer"
    """
    valid_resolutions = ("accept_new", "accept_existing", "mark_regime_dependent", "defer")
    if resolution not in valid_resolutions:
        return {"message": f"Invalid resolution '{resolution}'. Must be one of {valid_resolutions}."}

    root = _topic_root(topics_root, topic_slug)
    global_l2 = _global_l2_path(topics_root)
    conflict_path = global_l2 / "conflicts" / f"{_slugify(conflict_id)}.md"

    if not conflict_path.exists():
        return {"message": f"Conflict '{conflict_id}' not found in L2/conflicts/."}

    cfm, cbody = _parse_md(conflict_path)

    if resolution == "defer":
        cfm["status"] = "deferred"
        cfm["resolved_at"] = _now()
        _write_md(conflict_path, cfm, cbody)
        _append_to_topic_log(root, f"conflict {conflict_id} deferred")
        return {"message": f"Conflict '{conflict_id}' deferred.", "status": "deferred"}

    if resolution == "accept_existing":
        cfm["status"] = "rejected"
        cfm["resolved_at"] = _now()
        _write_md(conflict_path, cfm, cbody)
        _append_to_topic_log(root, f"conflict {conflict_id}: accepted existing, rejected new")
        return {"message": f"Conflict '{conflict_id}': new claim rejected.", "status": "rejected"}

    slug = _slugify(conflict_id)

    if resolution == "accept_new":
        # Move old L2 node to superseded/
        l2_path = global_l2 / f"{slug}.md"
        if l2_path.exists():
            sup_dir = global_l2 / "superseded"
            sup_dir.mkdir(parents=True, exist_ok=True)
            existing_fm, existing_body = _parse_md(l2_path)
            existing_version = int(existing_fm.get("version", 1))
            existing_fm["superseded_at"] = _now()
            existing_fm["superseded_by"] = slug
            _write_md(sup_dir / f"{slug}_v{existing_version}.md", existing_fm, existing_body)
            l2_path.unlink()

        # Write new claim into L2 from candidate
        cand_path = root / "L3" / "candidates" / f"{slug}.md"
        if cand_path.exists():
            new_fm, new_body = _parse_md(cand_path)
            new_fm["status"] = "promoted"
            new_fm["promoted_at"] = _now()
            new_fm["version"] = int(new_fm.get("version", 0)) + 1
            _write_md(l2_path if not l2_path.exists() else global_l2 / f"{slug}.md",
                       new_fm, new_body)
            # Ensure the file exists (l2_path may have been unlinked above)
            target = global_l2 / f"{slug}.md"
            if not target.exists():
                _write_md(target, new_fm, new_body)

        # Also supersede old graph node and entry, create new entry
        try:
            old_node = global_l2 / "graph" / "nodes" / f"{slug}.md"
            if old_node.exists():
                old_nfm, old_nbody = _parse_md(old_node)
                old_nfm["superseded_at"] = _now()
                old_nfm["superseded_by"] = slug
                _write_md(sup_dir / f"{slug}_node_v{old_nfm.get('version',1)}.md", old_nfm, old_nbody)
                old_node.unlink()
            old_entry = global_l2 / "entries" / f"{slug}.md"
            if old_entry.exists():
                old_efm, old_ebody = _parse_md(old_entry)
                old_efm["superseded_at"] = _now()
                _write_md(sup_dir / f"{slug}_entry_v{old_efm.get('version',1)}.md", old_efm, old_ebody)
                old_entry.unlink()
            # Create new v5 entry for accepted claim
            entries_dir = global_l2 / "entries"
            entries_dir.mkdir(parents=True, exist_ok=True)
            entry_fm = {
                "entry_id": slug, "role": "claim", "title": str(new_fm.get("title", slug)),
                "lane": [], "status": "verified", "regime": str(new_fm.get("regime_of_validity", "")),
                "claim_type": "result", "statement": str(new_fm.get("claim", "")),
                "source_ref": f"topic:{topic_slug}/conflict-resolution",
                "updated": _now(), "version": 1, "created_at": _now(),
            }
            _write_md(entries_dir / f"{slug}.md", entry_fm, f"# {new_fm.get('title', slug)}\n\n**Claim:** {new_fm.get('claim', '')}\n\n## Relationships\n- supersedes: prior conflicting claim\n")
            _rebuild_entry_index(global_l2)
        except Exception:
            pass

        cfm["status"] = "resolved"
        cfm["resolution"] = "accept_new"
        cfm["resolved_at"] = _now()
        _write_md(conflict_path, cfm, cbody)
        _append_to_topic_log(root, f"conflict {conflict_id}: accepted new claim, superseded old")
        return {"message": f"Conflict '{conflict_id}': new claim accepted, old superseded.", "status": "resolved"}

    if resolution == "mark_regime_dependent":
        # Keep both: create a regime_boundary node linking them
        l2_path = global_l2 / f"{slug}.md"
        new_claim = cfm.get("new_claim", "")
        existing_claim = cfm.get("existing_claim", "")

        # Create regime_boundary node
        _ensure_l2_graph_dirs(topics_root)
        boundary_slug = f"{slug}-regime-boundary"
        node_path = global_l2 / "graph" / "nodes" / f"{boundary_slug}.md"
        node_fm = {
            "node_id": boundary_slug,
            "type": "regime_boundary",
            "title": f"Regime boundary for {slug}",
            "regime_of_validity": "see conflicting claims",
            "trust_basis": "conflict_resolved",
            "trust_scope": "bounded_reusable",
            "version": 1,
            "conflicting_claims": [existing_claim[:100], new_claim[:100]],
            "created_at": _now(),
            "updated_at": _now(),
        }
        node_body = (
            f"# Regime Boundary: {slug}\n\n"
            f"## Existing Claim\n{existing_claim}\n\n"
            f"## New Claim\n{new_claim}\n\n"
            f"## Boundary Description\nBoth claims retained as regime-dependent.\n"
        )
        _write_md(node_path, node_fm, node_body)

        cfm["status"] = "resolved"
        cfm["resolution"] = "mark_regime_dependent"
        cfm["resolved_at"] = _now()
        _write_md(conflict_path, cfm, cbody)
        _append_to_topic_log(
            root,
            f"conflict {conflict_id}: marked regime-dependent, boundary node created",
        )
        return {
            "message": f"Conflict '{conflict_id}': both claims retained as regime-dependent.",
            "status": "resolved",
            "boundary_node": boundary_slug,
        }

    return {"message": f"Unhandled resolution: {resolution}"}


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
    domain_prereqs = resolve_domain_prerequisites(root, topic_slug)

    # Scan pending L0 evidence requests
    pending_requests = []
    req_dir = root / "L0" / "pending_requests"
    if req_dir.is_dir():
        for req_path in sorted(req_dir.glob("*.md")):
            rfm, _ = _parse_md(req_path)
            if rfm.get("status") == "pending":
                pending_requests.append({
                    "request_id": rfm.get("request_id", req_path.stem),
                    "required_claim": str(rfm.get("required_claim", ""))[:120],
                    "requested_from": rfm.get("requested_from_stage", "unknown"),
                })

    # Scan L2 conflicts with open/pending status
    active_conflicts = []
    global_l2 = _global_l2_path(topics_root)
    conflicts_dir = global_l2 / "conflicts"
    if conflicts_dir.is_dir():
        for cp in sorted(conflicts_dir.glob("*.md")):
            cfm, _ = _parse_md(cp)
            cstatus = cfm.get("status", "")
            if cstatus in ("", "open", "pending"):
                active_conflicts.append({
                    "conflict_id": cfm.get("candidate_id", cp.stem),
                    "conflict_type": cfm.get("conflict_type", "unknown"),
                    "new_claim": str(cfm.get("new_claim", ""))[:120],
                    "existing_claim": str(cfm.get("existing_claim", ""))[:120],
                })

    # Common metadata for all branches
    _meta = {
        "research_intensity": str(fm.get("research_intensity", "standard")).strip() or "standard",
        "interaction_level": str(fm.get("interaction_level", "collaborative")).strip() or "collaborative",
    }

    if stage == "L3":
        snapshot = evaluate_l3_stage(_parse_md, root, lane=fm.get("lane", "unspecified"))
        return {
            "topic_slug": topic_slug,
            "stage": snapshot.stage,
            "posture": snapshot.posture,
            "lane": snapshot.lane,
            "research_intensity": _meta["research_intensity"],
            "interaction_level": _meta["interaction_level"],
            "compute_target": str(fm.get("compute", "local")),
            "gate_status": snapshot.gate_status,
            "required_artifact_path": snapshot.required_artifact_path,
            "missing_requirements": snapshot.missing_requirements,
            "next_allowed_transition": snapshot.next_allowed_transition,
            "skill": snapshot.skill,
            "l3_subplane": snapshot.l3_subplane,
            "l3_mode": snapshot.l3_mode,
            "domain_prerequisites": domain_prereqs,
            "domain_constraints": getattr(snapshot, "domain_constraints", {}),
            "l4_background_status": getattr(snapshot, "l4_background_status", ""),
            "immediate_allowed_work": (
                [f"edit {snapshot.required_artifact_path}"]
                if snapshot.required_artifact_path
                else [f"advance from {snapshot.l3_subplane}"]
            ),
            "pending_evidence_requests": pending_requests,
            "active_conflicts": active_conflicts,
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
            "research_intensity": _meta["research_intensity"],
            "interaction_level": _meta["interaction_level"],
            "compute_target": str(fm.get("compute", "local")),
            "gate_status": snapshot.gate_status,
            "required_artifact_path": snapshot.required_artifact_path,
            "missing_requirements": snapshot.missing_requirements,
            "next_allowed_transition": snapshot.next_allowed_transition,
            "skill": snapshot.skill,
            "l3_subplane": snapshot.l3_subplane,
            "domain_prerequisites": domain_prereqs,
            "domain_constraints": getattr(snapshot, "domain_constraints", {}),
            "l4_background_status": getattr(snapshot, "l4_background_status", ""),
            "immediate_allowed_work": (
                [f"edit {snapshot.required_artifact_path}"]
                if snapshot.required_artifact_path
                else ["advance to L1 (reading and framing)"]
            ),
            "pending_evidence_requests": pending_requests,
            "active_conflicts": active_conflicts,
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
            "research_intensity": _meta["research_intensity"],
            "interaction_level": _meta["interaction_level"],
            "compute_target": str(fm.get("compute", "local")),
            "gate_status": snapshot.gate_status,
            "required_artifact_path": snapshot.required_artifact_path,
            "missing_requirements": snapshot.missing_requirements,
            "next_allowed_transition": snapshot.next_allowed_transition,
            "skill": snapshot.skill,
            "l3_subplane": snapshot.l3_subplane,
            "domain_prerequisites": domain_prereqs,
            "domain_constraints": getattr(snapshot, "domain_constraints", {}),
            "l4_background_status": getattr(snapshot, "l4_background_status", ""),
            "immediate_allowed_work": (
                [f"edit {snapshot.required_artifact_path}"]
                if snapshot.required_artifact_path
                else ["submit L4 review for unreviewed candidates"]
            ),
            "pending_evidence_requests": pending_requests,
            "active_conflicts": active_conflicts,
            "immediate_blocked_work": ["L2 promotion (until validated)"],
            "_agent_behavior_reminder": _AGENT_BEHAVIOR_REMINDER,
        }

    # L5 writing removed in v4.0. If a legacy topic is at L5, redirect to L1.
    if stage == "L5":
        snapshot = evaluate_l1_stage(_parse_md, root, lane=fm.get("lane", "unspecified"))
        return {
            "topic_slug": topic_slug,
            "stage": snapshot.stage,
            "posture": snapshot.posture,
            "lane": snapshot.lane,
            "research_intensity": _meta["research_intensity"],
            "interaction_level": _meta["interaction_level"],
            "compute_target": str(fm.get("compute", "local")),
            "gate_status": snapshot.gate_status,
            "required_artifact_path": snapshot.required_artifact_path,
            "missing_requirements": snapshot.missing_requirements,
            "next_allowed_transition": snapshot.next_allowed_transition,
            "skill": snapshot.skill,
            "l3_subplane": snapshot.l3_subplane,
            "domain_prerequisites": domain_prereqs,
            "domain_constraints": getattr(snapshot, "domain_constraints", {}),
            "l4_background_status": getattr(snapshot, "l4_background_status", ""),
            "immediate_allowed_work": (
                [f"edit {snapshot.required_artifact_path}"]
                if snapshot.required_artifact_path
                else ["edit L1 artifacts"]
            ),
            "pending_evidence_requests": pending_requests,
            "active_conflicts": active_conflicts,
            "immediate_blocked_work": ["L3 derivation", "L4 validation", "L2 promotion"],
            "_agent_behavior_reminder": _AGENT_BEHAVIOR_REMINDER,
        }

    snapshot = evaluate_l1_stage(_parse_md, root, lane=fm.get("lane", "unspecified"))
    physics_context = _generate_physics_next_action(
        _parse_md, root, "L1", snapshot.gate_status
    )
    return {
        "topic_slug": topic_slug,
        "stage": snapshot.stage,
        "posture": snapshot.posture,
        "lane": snapshot.lane,
        "research_intensity": _meta["research_intensity"],
        "interaction_level": _meta["interaction_level"],
        "compute_target": str(fm.get("compute", "local")),
        "gate_status": snapshot.gate_status,
        "required_artifact_path": snapshot.required_artifact_path,
        "missing_requirements": snapshot.missing_requirements,
        "next_allowed_transition": snapshot.next_allowed_transition,
        "skill": snapshot.skill,
        "l3_subplane": snapshot.l3_subplane,
        "domain_prerequisites": domain_prereqs,
        "domain_constraints": getattr(snapshot, "domain_constraints", {}),
        "physics_context": physics_context,
        "immediate_allowed_work": (
            [f"edit {snapshot.required_artifact_path}"]
            if snapshot.required_artifact_path
            else ["prepare transition to L3"]
        ),
        "pending_evidence_requests": pending_requests,
        "active_conflicts": active_conflicts,
        "immediate_blocked_work": ["L3 derivation", "L4 validation", "L2 promotion"],
        "_agent_behavior_reminder": _AGENT_BEHAVIOR_REMINDER,
    }


@mcp.tool()
@require_stage
def aitp_l4_background_submit(
    topics_root: str,
    topic_slug: str,
    job_id: str = "",
    host: str = "",
    estimated_wall_time: str = "",
    notes: str = "",
) -> dict[str, Any]:
    """Submit L4 validation as a background HPC job and return to L3.

    Use when numerical validation requires long-running HPC jobs (QSGW, GW, DFT).
    The agent can switch back to L3 to ideate/plan/derive while the test runs.
    When the test completes, use aitp_l4_check_results to review.

    Args:
        topics_root: Path to AITP topics directory
        topic_slug: Topic identifier
        job_id: Slurm job ID or equivalent
        host: Host where the job is running
        estimated_wall_time: Expected duration (e.g. "2h", "30m")
        notes: What this test is validating
    """
    root = _topic_root(topics_root, topic_slug)
    state_path = root / "state.md"
    if not state_path.exists():
        return {"error": f"Topic {topic_slug} not found"}

    fm, body = _parse_md(state_path)
    fm["l4_background_status"] = "submitted"
    fm["l4_job_id"] = job_id
    fm["l4_job_host"] = host
    fm["l4_job_estimated_time"] = estimated_wall_time
    fm["l4_job_submitted_at"] = _now()
    fm["updated_at"] = _now()

    _write_md(state_path, fm, body)
    _append_to_topic_log(root, f"L4_background_submit: {job_id} on {host} ({estimated_wall_time})")

    # Build cron setup instructions for autonomous L4 polling
    poll_interval = _estimate_poll_interval(estimated_wall_time)
    watchdog_script = str(
        Path(__file__).resolve().parent.parent / "hooks" / "aitp_l4_watchdog.py"
    )
    cron_prompt = (
        f"Run `python {watchdog_script} {topics_root} --topic {topic_slug}`. "
        f"If exit code is 1 (job completed), call aitp_l4_check_results with the job result. "
        f"If exit code is 0 (still running), do nothing. "
        f"If exit code is 2 (error), record the error and cancel this cron job."
    )
    cron_setup = {
        "poll_interval": poll_interval,
        "watchdog_script": watchdog_script,
        "prompt": cron_prompt,
        "durable": True,
        "cron_expression": _to_cron_expression(poll_interval),
    }

    return {
        "status": "submitted",
        "job_id": job_id,
        "host": host,
        "estimated_wall_time": estimated_wall_time,
        "cron_setup": cron_setup,
        "message": (
            "L4 validation is now running in background. "
            "The agent SHOULD set up a durable cron job to poll this job "
            f"every {poll_interval}min using the watchdog script. "
            "Use aitp_switch_l3_activity to return to L3 for ideation/planning/derivation "
            "while the test runs. When the job completes, the watchdog will auto-update "
            "state.md and the SessionStart hook will surface it on next session."
        ),
    }


@mcp.tool()
@require_stage
def aitp_l4_check_results(
    topics_root: str,
    topic_slug: str,
    job_status: str = "",
    output_summary: str = "",
) -> dict[str, Any]:
    """Check L4 background validation results and return to L4 for review.

    Call this when the HPC job completes. Updates topic state to return to L4.

    Args:
        topics_root: Path to AITP topics directory
        topic_slug: Topic identifier
        job_status: Status of the completed job ("success", "failed", "timeout")
        output_summary: Brief summary of results
    """
    root = _topic_root(topics_root, topic_slug)
    state_path = root / "state.md"
    if not state_path.exists():
        return {"error": f"Topic {topic_slug} not found"}

    fm, body = _parse_md(state_path)
    old_status = fm.get("l4_background_status", "")
    fm["l4_background_status"] = "completed"
    fm["l4_job_result"] = job_status
    fm["l4_job_completed_at"] = _now()
    if output_summary:
        fm["l4_job_output_summary"] = output_summary
    fm["stage"] = "L4"
    fm["posture"] = "verify"
    fm["l4_review_needed"] = True   # flag: agent MUST create L4 reviews
    fm["updated_at"] = _now()

    _write_md(state_path, fm, body)
    _append_to_topic_log(root, f"L4_check_results: background job {job_status}. Returning to L4 verification.")

    return {
        "previous_status": old_status,
        "job_result": job_status,
        "stage": "L4",
        "posture": "verify",
        "l4_review_needed": True,
        "message": (
            "Returned to L4 for verification review. "
            f"Job result: {job_status}. "
            "l4_review_needed=True: you MUST call aitp_submit_l4_review "
            "for each candidate before the L4 gate will be ready. "
            "Review outputs in L4/outputs/ and file L4 reviews for candidates."
        ),
    }


@mcp.tool()
@require_stage
def aitp_record_numerical_result(
    topics_root: str,
    topic_slug: str,
    observable: str,
    computed_value: str,
    uncertainty: str = "",
    units: str = "",
    system: str = "",
    method: str = "",
    k_grid: str = "",
    host: str = "",
    job_id: str = "",
    literature_value: str = "",
    literature_source: str = "",
    agreement_status: str = "",
) -> str:
    """Record a structured numerical result with benchmark comparison.

    Creates a file in L4/outputs/ with structured frontmatter for L2 querying.
    Each result is traceable to execution conditions and literature benchmarks.

    Args:
        topics_root: Path to AITP topics directory
        topic_slug: Topic identifier
        observable: What was measured (e.g. "Si indirect band gap")
        computed_value: The computed value (e.g. "1.15")
        uncertainty: Estimated uncertainty (e.g. "0.05")
        units: Physical units (e.g. "eV")
        system: Physical system (e.g. "Si bulk 2x2x2")
        method: Method used (e.g. "QSGW band0, option_dielect_func=3")
        k_grid: k-point grid (e.g. "4x4x4")
        host: Execution host
        job_id: Slurm job ID
        literature_value: Known literature value
        literature_source: Reference for literature value
        agreement_status: "agrees", "deviates", "inconclusive", or empty
    """
    root = _topic_root(topics_root, topic_slug)
    outputs_dir = root / "L4" / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    slug = _slugify(observable)
    result_path = outputs_dir / f"{slug}.md"

    fm: dict[str, Any] = {
        "artifact_kind": "numerical_result",
        "observable": observable,
        "computed_value": computed_value,
        "uncertainty": uncertainty,
        "units": units,
        "system": system,
        "method": method,
        "k_grid": k_grid,
        "host": host,
        "job_id": job_id,
        "literature_value": literature_value,
        "literature_source": literature_source,
        "agreement_status": agreement_status,
        "recorded_at": _now(),
    }

    body = (
        f"# Numerical Result: {observable}\n\n"
        f"## Computed Value\n"
        f"- **Value**: {computed_value} ± {uncertainty} {units}\n"
        f"- **System**: {system}\n"
        f"- **Method**: {method}\n"
        f"- **k-grid**: {k_grid}\n\n"
        f"## Execution\n"
        f"- **Host**: {host}\n"
        f"- **Job ID**: {job_id}\n\n"
        f"## Benchmark Comparison\n"
        f"- **Literature value**: {literature_value} {units}\n"
        f"- **Source**: {literature_source}\n"
        f"- **Agreement**: {agreement_status}\n"
    )

    _write_md(result_path, fm, body)

    return (
        f"Recorded numerical result '{observable}': {computed_value} ± {uncertainty} {units} "
        f"(vs literature {literature_value} {units}, {agreement_status}). "
        f"Saved to L4/outputs/{slug}.md"
    )


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
    domain_prereqs = resolve_domain_prerequisites(root, topic_slug)

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
    elif stage == "L4":
        snapshot = evaluate_l4_stage(_parse_md, root, lane=fm.get("lane", "unspecified"))
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
    if snapshot.gate_status != "ready":
        summary_parts.append(f"gated by: {snapshot.missing_requirements}")
    if recent_events:
        summary_parts.append(f"last activity: {recent_events[-1]}")

    return {
        "topic_slug": topic_slug,
        "stage": stage,
        "posture": fm.get("posture", snapshot.posture),
        "lane": fm.get("lane", ""),
        "research_intensity": str(fm.get("research_intensity", "standard")).strip() or "standard",
        "interaction_level": str(fm.get("interaction_level", "collaborative")).strip() or "collaborative",
        "l3_mode": l3_mode,
        "l3_subplane": last_subplane,
        "gate_status": snapshot.gate_status,
        "skill": snapshot.skill,
        "domain_prerequisites": domain_prereqs,
        "domain_constraints": getattr(snapshot, "domain_constraints", {}),
        "required_artifact_path": snapshot.required_artifact_path,
        "missing_requirements": snapshot.missing_requirements,
        "recent_events": recent_events,
        "resume_summary": ". ".join(summary_parts) + ".",
        "instruction": (
            f"Resume by reading skill '{snapshot.skill}' and continuing "
            f"from where the last session left off. "
            f"Before continuing, check what L2 already knows: "
            f"call aitp_query_entries to find relevant verified claims, "
            f"methods, and pitfalls for this topic's domain."
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
) -> dict[str, Any]:
    """Transition a topic from L1 (ready) to L3 flexible workspace.

    L3 has no forced mode  --  the agent chooses activities as needed.
    Default starting activity: ideate.
    """
    root = _topic_root(topics_root, topic_slug)
    l1_snapshot = evaluate_l1_stage(_parse_md, root)
    if l1_snapshot.gate_status != "ready":
        return _GateResult({"message": f"L1 gate is not ready (status: {l1_snapshot.gate_status}). Fill missing artifacts first."})

    state_path = root / "state.md"
    fm, body = _parse_md(state_path)
    fm["stage"] = "L3"
    fm["posture"] = "derive"
    fm["l3_activity"] = "ideate"
    fm["updated_at"] = _now()
    _write_md(state_path, fm, body)

    # Create L3 activity directories and scaffolds
    for activity in L3_ACTIVITIES:
        (root / "L3" / activity).mkdir(parents=True, exist_ok=True)
        if activity in L3_ACTIVITY_TEMPLATES:
            _, template_fm, template_body = L3_ACTIVITY_TEMPLATES[activity]
            artifact_name = L3_ACTIVITY_ARTIFACT_NAMES.get(activity, f"active_{activity}.md")
            artifact_path = root / "L3" / activity / artifact_name
            if not artifact_path.exists():
                _write_md(artifact_path, template_fm, template_body)

    return _GateResult({
        "message": "Advanced to L3 flexible workspace. All activities available. Default: ideate.",
        "popup_gate": {
            "question": "L1 complete. Enter L3 flexible workspace?",
            "header": "L1→L3",
            "options": [
                {"label": "Enter L3", "description": "Start working in L3. All activities available. Switch freely."},
                {"label": "Review L1 first", "description": "Go back and review L1 artifacts before advancing."},
            ],
        },
    })


# dispatch: aitp switch-activity (partial — L4→L3 bg job logic is MCP-native)
# dispatch: switch-activity — normal case dispatched to CLI; L4→L3 bg job MCP-only
@mcp.tool()
def aitp_switch_l3_activity(
    topics_root: str, topic_slug: str, activity: str, reason: str = "",
) -> str:
    """Switch to a different L3 activity. No forced sequence: any activity
    can be entered at any time. All activities are available regardless of
    the current one. Only allows valid forward transitions and backedges.
    """
    root = _topic_root(topics_root, topic_slug)
    state_path = root / "state.md"
    fm, body = _parse_md(state_path)

    if activity not in L3_ACTIVITIES:
        return f"Unknown activity '{activity}'. Valid: {L3_ACTIVITIES}"

    # Allow switching from L4 back to L3 when background validation is running
    # (MCP-only — no CLI equivalent for L4→L3 bg job transition)
    current_stage = fm.get("stage", "L3")
    if current_stage == "L4":
        l4_bg = fm.get("l4_background_status", "")
        if l4_bg in ("submitted", "running"):
            fm["stage"] = "L3"
            fm["posture"] = "derive"
            fm["l3_activity"] = activity
            fm["l3_subplane"] = activity
            fm["updated_at"] = _now()
            _write_md(state_path, fm, body)
            _append_to_topic_log(root,
                f"L4→L3: switched to {activity} while L4 background job {fm.get('l4_job_id', '?')} "
                f"is {l4_bg} on {fm.get('l4_job_host', '?')}. "
                f"Use aitp_l4_check_results when job completes."
            )
            skill = L3_ACTIVITY_SKILL_MAP.get(activity, "skill-l3-ideate")
            return (
                f"Switched from L4 to L3 ({activity}) while background validation runs "
                f"(job {fm.get('l4_job_id', '?')} on {fm.get('l4_job_host', '?')}). "
                f"Follow {skill}. Use aitp_l4_check_results when the job completes."
            )
        else:
            return (
                f"Cannot switch from L4 to L3: no background job submitted. "
                f"Use aitp_l4_background_submit to submit validation as a background job first, "
                f"or complete L4 review to advance."
            )

    old = fm.get("l3_activity", "ideate")

    # Dispatch normal case to CLI
    from brain.cli._dispatch_helpers import dispatch
    from brain.cli.commands.l3_workflow import cmd_switch_activity

    os.environ["AITP_TOPICS_ROOT"] = topics_root
    result = dispatch(cmd_switch_activity,
        topic=topic_slug, activity=activity,
        success_msg=f"Switched L3 activity: {old} → {activity}")

    # MCP-only artifact warning (CLI doesn't do this)
    if old and old in L3_ACTIVITY_ARTIFACT_NAMES:
        artifact_name = L3_ACTIVITY_ARTIFACT_NAMES[old]
        old_artifact = root / "L3" / old / artifact_name
        if not old_artifact.exists():
            _append_to_topic_log(root,
                f"WARNING: switching from '{old}' to '{activity}' but "
                f"artifact {old_artifact.name} was not created. "
                f"Gate will block advance if this activity is needed."
            )

    _append_to_topic_log(root,
        f"L3 activity: {old} → {activity}" + (f" ({reason})" if reason else ""))

    skill = L3_ACTIVITY_SKILL_MAP.get(activity, "skill-l3-ideate")
    return f"{result}. Follow {skill}."


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

@mcp.tool()
def aitp_advance_l3_subplane(topics_root: str, topic_slug: str, target: str = "") -> str:
    """Deprecated alias for aitp_switch_l3_activity. Preserved for test compat."""
    return aitp_switch_l3_activity(topics_root, topic_slug, target)

@mcp.tool()
def aitp_switch_l3_mode(topics_root: str, topic_slug: str, new_mode: str) -> str:
    """Deprecated — L3 mode switching removed in v4.0. No-op for test compat."""
    root = _topic_root(topics_root, topic_slug)
    state_path = root / "state.md"
    fm, body = _parse_md(state_path)
    fm["l3_mode"] = new_mode
    fm["updated_at"] = _now()
    _write_md(state_path, fm, body)
    return f"L3 mode set to {new_mode} (deprecated)"

@mcp.tool()
def aitp_return_to_l3_from_l4(
    topics_root: str,
    topic_slug: str,
    reason: str = "post_l4_analysis",
) -> _GateResult:
    """Return from L4 validation to L3 analysis.

    Required by SPEC S3: L4 does not write directly to L2. All L4 results
    must flow through L3 analysis first. Sets L3 activity to integrate
    for post-validation analysis.
    """
    root = _topic_root(topics_root, topic_slug)
    state_path = root / "state.md"
    fm, body = _parse_md(state_path)
    current_stage = fm.get("stage", "L1")
    if current_stage != "L4":
        return _GateResult({
            "message": f"Cannot return: topic is at {current_stage}, not L4."
        })

    review_dir = root / "L4" / "reviews"
    if not review_dir.is_dir() or not list(review_dir.glob("*.md")):
        return _GateResult({
            "message": (
                "No L4 reviews found. Submit at least one validation "
                "review before returning to L3."
            ),
        })

    fm["stage"] = "L3"
    fm["posture"] = "derive"
    fm["l3_activity"] = "integrate"
    fm["returned_from_l4"] = True
    fm["l4_return_reason"] = reason
    fm["updated_at"] = _now()
    _write_md(state_path, fm, body)
    _append_to_topic_log(root, f"returned from L4 to L3/integrate: {reason}")
    return _GateResult({
        "message": (
            "Returned to L3/integrate. Analyze L4 validation results, "
            "check consistency, and decide: persist and advance, "
            "continue iterating, revise scope, or switch lane."
        ),
    })


# ---------------------------------------------------------------------------
# Gate override
# ---------------------------------------------------------------------------


@mcp.tool()
# dispatch: aitp gate override
def aitp_gate_override(
    topics_root: str,
    topic_slug: str,
    reason: str = "",
    scope: str = "current_gate",
) -> dict[str, Any]:
    """Override a blocked gate. Dispatches to CLI gate override.

    Args:
        topics_root: Path to AITP topics directory
        topic_slug: Topic identifier
        reason: Human-readable reason for the override (required)
        scope: 'current_gate' (one-time), 'this_session' (session duration),
               or 'permanent' (never block this gate again)
    """
    if not reason.strip():
        return {"error": "Reason is required for gate override. Use --reason to explain why."}

    from argparse import Namespace
    from brain.cli.__init__ import cmd_gate_override, _resolve_topic_root
    args = Namespace(
        topic=topic_slug, reason=reason, scope=scope,
        topics_root=topics_root,
    )
    root = _resolve_topic_root(topic_slug)
    state_path = root / "state.md"
    _, prev_body = _parse_md(state_path)
    prev_fm, _ = _parse_md(state_path) if state_path.exists() else ({}, "")
    gs = prev_fm.get("gate_status", "")

    # CLI function handles the state mutation and atomic write
    cmd_gate_override(args)

    return {
        "status": "overridden",
        "scope": scope,
        "previous_gate": gs,
        "message": f"Gate overridden: {gs} → ready_override. Scope: {scope}.",
    }


# ---------------------------------------------------------------------------
# L3 mode switching (research <-> study)
# ---------------------------------------------------------------------------


@mcp.tool()
def aitp_estimate_order(
    topics_root: str,
    expression: str,
    parameter_ranges: str = "",
) -> dict[str, Any]:
    """Estimate the order of magnitude of a physical expression.

    Given a symbolic expression and parameter value ranges, returns an
    order-of-magnitude estimate with uncertainty bounds. Uses dimensional
    analysis and provided parameter ranges.

    expression: a physical formula (e.g. "hbar * c / (G * M)")
    parameter_ranges: JSON string mapping parameter names to numeric ranges
        (e.g. '{"hbar": "1e-34", "c": "3e8", "G": "6.67e-11", "M": "2e30"}')
        Values can be single numbers or "min,max" ranges.

    Returns: dict with estimated_order (power of 10), lower_bound, upper_bound,
        units_hint, and a note about confidence.

    IMPORTANT: This is an order-of-magnitude estimate only. Results should be
    treated as ±1 order of magnitude. Use for sanity checks, not proofs.
    """
    import json as _json
    import math

    try:
        ranges = _json.loads(parameter_ranges) if parameter_ranges else {}
    except _json.JSONDecodeError:
        return {"error": "parameter_ranges must be valid JSON"}

    # Parse each parameter
    params = {}
    for name, val in ranges.items():
        if isinstance(val, str) and "," in val:
            lo, hi = val.split(",")
            params[name] = (float(lo), float(hi))
        else:
            v = float(val) if isinstance(val, str) else float(val)
            params[name] = (v, v)

    # Known physical constants for auto-fill
    constants = {
        "hbar": 1.054571817e-34,
        "h": 6.62607015e-34,
        "c": 2.99792458e8,
        "e": 1.602176634e-19,
        "k_B": 1.380649e-23,
        "G": 6.67430e-11,
        "m_e": 9.10938356e-31,
        "m_p": 1.67262192e-27,
        "epsilon_0": 8.8541878128e-12,
        "mu_0": 1.25663706212e-6,
    }

    # Try to evaluate the expression with nominal parameter values
    import sympy as _sp
    try:
        expr = _sp.sympify(expression)
    except Exception:
        return {"error": f"Cannot parse expression: {expression}"}

    # Substitute known constants and parameters
    subs = {}
    for s in expr.free_symbols:
        name = str(s)
        if name in params:
            subs[s] = (params[name][0] + params[name][1]) / 2  # midpoint
        elif name in constants:
            subs[s] = constants[name]

    try:
        nominal = float(expr.subs(subs))
    except Exception:
        nominal = None

    # Estimate order of magnitude
    if nominal and nominal != 0:
        order = int(math.floor(math.log10(abs(nominal))))
        lower = 10 ** (order - 1)
        upper = 10 ** (order + 1)
        return {
            "expression": expression,
            "estimated_order": order,
            "estimated_value": nominal,
            "lower_bound": lower,
            "upper_bound": upper,
            "confidence_note": "Order-of-magnitude estimate only. ±1 order. Use for sanity checks, not proofs.",
        }
    else:
        # Pure dimensional estimate
        return {
            "expression": expression,
            "estimated_order": "unknown",
            "note": "Could not evaluate numerically. Check parameter values.",
            "missing_params": [str(s) for s in expr.free_symbols if str(s) not in subs],
            "confidence_note": "Could not compute. Provide parameter_ranges for all symbols.",
        }


# ---------------------------------------------------------------------------
# Flow TeX
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# L4 physics adjudication
# ---------------------------------------------------------------------------


@mcp.tool()
@require_stage
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
        correspondence_check  --  OR verification_evidence from SymPy verification tools.
      Each check must describe what was verified and the outcome.

    devils_advocate: REQUIRED for "pass". State at least one specific way the
      claim could still be wrong despite passing all checks. This is the
      adversarial collaborator's duty  --  no claim is beyond doubt.

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
                    "State at least one specific way the claim could still be wrong  --  "
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
                        f"Python cannot certify physics  --  you must provide the evidence."
                    ),
                }

    (root / "L4" / "reviews").mkdir(parents=True, exist_ok=True)
    cycle = int(state_fm.get("l4_cycle_count", 0)) + 1
    max_cycles = int(state_fm.get("research_loop_max_cycles", 0))
    loop_warning = ""
    if max_cycles > 0 and cycle > max_cycles:
        loop_warning = (
            f" WARNING: L4 cycle {cycle} exceeds max_cycles={max_cycles}. "
            f"Consider: (a) switching lane via aitp_switch_lane, "
            f"(b) narrowing the claim scope, or (c) accepting current result."
        )
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
            # Reset status if previously validated  --  new review invalidates old result
            if cand_fm.get("status") in ("validated", "partial_validated"):
                cand_fm["status"] = "submitted"
        _write_md(cand_path, cand_fm, cand_body)

    msg = f"L4 review submitted for {slug}: {outcome} (cycle {cycle}).{loop_warning}"
    result: dict[str, Any] = {"message": msg}
    result["l4_cycle"] = cycle
    if max_cycles > 0:
        result["max_cycles"] = max_cycles
        result["cycles_remaining"] = max(0, max_cycles - cycle)

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
    state_fm["l4_cycle_count"] = cycle
    state_fm.pop("l4_review_needed", None)  # review submitted → flag resolved
    _write_md(root / "state.md", state_fm, _parse_md(root / "state.md")[1])
    return _GateResult(result)


# ---------------------------------------------------------------------------
# Topic lifecycle
# ---------------------------------------------------------------------------


@mcp.tool()
@require_stage
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
@require_stage
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
    This is a pure symbolic check  --  no LLM judgment involved.

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
    output correctly follows from the input using this rule  --  independent
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
    # For code_method steps that are source_anchored, skip SymPy verification
    if rule == "source_anchored":
        return {
            "pass": True,
            "method": "source_anchored",
            "rule": rule,
            "note": (
                "code_method lane: this step is verified by source anchoring "
                "(file:line reference to real code). Numerical verification "
                "required at L4 (compile + run + compare output)."
            ),
        }
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
def aitp_set_interaction_level(
    topics_root: str,
    topic_slug: str,
    level: str,
) -> dict[str, Any]:
    """Change the interaction level for the current topic.

    Valid levels:
      - collaborative: full popup gates, AskUserQuestion at all decision points
      - direct: popup gates for gate transitions only, skip discussion rounds
      - silent: no popup gates (human override only on promotion rejection)

    Use when the user says "just go ahead", "don't ask me", or wants more control.
    """
    valid_levels = {"collaborative", "direct", "silent"}
    if level not in valid_levels:
        return {
            "message": f"Invalid interaction level '{level}'. Valid: {sorted(valid_levels)}",
        }

    root = _topic_root(topics_root, topic_slug)
    state_path = root / "state.md"
    fm, body = _parse_md(state_path)
    old_level = str(fm.get("interaction_level", "collaborative")).strip() or "collaborative"

    fm["interaction_level"] = level
    fm["updated_at"] = _now()
    _write_md(state_path, fm, body)
    _append_to_topic_log(
        root,
        f"interaction level: {old_level} -> {level}",
    )

    return {
        "message": f"Interaction level set to '{level}' (was '{old_level}').",
        "old_level": old_level,
        "new_level": level,
    }



@mcp.tool()
@require_stage
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
# L4 watchdog helpers
# ---------------------------------------------------------------------------


def _estimate_poll_interval(wall_time: str) -> int:
    """Estimate polling interval in minutes from wall time string like '2h', '30m'."""
    if not wall_time:
        return 5
    wall = wall_time.lower().strip()
    match = re.match(r"(\d+)\s*(h|m|hour|min)", wall)
    if not match:
        return 5
    value, unit = int(match.group(1)), match.group(2)[0]
    total_minutes = value * 60 if unit == "h" else value
    # Poll at ~1/10 of estimated wall time, min 2min, max 15min
    interval = max(2, min(15, total_minutes // 10))
    return interval


def _to_cron_expression(interval_minutes: int) -> str:
    """Convert poll interval to cron expression."""
    if interval_minutes <= 1:
        return "*/1 * * * *"
    return f"*/{interval_minutes} * * * *"


# Knowledge-base operations
# ---------------------------------------------------------------------------


def _append_to_topic_log(root: Path, event: str, *args, **kwargs) -> None:
    """Append a dated event to the topic runtime log."""
    if args:
        import sys
        print(f"WARNING: _append_to_topic_log received extra args: {args} {kwargs}", file=sys.stderr)
        event = f"{event} {' '.join(str(a) for a in args)}"
    log_path = root / "runtime" / "log.md"
    if log_path.exists():
        existing = log_path.read_text(encoding="utf-8")
    else:
        existing = f"# Topic Log\n\n## Events\n"
    if not existing.endswith("\n"):
        existing += "\n"
    _atomic_write_text(log_path, existing + f"- {_now()} {event}\n")


def _validate_entry_referential_integrity(
    global_l2: Path, slug: str, fm: dict[str, Any], relationships: str
) -> list[str]:
    """Validate referential integrity of an entry's relationships.

    Checks:
    1. All referenced entry IDs in relationships text exist
    2. No circular trust (verified_by → unverified method)
    3. Lane is not empty for claim/system/method/pitfall roles
    4. Regime is not empty for claim/system/method roles

    Returns list of validation issues (empty = valid).
    """
    import re
    issues: list[str] = []

    # 1. Lane is required
    lane = fm.get("lane", [])
    if not lane or (isinstance(lane, list) and len(lane) == 0):
        issues.append("lane is required — specify at least one lane (formal_theory, code_method, toy_numeric)")

    # 2. Regime is required for claim, system, method
    role = str(fm.get("role", ""))
    regime = str(fm.get("regime", "")).strip()
    if role in ("claim", "system", "method") and not regime:
        issues.append(f"regime is required for role={role} — specify where this holds")

    # 3. Referential integrity: check all entry slugs referenced in relationships
    entries_dir = global_l2 / "entries"
    existing_slugs: set[str] = set()
    if entries_dir.is_dir():
        for ep in entries_dir.glob("*.md"):
            if ep.stem not in ("INDEX", "INDEX_status", "INDEX_pitfalls", "INDEX_reverse"):
                existing_slugs.add(ep.stem)

    # Parse relationship entries: "- edge_type: target_slug"
    ref_pattern = re.compile(r'[-*]\s+\w+:\s*([a-z][a-z0-9-]+)', re.IGNORECASE)
    for match in ref_pattern.finditer(relationships):
        ref_slug = match.group(1).strip()
        if ref_slug and ref_slug != slug and ref_slug not in existing_slugs:
            # Check if it's a graph node reference (not yet migrated)
            node_path = global_l2 / "graph" / "nodes" / f"{ref_slug}.md"
            if not node_path.exists():
                issues.append(f"Referenced entry/node '{ref_slug}' does not exist in L2")

    # Also validate frontmatter list fields
    for field_name in ("affects_methods", "depends_on_claims", "depends_on"):
        values = fm.get(field_name, [])
        if isinstance(values, str):
            values = [v.strip() for v in values.split(",") if v.strip()]
        if not isinstance(values, list):
            values = []
        for v in values:
            v_slug = str(v).strip()
            if v_slug and v_slug not in existing_slugs:
                node_path = global_l2 / "graph" / "nodes" / f"{v_slug}.md"
                if not node_path.exists():
                    issues.append(f"{field_name} references '{v_slug}' which does not exist in L2")

    # 4. Trust circularity check: status=verified but verified_by points to unverified
    if role == "claim" and fm.get("status") == "verified":
        verified_by_match = re.search(r'[-*]\s*verified_by\s*:\s*([a-z][a-z0-9-]+)', relationships, re.IGNORECASE)
        if verified_by_match:
            vfy_slug = verified_by_match.group(1).strip()
            if vfy_slug in existing_slugs:
                vfy_path = entries_dir / f"{vfy_slug}.md"
                vfy_fm, _ = _parse_md(vfy_path)
                vfy_status = str(vfy_fm.get("status", ""))
                if vfy_status not in ("verified", "consistent"):
                    issues.append(
                        f"Circular trust: status=verified but verified_by='{vfy_slug}' "
                        f"has status='{vfy_status}'. Change verified_by target or downgrade status."
                    )

    return issues


def _detect_duplicate_entries(
    global_l2: Path, title: str, slug: str, threshold: float = 0.85
) -> list[dict[str, Any]]:
    """Detect existing entries with similar titles (content-based dedup).

    Uses semantic_score from brain.semantic for title comparison.
    Returns list of near-duplicate candidates (empty = no duplicates).
    """
    entries_dir = global_l2 / "entries"
    if not entries_dir.is_dir():
        return []

    duplicates: list[dict[str, Any]] = []
    for ep in entries_dir.glob("*.md"):
        if ep.stem in ("INDEX", "INDEX_status", "INDEX_pitfalls", "INDEX_reverse"):
            continue
        if ep.stem == slug:
            continue
        efm, _ = _parse_md(ep)
        existing_title = str(efm.get("title", ""))
        if not existing_title:
            continue
        score = semantic_score(title, [existing_title])
        if score >= threshold:
            duplicates.append({
                "entry_id": efm.get("entry_id", ep.stem),
                "title": existing_title,
                "role": efm.get("role", ""),
                "status": efm.get("status", ""),
                "similarity": round(score, 3),
            })

    duplicates.sort(key=lambda d: d["similarity"], reverse=True)
    return duplicates


def _log_l2_query(tool_name: str, params: dict[str, Any], result_count: int) -> None:
    """Log an L2 query for telemetry. Appends to L2/log.md."""
    try:
        base = topics_dir(params.get("topics_root", "")) if params.get("topics_root") else None
        if not base:
            return
        log_path = base / "L2" / "log.md"
        # Build a compact event string
        compact_params = {k: v for k, v in params.items()
                         if k != "topics_root" and v not in ("", None, [], {})}
        params_str = ", ".join(f"{k}={str(v)[:60]}" for k, v in list(compact_params.items())[:3])
        qlog_line = f"- Q {_now()} {tool_name}({params_str}) → {result_count} results"
        existing = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
        # Keep query log under 50 lines (rolling)
        qlog_start = existing.find("## Query Log")
        if qlog_start == -1:
            existing = existing.rstrip() + "\n\n## Query Log\n\n"
            existing += qlog_line + "\n"
        else:
            # Insert after ## Query Log header, limit to 50 lines
            header_end = existing.find("\n", qlog_start) + 1
            qlog_lines = [l for l in existing[header_end:].split("\n") if l.startswith("- Q ")]
            qlog_lines = (qlog_lines[-49:] + [qlog_line]) if qlog_lines else [qlog_line]
            before = existing[:header_end]
            after_start = existing.find("\n## ", header_end + 1)
            after = existing[after_start:] if after_start != -1 else ""
            existing = before + "\n".join(qlog_lines) + "\n" + after
        _atomic_write_text(log_path, existing)
    except Exception:
        pass  # Never block operations for logging


def _global_l2_path(topics_root: str) -> Path:
    """Return the global L2 directory under the resolved topics directory.

    The L2 directory lives alongside topic directories, not outside the topics root.
    This is the single source of truth for all L2 data: promoted candidates,
    graph nodes/edges/towers, and v5 entries.
    """
    base = topics_dir(topics_root)
    return base / "L2"


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

    # Scan v5 entries (canonical source) for structured knowledge
    entries_dir = global_l2 / "entries"
    if entries_dir.is_dir():
        for ep in sorted(entries_dir.glob("*.md")):
            fm, body = _parse_md(ep)
            if ep.stem == "INDEX":
                continue
            entry_role = str(fm.get("role", ""))
            title = str(fm.get("title", ""))
            # Collect searchable text based on role
            search_text = title
            if entry_role == "claim":
                search_text += " " + str(fm.get("statement", ""))
                search_text += " " + str(fm.get("mathematical_expression", ""))
            elif entry_role == "pitfall":
                search_text += " " + str(fm.get("symptom", ""))
                search_text += " " + str(fm.get("cause", ""))
            elif entry_role == "question":
                search_text += " " + str(fm.get("question_statement", ""))
            elif entry_role == "method":
                search_text += " " + str(fm.get("steps", ""))
            elif entry_role == "system":
                search_text += " " + str(fm.get("formula_or_identifier", ""))
            if query:
                score = semantic_score(query, [search_text, body])
                if score < 0.15:
                    continue
            else:
                score = 1.0
            results.append({
                "candidate_id": fm.get("entry_id", ep.stem),
                "title": title,
                "entry_role": entry_role,
                "claim": (
                    str(fm.get("statement", "")) or
                    str(fm.get("question_statement", "")) or
                    str(fm.get("symptom", "")) or
                    str(fm.get("formula_or_identifier", "")) or
                    title
                ),
                "trust_basis": fm.get("status", ""),
                "trust_scope": fm.get("regime", ""),
                "version": 1,
                "promoted_at": fm.get("updated", ""),
                "relevance": round(score, 3),
                "source": "v5_entry",
            })

    results.sort(key=lambda r: r.get("relevance", 0.0), reverse=True)
    result_count = len(results)
    _log_l2_query("aitp_query_l2", {"topics_root": topics_root, "query": query}, result_count)
    return {
        "results": results,
        "conflicts": conflicts,
        "count": result_count,
        "authority_level": "L2_validated_reusable",
    }


@mcp.tool()
def aitp_query_l2_index(
    topics_root: str,
    domain_filter: str = "",
) -> dict[str, Any]:
    """Query the L2 knowledge base index  --  progressive disclosure entry point.

    Returns a domain taxonomy tree with per-domain summaries and node counts.
    Use this FIRST when starting a new topic to discover what L2 already knows.
    Then drill down with aitp_query_l2_graph for specific nodes.

    If domain_filter is given, returns only that domain with full node listings.
    Otherwise returns all domains with summary-level detail.
    """
    global_l2 = _global_l2_path(topics_root)
    entries_dir = global_l2 / "entries"
    if not entries_dir.is_dir() or not any(
        ep.stem != "INDEX" for ep in entries_dir.glob("*.md")
    ):
        return {
            "domains": {},
            "total_nodes": 0,
            "valid_domains": sorted(VALID_DOMAINS),
            "message": (
                "L2 entries directory is empty — no validated knowledge yet. "
                "Use aitp_create_entry to seed foundational knowledge."
            ),
        }

    # Scan entries (canonical source) and group by role
    domains: dict[str, dict[str, Any]] = {}
    for ep in sorted(entries_dir.glob("*.md")):
        if ep.stem.startswith("INDEX"):
            continue
        fm, body = _parse_md(ep)
        entry_role = str(fm.get("role", "uncategorized"))

        if entry_role not in domains:
            domains[entry_role] = {
                "node_count": 0,
                "by_type": {},
                "nodes": [],
            }

        node_info = {
            "node_id": fm.get("entry_id", ep.stem),
            "title": fm.get("title", ep.stem),
            "type": entry_role,
            "trust_basis": fm.get("status", "unverified"),
            "regime_of_validity": fm.get("regime", ""),
            "mathematical_expression": fm.get("mathematical_expression", ""),
            "physical_meaning": (str(fm.get("statement", "")) or "")[:200],
        }

        domains[entry_role]["node_count"] += 1
        # Sub-type within role
        subtype = fm.get("claim_type", "") or entry_role
        domains[entry_role]["by_type"][subtype] = domains[entry_role]["by_type"].get(subtype, 0) + 1
        domains[entry_role]["nodes"].append(node_info)

    # Build progressive-disclosure response (entry-based)
    domain_summaries: dict[str, Any] = {}
    for domain_name, data in domains.items():
        summary = {
            "node_count": data["node_count"],
            "by_type": data["by_type"],
            "key_results": [
                n["title"] for n in data["nodes"]
                if n["trust_basis"] == "verified"
            ][:5],
            "established_concepts": [
                n["title"] for n in data["nodes"]
                if n["type"] == "claim"
            ][:5],
            "open_questions": [
                n["title"] for n in data["nodes"]
                if n["type"] == "question"
            ],
            "pitfalls": [
                n["title"] for n in data["nodes"]
                if n["type"] == "pitfall"
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
        "hint": "Use aitp_query_l2_graph to drill into specific entries, or aitp_query_entries for filtered queries.",
    }


@mcp.tool()
def aitp_query_entries(
    topics_root: str,
    role: str = "",
    system: str = "",
    status: str = "",
    query: str = "",
) -> dict[str, Any]:
    """Query L2 v5 faceted entries by role, system, status, or free text.

    This is the PRIMARY L2 query tool for physicist workflow patterns:
    - "What's known about system X?" → role="claim", system="X"
    - "What methods exist for this?" → role="method"
    - "Known pitfalls?" → role="pitfall"
    - "Open questions?" → role="question"
    - "Verified claims?" → role="claim", status="verified"

    Entries use the v5 faceted schema with five roles:
    - claim: statements about nature (theorem, result, equation, definition, ...)
    - system: physical systems (material, hamiltonian, field_theory, ...)
    - method: techniques and workflows (code, numerics, analytics, ...)
    - pitfall: known failure modes (symptom + cause + fix)
    - question: open research problems (question + competing hypotheses)

    Use aitp_query_entries BEFORE aitp_query_l2_graph — entries are the
    primary knowledge store. Drill into graph nodes for theoretical relationships.
    """
    global_l2 = _global_l2_path(topics_root)
    entries_dir = global_l2 / "entries"

    if not entries_dir.is_dir():
        return {
            "entries": [],
            "count": 0,
            "message": "No entries directory found. Create entries with aitp_create_entry or promote candidates.",
        }

    results = []
    for ep in sorted(entries_dir.glob("*.md")):
        if ep.stem == "INDEX":
            continue
        fm, body = _parse_md(ep)
        entry_role = str(fm.get("role", ""))
        entry_title = str(fm.get("title", ""))

        # Filter by role
        if role and entry_role != role:
            continue

        # Filter by status
        entry_status = str(fm.get("status", ""))
        if status and entry_status != status:
            continue

        # Filter by system (checks relationships and system_id fields)
        if system:
            system_match = False
            # Check if this entry relates to the target system
            sys_id = str(fm.get("system_id", "")).lower()
            if system.lower() in sys_id:
                system_match = True
            # Check title for system name
            if system.lower() in entry_title.lower():
                system_match = True
            # Check body for system slug or name
            if f"system-{system}" in body.lower() or system.lower() in body.lower():
                system_match = True
            # Check relationships section
            rel_section = body.find("## Relationships")
            if rel_section != -1:
                rel_text = body[rel_section:]
                if system.lower() in rel_text.lower():
                    system_match = True
            if not system_match:
                continue

        # Free text search
        if query:
            search_text = entry_title
            if entry_role == "claim":
                search_text += " " + str(fm.get("statement", ""))
                search_text += " " + str(fm.get("mathematical_expression", ""))
                search_text += " " + str(fm.get("claim_type", ""))
            elif entry_role == "pitfall":
                search_text += " " + str(fm.get("symptom", ""))
                search_text += " " + str(fm.get("cause", ""))
                search_text += " " + str(fm.get("fix", ""))
            elif entry_role == "question":
                search_text += " " + str(fm.get("question_statement", ""))
            elif entry_role == "method":
                search_text += " " + str(fm.get("method_type", ""))
                search_text += " " + str(fm.get("toolchain", ""))
                search_text += " " + str(fm.get("steps", ""))
            elif entry_role == "system":
                search_text += " " + str(fm.get("system_type", ""))
                search_text += " " + str(fm.get("formula_or_identifier", ""))
                search_text += " " + str(fm.get("parameters", ""))

            score = semantic_score(query, [search_text, body])
            if score < 0.15:
                continue
            relevance = round(score, 3)
        else:
            relevance = 1.0

        # Build entry result with role-specific fields
        entry_result = {
            "entry_id": fm.get("entry_id", ep.stem),
            "role": entry_role,
            "title": entry_title,
            "status": entry_status,
            "lane": fm.get("lane", []),
            "regime": fm.get("regime", ""),
            "source_ref": fm.get("source_ref", ""),
            "updated": fm.get("updated", ""),
            "relevance": relevance,
        }

        # Role-specific facet exposure
        if entry_role == "claim":
            entry_result["claim_type"] = fm.get("claim_type", "")
            entry_result["statement"] = fm.get("statement", "")
            entry_result["observable"] = fm.get("observable", "")
            entry_result["evidence_type"] = fm.get("evidence_type", "")
        elif entry_role == "system":
            entry_result["system_type"] = fm.get("system_type", "")
            entry_result["formula_or_identifier"] = fm.get("formula_or_identifier", "")
            entry_result["parameters"] = fm.get("parameters", "")
            entry_result["reference_values"] = fm.get("reference_values", {})
        elif entry_role == "method":
            entry_result["method_type"] = fm.get("method_type", "")
            entry_result["toolchain"] = fm.get("toolchain", [])
            entry_result["steps"] = fm.get("steps", [])
            entry_result["compatibility"] = fm.get("compatibility", {})
            entry_result["resource_estimate"] = fm.get("resource_estimate", "")
        elif entry_role == "pitfall":
            entry_result["symptom"] = fm.get("symptom", "")
            entry_result["cause"] = fm.get("cause", "")
            entry_result["fix"] = fm.get("fix", "")
            entry_result["affects_methods"] = fm.get("affects_methods", [])
        elif entry_role == "question":
            entry_result["question_statement"] = fm.get("question_statement", "")
            entry_result["competing_hypotheses"] = fm.get("competing_hypotheses", [])

        results.append(entry_result)

    # Sort: verified first, then by relevance
    status_rank = {"verified": 0, "consistent": 1, "unverified": 2, "failed": 3, "conjectured": 4}
    results.sort(key=lambda r: (status_rank.get(r.get("status", ""), 5), -r.get("relevance", 0)))

    return {
        "entries": results,
        "count": len(results),
        "roles_present": list(set(r["role"] for r in results)),
        "authority_level": "L2_entries_v5",
    }


# ---------------------------------------------------------------------------
# L2 knowledge graph operations
# ---------------------------------------------------------------------------


def _ensure_l2_graph_dirs(topics_root: str) -> Path:
    """Ensure L2 subdirectories exist and return the L2 root.

    Creates the full v5 faceted layout: entries/, graph/{nodes,edges,towers,
    diagrams,steps}, templates/, conflicts/. Also bootstraps INDEX.md,
    INDEX_status.md, and INDEX_pitfalls.md if they don't exist.
    """
    global_l2 = _global_l2_path(topics_root)
    global_l2.mkdir(parents=True, exist_ok=True)
    for sub in [
        "entries", "templates",
        "graph/nodes", "graph/edges", "graph/towers",
        "graph/diagrams", "graph/steps",
        "conflicts",
    ]:
        (global_l2 / sub).mkdir(parents=True, exist_ok=True)

    # Bootstrap index files if missing
    now_ = _now()
    for fname, fm, body in [
        ("INDEX.md", {
            "kind": "l2_index", "created_at": now_,
        }, (
            "# L2 Knowledge Index\n\n"
            "## By Role\n\n"
            "## By Status\n\n"
            "## By Lane\n\n"
            "## By Regime\n"
        )),
        ("INDEX_status.md", {
            "kind": "l2_status_index", "created_at": now_,
        }, (
            "# L2 Status Index — Verified Entries Only\n\n"
            "Bootstrap-only index. Contains only entries with status=verified.\n\n"
            "## Claims\n\n## Systems\n\n## Methods\n\n## Pitfalls\n\n## Questions\n"
        )),
        ("INDEX_pitfalls.md", {
            "kind": "l2_pitfalls_index", "created_at": now_,
        }, (
            "# L2 Pitfalls Index — All Pitfalls with Symptoms\n\n"
            "## By Symptom\n\n## By Affected Method\n\n## By Status\n"
        )),
    ]:
        p = global_l2 / "entries" / fname
        if not p.exists():
            _write_md(p, fm, body)

    return global_l2


@mcp.tool()
@require_stage
# MCP-native: writes to global L2/nodes/ — no CLI equivalent by design
def aitp_create_l2_node(
    topics_root: str,
    node_id: str,
    node_type: str,
    title: str,
    source_ref: str = "",
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
    domain: must be a valid domain from the taxonomy (see DOMAIN_TAXONOMY)
    source_ref: REQUIRED. Traceable reference to evidence (e.g. 'raw/paper.md L42-45' or 'topic:crpa-librpa/candidate:gw-correction').
        Stored for auditing but hidden from default L2 query output.
    """
    if node_type not in L2_NODE_TYPES:
        return f"Invalid node_type '{node_type}'. Valid: {L2_NODE_TYPES}"

    # Domain is open — any string is valid. VALID_DOMAINS is a suggested list.
    # New domains auto-register on first use.

    if not source_ref and not source_candidate:
        return (
            "source_ref is REQUIRED for L2 nodes. Every assertion must have provenance. "
            "Provide source_ref (e.g. 'raw/paper.md L42-45') or source_candidate "
            "(e.g. 'topic:crpa-librpa/candidate:gw-correction')."
        )

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
        "source_ref": source_ref,
        "created_at": existing_fm.get("created_at", _now()),
        "updated_at": _now(),
    }
    # Generate TF-IDF embedding for semantic search
    try:
        from brain.l2_embedding import embed_concept, encode_vector
        vec = embed_concept(title, physical_meaning)
        fm["_embedding"] = encode_vector(vec)
    except Exception:
        pass

    if source_candidate:
        fm["source_candidate"] = source_candidate

    # Preserve higher trust level if merging.
    # Multi-source confirmation: when a DIFFERENT source confirms an existing
    # node, auto-upgrade trust (Bayesian updating as evidence accumulates).
    if existing_fm:
        trust_order = ["source_grounded", "multi_source_confirmed", "validated", "independently_verified"]
        old_idx = trust_order.index(existing_fm.get("trust_basis", "source_grounded")) if existing_fm.get("trust_basis") in trust_order else 0
        new_idx = trust_order.index(fm["trust_basis"])

        # Detect multi-source confirmation: different source_ref → upgrade
        existing_refs = str(existing_fm.get("source_ref", ""))
        new_ref = str(source_ref or "")
        is_different_source = (
            new_ref
            and existing_refs
            and new_ref.strip() != existing_refs.strip()
            and not (new_ref.strip() in existing_refs or existing_refs in new_ref.strip())
        )

        if is_different_source and old_idx < 2:
            # Two independent sources → multi_source_confirmed
            fm["trust_basis"] = "multi_source_confirmed"
            fm["trust_scope"] = "bounded_reusable"
            fm["trust_upgraded_at"] = _now()
            fm["trust_upgrade_reason"] = (
                f"Confirmed by independent source: {new_ref} "
                f"(previous: {existing_refs[:80]})"
            )
            # Accumulate source references
            fm["source_ref"] = f"{existing_refs} | {new_ref}"
        elif old_idx > new_idx:
            fm["trust_basis"] = existing_fm["trust_basis"]
            fm["trust_scope"] = existing_fm.get("trust_scope", fm["trust_scope"])
            if existing_fm.get("source_ref") and source_ref:
                fm["source_ref"] = existing_fm["source_ref"]
        else:
            if existing_fm.get("source_ref") and source_ref:
                fm["source_ref"] = existing_fm["source_ref"]

    body = (
        f"# {title}\n\n"
        f"## Physical Meaning\n{physical_meaning}\n\n"
        f"## Mathematical Expression\n{mathematical_expression}\n\n"
        f"## Regime and Limits\n\n"
        f"## Derivation Chain\n\n"
        f"## Open Questions\n"
    )
    _write_md(node_path, fm, body)

    # Auto-create corresponding v5 entry for mappable node types
    _NODE_TYPE_TO_ENTRY: dict[str, str] = {
        "concept": "claim", "theorem": "claim", "result": "claim",
        "approximation": "claim", "negative_result": "claim",
        "definition": "claim", "equation": "claim",
        "assumption_card": "claim", "proof_fragment": "claim",
        "technique": "method", "open_question": "question",
    }
    if node_type in _NODE_TYPE_TO_ENTRY:
        try:
            entry_role = _NODE_TYPE_TO_ENTRY[node_type]
            entries_dir = global_l2 / "entries"
            entries_dir.mkdir(parents=True, exist_ok=True)
            entry_path = entries_dir / f"{slug}.md"
            entry_fm: dict[str, Any] = {
                "entry_id": slug,
                "role": entry_role,
                "title": title,
                "lane": [],
                "status": "unverified",
                "regime": regime_of_validity,
                "source_ref": source_ref,
                "updated": _now(),
                "version": 1,
                "created_at": _now(),
            }
            if entry_role == "claim":
                entry_fm["claim_type"] = node_type if node_type in (
                    "theorem", "result", "approximation", "negative_result",
                    "definition", "equation"
                ) else "definition"
                entry_fm["statement"] = physical_meaning
                entry_fm["mathematical_expression"] = mathematical_expression
            elif entry_role == "method":
                entry_fm["method_type"] = "analytics" if "analytic" in physical_meaning.lower() else "numerics"
            elif entry_role == "question":
                entry_fm["question_statement"] = physical_meaning
            entry_body = (
                f"# {title}\n\n"
                f"{physical_meaning}\n\n"
                f"## Relationships\n"
                f"- auto_generated_from: graph node {slug}\n"
            )
            if entry_path.exists():
                existing_efm, _ = _parse_md(entry_path)
                entry_fm["version"] = int(existing_efm.get("version", 1)) + 1
            _write_md(entry_path, entry_fm, entry_body)
            _rebuild_entry_index(global_l2)
        except Exception:
            pass  # entry creation is additive; never block graph node creation

    return f"Created L2 graph node {slug} (type={node_type}, v{fm['version']})"


@mcp.tool()
@require_stage
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
    # Multi-dimensional trust: trust_level can be a single key or
    # comma-separated list (e.g. "validated, numerical").
    # Takes the highest trust level across all specified dimensions.
    if trust_level:
        levels = trust_level.replace(" ", "").split(",")
        highest = "source_grounded"
        trust_order = list(TRUST_EVOLUTION.keys())
        for lvl in levels:
            if lvl in TRUST_EVOLUTION:
                if trust_order.index(lvl) > trust_order.index(highest):
                    highest = lvl
        fm.update(TRUST_EVOLUTION[highest])
        fm["trust_dimensions"] = levels  # record all dimensions
    fm["updated_at"] = _now()
    fm["version"] = int(fm.get("version", 1)) + 1
    _write_md(node_path, fm, body)

    # Sync update to corresponding v5 entry if it exists, with consistency checks
    warnings: list[str] = []
    try:
        entry_path = global_l2 / "entries" / f"{slug}.md"
        if entry_path.exists():
            efm, ebody = _parse_md(entry_path)
            # Cross-layer consistency checks
            node_title = str(fm.get("title", ""))
            entry_title = str(efm.get("title", ""))
            # Detect contradiction: node title contains "invalidated", "failed", etc.
            # but entry status still says "verified"
            contradiction_signals = ["incomplete", "not validated", "unverified", "failed",
                                     "did not complete", "did not finish", "did not reach"]
            any_signal = any(s in node_title.lower() or
                           s in str(fm.get("physical_meaning", "")).lower()
                           for s in contradiction_signals)
            if any_signal and efm.get("status") == "verified":
                warnings.append(
                    f"Node '{slug}' signals non-verified status but entry status is 'verified'. "
                    "Consider downgrading entry status."
                )

            if physical_meaning is not None:
                if efm.get("role") == "claim":
                    efm["statement"] = physical_meaning
                elif efm.get("role") == "question":
                    efm["question_statement"] = physical_meaning
            if mathematical_expression is not None and efm.get("role") == "claim":
                efm["mathematical_expression"] = mathematical_expression
            if regime_of_validity is not None:
                efm["regime"] = regime_of_validity
            if trust_level is not None:
                trust_to_status = {"validated": "verified", "independently_verified": "verified",
                                   "multi_source_confirmed": "consistent", "source_grounded": "unverified"}
                new_status = trust_to_status.get(highest if trust_level else "source_grounded", "unverified")
                if efm.get("status") != new_status:
                    warnings.append(
                        f"Entry status changed: '{efm.get('status')}' → '{new_status}' "
                        f"(trust: {trust_level})"
                    )
                efm["status"] = new_status
            efm["updated"] = _now()
            efm["version"] = int(efm.get("version", 1)) + 1
            _write_md(entry_path, efm, ebody)
    except Exception:
        pass

    result = f"Updated L2 node {slug} (v{fm['version']})"
    if warnings:
        result += "\n" + "\n".join(f"  [WARN] {w}" for w in warnings)
    return result


@mcp.tool()
@require_stage
def aitp_create_entry(
    topics_root: str,
    entry_id: str,
    role: str,
    title: str,
    source_ref: str,
    status: str = "unverified",
    lane: list[str] | None = None,
    regime: str = "",
    # Role-specific fields (only relevant fields for the given role are used)
    claim_type: str = "",
    statement: str = "",
    mathematical_expression: str = "",
    observable: str = "",
    evidence_type: str = "",
    system_type: str = "",
    formula_or_identifier: str = "",
    parameters: str = "",
    reference_values: str = "",
    method_type: str = "",
    toolchain: str = "",
    steps: str = "",
    compatibility: str = "",
    resource_estimate: str = "",
    symptom: str = "",
    cause: str = "",
    fix: str = "",
    affects_methods: str = "",
    question_statement: str = "",
    competing_hypotheses: str = "",
    body_content: str = "",
    relationships: str = "",
    depends_on: str = "",
) -> str:
    """Create or update a v5 faceted L2 entry.

    Entries are the primary L2 knowledge store. Five roles:
    - claim: statement about nature → use claim_type, statement, mathematical_expression, observable, evidence_type
    - system: physical system → use system_type, formula_or_identifier, parameters, reference_values
    - method: technique/workflow → use method_type, toolchain, steps, compatibility, resource_estimate
    - pitfall: known failure → use symptom, cause, fix, affects_methods
    - question: open problem → use question_statement, competing_hypotheses

    source_ref is REQUIRED. Every entry must have provenance.
    body_content: Markdown body (all sections after the frontmatter).
    relationships: text for the ## Relationships section (e.g. "- derives_from: other-entry-id").
    """
    VALID_ROLES = {"claim", "system", "method", "pitfall", "question"}
    if role not in VALID_ROLES:
        return f"Invalid role '{role}'. Valid: {sorted(VALID_ROLES)}"

    if not source_ref or not source_ref.strip():
        return "source_ref is REQUIRED for L2 entries. Every entry must have provenance."

    global_l2 = _ensure_l2_graph_dirs(topics_root)
    slug = _slugify(entry_id)
    entry_path = global_l2 / "entries" / f"{slug}.md"

    # Check for existing entry (merge scenario)
    existing_version = 0
    if entry_path.exists():
        existing_fm, _ = _parse_md(entry_path)
        existing_version = int(existing_fm.get("version", 1))

    fm: dict[str, Any] = {
        "entry_id": slug,
        "role": role,
        "title": title,
        "lane": lane or [],
        "status": status,
        "regime": regime,
        "source_ref": source_ref,
        "updated": _now(),
        "version": existing_version + 1,
        "created_at": existing_fm.get("created_at", _now()) if entry_path.exists() else _now(),
    }

    # Role-specific frontmatter
    if role == "claim":
        fm["claim_type"] = claim_type
        fm["statement"] = statement
        fm["mathematical_expression"] = mathematical_expression
        fm["observable"] = observable
        fm["evidence_type"] = evidence_type
    elif role == "system":
        fm["system_type"] = system_type
        fm["formula_or_identifier"] = formula_or_identifier
        fm["parameters"] = parameters
        if reference_values:
            fm["reference_values"] = reference_values
    elif role == "method":
        fm["method_type"] = method_type
        if toolchain:
            fm["toolchain"] = [t.strip() for t in toolchain.split(",")]
        if steps:
            fm["steps"] = [s.strip() for s in steps.split("\n") if s.strip()]
        if compatibility:
            fm["compatibility"] = compatibility
        if resource_estimate:
            fm["resource_estimate"] = resource_estimate
    elif role == "pitfall":
        fm["symptom"] = symptom
        fm["cause"] = cause
        fm["fix"] = fix
        if affects_methods:
            fm["affects_methods"] = [m.strip() for m in affects_methods.split(",")]
    elif role == "question":
        fm["question_statement"] = question_statement
        if competing_hypotheses:
            fm["competing_hypotheses"] = [h.strip() for h in competing_hypotheses.split("\n") if h.strip()]

    # Transitive dependencies (Phase 2)
    if depends_on and depends_on.strip():
        fm["depends_on_claims"] = [d.strip() for d in depends_on.split(",") if d.strip()]

    # Build body
    body = f"# {title}\n\n"
    if body_content:
        body += body_content
    else:
        if role == "claim":
            body += f"**Claim:** {statement}\n\n"
        elif role == "system":
            body += f"**Identifier:** {formula_or_identifier}\n\n"
        elif role == "method":
            body += f"**Toolchain:** {toolchain}\n\n"
        elif role == "pitfall":
            body += f"**Symptom:** {symptom}\n\n**Cause:** {cause}\n\n**Fix:** {fix}\n\n"
        elif role == "question":
            body += f"**Question:** {question_statement}\n\n"

    body += "\n## Relationships\n"
    if relationships:
        body += relationships + "\n"

    # -- Validation (Phase 1) --
    validation_messages: list[str] = []

    # Content-based dedup (only for new entries, not updates of existing)
    if not entry_path.exists():
        duplicates = _detect_duplicate_entries(global_l2, title, slug)
        if duplicates:
            dup_details = "; ".join(
                f"{d['entry_id']} (score={d['similarity']})" for d in duplicates[:3]
            )
            validation_messages.append(f"DEDUP WARNING: Similar entries exist: {dup_details}")

    # Referential integrity
    integrity_issues = _validate_entry_referential_integrity(global_l2, slug, fm, relationships or "")
    validation_messages.extend(integrity_issues)

    # Fail if blocking issues (integrity problems, not dedup warnings)
    blocking = [m for m in validation_messages if not m.startswith("DEDUP WARNING")]
    if blocking:
        return (
            f"Validation failed for entry '{slug}':\n"
            + "\n".join(f"  - {m}" for m in blocking)
            + "\n\nFix the issues above and retry."
        )

    _write_md(entry_path, fm, body)

    # Auto-update INDEX.md + reverse index
    _rebuild_entry_index(global_l2)

    result = f"Created L2 entry {slug} (role={role}, v{fm['version']})"
    if validation_messages:
        result += "\n" + "\n".join(f"  [WARN] {m}" for m in validation_messages)
    return result


def _rebuild_entry_index(global_l2: Path) -> None:
    """Rebuild L2/entries/INDEX.md, INDEX_status.md, INDEX_pitfalls.md."""
    entries_dir = global_l2 / "entries"
    if not entries_dir.is_dir():
        return

    by_role: dict[str, list[dict[str, str]]] = {}
    for ep in sorted(entries_dir.glob("*.md")):
        if ep.stem in ("INDEX", "INDEX_status", "INDEX_pitfalls"):
            continue
        fm, _ = _parse_md(ep)
        r = str(fm.get("role", "other"))
        if r not in by_role:
            by_role[r] = []
        by_role[r].append({
            "entry_id": fm.get("entry_id", ep.stem),
            "title": str(fm.get("title", "")),
            "status": str(fm.get("status", "")),
            "lane": str(fm.get("lane", [])),
        })

    now_str = _now()
    role_labels = {
        "claim": "Claims", "system": "Systems", "method": "Methods",
        "pitfall": "Pitfalls", "question": "Questions",
    }
    role_order = ["claim", "system", "method", "pitfall", "question"]

    # --- INDEX.md (full) ---
    lines = [
        "---", "catalog: entries", f"updated: \"{now_str}\"", "---",
        "", "# L2 Entries Index", "", "## By Role",
    ]
    for r in role_order:
        entries = by_role.get(r, [])
        if not entries:
            continue
        lines.append(f"\n### {role_labels.get(r, r)}")
        lines.append("| ID | Title | Status | Lane |")
        lines.append("|----|-------|--------|------|")
        for e in entries:
            lines.append(f"| {e['entry_id']} | {e['title']} | {e['status']} | {e['lane']} |")
    lines.append("\n## By Status")
    for s in ["verified", "consistent", "unverified", "failed", "conjectured"]:
        items = [e for entries in by_role.values() for e in entries if e["status"] == s]
        if items:
            lines.append(f"\n### {s.capitalize()}")
            for e in items:
                lines.append(f"- {e['entry_id']} ({e['title']})")
    lines.extend(["\n## Quick Search", "```",
        '# All verified claims',
        'grep -l "role: claim" L2/entries/*.md | xargs grep -l "status: verified"',
        "", '# Everything about system X', 'grep -l "system-<slug>" L2/entries/*.md',
        "", '# Known pitfalls', 'grep -l "role: pitfall" L2/entries/*.md',
        "", '# Open questions', 'grep -l "role: question" L2/entries/*.md',
        "```"])
    _atomic_write_text(entries_dir / "INDEX.md", "\n".join(lines) + "\n")

    # --- INDEX_status.md (verified only, quick bootstrap) ---
    verified_by_role: dict[str, list[dict[str, str]]] = {}
    for r, entries in by_role.items():
        verified = [e for e in entries if e["status"] == "verified"]
        if verified:
            verified_by_role[r] = verified
    slines = [
        "---", "catalog: entries_verified", f"updated: \"{now_str}\"", "---",
        "", "# L2 Status Index — Verified Entries Only",
        "", "Bootstrap-only index. Contains only entries with status=verified.",
    ]
    for r in role_order:
        entries = verified_by_role.get(r, [])
        if entries:
            slines.append(f"\n## {role_labels.get(r, r)}")
            for e in entries:
                slines.append(f"- {e['entry_id']}: {e['title']} [{e['lane']}]")
    if not any(verified_by_role.values()):
        slines.append("\n*No verified entries yet. Run the full L0→L4→L2 pipeline to promote claims.*")
    _atomic_write_text(entries_dir / "INDEX_status.md", "\n".join(slines) + "\n")

    # --- INDEX_pitfalls.md (all pitfalls with symptoms) ---
    pitfalls = by_role.get("pitfall", [])
    plines = [
        "---", "catalog: entries_pitfalls", f"updated: \"{now_str}\"", "---",
        "", "# L2 Pitfalls Index",
    ]
    if pitfalls:
        plines.append("\n## By Symptom")
        for e in pitfalls:
            plines.append(f"- **{e['entry_id']}**: {e['title']} [{e['status']}]")
    else:
        plines.append("\n*No pitfalls recorded yet. Use `aitp_create_entry(role=\"pitfall\")` to add one.*")
    _atomic_write_text(entries_dir / "INDEX_pitfalls.md", "\n".join(plines) + "\n")

    # --- INDEX_reverse.md (Phase 2: reverse dependency map) ---
    reverse_map: dict[str, list[str]] = {}  # entry_id -> [dependents]
    for ep in sorted(entries_dir.glob("*.md")):
        if ep.stem in ("INDEX", "INDEX_status", "INDEX_pitfalls", "INDEX_reverse"):
            continue
        efm, ebody = _parse_md(ep)
        target = efm.get("entry_id", ep.stem)
        # Collect all references from frontmatter
        deps: list[str] = []
        for field in ("depends_on_claims", "depends_on", "affects_methods"):
            val = efm.get(field, [])
            if isinstance(val, str):
                val = [v.strip() for v in val.split(",") if v.strip()]
            if isinstance(val, list):
                deps.extend([str(v).strip() for v in val])
        # Collect from relationships text
        import re
        ref_pattern = re.compile(r'[-*]\s+\w+:\s*([a-z][a-z0-9-]+)', re.IGNORECASE)
        for match in ref_pattern.finditer(ebody):
            ref_slug = match.group(1).strip()
            if ref_slug not in deps:
                deps.append(ref_slug)
        for dep in set(deps):
            if dep not in reverse_map:
                reverse_map[dep] = []
            reverse_map[dep].append(target)
    rlines = [
        "---", "catalog: entries_reverse", f"updated: \"{now_str}\"", "---",
        "", "# L2 Reverse Dependency Index",
        "", "Maps entry_id → entries that depend on it (impact analysis).",
        "", "Generated automatically by _rebuild_entry_index.", "",
    ]
    if reverse_map:
        for src in sorted(reverse_map.keys()):
            dependents = sorted(reverse_map[src])
            rlines.append(f"- **{src}** ← {', '.join(dependents)}")
    else:
        rlines.append("\n*No dependency links recorded yet.*")
    _atomic_write_text(entries_dir / "INDEX_reverse.md", "\n".join(rlines) + "\n")


# dispatch: l2 edge-create (pending CLI alignment — currently writes to global L2 vs topic subgraph)
@mcp.tool()
def aitp_create_l2_edge(
    topics_root: str,
    edge_id: str,
    from_node: str,
    to_node: str,
    edge_type: str,
    source_ref: str = "",
    regime_condition: str = "",
    evidence: str = "",
    correspondence_verified: bool = False,
) -> str:
    """Create a typed edge between two L2 graph nodes.
    TODO: align with CLI l2 edge-create (global L2 vs topic subgraph path).
    """
    from brain.cli._dispatch_helpers import dispatch
    from brain.cli.commands.l2 import cmd_l2_edge_create
    return dispatch(cmd_l2_edge_create,
        edge_id=edge_id, from_node=from_node, to_node=to_node,
        edge_type=edge_type, source_ref=source_ref,
        topics_root=topics_root,
        success_msg=f"Created L2 edge {_slugify(edge_id)} ({_slugify(from_node)} --[{edge_type}]--> {_slugify(to_node)})")


@mcp.tool()
@require_stage
def aitp_quick_l2_concept(
    topics_root: str,
    concept_id: str,
    title: str,
    domain: str,
    physical_meaning: str,
    source_ref: str,
    mathematical_expression: str = "",
    related_concepts: list[dict[str, str]] | None = None,
    node_type: str = "concept",
) -> str:
    """Lightweight: create a concept node with optional edges to related concepts in one call.

    This is the L0→L2 fast path for well-understood concepts whose relationships
    are obvious and whose source is clear. No L3 derivation required.

    related_concepts: list of {concept_id, edge_type, source_ref}
        Each entry creates an edge from this concept to the related concept.
        The related concept must already exist in L2.
    """
    # Create the concept node
    result = aitp_create_l2_node(
        topics_root=topics_root,
        node_id=concept_id,
        node_type=node_type,
        title=title,
        domain=domain,
        physical_meaning=physical_meaning,
        mathematical_expression=mathematical_expression,
        source_ref=source_ref,
    )

    if related_concepts:
        edge_results = []
        for i, rel in enumerate(related_concepts):
            edge_id = f"{concept_id}--{rel.get('concept_id', '')}"
            edge_type = rel.get("edge_type", "uses")
            edge_src = rel.get("source_ref", source_ref)
            to_node = rel.get("concept_id", "")
            if not to_node:
                edge_results.append(f"[SKIP rel {i}: missing concept_id]")
                continue
            er = aitp_create_l2_edge(
                topics_root=topics_root,
                edge_id=edge_id,
                from_node=concept_id,
                to_node=to_node,
                edge_type=edge_type,
                source_ref=edge_src,
            )
            edge_results.append(er)

        return (
            f"{result}\n"
            + "\n".join(edge_results)
        )

    return result


@mcp.tool()
def aitp_get_l2_provenance(
    topics_root: str,
    node_id: str,
) -> dict[str, Any]:
    """Get the full provenance of an L2 entry, graph node, or promoted candidate.

    Use this for auditing — verify where a claim came from before trusting it.
    Searches three sources in order: v5 entries, graph nodes, promoted candidates.
    Default L2 queries hide source fields to prevent context bloat.
    """
    global_l2 = _global_l2_path(topics_root)
    slug = _slugify(node_id)

    # Try v5 entry first (primary knowledge store)
    entry_path = global_l2 / "entries" / f"{slug}.md"
    if entry_path.exists():
        fm, body = _parse_md(entry_path)
        return {
            "node_id": fm.get("entry_id", slug),
            "title": fm.get("title", ""),
            "type": fm.get("role", "") + (f"/{fm.get('claim_type', '')}" if fm.get("claim_type") else ""),
            "trust_basis": fm.get("status", ""),
            "trust_scope": fm.get("regime", ""),
            "source_ref": fm.get("source_ref", ""),
            "source_candidate": "",
            "source_topic": "",
            "version": fm.get("version", 1),
            "created_at": fm.get("created_at", fm.get("updated", "")),
            "updated_at": fm.get("updated", ""),
            "body_preview": body[:2000],
            "source": "v5_entry",
        }

    # Try graph node (legacy)
    node_path = global_l2 / "graph" / "nodes" / f"{slug}.md"
    if node_path.exists():
        fm, body = _parse_md(node_path)
        return {
            "node_id": fm.get("node_id", slug),
            "title": fm.get("title", ""),
            "type": fm.get("type", ""),
            "trust_basis": fm.get("trust_basis", ""),
            "trust_scope": fm.get("trust_scope", ""),
            "source_ref": fm.get("source_ref", ""),
            "source_candidate": fm.get("source_candidate", ""),
            "source_topic": fm.get("source_topic", ""),
            "version": fm.get("version", 1),
            "created_at": fm.get("created_at", ""),
            "updated_at": fm.get("updated_at", ""),
            "body_preview": body[:2000],
            "source": "graph_node",
        }

    # Try promoted candidate
    cand_path = global_l2 / f"{slug}.md"
    if cand_path.exists():
        fm, body = _parse_md(cand_path)
        return {
            "node_id": fm.get("candidate_id", slug),
            "title": fm.get("title", ""),
            "type": str(fm.get("candidate_type", "research_claim")),
            "trust_basis": fm.get("trust_basis", ""),
            "trust_scope": fm.get("trust_scope", ""),
            "source_ref": fm.get("source_ref", ""),
            "source_candidate": slug,
            "source_topic": str(fm.get("source_topic", "")),
            "version": fm.get("version", 1),
            "created_at": fm.get("promoted_at", ""),
            "updated_at": fm.get("promoted_at", ""),
            "body_preview": body[:2000],
            "source": "promoted_candidate",
        }

    return {"error": f"'{slug}' not found in L2 entries, graph nodes, or promoted candidates."}


@mcp.tool()
def aitp_query_impact(
    topics_root: str,
    entry_id: str,
) -> dict[str, Any]:
    """Query the transitive impact of changing an entry's status.

    Given an entry_id, returns all entries that directly or transitively depend
    on it (via depends_on_claims, verified_by, derives_from relationships).
    Use this BEFORE downgrading a claim to understand what might break.
    """
    global_l2 = _global_l2_path(topics_root)
    slug = _slugify(entry_id)

    # Load reverse index
    reverse_path = global_l2 / "entries" / "INDEX_reverse.md"
    reverse_map: dict[str, list[str]] = {}
    if reverse_path.exists():
        import re
        text = reverse_path.read_text(encoding="utf-8")
        for line in text.split("\n"):
            match = re.match(r'- \*\*([^*]+)\*\* ← (.+)', line)
            if match:
                src = match.group(1).strip()
                deps = [d.strip() for d in match.group(2).split(",")]
                reverse_map[src] = deps

    # Breadth-first transitive closure
    visited: set[str] = set()
    queue: list[str] = [slug]
    direct: list[str] = []
    indirect: list[str] = []

    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        if current == slug:
            continue
        # Classify as direct or indirect
        if current in reverse_map.get(slug, []):
            direct.append(current)
        else:
            indirect.append(current)
        # Enqueue dependents
        for dep in reverse_map.get(current, []):
            if dep not in visited:
                queue.append(dep)

    # Load entry details for affected entries
    affected: list[dict[str, Any]] = []
    entries_dir = global_l2 / "entries"
    for affected_slug in direct + indirect:
        ep = entries_dir / f"{affected_slug}.md"
        if ep.exists():
            fm, _ = _parse_md(ep)
            affected.append({
                "entry_id": affected_slug,
                "title": fm.get("title", ""),
                "role": fm.get("role", ""),
                "status": fm.get("status", ""),
                "distance": 1 if affected_slug in direct else 2,
            })

    # Also explain what the queried entry depends on
    ep = entries_dir / f"{slug}.md"
    upstream: list[str] = []
    if ep.exists():
        fm, _ = _parse_md(ep)
        for field in ("depends_on_claims", "depends_on"):
            val = fm.get(field, [])
            if isinstance(val, str):
                val = [v.strip() for v in val.split(",") if v.strip()]
            if isinstance(val, list):
                upstream.extend([str(v).strip() for v in val])

    return {
        "entry_id": slug,
        "depends_on": upstream,
        "direct_dependents": direct,
        "indirect_dependents": indirect,
        "total_affected": len(direct) + len(indirect),
        "affected_entries": affected,
        "authority_level": "L2_impact_analysis",
    }


@mcp.tool()
@require_stage
def aitp_record_numerical_result(
    topics_root: str,
    entry_id: str,
    observable: str,
    value: float,
    source_ref: str,
    uncertainty: float = 0.0,
    units: str = "",
    method_used: str = "",
    system: str = "",
    comment: str = "",
) -> str:
    """Record a numerical result on an existing L2 entry.

    Adds a structured numerical_results field to the entry frontmatter.
    The entry can be any role — claim entries are most common for results,
    but system entries can also store reference values.

    value: the numerical value (float)
    uncertainty: ± uncertainty (default 0 = exact)
    units: physical units (e.g. "eV", "meV", "Bohr")
    method_used: entry_id of the method that produced this result
    """
    global_l2 = _ensure_l2_graph_dirs(topics_root)
    slug = _slugify(entry_id)
    entry_path = global_l2 / "entries" / f"{slug}.md"

    if not entry_path.exists():
        return f"Entry '{slug}' not found. Create it first with aitp_create_entry."

    fm, body = _parse_md(entry_path)

    # Build numerical result record
    record: dict[str, Any] = {
        "observable": observable,
        "value": value,
        "uncertainty": uncertainty,
        "units": units,
        "source_ref": source_ref,
        "recorded_at": _now(),
    }
    if method_used:
        record["method_used"] = method_used
    if system:
        record["system"] = system
    if comment:
        record["comment"] = comment

    # Append to existing numerical_results or create new list
    existing_results = fm.get("numerical_results", [])
    if not isinstance(existing_results, list):
        existing_results = []
    existing_results.append(record)
    fm["numerical_results"] = existing_results
    fm["updated"] = _now()
    fm["version"] = int(fm.get("version", 1)) + 1

    # Update body if not already present
    if "## Numerical Results" not in body:
        body += "\n## Numerical Results\n\n"

    # Append result to body
    result_line = f"- {observable}: {value}"
    if uncertainty:
        result_line += f" ± {uncertainty}"
    if units:
        result_line += f" {units}"
    if method_used:
        result_line += f" (method: {method_used})"
    result_line += f" [{source_ref}]"
    body += result_line + "\n"

    _write_md(entry_path, fm, body)
    _rebuild_entry_index(global_l2)

    return f"Recorded numerical result on '{slug}': {observable} = {value}{' ± ' + str(uncertainty) if uncertainty else ''}{' ' + units if units else ''}"


@mcp.tool()
def aitp_find_cross_topic_bridges(
    topics_root: str,
) -> dict[str, Any]:
    """Find cross-topic knowledge bridges in the L2 entries catalog.

    Scans all entries for shared concepts across topics/domains:
    - Same observable (e.g. both topics measure "band gap")
    - Similar methods (e.g. both use "Green's function")
    - Same system_type or regime
    - Shared mathematical expressions or concepts

    Returns bridge candidates — pairs of entries that could be connected.
    """
    global_l2 = _global_l2_path(topics_root)
    entries_dir = global_l2 / "entries"
    if not entries_dir.is_dir():
        return {"bridges": [], "count": 0, "message": "No entries directory found."}

    # Load all entries with their key fields
    entries: list[dict[str, Any]] = []
    for ep in sorted(entries_dir.glob("*.md")):
        if ep.stem.startswith("INDEX"):
            continue
        fm, body = _parse_md(ep)
        entries.append({
            "entry_id": fm.get("entry_id", ep.stem),
            "title": str(fm.get("title", "")),
            "role": str(fm.get("role", "")),
            "observable": str(fm.get("observable", "")),
            "system_type": str(fm.get("system_type", "")),
            "method_type": str(fm.get("method_type", "")),
            "regime": str(fm.get("regime", "")),
            "body": body[:500],
            "source_ref": str(fm.get("source_ref", "")),
        })

    bridges: list[dict[str, Any]] = []

    # Bridge type 1: Shared observable
    observables: dict[str, list[str]] = {}
    for e in entries:
        obs = e["observable"].strip().lower()
        if obs:
            observables.setdefault(obs, []).append(e["entry_id"])
    for obs, ids in observables.items():
        if len(ids) >= 2:
            # Check they come from different topics
            sources = [e["source_ref"] for e in entries if e["entry_id"] in ids]
            if len(set(sources)) >= 2:
                bridges.append({
                    "type": "shared_observable",
                    "observable": obs,
                    "entries": ids,
                })

    # Bridge type 2: Shared method type
    methods: dict[str, list[str]] = {}
    for e in entries:
        mt = e["method_type"].strip().lower()
        if mt:
            methods.setdefault(mt, []).append(e["entry_id"])
    for mt, ids in methods.items():
        if len(ids) >= 2:
            sources = [e["source_ref"] for e in entries if e["entry_id"] in ids and e["source_ref"]]
            if len(set(sources)) >= 2:
                bridges.append({
                    "type": "shared_method",
                    "method_type": mt,
                    "entries": ids,
                })

    # Bridge type 3: Shared regime
    regimes: dict[str, list[str]] = {}
    for e in entries:
        reg = e["regime"].strip().lower()
        if reg and len(reg) > 5:
            # Use key phrases for matching
            for keyword in ["weak coupling", "strong coupling", "periodic solids",
                           "low energy", "high temperature", "2d", "3d", "q→0",
                           "long-wavelength", "topological", "strongly correlated"]:
                if keyword in reg:
                    regimes.setdefault(keyword, []).append(e["entry_id"])
    for reg, ids in regimes.items():
        if len(ids) >= 2:
            bridges.append({
                "type": "shared_regime",
                "regime_keyword": reg,
                "entries": ids,
            })

    # Deduplicate bridges
    seen = set()
    unique_bridges = []
    for b in bridges:
        key = (b["type"], tuple(sorted(b["entries"])))
        if key not in seen:
            seen.add(key)
            unique_bridges.append(b)

    # Update L2/index.md cross-topic bridges section
    try:
        index_path = global_l2 / "index.md"
        if index_path.exists():
            idx_text = index_path.read_text(encoding="utf-8")
            bridge_start = idx_text.find("## Cross-Topic Bridges")
            bridge_section = "\n## Cross-Topic Bridges\n\n"
            if unique_bridges:
                for b in unique_bridges[:10]:
                    bridge_section += f"- **{b['type']}**: {', '.join(b['entries'][:4])}\n"
            else:
                bridge_section += "*None detected yet.*\n"
            if bridge_start != -1:
                idx_text = idx_text[:bridge_start] + bridge_section
            else:
                idx_text = idx_text.rstrip() + "\n" + bridge_section
            _atomic_write_text(index_path, idx_text)
    except Exception:
        pass

    return {
        "bridges": unique_bridges,
        "count": len(unique_bridges),
        "authority_level": "L2_cross_topic",
    }


@mcp.tool()
@require_stage
def aitp_create_diagram(
    topics_root: str,
    diagram_id: str,
    title: str,
    what_it_shows: str = "",
    related_nodes: list[str] | None = None,
    related_edges: list[str] | None = None,
    source_ref: str = "",
    source_file: str = "",
) -> str:
    """Register a figure or diagram from the literature in L2.

    Diagrams are evidence attachments  --  they hang on nodes and edges, not
    enter the force graph as independent entities.

    what_it_shows: plain-language description of what the figure shows.
        Write this so that both a human and an AI can understand the
        physical content without needing to actually see the image.
        Include: key visual elements, physical interpretation,
        why this figure matters.

    related_nodes: list of L2 node_ids this figure supports.
    related_edges: list of L2 edge_ids this figure supports.
    source_ref: human-readable citation (e.g. "Hedin 1965, Fig. 1")
    source_file: path relative to L2/images/ for the image file.
    """
    global_l2 = _ensure_l2_graph_dirs(topics_root)
    slug = _slugify(diagram_id)
    diagrams_dir = global_l2 / "graph" / "diagrams"
    diagrams_dir.mkdir(parents=True, exist_ok=True)
    diagram_path = diagrams_dir / f"{slug}.md"

    fm: dict[str, Any] = dict(DIAGRAM_TEMPLATE)
    fm.update({
        "diagram_id": slug,
        "title": title,
        "what_it_shows": what_it_shows,
        "related_nodes": related_nodes or [],
        "related_edges": related_edges or [],
        "source_ref": source_ref,
        "source_file": source_file,
        "created_at": _now(),
        "updated_at": _now(),
    })

    body = (
        f"# {title}\n\n"
        f"## What This Figure Shows\n{what_it_shows}\n\n"
        f"## Source\n{source_ref}\n"
    )
    _write_md(diagram_path, fm, body)
    return (
        f"Created L2 diagram {slug}. "
        f"Linked to {len(related_nodes or [])} nodes, {len(related_edges or [])} edges."
    )


@mcp.tool()
def aitp_list_diagrams(
    topics_root: str,
    related_node: str = "",
) -> list[dict[str, Any]]:
    """List diagrams, optionally filtered by related node."""
    global_l2 = _global_l2_path(topics_root)
    diagrams_dir = global_l2 / "graph" / "diagrams"
    if not diagrams_dir.is_dir():
        return []

    results = []
    for dp in sorted(diagrams_dir.glob("*.md")):
        fm, _ = _parse_md(dp)
        if related_node and related_node not in (fm.get("related_nodes") or []):
            continue
        results.append({
            "diagram_id": fm.get("diagram_id", dp.stem),
            "title": fm.get("title", dp.stem),
            "what_it_shows": (fm.get("what_it_shows") or "")[:300],
            "related_nodes": fm.get("related_nodes", []),
            "related_edges": fm.get("related_edges", []),
            "source_ref": fm.get("source_ref", ""),
        })
    return results


@mcp.tool()
@with_preflight("derive-record")
@require_stage
def aitp_create_derivation_step(
    topics_root: str,
    step_id: str,
    chain_id: str,
    order: int,
    input_expr: str,
    output_expr: str,
    transform: str = "",
    justification_type: str = "",
    justification_detail: str = "",
    depends_on_steps: list[str] | None = None,
    depends_on_nodes: list[str] | None = None,
    approximation: str = "",
    regime_condition: str = "",
    source_ref: str = "",
    rigor_level: str = "",
    gap_marker: str = "",
) -> str:
    """Create a derivation step in the L2 knowledge graph  --  a first-class entity.

    Steps form a DAG within a derivation chain (chain_id groups them).
    Each step records: what came in, what transform was applied,
    what came out, why the transform is valid, and what it depends on.

    justification_type: definition | theorem | approximation |
        physical_principle | algebraic_identity | limit | assumption |
        conjecture | gap | numerical_evidence
    rigor_level: rigorous (full proof) | heuristic (physical reasoning) |
        handwaving (\"it can be shown\") | conjectured (not yet proven)
    gap_marker: non-empty = this step is an acknowledged gap in the derivation.
        Describe what is missing and what would fill it.
    depends_on_steps: list of step_ids this step requires (DAG edges)
    depends_on_nodes: list of L2 node_ids this step invokes
    source_ref: traceable reference to source (e.g. \"Hedin 1965, Eq. 13\")
    """
    if justification_type and justification_type not in JUSTIFICATION_TYPES:
        return f"Invalid justification_type '{justification_type}'. Valid: {JUSTIFICATION_TYPES}"

    # Detect lane from state.md to set lane-appropriate validation
    # Note: derivation steps are global (not topic-scoped), so we check
    # the resolved topics directory rather than an individual topic.
    base = topics_dir(topics_root)
    lane = "unspecified"
    state_path = base / "state.md"
    if state_path.exists():
        state_fm, _ = _parse_md(state_path)
        lane = str(state_fm.get("lane", "unspecified")).strip()

    global_l2 = _ensure_l2_graph_dirs(topics_root)
    slug = _slugify(step_id)
    steps_dir = global_l2 / "graph" / "steps"
    steps_dir.mkdir(parents=True, exist_ok=True)
    step_path = steps_dir / f"{slug}.md"

    fm: dict[str, Any] = dict(STEP_TEMPLATE)
    fm.update({
        "step_id": slug,
        "chain_id": chain_id,
        "order": order,
        "input_expr": input_expr,
        "output_expr": output_expr,
        "transform": transform,
        "justification_type": justification_type,
        "justification_detail": justification_detail,
        "rigor_level": rigor_level,
        "gap_marker": gap_marker,
        "depends_on_steps": depends_on_steps or [],
        "depends_on_nodes": depends_on_nodes or [],
        "approximation": approximation,
        "regime_condition": regime_condition,
        "source_ref": source_ref,
        "lane": lane,
        "created_at": _now(),
        "updated_at": _now(),
    })

    # Lane-specific validation: code_method uses source anchoring instead of SymPy
    if lane == "code_method" and source_ref:
        fm["validation_status"] = "source_anchored"
        fm["validation_note"] = (
            "code_method lane: source anchoring at file:line is the primary verification. "
            "Numerical verification required at L4 (compile + run + compare output)."
        )
    elif lane in ("toy_numeric",):
        fm["validation_status"] = "pending_numerical"

    body = (
        f"# Step {order}: {slug}\n\n"
        f"## Input\n{input_expr}\n\n"
        f"## Transform\n{transform}\n\n"
        f"## Output\n{output_expr}\n\n"
        f"## Justification\n{justification_type}: {justification_detail}\n\n"
        f"## Approximation\n{approximation}\n\n"
        f"## Regime Condition\n{regime_condition}\n\n"
        f"## Source\n{source_ref}\n"
    )
    _write_md(step_path, fm, body)

    deps_info = ""
    if depends_on_steps:
        deps_info += f" depends on steps: {depends_on_steps}"
    if depends_on_nodes:
        deps_info += f" depends on nodes: {depends_on_nodes}"

    return f"Created derivation step {slug} (chain={chain_id}, order={order}).{deps_info}"


@mcp.tool()
def aitp_list_steps(
    topics_root: str,
    chain_id: str = "",
) -> list[dict[str, Any]]:
    """List derivation steps, optionally filtered by chain_id. Returns in order."""
    global_l2 = _global_l2_path(topics_root)
    steps_dir = global_l2 / "graph" / "steps"
    if not steps_dir.is_dir():
        return []

    results = []
    for sp in sorted(steps_dir.glob("*.md")):
        fm, _ = _parse_md(sp)
        if chain_id and fm.get("chain_id") != chain_id:
            continue
        results.append({
            "step_id": fm.get("step_id", sp.stem),
            "chain_id": fm.get("chain_id", ""),
            "order": fm.get("order", 0),
            "input_expr": fm.get("input_expr", ""),
            "output_expr": fm.get("output_expr", ""),
            "transform": fm.get("transform", ""),
            "justification_type": fm.get("justification_type", ""),
            "depends_on_steps": fm.get("depends_on_steps", []),
            "depends_on_nodes": fm.get("depends_on_nodes", []),
            "approximation": fm.get("approximation", ""),
            "source_ref": fm.get("source_ref", ""),
        })

    results.sort(key=lambda s: s["order"])
    return results


@mcp.tool()
def aitp_traverse_derivation(
    topics_root: str,
    chain_id: str,
) -> dict[str, Any]:
    """Traverse a derivation chain's DAG from first step to last.

    Returns steps in topological order with dependency information,
    making the derivation traceable by both human and AI.
    """
    steps = aitp_list_steps(topics_root, chain_id=chain_id)

    if not steps:
        return {"chain_id": chain_id, "steps": [], "message": "No steps found."}

    # Build node lookup for depends_on_nodes
    global_l2 = _global_l2_path(topics_root)
    nodes_dir = global_l2 / "graph" / "nodes"
    node_titles = {}
    if nodes_dir.is_dir():
        for np in nodes_dir.glob("*.md"):
            nfm, _ = _parse_md(np)
            node_titles[np.stem] = nfm.get("title", np.stem)

    enriched = []
    for s in steps:
        deps = {
            "steps": s["depends_on_steps"],
            "concepts": {nid: node_titles.get(nid, nid) for nid in s["depends_on_nodes"]},
        }
        enriched.append({
            "order": s["order"],
            "step_id": s["step_id"],
            "input": s["input_expr"],
            "transform": s["transform"],
            "output": s["output_expr"],
            "justification": f"{s['justification_type']}: {s.get('approximation', '')}",
            "depends_on": deps,
            "source": s["source_ref"],
        })

    return {
        "chain_id": chain_id,
        "total_steps": len(steps),
        "steps": enriched,
    }


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

    Reads from canonical L2/entries/ (nodes) and reconstructs edges from
    entry relationships. Falls back to graph/ for legacy nodes and towers.
    """
    global_l2 = _global_l2_path(topics_root)
    entries_dir = global_l2 / "entries"
    nodes_dir = global_l2 / "graph" / "nodes"
    edges_dir = global_l2 / "graph" / "edges"

    # Node search: entries first (canonical), then graph nodes (legacy)
    nodes = []
    roles_seen: set[str] = set()

    if entries_dir.is_dir():
        for ep in sorted(entries_dir.glob("*.md")):
            if ep.stem.startswith("INDEX"):
                continue
            fm, body = _parse_md(ep)
            entry_role = str(fm.get("role", ""))
            # Filter by node_type → maps to entry role
            if node_type and entry_role != node_type:
                continue
            if query:
                q_fields = [
                    str(fm.get("title", "")),
                    str(fm.get("statement", "")),
                    str(fm.get("mathematical_expression", "")),
                    body,
                ]
                score = semantic_score(query, q_fields)
                if score < 0.15:
                    continue
            else:
                score = 1.0
            node_id = fm.get("entry_id", ep.stem)
            roles_seen.add(node_id)
            nodes.append({
                "node_id": node_id,
                "title": fm.get("title", ""),
                "type": entry_role,
                "tower": "",
                "regime_of_validity": fm.get("regime", ""),
                "trust_basis": fm.get("status", ""),
                "trust_scope": fm.get("regime", ""),
                "version": fm.get("version", 1),
                "mathematical_expression": fm.get("mathematical_expression", ""),
                "relevance": round(score, 3),
            })

    # Fallback: also scan graph nodes for entries not yet represented
    if nodes_dir.is_dir():
        for np in sorted(nodes_dir.glob("*.md")):
            fm, body = _parse_md(np)
            nid = fm.get("node_id", np.stem)
            if nid in roles_seen:
                continue  # entry already covers this
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
                "node_id": nid,
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

    # Edge search: from graph edges + reconstructed from entry relationships
    edges = []
    import re
    if entries_dir.is_dir():
        for ep in sorted(entries_dir.glob("*.md")):
            if ep.stem.startswith("INDEX"):
                continue
            fm, body = _parse_md(ep)
            from_id = fm.get("entry_id", ep.stem)
            # Parse relationships: "- edge_type: target_id"
            rel_section = body.find("## Relationships")
            if rel_section != -1:
                rel_text = body[rel_section:]
                for match in re.finditer(r'[-*]\s+(\w+)\s*:\s*([a-z][a-z0-9-]+)', rel_text):
                    rel_type = match.group(1)
                    to_id = match.group(2).strip()
                    if from_node and _slugify(from_node) not in (from_id, to_id):
                        continue
                    if edge_type and rel_type != edge_type:
                        continue
                    edges.append({
                        "edge_id": f"{from_id}--{rel_type}--{to_id}",
                        "from_node": from_id,
                        "to_node": to_id,
                        "type": rel_type,
                        "regime_condition": "",
                        "correspondence_verified": False,
                        "source": "entry_relationship",
                    })

    # Also include graph edges for legacy coverage
    if edges_dir.is_dir():
        for ep in sorted(edges_dir.glob("*.md")):
            efm, _ = _parse_md(ep)
            eid = efm.get("edge_id", ep.stem)
            if any(e["edge_id"] == eid for e in edges):
                continue  # Already captured from entry relationships
            if edge_type and efm.get("type") != edge_type:
                continue
            if from_node:
                fn = _slugify(from_node)
                if efm.get("from_node") != fn and efm.get("to_node") != fn:
                    continue
            edges.append({
                "edge_id": eid,
                "from_node": efm.get("from_node", ""),
                "to_node": efm.get("to_node", ""),
                "type": efm.get("type", ""),
                "regime_condition": efm.get("regime_condition", ""),
                "correspondence_verified": efm.get("correspondence_verified", False),
                "source": "graph_edge",
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
@require_stage
# MCP-native: bulk merge to global L2 — no CLI equivalent by design
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
@require_stage
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


def _auto_refresh_flow_notebook(root: Path, fm: dict) -> None:
    """Silently regenerate flow_notebook.tex at topic root.

    Only triggered on candidate submission (end of each L3→L4 cycle).
    Uses the section-based builder for incremental regeneration.
    Never blocks — errors are ignored.
    """
    try:
        from brain.flow_notebook import build_notebook
        tex_content, _regenerated = build_notebook(root)
        _atomic_write_text(root / "flow_notebook.tex", tex_content)
    except Exception:
        pass  # Never block normal operations


@mcp.tool()
def aitp_generate_flow_notebook(
    topics_root: str,
    topic_slug: str,
    force_full: bool = False,
) -> dict[str, Any]:
    """Generate or regenerate the flow notebook at the topic root.

    Uses the section-based template builder. By default, only sections
    whose source artifacts changed are regenerated (incremental).
    Pass force_full=True to rebuild all sections.

    The notebook is written to <topic_root>/flow_notebook.tex and is
    designed for human reading — AI should polish it after generation.

    Args:
        topics_root: Path to the topics root directory.
        topic_slug: Topic identifier.
        force_full: If True, force a full rebuild of all sections.
    """
    root = _topic_root(topics_root, topic_slug)
    from brain.flow_notebook import build_notebook, SECTION_ORDER
    tex_content, regenerated = build_notebook(root, force_full=force_full)
    _atomic_write_text(root / "flow_notebook.tex", tex_content)

    _append_to_topic_log(root, "generated flow_notebook.tex")

    return {
        "message": f"flow_notebook.tex written to topic root",
        "path": str(root / "flow_notebook.tex"),
        "size_bytes": len(tex_content),
        "sections_regenerated": regenerated,
        "sections_included": SECTION_ORDER,
    }


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

    # Count entries for metadata even though graph visualization focuses on nodes
    entries_dir = global_l2 / "entries"
    entry_count = 0
    if entries_dir.is_dir():
        entry_count = sum(1 for ep in entries_dir.glob("*.md") if ep.stem != "INDEX")

    if not nodes_dir.exists() or not any(nodes_dir.iterdir()):
        return {
            "ascii": "(empty graph)" if entry_count == 0 else f"(empty graph — {entry_count} v5 entries exist, use aitp_query_entries to search)",
            "metadata": {"node_count": 0, "edge_count": 0, "entry_count": entry_count},
        }

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
            "entry_count": entry_count,
            "conflict_count": len(conflicts),
            "missing_correspondence": len(missing_correspondence),
            "type_counts": {t: len(ns) for t, ns in by_type.items()},
        },
    }


# ---------------------------------------------------------------------------
# Experimental proposal — falsification-driven physics
# ---------------------------------------------------------------------------


@mcp.tool()
def aitp_propose_experiment(
    topics_root: str,
    topic_slug: str,
    candidate_id: str = "",
    claim: str = "",
    regime: str = "",
) -> dict[str, Any]:
    """Propose a falsifiable experimental/numerical test for a claim.

    Given a claim (from a candidate or free text), this tool asks the agent to
    reason about what measurement or computation would test it, under what
    conditions, and what result would falsify it. The output is recorded as
    a structured proposal in L4/proposals/.

    This is the physicist's core skill: not just verifying what was derived,
    but designing the test that could prove it wrong.
    """
    root = _topic_root(topics_root, topic_slug)
    proposals_dir = root / "L4" / "proposals"
    proposals_dir.mkdir(parents=True, exist_ok=True)

    # If candidate_id given, read claim from candidate
    if candidate_id and not claim:
        cand_path = root / "L3" / "candidates" / f"{_slugify(candidate_id)}.md"
        if cand_path.exists():
            cfm, _ = _parse_md(cand_path)
            claim = str(cfm.get("claim", ""))
            if not regime:
                regime = str(cfm.get("regime_of_validity", ""))

    if not claim.strip():
        return {
            "message": (
                "Provide a claim (directly or via candidate_id) to design "
                "an experimental proposal around."
            ),
        }

    proposal_id = _slugify(claim[:60])
    proposal_path = proposals_dir / f"{proposal_id}.md"

    fm = {
        "artifact_kind": "l4_experimental_proposal",
        "proposal_id": proposal_id,
        "claim": claim,
        "regime": regime,
        "candidate_id": candidate_id,
        "created_at": _now(),
    }

    body = (
        f"# Experimental Proposal: {claim[:80]}\n\n"
        f"## Claim Under Test\n{claim}\n\n"
        f"## Physical Regime\n{regime or '(unspecified)'}\n\n"
        f"## Proposed Measurement\n\n"
        f"What should be measured? Specify the observable, the system, "
        f"and the experimental or computational setup.\n\n"
        f"## Predicted Outcome (if claim is correct)\n\n"
        f"What value / signature / behavior is expected if the claim holds?\n\n"
        f"## Falsification Condition\n\n"
        f"What result would FALSIFY the claim? Be specific: "
        f"'if X < 0.5 meV' or 'if the spectral function shows a gap above 2 eV'.\n"
        f"A claim that cannot be falsified is not physics.\n\n"
        f"## Feasibility Assessment\n\n"
        f"Is this measurement/computation feasible with current methods? "
        f"If not, what would be needed?\n\n"
        f"## Existing Constraints\n\n"
        f"What do we already know from prior experiments or computations? "
        f"Does existing data already rule this claim out?\n\n"
        f"## Status\npending — agent must fill the sections above\n"
    )

    _write_md(proposal_path, fm, body)
    _append_to_topic_log(
        root,
        f"experimental proposal created for claim '{claim[:60]}'",
    )

    return _GateResult({
        "message": (
            f"Experimental proposal template created: {proposal_id}\n\n"
            f"Claim: {claim[:120]}\n"
            f"Regime: {regime or '(unspecified)'}\n\n"
            f"Fill the proposal sections: Proposed Measurement, "
            f"Predicted Outcome, Falsification Condition, "
            f"Feasibility Assessment, Existing Constraints.\n\n"
            f"REMINDER: A claim that cannot be falsified is not physics. "
            f"If you cannot think of a measurement or computation that "
            f"would prove the claim wrong, the claim may be ill-posed."
        ),
    })


@mcp.tool()
def aitp_find_cross_topic_bridges(
    topics_root: str,
    topic_slug: str = "",
    expression: str = "",
    concept_name: str = "",
) -> dict[str, Any]:
    """Search for structural isomorphisms across topics in L2.

    Given a mathematical expression or concept name, scans L2 across all
    domains and topics to find similar structures. A Green's function in
    condensed matter may have the same form as a propagator in QFT —
    this tool flags these deep connections.

    Args:
        topic_slug: If given, uses this topic's candidates/claims as the source.
        expression: A LaTeX mathematical expression to search for.
        concept_name: A physics concept name to search for.
    """
    global_l2 = _global_l2_path(topics_root)
    nodes_dir = global_l2 / "graph" / "nodes"
    edges_dir = global_l2 / "graph" / "edges"

    if not nodes_dir.is_dir():
        return {"bridges": [], "message": "L2 graph is empty."}

    # Collect source references if a topic is given
    source_expressions: list[str] = []
    source_concepts: list[str] = []

    if topic_slug:
        root = _topic_root(topics_root, topic_slug)
        cand_dir = root / "L3" / "candidates"
        if cand_dir.is_dir():
            for cp in cand_dir.glob("*.md"):
                cfm, _ = _parse_md(cp)
                claim = str(cfm.get("claim", ""))
                if claim:
                    source_concepts.append(claim[:200])
        # Also check L1 intake for concepts
        intake_dir = root / "L1" / "intake"
        if intake_dir.is_dir():
            for ip in intake_dir.rglob("*.md"):
                ifm, _ = _parse_md(ip)
                eqs = str(ifm.get("equations_found", ""))
                if eqs:
                    source_expressions.append(eqs[:300])

    if expression:
        source_expressions.append(expression)
    if concept_name:
        source_concepts.append(concept_name)

    if not source_expressions and not source_concepts:
        return {
            "bridges": [],
            "message": (
                "Provide a topic_slug, expression, or concept_name to search "
                "for cross-topic bridges."
            ),
        }

    # Scan all L2 nodes for structural similarity
    bridges = []
    for np in sorted(nodes_dir.glob("*.md")):
        fm, body = _parse_md(np)
        node_expr = str(fm.get("mathematical_expression", ""))
        node_meaning = str(fm.get("physical_meaning", ""))
        node_title = str(fm.get("title", ""))
        node_domain = str(fm.get("domain", ""))
        node_id = fm.get("node_id", np.stem)

        # Check expression similarity via LaTeX normalization
        for src_expr in source_expressions:
            if src_expr and node_expr:
                src_norm = normalize_latex(src_expr)
                node_norm = normalize_latex(node_expr)
                if src_norm and node_norm:
                    # Check for shared LaTeX commands as structural signature
                    src_cmds = set(re.findall(r'\\([a-zA-Z]+)', src_norm))
                    node_cmds = set(re.findall(r'\\([a-zA-Z]+)', node_norm))
                    shared = src_cmds & node_cmds
                    if len(shared) >= 2:
                        bridges.append({
                            "node_id": node_id,
                            "title": node_title,
                            "domain": node_domain,
                            "bridge_type": "mathematical_structure",
                            "shared_structures": sorted(shared),
                            "note": (
                                f"Shared LaTeX structures: {sorted(shared)}. "
                                f"Check if this is a deep correspondence or "
                                f"coincidental notation."
                            ),
                        })

        # Check concept similarity via semantic scoring
        for src_concept in source_concepts:
            if src_concept:
                score = semantic_score(
                    src_concept,
                    [node_title, node_meaning, body[:500]],
                )
                if score > 0.3 and node_domain:
                    bridges.append({
                        "node_id": node_id,
                        "title": node_title,
                        "domain": node_domain,
                        "bridge_type": "conceptual_similarity",
                        "similarity": round(score, 3),
                        "note": (
                            f"Conceptual similarity score {score:.2f}. "
                            f"Consider whether the same physics appears "
                            f"in a different regime."
                        ),
                    })

    # Also scan v5 entries for structural similarity
    entries_dir = global_l2 / "entries"
    if entries_dir.is_dir():
        for ep in sorted(entries_dir.glob("*.md")):
            if ep.stem == "INDEX":
                continue
            fm, body = _parse_md(ep)
            entry_expr = str(fm.get("mathematical_expression", ""))
            entry_title = str(fm.get("title", ""))
            entry_role = str(fm.get("role", ""))
            entry_id = fm.get("entry_id", ep.stem)
            # Build searchable text from entry role
            entry_text = entry_title
            if entry_role == "claim":
                entry_text += " " + str(fm.get("statement", ""))
            elif entry_role == "question":
                entry_text += " " + str(fm.get("question_statement", ""))

            # Check expression similarity
            for src_expr in source_expressions:
                if src_expr and entry_expr:
                    src_norm = normalize_latex(src_expr)
                    node_norm = normalize_latex(entry_expr)
                    if src_norm and node_norm:
                        src_cmds = set(re.findall(r'\\([a-zA-Z]+)', src_norm))
                        node_cmds = set(re.findall(r'\\([a-zA-Z]+)', node_norm))
                        shared = src_cmds & node_cmds
                        if len(shared) >= 2:
                            bridges.append({
                                "node_id": entry_id,
                                "title": entry_title,
                                "domain": f"entries/{entry_role}",
                                "bridge_type": "mathematical_structure",
                                "shared_structures": sorted(shared),
                                "note": (
                                    f"Shared LaTeX structures: {sorted(shared)}. "
                                    f"Found in v5 entry ({entry_role}). "
                                    f"Check if this is a deep correspondence or coincidental notation."
                                ),
                            })

            # Check concept similarity
            for src_concept in source_concepts:
                if src_concept:
                    score = semantic_score(
                        src_concept,
                        [entry_title, entry_text, body[:500]],
                    )
                    if score > 0.3:
                        bridges.append({
                            "node_id": entry_id,
                            "title": entry_title,
                            "domain": f"entries/{entry_role}",
                            "bridge_type": "conceptual_similarity",
                            "similarity": round(score, 3),
                            "note": (
                                f"Conceptual similarity score {score:.2f} with v5 entry ({entry_role}). "
                                f"Consider whether the same physics appears in a different regime."
                            ),
                        })

    # Deduplicate and sort by relevance
    seen = set()
    unique_bridges = []
    for b in bridges:
        key = (b["node_id"], b["bridge_type"])
        if key not in seen:
            seen.add(key)
            unique_bridges.append(b)

    unique_bridges.sort(
        key=lambda b: b.get("similarity", len(b.get("shared_structures", []))),
        reverse=True,
    )

    return {
        "bridges": unique_bridges[:10],
        "bridge_count": len(unique_bridges),
        "message": (
            f"Found {len(unique_bridges)} potential cross-topic bridges. "
            f"Review each: structural similarities may indicate deep "
            f"physical connections, or they may be coincidental."
        ) if unique_bridges else (
            "No cross-topic bridges found. The mathematical structure "
            "may be novel, or the L2 graph may not yet have enough "
            "entries in related domains."
        ),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

@mcp.tool()
def aitp_request_source_evidence(
    topics_root: str,
    topic_slug: str,
    required_claim: str,
    required_regime: str = "",
    reason: str = "",
) -> str:
    """Request additional source evidence from L0. Callable from L3/L4.

    When derivation or validation reveals a gap that needs source support
    (e.g. "need a proof of theorem X under condition Y"), this tool creates
    a structured request in L0 that the agent can pick up on next L0 pass.

    Each request is recorded as L0/pending_requests/<slug>.md and included
    in aitp_get_execution_brief so the agent sees outstanding evidence gaps.
    """
    root = _topic_root(topics_root, topic_slug)
    req_dir = root / "L0" / "pending_requests"
    req_dir.mkdir(parents=True, exist_ok=True)

    slug = _slugify(required_claim[:60])
    req_path = req_dir / f"{slug}.md"

    fm = {
        "kind": "l0_evidence_request",
        "request_id": slug,
        "required_claim": required_claim,
        "required_regime": required_regime,
        "reason": reason,
        "requested_from_stage": _parse_md(root / "state.md")[0].get("stage", "unknown"),
        "requested_at": _now(),
        "status": "pending",
    }
    body = (
        f"# Evidence Request: {required_claim[:80]}\\n\\n"
        f"**Required claim**: {required_claim}\\n\\n"
        f"**Required regime**: {required_regime or 'unspecified'}\\n\\n"
        f"**Reason**: {reason or 'Gap discovered during derivation/validation.'}\\n\\n"
        f"## Resolution\\n\\n"
        f"(Resolve by registering sources that address this claim, "
        f"then mark status as 'fulfilled' or 'deferred'.)\\n"
    )

    if req_path.exists():
        existing_fm, _ = _parse_md(req_path)
        if existing_fm.get("status") == "fulfilled":
            fm["status"] = "pending"  # Re-open

    _write_md(req_path, fm, body)
    _append_to_topic_log(root, f"L0 evidence request: {slug} — {required_claim[:60]}")
    return f"Evidence request '{slug}' filed in L0/pending_requests/. Resolve by registering supporting sources."


if __name__ == "__main__":
    mcp.run()



