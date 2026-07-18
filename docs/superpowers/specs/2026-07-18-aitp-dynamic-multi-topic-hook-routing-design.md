# AITP Dynamic Multi-Topic Hook Routing Design

Date: 2026-07-18
Status: approved direction; implementation planning pending written-spec review

## 1. Decision

AITP host hooks must use dynamic multi-topic routing by default. A fixed
`session_id` remains an explicit single-topic optimization, not the production
default and not the basis of M5 acceptance.

The hook is a trigger and bounded transport adapter. It does not own topic
selection, scientific interpretation, canonical recording policy, cross-topic
trust, or claim status. A read-only routing service resolves each host research
turn against the current AITP workspace before any session-specific context or
canonical write is allowed.

This decision replaces the current installation assumption:

```text
project hook -> preconfigured AITP session
```

with:

```text
project hook -> bounded host event -> read-only route decision
             -> selected session, bounded ambiguity, or no match
             -> context and recording policy only after route validation
```

## 2. User Outcome

One AITP-enabled research workspace may contain computational condensed-matter,
LibRPA, QFT, quantum-gravity, literature, software-development, and HPC topics.
The researcher installs one project hook. On each relevant turn AITP should:

1. recognize whether prior research state is needed;
2. find the most relevant existing topic and session without relying on a
   permanently configured session id;
3. expose a small orientation card and explicit expansion handles;
4. preserve multiple plausible topics when the request is ambiguous;
5. represent cross-topic work as a primary topic plus bounded supporting scope;
6. record only durable research moments after routing and recording policy both
   succeed;
7. avoid canonical writes when coverage is stale, malformed, partial, or
   ambiguous.

Generic questions remain outside AITP. Installing the hook must not turn every
conversation or tool call into a research record.

## 3. Existing Capabilities To Reuse

The implementation must compose existing v5 capabilities instead of creating a
second research runtime:

- compact `aitp_v5_codex_autoroute` for semantic research-intent assessment;
- `aitp_v5_codex_enter` and workspace recovery for bounded session recovery;
- `SessionBinding` as the single-topic canonical session anchor;
- `session_focus_sets`, research programs, and cross-topic relations for
  reviewed supporting scope;
- the query index and exact repository reads for candidate discovery and
  verification;
- `host_lifecycle_dispatch` for normalized host events and operation
  allowlists;
- context-injection receipts, Research Moment classification, and existing
  canonical writer boundaries;
- host install/audit/readiness surfaces for configuration and observation.

No new compact MCP tool is required. Compact remains exactly ten tools.

## 4. Architecture

### 4.1 Hook Adapter

The host-specific hook captures only bounded routing inputs that the host can
provide:

- host and host-session identity;
- project root and current working directory;
- repository identity, branch, and changed/visible paths when available;
- prompt or objective summary, not a full conversation transcript;
- explicit topic, session, record, or file references supplied by the user or
  agent;
- native event name, event id, and event time;
- optional explicit single-topic pin.

The adapter normalizes these fields into a host-neutral route request. It does
not scan the research graph, select a topic, build scientific context, or call a
family-specific writer.

### 4.2 Read-Only Route Resolver

One shared resolver consumes the normalized request and returns a bounded route
decision. It must use a coherent query snapshot for candidate discovery, then
exact-read every selected topic, session, focus, and claim anchor.

Candidate evidence is ordered by strength:

1. an explicit session or topic reference in the current request;
2. a validated optional project/subdirectory pin;
3. a still-valid runtime mapping for the same host session and workspace;
4. exact repository, branch, file, code-state, artifact, or record-ref matches;
5. current objective, active route, closeout, claim, and topic text matches;
6. recent workspace focus as a tie-breaker only;
7. research-program or cross-topic discovery as supporting scope, never as an
   implicit primary-session selection.

Recency alone cannot select a topic. Lexical or semantic similarity alone
cannot authorize a canonical write.

### 4.3 Route Decision

The decision has one of these statuses:

- `outside_aitp`: no research-memory entry is needed;
- `selected`: exactly one primary session is safely selected;
- `ambiguous`: multiple plausible primary sessions remain;
- `workspace_recovery`: research memory is relevant but no usable session is
  selected;
