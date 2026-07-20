---
title: AITP 2.0 Command-Skill Protocol – Independent Architecture Audit
date: 2026-07-20
auditor: Independent Chief Architecture Auditor (read-only, evidence-driven)
scope:
  primary: docs/superpowers/specs/2026-07-20-aitp-2-0-command-skill-protocol-design.md (895 lines)
  superseded: docs/superpowers/specs/2026-07-19-aitp-2-0-rewrite-design.md (1548 lines)
  prior_audit: docs/superpowers/audits/2026-07-19-aitp-2-0-rewrite-design-architecture-audit.md (601 lines)
  prior_disposition: docs/superpowers/audits/2026-07-20-aitp-2-0-rewrite-design-audit-disposition.md (54 lines)
baseline: v5 codebase — 741 .py files, ~168K LOC, 63+ registry record types, L0-L4 lifecycle, MCP server, hook infrastructure, context compiler, agent runtime
files_examined: 42 files across specs, audits, code, skills, templates, schemas, contracts, tests, and topic samples
commands_executed: find, glob, grep, ls across full worktree
verdict: CONDITIONAL PASS — 0 P0 blockers, 9 P1 findings, 7 P2 suggestions
---

# AITP 2.0 Command-Skill Protocol – Architecture Audit

## Executive Verdict

**CONDITIONAL PASS.** The 2026-07-20 spec is a genuine improvement over the 2026-07-19 design. All four P0 blockers from the prior audit have been resolved or acceptably dispositioned. The command-skill architecture is self-consistent at the design level, and the simplicity ratchet is correctly structured to prevent v5 complexity from re-entering.

However, nine P1 findings must be addressed before the corresponding S0-S7 phases begin — primarily around the `using-aitp` Skill specification gap, command-local Skill discovery mechanics, store-relative path resolution edge cases, Knowledge Card assertion binding granularity, Scientific Dreaming as a complete flow, Scenario A/B context budgets, and the complete absence of fixture data for the required verticals.

Zero P0 blockers exist: the architecture can proceed to S0 freeze. But S0 cannot complete without P1-1 (using-aitp Skill spec) and P1-2 (command Skill discovery), and S4 cannot begin without P1-5 through P1-7.

---

## Reconstructed Architecture

AITP 2.0 is a **local research-memory protocol operated through commands and Markdown guides**. Its complete required architecture is four components:

1. **One `using-aitp` Skill** — installed at the host level (Codex/Kimi). Contains a short router: trigger on research intent, run `aitp enter` on first relevant turn, select phase commands from a documented trigger table, run `aitp checkpoint` and `aitp closeout` at appropriate moments. No hooks, no MCP, no hidden inference.

2. **One thin `aitp` CLI** — 12 public command groups. Performs deterministic operational work: locate the store, resolve paths, run `rg`, render command guides, create workspaces from templates, validate required fields, show exact staged files and diffs, serialize canonical writes through Git. The CLI does not generate physics insight, choose scientific routes, or summarize hidden conversation state.

3. **Command-local Skills** — each command group owns `aitp/command_skills/<command>/SKILL.md` plus templates and `profile.yaml`. These are NOT registered globally with the host — the CLI renders them only when the command is used. Every command Skill has identical sections: Purpose, Use When, Do Not Use When, Read First, Research Procedure, Files To Produce Or Update, Canonical Effects, Human Decisions, Completeness Checks, Finish And Next Commands.

4. **One local research store** — `.aitp/` with fixed layout: `topics/<id>/` for canonical records, `shared/` for promoted reusable material, `runtime/` for noncanonical working state. All canonical records are Markdown with small YAML frontmatter. Git is the byte history. Seven record types + one Relation type. Store-relative path refs are transparent to Codex, Kimi, humans, `rg`, Git, and the CLI.

The architecture's core insight is that **"reading is context"**: when the CLI outputs Markdown, that output is part of the Agent's conversation — there is no separate context-pack compiler. Command selection is done by the host Agent from visible research intent, not by a hidden CLI classifier.

**Scientific Dreaming** (`aitp knowledge dream`) and **Skill Distillation** (`aitp skill distill`) are two parallel first-class compilation lanes — one for physical understanding, one for repeatable procedure. Both produce reviewed outputs (Knowledge Cards, Workflows/Skills) backed by exact record provenance.

**What makes this different from v5**: v5 has 63+ registry types, MCP servers, hooks, context compilers, L0-L4 state machines, agent dispatchers, and ~168K LOC. AITP 2.0 replaces all of that with 12 command groups, one record contract, Markdown files, `rg`, and Git. The conceptual compression is dramatic — and correct.

---

## P0 Blockers

**None.** All four P0 findings from the 2026-07-19 audit have been resolved:

| Prior P0 | Resolution in 2026-07-20 spec |
|----------|-------------------------------|
| P0-1: Statement kind overloading | Route becomes 7th node type (§6). Statement uses discriminated kind schemas. `system_feedback` is an Asset, not a Statement. |
| P0-2: Commit manifest circular dependency | Field renamed to `payload_paths_and_hashes`, explicitly excludes manifest itself (§14 step 6). Git tree covers manifest bytes. |
| P0-3: TOPIC.md dual truth source | `TOPIC.md` contains only stable material; `aitp enter` derives dynamic output from canonical nodes (§5, §7.1). No dual truth source. |
| P0-4: `aitp review` name collision | `audit` is deterministic; `review` is the human-decision surface with `show\|approve\|reject\|request-changes`. Separation is clear. |

The disposition document (`2026-07-20-aitp-2-0-rewrite-design-audit-disposition.md:54`) correctly records all resolutions. No new P0 issues are introduced by the command-skill redesign.

---

## P1 Important Findings

### P1-1: `using-aitp` Skill specification is incomplete — no concrete trigger recognition

- **Severity**: P1 (blocks S0 fixture creation and S1 `using-aitp` Skill shipping)
- **File:Line**: `2026-07-20-aitp-2-0-command-skill-protocol-design.md:63-85` (§3.1 Using-AITP)
- **Observed fact**: §3.1 lists what `using-aitp` "must" do: trigger on durable research, run `aitp enter`, select phase commands, run checkpoint/closeout, recover missed entry, never infer approval. But these are behavioral requirements, not an implementable Skill spec. The existing v5 `using-aitp` at `plugins/aitp-research-protocol/skills/using-aitp/SKILL.md` (98 lines) is entirely MCP-centric — it references `aitp_v5_codex_autoroute()`, `aitp_config_status()`, `aitp_configure()`, and MCP tools. None of these will exist in 2.0.
- **Real research failure scenario**: A Codex Agent with the 2.0 `using-aitp` Skill encounters a user saying "let me check my NiO band structure results." The Skill says "trigger on durable theoretical-physics research" but provides no concrete pattern for recognizing this as a trigger vs. a typo fix. The Agent either enters too aggressively (on every physics mention) or too conservatively (missing the entry entirely). Without a `semantic_assessment` MCP tool, the v5's `autoroute`-based pattern matching has no replacement.
- **Why spec is insufficient**: §3.1 lines 70-81 are all behavioral "must" statements. They do not provide: (a) a concrete checklist of trigger/non-trigger examples that a Markdown Skill can operationalize, (b) the exact output format of `aitp enter` the Skill should expect, (c) the recovery procedure text for when `aitp` is not installed or the store is broken.
- **Minimum fix**: Add a §3.1 appendix or companion file containing the actual `using-aitp` Skill Markdown content. It must include: trigger examples ("the user asks about prior results for topic X" → enter; "the user asks about a physics concept without mentioning a topic" → do not enter), non-trigger examples ("typo fix", "unrelated shell command"), the exact `aitp enter` invocation, the expected CLI output envelope, the missed-entry recovery procedure, and the durable-moment checklist that triggers `aitp checkpoint`. The existing `plugins/aitp-research-protocol/skills/using-aitp/SKILL.md` is v5-only and cannot be reused without complete rewriting.
- **Complexity increase**: No — this is specification work, not new infrastructure.
- **Phase**: Must be resolved in S0 (before S1 ships the first `using-aitp` Skill).

### P1-2: Command-local `SKILL.md` discovery mechanism is unspecified

- **Severity**: P1 (blocks S1 CLI implementation)
- **File:Line**: `2026-07-20-aitp-2-0-command-skill-protocol-design.md:108-118` (§3.3 Command Skills)
- **Observed fact**: §3.3 specifies that command Skills live at `aitp/command_skills/<command>/SKILL.md` and "the CLI renders it only when the command is used." But it does not specify: (a) where `aitp/command_skills/` is located relative to the store, the package installation, or the working directory, (b) how the CLI discovers this path — is it relative to the `.aitp/` root, the package installation, or a `AITP_HOME` environment variable? (c) whether command Skills are shipped with the CLI package, installed separately, or generated, (d) how versioning works — if the CLI is upgraded but an older `SKILL.md` is on disk, which takes precedence?
- **Real research failure scenario**: An Agent runs `aitp knowledge dream`. The CLI searches for `command_skills/knowledge/SKILL.md` relative to the current working directory but the package was installed via `pip` and the Skills are under `site-packages/aitp/command_skills/`. The CLI reports "command Skill not found" and the Agent has no guide for Scientific Dreaming. The Agent fabricates a Dreaming procedure from general knowledge, producing an invalid Knowledge Card.
- **Why spec is insufficient**: The package boundary is undefined. The old spec (§21, line 1314-1318) says AITP 2.0 "may be implemented permanently as one small Python package" but the 2026-07-20 spec does not address how command Skills are packaged, discovered, or versioned alongside the CLI.
- **Minimum fix**: Add to §3.3: "Command Skills are bundled with the `aitp` package and installed to `<package>/command_skills/`. The CLI resolves them relative to its own installation path. A `SKILL.md` version declared in its frontmatter is compared against the CLI version; a mismatch produces a warning but the bundled Skill takes precedence. For development, `AITP_DEV_COMMAND_SKILLS=<path>` overrides the bundled path." Add a `profile.yaml` example showing the `version` field.
- **Complexity increase**: Minimal — one environment variable and one version comparison.
- **Phase**: Must be resolved in S0 (affects all command rendering code in S1).

