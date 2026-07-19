---
title: AITP 2.0 Local Research Memory Rewrite
date: 2026-07-19
status: draft-for-user-review
supersedes:
  - docs/superpowers/specs/2026-07-10-aitp-final-research-operating-memory-design.md
  - docs/superpowers/plans/2026-07-09-aitp-final-research-lifecycle-roadmap.md
scope: AITP 2.0 product boundary, storage, protocol kernel, CLI, research lifecycle, code provenance, literature, skills, legacy cutover, and release acceptance
---

# AITP 2.0 Local Research Memory Rewrite

## 1. Executive Decision

AITP 2.0 is a clean, parallel rewrite of AITP as a local-first research memory
protocol for real theoretical-physics work. It preserves the existing research
store byte-for-byte as a read-only legacy layer and does not use the current v5
runtime, v5 public APIs, MCP surface, L0-L4 write lifecycle, host hook machinery,
or full v5 test suite as the new implementation baseline.

AITP 2.0 is not a general agent runtime. Codex, Kimi, or another host performs
reasoning, shell execution, web research, code editing, remote HPC work, and
multi-agent dispatch. AITP supplies a small, explicit protocol for:

1. entering the right research topic with bounded context;
2. finding exact prior records, files, code revisions, papers, and cross-topic
   reusable material;
3. staging and auditing durable research records at meaningful moments;
4. preserving formula-to-code, run-to-code, source-to-statement, and
   conclusion-to-assessment provenance;
5. compiling repeated, validated Episodes into reviewable Workflows and Skills;
6. keeping every canonical write visible, reviewable, and recoverable.

The rewrite deliberately replaces implementation breadth with a small protocol
budget:

- six canonical node types;
- one Relation edge schema;
- at most thirteen normal CLI command groups;
- one `admin` namespace;
- one canonical commit path;
- filesystem and `rg` as the baseline read path;
- zero MCP servers in the 2.0 runtime;
- zero required host hooks;
- zero required database or vector index for correctness.

## 2. Product Outcome

During a real research session, the user should be able to ask Codex or Kimi to
work on a condensed-matter calculation, a LibRPA code change, a formal
derivation, a quantum-gravity literature question, or a new scientific package.
The host should then:

1. run `aitp enter` on the first relevant research turn;
2. recover the topic background, goals, conventions, operational constraints,
   active route portfolio, validated and failed paths, open questions, exact
   Must Read references, and applicable reviewed workflows;
3. expand only the records needed for the current route;
4. conduct the actual research with its normal tools;
5. create a checkpoint only when a durable result, failure, decision, code
   change, source acquisition, run, or route transition has occurred;
6. expose the exact staged Markdown and diff to the Agent and human;
7. commit only after deterministic audit and any required human approval;
8. close out with route-specific next actions and declared gaps rather than an
   artificial claim that the research problem is complete.

AITP must remain secondary to the physics. Ordinary shell listings, exploratory
chat, failed typo-level commands, and transient model thoughts are not canonical
research memory.

## 3. Non-Goals

AITP 2.0 does not:

- automatically decide that a scientific conclusion is true;
- turn retrieval relevance, a RAG chunk, a summary, or a successful command into
  evidence;
- record every tool call or complete conversation transcript;
- orchestrate generic tools, agents, Slurm jobs, or unattended research loops;
- create a complete physics ontology;
- expose MCP as an alternative public API;
- require lifecycle hooks for correctness;
- preserve every v5 family, capability, facade, state machine, or test;
- rewrite existing canonical research records;
- require a graph database, SQLite index, or vector database;
- plan a second implementation-language rewrite after 2.0.

## 4. System Boundary

The architecture has four responsibilities, not four independent truth layers:

```text
Codex / Kimi / human
        |
        | shell commands and visible files
        v
AITP CLI contracts
        |
        +-- direct file reads and deterministic ref resolution
        +-- scoped rg and Git history queries
        +-- staging templates and deterministic audits
        +-- atomic compare-and-swap commit and receipts
        |
        v
.aitp canonical Markdown graph
        |
        +-- optional disposable FTS/vector indexes
        +-- optional generated entry/search views
        +-- reviewed WorkflowSpec and Skill packages
```

The CLI is a protocol boundary, not an intelligence layer. It does not hide the
semantic research content from the Agent. The Agent reads and writes the exact
Markdown that will become canonical.

## 5. Workspace And Storage

### 5.1 One Research Store, Many Topics

