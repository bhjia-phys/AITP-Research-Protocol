# FIXTURE PROVENANCE — T1a Pre-Read Authorization Stubs

> **Status**: T1a pre-read authorization stubs for Oracle Gate B review.
> This document is noncanonical evidence, not a fixture corpus.
> No source bytes have been read. No source snapshot commit SHA or file
> hash has been computed. No fixture byte has been selected or copied.

## Authorization Record

| Field | Value |
|-------|-------|
| Approver | `human:bhjia` |
| Approval date | 2026-07-23 |
| Approval evidence | User explicitly selected "Authorize both" for quantum-chaos and NiO sources under the listed restrictions during this session |
| Artifact stage | S0/T1a — pre-read only |
| Next lawful step | Oracle Gate B review (artifacts only); if Gate B passes, T1b validator core begins. Source post-authorization provenance/read/copy occurs only in later T3 per plan (§4). No source reading or fixture corpus creation is authorized before Gate B pass. |

## Source Authorization Stubs

### Source 1: quantum-chaos

| Field | Value |
|-------|-------|
| Symbolic source ID | `quantum-chaos` |
| Source / root class | Real research source — quantum chaos long-range spin chains (authorized symbolic root; no machine path recorded) |
| Status | `authorized_pre_read` |
| Authorized scope | Selected text, Markdown, and metadata required to construct sanitized *structural* fixtures (record profiles, path mapping, ref grammar, relation predicates, store/Git invariants, navigation spine, content envelope boundaries). Must be the minimum content needed to demonstrate S0 structural invariants — not full E2E command behavior. |
| Access mode | Controlled read-only; pre-read authorization only — no source byte has been read yet |
| Snapshot evidence | MUST be recorded post-authorization in T3 (Git commit SHA for Git-tracked sources, or per-file SHA-256 for non-Git sources) before any fixture byte is selected or copied. No snapshot SHA or file hash is present at this T1a stage. |
| Version ranges | Exactly one current source snapshot, identified and pinned from source-control/filesystem metadata at T3 before any content byte is read; no historical range is authorized without new approval |
| Directories / files | Only selected UTF-8 text, Markdown, or structured metadata beneath the authorized symbolic root that is necessary for listed structural invariants; an exact relative-path allowlist MUST be recorded before content read or copy; PDF, binary, paywalled, credential-bearing, and private-locator files are excluded |

#### Restrictions (quantum-chaos)

- No write or mutation of any source content.
- No redistribution or raw source publication.
- No PDF, raw binary, or paywalled bytes committed.
- No credentials, tokens, or keys.
- No private absolute path, hostname, IP address, or private URL.
- No source trust promotion — fixtures are evidence, not canonical research truth.
- Only minimal selected structural content; all machine-specific paths → symbolic placeholders.
- All personal/private identifiers → redacted or replaced with symbolic placeholders.

### Source 2: nio

| Field | Value |
|-------|-------|
| Symbolic source ID | `nio` |
| Source / root class | Real research source — LibRPA / magnetic NiO (authorized symbolic root; no machine path recorded) |
| Status | `authorized_pre_read` |
| Authorized scope | Selected text, Markdown, and metadata required to construct sanitized *structural* fixtures (code revisions, patches, runs, workflows, skills, install receipts, formula-to-code mappings). Must be the minimum content needed to demonstrate S0 structural invariants — not full E2E command behavior. |
| Access mode | Controlled read-only; pre-read authorization only — no source byte has been read yet |
| Snapshot evidence | MUST be recorded post-authorization in T3 (Git commit SHA for Git-tracked sources, or per-file SHA-256 for non-Git sources) before any fixture byte is selected or copied. No snapshot SHA or file hash is present at this T1a stage. |
| Version ranges | Exactly one current source snapshot, identified and pinned from source-control/filesystem metadata at T3 before any content byte is read; no historical range is authorized without new approval |
| Directories / files | Only selected UTF-8 text, Markdown, or structured metadata beneath the authorized symbolic root that is necessary for listed structural invariants; an exact relative-path allowlist MUST be recorded before content read or copy; PDF, binary, paywalled, credential-bearing, and private-locator files are excluded |

#### Restrictions (nio)

- No write or mutation of any source content.
- No redistribution or raw source publication.
- No PDF, raw binary, or paywalled bytes committed.
- No credentials, tokens, or keys.
- No private absolute path, hostname, IP address, or private URL.
- No source trust promotion — fixtures are evidence, not canonical research truth.
- Only minimal selected structural content; all machine-specific paths → symbolic placeholders.
- All personal/private identifiers → redacted or replaced with symbolic placeholders.

## Current State Declaration

- **No source bytes have been read.** This T1a artifact records pre-read authorization only.
- **No source snapshot commit SHA or file hash has been computed.** These fields are intentionally absent — they are filled at T3 post-authorization.
- **No fixture byte has been selected or copied.** No `tests/fixtures/aitp2/quantum-chaos/`, `tests/fixtures/aitp2/nio/`, or any other fixture family exists.
- **T0 authority metadata is recorded only in `S0_DECISIONS.json`**, not in source snapshot fields here.
- **FIXTURE_PROVENANCE.md is noncanonical evidence.** The active spec and S0 plan are the sole normative authorities. This file is a Gate B review artifact.

## Planned Next Steps (Post Gate B)

1. Oracle Gate B reviews these T1a artifacts (decisions + authorization stubs) — not the spec amendment.
2. If Gate B passes: T1b validator core begins. No fixture corpus yet.
3. T2: FREEZE.json oracle + synthetic negatives. Still no real source fixtures.
4. **T3 (only after T2 pass)**: Post-authorization provenance read. For each authorized source root, read-only access to compute Git snapshot commit SHA or per-file SHA-256; complete provenance snapshot fields; select minimal records for structural invariants; redact private content; create sanitized fixture families under `tests/fixtures/aitp2/`.
5. T4–T5 continue per plan.

**No source reading, snapshot hashing, or fixture byte copying is authorized before T3.**
