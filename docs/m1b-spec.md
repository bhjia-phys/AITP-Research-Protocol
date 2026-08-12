# M1b — Open items and behavior pilot: candidate inventory

Status: candidate-inventory pre-spec; **reviewed freeze revision 2026-08-12
recorded** (`docs/archive/m1b-adjudication.md`). The read-side slice **M1b-R1**
(`aitp check` v0.1-only + compact `enter` text) is **selected and
implemented** per its implementation-level spec `docs/archive/m1b-r1-spec.md`;
its deterministic gate **passed** (evidence recorded in
`docs/archive/m1b-r1-stage-notes.md`). All other rows
— including the Followup-2 lineage projection, re-deferred at the budget
reconciliation — are deferred, moved, or dropped and produce no
implementation spec.

This document is the M1b candidate pre-spec under `docs/roadmap.md` §M1b and
the M1 index. It is not an implementation-level spec or permission to code.
§§1–11 are candidate contracts; only selected rows bind, per the §0.1 process
below and the 2026-08-12 reviewed freeze revision. **§§1–11 are historical
candidates, not default designs**: a deferred capability that reappears is
re-derived from fresh natural-use evidence, not resurrected from these
sections. The M1a gate and the
two-session natural-use pause are complete; the §0.1 freeze revision is done
and selects M1b-R1. Its implementation-level spec (`docs/archive/m1b-r1-spec.md`) is
implemented and its deterministic gate has passed; deferred, moved, dropped,
and no-runtime outcomes produce no implementation spec. Selecting no M1b
runtime slice remains a valid outcome for every other row.

Beyond the selected read slice, M1b stays design-only: `check` is shipped and
gated, while
`aitp/lite-entry-0.2` and its commands are candidate contracts, not existing
interfaces.

## 0. Binding rules

- The sections below are candidate contracts, not a monolithic implementation
  commitment. For any capability selected, its semantics are frozen. The
  post-gate implementation spec may choose implementation economy (shared
  validators, single-pass scans, module placement) but may not weaken, extend,
  or re-interpret the selected rules.
- Templates and Skills are part of the deliverable for selected capabilities.
  Templates are not counted in the Python line budget, but their section sets
  are frozen here; exact prompt wording is fixed by the implementation spec.
- The §0.1 roster is the disposition protocol: each row gets selected,
  deferred, moved to a named slice, or dropped. A moved row re-freezes coherent
  schema/payload versions for its named slice; nonselected or no-runtime rows
  produce no implementation spec. Only selected rows may enter the separately
  reviewed implementation spec described by §0.1.
- Everything in this document stays inside the trust model: auditable and
  tamper-evident, never tamper-proof. Nothing here promises detection of
  forged attribution, early outcome exposure, or dishonest claims.

## 0.1 Authoritative candidate roster and current dispositions

This table is the authoritative M1b unit roster, not one implementation
bundle. The **disposition** column is the current freeze outcome — the
**2026-08-12 reviewed freeze revision** recorded in
[`docs/archive/m1b-adjudication.md`](archive/m1b-adjudication.md), the single record that
confirms or revises all rows and their dependencies after the M1a gate and the
completed two-session natural-use pause. Deferred, moved, dropped, and
no-runtime outcomes produce no implementation spec; only selected rows enter a
separately reviewed, green-lit implementation spec. The revision selects the
read-side slice **M1b-R1** (implemented per `docs/archive/m1b-r1-spec.md`;
deterministic gate passed);
every other row produces no implementation spec.

| ID | Candidate unit | Dependencies and boundary | Current disposition |
|---|---|---|---|
| A | Store health: a read-only `check` report over current v0.1 records and any selected M1b schemas | M1a gate, the post-M1a natural-use review, a selected report schema, and the existing validators; no index. Independent of B–D. It is a candidate command only if selected and shipped. | **selected in M1b-R1 — v0.1-only, read-only `check`**; schema `aitp/check-report-0.1`; exit 0 clean / 1 findings / 2 unable; zero-write, no fix, no migration; diagnostics for unselected M1b schemas are **not** in R1; implemented per `docs/archive/m1b-r1-spec.md`, deterministic gate passed |
| B | Dependency links: `based_on`, derived `used_by`, and the required success-envelope/schema versioning | M1a versioned `list`/`show`/`enter` payloads for projections; a versioned `record save` success envelope before any warning key, or an explicitly revised Hakimi adapter contract in the same slice; A is required only if full `based_on` semantics retain `check`; no index. | **deferred** (persisted `based_on`, derived `used_by`, and their envelope/schema versioning are all deferred; the narrow read-side lineage view is tracked separately as Followup-2 below) |
| C | Open-item schema: `prediction`, `question`, typed `resolves`/`resolution`, `contradicts`, and Note `supersedes` | v0.1 compatibility, selected v0.2 file schemas, templates, and validators; A is optional unless whole-store diagnostics are selected; no semantic judgment in Python. | **deferred** |
| D | Remote-run pointer bundle plus run/source templates | Existing local `sha256:`/`git:` pin machinery and external run tooling; the bundle is a local evidence object, while a naked remote path remains location metadata and cannot verify remote bytes; independent of A–C. | **deferred** (only the GW session needs it; one-session evidence) |
| E | Conditional quick-run experiment | Existing prepare/save validator, lock, idempotency, and evidence path; D is required for remote-run evidence; suite or at least four real sessions must show write friction is the cause before consideration. It is not committed M1b core. | **deferred** (the structured-prepare followup suggestion is separately explicitly deferred — see the R1 boundary note below) |
| F | Optional `aitp-collaborator` Skill behavior pilot | F is moved to M4 and does not force any A–E selection now; M4 adjudication must resolve dependencies. If the selected collaborator protocol requires typed `prediction`/`question` records, roster C or an explicitly reviewed equivalent contract must first be selected and shipped. | **moved to M4** |
| G | Methodology Skills: `surveying-literature` and `analyzing-a-source` | Independent use-driven Skill track; no M1b runtime, schema, or gate dependency. Each Skill may land only after real use separately justifies it and its own reviewed Skill change is ready. | **moved to an independent use-driven Skill track** |
| H | Next-action closure relation | Dropped because M1a's closeout-first handoff is the selected solution and no evidence yet justifies another task lifecycle. It may return only as a new reviewed proposal after natural-use evidence, never through silent M1b scope growth. | **dropped from M1b** |

