---
title: AITP 2.0 Command And Skill Research Protocol
date: 2026-07-20
status: draft-for-user-review
supersedes:
  - docs/superpowers/specs/2026-07-19-aitp-2-0-rewrite-design.md
scope: AITP 2.0 product boundary, command-guided research lifecycle, local file layout, scientific dreaming, Skill distillation, writing, provenance, and release sequence
---

# AITP 2.0 Command And Skill Research Protocol

> This specification replaces
> `2026-07-19-aitp-2-0-rewrite-design.md`. The earlier document remains only as
> design history and must not drive implementation.

## 1. Executive Decision

AITP 2.0 is a local research-memory protocol operated through commands and
Markdown guides. Its complete required architecture is:

1. one host-discovered `using-aitp` Skill;
2. one thin `aitp` CLI;
3. one bundled command-local `SKILL.md` and small template set for each command;
4. one local, human-readable research store;
5. Git history plus visible audit and review before sensitive writes.

Codex, Kimi, or another host performs the physics reasoning, browsing, coding,
shell work, HPC operation, and document authoring. AITP tells the host what
research memory to read, where work belongs, what must be recorded, what is
missing, and how to finish the current research phase without hiding the work.

AITP 2.0 does not need MCP, required hooks, a graph database, a general context
compiler, an Agent runtime, or a second orchestration system. Reading a selected
Markdown file or command result already places that material in the Agent's
context. The protocol therefore focuses on selecting the right files and making
the resulting writes complete and reviewable.

## 2. Product Outcome

The intended user experience is:

```text
first relevant research turn
    -> using-aitp selects `aitp enter`
    -> enter identifies one topic and returns a small orientation
    -> the Agent invokes the command for the current research phase
    -> that command returns its guide, exact input files, target workspace,
       required records, completeness checks, and finish command
    -> the Agent conducts the real research with normal host tools
    -> the command audits visible files and stages durable records
    -> required human review sees exact bytes and links
    -> approved files enter the local research store
    -> later commands compile those records into Knowledge Cards, Workflows,
       Skills, notes, derivations, reports, or articles
```

The primary product is the local research record. Knowledge Cards, Workflows,
Skills, and writing are compiled products of that record, not alternative truth
stores.

## 3. Minimal System Boundary

### 3.1 `using-aitp`

`using-aitp` is the only host-level Skill required by AITP. It contains a short
router rather than the complete research protocol.

It must:

- trigger on durable theoretical-physics research, prior-result questions,
  literature study, derivations, scientific code changes, meaningful numerical
  or HPC work, and research writing;
- run `aitp enter --cwd <cwd>` on the first relevant turn;
- ask the human when more than one topic is plausible;
- select a phase command from its documented trigger table;
- run `aitp checkpoint` at durable moments and `aitp closeout` near the end of a
  meaningful research session;
- report a missed entry and recover by entering late rather than fabricating
  prior memory;
- never infer human approval, scientific validation, a canonical commit, or a
  Skill installation.

Without required host hooks, this is protocol-level mandatory behavior rather
than a technical guarantee that every host will trigger perfectly. A late entry
must remain recoverable and visible.

### 3.2 Thin CLI

The CLI performs deterministic operational work:

- locate the research store and current topic;
- resolve exact local refs and paths;
- run scoped `rg` searches and report coverage;
- render the selected command guide;
- create a command workspace from templates;
- validate required fields, refs, paths, hashes, and declared gaps;
- display exact staged files and diffs;
- request human review where required;
- serialize canonical writes through Git and read them back;
- report recovery state after interruption.

The CLI does not generate physical insight, choose the scientifically correct
route, summarize hidden conversation state, operate HPC jobs, browse the web,
or author a Skill body on its own. Those remain visible Agent activities guided
by command Markdown.

### 3.3 Command Skills

Each command owns a packaged, versioned Skill:

```text
aitp/command_skills/<command>/SKILL.md
aitp/command_skills/<command>/templates/
aitp/command_skills/<command>/profile.yaml
```

The command-local `SKILL.md` uses the same readable instructional style as a
host Skill, but it is not registered globally with the host. The CLI renders it
only when the command is used, keeping normal startup context small. A rendered
copy may be named `GUIDE.md` inside a working directory so the Agent can edit
the work without modifying the packaged Skill.

