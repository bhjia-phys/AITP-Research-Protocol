"""L3 workflow commands: derive pack, candidate submit, quick compute, switch activity."""
from __future__ import annotations
from pathlib import Path


def _now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _parse_md(path: Path):
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


def _write_md(path: Path, fm: dict, body: str):
    import yaml
    from brain.cli.state import atomic_write
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---", yaml.dump(dict(fm), default_flow_style=False, allow_unicode=True).rstrip(),
             "---", str(body).lstrip("\n")]
    atomic_write(path, "\n".join(lines))


def _atomic_write(path: Path, content: str):
    import os, tempfile
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix="." + path.name + ".")
    try:
        os.write(fd, content.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)


def _resolve_topic_root(topic_slug: str) -> Path:
    import os
    base = Path(os.environ.get("AITP_TOPICS_ROOT",
        "D:/BaiduSyncdisk/Theoretical-Physics/research/aitp-topics"))
    for candidate in [base / topic_slug, base / "topics" / topic_slug]:
        if (candidate / "state.md").exists():
            return candidate
    return base / topic_slug


def cmd_derive_pack(args):
    """Package derivation chain into a candidate draft."""
    root = _resolve_topic_root(args.topic)
    steps_dir = root / "L2" / "graph" / "steps"
    if not steps_dir.exists() or not list(steps_dir.glob("*.md")):
        print("No derivation steps found. Use 'aitp derive record' to add steps first.")
        return 1

    steps = sorted(steps_dir.glob("*.md"))
    chain_id = args.chain or "default"
    step_ids = []
    source_refs = set()
    for s in steps:
        fm, _ = _parse_md(s)
        if fm.get("chain_id") == chain_id:
            step_ids.append(fm.get("step_id", s.stem))
            ref = fm.get("source_ref", "").strip()
            if ref:
                source_refs.add(ref)

    if not step_ids:
        print(f"No steps found for chain '{chain_id}'")
        return 1

    # Generate claim and evidence summary from steps
    claim_parts = []
    for sid in step_ids:
        for s in steps:
            fm, _ = _parse_md(s)
            if fm.get("step_id") == sid:
                claim_parts.append(fm.get("output_expr", sid))
                break

    cand_dir = root / "L3" / "candidates"
    cand_dir.mkdir(parents=True, exist_ok=True)
    cand_id = args.candidate_id
    fm = {
        "candidate_id": cand_id,
        "status": "draft",
        "derivation_chain_id": chain_id,
        "source_refs": sorted(source_refs),
        "claim_statement": " → ".join(claim_parts[:3]) or "Derived from steps: " + ", ".join(step_ids),
        "depends_on": [],
        "created_at": _now_iso(),
    }
    body = f"# {cand_id}\n\n## Claim\n{fm['claim_statement']}\n\n## Derivation Steps\n" + "\n".join(f"- {s}" for s in step_ids) + "\n\n## Evidence\n\n## Assumptions\n"
    _write_md(cand_dir / f"{cand_id}.md", fm, body)

    # Update state
    state_fm, state_body = _parse_md(root / "state.md")
    state_fm["l3_activity"] = "integrate"
    _write_md(root / "state.md", state_fm, state_body)

    # Append research.md
    line = f"- {_now_iso()} [L3] Packed derivation → candidate {cand_id} ({len(step_ids)} steps in chain {chain_id})\n"
    rp = root / "research.md"
    if rp.exists():
        _atomic_write(rp, rp.read_text(encoding="utf-8") + line)
    else:
        _atomic_write(rp, f"# Research Trail\n\n{line}")

    print(f"Candidate '{cand_id}' drafted with {len(step_ids)} steps in chain '{chain_id}'")
    if not source_refs:
        print("Warning: no source_refs found in derivation steps. Candidate will fail Pydantic contract validation.")
        print("Add --source to each 'aitp derive record' call.")
    return 0


