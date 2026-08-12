# External evaluation harness

- Contract version: **0.1**
- Status: **optional future external contract; requirements and handoff only**
- Owner: a future project separate from AITP

This document is the single source of truth for the requirements handed to that
future project. References from AITP documents are intentionally short. The
contract does not choose the external repository, path, implementation
language, toolchain, or API/schema format. It is not an AITP runtime component
or a required dependency.

## Eligibility and current v6 status

FROZEN v6 is an anchored, unexecuted preregistration. No future harness output
can retroactively satisfy the original M0.6 scored-run or bootstrap evidence
gaps. Before any external output could be considered as new AITP evidence, AITP
must separately review a protocol revision, record the changed conclusion
strength, issue a new freeze version before any held-out turn is sent, and
update `docs/roadmap.md`, `README.md`, and `docs/m0.6-stage-notes.md`. Until
then, external output is rehearsal/engineering evidence only. This contract
does not itself revise or refreeze FROZEN v6. M1a is now **done; deterministic
gate passed**; see [`docs/m1a-stage-notes.md`](m1a-stage-notes.md).

## 1. Purpose and ownership

The future project will provide controlled execution and assessment around the
AITP conformance suite. It must consume AITP's frozen inputs without turning
the AITP repository into an evaluation platform.

AITP owns:

- the frozen scenarios and scripts;
- portable seeds and event artifacts;
- treatment and control adapter appendixes;
- the semantic policy, rubric, and pre-registered thresholds;
- the AITP CLI, Skills, and canonical runtime used by the treatment condition;
- the FROZEN v6 record and the gate decision based on the resulting evidence.

The separate future project owns:

- orchestration and run lifecycle;
- independent treatment/control isolation;
- model/session launching;
- raw instrumentation and transcript capture;
- execution-order and packet-order randomization;
- condition-neutral packet extraction;
- independent assessment workflow and score aggregation;
- deterministic archive manifests and archive lifecycle.

External repository ownership, location, language, and toolchain are **TBD**.
No decision about them is implied by this contract.

## 2. Hard boundary and non-goals

The AITP repository stores this contract and the frozen suite inputs only. It
must not gain any harness implementation, SDK, service, required dependency,
daemon, hook, model runner, transcript store, or CI workflow.

The future harness:

- never imports the AITP runtime and does not make AITP a prerequisite for
  ordinary use;
- never writes canonical research records except through the declared
  participant adapter;
- keeps evaluation artifacts outside canonical `.aitp` memory;
- keeps sensitive prompt and transcript material local/private by default and
  never commits it to AITP;
- treats the AITP CLI and files as the integration boundary, not an API or SDK;
- makes no claim of causal superiority unless every controlled-run
  requirement in this contract passes.

The harness is not an AITP stage and does not replace the human operator. It
never independently flips a roadmap row; any result is evidence for a separately
reviewed human decision.

## 3. Normative execution requirements

The future project must satisfy all requirements in this section before a run
can be valid.

### 3.1 Immutable run identity

Every batch, run, condition, session, and artifact must have a stable identity
and a deterministic manifest. Before participant turn 1, record at least:

- model, provider/endpoint, model version, and generation settings;
- the exact system-prompt and developer-prompt bytes, with hashes;
- harness, runner, and configuration versions;
- every delivered Skill's bytes or hash and its source revision;
- launcher path and hash;
- interpreter path and version output;
- installed manifest fields and manifest hash;
- AITP checkout/anchor, canonical runtime revision, and runtime-tree hash;
- scenario, seed, policy, adapter, and event-artifact hashes;
- participant identity/configuration and the run's declared budgets.

Missing, mutable, or condition-inconsistent identity data invalidates the run.
The manifest must make it possible to identify exactly what was delivered,
not merely what was intended.

### 3.2 Independent environments

The original/source seed and any canonical research store used to prepare it
are immutable inputs: setup, teardown, and the harness never modify them. Each
condition receives a disposable run-workspace copy. That copy is expected to
change only through declared participant-adapter writes and recorded event
injections; it is not the source seed or canonical store.

