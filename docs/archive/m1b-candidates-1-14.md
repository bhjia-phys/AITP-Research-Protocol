# M1b candidate contracts §§1–14 (frozen 2026-08-12)

Moved here from `docs/m1b-spec.md` on 2026-08-12 so the active file keeps
only §0 binding rules and the §0.1 authoritative roster. These sections
are **historical candidates, not default designs**: a deferred capability
that reappears is re-derived from fresh natural-use evidence, not
resurrected from these sections. §7 below is the *candidate* check
contract; the current shipped contract lives in
`docs/design.md` §"`aitp check`". Section numbers and internal
cross-references are kept verbatim from the original file.

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
  condition exists; no warning ⇒ payload unchanged) and, if the A capability
  is selected and shipped, by `check` as `based_on_superseded` — nowhere else.
  `prepare` adds no flag and no `warnings` field; supersession of an existing
  target is only checkable at save, not at prepare.
- The save-response warning is a candidate behavior and cannot silently add a
  key to the current unversioned exact-key success envelope. If this capability
  is selected, the implementation-level spec must first freeze a versioned
  success-envelope schema for the changed save response (preferred), including
  its exact success keys and warning shape, or explicitly revise the Hakimi
  adapter contract in the same selected-slice change. No implemented schema is
  claimed here; no silent key addition is allowed.
- If the A capability is selected and shipped, `check` validates all targets
  (`missing_relation` when absent). If A is omitted, the full `based_on`
  candidate is deferred or moved to a named slice, with that disposition
  recorded in the §0.1 freeze revision, unless its semantics are explicitly
  revised and re-reviewed.

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

## 6. Note `supersedes` validation — frozen candidate rule

`save_note` validates a Note's `supersedes` like Entry supersession plus a kind
boundary: list of Note IDs only (`invalid_supersedes_target` for a non-Note
target), no self-target, target exists (`missing_relation`). Supersession
ordering is write-time causality — the target already exists at save time —
not a `created_at` comparison (roadmap §Auditability); the 2026-08-12
stability revision removed the `invalid_supersession` timestamp rule. If
roster A is selected and
shipped, `check` also validates that rule. Entry `supersedes` likewise requires
Entry targets (`invalid_supersedes_target`). A superseded Note remains readable;
nothing is rewritten. (The GW_librpa corpus contains no Notes, so no legacy
exposure.)

## 7. `aitp check` — candidate read-only contract

This is the candidate A store-health contract. The 2026-08-12 reviewed
freeze revision **selects it in M1b-R1 as a v0.1-only read-only `check`**;
the frozen implementation-level subset (per-file rules, grading, exact
payload/text, exit codes, budget, tests) is in
[`docs/archive/m1b-r1-spec.md`](archive/m1b-r1-spec.md) and is **implemented and gated** —
`check` is a shipped CLI. The contract below
remains the full candidate (v0.1 plus selected M1b schemas); the parts that
depend on unselected M1b schemas (§7.6 codes for 0.2 records, pointer
bundles, Note `supersedes` target rules) are **not** in R1. The R1 spec
adds one R1-only code, `empty_topic_goal` (warning), and grades
`invalid_timestamp` warnings exactly as §7.6 below.

### 7.1 CLI

```
aitp check [--json] [--cwd PATH]
```

If shipped, whole-store re-validation covers every canonical Entry and Note,
using the same structural validators as the save path, plus relation closure
rules (§2, §4, §5, §6). Store metadata must load (`not_initialized`,
`malformed_store` → cannot run).

### 7.2 Read-only scope

If shipped, `check` writes nothing: no lock file (it must not take
`store_lock`, which creates a file), no cache, no index, no repair, no
migration, no scratch, no new canonical files, no `--fix` flag now or later.
It is a projection like `enter`/`list`/`show`. A test asserts the `.aitp` tree
is byte-identical before and after a check run.

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
      "code": "missing_relation",
      "path": ".aitp/topic/entries/entry-<hex>.md",
      "message": "supersedes target does not exist: entry-<hex>"
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
`invalid_relation`, `missing_relation`, `missing_ref`,
`hash_mismatch`, `invalid_run_ref` — are reused for errors (a pin that fails
verification makes the record invalid as written, exactly as on the save
path); `invalid_git_ref` is reused for both grades — error when Git is
available and the commit genuinely lacks the target, warning when the Git
environment is unavailable (no Git binary, or the workspace is not inside a
Git work tree) so the pin cannot be verified). `invalid_supersession` is no
longer produced: the 2026-08-12 stability revision removed the `created_at`
ordering rule; supersession ordering is target-existence causality only:

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

## 8. Remote evidence — local pointer bundle (candidate contract)

- A remote path is location metadata, not locally verifiable evidence. If the
  D row is selected and shipped, a 0.2 `run` Entry that depends on remote
  outputs would pin an **existing local pointer bundle** through the ordinary
  `refs` machinery. This design is a candidate, not a current contract.