Every command Skill has the same sections:

```text
Purpose
Use When
Do Not Use When
Read First
Research Procedure
Files To Produce Or Update
Canonical Effects
Human Decisions
Completeness Checks
Finish And Next Commands
```

`profile.yaml` contains only deterministic requirements that the CLI can check.
Scientific judgment remains in the visible guide, Agent work, and human review.

### 3.4 Local Research Store

Canonical memory is Markdown with small YAML frontmatter plus exact local or
portable locators to PDFs, repositories, commits, scripts, run outputs, and
remote systems. Git is the byte history. Binary and external artifacts are not
duplicated merely to create records.

Derived indexes may accelerate search, but deleting them must not remove
research information or prevent direct `rg` and path-based reads.

## 4. Public Commands

AITP 2.0 has the following normal command groups.

| Command | Research role |
| --- | --- |
| `aitp enter` | Resolve a topic and read its minimum orientation. |
| `aitp search` | Find records, sources, files, code, and cross-topic material. |
| `aitp show` | Read one exact ref or path, optionally at a Git revision. |
| `aitp research` | Prepare and finish a discussion, derivation, deep-research, code, numerical, or HPC phase. |
| `aitp literature` | Add, extract, study, link, and audit one-copy literature. |
| `aitp checkpoint` | Record one durable research event. |
| `aitp closeout` | Check the declared session work for durable omissions and next actions. |
| `aitp knowledge` | Perform Scientific Dreaming and produce or refresh Knowledge Cards and linked insight records. |
| `aitp skill` | Distill, package, review, install, update, or roll back a reusable research Skill. |
| `aitp write` | Prepare a note, derivation, report, article, or presentation from research memory. |
| `aitp audit` | Run deterministic checks on a workspace, record set, or store. |
| `aitp admin` | Doctor, initialize, migrate, back up, recover, and inspect configuration. |

The CLI may implement subcommands, but it must not expose a generic `run`, Agent
dispatcher, scheduler, or hidden automation loop.

### 4.1 Standard Command Output

Every phase command returns readable Markdown and optional JSON with the same
spine:

```text
Command purpose
Selected store and topic
Command Skill version
Exact files read
Coverage and material not shown
Workspace created or selected
Allowed write paths
Required outputs and declared gaps
Human decisions required
Finish command
Likely next commands
```

Because this output is part of the Agent conversation, it is the normal context
injection mechanism. There is no separate required context-pack subsystem.

### 4.2 Agent Command Selection

`using-aitp` and the host Agent select commands from the visible research
intent, not from a hidden CLI classifier:

| Current intent | Command |
| --- | --- |
| Resume or orient | `aitp enter` |
| Find prior work | `aitp search`, then `aitp show` |
| Discuss, derive, investigate, code, calculate, or operate HPC | `aitp research` |
| Acquire or study a paper | `aitp literature` |
| Preserve a durable event | `aitp checkpoint` |
| End or hand off a meaningful session | `aitp closeout` |
| Combine physical insights across records | `aitp knowledge dream` |
| Extract repeatable procedure | `aitp skill distill` |
| Produce a research document | `aitp write` |

Commands may report likely next commands based on deterministic conditions such
as an unfinished workspace, a new durable Episode, or a changed source ref. The
host Agent decides whether the scientific meaning warrants that command. A CLI
condition never performs Scientific Dreaming or Skill distillation itself.

## 5. Fixed File Layout

The active store remains named `.aitp` and contains many topics.

```text
.aitp/
  STORE.md

  topics/
    <topic-id>/
      TOPIC.md
      entities/
      routes/
      statements/
      episodes/
      assessments/
      relations/

      sources/
        notes/

      knowledge/
        cards/

      reuse/
        workflows/
        skill-candidates/
        scripts/

      code/
        revisions/
        mappings/

      runs/

      writing/
        notes/
        derivations/
        reports/
        articles/
        presentations/

  shared/
    library/
      papers/
        <source-id>/
          source.pdf
          SOURCE.md
          extractions/
            <extraction-id>/
              text.md
              anchors.jsonl

    knowledge/
      cards/

    workflows/
    scripts/

  runtime/
    workspaces/
      <command>/<workspace-id>/
    staging/
    indexes/
    recovery/
    local.toml
```

