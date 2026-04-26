# L1 Intake Protocol

Domain: Point (L1)
Authority: subordinate to AITP SPEC S3.
References: L0_SOURCE_LAYER.md, intake/L1_VAULT_PROTOCOL.md,
intake/ARXIV_FIRST_SOURCE_INTAKE.md, research-question.schema.json.

---

## 1.1. Role

L1 is the provisional source-analysis and provenance layer. It builds
structured, explicit models from L0 sources WITHOUT promoting them to trusted
knowledge.

Every claim in L1 is marked "provisional" via the blanket authority level
`non_authoritative_compiled_l1`. Individual claims carry evidence sentence
anchors for traceability.

## 1.2. Intake Workflow

When sources are registered in L0, L1 receives them and:

1. **Assumption extraction** — structural, not keyword-based. Now captured
   with sub-categorization in `convention_snapshot.md` under
   `## Categorized Assumptions`:
   - **Mathematical**: topology, dimensionality, symmetry group, completeness,
     convergence properties.
   - **Physical**: energy regime, coupling limits, boundary conditions,
     equilibrium vs non-equilibrium, thermodynamic limit.
   - **Notational**: sign conventions, normalization choices, index ranges,
     Fourier convention (factors of 2π).
   
   Each category has different failure modes — a violated mathematical
   assumption is a hard error; a violated physical assumption may only
   change the regime of validity.

2. **Reading depth tracking** — each source gets a depth grade:
   - `skim` — title, abstract, key results only (default),
   - `full_read` — full text with derivation checking,
   - `multi_pass` — cross-checked against other sources for contradictions.

   Note: the code uses `skim`/`full_read` rather than `scan`/`close_read`.
   Any string is accepted; these are the conventional values.

3. **Contradiction detection** — flag when two sources:
   - use the same term for different concepts,
   - make incompatible assumptions under the same scope,
   - give conflicting results that cannot be reconciled within stated regimes.

   Implementation: `contradiction_candidates` structure captures detected
   contradictions, and `notation_tension_candidates` captures notation
   conflicts between sources.

4. **Notation regime identification** — when sources use different notation
   for the same objects, L1 records:
   - which notation each source uses (per-source notation rows),
   - translation maps between conventions (notation tension candidates),
   - canonical notation selection: NOT YET IMPLEMENTED. Currently only
     records per-source notation; no canonical selection mechanism.

5. **Derivation anchor capture** — IMPLEMENTED. The `derivation_anchor_map.md`
   artifact now captures:
   - **Section pointer** — exact source location where the derivation lives.
   - **Derivation type** — `derived_in_full`, `stated_with_sketch`, or
     `handwaved` ("it can be shown that...").
   - **Depends on** — prior equations or results within the source.
   - **Feeds into** — downstream results that depend on it.
   - **Assumptions used** — categorized as mathematical/physical/notational.
   - **Dependency graph** — equation dependency graph across all sources.
   - **Missing steps** — skipped or unclear steps that L3 needs to fill in.
   - **Candidate starting points** — strongest entry points for L3 derivation.

   Gate requires `starting_anchors` (non-empty) and `anchor_count` (> 0).
   The detailed derivation body still belongs in L3; L1 records the map.

6. **Method specificity tracking** — IMPLEMENTED (not in original protocol).
   Tracks `method_family` and `specificity_tier` per source, classifying
   methods by their computational or analytical approach.

7. **Concept graph** — IMPLEMENTED (not in original protocol). Maintains a
   concept graph with nodes, edges, hyperedges, communities, and god-nodes
   to capture the conceptual structure of the source material.

8. **Source intelligence** — IMPLEMENTED (not in original protocol). Enriches
   source records with citation edges, neighbor detection, cross-topic
   matching, fidelity tiers, and relevance tiers.

9. **Evidence sentence anchoring** — IMPLEMENTED (not in original protocol).
   Every anchor row carries `evidence_sentence_ids` and `evidence_excerpt`
   fields for sentence-level traceability to source material.

10. **Figure & diagram extraction** — IMPLEMENTED. The section intake template
    now includes a `## Figures & Diagrams` heading and optional `figure_refs`
    frontmatter. For each figure that conveys physics content, the agent records:
    - Figure number and label from source.
    - What it shows (phase diagram, Feynman diagram, band structure, energy
      landscape, schematic, data plot, etc.).
    - Which equations or concepts it illustrates.
    - Whether it is essential for understanding the argument.
    - Link to L2 diagram node if already created.

    This bridges L1 reading to L2 diagram nodes, enabling the L2 knowledge
    graph to accumulate figure-based evidence alongside concept and
    derivation nodes.

## 1.3. Three-Layer Vault

Each topic may materialize an L1 vault:

```
intake/topics/<topic_slug>/vault/
├── raw/       # Immutable source pointers (manifests with read_only flag)
├── wiki/      # Human-browsable compiled L1 surface
└── output/    # Derived query products
```

### Raw Layer
- Contains manifests with source metadata (title, summary, source_type,
  canonical_source_id, locator fields) marked `read_only: True`.
- Uses manifests and pointers, not separate writable knowledge copies.

