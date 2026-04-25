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

## Required artifacts

- `L1/source_basis.md`
- `L1/question_contract.md`
- `L1/source_toc_map.md`

## Reading workflow (mandatory sequence)

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
2. For each section, call `aitp_write_section_intake` with:
   - `section_title`: from the TOC entry
   - `summary`: 1-3 sentence summary of what this section is about
   - `completeness_confidence = ""` (leave unset during skim)
3. After the skim pass, call `aitp_update_section_status` with `new_status = "skimming"`
   for each section.

This first pass builds a mental map of the entire source and identifies priority sections
vs. peripheral sections.

### Step 3B: Deep-extract priority sections (second pass)
For sections identified as relevant by the skim pass:

1. Re-read the section in detail. Extract:
   - **Key concepts** — precise definitions, physical quantities introduced
   - **Equations** — numbered equations and their role in the argument
   - **Physical claims** — every non-trivial assertion about the physical system
   - **Prerequisites** — what the reader must know to understand this section
   - **Cross-references** — other sections or external sources this section depends on
2. Call `aitp_write_section_intake` with all fields filled and
   `completeness_confidence` set honestly:
   - `"high"` — every claim and equation captured, no ambiguities
   - `"medium"` — main points captured, some details may be glossed
   - `"low"` — significant gaps, need to re-read or consult external sources
3. The tool automatically marks sections with `completeness_confidence ∈ {high, medium}`
   as `extracted` in the TOC map and links the intake note.

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