Treatment and control must run in independent environments with fresh
workspaces. Isolation must be explicit and testable for both `PATH` and import
resolution:

- treatment can reach only the declared AITP launcher and its declared
  runtime/files;
- control cannot find an AITP executable on `PATH`, import AITP modules, or
  invoke an AITP command indirectly;
- neither condition can read scenarios, seeds, gold, rubric, other runs, or
  the external project's private control data;
- setup and teardown cannot mutate the canonical AITP runtime, original/source
  seed, or canonical research store.

A same-account directory namespace is not sufficient evidence of independent
conditions where the protocol requires separate machines or accounts.

### 3.3 Byte-identical treatment and control inputs

The seed, policy, shared participant configuration, declared budgets, and all
shared scenario material must be byte-identical between conditions. Skill parity
has exactly two allowed choices: identical Skills in both conditions, or
predeclared treatment-only `aitp`/`using-aitp` Skills as part of the treatment
adapter envelope. No arbitrary treatment-only Skill additions are allowed.
Apart from that declared envelope, the condition must differ only through the
participant adapter and its necessary execution envelope. The harness must
hash and compare deployed bytes before turn 1 and record any mismatch as a
failed preflight.

Gold answers, assessor material, and condition mappings must never enter a
participant-readable environment.

### 3.4 Batch order and sealed randomization

The held-out S3 scenario is run and reported first in the batch. S3 must not
be used for prompt, Skill, policy, adapter, or configuration iteration after
the participant configuration is frozen.

The treatment/control execution order must be drawn and sealed before the
paired run begins. After raw transcripts are extracted into condition-neutral
packets, the packet presentation order must be drawn independently and sealed
before assessor presentation; it need not be drawn before participant turn 1.
A different timing requires a protocol revision and a new freeze. The execution
mapping is hidden from participants; the packet mapping is assessor-private
until presentation. No S3 result may drive iteration or selection of later
runs.

### 3.5 Scripted turns, conditionals, sessions, and budgets

The delivered user bytes for every scripted turn must equal the frozen script
bytes exactly. Operator instructions, framing, tool-budget rules, and paths
belong outside the participant's user turn or in the fixed environment.

Conditional turns require a predeclared predicate. The harness must record the
predicate input, outcome, whether the turn was delivered, and the exact bytes
if delivered. A skipped or unmet conditional turn must not silently count as a
successful scripted turn.

Budgets must be declared before the run and counted under one fixed rule in
both conditions. At the first completed reply boundary at or after the
predeclared budget, stop the session, mark it `budget-exceeded`, record the
budget-stop marker, and score the available evidence. Budget excess alone is
not void; invalid/void applies only when enforcement or counts are missing, or
execution improperly continues after the stop.

Session 2 must begin at a fresh boundary: a new conversation and agent
process, a fresh copy of the declared session-1 end state, and no session-1
transcript or hidden runner state. Its prompt and budgets must be present,
frozen before session 1, and condition-consistent; absence, an unfrozen value,
or a condition mismatch fails preflight before session-2 turn 1. The
ledger/workspace is the only intended continuity mechanism.

### 3.6 Authoritative raw instrumentation

The raw per-turn transcript and instrumentation are operator/harness output,
not participant-authored summaries. For every turn, retain at least:

- the exact delivered user bytes;
- the participant's complete reply;
- UTC turn start and end timestamps;
- cumulative tool-call count under the fixed budget rule;
- a first-grounded-proposal marker and its definition;
- session, condition, scenario, and run identifiers.

Raw transcripts remain untouched. Redaction or anonymization happens only in
condition-neutral packet extraction and must be reproducible from the archive
manifest. Missing instrumentation makes the affected run unscorable; it must
not be reconstructed after the fact.

### 3.7 Turn-time event injection

When a scenario declares an event artifact, the harness must inject it only
at the declared turn, after the preceding reply has completed and immediately
before the next user turn. For each injection, retain:

- canonical source path and source hash;
- workspace target path and target hash;
- UTC injection timestamp;
- run, condition, scenario, and turn identifiers;
- the declared expected hash and an equality result.

