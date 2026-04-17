# L2 Backend Interface

Domain: Point (L2)
Authority: subordinate to AITP SPEC S3.
References: canonical/PROMOTION_POLICY.md, canonical/L2_COMPILER_PROTOCOL.md,
canonical/L2_STAGING_PROTOCOL.md, canonical/LAYER_MAP.md,
canonical/LAYER2_OBJECT_FAMILIES.md, canonical/L2_BACKEND_BRIDGE.md,
L2_CONSULTATION_PROTOCOL.md, INDEXING_RULES.md.

---

## 2.1. Role

L2 is the only layer whose outputs survive across topics and sessions. It stores
reusable typed knowledge objects that have been validated and promoted through
the promotion pipeline.

L2 is the active memory surface of the system. That includes reusable execution
memory, not only reusable knowledge statements.

## 2.2. Paired Backend Architecture

L2 maintains a paired backend:

### Human-Readable Backend (Brain Side)
- Topic-owned Markdown surfaces: research questions, dashboards, gap maps.
- The human researcher reads one Markdown-first journal.
- No JSON scraping required for human review.

### Typed Backend (Knowledge Network)
- JSON/JSONL canonical store: units, edges.
- Deterministic projections: compiled reports, Obsidian mirror.
- Typed retrieval for agents and scripts.

### Compatibility Rule
- Markdown and JSON are companions, not duplicates.
- Markdown carries narrative and judgment.
- JSON carries stable ids, statuses, triggers, and replay pointers.
- On machine-actionable field conflicts, JSON wins.
- On human-judgment field conflicts, Markdown wins.

### Paired Backend Audit
The implementation provides `paired_backend_audit()` and
`build_runtime_backend_bridges()` to audit the pairing status between
brain and TPKN backends, detecting drift and semantic separation issues.
NOT described in the original protocol.

## 2.3. Canonical Storage

### Protocol-Specified Layout
```
units/           # Typed knowledge objects (JSON)
edges/           # Typed graph relations (JSONL)
queues/          # Durable work routing
regressions/     # Topic regression manifests and pass logs
sources/         # Source manifests
```

Projection surfaces:
```
indexes/         # Deterministic retrieval surfaces
portal/          # Generated human-readable projection
```

### Implementation Layout (Actual)
The code uses a **family-based directory layout**:

```
canonical/
├── concepts/              # concept units
├── methods/               # method units
├── workflows/             # workflow units
├── bridges/               # bridge units
├── ...                    # other family-based dirs
├── edges.jsonl            # flat edge file (not edges/ directory)
├── index.jsonl            # primary index
├── staging/
│   ├── staging_index.jsonl
│   └── *.json + *.md      # paired staging entries
└── compiled/
    ├── workspace_memory_map.md
    ├── graph_report.md
    ├── knowledge_report.md
    ├── derived_navigation/  # per-unit navigation pages
    └── obsidian_l2/        # Obsidian-compatible mirror
```

The `queues/`, `regressions/`, and `sources/` directories do NOT exist at the
L2 canonical level. Queues and regressions are managed at the topic runtime
level. Sources are managed at the L0 level.

`CANONICAL_DIR_BY_TYPE` in `l2_graph.py` maps unit types to family directories.

## 2.4. Unit Families

### Protocol-Specified Families
- `concept`, `definition`, `theorem`, `lemma`, `equivalence`
- `proof_fragment`, `proof_obligation`, `proof_state`
- `derivation_step`, `dependency_graph_snapshot`
- `equation_context`, `theorem_family`, `definition_family`, `notation_family`
- `source_fusion_record`, `conflict_record`, `notation_map`
- `open_gap`, `regression_question`, `question_oracle`
- `followup_source_task`, `computation_spec`
- `codebase_source`, `code_module`, `code_function`, `code_algorithm`, `code_test`
- `method`, `model`, `warning`, `bridge`

### Implementation Unit Types (Actual)
The canonical-unit schema (`canonical-unit.schema.json`) allows these types:
- `concept`, `definition_card`, `theorem_card`, `lemma_card`
- `proof_fragment`, `proof_obligation`, `proof_state`
- `derivation_step`, `derivation_object`
- `equation_card`, `equivalence_map`, `notation_card`, `symbol_binding`
- `assumption_card`, `regime_card`, `caveat_card`, `warning_note`
- `example_card`, `method`, `bridge`, `workflow`
- `gap_record`, `computation_spec`
- `open_physics_index_entry`, `formalization_candidate`

