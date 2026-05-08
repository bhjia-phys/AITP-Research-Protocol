---
name: skill-frame
description: Frame posture — lock conventions, anchors, contradictions, and cross-source maps before derivation.
trigger: posture == "frame"
---

# Frame Posture

## MANDATORY: AskUserQuestion rule

When you need to ask the user ANY question (clarification, scope, direction, missing info), you MUST:
1. Call `ToolSearch(query="select:AskUserQuestion", max_results=1)` to load the tool.
2. Call `AskUserQuestion(questions=[{...}])` with your question and options.
NEVER type questions or options as plain text. ALWAYS use the popup tool.

---

You are preparing the topic for honest derivation. Your job: lock down conventions, map derivation anchors from sources, register contradictions, and build the cross-source equation map — BEFORE any L3 derivation begins.

## Step 0: Load domain context

Before framing, check if the topic has a domain manifest:

```
aitp_load_domain_manifest(topics_root, topic_slug)
```

If a manifest exists, its invariants, notation choices, and known parameters
constrain what you must lock down. Read the returned manifest fields and use
them when filling convention_snapshot.md.

## Step 1: Lock conventions (`L1/convention_snapshot.md`)

1. Read existing intake notes to find notational differences between sources:
   - Call `aitp_list_sources(topics_root, topic_slug)` to see all registered sources
   - For each source, scan `L1/intake/<source_id>/` for equations and notation
   - Use `aitp_query_l2_index(topics_root)` to check if L2 has canonical notation
     for this domain

2. Fill `L1/convention_snapshot.md` with these sections (write directly to the file):
   - `## Notation Choices` — one canonical notation per concept, justified
   - `## Unit Conventions` — natural units, energy units, length scales
   - `## Sign Conventions` — metric signature, Fourier sign, coupling sign
   - `## Categorized Assumptions` — mathematical, physical, notational
   - `## Canonical Notation` — translation table between source notations
   - `## Unresolved Tensions` — where sources disagree and you chose one

3. Discuss notation choices with the human via AskUserQuestion before locking.
   Present: "Source A uses <X>, Source B uses <Y>. I propose canonical <Z> because <reason>."

## Step 2: Map derivation anchors (`L1/derivation_anchor_map.md`)

1. For each core source, identify the key equations that serve as starting points:
   - Use intake notes in `L1/intake/<source_id>/` to find key equations
   - For each anchor: record source_file:line, equation LaTeX, derivation type

2. Use `aitp_list_steps(topics_root, topic_slug)` if derivation steps were already
   created during reading (e.g., from code_method lane function tracing).

3. Fill `L1/derivation_anchor_map.md`:
   - `## Source Anchors` — table with: Anchor ID, Source:File:Line, Equation, Type, Feeds Into
   - `## Dependency Graph` — how equations depend on each other across sources
   - `## Missing Steps` — gaps the L3 derivation must fill
   - `## Candidate Starting Points` — which anchors are the best entry points

4. Discuss anchors with the human: "These are the strongest starting points I found.
   Should we prioritize any particular anchor for L3?"

## Step 3: Register contradictions (`L1/contradiction_register.md`)

1. Compare sources systematically:
   - Check if two sources use the same symbol for different quantities
   - Check if two sources give different forms of the "same" equation
   - Check if approximations made in one source are violated in another

2. Fill `L1/contradiction_register.md`:
   - `## Unresolved Source Conflicts` — concrete disagreements between sources
   - `## Internal Inconsistencies` — places a single source contradicts itself
   - `## Regime Mismatches` — source A's regime doesn't overlap with source B's
   - `## Notation Collisions` — same symbol, different meanings
   - `## Blocking Status` — does any contradiction block L3 derivation?

3. Use `aitp_resolve_conflict(topics_root, topic_slug, conflict_id=...)` if you
   find contradictions that need programmatic resolution tracking.

4. If contradictions are blocking, offer to retreat to L0 for more sources:
   `aitp_retreat_to_l0(topics_root, topic_slug, reason="Blocking contradiction: ...")`.

## Step 4: Build cross-source map (`L1/source_cross_map.md`)

1. Trace key equations across sources:
   - When equation A in source X is the same as equation B in source Y, record it
   - When source X uses a result from source Y, record the dependency

2. Fill `L1/source_cross_map.md`:
   - `## Cross-Source Dependencies` — which source depends on which
   - `## Equation Lineage` — table: Equation, Origin Source, Also Appears In
   - `## Unresolved Cross-References` — references you couldn't verify

3. Use `aitp_find_cross_topic_bridges(topics_root, topic_slug)` to search for
   structural isomorphisms in L2 — a Green's function in your topic may match
   one from a different domain.

## Step 5: Verify framing completeness

Before advancing, run these checks:

1. `aitp_get_execution_brief(topics_root, topic_slug)` — check `gate_status`.
   If blocked, fix the listed `missing_requirements`.

2. Physicist check — load `skill-physicist-check`. Answer all four questions
   about the framing: L2 coverage, correspondence limits, anomalies, and
   what the human should verify.

3. Review `L1/convention_snapshot.md` `## L3 Discoveries` — if previous L3
   work produced feedback, integrate it into the main convention sections.

## Escape hatches

At any point:
- **Retreat to L0**: `aitp_retreat_to_l0(topics_root, topic_slug, reason="...")` —
  if sources are insufficient or contradictory beyond resolution
- **Query L2**: `aitp_query_l2(topics_root, query="...")` —
  check if L2 has relevant conventions, anchors, or resolution patterns
- **Switch lane**: `aitp_switch_lane(topics_root, topic_slug, new_lane="...")` —
  if the framing reveals the topic needs a different research lane

## Required artifacts

All artifacts MUST include `source_refs: [...]` in YAML frontmatter. The gate blocks
advancement without this field. Each entry must be a real L0 source slug.

- `L1/convention_snapshot.md` — with all headings filled, `source_refs` set, notation locked
- `L1/derivation_anchor_map.md` — with at least one anchor per core source, `source_refs` set
- `L1/contradiction_register.md` — with blocking status assessed, `source_refs` set
- `L1/source_cross_map.md` — with cross-source equation lineage, `source_refs` set

## Exit condition

Call `aitp_get_execution_brief(topics_root, topic_slug)`. When `gate_status` is
`ready`, advance to L3:

```
aitp_advance_to_l3(topics_root, topic_slug)
```

Do NOT advance while any of the four artifacts have placeholder-only content.