One research workspace owns one active `.aitp/` store. That store may describe
many topics and may map each topic to several external repositories, note trees,
data directories, or remote HPC locations. A code repository does not need its
own copy of the topic memory.

The active layout is:

```text
.aitp/
  config.toml
  protocol/
    schemas/
    templates/
    command-guides/
  topics/
    <topic-id>/
      TOPIC.md
      entities/
      statements/
      episodes/
      assets/
      assessments/
      relations/
  shared/
    entities/
    assets/
    assessments/
    relations/
    workflows/
  manifests/
    commits/
    approvals/
  runtime/
    local.toml
    sessions/
    staging/
    locks/
    recovery/
  indexes/
```

Canonical content is limited to `topics/`, `shared/`, portable reviewed protocol
configuration, and commit or approval manifests. `runtime/` and `indexes/` are
noncanonical and rebuildable. They are excluded from ordinary Git commits.
Machine-specific workspace paths and local host aliases live in
`runtime/local.toml`; canonical records refer to stable workspace and host
profile IDs.

### 5.2 Research Workspace Roles

AITP maps existing project directories to roles instead of forcing projects to
move into a new layout. A new topic may use the following recommended roles:

```text
notes/discussions
notes/derivations
notes/literature
notes/decisions
code/analysis
code/experiments
runs/local
runs/remote
runs/manifests
outputs/data
outputs/figures
outputs/tables
outputs/reports
writing/notes
writing/manuscripts
writing/presentations
sources/INDEX.md
reuse-candidates
scratch/scripts
scratch/downloads
scratch/outputs
```

Existing projects keep their current directories. Portable role declarations
live in `config.toml`; `runtime/local.toml` records which path on the current
machine fulfils each role. Absolute machine-specific paths are local
configuration, not portable scientific identity.

### 5.3 One Copy Of Each Paper

The shared literature library has one content copy per source:

```text
research/_shared/library/papers/<source-id>/
  source.pdf
  source.yaml
  extracted/
    text.md
    anchors.jsonl
    figures/
  notes/
```

Topic-local `sources/INDEX.md` files reference the source ID, its role in that
topic, and exact AITP refs. They never duplicate the PDF.

## 6. Canonical Research Model

AITP has six node types and one edge type.

| Type | Purpose |
| --- | --- |
| `Topic` | Stable research scope, background, goals, conventions, constraints, and workspace mappings. |
| `Entity` | A physical, mathematical, software, computational, or organizational object. |
| `Statement` | A question, hypothesis, claim, definition, insight, decision, constraint, open gap, or research route. |
| `Episode` | A bounded research event: discussion, derivation, code change, run, diagnosis, literature pass, or decision session. |
| `Asset` | A source, note, script, dataset, figure, report, code revision, patch, run manifest, workflow, knowledge card, or Skill package. |
| `Assessment` | An append-only evaluation of a node or relation, with method, scope, assumptions, outcome, and provenance. |
| `Relation` | One typed, attributable edge between exact refs. |

No Workflow, Skill, Knowledge, HPC, CodeState, Claim, Evidence, or Route record
family is added. These are represented by node kinds and Relations.

### 6.1 Statement Kinds

The initial controlled values are:

```text
question
hypothesis
claim
definition
insight
decision
constraint
open_gap
research_route
system_feedback
```

Project extensions use a namespaced value and must not create a new top-level
record type.

Statements also have a non-epistemic lifecycle value:

```text
active
resolved
superseded
archived
```

This supports active-route lookup without storing trust on the Statement.

### 6.2 Episode Kinds

The initial values are:

```text
exploratory_discussion
theory_derivation
literature_study
numerical_run
hpc_run
code_change
code_investigation
validation
writing_synthesis
research_decision
```

### 6.3 Asset Kinds

The initial values include:

```text
source
note
script
dataset
figure
table
report
code_revision
working_tree_snapshot
patch
run_manifest
environment_manifest
knowledge_card
workflow_candidate
workflow_spec
skill_package
install_receipt
```

Kinds are extensible metadata. They are not separate repositories, writers, or
public APIs.

### 6.4 Assessment Contract

An Assessment contains:

```text
target_ref
assessment_kind
outcome
method
scope
assumptions
basis_refs[]
assessor
independence
human_review_ref, when applicable
created_at
```

Its `outcome` is one of:

```text
supports
contradicts
inconclusive
scope_limits
reproduces
fails_to_reproduce
supersedes
```

Effective epistemic state is a derived, non-total-order projection:

```text
unassessed
open
hypothetical
finite_evidence
conditional
proved_within_assumptions
validated
contested
refuted
superseded
```

`proved_within_assumptions` requires explicit assumptions and either human
review or an independent deterministic check. Retrieval, an Agent summary, and
a successful execution cannot produce this state.

## 7. Identity And Revision

### 7.1 Stable IDs

Topic IDs are stable human-readable slugs. Other records use a type prefix plus
a sortable unique ID. Canonical non-Topic refs include the owning topic or
`_shared`, so a ref resolves to one path without a global database. Titles
remain human-readable but are not identity.

```text
topic:quantum-chaos-long-range-spin-chains
statement:quantum-chaos-long-range-spin-chains/stmt-01K0...
episode:quantum-chaos-long-range-spin-chains/ep-01K0...
asset:g0w0-magnetic-nio/asset-01K0...
assessment:g0w0-magnetic-nio/assessment-01K0...
relation:g0w0-magnetic-nio/rel-01K0...
asset:_shared/asset-01K0...
```

The record type and ID determine the canonical path. `aitp show` therefore does
not need to scan a database to resolve an exact ref.

### 7.2 Git Is The Byte Revision Ledger

AITP does not build a second integer revision state machine. A current ref omits
a revision; a pinned ref uses a Git commit:

```text
statement:quantum-chaos-long-range-spin-chains/stmt-01K0...
statement:quantum-chaos-long-range-spin-chains/stmt-01K0...@48fd02a...
```

Minor editorial corrections may update the same file. A change in scientific
meaning, scope, assumptions, or conclusion creates a new Statement linked with
`supersedes`. Past bytes remain available through Git.

The active `.aitp` canonical store is Git-backed. Git is required for canonical
writes and byte-pinned historical refs. The commit manifest stores the hash of
every changed canonical record. A content hash is not embedded in the file it
hashes.

### 7.3 Concurrent Writes

Every staging bundle records `base_commit` and expected hashes for any record it
changes. Commit is compare-and-swap:

1. acquire the single AITP writer lock;
2. verify the current commit equals the bundle base or that all expected paths
   are unchanged;
3. reject stale conflicting bundles;
4. move the exact staged bytes into canonical paths;
5. create the commit manifest, then create one Git commit containing the exact
   records and that manifest;
6. release the lock;
7. update disposable indexes;
8. read back and re-audit the committed bytes.

An index failure never invalidates a successful canonical commit. It marks the
index dirty and forces filesystem fallback.

## 8. Relations And Locators

One Relation record contains:

```text
id
from_ref
predicate
to_ref
scope
basis_refs[]
annotations
created_at
created_by
```

The initial predicate vocabulary is intentionally small:

```text
about
related_to
depends_on
derived_from
supports
contradicts
implements
implemented_by
uses
produced
validated_by
failed_because
supersedes
applies_to
candidate_for
installed_as
```

Cross-topic Relations are explicit and do not transfer epistemic state. A
workflow or source may be reused across topics; a target topic must create its
own Assessment before treating a scientific Statement as validated there.

Portable locators use schemes rather than unqualified machine paths:

```text
workspace://<workspace-id>/<path>
git://<repo-id>@<commit>/<path>#symbol=<symbol>&lines=<start>-<end>
pdf://<source-id>#page=<page>&anchor=<anchor-id>
ssh://<host-profile>/<path>
blob://sha256/<hash>
url://<https-url>
```

Credentials, private keys, tokens, and passwords are never locators or Assets.
An SSH host profile records a stable alias, capabilities, policy, and path roles,
not authentication secrets or live queue state.

## 9. Code, Formula, And Version Provenance

Code-changing research is a first-class vertical but does not require a new
record type.

### 9.1 Code Revision Asset

An `Asset(kind=code_revision)` records:

```text
repository_id
vcs = git
commit
parent_commits[]
branch_observed
remote_identity
submodule_commits
dirty = false
affected_paths[]
affected_symbols[]
build_assessment_refs[]
test_assessment_refs[]
```

Branch is orientation only. Exact provenance always uses the commit.

### 9.2 Uncommitted Code

If research must use uncommitted code, AITP records
`Asset(kind=working_tree_snapshot)` with:

```text
base_commit
patch_locator
patch_sha256
untracked_file_manifest
dirty = true
```

Such a snapshot is explicitly less portable than a code revision. A later
Episode links it to the final commit or explains why it was abandoned.

