# AITP Research Graph

Status: design baseline
Base: `memory-core`
Development: `research-graph`

## Goal

Build two layers above single-Topic memory:

1. grounded knowledge management and lookup across multiple Topics;
2. provenance-preserving Skill distillation from one Topic.

Each Topic repository remains authoritative. The graph is a projection, not a new source of scientific truth.

## Boundaries

```text
Topic repositories ──> Research Graph ──> cross-Topic views
                              │
                              └─────────> reviewed Skill candidates
```

- Do not change the Topic, Entry, Note, relation, or evidence-pin contracts.
- Do not copy canonical artifacts into the graph.
- Inferred links remain proposals until explicitly saved.
- No required vector service, MCP server, hook, or daemon.
- A local SQLite/FTS index is allowed only as a disposable cache.
- Generated Skills are never published automatically.

## Workspace

```text
.aitp-graph/
├── GRAPH.toml
├── topics.toml
├── links/
├── candidates/<topic-id>/<skill-name>/
│   ├── SKILL.md
│   ├── provenance.json
│   └── evals.yaml
└── local/
    ├── roots.toml
    ├── graph.sqlite
    ├── graph.jsonl
    ├── snapshots/
    └── locks/
```

Versioned: portable Topic identities, explicit links, Skill candidates.
Local: absolute paths, derived indexes, snapshots, locks.

## Catalog

`topics.toml` contains portable identity:

```toml
[[topics]]
id = "route-d-plus-haldane-sphere"
title = "Route D+"
uri = "git+https://example/repository.git"
labels = ["fqhe", "vmc", "nqs"]
```

`local/roots.toml` maps Topic IDs to local paths. Sync rejects a path whose `.aitp/STORE.toml` has a different Topic ID.

## Graph model

Projected nodes:

```text
topic  entry  note  artifact  skill-candidate
```

Projected edges:

```text
contains  references  resolves  supersedes  compiled_into
```

Explicit cross-Topic edges:

```text
related_to  supports  contradicts  uses_method  same_object  extends
```

Every explicit edge records source, target, rationale, author, time, limitations, and pinned evidence.

## Index and lookup

`graph.sqlite` stores normalized nodes, edges, FTS text, source paths, locators, hashes, and sync times. It must rebuild deterministically from Topic stores and explicit links.

`graph.jsonl` is the portable fallback readable with `rg`. No vector index is required.

A query result must include:

- Topic and record IDs;
- exact source path and locator;
- summary and limitations;
- index freshness;
- stale or unavailable source warnings.

The query layer returns evidence-bearing matches, not an unsupported synthesized answer.

## Commands

Memory-core commands remain unchanged. This branch adds:

```text
aitp graph init
aitp graph topic add|remove|list
aitp graph sync
aitp graph enter
aitp graph query
aitp graph show
aitp graph link prepare|save

aitp distill prepare
aitp distill check
aitp distill publish
```

`graph sync` atomically replaces each Topic's projection. An unavailable Topic keeps its last snapshot marked stale instead of silently disappearing.

`graph enter` reports catalog health, unavailable roots, sync freshness, unresolved failures by Topic, recent links, and pending Skill candidates.

## Skill distillation

`distill prepare --topic <id> --name <name>` reads one Topic's:

- active Entries and reviewed Notes;
- pinned artifacts;
- decisions, constraints, and conventions;
- resolved and unresolved failures;
- repeated, evidenced procedures.

It produces:

- `SKILL.md`: reusable workflow and validity boundaries;
- `provenance.json`: each nontrivial instruction mapped to Entry, Note, and artifact evidence;
- `evals.yaml`: positive, negative, boundary, and failure cases.

It must not generalize a one-off result without evidence, hide contradictions, omit limitations, or use scratch/conversation history as authority.

`distill check` fails on missing provenance, unavailable records, unresolved template prompts, absent validity boundaries, failed evaluations, or destination collision.

`distill publish` requires explicit human approval and writes to a selected destination such as:

```text
<topic-repository>/.agents/skills/<skill-name>/
```

It never overwrites an existing Skill or edits research records.

## Agent entrypoints

```text
$aitp          single-Topic research work
$aitp-graph    multi-Topic lookup and linking
$aitp-distill  single-Topic Skill candidate workflow
```

Graph answers cite sources and disclose stale or unavailable Topics.

## Delivery stages

1. G0: schemas, fixtures, errors.
2. G1: catalog, sync, JSONL/SQLite, query.
3. G2: explicit links and neighborhood views.
4. G3: candidate generation, provenance, evaluations.
5. G4: approval-gated publication and plugin Skills.

## Acceptance

- Three fixture Topics query with exact provenance.
- Deleting and rebuilding the index gives the same projection.
- Missing Topic roots remain visible as stale.
- Suggested links cannot become durable without `link save`.
- Missing provenance blocks `distill check`.
- Publication requires explicit approval.
- All memory-core tests remain unchanged and pass.
