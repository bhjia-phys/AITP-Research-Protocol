# Phase 173: LibRPA QSGW Bounded Target And Trust Contract - Context

**Gathered:** 2026-04-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Choose one honest bounded positive `LibRPA QSGW` target for the
first-principles / code-method lane, then materialize an explicit
codebase/workflow trust contract for that target before any authoritative-L2
promotion claim.

</domain>

<decisions>
## Implementation Decisions

### Source-of-truth codebase posture
- Treat the local `LibRPA` checkout at
  `D:\BaiduSyncdisk\Theoretical-Physics\LibRPA-develop` as the primary code
  source of truth for codebase learning.
- Treat `D:\BaiduSyncdisk\repos\oh-my-LibRPA` as the existing orchestration
  layer and operator-facing workflow wrapper, not the scientific code source of
  truth.
- Treat the recent `el`-host QSGW run evidence as first-class supporting
  workflow truth for bounded trust decisions.

### Bounded target posture
- Do **not** try to ingest or validate the whole `LibRPA QSGW` stack in this
  phase.
- Start from the most concrete existing evidence chain: the
  `H2O/really_tight` QSGW workflow, its mixing/convergence experiments, and the
  already-recorded deterministic reduction / validation surfaces.
- Keep the eventual target bounded to one workflow, algorithmic, or
  code-method positive unit that can be backed by code anchors plus explicit
  validator receipts.

### Honesty constraints
- Mixing-only runs that failed the `1e-3 eV` convergence gate must remain
  explicit failures, not silently upgraded to positive closure claims.
- If the chosen positive target depends on Hamiltonian-cut controls,
  deterministic reductions, or another stabilizing mechanism, the trust
  contract must say so explicitly.
- Do not flatten codebase knowledge into generic prose; preserve file/module or
  workflow provenance from the start.

### the agent's Discretion
The exact bounded target may be a workflow claim, a code-module/algorithmic
claim, or a validated operating regime, as long as it is concrete enough for a
later authoritative-L2 unit and stays tied to the real `LibRPA QSGW` codebase.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- Local codebase candidate:
  `D:\BaiduSyncdisk\Theoretical-Physics\LibRPA-develop`
- Local orchestration/workflow wrapper:
  `D:\BaiduSyncdisk\repos\oh-my-LibRPA`
- Existing QSGW convergence memory:
  `librpa-qsgw-mixing-convergence-memory`
- Existing AITP codebase-learning protocol:
  `aitp-codebase-learning`

### Established Patterns
- The user has already converged the three long-term lanes to:
  - pure formal theory
  - toy model numerical + derivation
  - large codebase / first-principles / algorithm development
- `v1.97` and `v1.98` both closed by first choosing one bounded positive lane,
  then promoting one authoritative unit, then writing replay receipts.
- This milestone should reuse that same bounded-closure pattern instead of
  reopening broad architecture work.

### Integration Points
- Phase `173` should create the first codebase-to-AITP narrowing contract for
  the remaining third lane.
- Phase `173.1` can then consume that bounded target for authoritative-L2
  promotion.
- Phase `173.2` can then close the three-lane convergence baseline for later
  natural-language real-topic tests.

</code_context>

<specifics>
## Specific Ideas

- Candidate bounded targets to evaluate first:
  - one `H2O/really_tight` QSGW workflow closure with explicit convergence gate
  - one mixing/control code path with explicit validator-backed operating regime
  - one deterministic reduction or stability mechanism that can be linked
    directly to the codebase and replay receipts
- Existing evidence from recent QSGW runs already says:
  - mixing-only scans at `0.05` and `0.02/history=2` did **not** satisfy the
    `1e-3 eV` gate
  - the next honest control surface to test is likely the Hamiltonian-cut /
    stabilizing-knob family rather than pretending current mixing runs already
    converge

</specifics>

<deferred>
## Deferred Ideas

- Do not run broad three-lane natural-language dialogue tests in this phase.
- Do not try to close every `LibRPA` subworkflow or every benchmark system.
- Do not reopen the already-closed formal or bounded HS toy-model baselines
  except as later convergence references.

</deferred>
