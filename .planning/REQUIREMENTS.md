# Requirements: v1.67 Cross-Runtime Deep Execution Parity

## Milestone Goal

Move Claude Code and OpenCode from install/front-door parity targets to honest
deep-execution parity probes against the Codex baseline, while keeping
OpenClaw explicitly deferred as a specialized lane.

## Active Requirements

### Parity Contract

- [x] `REQ-PARITY-01`: the repository distinguishes install/front-door
  readiness from deep-execution readiness through one explicit runtime parity
  contract instead of treating a green `doctor` row as sufficient proof.
- [x] `REQ-PARITY-02`: Codex remains the declared baseline runtime with one
  bounded real-topic execution lane and artifact-quality bar that parity
  targets must be compared against.

### Runtime Probes

- [ ] `REQ-PARITY-03`: Claude Code has one bounded real-topic deep-execution
  probe that enters through its supported bootstrap surface, reaches durable
  AITP artifacts, and records where it matches or falls short of the Codex
  baseline.
- [ ] `REQ-PARITY-04`: OpenCode has one bounded real-topic deep-execution
  probe that enters through its supported bootstrap surface, reaches durable
  AITP artifacts, and records where it matches or falls short of the Codex
  baseline.

### Verification And Closure

- [ ] `REQ-VERIFY-01`: the milestone closes with targeted regression coverage,
  one shared parity audit/report surface, and bounded acceptance evidence for
  Codex, Claude Code, and OpenCode.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| REQ-PARITY-01 | Phase 134 | Complete |
| REQ-PARITY-02 | Phase 134 | Complete |
| REQ-PARITY-03 | Phase 135 | Pending |
| REQ-PARITY-04 | Phase 136 | Pending |
| REQ-VERIFY-01 | Phase 137 | Pending |
