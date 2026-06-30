# AITP Codex App 1.0 Plan

Status: target architecture and implementation plan for AITP 1.0.0.
Implementation generation remains v5. This document specializes AITP for the
Codex App plugin path and does not require changing the typed graph kernel.

## Goal

AITP 1.0 should let Codex do real theoretical-physics work without losing the
research record and without filling every conversation with the whole graph.
The agent should be able to:

1. enter a new or existing research conversation with a compact, truthful view;
2. recognize the current research process and choose the right action family;
3. expand graph context only when the next scientific step needs it;
4. record durable sources, claims, evidence, validation, artifacts, route
   decisions, and handoffs at natural moments;
5. write notes or paper sections in a stable physics-note style while citing
   references and registering those references back into AITP.

The product version becomes 1.0.0. The active implementation generation,
schemas, tool prefix, and repository layout remain v5.

## Non-goals

- Do not record every chat turn.
- Do not make hooks trusted scientific evidence.
- Do not promote paper summaries, web pages, RAG chunks, or note prose into
  claim support without typed evidence or validation links.
- Do not expose the full kernel write surface as the first thing the agent sees.
- Do not require every exploratory thought to become a typed record.
- Do not make Codex App behavior depend on Claude Code, Kimi Code, or OpenCode
  lifecycle guarantees.

## Current Substrate

The current repository already has the right lower layers:

- typed graph records under `<topics-root>/.aitp/registry`;
- v5 MCP entrypoint at `brain/v5/native_mcp.py`;
- execution briefs, relation maps, process graph slices, recording navigator,
  context packs, active-claim focus, quiet checkpoints, objective graph,
  note-outline support, literature intake, curated RAG, source assets, and trust
  preflights;
- Codex plugin setup mode with `aitp_config_status`, `aitp_suggest_config`, and
  `aitp_configure`;
- project-local Codex hooks for prompt routing and direct-write guards;
- optional generated v5 adapter hooks for pre-tool and post-tool lifecycle
  traces.

The 1.0 work is mostly a surface and orchestration problem: define what Codex
sees first, when it expands, and when it writes.

## Layered Architecture

### Layer 1: Typed Research Graph

This is the source of truth. It stores topics, sessions, claims, source assets,
reference locations, artifacts, tool recipes, tool runs, evidence, validation,
physics objects, object relations, proof obligations, research runs, route
events, quiet checkpoints, human checkpoints, trust updates, promotion packets,
and memory entries.

Rules:

- source identity is not evidence;
- citation location is not evidence;
- tool execution is not validation;
- summary is not truth;
- hooks are runtime metadata;
- trust changes require typed support plus the proper preflight or checkpoint.

### Layer 2: Agent Context Surfaces

This layer is what Codex should read before acting. It is derived from the graph
and stays orientation-only unless the payload explicitly points back to typed
records.

Recommended surfaces:

- context pack: compact session/topic/claim entry view;
- active-claim focus: what claim is live, what is known, what cannot be said;
- execution brief: deeper current-state view;
- claim relation map: support, challenge, validation, blockers, and next valid
  actions;
- process graph slice: deeper chronology only when required;
- objective graph: research objective and sub-objective routing;
- recording navigation state: where a durable moment should be recorded;
- note outline: note/paper section skeleton backed by typed records;
- curated RAG and literature drafts: reading-oriented context that cannot update
  trust by itself.

The default Codex startup payload should use the smallest view that can answer
"where am I and what is safe to do next?".

### Layer 3: Research Process Controller

Codex should classify the conversation before choosing graph operations.

Process modes:

| Mode | Default reads | Default writes |
|---|---|---|
| Setup/config | setup status and path suggestions | configuration only |
| New topic exploration | none, then optional topic creation after user accepts a durable objective | topic/session/claim only after commitment |
| Existing topic continuation | context pack, active-claim focus, relation map if needed | durable moments only |
| Literature discussion | source lookup/intake surfaces, local notes, reference locations | source asset, reference location, paper-note artifact, evidence only after a claim link is explicit |
| Derivation/theory work | focus, relation map, object/relation context | equations, assumptions, proof obligations, route events, evidence after checked support |
| Numerical/code work | focus, tool/code context, validation contracts | code state, recipe, run, artifact, validation result, evidence |
| Synthesis/note/paper writing | note outline, relation map, source reconstruction, trust audit | artifacts and source registrations; trust only through gates |
| Closeout/handoff | compact status, recording classifier, quiet checkpoint | session summary, research run event, checkpoint or handoff record |

The controller should prefer read-only recovery when the mode is ambiguous.

### Layer 4: Codex Plugin Surface

The plugin should be the main Codex App entrypoint. It should provide skills and
a small MCP front door first, then reveal deeper tools progressively.

Recommended plugin skills:

- `configure-aitp`: first-run setup and moved-path repair;
- `using-aitp`: lightweight entry, intent classification, and topic/session
  recovery;
- `aitp-runtime`: durable recording, trust gates, validation, and full graph
  operations;
- future `aitp-writing`: note/paper style, JHEP-like section discipline,
  citations, and source registration;
- future `aitp-literature`: paper reading, comparison, source stack, and
  reference-location discipline.

The current skills can absorb the writing and literature rules first. Separate
skills are useful only when the text becomes too heavy for startup context.

## Progressive MCP Exposure

The full `aitp_v5_*` surface should remain available for kernel development and
fallback use, but Codex App should not need to see it all at first.

Recommended profiles:

### Profile A: setup

Exposed when paths are missing:

- `aitp_config_status`
- `aitp_suggest_config`
- `aitp_configure`

No graph reads or writes are exposed until setup succeeds.

### Profile B: entry

Default after setup:

- enter/recover topic;
- get context pack;
- get active-claim focus;
- build workspace recovery or recording audit;
- classify request/process mode;
- list recommended expansions.

This answers "what topic/session/claim am I in?" and "what should I read next?"
without exposing the deep write catalog.

### Profile C: read expansion

Exposed by explicit expansion:

- execution brief;
- claim relation map;
- process graph slice;
- objective graph;
- source reconstruction audit;
- trust audit;
- literature comparison/read drafts;
- curated RAG read/search/chunk reads.

This is where Codex learns enough to answer or plan.

### Profile D: guided recording

Exposed only after a candidate durable moment exists:

- classify recording candidate;
- read recording navigation state;
- expand exactly one recording slot;
- lookup required refs;
- call the named typed write/preflight;
- verify recording effect.

The write tool itself is not chosen by prose guessing. It is selected by the
slot expansion.

### Profile E: trust and promotion

Exposed only after explicit request or final-synthesis need:

- pre-tool policy;
- trust preflight;
- human checkpoint request/decision;
- promotion packet creation/application.

Applying trust remains gated. The plugin should never make trust application a
default first-level action.

Implementation option: keep `brain/v5/native_mcp.py` as the full kernel MCP
server and add a Codex-facing facade server or tool catalog layer. The facade
can call the same v5 functions internally while presenting fewer tools to
Codex. A temporary environment flag such as `AITP_MCP_SURFACE=full` can keep
the old full surface available for developers and tests.

## Context Weight Budget

AITP should not push the whole graph into every prompt.

Default entry payload should include:

- topic id, session id, active claim id;
- claim statement, confidence state, active uncertainty;
- strongest blockers and forbidden conclusions;
- next valid actions;
- source/evidence/validation counts with refs, not full text;
- recent durable events, capped;
- expansion menu with reasons.

Deep payloads should be lazy:

- relation map only when support/challenge/validation matters;
- process graph only when chronology matters;
- source stack only when writing, citation, or reconstruction matters;
- trust audit only when confidence, memory, or promotion is requested;
- literature text only when the user is reading or writing about a paper.

The agent should keep stable refs in context and fetch details by ref lookup
instead of copying full notes repeatedly.

