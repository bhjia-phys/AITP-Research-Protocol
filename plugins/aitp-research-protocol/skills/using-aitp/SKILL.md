---
name: using-aitp
description: "Use AITP Research Protocol to recover and preserve grounded research state while working in a theoretical-physics repository. Trigger when entering or resuming a project, after a durable result, failure, decision, source assessment, code change, reproducible run, or closeout, when writing a working or theory note from recorded evidence, and when a stable workflow recurs — retrieve Method cards by their generic marker and, if the distillation triggers hold, follow the distilling-methods Skill. Maintain current state automatically at session start and end: enter/check, evidence review, method-card retrieval, and closeout/working-note maintenance when the state fell behind."
---

# Using AITP

Use the CLI bundled with this plugin. Resolve `../../scripts/aitp.py` relative
to this `SKILL.md` and convert it to an absolute path. Select the first
available compatible interpreter from `python3.13`, `python3.12`, `python3.11`,
and `python3`, verifying that it is Python 3.11 or newer before invoking:

```text
<compatible-python> <absolute-plugin-root>/scripts/aitp.py <command>
```

If no compatible interpreter exists, report that Python 3.11 or newer is
required. Do not require a globally installed `aitp` executable. In
user-facing explanations, the shorter `aitp <command>` spelling is acceptable.
Use ordinary filesystem tools and `rg` for ad hoc reading; there is no
`aitp search`.

## Current command map

Every command accepts `--cwd PATH` (default `.`) and `--json`. No `aitp
search` exists — `rg` over `.aitp/topic/` is the query path.

- `aitp init --topic <slug> --title "<title>"` — blank repository only;
  `--adopt` creates `.aitp/` inside an existing tree without touching
  content; `--dry-run` previews without writing.
- `aitp enter [--recent N] [--workstream <slug>]` — orientation at
  session start and before ending; `--recent` defaults to 20 and is a
  projection, not the whole ledger. The M1c `--workstream` flag (shipped;
  deterministic gate passed) takes a single slug and scopes the view to that
  research line (a repeated flag is parser-rejected misuse).
- `aitp check [--cwd PATH] [--json] [--workstream <slug>]` — read-only
  whole-store health validation; zero-write. No flag:
  `aitp/check-report-0.1` (byte-unchanged). The M1d single-occurrence
  `--workstream` flag emits the scoped `aitp/check-report-0.2`
  (shipped; deterministic gate passed) — see §M1d.
  Exit 0 clean / 1 findings / 2 cannot run or misuse, in both modes.
- `aitp inventory <path> --name <slug>` — operator-only M0.6 bootstrap tool
  (legacy scan + hash manifest); not part of routine session flow.
- `aitp backfill workstreams --mapping <path> --decision <entry-id> [--apply]`
  — M1e reviewed explicit workstream backfill for legacy records; dry-run by
  default, requires a human decision Entry that sha256-pins the mapping file
  (see §M1e).
- `aitp record prepare --kind <kind> --authority <level> --created-by <id>
  [--idempotency-key <key>] [--workstream <slug>]...` → `aitp record save
  <draft-path>`.
- `aitp note prepare --mode working|theory --title "<title>" --created-by
  <id> [--workstream <slug>]...` → `aitp note save <draft-path>`.

## M1a/M1b-R1 read commands — implemented (sync checklist)

The current CLI is `init`, `enter`, `inventory`, `backfill`, `record`,
`note`, `list`, `show`, and `check`. `check` is the read-only store-health command with two
read-only transports — `aitp/check-report-0.1` no-flag and
`aitp/check-report-0.2` scoped (M1d, §M1d) — while the **diagnosed file
schemas remain the shipped v0.1 ones** (`aitp/lite-entry-0.1`/
`aitp/lite-note-0.1`). The M1b-R1 baseline (no-flag `check`,
[`docs/archive/m1b-r1-spec.md`](../../../../docs/archive/m1b-r1-spec.md))
shipped with its deterministic gate **passed** (evidence recorded in
`docs/archive/m1b-r1-stage-notes.md`). `lineage` is a deferred candidate — do not
invoke or teach it.
M1a is **done; deterministic gate passed**; the implementation evidence is in
[`docs/archive/m1a-stage-notes.md`](../../../../docs/archive/m1a-stage-notes.md).

- `aitp list [--kind KIND] [--since DATE] [--workstream <slug>] [--json]`
  is the read-only retrieval
  projection. Use `--kind` for a kind filter and `--since` for an inclusive
  recorded-time filter; superseded Entries remain visible. Its JSON schema is
  `aitp/list-0.1`; with the M1c single-occurrence `--workstream` flag it is
  `aitp/list-0.2` (shipped; deterministic gate passed).
