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

You are in **validate** mode. Your job: verify candidates against their declared
validation criteria by **actually running computations or proofs** — NOT by self-certifying.

## What to Do

### Step 1: Read the candidate

Read `L3/candidates/<id>.md`. Note its:
- Claim
- Evidence provided
- Assumptions
- Validation criteria

### Step 2: Confirm execution environment

- Read the plan's Execution Environment section for the target machine.
- If no execution environment is documented, use AskUserQuestion to ask the human
  BEFORE running any computation.
- Verify you are on the correct machine (hostname, available packages).
- Do NOT run computations on the wrong machine.
- Record the machine name, OS, and key package versions.

### Step 3: Write validation scripts (MANDATORY for toy_numeric / code_method)

For numerical topics, you MUST write executable validation scripts. This is not optional.

1. **Create** validation scripts in `L4/scripts/`:
   - `L4/scripts/validate_<check_name>.py` — one script per major check
   - Each script must be self-contained and runnable on the target machine
   - Scripts must produce clear pass/fail output (print statements with results)
   - Each script MUST print provenance metadata: which data points it computed,
     how, and from what inputs

2. **Execute** scripts on the target machine:
   ```bash
   ssh <target_host> "cd <data_path> && python3 L4/scripts/validate_<check>.py"
   ```
   or use Jupyter MCP tools if available.

3. **Save** outputs to `L4/outputs/`:
   - Console output: `L4/outputs/<check_name>.log`
   - Plots/figures: `L4/outputs/figures/<check_name>.png`
   - Data tables: `L4/outputs/<check_name>.csv`

4. **Collect evidence paths** — you will need these when submitting the review.

### Step 4: Run validation checks

#### Numerical Validation
- Run benchmark comparisons — actual code execution, not paper reasoning
- Check convergence (parameter sweeps, finite-size scaling) — compute and plot
- Verify error budgets are within tolerance — calculate numerically
- All results must come from executed code, not from argumentation

For numerical work, use the **Jupyter MCP server** tools or Bash (ssh):
- `jupyter-mcp-server__connect_to_jupyter` — connect to running Jupyter
- `jupyter-mcp-server__use_notebook` — open a notebook for the validation
- `jupyter-mcp-server__insert_execute_code_cell` — run Python code inline
- `jupyter-mcp-server__read_cell` — read output for results
- Save generated plots to `L4/outputs/figures/` for L5 inclusion

#### Analytical Validation (formal_theory lane)
- Check limiting cases: do formulas reduce correctly?
- Dimensional analysis: do equations have correct dimensions?
- Symmetry checks: do results respect declared symmetries?
- Self-consistency: are different parts of the derivation compatible?

For formal verification, use the **Lean MCP server** tools:
- `lean-lsp-mcp__lean_goal` — check proof state at a position
- `lean-lsp-mcp__lean_diagnostic_messages` — find errors in formalization
- `lean-lsp-mcp__lean_leansearch` — search mathlib for relevant lemmas
- `lean-lsp-mcp__lean_multi_attempt` — test tactics without editing
- `lean-lsp-mcp__lean_verify` — verify a theorem with axiom check

#### Comparison Validation
- Compare candidate against known L2 results
- If contradiction found, record it explicitly

### Step 5: Submit L4 review with evidence and provenance

Call `aitp_submit_l4_review` with ALL of the following:

```
aitp_submit_l4_review(
    topics_root, topic_slug, candidate_id,
    outcome="pass" or "fail" or ...,
    notes="...",
    check_results={"check_name": "PASS/FAIL", ...},
    evidence_scripts=["L4/scripts/validate_xxx.py", ...],    # REQUIRED for numeric lanes
    evidence_outputs=["L4/outputs/xxx.log", ...],            # REQUIRED for numeric lanes
    execution_environment="Fisher (ssh Fisherd-Server100.96.1.64), Python 3.13.5",
    data_provenance=[                                         # REQUIRED for numeric lanes
        {
            "data_point": "OTOC area average at alpha=0.6, L=8",
            "script": "L4/scripts/validate_otoc_benchmark.py",
            "executed_at": "2026-04-21T03:20:00+08:00",
            "method": "Exact diagonalization in Sz=0/k=0/parity+ sector, time-averaged OTOC"
        },
        ...
    ],
)
```

