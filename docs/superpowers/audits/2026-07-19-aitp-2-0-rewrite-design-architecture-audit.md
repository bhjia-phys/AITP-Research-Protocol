---
title: AITP 2.0 Rewrite Design – Independent Architecture Audit
date: 2026-07-19
auditor: Architecture review (read-only, evidence-based)
scope: docs/superpowers/specs/2026-07-19-aitp-2-0-rewrite-design.md (lines 1–1248)
baseline: v5 codebase (741 .py files, ~168K LOC, 63+ registry record types, L0-L4 lifecycle)
real_research_checked:
  - F:/AI_Workspace/Theoretical-Physics/research/hs-like-chaos-window (no .aitp; real research dirs)
  - F:/AI_Workspace/Theoretical-Physics/research/librpa (patches, runbooks, analysis, scripts)
  - F:/AI_Workspace/Theoretical-Physics/research/aitp-topics/.aitp (legacy v5 store, ~50 topics, 63+ registry types)
method: Read full spec + historical docs + real repos + existing brain/ schemas/ adapters/
verdict: APPROVE WITH CONDITIONS – 4 P0 blockers, 8 P1 concerns, 6 P2 suggestions
---

# AITP 2.0 Rewrite Design – Architecture Audit

## Executive Summary

The 2.0 design is a **real and necessary simplification**. It correctly identifies that v5
has accumulated 63+ record types, 168K lines of Python, L0-L4 state machines, MCP servers,
hooks, and multiple agent-runtime surfaces that do not belong in a research memory protocol.
The reduction to six nodes, one Relation, deterministic paths, `rg`-first reads, and Git as
the byte ledger is architecturally sound.

However, the design has four P0 issues that must be resolved before R0 freeze, primarily
around data model overloading (Statement carrying 11 semantically divergent kinds), the
commit manifest circular dependency, TOPIC.md route staleness, and a command name collision.
These are all fixable in the spec text without changing the architecture.

---

## P0 – Blockers (must resolve before R0 contract freeze)

### P0-1: Statement kind overloading – one type for 11 divergent semantics

- **File:Line**: `2026-07-19-aitp-2-0-rewrite-design.md:239-251` (Statement kinds) and `:257-264` (lifecycle values)
- **Problem**: The Statement type covers `question`, `hypothesis`, `claim`, `definition`, `insight`,
  `decision`, `constraint`, `open_gap`, `research_route`, and `system_feedback`. These are not
  subtypes of a common concept:

  - A `question` is resolved when answered; a `constraint` is never "resolved" but "satisfied" or "violated".
  - A `system_feedback` is not epistemic at all — it's machine provenance.
  - A `research_route` has `goal`, `next_action`, `dependencies`, `stop_conditions`, `cost_or_execution_mode`
    (§11:649-661) — these fields are meaningless for a `definition` or `insight`.
  - A `decision` has different completeness criteria than a `hypothesis`.

  The single lifecycle enum `active/resolved/superseded/archived` does not fit half the kinds.

- **Failure scenario**: An Agent creates a `Statement(kind=system_feedback, status=resolved)`.
  A downstream route portfolio reader treats "resolved" feedback as a validated claim.
  The `research_route` kind silently acquires fields that make no sense for `open_gap`.
  Schema validation can't catch this because all kinds share one schema.

- **Impact**: The route portfolio in §11 becomes unreliable. Agents will misuse the lifecycle
  enum. Active routes, blocked gaps, and resolved decisions will be indistinguishable
  without parsing the `kind` field — and even then, the lifecycle semantics are wrong.

- **Recommendation**: Two options:

  **Option A (Recommended)**: Split Statement into three node types:
  - `Statement` — epistemic content: question, hypothesis, claim, definition, insight.
    Lifecycle: `active | resolved | superseded | archived`.
  - `Route` — a planned research path: goal, next_action, dependencies, stop_conditions,
    parallelizable_with, cost_or_execution_mode, human_gate. No epistemic lifecycle.
    State: `proposed | active | completed | abandoned | blocked`.
  - `Constraint` — a boundary condition, convention, or operational rule.
    State: `active | relaxed | removed`.

  This keeps the node budget at 8 instead of 6, which is still far below v5's 63+.
  The increase is justified because Route and Constraint are structurally different.

  **Option B**: Keep six nodes but restrict Statement kinds to epistemic content only
  (question, hypothesis, claim, definition, insight). Move `research_route` to
  `Episode(kind=research_route_proposal)` or a dedicated `Route` record within the
  topic directory. Move `system_feedback` to Episode provenance. Move `decision` and
  `constraint` to a structured section of `TOPIC.md` or `Assessment` target.

  Option A is architecturally cleaner; Option B preserves the six-node budget but
  requires more convention discipline from Agents.