- Candidate bundle contract: a JSON file, schema `aitp/run-pointer-0.1`, with
  host, remote path, scheduler/job ID and collection time; binary and input
  identities; output file names, sizes, and remotely computed digests;
  validation status and any unavailable objects. It is written by the run
  tooling next to its outputs (no fixed location imposed by AITP); AITP never
  creates it, only pins and reads it.
- If shipped, the bundle is pinned with the existing `sha256:` (preferred) or
  `git:` scheme. **No new pin scheme is introduced** — the five explicit
  schemes (sha256, git, run, version, retrieved) are unchanged, and
  `retrieved:` never serves as integrity.
- What this candidate buys: the captured claim and its provenance would be
  auditable because the bundle's bytes are bound to the record. Whole-store
  re-verification through `check` is conditional on the A row also shipping;
  it would report `missing_ref`/`hash_mismatch` on drift and
  `invalid_pointer_bundle` when pinned bytes are not a valid bundle. It does
  not prove the remote host was honest.
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
`docs/archive/m1-read-write-balance.md` §Suite additions (no private-project claims;
long supersession chain; invalid legacy timestamp; stale handoff replaced by
a later closeout; a run whose evidence is a local pointer bundle; Note-trigger
distractors), with the rubric diff recorded. **Not in R1**: the suite stays
frozen and unchanged; R1 has no suite deliverable.

Skills: `using-aitp` gains the M1b norms (evidence-backed `resolves`,
`based_on` discipline, prediction/question recording, pointer-bundle
disclosure) **only when the corresponding capabilities ship**; R1 syncs the
Skill for `check` and the compact `enter` text semantics per
`docs/archive/m1b-r1-spec.md` §Version and docs sync. Roster G's
`surveying-literature` and `analyzing-a-source` remain
independent use-driven Skill-track work, not M1b runtime/schema/gate
deliverables; each lands only after real use separately justifies it and its own
reviewed Skill change is ready. Runtime never enforces any of this.

## 11. GW_librpa read-only acceptance

The real store is compatibility evidence, not a test namespace.

- In-place read acceptance runs `list`/`show` and, with A selected in
  M1b-R1, `check` (all read-only). Before and after, hash every file under
  `.aitp`; the maps must be byte-identical. The frozen R1 acceptance
  procedure is in `docs/archive/m1b-r1-spec.md` §Real-store acceptance; the
  candidate notes below are the fuller M1b picture.
- Historical compatibility snapshot (2026-08-06 audit): 60 structurally
  readable v0.1 Entries; 41 active, 19 superseded; 26 `result` Entries; one
  unresolved active failure; if shipped, `check` reports zero record-content
  errors under v0.1 rules; drifted local pins (37 missing, 78 hash-mismatched
  in that dated snapshot) surface as errors — the same grading the save path
  applies — with exit 1, never as crashes; `list`/`show` remain readable.
- These historical values are not fixed current-count assertions; current read
  acceptance records dynamic counts as observed and requires the read-only
  projection and before/after byte-identity invariants.
- Write-path acceptance runs only on a `cp -a` temporary copy or a fresh
  temporary store: valid and missing `based_on` targets; reverse `used_by`
  projection; a remote run pinning a local pointer bundle; rejection of a
  naked remote path presented as a local `sha256:` pin; the
  `resolves`/`resolution` matrix; `contradicts` structure; Note `supersedes`.
  A new Entry reaches the real project only for a genuine research event
  with the researcher's approval and real evidence.

## 12. Budget: the 1,450 cap, structural risk, adjudication

### 12.1 Numbers

M0.5 actual: 981 nonblank lines (recorded in `docs/archive/slim-core-plan.md`).
M0.6 actual: 1,082 nonblank lines (the frozen baseline recorded in
`docs/archive/m1a-spec.md`; the ≤ 1,100 cap was met).
Caps are fixed and never adjusted: M1a ≤ 1,300; M1b ≤ 1,450. M1b headroom
is 1,450 minus the actual M1a total; if M1a lands near its cap, M1b has
roughly 150 lines.

### 12.2 Structural risk

If the runtime rows are selected, M1b is the largest validation-surface
addition since M0.5: two new kinds, four new relation/closure rules, and a
whole-store check module only if A is selected. The nonbinding estimate in §10.1
sums to roughly +250–375 lines — above the likely headroom even at the low end.
This is a structural risk, not a cosmetic one: the full selected runtime subset
may exceed the cap. G's independent Skills and H's dropped relation do not enter
this runtime budget. The 2026-08-12 adjudication avoided the risk by selecting
only the read-side slice M1b-R1; its per-module budget and cut order are frozen
in `docs/archive/m1b-r1-spec.md` §Implementation map / §Cut order, proving each module
stays below 400 nonblank lines and the cumulative total stays ≤ 1,450 (target
1,425), not only a cumulative total.