Rules:

- `topics/` and `shared/` are canonical and reviewable.
- `runtime/` is noncanonical working state and may be rebuilt or cleaned only by
  explicit administrative action.
- a paper has one physical copy under `shared/library/papers/`; topics link to
  it rather than copying it;
- topic-local Knowledge Cards and Workflows stay local until explicit reviewed
  promotion to `shared/`;
- temporary scripts remain in the command workspace; useful topic scripts move
  to `reuse/scripts/`; genuinely cross-topic scripts require reviewed promotion
  to `shared/scripts/`;
- source repositories, large datasets, HPC output trees, and credentials remain
  in their real locations and are referenced through exact locators;
- secrets never enter `.aitp`.

`TOPIC.md` records stable background, goals, related topics, workspace roles,
Must Read refs, conventions, and durable constraints. Active routes, recent
events, and changing next actions remain in their own files and are selected by
`aitp enter`.

## 6. Simple Record Contract

All canonical Markdown records use a small common header:

```yaml
schema: aitp/2.0
id: <stable-id>
type: topic | entity | route | statement | episode | assessment | relation | asset
kind: <type-specific-kind>
topic: <topic-id> | _shared
title: <human-readable title>
created_at: <timestamp>
created_by: <human-or-agent identity>
```

Only `kind`-specific fields needed by a real command profile are added. A file
must remain useful when read directly without the CLI.

Canonical refs are store-relative paths, optionally pinned to a Git commit:

```text
topics/<topic-id>/statements/<id>.md
topics/<topic-id>/knowledge/cards/<id>.md
shared/knowledge/cards/<id>.md
topics/<topic-id>/statements/<id>.md@<git-commit>
```

Store-relative paths are transparent to Codex, Kimi, humans, `rg`, Git, and the
CLI. Canonical files do not move after publication. Promotion to `shared/`
creates a new reviewed file linked to its source rather than relocating it.

Relations are small Markdown files with:

```yaml
from_ref: <exact store-relative ref>
predicate: about | related_to | depends_on | conflicts_with | parallelizable_with | derived_from | supports | contradicts | produced | uses | implements | validated_by | failed_because | supersedes | applies_to | installed_as
to_ref: <exact store-relative ref>
basis_refs: []
scope: <where this relation applies>
```

A Relation describes a link. It never validates a scientific Statement by
itself.

## 7. Reading Is Context

### 7.1 Enter

`aitp enter --cwd <cwd>` performs only bounded orientation:

1. find the store and mapped workspace;
2. resolve zero, one, or several candidate topics;
3. ask the human if routing is ambiguous;
4. read `TOPIC.md`;
5. list active routes in explicit human priority order;
6. show each route's next action, boundary, and stop condition;
7. show required Must Read refs and unfinished command workspaces;
8. list recent durable Episodes without expanding all of them;
9. provide exact `show` and `search` commands for omitted material.

The response has a fixed character budget and reports what was not shown. It
does not recursively generate briefs, summaries, relation maps, or other
context products.

### 7.2 Search And Show

`aitp search` uses scoped `rg` as the baseline. Default scope is the current
topic. Shared, cross-topic, legacy, source extraction, code workspace, and
remote scopes require explicit flags.

Every result reports path, line, matched field or body, scope, and whether the
search was complete, partial, stale, or not run for optional scopes.

`aitp show` reads an exact path and may include directly linked Relations. It
does not scan the entire store when a path is already known.

Optional semantic retrieval may later return candidate paths for literature or
Knowledge Cards. The Agent must still read the exact file and source refs.
Retrieval scores, chunks, summaries, and embeddings are never evidence.

## 8. Research Phase Commands

`aitp research begin --mode <mode>` supports:

```text
discussion
derivation
deep-research
code
numerical
hpc
```

It creates:

```text
runtime/workspaces/research/<workspace-id>/
  GUIDE.md
  CONTEXT.md
  QUESTION.md
  NOTES.md
  SOURCES.md
  RESULTS.md
  GAPS.md
  RECORD_PLAN.md
```

