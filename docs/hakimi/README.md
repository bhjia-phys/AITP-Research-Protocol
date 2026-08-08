# Hakimi integration handoff

Single entry point for the cross-repository handoff between AITP (protocol,
persistence, evidence authority) and Hakimi (agent orchestration, tool
invocation, interaction UX). This directory is the AITP-side baseline that a
Hakimi development session should read before building or changing its AITP
adapter, and that AITP sessions must keep current whenever a stage, CLI, or
schema status changes.

- Baseline audit: **2026-08-08**, AITP HEAD `8658f6827288f4bb61e5c193a346f0f73ebbe3b2`,
  read-only (only `/tmp` throwaway copies were written; no runtime, spec, or
  record was changed). The audit concluded that **no AITP plan change is
  required**: the frozen M1a/M1b specifications already cover every Hakimi
  integration need.
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

| Phase | AITP prerequisite | Hakimi work |
|---|---|---|
| H0 | now (no gate) | Launcher adapter (argv-only, Python ≥ 3.11 probe), strict shape validation of unversioned envelopes, capability detection from `--help`, `enter` lifecycle, prepare→fill→save flow, graceful degradation on `not_initialized`, tree-hash zero-write tests |
| H1 | M1a gate | Schema dispatch on `aitp/enter-0.2`, `aitp/list-0.1`, `aitp/show-0.1`; closeout-first handoff; Note-age signal; AITP golden-fixture compatibility tests |
| H2 | M1b gate | `aitp check` exit 0/1/2; `aitp/lite-entry-0.2` (`based_on`, typed closures); derived `used_by`; pointer bundles (read-only) |
| Formal Hakimi contract | after M4 | Versioned `--json` + extended golden fixtures as the pass gate for any agent integration |

Hakimi's research-loop capabilities (web, PDF, reasoning, session UX, private
caches) are independent of all AITP gates and can proceed in parallel at any
time.

## Maintenance contract (binding)

Update this directory **in the same change** as any of the following:

- stage status flips (M0.6 gate, M1a gate, M1b gate, M2–M4);
- CLI surface change (new or removed command/flag; `--help` output);
- schema status change (new frozen payload/file schema, version bump);
- a Hakimi-side integration finding that changes a matrix row or a red line.

The flip of a roadmap row happens through the gate review; this directory only
records the consequence. Never edit `docs/roadmap.md` stage statuses from
here. When M1a lands, also sync per `docs/m1a-spec.md` §Sync (roadmap, README,
design.md, spec index, Skills, `suite/adapters/cli.md`, plugin version bump).

## Reading order

1. `/home/bhjia/physics/repo/AITP-Research-Protocol/AGENTS.md`
2. `/home/bhjia/physics/repo/AITP-Research-Protocol/README.md`
3. `/home/bhjia/physics/repo/AITP-Research-Protocol/docs/roadmap.md` (stage table, M1a, M1b, Hakimi contract)
4. `compatibility-matrix.md` (this directory)
5. `docs/m1a-spec.md`, `docs/m1b-spec.md`, `docs/collaborator-design.md`
6. The installed plugin's `skills/using-aitp/SKILL.md` (python probe order, command map)
7. The runtime: `plugins/aitp-research-protocol/scripts/aitp.py` + `scripts/vendor/aitp/`

Then the Hakimi repository's own `AGENTS.md`/`README.md`/architecture.
