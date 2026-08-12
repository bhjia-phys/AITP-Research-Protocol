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
  the 2026-08-12 M1b planning sync, and the 2026-08-12 M1b-R1 gate
  completion below.
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
  report on exits 0 and 1; exit 2 is the error envelope). `lineage` is a
  deferred candidate.
  `enter` stays at `aitp/enter-0.2`; its text rendering is now
  compact, and that text is human-facing only — never feature-detected.
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
| H1 | M1a done; deterministic gate passed | Read-only feature detection and schema dispatch for `aitp/enter-0.2`, `aitp/list-0.1`, and `aitp/show-0.1`; closeout-first handoff; Note-age signal; generated-golden compatibility tests; plugin version `0.2.0` |
| H2 | M1b-R1 selected 2026-08-12; implemented per `docs/archive/m1b-r1-spec.md`; deterministic gate passed 2026-08-12 | Integrate only capabilities actually shipped by the R1 gate: `aitp check` (parse `aitp/check-report-0.1` on exits 0 and 1; exit 2 is the error envelope), and consume the compact `enter` text only as human-facing output (never parse it; machine output is the versioned JSON). Persisted `based_on`/`used_by`, pointer bundles, quick-run, and `lineage` are **not** in R1 and must not be scheduled for H2 |
| Formal Hakimi contract | after M4 | Versioned `--json` + extended golden fixtures as the pass gate for any agent integration |

Hakimi's research-loop capabilities (web, PDF, reasoning, session UX, private
caches) are independent of all AITP gates and can proceed in parallel at any
time.

## Maintenance contract (binding)

Update this directory **in the same change** as any of the following:

- stage status flips (M0.6 gate, M1a gate, M1b gate, M2–M4);
- CLI surface change (new or removed command/flag; `--help` output);
- schema status change (new frozen payload/file schema, version bump);
- M1b scope or gate sequencing change (natural-use review, candidate
  disposition, selected slice, split/revision/deferral, or no-runtime result);
- a Hakimi-side integration finding that changes a matrix row or a red line.

The flip of a roadmap row happens through the gate review; this directory only
records the consequence. Never edit `docs/roadmap.md` stage statuses from
here. M1a has landed; the synchronized version metadata is `0.3.0` and the
read contracts are available. Keep the frozen `suite/adapters/cli.md`
unchanged until a separately reviewed suite refreeze. Hakimi H1 may now
feature-detect the three versioned read schemas; `check` is shipped and
gated (M1b-R1 per `docs/archive/m1b-r1-spec.md`; gate evidence in
`docs/archive/m1b-r1-stage-notes.md`) and may be feature-detected now;
`lineage`
is a deferred candidate.

## Reading order

1. `/home/bhjia/physics/repo/AITP-Research-Protocol/AGENTS.md`
2. `/home/bhjia/physics/repo/AITP-Research-Protocol/README.md`
3. `/home/bhjia/physics/repo/AITP-Research-Protocol/docs/roadmap.md` (stage table, M1a, M1b, Hakimi contract)
4. `compatibility-matrix.md` (this directory)
5. `docs/archive/m1a-spec.md`, `docs/m1b-spec.md`, `docs/archive/collaborator-design.md`
6. The installed plugin's `skills/using-aitp/SKILL.md` (python probe order, command map)
7. The runtime: `plugins/aitp-research-protocol/scripts/aitp.py` + `scripts/vendor/aitp/`

Then the Hakimi repository's own `AGENTS.md`/`README.md`/architecture.