### P1-3: Store-relative path refs have no resolution algorithm for `show` without a database

- **Severity**: P1 (blocks S1 `aitp show` implementation)
- **File:Line**: `2026-07-20-aitp-2-0-command-skill-protocol-design.md:324-335` (§6 record contract, store-relative refs)
- **Observed fact**: Store-relative paths like `topics/<topic-id>/statements/<id>.md` require `<topic-id>` and `<id>` to be embedded in the ref string. The spec says these paths are "transparent to Codex, Kimi, humans, `rg`, Git, and the CLI." But the old spec's §7.1 had an explicit path-derivation algorithm (line 458-462):
  ```
  topic:<topic-id>  → .aitp/topics/<topic-id>/TOPIC.md
  <type>:<topic-id>/<id> → .aitp/topics/<topic-id>/<type-plural>/<id>.md
  ```
  The 2026-07-20 spec changed the ref format to `topics/<topic-id>/statements/<id>.md` but removed the explicit path derivation algorithm. The mapping from type to plural directory name (`statement` → `statements/`, `episode` → `episodes/`) is not specified.
- **Real research failure scenario**: An Agent reads a Relation record containing `from_ref: topics/quantum-chaos-long-range-spin-chains/statements/stmt-01K0ABC.md`. It passes this to `aitp show`. The CLI must resolve the path. If the store is at `~/research/.aitp/`, the full path is `~/research/.aitp/topics/quantum-chaos-long-range-spin-chains/statements/stmt-01K0ABC.md`. But the ref uses `statements/` while the store uses `statements/` — this is fine if the ref IS the store-relative path. But the old spec used typed refs (`statement:<topic>/<id>`) that required a mapping. The new spec switched to store-relative paths but did not explicitly restate that the ref text IS the path relative to `.aitp/`. Without this, `aitp show` has no deterministic resolution algorithm.
- **Why spec is insufficient**: The 2026-07-20 spec removed the explicit path derivation from the old spec without replacing it. §6 lines 324-335 give examples but no algorithm. An implementer cannot write `aitp show` from the current text alone.
- **Minimum fix**: Add to §6: "A canonical ref `topics/<topic-id>/<type-plural>/<id>.md` resolves to `.aitp/topics/<topic-id>/<type-plural>/<id>.md`. A shared ref `shared/<type-plural>/<id>.md` resolves to `.aitp/shared/<type-plural>/<id>.md`. The `<type-plural>` directories are: `entities/`, `routes/`, `statements/`, `episodes/`, `assessments/`, `relations/` for the six node types; `knowledge/cards/` for Knowledge Cards; `reuse/workflows/`, `reuse/skill-candidates/`, `reuse/scripts/` for reuse; `code/revisions/`, `code/mappings/` for code; `runs/` for runs; `writing/notes/`, `writing/derivations/`, `writing/reports/`, `writing/articles/`, `writing/presentations/` for writing. A ref ending in `@<git-commit>` pins to that revision; `aitp show` reads the file at that commit via `git show`."
- **Complexity increase**: No — this is a specification of an already-implied mapping.
- **Phase**: Must be resolved in S1 (before `aitp show` implementation).

### P1-4: `aitp closeout` suggestion of `aitp knowledge dream` creates an implicit Dreaming trigger without explicit Agent decision

- **Severity**: P1 (potential for automation creep)
- **File:Line**: `2026-07-20-aitp-2-0-command-skill-protocol-design.md:490-493` (§10.1 Dream)
- **Observed fact**: §10.1 lines 490-493: "`aitp closeout` may suggest `aitp knowledge dream` when the declared session contains several linked insights, a resolved conceptual conflict, or a reusable derivation boundary. This is a visible next-command suggestion, not automatic card generation." This is correctly qualified as a suggestion. However, the triggering conditions ("several linked insights", "resolved conceptual conflict", "reusable derivation boundary") require the CLI to make a semantic judgment about the session's content. The CLI "does not generate physical insight" (§3.2), yet detecting "linked insights" across Episodes is exactly that.
- **Real research failure scenario**: `aitp closeout` scans a session's Episodes and finds three that mention "MBL" (many-body localization). It suggests `aitp knowledge dream`. The Agent follows the suggestion. But the three Episodes are about different MBL regimes with contradictory assumptions — the Agent didn't notice because the suggestion seemed authoritative. The resulting Knowledge Card conflates incompatible regimes without detecting the conflict.
- **Why spec is insufficient**: The deterministic conditions for closeout's Dreaming suggestion need to be based on structural properties (e.g., "3+ Episodes in this session share at least one topic-local ref" or "a new Statement kind=insight was created in this session"), not semantic judgments. The current text at lines 490-493 describes semantic conditions that the CLI cannot detect without becoming an intelligence layer.
- **Minimum fix**: Change lines 490-493 to: "`aitp closeout` suggests `aitp knowledge dream` when at least three new Episodes were created in the current session, or when a new `Statement(kind=insight)` was recorded. The host Agent must assess whether these Episodes contain linked physical insights before invoking `knowledge dream`. The suggestion is advisory and structural, not semantic." This makes the trigger deterministic while keeping the Agent responsible for semantic judgment.
- **Complexity increase**: No — reduces semantic leakage into the CLI.
- **Phase**: Resolve in S2 (closeout implementation) or earlier.

### P1-5: Knowledge Card source binding granularity — `source_reported` can mask untraceable claims

- **Severity**: P1 (blocks S4 Knowledge Card correctness)
- **File:Line**: `2026-07-20-aitp-2-0-command-skill-protocol-design.md:527-537` (§10.2 Knowledge Card assertion binding)
- **Observed fact**: §10.2 specifies three assertion labels: `source_reported` (with exact source and anchor), `aitp_statement` (with exact Statement ref and derived assessment state), and `new_synthesis` (with staged insight Statement). The `source_reported` label requires an "exact source and anchor" — but a Knowledge Card is a synthesis that may combine claims from multiple paragraphs, equations, and figures across a paper. How does the card bind a multi-paragraph synthesis to a single anchor? The spec implies one assertion = one source anchor, but real scientific synthesis combines material.
- **Real research failure scenario**: A Knowledge Card asserts "The MBL transition in the XXZ model occurs at Δ = 1.0 for disorder strength W ≥ 3.5." This combines the XXZ Hamiltonian definition (source A, page 2), the MBL transition criterion (source B, page 7), and the numerical threshold (source C, page 12). The card marks this as `source_reported` with anchor `pdf://source-a#page=2`. A later Agent reads the card, follows the anchor to source A page 2, and finds only the Hamiltonian — the transition criterion and threshold are untraceable. The card's grounding is misleading.
- **Why spec is insufficient**: The `source_reported` label needs a multi-anchor variant or a composite assertion structure. The current one-assertion-one-source model doesn't match how scientific synthesis actually works.
- **Minimum fix**: Add to §10.2 body sections: "A `source_reported` assertion may list multiple `source_refs[]` pointing to exact anchors. The assertion text must indicate which part of the claim comes from which source. A `new_synthesis` assertion may combine source-reported and AITP-statement material; its `basis_refs[]` must enumerate all source anchors and Statement refs used." Rename the single-anchor field to `source_refs[]` (plural) throughout.
- **Complexity increase**: Minimal — one field changes from singular to plural.
- **Phase**: Resolve before S4 (Scientific Dreaming implementation).

### P1-6: Scientific Dreaming flow — `knowledge dream` is a single command but the required Agent workflow is multi-step and underspecified

- **Severity**: P1 (blocks S4 Scientific Dreaming implementation)
- **File:Line**: `2026-07-20-aitp-2-0-command-skill-protocol-design.md:458-488` (§10.1 Dream guide)
- **Observed fact**: §10.1 describes what the Dreaming guide instructs the Agent to do (reread records, separate claims, identify conflicts, create Statements, propose Relations, declare gaps). This is a 7-step workflow that the Agent must execute. But `aitp knowledge dream` is a single command — there is no subcommand structure for the intermediate steps. How does the Agent report progress? How does the CLI validate intermediate outputs? If the Agent writes all workspace files in one pass, the Dreaming workspace is effectively a monolithic output with no incremental validation.
- **Real research failure scenario**: An Agent runs `aitp knowledge dream` on a topic with 50+ Episodes and 30+ Statements. The guide says "reread selected Statements, Episodes, derivations..." but `aitp enter` doesn't pre-select these — the Agent must choose. The Agent reads 8 Episodes, misses 3 that contain contradictory evidence, and produces a Knowledge Card that is factually incomplete. The CLI's `AUDIT.md` checks file structure but cannot detect that 3 relevant Episodes were never read. The card passes audit and is published with gaps.
- **Why spec is insufficient**: The guide describes what the Agent should do but the CLI provides no structural support for coverage assurance. The `knowledge dream` command creates a workspace with `INPUTS.md` — but the spec doesn't say the CLI should pre-populate `INPUTS.md` with candidate records from deterministic search. Without this, the Agent's input selection is unguided and unverifiable.
- **Minimum fix**: Extend the `knowledge dream` command to: (1) pre-populate `INPUTS.md` with a deterministic list of candidate records — all Statements with kind=insight/hypothesis/claim in the topic, all Episodes in the selected time range, all Assessments, all existing Knowledge Cards, and all source anchors referenced by those records, (2) require the Agent to mark each input as `used` or `skipped` with a reason in `INPUTS.md`, (3) add to `AUDIT.md` a check that no Statement tagged as `kind=insight` or `kind=claim` in the topic was omitted without a reason. This makes input selection auditable without requiring the CLI to judge scientific relevance.
- **Complexity increase**: Low — adds one deterministic pre-population step and one audit rule.
- **Phase**: Resolve before S4.

### P1-7: Scenario A context budget — quantum-chaos topic with many Episodes will likely exceed context window during Dreaming