- `conflict`: explicit inputs or a pin disagree;
- `coverage_blocked`: index, exact reads, or coverage are stale, malformed,
  truncated, or otherwise insufficient.

Every decision includes:

- selected topic/session refs when status is `selected`;
- at most three candidate cards with component scores and reason codes;
- checked, not-shown, not-checked, malformed, and read-error coverage;
- index generation and canonical watermark;
- the routing-input fingerprint;
- recommended next compact operation;
- `orientation_only=true`;
- `can_update_claim_trust=false`;
- `canonical_write_allowed=false`.

The route decision never creates a topic, binds a session, changes an active
claim, writes a focus set, or promotes memory.

### 4.4 Runtime Host-Session Mapping

After a `selected` decision, AITP may cache a runtime-only mapping from
`(workspace, host, host_session_id)` to the exact selected session. The mapping
contains the route fingerprint, selected refs, index generation, creation time,
last verification time, and optional expiry.

The mapping is a performance and continuity hint, not a truth source. Every use
must exact-read the canonical session and topic again. A changed explicit
request, repository identity, topic reference, or focus invalidates or
supersedes the mapping.

Runtime mappings live below `.aitp/runtime`, use hashed path components, and do
not enter the Research Graph or change the canonical watermark.

### 4.5 Multi-Topic Turns

Canonical `SessionBinding` remains single-topic. Dynamic routing selects one
primary session only when the primary topic is clear.

If a turn genuinely combines topics, the resolver returns:

- one primary selected session when evidence clearly identifies it;
- bounded supporting topic candidates;
- `requires_target_revalidation=true` for cross-topic scientific material;
- a focus-set proposal, not an automatically written focus-set record.

If no primary topic is clear, status is `ambiguous`. A human or explicit agent
choice is required before session-specific context or canonical recording.

Reviewed grounded knowledge and procedural workflows may orient another topic.
Topic-local claims, insights, derivation conclusions, baselines, validation,
and trust never transfer through routing or a focus set.

## 5. Event Behavior

### 5.1 Session Start

Many hosts do not provide a research prompt at process start. Session start may
restore a still-valid runtime route or return workspace orientation only. It
must not guess a topic from recency.

### 5.2 Prompt Or First Relevant Turn

Prompt-submit is the preferred dynamic-routing point. Hosts without that event
use the existing first-relevant-prompt compact facade fallback. Only a
`selected` decision may prepare session-specific context.

### 5.3 Pre-Tool And Post-Tool

Before a route is selected, pre/post-tool hooks may apply generic safety policy
and append bounded runtime trace only. They cannot write a scientific Research
Moment.

After selection, an explicit validated top-level Research Event may enter the
existing Research Moment Controller. Raw tool output, nested payloads, and
ordinary tool noise remain trace-only.

### 5.4 Closeout

Closeout uses the validated runtime host-session mapping or an explicit session
choice. It remains preview-first and cannot infer a primary session from the
last tool call. Ambiguous or missing routes return a closeout-selection request
without canonical writes.

## 6. Installation Contract

Project hook installation defaults to dynamic routing:

```text
install-hooks <host> --routing-mode dynamic --settings <project-config>
```

The topics root and project root are explicit independent inputs. The hook is
installed at the host project root; the canonical AITP store may live elsewhere.

An optional single-topic mode remains available:

```text
install-hooks <host> --routing-mode pinned --session-id <session-id>
```

Pinned mode must be explicit in the generated configuration and audit output.
If the current request explicitly names a different topic/session, pinned mode
returns `conflict` instead of silently routing or writing.

Existing non-AITP host configuration is merged only through the current
reviewed install boundary. Legacy full-memory or keyword-router injection is
reported as a conflict and is never silently retained as an equivalent routing
path.

## 7. Safety And Failure Policy

Dynamic routing fails closed:

- stale, truncated, malformed, or read-error coverage cannot produce
  `selected`;
