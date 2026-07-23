# AITP 2.0 S0 Contract and Fixture Freeze Implementation Plan

> **Status**: proposed plan-only amendment. This document is a Phase 1 deliverable
> that amends the original S0 plan to freeze observable behavior contracts
> (disk, file, navigation, read/write, CLI/Agent contract, runtime inventory,
> content envelopes, route navigation, read coverage, failure recall, gate
> matrix) without freezing Python code shape. It is NOT an S0 execution
> artifact.
>
> **Amendment scope**: this plan-only amendment updates the active spec
> (`2026-07-20-aitp-2-0-command-skill-protocol-design.md`) and this plan
> document. It does not create production code, packages, fixtures, CLI
> scaffolding, `.aitp` directories, CI workflows, or runtime objects.
>
> **Baseline**: the plan being amended was committed at
> `b470bd809a8f31bf794c8e8a01721c7b9e8ed195`. This SHA is recorded
> statically; the amended plan must not self-embed a future amendment SHA.
>
> **Historical Phase 1 gating (completed)**:
> - The Phase 1 amendment required Council review of the planning approach +
>   Oracle Gate A (renewed plan-only Gate 3) before its exact four-path commit
>   (active spec, S0 plan, `.gitignore`, `.ignore`). Both reviews passed and
>   commit `7de57f34ae3b77f133cee83ac8ee44084bb42c81` completed that amendment.
>   The `.gitignore` and `.ignore` changes were audited orchestration-support
>   changes, not product authority; they are not part of the current amendment.
>
> **Current execution gating**:
> - After this amendment is committed, S0 execution follows a strict sequence:
>   1. T1a creates `S0_DECISIONS.json` (populated decision register) and
>      pre-read `FIXTURE_PROVENANCE.md` (authorization stubs). These are the
>      only S0 artifacts allowed before Oracle Gate B.
>   2. Oracle Gate B reviews those T1a artifacts only — it does not review
>      the spec amendment.
>   3. Only after Gate B passes may T1b (validator skeleton) begin. No custom
>      validator, fixture corpus, or production package/CLI may exist before
>      Gate B pass.
> - U1 is `frozen`: S0 = pure contract/oracle/
>   fixture/static test-only validation; production CLI, wheel/resources,
>   legacy reader, and CLI subprocess/runtime acceptance belong to S1.
> - S1 CLI implementation MUST NOT begin before S0 execution achieves S0 PASS.
> - Once reviewed, this document is the sole normative S0 execution plan.
>   Previous v5/pre-cutover implementation sequences are historical and
>   non-normative.

> **Current amendment status (2026-07-23)**: Phase 1 four-path commit
> `7de57f34ae3b77f133cee83ac8ee44084bb42c81` (active spec, S0 plan,
> `.gitignore`, `.ignore`) is already committed and pushed; Oracle Gate A
> passed; T0 passed. This edit is a later **two tracked-path authority
> amendment** (active spec + S0 plan only) caused by T1a human decisions.
> The `.gitignore` and `.ignore` are not touched and remain as committed
> in the Phase 1 four-path commit. This amendment requires focused Council +
> independent Oracle review, then exact two-path commit and push before T1a
> artifacts. Suggested commit message: `docs: freeze S0 lexical decisions`.
>
> After this amendment commit, rerun T0 clean-tree/remote/guard check, then
> create exactly `S0_DECISIONS.json` and pre-read `FIXTURE_PROVENANCE.md`,
> then Oracle Gate B (reviews artifacts only), then T1b.
>
> **Review strategy**: Council reviews the decision coherence and spec
> consistency of this two-path amendment. Independent Oracle reviews the
> exact same two tracked paths. Both must pass before commit. The Phase 1
> four-path commit (`7de57f34`) is historical and remains accurate — it
> does not describe the current commit allowlist.

## Authoritative References

| Reference | Path | Role |
|-----------|------|------|
| Active protocol spec | `docs/superpowers/specs/2026-07-20-aitp-2-0-command-skill-protocol-design.md` | Normative contract — all 9 P1 findings closed per audit disposition |
| Architecture audit | `docs/superpowers/audits/2026-07-20-aitp-2-0-command-skill-protocol-architecture-audit.md` | Non-normative; findings already resolved in revised spec |
| Audit disposition | `docs/superpowers/audits/2026-07-20-aitp-2-0-command-skill-protocol-audit-disposition.md` | P1 closures accepted; patches are non-normative |
| Cutover design | `docs/superpowers/specs/2026-07-21-aitp-2-0-repository-authority-cutover-design.md` | Phase 1–3 ordering; this plan's authority |
| Project memory | `PROJECT_MEMORY.md` | Sole active authority; 2.0 boundary |

None of these documents are superseded by this plan. They are referenced, not
replaced. The audit disposition already closed all nine P1 findings in the
revised spec; this plan does NOT re-apply audit patches. Any contract
clarification needed is handled through the decision register (§3) and, if
normative amendment is required, a separate reviewed spec/disposition
amendment — never a silent rewrite.

## 1. Scope and Non-Goals

### 1.1 Historical Phase 1 Plan Commit (Completed)

The Phase 1 plan commit (`7de57f34ae3b77f133cee83ac8ee44084bb42c81`)
modified exactly four paths and is complete:

1. `docs/superpowers/specs/2026-07-20-aitp-2-0-command-skill-protocol-design.md`
   (active spec amendment)
2. `docs/superpowers/plans/2026-07-23-aitp-2-0-s0-contract-and-fixture-freeze-plan.md`
   (this plan)
3. `.gitignore`
4. `.ignore`

Paths 3–4 were audited orchestration-support changes (`.gitignore` adds
`.slim/deepwork/` ignore; `.ignore` adds deepwork read allowlist). They
are not product authority and are not part of the current two-path
authority amendment. Deepwork content is ignored and not committed.

Commit message: `docs: freeze AITP 2.0 store and CLI behavior contracts`

**Current amendment** (see status block at top): exactly two tracked paths
(active spec + S0 plan only). The `.gitignore` and `.ignore` remain as
committed in the Phase 1 four-path commit and are not touched. Suggested
commit message: `docs: freeze S0 lexical decisions`.

### 1.2 Non-Goals (Current Amendment)

- No `tests/fixtures/aitp2/`, `FREEZE.json`, or fixture content.
- No `src/aitp/`, `pyproject.toml`, `__init__.py`, or Python package.
- No wheel, package resources, or `importlib.resources` metadata.
- No validators (`check_s0_freeze.py`, `test_s0_*.py`, `check_aitp2_simplicity.py`).
- No modification to `.gitignore`, `.ignore`, `.github/workflows/authority-guard.yml`, or any CI workflow.
- No real `.aitp`, store records, legacy adapter, CLI, writer, or dispatcher.
- No access to external `.aitp` or private research directories.
- No implementation commit, merge, or PR. After Council + independent Oracle
  review pass, only the exact two-path commit and push are permitted.

### 1.3 Non-Goals (Future S0 Execution)

U1 is `frozen`: S0 = static-only contract/oracle/fixture/validation;
S1 = production CLI/wheel/resources/legacy reader/CLI runtime acceptance.
The boundary below is normative for S0 execution.

S0 execution does NOT: implement CLI/parser/dispatcher/command behavior;
ship `using-aitp` or any installed Skill; build/publish a wheel; add MCP, hooks,
context compilers, databases, indexes, scanners, or semantic validators; mutate
any v5 canonical record or archive entry; install or uninstall anything.

Additionally, the following repository-local production artifacts MUST NOT exist
during S0 (historical archive and test fixture descriptions are NOT production):

- Root `pyproject.toml`, `setup.py`, `setup.cfg`, `MANIFEST.in`.
- `src/aitp/` or any non-historical, non-fixture path containing
  `aitp/__init__.py` as a package root.
- Any `*.dist-info/`, `*.egg-info/`, `dist/*.whl`, `build/**/aitp/` inside
  the repository.
- Repository-local command resources / `command_skills/` (wheel-resource
  scaffolding).

Repository-local import detectability is checked via
`importlib.machinery.PathFinder.find_spec("aitp", [<repo>/src, <repo>])` or an
equivalent explicit repo-root path list; it MUST NOT query or fail on globally
installed `aitp` packages outside the repository. S0 PASS is not satisfied by
merely asserting no console-entry point exists.

## 2. Future S0 Execution — Product Boundary

S0 delivers: (a) a frozen normative contract machine-checkable through fixtures,
(b) an authorized sanitized evidence corpus, (c) a blocking absence ratchet in CI.

This amendment extends the S0 product boundary with:

- **behavior-not-code-shape**: frozen contracts specify expected CLI
  subprocess, filesystem, Git, and stdout JSON observable behavior as
  fixture contracts and static oracles — not as executed production CLI
  behavior. Production CLI acceptance belongs to S1 per U1 resolution.
- **content envelopes**: natural Markdown note/derivation boundaries;
  Statement/Assessment/Relation/Episode extraction triggers (§6.0.1).
- **TOPIC/Route navigation**: homomorphic human/Agent spine with frozen
  Route fields (§5.1).
- **read coverage**: exact/deferred/skipped/not_checked vocabulary with
  budget and completeness reporting (§7.5).