- `aitp show <entry-id> [--json]` opens one exact Entry. Its JSON schema is
  `aitp/show-0.1`. Do not emulate `show` with ad-hoc parsing.
- `aitp check [--cwd PATH] [--json] [--workstream <slug>]` validates the
  store read-only with two transports: no-flag `aitp/check-report-0.1`
  (byte-unchanged; whole store) and the M1d scoped flag variant
  `aitp/check-report-0.2` (§M1d; shipped; deterministic gate passed).
  Both: exit 0 clean, 1 findings, 2 cannot run (not a
  workspace, unreadable store metadata, or CLI misuse); zero-write (no lock,
  cache, index, repair, or migration); findings deterministic, sorted by
  `(path, code, message)`. The diagnosed file schemas stay the shipped v0.1
  ones (`aitp/lite-entry-0.1`/`aitp/lite-note-0.1`) in both transports. Run
  it before resuming a dense store; parse the report on exits 0 and 1;
  warnings are non-blocking.
- `aitp enter --json` uses `aitp/enter-0.2`: the latest active closeout with a
  non-empty `next_action` is the handoff; only without such a closeout does it
  fall back to another active Entry. Notes sort by recorded time. With the M1c
  single-occurrence `--workstream <slug>` flag the payload is `aitp/enter-0.3`
  (shipped; deterministic gate passed).
- `enter`'s text rendering is compact: two frozen M1a safety lines
  (`recent_entries: <shown> of <active> active (<omitted> omitted)`;
  `recent_notes: <shown>; latest_working_note: <id @ time|(none)>;
  active_newer: <n|unknown>`), a `goal_status: not_established`/`goal:` hint,
  an optional `handoff_status: review` hint, and a `warnings:` count pointing
  at `aitp check`. The goal and handoff hints are **structural**, not
  semantic — `goal_status` mirrors the normalized Research Goal placeholder
  and `handoff_status: review` only means a newer unresolved failure exists
  than the handoff; never read scientific staleness or quality into them.
  Machine output is the versioned JSON; never parse the text.
- A Note or Entry is `legacy_derived` only when its body first line is exactly:
  `> legacy-derived: recovery orientation only — not re-validated`
- `counts.malformed` counts records that could not be parsed or structurally
  validated at all. A record that parses but carries an invalid field value
  (for example an unparseable `created_at`) is reported as a separate
  field-level warning (`invalid_timestamp`) and is **not** counted in
  `counts.malformed`; the two can therefore differ, and `memory_status:
  available` can appear beside a non-empty `warnings:` count. Check the
  `warnings` detail (`aitp check`) instead of reading `malformed` as a
  total health count.
- `latest_working_note` and `active_newer_than_latest_working_note` are
  structural Note-age signals only, not semantic coverage or credibility.
- When four or more related durable Entries form a conclusion chain a returning
  session would otherwise reconstruct, consider a working Note. This is a Skill
  judgment, never a runtime rule.
- Also consider a working Note when `enter` reports `latest_working_note =
  None` while several recently recorded Entries depend on each other, or when
  the researcher asks what the actual current conclusion is. These are
  natural-use checks applied by Skill judgment, never by the runtime or by
  semantic rules.
- Keep `rg` over `.aitp/topic/` for full-text search. There is no
  `aitp search`; `list`/`show` are projections, not a semantic search engine.

