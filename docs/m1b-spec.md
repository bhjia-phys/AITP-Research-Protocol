# M1b — Open items and behavior pilot: pre-specification

Status: pre-spec; blocked until the M1a gate and fixed-cap line-budget reconciliation.

This document freezes the M1b design per `docs/roadmap.md` §M1b (v3.4) and
`docs/m1-read-write-balance.md` §M1b. It is **not** an implementation-level
specification and does **not** green-light M1b runtime work. Implementation
may start only when all of the following hold:

1. the M1a gate has passed (roadmap stage table);
2. the line-budget reconciliation of §12 has been performed and recorded in
   the implementation spec;
3. a separate implementation-level spec derived from this freeze has been
   reviewed and green-lit.

Until then the roadmap stage table governs: M1b stays design only. The
`aitp/lite-entry-0.2` freeze milestone listed there is achieved by this
document, which is not the same as permission to code.

## 0. Binding rules

- Semantics below are frozen. The post-gate implementation spec may choose
  implementation economy (shared validators, single-pass scans, module
  placement) but may not weaken, extend, or re-interpret these rules.
- Templates and Skills are part of the deliverable. Templates are not counted
  in the Python line budget, but their section sets are frozen here; exact
  prompt wording is fixed by the implementation spec.
- Everything in this document stays inside the trust model: auditable and
  tamper-evident, never tamper-proof. Nothing here promises detection of
  forged attribution, early outcome exposure, or dishonest claims.

## 1. Schema freeze — `aitp/lite-entry-0.2`

`prepare_entry` emits `schema: aitp/lite-entry-0.2`; `save_entry` accepts both
schemas. New frontmatter fields are all optional: `kind` gains
`prediction` and `question`; `based_on`; `resolution`; `contradicts`;
`citekey` and `trust` on `source` Entries only. `resolves` and `supersedes`
keep their v0.1 list shape.

Validation is version-scoped:

- Existing canonical records carrying `aitp/lite-entry-0.1` remain valid under
  today's field rules: no `resolution` requirement, multi-target `resolves`
  permitted, and `based_on`/`contradicts`/`citekey`/`trust` fields carry no
  semantics. None is migrated, rewritten, or re-validated under 0.2 rules.
  After M1b, a newly saved resolver that targets a 0.2 open item must itself
  use schema 0.2 and carry the typed `resolution`; a hand-written v0.1 draft
  attempting that cross-version closure is rejected as `invalid_resolution`.
- A record carrying `aitp/lite-entry-0.2` is validated under §2–§5.
- A 0.2 `prediction` Entry must carry at least one pinned `ref` (a `refs`
  entry with an `at:` pin) and at least one `limitation` at save time
  (`missing_refs` / `missing_limitations` otherwise): a prediction is a
  falsifiable claim, and the Planned Test section prompts for the
  constraining evidence and the acknowledged limitations.
- Relation targets may cross schema versions: a 0.2 resolver may close a
  v0.1 open item (kind rules apply to the target's `kind` field, not its
  schema). `used_by` derivation covers all schemas; v0.1 records simply have
  no `based_on`, so they never appear as sources.
- Notes keep `aitp/lite-note-0.1`; only the `supersedes` validation of §6 is
  added, and it applies to all Notes.

## 2. `based_on` — frozen rules

```yaml
based_on:
  - entry-<32hex>
```

Definition (fixed): the durable claim in this Entry materially depends on
the recorded content of the target Entry.

- Optional; v0.1 records remain valid without it.
- A list of Entry IDs only (no Notes, no paths, no pins); no self-target;
  every target must already exist at save time (save-time target-existence
  is the protocol-order guarantee; `created_at` is not causal proof).
- It expresses a claim dependency — not chronology, topical similarity, or
  replacement — and it never satisfies a kind's evidence-`refs` requirement.
- Dependence on a superseded Entry is allowed for history but is a
  **warning**, not an error: reported at save time through a new optional
  `warnings` list on the **save payload** (only present when a non-blocking
  condition exists; no warning ⇒ payload unchanged) and by `aitp check` as
  `based_on_superseded` — nowhere else. `prepare` adds no flag and no
  `warnings` field; supersession of an existing target is only checkable
  at save, not at prepare.