- **failure recall — three machine oracles** (per active spec Assessment
  `route_effect` rules):
  1. Route-scoped unresolved failure Episode ↔ Route.known_failure_refs;
     resolved Episode ↔ Route.prior_attempt_refs + Episode.resolution_refs.
  2. Human-reviewed route_effect:blocks Assessment ↔ Route.blocking_assessment_refs.
  3. Human-reviewed route_effect:resolves_failure Assessment: target_ref must
     be a failure Episode, route sets equal, Episode.resolution_refs includes
     the Assessment, Route moves from known to prior.
   Plus: route_effect:unblocks Assessment: target_ref must point to a prior
   blocking Assessment currently on the Route; from each matching Route's
   `blocking_assessment_refs`, remove the prior blocking Assessment identified
   by `target_ref` (not the new unblocking Assessment). Both the prior blocking
   Assessment and the new unblocking Assessment must carry the same Route set
   and both remain in canonical/Git audit history. `enter` shows all; new
   success does not overwrite old failure.
- **gate matrix**: action→minimum gate table frozen (§14.0.1).
- **static expected-output contract fixtures**: JSON envelope (§4.1.1), error codes (§7.3),
  workspace states (§7.4), `not_available_in_stage` for unimplemented
  commands.
- **runtime inventory**: `runtime/indexes/topics/<topic-id>/INDEX.md` as
  noncanonical generated view; no canonical `topics/<id>/INDEX.md` (§5).

### 2.1 Twelve Command Groups — Name-Only Freeze

12 public command groups are frozen in name, topic/workspace/roots/outputs/
deterministic-checks/human-gates/finish contract only:

| Command | Frozen contract elements |
|---------|-------------------------|
| `enter` | topic resolution, orientation spine, `--budget-chars` |
| `search` | scoped `rg` coverage, scope flags |
| `show` | store-relative path, `@<commit>`, selectors |
| `research` | 6 modes, workspace scaffold, RECORD_PLAN gap reporting |
| `literature` | one-copy source, extraction immutability, anchor selectors |
| `checkpoint` | durable-moment triggers, minimal record set |
| `closeout` | declared-session-only sweep, no empty Episode |
| `knowledge` | dream/refresh/link/finish; card assertion binding; input budget |
| `skill` | distill/package/install/update/rollback; receipt; card deps |
| `write` | note/derivation/report/article/presentation; format convention |
| `audit` | deterministic structural checks; no scientific judgment |
| `admin` | init/doctor/migrate/backup/recover/config-show; Git ownership |

S0 does NOT implement parser, dispatcher, subcommand routing, or runtime behavior.

### 2.2 Seven Node Roles + One Relation Edge — Registry Freeze

Exactly 7 node roles + 1 edge role:
`Topic | Entity | Route | Statement | Episode | Assessment | Asset` + `Relation`.

Asset kinds use purpose-specific path profiles from active spec §5. No Asset
kind creates an 8th node role or a generic `assets/` directory.

### 2.3 Common Header and Profile-Specific Rules

Seven common header fields: `schema`, `id`, `type`, `topic`, `title`, `created_at`,
`created_by`. `kind` is required only when the type profile has multiple kinds
(Entity, Statement, Episode, Assessment, Asset); omitted for Topic, Route, Relation.
Each kind-specific profile may require at most 12 additional frontmatter fields.

### 2.4 Canonical Asset-Kind Path Mapping

Every Asset kind has exactly one scope-sensitive path profile. A profile may
enumerate multiple legitimate path templates (topic-local vs. shared, e.g.,
`topics/<topic-id>/knowledge/cards/<id>.md` and `shared/knowledge/cards/<id>.md`).
Each concrete record maps to exactly one of those templates based on its `topic`
field. No kind has ambiguous paths; no single path hosts multiple kinds.

### 2.5 Ref Grammar

Canonical refs are store-relative POSIX paths with an optional full Git object-id
revision (`@<full-git-object-id>`) and at most one payload/anchor selector
(`#payload=<rel>` or `#anchor=<extraction-id>/<anchor-id>`). The object-id is
whatever full form the owning Git resolves and emits — no fixed length is
hardcoded. Resolution constraints (reject traversal, drive letters, backslash,
symlink escape; pinned read through `git show`; distinct error codes
`not_found`, `invalid_ref`, `outside_store`, `forbidden_canonical_path`,
`revision_not_found`, `profile_mismatch`, `payload_hash_mismatch`,
`anchor_not_found`) are as specified in active spec §6.1 and the frozen
error enum in active spec §7.3 with per-code integer priorities.

### 2.6 Relation Contract

The 16 predicates are the exact closed set from active spec §6.2:
`about | related_to | depends_on | conflicts_with | parallelizable_with |
derived_from | supports | contradicts | produced | uses | implements |
validated_by | failed_because | supersedes | applies_to | installed_as`.
Relations record links; they never promote scientific trust.

### 2.7 Store / Git Ownership

Topics and shared are canonical; runtime is noncanonical. One-copy paper model.
Promotion creates a new reviewed file (copy, not move). Enclosing Git and
standalone Git are exclusive; no implicit nested `.git`.

### 2.8 Command-Skill Package Contract (Freeze Only)

Resources at `aitp/command_skills/<command>/SKILL.md`, `templates/`, `profile.yaml`;
resolved through `importlib.resources`, version-matched. No cwd override, no
second Skill root. S0 freezes the expected inventory assertion only — no
implementation, no wheel, no `importlib.resources` call.

### 2.9 Writer / Human-Review Transaction Invariants

One canonical writer, one visible finish path. Invariant: audit → stage →
exact diff → human review binding → serialized Git commit → readback. Frozen
as structural invariant only; no writer code.

### 2.10 Legacy Compatibility Boundary

Legacy records: read-only, no-import, no-write, no-dual-write, no-fallback.
Adapter may return paths + clearly labelled legacy metadata; cannot write,
mutate, promote trust, or make old schemas canonical. Legacy reader
implementation belongs to S1 per U1 resolution. S0 freezes byte-preservation
and read-only compatibility fixtures only. See §3.1.

## 3. Blocking Decision Register

S0 execution must carry a machine-readable JSON decision register (NOT YAML)
committed as `tests/fixtures/aitp2/S0_DECISIONS.json`. It is review/test
evidence, not a second authority. Any normative resolution MUST be reflected in
an approved active-spec/disposition authority amendment before it can be marked
`frozen`. The decision register catalogs open items; the spec + disposition
remain the sole normative truth.

### 3.1 Decision Table

T0 passed and the user explicitly resolved D1–D6 and D8–D9 on 2026-07-23;
D7 and U1 were previously frozen. This later authority amendment updates the
plan's current decision status to reflect those completed T1a human decisions.
All decisions are now `frozen` — zero `user-decision-required` entries remain
once reviewed and committed. The decision register is reproduced below with
exact resolutions:

| # | Decision | Status | Spec ref | Notes |
|---|----------|--------|----------|-------|
| D1 | Timestamp lexical form | `frozen` | active spec §6 (T1a D1) | `YYYY-MM-DDTHH:MM:SSZ` UTC, uppercase `Z`, no offset/space/fractional. `decided_by: user`, `decided_at: 2026-07-23`. |
| D2 | `created_by` identity format | `frozen` | active spec §6 (T1a D2) | `human:<slug>` or `agent:<slug>`; slug grammar `[a-z0-9]+(?:[._-][a-z0-9]+)*`, 1–64 code points. `decided_by` and `reviewer` must use `human:`. `decided_by: user`, `decided_at: 2026-07-23`. |
| D3 | YAML subset for frontmatter | `frozen` | active spec §6 (T1a D3) | **User engineering decision (2026-07-23)**: simplest standard approach — comments completely forbidden (no MAY), `#` as first character forbidden (conflicts with YAML comment indicator), internal `#` not preceded by space is ordinary scalar data. Two scalar forms frozen: (1) plain scalar with positional character restrictions (first-char indicator list including `#`, `: ` and ` #` forbidden internally, `RPA & GW` and `path.md#anchor=...` valid; bare leading `#anchor=...` requires JSON double-quote), and (2) JSON double-quoted string via stdlib `json.loads` with post-decode constraint (nonempty single-line printable Unicode, no CR/LF/ASCII controls, no escape-bypassed newlines) for ambiguous content. Exact tokens `[]` and `{}` are the only flow-collection exception (empty sequence/map only). Exact line grammar frozen. Quoted scalars other than JSON double-quoted forbidden. Bounded typed interpretation. Deterministic error mapping: malformed/duplicate keys/unknown fields → primary `profile_mismatch`; candidate `validation` list entry `{check_id: frontmatter_profile, status: fail}`; optional secondary `validation_failed` appears only in common envelope `errors[]` per frozen error total order. No PyYAML import; S0 test-only parser uses stdlib only. `decided_by: user`, `decided_at: 2026-07-23`. |
| D4 | Duplicate YAML keys | `frozen` | active spec §6 (T1a D4) | Rejected at every nesting level. Fail closed with `profile_mismatch` (per D3 deterministic error mapping). `decided_by: user`, `decided_at: 2026-07-23`. |
| D5 | ULID case normalization | `frozen` | active spec §6 (T1a D5) | Uppercase Crockford Base32 `[0-9A-HJKMNP-TV-Z]{26}`. Reject lowercase and I/L/O/U. `decided_by: user`, `decided_at: 2026-07-23`. |
| D6 | Encoding and newline | `frozen` | active spec §6 (T1a D6) | UTF-8 without BOM, LF-only, exactly one trailing LF, no CR bytes. `decided_by: user`, `decided_at: 2026-07-23`. |
| D7 | Full Git object-id in refs | `frozen` | active spec §6.1 | Use whatever full object-id the owning Git resolves and emits. No fixed hex length. Interactive `show` may accept unambiguous abbreviations but emits the full id. |
| D8 | Field order normative? | `frozen` | active spec §6 (T1a D8) | No — equality is semantic, not byte-order. Validators MUST NOT reject solely for key reordering. `decided_by: user`, `decided_at: 2026-07-23`. |
| D9 | Unknown frontmatter fields | `frozen` | active spec §6 (T1a D9) | Rejected at every level including nested objects (e.g. `assessor`). Fail closed with `profile_mismatch` (per D3 deterministic error mapping). `approval_binding` is NOT a nested frontmatter example — it is runtime CANDIDATE JSON/commit metadata. `decided_by: user`, `decided_at: 2026-07-23`. |
| **U1** | **S0 wheel/resource and legacy-read stage interpretation** | **`frozen`** | active spec §17 S0/S1 | **Resolved**: S0 = pure contract/oracle/fixture/static test-only validation. Production CLI, wheel/resources, legacy reader, and CLI subprocess/runtime acceptance belong to S1. `decided_by: user`, `decided_at: 2026-07-23`. Resolution recorded in this plan amendment; the active spec §17 S0/S1 reflects this boundary. |