### 9.3 Formula-To-Code Mapping

A formula, convention, or algorithm is a Statement. Its implementation mapping
is a Relation with pinned locators:

```text
statement:g0w0-magnetic-nio/formula-id
  -- implemented_by -->
asset:g0w0-magnetic-nio/code-revision-id
```

The Relation annotations include:

```text
formula_locator
code_locator
symbol
blob_hash
convention_refs[]
mapping_notes
```

Line numbers alone are not sufficient. The Git commit and blob hash make the
mapping stable even after later edits. An Assessment may target the mapping
Relation and record derivation review, tests, numerical comparisons, known
limits, or discrepancies.

### 9.4 Code-Change Checkpoint

A durable code-change checkpoint records only research-relevant changes and
must include:

- base and resulting commit, or a declared working-tree snapshot;
- changed paths and important symbols;
- scientific or algorithmic reason for the change;
- formula, convention, issue, or route refs that motivated it;
- tests or numerical checks actually run;
- observed failures and unsupported conclusions;
- migration, compatibility, or reproducibility notes;
- the next route action.

Every numerical or HPC Episode that depends on code links the exact
`code_revision` or `working_tree_snapshot`. This allows an old output, formula,
and source implementation to be reconstructed together.

## 10. Read And Search Architecture

AITP uses the cheapest precise method and expands progressively.

### 10.1 Read Order

```text
known exact ref       -> deterministic file read
topic entry           -> TOPIC.md plus scoped active-route query and exact refs
lexical discovery     -> scoped rg
historical question   -> Git log/show/diff
structured relation   -> parse only matching Relation or target records
semantic literature   -> optional derived FTS/RAG candidates, then exact source
external information  -> host web, connector, repository, or HPC tools
```

`rg` is the baseline lexical engine, not the only retrieval mechanism. The host
may also run `rg` directly. `aitp search` adds safe scope selection, standard
globs, typed result formatting, malformed-file reporting, and coverage.

### 10.2 Search Scope

Default search is current-topic only. Cross-topic, shared-library, legacy, PDF
extraction, code workspace, and remote scope are explicit expansions. Search
never silently crosses all topics because a keyword happens to match.

Every result reports:

```text
snapshot_commit
method
searched_roots
included_scope
excluded_scope
malformed_files
truncation
index_freshness, when an index was used
coverage = exhaustive | partial | stale | unreadable
```

Absence is reported as:

```text
not_found       searched scope was exhaustive and readable
not_checked     relevant scope was not searched
not_shown       matching material was excluded by result/context budget
stale           derived index may not match canonical bytes
partial         some relevant roots or files were unavailable
```

Only `not_found` is an absence claim.

### 10.3 Optional Indexes

SQLite FTS and vector indexes are optional disposable accelerators. A clean
installation works without either. Deleting `.aitp/indexes/` changes performance,
not meaning, provenance, or the ability to search canonical Markdown.

## 11. Topic Entry Context

`aitp enter` produces concise Markdown for the Agent and the same data as JSON
with `--format json`. It does not inject all topic memory or recursively build a
large context pack.

The default order is:

1. Background
2. Related Topics
3. Research Goal
4. Must Read And Conventions
5. Operational Constraints
6. Current State
7. Active Research Routes
8. Validated Paths
9. Rejected, Failed, Inconclusive, And Superseded Paths
10. Open Questions And Blockers
11. Route Portfolio Proposal
12. Reusable Workflows And Skills
13. Expansion And Recall Status

`Selected because` is not model-facing content. Routing reasons remain available
in JSON or debug output.

Each active route includes:

```text
route_ref
goal
current_boundary
next_action
expected_output
dependencies
stop_conditions
cost_or_execution_mode
parallelizable_with[]
human_gate
exact_refs[]
```

AITP proposes a route portfolio. The human chooses when priority is ambiguous,
the route changes scope, shared files may conflict, or significant HPC cost is
involved.

## 12. Transparent Write Pipeline

### 12.1 Staging

The Agent writes the exact final Markdown under:

```text
.aitp/runtime/staging/<bundle-id>/
  GUIDE.md
  BUNDLE.json
  records/
    *.md
  AUDIT.md
```

The CLI pre-fills only mechanical fields such as ID, type, topic, timestamp,
template version, and base commit. The Agent writes all semantic content and can
inspect the files with ordinary reads, `rg`, and diff.

### 12.2 Audit

Every CLI command performs a cheap preflight appropriate to its action. Reads do
not run a full-store audit. Canonical writes require a blocking bundle audit.

