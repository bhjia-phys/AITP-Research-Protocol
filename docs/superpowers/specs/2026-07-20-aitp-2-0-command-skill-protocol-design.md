---
title: AITP 2.0 Command And Skill Research Protocol
date: 2026-07-20
revised: 2026-07-20
status: revised-for-user-review
reviewed_against:
  - docs/superpowers/audits/2026-07-20-aitp-2-0-command-skill-protocol-architecture-audit.md
review_disposition:
  - docs/superpowers/audits/2026-07-20-aitp-2-0-command-skill-protocol-audit-disposition.md
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

#### 3.1.1 Normative `using-aitp` Content

The installed Skill is short and host-neutral. Its host-specific wrapper may
change installation paths and shell syntax, but not the following behavior.

Trigger `aitp enter --cwd <cwd>` before answering when the request concerns:

- a named or cwd-mapped research topic;
- prior calculations, derivations, sources, conclusions, failures, code
  changes, runs, or next actions;
- literature study intended to affect an active research topic;
- a durable derivation, scientific code change, numerical/HPC run, research
  decision, Scientific Dreaming pass, Skill distillation, or research product.

Do not enter for:

- a generic textbook question with no project or prior-memory dependency;
- ordinary repository navigation, a typo-only edit, or transient shell
  inspection unrelated to research memory;
- an unrelated coding task merely because the workspace also contains AITP.

After entry, inspect the standard output spine from Section 4.1. If more than one
topic is plausible, ask the human before reading or writing topic-specific
records. If no topic is found, continue normally unless the user explicitly asks
to initialize or bind one.

Select the next command from Section 4.2. The host Agent performs this semantic
selection visibly; it never delegates it to a hidden CLI classifier.

Recovery behavior is mandatory:

- if `aitp` is unavailable, report that AITP is not installed and do not
  fabricate memory;
- if entry reports unresolved staging or a prior workspace, show the exact
  paths and ask before committing, discarding, or replacing anything;
- if entry should have occurred earlier, enter immediately, declare the
  late-entry boundary, and prepare retrospective records only for work that can
  be reconstructed from visible files, commands, sources, or the user's
  explicit account;
- if a read is partial or malformed, preserve that coverage state rather than
  claiming absence.

Invoke `aitp checkpoint` only for the durable moments in Section 9. Invoke
`aitp closeout` near the end of a meaningful session, not after every response.
Never infer human approval, scientific validation, a canonical commit, or a
Skill installation from conversational tone or an Agent-authored field.

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

#### 3.2.1 AITP 2.0 Package Boundary

The release is one clean Python distribution with one console entry point:

```text
pyproject.toml
src/aitp/
  cli.py
  command_skills/
  legacy_read/

[project.scripts]
aitp = "aitp.cli:main"
```

The exact internal module split may follow implementation evidence, but all 2.0
production imports originate below `src/aitp/`. Production code must not import
`brain/`, `brain/v5/`, legacy MCP or hook modules, old lifecycle gates, old
context compilers, or old package managers. A useful parser or Git primitive is
copied or reimplemented behind a 2.0 contract and covered by 2.0 tests rather
than imported across that boundary.

`src/aitp/legacy_read/` is a narrow compatibility reader. It may recognize old
files and return paths plus clearly labelled legacy metadata, but it cannot call
an old writer, mutate an old record, promote trust, rebuild an L0-L4 graph, or
make old schemas part of the 2.0 canonical write contract. The generated
platform launcher may be named `aitp.exe` on Windows; that launcher is only the
installed form of the same `aitp` command, not a second architecture.

### 3.3 Command Skills

Each command owns a packaged, versioned Skill inside the installed `aitp`
package:

```text
<installed-package>/aitp/command_skills/<command>/SKILL.md
<installed-package>/aitp/command_skills/<command>/templates/
<installed-package>/aitp/command_skills/<command>/profile.yaml
```

These files are package resources shipped in the same distribution as the CLI.
The baseline Python implementation resolves them through
`importlib.resources`, never relative to cwd, the research store, or a second
user-configured Skill root. Development uses the same package-resource contract
through an editable install. A missing resource or protocol-version mismatch is
a packaging error and fails the command; the CLI never silently loads a stale
external copy.