The artifact must be absent from the seed and workspace before its turn. Early,
missing, duplicated, or divergent injection invalidates the dependent probes
and is recorded as a deviation.

### 3.8 Neutral packet extraction and blind assessment

Packets supplied for scoring must be condition-neutral and must not reveal
condition through paths, model names, prompt text, timestamps, tool patterns,
file names, or archive ordering beyond what the frozen rubric permits. The
operator or harness may hold the condition mapping, but the assessor must not.

Assessment must be independent of run orchestration. It must implement the
frozen metric definitions, including:

- hidden-fact action score;
- typed durable-event recall and precision;
- non-durable rejection;
- resumption checklist;
- cold-start and budget metrics;
- any other metric already fixed by the AITP rubric.

S1/S2 scores are pooled only under predeclared pooling rules and are reported
with the paired-run validity result. S3 is reported separately and first. The
report must not claim statistical significance or causal superiority from the
suite unless a separately approved design establishes that claim; passing the
AITP thresholds is evidence for a human gate review, not a causal theorem.

### 3.9 Deterministic archive and validity decisions

The archive must be reproducible from a manifest containing the batch/run
identity, all input and output hashes, randomization commitments, timestamps,
boundaries, deviations, and validity decisions. It must distinguish at least:

- valid and scorable;
- invalid start or void;
- deviation with partial scoring allowed by the rubric;
- budget-exceeded/script-incomplete, with available evidence scored;
- unscored rehearsal.

Budget excess alone is not invalid or void. Invalid/void applies when budget
enforcement or counts are missing, or execution improperly continues after the
first completed reply boundary at or after the budget. A validity decision must
name the failed requirement, affected turns or probes,
who made the decision, and the evidence locator. The harness must fail closed
before participant turn 1 when identity or isolation is incomplete.

## 4. Minimal external artifact contract

This is a requirements-level artifact contract, not an implementation schema,
wire format, filename mandate, or API commitment. The future project may choose
its own representation if it preserves the required fields and hashes.

A conceptual batch layout is:

```text
batch/
  manifest/
  preflight/
  mappings/       # sealed, assessor-private
  runs/<run-id>/
    transcripts/  # raw, untouched, private by default
    end-state/
    injections/
  packets/        # condition-neutral assessor inputs
  scoring/        # independent score sheets
  reports/
```

### 4.1 Required inputs

Each batch must identify and hash:

- the frozen AITP checkout or anchor;
- the selected scenario and its frozen script/probe material;
- the selected portable seed;
- the treatment adapter and control adapter;
- the byte-identical semantic policy;
- participant identity and configuration, including model/provider,
  system/developer prompts, generation settings, delivered Skills, launcher,
  interpreter, manifest, and declared budgets.

The inputs must be copied into isolated run environments through a recorded
preflight process. Gold and assessor-only material is an input to assessment,
not to either participant environment.

### 4.2 Required outputs

A completed batch must produce, or explicitly mark absent with a reason:

- a preflight report;
- sealed execution and packet mappings;
- raw per-turn transcripts and instrumentation;
- end-state manifests for each session;
- the turn-time injection log;
- condition-neutral packets;
- independent score sheets;
- the separate held-out S3 report;
- the pooled paired S1/S2 report;
- a final validity verdict and deviation/void record.

### 4.3 Required metadata fields

The representation chosen by the future project must carry these fields or
lossless equivalents on the relevant artifacts:

- batch/run/session/condition/scenario identifiers;
- UTC timestamps and declared turn/session boundaries;
- source, target, and deployed-byte hashes;
- model/provider/prompt/generation identity;
- harness/config/adapter/Skill/launcher/interpreter/runtime identity;
- seed/policy/gold-separation and isolation results;
- random draws, sealed mappings, and access restrictions;
- budget values, cumulative counts, stop markers, and overruns;
- turn delivery, conditional-predicate, injection, and instrumentation data;
- packet transformation version and leakage checks;
- assessor identity/independence declaration, score calculations, pooling rule,
  and validity/deviation rationale.