- equal or near-equal primary candidates produce `ambiguous`;
- a missing exact session/topic read invalidates cached runtime selection;
- generic host events cannot create topics, sessions, claims, or focus sets;
- route scores and model semantic assessment are orientation signals, not
  evidence;
- hook/context/RAG/summary content cannot update claim trust;
- cross-topic routing cannot turn supporting material into target evidence;
- no raw prompt, full conversation, or unbounded tool output is persisted by
  default;
- no hook path may install or update a Skill.

Unsupported hosts continue through compact facade calls. Hook absence degrades
automation, not research correctness.

## 8. Alternatives Considered

### 8.1 Dynamic Default With Optional Pin - Selected

This matches the multi-topic research-memory objective while retaining a useful
single-topic optimization. It reuses current recovery, focus, index, and host
dispatch capabilities and keeps ambiguity visible.

### 8.2 Fixed Session Per Project - Rejected As Default

This is simple and precise for dedicated workspaces but misroutes integrated
multi-topic research and makes repository layout determine scientific context.
It remains an explicit optional mode.

### 8.3 No Hooks, Agent-Only MCP Calls - Rejected As Final Form

This preserves correctness but loses automatic lifecycle reminders, runtime
policy checks, and low-noise research-moment opportunities. It remains the
fallback when a host cannot expose suitable events.

## 9. Verification

Implementation acceptance requires deterministic tests for:

1. two or more topics in one project route to different existing sessions from
   different research prompts;
2. generic textbook prompts remain `outside_aitp`;
3. a mixed-topic request returns a primary-plus-supporting proposal only when
   the primary is clear, otherwise `ambiguous`;
4. ambiguous, stale, malformed, truncated, and missing-ref cases perform zero
   canonical writes;
5. a valid runtime route is reused only after exact session/topic verification;
6. route-changing prompt or repository identity invalidates runtime reuse;
7. pinned mode works for a dedicated project and conflicts with an explicit
   different topic;
8. pre/post-tool events before selection remain runtime trace only;
9. cross-topic candidates carry target-revalidation boundaries and transfer no
   trust;
10. dynamic installer output contains no fixed session id, preserves unrelated
    host config, and audits legacy injection conflicts;
11. compact MCP remains exactly ten tools;
12. routing and lifecycle events leave the canonical watermark unchanged unless
    a separately validated durable Research Moment is explicitly applied.

Real M5 acceptance requires one installed dynamic project hook in a multi-topic
workspace and observed lifecycle evidence showing:

- one prompt selects topic/session A;
- another host session or explicit topic shift selects topic/session B;
- an ambiguous prompt does not write or silently choose;
- context remains bounded and ref-traceable;
- no claim trust, Skill, baseline, or cross-topic evidence authority changes.

Host process availability, generated fixture commands, and a fixed-session hook
smoke do not satisfy this acceptance item.

## 10. Compatibility And Migration

Existing generated fixed-session hook files remain readable and are classified
as `pinned` compatibility installations. They are not production-ready for a
multi-topic project.

Installation audit reports routing mode, pinned session if present, legacy
injection conflicts, project root, topics root, and required migration action.
Migration is preview-first and preserves unrelated host configuration. It does
not automatically remove an existing keyword router or full-memory injection;
those changes require exact reviewed configuration diffs.

No canonical record migration is required for this design. Runtime route caches
are disposable.

## 11. Non-Goals

- building a second general agent runtime;
- creating a universal physics ontology for routing;
- automatically creating topics or sessions from every new question;
- persisting complete prompts, transcripts, or tool output;
- using the most recent topic as an automatic default;
- transferring claim trust across topics;
- changing the ten-tool compact MCP surface;
- making hook installation mandatory for correct manual AITP use.

## 12. Roadmap Consequence

M5 remains open until dynamic multi-topic routing is implemented and observed in
a real installed project hook. The old fixed-session installation smoke is a
compatibility/fixture check only.

M6 may continue its read-only real vertical probes independently, but final
release readiness requires this corrected M5 host-entry contract. The overall
AITP Goal remains unchanged: one minimal, trustworthy theoretical-physics
research operating memory that recovers and records the right topic without
making AITP engineering the purpose of the research conversation.