### 3.2 Statuses

- **`frozen`** — resolved deterministically; S0 machines can enforce.
- **`user-decision-required`** — must be resolved by explicit human decision before S0 PASS. No default assumed.
- **`explicitly-deferred`** — deferred to a named slice with rationale and acceptance criteria.

No `TBD`, `pending`, `discuss`, or blank. Any decision not `frozen` or
`explicitly-deferred` at S0 PASS time blocks S0 PASS.

### 3.3 Decision Status

All D1–D9 and U1 decisions are now `frozen`. The user resolved D1–D6 and
D8–D9 on 2026-07-23; D7 and U1 were previously frozen. The active spec
§6 T1a subsection is the sole normative authority for the resolved lexical
rules. Gate A did not make these decisions — the user did at T1a-time via
this authority amendment.

**Generic rule for any future amendment**: If a future review or execution
phase reveals a genuine ambiguity or contradiction not covered by an
existing decision entry, S0 (or the affected stage) is BLOCKED. A separate
reviewed authority amendment — never a silent plan edit — must precede any
decision freeze. The decision register gate (`valid statuses only`,
`no TBD/pending/discuss/blank`) remains active for all future S0 execution
phases.

## 4. Fixture Authorization, Provenance, and Redaction

### 4.1 Authorization (Pre-Read)

For each real research source (quantum-chaos, NiO), BEFORE reading any source
byte, the S0 executor must:

- Record in `FIXTURE_PROVENANCE.md`:
  - Symbolic source ID and root class.
  - Owner/approver identity and approval evidence.
  - Authorized scope (which directories/files/version ranges).
  - Access restrictions (read-only, no redistribution, no raw binary, etc.).
- No snapshot commit SHA or file hash is required at this stage; the executor
  has not yet read any source byte.

### 4.2 Provenance Record (Post-Authorization, Pre-Copy)

After authorization is obtained, the executor may:

- Read source bytes in a controlled, read-only manner.
- Compute Git snapshot commit SHA and/or selected file hashes:
  - For Git-tracked sources: prefer `commit` SHA + selected per-file hashes.
  - For non-Git sources: use file hashes (SHA-256).
- Complete `FIXTURE_PROVENANCE.md` snapshot fields.

All provenance snapshot fields (commit SHA, file hashes, inventory) MUST be
completed BEFORE selecting or copying any fixture byte into
`tests/fixtures/aitp2/`.

### 4.3 Provenance Record Content

`tests/fixtures/aitp2/FIXTURE_PROVENANCE.md` records per fixture file: source
class, snapshot Git commit SHA (if Git) or file hash (if non-Git), authorized
scope, selected records + rationale, redactions (paths → symbolic placeholders;
credentials → removed; private URLs/hosts → removed), transformations,
synthetic markers (`synthetic: true`), and restrictions.

### 4.4 Prohibited Content

No private absolute paths, credentials/tokens/keys, hostnames/IPs/private URLs,
restricted PDF or raw binary content, or paywalled source bytes.

### 4.5 Seeding State

If authorized material is insufficient, declare `state: seeding` for the affected
vertical. Seeding allows controlled synthetic content labelled `synthetic: true`
but MUST NOT claim the vertical is `frozen`. S0 remains BLOCKED on that vertical
until authorization or spec amendment.

### 4.6 Plan Boundaries

This plan references no machine-specific path, hostname, credential, or private
locator. Source categories use symbolic placeholders per the cutover design
appendix.

## 5. Future S0 Minimum Expected Layout

None of the following are created by this plan commit.

### 5.1 Fixture Corpus (Structural Evidence Only)

Fixtures cover S0 frozen structural invariants: record profiles, path mapping,
ref grammar, relation predicates, store/Git invariants, and safety boundaries
(ref traversal, symlink escape, legacy-write rejection). They do NOT cover full
command E2E behavior, Dreaming, Skill install, writing, or host behavior — those
belong to S3–S6. Required fixture families:

```
tests/fixtures/aitp2/
  FIXTURE_PROVENANCE.md
  FREEZE.json                   — human-reviewed test oracle (see §5.3)
  quantum-chaos/                — structural positive: topic, entities, routes,
                                   statements, episodes, assessments, relations,
                                   knowledge cards, code revisions, runs
  nio/                          — structural positive: code revisions, patches,
                                   runs, workflows, skills, install receipts
  shared-paper/                 — one-copy paper, extraction, cross-topic anchors
  knowledge-card/               — multi-anchor assertions, card health states
  skill/                        — Relation(predicate=uses) exemplars
  negative/                     — invalid header/path/ref/relation/provenance;
                                   traversal escape; legacy-write-attempt
```

Coverage rule: each S0 frozen structural invariant must have at least one
direct positive or negative evidence fixture. Safety boundaries (traversal,
symlink escape, credential rejection, legacy write) require negative evidence.
Requiring "positive + negative per normative rule" is rejected as over-broad.

Extended fixture families for behavior contracts added by this amendment:

```
tests/fixtures/aitp2/
  ...
  navigation/                   — TOPIC.md → Route → context/source_note/
                                    SOURCE/prior_attempt/known_failure/
                                    blocking_assessment/next_action spine
  content-envelope/             — natural Markdown note with formulas +
                                    sidecars NOT decomposed into per-sentence
                                    nodes; Episode distinct from transcript
  read-coverage/                — exact/deferred/skipped/not_checked states;
                                    budget/truncated/completeness reporting
  gate-matrix/                  — action→minimum gate assertions
  cli-contract/                 — JSON envelope, error codes,
                                    not_available_in_stage response
  runtime-inventory/            — noncanonical INDEX.md with generated/
                                    canonical fields
```

Additional negative fixture cases required (at minimum):

| Negative case | What it proves |
|---------------|---------------|
| Canonical `topics/<id>/INDEX.md` exists | Rejected as forbidden canonical path |
| Missing `known_failure_refs` on Route with unresolved route-scoped failure Episode | Failure recall oracle 1: unresolved failure must appear in known_failure_refs |
| Truncated file marked `exact` when itself truncated | Truncated individual item ≠ exact per §7.5; global truncation does not affect unrelated fully-read items |
| Partial search reported as absence | Absence claim requires complete search |
| Profile/Skill version bump lowers gate | Gate matrix floor cannot be downgraded |
| Unknown stage returns silent no-op | Must return `not_available_in_stage` |
| Noncanonical INDEX treated as canonical truth | INDEX is generated, canonical is authoritative |
| `forbidden_canonical_path` not raised for path profile violation | Must reject record at wrong kind path |
| Bidirectional ref mismatch per oracle 1/2/3 | Route refs must agree with Episode/Assessment per three machine oracles; blocks Assessment in blocking_assessment_refs |
| Draft Assessment mutates trust/unblocks/resolves | `review_state:draft` must not affect derived states |
| `run-ULID` Asset ID prefix used | All Asset IDs must use `asset-ULID` |
| Decision overlay missing `decided_by` or self-approved by Agent | Canonical decisions require human gate |

### 5.2 Validators and Tests

```
tests/aitp2/
  check_s0_freeze.py            — stdlib-only oracle validator
  test_s0_contract_freeze.py    — unittest: positive corpus
  test_s0_negative_contracts.py — unittest: negative corpus, distinct errors
  test_s0_simplicity_ratchet.py — unittest: phase-aware S0 absence
  test_s0_workflow_contract.py  — unittest: bounded workflow structural contract
```

### 5.3 FREEZE.json — Human-Reviewed Test Oracle

