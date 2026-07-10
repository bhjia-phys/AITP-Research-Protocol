# AITP Bounded Host Injection Report

Date: 2026-07-10

## Router Contract

- The UserPromptSubmit router reads topic metadata only. It contains no
  `MEMORY.md` read path and never injects topic memory bodies.
- Valid UTF-8 English and Chinese signals replace the previous mojibake list.
- Legacy `state.md` and v5 `.aitp/topics/<id>/topic.md` metadata are merged by
  topic id.
- Candidate topics are scored against topic id, title, short research question,
  lane, matched domain signals, and request terms.
- At most six matching topics are emitted. Unmatched topics are not listed.
- Output contains only matched signals, topic ids/titles/short questions,
  canonical base, compact facade entrypoints, and the trust-neutral boundary.
- `additionalContext` has a hard 4,096-byte ceiling.

## Startup Contract

- Full topic status remains an explicit explainability surface.
- Host startup uses `topic_status_startup.py`, which builds a bounded context
  pack and exact session binding without constructing the full execution brief.
- Full topic status, generated session-start files, and startup refresh share a
  stable `compact_context_boundary`: fingerprint, pack id, index generation,
  retrieval coverage, byte/token counts, and trust-neutral flags.
- The lightweight startup relation map explicitly says exact expansion is
  required; it does not invent evidence support or validation state.

## Measurements

On the real 43-topic research workspace, a LibRPA/QSGW continuation request
produced:

| Measure | Result |
|---|---:|
| Additional context | 2,027 bytes |
| Candidate topics | 6 |
| Memory bodies/headings | 0 |
| First candidate | `qsgw-headwing-update-librpa` |

The focused full-topic-status plus lightweight-startup consistency pair passed
in 0.46 seconds. The broader 40-test compatibility slice passed in 163.56
seconds; most of that time belongs to explicit full topic-status compatibility
tests, not the new startup path.

## Verification

- 40 router, deployment-template, full topic-status, lightweight startup,
  workspace refresh, and adapter event-runner tests passed.
- Both deployed router copies are byte-identical and compile under Python.
- New and modified Task 7 modules remain below 500 lines.
- Every injected/generated surface remains orientation-only and cannot update
  kernel state or claim trust.
