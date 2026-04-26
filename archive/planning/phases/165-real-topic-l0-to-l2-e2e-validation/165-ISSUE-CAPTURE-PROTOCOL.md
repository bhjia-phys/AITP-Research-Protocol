# Issue Capture Protocol

Use this protocol for every problem discovered during the real-topic E2E run.

## Why this exists

GSD does not reliably auto-discover arbitrary runtime or product problems from
AITP artifacts alone.

So the issue-discovery step must be explicit.

This protocol ensures that:

- issue capture is uniform
- later GSD routing is easy
- no real-topic finding is lost in chat memory

## One issue = one row

Record one issue per row in `165-ISSUE-LEDGER.md`.

Do not pack all friction from one session into one mega-row.

## Required fields

Each issue row must answer:

- `issue_id`
  - stable issue label such as `issue:codex-bootstrap-001`
- `severity`
  - `P0`, `P1`, `P2`, or `P3`
- `category`
  - one short category such as `runtime`, `ux`, `protocol`, `docs`, `adapter`, `install`
- `front_door`
  - where the issue was observed:
    - `codex`
    - `claude-code`
    - `opencode`
    - `openclaw`
    - `kernel-cli`
- `topic_slug`
  - the real topic that exposed the problem
- `summary`
  - one-sentence problem statement
- `expected`
  - what should have happened
- `actual`
  - what actually happened
- `evidence_ref`
  - one or more durable artifact paths or command outputs
- `discovered_during`
  - the command or step where the issue appeared
- `proposed_gsd_destination`
  - `current-milestone-decimal`, `next-milestone-candidate`, or `backlog`
- `status`
  - `open`, `triaged`, `routed`, `resolved`, or `deferred`

## Severity rules

### `P0`

Use when:

- the run cannot continue at all
- trusted state is corrupted
- a core trust boundary is violated

Default routing:

- `current-milestone-decimal`

### `P1`

Use when:

- the run can continue only by bypassing the intended product path
- the current bounded route is effectively blocked

Default routing:

- `current-milestone-decimal`
  or `next-milestone-candidate`

### `P2`

Use when:

- the run is still possible
- but the product behavior is confusing, misleading, or much rougher than intended

Default routing:

- `next-milestone-candidate`

### `P3`

Use when:

- the problem is clarity, polish, or maintenance debt
- it did not materially distort the route outcome

Default routing:

- `backlog`

## Evidence rules

Always attach a durable ref when possible:

- `runtime/topics/<topic_slug>/topic_dashboard.md`
- `runtime/topics/<topic_slug>/runtime_protocol.generated.json`
- `runtime/topics/<topic_slug>/topic_replay_bundle.json`
- `runtime/topics/<topic_slug>/layer_graph.generated.md`
- `runtime/explorations/<exploration_id>/explore_session.md`
- `doctor --json` output snapshots
- adapter install/config artifacts

If the evidence came from a conversation turn, copy the relevant result into:

- `evidence/<topic-slug>/COMMANDS.md`

and then point the ledger row at that file.

## Routing rules into GSD

After adding a row to the ledger, do one more explicit step:

### Route to current milestone decimal phase

Use this when the issue blocks the real-topic milestone itself.

Example destination text:

- `v1.91 / Phase 165.1 urgent blocker fix`

### Route to next milestone candidate

Use this when the issue is important and real but does not need to stop the
current real-topic run.

Example destination text:

- `candidate: next milestone after v1.91`

### Route to backlog

Use this when the issue is real but safely deferrable.

Example destination text:

- `BACKLOG 999.x candidate`

## Relationship to postmortem

The postmortem explains the run.

The issue ledger enumerates actionable follow-up.

Rule:

- every issue mentioned in the postmortem must appear in the ledger
- the postmortem may summarize
- the ledger is the actionable tracking surface