Each command `SKILL.md` starts with:

```yaml
---
protocol: aitp/2.0
command: knowledge
skill_version: 1
profile_version: 1
---
```

The command and profile versions must match the selected resources. The
installed distribution version and resource SHA-256 are added to rendered
output so a workspace remains auditable after an upgrade.

The command-local `SKILL.md` uses the same readable instructional style as a
host Skill, but it is not registered globally with the host. The CLI renders it
only when the command is used, keeping normal startup context small. A rendered
copy is named `GUIDE.md` inside a working directory so the Agent can work
without modifying the packaged Skill. The copy records the command Skill
version and SHA-256.

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

The minimal profile contract is:

```yaml
protocol: aitp/2.0
command: knowledge
profile_version: 1
requires_topic: true
workspace_template: knowledge
allowed_canonical_roots:
  - topics/<topic-id>/knowledge/cards/
  - topics/<topic-id>/statements/
  - topics/<topic-id>/relations/
required_workspace_files:
  - INPUTS.md
  - CARD.md
  - RECORD_CHANGES.md
deterministic_checks:
  - required_sections
  - ref_resolution
  - source_anchor_resolution
human_gates:
  - knowledge_card_publication
```

Profiles may require files, paths, resolvable refs, hashes, declared coverage,
and human gates. They may not contain prompts that judge scientific truth,
semantic relevance scores, or hidden route-selection rules.

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

`literature` owns the identity, one-copy bytes, extraction, anchors, and study
notes of a source. `research --mode deep-research` owns a question-bounded
investigation that may consume several existing sources and invoke `literature`
for newly acquired ones. The two commands never create competing source copies.

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
        skill-packages/
        install-receipts/
        scripts/

      code/
        revisions/
        patches/
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

Asset records use purpose-specific directories rather than a second generic
`assets/` directory. The mapping is normative:

| Asset kind | Canonical path |
| --- | --- |
| `source` | `shared/library/papers/<source-id>/SOURCE.md`; owned `source.pdf` and content-addressed extraction bytes remain in the same directory |
| `source_note` | `topics/<topic-id>/sources/notes/<id>.md` |
| `knowledge_card` | `topics/<topic-id>/knowledge/cards/<id>.md` or reviewed `shared/knowledge/cards/<id>.md` |
| `workflow` | `topics/<topic-id>/reuse/workflows/<id>.md` or reviewed `shared/workflows/<id>.md` |
| `skill_candidate` | `topics/<topic-id>/reuse/skill-candidates/<id>/CANDIDATE.md` |
| `skill_package` | `topics/<topic-id>/reuse/skill-packages/<id>/PACKAGE.md` |
| `install_receipt` | `topics/<topic-id>/reuse/install-receipts/<id>.md` |
| `script` | `topics/<topic-id>/reuse/scripts/<id>/SCRIPT.md` or reviewed `shared/scripts/<id>/SCRIPT.md`; owned script bytes stay beside it |
| `code_revision` | `topics/<topic-id>/code/revisions/<id>.md` |
| `working_tree_snapshot` or `patch` | `topics/<topic-id>/code/patches/<id>/PATCH.md`; owned patch and permitted untracked-file bytes stay beside it |
| `code_mapping` | `topics/<topic-id>/code/mappings/<id>.md` |
| `run` | `topics/<topic-id>/runs/<id>.md` |
| `note`, `derivation`, `report`, `article`, or `presentation` | `topics/<topic-id>/writing/<kind-plural>/<id>/ASSET.md`; authored source and generated outputs stay beside it |

Large datasets, figures, tables, raw outputs, and repository trees are not new
canonical Asset kinds by default. Their bytes stay at exact locators and are
described by the source, run, code, or writing record that owns their research
role. Adding an Asset kind requires both a unique canonical path and a real
vertical that cannot express the artifact through an existing owner.

A container Asset has exactly one Markdown owner record. Its manifest lists
payload paths and SHA-256 values but excludes the owner record itself, avoiding
self-hash recursion. Sidecars are not additional graph nodes and cannot be
referenced without their owner Asset ref.

`TOPIC.md` records stable background, goals, related topics, workspace roles,
Must Read refs, conventions, and durable constraints. Active routes, recent
events, and changing next actions remain in their own files and are selected by
`aitp enter`.