`FREEZE.json` is a human-reviewed, hand-maintained test oracle. Every field
must carry `authority_path`: an authority commit SHA (the spec/disposition
commit that normatively defines the field) + its section anchor (e.g.,
`"authority_path": "<spec-commit-sha>:§6.1"`). Line numbers are permitted as
auxiliary information but are not authoritative — section anchors bind to
normative content, not byte offsets.

**Normative priority**: The active spec text is the normative authority.
FREEZE.json is a reviewed oracle derived from the spec. In case of conflict,
the active spec text wins; FREEZE.json must be re-reviewed and updated to
match. Any spec change that affects a frozen contract surface requires
synchronized re-review of the oracle.

### 5.4 Simplicity / CI

```
scripts/
  check_aitp2_simplicity.py     — stdlib-only; --phase s0 (see §8)
.github/workflows/
  aitp2-s0-contract.yml         — NEW independent workflow (does NOT modify
                                   existing authority-guard.yml, whose
                                   self-contract locks it to 1 job / 3 steps)
```

## 6. Task DAG (T0–T5)

Tasks are ordered: validator exists before fixtures depend on it. No task defines
success by "a CLI could implement this." Every task's verification command must
be actually runnable at the time the task is executed.

### T0 — Preflight (No Commit)

- **Depends on**: reviewed plan commit.
- **Files**: none created.
- **Observable claim**: S0 execution base is a descendant of the reviewed plan
  commit that includes `389b...` in its ancestry; local == remote; tree clean;
  `check_repository_authority.py` passes.
- **Main baseline (`origin/main`)**: `eec20f6faeb089ec2fcdc982ad65adce242a21a9`
  is the recorded cutover baseline. If at T0 time `origin/main` differs from
  this SHA, do NOT automatically merge, rebase, or silently treat the
  difference as passing. STOP and perform an authority impact review: the
  advanced `origin/main` may contain spec/authority changes that affect S0
  scope. S0 is never required to roll back its branch to match the baseline;
  divergence must be explicitly acknowledged and assessed. Snapshot evidence
  (the checked `origin/main` SHA) is recorded as metadata in the first tracked
  S0 artifact commit (T1a), not in a separate empty commit.
- **Main failure modes**: wrong base; remote diverged; dirty tree; baseline
  drifted without impact review.
- **Steps**:
   1. `git fetch origin`
   2. Verify current HEAD is a descendant of `389b3149ef9f6dd054ed82e0e7821c2868a4972e`:
      `git merge-base --is-ancestor 389b3149ef9f6dd054ed82e0e7821c2868a4972e HEAD`
   3. Verify local HEAD == remote HEAD for this branch.
   4. `git status --porcelain` must be empty.
   5. `python3 scripts/check_repository_authority.py` exits 0.
   6. Compare `origin/main` SHA against cutover baseline
      `eec20f6faeb089ec2fcdc982ad65adce242a21a9`. If different:
      STOP — record the discrepancy and perform an authority impact review
      before proceeding. Do not auto-merge, rebase, or silently accept.
- **Verification**: all `git` commands pass; guard exits 0; baseline impact
  acknowledged.

### T1a — Authority Interpretation + Blocking Decisions + Authorization Record

- **Sequence constraint**: The T1a spec amendment (D1–D9 decisions recorded in the
  active spec, plus this plan) must be reviewed and committed first
  before T1a creates any S0 artifacts. T1a then creates
  `S0_DECISIONS.json` and pre-read `FIXTURE_PROVENANCE.md`. Oracle Gate B
  reviews those artifacts; only after Gate B passes may T1b begin.
- **Depends on**: T0 (spec amendment committed, tree clean, authority guard passes).
- **Files (create)**:
    - `tests/fixtures/aitp2/S0_DECISIONS.json` — copies all now-frozen
      D1–D9 plus U1 decisions and authority refs from §3.1. No new
      decision is needed at T1a artifact time — all decisions were
      already resolved by the user on 2026-07-23 and recorded in the
      active spec §6 T1a subsection and this plan §3.1. The register
      is a machine-readable copy for traceability and validator use;
      if review finds any inconsistency between the register and the
      active spec, that is a blocking finding. U1 remains traceability-only
      (copied from §3.1, not re-opened).
   - `tests/fixtures/aitp2/FIXTURE_PROVENANCE.md` — authorization stubs
     with pre-read fields per §4.1 (symbolic source ID/class, owner/approver,
     authorized scope, restrictions, approval evidence); NO snapshot hashes
     or source bytes at this stage.
- **Observable claim**: all `user-decision-required` entries resolved by
  explicit T1a human decisions; U1 already frozen; authority traceability
  established.
- **Main failure modes**: decision register contains `TBD`; spec amendment
  needed but not done.
- **Decision register validation** (manual + simple JSON check):
  - Exact entry set is D1–D9 plus U1; U1 is `frozen`
    and requires no further resolution.
  - Only three statuses allowed: `frozen`, `user-decision-required`,
    `explicitly-deferred`.
  - T1a completion condition: ZERO `user-decision-required` entries remain.
  - D7 is `frozen` and includes an active-spec authority ref.
  - Each `frozen` normative resolution includes an approved
    authority/amendment ref.
  - Each `explicitly-deferred` entry includes named slice, rationale, and
    acceptance criteria.
  - FIXTURE_PROVENANCE.md authorization stub exists and contains pre-read
    fields: symbolic source ID/class, approver, scope, restrictions,
    approval evidence. MUST NOT contain unauthorized snapshot bytes or
    hashes computed before authorization.
  Any failure → STOP; T1a cannot proceed to Oracle Gate B.
- **Steps**:
   1. Populate `S0_DECISIONS.json` with all entries from §3.1.
   2. User/designated human authority explicitly decides each
      `user-decision-required` entry; T1a STOP if any blocker remains.
   3. If resolution requires a normative spec/disposition authority amendment,
      produce that as a separate reviewed commit before continuing. T1a STOP
      until the amendment is independently reviewed and approved.
   4. If any decision reveals a genuine active-spec ambiguity or conflict not
      in the register, BLOCK and obtain explicit user approval for an
      authority amendment before proceeding.
   5. Write FIXTURE_PROVENANCE.md authorization stubs per §4.1.
- **Verification**:
  - Manual review of `S0_DECISIONS.json` confirms zero
    `user-decision-required`.
  - Simple JSON validation: all entries present, statuses valid.
  Any failure → STOP; T1a incomplete.
- **Commit**: `docs: establish S0 decisions and authorization record`

### Oracle Gate B

Oracle Gate B reviews T1a artifacts only — it does NOT review the spec
amendment, resolve fixture authorization, implementation choices, or
S0 acceptance. Gate B confirms that T1a correctly produced:
- All D1–D9 decisions explicitly resolved (U1 already frozen).
- Decision register entries are authority-traceable.
- FIXTURE_PROVENANCE.md authorization stubs are present and follow §4.1.
- No source bytes have been read or committed.
- No custom validator, fixture corpus, or production package/CLI exist yet
  (T1a decision register and pre-read provenance stubs are the only S0
  artifacts present).
Gate B STOP if any failure. T1b (validator skeleton) MUST NOT begin
before Gate B passes.

### T1b — Validator Core And Synthetic Self-Tests

- **Depends on**: Oracle Gate B pass.
- **Inputs**: `S0_DECISIONS.json` (all decisions frozen/explicitly-deferred,
  zero `user-decision-required`), `FIXTURE_PROVENANCE.md` pre-read stubs
  (no source bytes committed), active spec authorities.
- **Files (create)**:
   - `tests/aitp2/check_s0_freeze.py` — stdlib-only oracle validator skeleton
     supporting `--decisions-only` mode.
   - `tests/aitp2/test_s0_contract_freeze.py` — synthetic temp-dir self-tests
     proving the validator core works (no real fixtures).
- **Observable claim**: validator core functional; `--decisions-only` passes
  and validates the decision register against the frozen error enum from the
  active spec §7.3.
- **Main failure modes**: validator imports non-stdlib; `--decisions-only`
  passes on invalid register; decision register contains unrecognized status;
  validator uses non-frozen error codes; validator touches external `.aitp`.
- **Steps**:
   1. Implement `check_s0_freeze.py` skeleton: stdlib-only, no third-party
      imports, no `aitp` imports.
   2. Implement `--decisions-only` mode: reads `tests/fixtures/aitp2/S0_DECISIONS.json`,
      validates JSON schema, all entry statuses in `{frozen, user-decision-required,
      explicitly-deferred}`, D1-D9 entries present plus U1, U1 is `frozen`,
      D7 is `frozen`, no `TBD`/`pending`/`discuss`/blank statuses, all `frozen`
      entries have authority ref, all `explicitly-deferred` entries have slice/rationale/acceptance.
   3. Implement synthetic self-tests in `test_s0_contract_freeze.py`: create
      tempdirs with valid/invalid `S0_DECISIONS.json` files, run
      `check_s0_freeze.py --decisions-only`, assert exit codes and error messages
      reference the frozen error enum from §7.3.