- **Severity**: P1 (blocks S4 pass on the quantum-chaos vertical)
- **File:Line**: `2026-07-20-aitp-2-0-command-skill-protocol-design.md:366-368` (§7.1 enter character budget) and `:474-487` (§10.1 dream guide)
- **Observed fact**: §7.1 sets a "fixed character budget" for `aitp enter`, but no budget is specified for `aitp knowledge dream`. The Dreaming guide instructs the Agent to "reread selected Statements, Episodes, derivations, source anchors, Assessments, failed routes, conventions, and related Knowledge Cards." A real quantum-chaos topic could easily have 20+ Episodes, 15+ Statements, 5+ Assessments, and 3 Knowledge Cards. Full expansion could be 80K-150K tokens. The 2026-07-19 audit's P1-7 (context budget enforcement) was accepted and resolved with a character budget for `enter` — but the resolution did not extend to `knowledge dream`.
- **Real research failure scenario**: The quantum-chaos vertical accumulates 25 Episodes across 3 routes. The Agent runs `aitp knowledge dream`. The `INPUTS.md` lists all 25 Episodes plus 18 Statements. The Agent expands everything. Total context: 180K tokens. The host truncates silently. The Agent produces a Knowledge Card based on only the first 15 Episodes it could fit in context. The card misses critical contradictory evidence from Episodes 16-25. The card passes audit because the audit can't detect context truncation.
- **Why spec is insufficient**: `knowledge dream` has no context budget, no progressive loading mechanism, and no coverage report for what was actually read vs. what was listed in `INPUTS.md`. The "reading is context" model breaks when too much must be read.
- **Minimum fix**: Add to §10.1: "`knowledge dream` pre-populates `INPUTS.md` with a total-character estimate. The Agent must mark each input as `expanded` or `summarized_from_ref`. If the total exceeds the host's estimated context window, the Agent must perform Dreaming in passes: first pass reads all summaries, second pass expands high-priority records, third pass cross-checks. `AUDIT.md` reports the number of records expanded vs. summarized and flags when any Statement kind=insight was only summarized rather than expanded."
- **Complexity increase**: Moderate — adds a two-pass Dreaming protocol and audit rule. Justified by the real risk of silent context truncation in a vertical that the spec itself requires.
- **Phase**: Resolve before S4.

### P1-8: Skill distillation boundaries — `skill distill` vs. `knowledge dream` overlap when physical conventions meet executable procedure

- **Severity**: P1 (blocks S5 Skill lifecycle)
- **File:Line**: `2026-07-20-aitp-2-0-command-skill-protocol-design.md:580-586` (§11 Workflow and Skill compilation) and `:632-634` (Skill referencing Knowledge Cards)
- **Observed fact**: §11 correctly separates scientific meaning (Knowledge) from repeatable procedure (Skill). §11 lines 632-634 state: "A Skill may reference Knowledge Cards as prerequisites or scientific context. Those references do not copy scientific trust into the Skill." This is correct in principle. But the `skill distill` workspace (§11, lines 598-611) includes `WORKFLOW.md`, `APPLICABILITY.md`, and `PROVENANCE.md` — none of which are specified to reference Knowledge Cards explicitly. A Skill that depends on physical conventions (e.g., "this RPA workflow assumes the static Coulomb interaction is screened per convention C1") must encode that dependency somewhere, but the current workspace doesn't have a slot for it.
- **Real research failure scenario**: An Agent distills a LibRPA NiO workflow with the `skill distill` command. The workflow uses the static-screening approximation defined in Knowledge Card `shared/knowledge/cards/kc-rpa-screening.md`. The Agent writes this dependency in `WORKFLOW.md` body text but no structured field links it. Later, the Knowledge Card is superseded by a new card that shows the static screening breaks down for NiO at certain k-points. The Skill's `APPLICABILITY.md` should be updated but there's no structured reference for the CLI to detect the dependency. The Skill becomes silently stale.
- **Why spec is insufficient**: The workspace structure for `skill distill` needs a `KNOWLEDGE_REFS.md` or a structured `knowledge_card_refs[]` field in the Skill's frontmatter or `profile.yaml`. Without this, Knowledge Card → Skill dependencies are invisible to audit and refresh.
- **Minimum fix**: Add to the `skill distill` workspace (lines 598-611): a `KNOWLEDGE_DEPS.md` file listing exact Knowledge Card refs that the Skill depends on. Add to the Skill installation audit: a check that all referenced Knowledge Cards are `current` (not stale, contested, or broken). Add to §11 lines 632-634: "A Skill's `KNOWLEDGE_DEPS.md` lists exact Knowledge Card refs for physical conventions, approximations, and applicability boundaries the Skill assumes. `aitp skill update` checks these refs for staleness; a stale dependency does not block use but produces a visible warning."
- **Complexity increase**: Low — one additional workspace file and one audit rule.
- **Phase**: Resolve before S5.

### P1-9: Complete absence of fixture data for required verticals — S0 cannot freeze against nothing

- **Severity**: P1 (blocks S0 freeze)
- **File:Line**: `2026-07-20-aitp-2-0-command-skill-protocol-design.md:802-804` (§17 S0 freeze) and `:755-792` (§16 Required End-To-End Verticals)
- **Observed fact**: §17 S0 requires "write quantum-chaos, NiO, shared-paper, Knowledge Card, and Skill fixtures." §16 requires three end-to-end verticals (quantum chaos, NiO, multi-topic reuse). But the repository contains ZERO real research data: `.aitp/topics/` is empty, `.aitp/registry/` has 52 empty subdirectories, no `quantum-chaos-long-range-spin-chains/` directory exists anywhere, no NiO topic exists, no `TOPIC.md` exists anywhere in the repository. The only research-like content is `tmp/nl-test-topics/nl-test-qsgw/` — a v0.6-era QSGW test topic with L0-L4 structure that does not conform to the 2.0 record contract.
- **Real research failure scenario**: S0 attempts to write quantum-chaos fixtures. The fixture author has no real Episodes, Statements, or Routes to work from. They invent plausible-but-fictional physics content. The fixtures pass syntactic validation but encode patterns that don't match real research — e.g., they assume Routes are linear when real quantum-chaos research has branching dead ends, or they assume source anchors are always available when real preprints lack clean extractions. The 2.0 protocol is frozen against fixtures that don't represent real research, and the S3/S4 verticals fail because the real research patterns weren't captured in the fixture-based contract.
- **Why spec is insufficient**: §17 says "write ... fixtures" but doesn't say where the fixture content comes from. If there are real quantum-chaos and NiO research directories on the user's machine (the old audit mentioned `F:/AI_Workspace/Theoretical-Physics/research/hs-like-chaos-window` and `F:/AI_Workspace/Theoretical-Physics/research/librpa` at lines 8-9), the spec should require that these real directories be used as the source for fixtures — or explain that they will be. Currently the spec is silent on fixture provenance.
- **Minimum fix**: Add to §17 S0: "Fixtures are constructed from the existing research directories `F:/AI_Workspace/Theoretical-Physics/research/hs-like-chaos-window` (quantum chaos) and `F:/AI_Workspace/Theoretical-Physics/research/librpa` (NiO), plus any new 2.0-conformant content generated during a controlled S0 pilot session. Fixture content must represent real physics questions, real dead ends, and real code provenance rather than idealized linear research." If those directories don't contain enough material, the spec must acknowledge that S0 will create initial topic structures from available notes and mark them as `status: seeding` rather than `status: frozen`.
- **Complexity increase**: No — this is a process requirement, not new code.
- **Phase**: Must be resolved before S0 begins.

---

## P2 Suggestions

### P2-1: 12 command groups — `aitp literature` and `aitp research` have overlapping "study/investigate" semantics

- **File:Line**: `2026-07-20-aitp-2-0-command-skill-protocol-design.md:155-168` (§4 public commands table)
- **Observation**: `aitp research` supports modes including `deep-research`. `aitp literature` supports `study`. Both involve reading papers and recording findings. The distinction is that `research` is for open-ended investigation and `literature` is for focused paper study — but in practice, most literature study IS open-ended investigation. An Agent deciding between `aitp research begin --mode deep-research` and `aitp literature study` faces ambiguity.
- **Recommendation**: Do not merge now. The command-skill architecture handles this through the guide's "Use When / Do Not Use When" sections — the Agent reads the guide and decides. If usage data from R4/R5 shows confusion, consider making `literature study` a mode of `research` in 2.1. Defer with a note in the spec.
- **Complexity**: No change needed now.

### P2-2: `aitp write` output formats — `presentation` is underspecified relative to `article` and `report`

- **File:Line**: `2026-07-20-aitp-2-0-command-skill-protocol-design.md:671-682` (§13 Writing Products)
- **Observation**: `note`, `derivation`, `report`, and `article` have clear LaTeX/Markdown output formats. `presentation` (line 671) has no format specification — is it Beamer LaTeX, Marp Markdown, PowerPoint, or Reveal.js? Without a format, the writing workspace can't provide a meaningful template.
- **Recommendation**: Specify presentation format as "Beamer LaTeX or Marp Markdown, selected by the topic convention declared in `TOPIC.md`." Add a `presentation_format` field to `TOPIC.md` conventions.
- **Complexity**: Minimal — one field addition.

### P2-3: `run` records — no explicit `run_id` format or linking to code revisions

- **File:Line**: `2026-07-20-aitp-2-0-command-skill-protocol-design.md:659-668` (§12.3 Runs and HPC)
- **Observation**: Run records must "identify exact command or script, code revision, environment, inputs, outputs..." but no record type is defined. The old spec had `Asset(kind=run_manifest)` with specific fields. The 2026-07-20 spec says runs live under `topics/<id>/runs/` but doesn't specify the record structure.
- **Recommendation**: Add a run record template to §12.3 or reference it as an Asset kind with required fields: `code_revision_ref`, `command`, `environment_ref`, `input_paths[]`, `output_paths[]`, `status`, `validation`, `failure_description`. This doesn't add a new node type — it's a kind-specific Asset.
- **Complexity**: Low — just needs specification, not new infrastructure.