Topic IDs are lowercase ASCII slugs matching
`[a-z0-9]+(?:-[a-z0-9]+)*` and are unique within one store. On collision, the
human chooses a meaningful scope suffix such as `mbl-transition-floquet`; the
CLI never silently assigns an ambiguous numeric identity. A published Topic ID
and directory never change.

### 5.1 Store Initialization And Git Ownership

`aitp admin init [--path <research-root>]` creates `<research-root>/.aitp/`,
`STORE.md`, and the top-level `topics/`, `shared/`, and `runtime/` structure. It
does not overwrite an existing `.aitp` directory.

`STORE.md` records:

```yaml
protocol: aitp/2.0
store_id: <stable-id>
created_at: <timestamp>
git_mode: enclosing | standalone
git_root: <store-relative or research-root-relative locator>
```

If the research root is already inside a Git worktree, initialization uses that
enclosing repository after showing it to the human. It never creates a nested
`.aitp/.git`. If no enclosing repository exists, the human may approve
`git_mode: standalone`, in which case `.aitp` itself becomes the Git worktree.
Ref resolution and canonical commits always use the Git owner recorded in
`STORE.md`.

Machine identity, SSH aliases, and external workspace paths go only in
`runtime/local.toml`. A missing store makes `aitp enter` return an explicit
`not_initialized` result with the exact `aitp admin init` command; entry never
initializes or mutates a store implicitly.

The remaining administrative operations stay narrow:

- `aitp admin topic init <topic-id>` creates a staged Topic workspace and
  publishes it only through the normal audit, diff, and human-review path;
- `aitp admin bind --cwd <path> --topic <topic-id>` changes only the local
  workspace mapping in `runtime/local.toml`;
- `aitp admin doctor` is read-only and checks store identity, Git ownership,
  package-resource versions, ref integrity, permissions, and unresolved work;
- `aitp admin migrate` inventories legacy material and stages explicit 2.0
  copies while leaving every source byte unchanged;
- `aitp admin backup` creates and verifies a user-selected Git bundle or archive
  outside the store without changing canonical records;
- `aitp admin recover` shows one interrupted transaction and requires an
  explicit resume or abandon decision; abandon preserves its audit trail;
- `aitp admin config show` displays effective non-secret configuration and its
  source files without editing them.

## 6. Simple Record Contract

All canonical Markdown records use seven required common fields and one
optional discriminant:

```yaml
schema: aitp/2.0
id: <stable-id>
type: topic | entity | route | statement | episode | assessment | relation | asset
topic: <topic-id> | _shared
title: <human-readable title>
created_at: <timestamp>
created_by: <human-or-agent identity>
kind: <required only when the type profile has multiple kinds>
```

`kind` is required for Entity, Statement, Episode, Assessment, and Asset and is
omitted for Topic, Route, and Relation. Only fields needed by a real command
profile are added. A file must remain useful when read directly without the
CLI.

AITP has seven node roles plus one Relation edge role:

```text
Topic
Entity
Route
Statement
Episode
Assessment
Asset
Relation
```

The first seven are nodes. `Relation` is the only edge shape. Purpose-specific
Asset paths from Section 5 do not create additional node types.

The S0 fixture freeze must define these minimum profiles without importing
definitions from a superseded v5 document:

- `Topic`: stable background, scope, research goals, related-topic refs,
  workspace roles, Must Read refs, convention refs, and constraint refs;
- `Entity`: `kind`, aliases, definition or identity, and exact external locators
  when applicable;
- `Route`: goal, `proposed|active|paused|completed|abandoned` state, scope
  boundary, next action, expected output, stop conditions, execution/cost mode,
  required human decision, and optional human-set priority;
- `Statement`: `question|hypothesis|claim|definition|insight|decision|constraint|open_gap`
  kind, bounded content, scope, and explicit assumptions where applicable;
- `Episode`: `discussion|derivation|literature|code_change|code_investigation|run|validation|writing|research_decision|protocol_feedback`
  kind, time boundary, summary, `result|failure|inconclusive|decision|progress`
  outcome, and declared gaps;