Audit checks include:

- schema and frontmatter parsing;
- deterministic path and unique ID;
- reference and locator existence;
- relation endpoint compatibility;
- required sections for the recording profile;
- code commit, patch, source anchor, or output provenance where required;
- declared assumptions and applicability boundaries;
- unsupported validation or trust language;
- stale base commit and conflicting staged bundles;
- path traversal, symlink escape, and forbidden write roots;
- human approval requirements.

`AUDIT.md` contains stable rule IDs, exact file locations, severity, explanation,
and a suggested next action. Audit does not rewrite files or silently repair
semantic content.

### 12.3 Completeness

Completeness describes the quality of the record, not whether the scientific
problem is solved:

```text
complete
complete_with_declared_gaps
incomplete
blocked_for_human_review
```

A theory discussion may be complete with declared gaps when the question,
assumptions, derivation progress, failed step, uncertainty, exact notes, and next
action are all recorded even though no conclusion has been reached.

### 12.4 Commit

Commit preserves the exact audited staging bytes. Before creating the Git
commit, it writes a JSON commit manifest containing:

```text
bundle_id
base_commit
record_paths_and_hashes
approval_refs[]
audit_result_hash
actor
timestamp
```

The manifest intentionally does not contain the resulting Git commit hash or its
own content hash; either would be self-referential. The Git commit message binds
the bundle ID. After the commit, the CLI emits a regenerable runtime receipt
containing `new_commit`, index update status, and readback status. Durable truth
is the Git commit plus its in-tree manifest. There is no hidden semantic
compilation between human review and canonical write.

## 13. Recording Profiles

Profiles are visible, versioned templates and audit rules, not record families:

```text
exploratory-discussion
theory-derivation
literature-study
numerical-hpc
code-investigation
code-change
writing-synthesis
```

Profiles specify what a complete Episode bundle should address. They do not
force empty records for fields that are genuinely inapplicable; the Agent must
declare `not_applicable` with a reason.

## 14. CLI Contract

The normal command groups are:

### Read And Entry

- `aitp enter`
- `aitp search`
- `aitp show`

### Research And Sources

- `aitp research`
- `aitp literature`

### Recording And Review

- `aitp checkpoint`
- `aitp closeout`
- `aitp audit`

### Organization And Writing

- `aitp organize`
- `aitp compose`

### Reuse

- `aitp distill`
- `aitp review`
- `aitp install`

Maintenance lives under `aitp admin ...`. There is no `aitp run`; execution
belongs to the host.

Each command is self-describing and exposes one internal response as readable
Markdown or structured JSON. The response envelope includes, as applicable:

```text
status
snapshot_commit
scope
exact_refs
coverage
must_read
write_effects
human_decision_required
next_cli_commands
errors_and_warnings
```

Each command guide declares:

```text
purpose
use_when
reads
allowed_write_roots
must_read_rules
human_gates
possible_canonical_effects
completeness_checks
next_commands
```

The CLI uses stable nonzero exit codes for invalid input, incomplete audit,
required human review, stale concurrency state, proven not-found, partial read,
and operational failure. Prose is never the only failure signal.

## 15. Session Lifecycle

### 15.1 First Relevant Turn

The installed `using-aitp` Skill tells the host to invoke `aitp enter` on the
first turn that concerns durable research. Entry:

1. discovers the research root and workspace mappings;
2. reports unfinished sessions and staging bundles;
3. resolves a topic from cwd, explicit refs, and mapped workspaces;
4. asks the human when routing is ambiguous;
5. pins one snapshot commit;
6. returns bounded entry context and exact expansion commands.

The host does not need a lifecycle hook. A missed entry is recoverable by
running it later.

### 15.2 Durable Moments

A checkpoint is appropriate when one or more of these occurs:

- a new result or derivation boundary;
- an important failed or inconclusive route;
- a scientific or operational decision;
- a useful paper or source is fixed and anchored;
- a research-relevant code commit or patch is created;
- a reproducible local or HPC run completes or fails meaningfully;
- assumptions, conventions, applicability, or next action changes;
- a reusable workflow candidate becomes visible.

It is not appropriate after every tool call.

### 15.3 Closeout

`aitp closeout` checks for durable unrecorded work, route results, new assets,
failures, code changes, pending human decisions, and unresolved staging. It may
prepare a staging bundle but uses the same audit, review, and commit path.

