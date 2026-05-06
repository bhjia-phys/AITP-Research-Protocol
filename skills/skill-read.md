---
name: skill-read
description: Read posture — build the source basis with mechanical TOC extraction before framing or derivation.
trigger: posture == "read"
---

# Read Posture

## MANDATORY: AskUserQuestion rule

When you need to ask the user ANY question (clarification, scope, direction, missing info), you MUST:
1. Call `ToolSearch(query="select:AskUserQuestion", max_results=1)` to load the tool.
2. Call `AskUserQuestion(questions=[{...}])` with your question and options.
NEVER type questions or options as plain text. ALWAYS use the popup tool.

---

You are building the topic's source-grounded basis with **mechanical completeness guarantees**.

## Lane Branch

### formal_theory lane: Paper reading (default)

Follow the Reading workflow below. Sources are papers with TOCs, sections, subsections.
Use arxiv-latex-mcp for machine-parsed section lists. Skim all sections, then deep-extract
priority sections. Every section must be `extracted` or `deferred`.

### code_method lane: Code function tracing

For code sources, "reading" means **tracing the algorithm through function calls**:

1. **Identify the entry point**: Which function is the first call in the algorithm chain?
   Ask the researcher: "I'll trace from the entry point. Is `function_X()` the right starting point?"
2. **Read one function at a time**:
   - Read the function body
   - Extract the formula (LaTeX) and data flow (inputs → transform → outputs)
   - Record via `aitp_create_derivation_step` with `source_ref = "file.cpp:start-end"`, `justification_type`, and `rigor_level`
3. **After each function**: Present the formula and physical meaning.
   Ask: "Does this match your understanding? Next I'll trace its caller/callee `function_Y()`."
4. **TOC for code** = the call graph. Record function names, file:line ranges, and what each calls.
   Write this into `source_toc_map.md` under `## Per-Source TOC` as a function table.
5. **Coverage**: All functions in the algorithm chain must be traced. Mark infrastructure
   code (MPI setup, I/O boilerplate) as `deferred` with explicit reason.
6. **Source basis**: Core sources are the key algorithm files. Peripheral sources are
   build configs, test scripts, I/O helpers. Record roles in `source_basis.md`.

### toy_numeric lane

Follow the code_method lane for numerical scripts and notebooks. Replace "function call graph"
with "computational pipeline steps." Record each step's input data, transform, output data,
and expected numerical behavior.

## Required artifacts

- `L1/source_basis.md`
- `L1/question_contract.md`
- `L1/source_toc_map.md`

## Reading workflow (mandatory sequence for formal_theory)

### Step 1: Register sources
1. Register or inspect sources using `aitp_register_source`.
2. Fill the bounded question if it is still blank.
3. Record source roles and reading depth in `source_basis.md`.

### Step 2: Parse source TOC
For **each registered source**, before any extraction:

1. Access the full text (arxiv-latex-mcp, web reader, PDF reader, etc.).
2. Extract the table of contents mechanically — every section, subsection, appendix.
   - **arXiv sources (preferred):** Use `arxiv-latex-mcp` `list_paper_sections` for
     machine-parsed, 100% reliable section list. Set `toc_confidence = "high"`.
   - **Well-structured PDFs:** AI-extract section headings from text. Set
     `toc_confidence = "medium"`.
   - **Unstructured sources:** Extract best-effort. Set `toc_confidence = "low"`.
3. Call `aitp_parse_source_toc` with all sections found. Each entry is the smallest
   identifiable structural unit (typically subsections for papers, sections for books).
   Include the `toc_confidence` field.
4. Do NOT skip any section, even if it seems irrelevant. The TOC must be exhaustive.
5. **Validate TOC**: Spot-check the first and last paragraph of at least 3 sections
   to confirm the TOC entries match actual content. If mismatches found, adjust and
   lower `toc_confidence`.

### Step 3A: Skim all sections (first pass)
Before deep extraction, do a rapid first pass over ALL sections:

1. Read each section quickly — focus on structure, not detail.
2. For each section, call `aitp_batch_extract_section` with just summary + empty concepts:
   - `summary`: 1-3 sentence summary
   - `completeness_confidence = ""` (leave unset during skim)
   - `concepts = []` (no deep extraction during skim)
3. The tool automatically updates section status.

This first pass builds a mental map of the entire source and identifies priority sections
vs. peripheral sections.

### Step 3B: Deep-extract priority sections (second pass)
For sections identified as relevant by the skim pass:

**When there are many pending sections (>3 across >1 source), use parallel sub-agents.**
This is the recommended approach for efficiency — each agent handles one source's
sections independently. See "Parallel extraction" below for the exact workflow.

For small-scale extraction (≤3 sections or single source), do sequential extraction:

1. Re-read the section in detail. Extract:
   - **Key concepts** — precise definitions, physical quantities introduced
   - **Equations** — numbered equations and their role in the argument
   - **Physical claims** — every non-trivial assertion about the physical system
   - **Prerequisites** — what the reader must know to understand this section
   - **Cross-references** — other sections or external sources this section depends on
2. Call `aitp_batch_extract_section` — a SINGLE call that does ALL of:
   - Writes the intake note
   - Creates L2 concept nodes for each discovered concept
   - Creates L2 edges for each obvious relationship
   - Auto-suggests related existing L2 concepts
   - Updates section status to `extracted`
   
   ```
   aitp_batch_extract_section(
       source_id="hedin1965", section_id="sec3",
       summary="Hedin derives the set of coupled equations...",
       key_concepts="self-energy Σ, Green's function G, screened interaction W,
                     vertex function Γ, Dyson equation",
       completeness_confidence="medium",
       concepts=[
           {"concept_id": "hedin-equations", "title": "Hedin Equations",
            "domain": "electronic-structure", "node_type": "theorem",
            "physical_meaning": "Coupled integro-differential equations...",
            "expression": "Σ(1,2) = -i∫G(1,3)Γ(3,2;4)W(4,1)d3d4"},
       ],
       edges=[
           {"from_node": "hedin-equations", "to_node": "greens-function",
            "edge_type": "uses"},
           {"from_node": "hedin-equations", "to_node": "self-energy",
            "edge_type": "derives_from"},
       ],
   )
   ```
   
   One call replaces 5 (intake + node + edge + status + search).
   If the tool returns `suggestions`, review and create edges for matching concepts.

### Parallel extraction with sub-agents (preferred for >3 sections across >1 source)

When the TOC has many pending sections across multiple sources, use parallel
general-purpose agents. Each agent handles ONE source's pending sections —
they have no shared state and write to independent intake files.

**Decision rule**: If `pending_sections > 3` AND `pending_sources > 1` → spawn
one agent per source. Otherwise, do sequential extraction (Step 3B).

**Workflow**:

1. Count pending sections per source from `source_toc_map.md`.
2. For each source with ≥1 pending section, spawn a background agent:

   ```
   Agent(
       subagent_type="general-purpose",
       description="Extract <source_id> pending sections",
       run_in_background=True,
       prompt="""You are extracting L1 intake notes for source <source_id>.
   
   **Source**: L0/sources/<source_id>/original/<main_file>
   Full path: <absolute_path_to_source_file>
   
   **Pending sections** (from source_toc_map.md):
   <list each pending section with its section_id and title>
   
   **Already done** (skip these):
   <list extracted sections>
   
   **How to extract**: For each pending section:
   1. Read the source file to understand the content
   2. Call aitp_write_section_intake with:
      - topics_root = '<topics_root>'
      - topic_slug = '<topic_slug>'
      - source_id = '<source_id>'
      - section_id = '<section_id>'
      - section_title = '<descriptive title>'
      - summary = '<1-3 paragraph summary of what this section covers>'
      - key_concepts = '<bullet list of key concepts introduced>'
      - equations_found = '<key equations with line numbers from source>'
      - physical_claims = '<numbered list of physical claims>'
      - completeness_confidence = 'high' or 'medium'
      - source_file = '<file path within repo>' (REQUIRED for repo-type sources)
   
   IMPORTANT:
   - source_file must be the EXACT relative path for repo sources (e.g. 'driver/task_qsgw.cpp')
   - For paper sources, include line numbers in equations_found (e.g. 'paper.tex line 117')
   - Report which sections you completed."""
   )
   ```

