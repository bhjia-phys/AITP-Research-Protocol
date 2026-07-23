---
title: AITP 2.0 Command And Skill Research Protocol
date: 2026-07-20
revised: 2026-07-23
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

> **Revision note (2026-07-23)**: This amendment freezes observable
> behavior contracts (disk, file, navigation, read/write, CLI/Agent contract,
> runtime inventory, content envelopes, route navigation, read coverage,
> failure recall, gate matrix) without freezing Python code shape. Internal
> module layout, class/function boundaries, parser library, dispatch, and
> helper layering are implementation choices, not normative protocol. This
> amendment awaits Council + Oracle Gate A review. No normative authority
> changes that would reopen closed audit patches.

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

**Normative (behavior contract)**:

- One distribution providing one `aitp` console entry point.
- All 2.0 production imports originate below `src/aitp/`.
- Production code must not import `brain/`, `brain/v5/`, legacy MCP or hook
  modules, old lifecycle gates, old context compilers, or old package managers.
  A useful parser or Git primitive is copied or reimplemented behind a 2.0
  contract and covered by 2.0 tests rather than imported across that boundary.
- Command Skills and templates are package resources resolved through
  `importlib.resources` in the same distribution as the CLI; they are never
  resolved relative to cwd, the research store, or a second Skill root.
- A narrow legacy compatibility reader may recognize old files and return paths
  plus clearly labelled legacy metadata, but it cannot call an old writer,
  mutate an old record, promote trust, rebuild an L0-L4 graph, or make old
  schemas part of the 2.0 canonical write contract.
- The generated platform launcher (e.g. `aitp.exe` on Windows) is only the
  installed form of the same `aitp` command, not a second architecture.

**Non-normative (implementation shape — not protocol)**:

Internal module names, class/function boundaries, argument parser library
choice (argparse, Click, Typer), dict vs. dataclass vs. other internal data
representation, and writer implementation shape are implementation choices
that may follow evidence. The following is a non-normative illustration of one
possible layout:

```text
# ILLUSTRATIVE ONLY — not a normative module contract
pyproject.toml
src/aitp/
  cli.py                # entry-point module name not normative
  command_skills/       # resources, not named modules
  legacy_read/          # directory name not normative
```

The actual Python file/module inventory is determined by implementation
evidence, not by this spec. Contract tests verify behavior through CLI
subprocess invocation, filesystem state, Git state, and stdout JSON, not
through import of internal Python modules or assertion of module count/names.

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

#### 4.1.1 Common JSON Envelope (Frozen)

When a command returns JSON (e.g. `--json` flag, or machine-readable mode),
every response uses the same envelope:

```json
{
  "protocol": "aitp/2.0",
  "command": "<command-group>",
  "status": "ok | blocked | error",
  "store": "<store-relative-path> | null",
  "topic": "<topic-id> | _shared | null",
  "workspace": "<workspace-id> | null",
  "reads": {
    "items": [
      {
        "ref": "<store-relative-ref>",
        "status": "exact | deferred | skipped | not_checked",
        "reason": "<human-readable reason when not exact>"
      }
    ],
    "budget": {
      "unit": "unicode_characters",
      "requested": 8000,
      "used": 0,
      "truncated": false
    },
    "search_coverage": [
      {
        "scope": "<scope-name>",
        "status": "complete | partial | not_searched | stale",
        "next_command": "<exact next command to search this scope> | null"
      }
    ],
    "omitted_refs": [
      {
        "ref": "<store-relative-ref>",
        "reason": "<human-readable reason for omission>",
        "scope": "<route|body|source|search|other>"
      }
    ],
    "unexpanded_failures": {
      "count": 0,
      "refs": []
    }
  },
  "allowed_writes": [ "<store-relative-path>" ],
  "human_decisions": [ "<decision-id>" ],
  "finish_command": "<command> <args> | null",
  "next_commands": [ "<command>" ],
  "errors": [ { "code": "...", "detail": "..." } ],
  "result": { }
}
```

Semantics:
- All common envelope keys (protocol, command, status, store, topic,
  workspace, reads, allowed_writes, human_decisions, finish_command,
  next_commands, errors, result) must always be present. Use `null` or
  empty list/object when a field is not applicable (e.g. `"workspace": null`
  for commands that do not create one). No envelope key may be omitted.
- The default read budget for `aitp enter` is 8,000 Unicode characters
  (the `requested: 8000` in the example above is illustrative of this
  default; the actual canonical default is specified in §7.1).
  `--budget-chars` may raise it up to a documented host limit but must not
  reduce it below the 8,000 body/prose soft cap (the canonical default
  per §7.1). Nondiscardable overflow (navigation identities exceeding the
  cap) is unaffected by `--budget-chars`.
- Command-specific fields may appear only inside `result`, never at the
  top-level envelope.
- `status` is always `ok`, `blocked`, or `error`.
- `reads.items[].status` (per-item: `exact|deferred|skipped|not_checked`) and
  `search_coverage[].status` (per-scope: `complete|partial|not_searched|
  stale`) are independent dimension-specific enums. They are not alternative
  views of a single coverage enum. See §7.5 for full semantics.
- `not_searched` scopes require the `next_command` to suggest the exact search
  command; they do not require predicting unknown refs.
- An absence claim (asserting a ref does not exist) is valid only when all
  relevant `search_coverage` entries report `complete`.
- `unexpanded_failures.count` and `unexpanded_failures.refs` report
  `known_failure_refs` and `prior_attempt_refs` that enter did not expand due
  to budget. These fields are not truncated by the body budget — they must
  always be present when nonzero.
- `omitted_refs`: each entry is `{ref, reason, scope}`. `ref` is the
  store-relative ref that was omitted; `reason` is a human-readable explanation;
  `scope` categorizes why omission occurred (`route` — not part of current
  route's priority scope; `body` — body text truncated by budget (see below);
  `source` — source material not yet acquired; `search` — scope not yet
  searched; `other` — explicit human or Agent deferral). An empty
  `omitted_refs` array means no refs were identified for omission at this
  time — it does not mean the set of all possible omissions is empty.

**Budget overflow rules**: `budget.requested` is a body soft cap.
Nondiscardable navigation identities (Route `id`, `state`, `title`,
`next_action`, `stop_conditions`; `unexpanded_failures`; `search_coverage`
status and next-command) are always output in full and their character
count is included in `budget.used`. If the nondiscardable identities alone
exceed `budget.requested`, `budget.used` may be greater than
`budget.requested` — the nondiscardable requirement overrides the cap.
`budget.truncated` is `true` only when actual body text or body refs were
omitted because the cap was reached (not when nondiscardable identities
alone consumed the budget). `budget.truncated: true` is a signal that at
least one body item or ref was truncated/omitted — it does not mean every
item was truncated. Items that were read in full may retain `status: exact`
alongside a global `truncated: true`. Only items that were themselves
truncated or omitted due to budget must not be marked `exact`.
Truncated body refs appear in `omitted_refs` with `scope: body`.

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
      topics/
        <topic-id>/
          INDEX.md
    recovery/
    local.toml
