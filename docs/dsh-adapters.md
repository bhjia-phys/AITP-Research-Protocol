# DeepSeek Harness AITP adapter (anchored-aitp)

AITP-side record for the DeepSeek Harness adapter. The adapter is the
`anchored-aitp` mode in the external
[`xiaobright/dsh-anchored-standard`](https://github.com/xiaobright/dsh-anchored-standard)
repository: Anchored Standard's two-phase tool catalog with the AITP Research
Protocol layer on top. This document is the AITP-side baseline that a dsh
development session should read before building or changing its AITP adapter,
and that AITP sessions must keep current whenever a stage, CLI, or schema
status changes (the same discipline as the
[Hakimi handoff](hakimi/README.md)).

- Recorded: **2026-08-17**, AITP HEAD `9f9e873440b8d88bfbb2963d8b5717c83b9ef4cc`,
  contract `aitp/adapter-contract-0.1` (sha256
  `c6d815dd4c0abba98b2354da6653e0db9156a455197610c4212c3ca448f229b1`),
  launcher sha256
  `d6fca2789be428faa1c81eb532a9072ea99a4a5ae69029687f2a37d9ab7124f9`.
  **Pending re-sync**: the 2026-08-21 0.8.0 Skill-only amendment changed
  plugin version to 0.8.0 and updated Skill text and manifest descriptions
  (method-observation markers, two-step human decisions, platform
  tool/card/Skill boundary, best-effort fallback) but changed **no** CLI
  command, flag, transport schema, or `aitp/adapter-contract-0.1` schema —
  only the `plugin.version` field and Skill/manifest text. The external dsh
  repo must run `sync:aitp` on its next change to pick up the new version
  and Skill hashes; no adapter code change is required.
- Status: **draft adapter; deterministic tests pass; no AITP gate evidence**.
  This adapter is a consumption surface, not AITP evidence. It does not
  revise or refreeze FROZEN v6 and makes no treatment-superiority claim.

## Adapter mechanism

Everything AITP is materialized (copied, never forked) from this repository's
plugin bundle into the self-contained `anchored-aitp/` mode directory by the
mode repository's `scripts/sync-aitp.mjs`, which records a delivery manifest
(`aitp-vendor.json`: source commit, contract/launcher/Skill sha256) and can
verify drift with `--check`.

| AITP surface | dsh consumption |
|---|---|
| `aitp.contract.json` | `aitp-tools.mjs` builds every `aitp_*` tool from it — names, descriptions, and parameter schemas verbatim; no reworded model-facing text. The contract is the adapter's single authority: launcher path and Python minimum come from `python.launcher`/`python.min_minor`, the Skill set from `skills[]` (every declared Skill file must be materialized or the mount fails), and `operator_only` (init/inventory) is deliberately absent from the tool surface — the same restriction Hakimi has |
| `semantic_policy_files` (`suite/policy.md`) | evaluation-policy input of the AITP suite, resolved against the AITP repository root; not a runtime surface, not materialized |
| `scripts/aitp.py` | the tool runner shells out to the canonical launcher (`--json`); Python 3.13/3.12/3.11/3 probed with version >= 3.11 |
| `skills/` | `aitp-skills.mjs` registers the three Skills (`aitp`, `using-aitp`, `distilling-methods`) as a provider behind `skill_search`/`skill_load` — no catalog injection |
| exit codes | 0/1 carry the JSON result; 2 surfaces the AITPError JSON envelope (`status`/`code`/`message`) as a tool error, fail closed |
| session-boundary maintenance | the mode's `aitp-orient` hint fires once after the anchored promotion in `.aitp/` workspaces ("call `aitp_enter` first"); closeout/working-note upkeep stays Skill-guided — no hooks, no daemons |

## Anchored two-phase interaction (dsh-specific)

- Request #1 stays the Minimal tool pair (`bash` + `str_replace_editor`);
  no `aitp_*` tool, no orientation message, no AITP context — the trajectory
  anchor is untouched (the mode's whole reason to exist).
- After promotion the resident catalog adds the AITP read tools
  (`aitp_enter`, `aitp_check`, `aitp_list`, `aitp_show`); the write tools
  (`aitp_record_*`, `aitp_note_*`, `aitp_backfill_workstreams`) stay one
  `dev_tool_search` unlock away.
- After compaction the controlled set keeps `aitp_enter`/`aitp_check`
  (restoring recorded state matters most right after a compaction).

## Contract-compliance checklist

Per the README's cross-harness adapter sync rules, this adapter:

1. builds its `aitp_*` tools from `aitp.contract.json` — yes (verbatim);
2. reads Skills from the AITP surface — yes (materialized from the checkout,
   hashed in `aitp-vendor.json`);
3. passes a preflight (`contractSchema` known-set check, launcher existence,
   logged sha256, optional `pinSha256` hard pins) — yes, and an unknown
   contract schema fails the mount closed instead of falling back to a stale
   command surface;
4. records the exact AITP commit, contract sha256, launcher sha256, and
   delivered Skill hashes with the run — yes (`aitp-vendor.json` + mount log);
5. treats the CLI as the integration boundary — yes; no MCP, hook, or daemon.

Additive contract changes propagate on the next `sync:aitp`. A breaking or
semantic contract change must go through the same explicitly reviewed adapter
revision process as Hakimi (update `aitp.contract.json` +
`tests/ledger/test_adapter_contract.py` in the same change, then re-sync both
adapters).
