---
title: AITP 2.0 Command And Skill Protocol Audit Disposition
date: 2026-07-20
status: resolved-in-revised-spec
audit: docs/superpowers/audits/2026-07-20-aitp-2-0-command-skill-protocol-architecture-audit.md
spec: docs/superpowers/specs/2026-07-20-aitp-2-0-command-skill-protocol-design.md
---

# AITP 2.0 Command And Skill Protocol Audit Disposition

## Decision

The audit's overall verdict is accepted: the command-and-Skill architecture has
no P0 design blocker, but the first draft did not close several operational
contracts. The revised spec closes all nine P1 concerns before implementation.

The audit is preserved unchanged as review evidence. Its proposed patches are
not normative by themselves; the dispositions below explain where the final
resolution intentionally differs.

## P1 Dispositions

| Finding | Disposition | Resolution in revised spec |
| --- | --- | --- |
| P1-1: `using-aitp` content | Accepted | Section 3.1.1 now defines triggers, non-triggers, exact entry behavior, ambiguous-topic handling, recovery, durable moments, and prohibited inferences. |
| P1-2: command Skill discovery | Accepted with a different mechanism | Section 3.3 makes command Skills versioned resources in the same installed package and resolves them with `importlib.resources`. No development environment override or second Skill root is allowed because either would recreate version drift. |
| P1-3: ref resolution | Accepted in part | Refs were already exact store-relative paths, so no type-to-plural lookup is added. Section 6.1 now defines parsing, Git revision reads, containment, symlink handling, profile checks, and distinct failures. |
| P1-4: closeout Dreaming suggestion | Accepted with a stricter boundary | The CLI does not count Episodes or interpret prose. The Agent must visibly declare `knowledge_candidate: true`, exact refs, and a rationale; closeout may only echo that declaration. |
| P1-5: Knowledge assertion binding | Accepted | Each card assertion now has an ID, plural exact basis refs, and clause-level source mapping. Cross-source inference is `new_synthesis`, not `source_reported`. |
| P1-6: Dreaming flow | Accepted without adding commands | `knowledge dream` keeps one visible workspace. The CLI pre-populates a scoped inventory; the Agent reads in bounded passes; `aitp audit` can run between passes; `knowledge finish` checks coverage. |
| P1-7: Dreaming context budget | Accepted | `INPUTS.md` records character estimates and exact read state. Generated summaries cannot act as basis refs, and unresolved coverage remains explicit. |
| P1-8: Skill and Knowledge boundary | Accepted with a different canonical form | Existing `Relation(predicate=uses)` records are canonical. The package manifest mirrors them for portability. A separate canonical `KNOWLEDGE_DEPS.md` would create a second truth source and is rejected. |
| P1-9: fixture provenance | Accepted after correcting scope | The protocol repository lacks frozen 2.0 fixtures, but real research material exists outside it. S0 now requires explicitly authorized read-only snapshots, a sanitized committed fixture, provenance and redaction records, and a `seeding` state when evidence is incomplete. |

## P2 Dispositions

| Finding | Disposition | Resolution in revised spec |
| --- | --- | --- |
| P2-1: command overlap | Deferred intentionally | The 12 groups remain the public ceiling. `research` owns a research phase; `literature` owns one-copy source intake and anchors. Consolidation requires usage evidence, not pre-implementation taste. |
| P2-2: presentation format | Accepted | `aitp write` requires an explicit format or Topic convention; baseline presentation formats are Beamer and Marp. |
| P2-3: run profile | Accepted | Section 12.3 defines one immutable run Asset per attempt, code refs, environment, inputs, outputs, scheduler identity, validation, and failure. |
| P2-4: store initialization | Accepted with corrected Git ownership | `admin init` uses an enclosing Git worktree when present and never creates a nested repository silently. Standalone Git requires human approval and is recorded in `STORE.md`. |
| P2-5: Topic ID collision | Accepted with human semantics | The human chooses a meaningful scope suffix. Automatic numeric suffixes are rejected because they hide topic identity decisions. |
| P2-6: Knowledge health trigger | Accepted | Health is checked on show, enter-before-render, refresh, audit, and relation-bounded checkpoint impact reporting. No background scanner is added. |
| P2-7: `profile.yaml` format | Accepted | Section 3.3 includes a minimal deterministic profile and explicitly excludes scientific truth or relevance judgments. |

## Additional Corrections

The review surfaced four issues that are stronger or broader than its final P1
list:

1. The audit noticed that Asset kinds lacked canonical paths but left the issue
   outside its P1 summary. The revised spec treats this as a required closure and
   maps every baseline Asset kind to one purpose-specific path; it does not add a
   generic dumping-ground `assets/` directory.
2. The new spec cannot inherit record profiles silently from the superseded
   design. Section 6 now freezes the minimum Topic, Entity, Route, Statement,
   Episode, Assessment, Asset, and Relation profiles in the current document.
3. A bare instruction to initialize Git below `.aitp` would create nested
   repositories in common research workspaces. Section 5.1 now records and
   respects one Git owner.
4. The audit correctly warns about legacy-code pull but does not make the package
   boundary normative. Sections 3.2.1 and 15.1 now require a clean `src/aitp/`
   package, forbid production imports from legacy surfaces, and add blocking
   complexity checks.

The audit's final patch numbering is also inconsistent: its recommendation for
P2-2 points to Patch 8, while Patch 8 describes research-finish checkpoint
reporting. The revised spec implements the presentation requirement directly.

## Evidence Boundary

This disposition revises architecture documents only. It does not assert that
the CLI, package resources, fixtures, migration adapter, or end-to-end verticals
already exist. No real canonical research record is modified by this review.

S0 may inspect external research material only after explicit read authorization
and may commit only a minimal sanitized fixture. Private paths, credentials,
restricted source bytes, and unrelated research content remain outside the
public repository.

## Re-Review Gate

Implementation may begin at S0 only after the revised spec is accepted. S0 is
complete only when the fixture provenance, clean-package boundary, frozen
profiles, built-wheel resources, and blocking simplicity checks exist as
executable tests rather than prose alone.