```

Rules:

- `topics/` and `shared/` are canonical and reviewable.
- `runtime/` is noncanonical working state and may be rebuilt or cleaned only by
  explicit administrative action.
- Directories are not pre-created for every possible topic or kind; the layout
  above describes the allowed namespace, not a required empty skeleton at
  initialization time.
- a paper has one physical copy under `shared/library/papers/`; topics link to
  it rather than copying it;
- `runtime/indexes/topics/<topic-id>/INDEX.md` is a generated noncanonical
  convenience view. It must carry the following frontmatter fields:
  `generated: true`, `canonical: false`, `source_commit` (the Git commit from
  which it was generated), `generator_protocol` (the protocol version of the
  index generator), `topic` (the topic-id it indexes). It may be deleted,
  rebuilt, or carry a stale warning without affecting path-based or `rg`
  reads. A generation failure must not affect any other command.
  `topics/<topic-id>/INDEX.md` is a forbidden canonical path — no canonical
  record may live at that location;
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
| `working_tree_snapshot` | `topics/<topic-id>/code/patches/<id>/PATCH.md`; owned patch and permitted untracked-file bytes stay beside it |
| `patch` | (retired — use `working_tree_snapshot`; the `kind` value `patch` is not a valid Asset kind for 2.0 canonical records) |
| `code_mapping` | `topics/<topic-id>/code/mappings/<id>.md` |
| `run` | `topics/<topic-id>/runs/<id>.md` |
| `note`, `derivation`, `report`, `article`, or `presentation` | `topics/<topic-id>/writing/<kind-plural>/<id>/ASSET.md`; authored source and generated outputs stay beside it |

**Exhaustive Asset kind→profile→canonical path mapping** (normative):

| Asset `kind` | Profile fields (beyond common + kind) | Canonical path template(s) |
|---|---|---|
| `source` | `authors`, `year`, `version`, `identifiers`, `access`, `acquisition_refs`, `source_sha256` (cond), `extractions` | `shared/library/papers/<source-id>/SOURCE.md` |
| `source_note` | `source_ref` | `topics/<topic-id>/sources/notes/<id>.md` |
| `knowledge_card` | `card_form`, `question`, `summary`, `scope`, `use_when`, `do_not_use_when` | `topics/<topic-id>/knowledge/cards/<id>.md` or `shared/knowledge/cards/<id>.md` |
| `workflow` | `purpose`, `inputs`, `actions`, `outputs`, `validation`, `applicability`, `origins` | `topics/<topic-id>/reuse/workflows/<id>.md` or `shared/workflows/<id>.md` |
| `skill_candidate` | `workflow_ref`, `dependencies`, `tests` | `topics/<topic-id>/reuse/skill-candidates/<id>/CANDIDATE.md` |
| `skill_package` | `manifest_ref`, `files`, `hashes` | `topics/<topic-id>/reuse/skill-packages/<id>/PACKAGE.md` |
| `install_receipt` | `package_ref`, `target`, `before_hash`, `after_hash`, `result` | `topics/<topic-id>/reuse/install-receipts/<id>.md` |
| `script` | `purpose`, `inputs`, `outputs`, `environment` | `topics/<topic-id>/reuse/scripts/<id>/SCRIPT.md` or `shared/scripts/<id>/SCRIPT.md` |
| `code_revision` | `repository`, `commit`, `branch`, `files`, `symbols`, `formula_refs` | `topics/<topic-id>/code/revisions/<id>.md` |
| `working_tree_snapshot` | `base_commit`, `changes_patch_sha256`, `untracked_manifest` | `topics/<topic-id>/code/patches/<id>/PATCH.md` |
| `code_mapping` | `formula_ref`, `commit`, `blob_hash`, `path`, `locator` | `topics/<topic-id>/code/mappings/<id>.md` |
| `run` | `run_kind`, `status`, `command`, `code_ref`, `environment`, `input_refs`, `output_locators`, `host_profile`, `scheduler_job_id` (no), `validation_refs` (no), `failure` (cond) | `topics/<topic-id>/runs/<id>.md` |
| `note` | (uses generic container fields) | `topics/<topic-id>/writing/notes/<id>/ASSET.md` |
| `derivation` | (uses generic container fields) | `topics/<topic-id>/writing/derivations/<id>/ASSET.md` |
| `report` | (uses generic container fields) | `topics/<topic-id>/writing/reports/<id>/ASSET.md` |
| `article` | (uses generic container fields) | `topics/<topic-id>/writing/articles/<id>/ASSET.md` |
| `presentation` | (uses generic container fields) | `topics/<topic-id>/writing/presentations/<id>/ASSET.md` |

Each `kind` maps to exactly one canonical path profile (with topic-local
vs. shared variants allowed only where listed). No path hosts multiple
`kind` values. A record whose `kind` does not match its canonical path's
expected kind triggers `forbidden_canonical_path`.

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

### 5.1 Human/Agent Navigation Spine (Homomorphic)

Both human and Agent follow the same navigation structure. Navigation is
deterministic and file-grounded; no semantic inference, hidden classifier, or
graph walk substitutes for the visible files below.

The stable navigation spine is:

```text
TOPIC.md
  └─ active Route (sorted by explicit human-set priority)
       ├─ context_refs          — Must Read refs, conventions, related topics
       ├─ source_note           — topic-local interpretation of a shared SOURCE
       ├─ shared SOURCE.md      — one-copy source identity, extractions, anchors
       ├─ PDF anchor            — exact extraction anchor within a source
       ├─ prior_attempt_refs    — previous attempts at this route's goal
       ├─ known_failure_refs    — Episodes/Assessments recording failures
       ├─ blocking_assessment_refs — Assessments that block progress
       └─ next_action           — the next concrete step, with expected_output
                                  and stop_conditions
```

Navigation rules:

- `TOPIC.md` records stable background, goals, related topics, workspace roles,
  Must Read refs, conventions, and durable constraints.
- `aitp enter` enumerates active Routes in explicit human-set priority order and
  for each active Route shows its `context_refs`, `prior_attempt_refs`,
  `known_failure_refs`, `blocking_assessment_refs`, and `next_action`.
- A Route may reference a topic-local `source_note` for interpretation of a
  shared `SOURCE.md`. `SOURCE.md` lives under `shared/library/papers/` and is
  referenced, not copied.
- Exact source anchors use the `#anchor=<extraction-id>/<anchor-id>` selector.
- The navigation spine is stable across human and Agent reads — both see the
  same files in the same order. No Agent-only or human-only navigation path
  exists.
- Newly discovered context does not alter the file layout; it creates new
  records (Statements, Episodes, Relations, etc.) linked into the Route's ref
  lists through explicit human or Agent edits.

### 5.2 Noncanonical Workspace State

#### 5.2.1 `WORKSPACE.json` External Fields (Frozen)

Each command workspace under `runtime/workspaces/<command>/<workspace-id>/`
may carry a `WORKSPACE.json` for machine-visible state. The following
external fields are frozen; internal stack/transient state is not protocol.

| Field | Description |
|-------|-------------|
| `protocol` | `aitp/2.0` |
| `id` | workspace ULID |
| `command` | command group name |
| `mode` | command mode (e.g. research mode, dream) |
| `state` | one of the external workspace states (see §7.4) |
| `store` | store-relative path to `.aitp` |
| `topic` | topic-id or `null` |
| `base_commit` | Git commit at workspace creation |
| `skill_version` | command Skill version |
| `profile_version` | command profile version |
| `allowed_roots` | list of allowed canonical root paths |
| `input_refs` | refs supplied at workspace creation |
| `read_coverage` | coverage summary per §7.5 |

#### 5.2.2 `CANDIDATE.json` — Universal Canonical Write Candidate (Frozen)

Every canonical write produces exactly one `CANDIDATE.json` at:

```text
runtime/workspaces/<command>/<workspace-id>/CANDIDATE.json
```

This is the authoritative approval-binding instance for the transaction.
A noncanonical mirror may appear beside an Asset for convenience but is
not the approval authority; only the `runtime/workspaces/` copy binds the
approval. The runtime copy is noncanonical research data — Git commit
metadata provides the durable correspondence between approval and
committed canonical records.

Frozen external fields:

| Field | Description |
|-------|-------------|
| `protocol` | `aitp/2.0` |
| `workspace_id` | owning workspace ULID |
| `candidate_revision` | monotonic revision counter within the workspace |
| `state` | `draft \| review_ready \| approved \| committed \| rejected \| superseded` |
| `base_commit` | Git commit against which the candidate was prepared |
| `tree_object_id` | proposed Git tree object ID |
| `operations` | list of `{path, operation, sha256}` for each proposed file. `operation` is one of `create`, `update`, `delete`. For `delete`, `sha256` is the expected SHA-256 of the blob being deleted (the prior content must match; `delete` without a matching prior blob SHA fails). For `create` and `update`, `sha256` is the SHA-256 of the proposed new blob content. Every `path` in the list MUST be unique (duplicate paths within a single candidate are a `validation_failed` error and must be rejected before sorting or hashing). |
| `content_sha256` | SHA-256 of the concatenated operation payloads (deterministic canonical order) |
| `validation` | deterministic check results. Frozen shape: a sorted unique list of `{check_id, status}` objects. `check_id` is an ASCII identifier (pattern `[a-z][a-z0-9_]*`); `status` is `pass` or `fail`. Duplicate `check_id` entries are a `validation_failed` error. The universal `candidate_integrity` check (covering at minimum duplicate paths, operation/blob hash correctness, gate classification, and canonical byte-frame `content_sha256`) MUST always be present. An empty or missing `validation` list at `review_ready` is a `validation_failed` error. The `validation` digest is the SHA-256 hash of the concatenated per-`check_id` byte frames `<check_id> + NUL + <status> + LF` (sorted by `check_id` lexicographically, no separator between frames). For a deterministic-only commit, every entry must have `status: pass`. |
| `validation_sha256` | SHA-256 digest of the `validation` list computed by the canonical byte framing defined above (`validation` digest). This field is a frozen content identity field — it binds the validation result and must be included in `approval_binding` and commit metadata. |
| `required_gates` | human gate IDs required for this candidate. The frozen legal human gate ID set is `exact_diff_human_review | human_review`. Empty list (`[]`) means the candidate uses the deterministic-only path — every operation must pass deterministic validation and no human approval is required. A non-empty list must contain at least one legal gate ID, must be sorted lexicographically and de-duplicated, and each ID must map to at least one operation per the §14.0.1 matrix. Deterministic audit gates (add-only, assessor declaration) are NOT listed as gate IDs — they are always run and, if they pass, their corresponding matrix rows contribute no entries to `required_gates`. |
| `review` | review binding state |
| `approval_binding` | `{base_commit, tree_object_id, paths, content_sha256, validation_sha256, reviewer, timestamp, signature}` |
| `commit_oid` | Git commit OID after successful commit (absent until `state: committed`) |

Rules:

- After `state` transitions to `review_ready`, the **candidate content
  identity fields** (`base_commit`, `tree_object_id`, `operations`,
  `content_sha256`, `validation_sha256`, `required_gates`) are immutable. Lifecycle fields
  (`state`, `review`, `approval_binding`, `commit_oid`) may still
  transition through the lawful state machine (e.g. `review_ready` →
  `approved` → `committed`). Any content or path change creates a new
  revision with a new `candidate_revision`, `tree_object_id`, and
  `content_sha256`, and the prior `approval_binding` is invalidated.
- A candidate transitioning to `review_ready` MUST have a non-empty
  `validation` list. An empty or missing `validation` at `review_ready` is a
  `validation_failed` error. The `validation` list MUST include the universal
  `candidate_integrity` check covering at minimum: duplicate `path` entries
  in `operations`, operation→blob hash correctness, gate classification
  compliance per §14.0.1, and the canonical byte-frame `content_sha256`. Each
  `operation` and each declared `required_gates` entry MUST have at least one
  applicable deterministic check listed in `validation`. The `validation`
  byte digest shape (concatenated `<check_id> + NUL + <status> + LF` frames,
  sorted by `check_id`) is unchanged. A deterministic commit still requires
  every entry to have `status: pass`.
- `approval_binding` binds `base_commit`, `tree_object_id`, `paths`,
  `content_sha256`, and `validation_sha256`. If any of these change after
  approval, the binding is broken and a new review is required. Human
  approval must only be generated when all of: `validation` is non-empty,
  `candidate_integrity` has `status: pass`, and every `validation` entry
  has `status: pass`. An `approval_binding` generated against a failing or
  empty `validation` is invalid.
- After `review_ready`, the `validation` list and `validation_sha256` must
  not drift. If a deterministic check is re-executed and produces a different
  result or the computed `validation_sha256` changes, the current revision
  becomes `superseded` and a new `candidate_revision` starts in `draft` —
  there is no backward state transition, and the prior `approval_binding`
  (if any) is invalidated.
- **Pre-commit integrity re-execution**: Before transitioning to
  `committed`, the full deterministic validation suite MUST be re-executed
  (including `candidate_integrity` and all listed checks) and the
  `validation_sha256` MUST be recomputed from the canonical byte framing
  and confirmed to match the candidate's stored `validation_sha256`. Every
  check must have `status: pass`. Any failure or mismatch blocks the commit.
  In the human-gated path, `validation_sha256` must also match the value
  bound in `approval_binding` — the human cannot override deterministic
  integrity. In the deterministic-only path, `validation_sha256` must match
  the `validation` digest recorded in commit metadata. Neither path creates
  a third path — there are exactly two lawful paths as defined in the state
  machine below.
- `content_sha256` is computed over the `operations` list in canonical
  order: operations are sorted by POSIX target `path` (lexicographic by
  path string, UTF-8 byte order). For each operation in sorted order,
  produce a deterministic byte frame:

  ```
  <operation> + NUL + <path> + NUL + <sha256hex> + LF
  ```

  where `operation` is one of `create`, `update`, `delete`; `path` is
  the canonical store-relative POSIX path (UTF-8, must not contain NUL
  or ASCII control characters 0x00–0x1F, 0x7F); `sha256hex` is the
  lowercase hexadecimal SHA-256 digest of the blob content (for `create`
  and `update`) or the expected prior blob (for `delete`); `NUL` is the
  single byte 0x00; `LF` is the single byte 0x0A. The concatenation of
  these per-operation byte frames (no additional separator between
  operations) forms the byte sequence. The SHA-256 hash of this
  concatenated byte sequence is `content_sha256`.

  This byte-framed format eliminates the ambiguity of JSON object
  concatenation (field order variations, escaping differences,
  whitespace normalization) — the NUL delimiter and fixed field sequence
  make the encoding single-interpretation. The same set of operations
  always produces the same `content_sha256` regardless of insertion
  order.
- After successful commit, `state` becomes `committed` and `commit_oid` is
  recorded. The Git commit metadata (as part of the commit message or a
  machine-parseable trailer) must be recoverable from the commit object
  alone without requiring the runtime CANDIDATE copy.
  * **Human-gated commits**: metadata must include the complete approval
    identity: `candidate_revision`, `reviewer`, `timestamp`, `signature`,
    `paths`, `base_commit`, `tree_object_id`, `content_sha256`, and
    `validation_sha256`.
  * **Deterministic-only commits**: metadata must include `gate_mode:
    deterministic`, `candidate_revision`, `validation_sha256`, `paths`,
    `base_commit`, `tree_object_id`, and `content_sha256`. No `reviewer`
    or `signature` is required.
  A commit whose metadata lacks the fields required for its path, or
  where the metadata fields do not match the committed tree, is not a
  valid canonical commit — it must be treated as an unreviewed mutation.
- Runtime evidence (WORKSPACE.json, CANDIDATE.json, staging artifacts) is
  removed only by explicit `aitp admin cleanup` or recovery; committed
  candidates persist until explicitly cleaned.

**Candidate state machine**: Two exclusive lawful paths exist:

1. **Human-gated path**: `draft → review_ready → approved → committed`.
   `approval_binding` must be absent in `draft` and `review_ready` states
   and must be present in `approved` and `committed` states. A candidate in
   `approved` or `committed` state without `approval_binding` is invalid.
   Before `approved → committed`, the pre-commit integrity re-execution rule
   applies: all deterministic checks must be re-executed (including
   `candidate_integrity`), `validation_sha256` recomputed and confirmed to
   match the stored value and the `approval_binding.validation_sha256`.
   Commit metadata must preserve the complete approval identity:
   `candidate_revision`, `reviewer`, `timestamp`, `signature`, `paths`,
   `base_commit`, `tree_object_id`, `content_sha256`, and
   `validation_sha256`.

2. **Deterministic-only path**: `draft → review_ready → committed`.
   Permitted only when `required_gates` is empty (`[]`), every
   deterministic validation entry has `status: pass`, and the pre-commit
   integrity re-execution rule is satisfied. `approval_binding` MUST remain
   absent — no `reviewer` or `signature` is required. Commit metadata must
   record: `gate_mode: deterministic`, `candidate_revision`,
   `validation_sha256`, `paths`, `base_commit`, `tree_object_id`, and
   `content_sha256`. The metadata must be recoverable from the commit
   object alone.

If `required_gates` is non-empty, the human-gated path MUST
be used — a deterministic skip to `committed` is not permitted. Terminal
states `rejected` (from any pre-commit state) and `superseded` (replaced
by a later revision) apply to both paths. A candidate in `committed`
state without the appropriate metadata (approval identity for human-gated,
`gate_mode: deterministic` for deterministic-only) is invalid.