### P0-2: Commit manifest circular dependency – manifest path hash unknown at commit time

- **File:Line**: `2026-07-19-aitp-2-0-rewrite-design.md:404-417` (CAS commit steps) and `:727-745` (manifest contents)
- **Problem**: The commit procedure in §7.3 step 5 says "create the commit manifest, then create one
  Git commit containing the exact records and that manifest." §12.4 says the manifest contains
  `record_paths_and_hashes` which includes "every changed canonical record." But the manifest
  itself is a new file being written — its own content hash is not known until the bytes are
  finalized. The design acknowledges "The manifest intentionally does not contain the resulting
  Git commit hash or its own content hash" (line 740-741), but the conceptual problem remains:

  The `record_paths_and_hashes` field lists hashes of committed files. If the manifest lists
  itself as one of the committed paths, its hash must be computed from content that includes
  the hash of that content. This is a standard self-reference problem, solvable but only if the
  design explicitly states that the manifest hash is computed against the manifest content
  *excluding* the manifest's own entry in `record_paths_and_hashes`, OR that the manifest
  simply does not list itself.

- **Failure scenario**: An implementer writes the manifest, hashes all committed records,
  includes the manifest path with hash H1, but the act of writing hash H1 into the manifest
  changes the manifest content to a new hash H2. The stored hash H1 never matches. A readback
  audit at step 8 (§7.3:417) detects the mismatch and rejects the commit as corrupted.

- **Impact**: The CAS commit step 8 readback will fail on the manifest itself unless the design
  explicitly handles this. Without clarification, every commit could appear corrupted.

- **Recommendation**: Add to §12.4: "The manifest's own path is listed in `record_paths_and_hashes`
  with hash computed against the manifest content *after* all other record hashes are finalized
  and written. The readback auditor skips the manifest's own hash — it verifies the Git tree
  hash instead." Alternatively, state explicitly: "The manifest does not list itself; the Git
  commit tree hash implicitly covers it."

### P0-3: TOPIC.md → Route Statements → dual truth source for active research state

- **File:Line**: `2026-07-19-aitp-2-0-rewrite-design.md:135-136` (TOPIC.md location) and `:628-665` (entry context with routes)
- **Problem**: `TOPIC.md` is a single file at `topics/<id>/TOPIC.md`. Active research routes are
  individual `Statement(kind=research_route)` records with their own lifecycle values. The
  `aitp enter` output (§11:628-643) contains "Active Research Routes" (item 7) and a "Route
  Portfolio Proposal" (item 11). If `TOPIC.md` contains a "Current State" section listing
  active routes, and route Statements also carry lifecycle, there are two representations of
  the same information.

  The design does not specify:
  - Whether `TOPIC.md`'s route list is derived from route Statement lifecycle or independently edited.
  - Whether `aitp enter` reads route Statements or `TOPIC.md`'s inline summary.
  - Who updates `TOPIC.md` when a route transitions from `active` to `superseded`.

- **Failure scenario**: An Agent reads `TOPIC.md` and sees route A as active. Route A's
  Statement was superseded by another Agent in a prior session via a normal checkpoint commit.
  `TOPIC.md` was not regenerated. The Agent proceeds on a stale route, writes a new Episode
  that conflicts with the superseded state, and the audit at commit time catches the conflict
  but only after wasted work.

- **Impact**: Route staleness undermines the core value proposition of `aitp enter` as the
  reliable re-entry point. Duplicate truth sources create exactly the kind of confusion
  the design is trying to eliminate.

- **Recommendation**: Specify that `TOPIC.md` is a **derived/regenerated view**, not an
  Agent-edited file. Its content is produced by `aitp enter` or `aitp organize` from the
  canonical Statement (kind=research_route) records and other node records. The `TOPIC.md`
  header should state: "This file is regenerated from canonical records. Direct edits will
  be overwritten." The Agent edits route Statements; `aitp organize` regenerates `TOPIC.md`.
  This is consistent with the design's "derived views" philosophy in §10.3.

### P0-4: `aitp review` command name collision – ambiguous across Recording and Reuse groups