### P2-4: Store initialization — `aitp admin init` is implied but never specified

- **File:Line**: `2026-07-20-aitp-2-0-command-skill-protocol-design.md:167` (§4 public commands, `aitp admin`)
- **Observation**: `aitp admin` handles "doctor, initialize, migrate, back up, recover." But the initialization procedure — creating `.aitp/` with the correct directory structure, initializing Git, writing `STORE.md` — is never described. The `enter` command must handle the case where `.aitp/` doesn't exist (first use).
- **Recommendation**: Add a §5 appendix or admin section specifying `aitp admin init`: creates `.aitp/STORE.md`, initializes `topics/`, `shared/`, `runtime/` directories, and runs `git init` if `.aitp/` is its own repository (or adds a `.gitkeep` if the store is tracked within a parent repo). The `enter` command should detect a missing store and direct the user to `aitp admin init`.
- **Complexity**: Low — typical CLI init command.

### P2-5: Topic ID format — human-readable slugs are specified but no collision strategy

- **File:Line**: `2026-07-20-aitp-2-0-command-skill-protocol-design.md:220-283` (§5 Fixed File Layout, implied by directory structure)
- **Observation**: Topic directories use `<topic-id>` as the directory name. The old spec said "Topic IDs are stable human-readable slugs" (line 440). But the 2026-07-20 spec doesn't address what happens when two topics would naturally have the same slug (e.g., two different "MBL-transition" projects). Slug collision would cause directory conflicts.
- **Recommendation**: Add to §5: "Topic IDs are unique within a store. When a new topic's natural slug conflicts with an existing topic, the CLI appends a disambiguating suffix (e.g., `mbl-transition-2`). The human may override the ID during `aitp admin topic init`."
- **Complexity**: Trivial.

### P2-6: Knowledge Card health — `stale/contested/broken` detection requires active scanning that has no trigger

- **File:Line**: `2026-07-20-aitp-2-0-command-skill-protocol-design.md:561-572` (§10.3 Card health)
- **Observation**: Card health is derived as `current/stale/contested/broken`. But the derivation requires scanning: "newer superseding Statements or sources make a card stale; applicable contradictory assessments make it contested; missing refs or failed source anchors make it broken." This scanning has no scheduled trigger — it's not part of `enter`, `checkpoint`, or `closeout`. The spec says `enter` includes a card only when explicitly named (§10.3 lines 574-576), so stale detection is deferred to the moment the card is used. By then, the Agent may have already based decisions on it.
- **Recommendation**: Add to `aitp checkpoint`: "When a checkpoint creates a new Statement, Assessment, or source link, the CLI checks whether any Knowledge Card in the same topic has a `source_ref` or `statement_ref` affected by the new record. If so, the checkpoint output includes a 'potentially stale Knowledge Cards' warning." This makes staleness detection event-driven rather than scan-deferred.
- **Complexity**: Low — one additional check in the checkpoint audit.

### P2-7: `profile.yaml` format — referenced but never defined with an example

- **File:Line**: `2026-07-20-aitp-2-0-command-skill-protocol-design.md:114` (§3.3 command skills) and `:138-139` (profile.yaml description)
- **Observation**: §3.3 says `profile.yaml` "contains only deterministic requirements that the CLI can check." But no example is given. Without a concrete example, every command Skill author will invent their own format, and the CLI's profile validation will be inconsistent across commands.
- **Recommendation**: Add a `profile.yaml` example to §3.3:
  ```yaml
  command: knowledge
  version: 1.0.0
  requires_topic: true
  allowed_write_roots: [runtime/workspaces/knowledge/, topics/<topic>/knowledge/cards/]
  required_outputs: [CARD.md, INSIGHTS.md, RECORD_CHANGES.md]
  human_gates: [knowledge_card_publication, shared_promotion]
  audit_rules: [frontmatter_completeness, ref_existence, source_anchor_validity]
  ```
- **Complexity**: No — this is documentation, not new code.

---

## Command-by-Command Audit

### `aitp enter`
- **Status**: Design-complete for orientation. Missing: store initialization handling (first use), topic creation flow when no topics exist, exact character budget value (the old spec had 8000 chars at line 825; the new spec says "fixed character budget" at line 366 without the number).
- **Risk**: Without a concrete budget, different implementations will choose different defaults, making Codex/Kimi behavior inconsistent.
- **Fix**: Restore the 8000-character default from the old spec §11.1.

### `aitp search`
- **Status**: Design-complete. `rg`-based with scope controls, coverage reporting, and frontmatter/body distinction (inherited from P1-2 resolution). Missing: the `--legacy` scope for old-store search (required by §17 S0 "keep old records byte-identical and searchable through a read-only adapter").
- **Risk**: The legacy search adapter is mentioned but not specified — it needs a separate search path for `.aitp-legacy/`.
- **Fix**: Add `aitp search --scope legacy` to §7.2.

### `aitp show`
- **Status**: Design-complete in concept, blocked by P1-3 (path resolution algorithm missing). The `@<git-commit>` pinning is specified but the base path derivation is not.
- **Risk**: Cannot implement without P1-3 resolution.

### `aitp research`
- **Status**: Design-complete. Six modes, clear workspace structure, mode-specific guides. The mode-to-guide mapping is clear.
- **Minor note**: The `deep-research` mode implies web searching, but the CLI provides only workspace scaffolding — the Agent brings its own web tools. This boundary is correctly maintained.

### `aitp literature`
- **Status**: Design-complete for the one-copy model. The extraction immutability and content-addressed anchors are correctly specified (inherited from P1-5 resolution in the old audit). Missing: the `add` subcommand must handle the case where the PDF is behind a paywall and only metadata is available — the spec should allow `source.pdf` to be absent with `access: restricted` in `SOURCE.md`.
- **Risk**: Minor — all real papers have at least arXiv preprints.

### `aitp checkpoint`
- **Status**: Design-complete. Clear durable-moment triggers, clear separation from closeout (inherited from P1-6 resolution). The checkpoint creates "the smallest set of records that preserves the event" — this is a good minimality constraint.
- **Minor note**: The spec doesn't say whether checkpoint can be called multiple times in one session for different events. It should: "checkpoint is idempotent per event — calling it twice for the same workspace produces a warning, not a duplicate Episode."

### `aitp closeout`
- **Status**: Design-complete. The completeness sweep over declared session workspaces is correctly scoped. The "no empty Episode" rule is important.
- **Risk**: P1-4 (closeout's Dreaming suggestion semantic leakage).

### `aitp knowledge`
- **Status**: Architecture-complete as a first-class lane. Subcommands `dream|refresh|link|finish` are well-scoped. Blocked by P1-5 (assertion binding), P1-6 (workflow underspecification), P1-7 (context budget).
- **Strong**: The immutability of published cards and the `supersedes` Relation for refresh are correctly designed. Card health derivation is sound in concept but needs P2-6 (trigger mechanism).

### `aitp skill`
- **Status**: Architecture-complete as a parallel lane to knowledge. Subcommands `distill|package|install|update|rollback` are well-scoped. Blocked by P1-8 (Knowledge Card dependency tracking).
- **Strong**: The human-review requirement for install, update, and rollback is correctly gated. The install receipt design (inherited from P2-3 resolution) is sound.

### `aitp write`
- **Status**: Design-complete for note, derivation, report, article. Presentation format underspecified (P2-2). The citation/ref integrity check is correctly scoped as a CLI responsibility without making the CLI a prose generator.

### `aitp audit`
- **Status**: Design-complete as deterministic pre-commit validation. The audit rule set is correctly scoped to structural and provenance checks, not scientific judgment.

### `aitp admin`
- **Status**: Under-specified. Only names are listed: "doctor, initialize, migrate, back up, recover, and inspect configuration." No subcommand descriptions, no expected outputs, no error handling. This is acceptable for S0-S1 (admin is low-priority for research use) but must be specified before S7 release.
- **Risk**: Low for early phases; becomes P1 if still unspecified at S6.

---

## Directory And Record Audit

### Fixed Layout Assessment
The layout at §5 is sound and maps cleanly to filesystem operations:

| Path | Purpose | Verdict |
|------|---------|---------|
| `.aitp/STORE.md` | Store identity | Correct — single point of store identification |
| `topics/<id>/TOPIC.md` | Stable topic orientation | Correct — P0-3 resolution ensures no route state leakage |
| `topics/<id>/entities/` through `relations/` | 7 node types | Correct — plural names match type-to-directory convention |
| `topics/<id>/sources/notes/` | Source notes | Correct — one level, no deep nesting |
| `topics/<id>/knowledge/cards/` | Topic-local Knowledge Cards | Correct — separate from shared |
| `topics/<id>/reuse/` | Topic-local reuse | Correct — workflows, skill-candidates, scripts are three kinds of reuse |
| `topics/<id>/code/` | Code provenance | Correct — revisions and mappings are the two code concerns |
| `topics/<id>/runs/` | Run records | Correct — flat directory |
| `topics/<id>/writing/` | Writing products | Correct — five product types, each a directory |
| `shared/library/papers/` | One-copy paper store | Correct — source ID directories with PDF, SOURCE.md, extractions |
| `shared/knowledge/cards/` | Shared Knowledge Cards | Correct — separate from topic-local |
| `shared/workflows/` | Shared workflows | Correct |
| `shared/scripts/` | Shared scripts | Correct |
| `runtime/workspaces/` | Command workspaces | Correct — `<command>/<workspace-id>/` pattern |
| `runtime/staging/` | Pre-commit staging | Correct |
| `runtime/indexes/` | Optional indexes | Correct — disposable |
| `runtime/recovery/` | Crash recovery | Correct |
| `runtime/local.toml` | Machine-local config | Correct — not canonical |

**Issue**: The `code/` directory has `revisions/` and `mappings/`. A code revision is an Asset — it should live under a canonical record directory, not a separate `code/` top-level. The `code/revisions/` directory is a topic-level directory that doesn't correspond to any of the seven node types. Recommendation: either make `code/revisions/` store `Asset(kind=code_revision)` records (which belong under `assets/` if `assets/` existed as a directory — but it doesn't in the 2026-07-20 layout), or clarify that `code/revisions/` is the canonical location for `Asset(kind=code_revision)` records and add `assets/` as a type plural directory under `topics/<id>/`.

