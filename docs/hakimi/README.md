# Hakimi integration handoff

Single entry point for the cross-repository handoff between AITP (protocol,
persistence, evidence authority) and Hakimi (agent orchestration, tool
invocation, interaction UX). This directory is the AITP-side baseline that a
Hakimi development session should read before building or changing its AITP
adapter, and that AITP sessions must keep current whenever a stage, CLI, or
schema status changes.

- Historical runtime audit: **2026-08-08**, AITP HEAD
  `8658f6827288f4bb61e5c193a346f0f73ebbe3b2`, read-only (only `/tmp`
  throwaway copies were written; no runtime, spec, or record was changed).
  This is historical audit evidence, not the current stage status. The
  current amendments are the 2026-08-10 M1a deterministic-gate completion,
  the 2026-08-12 M1b planning sync, the 2026-08-12 M1b-R1 gate completion,
  the 2026-08-13 M1c gate completion, the 2026-08-14 M1d gate completion,
  the 2026-08-15 0.6.0 Skill-only amendment, the 2026-08-15 M1e runtime slice, and the 2026-08-21 0.8.0 Skill-only amendment below.
- 2026-08-15 machine-readable adapter surface: `plugins/aitp-research-protocol/aitp.contract.json` (`aitp/adapter-contract-0.1`) is the executable projection of the command/schema decisions in `compatibility-matrix.md` and is shared by Hakimi and external harness adapters. Any CLI, transport-schema, model-facing description, or Skill-surface change updates it in the same change; `tests/ledger/test_adapter_contract.py` enforces consistency.
- Current amendment: the approved 2026-08-10 narrowed review closes M0.6;
  M1a is now **done; deterministic gate passed**. The 2026-08-09 no-turn
  preflight verified FROZEN v6 preparation and stopped before S3; it is not
  scored evidence. The original bootstrap Notes/decisions,
  recall/false-import/human-time, held-out S3, paired S1/S2, cold-start,
  conformance, causal, and treatment-advantage evidence remains not measured;
  deferred; not counted. M1a now exposes the versioned read contracts; see
  [`docs/archive/m1a-stage-notes.md`](../archive/m1a-stage-notes.md),
  [`docs/archive/m0.6-stage-notes.md`](../archive/m0.6-stage-notes.md), and the
  [review packet](../archive/m0.6-gate-review.md).
- 2026-08-12 M1b planning sync: the natural-use pause is complete and the
  reviewed freeze revision ([`docs/archive/m1b-adjudication.md`](../archive/m1b-adjudication.md))
  selected the read-side slice **M1b-R1**, implemented per its
  implementation spec
  [`docs/archive/m1b-r1-spec.md`](../archive/m1b-r1-spec.md).
- 2026-08-12 M1b-R1 gate completion: the R1 deterministic gate **passed**
  (evidence in
  `docs/archive/m1b-r1-stage-notes.md`). Hakimi may now feature-detect
  `aitp/check-report-0.1` (parsing the
  report on exits 0 and 1; exit 2 is the AITPError-driven JSON error
  envelope — argparse misuse (an unknown/repeated flag) exits 2 with
  stderr usage only, no JSON envelope). `lineage` is a
  deferred candidate.
  `enter` stays at `aitp/enter-0.2`; its text rendering is now
  compact, and that text is human-facing only — never feature-detected.
