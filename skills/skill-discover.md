---
name: skill-discover
description: Discover posture — find, evaluate, and register sources before reading.
trigger: posture == "discover"
---

# Discover Posture

## MANDATORY: AskUserQuestion rule

When you need to ask the user ANY question (clarification, scope, direction, missing info), you MUST:
1. Call `ToolSearch(query="select:AskUserQuestion", max_results=1)` to load the tool.
2. Call `AskUserQuestion(questions=[{...}])` with your question and options.
NEVER type questions as plain text. ALWAYS use the popup tool.

---

You are in the source discovery phase. Your job is to find and register all relevant materials before the deep reading begins.

## What this stage is about

Source discovery is not just "list some papers." It is a deliberate survey of what exists, what coverage you have, and what is missing. Sources go beyond literature:

- **Papers and preprints** — journal articles, arXiv preprints, conference proceedings
- **Datasets** — experimental data, simulation outputs, benchmark results
- **Code** — reference implementations, computational libraries, notebooks
- **Books and lectures** — textbook chapters, lecture notes, review articles
- **Experiments** — lab protocols, measurement setups, raw observations

## Required artifacts

- `L0/source_registry.md` — the master inventory with search methodology and coverage assessment
- `L0/sources/*.md` — individual source files (created by `aitp_register_source`)

## What to do now

1. Discuss with the researcher what kind of sources are relevant to this topic.
2. Search systematically using available tools (paper-search-mcp, arxiv-latex-mcp, knowledge-hub).
3. Register each source with `aitp_register_source`. Be specific about source_type.
4. Fill `L0/source_registry.md`:
   - **Search Methodology** — where you looked, what queries you used, what databases
   - **Source Inventory** — grouped by type (papers, datasets, code, etc.)
   - **Coverage Assessment** — what areas are well-covered, what is missing
   - **Gaps And Next Sources** — what still needs to be found
5. Set `source_count` to the actual number of registered sources.
6. Set `search_status` to one of: `initial`, `focused`, `comprehensive`, `exhausted`.

## Gate requirements

Before advancing to L1 (reading and framing), ALL of these must be true:

- `L0/source_registry.md` exists with all required headings filled
- `source_count` > 0 (at least one source registered)
- `search_status` is set (not empty)

## Exit condition

Move on to L1 only after the researcher confirms the source coverage is adequate.
Call `aitp_advance_to_l1` to transition.