3. Wait for all agents to complete (you will be notified automatically).
4. After all agents finish, proceed to Step 4 (coverage verification).

**Agent prompt template — paper source**:

```
You are extracting L1 intake notes for the paper <source_id>.
Read <path_to_tex_or_pdf> and write intake notes for <N> pending sections:
<section_list_with_descriptions>

For each section, call:
from brain.mcp_server import aitp_write_section_intake
aitp_write_section_intake(
    topics_root='<topics_root>',
    topic_slug='<topic_slug>',
    source_id='<source_id>',
    section_id='<section_id>',
    section_title='<title>',
    summary='<1-3 paragraph summary>',
    key_concepts='<bullet list>',
    equations_found='<equations with line numbers>',
    physical_claims='<numbered claims>',
    completeness_confidence='high'
)
```

**Agent prompt template — repo source**:

```
You are extracting L1 intake notes for the repo <source_id>.
Read files from <path_to_repo> and write intake notes for <N> pending files:
<file_list_with_descriptions>

For each file, call:
from brain.mcp_server import aitp_write_section_intake
aitp_write_section_intake(
    topics_root='<topics_root>',
    topic_slug='<topic_slug>',
    source_id='<source_id>',
    section_id='<section_id>',
    section_title='<title>',
    source_file='<exact/relative/path>',
    summary='<what this file does>',
    key_concepts='<key functions/classes with line numbers>',
    equations_found='<formulas with line numbers>',
    physical_claims='<physical behavior this code controls>',
    completeness_confidence='high'
)
IMPORTANT: source_file MUST be the exact relative path. This field is critical for L3 traceability.
```

**After all agents complete**: Verify every section has an intake note with
non-empty `completeness_confidence`. Rerun any agent whose sections are missing
or have `completeness_confidence = "low"`.

### Step 3C: Defer genuinely out-of-scope sections
For sections that are genuinely irrelevant to the bounded question:

1. Call `aitp_update_section_status` with `new_status = "deferred"` and
   `extraction_note` containing the specific reason.
2. Do NOT create an intake note for deferred sections.

### Step 4: Coverage verification and completeness audit
Before exiting:

1. Check `source_toc_map.md` — all sections must be `extracted` or `deferred`.
2. Deferred sections must have explicit reasons documented in `## Deferred Sections`.
3. The `coverage_status` must be `complete` or `partial_with_deferrals`.
4. **Intake quality check**: Every `extracted` section must have a corresponding
   intake note with `completeness_confidence` set (not empty).
5. **Low-confidence audit**: Any intake note with `completeness_confidence = "low"`
   represents a coverage gap. Either:
   - Re-read the section more carefully and upgrade the confidence, or
   - Mark it as `deferred` with a clear reason why full extraction isn't possible.

## Critical rules

- **Never skip the TOC parse.** Reading sources without first registering their full
  structure defeats the completeness guarantee.
- **Skim ALL before deep-reading ANY.** The first pass prevents tunnel vision.
- **Never mark a section "extracted" without an intake note.** The gate checks that
  intake notes exist for every extracted section.
- **Defer sparingly.** Only sections genuinely outside the bounded question scope.
- **Honest confidence.** `completeness_confidence = "low"` is better than a false
  `"high"`. Low-confidence notes trigger re-reading, not advancement.
- **Do not start L3 derivation yet.** L3 depends on a complete source extraction.

## Exit condition

Move on only when:
- Source basis and bounded question are explicit.
- `source_toc_map.md` has `coverage_status = complete` or `partial_with_deferrals`.
- Every section in the TOC map is `extracted` or `deferred` with a documented reason.
- Every `extracted` section has an intake note with non-empty `completeness_confidence`.
- No intake notes remain at `completeness_confidence = "low"` without action.