### Wiki Layer
- Human-browsable compiled surface.
- Lowercase filenames, frontmatter, Obsidian-compatible wikilinks.
- Page types: `home`, `source-intake`, `source-bridge`, `open-questions`,
  `runtime-bridge`, `concept-graph/index`.
  - `source-bridge` — unified source anchor index with L0 references.
  - `concept-graph/index` — concept graph visualization page.

### Output Layer
- Derived query products downstream of raw/wiki.
- Summaries, active read paths, question-state digests.

### Flowback Rule
- Output may flow back to wiki only with an explicit receipt naming:
  source artifact, target wiki page, reason, applied status.
- Implementation: `flowback.jsonl` with structured entries containing
  `target_page`, `source_output_path`, `status`, `reason`, `content_preview`.
- Silent wiki rewrites without receipts are not acceptable.

### Compatibility Projection
- All vault writes go through `compatibility_projection_path` for dual-path
  support, maintaining both `runtime/topics/` and `topics/runtime/` layouts.

## 1.4. Source Intake Helpers

For arXiv-backed theory papers:
- Default opening priority: TeX source > HTML > PDF > summaries.
- Helper: `source-layer/scripts/register_arxiv_source.py`.
- Policy: `intake/ARXIV_FIRST_SOURCE_INTAKE.md`.
- `source_intelligence.py` provides `ARXIV_RE` pattern for citation extraction.

For natural-language discovery:
- Helper: `source-layer/scripts/discover_and_register.py`.
- Search stays external to L0; evaluation stays explicit and durable.

## 1.5. Research Question Contract

Every L1 session should produce or update a research question contract.

Current implementation reads these fields: `question`, `status`,
`research_mode`, `l1_source_intake`, `open_ambiguities`, `uncertainty_markers`.

Recommended fields (not all enforced yet):
- scoped question,
- scope boundaries,
- explicit assumptions,
- target claims,
- forbidden proxies (what NOT to use as evidence),
- deliverables,
- acceptance criteria.

Schema: `schemas/research-question.schema.json`.

The research contract is passed as `research_contract: dict[str, Any]` with
no schema validation currently enforced.

## 1.6. Compatibility Rule

L1 vault surfaces must link existing runtime surfaces:
- `runtime/topics/<slug>/research_question.contract.json|md`,
- `runtime/topics/<slug>/control_note.md`,
- `runtime/topics/<slug>/operator_console.md`.

The vault contextualizes them. It does not replace them.

Implementation: `runtime-bridge` vault page links runtime surfaces.
A separate `source-bridge` page provides a unified source anchor index.

## 1.7. Authority Rule

L1 is NOT canonical L2 memory. The `authority_level` field is always set to
`non_authoritative_compiled_l1`. It must not:
- bypass L0 recovery,
- bypass L4 validation,
- silently promote compiled wiki notes into reusable L2 truth.

Note: as of v4.0, `aitp_request_promotion` enforces a runtime guard:
the topic must be at L4 or L2 stage; promotion is blocked if the topic
is still at L0/L1/L3. This prevents bypassing L4 validation.

## 1.8. Implementation Status

### Currently implemented
- Assumption extraction with sub-categorization (mathematical, physical,
  notational) in `convention_snapshot.md`.
- Reading depth tracking (`skim`/`full_read`/`multi_pass`).
- Contradiction detection and notation tension detection, including
  internal inconsistencies and weakest-step flagging.
- Notation regime recording with canonical notation selection
  (`## Canonical Notation` in convention snapshot).
- Derivation anchor capture with dependency graph, derivation types, and
  per-anchor assumption tracking (`derivation_anchor_map.md`).
- Figure and diagram extraction with bridge to L2 diagram nodes.
- Regime and validity condition tracking in section intake notes.
- Argument structure and role classification (physical_principle,
  algebraic_identity, assumption, approximation, conjecture).
- Per-claim authority level marking (source_grounded, provisional, tentative)
  in section intake `## Physical Claims`.
- Competing hypotheses gate-check in question contract.
- Question contract content guardrails: forbidden proxies, deliverables,
  acceptance criteria headings in template.
- Convention backflow mechanism (`## L3 Discoveries` in convention snapshot).
- Runtime guard: `aitp_request_promotion` blocks promotion if topic stage
  is not L4 or L2 (prevents L1→L2 bypass).
- Three-layer vault with manifest, schema, and flowback system.
- Concept graph (nodes, edges, hyperedges, communities, god-nodes).
- Source intelligence (citations, neighbors, fidelity, relevance).
- Method specificity tracking.
- Evidence sentence anchoring.
- Source anchor index and bridge page.
- Compatibility projection (dual-path writes).
- Obsidian concept graph export.

### Not yet implemented
- Research question contract JSON Schema validation (schema exists but
  not enforced at gate level; gate relies on frontmatter + heading checks).

## 1.9. What L1 Should Not Do

- Decide canonical promotion.
- Store provisional reasoning as if it were source identity.
- Own the detailed derivation body for the topic.
- Replace L3 candidate formation.
- Replace L4 adjudication.
- Substitute summary plausibility for actual derivation checking.
