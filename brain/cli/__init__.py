"""AITP CLI — enforcement engine for the research protocol.

Usage:
    python -m brain.cli <command> <subcommand> [--flags]
    aitp <command> <subcommand> [--flags]

All business logic lives here. MCP tools are thin wrappers that dispatch to CLI.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from brain.cli.state import (
    load_state, advance_stage, atomic_write, current_gate_status,
    InvalidStateTransition,
)
from brain.cli.preflight import (
    run_preflight,
)

# Default topics root (can be overridden by env var)
DEFAULT_TOPICS_ROOT = os.environ.get(
    "AITP_TOPICS_ROOT",
    "D:/BaiduSyncdisk/Theoretical-Physics/research/aitp-topics"
)

def _resolve_topic_root(topic_slug: str) -> Path:
    from brain.cli.state import resolve_topic_root
    return resolve_topic_root(DEFAULT_TOPICS_ROOT, topic_slug)

def _parse_md(path: Path):
    """Local YAML frontmatter parser."""
    import yaml
    if not path.exists():
        return {}, ""
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            try:
                fm = yaml.safe_load(parts[1]) or {}
            except Exception:
                fm = {}
            return fm, parts[2] if len(parts) > 2 else ""
    return {}, text

def _write_md(path: Path, fm, body):
    """Write YAML frontmatter + body to a Markdown file."""
    import yaml
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---", yaml.dump(dict(fm), default_flow_style=False, allow_unicode=True).rstrip(), "---", str(body).lstrip("\n")]
    atomic_write(path, "\n".join(lines))


# ═══════════════════════════════════════════════════════════════════════════════
# Commands
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_state_show(args):
    """Show current topic state."""
    root = _resolve_topic_root(args.topic)
    fm, _ = load_state(root)
    if not (root / "state.md").exists():
        print(json.dumps({"error": f"Topic '{args.topic}' not found"}))
        return 1
    stage = fm.get("stage", "L0")
    lane = fm.get("lane", "unspecified")
    gate = fm.get("gate_status", "?")
    activity = fm.get("l3_activity", "")
    cycle = fm.get("l4_cycle_count", 0)
    loop = fm.get("research_loop_active", False)
    override = fm.get("gate_override", False)
    override_reason = fm.get("gate_override_reason", "")
    print(f"Stage: {stage}  Lane: {lane}  Gate: {gate}  Activity: {activity or '-'}")
    print(f"Cycle: {cycle}  Loop: {loop}  Override: {override}")
    if override:
        print(f"Override reason: {override_reason}")
    return 0


def cmd_state_advance(args):
    """Advance topic to the next stage."""
    root = _resolve_topic_root(args.topic)
    try:
        advance_stage(root, args.to_stage)
        print(f"Advanced to {args.to_stage}")
    except InvalidStateTransition as e:
        print(f"Error: {e}")
        return 1
    return 0


def cmd_state_retreat(args):
    """Retreat topic to an earlier stage, preserving all artifacts."""
    root = _resolve_topic_root(args.topic)
    try:
        from brain.cli.state import retreat_stage
        retreat_stage(root, args.to_stage, reason=args.reason or "")
        print(f"Retreated to {args.to_stage}")
    except InvalidStateTransition as e:
        print(f"Error: {e}")
        return 1
    return 0


def cmd_gate_check(args):
    """Check gate readiness for a topic."""
    root = _resolve_topic_root(args.topic)
    gs, override = current_gate_status(root)
    print(f"Gate: {gs}")
    print(f"Override: {'active' if override else 'none'}")
    return 0 if gs.startswith("ready") else 1


def cmd_gate_override(args):
    """Override a blocked gate with explicit reason."""
    root = _resolve_topic_root(args.topic)
    state_path = root / "state.md"
    if not state_path.exists():
        print(f"Error: Topic '{args.topic}' not found")
        return 1

    fm, body = load_state(root)
    gs = fm.get("gate_status", "")
    if gs.startswith("ready"):
        print(f"Gate is already ready ({gs}). No override needed.")
        return 0

    reason = args.reason or "manual override"
    scope = args.scope or "current_gate"
    fm["gate_override"] = True
    fm["gate_override_reason"] = reason
    fm["gate_override_scope"] = scope
    fm["gate_override_at"] = _now_iso()
    fm["gate_status"] = "ready_override"
    fm["updated_at"] = _now_iso()
    _write_md(state_path, fm, body)

    print(f"Gate overridden: {gs} → ready_override")
    print(f"Reason: {reason}")
    print(f"Scope: {scope}")
    return 0


def cmd_lane_switch(args):
    """Switch the research lane for a topic."""
    root = _resolve_topic_root(args.topic)
    fm, body = load_state(root)
    old_lane = fm.get("lane", "unspecified")
    new_lane = args.lane
    fm["lane"] = new_lane
    fm["updated_at"] = _now_iso()
    _write_md(root / "state.md", fm, body)
    line = f"- {_now_iso()} [Lane] Switched from {old_lane} to {new_lane}\n"
    rp = root / "research.md"
    if rp.exists():
        atomic_write(rp, rp.read_text(encoding="utf-8") + line)
    else:
        atomic_write(rp, f"# Research Trail\n\n{line}")
    print(f"Lane switched: {old_lane} → {new_lane}")
    return 0


def cmd_topic_init(args):
    """Initialize a new research topic."""
    slug = _slugify(args.slug)
    root = _resolve_topic_root(slug)

    if (root / "state.md").exists():
        print(f"Topic '{slug}' already exists at {root}")
        return 1

    # Create directory tree
    dirs = [
        "L0/sources", "L1/intake", "L2/graph/steps", "L2/graph/edges",
        "L3/candidates", "L3/ideate", "L4/reviews", "L4/reports",
        "L4/scripts", "L4/outputs", "compute", "runtime", "contracts",
    ]
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)

    # Write state.md
    state_fm = {
        "stage": "L0", "posture": "discover", "lane": args.lane or "unspecified",
        "gate_status": "blocked_missing_artifact", "protocol_version": "v1.0",
        "research_intensity": args.intensity or "standard",
        "memory_gate_enabled": False, "research_loop_active": False,
        "l4_cycle_count": 0, "updated_at": _now_iso(),
    }
    state_body = "# Topic State\n\nInitialized.\n"
    _write_md(root / "state.md", state_fm, state_body)

    # Write MEMORY.md scaffold
    memory_body = "# Memory\n\n## Steering\n\n## Decisions\n\n## Dead Ends\n\n## Pitfalls\n"
    (root / "MEMORY.md").write_text(memory_body, encoding="utf-8")

    # Write research.md scaffold
    (root / "research.md").write_text(f"# Research Trail\n\n- {_now_iso()} [L0] Topic initialized\n", encoding="utf-8")

    # Write compute/targets.yaml scaffold
    targets_yaml = (
        "targets:\n"
        "  local:\n"
        "    type: local\n"
        "    python: python\n"
        "    sympy: available\n"
    )
    (root / "compute" / "targets.yaml").write_text(targets_yaml, encoding="utf-8")

    # Write L0/L1 artifact scaffolds from protocol templates
    from brain.contracts import L0_ARTIFACT_TEMPLATES, L1_ARTIFACT_TEMPLATES
    for rel_name, (artifact_fm, artifact_body) in L0_ARTIFACT_TEMPLATES.items():
        _write_md(root / "L0" / rel_name, artifact_fm, artifact_body)
    for rel_name, (artifact_fm, artifact_body) in L1_ARTIFACT_TEMPLATES.items():
        _write_md(root / "L1" / rel_name, artifact_fm, artifact_body)

    # Write runtime log scaffold
    (root / "runtime" / "log.md").parent.mkdir(parents=True, exist_ok=True)
    (root / "runtime" / "log.md").write_text("# Topic Log\n\n## Events\n", encoding="utf-8")

    print(f"Topic '{slug}' initialized at {root}")
    print(f"Lane: {args.lane or 'unspecified'}  Intensity: {args.intensity or 'standard'}")
    print(f"\nNext: aitp session resume {slug}")
    return 0


def cmd_session_list(args):
    """List all active topics."""
    sessions_path = Path.home() / ".aitp" / "sessions.json"
    if not sessions_path.exists():
        print("No active sessions.")
        return 0
    data = json.loads(sessions_path.read_text(encoding="utf-8"))
    current = data.get("current", "")
    history = data.get("history", [])
    if not history:
        print("No topics in session history.")
        return 0
    for h in history:
        marker = "▶" if h["slug"] == current else " "
        print(f" {marker} {h['slug']:<40} {h.get('stage','?'):<6} {h.get('lane',''):<15} {h.get('last_active','')[:16]}")
    return 0


def cmd_session_resume(args):
    """Resume a topic session."""
    root = _resolve_topic_root(args.topic)
    if not (root / "state.md").exists():
        print(f"Error: Topic '{args.topic}' not found")
        return 1
    fm, _ = load_state(root)
    # Update sessions.json
    sess_dir = Path.home() / ".aitp"
    sess_dir.mkdir(parents=True, exist_ok=True)
    sessions_path = sess_dir / "sessions.json"
    data = {"current": "", "history": []}
    if sessions_path.exists():
        data = json.loads(sessions_path.read_text(encoding="utf-8"))
    data["current"] = args.topic
    # Update or append history
    entry = {
        "slug": args.topic,
        "stage": fm.get("stage", "L0"),
        "lane": fm.get("lane", "unspecified"),
        "last_active": _now_iso(),
    }
    history = data.get("history", [])
    existing = [i for i, h in enumerate(history) if h["slug"] == args.topic]
    if existing:
        history[existing[0]] = entry
    else:
        history.insert(0, entry)
    data["history"] = history[:50]
    atomic_write(sessions_path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    stage = fm.get("stage", "L0")
    lane = fm.get("lane", "unspecified")
    gate = fm.get("gate_status", "?")
    activity = fm.get("l3_activity", "")
    cycle = fm.get("l4_cycle_count", 0)
    bg_status = fm.get("l4_background_status", "")
    job_id = fm.get("l4_job_id", "")
    print(f"Resumed: {args.topic}")
    print(f"Stage: {stage}  Lane: {lane}  Gate: {gate}  Activity: {activity or '-'}")
    print(f"Cycle: {cycle}  HPC: {bg_status}" + (f" (job #{job_id})" if job_id else ""))
    # Show last 10 log events from observability
    from brain.cli.observability import recent_events
    events = recent_events(root, limit=10)
    if events:
        print(f"\nLast {len(events)} events:")
        for ev in events:
            ts = ev.get("timestamp", "")[:19]
            print(f"  {ts} [{ev.get('category','')}] {ev.get('action','')} — {ev.get('status','')}")
    return 0


def cmd_session_status(args):
    """Show current session binding."""
    sessions_path = Path.home() / ".aitp" / "sessions.json"
    if not sessions_path.exists():
        print("No active session. Use 'aitp session resume <topic>' to bind a topic.")
        return 0
    data = json.loads(sessions_path.read_text(encoding="utf-8"))
    current = data.get("current", "")
    if not current:
        print("No topic bound. Use 'aitp session resume <topic>' to bind.")
    else:
        root = _resolve_topic_root(current)
        if not (root / "state.md").exists():
            print(f"Bound to '{current}' but state.md not found.")
        else:
            fm, _ = load_state(root)
            stage = fm.get("stage", "L0")
            lane = fm.get("lane", "unspecified")
            activity = fm.get("l3_activity", "")
            gate = fm.get("gate_status", "?")
            print(f"Current topic: {current}")
            print(f"Stage: {stage}  Lane: {lane}  Gate: {gate}  Activity: {activity or '-'}")
    return 0


def cmd_derive_record(args):
    """Record a derivation step."""
    root = _resolve_topic_root(args.topic)
    # Preflight: advisory in L3, blocking in L0/L1/L4
    from brain.cli.state import current_stage
    stage = current_stage(root)
    failures = run_preflight("derive-record", root)
    if failures:
        if stage == "L3":
            print("Preflight advisory:")
            for f in failures:
                print(f"  • {f}")
        else:
            print("Preflight blocked:")
            for f in failures:
                print(f"  • {f}")
            return 1
    # Write step
    steps_dir = root / "L2" / "graph" / "steps"
    steps_dir.mkdir(parents=True, exist_ok=True)
    step_id = args.step.upper() if not args.step.startswith("D") else args.step
    from brain.state_model import L2_NODE_TYPES, JUSTIFICATION_TYPES
    step_fm = {
        "step_id": step_id,
        "chain_id": args.chain or "default",
        "order": args.order or "1",
        "input_expr": args.input or "",
        "output_expr": args.output or "",
        "transform": args.transform or "",
        "justification_type": args.justification or "definition",
        "source_ref": args.source or "",
        "rigor_level": args.rigor or "rigorous",
        "created_at": _now_iso(),
    }
    step_body = f"# Step {step_id}\n\n"
    for k, v in step_fm.items():
        if v:
            step_body += f"**{k}**: {v}\n\n"
    step_path = steps_dir / f"{step_id.lower()}.md"
    _write_md(step_path, step_fm, step_body)
    print(f"Step {step_id} recorded → {step_path}")
    return 0


def _slugify(text: str) -> str:
    import re
    return re.sub(r'[^a-z0-9-]', '-', (text or "untitled").lower().strip())[:60]


def _append_research_md(root: Path, layer: str, entry: str):
    path = root / "research.md"
    line = f"- {_now_iso()} [{layer}] {entry}\n"
    if path.exists():
        atomic_write(path, path.read_text(encoding="utf-8") + line)
    else:
        atomic_write(path, f"# Research Trail\n\n{line}")


def _trigger_notebook_section(root: Path, section: str):
    """Regenerate a single notebook section.

    Called by MCP tools after state-changing operations to keep the
    notebook current.  Only the affected section is rebuilt.
    """
    try:
        from brain.flow_notebook import build_notebook
        tex_content, regenerated = build_notebook(
            root, changed_sections=[section],
        )
        if regenerated:
            from brain.cli.state import atomic_write
            atomic_write(root / "flow_notebook.tex", tex_content)
    except Exception:
        pass  # Non-blocking — notebook is derivative, not source of truth


def cmd_l2_ask(args):
    """Query the L2 knowledge base — delegates to l2 query."""
    from brain.cli.commands.l2 import cmd_l2_query
    return cmd_l2_query(args)


def _now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def build_parser():
    p = argparse.ArgumentParser(prog="aitp",
        description="AITP CLI — enforcement engine for AI-assisted theoretical physics",
        epilog="Typical workflow: topic init → session resume → source add → state advance → derive record → derive pack → candidate submit")
    sub = p.add_subparsers(dest="command")

    # topic init
    p_topic = sub.add_parser("topic", help="Topic lifecycle")
    p_topic_sub = p_topic.add_subparsers(dest="subcommand")
    p_ti = p_topic_sub.add_parser("init", help="Initialize a new research topic")
    p_ti.add_argument("slug", help="Short name for the topic (lowercase, hyphens for spaces)")
    p_ti.add_argument("--lane", "-l", default="unspecified",
                      choices=["code_method", "formal_theory", "unspecified"],
                      help="Research approach: code_method (numerical/HPC), formal_theory (analytic/SymPy)")
    p_ti.add_argument("--intensity", "-i", default="standard",
                      choices=["quick", "standard", "full"],
                      help="Gate strictness: quick (advisory only), standard (normal), full (extra checks)")
    p_ti.set_defaults(func=cmd_topic_init)
    p_tl = p_topic_sub.add_parser("lane", help="Switch research lane")
    p_tl.add_argument("topic")
    p_tl.add_argument("lane", choices=["code_method", "formal_theory"])
    p_tl.set_defaults(func=cmd_lane_switch)

    # state show
    p_state = sub.add_parser("state", help="State operations")
    p_state_sub = p_state.add_subparsers(dest="subcommand")
    p_show = p_state_sub.add_parser("show", help="Show topic state")
    p_show.add_argument("topic")
    p_show.set_defaults(func=cmd_state_show)
    p_adv = p_state_sub.add_parser("advance", help="Advance topic to next stage (L0→L1→L3→L4→promotion)")
    p_adv.add_argument("topic", help="Topic slug")
    p_adv.add_argument("to_stage", help="Target stage: L1, L3, L4, or promotion")
    p_adv.set_defaults(func=cmd_state_advance)
    p_ret = p_state_sub.add_parser("retreat", help="Retreat to an earlier stage")
    p_ret.add_argument("topic")
    p_ret.add_argument("to_stage", choices=["L0", "L1", "L3"])
    p_ret.add_argument("--reason", "-r", help="Reason for retreat")
    p_ret.set_defaults(func=cmd_state_retreat)

    # gate
    p_gate = sub.add_parser("gate", help="Gate operations")
    p_gate_sub = p_gate.add_subparsers(dest="subcommand")
    p_gc = p_gate_sub.add_parser("check", help="Check gate status")
    p_gc.add_argument("topic")
    p_gc.set_defaults(func=cmd_gate_check)
    p_go = p_gate_sub.add_parser("override", help="Override a blocked gate")
    p_go.add_argument("topic")
    p_go.add_argument("--reason", "-r", help="Reason for override")
    p_go.add_argument("--scope", "-s", default="current_gate",
                      choices=["current_gate", "this_session", "permanent"])
    p_go.set_defaults(func=cmd_gate_override)

    # session
    p_sess = sub.add_parser("session", help="Session management")
    p_sess_sub = p_sess.add_subparsers(dest="subcommand")
    p_sl = p_sess_sub.add_parser("list", help="List session history")
    p_sl.set_defaults(func=cmd_session_list)
    p_sr = p_sess_sub.add_parser("resume", help="Resume a topic")
    p_sr.add_argument("topic")
    p_sr.set_defaults(func=cmd_session_resume)
    p_ss = p_sess_sub.add_parser("status", help="Show current session binding")
    p_ss.set_defaults(func=cmd_session_status)

    # derive
    p_derive = sub.add_parser("derive", help="Derivation operations")
    p_derive_sub = p_derive.add_subparsers(dest="subcommand")
    p_dr = p_derive_sub.add_parser("record", help="Record a derivation step (L3)")
    p_dr.add_argument("topic", help="Topic slug")
    p_dr.add_argument("--step", required=True, help="Step ID (e.g. D1, D2)")
    p_dr.add_argument("--chain", help="Derivation chain ID (default: 'default')")
    p_dr.add_argument("--order", help="Step order in chain (1, 2, ...)")
    p_dr.add_argument("--input", help="Input expression (LaTeX or SymPy)")
    p_dr.add_argument("--output", help="Output expression (LaTeX or SymPy)")
    p_dr.add_argument("--transform", help="What transform was applied?")
    p_dr.add_argument("--justification", help="Justification type: definition, theorem, approximation, physical_principle, algebraic_identity, limit, assumption, conjecture, gap, numerical_evidence")
    p_dr.add_argument("--source", help="Source reference (e.g. 'hedin1965:Eq20')")
    p_dr.add_argument("--rigor", help="Rigor level: rigorous, heuristic, conjectural")
    p_dr.set_defaults(func=cmd_derive_record)

    # ── Phase 1: L0-L1 commands ────────────────────────────────────────
    from brain.cli.commands.source import (cmd_source_add, cmd_source_discover,
                                             cmd_source_registry, cmd_source_read)
    from brain.cli.commands.reading import (cmd_source_parse_toc, cmd_source_extract,
                                              cmd_source_extract_all)
    from brain.cli.commands.framing import (cmd_question_frame, cmd_convention_lock,
                                              cmd_anchor_map, cmd_contradiction_register,
                                              cmd_source_cross_map)

    # source
    p_src = sub.add_parser("source", help="Source management")
    p_src_sub = p_src.add_subparsers(dest="subcommand")
    p_sa = p_src_sub.add_parser("add", help="Register a new source (L0)")
    p_sa.add_argument("topic", help="Topic slug")
    p_sa.add_argument("--id", help="Source identifier (e.g. arxiv ID, DOI)")
    p_sa.add_argument("--title", help="Source title")
    p_sa.add_argument("--path", help="Local file/directory path to preserve in original/")
    p_sa.add_argument("--url", help="Download URL for original source file")
    p_sa.add_argument("--type", default="paper", help="Source type: paper, code, data, book")
    p_sa.add_argument("--role", default="direct_dependency", help="Role: foundational, direct_dependency, contrast_reference, background")
    p_sa.add_argument("--notes", help="Free-text notes")
    p_sa.set_defaults(func=cmd_source_add)
    p_sd = p_src_sub.add_parser("discover", help="Search arXiv for sources")
    p_sd.add_argument("topic", help="Topic slug")
    p_sd.add_argument("--query", required=True, help="arXiv search query")
    p_sd.add_argument("--max", type=int, default=10, help="Max results (default 10)")
    p_sd.set_defaults(func=cmd_source_discover)
    p_sr = p_src_sub.add_parser("registry", help="Synthesize source coverage assessment")
    p_sr.add_argument("topic", help="Topic slug")
    p_sr.set_defaults(func=cmd_source_registry)
    p_srd = p_src_sub.add_parser("read", help="Quick-read a registered source")
    p_srd.add_argument("topic", help="Topic slug")
    p_srd.add_argument("--source", required=True, help="Source ID to read")
    p_srd.set_defaults(func=cmd_source_read)
    p_sparse = p_src_sub.add_parser("parse-toc", help="Parse source table of contents (L1)")
    p_sparse.add_argument("topic", help="Topic slug")
    p_sparse.add_argument("--source", required=True, help="Source ID")
    p_sparse.add_argument("--sections", help="Comma-separated section names")
    p_sparse.set_defaults(func=cmd_source_parse_toc)
    p_sext = p_src_sub.add_parser("extract", help="Extract a section into intake notes (L1)")
    p_sext.add_argument("topic", help="Topic slug")
    p_sext.add_argument("--source", required=True, help="Source ID")
    p_sext.add_argument("--section", required=True, help="Section name")
    p_sext.add_argument("--content", help="Section content / key equations")
    p_sext.add_argument("--confidence", help="Extraction confidence: low, medium, high")
    p_sext.set_defaults(func=cmd_source_extract)
    p_sexta = p_src_sub.add_parser("extract-all", help="List all pending sections for batch extraction")
    p_sexta.add_argument("topic", help="Topic slug")
    p_sexta.add_argument("--source", help="Filter by source ID (optional)")
    p_sexta.set_defaults(func=cmd_source_extract_all)

    # question
    p_q = sub.add_parser("question", help="Question framing")
    p_q_sub = p_q.add_subparsers(dest="subcommand")
    p_qf = p_q_sub.add_parser("frame", help="Create/update question contract (L1)")
    p_qf.add_argument("topic", help="Topic slug")
    p_qf.add_argument("--question", help="The bounded research question")
    p_qf.add_argument("--scope", help="Scope boundaries")
    p_qf.add_argument("--targets", help="Target quantities or claims")
    p_qf.set_defaults(func=cmd_question_frame)

    # convention
    p_cv = sub.add_parser("convention", help="Convention management")
    p_cv_sub = p_cv.add_subparsers(dest="subcommand")
    p_cvl = p_cv_sub.add_parser("lock", help="Lock a convention (L1)")
    p_cvl.add_argument("topic", help="Topic slug")
    p_cvl.add_argument("--add", help="Convention to add (e.g. 'Fourier conv: f(t) = ∫ f(ω) e^{-iωt}')")
    p_cvl.add_argument("--text", help="Free-text convention note")
    p_cvl.set_defaults(func=cmd_convention_lock)

    # anchor
    p_an = sub.add_parser("anchor", help="Derivation anchor management")
    p_an_sub = p_an.add_subparsers(dest="subcommand")
    p_am = p_an_sub.add_parser("map", help="Map a derivation anchor to its source (L1)")
    p_am.add_argument("topic", help="Topic slug")
    p_am.add_argument("--source", required=True, help="Source ID")
    p_am.add_argument("--equation", help="Equation reference in source")
    p_am.add_argument("--note", help="Note about this anchor")
    p_am.set_defaults(func=cmd_anchor_map)

    # contradiction
    p_ct = sub.add_parser("contradiction", help="Contradiction register")
    p_ct_sub = p_ct.add_subparsers(dest="subcommand")
    p_cr = p_ct_sub.add_parser("register", help="Register a contradiction between sources (L1)")
    p_cr.add_argument("topic", help="Topic slug")
    p_cr.add_argument("--source-a", required=True, help="First source ID")
    p_cr.add_argument("--source-b", required=True, help="Second source ID")
    p_cr.add_argument("--conflict", required=True, help="Description of the contradiction")
    p_cr.add_argument("--status", default="unresolved", help="Status: unresolved, resolved, deferred")
    p_cr.set_defaults(func=cmd_contradiction_register)

    # source cross-map (under source subcommand)
    p_src_xm = p_src_sub.add_parser("cross-map", help="Generate cross-map of source relationships")
    p_src_xm.add_argument("topic", help="Topic slug")
    p_src_xm.set_defaults(func=cmd_source_cross_map)

    # ── Phase 2: L3 commands ───────────────────────────────────────────
    from brain.cli.commands.sympy_check import cmd_sympy_check, cmd_sympy_execute
    from brain.cli.commands.memory_cmd import cmd_memory_steer, cmd_memory_decide, cmd_memory_pitfall
    from brain.cli.commands.l3_workflow import (cmd_derive_pack, cmd_candidate_submit,
                                                   cmd_quick_compute, cmd_switch_activity)

    # derive pack + candidate submit
    p_dp = p_derive_sub.add_parser("pack", help="Package derivation steps into a candidate draft (L3)")
    p_dp.add_argument("topic", help="Topic slug")
    p_dp.add_argument("--candidate-id", required=True, help="ID for the candidate (e.g. gw-correction-v1)")
    p_dp.add_argument("--chain", help="Derivation chain ID (default: 'default')")
    p_dp.set_defaults(func=cmd_derive_pack)

    p_cand = sub.add_parser("candidate", help="Candidate management")
    p_cand_sub = p_cand.add_subparsers(dest="subcommand")
    p_cs = p_cand_sub.add_parser("submit", help="Submit candidate for L4 verification (L3→L4)")
    p_cs.add_argument("topic", help="Topic slug")
    p_cs.add_argument("--candidate-id", required=True, help="Candidate ID from derive pack")
    p_cs.add_argument("--type", default="research_claim", help="Candidate type: research_claim (new result) or atomic_concept (study mode)")
    p_cs.add_argument("--chain", help="Derivation chain ID (default: 'default')")
    p_cs.add_argument("--claim", help="One-sentence claim statement (≥20 chars required)")
    p_cs.add_argument("--source-refs", help="Comma-separated source references")
    p_cs.set_defaults(func=cmd_candidate_submit)

    # sympy
    p_sympy = sub.add_parser("sympy", help="Interactive SymPy verification")
    p_sympy_sub = p_sympy.add_subparsers(dest="subcommand")
    p_sympy_chk = p_sympy_sub.add_parser("check", help="Quick SymPy verification (dimensions/algebra/limits)")
    p_sympy_chk.add_argument("sympy_subcommand", choices=["dim", "algebra", "limit"], help="Check type: dim (dimensional), algebra (LHS=RHS), limit (limiting behavior)")
    p_sympy_chk.add_argument("expression", nargs="+", help="Expression to check")
    p_sympy_chk.set_defaults(func=cmd_sympy_check)
    p_sympy_exe = p_sympy_sub.add_parser("execute", help="Batch formal verification of entire derivation chain (L4)")
    p_sympy_exe.add_argument("topic", help="Topic slug")
    p_sympy_exe.add_argument("--candidate", required=True, dest="candidate_id", help="Candidate ID to verify")
    p_sympy_exe.add_argument("--target", default="local", choices=["local", "fisher"], help="Compute target")
    p_sympy_exe.set_defaults(func=cmd_sympy_execute)

    # memory
    p_mem = sub.add_parser("memory", help="Memory recording")
    p_mem_sub = p_mem.add_subparsers(dest="subcommand")
    p_ms = p_mem_sub.add_parser("steer", help="Record user steering decision")
    p_ms.add_argument("topic", help="Topic slug")
    p_ms.add_argument("--text", required=True, help="Steering content")
    p_ms.set_defaults(func=cmd_memory_steer)
    p_md = p_mem_sub.add_parser("decide", help="Record a research decision")
    p_md.add_argument("topic", help="Topic slug")
    p_md.add_argument("--text", required=True, help="Decision content")
    p_md.add_argument("--rejected", help="Rejected alternative")
    p_md.set_defaults(func=cmd_memory_decide)
    p_mp = p_mem_sub.add_parser("pitfall", help="Record a pitfall encountered")
    p_mp.add_argument("topic", help="Topic slug")
    p_mp.add_argument("--text", required=True, help="Pitfall description (symptom + cause + fix)")
    p_mp.set_defaults(func=cmd_memory_pitfall)

    # quick compute
    p_qc = sub.add_parser("quick", help="Quick compute — sandboxed Python, no topic needed")
    p_qc_sub = p_qc.add_subparsers(dest="subcommand")
    p_qcc = p_qc_sub.add_parser("compute", help="Run sandboxed Python code")
    p_qcc.add_argument("--script", help="Python script to execute")
    p_qcc.add_argument("--expr", help="Python expression to evaluate")
    p_qcc.set_defaults(func=cmd_quick_compute)

    # switch-activity
    p_sw = sub.add_parser("switch-activity", help="Switch L3 activity (ideate/plan/derive/gap-audit/...)")
    p_sw.add_argument("topic", help="Topic slug")
    p_sw.add_argument("activity", help="Target activity: ideate, plan, derive, trace-derivation, gap-audit, connect, integrate, distill")
    p_sw.set_defaults(func=cmd_switch_activity)

    # ── Phase 3: L4 commands ───────────────────────────────────────────
    from brain.cli.commands.verify import cmd_verify_run, cmd_verify_results, cmd_promote

    p_v = sub.add_parser("verify", help="L4 verification")
    p_v_sub = p_v.add_subparsers(dest="subcommand")
    p_vr = p_v_sub.add_parser("run", help="Spawn Verifier agents (Algebraic + Physical + Numerical + Skeptic)")
    p_vr.add_argument("topic", help="Topic slug")
    p_vr.add_argument("--candidate", required=True, dest="candidate_id", help="Candidate ID to verify")
    p_vr.set_defaults(func=cmd_verify_run)
    p_vres = p_v_sub.add_parser("results", help="Collect verification results and build disagreement matrix")
    p_vres.add_argument("topic", help="Topic slug")
    p_vres.add_argument("--candidate", required=True, dest="candidate_id", help="Candidate ID")
    p_vres.set_defaults(func=cmd_verify_results)

    p_prom = sub.add_parser("promote", help="Promote validated candidate to L2 knowledge graph (requires unanimous_pass + Skeptic)")
    p_prom.add_argument("topic", help="Topic slug")
    p_prom.add_argument("--candidate", required=True, dest="candidate_id", help="Candidate ID to promote")
    p_prom.set_defaults(func=cmd_promote)

    # ── L4 compute commands ────────────────────────────────────────────
    from brain.cli.commands.compute import (cmd_compute_prepare, cmd_compute_submit,
                                              cmd_compute_check, cmd_compute_validate,
                                              cmd_compute_report)
    p_comp = sub.add_parser("compute", help="L4 computational execution")
    p_comp_sub = p_comp.add_subparsers(dest="subcommand")
    for name, fn, desc in [
        ("prepare", cmd_compute_prepare, "Generate Slurm script + parameter audit (L4)"),
        ("submit", cmd_compute_submit, "Submit to HPC or run locally (L4)"),
        ("check", cmd_compute_check, "Check output files for completion (L4)"),
        ("validate", cmd_compute_validate, "Parse outputs, compare to claim, check invariants (L4)"),
        ("report", cmd_compute_report, "Generate comprehensive computational report (L4)"),
    ]:
        p_c = p_comp_sub.add_parser(name, help=desc)
        p_c.add_argument("topic", help="Topic slug")
        p_c.add_argument("--candidate-id", default="cand-v1", help="Candidate ID")
        p_c.add_argument("--stage", default=None, help="Computation stage override")
        p_c.set_defaults(func=fn)

    # ── Phase 5: L2 + notebook ──────────────────────────────────────────
    from brain.cli.commands.l2 import (cmd_l2_node_create, cmd_l2_edge_create,
                                         cmd_l2_merge, cmd_l2_query, cmd_notebook_generate)

    p_l2 = sub.add_parser("l2", help="L2 knowledge graph operations")
    p_l2_sub = p_l2.add_subparsers(dest="subcommand")
    p_l2a = p_l2_sub.add_parser("ask", help="Query the L2 knowledge base by keyword")
    p_l2a.add_argument("query", nargs="+", help="Search terms")
    p_l2a.set_defaults(func=cmd_l2_ask)

    p_l2n = p_l2_sub.add_parser("node-create", help="Create an L2 knowledge graph node")
    p_l2n.add_argument("--node-id", required=True, help="Unique node identifier")
    p_l2n.add_argument("--title", help="Human-readable title")
    p_l2n.add_argument("--node-type", default="concept", help="Node type: concept, theorem, technique, result, approximation")
    p_l2n.add_argument("--domain", default="abacus-librpa", help="Knowledge domain")
    p_l2n.add_argument("--source-ref", help="Source reference for provenance")
    p_l2n.add_argument("--topics-root", default=None, help="Topics root directory override")
    p_l2n.set_defaults(func=cmd_l2_node_create)

    p_l2e = p_l2_sub.add_parser("edge-create", help="Create a typed edge between L2 nodes")
    p_l2e.add_argument("--edge-id", required=True, help="Unique edge identifier")
    p_l2e.add_argument("--from-node", required=True, help="Source node ID")
    p_l2e.add_argument("--to-node", required=True, help="Target node ID")
    p_l2e.add_argument("--edge-type", default="uses", help="Edge type: derives_from, uses, generalizes, contradicts, ...")
    p_l2e.add_argument("--source-ref", help="Source reference for provenance")
    p_l2e.add_argument("--topics-root", default=None, help="Topics root directory override")
    p_l2e.set_defaults(func=cmd_l2_edge_create)

    p_l2m = p_l2_sub.add_parser("merge", help="Merge topic subgraph into global L2")
    p_l2m.add_argument("topic", help="Topic slug")
    p_l2m.set_defaults(func=cmd_l2_merge)

    p_l2q = p_l2_sub.add_parser("query", help="Search L2 graph by substring")
    p_l2q.add_argument("query", nargs="+", help="Search terms")
    p_l2q.set_defaults(func=cmd_l2_query)

    # notebook
    p_nb = sub.add_parser("notebook", help="Flow notebook operations")
    p_nb_sub = p_nb.add_subparsers(dest="subcommand")
    p_nbg = p_nb_sub.add_parser("generate", help="Generate flow notebook LaTeX/PDF")
    p_nbg.add_argument("topic", help="Topic slug")
    p_nbg.add_argument("--force", action="store_true", help="Force full rebuild of all sections")
    p_nbg.set_defaults(func=cmd_notebook_generate)

    # migrate
    p_mig = sub.add_parser("migrate", help="Migrate a topic from v0.6 to v1.0 protocol")
    p_mig.add_argument("topic", help="Topic slug")
    from brain.cli.migrate import cmd_migrate
    p_mig.set_defaults(func=cmd_migrate)

    return p


def _cli_stage_check(args) -> bool:
    """Check stage permission for CLI commands before dispatch.
    Returns True if blocked, False if allowed to proceed.
    """
    # Extract topic slug from args (different commands use different arg names)
    topic_slug = getattr(args, 'topic', None)
    if not topic_slug:
        # Commands without a topic arg (quick, session list) are allowed
        return False

    root = _resolve_topic_root(topic_slug)
    if not (root / "state.md").exists():
        return False  # Topic not initialized yet, allowed

    # Determine command name from argparse
    cmd = getattr(args, 'command', '')
    subcmd = getattr(args, 'subcommand', '')
    cmd_name = f"{cmd}-{subcmd}" if subcmd else cmd

    # Check command policy for stage restrictions
    from brain.cli.preflight import _load_command_policy
    policy = _load_command_policy(cmd_name)
    if not policy or not policy.get("stage"):
        return False  # No policy or no stage restriction, allowed

    from brain.cli.state import current_stage
    current = current_stage(root)
    required = policy["stage"]
    stages = required if isinstance(required, list) else [required]
    if current not in stages:
        print(f"Stage gate: '{cmd_name}' requires stage {stages}, currently {current}")
        # Suggest how to advance
        stage_order = ["L0", "L1", "L3", "L4"]
        if current in stage_order:
            target = min(stages, key=lambda s: stage_order.index(s) if s in stage_order else 99)
            if target in stage_order and stage_order.index(target) > stage_order.index(current):
                steps = " → ".join(stage_order[stage_order.index(current):stage_order.index(target)+1])
                print(f"Advance: aitp state advance <topic> {target}  ({steps})")
        return True  # Blocked

    # L3 lateral L0-L1 access: log advisory trail entry
    l0_l1_stages = {"L0", "L1"}
    if current == "L3" and set(stages) & l0_l1_stages:
        line = f"- {_now_iso()} [L3 advisory] Lateral {cmd_name} from L3 (allowed stages: {stages})\n"
        rp = root / "research.md"
        if rp.exists():
            atomic_write(rp, rp.read_text(encoding="utf-8") + line)
        else:
            atomic_write(rp, f"# Research Trail\n\n{line}")

    return False


def main():
    """CLI entry point. Routes commands to sub-modules."""
    p = build_parser()
    if len(sys.argv) < 2:
        p.print_help()
        return 0

    args = p.parse_args()
    if not hasattr(args, "func"):
        p.print_help()
        return 0

    # Stage gate check before dispatch
    if _cli_stage_check(args):
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main() or 0)