- `Assessment`: target ref, assessment kind, method, scope, assumptions,
  basis refs, assessor, independence, and
  `supports|contradicts|inconclusive|scope_limits|reproduces|fails_to_reproduce|supersedes`
  outcome;
- `Asset`: one allowed kind from Section 5 or a later reviewed profile, its
  content or exact locator, hashes where bytes matter, and provenance;
- `Relation`: the fields and predicates below.

Statement trust is derived from applicable Assessments and human decisions. It
is not a mutable confidence field written by a Statement author. Route state,
Episode outcome, command success, retrieval rank, and Knowledge Card approval
cannot update Statement trust.

Topic IDs use Section 5's stable slug. Other IDs use a role prefix plus a ULID:
`ent-`, `route-`, `stmt-`, `ep-`, `assess-`, `asset-`, or `rel-`. File names
equal the record ID in flat record families. Container records such as
`TOPIC.md`, `SOURCE.md`, `CANDIDATE.md`, and `PACKAGE.md` take their ID from the
owning directory. Named package members and scripts take their stable identity
from the owning manifest.

### 6.1 Ref Resolution

Canonical refs are store-relative paths, optionally pinned to a Git commit:

```text
topics/<topic-id>/statements/<id>.md
topics/<topic-id>/knowledge/cards/<id>.md
shared/knowledge/cards/<id>.md
topics/<topic-id>/statements/<id>.md@<git-commit>
topics/<topic-id>/reuse/scripts/<id>/SCRIPT.md#payload=<relative-path>
shared/library/papers/<source-id>/SOURCE.md#anchor=<extraction-id>/<anchor-id>
shared/library/papers/<source-id>/SOURCE.md@<git-commit>#anchor=<extraction-id>/<anchor-id>
```

Store-relative paths are transparent to Codex, Kimi, humans, `rg`, Git, and the
CLI. Canonical files do not move after publication. Promotion to `shared/`
creates a new reviewed file linked to its source rather than relocating it.

The base ref before an optional selector is the exact POSIX-style owner-record
path relative to the `.aitp` store root, followed by an optional
`@<git-object-id>`. Current refs resolve by joining that path to the discovered
store root. Pinned refs resolve through the Git owner recorded in `STORE.md`
using the full commit object ID and the store path relative to that Git root.

Two selectors are allowed after one `#`:

- `payload=<relative-path>` selects a hash-listed sidecar owned by a container
  Asset;
- `anchor=<extraction-id>/<anchor-id>` selects one row in a source extraction.

Selectors do not create graph nodes. Relations and provenance point to the owner
record and may add the selector when the exact payload or source location
matters.

Resolution must:

1. reject absolute paths, drive-qualified paths, NUL bytes, empty components,
   `.` or `..` components, backslash-stored canonical refs, and paths outside
   `topics/` or `shared/`;
2. reject a current filesystem symlink whose resolved target escapes the store;
3. split and validate at most one selector, then parse a revision only from the
   final `@<object-id>` suffix of the owner-record portion and verify that it
   names a commit;
4. read pinned content through Git without checking it out or changing the
   working tree;
5. validate that frontmatter `id`, `type`, `topic`, and Asset kind agree with
   the resolved path profile;
6. resolve a payload only within the owner directory, verify its manifest hash,
   and resolve an anchor only within an extraction declared by `SOURCE.md`;
7. return `not_found`, `invalid_ref`, `outside_store`, `revision_not_found`,
   `profile_mismatch`, `payload_hash_mismatch`, or `anchor_not_found`
   distinctly.

Canonical records use full Git object IDs. Interactive `show` may accept an
unambiguous abbreviated revision but reports and emits the resolved full ID. No
database or type-to-plural lookup is involved because the canonical ref already
contains its directory.

### 6.2 Relation Contract

Relations are small Markdown files with:

```yaml
from_ref: <exact store-relative ref>
predicate: about | related_to | depends_on | conflicts_with | parallelizable_with | derived_from | supports | contradicts | produced | uses | implements | validated_by | failed_because | supersedes | applies_to | installed_as
to_ref: <exact store-relative ref>
basis_refs: []
scope: <where this relation applies>
qualifiers: {}
```

