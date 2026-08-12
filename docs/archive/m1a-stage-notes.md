# M1a stage notes — deterministic gate closure

Status: **done; deterministic gate passed**

Evidence timestamp (UTC): `2026-08-10T16:24:52Z`

M1a is closed as an implementation and deterministic-regression stage. This
closure does not claim behavioral superiority, treatment-over-control advantage,
causal effect, bootstrap validation, or that AITP is better than plain files.
The M1b natural-use pause is complete and the 2026-08-12 reviewed freeze
revision selected the read-side slice M1b-R1, implemented per
`docs/m1b-r1-spec.md` with its deterministic gate **passed** — auditable
evidence in `docs/m1b-r1-stage-notes.md`
(`docs/m1b-adjudication.md`, `docs/m1b-r1-spec.md`).

## Gate evidence

### 1. Full ledger and M1a tests

The unchanged ledger tests plus M1a query tests passed:

```text
pytest: 56 passed in 6.98s
```

The run covered the M1a read projections, Note structural-read behavior,
error compatibility, generated golden contracts, and S1/S2 deterministic
regression. The S1/S2 regression used fresh copies and verified that all reads
leave the source workspaces byte-identical.

### 2. Benchmark and runtime budget

Benchmark: **PASS**, Python `3.12.13`.

```text
module_help       74.831 ms
plugin_help       71.497 ms
module_enter_1000 599.621 ms
plugin_enter_1000 622.953 ms
module_list_1000  862.335 ms
plugin_list_1000  850.805 ms
```

The M1a performance limits are satisfied: help is below 250 ms and 1,000-Entry
`enter` is below 1 s. The canonical runtime has 1,256 nonblank lines against the
1,082-line baseline, a delta of +174 within the +149–176 target. Every module
is below 400 nonblank lines:

```text
__init__.py   2
__main__.py   2
cli.py        145
core.py       26
md.py         63
notes.py      143
query.py      146
records.py    311
state.py      106
workspace.py  312
TOTAL         1256
```

### 3. Generated goldens and S1/S2 regression

The generated goldens are public API schema outputs for:

- `aitp/enter-0.2`;
- `aitp/list-0.1`;
- `aitp/show-0.1`.

The deterministic S1/S2 regression passed with the declared counts and
payloads. Read commands preserved byte identity before and after the reads;
no suite seed or frozen input was modified.

### 4. Read-only GW_librpa acceptance

The latest in-place read-only acceptance was run against the concurrent active
`/home/bhjia/physics/GW_librpa` store. At the evidence timestamp:

- `.aitp`: **417 files before and after, byte-identical**;
- `list --json`: schema `aitp/list-0.1`, count **194**;
  active **156**, superseded **38**;
- `list --kind result --json`: **34** results;
- `enter --json`: schema `aitp/enter-0.2`, active **156**, superseded **38**,
  unresolved **17**, malformed **0**, omitted_active **136**;
- `show` of a superseded Entry succeeded;
- every read window was identical before and after the command sequence.

The only warning was the historical Entry
`entry-97bec98c58634e21aecbba57a2bee48e`, whose raw `created_at` is
`+now+` and therefore produces an `invalid_timestamp` warning. This is an
honest read warning, not a read failure and not a save-path validation change.

The GW snapshot is dynamic compatibility evidence, not a frozen golden count.
Concurrent sessions changed the natural store during acceptance; an earlier
same-session snapshot reported 188/150/38/33/19. The older 2026-08-06
60-Entry observation is historical dogfood evidence. Count differences between
these snapshots are expected natural activity and must not be treated as a
regression or a failed acceptance. The invariant tested here is deterministic,
read-only projection behavior and byte-identical `.aitp` state before/after.

### 5. Version and frozen-boundary checks

M1a version metadata is **0.2.0**; the Codex manifest carries its timestamp
suffix. FROZEN v6 and all 15 frozen suite inputs remain unchanged. The frozen
suite remains an anchored, unexecuted preregistration and is not retroactive
behavioral or treatment evidence for M1a.

Bootstrap Notes/decisions, recall, false-import rate, human time, held-out S3,
paired S1/S2 treatment-control scores, cold-start, conformance, causal claims,
and treatment advantage remain **not measured; deferred; not counted**. The
external evaluation harness remains optional future work and cannot retroactively
satisfy those gaps.

## Gate checklist