- **Local verification**:
  - `python3 tests/aitp2/check_s0_freeze.py --decisions-only` exits 0 on valid register.
  - `python3 tests/aitp2/check_s0_freeze.py --decisions-only` exits non-zero on
    register with `TBD`, unrecognized status, missing U1, or missing authority refs.
  - `python3 -m unittest tests/aitp2/test_s0_contract_freeze.py` exits 0.
- **Stop conditions**: T1b STOP if any `user-decision-required` entry remains;
  if spec ambiguity not covered by a decision entry blocks validator rules;
  if stdlib-only constraint violated; if existing authority files modified.
- **Commit**: `test: establish S0 validator core`

### T2 — Reviewed FREEZE.json + Validator Integration + Synthetic Negatives

- **Depends on**: T1b (`--decisions-only` pass confirmed; no `user-decision-required`
  entries remain).
- **Files (create/modify)**:
  - Create: `tests/fixtures/aitp2/FREEZE.json` — reviewed, authority-annotated.
  - Create: `tests/aitp2/test_s0_negative_contracts.py` — synthetic negative
    tests using `tempfile.TemporaryDirectory`.
  - Modify: `tests/aitp2/check_s0_freeze.py` — implement two explicit modes
    (see below).
- **Observable claim**:
  - FREEZE.json encodes the complete frozen contract surface with
    `authority_path` annotations referencing the active spec and decision
    register. The frozen surface now includes: 12 command groups, 7+1
    node/edge roles, 16 predicates, common header + kind, Asset path
    profiles, ref grammar, Relation contract, store/Git ownership,
    content envelope boundaries (§6.0.1), minimum profile fields (§6.0.2),
    Route navigation fields (§5.1), JSON envelope (§4.1.1), error codes
    (§7.3), workspace states (§7.4), read coverage semantics (§7.5),
    enter behavior (§7.6), gate matrix (§14.0.1), writer behavioral
    contract (§14.0.2), and noncanonical INDEX contract (§5).
  - `check_s0_freeze.py --oracle-only` validates FREEZE.json schema correctness,
    12 command groups, 7+1 node/edge roles, 16 predicates, authority anchor
    presence, decision refs, and synthetic temp-directory negatives. It does
    NOT claim real fixture coverage or skip/pass on empty fixture directories.
  - Negative suite exercises distinct error codes via synthetic
    `TemporaryDirectory` fixtures.
- **Main failure modes**: FREEZE.json field lacks authority anchor; validator
  passes on a violation; empty fixture directories incorrectly report PASS
  (must NOT — `--oracle-only` reports "no real fixture coverage claimed" but
  synthetic negatives must still pass); D3/D4 frontmatter parser contract
  is now `frozen` (T1a authority amendment 2026-07-23 — see active spec
  §6 D3/D4); resolution is complete and not deferrable.
- **`check_s0_freeze.py` Modes**:
  1. **`--oracle-only`** (T2): Validates FREEZE.json JSON schema, 12/7+1/16
     counts, every field carries `authority_path`, decision register refs
     resolve, and synthetic temp-directory negatives produce distinct error
     codes. Does NOT require real fixture families to exist — explicitly
     reports "oracle-only: no real fixture coverage claimed." Empty fixture
     directories do NOT cause PASS for real fixture checks; they are
     acknowledged as absent with a diagnostic note. This mode is sufficient
     for T2 completion.
  2. **Default / full mode** (T3+): In addition to all `--oracle-only` checks,
     requires every expected fixture family from §5.1 to be present with
     FIXTURE_PROVENANCE.md entries. Missing families → FAIL. No skip-as-pass.
     Synthetic-only coverage is insufficient; real structural fixtures must
     exist.
- **Steps**:
   1. Author FREEZE.json by hand from active spec and decision register.
      Every field includes `authority_path` (e.g.,
      `"authority_path": "<spec-commit-sha>:§6.1"`; line numbers may be
      appended as auxiliary data but are not authoritative).
   2. Implement `check_s0_freeze.py` with both `--oracle-only` and default/full
      modes per the contract above.
   3. Write negative tests: each creates a tempdir, writes a deliberately
      invalid fixture, and asserts the exact expected error code.
   4. D3/D4 (frontmatter YAML lexical policy) are already `frozen` per
      the T1a authority amendment 2026-07-23 (active spec §6 D3/D4).
      The bounded two-form scalar grammar — two scalar forms, first-
      character restrictions, internal-sequence rules, JSON double-quote
      post-decode constraints, forbidden YAML syntax forms, empty `[]`/`{}`
      sentinels only — is the sole normative rule. The FREEZE.json and
      validator MUST encode these frozen D3/D4 rules directly. Any
      future change to D3/D4 requires a new reviewed authority amendment;
      deferral to S1 is prohibited.
- **Verification**:
  - `python3 tests/aitp2/check_s0_freeze.py --oracle-only` exits 0; reports
    12/7+1/16 counts confirmed; all authority anchors present; synthetic
    negatives produce distinct errors.
  - `python3 -m unittest tests/aitp2/test_s0_negative_contracts.py` exits 0.
- **Commit**: `test: reviewed FREEZE.json oracle with authority anchors and synthetic negative suite`

#### T2 Future Negative Evidence (Council Required — No Files Created Before Gate B)

The following contract surfaces require negative fixture evidence at T2/T3.
They are specified here as planning requirements; no files are created now.

- Assessment `kind: assessment` valid/invalid — common kind literal presence.
- `budget.truncated: true` with fully-read unrelated items still `exact` —
  item-local truncation semantics.
- Mandatory nondiscardable refs overflow — `used > requested` legal.
- Frontmatter-only validation — no semantic Markdown body/frontmatter
  consistency judgment; `profile_mismatch` only for mechanical mismatches.
- Candidate `validation` digest: golden vector, check_id reorder invariance,
  duplicate check_id fail, deterministic commit all-pass vs. one-fail.
- Deterministic `required_gates: []` candidate vs. non-empty human gate ID
  candidate; illegal gate ID `required_gates` fail.
- Empty `validation` list at `review_ready` → `validation_failed` negative;
  missing universal `candidate_integrity` check → `validation_failed`; each
  operation and declared gate must have ≥1 applicable deterministic check.
- Per-code error total order: each frozen error code produces its unique
  priority as primary; fixtures cover all 19 codes with golden vectors.
- Three failure link oracles: (1) unresolved ↔ known_failure_refs,
  (2) blocks ↔ blocking_assessment_refs, (3) resolves_failure machine
  rules; plus unblocks removal.
- U1 traceability-only scan: T1a entry present with user decision copy and
  authority ref, not re-opened.

### T3 — Provenance + Minimal Sanitized Structural Fixtures

- **Depends on**: T2 (validator exists with `--oracle-only` mode verified).
- **Files (create)**: all positive and negative fixture families under
  `tests/fixtures/aitp2/`:
  `quantum-chaos/`, `nio/`, `shared-paper/`, `knowledge-card/`, `skill/`,
  `navigation/`, `content-envelope/`, `read-coverage/`, `gate-matrix/`,
  `cli-contract/`, `runtime-inventory/`, `negative/`.
  Updates to FIXTURE_PROVENANCE.md.
- **Observable claim**: validator default/full mode (no `--oracle-only` flag)
  passes on all positive fixtures and reports expected failures on all negative
  fixtures; FIXTURE_PROVENANCE.md records source class, snapshot hashes,
  redactions, and `seeding` declarations; no private path/credential/host/URL
  exists. Missing fixture families → FAIL (no skip-as-pass in full mode).
  Structural fixtures must cover TOPIC → Route → source_note / SOURCE /
  prior_attempt / known_failure / blocking_assessment / next_action spine,
  content envelope boundaries, read coverage reporting, gate matrix, CLI
  static expected-output contract fixtures, runtime inventory, human decision overlay, and
  failure-recall bidirectional refs. Run and code fixture records are
  record/profile schema fixtures only — not command integration/E2E; real
  command E2E belongs to S3. All Asset owner IDs use `asset-<ULID>`.
- **Main failure modes**: unauthorized source access; private data leakage;
  insufficient authorized material → `seeding` declared; fixture family absent
  from provenanced corpus → full mode FAIL.
- **Steps**:
   1. Verify authorization stubs per §4.1 exist for every source root before
      any read.
   2. For each authorized source root, read-only access to compute Git
      snapshot commit SHA (Git sources) or file hashes (non-Git sources),
      and complete provenance snapshot fields per §4.2.
   3. Select records demonstrating S0 structural invariants only (not E2E
      command behavior).
   4. Redact: machine paths → symbolic placeholders; credentials → removed;
      private URLs/hosts → removed; restricted bytes → not copied.
   5. Create negative fixtures for safety boundaries: traversal refs, symlink
      escape, invalid profiles, legacy-write-attempt.
   6. Run provenance/secret scan via validator's built-in rules + synthetic
      negatives (no ad-hoc grep).
   7. Update FIXTURE_PROVENANCE.md with per-file records and `seeding` states.
- **Verification**:
  - `python3 tests/aitp2/check_s0_freeze.py` (default/full mode) exits 0,
    reports PASS for all present fixture families, FAIL for any missing
    required family.
  - `python3 -m unittest discover -s tests/aitp2 -p 'test_*.py'` exits 0.
- **Commit**: `test: authorized sanitized structural fixtures with provenance`