- 2026-08-13 M1c sync: **M1c (Topic workstreams) done; deterministic gate
  passed** per the frozen implementation spec
  `docs/archive/m1c-workstreams-spec.md` (gate evidence in
  `docs/m1c-stage-notes.md`). Optional explicit `workstreams`
  membership (unscoped legacy visible only in the global view), a repeatable
  `--workstream` prepare flag (duplicates rejected), and single-slug scoped
  read projections: with the single-occurrence `--workstream <slug>`, `enter`
  emits `aitp/enter-0.3` and `list` emits `aitp/list-0.2` (old payload plus
  one additive top-level singular `workstream` key; strict exact membership
  — unscoped records are excluded; relations computed on the whole store
  first, then strictly scoped projections including handoff; warnings stay
  global, and `check` stays global in M1c (pre-M1d — M1d supersedes the
  M1c no-scope-flag rule for `check`'s flag variant only; see the
  2026-08-14 sync below). **Without the flag the
  payloads stay `aitp/enter-0.2`/`aitp/list-0.1`, byte-unchanged.** No
  registry; `show`/`check` contracts unchanged in M1c (pre-M1d — the scoped
  `check` flag variant is M1d, superseding this for the flag variant only;
  see the 2026-08-14 sync below). Hakimi may now feature-detect
  and integrate the scoped contracts (H3).
- 2026-08-14 M1d sync: **M1d (Workstream health) done; deterministic gate
  passed** per the frozen implementation spec
  `docs/archive/m1d-workstream-health-spec.md` (gate evidence in
  `docs/m1d-stage-notes.md`). `check` gains a **single-occurrence
  `--workstream <slug>`** flag (a repeated flag is parser-rejected misuse)
  emitting the scoped transport **`aitp/check-report-0.2`**; **without the
  flag every `check` surface stays byte-identical `aitp/check-report-0.1`**
  (JSON, text, exit 0/1/2, zero-write). Scoped `counts` add the per-level
  `by_code` tally and the derived `outside_scope` level delta (global −
  scoped); scoped `counts.entries`/`counts.notes` are **admitted in-scope**
  counts — **not directly comparable** with `aitp/check-report-0.1`; exit
  0/1 are evaluated on the scoped report, so a scoped `clean` claims only
  "no attributable findings for this workstream", never whole-store health
  (`outside_scope` and the no-flag run carry the remainder); a well-formed
  slug with no admitted in-scope records is a valid empty scope. The scoped
  text is **exactly four human-only lines** — never parse or feature-detect
  it. Hakimi may now integrate the scoped contract (H4).
- 2026-08-15 0.6.0 Skill-only amendment: **0.6.0 is a Skill-only release,
  not a stage** — automatic session-boundary current-state maintenance
  (`using-aitp` Skill) and local method-card distillation
  (`distilling-methods` Skill). It changes **no** CLI command, flag, file
  schema, transport schema, exit code, or zero-write property; CLI/schema
  feature detection and every red line in `compatibility-matrix.md` are
  completely unchanged. Hakimi may orchestrate the existing commands for
  session-boundary maintenance (enter/check at session start; scoped
  variants per H3/H4 for the worked line; closeout/working-Note
  prepare→fill→save at session end per the H0 flow) and may treat method
  cards as ordinary local theory-mode Notes (H1/H3 read contracts apply,
  `show`/`list` unchanged; a card is just a Note whose body first line is
  the marker `> method-card: <slug>`). Publication of a method card into a
  Skill is human-gated and happens inside the AITP protocol repository, not
  by Hakimi. Hakimi must not direct-write canonical files, auto-run
  `inventory`, auto-backfill `workstreams`, or auto-publish method cards.
  Manual reviewed backfill is available only through `aitp backfill workstreams`
  with a human decision pinning the mapping; no inference/auto-backfill exists.
- 2026-08-15 M1e runtime slice: **M1e (Evidence lifecycle + reviewed
  backfill) done; deterministic gate passed** per
  `docs/archive/m1e-evidence-lifecycle-backfill-spec.md` (gate evidence in
  `docs/m1e-stage-notes.md`). Runtime version 0.7.0. Hakimi may feature-detect
  the `aitp/backfill-0.1` success envelope and may read `sha256-once`/policy
  finding codes in the existing check transports; no check transport schema
  changed. `backfill` is dry-run by default and write-on-`--apply`; it must
  only be called with a human decision Entry that sha256-pins the mapping.
  (red lines 2 and 4 remain in force).
- 2026-08-21 0.8.0 Skill-only amendment: **0.8.0 is a Skill-only release,
  not a stage** — method-observation markers (`> method-observation: <slug>`
  on eligible durable Entries; low-trust candidate, not proof; runtime never
  validates), conservative candidate review, post-card exact trials, two-step
  human decisions (card `Approve`/`Defer`/`Reject` then separate `Publish
  now`/`Keep local`; both saved as independent human `decision` Entries by
  the main agent; main-agent-only; no hardcoded model/preset), the platform
  tool/card/Skill three-layer boundary (tool executes, card records, Skill
  routes; bare `host:path` never accepted as evidence; host Goal never
  auto-imported), and a best-effort fallback lifecycle (no runtime hook, no
  exactly-once; native host coordinator planned but not implemented). It
  changes **no** CLI command, flag, file schema, transport schema, exit
  code, or zero-write property; CLI/schema feature detection and every red
  line in `compatibility-matrix.md` are completely unchanged. Plugin version
  moves to 0.8.0 on all four surfaces. A future Hakimi native C6/H6 Feature
  would own session/turn checkpoint, deduplication, recovery, question
  interaction, and adapter state for method distillation — but is not
  implemented; until then the Skill fallback is independently usable. The
  design record is `docs/method-cards-and-distillation.md`.
- Future evaluation-harness integration: Hakimi may consume or host an adapter
  for the separate project, but AITP does not assign harness ownership to
  Hakimi. No H0, H1, or H2 capability depends on harness implementation; see
  the [external evaluation-harness contract](../external-evaluation-harness.md).
- Full compatibility matrix, assumptions check, and decisions:
  [`compatibility-matrix.md`](compatibility-matrix.md).

## Boundary (both sides agree; re-verify before relying)

- AITP = protocol, persistence, evidence authority. Interface is **CLI +
  files**; no SDK, API server, MCP server, daemon, or vector service.
- Hakimi = agent orchestration, tool invocation, web retrieval, PDF reading,
  reasoning, and private caches. Private caches are **never written back** to
  AITP.
- Hakimi never copies the AITP runtime/parser/validator, never writes
  `.aitp` canonical files (`entries/`, `notes/`, `TOPIC.md`, `STORE.toml`),
  and never bypasses `record/note prepare|save`.

## Phased plan (Hakimi side; AITP side is the roadmap gates)

M0.6→M1a authorization belongs to AITP: the approved 2026-08-10 narrowed
gate review flipped M1a to ready, and the post-review deterministic gate is
now passed. Hakimi may feature-detect the shipped read contracts; it adds no
M1b adjudication. The exhaustive A–H roster and freeze process are normative in
[`docs/m1b-spec.md` §0.1](../m1b-spec.md#01-authoritative-candidate-roster-and-current-dispositions).
The H2 summary is non-exhaustive: integrate only capabilities shipped by a
selected, reviewed slice; see the A–H roster for E quick-run if separately
selected and shipped. G is independent Skill-track work and H is dropped.
Selected prepare/save changes follow the versioned-envelope or same-change
adapter-revision rule in [`compatibility-matrix.md` §3](compatibility-matrix.md).

| Phase | AITP prerequisite | Hakimi work |
|---|---|---|
| H0 | now (no gate) | Launcher adapter (argv-only, Python ≥ 3.11 probe), strict shape validation of unversioned envelopes, capability detection from `--help`, `enter` lifecycle, prepare→fill→save flow, graceful degradation on `not_initialized`, tree-hash zero-write tests |
| H1 | M1a done; deterministic gate passed | Read-only feature detection and schema dispatch for `aitp/enter-0.2`, `aitp/list-0.1`, and `aitp/show-0.1`; closeout-first handoff; Note-age signal; generated-golden compatibility tests; plugin version `0.2.0` (H1-era; current plugin version `0.8.0`, 2026-08-21 0.8.0 Skill-only amendment) |
| H2 | M1b-R1 selected 2026-08-12; implemented per `docs/archive/m1b-r1-spec.md`; deterministic gate passed 2026-08-12 | Integrate only capabilities actually shipped by the R1 gate: `aitp check` (parse `aitp/check-report-0.1` on exits 0 and 1; exit 2 is the AITPError-driven JSON error envelope — argparse misuse (an unknown/repeated flag) exits 2 with stderr usage only, no JSON envelope), and consume the compact `enter` text only as human-facing output (never parse it; machine output is the versioned JSON). Persisted `based_on`/`used_by`, pointer bundles, quick-run, and `lineage` are **not** in R1 and must not be scheduled for H2. The M1d scoped `check` variant (`aitp/check-report-0.2`, single-occurrence `--workstream`) is H4 scope |
| H3 | M1c done; deterministic gate passed 2026-08-13 (evidence in `docs/m1c-stage-notes.md`; frozen spec `docs/archive/m1c-workstreams-spec.md`) | Integrate the scoped read contracts **only when passing the single-occurrence `--workstream <slug>`**: feature-detect `aitp/enter-0.3`/`aitp/list-0.2` (old payload plus one additive top-level singular `workstream` key), scope strictly by exact membership (unscoped records are **not** in scope), and keep warnings/malformed global; relations are computed on the whole store first, then projections including the handoff are strictly scoped. Without the flag, keep consuming `aitp/enter-0.2`/`aitp/list-0.1`; never parse the scoped `workstream:` text line. The repeatable `--workstream` prepare flag seeds draft frontmatter only (duplicates rejected) — prepare/save envelopes are unchanged |
| H4 | M1d done; deterministic gate passed 2026-08-14 (evidence in `docs/m1d-stage-notes.md`; frozen spec `docs/archive/m1d-workstream-health-spec.md`) | Integrate the scoped `check` contract **only when passing the single-occurrence `--workstream <slug>`**: feature-detect `aitp/check-report-0.2` (complete 0.1 payload plus additive top-level singular `workstream`, `counts.by_code` per-level tally, `counts.outside_scope` global−scoped level delta). Attribution is strict exact membership on **admitted** records only (parse + structure passed, ID unique) — unscoped, out-of-scope, malformed, duplicate-ID, and TOPIC.md findings are never scoped and surface only via `outside_scope`; relations are validated on the whole store first, then the globally sorted findings are restricted by scoped path (subset invariant). Scoped `counts.entries`/`counts.notes` are **admitted in-scope** counts, **not comparable across `aitp/check-report-0.1`/`0.2`**; exit 0/1 are evaluated on the scoped report (a scoped `clean` is not whole-store health), exit 2 unchanged; the four-line scoped text is human-facing only — never parse it. Without the flag keep consuming `aitp/check-report-0.1`, byte-unchanged |
| H5 | M1e done; deterministic gate passed 2026-08-15 (evidence in `docs/m1e-stage-notes.md`; frozen spec `docs/archive/m1e-evidence-lifecycle-backfill-spec.md`) | Integrate the M1e evidence-lifecycle surface: feature-detect `aitp/backfill-0.1` success envelope (status `dry_run`/`applied`; `changed`/`unchanged` lists), and read `sha256-once`/`historical_pin_drift`/`historical_ref_missing` and `invalid_check_policy` finding codes in the existing check transports. `backfill` must only be called with a human decision Entry that sha256-pins the mapping; dry-run by default, write on `--apply` only |
| H6 / C6 | **planned; not implemented** — 0.8.0 Skill-only amendment defines the rule surface; future native method-distillation coordinator | A future Hakimi native Feature (`packages/agent-core-v2/src/features/aitp/`, not yet created) would own session/turn checkpoint, deduplication, recovery, question interaction, and adapter state for method distillation — bounded checkpoints at session start/resume, after adapter-save, turn-end/idle, state-change, dispose, and crash/cold-resume. Requires a reviewed adapter-contract extension (preferred: new schema version) before implementation. The 0.8 Skill fallback is independently usable until then. Detailed design is planned for a separate `docs/hakimi/method-distillation-orchestration.md` (not yet created) |
| Formal Hakimi contract | after M4 | Versioned `--json` + extended golden fixtures as the pass gate for any agent integration |

Hakimi's research-loop capabilities (web, PDF, reasoning, session UX, private
caches) are independent of all AITP gates and can proceed in parallel at any
time.

## Maintenance contract (binding)

Update this directory **in the same change** as any of the following:

- stage status flips (M0.6 gate, M1a gate, M1b gate, M1c/M1d slice gates,
  M2–M4);
- CLI surface change (new or removed command/flag; `--help` output);
- schema status change (new frozen payload/file schema, version bump);
- M1b scope or gate sequencing change (natural-use review, candidate
  disposition, selected slice, split/revision/deferral, or no-runtime result);
- a Hakimi-side integration finding that changes a matrix row or a red line.

The flip of a roadmap row happens through the gate review; this directory only
records the consequence. Never edit `docs/roadmap.md` stage statuses from
here. M1a has landed; the synchronized version metadata is `0.8.0`
(2026-08-21 0.8.0 Skill-only amendment; 0.7.0 was the preceding M1e runtime
slice; 0.6.0 was the preceding Skill-only release — no
CLI or schema change) and
the read contracts are available. Keep the frozen `suite/adapters/cli.md`
unchanged until a separately reviewed suite refreeze. Hakimi H1 may now
feature-detect the three versioned read schemas; `check` is shipped and
gated (M1b-R1 per `docs/archive/m1b-r1-spec.md`; gate evidence in
`docs/archive/m1b-r1-stage-notes.md`) and may be feature-detected now;
`lineage`
is a deferred candidate. M1c (Topic workstreams) is **done; deterministic
gate passed** (2026-08-13) per `docs/archive/m1c-workstreams-spec.md`; the
gate evidence is in `docs/m1c-stage-notes.md`, and H3 may now integrate the
scoped contracts. **M1d (Workstream health) is done; deterministic gate
passed (2026-08-14)** per `docs/archive/m1d-workstream-health-spec.md`
(gate evidence in `docs/m1d-stage-notes.md`) and M1e (evidence lifecycle + reviewed backfill, `docs/m1e-stage-notes.md`): `check` now exposes two read
transports — `aitp/check-report-0.1` no-flag (byte-unchanged) and
`aitp/check-report-0.2` with the single-occurrence `--workstream` — and H4
may now integrate the scoped contract. **0.6.0 (2026-08-15) is Skill-only**:
no new command, flag, or schema, so feature detection and red lines are
unchanged; Hakimi may orchestrate the existing commands for session-boundary
maintenance and treat method cards as local theory Notes (see the 2026-08-15
amendment above). The 2026-08-21 **0.8.0** Skill-only amendment
(method-observation markers, two-step human decisions, platform
tool/card/Skill boundary, best-effort fallback) moves plugin version to
0.8.0 with no CLI or schema change; a future H6/C6 native coordinator is
planned but not implemented.

## Reading order

1. `/home/bhjia/physics/repo/AITP-Research-Protocol/AGENTS.md`
2. `/home/bhjia/physics/repo/AITP-Research-Protocol/README.md`
3. `/home/bhjia/physics/repo/AITP-Research-Protocol/docs/roadmap.md` (stage table, M1a, M1b, Hakimi contract)
4. `compatibility-matrix.md` (this directory)
5. `docs/archive/m1a-spec.md`, `docs/m1b-spec.md`, `docs/archive/collaborator-design.md`
6. The installed plugin's `skills/using-aitp/SKILL.md` (python probe order, command map)
7. The runtime: `plugins/aitp-research-protocol/scripts/aitp.py` + `scripts/vendor/aitp/`

Then the Hakimi repository's own `AGENTS.md`/`README.md`/architecture.