- [x] M1a implementation from `docs/m1a-spec.md` completed.
- [x] `aitp/enter-0.2`, `aitp/list-0.1`, and `aitp/show-0.1` generated outputs
      match the public schema contracts.
- [x] Read-only Note structural validation: malformed structural Notes are
      omitted with warning and `counts.malformed`; structurally valid Notes
      with missing or drifted `basis_refs` remain readable because reads use
      `validate_evidence=False`; `.aitp` remains byte-identical and reads take
      no lock or write local state; save evidence validation is unchanged.
- [x] S1/S2 deterministic seed regression and read-before/after byte identity.
- [x] Generated goldens and all 56 tests.
- [x] GW_librpa read-only byte-identical acceptance, with dynamic snapshot
      counts recorded above and the single historical timestamp warning
      preserved.
- [x] Help, 1,000-Entry `enter`/`list`, module, and cumulative line caps.
- [ ] Paired treatment-control evidence — optional future evidence, not an M1a
      gate and not a claim made by this closure.

## Post-M1a natural-use pause

The next step is a deliberately small review period:

1. hold at least two ordinary, unscripted real-Topic sessions using the now
   available `init`, `enter`, `inventory`, `record`, `note`, `list`, and `show`
   commands;
2. review actual use, unmet pain, workarounds, maintenance cost, and whether
   the read projections restore state without unnecessary complexity;
3. record whether any M1b runtime slice is naturally demanded; **no M1b runtime
   slice remains a valid result**;
4. only after that pause, review/freeze the authoritative A–H dispositions in
   `docs/m1b-spec.md` §0.1 and separately authorize any selected slice.

### First natural-use feedback (2026-08-11)

The first natural-use feedback arrived 2026-08-11 from
`/home/bhjia/physics/GW_librpa`
([`feedback/2026-08-11-gw-librpa-natural-use-feedback.md`](../feedback/2026-08-11-gw-librpa-natural-use-feedback.md)):

- it is one single long-session chain, not two ordinary sessions, so the
  pause requirement is not met; a second ordinary session is still pending;
- it authorizes only Skill/docs improvements — dense-campaign record
  granularity, working-Note natural-use checks, closeout replacement over
  stale-handoff edits, and an illustrative (non-normative) pointer-manifest
  example; no M1b runtime, schema, or command change;
- the A–H dispositions in `docs/m1b-spec.md` §0.1 are unchanged;
- its §6 provisional order (D, then B, then A) is only a future re-review
  order, not a selected disposition;
- the historical `created_at: +now+` warning on
  `entry-97bec98c58634e21aecbba57a2bee48e` remains a documented ledger record;
  repairing it is a separate audited action, not part of this change.

### Natural-use pause complete (2026-08-12)

The two-session ordinary natural-use pause is complete:

- first ordinary session: the 2026-08-11 GW/LibRPA long session chain
  ([`feedback/2026-08-11-gw-librpa-natural-use-feedback.md`](../feedback/2026-08-11-gw-librpa-natural-use-feedback.md));
- second ordinary session: the 2026-08-12 Power-law Heisenberg independent
  real-Topic correction session
  ([`feedback/2026-08-12-power-law-heisenberg-natural-use-feedback.md`](../feedback/2026-08-12-power-law-heisenberg-natural-use-feedback.md));
- the researcher's six followup suggestions are archived in
  [`feedback/2026-08-12-gw-librpa-followup-feedback.md`](../feedback/2026-08-12-gw-librpa-followup-feedback.md).

The reviewed freeze revision is recorded in
[`docs/m1b-adjudication.md`](../docs/m1b-adjudication.md) (actual M1a total
1,256; M1b headroom 194) and selected the read-side slice **M1b-R1** —
read-only `check` over v0.1 contracts and a compact `enter` text renderer
with two frozen M1a safety lines and two structural hints — implemented per
the implementation-level spec
[`docs/m1b-r1-spec.md`](../docs/m1b-r1-spec.md); the deterministic gate
**passed** (evidence recorded in
`docs/m1b-r1-stage-notes.md`).
`lineage` (Followup 2) was re-deferred at the 2026-08-12 budget
reconciliation (measured prototype with lineage leaves insufficient cap
margin). Neither session is a
controlled experiment; no superiority claim is made.

M2 and M3 remain design options requiring their own natural-demand evidence.
The M1b-R1 deterministic gate passed on 2026-08-12 (evidence in
`docs/m1b-r1-stage-notes.md`); `check` is shipped and gated;
`lineage` is
a deferred candidate.