- **File:Line**: `2026-07-19-aitp-2-0-rewrite-design.md:782-796` (CLI command groups)
- **Problem**: The "Recording And Review" group (line 782-785) contains `aitp audit` as the
  deterministic schema checker. The "Reuse" group (line 791-796) contains `aitp review` for
  human review of Workflow candidates. The group name "Recording And Review" implies `audit`
  is the review mechanism, while `aitp review` in Reuse sounds like a different review.
  An Agent or human will not know which command checks what:

  - `aitp audit` = deterministic pre-commit schema validation.
  - `aitp review` = human approval workflow for Workflow/Knwoledge Card candidates.

  These are fundamentally different operations but the names are confusingly similar.
  In the spec text, "review" appears 31 times with at least 4 distinct meanings.

- **Failure scenario**: A user runs `aitp review` expecting a bundle audit before commit.
  Instead they get the Workflow candidate review workflow. Or an Agent writes code to call
  `aitp audit` for human approval, but the actual human approval path requires `aitp review`.

- **Impact**: CLI usability regression. Agents will call the wrong command even with the
  command guide.

- **Recommendation**: Rename `aitp review` (Reuse group) to `aitp approve`. The Reuse group
  becomes: `aitp distill`, `aitp approve`, `aitp install`. This cleanly separates:
  - `aitp audit` = deterministic, automated, pre-commit.
  - `aitp approve` = human judgment, post-audit, gated.
  The word "review" is removed from command names entirely.

---

## P1 – Important (should resolve before R1/R2 implementation)

### P1-1: `using-aitp` Skill content is undefined – host integration gap

- **File:Line**: `2026-07-19-aitp-2-0-rewrite-design.md:838` (first relevant turn) and `:1132-1134` (Codex/Kimi vertical)
- **Problem**: The entire host integration story depends on "a short `using-aitp` Skill" that
  "tells the host to invoke `aitp enter` on the first turn that concerns durable research."
  This Skill is never specified in the document — no content, no triggers, no error handling.
  Since there are no MCP servers and no required hooks, the Skill is literally a `.md` file
  that the host reads as instructions. But hosts (Codex, Kimi) have different Skill formats,
  different context windows, and different turn-detection capabilities.

  The legacy adapters at `adapters/codex/SKILL.md` and `adapters/kimi-code/SKILL.md` exist
  but are v5-specific (they reference hooks, MCP, and L0-L4 lifecycle).

- **Failure scenario**: A host reads the Skill instructions but cannot reliably determine
  "the first turn that concerns durable research" because it's a semantic judgment call.
  The host enters too early (on a typo fix) or too late (after a key result is already
  produced but not recorded). The Skill, being static text, has no programmatic detection.

