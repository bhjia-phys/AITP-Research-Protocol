# Harness Feedback Case: <CASE_ID>

Status: `pending_review`
Problem type: `missing_workflow_provenance`
Topic: `nio-magnetic-gw`
Host: `codex`
Affected capability: `execution_recall`
Affected record family: `tool_runs`
Source fingerprint: `<SOURCE_FINGERPRINT>`

## Observed Friction

The resumed calculation does not identify the exact magnetic setup used by the prior run.

## Expected Behavior

Recall should expose the pinned input, code state, and run references before reuse.

## Actual Behavior

The compact summary names the result but omits the executable provenance chain.

## Impact

A later calculation can reuse an incompatible setup while appearing to follow the same workflow.

## Reproduction

1. Resume the NiO magnetic GW topic in a fresh host session.
2. Request the compact execution context.
3. Inspect whether the FHI-aims input and LibRPA code-state references are present.

## Runtime Context

- `event`: `session_start`
- `surface`: `compact`

## Source References

- `tool_run:nio-gw-run-17`
- `code_state:librpa-nio-state-4`

## Proposed Direction

Expose the exact input and code-state references in the compact execution entry.

## Review Boundary

This is an observation-only review input. It cannot change research records or runtime behavior.
