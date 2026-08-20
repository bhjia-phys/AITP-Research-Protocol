# M1e stage notes — evidence lifecycle + reviewed workstream backfill

Date: 2026-08-15
Spec: `docs/archive/m1e-evidence-lifecycle-backfill-spec.md`
Status: deterministic gate passed

## Implementation summary

- `records.py`: `sha256-once:` scheme in the single `_verify_refs` path with
  save/check grading; `validate_refs` uses save grading.
- `diagnostics.py`: optional `.aitp/local/check-policy.json` loader and
  matcher; `_grade_records` downgrades legacy strict `hash_mismatch` /
  `missing_ref` only for mutable policy matches. No policy file => unchanged
  code path.
- `backfill.py` + `cli.py` + `core.py`: dry-run-first
  `aitp backfill workstreams` with human-decision mapping anchor, surgical
  frontmatter workstreams block edit, idempotence, and JSON/text envelopes.
- `using-aitp` Skill updated with the new pin scheme, policy contract, and
  backfill protocol.
- Version strings synchronized to 0.7.0 on all four surfaces.

## Gate evidence

- Full ledger suite: **154 passed**.
  - New `tests/ledger/test_evidence_lifecycle.py` covers save-time strict
    `sha256-once`, check-time historical warning codes, mutable/immutable
    policy grading, malformed policy, and no-policy legacy strict behavior.
  - New `tests/ledger/test_backfill.py` covers dry-run zero-write, apply,
    idempotence, Entry and Note backfill, body preservation, human-decision
    anchor, invalid slugs, duplicate IDs, and missing records.
- Runtime nonblank lines: **1,793** (target ≤ 1,800 / cap ≤ 1,850).
  - `records.py` 379 (< 400); all other modules < 400.
- `git diff --check`: clean.
- Benchmark thresholds: unchanged and not re-tuned.
- Real-store acceptance: not measured, not claimed. The live GW_librpa and
  Power_Law_Heisenberg_Chain stores were inspected for natural demand but no
  policy files were installed by the gate.

## Boundaries

- `sha256-once:` and `check-policy` execute explicit record/policy
  declarations; they never infer whether drift is benign.
- No Entry/Note file schema changed; no old record content was rewritten by
  the runtime.
- `aitp backfill workstreams` only writes when `--apply` is supplied and a
  human decision pins the mapping.

## Post-gate live policy application

After the deterministic gate, reviewed `check-policy.json` files were written
for the two live dense stores. Check findings changed as follows (same
underlying records; no old Entry edited):

- GW_librpa: 218 errors / 2 warnings -> **23 errors / 197 warnings**.
- Power_Law_Heisenberg_Chain: 175 errors / 0 warnings -> **15 errors / 160 warnings**.

The remaining errors are strict immutable-evidence and unmatched-path
findings; the warnings are now explicitly historical drift/missing codes.