- `aitp check` validates all targets (`missing_relation` when absent).

## 3. `used_by` — reverse of `based_on` only

- `used_by` lists exactly the Entries whose `based_on` includes this Entry.
  `resolves`, `supersedes`, and `contradicts` contribute nothing; v0.1
  records contribute nothing.
- Derived by scanning canonical Markdown (one pass builds the reverse map);
  no reverse index, cache, or derived file is ever written.
- Exposed in M1b by `aitp show` (text `used_by:` line; `--json` payload key)
  and by `enter`'s per-Entry projections. `aitp list` gains nothing.
- The M1a payload schemas are frozen (`aitp/enter-0.2`, `aitp/show-0.1`);
  M1b's field additions ship as **new frozen schema versions** — the M1b
  implementation spec must freeze `aitp/enter-0.3` and `aitp/show-0.2`
  (additive bumps) before implementation. A frozen payload schema version is
  never edited in place; changing one is always a versioned bump.

## 4. `resolves` and `resolution` — frozen rules

- `resolves` remains a YAML list but in 0.2 records holds **exactly zero or
  one** target (`resolves_multiple` when longer). To close two items with one
  piece of work, write two resolving Entries; both may pin the same evidence.
- The target must exist (`missing_relation`) and be an open-item kind —
  `failure` | `prediction` | `question` (`resolves_target_kind` otherwise).
- `resolution` is a single string, present if and only if `resolves` is
  non-empty (`invalid_resolution` otherwise), and must be an allowed closure
  for the target kind:

  | Target kind | Allowed closures |
  |---|---|
  | `failure` | `fixed`, `cancelled`, `invalidated` |
  | `prediction` | `observed`, `cancelled`, `invalidated` |
  | `question` | `answered`, `cancelled`, `invalidated` |

  `cancelled` means the test or work was abandoned — never an outcome;
  `invalidated` means the item itself was ill-posed or based on an error.
  These meanings are stated in the Skill, not machine-checked.

- `observed` resolver evidence (frozen): a closure of `observed` requires
  (a) the resolving Entry's kind is `observation`, `result`, or `run`
  (`resolver_kind_mismatch` otherwise); (b) at least one pinned `ref`
  (enforced for every `observed` closure regardless of authority —
  `missing_refs` when absent). The body's statement of the outcome against
  the written expectation — matched, partly matched, or did not match, and
  why — is a body convention (prompted by the prediction template's Planned
  Test section and the Skill), auditable in Git, and not machine-checked.
- No other closure carries extra structural requirements; any Entry kind may
  carry `fixed`, `cancelled`, `invalidated`, or `answered`.
- Reopen: the existing M0 mechanism extends to all three kinds — when a
  resolving Entry is superseded and no other active resolver remains, the
  target reopens. No new closure state is added for this.

## 5. `contradicts` — structural boundary

- A contradiction is not a kind. It is a 0.2 `failure` Entry carrying
  `contradicts: [A, B]` — exactly two distinct, existing Entry IDs, neither
  self, both of kind `failure` (`invalid_contradicts` for shape/self/dupes,
  `contradicts_target_kind` for a non-failure target, `missing_relation` for
  a missing target).
- Present on a non-`failure` kind ⇒ `invalid_contradicts`.
- The validator checks structure, not substance. The claim that both sides
  share one validity domain and one set of conventions, are expected to hold
  simultaneously, and are logically or numerically incompatible is the
  author's claim. Python validates only the `contradicts` structure: the two
  distinct failure targets, both existing, neither self, both present — plus
  the ordinary `failure` template sections.
