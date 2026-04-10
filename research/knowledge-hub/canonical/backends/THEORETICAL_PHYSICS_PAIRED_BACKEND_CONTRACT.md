# Theoretical Physics Paired Backend Contract

Status: active working contract

## Purpose

This file defines the shared contract for the paired theoretical-physics
backends:

- `backend:theoretical-physics-brain`
- `backend:theoretical-physics-knowledge-network`

It exists to prevent three confusions:

- confusing human-readable versus typed storage with epistemic layers;
- confusing typed structure with global authority;
- confusing compiled helper views with downstream knowledge realizations.

## Decision

The paired theoretical-physics backends are:

- two governed realizations of one downstream knowledge network;
- operator-primary versus machine-primary by role;
- but not globally ranked by file format alone.

Short form:

- shared identity
- different strengths
- no silent hierarchy

## 1. Shared identity rule

The two backends must represent the same promoted object identity whenever they
are both present for a given item.

That shared identity is anchored by:

- promotion packet semantics,
- reusable unit id,
- source anchors,
- assumptions and regime limits,
- unresolved-gap boundaries,
- and promotion / provenance receipts.

Backend path or serialization format does not define identity on its own.

## 2. Primary roles

The paired backends are intentionally asymmetric in role, not in trust
entitlement.

### Human-readable backend

`backend:theoretical-physics-brain` is:

- operator-primary
- reading-primary
- curation-primary
- narrative and explanation primary

Use it for:

- human study and editing,
- domain-facing note maintenance,
- explicit unresolved queues,
- and operator-visible semantic refinement.

### Typed backend

`backend:theoretical-physics-knowledge-network` is:

- machine-primary
- retrieval-primary
- graph-check-primary
- deterministic-rebuild primary

Use it for:

- relation traversal,
- structural consistency checks,
- machine-oriented retrieval and expansion,
- and future graph-backed rebuilding or export bridges.

## 3. No silent hierarchy rule

The typed backend is not globally more authoritative just because it is typed.

The human-readable backend is not globally more authoritative just because it is
human-edited.

Authority remains with:

- the shared promotion and alignment contract,
- the AITP-governed `L2` trust surfaces,
- and the explicit backend-drift record when the pair is temporarily out of
  sync.

## 4. Relationship to canonical / compiled / staging

`canonical / compiled / staging` is an AITP `L2` trust distinction.

It is not the same thing as:

- human-readable backend
- typed backend

Use this separation:

- canonical `L2` = authoritative reusable memory contract
- compiled `L2` = derived helper surface
- staging `L2` = provisional memory quarantine
- paired backends = downstream realizations of promoted knowledge

Consequences:

- the human-readable backend is not merely a compiled markdown view;
- the typed backend is not automatically the whole canonical truth;
- compiled helper views may summarize either backend-facing material but do not
  replace paired backend realizations.

## 5. Read and write rule

When both paired backends are active:

- read the human-readable backend when operator comprehension, note editing, or
  narrative clarification is primary;
- read the typed backend when graph expansion, relation checks, deterministic
  retrieval, or machine-facing rebuild is primary;
- keep both aligned at the level of identity, evidence, assumptions, and
  unresolved boundaries.

When only one backend is available:

- proceed honestly with the available backend;
- record any missing paired realization as backend debt if it matters for the
  current work.

## 6. Drift rule

Drift between the pair must be treated as explicit backend debt.

Examples:

- one side has a newer source anchor set;
- one side carries an unresolved caveat that the other omits;
- one side collapses two identities that the other keeps distinct;
- one side cannot yet express the full structure of the other.

Required behavior:

- do not silently pretend they are equivalent;
- record the reduction or lag explicitly;
- prefer honest mismatch reporting over forced lossy synchronization.

## 7. Promotion rule

Promotion does not target "the typed side first" or "the human side first" as
a universal law.

Instead:

- promotion targets the shared knowledge object;
- backend-specific writeback materializes the object in one or both
  realizations;
- any one-sided materialization must say what still remains to align.

## 8. One-line doctrine

The theoretical-physics brain and the typed knowledge network are paired
realizations of the same downstream knowledge object: the brain is
operator-primary, the typed network is machine-primary, and neither gains
silent authority merely from its file format.
