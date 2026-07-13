# AITP Capability Registry Report

Date: 2026-07-10

## Contract

`CapabilitySpec` now joins the compatibility runtime catalog, complete MCP
surface, public validators, compact allowlist, and host bridge targets. Every
capability declares one of three AITP state effects:

- `read_only`: no AITP runtime or canonical write;
- `runtime_write`: derived indexes, generated views, installation/configuration,
  or other non-canonical runtime state;
- `kernel_write`: canonical typed research or process state.

The live audit rejects missing or duplicate MCP names, unknown public surfaces,
compact allowlist drift, bridge-target drift, conflicting state effects, and
unclassified compatibility-catalog operations.

## M0 Operations

The full MCP surface now exposes contracted operations for:

- capability-registry audit;
- source/file/runtime capability audit;
- derived query-index build and read-only status;
- exact typed-record expansion with retrieval coverage;
- bounded research-context compilation.

Context compilation requires a prebuilt index on this read-only wrapper. It
does not silently create derived state. Query-index construction is explicitly
classified as `runtime_write` and was verified not to change canonical
Markdown content.

## Live Parity

| Measure | Result |
|---|---:|
| Registered capabilities | 225 core + 1 detected extension |
| Compatibility catalog operations | 199 |
| Complete MCP wrappers | 225 core + 1 detected extension |
| Public surface contracts | 198 |
| Compact MCP tools | 16 |
| Host bridge targets | 43 |
| Read-only operations | 120 |
| Runtime-write operations | 34 |
| Kernel-write operations | 72 |
| Registry audit issues | 0 |

The 26 core MCP-only operations are explicit registry entries. They include
the compact facade, setup and legacy compatibility wrappers, Harness Feedback
read surfaces, and the new M0 operations. The current shared worktree also
contains one independently developed Harness Feedback dossier wrapper; its
explicit optional declaration is activated only when that wrapper is present.
A stable registry reference in `runtime_entrypoint_catalog.py` keeps the old
CLI/MCP catalog auditable during migration.

## Verification

- Capability registry, M0 wrapper behavior, and optional-extension
  isolation: 8 passed in 3.56 seconds.
- Public surface, runtime entrypoint, and bridge parity: 32 passed in 8.23
  seconds.
- Full capability/public/bridge/adapter matrix: 127 passed in 547.07 seconds.
- Runtime audit, Codex facade, MCP, query-index, and context regressions: 48
  passed in 5.23 seconds.
- Staged-tree isolation without the uncommitted Harness Feedback extension: 32
  capability and public-surface tests passed in 14.99 seconds.
- Architecture RED baseline: 2 failed and 4 passed, with 39 oversized modules
  and the 1,509-line `cli.py` boundary failure.
- M0 release architecture verification: all six architecture tests pass;
  recursive release checks also cover every compatibility shard without
  increasing a line limit.

The 9-minute adapter matrix is now a separate `slow-adapter` CI lane; foundation
and compatibility remain the fast feedback paths. The scheduled full suite is
rooted explicitly at `tests/` so local historical `tmp/` worktrees cannot be
collected as duplicate tests.