### T4 — Simplicity Ratchet and S0 CI Workflow

- **Depends on**: T3.
- **Files (create)**:
  - `scripts/check_aitp2_simplicity.py` — stdlib-only; `--phase s0`.
  - `tests/aitp2/test_s0_simplicity_ratchet.py` — unittest asserting Phase
    S0 rules.
  - `tests/aitp2/test_s0_workflow_contract.py` — stdlib structural contract
    test for the fixed S0 CI workflow (see below).
  - `.github/workflows/aitp2-s0-contract.yml` — NEW independent workflow
    (does NOT modify `.github/workflows/authority-guard.yml`).
- **Observable claim**: ratchet passes when all repository-local production
  artifacts listed in §8.1 are absent; any presence is immediate FAIL (no
  Phase 1+ alternative in S0). Import check uses explicit repo-root paths
  only, never global site-packages.
- **Main failure modes**: ratchet passes when `src/aitp/` exists; wrong phase
  invoked; workflow overlaps with authority-guard.
- **Steps**:
   1. Implement `check_aitp2_simplicity.py` with `--phase s0` enforcing the
      complete absence table in §8.1:
      - Assert no root `pyproject.toml`, `setup.py`, `setup.cfg`, `MANIFEST.in`.
      - Assert `src/aitp/` does not exist and no non-historical, non-fixture
        path contains `aitp/__init__.py`.
      - Assert no `*.dist-info/`, `*.egg-info/`, `dist/*.whl`, `build/**/aitp/`.
      - Assert no repository-local `command_skills/`.
      - Assert `importlib.machinery.PathFinder.find_spec("aitp", [<repo>/src,
        <repo>])` returns `None`.
      - Any presence → FAIL immediately.
      - Document (but do not enforce in S0) the future S1 ceilings: ≤12 commands,
        7+1 nodes, 1 writer, ≤12K LOC, ≤500 LOC/file, zero v5 imports,
        wheel resources present — as a synthetic future-mode contract for
        reference only.
  2. Write `test_s0_simplicity_ratchet.py` asserting the above.
   3. Create `.github/workflows/aitp2-s0-contract.yml` with exactly four jobs:
      - `s0-decisions`: `python3 tests/aitp2/check_s0_freeze.py --decisions-only`
      - `s0-freeze-full`: `python3 tests/aitp2/check_s0_freeze.py`
      - `s0-negative-suite`: `python3 -m unittest discover -s tests/aitp2 -p 'test_*.py'`
      - `s0-simplicity`: `python3 scripts/check_aitp2_simplicity.py --phase s0`
      Every job has exactly three ordered steps: (1) `actions/checkout@v6`
      with `fetch-depth: 0`; (2) `actions/setup-python@v5` with
      `python-version: "3.12"`; (3) that job's sole `run` command above.
      No job may override the workflow-level `permissions: contents: read`.
   4. Implement `test_s0_workflow_contract.py` (stdlib-only; does NOT claim
      general-purpose YAML parsing). This test enforces a bounded
      indentation/text structure contract for the exact fixed workflow at
      `.github/workflows/aitp2-s0-contract.yml`:
      - Triggers are exactly `pull_request` and `push.branches: [main]`.
        `pull_request_target`, `schedule`, and `workflow_dispatch` are forbidden.
      - Permissions: read-only `contents`; NO write, admin, or deploy
        permissions.
      - Exact expected job names and run commands are the four pairs in Step 3.
      - Every job has exactly the three ordered steps from Step 3. The only
        allowed `uses` steps are `actions/checkout@v6` (`fetch-depth: 0`) and
        `actions/setup-python@v5` (`python-version: "3.12"`); each job then has
        exactly one `run` step with its assigned command.
      - NO other network access, publish, deploy, or artifact-upload steps.
      Any structural deviation (missing job, extra job, wrong trigger, write
      permission, unexpected step) → test FAIL. This test is a structural
      contract guard, not a valid YAML schema for all workflows.
   5. Run locally: `python3 scripts/check_aitp2_simplicity.py --phase s0` exits 0.
- **Verification**: local ratchet passes; test suite passes including
  `test_s0_workflow_contract.py`; its bounded structural workflow contract
  confirms the exact triggers, permissions, jobs, and commands.
- **Commit**: `ci: S0 simplicity ratchet and contract workflow`

### T5 — Acceptance Packet / S0 Acceptance Gate

- **Depends on**: T0–T4 all passing.
- **Files (create)**: `docs/superpowers/progress/<execution-date>-aitp-2-0-s0-acceptance.md`
- **Observable claim**: all PASS criteria from §9 verified; S0 Acceptance Gate
  independent review confirms no blocking findings; S0 PASS declared.
- **Main failure modes**: missing evidence; unresolved decisions; PASS claimed
  on failure.
- **Steps**:
  1. Run all commands from §7.
  2. Fill acceptance checklist from §9.1 (now includes content envelope,
      navigation, read coverage, failure recall, gate matrix, static expected-output contract fixtures,
     runtime inventory contracts).
  3. Confirm: `git diff --check` clean; remote SHA == local HEAD;
     `check_repository_authority.py` exits 0.
  4. Independent S0 Acceptance Gate review confirms no blocking findings.
  5. Declare S0 PASS.
- **Verification**: acceptance doc references exact command outputs, SHAs,
  timestamps.
- **Commit**: `docs: S0 freeze acceptance`

S1 MUST NOT begin until T0–T5 all pass S0 Acceptance Gate.

## 7. Evidence Path

| Claim | Artifact | Command | Expected |
|-------|----------|---------|----------|
| Decision register complete + authorization stubs valid | S0_DECISIONS.json + FIXTURE_PROVENANCE.md | Manual review + simple JSON validation (T1a) | exit 0, zero `user-decision-required`, U1 frozen, frozen entries authority-ref'd |
| Validator core functional | check_s0_freeze.py + test_s0_contract_freeze.py | `python3 tests/aitp2/check_s0_freeze.py --decisions-only` (T1b) | exit 0 |
| 12 command groups + 7+1 registry + 16 predicates + content envelopes + navigation + read coverage + gate matrix + CLI contracts + human decision overlay + failure recall | FREEZE.json + fixtures | `python3 tests/aitp2/check_s0_freeze.py --oracle-only` (T2) / `python3 tests/aitp2/check_s0_freeze.py` (T3+ full) | exit 0, reports all frozen contract surfaces |
| All profiles compliant (common header + additional fields, Entity kinds, SOURCE fields, body sections, route_refs, decision overlay, asset-ULID IDs) | Fixtures | `python3 -m unittest discover -s tests/aitp2 -p 'test_*.py'` | exit 0 |
| Negative structural errors distinct (canonical INDEX/forbidden_canonical_path, missing failure recall, truncated-as-exact, partial-search-as-absence, gate downgrade, unknown-stage silent no-op, inventory second-truth, bidirectional ref mismatch, draft Assessment trust mutation, run-ULID prefix) | Negative fixtures | same | exit 0, one distinct error per boundary |
| Simplicity — S0 production absence | `src/aitp/`, `pyproject.toml` | `python3 scripts/check_aitp2_simplicity.py --phase s0` | exit 0 |
| Repository authority intact | All tracked files | `python3 scripts/check_repository_authority.py` | exit 0 |
| Whitespace clean | Changed files | `git diff --check` | exit 0, no warnings |

### 7.1 Constraints

- Tests must NOT judge scientific truth, semantic relevance, or command intent.
- Negative tests use `tempfile.TemporaryDirectory`; never touch external `.aitp`.
- No network, external Git remote, or external filesystem access in any test.
- Frontmatter YAML lexical validation (duplicate keys, forbidden YAML
  syntax forms per D3/D4) uses a bounded stdlib-only test-only parser
  contract per the now-frozen D3/D4 rules (active spec §6 T1a D3/D4).
  The exact empty `[]` and `{}` sentinels are permitted; all nonempty
  flow structures (`[...]`, `{...}`) are forbidden as scalar values —
  flow-looking content must use the JSON double-quoted string form.
  D3 and D4 were resolved by the user on 2026-07-23 and are not deferrable;
  S0 validators implement the frozen rules directly.

## 8. Phase S0 Ratchet

`scripts/check_aitp2_simplicity.py` operates in `--phase s0` for S0 CI.

### 8.1 S0 Mode — Production Code Absence (HARD FAIL)

| Check | Expectation |
|-------|-------------|
| Root `pyproject.toml`, `setup.py`, `setup.cfg`, `MANIFEST.in` | Must NOT exist |
| `src/aitp/` directory or any non-historical, non-fixture `aitp/__init__.py` | Must NOT exist |
| `*.dist-info/`, `*.egg-info/`, `dist/*.whl`, `build/**/aitp/` | Must NOT exist |
| Repository-local `command_skills/` (wheel-resource scaffolding) | Must NOT exist |
| `importlib.machinery.PathFinder.find_spec("aitp", [<repo>/src, <repo>])` | Must return `None` |

Any presence → immediate FAIL. There is NO Phase 1+ alternative branch in S0 CI.
Even if the repository hypothetically satisfies all future S1 ceilings, the
ratchet fails if any production scaffold exists during S0.

