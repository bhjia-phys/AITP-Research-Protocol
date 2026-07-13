---
title: AITP M0.5 Complexity Reduction Design
date: 2026-07-11
status: approved-soft-deprecation-one-release
scope: v5 capabilities, record families, writers, imports, compatibility shards, legacy isolation, and context quality
---

# AITP M0.5 Complexity Reduction Design

## 1. Decision To Make

M0 established a safe repository, indexed retrieval, bounded context, explicit
capability registry, v5-only production boundary, and an isolated release lane.
It did not prove that all existing v5 abstractions should survive.

M0.5 is therefore a mandatory reduction review before M1-M6. It freezes broad
feature expansion and asks one question for every existing public capability,
record family, writer, import dependency, and compatibility facade:

> Which observed theoretical-physics research event or host obligation requires
> this surface, and what is the smallest contract that preserves that outcome?

The approved compatibility decision is one release of soft deprecation:

1. shrink Codex default/compact exposure immediately;
2. keep full-surface and CLI forwarding shims for one release with explicit
   lifecycle metadata and warnings;
3. run the required real verticals;
4. delete only the surfaces that remain unneeded after those verticals.

Immediate deletion may break un-inventoried scripts. Audit-only freeze leaves
the default system needlessly complex. The user approved the one-release soft
deprecation policy on 2026-07-12; CR1 may now reduce default exposure while
preserving full/CLI forwarding and observable compatibility metadata.

## 2. Evidence Baseline

All measurements below come from the final M0 staged candidate and the fresh
generation 7 real-store index. The optional Harness Feedback extension in the
dirty primary worktree is deliberately excluded from core counts.

### 2.1 Capability And Host Surface

| Measure | M0.5 baseline |
|---|---:|
| Core capabilities / MCP wrappers | 225 / 225 |
| Read-only / runtime-write / kernel-write | 119 / 34 / 72 |
| Full / compact visibility | 209 / 16 |
| Capabilities without CLI route | 19 |
| Runtime bridge targets | 43 |
| Public surfaces | 197 |
| Full MCP schema bytes | 92,953 |
| Compact MCP schema bytes | 7,331 |

The M0 baseline compact surface contained eight Codex facade tools, two
research-policy/trust tools, and six installation or bridge-maintenance tools.
Removing only those six maintenance tools from default exposure yields ten
tools and 5,945 schema bytes without deleting any full-surface capability.

CR1 implemented that reduction on 2026-07-12. The cold compact probe now
measures 10 tools, 5,945 schema bytes, 108 loaded `brain.v5` modules, and three
explicitly allowed schema-v1/legacy-read modules. It does not load
`brain.v5.mcp_tools`. Full MCP and the six existing CLI routes remain available
for the one-release compatibility window, and old compact calls receive a
structured migration error. An absent `AITP_MCP_SURFACE` preserves the existing
full default; an explicitly blank or unknown value fails closed to compact.

The fresh canonical index contains exact text mentions of only 11 registered
MCP names. A broader Theoretical-Physics workspace scan found 27 `aitp_v5_*`
spellings, with two inaccessible temporary paths. These counts do not prove
that unmentioned tools are unused; they prove that capability count cannot be
used as a proxy for research value. A compatibility inventory is required
before deletion.

### 2.2 Record Families And Real Data

| Measure | M0.5 baseline |
|---|---:|
| Registered families | 46 |
| Families present in generation 7 | 34 |
| Families with zero real records | 12 |
| Families without a record class | 5 |
| Indexed real records | 9,772 |
| Malformed indexed records | 0 |

Zero-record families:

- `active_claim_rebind_audits`
- `attempts`
- `benchmarks`
- `code_workspaces`
- `failure_mode_reviews`
- `ideas`
- `intents`
- `monitor_snapshots`
- `outputs`
- `promotion_packets`
- `questions`
- `skill_patch_proposals`

The five families without a record class are `attempts`, `ideas`, `intents`,
`legacy_source_reconstruction_repairs`, and `outputs`. Their registry metadata
currently labels them `unimplemented_layout`; they are hypotheses, not proven
runtime requirements.

The real store has 2,356 `memory_entries`, all marked `legacy_seed` and all
requiring `legacy_migration_review_required`. They represent only 248 unique
`source_packet_id` values: 124 packets were copied three times and 124 were
copied sixteen times, producing 2,108 duplicate rows. M0.5 must not rewrite or
delete those canonical records. It may provide a derived deduplicated migration
view and an explicit review/migration plan.