The mode-specific guide identifies which existing files to read and which
external tools are appropriate. The Agent performs the research and writes the
workspace files directly.

`aitp research finish <workspace-id>` does not decide whether the physics is
correct. It checks whether the declared result, assumptions, failures, sources,
code/run provenance, and next actions are sufficiently explicit to prepare a
checkpoint. It reports missing information rather than inventing it.

## 9. Checkpoint And Closeout

A checkpoint is appropriate after a durable result, useful failure, decision,
source acquisition, derivation boundary, code change, meaningful run, route
transition, reusable procedure, or new physical insight.

It is not appropriate after every command or transient thought.

`aitp checkpoint` prepares the smallest set of records that preserves the
event. The Agent sees and edits the Markdown before finish. Low-authority
Episodes, questions, hypotheses, failed routes, provenance, and declared gaps
may be committed after deterministic audit. Trust promotion and the products
listed in Section 13 require human review.

`aitp closeout` examines only declared session workspaces, mapped Git changes,
staging, route files, and the Agent's explicit summary. It checks for omitted
durable work and route-specific next actions. It cannot infer facts from an
unavailable hidden transcript, and it writes no empty Episode when nothing
durable occurred.

## 10. Scientific Dreaming And Knowledge

`aitp knowledge` is a first-class research-compilation lane parallel to
`aitp skill`. Its purpose is to reorganize accumulated physical insight into
source-grounded, reusable scientific understanding.

The public lifecycle is:

```text
aitp knowledge dream
aitp knowledge refresh <card-ref>
aitp knowledge link <card-ref>
aitp knowledge finish <workspace-id>
```

### 10.1 Dream

`aitp knowledge dream` selects an explicit topic, routes, time range, refs, or
question and creates:

```text
runtime/workspaces/knowledge/<workspace-id>/
  GUIDE.md
  INPUTS.md
  INSIGHTS.md
  CONFLICTS.md
  OPEN_GAPS.md
  CARD.md
  RECORD_CHANGES.md
  AUDIT.md
```

The guide instructs the Agent to:

- reread selected Statements, Episodes, derivations, source anchors,
  Assessments, failed routes, conventions, and related Knowledge Cards;
- separate author-reported claims, established AITP Statements, Agent
  synthesis, hypotheses, and open gaps;
- identify compatible, conflicting, or scope-dependent insights;
- create new Statement drafts when a new scientific assertion would otherwise
  exist only inside the card;
- propose Relations from the new card and Statements to their exact origins;
- propose route questions or next actions exposed by the synthesis;
- declare applicability, conventions, unresolved conflict, and missing source
  support.

The CLI selects and checks files. The Agent performs the dreaming.

`aitp closeout` may suggest `aitp knowledge dream` when the declared session
contains several linked insights, a resolved conceptual conflict, or a reusable
derivation boundary. This is a visible next-command suggestion, not automatic
card generation.

### 10.2 Knowledge Card

A Knowledge Card is a reviewed, compact synthesis for one narrow concept,
question, derivation, convention, or source comparison. It is not a raw note,
an atomic scientific claim, a workflow, a Skill, or primary evidence.

Required frontmatter is:

```yaml
type: asset
kind: knowledge_card
card_form: concept | derivation | comparison | convention
question: <one bounded question>
summary: <compact context-ready answer>
scope: <theories, approximations, conventions, and regimes>
use_when: []
do_not_use_when: []
```

Required body sections are:

```text
Compact Answer
Prerequisites And Conventions
Grounded Synthesis
Derivation Or Comparison
Applicability Boundaries
Conflicts And Alternatives
Open Gaps
Source Map
```

Every substantive assertion in a card is marked as one of:

- `source_reported`, with an exact source and anchor;
- `aitp_statement`, with an exact Statement ref and its derived assessment
  state;
- `new_synthesis`, with a separately staged insight, hypothesis, claim, or open
  gap Statement.

Approving a card means that its synthesis, sourcing, labels, and boundaries are
acceptable research memory. Approval does not validate every contained
Statement or convert source-reported content into an AITP conclusion.