### 12.3 Adjudication (recorded 2026-08-12)

The §0.1 review is complete and recorded in
[`docs/archive/m1b-adjudication.md`](archive/m1b-adjudication.md): actual M1a total 1,256
against fixed caps (M1b headroom **194**), every A–H disposition and every
followup suggestion with the full roster/dependencies, the smallest
selected slice (**M1b-R1**, read-side: `check` v0.1-only + compact `enter`
text), the re-frozen schema (`aitp/check-report-0.1`), the attributable
approval, and the budget-reconciliation re-deferral of Followup 2
(`lineage`). Deferred, moved, dropped, and no-runtime outcomes produce no
implementation spec. Budget review never adjusts caps, compresses
validators, or silently grows the roster; the selected spec
(`docs/archive/m1b-r1-spec.md`) was separately reviewed and green-lit after this
§0.1 record, and the R1 deterministic gate passed on 2026-08-12 (evidence
in `docs/archive/m1b-r1-stage-notes.md`).

### 12.4 Cut order and prohibitions

Cut order (from `docs/roadmap.md` §M1b and `docs/archive/m1-read-write-balance.md`
§Scope and cut order):

1. the quick-run experiment — roster E is currently deferred/not selected by
   the present disposition freeze; it is not committed implementation scope and
   can be selected only through the post-M1a reviewed freeze revision (§13);
2. nonessential save-time hints that duplicate the Skill;
3. cosmetic output features.

For any selected capability, never cut its required evidence/relation
validation, v0.1 compatibility, or no-index boundary. `check` and deterministic
projections are candidate capabilities, not universal M1b indivisibles: a
check-only slice is allowed; a `based_on` capability may be deferred or moved
to a named slice when its required `check` capability is omitted, with that
disposition recorded in the reviewed freeze revision. Never expand a cap or
compress a validator to preserve a monolithic candidate bundle.

Standing prohibitions for M1b:

- No new pin scheme; pointer bundles pin with existing `sha256:`/`git:` only.
- No quick-run promise and no in-place upgrade of any record.
- No reverse index or derived cache; `used_by` is always computed from
  Markdown.
- No migration or rewriting of v0.1 records; if A ships, `check` never
  repairs.
- No semantic enforcement: contradiction substance, outcome-vs-expectation
  honesty, and claim-dependency truth are author claims, auditable in Git,
  not validator checks.
- No M1b commands beyond the selected candidate interfaces; A's `check` is
  only present if that row is selected and shipped. No hooks, daemons, MCP, or
  scheduler; no new dependencies beyond the vendored YAML.

## 13. Non-commitments

- **Deferred quick-run candidate.** `aitp record quick` remains a suite-gated
  addendum per `docs/roadmap.md` §M1b, considered only if suite or ≥ 4 real
  sessions show that durable run events are missed primarily because of write
  friction. It is part of the authoritative candidate roster as E but is
  currently deferred/not selected by the present disposition freeze; it is not
  committed implementation scope, is the first feature cut, and no CLI shape
  for it is promised here. It can be selected only through the post-M1a
  reviewed freeze revision.
- No new pin scheme (§8).
- No dedicated contradiction template and no new prepare flag: a
  contradiction is a plain 0.2 `failure` Entry whose Evidence And Next
  Diagnostic section carries the §5 prompts.
- No reverse index, no derived cache, no index of any kind.
- No migration, no repair, no tamper-proofing additions.
- The roster's `aitp-collaborator` row is explicitly **moved to M4**. It is a
  Skill-only behavior track, not an M1b runtime or gate prerequisite. A later
  reviewed freeze revision may move it back into M1b only if the adjudication has a
  concrete reason; only then would its pilot evidence enter an M1b gate.

## 14. Gate restated

The 2026-08-12 reviewed freeze revision selects the **M1b-R1** read-side
slice (`aitp check` v0.1-only + compact `enter` text), implemented per its
implementation-level spec
`docs/archive/m1b-r1-spec.md`; its deterministic gate **passed** (evidence recorded
in `docs/archive/m1b-r1-stage-notes.md`); B, C–E,
Followup 2 (lineage), and Followup 6 (structured prepare) deferred, F → M4,
G → the independent Skill track, H dropped. The unselected rows produce no
implementation spec. This selection does not authorize M2; M2 needs its own
natural-demand adjudication.

Any later selected runtime row is subject to §0.1 and its separately reviewed
implementation spec: preserve that row's validation, v0.1 compatibility, and
no-index boundary; the full inventory never becomes a gate automatically. F's
pilot enters an M1b gate only if row F is changed there; G remains independent,
and H requires a new reviewed proposal after natural-use evidence. M4 has its
own natural-demand and prospective-evidence adjudication.
