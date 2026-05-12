"""L4 verification commands: verify run, verify results, promote."""
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


# ── Shared functions (used by both CLI and MCP) ─────────────────────────

def _build_verify_spawn_json(root: Path, candidate_id: str) -> dict:
    """Build the verifier spawn plan dict. Shared by CLI and MCP.

    Returns a dict with: candidate, topic, claim, chain, type, verifiers,
    preflight_checks, isolation, parallel, next_command.

    Study mode (atomic_concept, derivation_chain): 1 adversarial verifier.
    Research mode (all other types): 3 verifiers (algebraic, physical, numerical).
    """
    cand_path = root / "L3" / "candidates" / f"{candidate_id}.md"
    if not cand_path.exists():
        raise FileNotFoundError(f"Candidate '{candidate_id}' not found")

    cand_fm, cand_body = _parse_md(cand_path)
    claim = cand_fm.get("claim_statement", "")
    chain_id = cand_fm.get("derivation_chain_id", "default")
    ctype = cand_fm.get("candidate_type", "research_claim")
    topic = root.name

    if ctype in ("atomic_concept", "derivation_chain"):
        verifiers = [
            {"type": "adversarial", "prompt": "brain/agents/skeptic.md",
             "input": f"L3/candidates/{candidate_id}.md (study mode: source anchoring + coverage check)",
             "output": f"L4/reviews/{candidate_id}_adversarial.md"},
        ]
        preflight_checks = ["source_chain_anchored", "coverage_completeness_check"]
    else:
        verifiers = [
            {"type": "algebraic", "prompt": "brain/agents/algebraic_verifier.md",
             "input": f"L3/candidates/{candidate_id}.md + L2/graph/steps/ (chain={chain_id})",
             "output": f"L4/reviews/{candidate_id}_algebraic.md"},
            {"type": "physical", "prompt": "brain/agents/physical_verifier.md",
             "input": "claim statement + L2 access",
             "output": f"L4/reviews/{candidate_id}_physical.md"},
            {"type": "numerical", "prompt": "brain/agents/numerical_verifier.md",
             "input": "candidate + L4/outputs/ + compute/targets.yaml",
             "output": f"L4/reviews/{candidate_id}_numerical.md"},
        ]
        preflight_checks = []

    return {
        "candidate": candidate_id, "topic": topic,
        "claim": claim[:200], "chain": chain_id, "type": ctype,
        "verifiers": verifiers,
        "preflight_checks": preflight_checks,
        "isolation": "worktree", "parallel": True,
        "next_command": f"aitp verify results {topic} --candidate {candidate_id}",
    }


def _compute_verify_results(root: Path, candidate_id: str) -> dict:
    """Read L4 review files and compute disagreement matrix.

    Returns dict with: candidate, results (per-verifier outcome), verdict, next_action.
    """
    reviews_dir = root / "L4" / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)

    review_types = ["algebraic", "physical", "numerical", "skeptic"]
    results = {}
    for rtype in review_types:
        path = reviews_dir / f"{candidate_id}_{rtype}.md"
        if path.exists():
            fm, _ = _parse_md(path)
            results[rtype] = fm.get("outcome", "unknown")
        else:
            results[rtype] = "missing"

    outcomes = list(results.values())
    if "missing" in outcomes:
        verdict = "incomplete"
    elif all(o == "pass" for o in outcomes):
        verdict = "unanimous_pass"
    elif all(o in ("pass", "fail") for o in outcomes) and "fail" in outcomes:
        verdict = "divergent"
    else:
        verdict = "mixed"

    state_fm, state_body = _parse_md(root / "state.md")
    state_fm["l4_verdict"] = verdict
    _write_md(root / "state.md", state_fm, state_body)

    result = {"candidate": candidate_id, "results": results, "verdict": verdict}

    if verdict == "unanimous_pass":
        result["next_action"] = (
            "All verifiers passed. Spawn Skeptic agent "
            "(brain/agents/skeptic.md) with claim-only input. "
            "If Skeptic passes, call aitp_promote_candidate."
        )
    elif verdict == "divergent":
        result["next_action"] = (
            "Disagreement among verifiers. Human review recommended. "
            "Examine individual review files in L4/reviews/."
        )
    elif verdict == "incomplete":
        result["next_action"] = (
            "Some verifier reviews missing. Run remaining verifiers, "
            "then re-run aitp_verify_results."
        )
    else:
        result["next_action"] = f"Verdict '{verdict}'. Human review recommended."

    return result