### Vocabulary Mismatches
| Protocol | Code/Schema |
|----------|-------------|
| `definition` | `definition_card` |
| `theorem` | `theorem_card` |
| `notation_map` | `notation_card`, `symbol_binding` |
| `equivalence` | `equivalence_map` |
| `warning` | `warning_note` |
| `example` | `example_card` |
| `open_gap` | `gap_record` |

### Unit Backbone

Protocol-specified backbone fields:
`id, type, title, summary, domain, tags, aliases, assumptions, regime, scope,
dependencies, related_units, source_anchors, formalization_status,
validation_status, maturity, created_at, updated_at`

Implementation schema uses `unit_type` (not `type`). Several backbone fields
are missing from the schema:
- `aliases` — not in schema,
- `source_anchors` — covered by `provenance.source_ids`,
- `formalization_status` — not in schema,
- `validation_status` — replaced by `topic_completion_status`,
- `domain` (top-level) — nested inside `regime.domain`.

The schema includes many fields NOT in the protocol backbone:
- `origin_topic_refs`, `origin_run_refs`, `validation_receipts`, `reuse_receipts`
- `related_consultation_refs`, `applicable_topics`, `failed_topics`, `regime_notes`
- `provenance.backend_refs`
- `promotion.coverage_status`, `promotion.consensus_status`, `promotion.regression_gate_status`
- `promotion.supporting_regression_question_ids`, `promotion.supporting_oracle_ids`
- `promotion.promotion_blockers`, `promotion.blocking_reasons`
- `promotion.followup_gap_ids`, `promotion.split_clearance_status`

## 2.5. Edge Layer

### Protocol-Specified Relations (24 types)

Semantic: `depends_on, defines, uses, explains, motivates, specializes,
generalizes, contrasts_with, derived_from, supports, warned_by, bridges_to,
formalizes_toward, anchored_in_source`

Workflow: `tests, oracles, blocked_by, resolves, routes_to`

Code-theory: `implements, numerical_instance_of, assumes, tested_by`

### Implementation Edge Relations (Actual)
The edge schema (`edge.schema.json`) allows these relation types:
- `depends_on`, `supports`, `contradicts`, `specializes`, `generalizes`
- `derived_from`, `bridged_to`, `warned_by`, `validated_by`, `applies_in_regime`
- `uses_method`

### Vocabulary Mismatches
| Protocol | Schema |
|----------|--------|
| `bridges_to` | `bridged_to` |
| `tested_by` | `validated_by` |
| (not in protocol) | `contradicts` |
| (not in protocol) | `uses_method` |
| (not in protocol) | `applies_in_regime` |

Missing from schema entirely: `defines`, `uses`, `explains`, `motivates`,
`contrasts_with`, `formalizes_toward`, `anchored_in_source`, all workflow
relations, all code-theory relations.

## 2.6. Promotion Policy

L2 writes require the promotion pipeline (see SPEC S8):
1. Candidate in L3.
2. Validated through L4.
3. Integration complete, human not objected.
4. Human explicitly approved.

Auto-promotion may advance to L2_auto if all criteria are met and the
topic's trust boundary permits it. See `promotion_pipeline.md` P4 for
auto-promotion details.

The L2 staging modules (`l2_staging.py`) accept writes without checking
promotion gate status directly. The promotion pipeline enforcement is
handled by the candidate promotion support module separately.

See: `canonical/PROMOTION_POLICY.md`.

## 2.7. Staging and Compilation

Before promotion, candidates go through staging:
- `canonical/L2_STAGING_PROTOCOL.md` — staging before canonical promotion.
- `canonical/L2_COMPILER_PROTOCOL.md` — knowledge graph compilation.

### Staging Entry
Each staging entry is stored as paired JSON + Markdown:
- `{entry_id}.json` — typed staging data,
- `{entry_id}.md` — human-readable staging surface.

