# AITP M5 Task 1 Research Moments Audit

## Scope

This slice implements the host-neutral `ResearchEvent -> ResearchMomentDecision
-> MomentReceipt` boundary. It does not expose new MCP/CLI tools, alter compact
tool count, connect host hooks, or change Harness Feedback.

## Implemented Boundary

- Ten structured logical event types and exactly six outcomes.
- Pure deterministic policy with workspace/host/session/topic/event/payload
  identity bound into one SHA-256 decision digest.
- Exact, allowlisted objective capture for source assets, code states, tool runs,
  and artifacts through existing canonical writers.
- Existing-record verification for already captured process facts.
- Runtime-only semantic staging and one closeout review batch.
- Human checkpoints for authority-bearing or expensive actions.
- Closed prerequisites for missing refs, stale pins, malformed structured
  payloads, mixed objective/semantic events, and unsafe auto-capture options.
- Bounded read-only literature-discovery handoff from an exact persisted gap and
  recall-audit pin. The handoff cannot acquire a source or update trust.
- Recursive AITP output and unchanged status polls are ignored.
- Per-decision runtime transaction locks make concurrent replay apply once.
- Runtime receipts are hash checked, path contained, idempotent, and
  trust-neutral.

## Trust And Ownership

- `can_update_claim_trust` is always false on events, decisions, staging, and
  receipts.
- Automatic tool-run capture is diagnostic and unreviewed; it cannot declare a
  final lane.
- Source capture cannot force-refresh stored bytes through the moment path.
- Decision application verifies the operation's declared effect against the
  generated `CapabilitySpec` before any side effect.
- Semantic content never calls evidence, validation, memory promotion, Skill
  install, or claim-trust writers.
- No real topic-store canonical records were modified. All write tests used
  isolated system-Temp workspaces.

## Verification Evidence

- RED: 18 expected failures because the two initial modules did not exist.
- Focused final moment suite: 26 passed.
- Moment plus ranked-lock concurrency: 44 passed.
- Expanded recording, literature, execution, checkpoint, capability, runtime,
  architecture, repository, trust, and session-lifecycle regression: 181 passed.
- Final expanded regression including ranked-lock concurrency: 200 passed.
- Exact staged-index export reran the same final regression: 200 passed.
- Compact MCP registry readback: exactly 10 tools.
- Python compilation and `git diff --check`: passed.
- New behavior modules remain bounded: contracts 290 lines, validation 234,
  policy 472, application 314, facade 21.

## Deliberate Non-Changes

`brain/v5/moment_policy.py` remains the existing graph-orientation policy and
`brain/v5/recording_navigator.py` remains the existing recording workflow.
Merging host-event policy into either would recreate a mixed-responsibility
module. The new `research_moments.py` facade is the stable composition boundary.

Context injection, real host lifecycle adapters, generic Harness Feedback, and
MCP/CLI exposure remain M5 Tasks 2-5. In particular, Harness Feedback must be
aligned with the approved no-Skill-candidate boundary before it enters the M5
release candidate.
