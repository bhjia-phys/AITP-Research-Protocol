#!/usr/bin/env python3
"""Generate concrete example output for the full AITP v2 flow."""

import sys, os, tempfile, pathlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain import mcp_server
from tests.test_l3_subplanes import _bootstrap_l1_complete
from tests.test_l4_l2_memory import _bootstrap_with_candidate

SEPARATOR = "=" * 60

def main():
    with tempfile.TemporaryDirectory() as tmp:
        print(SEPARATOR)
        print("AITP v2 Protocol — Full Flow Example Output")
        print(SEPARATOR)

        # ── Step 1: Bootstrap topic ──
        print("\n[1] Bootstrapping topic 'demo-topic'...")
        result = mcp_server.aitp_bootstrap_topic(
            tmp, "demo-topic",
            title="AITP v2 Flow Verification",
            question="Does the AITP v2 protocol produce correct provenance chains?",
            lane="formal_theory")
        print(result)
        repo_root = pathlib.Path(tmp)
        tr = repo_root / "topics" / "demo-topic"

        # ── Step 2: Fill L1 artifacts ──
        print("\n[2] Filling L1 artifacts...")
        _bootstrap_l1_complete(tmp)

        # Ensure lane is set to formal_theory (bootstrap helper resets it)
        state_fm, state_body = mcp_server._parse_md(tr / "state.md")
        state_fm["lane"] = "formal_theory"
        mcp_server._write_md(tr / "state.md", state_fm, state_body)

        # ── Step 3: Get execution brief at L1 ──
        print("\n[3] Execution brief after L1 completion:")
        brief = mcp_server.aitp_get_execution_brief(tmp, "demo-topic")
        print(brief)

        # ── Step 4: Advance to L3 ──
        print("\n[4] Advancing to L3...")
        result = mcp_server.aitp_advance_to_l3(tmp, "demo-topic")
        print(result)

        # ── Step 5: Walk through L3 subplanes ──
        print("\n[5] Walking through L3 subplanes (ideation → distillation)...")
        for sp, artifact_name, fields, headings in [
            ("ideation", "active_idea.md",
             {"idea_statement": "Test AITP flow coherence", "motivation": "Verify full pipeline"},
             ["## Idea Statement", "## Motivation"]),
            ("planning", "active_plan.md",
             {"plan_statement": "Plan: trace full flow", "derivation_route": "Step-by-step verification"},
             ["## Plan Statement", "## Derivation Route"]),
            ("analysis", "active_analysis.md",
             {"analysis_statement": "Analyzing flow correctness", "method": "Unit tests + manual inspection"},
             ["## Analysis Statement", "## Method"]),
            ("result_integration", "active_integration.md",
             {"integration_statement": "Integration verified", "findings": "All stages connected properly"},
             ["## Integration Statement", "## Findings"]),
            ("distillation", "active_distillation.md",
             {"distilled_claim": "AITP v2 protocol produces correct provenance chain", "evidence_summary": "Tests pass, flow TeX renders"},
             ["## Distilled Claim", "## Evidence Summary"]),
        ]:
            mcp_server._write_md(
                tr / "L3" / sp / artifact_name,
                {"artifact_kind": f"l3_active_{sp}", "subplane": sp, **fields},
                "# Active\n\n" + "\n".join(f"{h}\nContent here." for h in headings) + "\n",
            )
            if sp != "distillation":
                next_sp = ["planning", "analysis", "result_integration", "distillation"][
                    ["ideation", "planning", "analysis", "result_integration"].index(sp)
                ]
                mcp_server.aitp_advance_l3_subplane(tmp, "demo-topic", next_sp)
                print(f"  → Advanced to {next_sp}")

        # ── Step 6: Submit candidate ──
        print("\n[6] Submitting candidate 'cand-1'...")
        mcp_server.aitp_submit_candidate(tmp, "demo-topic", "cand-1",
            "AITP v2 protocol produces correct provenance chain",
            "Tests pass, flow TeX renders correctly")

        # ── Step 7: L4 validation ──
        print("\n[7] Submitting L4 review...")
        mcp_server.aitp_submit_l4_review(
            tmp, "demo-topic", "cand-1", "pass", "All physics checks passed.")

        # ── Step 8: Flow notebook ──
        # Note: In production, the agent generates flow_notebook.tex during
        # L3 distillation with proper Markdown→LaTeX conversion.
        # Here we create a minimal placeholder for the demo.
        print("\n[8] Creating minimal flow_notebook.tex placeholder...")
        tex_dir = tr / "L3" / "tex"
        tex_dir.mkdir(parents=True, exist_ok=True)
        tex_path = tex_dir / "flow_notebook.tex"
        tex_path.write_text(
            "\\documentclass{article}\n\\begin{document}\nDemo\n\\end{document}\n",
            encoding="utf-8",
        )
        print(f"  Created {tex_path}")

        # ── Step 9: Promote candidate ──
        print("\n[9] Promoting candidate to global L2...")
        cand_path = tr / "L3" / "candidates" / "cand-1.md"
        fm, body = mcp_server._parse_md(cand_path)
        fm["status"] = "validated"
        fm["claim"] = "AITP v2 protocol produces correct provenance chain"
        mcp_server._write_md(cand_path, fm, body)
        mcp_server.aitp_request_promotion(tmp, "demo-topic", "cand-1")
        mcp_server.aitp_resolve_promotion_gate(tmp, "demo-topic", "cand-1", "approve")
        result = mcp_server.aitp_promote_candidate(tmp, "demo-topic", "cand-1")
        print(f"  {result}")

        # Show global L2 unit
        from brain.mcp_server import _global_l2_path
        g2 = _global_l2_path(tmp)
        l2_unit = g2 / "cand-1.md"
        if l2_unit.exists():
            print("\n--- Global L2 unit (cand-1.md) ---")
            print(l2_unit.read_text(encoding="utf-8"))
            print("--- end L2 unit ---")

        # ── Step 10: Runtime log ──
        print("\n[10] Runtime log:")
        log_path = tr / "runtime" / "log.md"
        if log_path.exists():
            print(log_path.read_text(encoding="utf-8"))

        # ── Step 11: Advance to L5 ──
        print("\n[11] Advancing to L5 writing...")
        mcp_server.aitp_advance_to_l5(tmp, "demo-topic")

        # Show L5 provenance files
        l5_dir = tr / "L5_writing"
        print("\n[12] L5 Writing provenance scaffolds:")
        for name in ["outline.md", "claim_evidence_map.md", "equation_provenance.md",
                      "figure_provenance.md", "limitations.md"]:
            fpath = l5_dir / name
            if fpath.exists():
                print(f"\n--- {name} ---")
                content = fpath.read_text(encoding="utf-8")
                # Show first 20 lines
                for i, line in enumerate(content.splitlines()):
                    if i >= 20:
                        print(f"  ... ({len(content.splitlines())} total lines)")
                        break
                    print(line)
                print(f"--- end {name} ---")

        # ── Final status ──
        print("\n" + SEPARATOR)
        print("Final status:")
        print(mcp_server.aitp_get_execution_brief(tmp, "demo-topic"))
        print(SEPARATOR)

if __name__ == "__main__":
    main()