### 5.3 Store Initialization And Git Ownership

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
omitted for Topic, Route, and Relation. The common `kind` is a **record-profile
discriminant** that selects the subtype within a node role (e.g.
`Statement(kind=decision)`). Some profiles define additional subtype fields with
their own frozen value sets (e.g. `assessment_kind` for Assessment,
`scope_kind` for Episode/Assessment); these are profile-specific subtype fields,
not aliases for the common `kind` discriminant. Validators must enforce the
frozen value sets for each such field independently. Only fields needed by
a real command profile are added. A file must remain useful when read directly
without the CLI.

**Frontmatter vs body authority**: Frontmatter fields (YAML between `---`
delimiters) are the **sole machine authority** — validators, auditors, and
the CLI act exclusively on frontmatter values. Required human-readable body
sections (listed per record type below) are the **human projection** of
the same information. A static validator checks only that the required
headings/sections exist and that frontmatter fields satisfy machine-
parseable profile/path/type/kind/ref constraints. The validator does not
compare body prose to frontmatter for semantic agreement or consistency —
body text may express nuances, qualifiers, and context that machine rules
cannot adjudicate. `profile_mismatch` applies only to mechanically
determinable schema, path, type, kind, or ref mismatches; it is never
raised for natural-language semantic differences between frontmatter
and body. Repetition of information across frontmatter and body is
expected for human readability; the validator does not interpret prose.

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
- `Route`: `proposed|active|paused|completed|abandoned` state, scope
  boundary, next action, expected output, stop conditions, execution/cost mode,
  required human decision, and optional human-set priority;
- `Statement`: `question|hypothesis|claim|definition|insight|decision|constraint|open_gap`
  kind, bounded content, scope, and explicit assumptions where applicable;
- `Episode`: `route|topic|shared` scope kind,
  `discussion|derivation|literature|code_change|code_investigation|run|validation|writing|research_decision|protocol_feedback`
  kind, time boundary, `result|failure|inconclusive|decision|progress`
  outcome, and Route refs when route-scoped;
- `Assessment`: `scope_kind: route|topic|shared`, target ref, `assessment_kind`,
  method, assumptions, basis refs, `assessor: {identity, independence}`,
  `supports|contradicts|inconclusive|scope_limits|reproduces|fails_to_reproduce|supersedes`
  outcome, and body sections Applicability and Question. This list is a
  human-facing profile summary — the normative schema is the full Assessment
  record profile below; the summary does not define independent or additional
  fields. `scope` and `independence` are not top-level Assessment fields.
- `Asset`: one allowed kind from Section 5 or a later reviewed profile, its
  content or exact locator, hashes where bytes matter, and provenance;
- `Relation`: the fields and predicates below (see §6.2).

### 6.0 Record Envelope Foundations

#### 6.0.1 Content Envelope Boundaries

Record bodies use natural Markdown. A note or derivation Asset may embed
formulas, notebook references, intermediate failures, and supporting sidecar
files without creating a Statement, Assessment, or Episode per sentence or
formula. The following conditions are the **only** triggers for extracting a
separate canonical record:

1. **Cross-session stable identity**: the content must be referenced by
   multiple sessions, Routes, or topics.
2. **Independent provenance/review**: the content was created or reviewed
   independently of its container and carries its own provenance.
3. **Route or trust change**: the content changes the active Route's state,
   trust assessment, or next action.
4. **Conflict or reuse**: the content conflicts with or is reused by another
   record, requiring an explicit Relation.
5. **Human explicit `promote_to_record`**: a human (not the CLI or Agent)
   explicitly requests promotion of embedded content to a standalone record.
   This trigger requires provenance via the normal candidate workflow
   (`CANDIDATE.json`), human approval, and an audit trail. The CLI does not
   semantically judge whether promotion is appropriate.

If none of these conditions hold, the content remains within its owner Asset
as natural Markdown. An Episode is a bounded durable event summary with
time boundary and outcome — it is **not** a conversation transcript or a
per-turn log. A Relation expresses a meaningful logical link; it is **not**
used for containment (a note "contains" a derivation is not a Relation) or
ordinary mention (a Statement cites a source is not a Relation unless it
also satisfies one of the five triggers above).

#### 6.0.2 Minimum Required Profile Fields (Frozen)

All canonical record profiles (except `STORE.md`, `WORKSPACE.json`, and
`CANDIDATE.json`) **superimpose the 7-field common header** (`schema`,
`id`, `type`, `topic`, `title`, `created_at`, `created_by`) plus optional
`kind` where applicable. The `kind` field serves as a discriminant when
a type has multiple profiles (Entity, Statement, Episode, Assessment,
Asset); it is omitted for types with a single profile (Topic, Route,
Relation). The tables below display `kind` as a discriminant for
readability even though `kind` already belongs to the common-header
envelope. **For the 12-field ceiling, `kind` is not counted** — only the
remaining fields in each table are the profile-specific additional fields.

The 12-field ceiling from §15.1 counts **all additional profile frontmatter
fields** (required + optional) — the 7 common fields and `kind` are excluded
from the 12. Body sections and body-only titles are not counted.
No profile may exceed 12 additional frontmatter fields.

Each record type must expose at least the fields and body sections below.

**`STORE.md`** (standalone; does not use common header)

| Field | Required | Description |
|-------|----------|-------------|
| `protocol` | yes | `aitp/2.0` |
| `store_id` | yes | stable store identity |
| `created_at` | yes | ISO-8601 UTC |
| `git_mode` | yes | `enclosing` or `standalone` |
| `git_root` | yes | store-relative or root-relative locator |

Required human-readable sections: Store Identity, Git Ownership, Topic Index,
Conventions.

**`TOPIC.md`** (uses common header; `type: topic`; `topic` equals own `id`)

| Additional field | Required | Description |
|-------|----------|-------------|
| *(none beyond common header)* | | |

Required human-readable sections: Background, Research Goals, Related Topics,
Workspace Roles, Must Read, Conventions, Durable Constraints.

**Route** (uses common header; `type: route`)

| Additional field | Required | Description |
|-------|----------|-------------|
| `state` | yes | `proposed\|active\|paused\|completed\|abandoned` |
| `scope` | yes | scope boundary |
| `context_refs` | yes | Must Read refs, conventions, related topics for this Route |
| `prior_attempt_refs` | yes | refs to prior Episodes/attempts at this Route's goal |
| `known_failure_refs` | yes | refs to Episodes/Assessments recording known failures |
| `blocking_assessment_refs` | no | Assessments that block further progress |
| `next_action` | yes | next concrete step description |
| `expected_output` | yes | what completing the next action should produce |
| `stop_conditions` | yes | conditions under which the Route is paused or abandoned |
| `execution_mode` | no | cost/time/compute classification |
| `required_human_decision` | no | explicit human decision needed before next action |
| `priority` | no | explicit human-set priority |

Route `context_refs`, `prior_attempt_refs`, `known_failure_refs`, and
`blocking_assessment_refs` are frozen; `aitp enter` must report them
deterministically per §7.6.

Required human-readable sections: Goal, Scope Boundary, Current State,
Next Action, Expected Output, Stop Conditions, Required Context,
Prior Attempts And Known Failures, Human Decisions, Open Gaps.

**Entity** (uses common header; `type: entity`)

| Additional field | Required | Description |
|-------|----------|-------------|
| `kind` | yes | `physical_system\|mathematical_object\|observable\|method\|software\|compute_resource` |
| `aliases` | no | alternative names or symbols |
| `definition` | yes | bounded definition or identity |
| `external_locators` | no | exact external locators when applicable |

Required human-readable sections: Definition Or Identity, Scope And
Applicability, Aliases, External Locators. Additional kinds require a
reviewed profile but do not create a new node role.

**`shared/library/papers/<source-id>/SOURCE.md`** (uses common header;
`type: asset; kind: source`)

| Additional field | Required | Description |
|-------|----------|-------------|
| `authors` | yes | author list |
| `year` | yes | publication year |
| `version` | yes | version identifier |
| `identifiers` | yes | at least one of `{doi, arxiv, isbn, other}`; metadata-only sources use `other` with a stable descriptive value |
| `access` | yes | `full` or `restricted` |
| `acquisition_refs` | yes | refs documenting how the source was acquired |
| `source_sha256` | cond | SHA-256 of owned PDF; required when a PDF file is present in the source directory; omitted for metadata-only sources |
| `extractions` | yes | list of extraction IDs, hashes, extractor identity — may be empty for unprocessed sources |