The import check uses explicit repository-root paths only; it MUST NOT query or
fail on a globally installed `aitp` package outside the repository.

### 8.2 Future S1 Ceilings (Documented, Not Enforced in S0)

For reference in ratchet source and as a synthetic future-mode contract:
≤12 commands, 7+1 nodes/edges, 1 writer, ≤12K nonblank noncomment Python LOC,
≤500 LOC/file, zero `import brain` or `from brain`, all 12 wheel resources
present. These are NOT enforced in S0 CI.

## 9. Exact Acceptance Criteria

### 9.1 S0 PASS

- [ ] Authorized sanitized structural fixtures with FIXTURE_PROVENANCE.md
  recording source class, snapshot hashes, redactions, restrictions; no required
  fixture family remains in `seeding` state.
- [ ] FREEZE.json encodes 12 command groups, 7 node roles, 1 edge role, 16
  relation predicates, content envelope boundaries, minimum profile fields
  (including Entity kinds, SOURCE fields, body sections, route_refs, decision
  overlay, asset-ULID IDs), Route navigation fields, JSON envelope with reads
  object, error codes (including `forbidden_canonical_path`), workspace states,
  read coverage semantics, enter behavior with unexpanded failures, gate matrix
  with mutation taxonomy + draft Assessment, writer behavioral contract, and
  noncanonical INDEX contract. Every field has `authority_path` annotation.
  FREEZE is a reviewed oracle; the active spec text is normative and wins in
  case of conflict.
- [ ] Common header (7 fields + optional `kind`) machine-checkable.
- [ ] Every Asset kind has a scope-sensitive path profile; records match exactly
  one legitimate template.
- [ ] Content envelope boundaries respected: natural Markdown note/derivation
  Assets are not per-sentence nodes; Episodes are not transcripts; Relations
  are not containment/ordinary mention; human `promote_to_record` trigger
  requires provenance + candidate + human approval.
- [ ] Entity profile frozen with baseline kinds; new kind requires reviewed
  profile but not a new node.
- [ ] `route_refs` present on Episode and Assessment; bidirectional refs with
  Route fields verified by three machine oracles:
  1. unresolved failure Episode ↔ `known_failure_refs`; resolved ↔
     `prior_attempt_refs` + Episode `resolution_refs`.
  2. `route_effect: blocks` Assessment ↔ `blocking_assessment_refs`.
  3. `route_effect: resolves_failure` Assessment: target_ref is failure
     Episode, route sets equal, Episode `resolution_refs` includes it,
     Route moves from known to prior.
   Plus `route_effect: unblocks` removes target_ref's prior blocker from
   each Route.blocking_assessment_refs; route sets equal; both Assessments
   remain in audit history.
- [ ] Resolved failures move from `known_failure_refs` to `prior_attempt_refs`
  only via `route_effect: resolves_failure` Assessment; failures are never
  deleted; new success does not overwrite old failure.
- [ ] Decision overlay frozen for Statement(kind=decision) and
  Episode(kind=research_decision); canonical decisions require human gate;
  Agent may draft but not self-approve.
- [ ] Gate matrix floor enforced with mutation taxonomy + unclassified→human
  review default; add-only semantics for low-authority actions; draft
  Assessment must not change trust/unblock/resolve/promote.
- [ ] U1 `frozen` per user decision 2026-07-23: S0 = pure contract/
  oracle/fixture/static validation; S1 = production CLI/wheel/resources/
  legacy reader/CLI runtime acceptance.
- [ ] All Asset owner IDs use `asset-<ULID>`; `run-<ULID>` is retired.
- [ ] Route `context_refs`, `prior_attempt_refs`, `known_failure_refs`,
  `blocking_assessment_refs` are frozen and enter reports them deterministically.
- [ ] Read coverage vocabulary (exact/deferred/skipped/not_checked) enforced;
  an item whose content was actually truncated or omitted must not be marked
  `exact`; global `budget.truncated: true` can coexist with unaffected,
  fully-read items retaining `status: exact`. Absence claims require complete
  search.
- [ ] Gate matrix floor enforced; no profile/Skill version bump lowers the
  global gate.
- [ ] static expected-output contract fixtures: JSON envelope, error codes (including
  `not_available_in_stage`), workspace states.
- [ ] Ref grammar constraints verified: store-relative POSIX, no traversal,
  symlink escape rejected, pinned read via `git show`, distinct errors.
- [ ] Each S0 frozen structural invariant has at least one positive or negative
  evidence fixture; safety boundaries (traversal, legacy-write, credential
  rejection) have negative evidence; extended negative cases (canonical INDEX,
  missing failure recall, truncated-as-exact, partial-search-as-absence, gate
  downgrade, unknown-stage silent no-op, inventory second-truth) are covered.
- [ ] No legacy import, write, dual-write, or fallback in 2.0 contract surface.
- [ ] One canonical writer finish-path invariant frozen and testable per §14.0.2.
- [ ] Simplicity ratchet passes in `--phase s0` — zero production code/package.
- [ ] S0 historical protection is exactly consistent with cutover authority
  (`docs/superpowers/specs/2026-07-21-aitp-2-0-repository-authority-cutover-design.md`
  §§4.4, 5.2). Zero modifications to every protected existing file.
  **KEEP-HISTORICAL** (derived from cutover §4.4 L210–237 + §5.2 L369–399;
  no edit, delete, move, or overwrite on any file under these repo-relative
  roots):
  - `AGENTS.md`
  - `CLAUDE.md`
  - `bin/**`
  - `brain/v5/**`
  - `contracts/**`
  - `deploy/**`
  - `docs/CHARTER.md`
  - `docs/protocols/**`
  - `docs/superpowers/audits/**` (existing audit files)
  - `docs/superpowers/plans/**` except this active plan
  - `docs/superpowers/progress/**` except the future S0 acceptance doc
  - `docs/superpowers/specs/**` except the active spec
  - `hooks/**`
  - `plugins/aitp-research-protocol/scripts/**`
  - `plugins/aitp-research-protocol/skills/**`
  - `plugins/aitp-research-protocol-kimi/scripts/**`
  - `plugins/aitp-research-protocol-kimi/skills/**`
  - `research/adapters/openclaw/scripts/**`
  - `research/adapters/openclaw/plugin/**`
  - `research/knowledge-hub/**`
  - `schemas/**`
  - `scripts/split_*.py`
  - `scripts/run_v5_test_lanes.py`
  - `tests/**` (existing historical tests; only new files under
    `tests/aitp2/**` and `tests/fixtures/aitp2/**` are allowed)
  The list is exhaustive and literal — no basename-recursive matching, no
  shorthand expansion. External stores/repos and `.aitp` directories are
  never accessed.

- [ ] **Fail-closed baseline rule**: After this reviewed Phase 1 plan commit,
  the set of S0 changed/created paths relative to that commit MUST be a
  subset of the Allowed new/modify S0 paths below. Every tracked path
  existing at the plan commit outside that allowlist must remain
  byte-identical. Under `tests/**`, existing files are protected; only new
  files under `tests/aitp2/**` and `tests/fixtures/aitp2/**` are allowed.
  The active spec and plan are not authorized for silent S0 edits; any
  later normative change requires a separate reviewed amendment before S0
  continues. The authority guard and S0 simplicity ratchet must compare
  against the reviewed Phase 1 plan commit and fail on any path outside the
  exact S0 allowlist or any modified pre-existing historical file under
  protected roots.

  **Allowed new/modify S0 paths**: S0 may create or modify files only under:
  - `tests/aitp2/**` — validators, test files, synthetic test fixtures
  - `tests/fixtures/aitp2/**` — authorized sanitized structural fixtures,
    FREEZE.json, S0_DECISIONS.json, FIXTURE_PROVENANCE.md, fixture families
    (quantum-chaos/, nio/, shared-paper/, knowledge-card/, skill/,
    navigation/, content-envelope/, read-coverage/, gate-matrix/,
    cli-contract/, runtime-inventory/, negative/)
  - `scripts/check_aitp2_simplicity.py` — simplicity ratchet (single file)
  - `.github/workflows/aitp2-s0-contract.yml` — S0 CI workflow (single file)
  - `docs/superpowers/progress/<date>-aitp-2-0-s0-acceptance.md` — acceptance
    doc (newly created only; may not modify pre-existing progress files)
  These allowed paths are precise exceptions to baseline protection, not
  exceptions that permit modifying pre-existing historical files.
  `docs/superpowers/progress/<date>-aitp-2-0-s0-acceptance.md` may be newly
  created only; current plan/spec changes happen now in Phase 1, not during
  S0. Any S0-created file outside these allowed paths → S0 FAIL. The T1a
  decision register and provenance stubs (allowed before Gate B) live under
  `tests/fixtures/aitp2/`; custom validators, fixture corpus, and production
  artifacts are forbidden before Gate B per §10.2. U1 and Gate B ordering
  unchanged.
- [ ] Zero unresolved `user-decision-required` in decision register.
- [ ] Local HEAD equals remote HEAD for this branch.
- [ ] `python3 scripts/check_repository_authority.py` exits 0.
- [ ] Separate S0 CI workflow passes.
- [ ] Independent S0 Acceptance Gate review confirms no blocking findings.
- [ ] Python file/module inventory is determined by implementation evidence only;
  no normative assertions about module count, class/function names, parser
  library, dispatch, or helper layering appear in fixtures or validators.
