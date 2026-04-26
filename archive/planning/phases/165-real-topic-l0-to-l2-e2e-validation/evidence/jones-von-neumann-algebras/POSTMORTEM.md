# Postmortem: Jones Von Neumann Algebras — Lean Formalization E2E

## Topic

- **initial idea**: Add a range-facing LinearEquiv theorem for |A| on the support submodule in the Jones (2015) finite-coordinate finite-dimensional polar decomposition model, as part of the Chapter 2 polar backbone.
- **chosen front door**: opencode (oh-my-opencode)
- **topic slug**: `jones-von-neumann-algebras`
- **run date**: 2026-04-12

## Route Taken

- **entry path**: continued existing topic (not fresh bootstrap). Topic runtime shell already existed from prior runs.
  - **Protocol deviation**: The E2E runbook requires using "current public AITP entry surfaces" (`aitp explore` or `aitp bootstrap`). This run bypassed those surfaces and continued directly from conversation context. This means we did NOT validate the public entry path in this E2E run.
- **key commands**:
  - Local: `lake build JonesVonNeumannDefinitions` (2800 jobs, 0 errors)
  - Remote: SSH to el, `lake build JonesVonNeumannDefinitions.Jones2015.Section2PolarSupportProjection` (2605 jobs, 0 errors)
  - AITP runtime: manual sync of 6 markdown/JSON files + 1 lightweight knowledge packet (NOT a canonical L2 CanonicalUnit)
- **actual layer/subplane path**: L3 (implementation) → L4 (validation: local + remote) → runtime knowledge packet (NOT canonical L2)
  - Important distinction: the created packet is a lightweight agent-facing `KnowledgePacket` in `runtime/topics/<slug>/knowledge_packets/`, not a canonical `CanonicalUnit` in `canonical/`. No promotion to canonical L2 actually occurred.
- **final bounded outcome**: `validated` at theorem level — Lean code compiles locally and remotely. However: (1) proof engineering knowledge was NOT captured in any persistent reusable form, (2) no artifact was promoted to canonical L2, and (3) the public AITP entry surface was bypassed.

## What Helped

1. **AITP `topic_skill_projection`** — scope constraints like "don't touch Chapter 4" and "keep abstract/concrete boundary" were respected throughout, preventing scope creep.
2. **`validation_contract.active.md`** — provided a clear target for what "done" looks like (local build + remote build pass).
3. **Existing reference patterns** — `Section4FiniteDimensionalBlockProjectionCentralizer.lean` (lines 620-677) provided the codRestrict pattern that ultimately worked.
4. **Remote el validation** — in this specific run both local and remote passed identically, so no extra bugs were caught. However, the discipline of mandatory remote re-validation prevented us from claiming victory prematurely in earlier rounds (where local might have passed but remote would have diverged).

## What Created Friction

1. **No reusable proof engineering memory** — 7 rounds of iteration (rounds 1-6 all failed) produced zero reusable artifacts. Each failure was a unique discovery about mathlib API patterns, tactic workarounds, and construction recipes. None of these were captured in any AITP persistent surface. → **issue:e2e-proof-engineering-knowledge-gap**
2. **`strategy_memory.jsonl` exists in code but has zero rows** — the mechanism for recording strategy lessons is fully implemented (reader, writer, consumer) but was never used during this topic run. → **issue:e2e-strategy-memory-empty**
3. **`proof_fragment` unit_type reserved but no schema** — the 23-family L2 canonical system has `proof_fragment` as a typed family, but no JSON schema file exists, no payload contract is defined, and no instances have been created. → **issue:e2e-proof-fragment-no-schema**
4. **`negative_result` reserved but not activated** — failed proof approaches (wrong codRestrict argument order, non-existent lemmas, CoeFun coercion issues) are valuable negative knowledge but have no canonical home. → **issue:e2e-negative-result-inactive**
5. **Runtime proof schemas have no L2 promotion path** — `lean-ready-packet`, `proof-repair-plan`, `statement-compilation-packet` schemas exist at the runtime layer but cannot be promoted to canonical L2 storage. → **issue:e2e-runtime-to-l2-no-promotion**

## Key Proof Engineering Discoveries (Not Captured Anywhere)

These are the findings from 7 rounds that should have been recorded:

| # | Discovery | Category | Reuse Scope |
|---|-----------|----------|-------------|
| 1 | Two-step codRestrict+comp pattern: codRestrict f.toLinearMap to range, then comp Submodule.subtype | construction recipe | All submodule→submodule LinearMap/LinearEquiv |
| 2 | CoeFun coercion hides CLMap structure; `rw [ContinuousLinearMap.map_sub]` fails; use `have h := LinearMap.map_sub _ _ _` instead | tactic workaround | Any code mixing CLMap and LinearMap |
| 3 | `sub_eq_zero` direction: `rw` goes L→R (a-b=0→a=b), `.mpr` goes R→L | tactic gotcha | Any proof using subtraction |
| 4 | `Submodule.range_starProjection` needs explicit `(U := ...)` for instance inference | API gotcha | Any code using starProjection range |
| 5 | `jonesFiniteCoordinatePolarPositivePart_ker_eq_ker` bridges ker |A| = ker A for kernel membership | domain lemma | Future Chapter 2 proofs |
| 6 | `show f (x-y) = 0` fails when goal is `f x - f y = 0`; use `have` + `rw` instead | tactic gotcha | Any proof goal massaging |

## Outcome

The topic reached **`validated`** at the theorem level: the Lean code compiles locally and remotely, and a knowledge packet was created. However, at the **proof engineering knowledge** level, the outcome is **`incomplete`** — valuable construction recipes, tactic workarounds, and failure patterns were discovered but not durably captured.

## Follow-Up

### Urgent GSD Follow-Up

- **Phase 165.1**: Define `proof_fragment` schema + seed `strategy_memory.jsonl` with the 6 discoveries above (issues 1-3)

### Next Milestone Candidates

- Create the Jones codRestrict `proof_fragment` instance as first canonical proof engineering object (after 165.1 ships schema)
- Activate `negative_result` in staging → canonical promotion pipeline (issue 4)
- Define runtime→L2 promotion path for proof engineering knowledge (issue 5)
- Make `topic_skill_projection` enforcement mandatory rather than advisory
- Re-run E2E with a fresh topic using the actual public entry surfaces (`aitp bootstrap`)

### Backlog-Worthy Findings

- `topic_skill_projection` enforcement strength (currently advisory)
- Cross-topic proof_fragment reuse validation (do Lean4 tactics from one topic apply to another?)