- A contradiction is recorded through the ordinary `record prepare --kind
  failure` path — no dedicated template, no new prepare flag. The existing
  `failure.md` template's Evidence And Next Diagnostic section is updated to
  prompt, when `contradicts` is present, for the contradiction domain and
  conventions shared by both sides; why coexistence is impossible; and
  pinned evidence for both sides (the Entry's own `refs`). `empty_section`
  applies as usual; the substance of these prompts is never machine-checked.
- Competing hypotheses not yet discriminated, and claims in disjoint validity
  domains, are not contradictions — they live as hypothesis artifacts or open
  questions (Skill discipline; not machine-checkable).
- `enter` groups unsettled contradictions (open items whose `contradicts`
  targets are both still active) in its M1b output.

## 6. Note `supersedes` validation — frozen

`save_note` and `aitp check` validate a Note's `supersedes` like Entry
supersession plus a kind boundary: list of Note IDs only
(`invalid_supersedes_target` for a non-Note target), no self-target, target
exists (`missing_relation`), target `created_at` older
(`invalid_supersession`). Entry `supersedes` likewise requires Entry targets
(`invalid_supersedes_target`). A superseded Note remains readable; nothing is
rewritten. (The GW_librpa corpus contains no Notes, so no legacy exposure.)

## 7. `aitp check` — frozen contract

### 7.1 CLI

```
aitp check [--json] [--cwd PATH]
```

Whole-store re-validation: every canonical Entry and Note, using the same
structural validators as the save path, plus relation closure rules
(§2, §4, §5, §6). Store metadata must load (`not_initialized`,
`malformed_store` → cannot run).

### 7.2 Read-only scope

`check` writes nothing: no lock file (it must not take `store_lock`, which
creates a file), no cache, no index, no repair, no migration, no scratch, no
new canonical files, no `--fix` flag now or later. It is a projection like
`enter`/`list`/`show`. A test asserts the `.aitp` tree is byte-identical
before and after a check run.

### 7.3 Exit codes

- `0` — clean: zero findings.
- `1` — findings: at least one error or warning reported.
- `2` — could not run: not a workspace, unreadable store, or CLI misuse
  (argparse and `AITPError` paths keep the existing text/JSON error shapes
  and exit-2 behavior).

### 7.4 Error/warning principle

- **Error** — the record's own content violates a protocol contract: schema,
  fields, kinds, sections, relations, closures, duplicate IDs, unfilled
  template prompts, or a pin that fails verification (`missing_ref`,
  `hash_mismatch`, `invalid_run_ref`, a `git:` pin verified wrong). The
  record as written is invalid.
- **Warning** — the record is valid as written but its referenced world is
  degraded in a way the save path never grades: `based_on` on a superseded
  target (stale dependency), a `based_on`/`supersedes` cycle, an open item
  closed by more than one active resolver (double resolution), invalid
  legacy timestamps, or a `git:` pin that cannot be verified because the Git
  environment is unavailable.
- Grading is by this principle, not by code name: `missing_ref`/`hash_mismatch`
  block a save today and remain **errors** in `check` — one grading rule,
  never two. The implementation must split world-dependent pin checks from
  structural checks inside the ref validator so `check` can grade them
  separately — including telling "Git is available and the commit lacks the
  target" (error) apart from "no Git / not a Git work tree, cannot verify"
  (warning); save-time semantics do not change.
- Warnings never block; errors in a store do not crash reads (`enter`/`list`/
  `show` never run `check`).

### 7.5 JSON — `aitp/check-report-0.1`

```json
{
  "schema": "aitp/check-report-0.1",
  "status": "clean" | "findings",
  "root": "<absolute path>",
  "counts": {"entries": 60, "notes": 1, "errors": 3, "warnings": 2},
  "findings": [
    {
      "level": "error" | "warning",
      "code": "invalid_supersession",
      "path": ".aitp/topic/entries/entry-<hex>.md",
      "message": "supersedes target is not older: entry-<hex>"
    }
  ]
}
```

Findings sort deterministically by `(path, code)`; the report carries no
volatile fields (no wall-clock timestamp), so its output is golden-testable.
Text mode prints one line per finding to stdout
(`error[code]: path: message` / `warning[code]: path: message`) plus a
summary line; `--json` emits the payload above. `findings` is empty when
status is `clean`.

### 7.6 Core diagnostic codes

New codes (existing codes — `malformed_record`, `unreadable_record`,
`duplicate_id`, `missing_field`, `invalid_schema`, `invalid_id`,
`topic_mismatch`, `invalid_kind`, `invalid_authority`, `missing_summary`,
`invalid_limitations`, `missing_limitations`, `missing_refs`, `invalid_refs`,
`invalid_ref`, `invalid_ref_pin`, `invalid_retrieved_ref`,
`invalid_version_ref`, `unfilled_template`, `empty_section`,
`invalid_relation`, `missing_relation`, `invalid_supersession`, `missing_ref`,
`hash_mismatch`, `invalid_run_ref` — are reused for errors (a pin that fails
verification makes the record invalid as written, exactly as on the save
path); `invalid_git_ref` is reused for both grades — error when Git is
available and the commit genuinely lacks the target, warning when the Git
environment is unavailable (no Git binary, or the workspace is not inside a
Git work tree) so the pin cannot be verified):

| Code | Level | Meaning |
|---|---|---|
| `resolves_multiple` | error | 0.2 record: `resolves` has more than one target |
| `resolves_target_kind` | error | 0.2 record: `resolves` target is not `failure`/`prediction`/`question` |
| `invalid_resolution` | error | 0.2 record: `resolution` not in the target kind's enum, present without target, or absent with target |
| `resolver_kind_mismatch` | error | 0.2 record: `resolution: observed` on a non-`observation`/`result`/`run` Entry |
| `invalid_contradicts` | error | 0.2 record: `contradicts` on a non-failure kind, or not exactly two distinct non-self IDs |
| `contradicts_target_kind` | error | 0.2 record: a `contradicts` target is not a failure Entry |
| `invalid_supersedes_target` | error | `supersedes` target is not a Note ID (Notes) or Entry ID (Entries) |
| `invalid_pointer_bundle` | error | pinned pointer bundle does not parse or lacks schema `aitp/run-pointer-0.1` |
| `based_on_superseded` | warning | `based_on` target is superseded (also reported in the save payload) |
| `invalid_timestamp` | warning | `created_at` does not parse as ISO (legacy records; never crashes reads) |
| `relation_cycle` | warning | a cycle in `based_on`/`supersedes` links — each record is valid as written, the relation graph is degraded |
| `double_resolution` | warning | an open item closed by more than one active resolver |

## 8. Remote evidence — local pointer bundle (frozen)

- A remote path is location metadata, not locally verifiable evidence. A 0.2
  `run` Entry that depends on remote outputs pins an **existing local pointer
  bundle** through the ordinary `refs` machinery.
- Bundle contract: a JSON file, schema `aitp/run-pointer-0.1`, with host,
  remote path, scheduler/job ID and collection time; binary and input
  identities; output file names, sizes, and remotely computed digests;
  validation status and any unavailable objects. It is written by the run
  tooling next to its outputs (no fixed location imposed by AITP); AITP never
  creates it, only pins and reads it.
- The bundle is pinned with the existing `sha256:` (preferred) or `git:`
  scheme. **No new pin scheme is introduced** — the five explicit schemes
  (sha256, git, run, version, retrieved) are unchanged, and `retrieved:` never
  serves as integrity.
- What this buys: the captured claim and its provenance are auditable — the
  bundle's bytes are bound to the record and re-verified by `check`
  (`missing_ref`/`hash_mismatch` errors on drift — the same grading the save
  path applies; `invalid_pointer_bundle` error when the pinned bytes are not
  a valid bundle). It does not prove the remote host was honest.
- Rejected alternatives (unchanged from the design base): `target: host:/path`
  with `sha256:` when the local validator did not read those bytes; local
  mutable files with `retrieved:` as if observation time were integrity;
  extension-based static-vs-mutable inference.

## 9. Run/source template conventions (frozen)

- `resources/templates/record/run.md` gains an Execution Context And Cost
  section carrying, where applicable: host and remote path; scheduler and
  job ID; exact command/config; binary sha256 or stable version;
  consequential build flags; input directory or input-manifest identity;
  seed; exit status and partial/cancelled state; estimated vs. actual
  wall/memory cost. Consequential parameters stay source/why/risk/fix rows —
  a template convention, not validator schema. Unknown or inapplicable values
  are stated explicitly.
- `resources/templates/record/source.md` prompt additions: stable identity,
  version/retrieval context, and binary/build context when the source is an
  executable artifact. Optional `citekey`/`trust` frontmatter on `source`
  Entries: `citekey` is a string (the universal human handle), `trust` a
  string; both are advisory and never change validation.
- No generic nested frontmatter schema for execution metadata.

## 10. File map

### 10.1 Runtime — `plugins/aitp-research-protocol/scripts/vendor/aitp/`

| File | Change | Est. nonblank impact (nonbinding) |
|---|---|---|
| `records.py` | 0.2 prepare; version-scoped validation; `based_on`/`resolves`+`resolution`/`contradicts` rules (structure only); ref-validator split for check grading | +85–120 |
| `check.py` (new) | whole-store re-validation, error/warning grading, report builder, exit mapping | +110–160 |
| `state.py` | `enter` groups open items by kind (unresolved failures, open predictions, unanswered questions, unsettled contradictions); `used_by` in projections | +25–45 |
| `cli.py` | `check` subcommand | +15–25 |
| `notes.py` | Note `supersedes` validation (§6) | +12–20 |
| `core.py` | export the check entry point | +2–4 |
| `md.py`, `workspace.py`, `__init__.py`, `__main__.py` | unchanged | 0 |

`check` must be a thin module over the existing save-time validators — one
validation code path, never a second implementation of record rules.

### 10.2 Templates — `resources/templates/record/`

New: `prediction.md` (Durable Summary; Prediction And Basis; Distinguishing
Power; Planned Test — at least one pinned ref and one limitation required at
save, per §1); `question.md` (Durable Summary; Precise Question Or Obligation;
Context, Assumptions, And Dependencies — agent-authored questions state their
basis there; Why It Matters; Discharge Criterion And Evidence Required).
Edited: `failure.md` (its Evidence And Next Diagnostic section gains the
contradiction prompts of §5), `run.md`, `source.md` (§9). Unchanged:
`observation.md`, `result.md`, `decision.md`, `code-change.md`, `closeout.md`,
all of `note/` and `init/`.

### 10.3 Tests — `tests/ledger/`

New: `test_check.py` (CLI, exit 0-1-2, JSON schema, read-only byte-identity,
error/warning grading, deterministic ordering, drift fixtures graded as
errors, pointer-bundle cases, invalid timestamps); `test_schema_02.py`
(`based_on` save rules;
`resolves` single-target + `resolution` enum matrix; `observed` resolver
rules; `contradicts` structure; Note `supersedes`; v0.1 compatibility —
multi-target 0.1 `resolves` still accepted, 0.1 records byte-untouched).

Edited: `fixtures/golden/` and `test_golden.py` — new 0.2 fixture records, a
deterministic `check`-report golden, and the deliberate regeneration of the
`enter` goldens (enter output changes with §3 and §5). Existing v0.1 golden
records are not rewritten; regeneration is the documented, deliberate
procedure, never a routine side effect.

Unchanged and green: `test_cli.py`, `test_core.py`, `test_adopt.py`,
`test_inventory.py`, `test_distribution.py`, `test_plugin.py`,
`benchmark.py`.

### 10.4 Suite and Skills

Suite: after the M0.6 baseline, add the dense-ledger scenario per
`docs/m1-read-write-balance.md` §Suite additions (no private-project claims;
long supersession chain; invalid legacy timestamp; stale handoff replaced by
a later closeout; a run whose evidence is a local pointer bundle; Note-trigger
distractors), with the rubric diff recorded.

Skills: `using-aitp` gains the M1b norms (evidence-backed `resolves`,
`based_on` discipline, prediction/question recording, pointer-bundle
disclosure); `surveying-literature` and `analyzing-a-source` land here as
use-driven Skill-only increments. Runtime never enforces any of this.

## 11. GW_librpa read-only acceptance

The real store is compatibility evidence, not a test namespace.

- In-place read acceptance runs `list`/`show`/`check` (all read-only).
  Before and after, hash every file under `.aitp`; the maps must be
  byte-identical.
- Expected dated baseline (2026-08-06 audit): 60 structurally readable v0.1
  Entries; 41 active, 19 superseded; 26 `result` Entries; one unresolved
  active failure; `check` reports zero record-content errors under v0.1 rules;
  drifted local pins (37 missing, 78 hash-mismatched in that dated snapshot)
  surface as errors — the same grading the save path applies — with exit 1,
  never as crashes; `list`/`show` remain readable.
- Write-path acceptance runs only on a `cp -a` temporary copy or a fresh
  temporary store: valid and missing `based_on` targets; reverse `used_by`
  projection; a remote run pinning a local pointer bundle; rejection of a
  naked remote path presented as a local `sha256:` pin; the
  `resolves`/`resolution` matrix; `contradicts` structure; Note `supersedes`.
  A new Entry reaches the real project only for a genuine research event
  with the researcher's approval and real evidence.

## 12. Budget: the 1,450 cap, structural risk, adjudication

### 12.1 Numbers

M0.5 actual: 981 nonblank lines (recorded in `docs/slim-core-plan.md`).
M0.6 actual: 1,082 nonblank lines (the frozen baseline recorded in
`docs/m1a-spec.md`; the ≤ 1,100 cap was met).
Caps are fixed and never adjusted: M1a ≤ 1,300; M1b ≤ 1,450. M1b headroom
is 1,450 minus the actual M1a total; if M1a lands near its cap, M1b has
roughly 150 lines.

### 12.2 Structural risk

M1b is the largest validation-surface addition since M0.5: two new kinds,
four new relation/closure rules, and a whole-store check module. The
nonbinding estimate in §10.1 sums to roughly +250–375 lines — above the
likely headroom even at the low end. This is a structural risk, not a
cosmetic one: the frozen contract's minimal implementation may exceed the
cap. The post-M1a reconciliation must include a per-module table proving each
module remains below 400 nonblank lines, not only a cumulative total.

### 12.3 Adjudication (after the M1a gate)

The implementation spec must open with a reconciliation table: actual M1a
total → the fixed 1,300 M1a cap and the fixed 1,450 M1b cap → the actual M1b
headroom (1,450 minus the actual M1a total) → the minimal implementation of
this freeze → the cut list (empty, or named items from §12.4). Every budget
review reconciles the actual M1a total against the fixed caps; the caps are
never adjusted, stretched, or reinterpreted. If the cut order is exhausted
and the minimal implementation still exceeds 1,450, the gatekeeper does not
expand the cap: a documented freeze revision names each dropped or narrowed
feature in the roadmap stage table and the implementation spec, then the
revised scope is re-reviewed before implementation. The freeze binds
semantics; the reconciliation decides line economy.

### 12.4 Cut order and prohibitions

Cut order (from `docs/roadmap.md` §M1b and `docs/m1-read-write-balance.md`
§Scope and cut order):

1. the quick-run experiment — already not committed core and not part of
   this freeze (§13);
2. nonessential save-time hints that duplicate the Skill;
3. cosmetic output features.

Never cut: evidence validation, relation validation, v0.1 compatibility,
read-only `check`, deterministic projections, the no-index rule.

Standing prohibitions for M1b:

- No new pin scheme; pointer bundles pin with existing `sha256:`/`git:` only.
- No quick-run promise and no in-place upgrade of any record.
- No reverse index or derived cache; `used_by` is always computed from
  Markdown.
- No migration or rewriting of v0.1 records; `check` never repairs.
- No semantic enforcement: contradiction substance, outcome-vs-expectation
  honesty, and claim-dependency truth are author claims, auditable in Git,
  not validator checks.
- No commands beyond `check`; no hooks, daemons, MCP, or scheduler; no new
  dependencies beyond the vendored YAML.

## 13. Non-commitments

- **No quick-run.** `aitp record quick` remains a suite-gated addendum per
  `docs/roadmap.md` §M1b, considered only if suite or ≥ 4 real sessions show
  that durable run events are missed primarily because of write friction. It
  is the first feature cut, it is not in this freeze, and no CLI shape for it
  is promised here.
- No new pin scheme (§8).
- No dedicated contradiction template and no new prepare flag: a
  contradiction is a plain 0.2 `failure` Entry whose Evidence And Next
  Diagnostic section carries the §5 prompts.
- No reverse index, no derived cache, no index of any kind.
- No migration, no repair, no tamper-proofing additions.
- The `aitp-collaborator` alpha remains a later Skill/pilot track from the
  roadmap; it is not part of this M1b runtime or gate.

## 14. Gate restated

The roadmap §M1b gate, plus this pre-spec's additional condition: suite shows
prediction order respected and corrections persisting across sessions;
based-on targets and reverse views are correct without an index; a
remote-run pointer bundle is auditable; the pilot advances one real question
over ≥ 2 sessions; v0.1 records and the GW_librpa corpus remain untouched;
and the §12.3 line-budget reconciliation is recorded in the implementation
spec.