# ── CLI entry points ────────────────────────────────────────────────────

def cmd_verify_run(args):
    """Spawn verification agents for a candidate. Prints spawn JSON to stdout."""
    root = _resolve_topic_root(args.topic)
    from brain.cli.preflight import run_preflight

    failures = run_preflight("verify-run", root, candidate_id=args.candidate_id)
    if failures:
        print("Preflight blocked:")
        for f in failures:
            print(f"  * {f}")
        return 1

    try:
        spawn_json = _build_verify_spawn_json(root, args.candidate_id)
        import json
        print(json.dumps(spawn_json, indent=2, ensure_ascii=False))
        return 0
    except FileNotFoundError as e:
        print(str(e))
        return 1


def cmd_verify_results(args):
    """Collect Verifier outputs and generate disagreement matrix. Prints to stdout."""
    root = _resolve_topic_root(args.topic)
    from brain.cli.preflight import run_preflight

    failures = run_preflight("verify-results", root, candidate_id=args.candidate_id)
    if failures:
        print("Preflight blocked:")
        for f in failures:
            print(f"  * {f}")
        return 1

    result = _compute_verify_results(root, args.candidate_id)

    print(f"""
  VERIFICATION RESULTS -- {args.candidate_id}

  | Verifier     | Outcome    |
  |-------------|-----------|""")
    for rtype, outcome in result["results"].items():
        print(f"  | {rtype:<11} | {outcome:<10} |")
    print(f"\n  Verdict: {result['verdict']}")
    print(f"\n  {result['next_action']}")

    return 0


def cmd_promote(args):
    """Promote a validated candidate to L2."""
    root = _resolve_topic_root(args.topic)
    from brain.cli.preflight import run_preflight

    failures = run_preflight("promote", root, candidate_id=args.candidate_id)
    if failures:
        print("Preflight blocked:")
        for f in failures:
            print(f"  * {f}")
        return 1

    state_fm, state_body = _parse_md(root / "state.md")
    cand_path = root / "L3" / "candidates" / f"{args.candidate_id}.md"

    if not cand_path.exists():
        print(f"Candidate '{args.candidate_id}' not found")
        return 1

    verdict = state_fm.get("l4_verdict", "")
    if verdict not in ("unanimous_pass",):
        print(f"Verification not complete. Current verdict: {verdict or 'none'}")
        print("Run 'aitp verify results' first.")
        return 1

    # Skeptic gate: must pass blind adversarial review before promotion
    skeptic_path = root / "L4" / "reviews" / f"{args.candidate_id}_skeptic.md"
    if not skeptic_path.exists():
        print(f"Skeptic review not found: {skeptic_path}")
        print("Run the Skeptic agent (brain/agents/skeptic.md) before promoting.")
        return 1
    sfm, _ = _parse_md(skeptic_path)
    skeptic_outcome = sfm.get("outcome", "unknown")
    if skeptic_outcome != "pass":
        print(f"Skeptic review outcome: {skeptic_outcome} (requires 'pass')")
        print("Address the Skeptic's concerns before re-submitting.")
        return 1
    print(f"Skeptic gate: {skeptic_outcome}")

    # Update candidate status
    cand_fm, cand_body = _parse_md(cand_path)
    cand_fm["status"] = "validated"
    _write_md(cand_path, cand_fm, cand_body)

    # Advance to promotion
    from brain.cli.state import validate_state_transition, save_state
    ok, msg = validate_state_transition(root, "promotion")
    if not ok:
        print(f"Stage transition blocked: {msg}")
        return 1
    state_fm["research_loop_active"] = False
    state_fm["stage"] = "promotion"
    state_fm["updated_at"] = _now_iso()
    save_state(root, state_fm, state_body)

    print(f"Candidate '{args.candidate_id}' promoted to validation. Ready for human review -> L2.")
    return 0