## Recording Policy

AITP should record durable scientific changes, not agent thinking.

Always consider recording:

- new accepted research objective, route, or subquestion;
- source asset or exact reference location that may be reused;
- note, figure, table, log, raw dump, code patch, or report artifact;
- equation, definition, assumption, physics object, or object relation;
- tool recipe, code state, tool run, or validation result;
- result, anomaly, contradiction, negative result, or failed check;
- proof obligation, validation gap, or missing provenance;
- route pivot, abandoned route, blocked attempt, or split;
- human checkpoint, quiet checkpoint, trust preflight, or handoff.

Usually do not record:

- generic explanations;
- unaccepted brainstorming;
- repeated summaries;
- file scans with no scientific state change;
- setup noise unless it affects reproducibility;
- hooks firing without a durable research event.

The default sequence is:

```text
candidate durable moment
  -> classify
  -> read recording navigation state
  -> expand one slot
  -> perform the named typed write/preflight
  -> verify effect
```

This keeps recording from blocking normal research. The classifier can return
`ignore`, `defer`, `navigate`, or `write-ready`; only the last two lead toward a
record.

## Literature And Web Reference Registration

When Codex writes notes or paper sections, it may search the web for references
when current bibliographic data, paper versions, or external sources are needed.
Any reference used in a durable note or claim discussion should be registered in
AITP at the right layer.

Reference layers:

| Layer | Meaning | Typical record |
|---|---|---|
| Source identity | A paper, book, dataset, repository, web page, or local note exists | source_asset |
| Source location | Exact section, page, theorem, equation, figure, table, URL fragment, timestamp, or local path | reference_location |
| Reading artifact | Agent or human note about what was read | artifact or sensemaking report |
| Claim link | A statement in the source supports, challenges, bounds, or motivates an AITP claim | evidence |
| Physical content | Definitions, assumptions, equations, objects, regimes, or relations extracted from the source | physics_object, object_relation, proof_obligation |
| Validation basis | The source defines a check, benchmark, or failure mode used for validation | validation_contract or validation_result link |
| Trust basis | The source participates in confidence or memory promotion | trust preflight, checkpoint, promotion packet |

Do not jump from source identity directly to evidence. Evidence requires an
explicit claim link, status, summary, and typed refs.

For literature discussions:

1. read existing AITP/local-note context first when a topic is known;
2. register or reuse source identity;
3. register exact reference locations for quoted or relied-on passages;
4. record a reading artifact if the discussion produced reusable notes;
5. create evidence only when the source is tied to an AITP claim;
6. keep open interpretive gaps as proof obligations or route questions.

For paper/note writing:

1. build a note outline from typed records and the desired style;
2. fetch only needed source details;
3. write with clear claim/evidence/assumption separation;
4. register any newly used references;
5. record the produced note/paper draft as an artifact;
6. run source reconstruction/trust audits before writing final-sounding claims.

## Note And Paper Style

AITP writing should be substantive physics writing, not a protocol dump.

Default style:

- concise abstract or problem statement;
- setup and notation before conclusions;
- definitions, assumptions, and regimes stated explicitly;
- derivations written algebra-first when relevant;
- claims separated from evidence and open gaps;
- citations placed where they support a specific statement;
- "proved", "checked", "finite-evidence", "conditional", and "open" boundaries
  made explicit;
- final section lists remaining gaps and next checks.

The JHEP-like skill style should be treated as an output template. It should not
override AITP trust rules. The note may cite external literature, but the AITP
graph must still record which source supports which conclusion.

## Hooks In Codex App

Codex hooks should cooperate with AITP but not replace MCP/skill logic.

Recommended roles:

- `UserPromptSubmit`: detect research/topic/literature/writing cues and attach
  a compact reminder to enter AITP through the plugin skill;
- `PreToolUse`: block direct file writes into `.aitp` state and evaluate risky
  research actions when a generated session bridge is installed;