If no durable change occurred, closeout writes no empty Episode. An abandoned
session is recovered at the next entry, and pending staging is never
automatically deleted.

Optional future host adapters may call `enter --noninteractive` and
`closeout --prepare-only`; they may not commit or bypass human gates. AITP 2.0
correctness does not depend on those events.

## 16. Research, Literature, Knowledge, And Writing

### 16.1 Deep Research

`aitp research begin|status|finish` prepares a topic-local scratch bundle with:

```text
GUIDE.md
question.md
search-plan.md
candidate-sources.md
source-notes/
synthesis-draft.md
```

Codex or Kimi uses its available web, browser, INSPIRE, repository, or other
tools. AITP provides the question, prior state, source criteria, output roles,
and recording contract. It does not implement a web-research agent.

### 16.2 Literature

`aitp literature add|inspect|link|extract|audit` records content hash, DOI or
arXiv identity, version, title, authors, source URL, acquisition date, access
restrictions, duplicate detection, topic role, and exact anchors.

Source notes distinguish author claims from Agent interpretation. A PDF,
extracted chunk, or embedding is not evidence by itself.

### 16.3 Knowledge Cards

A derived search or synthesis may propose a knowledge card. After review it may
become `Asset(kind=knowledge_card)` linked to exact source Assets, Statements,
and Assessments. Advanced ontology induction and automatic formal-theory
knowledge construction are deferred beyond 2.0.

### 16.4 Writing

`aitp compose note|article|report|derivation|presentation` prepares:

- allowed and disallowed claims;
- exact source and formula anchors;
- Must Read conventions;
- unresolved conflicts and human decisions;
- an outline and target workspace role.

The host writes Markdown, LaTeX, or presentation sources in the mapped writing
directory. A manuscript audit checks provenance and unsupported claims before a
writing-synthesis checkpoint.

## 17. Workflow And Skill Lifecycle

The reuse path is:

```text
successful Episodes
  -> workflow candidate
  -> applicability and completeness audit
  -> human review
  -> host-neutral WorkflowSpec
  -> Skill package candidate
  -> human install approval
  -> install receipt and rollback data
```

A WorkflowSpec is YAML and contains:

```text
identity_and_version
purpose
inputs_and_outputs
ordered_steps
preconditions
environment_and_hpc_profile_refs
code_revision_or_version_requirements
validation_checks
success_conditions
failure_conditions
stop_conditions
applicability_boundaries
source_episode_refs
assessment_refs
```

A Skill is host packaging around that workflow. It contains a normal `SKILL.md`,
host metadata such as `agents/openai.yaml`, optional scripts, references, and
assets, plus an AITP provenance manifest. Conceptual discussion and literature
summary alone cannot become a Skill.

The default project installation root is:

```text
.agents/skills/aitp-generated/<skill-name>/
```

Installation, replacement, update, and rollback require human approval. Later
usage Episodes and Assessments may create update candidates; they never
overwrite an installed Skill automatically.

## 18. Multi-Agent Research

AITP describes route dependencies and conflicts but does not dispatch agents.
For parallel routes:

1. the human approves the route portfolio when needed;
2. each Agent receives a route-specific bounded context;
3. each Agent writes a separate staging bundle with the same or declared base
   commit;
4. each result packet contains route ref, base commit, summary, Statement drafts,
   Asset refs, Assessment draft, unresolved issues, and next action;
5. commits are serialized;
6. a stale conflicting bundle is rejected and must be reconciled visibly.

No last-writer-wins merge is allowed for canonical records.

## 19. Human Gates And Safety

Low-authority records may be committed without per-record human approval after
audit:

- Episodes;
- Asset provenance;
- questions and hypotheses;
- explicit failed, inconclusive, or open paths;
- route next actions;
- working-tree snapshots and diagnostic observations with clear boundaries.

Human approval is required for:

- `proved_within_assumptions` or validated scientific promotion;
- replacing or superseding an accepted conclusion;
- resolving a contested conclusion;
- cross-topic scientific trust use;
- ambiguous route priority or scope change;
- significant HPC cost, cancellation, remote mutation, or shared writes;
- WorkflowSpec or Knowledge Card approval;
- Skill install, update, replacement, or rollback.

An approval receipt binds the actor, time, action, exact bundle hash, exact
subject refs, scope, and optional conversation locator. Generic approval text
cannot authorize changed bytes. Host sandbox approval for an external command
is separate from scientific approval.

## 20. Legacy Preservation And Cutover

The existing store is historical input, not the new runtime.