**Revised recommendation**: The 2026-07-20 layout dropped `assets/` from the old spec's layout (old spec §5.1:162 had `assets/`). The new layout has `code/revisions/`, `code/mappings/`, `runs/`, `knowledge/cards/`, `reuse/`, and `writing/` — but no `assets/` directory for source notes, scripts, datasets, figures, tables, reports, patches, install receipts, etc. This is a gap. The old spec's `assets/` directory covered 18+ Asset kinds. The new spec distributes specific Asset kinds to purpose-specific directories (knowledge cards → `knowledge/cards/`, workflows → `reuse/workflows/`) but doesn't say where generic Assets live.

**Recommendation**: Add `assets/` to the topic layout for Asset kinds that don't have a purpose-specific directory (source notes, scripts, datasets, figures, tables, reports, code revisions, patches, run manifests, install receipts, problem dossiers). Or, explicitly map every Asset kind to a directory and remove the need for `assets/`. The current layout is missing this mapping.

### Record Contract Assessment

The seven record types + Relation cover the required research semantics:

| Type | Coverage | Gaps |
|------|----------|------|
| `topic` | Stable orientation | None |
| `entity` | Physical/mathematical/software objects | None |
| `route` | Research planning, state, dependencies | None (P0-1 resolved) |
| `statement` | Epistemic content (8 kinds) | None (P0-1 resolved) |
| `episode` | Bounded research events (10 kinds) | `hpc_run` kind overlaps with `run` Asset — an Episode is the event, an Asset(kind=run_manifest) is the durable output. This is correctly separated. |
| `assessment` | Append-only evaluation | None |
| `asset` | Durable research artifacts | Kind mapping to directories is incomplete (see above) |
| `relation` | Typed edges | Predicate vocabulary (18 values) is comprehensive without bloat |

**Verdict**: The record model is minimal and sufficient. The only gap is the Asset directory mapping.

---

## Scientific Dreaming Audit

### Dream As A Complete CLI Flow

The `aitp knowledge` lane has four subcommands:

1. **`dream`**: Creates a workspace, selects inputs, guides the Agent through synthesis. The output is a draft Knowledge Card plus supporting files.
2. **`refresh`**: Creates a new card with a `supersedes` Relation. Old card remains immutable.
3. **`link`**: Adds Relations between an existing card and topic records.
4. **`finish`**: Finalizes the workspace, runs audit, stages for human review.

This is a complete flow. The immutability of published cards plus `supersedes` for refresh is the correct design for scientific memory — it preserves provenance without rewriting history.

### Knowledge Card Generation Conditions

The spec describes when Dreaming is appropriate (§10.1 lines 490-493 — with P1-4 caveat) but doesn't specify when it is NOT appropriate. A card should NOT be generated when:
- The topic has fewer than 3 Episodes (insufficient synthesis material).
- All Statements in scope are `kind=question` or `kind=open_gap` (no conclusions to synthesize).
- The Agent cannot identify at least one source anchor or AITP Statement for every assertion.
- The card's `question` field cannot be stated as one bounded question.

**Recommendation**: Add a "Do Not Dream When" section to the knowledge command Skill (these conditions come from the Skill, not the spec — but the spec should note them).

### Input Selection

As noted in P1-6, input selection is currently unguided. The fix (pre-populating `INPUTS.md` with deterministic candidates) addresses this.

### Proposition Binding

As noted in P1-5, single-anchor binding is insufficient for synthetic assertions. The fix (plural `source_refs[]`) addresses this.

### Human Review Boundary

The spec correctly states that "Approving a card means that its synthesis, sourcing, labels, and boundaries are acceptable research memory. Approval does not validate every contained Statement or convert source-reported content into an AITP conclusion" (§10.2 lines 535-537). This is the single most important boundary in the Scientific Dreaming design — and it's correctly drawn.

### Card Health

The four-state model (`current/stale/contested/broken`) is correct. P2-6 recommends adding event-driven detection triggers.

### Context Usage

As noted in P1-7, context budget for Dreaming is unmanaged. The fix (two-pass protocol with audit) addresses this.

---

## Skill Lifecycle Audit

### Distillation Flow

The `skill distill` command creates a workspace with 10 files (§11 lines 598-611). This is significantly more structured than the Knowledge Card workspace — and correctly so, because executable procedures need more verification.

### Skill And Knowledge Boundary

The parallel lanes (§11 lines 583-586) are correctly designed:
- Scientific meaning → `aitp knowledge` → Knowledge Card
- Repeatable procedure → `aitp skill` → Workflow and installed Skill

The addition of `KNOWLEDGE_DEPS.md` (P1-8) closes the gap between them.

### Install, Update, Rollback

The install→receipt→update→rollback cycle is correctly designed:
- Install requires human approval and writes a receipt with before/after hashes.
- Update is a new reviewed transaction, not an overwrite.
- Rollback is a new install of the prior package, not a deletion.

The one gap: rollback doesn't specify whether it restores to the immediate prior version or to any prior version identified by install receipt. The spec should clarify: "`aitp skill rollback <install-ref>` restores the Skill to the exact package Asset recorded in the named install receipt. To roll back further, chain rollback commands or specify the earlier receipt."

### Applicability Boundaries

The `APPLICABILITY.md` in the distill workspace is correctly required. However, there's no requirement that `APPLICABILITY.md` be machine-checkable — it's currently free-form Markdown. For HPC skills, a machine-checkable precondition (e.g., "requires Slurm with GPU partition") would be valuable.

**Recommendation**: Add to the `APPLICABILITY.md` guide: "Preconditions that can be checked by the CLI (Slurm availability, Python version, required executables) should be listed in a structured YAML block within `APPLICABILITY.md`. The CLI may check these during `skill install` and warn if they are not met."

### HPC Constraints

The `PROVENANCE.md` in the distill workspace should include explicit HPC constraints: required scheduler, queue, GPU type, memory, walltime, and environment modules. This is research-critical for reproducibility — a Skill that "runs on HPC" without specifying the HPC environment is not reproducible.

**Recommendation**: Add to the `PROVENANCE.md` guide: "For HPC-dependent Skills, record: scheduler type and version, required queue/partition, GPU model and count, minimum memory per node, typical walltime, and environment module list with versions."

### Verification

The `TESTS.md` in the distill workspace is correctly required. But the spec doesn't say what constitutes a valid test for a research Skill. A research Skill is not a software library — its "test" might be "runs successfully on the known NiO 2×2×2 supercell and reproduces the band gap to within 0.1 eV."

**Recommendation**: Add to the `TESTS.md` guide: "Tests for a research Skill are validation Episodes that exercise the workflow on known inputs and check outputs against known results. At minimum, one success case and one known failure case must be documented."

---

## Two Vertical Walkthroughs

### Scenario A: Quantum Chaos Long-Range Spin Chains

**Setup**: Topic exists with 5 Routes, 15 Episodes, 10 Statements, 3 papers in `shared/library/`, 2 source extractions.

**Step-by-step**:

1. **Entry**: User says "Let's continue the MBL route." Agent runs `aitp enter --cwd .`. CLI reads `TOPIC.md`, lists 5 active routes, shows MBL route as priority 1 with next action "study arXiv:2401.xxxxx for finite-size scaling." Context: ~3000 chars.

2. **Literature study**: Agent runs `aitp literature study --source-id arxiv-2401.xxxxx`. CLI creates a workspace with paper-specific guide, extraction, and source notes. Agent reads the paper, identifies Section 3.2's scaling ansatz, writes source notes with exact anchors.

3. **Derivation**: Agent runs `aitp research begin --mode derivation`. CLI creates workspace. Agent derives the finite-size scaling form from the paper's ansatz, writes `RESULTS.md` with LaTeX derivation.

4. **Failed hypothesis**: During derivation, Agent realizes the ansatz assumes power-law scaling but numerical evidence suggests logarithmic corrections. Agent runs `aitp checkpoint` with a `Statement(kind=hypothesis, status=withdrawn)` recording "power-law scaling ansatz fails for L < 20."