Required human-readable sections: Bibliographic Identity, Version And File
Identity, Access And Rights, Acquisitions, Extractions, Known Limitations.

**Topic `source_note`** (uses common header; `type: asset; kind: source_note`)

| Additional field | Required | Description |
|-------|----------|-------------|
| `source_ref` | yes | ref to shared `SOURCE.md` |

Required human-readable sections: Why This Source Matters, Coverage,
Author-Reported Content, Topic-Specific Interpretation, Conventions And
Differences, Applicability And Caveats, Implications For Current Routes,
Open Questions, Exact Anchors.

**Statement** (uses common header; `type: statement`)

| Additional field | Required | Description |
|-------|----------|-------------|
| `kind` | yes | `question\|hypothesis\|claim\|definition\|insight\|decision\|constraint\|open_gap` |
| `content` | yes | bounded statement content |
| `scope` | yes | applicability scope |
| `assumptions` | no | explicit assumptions |

Required human-readable sections: Statement, Scope, Assumptions, Basis,
Known Limits.

When `kind: decision`, a decision overlay is required (frozen):

| Decision field | Required | Description |
|-------|----------|-------------|
| `decided_by` | yes | human identity (not Agent) |
| `alternatives` | yes | alternatives considered |
| `rationale` | yes | why this choice over alternatives |
| `basis_refs` | yes | refs supporting the decision |
| `decision_scope` | yes | scope of the decision |
| `decided_at` | yes | ISO-8601 UTC timestamp |
| `supersedes` | no | ref to a prior committed canonical decision (not a CANDIDATE or runtime object) being superseded; must be acyclic |

`created_by` records the file author; `decided_by` records the deciding
human. A canonical human decision requires a human gate; an Agent may
draft but must not self-approve as `decided_by`. `decided_by` and
`decided_at` are science/governance decision content (who decided what and
when), not a transaction approval binding. Transaction approval exists
only in the runtime CANDIDATE (per §5.2.2) and durable commit metadata —
it must never be embedded in the candidate content that it approves.

**Episode** (uses common header; `type: episode`)

| Additional field | Required | Description |
|-------|----------|-------------|
| `scope_kind` | yes | `route\|topic\|shared` — Episode scope classification |
| `kind` | yes | `discussion\|derivation\|literature\|code_change\|code_investigation\|run\|validation\|writing\|research_decision\|protocol_feedback` |
| `time_boundary` | yes | start/end timestamps |
| `outcome` | yes | `result\|failure\|inconclusive\|decision\|progress` |
| `route_refs` | yes | list of Route refs this Episode belongs to; must be non-empty when `scope_kind: route`; may be empty only for `scope_kind: topic` or `scope_kind: shared` |
| `resolution_refs` | cond | when this Episode records a resolved failure, refs to the resolving Assessment(s); may be absent for unresolved failures and non-failure Episodes |

When `kind: research_decision`, the decision overlay (see Statement above)
requires at most 12 total additional frontmatter fields including the
decision-specific fields.

Required human-readable sections: What Happened, Durable Summary, Durable
Result, Evidence And Artifacts, Failure Or Inconclusive Boundary, Decisions,
Next Actions, Declared Gaps.