M1b's exhaustive A–H + Followup roster, dispositions, and freeze rule remain
normative in [`docs/m1b-spec.md` §0.1](../../../../docs/m1b-spec.md#01-authoritative-candidate-roster-and-current-dispositions).
The natural-use pause is complete and the 2026-08-12 reviewed freeze revision
([`docs/archive/m1b-adjudication.md`](../../../../docs/archive/m1b-adjudication.md)) selected
the read-side slice **M1b-R1** — `aitp check` (no-flag
`aitp/check-report-0.1`) and a compact
`enter` text renderer — implemented per its
implementation-level spec
[`docs/archive/m1b-r1-spec.md`](../../../../docs/archive/m1b-r1-spec.md); the deterministic
gate **passed** (evidence recorded in
`docs/archive/m1b-r1-stage-notes.md`). Do not teach or invoke the deferred candidates
(`based_on`/`used_by`, typed open items, pointer bundles, quick-run,
structured prepare, `lineage`) — they stay out of this Skill.

When a selected slice lands, sync the roadmap, README, Hakimi handoff, and
this command map in the same change; historical specs, adjudications, and
stage notes live frozen in `docs/archive/` and are not updated. A
selected capability that changes an unversioned success envelope must first use
a versioned envelope (preferred) or an explicit same-change Hakimi adapter
revision; never add a response key silently.

## M1c — Topic workstreams (shipped; deterministic gate passed)

The frozen implementation spec is
[`docs/archive/m1c-workstreams-spec.md`](../../../../docs/archive/m1c-workstreams-spec.md)
(2026-08-13). Status: **done; deterministic gate passed** — the auditable
gate evidence is in
[`docs/m1c-stage-notes.md`](../../../../docs/m1c-stage-notes.md).
M1c is independent of the frozen M1b roster
(`docs/m1b-spec.md` §0.1 dispositions unchanged) and of M3.

- `workstreams` is an **optional frontmatter list** on Entries and Notes
  (e.g. `workstreams: [crpa, magnetic-symmetry]`). A record without it is
  **unscoped legacy**: it appears only in the unfiltered global view and is
  excluded from every scoped view. A present field must be a non-empty,
  no-duplicate slug list (an empty list is invalid). Membership is explicit
  and multi-valued — never infer it from summary text, paths, kinds, or
  relations; a cross-line record lists all its workstreams.
- `record prepare`/`note prepare` accept a **repeatable** `--workstream
  <slug>` flag that seeds the draft's list in flag order; a repeated
  identical slug is rejected as a duplicate (no silent dedup); the
  prepare/save envelopes are unchanged. Slugs reuse the Topic slug rule
  `[a-z0-9][a-z0-9-]{0,62}`.
- `enter --workstream <slug>` and `list --workstream <slug>` emit the
  scoped schemas `aitp/enter-0.3`/`aitp/list-0.2`: the old payload plus one
  additive top-level singular `workstream` key, with entries/notes/counts
  filtered to strict exact membership (unscoped records are not in scope).
  The flag is single-occurrence on both read commands. **Relations run on
  the whole store first** — the superseded set and the resolved set are
  global, so a cross-line resolver/superseder still closes/replaces its
  target; then the projections, including the handoff (`next_action`), are
  strictly scoped — an out-of-scope handoff is never shown.
  `warnings`, `counts.malformed`,
  and `memory_status` stay global in scoped `enter`/`list`. **Without the
  flag the old schemas are byte-unchanged** (`aitp/enter-0.2`,
  `aitp/list-0.1`). The M1c "`check` has no scope flag" rule is superseded
  **for the flag variant only** (frozen M1c clause replaced per
  `docs/archive/m1d-workstream-health-spec.md` §Supersession); every other
  M1c clause stays in force and no-flag `check` is byte-unchanged. Note the
  frozen asymmetry: scoped `enter` `warnings` are **global**, while scoped
  `check` `counts.warnings` is **scoped**, with `outside_scope` carrying the
  global−scoped remainder (§M1d).
- No registry: there is no workstream file or command; enumerate slugs with
  `rg` over frontmatter when needed.
- In a dense multi-line store (e.g. GW_librpa running crpa,
  magnetic-symmetry, and qsgw-semiconductor lines sharing one
  source/build/provenance), scope `enter`/`list` to the line you are working
  on; unscoped legacy records stay global-only — they do not appear in a
  scoped view. When a record genuinely belongs to several lines, list all of
  them explicitly in `workstreams`.

## M1d — scoped `check` (shipped; deterministic gate passed)

The frozen implementation spec is
[`docs/archive/m1d-workstream-health-spec.md`](../../../../docs/archive/m1d-workstream-health-spec.md)
(2026-08-14). Status: **done; deterministic gate passed** — the auditable
gate evidence is in
[`docs/m1d-stage-notes.md`](../../../../docs/m1d-stage-notes.md)
(2026-08-14). M1d selects no M1b candidate; M1b/M1c frozen dispositions are
unchanged; the M1c "`check` has no scope flag" clause is superseded for the
flag variant only (§M1c; §Supersession in the spec).

- `check --workstream <slug>` takes **exactly one slug** (not a repeatable
  union): a repeated `--workstream` is parser-rejected misuse (exit 2,
  "may only be given once"); an invalid slug (or `""`) raises
  `invalid_workstreams` (exit 2 with the standard JSON error envelope under
  `--json`), same validation as the M1c read commands. The frozen help
  string is `only findings on records that explicitly list this workstream
  (single slug)`.
- Every run, scoped or not, scans the **whole store once** and computes the
  global report exactly as a no-flag run; the flag restricts only the
  report, never the scan. Relations are validated on the **global**
  `entry_map` first — an in-scope resolver/superseder whose target exists
  out-of-scope or unscoped validates cleanly (a cross-workstream resolver
  still closes its target); `missing_relation` fires only against the whole
  store.
- **Attribution (frozen)**: a finding is in the scoped view iff its path is
  an **admitted** record (parse and structure passed **and** the ID is
  unique — malformed and duplicate-ID files are never attributable) whose
  frontmatter `workstreams` **explicitly** contains the slug (strict exact
  membership, never inferred). Findings on out-of-scope, unscoped,
  malformed, duplicate-ID, and `TOPIC.md` records are excluded from every
  scoped view; they stay in the no-flag report and in `counts.outside_scope`.
  The scoped `findings` list is the globally sorted list restricted to
  attributable in-scope paths — same levels, codes, messages, `(path, code,
  message)` order; nothing is re-sorted, re-graded, or re-worded.
- Scoped `--json` is `aitp/check-report-0.2`: the complete 0.1 payload plus
  exactly three additive changes — one top-level **singular** `workstream:
  "<slug>"` key (appended last; there is no `workstreams` key anywhere),
  `counts.by_code`, and `counts.outside_scope`. Frozen key order: top level
  `schema, status, root, counts, findings, workstream`; inside `counts`:
  `entries, notes, errors, warnings, by_code, outside_scope` (no `malformed`
  key).
- Scoped `counts.entries`/`counts.notes` are the **admitted in-scope**
  canonical files (deliberately different from the global "count every
  canonical file" rule, because malformed files cannot be attributed to any
  scope). `counts.errors`/`counts.warnings` are the scoped findings by
  level; `status` is `"findings"` iff the scoped `findings` list is
  non-empty, else `"clean"`.
- **`by_code`** is a map `code → {"errors": n, "warnings": m}` over the
  scoped findings, keys sorted lexicographically by code, **always present**
  (`{}` on a clean scope). Buckets are per-level, so a code that grades as
  an error on one finding and a warning on another (e.g. `invalid_git_ref`)
  is tallied separately; the buckets sum exactly to `counts.errors`/
  `counts.warnings`/`len(findings)`. **`by_code` is a tally, not a
  diagnosis**: it never classifies a `hash_mismatch` as "expected historical
  pin drift" vs. "current evidence damage" — that is a human judgment
  informed by the tally, never a runtime call.
- **`counts.outside_scope`** is the derived level-delta
  `{"errors": n, "warnings": m}` = **global totals minus scoped totals**,
  per level, always present. It is not a finding: no paths, no codes, no
  `by_code` contribution, never in `findings`, never affects `status` or the
  exit code. It exists so a scoped report can never silently mask global
  findings — it names no workstream and labels nothing as "debt" or
  "damage". When `outside_scope` is large, run `aitp check` (no flag) for
  the whole store.
- Scoped text prints **exactly four stdout lines, always — including a
  clean scope** (stderr is empty on exits 0/1); details live in `--json`
  only, so scoped text never truncates:

  ```text
  workstream: <slug>
  check: <e> error(s), <w> warning(s)
  by_code: <compact JSON>
  outside_scope: <e> error(s), <w> warning(s) (run "aitp check" for the whole store)
  ```

  `by_code:` is the compact JSON serialization of `counts["by_code"]`
  (no indent), e.g. `by_code: {"hash_mismatch": {"errors": 2, "warnings":
  0}}`, and `by_code: {}` on a clean scope. No per-finding lines. The text
  is human-facing only — machine output is the versioned JSON; never parse
  the text.
- Exit codes, evaluated on the scoped report: `0` = zero scoped findings
  (the store may still have global findings — see `outside_scope`); `1` =
  at least one attributable in-scope error or warning; `2` = could not run
  (not a workspace, unreadable/invalid store metadata) or CLI misuse
  (repeated `--workstream`, invalid slug). Payload and exit are mutually
  consistent: non-empty scoped `findings` ⇒ exit 1, empty ⇒ exit 0.
  `outside_scope` never affects `status` or the exit code.
- **An empty scope is a valid result, not an error**: a well-formed slug
  with no admitted in-scope records yields counts 0, `findings` `[]`,
  `by_code` `{}`, `outside_scope` = the global totals, status `clean`,
  exit 0. **Unscoped legacy records are in no scope**: on a store whose
  records carry no `workstreams` (e.g. the GW_librpa legacy store), every
  scoped view is empty — a scoped `clean`/exit 0 may simply mean **nothing
  is attributable, not health**. Scoped health is meaningful only once
  records explicitly carry `workstreams` — new scoped records or a
  **reviewed manual backfill** (the runtime never backfills; a backfill
  only adds the explicit membership list, never content, and is a human
  decision, never automatic).
- **A scoped `clean`/exit 0 is not a whole-store health certificate**: it
  claims only "no attributable findings for this workstream". The no-flag
  run remains the whole-store instrument.
- **Deterministic baseline/delta is manual, not runtime**: `check` reports
  are deterministic in both modes (same store ⇒ byte-identical JSON/text;
  findings sorted by `(path, code, message)`; no wall-clock fields), so a
  baseline/delta reading is saving `check --json` outputs over time and
  `diff`/`rg`-ing them. There is **no report-comparison runtime** (deferred
  by the spec) — do not teach one.
- **Claims and boundaries**: M1d claims only deterministic implementation
  and read-only compatibility. It does **not** fix handoff staleness
  (closeout-first handoff is unchanged; roster H stays dropped), does not
  change exit-1 semantics (exit codes are byte-identical; the flag only
  gives recovery scripts a per-workstream signal), does not reduce write
  friction (structured prepare is Followup 6, deferred), and claims no
  behavioral, causal, or treatment-advantage evidence. `by_code` is never a
  drift-vs-damage classification and a scoped clean is never a health
  certificate.

## M1e — evidence lifecycle + reviewed backfill (shipped)

The frozen implementation spec is
[`docs/archive/m1e-evidence-lifecycle-backfill-spec.md`](../../../../docs/archive/m1e-evidence-lifecycle-backfill-spec.md)
(2026-08-15). It changes no M1b/M1c/M1d disposition.

- **`sha256-once:`** is the mutable-target observation pin. Save verifies
  exactly like `sha256:`; later check drift is `historical_pin_drift`
  warning and a missing target is `historical_ref_missing` warning. Use it
  for live canonical files (`PROJECT_MEMORY.md`, execution-note pdf/zip,
  live status JSON) only when the historical record intentionally observes
  that mutable path. Immutable evidence and manifests stay `sha256:`; tracked
  source stays `git:`.
- **`check-policy`** is the optional reviewed store-local file
  `.aitp/local/check-policy.json` (schema `aitp/check-policy-0.1`) with
  `mutable` and `immutable` path-pattern lists. On legacy records that still
  use strict `sha256:`, a mutable match downgrades `hash_mismatch` to
  `historical_pin_drift` warning and `missing_ref` to
  `historical_ref_missing` warning; immutable matches and unmatched paths
  stay errors. No policy file ⇒ check output is byte-unchanged. The policy
  is explicit reviewed configuration, never runtime drift/damage inference.
- **`aitp backfill workstreams`** performs reviewed, explicit, idempotent
  backfill. The mapping file (schema `aitp/backfill-workstreams-0.1`) lists
  slugs and record IDs; `--decision` must be a human decision Entry whose
  `refs` sha256-pin the mapping file. The command only adds/merges the
  `workstreams` frontmatter block and preserves body and all other fields;
  it is dry-run by default and writes only with `--apply`. Never infer
  workstreams from paths or summaries — backfill only what the human-anchored
  mapping explicitly says.

### `check` exit codes in scripts — capture explicitly, fail closed on 2

Under `set -e`, a bare `aitp check` aborts the script on exit 1 before
`enter` can run; capture the exit code explicitly and branch. Exit 2
(cannot run: not a workspace, unreadable store metadata, misuse) means the
health state is unknown — **fail closed** on it, never treat it as clean:

```sh
set -e
code=0
report="$(aitp check --json 2>&1)" || code=$?
case "$code" in
  0) : ;;                                          # clean — proceed
  1) echo "check found findings; inspect the report" ;;  # non-blocking
  2) echo "check could not run; state unknown" >&2; exit 2 ;;  # fail closed
  *) echo "check exited with unexpected status $code; state unknown" >&2; exit 2 ;;  # fail closed (126/127 etc.)
esac
```

On exits 0 and 1 the check ran and the report is parseable; on exit 2 the
store state is unverified — do not proceed on unverified state. Scoped runs
behave the same, with the exit evaluated on the scoped report. `check`
never writes, so it is safe anywhere in a script.

## Start or resume work

1. If `.aitp/topic/TOPIC.md` does not exist and the repository is blank except for `.git`, run `aitp init --topic <slug> --title "<title>"`.
2. At the beginning of every research session, run `aitp enter`.
3. Run `aitp check` (read-only, zero-write; parse the report on exits 0 and 1,
   fail closed on exit 2). `enter` and `check` are two different projections —
   never substitute one for the other.
4. Treat its output as recorded project state, not as scientific truth. Open cited Entries, Notes, code, calculations, and pinned references before relying on a claim.
5. `memory_status` is a structural Research-Goal signal (`available` /
   `partial` / `not_established`), **not evidence health**: it says nothing
   about pins, refs, or relations. If it is `partial` or `not_established`,
   state what is missing and inspect files directly. Evidence health is
   `aitp check` — a store can report `memory_status: available` while
   `check` finds many errors (the two projections never substitute for each
   other).
6. When the session's task may follow a known procedure, retrieve it with
   the generic marker search `rg "^> method-card:"` over `.aitp/topic/`,
   then read each matching card Note directly at
   `.aitp/topic/notes/<note-id>.md` — `list`/`show` project Entries only
   and never open Notes. Cards inform, never dispatch, and there is no card
   registry or INDEX to enumerate — the marker search is the query path.

After `enter`, treat `next_action` and `handoff_status` as structural.
`handoff_status: review` only means a newer unresolved failure exists than
the handoff — it is not the only staleness check. Compare the `@ <time>`
printed on the `next_action` line with the newest `recent_entries`: if any
active Entry is newer than the handoff source (a newer result or closeout,
not only a failure), open those newer records before planning and treat the
old handoff as possibly behind. `active_newer` is a working-Note age
signal, not handoff age. If the handoff is genuinely behind, plan the
end-of-session closeout/working-Note upkeep from §Before ending; never edit
the old handoff.

`goal_status: not_established` means only that `.aitp/topic/TOPIC.md`'s
Research Goal section is still the placeholder. It says nothing about an
external host/session goal, and AITP never infers or imports a host goal.
If the researcher has confirmed a durable Topic goal, record it in
`TOPIC.md` once with an ordinary file edit (preserving frontmatter) and,
when the confirmation is a research decision, record it as a human
`decision` Entry; a transient session task is not the Topic goal.

The `enter` recent window is a projection, not the whole ledger: it shows the newest records and omits older active ones (`omitted_active`). Records outside the window are unread, not absent. Before planning, search the store — `rg` over `.aitp/topic/` — for the entries relevant to the current question: the newest record on every topic you will rely on, its `supersedes`/`resolves` chains, and the pinned evidence behind its claims. Before asserting that a record, pin, or relation does not exist, search the store for it.

Never infer the real research state merely from directory names, Git history, or the latest modified file.

### Automatic current-state maintenance

Keeping the ledger current at session boundaries is the agent's job — never
hand the tidy-up to the researcher. Maintenance is automatic, but it is
**judgment, not a runtime rule**, and it writes only through the normal
prepare/save path.

- **Session start** (this section): `enter` + `check` + evidence review +
  method-card retrieval, per the numbered list above. Treat the results as
  recorded state, then plan.
- **Session end** (§Before ending): if this session produced a durable
  delta and the current state is behind it, write the missing closeout
  Entry (`--kind closeout --authority agent --created-by agent:<name>`)
  and/or a working Note (`--created-by agent:<name>` — Notes carry
  `created_by`, never `authority`), superseding only an agent-authored
  closeout Entry or agent-created working Note that is genuinely behind;
  never supersede a human-authored Entry or Note — a human closeout
  included; never supersede a human `decision` or `result` Entry; never
  edit the old record; no durable delta ⇒ zero-write.
- **No-op/low-noise**: an ordinary re-read, an un-triggered check, or a
  restatement of an already-recorded event is not a durable delta — write
  nothing.
- **Pre/post verification**: before ending, verify the current state
  (`enter`/`check`); after any save, re-run both and confirm the new record
  is active, evidence is reachable, and the handoff is current.

When this session may trigger method distillation, read
[`../distilling-methods/SKILL.md`](../distilling-methods/SKILL.md) before
drafting anything. It is the **only detailed rule source** for method cards:
the draft triggers and every gate (trial, revision, approval, publication)
are defined there and nowhere else; do not duplicate its rules here or
invent your own.

## Record a durable moment

Record only information that should survive the current conversation:

```text
aitp record prepare --kind <kind> --authority <level> \
  --created-by agent:<name> --idempotency-key <stable-key>
```

Choose one kind: `observation`, `result`, `failure`, `decision`, `source`, `code-change`, `run`, or `closeout`. Set `authority` to the source of the event: `human` (`--created-by researcher`) when the researcher asserts it, `agent` when you act or observe.

Open the returned draft, replace every inline prompt, add precise relations and pinned references, then run:

```text
aitp record save <draft-path>
```

The CLI template is the schema. Keep claims small, state limitations, and distinguish evidence from interpretation. The generated frontmatter starts with `refs: []` (Notes: `basis_refs: []`) — that is a schema placeholder, not a valid evidence list. The draft prompts show the required shape; replace the list with maps containing `target` and `at`. The pin key is `at`, never `pin:`.

- Before preparing a record, check that the ledger does not already contain the same logical event. A restatement, confirmation, or re-verification of an already-recorded convention, decision, or claim is not a durable event: cite the existing record and write nothing new. Never re-issue with `agent` authority a decision the ledger already records as `human`.
- Record a verification only when it changes a live claim or surfaces auditable evidence the ledger lacks; do not wrap an ordinary re-read or an un-triggered check as a durable event.
- Use `resolves` only when this Entry's own evidence directly closes an active failure — first check the failure's state and its `supersedes`/`resolves` chain, and confirm no existing record already settles the failure's subject. A projected counter (such as `unresolved_failures`) is ledger state, not an instruction: do not change a failure's status unless the records support the change.
- Use `supersedes` only when replacing an older Entry; never silently rewrite history.
- When the researcher challenges an existing result/closeout: first write a narrowly scoped `failure`; after the fix, resolve it with direct evidence and write a new closeout; never rewrite the old result to manufacture a clean history. If the main claim stands and only a local statement is corrected, state that distinction in the failure/resolver `limitations`.
- Use `git`, `sha256`, `run`, `version`, or `retrieved` pins for evidence that may change.

### Pinned references — exact YAML and lifecycle

`refs` (and a Note's `basis_refs`) is a YAML list of maps. Every mutable
reference uses this exact shape:

```yaml
- target: relative/path-or-url
  at: sha256:<digest> | sha256-once:<digest> | git:<revision> | run:<id> | version:<id> | retrieved:<time>
  locator: exact section, equation, line, or object   # optional
```

Pin lifecycle (frozen in `docs/archive/m1b-r1-spec.md`; unchanged by M1d):
a pin is verified at **save** — a failing pin makes the record invalid as
written, and save errors with the same code/message the `check` path reports
— and re-verified read-only at every `check`. A `sha256:` pin records the
file's digest at save time; if the target file later changes, `check`
reports `hash_mismatch` (error). A `sha256-once:` pin also verifies at save
but later drift is `historical_pin_drift` warning (§M1e). Whether that mismatch is the expected
drift of a historical pin (e.g. a legitimately regenerated inputs manifest)
or current evidence damage is a **human judgment** — the runtime never
classifies it. When evidence legitimately changes, update the pin
deliberately in a new record; never silently edit the old record's pin.

Choose the pin by evidence lifecycle:

- **immutable evidence** (one-time snapshot, provenance report, local
  manifest, PDF/archive copy): pin the file directly with `sha256:`.
- **tracked evolving source** (code, TeX, audit scripts): prefer
  `git:<revision>` over a working-tree `sha256:` so later edits do not turn
  a historical record into a `hash_mismatch`.
- **mutable canonical working files** (`PROJECT_MEMORY.md`, a live
  note/report, a regenerated `MANIFEST.sha256`): do not make a historical
  Entry or Note depend on the file staying unchanged. Copy the point-in-time
  state to an immutable snapshot and pin that, or pin a `git:` revision; a
  body citation by path is not an evidence pin.
- **remote run**: pin the local immutable pointer manifest (below), never a
  bare `host:path`.

A pointer manifest is itself evidence. Once a saved Entry pins a local
pointer file, never edit that pointer file in place. If a legitimate
r3→r4 revision changes it, write a new versioned pointer file (e.g.
`data/run-<job-id>-r4.pointer.json`) and record the new state in a new
Entry; leave the old pointer and old Entry as history. The same rule
applies to Note `basis_refs`: do not edit an old Note to chase a changed
hash — leave it as historical evidence and record the new state in a new
Note/Entry. The resulting old-pin `hash_mismatch` findings are expected
historical drift, not current damage; interpret `check`/`by_code` with
that distinction and prevent future noise by pinning snapshots from the
start.
Scheme notes: `git:` local pins verify `git cat-file -e <revision>:<target>`
(an external http/https/arxiv/doi target is an error; when no Git
environment exists the pin grades as a warning, cannot verify); `run:`
requires a directory whose name is the value; `version:` requires an
external persistent identifier; `retrieved:` requires an HTTP(S) target and
an ISO-8601 retrieval time.

- Reuse the same idempotency key when retrying the same logical write.

For a dense campaign — many jobs serving one purpose — first write one local
immutable submission/result report (job IDs, binary/build/input identity,
boundaries and status), then index that durable campaign moment with a single
`run` or `result` Entry. One Entry per job is not expected; transient queue
snapshots and preflight churn are not separately recorded.

### Remote evidence — pointer manifest (non-normative example)

A naked remote path is location metadata, not locally verifiable evidence.
When a durable result depends on remote immutable runs, first write a local
pointer manifest (e.g. `data/run-<job-id>-r4.pointer.json`) carrying the host,
remote path, scheduler job ID, binary/input SHAs, a local hash manifest, the
verification time, and a `boundary` line stating that the remote bytes were
checked then and not re-verified since; then pin that local file with
`sha256:` in the Entry's `refs`. Make each pointer file an immutable
per-event object: include job/date/revision in its filename, and never edit
in place a pointer file already pinned by a saved Entry — write a new file
and a new Entry for the next event. Never record a bare `host:path` as a pin.
This is a Skill convention with no runtime support (roster D is deferred).

## Write a note from recorded evidence

Use a Note for synthesis, not as the only evidence for a result:

```text
aitp note prepare --mode working --title "<title>" --created-by agent:<name>
aitp note prepare --mode theory --title "<title>" --created-by agent:<name>
```

Fill the generated template, cite supporting pinned sources in `basis_refs`, and save with:

```text
aitp note save <draft-path>
```

A working Note explains the current line of attack. A theory Note gives a derivation or formal argument with assumptions, conventions, checks, and open gaps.

## Work with the researcher

- Before consequential compute — scientifically critical, expensive, or convention-ambiguous — state the setup: Hamiltonian with sign and coupling conventions, boundary, sector, target observable, scale. Get an explicit confirm-or-correct when anything could be misread; a silent assumption costs more than one line of confirmation. Do not pester on routine, cheap steps.
- When the researcher pushes back, genuinely reconsider: restate the prior reasoning, take the objection seriously, change the conclusion if warranted or present both readings for re-ratification. Never capitulate by default; never defend at length. If the exchange changes course, record it as a `decision`.
- Verification that backs the current claim is not optional. Extra verification beyond that is opt-in: when a result is challenged, propose checks along the ladder limits → symmetry/consistency → convergence → cross-method → literature, with rough costs, and run only what the researcher confirms.

## Before ending

Run `aitp enter` again and compare the reported handoff with the updated
active result: only if the old closeout is an agent-authored closeout whose
`next_action` has genuinely fallen behind the current durable state, append
a new closeout and supersede the old one — never supersede a human-authored
closeout, and never edit the old record. Automatic supersession is scoped
strictly to an agent-authored closeout Entry or agent-created working Note
that is genuinely behind: never supersede a human-authored Entry or Note — a
human closeout included; never supersede a human `decision` or `result`
Entry, and never supersede a closeout or working Note that is not actually
behind (a restatement of an unchanged handoff is noise, not maintenance). This is
automatic current-state maintenance, not a handoff to the researcher: the
agent appends the closeout (or, when the line of attack is still being worked
and several recent Entries form a conclusion chain, a working Note with
`created_by: agent:<name>` — Notes carry `created_by`, never `authority`)
without asking the researcher to do the organizing. Do not force a closeout
at every stage; write one only when
the session is unfinished and the handoff needs replacing. Confirm that
the new record is active, evidence is reachable, unresolved failures are
honest, and the next action is concrete. Do not record conversational filler,
speculative claims presented as results, duplicate retries, or transient
scratch work.

**No-op is the default.** If the session produced no durable delta (no new
observation, result, failure, decision, source assessment, code change, or
run, and the handoff is not behind), write nothing: no closeout, no Note, no
record — zero writes. A closeout that only restates an unchanged handoff is
noise, not maintenance.

**Pre/post verification.** Before writing, run `aitp check` and `aitp enter`
and note the state; after any save, re-run both to verify the new record is
active, pins verify, and no new findings were introduced. The save is not
verified until the post-run confirms it.

**Method-card harvest.** When a stable workflow recurred this session (see
Start or resume work), read `../distilling-methods/SKILL.md` and follow its
triggers before ending; the distillation rules live there only and are never
copied into this Skill.

Reviewed wrap-up checks on the re-run `enter`:

- When it prints `handoff_status: review`, a newer unresolved failure exists
  than the handoff — read it and decide whether the handoff needs replacing.
  If this session produced a durable delta and `latest_working_note` is also
  None, make the new closeout/current-state working Note an explicit
  end-of-session task rather than a soft option; with no durable delta,
  remain zero-write. The hint is **structural, never semantic**: it only
  means a newer unresolved failure exists; never read scientific staleness
  or quality into it.
- When `latest_working_note` is None while several recent Entries form a
  conclusion chain a returning session would otherwise reconstruct, consider
  writing a working Note (Skill judgment, never a runtime rule) so the
  handoff has a synthesis to point at.
- A scoped store: re-run `enter --workstream <slug>` and `check --workstream
  <slug>` for the line you worked on; an empty scope is expected until
  records explicitly carry the slug (§M1d).

### Natural-use feedback (optional, never blocking)

After ending an ordinary, unscripted research session on a real Topic, write
a 4–6 line natural-use note following
[`natural-use-session-template.md`](natural-use-session-template.md)
(bundled next to this Skill; a verbatim copy of the checkout's
`feedback/natural-use-session-template.md`) into the AITP protocol
checkout's `feedback/` directory as
`feedback/YYYY-MM-DD-<topic-slug>-natural-use.md`. This is an observation
log, not an evaluation or a gate: record observable facts only, never claim
superiority over plain files, and never edit the template. Skip it without
ceremony when the session had no research substance, when the AITP checkout
cannot be located, or when writing it would delay the researcher; a missing
note never blocks work and is never treated as a failure.