- [ ] S0 static validators verify expected-output fixtures (FREEZE.json and
  fixture corpus) and do not lock internal Python imports; real CLI subprocess,
  filesystem, Git, and stdout JSON acceptance belongs to S1 per U1 resolution.

### 9.2 S0 FAIL

Any one of: CLI scaffold/parser/writer exists; any repository-local production
artifact listed in §8.1 exists; installed Skill content committed (not fixture
exemplar); real `.aitp` created/modified; external store accessed; v5 record
mutated; migration/dual-write/coercion exists; semantic validator judging
physics truth exists; MCP/hook/compiler/database/index/scanner exists; fixture
without provenance; private credential/path committed; implementation-defined
contract asserted as normative; normative assertion of Python module count or
class/function names; canonical `topics/<id>/INDEX.md` created; gate matrix
floor violated by profile/Skill version bump; expected-output fixture
missing or does not conform to frozen contracts (real black-box CLI acceptance
belongs to S1).

## 10. Review and Commit Strategy

### 10.1 Historical Phase 1 Plan Commit

- **Exact change**: four paths — the active spec (amended), this plan (amended),
  `.gitignore`, and `.ignore`. The `.gitignore` adds `.slim/deepwork/`
  ignore; the `.ignore` adds deepwork read allowlist. These are audited
  orchestration-support changes, not product authority.
- **Commit message**: `docs: freeze AITP 2.0 store and CLI behavior contracts`
- **Allowlist**: exactly the four paths above. Deepwork content is ignored
  and not committed.
- **Pre-commit**: `git status --short --untracked-files=all` shows only the
  four allowlisted paths as modified/untracked; `git diff --check` no
  whitespace errors; `python3 scripts/check_repository_authority.py` exits 0.
- **After push**: verify remote SHA matches local HEAD. Then STOP. No further
  commits, no merge, no S0 execution until Council + Oracle Gate A pass and
  future T0.

### 10.2 Historical Council + Oracle Gate A

This amendment requires:

- **Council review**: the Council reviews the planning approach — specifically
  that this amendment correctly freezes observable behavior without freezing
  Python code shape, and that the extended contract surface is coherent.
- **Oracle Gate A** (renewed plan-only Gate 3): Oracle reviews this amended
  plan only. It does NOT resolve future fixture authorization, implementation
  choices, D1–D9 decisions, or S0 acceptance. Oracle Gate A confirms:
  - Amended plan consistency with the amended active spec and authoritative
    references.
  - No implementation coupling, semantic validators, or hidden infrastructure.
  - Fixture authorization/provenance/redaction rules sufficient.
  - All new frozen contract surfaces (content envelopes, navigation, read
    coverage, failure recall, gate matrix, static expected-output contract fixtures, runtime inventory,
    human decision overlay, Entity profile, route_refs, asset-ULID IDs,
    CANDIDATE universal model, reads JSON object) are correctly specified
    in both the active spec and this plan.
  - Historical Gate A confirmed U1 and D7 were `frozen` while D1–D6 and
    D8–D9 were exposed as `user-decision-required`. This later T1a authority
    amendment has resolved every D1–D9 entry; §3.1 reflects the current
    `frozen` status. Resolving them was the user's T1a authority, not Gate A's.
  - Plan does not silently modify the active spec or audit disposition.
  - Python file/module inventory is not normatively asserted. S0 expected-
    output fixtures are structural oracles (FREEZE.json), not actual CLI
    output — real CLI subprocess/filesystem/Git/stdout acceptance belongs
    to S1 per U1 resolution.

For the historical Phase 1 amendment, only after both Council and Oracle Gate A
passed could the exact four-path commit and push proceed. After the current
two-path authority amendment is separately reviewed and committed, S0 follows:
1. T1a creates `S0_DECISIONS.json` (copying frozen D1–D9 decisions; U1 frozen traceability-only)
   and pre-read `FIXTURE_PROVENANCE.md` — these are the only S0 artifacts
   allowed before Gate B.
2. Oracle Gate B reviews those T1a artifacts (not the spec amendment).
3. Only after Gate B passes may T1b (validator skeleton), custom validators,
   fixture corpus, or production package/CLI be created.

### 10.3 Future S0 Execution Commits

S0 execution (when authorized) follows T0–T5:
1. T1a: `docs: establish S0 decisions and authorization record`
2. Oracle Gate B review
3. T1b: `test: establish S0 validator core`
4. T2: `test: reviewed FREEZE.json oracle with authority anchors and synthetic negative suite`
5. T3: `test: authorized sanitized structural fixtures with provenance`
6. T4: `ci: S0 simplicity ratchet and contract workflow`
7. T5: `docs: S0 freeze acceptance`

### 10.4 Gate Naming

- **Council review (Phase 1)**: reviews the planning approach (behavior-not-
  code-shape coherence) before Oracle Gate A. Completed and passed for the
  Phase 1 four-path commit.
- **Council review (current)**: reviews the decision coherence and spec
  consistency of the two-path T1a authority amendment. Pending.
- **Oracle Gate A (completed, historical)**: reviewed the Phase 1 amended
  plan only (plan-only, before the four-path commit). Renewed from the
  original Oracle Gate 3 (renamed Gate A) to reflect the Phase 1 scope.
  Gate A passed; commit `7de57f34` reflects the reviewed state.
- **Independent Oracle review (current)**: reviews the exact two tracked
  paths (active spec + S0 plan) of the T1a authority amendment. This is a
  focused review distinct from historical Gate A — it does not re-open
  Gate A's scope and is not a new named gate. Pending.
- **Oracle Gate B**: reviews T1a artifacts (decisions, authorization stubs)
  before any custom validator or fixture corpus is created; the T1a decision
  register and pre-read provenance stubs are the only allowed exceptions.
  Must pass before T1b begins. Gate B reviews artifacts only, not the spec
  amendment. Gate B does NOT say validator exists before gates.
- **S0 Acceptance Gate**: final S0 execution gate (independent review of
  T1a + Gate B + T1b + T2 + T3 + T4 + T5).

## 11. Risks, Stop Conditions, and Explicit Stop Before S1

### 11.1 Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Insufficient authorized material | S0 BLOCKED; `seeding` | Obtain additional authorization or amend vertical requirements via governance |
| U1 stage-split boundary drift | S0/S1 scope confused mid-execution; production artifacts leak into S0 | U1 is frozen in this amendment (§3.1, active spec §17 S0/S1); any change requires a new reviewed amendment |
| Active spec genuinely ambiguous on unregistered point | S0 BLOCKED | Separate spec amendment + disposition update before resuming |
| Production artifact accidentally scaffolded in S0 | Ratchet FAIL | Local verification before commit + required S0 CI blocks |
| Plan confused with execution | Premature S0 PASS | Frontmatter states "proposed plan-only amendment"; no fixture/validator created |
| YAML lexical policy (D3/D4) — resolved | D3/D4 are `frozen` per T1a authority amendment 2026-07-23 (active spec §6 T1a D3/D4); the bounded two-form scalar grammar is the sole normative rule | No further risk — resolution is complete; any future change requires a new reviewed amendment |
| Council + Oracle Gate A before historical Phase 1 commit — satisfied | Historical Phase 1 four-path commit `7de57f34` passed both Council and Oracle Gate A review; no pending risk | No longer a risk — historical Gate A is complete and recorded in §10.2 |
| Two-path authority amendment requires focused Council + independent Oracle before commit | Amendment lacks authorization; may need rollback | The current two-path amendment (active spec + S0 plan only) requires focused Council review (decision coherence/spec consistency) + independent Oracle review (exact two tracked paths) before commit. Neither may be skipped or deferred. |
| Python code shape confused with behavior contract | Tests assert internal module names/class signatures instead of observable CLI/filesystem/Git behavior | Contract tests prioritize black-box; Python file/module inventory is implementation evidence only |

### 11.2 Stop Conditions

STOP and do NOT proceed to S1 if:

- Any `user-decision-required` remains unresolved.
- FIXTURE_PROVENANCE.md lacks explicit authorization for any real source used.
- Any committed file contains a machine path, credential, hostname, private URL,
  or restricted binary byte.
- FREEZE.json disagrees with active spec (active spec text is normative; FREEZE
  is a reviewed oracle — in conflict, the spec wins and FREEZE must be
  re-reviewed).
- Simplicity ratchet reports FAIL in `--phase s0`.
- `check_repository_authority.py` reports FAIL.
- S0 Acceptance Gate review reports any blocking finding.
- Any repository-local production artifact listed in §8.1 exists.
- Any v5 canonical record is mutated.
- S0 expected-output fixtures are confused with or tested as actual CLI behavior
  (those belong to S1).

### 11.3 Explicit Stop Before S1

S0 PASS is a hard gate. S1 CLI implementation MUST NOT begin until S0 achieves
PASS per §9.1, all S0 execution commits are on the dev branch, and S0 Acceptance
Gate is recorded. No conditional/parallel S0/S1 work, and no S1 feature may be
"mostly done" before S0 closes.