5. **Closeout**: Agent runs `aitp closeout`. CLI scans session workspaces, detects 1 new Episode (derivation), 1 new Statement (withdrawn hypothesis), 1 modified source note. Reports: "Consider `aitp knowledge dream` — this session contains a resolved conflict between literature ansatz and numerical evidence." (But see P1-4 — the CLI shouldn't semantically detect "resolved conflict"; the fix makes this structural.)

6. **Scientific Dreaming**: Agent accepts suggestion, runs `aitp knowledge dream`. CLI pre-populates `INPUTS.md` with 15 Episodes, 10 Statements, 2 source anchors (P1-6 fix). Agent reads inputs in two passes (P1-7 fix), identifies cross-record insight: "The power-law vs. logarithmic-correction conflict appears in 3 Episodes across Routes R1, R3, and R5." Agent writes `CARD.md` with `card_form=comparison`, `question="Is finite-size scaling in long-range spin chains power-law or logarithmic?"`, assertion labels using `source_refs[]` (P1-5 fix).

7. **Human review**: Agent runs `aitp knowledge finish`. CLI stages `CARD.md` and proposed `Statement(kind=insight)` and Relations. Human reviews exact bytes via `aitp review show`. Human approves. CLI commits.

8. **Write note**: Agent runs `aitp write note`. CLI creates writing workspace with the new Knowledge Card, relevant Statements, and source anchors as allowed claims. Agent writes a theory note in LaTeX.

**Reads at each step**:
- Step 1: `TOPIC.md`, 5 route files (summaries only), Must Read refs
- Step 2: `SOURCE.md`, `source.pdf` (host reads), extraction `anchors.jsonl`
- Step 3: Route file, prior derivation Episodes, source notes
- Step 4: Current workspace files
- Step 5: Session workspace manifests
- Step 6: 15 Episodes (2-pass: summaries then 5 expanded), 10 Statements, 2 source anchors, 1 existing Knowledge Card
- Step 7: Staged files
- Step 8: Knowledge Card, 3 Statements, 2 source anchors

**Canonical files created/modified**:
- `topics/quantum-chaos/statements/stmt-{id}.md` (withdrawn hypothesis)
- `topics/quantum-chaos/episodes/ep-{id}.md` (derivation)
- `topics/quantum-chaos/episodes/ep-{id}.md` (closeout sweep Episode)
- `topics/quantum-chaos/knowledge/cards/kc-{id}.md` (Knowledge Card)
- `topics/quantum-chaos/statements/stmt-{id}.md` (insight Statement)
- `topics/quantum-chaos/relations/rel-{id}.md` ×3 (card→sources, card→statements, card→episodes)
- `topics/quantum-chaos/writing/notes/note-{id}.md` or external `.tex` file

**Human review points**: Knowledge Card publication (step 7).

**Potential failure points**:
- Step 6 context budget (P1-7): if 15 Episodes are large, two-pass protocol mitigates.
- Step 4 checkpoint: if Agent doesn't explicitly checkpoint the failed hypothesis, closeout captures it only if the workspace is still open. If the Agent closed the derivation workspace before checkpointing, the hypothesis is lost. **The spec should say: `aitp research finish` automatically prompts for checkpoint if results include a withdrawn/contradicted claim.**

### Scenario B: LibRPA / NiO

**Setup**: Topic exists with LibRPA repository at `~/librap/`, commit `a1b2c3d`, 3 prior runs recorded.

**Step-by-step**:

1. **Entry**: Agent runs `aitp enter --cwd ~/librap`. CLI identifies topic `librpa-magnetic-nio`, reads `TOPIC.md`, shows active route "k444 frontier-inversion diagnostic" with next action "reproduce band-108 collapse at U=5.0 eV."

2. **Code record**: Agent runs `aitp research begin --mode code`. CLI creates workspace. Agent identifies the current HEAD commit, formula-to-code mapping for the RPA polarization function, and an uncommitted patch that changes the k-point mesh. Agent records `Asset(kind=code_revision)` for commit `a1b2c3d` and `Asset(kind=working_tree_snapshot)` for the dirty patch with k-point changes. Agent writes formula→code mapping as a Relation: `Statement(kind=definition, title="RPA Polarization")` → `implements` → `Asset(kind=code_revision)` with `blob_hash` and `symbol=Polarization::compute()`.

3. **HPC run**: Agent runs `aitp research begin --mode hpc`. CLI creates workspace. Agent writes the Slurm script, records the HPC host profile, submits the job, and records the job ID. The run completes with unexpected results — band 108 collapses at U=3.2 eV, not U=5.0 eV. Agent runs `aitp checkpoint`, records `Episode(kind=hpc_run)` with status `failed_to_reproduce` and `Asset(kind=run_manifest)` with exact command, inputs, outputs, and failure description.

4. **Failed run analysis**: Agent creates a new `Statement(kind=hypothesis, status=proposed)`: "The earlier collapse at U=5.0 eV may have been an artifact of the coarse k-point mesh — the new finer mesh reveals collapse at lower U." Agent links this to the run via Relation `derived_from`.

5. **Workflow distillation**: Agent realizes the k-point convergence test procedure is repeatable. Runs `aitp skill distill`. CLI creates workspace. Agent writes `WORKFLOW.md`: step-by-step procedure for k-point convergence testing in LibRPA NiO. Identifies required inputs (structure file, pseudopotentials, U value, k-point list), ordered actions (SCF → RPA → band structure → collapse detection), validation checks (band gap monotonicity, collapse U convergence), known failures (metalization at very fine k-meshes, need for SOC corrections), applicability boundaries (only for rocksalt NiO, only with NCPP pseudopotentials). Agent writes `TESTS.md` with one success case (reproduces known 2×2×2 result) and one failure case (8×8×8 metalization). Agent writes `PROVENANCE.md` linking to the 3 prior run Episodes. Agent writes `KNOWLEDGE_DEPS.md` referencing Knowledge Card `kc-nio-screening-convention` (P1-8 fix).

6. **Skill packaging**: Agent runs `aitp skill package <candidate-ref>`. CLI validates structure, exact refs, package files, tests, installation targets. CLI reports package ready for review.

7. **Human review and install**: Human runs `aitp review show <package-ref>`, reviews `WORKFLOW.md`, `TESTS.md`, `APPLICABILITY.md`, `PROVENANCE.md`. Human approves. Agent runs `aitp skill install <package-ref>`. CLI installs Skill to `.agents/skills/aitp-generated/nio-kpoint-convergence/`, writes install receipt `Asset(kind=install_receipt)` with before/after hashes.

8. **Rollback**: Later, the Skill is found to have an error in the U-value range. Human runs `aitp skill rollback <install-receipt-ref>`. CLI restores the previous package from the receipt, writes a new receipt documenting the rollback.

**Reads at each step**:
- Step 1: `TOPIC.md`, route files
- Step 2: `git log`, repository files, formula Statement
- Step 3: Slurm script, host profile, HPC output files, prior run records
- Step 4: Failed run Episode, prior success Episodes
- Step 5: 3 prior Episodes, run manifests, code revisions, Knowledge Card `kc-nio-screening-convention`
- Step 6: Distill workspace files
- Step 7: Staged package files, target directory diff
- Step 8: Install receipt Asset, prior package Asset

**Canonical files created/modified**:
- `topics/librpa-magnetic-nio/code/revisions/asset-{id}.md` (code revision)
- `topics/librpa-magnetic-nio/code/mappings/rel-{id}.md` (formula→code)
- `topics/librpa-magnetic-nio/runs/asset-{id}.md` (run manifest)
- `topics/librpa-magnetic-nio/episodes/ep-{id}.md` (HPC run Episode)
- `topics/librpa-magnetic-nio/statements/stmt-{id}.md` (hypothesis)
- `topics/librpa-magnetic-nio/relations/rel-{id}.md` ×3
- `topics/librpa-magnetic-nio/reuse/workflows/wf-{id}.md` (Workflow)
- `topics/librpa-magnetic-nio/reuse/skill-candidates/sk-{id}/` (Skill candidate)
- `topics/librpa-magnetic-nio/assets/asset-{id}.md` (install receipt) — assumes `assets/` exists
- `shared/workflows/wf-{id}.md` (if promoted to shared)
- Install target directory with `SKILL.md`, host metadata, scripts

**Human review points**: Skill package approval and installation (step 7), rollback (step 8).

**Potential failure points**:
- Step 2 formula→code mapping: if the formula Statement doesn't exist yet, the Agent must create it first. The `code` research mode guide should check for this.
- Step 3 HPC run: the HPC host profile must be pre-configured. If the Agent is on a different machine, `runtime/local.toml` must have the correct host profile mapping. The spec should require `aitp admin doctor` to validate host profiles.
- Step 5 Skill distillation: if the 3 prior Episodes don't have clean run manifests (e.g., they were recorded before 2.0), the provenance chain is incomplete. The `skill distill` guide must handle incomplete provenance.
- Step 6 skill packaging: if the Skill package contains host-specific metadata (Codex vs. Kimi), the packaging step must validate that the correct host adapter is present. The spec doesn't address multi-host Skill packaging.

---

## Legacy Reuse And Removal Matrix

### Reuse — v5 code directly usable in AITP 2.0

| v5 module | Reusable? | Reason |
|-----------|-----------|--------|
| YAML frontmatter parsing (any existing implementation) | Yes | Same Markdown+YAML format. Any robust YAML+Markdown parser works. |
| `brain/v5/record_refs.py` (ref parsing) | Partial | The ref format changed from typed (`statement:<topic>/<id>`) to store-relative (`topics/<id>/statements/<id>.md`). Parsing logic needs adaptation but the concept is identical. |
| `brain/v5/` Git commit/CAS logic | Partial | The CAS commit protocol (§14) is similar to v5's checkpoint commit logic. The lock+compare-and-swap code may be adaptable. |
| `scripts/aitp-pm.py` | No (for 2.0) | This is a v5 package manager that installs MCP servers and hooks. AITP 2.0 has no MCP or hooks, so the package manager is completely different. A new, simpler installer is needed. |
| `schemas/` JSON schemas | No | v5 schemas describe 63+ record types with L0-L4 fields. 2.0 uses 7 node types with one small contract. New schemas needed. |
| `brain/v5/skill_facade.py`, `skill_models.py` | No | v5 Skill system is tied to MCP tools, domain packs, and L0-L4 lifecycle. 2.0 Skills are Markdown-only with a different lifecycle. |
| `brain/v5/knowledge_facade.py`, `knowledge_retrieval.py` | No | v5 knowledge is tied to RAG, context packs, and automatic promotion. 2.0 knowledge is command-guided Scientific Dreaming. |
| `brain/v5/context_compiler.py` | No (delete from 2.0) | Explicitly absent from 2.0. "Reading is context" replaces it. |
| `brain/v5/hooks.py`, all `hook_*.py` | No (delete from 2.0) | Explicitly absent from 2.0. Zero required hooks. |
| `brain/v5/mcp_tools.py`, `mcp_*.py`, `native_mcp.py` | No (delete from 2.0) | Explicitly absent from 2.0. Zero MCP servers. |
| `brain/v5/host_lifecycle_*.py` | No (delete from 2.0) | v5 lifecycle routing is replaced by `using-aitp` Skill + CLI. |
| `brain/v5/execution_facade_*.py` | No (delete from 2.0) | v5 execution facade is an Agent runtime. 2.0 has no Agent runtime. |
| `brain/v5/legacy_bridge.py`, `legacy_*.py` | Read-only reference | The legacy bridge logic for reading old `.aitp-legacy/` records may inform the 2.0 read-only legacy adapter. The adapter must be written fresh for the 2.0 record contract. |
| `brain/v5/domain_packs.py` | No (delete from 2.0) | Domain packs are v5's way of bundling topic-specific skills. 2.0 uses topic-local command guides. |
| `adapters/*/SKILL.md` | No (rewrite for 2.0) | All five existing adapters reference MCP tools and hooks. They need complete replacement with `using-aitp` Skill content that uses only CLI commands. |
| `plugins/aitp-research-protocol/skills/using-aitp/SKILL.md` | No (rewrite for 2.0) | 98 lines, entirely MCP-centric. Must be rewritten per P1-1. |
| `templates/` LaTeX templates | Yes (unchanged) | Research paper templates are independent of the protocol. They can be used as-is or referenced by `aitp write` guides. |
| `contracts/` Markdown contracts | No (superseded) | v5 contracts describe L0-L4 protocol operations. 2.0 uses command-local `SKILL.md` guides instead. |

### Removal — v5 code that must NOT enter 2.0 package

These directories and modules are explicitly excluded by the 2.0 simplicity ratchet (§15.1):

| Path | Reason for exclusion |
|------|---------------------|
| `brain/mcp_server.py` (331KB) | MCP server — explicitly absent |
| `brain/v5/native_mcp.py` | MCP server — explicitly absent |
| `brain/v5/mcp_tools.py`, all `mcp_*.py` (~40 files) | MCP tools — explicitly absent |
| `brain/v5/hooks.py`, all `hook_*.py`, `hooks/` directory (~20+ files) | Host hooks — explicitly absent |
| `brain/v5/context_compiler.py`, all `context_*.py` (~15 files) | Context compiler — explicitly absent |
| `brain/v5/host_lifecycle_*.py` (~6 files) | Host lifecycle — explicitly absent |
| `brain/v5/execution_facade_*.py`, `bound_execution.py` (~10 files) | Agent runtime — explicitly absent |
| `brain/v5/domain_packs.py`, `domain_skill_shims.py` | Domain packs — explicitly absent |
| `brain/v5/dynamic_host_routing.py` | Host routing — replaced by `using-aitp` |
| `brain/v5/skill_facade.py`, `skill_surface_contracts.py` | v5 Skill system — replaced by command-local Skills |
| `brain/v5/knowledge_facade.py`, `knowledge_retrieval.py`, `knowledge_context.py` | v5 knowledge system — replaced by `aitp knowledge` |
| `brain/v5/record_family_registry.py` | 63+ record types — replaced by 7 node types |
| `brain/cli/state.py` (L0-L4 state machine) | Stage gates — explicitly absent |
| `brain/gates.py` (52KB) | Gate evaluation — explicitly absent |
| `brain/physicist.py` | Physicist agent — host performs reasoning |
| `brain/sympy_verify.py` | Not excluded — SymPy verification is a research tool, not protocol infrastructure. The Agent may still use it but the CLI doesn't require it. |
| `deploy/` templates, hooks, configs | v5 deployment — replaced by simpler 2.0 installation |
| `tests/test_v5_*.py` (~140 files) | v5 tests — do not apply to 2.0. New 2.0 tests needed. |
| `scripts/aitp-pm.py` (105KB) | v5 package manager — needs simpler 2.0 replacement |
| `bin/aitp-v5.mjs` | v5 launcher — replaced by `aitp` CLI |
| `research/knowledge-hub/` (50+ protocol docs) | v5 protocol documentation — retained as historical reference, not as 2.0 authority |

### Keep — unchanged and read-only

| Path | Disposition |
|------|-------------|
| `.aitp-legacy/` (after cutover) | Read-only via `aitp search --scope legacy` |
| `docs/superpowers/specs/2026-07-19-aitp-2-0-rewrite-design.md` | Design history — superseded, not deleted |
| `docs/superpowers/audits/2026-07-19-aitp-2-0-rewrite-design-architecture-audit.md` | Audit history — preserved as review evidence |
| `docs/superpowers/audits/2026-07-20-aitp-2-0-rewrite-design-audit-disposition.md` | Disposition history — preserved |
| `templates/` LaTeX files | Research paper templates — protocol-independent |
| `schemas/` (for historical reference) | v5 schemas — do not package into 2.0 |
| `AUDIT_2025.md`, `AUDIT_REPORT.md` | Historical audits — read-only |

---

## Simplicity Budget Audit

### Ratchet Compliance

The §15.1 simplicity ratchet establishes six hard limits. Current spec compliance:

| Limit | Spec claim | Compliance |
|-------|-----------|------------|
| One `using-aitp` Skill | §3.1 | ✅ COMPLIANT — no other host-level Skills required |
| ≤12 public command groups | §4 (12 groups) | ✅ COMPLIANT — exactly 12 |
| One canonical writer | §14 (one finish path) | ✅ COMPLIANT — one CAS commit path |
| One command-local SKILL.md per command | §3.3 | ✅ COMPLIANT — subcommand differences are sections/templates |
| Zero MCP/hooks/context compiler/database/scheduler | §15 | ✅ COMPLIANT — all explicitly absent |
| No hidden CLI heuristics | §3.2, §4.2 | ⚠️ PARTIAL — P1-4 identifies one semantic leakage (closeout Dreaming suggestion) |

### Complexity Vectors To Monitor

1. **Asset kind proliferation**: The old spec had 18 Asset kinds. The new spec doesn't enumerate them but implies at least: `source`, `note`, `script`, `dataset`, `figure`, `table`, `report`, `code_revision`, `working_tree_snapshot`, `patch`, `run_manifest`, `environment_manifest`, `knowledge_card`, `workflow_candidate`, `workflow_spec`, `skill_package`, `install_receipt`, `problem_dossier`. Add any new kind and the Asset becomes a dumping ground. **Rate limit**: each new Asset kind must cite a real vertical.

2. **Statement kind proliferation**: Current 8 kinds (§6.1 old spec, implied in new spec via discriminated schemas). The kind-specific state vocabularies add complexity but are justified by real physics semantics (a question resolves differently from a constraint). **Monitor**: if a 9th kind is proposed without a vertical.

3. **Relation predicate proliferation**: 18 predicates in the old spec (§8). The new spec's §6 lists "about | related_to | depends_on | conflicts_with | parallelizable_with | derived_from | supports | contradicts | produced | uses | implements | validated_by | failed_because | supersedes | applies_to | installed_as" (16 values, 2 fewer than the old spec's 18). **Monitor**: each new predicate must cite a real cross-record link that cannot be expressed with existing predicates.