Sensitive bytes may remain in a private store referenced by a hash and access
controlled locator. They must not be copied into AITP or committed to this
repository.

## 5. Acceptance tests for the future project

Before accepting an implementation, the future project must demonstrate tests
that detect and report all of the following. Tests must fail or classify at the
required boundary: preflight failures before participant turn 1,
execution-order checks before pair start, and packet-order checks before
assessor presentation:

- seed or policy drift;
- modification of the original/source seed or canonical research store, and
  disposable-workspace changes not caused by the declared adapter or event
  injection;
- same-account or directory-only isolation when the protocol requires
  separate accounts or machines;
- control reachability of the AITP executable or import tree;
- any missing required identity field, not only an identity mismatch;
- model, prompt, adapter, launcher, interpreter, manifest, runtime, or
  generation-config mismatch;
- arbitrary treatment-only Skill additions or failure to record one of the two
  allowed Skill-parity choices;
- invalid or unanchored AITP checkout;
- an execution-order draw not independently drawn and sealed before the pair,
  or a packet-order draw not independently drawn after extraction and sealed
  before assessor presentation;
- missing or unsealed execution/packet mappings;
- absent, unfrozen, or condition-inconsistent session-2 prompt or budgets;
- early, missing, duplicated, or hash-mismatched event injection;
- session-1 transcript or process-state leakage into session 2;
- budget handling that misses the first completed reply boundary at or after
  budget, lacks enforcement/counts, or improperly continues (budget excess
  alone is not void);
- missing, incomplete, or post-hoc reconstructed instrumentation;
- packet identity or condition leakage;
- missing operator/assessor separation or assessor access to the sealed mapping;
- nondeterministic or incomplete archive manifests;
- invalid-start handling that fails to stop before participant turn 1.

The project must also:

1. run an unscored rehearsal and verify its archive before any held-out
   scenario is used;
2. show that setup and teardown leave the canonical AITP runtime, original/
   source seed, and canonical research store unchanged, while disposable
   workspace changes are limited to declared adapter writes and event
   injections, using before/after hashes or an equivalent auditable check;
3. show that a failed preflight cannot silently become a scored run; and
4. show that packet extraction can be repeated without changing the raw
   transcript or the sealed mappings.

## 6. Integration and stop rules

Invocation is manual. No hook, daemon, background service, scheduled job, or
automatic stage progression is permitted or required.

The external result is optional evidence presented to a human AITP gate review;
it is never the authority that flips a roadmap row. The approved 2026-08-10
review closed M0.6 under the narrowed claim, and the post-review deterministic
M1a gate is now **done; passed**. The original bootstrap and scored-suite
evidence remains **not measured; deferred; not counted**, and no future harness
run can retroactively change that disposition. See
[`docs/m1a-stage-notes.md`](m1a-stage-notes.md) for the M1a evidence.

A run stops before participant turn 1 when identity, byte parity, anchor, or
isolation is incomplete. At the predeclared budget, it stops at the first
completed reply boundary at or after that budget, marks `budget-exceeded`, and
scores available evidence; budget excess alone is not void. Mark invalid/void
only when enforcement or counts are missing, execution improperly continues
after the stop, or another frozen script, session, instrumentation, event, or
blind-packet boundary cannot be honored. The stop record must preserve what
was verified and what remains unavailable; it must not be upgraded to a score
by interpretation.

The motivating evidence for this handoff is the 2026-08-09 AITP no-turn
preflight. It verified the FROZEN v6 inputs and preparation steps, then stopped
before S3 because exact model/provider and prompt identity plus genuinely
separate treatment/control machines or accounts were unavailable. It produced
no scored result and did not change the approved narrowed M0.6 disposition.
See [`docs/m0.6-stage-notes.md`](m0.6-stage-notes.md) for the AITP-side
record.

This contract describes future external work only. It does not implement or
retroactively change the human-executed FROZEN v6 suite rules in
[`docs/m0.6-suite.md`](m0.6-suite.md).