**Failure recall rules**: A route-scoped (`scope_kind: route`) Episode with
`outcome: failure` or `outcome: inconclusive` must appear in the referenced
Route's `known_failure_refs`. Audit must verify bidirectional refs — the
Episode's `route_refs` and the Route's `known_failure_refs` must agree.
An Episode with `scope_kind: topic` or `scope_kind: shared` may have empty
`route_refs` and is not subject to route-level failure-recall consistency.
When a failure Episode is resolved by a subsequent Assessment with
`route_effect: resolves_failure` (see Assessment rule below), the Episode
gains `resolution_refs` pointing to the resolving Assessment; the Route
removes the Episode from `known_failure_refs` and adds it to
`prior_attempt_refs`. The Assessment's `route_refs` and the Episode's
`route_refs` must agree (same Route). There is no conditional "if
criteria" branch — these actions are mandatory when `route_effect:
resolves_failure` is set. The Episode itself is never deleted. A new
successful Episode on the same Route does not automatically overwrite or
hide the old failure. The Route↔blocking Assessment bidirectional
consistency requires: an Assessment with `scope_kind: route` and
`route_effect: blocks` must appear in the Route's
`blocking_assessment_refs`; the Assessment's `route_refs` must include
that Route. An Assessment with `route_effect: unblocks` removes its
`target_ref` (the prior blocking Assessment), never itself, from every
Route named by the matching Route set, as frozen below.

**Assessment** (uses common header; `type: assessment`; `kind: assessment`)

The common `kind` is the literal string `assessment` — it is a required
discriminant per §6 (required for all types that have multiple kinds) but
is part of the common header, not an additional profile field. It does not
count toward the 12 additional-field ceiling below.

| Additional field | Required | Description |
|-------|----------|-------------|
| `scope_kind` | yes | `route\|topic\|shared` — Assessment scope classification |
| `target_ref` | yes | ref being assessed |
| `assessment_kind` | yes | `reproduction\|code_review\|derivation_check\|numerical_verification\|literature_corroboration\|experimental_comparison\|peer_review\|methodology_review` — Assessment subtype; distinct from the common `kind` discriminant |
| `method` | yes | assessment methodology |
| `assumptions` | no | explicit assumptions |
| `basis_refs` | yes | refs supporting the assessment |
| `assessor` | yes | object `{identity, independence}`: `identity` is the assessor identity; `independence` is the assessor independence declaration |
| `outcome` | yes | `supports\|contradicts\|inconclusive\|scope_limits\|reproduces\|fails_to_reproduce\|supersedes` |
| `review_state` | yes | `draft` or `reviewed` |
| `reviewer` | cond | human reviewer identity; required when `review_state: reviewed`; must be a human identity (not Agent) |
| `route_refs` | yes | list of Route refs this Assessment applies to; must be non-empty when `scope_kind: route`; may be empty for `scope_kind: topic` or `scope_kind: shared` |
| `route_effect` | yes | `none\|blocks\|unblocks\|resolves_failure` — what effect this Assessment has on the Route's lifecycle |

Total Assessment additional fields: 12. The previous separate `scope` and
`independence` fields are removed — scope information is conveyed through
`scope_kind`, the target ref, and the body sections "Applicability" and
"Question Being Assessed"; assessor independence is part of the `assessor`
object.

Required human-readable sections: Question Being Assessed, Method, Checks
Performed, Findings, Applicability, Limitations, Outcome Rationale.

**Route effect rules (machine-determined — no "if criteria" branch)**:

- `route_effect: none` — the default. Required for all Assessments with
  `review_state: draft`, and for all `scope_kind: topic` or `scope_kind:
  shared` Assessments. A draft Assessment must never change scientific
  trust, unblock a Route, resolve a failure, or participate in promotion.

- `route_effect: blocks` — permitted only when `review_state: reviewed`,
  `scope_kind: route`, and a human reviewer identity is present in the
  `reviewer` field. When set, the referenced Route's
  `blocking_assessment_refs` MUST include this Assessment's ref.

- `route_effect: unblocks` — permitted only when `review_state: reviewed`,
  `scope_kind: route`, a human reviewer identity is present, and `target_ref`
  points to a human-reviewed route-scoped Assessment currently listed in
  every referenced Route's `blocking_assessment_refs`. The new Assessment's
  `route_refs` must equal the target Assessment's Route set. When set, each
  Route removes `target_ref` (the prior blocking Assessment), not the new
  unblocking Assessment, from `blocking_assessment_refs`. Both Assessments
  remain canonical and Git history preserves the transition.

- `route_effect: resolves_failure` — permitted only when `review_state:
  reviewed`, `scope_kind: route`, a human reviewer identity is present,
  and `target_ref` points to a route-scoped failure Episode. When set:
  the Episode gains `resolution_refs` containing this Assessment's ref;
  the Route moves the Episode from `known_failure_refs` to
  `prior_attempt_refs`; the Assessment's `route_refs` and the Episode's
  `route_refs` must match (same Route); no "if criteria" branch — these
  actions are mandatory when `resolves_failure` is set.

Only an Assessment with `review_state: reviewed`, a human `reviewer`, and
`scope_kind: route` may have a `route_effect` other than `none`. The
Assessment author (`created_by`) may be an agent or human — the critical
gate is the independent human `reviewer`, not the author.

**Run Asset** (uses common header; `type: asset; kind: run`)

| Additional field | Required | Description |
|-------|----------|-------------|
| `run_kind` | yes | `local` or `hpc` |
| `status` | yes | `prepared\|submitted\|running\|succeeded\|failed\|cancelled\|unknown` |
| `command` | yes | exact argv or shell script ref |
| `code_ref` | yes | code revision or working-tree snapshot ref |
| `environment` | yes | inline bounded manifest or exact ref |
| `input_refs` | yes | refs to input data |
| `output_locators` | yes | stable locators to output data |
| `host_profile` | yes | stable non-secret host ID |
| `scheduler_job_id` | no | external scheduler job ID |
| `validation_refs` | no | refs to validation records |
| `failure` | cond | required when status is `failed` or `cancelled` |

Required human-readable sections: Purpose, Inputs And Parameters, Code And
Environment, Execution, Outputs, Validation, Failure Or Anomaly,
Reproducibility Boundary.

All Asset owner records (including Run) use the `asset-<ULID>` ID prefix.
The `run-<ULID>` prefix is retired and must not appear in 2.0 canonical
records.

**Relation** (uses common header; `type: relation`)

| Additional field | Required | Description |
|-------|----------|-------------|
| `from_ref` | yes | exact store-relative ref |
| `predicate` | yes | one of 16 frozen predicates (see §6.2) |
| `to_ref` | yes | exact store-relative ref |
| `basis_refs` | yes | refs supporting the relation |
| `scope` | yes | where this relation applies |
| `qualifiers` | no | predicate-specific qualifiers |

Body is optional. If present: Rationale, Applicability Notes.

**Generic container Asset** (uses common header; `kind` one of: `note`,
`derivation`, `report`, `article`, `presentation`)

| Additional field | Required | Description |
|-------|----------|-------------|
| `kind` | yes | one allowed Asset kind from §5 |
| `content_or_locator` | yes | inline content or exact external locator |
| `hashes` | cond | SHA-256 where bytes matter |
| `provenance` | yes | origin and creation context |

Required human-readable sections: Purpose, Provenance, Payload Or Locator,
Validation, Known Limits.

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
   `profile_mismatch`, `payload_hash_mismatch`, `anchor_not_found`, or
   `forbidden_canonical_path` distinctly.

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

The default response budget is 8,000 Unicode characters for body and prose
content. Nondiscardable Route navigation identities (Route `id`, `state`,
`title`, `next_action`, `stop_conditions`; `unexpanded_failures`;
`search_coverage` status and next-command) are always output in full per the
budget overflow rules in §4.1.1 and may cause `budget.used` to exceed
`budget.requested`. `--budget-chars` raises the body soft cap up to a
documented host limit. Every response reports `budget.requested`,
`budget.used`, `budget.truncated`, and omitted refs. It does not
recursively generate briefs, summaries, relation maps, or other context
products.

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

### 7.3 Standard Error Codes (Frozen)

Every command must distinguish the following error codes distinctly. This is
the single frozen 19-code enum with total order — implementation MUST NOT
add new externally observable primary error codes. A new code requires a
reviewed protocol amendment that assigns a unique integer priority and
inserts it into the total order. Implementation-specific internal diagnostic
codes are permitted only in the `detail`/secondary field and must not alter
the primary error enum or its priority ordering.
The **Prio** column is a unique per-code integer priority (lower = higher
priority). When multiple errors occur in a single operation, the code with
the lowest priority value is the primary error. Ties are resolved by
lexicographic code name order (not expected with unique priorities).

| Code | Prio | Meaning |
|------|------|---------|
| `outside_store` | 0 | Resolved path escapes `.aitp` |
| `forbidden_canonical_path` | 1 | Record exists at a forbidden path (e.g. canonical `topics/<id>/INDEX.md`, path profile violation) |
| `invalid_ref` | 2 | Ref syntax is invalid |
| `not_initialized` | 3 | No `.aitp` store found; run `aitp admin init` |
| `ambiguous_topic` | 4 | Multiple candidate topics; human must disambiguate |
| `topic_not_found` | 5 | Named or cwd-mapped topic does not exist |
| `profile_mismatch` | 6 | Resolved record type/kind/topic mismatch (mechanically determinable only; not natural-language semantics) |
| `payload_hash_mismatch` | 7 | Sidecar hash does not match manifest |
| `validation_failed` | 8 | Deterministic check failed |
| `not_found` | 9 | Ref or path does not resolve to any record |
| `revision_not_found` | 10 | Pinned Git object-id not in repository |
| `anchor_not_found` | 11 | Extraction anchor does not exist |
| `approval_required` | 12 | Human approval required before proceeding |
| `approval_mismatch` | 13 | Staged bytes differ from approved binding |
| `stale_base` | 14 | Base commit changed since workspace creation |
| `write_conflict` | 15 | Another writer modified the target path |
| `recovery_required` | 16 | Interrupted transaction needs explicit resume/abandon |
| `not_available_in_stage` | 17 | Command not implemented in current release stage |
| `internal_error` | 18 | Unexpected CLI failure |

Error responses include the error code, its priority, and a human-readable
detail. Recovery guidance (exact next command) is included where the
resolution is deterministic.

**Error code enumeration (frozen)**: The error codes in the table above are
the single normative frozen error enum. All validators, ref resolution, plan
fixtures, and S0 oracles must reference this enum and its exact code strings.
No alternative error code strings or aliases are normative.

**Multi-error total order (frozen)**: When a single operation encounters
multiple error conditions, the primary error is the code with the lowest
Prio value. The full precedence is defined by the Prio column above — there
is no separate group-based ordering. Secondary errors may be listed in
`errors[]` for diagnostic purposes. This total order is testable through
S0 negative fixtures and serves as the normative reference for all future
golden error vectors.

### 7.4 External Workspace States (Frozen)

A command workspace in `runtime/workspaces/` has a visible state. The following
states are frozen; internal transient states (parser stack, in-memory flags) are
not protocol.

| State | Meaning |
|-------|---------|
| `open` | Workspace created; Agent may write |
| `review_ready` | Agent work complete; awaiting human review |
| `approved` | Human review passed; ready for commit |
| `committed` | Canonical records committed to store |
| `blocked` | Cannot proceed (missing input, unresolved decision) |
| `abandoned` | Explicitly abandoned with audit trail |
| `recovery_required` | Interrupted transaction; resume or abandon needed |

States advance through explicit commands. A workspace in `blocked` state must
record the blocking condition. `committed` workspaces are immutable; `abandoned`
and `recovery_required` workspaces preserve their audit trail.

### 7.5 Read Coverage Semantics (Frozen)

Every command that reads store files must report read coverage. The
coverage report comprises two independent dimensions, each with its own
enumerated status set:

- **Per-item read status** (`reads.items[].status`): tracks whether each
  identified ref was actually read. States: `exact`, `deferred`, `skipped`,
  `not_checked`.

- **Per-scope search status** (`search_coverage[].status`): tracks whether
  each declared search scope was fully searched. States: `complete`,
  `partial`, `not_searched`, `stale`.

These two status enums are independent dimensions — they are not
alternative views of a single "coverage" enum and must not be merged or
conflated. An item can have `status: exact` (file was read) even when
its containing search scope has `status: partial` (the scope was not
fully searched). Conversely, a scope can have `status: complete` even
when some items within it have `status: deferred`.

The per-item vocabulary is:

| Coverage state | Meaning |
|----------------|---------|
| `exact` | Full file content was read into context (CLI emitted or Agent read) |
| `deferred` | File was identified but not yet read; budget or explicit deferral |
| `skipped` | File was intentionally not read with explicit reason |
| `not_checked` | File existence not verified (optional scope not searched) |

Budget reporting uses the canonical `reads.budget` object from §4.1.1
(`budget.requested`, `budget.used`, `budget.truncated`). The §4.1.1
fields are the single authoritative names; any other budget field names
used in examples or non-normative prose are illustrative only.

Rules:

- The `reads` object in the §4.1.1 JSON envelope is the **sole canonical
  machine representation** of read coverage. All other representations
  (Markdown coverage sections, guide prose, inline status markers) are
  human projections derived from the same underlying coverage state.
- The coverage states for `reads.items[].status` are exactly the four
  values from §4.1.1: `exact`, `deferred`, `skipped`, `not_checked`.
- `search_coverage[].status` uses: `complete`, `partial`, `not_searched`,
  `stale`.
- `omitted_refs` entries carry `{ref, reason, scope}` per §4.1.1.
- `budget.truncated: true` means at least one body item or ref was
  truncated or omitted due to the character cap. Items that were read in
  full may retain `status: exact` alongside a global `truncated: true`.
  An individual item whose own content was truncated or omitted due to
  budget must not be marked `exact` — but unrelated items that were
  fully read are unaffected.
- Absence of a ref from the reads list is not proof of non-existence.
  The `search_coverage` report must distinguish `complete` search (all
  declared scopes searched) from `partial` search (some scopes omitted).
- `not_searched` scopes require `next_command` to suggest the exact search
  command; they do NOT require predicting unknown refs.
- An absence claim (asserting a ref does not exist) is valid only when
  all relevant `search_coverage` entries report `complete`.
- The coverage report is a declaration, not a cryptographic guarantee.
  Agent direct file reads are marked by the Agent and remain declared.

**Budget algorithm (deterministic)**: The budget overflow rules in §4.1.1
define the exact relationship between `budget.requested`, `budget.used`,
`budget.truncated`, nondiscardable navigation identities, and body
truncation. `omitted_refs` entries for truncated body content carry
`scope: body` per §4.1.1.

### 7.6 Enter Behavior (Frozen)

`aitp enter --cwd <cwd>` performs deterministic orientation. In addition to the
spine in §7.1, the following behaviors are contract:

**Minimum nondiscardable information**: The following fields must be present
in every `enter` response regardless of budget. They are not truncated by the
body budget — only the descriptive body text for each item is subject to
the character limit.

- For each active Route: `id`, `state`, `title` (the Route's body Goal
  heading), `next_action`, `stop_conditions`. These identify the Route and
  its current actionable state.
- `unexpanded_failures.count` and `unexpanded_failures.refs`: summary of
  `known_failure_refs` and `prior_attempt_refs` that were not expanded in
  the body due to budget. Always present when nonzero.
- `search_coverage`: for each declared search scope, `status`
  (`complete|partial|not_searched|stale`) and the exact `next_command` to
  run to search that scope.

**Body subject to budget**: For each active Route, `enter` must show
`context_refs`, `prior_attempt_refs`, `known_failure_refs`, and
`blocking_assessment_refs` from the Route's frozen fields. These may be
truncated at the body budget; the unexpanded count is reported in the
nondiscardable section.

- A new successful Episode must not overwrite or hide a prior failure Episode.
  Both remain in the Route's `known_failure_refs` or `prior_attempt_refs` until
  explicitly resolved by a human-reviewed Assessment.
- A Run with `status: succeeded` is a technical execution success — it does not
  constitute scientific validation. Scientific validity requires a separate
  Assessment.
- `enter` reports the existence of unexpanded refs but does not perform semantic
  inference over them. The Agent must expand them explicitly.
- `enter` does not depend on any semantic retrieval, embedding, or model-based
  ranking. Its output is deterministic given the same store state.

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
event. The Agent sees and edits the Markdown before finish. The applicable
gate for each record is determined by the action→gate matrix in §14.0.1,
which is the **sole normative authority** for mutation gates.
Low-authority Episodes, questions, hypotheses, failed routes, provenance,
and declared gaps are governed by §14.0.1, not by a separate checkpoint
allowlist. Trust promotion and the products listed in Section 13 require
human review per §14.0.1.

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
read status = exact | deferred | skipped | not_checked
skip or not_checked reason
```