4. **Command subcommand proliferation**: 12 command groups × average 3-4 subcommands = ~40-50 subcommands. This is the largest potential complexity surface. **Rate limit**: each new subcommand requires a real use case from the verticals.

### What The Ratchet Prevents

The simplicity ratchet (§15.1) is correctly structured to prevent these specific v5 regressions:
- Someone adding an `aitp serve` command (MCP server reintroduction) → blocked by "zero required MCP servers".
- Someone adding `aitp hook install` (hook reintroduction) → blocked by "zero required hooks".
- Someone adding `aitp compile context` (context compiler reintroduction) → blocked by "zero required context compilers".
- Someone adding a 13th command group `aitp orchestrate` (agent runtime) → blocked by "at most twelve public command groups".
- Someone adding a hidden route-prioritization heuristic → blocked by "no scientific conclusion or command selection implemented as hidden CLI heuristics".

The ratchet has teeth. The only weakness is that it relies on CI enforcement (§21.1 old spec) which is not yet implemented.

---

## S0-S7 Implementation Sequence Audit

| Phase | Description | Dependencies | Status |
|-------|-------------|--------------|--------|
| **S0** | Freeze fixtures and compatibility boundary | None | 🔴 BLOCKED by P1-1 (using-aitp Skill spec), P1-9 (fixture data availability) |
| **S1** | Minimal store and read CLI | S0 | 🔴 BLOCKED by P1-2 (command Skill discovery), P1-3 (path resolution) |
| **S2** | Workspaces, audit, recording | S1 | 🟡 Has P1-4 (closeout semantic leakage) — must resolve before closeout implementation |
| **S3** | Research, literature, code, run guides | S2 | 🟢 No blockers identified in this audit |
| **S4** | Scientific Dreaming | S3 | 🔴 BLOCKED by P1-5 (assertion binding), P1-6 (workflow), P1-7 (context budget) |
| **S5** | Workflow and Skill | S4 | 🔴 BLOCKED by P1-8 (Knowledge Card dependency tracking) |
| **S6** | Writing and host acceptance | S5 | 🟡 P2-2 (presentation format) should be resolved |
| **S7** | Cutover and 2.0 release | S6 | 🟢 No blockers — requires admin command spec completion |

### Dependency Correctness

- S0→S1: Correct. Fixtures must be frozen before building the CLI that reads them.
- S1→S2: Correct. The read path must work before the write path.
- S2→S3: Correct. Workspaces and recording must work before research guides use them.
- S3→S4: Correct. Scientific Dreaming depends on having real Episodes, Statements, and source anchors to dream about.
- S4→S5: Correct. Skill distillation may reference Knowledge Cards (P1-8) — Knowledge Cards must exist first.
- S5→S6: Correct. Writing products use Knowledge Cards and Skills as sources.
- S6→S7: Correct.

**Verdict**: The sequence is dependency-correct. P1 issues must be resolved in their respective phases before implementation can begin.

---

## Required Spec Patches

### Patch 1: Using-AITP Skill Specification (§3.1 appendix)

Add after §3.1 line 85:

```markdown
### 3.1.1 Using-AITP Skill Content

The `using-aitp` Skill is a short Markdown file installed at the host's Skill
location. Its normative content is:

```markdown
# Using AITP 2.0

Use this Skill whenever the user's request concerns a known research topic,
prior results, literature study, derivation work, scientific code changes,
meaningful numerical or HPC work, or research writing.

## Entry

On the first turn that matches a research trigger, run:
  aitp enter --cwd <current working directory>

If the output shows more than one candidate topic, ask the user which topic
before proceeding. If no topic is found and the user has not named one, do
not enter — answer normally.