- `PostToolUse`: optionally capture tool trace metadata for sessions with an
  explicit v5 bridge;
- stop/session-end equivalent: not assumed available in Codex App today; use a
  skill-driven closeout command instead.

Start behavior:

1. plugin setup mode checks paths;
2. `using-aitp` reads compact context for known research requests;
3. if no session exists, the agent asks whether to create a topic/session only
   when the conversation has a durable objective.

End behavior:

1. classify whether a durable handoff exists;
2. write quiet checkpoint or session summary only when useful;
3. list open gaps, next valid actions, and refs to revisit;
4. do not force a record for a casual conversation.

Because Codex App lifecycle events can vary, the skill must be the reliable
control plane. Hooks are helpers.

## New Session And Topic Entry

New Codex thread:

1. If the user asks generic non-research questions, do not enter AITP.
2. If the user names AITP, a known topic, a prior research result, a paper in a
   project, or asks to continue physics work, load `using-aitp`.
3. Read setup status if the plugin is in setup mode.
4. Read compact workspace/topic recovery if the topic is unclear.
5. Read context pack or active-claim focus for the selected session.
6. Expand relation map only if the answer depends on support, challenge,
   validation, blockers, or trust.

Mid-conversation topic entry:

1. detect that the discussion has become a durable research process;
2. state the candidate topic/objective in one sentence;
3. ask before creating a new topic/session when no matching topic exists;
4. if matching topic exists, recover read-only first;
5. record new route/objective only after the user accepts it or the work creates
   a concrete artifact/source/result.

Literature-only entry:

1. treat the paper as source context, not a claim by default;
2. register source identity/location if it will be reused;
3. record reading notes/artifacts if they are substantive;
4. create claim/evidence only when the discussion ties the paper to a project
   claim or physical conclusion.

## Implementation Phases

### Phase 1: Documentation and version contract

- Set active product version to 1.0.0 while keeping implementation generation v5.
- Add this Codex App 1.0 plan.
- Update README and plugin README to describe compact/progressive Codex usage.
- Update tests that enforce the package/protocol/server version contract.

### Phase 2: Codex-facing facade

- Add an entry/read facade over existing v5 functions.
- Keep full kernel MCP available for development and compatibility.
- Add tests that the default Codex profile exposes only setup/entry/read tools.
- Add an explicit expansion path from entry profile to read expansion and guided
  recording.

### Phase 3: Skill routing

- Update `using-aitp` to classify process mode and use compact context first.
- Update `aitp-runtime` to use the recording navigator for durable moments.
- Add writing/literature subsections or separate skills once startup context
  becomes too heavy.
- Add examples for new topic entry, existing topic continuation, literature
  discussion, note writing, and closeout.

### Phase 4: Hooks integration

- Keep lightweight project hooks as default.
- Add optional session-bound bridge installation for pre-tool/post-tool events.
- Add hook audit checks specific to Codex App.
- Do not depend on unavailable stop/session-end hooks; provide explicit closeout
  skill flow instead.

### Phase 5: Writing and citation workflow

- Make note-outline and source-registration flows easy to call from skills.
- Add a citation registration checklist for web/literature references.
- Add tests that source identity, reference location, evidence, validation, and
  trust records remain separate.
- Add sample note and paper-section outputs grounded in typed refs.

## Acceptance Criteria

AITP 1.0 Codex App integration is acceptable when:

- a new Codex thread can configure AITP or recover a known topic without seeing
  the full kernel tool catalog;
- a continuing topic loads compact context first and expands only on demand;
- a literature discussion can register sources and notes without falsely
  creating evidence;
- a note/paper section can cite external references and record them in the
  correct AITP layers;
- durable research moments are recorded through the navigator and verified;
- hooks can remind, guard, and trace, but cannot update trust;
- final synthesis runs relation-map/source/trust checks before strong claims;
- package, protocol metadata, v5 kernel version, and MCP server info all report
  1.0.0.