### 10.3 Linking And Refresh

Finishing a dream may create:

- one Knowledge Card;
- new insight, hypothesis, decision, or open-gap Statements;
- Relations linking the card to exact Episodes, sources, Statements,
  Assessments, entities, routes, code, or runs;
- explicit route follow-ups.

Historical Episodes are not rewritten to insert retrospective understanding.
New Relations connect them to the card.

`knowledge link` prepares only explicit Relations between an existing card and
selected topic records. It does not edit the card, revise an Episode, or change
scientific trust. Cross-topic and shared links require the target scope to be
shown and reviewed.

Published Knowledge Cards are immutable. `knowledge refresh` creates a new card
and a `supersedes` Relation after review. The old card remains resolvable.

Card health is derived as:

```text
current
stale
contested
broken
```

Newer superseding Statements or sources make a card stale; applicable
contradictory assessments make it contested; missing refs or failed source
anchors make it broken. Non-current cards remain searchable but are never
injected without a warning.

`aitp enter` includes a Knowledge Card summary only when an active route or
Topic Must Read ref names it. Search and optional semantic retrieval may suggest
other cards, but the Agent must explicitly expand them.

## 11. Workflow And Skill Compilation

`aitp skill` compiles procedural reuse from research records. It is parallel to
Scientific Dreaming:

```text
scientific meaning     -> aitp knowledge -> Knowledge Card
repeatable procedure   -> aitp skill     -> Workflow and installed Skill
```

The public lifecycle is:

```text
aitp skill distill
aitp skill package <candidate-ref>
aitp skill install <package-ref>
aitp skill update <installed-skill>
aitp skill rollback <install-ref>
```

`distill` creates:

```text
runtime/workspaces/skill/<workspace-id>/
  GUIDE.md
  INPUT_EPISODES.md
  WORKFLOW.md
  APPLICABILITY.md
  FAILURES.md
  PROVENANCE.md
  TESTS.md
  PACKAGE/
  AUDIT.md
```

A Workflow candidate must identify:

- a bounded purpose;
- required inputs and prerequisites;
- ordered actions and decision points;
- exact code, script, command, environment, and HPC constraints where relevant;
- expected outputs and validation checks;
- known failures and stop conditions;
- applicability and non-applicability boundaries;
- exact originating Episodes, runs, artifacts, and assessments.

The Agent authors the workflow and Skill package by following the command guide.
The CLI validates structure, exact refs, package files, tests, and installation
targets. It never automatically installs or overwrites a Skill.

Installation, update, replacement, and rollback require the human to review the
exact package and target diff. An install receipt records before and after file
hashes, package ref, source workflow, target, and result. Rollback is a new
reviewed transaction, not deletion of history.

A Skill may reference Knowledge Cards as prerequisites or scientific context.
Those references do not copy scientific trust into the Skill.

## 12. Literature, Code, Runs, And HPC

### 12.1 Literature

`aitp literature add|extract|study|link|audit` keeps one physical PDF and exact
source identity. Extraction directories are immutable and content-addressed by
source hash, extractor version, and settings. Anchor rows record source hash,
page, kind, normalized location, text hash, and printed label.

A source note distinguishes what the author says from Agent interpretation.
Knowledge and writing commands consume exact source anchors, not untraceable RAG
chunks.

### 12.2 Code

Research-relevant code records pin repository identity, commit, branch as
observed, files, symbols, build/test evidence, and formula or Statement refs.
Uncommitted work uses a patch plus an untracked-file manifest. Credentials and
arbitrary repository copies do not enter the store.

Formula-to-code mappings bind an exact formula or convention ref to an exact
commit, blob hash, path, and symbol or line locator.

### 12.3 Runs And HPC

Run records identify exact command or script, code revision, environment,
inputs, outputs, host profile, scheduler/job identity, status, validation,
failure, and reproducibility boundary. Remote paths use stable host-profile
locators; authentication remains outside AITP.

The command guide tells the Agent how to operate the external host. AITP records
the durable result but does not become a scheduler or remote-control daemon.

## 13. Writing Products