Cutover occurs only after:

1. stopping all old writers;
2. producing a complete path, size, and SHA-256 manifest of the old `.aitp`;
3. renaming it to `.aitp-legacy` without changing contained bytes;
4. initializing a new `.aitp`;
5. building a disposable legacy catalog and topic mapping;
6. proving `aitp search --legacy` and `aitp show legacy:...` can recover every
   catalogued old record;
7. testing rollback to the original directory name on a copy;
8. repeating the manifest comparison.

No bulk semantic migration is required. When new work needs an old result, the
Agent may create a new 2.0 record linked to the exact legacy locator. That new
record is reviewed under normal 2.0 rules; the old bytes remain unchanged.

The 2.0 release suite includes legacy manifest, read, search, show, and write
guard tests. It does not require old candidate submission, L0-L4 advancement,
promotion, legacy graph writes, v5 MCP, or full v5 E2E workflows to pass.

## 21. Implementation And Packaging Boundary

The formal public contract is the `aitp` command, Markdown/JSON output, visible
workspace files, and exit codes. The implementation language is not part of the
research data model.

AITP 2.0 may be implemented permanently as one small Python package because the
repository already uses Python and it provides mature YAML, Git, filesystem,
SQLite, and testing support. This is not a prototype scheduled for a later
rewrite. Normal users and Agents invoke `aitp`, never scattered `python
brain/...` scripts.

The package is limited to:

- root, topic, workspace, and exact-ref resolution;
- Markdown/frontmatter parsing and schema validation;
- scoped `rg` and Git command construction;
- audit rules and human-gate detection;
- staging, locking, compare-and-swap commit, recovery, and receipts;
- optional index adapters;
- Workflow/Skill package validation and installation receipts.

It does not synthesize scientific conclusions, orchestrate research tools, or
hide semantic writes. A native Rust or Go binary is considered only if measured
installation, startup, or concurrency requirements cannot be met. It is not on
the 2.0 roadmap.

`rg` is preferred when available. A bounded lexical fallback may keep the CLI
usable where `rg` is absent, but output must report the actual search method.

## 22. Failure And Recovery Semantics

AITP fails visibly and conservatively:

- malformed canonical files make affected coverage partial or unreadable;
- a stale index triggers filesystem fallback or a stale result, never a false
  absence claim;
- a stale base commit blocks canonical write;
- interrupted commits leave a recovery journal and deterministic receipt path;
- a successful canonical commit with failed index update remains successful;
- ambiguous topic routing performs no canonical write;
- missing source, code, run, or locator provenance blocks profiles that require
  it;
- pending staging is preserved until explicit commit, discard, or archive;
- no command silently fixes scientific content.

## 23. Required Research Verticals

### 23.1 Quantum Chaos Long-Range Spin Chains

The vertical must demonstrate:

- topic entry with background, conventions, goals, and multiple routes;
- formal derivation and finite-size numerical Episodes;
- validated, failed, inconclusive, and superseded paths;
- exact source and formula anchors;
- route-specific next actions and parallel route proposal;
- a writing-synthesis output with bounded claims.

### 23.2 LibRPA / Magnetic NiO

The vertical must demonstrate:

- exact repository, branch orientation, commit, patch, module, and symbol
  provenance;
- formula-to-code mappings pinned to commits and blob hashes;
- local and HPC run manifests, environment, inputs, outputs, and scheduler refs;
- the k444 frontier-inversion diagnostic, full-q control, and unresolved band-108
  collapse as bounded rather than over-promoted conclusions;
- a failed or partial run that remains useful for diagnosis;
- a reviewed reusable workflow candidate with applicability and failure bounds.

### 23.3 Shared Literature And Cross-Topic Reuse

The vertical must demonstrate one PDF content copy referenced by at least two
topics, exact anchors, topic-local interpretation, and no automatic transfer of
scientific trust.

### 23.4 Skill Lifecycle

The vertical must demonstrate repeated Episodes, Workflow candidate, audit,
human review, WorkflowSpec, Skill package, install approval, receipt, later
update candidate, and rollback without auto-overwrite.

### 23.5 Codex And Kimi Use

Both hosts must complete entry, exact expansion, scoped search, checkpoint,
audit, and closeout using only the CLI contract and a short `using-aitp` Skill.
Neither may require MCP or lifecycle hooks.

## 24. Rewrite Sequence

This design is implemented as small vertical slices. Detailed task and file
lists are written only after this spec is approved.

