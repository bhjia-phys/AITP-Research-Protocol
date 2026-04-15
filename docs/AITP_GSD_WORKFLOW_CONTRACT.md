# AITP x GSD Workflow Contract

Status: active local workflow rule

Scope: how to decide when work should be treated as ordinary GSD repo execution
versus AITP-governed topic execution.

## 1. Why this contract exists

This repository now uses two different but compatible operating layers:

- `AITP`
  - governs research topics, runtime state, trust boundaries, operator
    checkpoints, validation gates, and promotion routes
- `GSD`
  - organizes implementation work on this repository itself: planning,
    execution waves, summaries, and developer-facing phase tracking

They solve different problems.

The failure mode to avoid is letting them collapse into each other:

- if GSD replaces AITP runtime state, research work turns into generic project
  management
- if AITP is forced to own ordinary repo maintenance, implementation work turns
  into an unnecessarily heavy topic ritual

This contract keeps the division explicit.

## 2. The short rule

Use `GSD` when the task is primarily about changing, testing, packaging, or
documenting the AITP codebase.

Use `AITP` when the task is primarily about advancing a research topic, even if
that topic includes code, benchmarks, or method development.

If there is a real research topic in play, `AITP` wins first.

## 3. Use GSD for repo work

Treat the task as `GSD` work when the real objective is one of these:

- implement or refactor AITP runtime code
- add tests, schemas, scripts, or docs for this repository
- improve adapter/bootstrap/install behavior
- harden protocol surfaces, runtime projections, or audits
- create acceptance scripts for the repository
- organize milestone work, phase plans, and execution summaries

Typical examples:

- "Improve source-to-question distillation in `aitp_service.py`."
- "Add a new runtime schema field and update tests."
- "Write the OpenCode installation docs."
- "Create a real-topic acceptance script for a new lane."

Operational rule:

- GSD may track phases, plans, summaries, and implementation decisions
- AITP runtime artifacts are still the source of truth only for research-topic
  state, not for repo-maintenance state

## 4. Use AITP for topic work

Treat the task as `AITP` work when the real objective is one of these:

- continue an active topic
- open a new topic from a paper, thesis, note set, or vague idea
- change novelty direction, scope, or validation route for a topic
- inspect or answer runtime status questions about a topic
- run bounded derivation, benchmark, implementation-validation, or promotion
  work inside a topic

Typical examples:

- "Continue this topic."
- "Read this thesis and find the first honest bounded question."
- "Switch the direction to X but keep numerics out of scope."
- "Run the smallest benchmark-first route for this method."
- "Is this candidate ready for promotion?"

Operational rule:

- enter through `using-aitp`
- materialize or refresh durable topic state first
- follow `runtime_protocol.generated.md`
- keep outputs inside `L0/L1/L3/L4` until the declared gates are satisfied
- keep the topic-owned truth root `topics/<topic_slug>/...` authoritative for
  research state; repo-planning files and helper projections do not replace it

## 5. Code inside a topic still belongs to AITP

Code work does not automatically mean `GSD`.

If the coding task is subordinate to an active research topic, it remains
`AITP` work.

Examples:

- reproducing a benchmark before trusting a new method claim
- validating a code path against a bounded observable
- refining a helper script that is part of a topic's declared validation route
- recording operation trust and strategy memory for a code-backed lane

In those cases:

- the coding step belongs to the topic's runtime state
- benchmarks, operation manifests, trust audits, and strategy memory should be
  written through AITP surfaces
- success is judged by the topic's declared checks, not by generic "code
  completed" status

This is the key boundary:

`code as research evidence` -> use `AITP`

`code as repo maintenance` -> use `GSD`

## 6. Mixed tasks: how to choose

Some requests mix both layers.

Use this priority order:

1. Is there an explicit or implied active research topic?
2. Does the next step need durable topic state, steering, validation, or
   promotion semantics?
3. Or is the next step just a repository implementation change?

Route like this:

- if `1` or `2` is yes -> start in `AITP`
- if only `3` is yes -> use `GSD`

When one task genuinely has both:

- do the topic-governed work in `AITP`
- if the result reveals a repo/product gap, capture that as `GSD` follow-up

Example:

- "The topic needs a better benchmark-first route for code-backed work."
  - topic execution and evidence handling: `AITP`
  - improving the general runtime so future topics do this automatically: `GSD`

## 7. What each layer owns

`AITP` owns:

- topic state
- research contracts
- validation contracts
- idea packets
- operator checkpoints
- steering artifacts
- strategy memory
- operation trust
- promotion readiness
- topic completion

Topic rule:

- the topic-owned truth root is `topics/<topic_slug>/...`
- when a human needs to read, review, steer, or resume, Markdown surfaces in
  that root stay authoritative
- JSON and JSONL remain machine-facing companions for handlers, ledgers,
  compatibility payloads, and replayable state

`GSD` owns:

- project and phase planning for this repository
- implementation task breakdown
- execution sequencing
- change summaries for repo-development phases
- milestone tracking for protocol/runtime product work

`GSD` does not replace:

- `topics/<topic_slug>/runtime/**`
- `topics/<topic_slug>/L3/**`
- `topics/<topic_slug>/L4/**`
- any other AITP research-state artifact

## 8. Recommended everyday usage

For repo development in this repository:

- use GSD to plan and execute feature work
- treat `.planning/` as implementation-tracking state
- keep protocol/runtime docs authoritative

For real research work:

- start with natural language through the adapter gatekeeper
- let `using-aitp` decide whether the request becomes topic state
- once AITP claims it, follow runtime surfaces rather than repo-planning files

For code-backed research:

- keep the benchmark-first or validation-first route inside AITP
- only move to generic repo work when the objective becomes "improve AITP
  itself"

## 9. Non-goals

This contract does not:

- make GSD the scientific source of truth
- force every coding task through AITP
- force every AITP topic change through GSD
- collapse research execution into generic milestone software

It exists only to make the handoff explicit.

## 10. One-line memory

`AITP governs research topics. GSD governs implementation of AITP itself.`