The CLI automatically marks records it rendered in full as `exact`. Direct
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
silently truncated and then marked `exact`. The audit reports budget use,
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
requires a coverage report for selected, exact, skipped, and not_checked
inputs. Every basis ref used by `CARD.md` must be marked `exact`; unresolved
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
`topics/<topic-id>/runs/asset-<ULID>.md` with at least:

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
5. human review gates the complete approval binding per §5.2.2:
   `{base_commit, tree_object_id, paths, content_sha256, validation_sha256,
   reviewer, timestamp, signature}` — commit-time revalidation includes both
   `content_sha256` and `validation_sha256` per the pre-commit integrity rule;
6. one writer checks the base Git commit, re-executes all deterministic
   checks, confirms `validation_sha256` match, writes the exact bytes,
   commits, and reads them back;
7. optional indexes update after the canonical commit.

Staging uses a temporary Git index based on the recorded base commit. The writer
computes the complete candidate tree object without changing the worktree.
Human review binds the complete §5.2.2 approval binding. Commit time re-executes
the full deterministic validation suite (including `candidate_integrity`) and
verifies both `content_sha256` and `validation_sha256` match, so validation
drift cannot enter the transaction silently.

Human review is required for:

- validated or proved-within-assumptions scientific promotion;
- replacement of an accepted scientific conclusion;
- contested conclusion resolution;
- Knowledge Card publication or refresh;
- shared promotion across topics;
- Workflow publication;
- Skill installation, update, replacement, or rollback;
- significant HPC cost, cancellation, or shared remote mutation.

### 14.0 Gate And Writer Floor

#### 14.0.1 Action → Minimum Gate Matrix (Frozen)

Each action class maps to a minimum required gate. A command may escalate
the gate but never reduce it below this matrix. A profile or Skill version
bump must not lower the global gate for any action — the gate matrix is a
floor, and version bumps can only raise it.

**Mutation taxonomy and default**: Every canonical mutation falls into a
category below or is unclassified. An unclassified mutation defaults to
`human_review` — the gate is fail-closed. The **Gate ID** column specifies
the frozen human gate identifier. Rows with no Gate ID use deterministic
audit only — they produce no entry in `required_gates`.

| Action | Minimum Gate | Gate ID |
|--------|-------------|---------|
| Low-authority failure Episode (topic/shared-scoped only; see escalation below) | Deterministic audit only (add-only) | — |
| Question or hypothesis draft Statement | Deterministic audit only (add-only) | — |
| Assessment draft (`review_state: draft`) | Deterministic audit + explicit assessor declaration | — |
| Failed Route creation or transition to `abandoned` / route priority change / route scope change / route failure-ref mutation | Exact diff + human review | `exact_diff_human_review` |
| Route canonical mutation (any of the 12 Route profile fields: `state`, `scope`, `context_refs`, `prior_attempt_refs`, `known_failure_refs`, `blocking_assessment_refs`, `next_action`, `expected_output`, `stop_conditions`, `execution_mode`, `required_human_decision`, `priority`) | Exact diff + human review | `exact_diff_human_review` |
| Route transition to `completed` or `abandoned` | Exact diff + human review | `exact_diff_human_review` |
| Validated/proved-within-assumptions scientific promotion | Human review | `human_review` |
| Knowledge Card publication or refresh | Human review | `human_review` |
| Shared promotion (topic-local → shared) | Human review | `human_review` |
| Workflow publication | Human review | `human_review` |
| Skill installation, update, or rollback | Human review | `human_review` |
| Significant HPC cost, cancellation, or shared remote mutation | Human review | `human_review` |
| Unclassified mutation | Human review (fail-closed default) | `human_review` |

The frozen legal human Gate ID set is exactly `{exact_diff_human_review,
human_review}`.

**Add-only semantics**: "Deterministic audit only (add-only)" means the
CLI runs structural checks and, if all pass, stages and commits the new
record without a human review gate. However, the action must not mutate
any existing canonical record's fields, change Route state, alter trust,
or modify ref lists in other records — it is a pure addition. The Agent
declares the action; the CLI never infers scientific meaning to escalate
or de-escalate.

**Route-scoped failure Episode escalation**: A route-scoped
(`scope_kind: route`) failure Episode that would require updating the
referenced Route's `known_failure_refs` or `prior_attempt_refs` to
satisfy bidirectional failure recall (§6.0.2) **cannot** use the
deterministic add-only gate — the entire candidate must escalate to
Route exact diff + human review. Only topic-scoped or shared-scoped
(`scope_kind: topic` or `scope_kind: shared`) failure Episodes that do
not modify any Route's refs may use the deterministic add-only gate.

