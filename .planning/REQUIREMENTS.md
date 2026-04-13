# Requirements: v1.94 L4 Analytical Cross-Check Surface

## Milestone Goal

Close the next post-`v1.93` validation-maturity gap by making bounded
analytical cross-checks explicit, durable, and visible on runtime/read-path
surfaces instead of leaving analytical validation as a thinner review artifact
that must be opened directly.

## Active Requirements

### Analytical Check Contract

- [x] `REQ-ANX-01`: analytical validation records explicit bounded check rows
  for limiting-case, dimensional, symmetry, self-consistency, and
  source-cross-reference checks instead of only a flatter aggregate review.
- [x] `REQ-ANX-02`: each analytical check row carries the exact source anchors,
  assumption or regime context, and per-check status needed to judge why the
  check passed, failed, or remained blocked.

### Runtime Surface

- [x] `REQ-ANX-03`: `status`, `runtime_protocol`, and the primary analytical
  read path expose the same analytical cross-check surface so the operator can
  inspect bounded validation state without opening raw review JSON.

### Verification

- [x] `REQ-VERIFY-01`: the milestone closes with one bounded analytical
  cross-check proof lane that shows a candidate can surface durable analytical
  checks and replay them through the runtime read path.

## v2 Requirements

### Broader Analytical Validation

- `REQ-ANX-V2-01`: analytical validation can compare multiple candidate routes
  or hypotheses instead of one bounded candidate at a time.
- `REQ-ANX-V2-02`: analytical cross-check outcomes can directly shape later
  route choice or contradiction adjudication rather than only informing read
  surfaces.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Full symbolic algebra or CAS integration | This milestone is about bounded analytical validation surfaces, not a new symbolic execution backend |
| Automatic route mutation from analytical checks | First make analytical cross-checks explicit and replayable |
| Broader numerical benchmark expansion | Keep the scope on analytical cross-check visibility rather than reopening the numerical lane |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| REQ-ANX-01 | Phase 168 | Complete |
| REQ-ANX-02 | Phase 168 | Complete |
| REQ-ANX-03 | Phase 168.1 | Complete |
| REQ-VERIFY-01 | Phase 168.1 | Complete |

**Coverage:**
- v1 requirements: 4 total
- Mapped to phases: 4
- Unmapped: 0

---
*Requirements defined: 2026-04-13*
*Last updated: 2026-04-13 after closing milestone v1.94*