## Phase Selection

After entry, select a command from this table based on the user's intent:

| Intent | Command |
|--------|---------|
| Find prior work | aitp search, then aitp show |
| Discuss, derive, code, calculate, HPC | aitp research begin --mode <mode> |
| Study a paper | aitp literature study |
| Record a durable result | aitp checkpoint |
| End a meaningful session | aitp closeout |
| Combine insights across work | aitp knowledge dream |
| Extract repeatable procedure | aitp skill distill |
| Write a note or paper | aitp write |

## Recovery

If `aitp` is not found: report "AITP is not installed" and do not fabricate memory.
If `aitp enter` reports staging bundles from a prior session: show them and ask
the user. Never delete or commit staging implicitly.
If you realize you should have entered earlier: run `aitp enter` immediately,
declare the late-entry boundary, and prepare a retrospective checkpoint only
for reconstructable durable work.

## Durable Moments

Run `aitp checkpoint` after:
- A new result or derivation boundary
- An important failed or inconclusive route
- A scientific or operational decision
- A paper is fixed and anchored
- A research-relevant code commit or patch
- A reproducible run completes or fails meaningfully
- Assumptions, conventions, or next actions change

Do not checkpoint after every command or transient thought.

## Never

- Infer human approval from conversation
- Claim a Statement is validated without an Assessment
- Commit canonical files without `aitp` audit and review
- Install a Skill without human approval
```

### Patch 2: Command Skill Discovery (§3.3 addition)

Replace §3.3 lines 108-118 with:

```markdown
### 3.3 Command Skills

Each command owns a packaged, versioned Skill bundled with the `aitp` package:

```text
<package>/command_skills/<command>/SKILL.md
<package>/command_skills/<command>/templates/
<package>/command_skills/<command>/profile.yaml
```

The CLI resolves command Skills relative to its own installation path. For
development, set `AITP_DEV_COMMAND_SKILLS=<path>` to override the bundled path.
A `SKILL.md` declares its version in frontmatter; the CLI compares this against
its own version and warns on mismatch, but the bundled Skill takes precedence.

The command-local `SKILL.md` ... [rest of existing text unchanged]
```

### Patch 3: Path Resolution Algorithm (§6 addition)

Add after §6 line 335:

```markdown
### 6.1 Path Resolution

A store-relative ref resolves to a filesystem path as follows:

```text
topics/<topic-id>/TOPIC.md                         → .aitp/topics/<topic-id>/TOPIC.md
topics/<topic-id>/entities/<id>.md                 → .aitp/topics/<topic-id>/entities/<id>.md
topics/<topic-id>/routes/<id>.md                   → .aitp/topics/<topic-id>/routes/<id>.md
topics/<topic-id>/statements/<id>.md               → .aitp/topics/<topic-id>/statements/<id>.md
topics/<topic-id>/episodes/<id>.md                 → .aitp/topics/<topic-id>/episodes/<id>.md
topics/<topic-id>/assessments/<id>.md              → .aitp/topics/<topic-id>/assessments/<id>.md
topics/<topic-id>/relations/<id>.md                → .aitp/topics/<topic-id>/relations/<id>.md
topics/<topic-id>/assets/<id>.md                   → .aitp/topics/<topic-id>/assets/<id>.md
topics/<topic-id>/knowledge/cards/<id>.md          → .aitp/topics/<topic-id>/knowledge/cards/<id>.md
topics/<topic-id>/reuse/workflows/<id>.md          → .aitp/topics/<topic-id>/reuse/workflows/<id>.md
topics/<topic-id>/reuse/skill-candidates/<id>/     → .aitp/topics/<topic-id>/reuse/skill-candidates/<id>/
topics/<topic-id>/reuse/scripts/<name>             → .aitp/topics/<topic-id>/reuse/scripts/<name>
topics/<topic-id>/code/revisions/<id>.md           → .aitp/topics/<topic-id>/code/revisions/<id>.md
topics/<topic-id>/code/mappings/<id>.md            → .aitp/topics/<topic-id>/code/mappings/<id>.md
topics/<topic-id>/runs/<id>.md                     → .aitp/topics/<topic-id>/runs/<id>.md
topics/<topic-id>/writing/<product>/<id>.md        → .aitp/topics/<topic-id>/writing/<product>/<id>.md
shared/<type-plural>/<id>.md                       → .aitp/shared/<type-plural>/<id>.md
shared/knowledge/cards/<id>.md                     → .aitp/shared/knowledge/cards/<id>.md
```

A ref ending in `@<git-commit>` resolves through `git show <commit>:<path>`.
`aitp show` validates that the file at the resolved path has frontmatter `id`
matching the ref's `<id>`.
```

### Patch 4: Closeout DREAMING Suggestion (§10.1 clarification)

Replace §10.1 lines 490-493 with:

```markdown
`aitp closeout` suggests `aitp knowledge dream` when at least three new
Episodes were created in the current session, or when a new
`Statement(kind=insight)` was recorded. This is a structural suggestion based
on session event count, not a semantic judgment about linked insights. The
host Agent must assess whether these Episodes contain connected physical
insights before invoking `knowledge dream`.
```

### Patch 5: Knowledge Card Source References (§10.2 pluralization)

Replace §10.2 line 529 `source_reported` entry:

```markdown
- `source_reported`, with exact source refs and anchors in `source_refs[]`;
```

Replace §10.2 line 530-532:

```markdown
- `aitp_statement`, with exact Statement refs in `statement_refs[]` and their
  derived assessment states;
- `new_synthesis`, with separately staged insight, hypothesis, claim, or open
  gap Statement refs in `basis_refs[]`.
```

### Patch 6: Knowledge Dream INPUTS Pre-population (§10.1 addition)

Add after §10.1 line 473:

```markdown
The CLI pre-populates `INPUTS.md` with a deterministic candidate list:

- all Statements with `kind=insight|hypothesis|claim|definition` in the topic;
- all Episodes in the selected time range, ordered by `created_at`;
- all Assessments in the topic;
- all existing Knowledge Cards in the topic;
- all source anchors referenced by any of the above records.

Each entry includes its ref, title, created_at, and a character-count estimate.
The Agent must mark each input as `expanded` (full body read), `summarized`
(skimmed via ref), or `skipped` with a reason. `AUDIT.md` reports the count of
expanded vs. summarized vs. skipped inputs and flags any `Statement(kind=insight)`
that was skipped without a reason.
```

### Patch 7: Skill KNOWLEDGE_DEPS.md (§11 addition)

Add to the `skill distill` workspace listing (§11 lines 598-611):

```markdown
KNOWLEDGE_DEPS.md
```

Add after §11 line 621 (`PROVENANCE.md` description):

```markdown
- `KNOWLEDGE_DEPS.md`: exact Knowledge Card refs for physical conventions,
  approximations, and applicability boundaries the Skill assumes. `aitp skill
  install` checks these refs for staleness; a stale dependency does not block
  installation but produces a visible warning.
```

### Patch 8: Research Finish Checkpoint Prompt (§8 addition)

Add at end of §8:

```markdown
`aitp research finish` reports whether the workspace contains a withdrawn
hypothesis, contradicted claim, or failed result that has no corresponding
checkpoint. If so, the finish output includes: "This workspace contains a
durable negative result. Run `aitp checkpoint` to preserve it before closing."
```

### Patch 9: Admin Init Specification (§5 or §17 addition)

Add a section or appendix:

```markdown
### Admin: Store Initialization

`aitp admin init [--path <store-root>]` creates a new AITP 2.0 store:

1. creates `.aitp/` directory at the specified or discovered root;
2. writes `STORE.md` with store identity, creation date, and protocol version;
3. creates directory structure: `topics/`, `shared/library/papers/`,
   `shared/knowledge/cards/`, `shared/workflows/`, `shared/scripts/`,
   `runtime/workspaces/`, `runtime/staging/`, `runtime/indexes/`,
   `runtime/recovery/`;
4. initializes a Git repository in `.aitp/` if one does not already exist;
5. writes `runtime/local.toml` with machine identity and empty host profiles.

Existing `.aitp/` directories are never overwritten. `aitp enter` detects a
missing store and directs the user to `aitp admin init`.
```

---

## Final Recommendation

**CONDITIONAL PASS.** Proceed to S0 with the following conditions:

1. **Before S0 freeze**: Resolve P1-1 (using-aitp Skill spec), P1-9 (fixture data availability). Apply Patches 1, 2, 3, 5, and 9 to the spec.
2. **Before S1 implementation**: Resolve P1-2 (command Skill discovery), P1-3 (path resolution). These are specification work, not new infrastructure.
3. **Before S2 implementation**: Resolve P1-4 (closeout semantic leakage). Apply Patch 4.
4. **Before S4 implementation**: Resolve P1-5 (assertion binding), P1-6 (Dreaming workflow), P1-7 (context budget). Apply Patches 5-7.
5. **Before S5 implementation**: Resolve P1-8 (Knowledge Card dependency tracking). Apply Patch 7.
6. **Before S6**: Resolve P2-2 (presentation format). Apply Patch 8.

**The architecture is fundamentally sound.** The command-skill design is a genuine simplification over both v5 and the 2026-07-19 rewrite design. The simplicity ratchet has correctly identified and blocked all re-entry paths for MCP, hooks, context compilers, and agent runtimes. The nine P1 findings are specification gaps, not architectural flaws — each has a concrete fix that adds minimal complexity.

The primary risk is not in the design but in the implementation: 741 .py files and 168K LOC of v5 code exert enormous gravitational pull. The S0-S7 phases must be implemented in a clean package that imports nothing from `brain/v5/` except possibly an adapted YAML frontmatter parser. The simplicity ratchet's CI enforcement (§21.1 old spec) is not yet implemented and must be part of S0 — without it, v5 code will leak into 2.0 through "just this one utility function" imports.

**The 12 command groups, 7 node types, one Relation, Markdown files, `rg`, Git, and human review gates are sufficient to constitute a complete theoretical-physics research memory system.** No additional infrastructure is needed.
