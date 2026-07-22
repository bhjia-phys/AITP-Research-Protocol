---
title: AITP 2.0 Rewrite Design Audit Disposition
date: 2026-07-20
status: resolved-in-spec-awaiting-user-review
audit: docs/superpowers/audits/2026-07-19-aitp-2-0-rewrite-design-architecture-audit.md
spec: docs/superpowers/specs/2026-07-19-aitp-2-0-rewrite-design.md
---

# AITP 2.0 Rewrite Design Audit Disposition

This document records the technical disposition of the independent architecture
audit. The audit remains unchanged as review evidence. Severity labels are not
accepted automatically; each recommendation is evaluated against the 2.0
simplicity and transparency boundaries.

## P0 Findings

| ID | Disposition | Spec resolution |
| --- | --- | --- |
| P0-1 | Accepted with a smaller model change | Route becomes the seventh node because it owns planning state. Constraint remains a kind-specific Statement. `system_feedback` becomes a problem-dossier Asset produced by an Episode. Statement uses discriminated kind schemas rather than one lifecycle. No eighth node is added. |
| P0-2 | Accepted as clarification | Commit manifest field is renamed `payload_paths_and_hashes`; it excludes the manifest itself. Git tree identity covers the manifest bytes. |
| P0-3 | Problem accepted; proposed fix rejected | `TOPIC.md` remains the canonical stable Topic node and may not contain active Route state or current state. `enter` derives dynamic output. Making `TOPIC.md` a generated view would invert the canonical/derived boundary. |
| P0-4 | Not a blocker; terminology clarified | `audit` remains deterministic. `review show|approve|reject|request-changes` remains the human-decision surface. Renaming the whole command to `approve` would make rejection and revision requests unnatural. |

## P1 Findings

| ID | Disposition | Spec resolution |
| --- | --- | --- |
| P1-1 | Accepted | Added the normative minimal `using-aitp` Skill triggers, non-triggers, entry, failure recovery, missed-entry, durable-moment, and closeout contract. |
| P1-2 | Accepted with technical correction | `aitp search` classifies `rg --json` hits as body or named frontmatter fields after parsing the file. Filename globs cannot exclude a frontmatter region. |
| P1-3 | Accepted | AITP lists Routes deterministically and performs no semantic portfolio selection. The host Agent may propose a portfolio only with visible reasoning and considered/omitted refs. |
| P1-4 | Accepted with storage boundary | Untracked entries record path, kind, size, hash, stored state, durable locator, and gaps. AITP does not copy arbitrary binaries into canonical `.aitp`. |
| P1-5 | Accepted with stronger identity | Anchors bind exact PDF hash, extraction identity, page, geometry, and text hash. Extraction runs are immutable. Page-sequence labels are not durable IDs. |
| P1-6 | Accepted at implementation boundary | Checkpoint and closeout are distinct public intents over one recording service. Closeout adds a declared-session completeness sweep; it does not infer an unavailable transcript. |
| P1-7 | Accepted | Entry has a normative character budget, advisory token estimate, zero automatic expansion depth, explicit included/not-shown counts, and exact expansion commands. |
| P1-8 | Accepted with a ratchet rather than arbitrary total LOC | CI inventories nodes, fields, predicates, commands, writers, dependencies, profiles, and LOC. Hard caps and per-module/schema thresholds apply; R1 establishes a ratcheted package baseline owned by real verticals. |

## P2 Findings

| ID | Disposition | Spec resolution |
| --- | --- | --- |
| P2-1 | Deferred as recommended | Command consolidation requires R4/R5 use data and is listed as post-2.0 evidence work. |
| P2-2 | Accepted now | Bundles pin immutable profile versions; later profiles do not invalidate old records. |
| P2-3 | Accepted now | Install receipts pin before/after package Assets and file manifests. Rollback is a new reviewed install transaction. |
| P2-4 | Accepted now | A writing-synthesis Episode records creation and review; the resulting Knowledge Card remains the portable Asset. |
| P2-5 | Accepted now | `parallelizable_with` is advisory for disjoint expected writes; dispatch remains host-owned and commits remain serialized. |
| P2-6 | Accepted now | Canonical host profiles contain no credentials. Local configuration maps profile IDs to external SSH aliases or credential providers. |

## Evidence Boundary

The audit's sub-second `rg` performance statement is a hypothesis until measured
on the specified index-free ten-thousand-record fixture. The revised release
gate requires that measurement and reports optional-index performance
separately.