def cmd_candidate_submit(args):
    """Submit candidate with full preflight + contract validation."""
    root = _resolve_topic_root(args.topic)
    from brain.cli.preflight import run_preflight
    from brain.cli.contracts import validate_candidate

    cand_id = args.candidate_id
    cand_path = root / "L3" / "candidates" / f"{cand_id}.md"

    if not cand_path.exists():
        print(f"Candidate '{cand_id}' not found. Use 'aitp derive pack' first.")
        return 1

    cand_fm, cand_body = _parse_md(cand_path)

    # CLI --claim flag overrides the file claim (for manual submission)
    if getattr(args, 'claim', None):
        cand_fm["claim_statement"] = args.claim
        _write_md(cand_path, cand_fm, cand_body)

    # Hard prerequisite checks: prevent submitting without gap-audit and
    # integration artifacts that have real content. These are physical
    # necessities, not optional workflow suggestions.
    from brain.contracts import _DIRECT_SUBMIT_ACTIVITIES
    from brain.checks import _check_heading_content

    state_fm, state_body = _parse_md(root / "state.md")
    current_activity = str(state_fm.get("l3_activity", "")).strip() or "ideate"

    if current_activity not in _DIRECT_SUBMIT_ACTIVITIES:
        print(f"Candidate submission not allowed from '{current_activity}' activity.")
        print(f"Direct submission is only allowed from: {sorted(_DIRECT_SUBMIT_ACTIVITIES)}")
        print("Switch to integrate or distill first: aitp switch-activity <topic> integrate")
        return 1

    prereq_issues = []

    def _check_prereq_artifact(activity: str, heading: str, label: str, min_chars: int = 30) -> None:
        name_map = {
            "ideate": "active_idea.md", "plan": "active_plan.md",
            "derive": "active_derivation.md", "trace-derivation": "active_trace.md",
            "gap-audit": "active_gaps.md", "integrate": "active_integration.md",
            "distill": "active_distillation.md",
        }
        fname = name_map.get(activity, f"active_{activity}.md")
        path = root / "L3" / activity / fname
        if not path.exists():
            prereq_issues.append(
                f"{label}: {activity}/{fname} does not exist. "
                f"Run the {activity} activity before submitting."
            )
            return
        _, body = _parse_md(path)
        if not _check_heading_content(body, heading, min_chars=min_chars):
            prereq_issues.append(
                f"{label}: '{heading}' in {activity}/{fname} is empty or has "
                f"insufficient content (need >= {min_chars} chars). "
                f"Complete the {activity} activity before submitting."
            )

    _check_prereq_artifact("derive", "## Derivation Chains", "Missing derivation", min_chars=50)
    _check_prereq_artifact("gap-audit", "## Correspondence Check",
                          "Missing correspondence check", min_chars=30)
    _check_prereq_artifact("integrate", "## Findings",
                          "Missing integration findings", min_chars=50)

    if prereq_issues:
        print("Candidate submission blocked — prerequisite artifacts incomplete:")
        for issue in prereq_issues:
            print(f"  • {issue}")
        print(f"\nTo resolve: fill the required sections in L3/<activity>/ and re-submit.")
        return 1

    # Run preflight
    lane = state_fm.get("lane", "unspecified")
    ctype = args.type or "research_claim"

    failures = run_preflight("candidate-submit", root,
        lane=lane, candidate_type=ctype, candidate_id=cand_id)
    if failures:
        print("Preflight blocked:")
        for f in failures:
            print(f"  • {f}")
        return 1

    # Contract validation
    try:
        validate_candidate({
            "candidate_id": cand_id,
            "status": cand_fm.get("status", "draft"),
            "derivation_chain_id": cand_fm.get("derivation_chain_id", "default"),
            "source_refs": cand_fm.get("source_refs", []),
            "claim_statement": cand_fm.get("claim_statement", ""),
        }, topic_root=root)
    except Exception as e:
        print(f"Contract validation failed: {e}")
        return 1

    # Update candidate status
    cand_fm["status"] = "draft"
    cand_fm["candidate_type"] = ctype
    _write_md(cand_path, cand_fm, _parse_md(cand_path)[1])

    # Update state — advance to L4 with validation
    from brain.cli.state import validate_state_transition, save_state
    ok, msg = validate_state_transition(root, "L4")
    if not ok:
        print(f"Stage transition blocked: {msg}")
        return 1
    state_fm["stage"] = "L4"
    state_fm["posture"] = "verify"
    # Increment cycle: first submit → 1, each re-submit after L4 feedback → +1
    state_fm["l4_cycle_count"] = int(state_fm.get("l4_cycle_count", 0)) + 1
    state_fm["research_loop_active"] = True
    state_fm["updated_at"] = _now_iso()
    save_state(root, state_fm, state_body)

    print(f"Candidate '{cand_id}' submitted → L4 verify (type={ctype})")
    return 0


def cmd_quick_compute(args):
    """Run a quick computation in a sandbox. No topic required."""
    import subprocess, sys, tempfile, os
    code = args.script or args.expr
    if not code:
        print("Provide --script or --expr")
        return 1

    # Safety preamble: block dangerous builtins and imports
    guard = (
        "import sys, os, builtins\n"
        "# AITP sandbox: restricted execution\n"
        "for _blocked in ('system', 'popen', 'spawn', 'exec', '__import__'):\n"
        "    os.__dict__.pop(_blocked, None)\n"
        "builtins.__dict__['__import__'] = lambda *a, **kw: (_ for _ in ()).throw("
        "ImportError('imports disabled in quick-compute sandbox. Use sympy or math only.'))\n"
        "# Pre-import allowed modules\n"
        "import math, cmath, json, re, itertools, functools, collections, typing\n"
        "try: import sympy\nexcept ImportError: pass\n"
        "try: import numpy as np\nexcept ImportError: pass\n"
    )
    code = guard + code

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        tmp = f.name
    try:
        result = subprocess.run([sys.executable, tmp], capture_output=True, text=True, timeout=60)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except subprocess.TimeoutExpired:
        print("Timeout (60s)")
        return 1
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def cmd_switch_activity(args):
    """Switch L3 activity — lightweight, no preflight."""
    root = _resolve_topic_root(args.topic)
    state_fm, state_body = _parse_md(root / "state.md")
    valid = ["ideate", "plan", "derive", "trace-derivation", "gap-audit", "integrate", "distill"]
    activity = args.activity
    if activity not in valid:
        print(f"Invalid activity '{activity}'. Valid: {valid}")
        return 1
    state_fm["l3_activity"] = activity
    state_fm["updated_at"] = _now_iso()
    _write_md(root / "state.md", state_fm, state_body)
    print(f"Switched to {activity}")
    return 0