**Route mutations**: Any mutation to a Route's 12 canonical frontmatter
fields (`state`, `scope`, `context_refs`, `prior_attempt_refs`,
`known_failure_refs`, `blocking_assessment_refs`, `next_action`,
`expected_output`, `stop_conditions`, `execution_mode`,
`required_human_decision`, `priority`) requires exact diff display and
human review. Transitions to `completed` or `abandoned` always require
human review regardless of how they are triggered.

**Assessment draft**: An Assessment with `review_state: draft` may be
created through deterministic audit + assessor declaration. However,
a draft Assessment must not change scientific trust, unblock a Route,
resolve a failure, or participate in promotion. Only a human-reviewed
Assessment (`review_state: reviewed`) may affect these derived states.
The Agent declares the action; the CLI never infers scientific meaning to
escalate or de-escalate.

#### 14.0.2 Writer Behavioral Contract (Frozen)

The canonical writer is a behavioral contract, not a Python class. The
following invariants are observable through CLI subprocess, filesystem,
and Git:

- **One visible writer**: exactly one command path (finish/commit) performs
  canonical writes. Whether this is implemented as one class, several
  functions, or a module split is not normative.
- **Candidate approval**: the writer produces a `CANDIDATE.json` at
  `runtime/workspaces/<command>/<workspace-id>/CANDIDATE.json` per §5.2.2.
  Human review binds the complete §5.2.2 `approval_binding`:
  `{base_commit, tree_object_id, paths, content_sha256, validation_sha256,
  reviewer, timestamp, signature}`. Pre-commit re-execution of all
  deterministic checks and `validation_sha256` digest match is required
  per §5.2.2; any mismatch blocks the commit.
- **Unrelated dirty exclusion**: staging uses a temporary Git index based on
  the recorded base commit. Unrelated working-tree changes (files not in the
  candidate path list) must not enter the transaction.
- **Stale / changed bytes fail**: at commit time, the writer verifies the base
  commit matches and the tree object ID matches the staged bytes. If the base
  commit changed or staged bytes changed since review, the write is blocked.
- **Git transaction**: commit writes the candidate tree as a single Git commit.
  The writer reads back the committed tree and verifies every path and hash.
- **Readback / recovery**: after commit, the writer confirms all paths are
  present in the committed tree. Interrupted writes leave a recovery record;
  no silent partial commit.
- **Single writer**, in this context, means a single behavioral entry point for
  canonical writes — not a single Python class or function.

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

S0 freezes these future ceilings and executes **production-absence + static
oracle checks only**:

- S0 asserts that no production `src/aitp/`, `pyproject.toml`, built wheel,
  package resources, `command_skills/`, or legacy imports exist in the
  repository (per the S0 simplicity ratchet §8.1 of the S0 plan).
- S0 asserts the static ceiling expectations (≤12 commands, 7+1 nodes,
  1 writer, ≤12 profile fields) against FREEZE.json as a reviewed oracle.

S1 is the first stage to enforce the full ratchet against an actual
production package:

- production code exists only below `src/aitp/` and has no imports from the
  excluded legacy/runtime surfaces in Section 3.2.1;
- the public registry contains at most 12 command groups, exactly seven node
  roles, one Relation edge role, and one canonical writer entry point;
- the common record header remains the seven required fields plus optional
  `kind` in Section 6, and a kind-specific profile may require at most 12
  additional frontmatter fields;
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

**S0 scope** (per U1 resolution 2026-07-23): pure contract freeze, oracle,
static fixture corpus, and static test-only structural validation. S0 does
NOT create or execute a production CLI, built wheel, package resources,
legacy reader, or CLI subprocess/runtime acceptance tests.

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
  format, Asset path mapping, all eight record-role profiles, common header,
  exact-ref syntax, content envelope boundaries (§6.0.1), profile fields
  (§6.0.2), Route navigation fields (§5.1), read coverage semantics (§7.5),
  failure recall / gate matrix (§14.0.1), static expected-output
  contract fixtures (§3.2.1,
  §4.1.1, §7.3, §7.4), human decision overlay (§6.0.2), and runtime inventory
  expectations against those fixtures;
- implement the blocking package, import, registry, schema-field, LOC, writer,
  and wheel-resource ratchets from Section 15.1 as **static absence/ceiling
  assertions only** — actual package build, resource loading, and legacy
  reader belong to S1;
- freeze byte-preservation and read-only compatibility fixtures for old
  records — actual legacy reader belongs to S1; real old-store cutover
  and stopping old production writers belong to S7;
- S0 keeps old records byte-identical and testable through a static
  compatibility fixture contract; the read-only adapter is deferred to S1
  per U1;
- expected-output fixtures are reviewed structural oracles (FREEZE.json).
  They are NOT actual CLI behavior tests — those belong to S1. FREEZE.json
  is reviewed by hand; in case of conflict the active spec text wins.

### S1. Minimal Store And Read CLI

**S1 scope** (per U1 resolution): first production package with real CLI.
S1 creates the production `src/aitp/` package, built wheel, package
resources (`command_skills/`, templates, `profile.yaml`), read-only
legacy reader, and real CLI subprocess/runtime acceptance.

- implement root/topic discovery (`aitp admin init`, `aitp admin bind`,
  `aitp admin doctor`, `aitp admin inventory`), path resolution, `enter`,
  `search`, and `show` in the clean `src/aitp/` package;
- build and ship the normative `using-aitp` Skill and all command Skills as
  version-matched resources in the same distribution;
- implement the read-only legacy reader;
- prove direct filesystem fallback with no index (path + `rg` + Git must
  suffice for all S1 operations);
- real CLI subprocess acceptance: validate JSON envelope (§4.1.1), error
  codes (§7.3), workspace states (§7.4), `not_available_in_stage` for
  unimplemented commands;
- any command not yet implemented (e.g. `research`, `literature`,
  `knowledge`, `skill`, `write`, `checkpoint`, `closeout`, `audit`) must
  return the error code `not_available_in_stage` with the expected release
  stage — never a silent no-op or fabricated result.

### S2. Workspaces, Audit, And Recording

- implement command workspace creation and guide rendering;
- implement checkpoint, closeout, deterministic profiles, staging, exact diff,
  human review binding, serialized Git commit, readback, and recovery;
- implement the canonical writer behavioral contract from §14.0.2;
- prove that Agents author visible bytes and the CLI performs no hidden semantic
  rewrite;
- S2 does NOT pull forward the complete research/literature/code/run profiles
  from S3. Research-mode guides and literature intake/extraction remain S3.

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
    production surface;
19. `enter` deterministically shows Route `context_refs`, `prior_attempt_refs`,
    `known_failure_refs`, and `blocking_assessment_refs`; a new succeeded Run
    does not hide a prior failure;
20. the content envelope boundaries in §6.0.1 are respected: Episodes are not
    transcripts, Relations are not containment/mention, and natural Markdown
    notes/derivations are not per-sentence nodes;
21. the action→gate matrix in §14.0.1 is enforced; no profile or Skill version
    bump lowers the global gate;
22. every command returns distinct error codes from the frozen set in §7.3;
    unimplemented commands return `not_available_in_stage`;
23. workspace states in §7.4 are the only visible states; internal transient
    state is not normatively asserted;
24. the writer behavioral contract in §14.0.2 is satisfied: candidate
    approval, unrelated-dirty exclusion, stale/changed bytes fail, single
    visible write path, readback, and recovery;
25. contract tests verify behavior through CLI subprocess, filesystem, Git,
    and stdout JSON — not through import of internal Python modules or
    assertion of module count/names.

## 19. Design Closure

AITP 2.0 is not a second researcher running beside the host Agent. It is the
protocol that makes an AI researcher's local memory legible, durable,
searchable, reusable, and reviewable.

The host reasons. Commands select the phase. Command guides teach the phase.
Files carry the memory. Scientific Dreaming compiles physical understanding.
Skill distillation compiles repeatable procedure. Writing commands compile
research products. Human review controls the transitions that can change
scientific trust or install reusable behavior.