Staging entry statuses: `staged`, `reviewed`, `dismissed` (in code) vs.
`staged`, `promoted`, `rejected` (in schema). Internal inconsistency between
code constants and schema enum.

### Compilation Pipeline
The `l2_compiler.py` provides:
- **Workspace knowledge report** — change tracking with added/updated/unchanged/removed
  rows, contradiction watch, provisional row tracking.
- **Topic L2 corpus baseline** — topic-local corpus baselines with source anchor
  resolution, entry graph analysis, hub detection, isolation detection.
- **Obsidian L2 mirror** — full Obsidian-compatible Markdown mirror with family
  shelves, profile shelves, topic shelves.
- **Change fingerprinting** — SHA-1 hashing for change detection between runs.
- **Derived navigation pages** — per-unit navigation with outgoing/incoming relations.

These compilation features are NOT described in the original protocol.

## 2.8. Consultation

L2 consultation allows L3 work to query the trusted knowledge store:
- `L2_CONSULTATION_PROTOCOL.md` — consultation rules and obligations.
- Implemented via `consult_canonical_l2` in `l2_graph.py` with retrieval
  profiles, graph traversal, and staging cross-reference.
- When consultation materially changes terminology, candidate shape, or
  validation route, the `non_trivial_consultation` trigger should fire.
  **NOT YET IMPLEMENTED** as a trigger mechanism.

## 2.9. Paired Backend Maintenance

When the typed backend and human-readable backend diverge:
- `canonical/L2_PAIRED_BACKEND_MAINTENANCE_PROTOCOL.md` governs reconciliation.
- Canonical JSON remains the machine-facing authority.
- Portal Markdown remains the human-facing projection.

### Workspace Hygiene Report
The implementation provides `build_workspace_hygiene_report()` which detects:
- stale summaries,
- missing bridges,
- contradictions,
- orphaned units,
- weakly connected units.

NOT described in the original protocol.

## 2.10. Indexing and Retrieval

### Protocol-Specified Indexes
- `indexes/unit_index.jsonl`
- `indexes/edge_index.jsonl`
- `indexes/source_anchor_index.jsonl`
- `indexes/symbol_index.jsonl`
- `indexes/formalization_index.jsonl`
- `indexes/domain_index.json`
- `indexes/gap_index.jsonl`
- `indexes/followup_task_index.jsonl`
- `indexes/queue_index.jsonl`
- `indexes/regression_suite_index.jsonl`
- `indexes/regression_run_index.jsonl`

### Implementation Indexes (Actual)
The code generates:
- `canonical/index.jsonl` — primary unit index,
- `canonical/staging/staging_index.jsonl` — staging entry index.

The named index files at `indexes/` do NOT currently exist in the L2 backend.
The `indexes/` directory is used by the knowledge-hub portal at the research
level, not the L2 canonical level.

## 2.11. Implementation Status

### Currently implemented
- Paired backend architecture with audit and drift detection.
- Family-based canonical storage with JSON schema validation.
- Edge layer with 11 relation types (subset of protocol's 24).
- Staging with paired JSON + Markdown entries and manifest.
- Compilation pipeline (knowledge report, corpus baseline, Obsidian mirror).
- Change fingerprinting for incremental updates.
- Derived navigation pages.
- Workspace hygiene report.
- Consultation with retrieval profiles and graph traversal.
- Source anchor resolution for staging entries.

### Not yet implemented
- Protocol-specified directory layout (queues/, regressions/, sources/ at L2 level).
- Full 24-type edge relation vocabulary (only 11 implemented).
- Missing backbone fields: `aliases`, `formalization_status`, `source_anchors` as top-level.
- All workflow edge relations (tests, oracles, blocked_by, resolves, routes_to).
- All code-theory edge relations (implements, numerical_instance_of, assumes, tested_by).
- Non-trivial consultation trigger mechanism.
- Named index files at protocol-specified paths.
- Staging entry status vocabulary alignment (code vs schema inconsistency).

## 2.12. What L2 Should Not Do

- Accept writes without promotion gate (except through staging).
- Auto-promote high-impact claims without human approval.
- Replace source traces with compiled summaries.
- Silently merge evidence levels.
- Treat coverage as a substitute for validation.
