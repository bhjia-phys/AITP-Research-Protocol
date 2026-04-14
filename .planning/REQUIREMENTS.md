# Requirements: v2.7 Consultation-Followup Selection Closure

## Milestone Goal

Make post-review consultation coherent enough that, once
`consultation_followup` becomes the selected route on a fresh topic, the loop
can execute that consultation, write a durable selection artifact, and advance
onto one selected topic-local staged candidate instead of stalling on the
generic consult prompt.

## Active Requirements

### Executable Consultation-Followup

- [x] `CFS-01`: once `consultation_followup` has been surfaced and the operator
  continues again, the bounded loop can execute one topic-local
  `consult-l2(record_consultation=True)` step.

- [x] `CFS-02`: that consultation-followup step writes durable consultation and
  selection artifacts rather than remaining an in-memory or prose-only step.

### Candidate-Specific Route Advancement

- [x] `CFS-03`: once a bounded topic-local staged candidate has been selected,
  queue materialization and public `next` / `status` advance to a
  candidate-specific follow-up action rather than staying on generic
  consultation-followup language.

### Replayable Proof

- [x] `CFS-04`: one replayable fresh-topic proof shows the same topic can
  execute consultation-followup, materialize the selection artifact, and
  advance onto the selected staged candidate while the earlier staged-L2
  baselines still pass.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Reopening staged-L2 post-review advancement from `v2.6` | treat the `v2.6` consultation surface as the new baseline unless a fresh regression appears |
| Automatic validation-route choice, candidate execution, or promotion | `v2.7` stops at bounded candidate selection and route advancement |
| Global canonical candidate auto-selection | keep the milestone honest by selecting only topic-local staged hits automatically |
| Broad three-lane scientific widening across formal, toy, and first-principles routes | defer until post-review candidate choice is mechanically stable |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CFS-01 | Phase 181 | Done |
| CFS-02 | Phase 181 | Done |
| CFS-03 | Phase 181.1 | Done |
| CFS-04 | Phase 181.2 | Done |

**Coverage:**
- v1 requirements: 4 total
- mapped to phases: 4
- unmapped: 0