### 2.3 Code And Import Complexity

| Measure | M0.5 baseline |
|---|---:|
| `brain/v5` Python files | 485 |
| Top-level modules | 378 |
| Python lines | 87,966 |
| `legacy_*` top-level modules | 62 |
| `mcp_*` / `cli_*` top-level modules | 33 / 33 |
| `*_contracts.py` top-level modules | 110 |
| Dataclasses / defining modules | 114 / 44 |
| Shard-loading facades | 37 |
| Numbered compatibility shards / lines | 94 / 29,580 |

Physical files now satisfy the 500-line architecture test, but logical
responsibilities remain large. The largest facade-plus-shard totals are:

| Logical module | Lines |
|---|---:|
| `mcp_tools.py` | 2,434 |
| `process_graph.py` | 2,205 |
| `codex_facade.py` | 2,010 |
| `cli.py` | 1,621 |
| `curated_rag_corpus.py` | 1,383 |
| `claim_relation_map.py` | 1,304 |
| `recording_navigator.py` | 1,167 |
| `lightweight_record_router.py` | 1,093 |
| `closeout_completeness.py` | 1,002 |

Importing `codex_facade` loads 102 `brain.v5` modules and three legacy-named modules.
Importing `native_mcp`, even for the compact surface, loads 236 modules and 40
legacy-named modules because all wrappers are imported before visibility filtering.
Boot latency is currently acceptable, so this is primarily an ownership and
maintenance defect, not a reason for a speculative rewrite.

The M0.5 writer scanner makes this boundary visible rather than hiding its own
cost: a fresh current compact import loads 237 `brain.v5` modules and 41
legacy-named modules, including both `runtime_audit` and `writer_scan`.
Maintenance audit code must therefore be lazy-loaded in CR1; merely removing
its tool names from compact visibility is insufficient.

### 2.4 Write Ownership

The current static audit recognizes 111 low-level helper call sites in 61 files
and 85 functions:

- 55 `write_record` calls;
- 30 `write_md` calls;
- 26 `write_text_atomic` calls.

Thirty-six calls in 25 files expose a literal registry-family target. Semantic
review of all 111 recognized rows classifies 47 as canonical record/repository,
21 as derived index/surface, 13 as host/runtime, 28 as migration/legacy
compatibility, and two as shared storage primitives. Only five modules
instantiate `RecordRepository`, and four of those are read paths.
`references.py` is the only clear canonical writer consumer.

This 111-row count is a lower bound. The scanner does not yet recognize direct
`Path.write_text`, append/write `Path.open`, JSONL helpers, copy/rename calls,
SQLite mutations, or all source trees. M0.5 may not claim repository-wide
writer closure until the scan policy covers those mechanisms or explicitly
excludes them with evidence.

A conservative follow-up scanner now finds 164 additional mutation candidates
across 63 production files, including 57 calls in 25 `brain/v5` files. The remainder
is split across legacy `brain` (40), scripts (59), host hooks (7), and a plugin
launcher (1). These counts are candidate call sites, not 164 additional
canonical writers; target-path and role classification remains mandatory.

The accepted implementation uses bounded rather than universal static closure.
`bounded_coverage_complete` means every Python file under the declared
production source prefixes was enumerated and parsed, and every recognized
helper/direct-mutation row is present for classification. `coverage_complete`
remains false because reflection, aliases not resolved by the AST scanner,
non-literal database operations, unrecognized helpers, and native extensions
are explicitly outside that proof boundary. No caller may translate bounded
closure into a repository-wide absence or no-bypass claim.

Therefore the M0 architectural invariant, "all canonical writes pass through
one safe repository," is not yet true for the whole runtime. This is the first
implementation priority after design approval. It must be completed one real
vertical at a time, not through a blind rewrite of the 111 currently recognized
calls.

### 2.5 Context Quality

Fresh generation 6/7 probes show that bounded context is fast and coverage is
honest, but selection is not yet optimal:

- LibRPA/QSGW: about 0.72 seconds, 3,889 bytes, 460 estimated tokens, 80 refs,
  12 candidate summaries, and explicit truncation;
- quantum gravity: about 0.68 seconds, 3,688 bytes, 358 estimated tokens, 37
  refs, 12 summaries, and no truncation;
- the LibRPA session exposes the legacy marker
  `unresolved_exact_ref:research_route:curated_legacy_migration` rather than
  hiding it.

