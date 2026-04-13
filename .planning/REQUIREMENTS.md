# Requirements: v2.2 Fresh-Topic First-Use Reliability

## Milestone Goal

Make fresh-topic public entry reliable enough that a real new topic can be
opened from natural language, register its first source on Windows without
path failure, and surface honest `L0` status immediately after first-use
actions.

## Active Requirements

### Front Door Routing

- [x] `FTF-01`: `aitp session-start "<natural-language request>"` recognizes
  explicit new-topic intent and allocates a fresh topic instead of reopening
  current-topic memory.

- [x] `FTF-02`: the new-topic route leaves durable routing evidence showing
  why fresh-topic intent beat current-topic continuation fallback.

### Source Registration Reliability

- [x] `FTF-03`: first-source registration survives long Windows topic slug +
  paper-title combinations without requiring a manual `\\?\` path workaround.

- [x] `FTF-04`: after successful source registration, status-facing `L0`
  counters and source presence are immediately coherent, or one explicit sync
  step is enforced and reflected honestly.

### Replayable First-Use Proof

- [x] `FTF-05`: one replayable fresh real-topic acceptance lane proves
  new-topic routing, first-source registration, and honest status coherence
  from the public front door.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Reopening the bounded `L2` hardening slice from `v2.1` | treat `v2.1` as the current truth unless a fresh regression appears |
| Broad benchmark-alignment schema overhaul (`999.87`–`999.92`) | still too wide for the immediate first-use reliability slice |
| New authoritative scientific claims in formal, toy-model, or first-principles lanes | `v2.2` is about honest first-use routing and source-state coherence |
| General retrieval redesign beyond first-use status and routing | keep the milestone bounded to fresh-topic entry reliability |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FTF-01 | Phase 176 | Done |
| FTF-02 | Phase 176 | Done |
| FTF-03 | Phase 176.1 | Done |
| FTF-04 | Phase 176.1 | Done |
| FTF-05 | Phase 176.2 | Done |

**Coverage:**
- v1 requirements: 5 total
- mapped to phases: 5
- unmapped: 0
