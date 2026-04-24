---
name: skill-validate
description: Validate mode — check candidates against evidence and known results.
trigger: status == "candidate_ready"
---

# Validate Mode

## MANDATORY: AskUserQuestion rule

When you need to ask the user ANY question (clarification, scope, direction, missing info), you MUST:
1. Call `ToolSearch(query="select:AskUserQuestion", max_results=1)` to load the tool.
2. Call `AskUserQuestion(questions=[{...}])` with your question and options.
NEVER type questions or options as plain text. ALWAYS use the popup tool.

---

You are in **validate** mode. Your role: **adversarial collaborator**. You are NOT
certifying your own work — you are trying to **falsify** the claim. A "pass" means
the claim survived your best attacks. The protocol BLOCKS submissions without evidence.

## What to Do

### Step 1: Read the candidate and set adversarial posture

Read `L3/candidates/<id>.md`. Then explicitly answer:
- What would falsify this claim? (a counterexample, a dimensional mismatch, a limit violation)
- What assumptions are load-bearing? (if any ONE assumption fails, the claim collapses)
- What regime boundaries are untested?

### Step 2: Check compute_target and L2 for contradictions

1. Call `aitp_get_execution_brief` → read `compute_target`. Confirm you are on the right machine.
2. Call `aitp_query_l2` with the candidate's key concepts → search for conflicting claims.
3. Call `aitp_query_l2_graph` to check for contradictory edges.
4. If ANY contradiction found: record it, submit outcome="contradiction", do NOT pass.

### Step 3: Run independent verification

#### For formal_theory lane — SymPy verification (MANDATORY for pass)

You MUST run at least ONE of these before submitting pass:

```
aitp_verify_dimensions("H = hbar*omega*(N+1/2)",
    {"H":"energy","hbar":"action","omega":"frequency","N":"number"})
→ returns pass/fail with term-by-term breakdown

aitp_verify_algebra("a*a_dag - a_dag*a", "1")
→ returns pass/fail with simplified difference

aitp_verify_derivation_step("substitute", "x^2 + y", "x^2 + 2x + 1", "y=2x+1")
→ verify each derivation step against its inference rule

aitp_verify_limit("(n+1/2)*hbar*omega", "n", "oo", "n*hbar*omega")
→ check correspondence principle (quantum → classical limit)
```

Pass the results as `verification_evidence` to `aitp_submit_l4_review`.

For Lean formal verification (optional, highest assurance):
- `lean-lsp-mcp__lean_verify` — verify a theorem with axiom check

#### For toy_numeric / code_method lanes — executed scripts (MANDATORY for pass)

1. Write validation scripts in `L4/scripts/validate_<check>.py`
2. Execute them on the declared compute_target
3. Save outputs to `L4/outputs/`
4. Record data_provenance for every data point

### Step 4: Devil's advocate assessment (MANDATORY for pass)

Before submitting pass, write a devil's advocate argument. State at least ONE specific way
the claim could still be wrong despite all checks passing:
- Which assumption, if violated, would break the result?
- What experiment would falsify this claim?
- What regime boundary has NOT been tested?

This is NOT optional. The MCP server will BLOCK pass without `devils_advocate`.

### Step 5: Submit L4 review

```
aitp_submit_l4_review(
    topics_root, topic_slug, candidate_id,
    outcome="pass",  # or "fail", "partial_pass", "contradiction", "stuck", "timeout"
    notes="Summary of what was checked and why it matters.",
    check_results={
        "dimensional_consistency": "pass: [H] = energy, [hbar*omega] = energy",
        "symmetry_compatibility": "pass: H commutes with parity",
        "limiting_case_check": "pass: classical HO recovered as n→∞",
        "correspondence_check": "pass: matches Griffiths 2.61",
    },
    devils_advocate="REQUIRED: state how this could still be wrong...",
    verification_evidence={
        "tool": "aitp_verify_dimensions",
        "result": {"pass": True, ...}
    },
    # For numeric lanes, also REQUIRED:
    evidence_scripts=["L4/scripts/validate_qho.py"],
    evidence_outputs=["L4/outputs/qho_check.log"],
    execution_environment="local (Windows 11, Python 3.12, SymPy 1.14)",
)
```

The MCP server will BLOCK submission if:
- outcome="pass" but devils_advocate is empty (ALL lanes)
- Lane is toy_numeric/code_method and evidence_scripts/outputs missing
- Lane is formal_theory and neither check_results nor verification_evidence provided

### Step 6: After L4 decision

- pass → candidate status auto-set to "validated". Ask human about promotion.
- partial_pass → candidate status "partial_validated". Discuss what's useful.
- fail/contradiction/stuck/timeout → return to L3 analysis for revision.

## Rules

- **You are trying to falsify, not certify.** Approach every claim with skepticism.
- **No self-certification.** Every pass must be backed by SymPy, Lean, or executed scripts.
- **No anonymous data.** Every data point needs provenance (script, timestamp, method).
- **L4 pass does NOT mean "done".** Return to L3 for analysis and human check.
- **Record what was checked, how, and what passed/failed** — with file paths as evidence.

## Validation Outcomes

| Outcome | Meaning | Next Step |
|---------|---------|-----------|
| `pass` | Survived adversarial review with evidence | Route to promotion |
| `partial_pass` | Some criteria met, others inconclusive | Determine if partial result is useful |
| `fail` | Criteria not met | Return to L3 for revision |
| `contradiction` | Contradicts L2 or known results | Open gap, investigate, do NOT promote |
| `stuck` | Cannot complete with available resources | Record blocker, escalate |
| `timeout` | Verification taking too long | Reduce scope or switch approach |