A Relation describes a link. It never validates a scientific Statement by
itself. Qualifiers are allowed only by the predicate profile. For
`predicate=uses` from a Workflow or Skill package to a Knowledge Card, they are:

```yaml
qualifiers:
  dependency_role: convention | approximation | applicability | background
  required: true | false
```

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

The default response budget is 8,000 Unicode characters, including headings and
refs. `--budget-chars` may reduce it or raise it up to a documented host limit,
but every response reports the requested budget, used characters, truncation,
and exact omitted refs. It does not recursively generate briefs, summaries,
relation maps, or other context products.

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

`RECORD_PLAN.md` explicitly declares whether the workspace contains a durable
positive, negative, inconclusive, or decision result and whether a checkpoint
is planned. If the Agent declares a durable result but no corresponding record,
`research finish` reports the gap and the exact `aitp checkpoint` command. The
CLI does not infer a failed hypothesis by semantically reading prose.

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

Dreaming never defaults to expanding an entire topic. The invocation records an
explicit selection scope. The CLI pre-populates `INPUTS.md` deterministically
from:

- exact refs supplied by the human or Agent;
- records owned by the selected Routes;
- records inside the selected time range or declared session workspaces;
- one-hop Relations from those records;
- source anchors and existing Knowledge Cards already referenced by that set.

`INPUTS.md` is an inventory, not an injected summary. Each row records:

```text
ref
title
kind
character estimate
selection reason
read status = unread | read_exact | skipped | not_checked
skip or not_checked reason
```

The CLI automatically marks records it rendered in full as `read_exact`. Direct
host file reads may be marked only by the Agent and remain declared rather than
cryptographically proven. The audit reports both sources of the mark.

The command Skill requires bounded passes. It first inspects the inventory and
coverage, then expands exact records in batches that fit the command's declared
character budget, then performs conflict and source cross-checks before writing
the card. It never substitutes a generated summary for a basis ref. Existing
`aitp show` performs the expansions; no Dreaming-specific context compiler or
additional subcommand is introduced.

The default Dreaming read budget is 24,000 Unicode characters per pass, with at
most three passes before the workspace must be resumed or the human explicitly
changes the budget. A record is either shown whole or deferred; it is never
silently truncated and then marked `read_exact`. The audit reports budget use,
deferred refs, pass count, and any Agent-declared direct reads separately.

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

The Agent may set `knowledge_candidate: true` with exact refs and a rationale in
`RECORD_PLAN.md` or the closeout summary. `aitp closeout` may then echo
`aitp knowledge dream` as a next command. Without that explicit declaration,
the CLI makes no semantic Dreaming suggestion. `using-aitp` may still select the
command from the visible user intent under Section 4.2.

`aitp audit <knowledge-workspace>` may run between passes. `knowledge finish`
requires a coverage report for selected, read-exact, skipped, and not-checked
inputs. Every basis ref used by `CARD.md` must be marked `read_exact`; unresolved
candidate coverage remains a visible limitation rather than a silent absence
claim.

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

Every substantive assertion has a local assertion ID and is marked as one of:

- `source_reported`, with one or more exact source-anchor refs;
- `aitp_statement`, with one or more exact Statement refs and their derived
  assessment states;
- `new_synthesis`, with one or more separately staged insight, hypothesis,
  claim, or open-gap Statement refs plus every source and Statement basis ref.

The readable body form is:

```markdown
### A-01 [source_reported]
Assertion: <bounded assertion text>
Basis:
- <exact source anchor ref> — supports <named clause or equation>
- <exact source anchor ref> — supports <named clause or boundary>
```

A `source_reported` assertion may combine several locations that report parts
of the same author claim, but its Basis list states which clause each location
supports. A new inference across authors, sources, Statements, approximations,
or regimes is `new_synthesis`, not `source_reported`.

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

Health is evaluated on `aitp show` of a card, before `aitp enter` renders a
Must Read card, during `knowledge refresh`, and during explicit `aitp audit`.
Checkpoint may report potentially affected cards by following exact Relations
from newly written Statements, Assessments, or sources. There is no background
scanner or scheduled health service.

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
    manifest.yaml
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
reviewed transaction, not deletion of history. `skill rollback <install-ref>`
restores the exact prior package recorded by the named receipt and writes a new
receipt; rolling back farther names an earlier receipt explicitly. Host-specific
packaging metadata is declared in the package manifest and validated against the
selected install target rather than inferred from cwd.

