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
§§1–14 are candidate contracts; only selected rows bind, per the §0.1 process
below and the 2026-08-12 reviewed freeze revision. **§§1–14 are historical
candidates, not default designs**, frozen verbatim in
[`docs/archive/m1b-candidates-1-14.md`](archive/m1b-candidates-1-14.md); a
deferred capability that reappears is re-derived from fresh natural-use
evidence, not resurrected from those sections. The M1a gate and the
two-session natural-use pause are complete; the §0.1 freeze revision is done
and selects M1b-R1. Its implementation-level spec (`docs/archive/m1b-r1-spec.md`) is
implemented and its deterministic gate has passed; deferred, moved, dropped,
and no-runtime outcomes produce no implementation spec. Selecting no M1b
runtime slice remains a valid outcome for every other row.

Beyond the selected read slice, M1b stays design-only: `check` is shipped and
gated, while
`aitp/lite-entry-0.2` and its commands are historical candidates (frozen in
the archive), not existing
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
cap margin). Candidate sections **not** in R1 — §§1–6 (0.2 schema,
`based_on`, `used_by`, typed closures, `contradicts`, Note `supersedes`
rules), §8 (pointer bundles), §9 (template additions), §10.2/§10.3 0.2
parts, §10.4 suite/Skill additions, and §11 write-path acceptance — live
frozen in
[`docs/archive/m1b-candidates-1-14.md`](archive/m1b-candidates-1-14.md).
They are historical candidates for future freeze revisions; none authorizes
code.