Retrieval already computes relevance ordering. `context_compiler` then builds
candidate summaries and re-sorts them by failure/claim/process family and
record ref, discarding retrieval score inside each group. It also reports
`truncated` but does not expose an explicit `not_shown` count/status. M0.5 should
preserve retrieval rank, add diversity/status gates, and expose `not_shown`.
It should not add another summarization or agent subsystem.

## 3. Required Classification Model

Every capability and family must receive exactly one lifecycle classification:

| Classification | Meaning | Default visibility |
|---|---|---|
| `core` | Required by every real research session or trust boundary. | compact only when needed at turn time |
| `vertical_extension` | Required by at least one accepted research vertical. | full/discoverable, loaded on demand |
| `maintenance` | Installation, diagnostics, release, or host administration. | never compact by default |
| `migration` | Legacy read, audit, reconstruction, or one-time migration. | explicit full/CLI migration lane only |
| `soft_deprecated` | Forwarding compatibility with no current vertical owner. | hidden from default; warning on explicit use |

Classification evidence must include:

- concrete research/host event;
- caller or compatibility consumer;
- state effect and trust boundary;
- canonical or derived write ownership;
- exact read/coverage behavior;
- vertical acceptance test or explicit migration fixture;
- removal condition and compatibility window.

Name matching and repository text mentions are discovery evidence only. They
cannot by themselves classify a capability as unused.

## 4. Record-Family Policy

No new family may be added during M0.5. Existing families follow these rules:

1. A populated family remains readable and exact-expandable.
2. A zero-record family is frozen until a vertical creates a valid event that
   cannot be represented by an existing family.
3. An `unimplemented_layout` family must either gain a concrete class and one
   vertical owner or become a soft-deprecated compatibility alias.
4. Family aliases may preserve old refs, but aliases are not independent truth
   stores.
5. Legacy duplicate memory remains canonical history; deduplication is a
   derived migration projection with no trust effect.
6. Cross-topic knowledge, workflow reuse, and topic-local trust remain separate
   even if they share storage machinery.

## 5. Default Surface Design

The proposed Codex default remains facade-first:

- `codex_autoroute`
- `codex_enter`
- `codex_expand`
- `codex_recording_step`
- `codex_record_apply`
- `codex_literature_step`
- `codex_closeout`
- `codex_tool_catalog`
- `evaluate_pre_tool_policy`
- `preflight_trust_update`

The six hook/bridge installation and audit tools move to the full maintenance
surface. This changes visibility, not capability availability. Exact expansion
and tool catalog discovery remain the path to non-default tools.

Caller audit found no canonical-topic mention of any of the six. Three have no
production-code reference outside declarations; the other three are consumed
only by bridge/final-readiness maintenance code. One historical workspace note
mentions the bridge-target manifest. This is sufficient evidence for a
soft-deprecated compact-visibility change, not for deletion or for assuming
that no external host caller exists.

Target budgets after approval:

- compact tools: at most 10;
- compact schema: at most 6,000 bytes;
- compact native-MCP imports: at most 120 `brain.v5` modules and at most five
  legacy modules;
- no installation or migration tool in compact visibility;
- no full tool body or topic memory injected into conversation context.

## 6. Canonical Writer Convergence

Writer migration uses an in-place strangler strategy:

1. classify each writer reported by the expanded scan policy and keep shared
   storage primitives separate from semantic writer ownership;
2. choose the next real vertical;
3. route only that vertical's canonical writes through `RecordRepository`;
4. add collision, revision, actor, ref, and trust-neutrality tests;
5. remove the bypass only after the vertical passes;
6. repeat until no canonical bypass remains.

Derived writers receive an explicit derived-output root and cannot share a
canonical family path. Host-install writers remain separately permissioned.
No large "repository adapter framework" is introduced unless two completed
verticals demonstrate the same irreducible pattern.

## 7. Legacy And Compatibility Isolation

Legacy support remains limited to read, audit, migration, schema-v1
materialization, and default write blocking. M0.5 must:

- prevent compact `native_mcp` from importing unrelated legacy modules;
- group migration tools behind an explicit migration catalog/lane;
- keep legacy route markers visible as compatibility diagnostics;
- preserve old exact refs through aliases where lossless;
- refuse to repair candidate/stage/promotion/legacy-graph writes for archived
  E2E compatibility;
- keep `legacy-write-archive` non-release and non-CI.

## 8. Compatibility Shards

Numbered shards are temporary extraction scaffolding, not the final domain
architecture. M0.5 does not rewrite all 94 shards. It applies these rules:

1. no new numbered shard unless required to keep an existing public import
   stable during one bounded extraction;
2. when a real vertical touches a large logical module, extract one named
   responsibility module with explicit imports and tests;
3. measure logical facade-plus-shard size, not only physical file size;
4. prioritize `mcp_tools`, `codex_facade`, writer-owning modules, and context
   selection before report-only modules;
5. preserve public import shims for one compatibility release.

## 9. Vertical-First Sequence

After classification and default-surface approval, implementation proceeds by
user outcome rather than by mechanically completing M1-M5:

1. LibRPA/HPC and code modification;
2. QFT/quantum-gravity literature and derivation;
3. new software onboarding from no recipe;
4. multi-topic isolation and reviewed reuse.

Each vertical must exercise recovery, exact expansion, recording, provenance,
validation, closeout, and the relevant knowledge or skill boundary. Only a
capability used by a passing vertical or a required compatibility fixture may
be promoted from hypothesis to retained architecture.

## 10. Work Packages

### CR0: Classification And Freeze

- produce complete capability/family/writer classification manifests;
- expand the writer scan beyond the 111-helper-call lower bound and publish its
  source-tree/API coverage policy;
- add CI checks for unclassified additions and compact maintenance leakage;
- prohibit new families/capabilities without a vertical owner.

### CR1: Compact Surface Reduction

- move six maintenance tools out of compact visibility;
- lazy-load full and migration MCP catalogs;
- preserve full/CLI forwarding compatibility for one release.

### CR2: Context Selection Closure

- preserve retrieval score/order through candidate summary selection;
- add family/status diversity and explicit `not_shown` accounting;
- keep stale, partial, not-found, not-checked, and read-error distinctions.

Implemented on 2026-07-12 with additive rank/score fields, bounded deterministic
priority/family/status selection, final-pack omission accounting, and separate
stale/partial/not-found/not-checked/read-error/retrieval-truncation/render-
truncation diagnostics. The real-store probe also exposed a concurrent index
snapshot race; index publication now aborts before writing derived files when
the canonical state changes during the scan.

### CR3: Writer Convergence

- migrate the canonical writers required by the first vertical;
- classify all derived/host writers;
- expand one vertical at a time until canonical bypass count is zero.

### CR4: Legacy And Import Isolation

- remove unrelated legacy imports from compact native MCP;
- expose migration only through an explicit catalog/lane;
- retain schema-v1 reads and write guards.

### CR5: Vertical-Driven Pruning

- execute the four required verticals;
- collect compatibility use evidence;
- remove soft-deprecated surfaces only after the review window.

## 11. Acceptance

M0.5 is complete only when:

- every capability, family, and writer reported by the closed scan policy has
  exactly one reviewed classification;
- no new unowned capability/family enters the registry;
- compact exposure meets the ten-tool/6,000-byte/import budgets;
- no maintenance or migration tool appears in compact context;
- context exposes `not_shown` and preserves retrieval relevance/diversity;
- all canonical writers used by the first accepted vertical pass through
  `RecordRepository`, with a measured plan for the remainder;
- legacy writes remain blocked and archived E2E failures remain non-release;
- logical module complexity has a non-increasing budget;
- M1-M5 detailed plans are explicitly treated as candidate catalogs rather
  than mandatory implementation checklists;
- the selected compatibility policy is documented and approved.

## 12. Stop Conditions

Stop and return to design review if a proposed reduction:

- loses an exact canonical ref or hides a read error;
- rewrites real canonical records for cleanup;
- transfers trust through migration, RAG, summary, context, or skill output;
- removes a surface with an identified active caller and no forwarding path;
- adds a second runtime, ontology, repository framework, or generic agent loop;
- repairs archived L0-L4 writes to satisfy historical tests;
- cannot be justified by a real vertical or required compatibility fixture.

## 13. Compatibility Decision

**Decision:** Option 1 was explicitly approved by the user on 2026-07-12.

The reviewed options were:

1. **Soft deprecation for one release (recommended):** reduce default exposure,
   retain forwarding full/CLI shims, then prune after vertical acceptance.
2. **Immediate removal:** delete unowned surfaces during M0.5 and accept host or
   script breakage risk.
3. **Classification-only freeze:** complete CR0 and verticals before changing
   visibility or deleting anything.

During the compatibility release, the six maintenance tools leave compact but
remain callable through full MCP and CLI maintenance routes. Their compatibility
metadata must identify the retained route, review window, and removal condition.
No surface is deleted until vertical acceptance and caller evidence are reviewed.