### Followup suggestions roster (2026-08-12; six independent rows)

The researcher's six followup suggestions (archived in
`feedback/2026-08-12-gw-librpa-followup-feedback.md`) each receive exactly
one disposition:

| ID | Candidate unit | Current disposition |
|---|---|---|
| Followup 1 | Compact `enter` **text renderer only** (`aitp/enter-0.2` JSON unchanged), restoring the two M1a safety lines | **selected in M1b-R1** |
| Followup 2 | Current-v0.1 lineage projection (`aitp lineage <entry-id>`, schema `aitp/lineage-0.1`: outgoing `resolves`/`supersedes`, incoming `resolved_by`/`superseded_by`; no recursion/graph/index) | **deferred** — selected in R1 at the freeze revision, **re-deferred at the 2026-08-12 budget reconciliation** (with it the measured prototype leaves ~5 lines of the 1,450 cap and exceeds the 1,425 target; see `docs/archive/m1b-adjudication.md` §Budget reconciliation). May return only through a new reviewed freeze revision |
| Followup 3 | `enter` text-only `handoff_status: review` (handoff source older than a newer unresolved active failure; factual structural prompt, not restored H) | **selected in M1b-R1** |
| Followup 4 | Malformed diagnostics: read-only `check` plus a warning-count summary in `enter` text pointing at it; no persistent suppression | **selected in M1b-R1** |
| Followup 5 | `enter` text-only `goal_status: not_established` on the placeholder, and `check` warning `empty_topic_goal` | **selected in M1b-R1** |
| Followup 6 | Structured JSON/YAML prepare input preserving the draft | **deferred (explicit)** — a separate candidate, not an E variant; mixed evidence; budget prioritized for the read-side slice; the draft-preserving property is kept as a design constraint if re-proposed |

Current dispositions are therefore: A and Followups 1, 3, 4, 5 selected in
M1b-R1 (implemented per `docs/archive/m1b-r1-spec.md`; deterministic gate passed);
B, C–E, Followup 2 (lineage), and Followup
6 (structured prepare) deferred; F moved to M4; G moved to the independent
use-driven Skill track; H dropped from M1b. G and H are outside M1b
runtime/schema/gate scope. F can move back only through §0.1; G needs
separate real-use justification and a reviewed Skill change; H and Followup
2 can return only as new reviewed proposals after natural-use evidence or a
new reviewed freeze revision. No later change may grow M1b scope silently.

### R1 boundary (frozen 2026-08-12)

The reviewed freeze revision selects exactly the **M1b-R1 read-side slice**,
fully specified in [`docs/archive/m1b-r1-spec.md`](archive/m1b-r1-spec.md):

1. compact `enter` **text renderer only** (`aitp/enter-0.2` JSON unchanged)
   with two frozen M1a safety lines (`recent_entries: <shown> of <active>
   active (<omitted> omitted)` and `recent_notes: <shown>;
   latest_working_note: <id @ time|(none)>; active_newer: <n|unknown>`);
2. `aitp check` over the current shipped v0.1 Entry/Note contracts only
   (schema `aitp/check-report-0.1`), with the frozen no-crash mappings
   (`unreadable_record`, `unreadable_ref`, `malformed_store`,
   `invalid_git_ref` warning/error split) and deterministic
   `(path, code, message)` findings;
3. `enter` text-only `goal_status: not_established` on the placeholder
   (empty/missing/literal all normalized to it), and `check` warning
   `empty_topic_goal`;
4. `enter` text-only `handoff_status: review` when the selected handoff
   source's `created_at` is older than a newer unresolved active failure —
   a factual structural prompt, not semantic staleness, not restored H;
5. `enter` text shows only a warning-count summary pointing at `aitp check`;
   JSON keeps the full warnings; no persistent suppression.

`aitp lineage` (Followup 2) is **not** in R1 (re-deferred at budget
reconciliation; measured with lineage the prototype leaves insufficient
cap margin). Candidate sections **not** in R1: §§1–6 (0.2 schema,
`based_on`, `used_by`, typed closures, `contradicts`, Note `supersedes`
rules), §8 (pointer bundles), §9 (template additions), §10.2/§10.3 0.2
parts, §10.4 suite/Skill additions, and §11 write-path acceptance. These
remain candidate contracts for future freeze revisions; none authorizes
code.

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