### R0. Contract Freeze And Historical Isolation

- approve this spec;
- mark prior v5 roadmaps and specs as superseded implementation authority;
- freeze old writers and define the legacy manifest/cutover rehearsal;
- create 2.0 schema, template, and CLI-output fixtures;
- establish architecture and complexity budgets.

### R1. Minimal Filesystem Kernel

- initialize the new `.aitp` layout on test fixtures;
- implement six node schemas, Relation, identity, pinned refs, and locators;
- implement exact `show`, Topic discovery, and Markdown/JSON response envelope;
- prove malformed records cannot disappear silently.

### R2. Progressive Read Path

- implement `enter`, scoped `search`, Git history expansion, and coverage;
- use deterministic reads and `rg` before any optional index;
- validate performance and context budgets against read-only copies of the two
  real topics;
- add optional FTS only if measurements justify it.

### R3. Transparent Write Kernel

- implement visible staging, profiles, audit, human-gate detection, lock,
  compare-and-swap commit, manifest, receipt, and crash recovery;
- prove exact staged-byte preservation and post-commit readback;
- prove multi-Agent conflicts never use last-writer-wins.

### R4. Research Verticals And Code Provenance

- implement the quantum-chaos and NiO verticals on fixtures or authorized
  staging copies;
- prove code revision, dirty patch, formula mapping, run, and HPC provenance;
- prove failed paths and declared gaps remain first-class;
- refine schemas only when a vertical cannot express a real event.

### R5. Literature, Writing, Workflow, And Skill

- implement one-copy literature intake and exact anchors;
- implement deep-research and compose workspaces;
- implement Workflow candidate, review, Skill package, install, update candidate,
  and rollback;
- keep vector RAG optional and trust-neutral.

### R6. Cutover And 2.0 Release

- rehearse legacy rename and rollback on a byte-identical copy;
- install and test the CLI and `using-aitp` Skill with Codex and Kimi;
- complete migration, backup, recovery, security, and user documentation;
- publish `v2.0.0-rc.1`;
- perform real read-only acceptance and explicitly authorized cutover checks;
- publish stable `v2.0.0` only after all release gates pass.

## 25. Release Gates

AITP 2.0 is release-ready only when:

1. the legacy before/after manifest is byte-identical;
2. every catalogued legacy record is available through search and exact show;
3. six node schemas and one Relation schema cover all required vertical events;
4. there is one canonical commit path and no MCP writer;
5. exact refs, Git-pinned revisions, locator validation, concurrent staging,
   stale-base rejection, and crash recovery pass;
6. malformed, partial, stale, not-checked, and not-shown states cannot be
   reported as not-found;
7. default `show`, `enter`, and scoped search meet documented local performance
   and context budgets on a representative ten-thousand-record fixture;
8. the quantum-chaos vertical covers theory, literature, finite numerical
   evidence, failure paths, route portfolio, and writing;
9. the NiO vertical covers code commits, formula mapping, dirty snapshots, HPC,
   remote assets, code diagnosis, bounded conclusions, and workflow extraction;
10. one PDF is referenced by multiple topics without duplicate content or trust
    propagation;
11. Workflow/Skill distill, review, install, update candidate, and rollback pass;
12. Codex and Kimi complete the lifecycle without MCP or required hooks;
13. no real canonical research record is modified without exact authorization;
14. README, installation, migration, backup, recovery, and actual behavior agree;
15. architecture-budget tests reject a second writer, required index, required
    hook, MCP surface, seventh node type, or unowned public command.

## 26. Deferred Beyond 2.0

The following require evidence from 2.0 use before design:

- default vector search or a production hybrid-RAG service;
- automatic formal-theory ontology construction;
- autonomous Insight promotion;
- an unattended Runtime Supervisor;
- automatic HPC monitoring and event-driven continuation;
- automatic Skill update or installation;
- a native implementation-language port;
- required host hooks;
- MCP compatibility;
- generalized external research-agent orchestration.

## 27. Design Closure

The 2.0 architecture is intentionally ordinary: transparent Markdown,
deterministic paths, `rg`, Git, a thin validator and transaction layer, and a
small CLI. Its value comes from choosing the right scientific recording
boundaries and preserving exact provenance, not from adding infrastructure.

The implementation plan must not reintroduce v5 abstractions merely to reuse
them. Existing code may be copied only when it satisfies this spec without
bringing old public surfaces, state machines, registries, or compatibility
dependencies into the new kernel.