The MCP server will **BLOCK** your submission if:
- Lane is `toy_numeric` or `code_method`
- Outcome is `pass`
- But `evidence_scripts` or `evidence_outputs` is missing

This is intentional — no self-certification for numerical claims.

### Step 6: Update candidate status

### Step 6: Update candidate status

- If passed: read the candidate .md, update frontmatter `status: validated`
- If failed: update `status: revision_needed`, explain what needs fixing
- If stuck: update `status: blocked`, explain what is missing

### Step 7: If candidate passes, update topic status

```
aitp_update_status(topics_root, topic_slug, status="validated")
```

### Step 8: Return to L3 (MANDATORY after pass)

After L4 pass, do NOT stop. Do NOT advance to L5 yet. You MUST return to L3:

```
aitp_return_to_l3_from_l4(topics_root, topic_slug, reason="post_l4_analysis")
```

Then follow the **post-L4 analysis flow** (see below).

## Post-L4 Analysis Flow (MANDATORY)

After returning to L3 from L4:

1. **Analyze** the L4 validation results in `L3/analysis/active_analysis.md`:
   - What passed? What was marginal? What was flagged as open question?
   - Were there quantitative discrepancies (e.g., normalization differences)?
   - Do the validated results suggest new questions or extensions?

2. **Update flow_notebook.tex** with the L4 findings (incremental update).

3. **Ask the human** (MANDATORY — use AskUserQuestion):
   - "L4 passed. The validated claim is: <claim>. Options:"
     - **Persist and advance**: promote to L2 / advance to L5 writing
     - **Continue iterating**: start a new L3 cycle (plan → analyze → integrate → distill → L4)
     - **Revise scope**: narrow or adjust the claim before persisting

4. **If human says "continue iterating"**:
   - Advance to `planning` subplane
   - Design new computational experiments based on L4 findings
   - Execute through the full L3 cycle (plan → analyze → integrate → distill)
   - Update flow_notebook.tex at each subplane
   - Submit new/updated candidate and re-enter L4

5. **If human says "persist and advance"**:
   - You may proceed to promotion (`aitp_request_promotion`) or L5 (`aitp_advance_to_l5`)

## Rules

- **L4 does NOT write to L2 directly.** All results return through L3-R.
- Do not weaken validation criteria to make a candidate pass.
- **No self-certification.** Every PASS must be backed by executed code or formal proof.
- **No anonymous data.** Every numerical data point used as evidence must have provenance:
  which script produced it, when it was executed, and what method was used. If you cannot
  trace a data point to a specific script execution, do NOT use it as evidence.
- **No stored-data-only checks.** Validation scripts that only load pre-existing JSON/data
  files and check their consistency are NOT independent validation. Each criterion must
  either be independently computed from scratch, or explicitly documented as "consistency
  check on stored data from <script> executed at <timestamp>".
- If you cannot complete validation (missing capability/source), record it honestly.
  Do not fake closure.
- Record what was checked, how, and what passed/failed — with file paths as evidence.
- **L4 pass does NOT mean "done".** After pass, return to L3 for analysis and human check.

## Validation Outcomes

| Outcome | Meaning | Next Step |
|---------|---------|-----------|
| `pass` | All criteria met, evidence provided | Route to promotion |
| `partial_pass` | Some criteria met | Determine if partial result is useful |
| `fail` | Criteria not met | Return to L3 for revision |
| `contradiction` | Contradicts known results | Open gap, investigate |
| `blocked` | Cannot complete | Record blocker, escalate if needed |