A Skill may reference Knowledge Cards as prerequisites or scientific context.
Those references do not copy scientific trust into the Skill.

Knowledge dependencies use the existing graph rather than a second canonical
dependency file. The reviewed Workflow and Skill package create exact
`Relation(predicate=uses)` records to each Knowledge Card. The Relation
qualifiers in Section 6.2 name the dependency role and whether it is required
for execution; `scope` states where that dependency applies scientifically.

`PACKAGE/manifest.yaml` mirrors those exact refs so the installed package is
self-describing outside the research store. Audit requires the manifest set and
the staged Relation set to match exactly; the Relations remain canonical.
`skill install` and `skill update` evaluate referenced card health. A broken
required dependency blocks installation. A stale or contested required
dependency requires an explicit human exception and an applicability warning.
A background-only dependency produces a visible warning without transferring
scientific trust.

## 12. Literature, Code, Runs, And HPC

### 12.1 Literature

`aitp literature add|extract|study|link|audit` keeps one physical PDF and exact
source identity. Extraction directories are immutable and content-addressed by
source hash, extractor version, and settings. Anchor rows record source hash,
page, kind, normalized location, text hash, and printed label.

Each `anchors.jsonl` line is one independently parseable object:

```json
{"id":"anchor-<ULID>","source_sha256":"<hash>","extraction_id":"<id>","page":12,"kind":"text|equation|figure|table|section","location":"<normalized locator>","text_sha256":"<hash>","label":"Eq. (3.7)"}
```

Anchor IDs are unique within one extraction. `SOURCE.md` lists each extraction
ID, source hash, extractor identity and version, settings hash, `text.md` hash,
and `anchors.jsonl` hash. Anchor selectors use Section 6.1 and fail closed when
the source, extraction, row, or text hash does not agree.

When full text is unavailable, `SOURCE.md` may declare `access: restricted` and
omit the PDF and extraction. Metadata and any lawfully available abstract or
notes remain usable, but the source cannot supply a page or equation anchor that
was not actually read. Later acquisition creates a content-addressed extraction
without rewriting the earlier access history.

A source note distinguishes what the author says from Agent interpretation.
Knowledge and writing commands consume exact source anchors, not untraceable RAG
chunks.

### 12.2 Code

Research-relevant code records pin repository identity, commit, branch as
observed, files, symbols, build/test evidence, and formula or Statement refs.
Uncommitted work uses a patch plus an untracked-file manifest. Credentials and
arbitrary repository copies do not enter the store.

A working-tree snapshot owns `changes.patch`, records its SHA-256 and base
commit, and inventories every untracked path with size, hash, capture state, and
reason. Small permitted files needed for reproduction are copied as
content-addressed sidecars. Large, secret, ignored, or unsafe files remain at
explicit locators and are marked `not_captured`; audit cannot call that snapshot
self-contained. The owner manifest excludes `PATCH.md` itself.

Formula-to-code mappings bind an exact formula or convention ref to an exact
commit, blob hash, path, and symbol or line locator.

### 12.3 Runs And HPC

Run records identify exact command or script, code revision, environment,
inputs, outputs, host profile, scheduler/job identity, status, validation,
failure, and reproducibility boundary. Remote paths use stable host-profile
locators; authentication remains outside AITP.

Each attempt is one `Asset(kind=run)` at
`topics/<topic-id>/runs/run-<ULID>.md` with at least:

```yaml
run_kind: local | hpc
status: prepared | submitted | running | succeeded | failed | cancelled | unknown
command: <exact argv or shell script ref>
code_ref: <code revision or working-tree snapshot ref>
environment: <inline bounded manifest or exact ref>
input_refs: []
output_locators: []
host_profile: <stable non-secret ID>
scheduler_job_id: <optional external ID>
validation_refs: []
failure: <required when status is failed or cancelled>
```

Retries create new run records and a `supersedes` or `related_to` Relation as
appropriate; an old attempt is not overwritten to look successful. A run that
depends on code cannot finish audit without `code_ref`.