`aitp write note|derivation|report|article|presentation` creates a writing
workspace containing the relevant guide, exact allowed Statements, source
anchors, Knowledge Cards, conventions, unresolved conflicts, and target output
path.

The Agent writes the document in normal Markdown, LaTeX, or presentation source.
The CLI checks citation/ref integrity and unsupported-claim declarations. It
does not become a prose generator separate from the host Agent.

Notes may remain exploratory. Derivations, reports, articles, and presentations
must distinguish established results, finite evidence, conditional arguments,
source-reported claims, and open gaps.

## 14. Audit, Review, And Canonical Writes

All commands use one visible finish path:

1. the Agent writes a command workspace;
2. deterministic audit reports missing fields, unresolved refs, invalid paths,
   source drift, provenance gaps, and declared incompleteness;
3. the Agent may correct files or explicitly preserve a declared gap;
4. the CLI stages the exact bytes and shows the target paths and diff;
5. required human review binds the exact staged hash;
6. one writer checks the base Git commit, writes the exact bytes, commits, and
   reads them back;
7. optional indexes update after the canonical commit.

Human review is required for:

- validated or proved-within-assumptions scientific promotion;
- replacement of an accepted scientific conclusion;
- contested conclusion resolution;
- Knowledge Card publication or refresh;
- shared promotion across topics;
- Workflow publication;
- Skill installation, update, replacement, or rollback;
- significant HPC cost, cancellation, or shared remote mutation.

An index failure cannot undo a successful canonical commit. A stale base commit
blocks the write. Interrupted work leaves a visible recovery record. There is no
last-writer-wins behavior.

## 15. What Is Deliberately Absent

AITP 2.0 has no required:

- MCP server or public MCP tools;
- host lifecycle hooks;
- full conversation recorder;
- context-pack compiler or recursive summary system;
- graph database, SQLite truth store, or vector database;
- autonomous route planner or multi-Agent dispatcher;
- web-research Agent;
- HPC scheduler or monitor daemon;
- automatic scientific trust promotion;
- automatic Knowledge Card publication;
- automatic Skill installation or update;
- rewrite of existing canonical research bytes.

Optional search indexes, semantic literature retrieval, and host adapters may be
added later only if the direct command-and-file protocol is already correct.

### 15.1 Simplicity Ratchet

The implementation must preserve these hard limits:

- one globally installed AITP routing Skill, `using-aitp`; generated research
  Skills are outputs rather than additional protocol modules;
- at most the twelve public command groups listed in Section 4;
- one canonical writer and one visible finish path;
- one command-local `SKILL.md` per command group, with subcommand differences
  expressed as short sections or templates rather than separately installed
  host Skills;
- zero required MCP servers, hooks, context compilers, databases, semantic
  indexes, dispatchers, schedulers, or background supervisors;
- no scientific conclusion or command selection implemented as hidden CLI
  heuristics.

A new public command, file family, required service, or semantic validator rule
requires a real research vertical that the existing command-and-file contract
cannot express. Convenience alone is not sufficient.

## 16. Required End-To-End Verticals

### 16.1 Quantum Chaos Long-Range Spin Chains

The vertical must prove:

- topic entry with background, goals, conventions, active routes, failed
  routes, and route-specific next actions;
- literature acquisition, exact anchors, source notes, and derivation records;
- finite numerical evidence kept separate from all-size claims;
- Scientific Dreaming over discussions, derivations, source conflicts, and
  failed hypotheses;
- reviewed Knowledge Card production and refresh;
- a note or derivation compiled from exact records.

### 16.2 LibRPA / Magnetic NiO

The vertical must prove:

- exact repository commit, branch, code path, formula mapping, and dirty patch
  recording;
- local and HPC run provenance, input parameters, outputs, failures, and
  applicability boundaries;
- reusable scripts promoted from temporary work;
- Workflow and Skill distillation from validated repeated work;
- human-reviewed local Skill installation and rollback;
- Knowledge Cards referenced by the Skill for physical conventions without
  transferring scientific trust.

### 16.3 Multi-Topic Reuse

The vertical must prove:

- one store supports several simultaneous topics;
- entry never silently merges topics;
- one physical paper can support several topics without byte duplication;
- a topic-local Knowledge Card or Workflow can be explicitly promoted to
  shared without moving or rewriting the original;