- **Impact**: R5/R6 release gate 12 ("Codex and Kimi complete the lifecycle without MCP or
  required hooks") cannot be verified because the Skill is undefined.

- **Recommendation**: Add a §27 appendix or a companion spec with the minimal `using-aitp`
  Skill content. It should include:
  - A checklist of "durable moment" signals that the host can pattern-match (see §15.2).
  - The exact `aitp enter` invocation and expected output format.
  - Error recovery: what to do when `aitp` is not installed, when topic routing is ambiguous,
    when a previous session left staging bundles.
  - A "missed entry" recovery procedure (since the design says this is recoverable at line 848,
    but doesn't say how the host knows it missed).

  The Skill should be host-neutral enough to work for both Codex and Kimi, with host-specific
  overrides in separate `adapters/<host>/SKILL.md` files.

### P1-2: `rg` search and YAML frontmatter – no content/metadata boundary

- **File:Line**: `2026-07-19-aitp-2-0-rewrite-design.md:568-602` (read order and search scope)
- **Problem**: The design uses `rg` as the baseline lexical engine. All canonical records are
  Markdown with YAML frontmatter (stated at premise 4). When `rg` searches these files, it
  matches on both frontmatter fields AND body text. A search for "quantum" matches the body
  content of a physics discussion AND the `tags: [quantum, chaos]` frontmatter of unrelated
  records. The design's search scope (§10.2) declares `coverage`, `searched_roots`, etc.
  but never distinguishes frontmatter hits from body hits.

  More subtly: frontmatter values ARE canonical content. A Statement's `title` field in
  frontmatter is searchable semantic content, but a `created_at` timestamp is not.
  `rg` can't tell the difference.

- **Failure scenario**: An Agent searches for "superseded" to find superseded Statements.
  `rg` matches the frontmatter `status: superseded` field of every superseded record AND
  any body text that happens to mention "superseded." The Agent receives 200 results,
  180 from frontmatter, 20 from body, and can't distinguish. The coverage report says
  `coverage: exhaustive` but the Agent only checks the first 50 results and misses
  a critical body mention.

- **Impact**: Search precision is degraded in a way the coverage semantics can't express.
  The `not_found` absence claim (§10.2:606-612) becomes unreliable because the Agent
  couldn't process all results meaningfully.

- **Recommendation**: Add to §10.2: "Search results distinguish frontmatter matches
  (key: `metadata`) from body matches (key: `content`). The host may filter by match
  location." The `aitp search` implementation should pass `--iglob '!---*'` or equivalent
  to exclude frontmatter delimiters, OR post-process results to annotate whether the
  match is in a frontmatter block. Since YAML frontmatter is delimited by `---`, this
  is straightforward to implement.

### P1-3: Route portfolio proposal by AITP – ambiguous authority

- **File:Line**: `2026-07-19-aitp-2-0-rewrite-design.md:643` ("Selected because is not model-facing content") and `:663-665` (human routing decision)
- **Problem**: §11 says "AITP proposes a route portfolio" but also says "The human chooses
  when priority is ambiguous." This creates an unclear boundary: does AITP select routes
  algorithmically (e.g., by Statement lifecycle, dependency graph, or recent Episode count)
  or does it simply list all `active` route Statements? If algorithmic, the selection
  logic is a hidden intelligence layer that contradicts §4 ("The CLI is a protocol boundary,
  not an intelligence layer"). If it just lists them, "proposes" is misleading.

  The phrase "Selected because is not model-facing content" at line 643 implies AITP does
  make a selection with reasoning, but the reasoning is hidden from the Agent. This is
  exactly the kind of hidden semantic compilation the design warns against in §12.4:745.

- **Failure scenario**: AITP's route selector deprioritizes a route because it has been
  `active` for 30 days (an implicit staleness heuristic). The human needed that route today.
  The human never sees it in the `aitp enter` output because it's below the default display
  budget. The "Selected because" reasoning exists in JSON but the Agent never reads JSON
  output. The human spends a session on the wrong route.

- **Impact**: Hidden routing heuristics undermine user trust and violate the transparency
  principles of §4 and §12.

- **Recommendation**: Explicitly define the route portfolio algorithm:
  1. List all Statements with `kind=research_route` and `status=active`, sorted by most
     recent Episode that references them.
  2. Include all routes with `human_gate=true` and flag them.
  3. Include all routes with unresolved `depends_on` blocking them, with the blocker ref.
  4. The "proposal" is this ordered list, not a subset.
  Remove "Selected because" from non-debug output. The Agent sees the full list with
  priority annotations; the human chooses.

### P1-4: Working tree snapshot – untracked files not addressed

- **File:Line**: `2026-07-19-aitp-2-0-rewrite-design.md:504-517` (uncommitted code)
- **Problem**: The `Asset(kind=working_tree_snapshot)` records `base_commit`, `patch_locator`,
  `patch_sha256`, `untracked_file_manifest`, and `dirty=true`. But:

  - The `patch_locator` presumably points to a `git diff` output stored as another Asset.
    The relationship between the snapshot Asset and the patch Asset is implicit.
  - `untracked_file_manifest` lists untracked files but doesn't say HOW they are stored.
    Are they copied to `.aitp/assets/`? Referenced by absolute path? Bundled into the
    patch? If an untracked file is a 500MB binary output, does AITP store it?
  - The "later Episode links it to the final commit or explains why it was abandoned"
    (line 516-517) puts the burden on the Agent to remember — but the whole point of
    the snapshot is that the Agent might forget or crash.

- **Failure scenario**: Research uses uncommitted changes plus a custom compiled binary
  (untracked). The Agent creates a working_tree_snapshot Asset recording the patch but
  the untracked binary path is `/tmp/build/a.out` which no longer exists when another
  Agent tries to reproduce. The `untracked_file_manifest` exists but the files don't.
  The snapshot claims `dirty=true` but can't be reconstructed.

- **Impact**: Formula-to-code provenance (§9.3) can't be verified for uncommitted code
  if untracked dependencies are missing. The reproductibility promise is broken.

- **Recommendation**: Add to §9.2:
  1. Untracked files listed in `untracked_file_manifest` are either (a) copied to
     `.aitp/assets/<asset-id>/untracked/` if under a size threshold (e.g., 10MB), or
     (b) recorded with their `sha256` and original path only, marked as `stored=false`.
  2. The patch Asset and the snapshot Asset are linked by a `Relation(predicate=produced)`.
  3. The snapshot completeness field says `complete_with_declared_gaps` listing which
     untracked files are not stored.

### P1-5: Literature `anchors.jsonl` format undefined

- **File:Line**: `2026-07-19-aitp-2-0-rewrite-design.md:209` (extracted/anchors.jsonl)
- **Problem**: The literature library stores `extracted/anchors.jsonl` but the anchor
  format is never specified. The locator scheme `pdf://<source-id>#page=<page>&anchor=<anchor-id>`
  (§8:468) references anchor IDs, but what IS an anchor? Is it a paragraph, a line range,
  a figure caption, an equation number? Without a spec, every PDF extraction tool will
  produce different anchor formats, and `aitp literature extract` has no stable contract.

- **Failure scenario**: Tool A extracts anchors as `{"id":"p3-l4","bbox":[...],"text":"..."}`.
  Tool B uses `{"id":"sec2.1-para3","type":"paragraph","content":"..."}`. An Episode
  references `pdf://arxiv-2109.05037#page=3&anchor=p3-l4`. Later, the PDF is re-extracted
  with Tool B and anchor `p3-l4` no longer exists. The reference is broken.

- **Impact**: Literature references decay when PDF extraction tools change. This undermines
  the "Must Read" and "exact source anchor" guarantees in §12 and §16.2.

- **Recommendation**: Define the anchor format in the spec:
  ```json
  {"id": "<stable-id>", "type": "paragraph|equation|figure|table|section",
   "page": <int>, "bbox": [x1,y1,x2,y2], "text_preview": "<first 200 chars>"}
  ```
  The stable ID should be `p<page>-<type>-<sequence>` (e.g., `p3-eq-2` for the 2nd
  equation on page 3). If the PDF is re-extracted, anchors with the same stable ID
  and similar `text_preview` are considered the same; mismatches raise an audit warning.

### P1-6: `aitp checkpoint` and `aitp closeout` – overlapping responsibilities

- **File:Line**: `2026-07-19-aitp-2-0-rewrite-design.md:782-783` (checkpoint and closeout) and `:852-878` (session lifecycle)
- **Problem**: `aitp checkpoint` is for "durable moments" (§15.2) during a session.
  `aitp closeout` is for end-of-session and "may prepare a staging bundle but uses the
  same audit, review, and commit path" (§15.3:869-870). But §15.3 also says closeout
  "checks for durable unrecorded work, route results, new assets, failures, code changes,
  pending human decisions, and unresolved staging." This is essentially a checkpoint
  plus a completeness sweep. The distinction is:

  - `checkpoint`: The Agent explicitly calls it at a known durable moment.
  - `closeout`: The Agent calls it at session end; AITP detects what was missed.

  But if the Agent can detect durable moments for `checkpoint`, why can't it detect them
  for closeout? And if closeout can auto-detect, why are checkpoints manual?

- **Failure scenario**: An Agent diligently calls `checkpoint` at every durable moment.
  At closeout, AITP finds nothing new (because the Agent was thorough) and writes
  "no durable change occurred" (line 872). But the closeout checklist in §15.3 reports
  "pending human decisions" that the Agent didn't create a checkpoint for (e.g., a
  human said "let me think about this"). The human decision is recorded nowhere.

- **Impact**: The boundary creates a gap: "open human decisions" should be captured
  at closeout but the Agent didn't checkpoint them. The design says "no empty Episode"
  but the human decision IS a durable event that deserves a record.

- **Recommendation**: Merge closeout's detection into checkpoint semantics:
  `aitp checkpoint` runs the closeout sweep internally and reports any unrecorded
  durable state (pending decisions, uncommitted staging, unlinked assets). If there
  are findings, it creates a closeout Episode. If there are no findings, it creates
  no Episode but reports success. `aitp closeout` becomes an alias for `aitp checkpoint`
  with a "this session is ending" annotation. This reduces the command count from 13
  to 12 and eliminates the overlap.

### P1-7: Route context explosion risk – no explicit context budget enforcement

- **File:Line**: `2026-07-19-aitp-2-0-rewrite-design.md:628-665` (entry context) and `:10-12` (topic background and linked refs)
- **Problem**: §11 says "It does not inject all topic memory or recursively build a large
  context pack." But the entry context includes 13 sections, each of which may expand to
  linked refs. The "Exact Refs" field in routes (§11:660) points to Statements, Episodes,
  Assets, and Assessments. A host that diligently expands every ref to satisfy the
  "Must Read" instruction could blow its context window. The design has no explicit
  context budget — no token limit, no expansion depth limit, no progressive loading
  mechanism.

  The host is told to "expand only the records needed for the current route" (§2:58)
  but this is a behavioral guideline, not an enforced constraint. Different hosts
  will interpret "needed" differently.

- **Failure scenario**: A topic has 15 active routes, each with 5-10 `exact_refs[]`.
  Kimi's context window is 128K tokens. The `aitp enter` output lists all routes with
  refs. The Agent expands all refs. The output plus expanded refs is 180K tokens,
  exceeding the window. The Agent truncates and misses a critical constraint that
  invalidates the chosen route's approach.

- **Impact**: Context overflow silently degrades research quality. The Agent doesn't
  know what it doesn't know because the truncation is at the host level, not at the
  AITP level. The coverage semantics in §10.2 don't apply to entry context expansion.

- **Recommendation**: Add to `aitp enter` output a `context_budget` section:
  ```markdown
  ## Context Budget
  - Total expanded refs available: 47
  - Estimated token cost if fully expanded: 210,000
  - Current context window estimate: 128,000
  - Recommended expansion depth: 1 (route summaries only)
  - Full expansion available via: `aitp show <ref>` (on-demand)
  - High-priority Must Read: [ref1, ref2, ref3] (estimated 15,000 tokens)
  ```
  This gives the Agent explicit guidance rather than leaving it to guess.

### P1-8: No conformance test for "no MCP, no hooks, no Agent runtime" budget

- **File:Line**: `2026-07-19-aitp-2-0-rewrite-design.md:1215` (release gate 15: architecture-budget tests)
- **Problem**: Release gate 15 requires architecture-budget tests that reject "a second
  writer, required index, required hook, MCP surface, seventh node type, or unowned public
  command." These are pass/fail for discrete items. But "Agent runtime" is not listed in
  the gate even though it's prohibited in §3 and §4. More importantly, there's no test
  for *accidental* complexity creep: a `Statement` schema gaining 15 optional fields that
  collectively make it as complex as the v5 `Claim` record.

- **Failure scenario**: During R4 (research verticals), a real physics Episode can't be
  expressed. A developer adds an optional `Statement.numerical_evidence` field. Another
  vertical needs `Statement.literature_support`. By R6, Statement has 20 optional fields,
  the schema is 400 lines, and the six-node simplicity is gone — but no gate catches it
  because each addition individually is "just an optional field."

- **Impact**: Architecture budgets are gamed through accretion. The v5 bloat repeats.

- **Recommendation**: Add a quantitative complexity gate: "No node schema may exceed 20
  required+optional fields total. The Relation schema may not exceed 12 fields. The total
  schema LOC (JSON Schema or Python dataclass definitions) must be < 500 lines. New
  fields require explicit architecture review." Gate 15 should also explicitly list
  "no Agent runtime dispatch, scheduling, or orchestration logic" as a test target.

---

## P2 – Suggestions (deferrable to 2.1 or resolved during implementation)

### P2-1: 13 CLI commands still feels heavy – consider merging

- **File:Line**: `2026-07-19-aitp-2-0-rewrite-design.md:766-800`
- **Observation**: `aitp organize` and `aitp compose` are both about producing derived
  output from canonical records. `organize` regenerates `TOPIC.md`; `compose` prepares
  writing scaffolds. These could be `aitp compose organize` and `aitp compose write`.
  Similarly, `aitp research` and `aitp literature` could be `aitp source research` and
  `aitp source literature`. This would reduce the top-level commands to ~10.
- **Recommendation**: Do not change now. Gather usage data from R4/R5 verticals. If
  `organize` is run only during `enter`, fold it into `enter`. If `compose` is rarely
  used, make it a `distill` subcommand. Defer to 2.1.

### P2-2: Recording profiles need explicit version compatibility

- **File:Line**: `2026-07-19-aitp-2-0-rewrite-design.md:748-763`
- **Observation**: Profiles are "versioned templates" but no version compatibility
  contract is specified. If profile v2 adds a required field, Episodes recorded under
  v1 are not retroactively invalid. But `aitp audit` might flag them as missing the
  v2 field. The spec should say: "A profile version applies to bundles created after
  that version's adoption date. Audit rules only check the profile version declared
  in the bundle. `AUDIT.md` warns when a bundle uses a superseded profile version."
- **Recommendation**: Add a §13.1 with the above.

### P2-3: Skill rollback data specification

- **File:Line**: `2026-07-19-aitp-2-0-rewrite-design.md:974-977`
- **Observation**: "Installation, replacement, update, and rollback require human approval."
  But rollback data is never specified. What does `aitp install --rollback <skill>` do?
  Presumably restore the previous `SKILL.md` and metadata from an `install_receipt` Asset,
  but this is implementation detail that needs at least a sketch.
- **Recommendation**: Add a rollback section to §17: "Rollback restores the previous
  `SKILL.md`, host metadata, scripts, and assets from the install receipt Asset. The
  receipt records the pre-install state as a tarball or path manifest. Rollback creates
  a new `Episode(kind=research_decision)` documenting the reason."

### P2-4: Knowledge Card as Asset vs Episode

- **File:Line**: `2026-07-19-aitp-2-0-rewrite-design.md:909-913` and `:301` (asset kinds)
- **Observation**: A Knowledge Card is `Asset(kind=knowledge_card)` linked to source Assets,
  Statements, and Assessments. But it is produced by a synthesis process (research, review,
  distillation) which is inherently episodic. Treating it as an Asset emphasizes the output
  but loses the process provenance. An alternative: the Knowledge Card is an
  `Episode(kind=writing_synthesis)` that produces an `Asset(kind=knowledge_card)`. The
  card itself is the Asset; the act of synthesis is the Episode.
- **Recommendation**: Clarify in §16.3: "A knowledge card is created by an
  `Episode(kind=writing_synthesis)` which records the derivation process, candidate
  sources, review decisions, and human approval. The resulting `Asset(kind=knowledge_card)`
  is the portable output linked to the synthesis Episode."

### P2-5: Route `parallelizable_with[]` is informational dead weight without dispatch

- **File:Line**: `2026-07-19-aitp-2-0-rewrite-design.md:658` (route spec) and `:980-992` (multi-agent)
- **Observation**: §18 says "AITP describes route dependencies and conflicts but does not
  dispatch agents." The `parallelizable_with[]` field tells a human which routes can be
  worked on simultaneously. But without a dispatch mechanism, this is purely advisory. If
  two Agents independently start parallelizable routes, they can still produce conflicting
  staging bundles (same base commit, different content), and one will be rejected at CAS
  commit. The field promises parallelism but the commit model is serial.
- **Recommendation**: Add to §18: "`parallelizable_with` indicates routes that modify
  disjoint node sets. The commit model still serializes; parallelism is advisory for
  human planning. Routes that touch overlapping records must not be marked
  `parallelizable_with` each other." Or consider removing the field for 2.0 and
  letting the human deduce parallelism from the route refs.

### P2-6: SSH host profile – credentials boundary unclear

- **File:Line**: `2026-07-19-aitp-2-0-rewrite-design.md:473-475`
- **Observation**: "An SSH host profile records a stable alias, capabilities, policy, and
  path roles, not authentication secrets or live queue state." This is correct, but the
  `runtime/local.toml` file (§5.1:164) contains machine-specific configuration. If an
  SSH host profile references a key file path, that path is machine-specific and belongs
  in `runtime/local.toml`. The design should explicitly state: "SSH key paths and
  credentials are in `runtime/local.toml` and are never canonical records. Host profiles
  are canonical and reference a `host_profile_id`; `runtime/local.toml` maps that ID to
  a local key path."
- **Recommendation**: Add this clarification.

---

## Cross-Cutting Observations

### What the design gets right

1. **Six nodes is the right target.** The reduction from 63+ v5 registry types is not
   premature — v5's `evidence`, `validation_results`, `promotion_packets`, `proof_obligations`,
   `lifecycle_events`, `monitor_snapshots`, `lane_contracts`, `scope_revalidation_decisions`,
   etc. are all process artifacts that don't belong in research memory.

2. **Git as byte ledger is correct.** The v5 approach of maintaining a separate `revisions/`
   directory with integer revision counters was redundant with Git's own history. Using Git
   commits as the revision anchor eliminates an entire subsystem.

3. **`rg`-first reads are appropriate.** The v5 store has ~50 topics with Markdown records.
   Full-text search over this scale with `rg` is fast (< 1 second), and the design's
   progressive expansion (exact ref → `rg` → Git history → optional index) is the right
   cost model.

4. **Formula-to-code mapping via blob hashes is robust.** The `git://...#symbol=<symbol>&...`
   locator plus `blob_hash` in the Relation annotations correctly pins code identity even
   after file edits. This is a real improvement over v5's `code_states` and
   `execution_baselines`.

5. **Human gates are at the right level.** Required approval for `proved_within_assumptions`,
   contested conclusions, cross-topic trust, WorkflowSpec, and Skill install covers the
   dangerous operations without requiring approval for routine Episodes.

6. **Legacy cutover is thorough.** The 8-step procedure (§20) with byte-identical manifest,
   search verification, and rollback test is correctly paranoid for historical research data.

### Architectural risks to monitor during implementation

1. **Statement kind inflation.** If P0-1 is not fully resolved, developers will add
   `Statement(kind=user_noted_bug)` and `Statement(kind=pending_hpc_job)` by R4 because
   there's no other place to put them. The Statement type will silently absorb all v5
   registry types.

2. **Profile as hidden complexity vector.** §13 lists 7 recording profiles. Each profile
   specifies what an Episode "should address" but these specifications could grow into
   mini-schemas with their own validation rules. If profiles become the v5 "lane contracts"
   in disguise, the audit rule system in §12.2 becomes the v5 "promotion pipeline."

3. **Optional indexes becoming required.** The design is clear that SQLite/RAG are optional
   disposable accelerators (§10.3). But performance budgets in release gate 7 require
   "documented local performance and context budgets on a representative ten-thousand-record
   fixture." If the `rg` path doesn't meet the budget, the natural response will be to make
   indexes semi-required ("you CAN run without them, but the performance budget assumes
   they exist"). The budget test should measure `rg`-only performance as the baseline.

4. **`aitp show` as the universal resolver.** The design says `aitp show` resolves exact
   refs without scanning a database (§7.1:380). This implies `aitp show` must parse the
   ref, compute the filesystem path from the type prefix and ID, and read the file. If
   the ID-to-path mapping ever becomes non-deterministic (e.g., records move between
   topics), this breaks. The path derivation algorithm must be fully specified and tested.

---

## Verdict

**APPROVE WITH CONDITIONS.** The four P0 issues must be addressed before R0 contract freeze.
The eight P1 issues should be addressed before R2 (read path) implementation, as they affect
the core data model, search, and host integration. The six P2 suggestions are deferrable.

The design's core insight — that AITP should be a thin protocol on top of Markdown, `rg`,
and Git, not an agent runtime — is correct and well-argued. The evidence from the v5 codebase
(741 .py files, 63+ registry types, L0-L4 state machine) strongly supports the conclusion
that a clean rewrite is the right path. The concerns raised here are about precision and
completeness, not about the architectural direction.

---

## Summary of Recommendations

| ID | Severity | Area | Summary |
|----|----------|------|---------|
| P0-1 | Blocker | Data model | Statement kind overloading — split into Statement/Route/Constraint |
| P0-2 | Blocker | Commit | Manifest self-hash circular dependency — specify resolution |
| P0-3 | Blocker | Entry | TOPIC.md vs route Statements as dual truth source — make TOPIC.md derived |
| P0-4 | Blocker | CLI | `aitp review` name collision — rename to `aitp approve` |
| P1-1 | Important | Host | `using-aitp` Skill undefined — spec appendix needed |
| P1-2 | Important | Search | `rg` + YAML frontmatter — annotate metadata vs content matches |
| P1-3 | Important | Routing | Route portfolio selection logic — make algorithm explicit |
| P1-4 | Important | Code | Working tree untracked files — storage/locator spec |
| P1-5 | Important | Literature | `anchors.jsonl` format undefined — spec the format |
| P1-6 | Important | Session | checkpoint vs closeout overlap — merge semantics |
| P1-7 | Important | Context | No context budget enforcement — add budget section to enter |
| P1-8 | Important | Budget | No quantitative complexity gate — add schema LOC and field count limits |
| P2-1 | Suggestion | CLI | Consider merging commands after data from verticals |
| P2-2 | Suggestion | Profiles | Profile version compatibility contract |
| P2-3 | Suggestion | Skills | Rollback data specification |
| P2-4 | Suggestion | Knowledge | Knowledge Card as Episode output, not standalone Asset |
| P2-5 | Suggestion | Multi-agent | `parallelizable_with[]` vs serial commit model |
| P2-6 | Suggestion | Config | SSH key paths belong in runtime/local.toml |
