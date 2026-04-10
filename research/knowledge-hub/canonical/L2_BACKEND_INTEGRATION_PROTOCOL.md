# L2 backend integration protocol

This file is the unified protocol for connecting new content sources to `L2`.

It does not create a new layer.
It defines how an external human/software knowledge store becomes a disciplined `L2` backend instead of an opaque side channel.

## 1. Goal

Use this protocol when adding any new backend such as:
- a human note vault,
- a software repository,
- a local documentation corpus,
- a result store,
- a mixed theory-plus-code workspace.

The goal is to ensure:
- the backend is explicit,
- downstream use is auditable,
- `L2` remains schema-first,
- future integrations reuse one contract instead of inventing new ad hoc rules.

## 2. Required surfaces

Every new backend must provide:

1. a backend card
   - `canonical/backends/<backend_slug>.json`
2. a compact registry row
   - `canonical/backends/backend_index.jsonl`
3. at least one declared intended `L2` target family
4. a retrieval policy statement
5. a source registration rule

Optional but recommended:

6. one onboarding note or bridge note
7. one smoke-test example showing how a concrete artifact enters `L0`

## 3. Hard rules

1. A backend root never counts as an AITP-governed downstream `L2` surface merely because a folder exists at that path; it becomes one only through an explicit backend card plus normal promotion gates.
2. A backend card is metadata, not promotion.
3. Concrete backend artifacts should usually be registered into `L0` before strong reuse.
4. `L2` promotion still follows normal `L1->L2` or `L3->L4->L2` gates.
5. Do not promote a whole folder tree as one canonical object.
6. If the backend is software-heavy, do not treat raw source code as self-justifying knowledge.
7. If the backend is human-note-heavy, do not treat folder structure as canonical ontology.
8. If two backends are declared as paired human-facing and structured realizations of the same downstream knowledge network, the pairing must be explicit and semantic drift between them must be surfaced as backend debt.

## 4. Minimal backend card contract

Use the schema:

- `schemas/l2-backend.schema.json`

Required fields:
- `backend_id`
- `title`
- `backend_type`
- `status`
- `root_paths`
- `purpose`
- `artifact_granularity`
- `source_policy`
- `l0_registration`
- `canonical_targets`
- `retrieval_hints`
- `notes`

## 5. Standard write protocol

When adding a new backend, write in this order:

### Step 1. Register the backend

Create:
- one backend card JSON
- one backend index row

This says the backend exists and what it is for.

### Step 2. Declare artifact granularity

State what the atomic reusable input is:
- single note,
- single doc,
- single test,
- single benchmark result,
- single code module,
- single derivation note.

Do not leave this implicit.
Record it directly in the backend card through `artifact_granularity`.

### Step 3. Register concrete artifacts into `L0`

When an artifact from the backend materially affects research work, register it into `L0`.

For `source-layer` registration, include backend-aware provenance fields such as:
- `provenance.backend_id`
- `provenance.backend_root`
- `provenance.backend_artifact_kind`
- `locator.backend_relative_path`

This is the bridge from backend storage into AITP's source substrate.
Record the expected registration helper and minimum required fields directly in the
backend card through `l0_registration`.

### Step 4. Use `L2 consultation` explicitly when needed

If `L1`, `L3`, or `L4` materially uses backend-derived `L2` knowledge, emit the normal consultation protocol artifacts.

Backend use must not remain chat-only.

### Step 5. Promote only the distilled reusable object

Promote:
- concept
- derivation object
- method
- workflow
- bridge
- validation pattern
- warning note

Do not promote:
- raw folder dumps
- unscoped code blobs
- unresolved scratch notes
- unexplained benchmark tables

## 6. Recommended backend profiles

### `human_note_library`

Best targets:
- `concept`
- `derivation_object`
- `bridge`
- `warning_note`

Typical examples:
- a local Markdown theory vault

### `software_repo`

Best targets:
- `method`
- `workflow`
- `validation_pattern`
- `warning_note`
- `bridge`

Typical examples:
- a numerical or formal code repository

### `local_result_store`

Best targets:
- `validation_pattern`
- `warning_note`
- `claim_card`

Use only when provenance and reproducibility paths are explicit.

## 7. Paired downstream backends

AITP may register a paired backend configuration when two backends are intended
to realize the same downstream knowledge network at different storage
resolutions.

Typical pattern:

- one `human_note_library` for operator-facing notes;
- one `mixed_local_library` for typed units, graph checks, and deterministic
  projections.

Rules:

- the pairing must be named explicitly in protocol docs or backend notes;
- neither backend becomes privileged by serialization format alone;
- the human-facing backend may be operator-primary and the typed backend may be
  machine-primary, but those are role distinctions rather than silent
  authority grants;
- normal promotion gates still decide whether writeback is allowed;
- semantic identity, source anchors, assumptions, regime limits, and unresolved
  boundaries must stay aligned across the pair;
- any one-sided simplification or lag must be recorded as backend debt rather
  than silently treated as equivalent.

## 8. Promotion-side rule

If an `L2` canonical unit was materially seeded by a backend, it may add:

- `provenance.backend_refs`

But `backend_refs` is supplemental.
It does not replace:
- `source_ids`
- `l1_artifacts`
- `l3_runs`
- `l4_checks`

## 9. Practical interpretation

AITP keeps one unified rule:
- human knowledge stores and software knowledge stores both enter through the same backend contract,
- but they seed different canonical object families.

In a paired-backend configuration, the human-facing note library and the typed
repository are treated as two governed downstream implementations of one
knowledge network.

## 10. Authoring checklist

Before a backend counts as integrated, confirm:

- backend card exists
- index row exists
- root paths are explicit
- artifact granularity is explicit
- `L0` registration path is defined
- intended canonical targets are explicit
- retrieval hints are explicit
- no folder-level canonicalization is implied
- paired-backend semantics are explicit if the backend is part of a downstream pair

If any of these is missing, the backend is only partially integrated.

## 11. Public formal-theory starter pack

The public repository ships a formal-theory starter example here:

- `canonical/backends/examples/formal-theory-note-library.example.json`
- `canonical/backends/FORMAL_THEORY_BACKEND_STARTER.md`
- `runtime/scripts/run_formal_theory_backend_smoke.sh`

Use that starter pack when you want to bridge an external theory-note library
into `L2` without turning the backend root itself into canonical memory.