- cross-topic use requires target-specific scope and assessment.

### 16.4 Host Use

Codex and Kimi must complete entry, search, research, checkpoint, closeout,
Scientific Dreaming, Skill distillation, and writing through the same command
semantics. Host-specific differences are limited to Skill installation paths
and shell invocation.

## 17. Implementation Sequence

### S0. Freeze Examples And Compatibility Boundary

- write quantum-chaos, NiO, shared-paper, Knowledge Card, and Skill fixtures;
- freeze command names, guide format, path layout, record header, and exact-ref
  syntax against those fixtures;
- inventory the old store and stop old production writers;
- keep old records byte-identical and searchable through a read-only adapter.

### S1. Minimal Store And Read CLI

- implement root/topic discovery, path resolution, `enter`, `search`, `show`,
  and `admin doctor`;
- ship the first `using-aitp` Skill and command guides;
- prove direct filesystem fallback with no index.

### S2. Workspaces, Audit, And Recording

- implement command workspace creation and guide rendering;
- implement checkpoint, closeout, deterministic profiles, staging, exact diff,
  human review binding, serialized Git commit, readback, and recovery;
- prove that Agents author visible bytes and the CLI performs no hidden semantic
  rewrite.

### S3. Research, Literature, Code, And Run Guides

- implement research modes and literature intake/extraction;
- implement code revision, patch, formula mapping, run, and HPC profiles;
- pass the basic quantum-chaos and NiO recording verticals.

### S4. Scientific Dreaming

- implement `knowledge dream|refresh|link|finish`;
- implement Knowledge Card profile, assertion/source binding, derived health,
  immutable refresh, and shared promotion;
- pass quantum-chaos Knowledge Card and multi-topic reuse tests.

### S5. Workflow And Skill

- implement `skill distill|package|install|update|rollback`;
- implement Workflow and package profiles, exact install receipts, target diff,
  and recovery;
- pass the NiO reusable workflow and installation vertical.

### S6. Writing And Host Acceptance

- implement note, derivation, report, article, and presentation guides;
- validate Codex and Kimi command selection and guide rendering;
- verify that normal use needs no MCP, hooks, database, or context compiler.

### S7. Cutover And 2.0 Release

- rehearse old-store preservation, read-only compatibility, backup, recovery,
  and rollback on copies;
- update README, installation, migration, command, directory, and research-flow
  documentation;
- publish an RC, run real read-only acceptance, and perform only explicitly
  authorized canonical writes;
- publish stable `v2.0.0` after all acceptance checks pass.

## 18. Release Acceptance

AITP 2.0 is complete only when:

1. one installed `using-aitp` Skill routes first relevant research turns;
2. every public command renders a versioned command Skill and exact file contract;
3. direct Markdown, path, `rg`, and Git reads work without a derived index;
4. command output is sufficient context without a separate context compiler;
5. one visible write path preserves exact Agent-authored bytes;
6. the fixed directory structure separates canonical, shared, and runtime work;
7. Scientific Dreaming creates reviewed, source-bound Knowledge Cards and
   links them to existing research without rewriting history;
8. Skill distillation creates tested, bounded, human-reviewed packages without
   automatic installation;
9. notes and papers compile from exact local records and expose unsupported
   claims;
10. quantum-chaos, NiO, shared-literature, multi-topic, Codex, and Kimi
    verticals pass;
11. old canonical records remain byte-identical unless separately authorized;
12. no MCP, required hook, graph database, vector database, Agent dispatcher,
    scheduler, or hidden semantic writer is required;
13. documentation, installed Skills, command Skills, CLI help, templates, and actual behavior
    agree.

## 19. Design Closure

AITP 2.0 is not a second researcher running beside the host Agent. It is the
protocol that makes an AI researcher's local memory legible, durable,
searchable, reusable, and reviewable.

The host reasons. Commands select the phase. Command guides teach the phase.
Files carry the memory. Scientific Dreaming compiles physical understanding.
Skill distillation compiles repeatable procedure. Writing commands compile
research products. Human review controls the transitions that can change
scientific trust or install reusable behavior.