The command guide tells the Agent how to operate the external host. AITP records
the durable result but does not become a scheduler or remote-control daemon.

## 13. Writing Products

`aitp write note|derivation|report|article|presentation` creates a writing
workspace containing the relevant guide, exact allowed Statements, source
anchors, Knowledge Cards, conventions, unresolved conflicts, and target output
path. The invocation supplies `--format`, or uses an explicit Topic writing
convention. Supported baseline formats are Markdown or LaTeX for notes,
derivations, reports, and articles, and Beamer LaTeX or Marp Markdown for
presentations. No presentation format is guessed silently.

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

Staging uses a temporary Git index based on the recorded base commit. The writer
computes the complete candidate tree object without changing the worktree.
Human review binds the base commit, candidate tree object ID, and target path
list. Commit time verifies those values again and commits that tree, so the
review hash has no self-referential manifest and unrelated working-tree changes
cannot enter the transaction silently.

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

S0 adds a blocking CI ratchet over the 2.0 package:

- production code exists only below `src/aitp/` and has no imports from the
  excluded legacy/runtime surfaces in Section 3.2.1;
- the public registry contains at most 12 command groups, exactly seven node
  roles, one Relation edge role, and one canonical writer entry point;
- the common record header remains the seven required fields plus optional
  `kind` in Section 6, and a
  kind-specific profile may require at most 12 additional frontmatter fields;
- nonblank, noncomment Python under `src/aitp/` is at most 12,000 lines for the
  2.0 release, and no production Python file exceeds 500 such lines;
- every command Skill, profile, and template is present as a resource in the
  same built wheel tested by CI.

These are release ceilings, not targets. Crossing one requires a user-approved
spec amendment backed by a failing real vertical; splitting or generating files
to evade a ceiling fails review.

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

- construct quantum-chaos, NiO, shared-paper, Knowledge Card, and Skill fixtures
  from explicitly authorized, read-only snapshots of real research material;
- keep the committed fixture minimal and sanitized, with real branching routes,
  useful failures, source limitations, formula-to-code provenance, run retries,
  and cross-topic reuse rather than an invented linear success story;
- write `tests/fixtures/aitp2/FIXTURE_PROVENANCE.md` with source class, snapshot
  Git commit or file hashes, selected records, redactions, transformations,
  access restrictions, and which content is synthetic; do not commit machine-
  specific absolute paths, credentials, restricted PDFs, or private raw data;
- if authorized material is insufficient, create a controlled fixture-only
  pilot labelled `seeding`; do not call the affected vertical frozen until its
  required behaviors are represented;
- freeze command names, normative `using-aitp` content, command Skill/profile
  format, Asset path mapping, all eight record-role profiles, common header, and
  exact-ref syntax against those fixtures;
- implement the blocking package, import, registry, schema-field, LOC, writer,
  and wheel-resource ratchets from Section 15.1;
- inventory the old store and stop old production writers;
- keep old records byte-identical and searchable through a read-only adapter.

### S1. Minimal Store And Read CLI

- implement root/topic discovery, path resolution, `enter`, `search`, `show`,
  `admin init`, and `admin doctor` in the clean `src/aitp/` package;
- ship the normative `using-aitp` Skill and all command Skills as version-matched
  resources in the same distribution;
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
14. secure current and revision-pinned ref resolution rejects traversal,
    symlink escape, profile mismatch, and worktree mutation;
15. store initialization never creates an unapproved nested Git repository;
16. Dreaming and entry report exact read coverage and obey their declared
    context budgets;
17. every Asset kind resolves to one frozen purpose-specific path and every
    required Skill-to-Knowledge dependency is auditable through Relations;
18. the built 2.0 wheel passes the simplicity ratchet and imports no legacy
    production surface.

## 19. Design Closure

AITP 2.0 is not a second researcher running beside the host Agent. It is the
protocol that makes an AI researcher's local memory legible, durable,
searchable, reusable, and reviewable.

The host reasons. Commands select the phase. Command guides teach the phase.
Files carry the memory. Scientific Dreaming compiles physical understanding.
Skill distillation compiles repeatable procedure. Writing commands compile
research products. Human review controls the transitions that can change
scientific trust or install reusable behavior.
