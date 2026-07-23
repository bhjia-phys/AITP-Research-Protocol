# AITP 2.0 S0 Contract and Fixture Freeze Implementation Plan

> **Current amendment status (2026-07-24)**: exact two-tracked-path authority
> amendment consisting only of active spec + S0 plan; records user-approved
> compact-checkpoint/derived-failure UX contract and natural T2 module
> organization. T1a, Oracle Gate B, and T1b are historical completed
> prerequisites and are not repeated. Current uncommitted FREEZE/validator
> work is superseded and must be regenerated after this amendment is reviewed,
> committed, and pushed. Focused Council + independent Oracle review of exact
> two docs required before commit. After push, rerun clean-tree/authority
> preflight and resume T2 regeneration.
>
> **Amendment scope**: this amendment updates the active spec
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
> **AUTHORITY_COMMIT**: The exact pushed commit of this two-doc authority
> amendment, obtained after push via `git rev-parse HEAD`. This SHA is the
> sole baseline for T2 regeneration, authority_path anchors, protected-path
> diff, simplicity ratchet, and S0 Acceptance. Historical SHAs
> (`389b...`, `7de57f34`, the cutover baseline `eec20f6`) are lineage and
> history references only — they are not the current S0 change baseline.
>
> **Current execution gating**:
> - After this amendment is reviewed, committed, and pushed, S0 execution
>   follows a strict sequence:
>   1. Verify local HEAD == remote branch HEAD; record AUTHORITY_COMMIT.
>   2. Verify that the authority commit changes exactly these two tracked docs.
>   3. Rerun T0 clean-tree/remote/guard preflight against AUTHORITY_COMMIT.
>   4. Regenerate FREEZE.json and T2 validator modules from the amended active
>      spec (authority_path anchors use AUTHORITY_COMMIT), execute the required
>      oracle/schema/vector/negative evidence, and achieve reviewed T2 PASS.
>      All stale prior digests are superseded.
>   5. Only after T2 PASS, continue with T3+ (fixture authorization/provenance,
>      structural fixtures, simplicity ratchet, CI workflow, acceptance).
> - T1a (decision register, provenance stubs), Oracle Gate B, and T1b
>   (validator skeleton) are historical completed prerequisites and are NOT
>   repeated.
> - U1 is `frozen`: S0 = pure contract/oracle/
>   fixture/static test-only validation; production CLI, wheel/resources,
>   legacy reader, and CLI subprocess/runtime acceptance belong to S1.
> - S1 CLI implementation MUST NOT begin before S0 execution achieves S0 PASS.
> - Once reviewed, this document is the sole normative S0 execution plan.
>   Previous v5/pre-cutover implementation sequences are historical and
>   non-normative.
>
> **Review strategy**: Council reviews the decision coherence and spec
> consistency of this two-path amendment. Independent Oracle reviews the
> exact same two tracked paths. Both must pass before commit. The Phase 1
> four-path commit (`7de57f34`) is historical and remains accurate — it
> does not describe the current commit allowlist.

> **UX behavior authority amendment (2026-07-24, user-approved)**: The user
> reviewed and approved the interaction-behavior rules now encoded in the
> active spec: compact default `aitp checkpoint "<summary>"` (spec §9.1),
> Episode author/attention gating (spec §14.0.1), derived failure/attempt/
> blocking view replacing synchronized Route failure-ref fields (spec §6.0.3;
> Route has 9 additional profile fields; Episode drops `resolution_refs`),
> rebuilt gate matrix with author/actor/scope/outcome rows and explicit
> decision-overlay and reviewed-Assessment trust-effect rows (spec §14.0.1),
> persistence/presentation boundary (spec §14.0.3), and the anti-complexity
> guard (spec §15.1). Every affected surface of this plan is updated in place
> below. The **current uncommitted `FREEZE.json` and the in-progress T2
> validators are superseded by this amendment** and must be regenerated
> against the amended active spec before T2 acceptance; no stale fixed FREEZE
> digest or `authority_commit` may be committed in docs or oracle files. The
> natural implementation amendment (2026-07-24) in T2 — its functional
> responsibilities, stdlib/no-cycle and behavioral acceptance constraints are
> frozen; concrete helper names, file count, and import edges are
> implementation evidence.

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
commit message: `docs: amend S0 checkpoint and derived failure contracts`.

### 1.2 Non-Goals (Current Amendment)

- This authority commit stages only the two tracked docs (active spec + S0
  plan). Existing uncommitted FREEZE.json, T2 validators, and fixture work
  are superseded by this amendment; they remain unstaged and are regenerated
  afterward.
- No `src/aitp/`, `pyproject.toml`, `__init__.py`, or Python package.
- No wheel, package resources, or `importlib.resources` metadata.
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
- **TOPIC/Route navigation**: homomorphic human/Agent spine with 9 frozen
  Route fields and the derived failure view (§5.1, §6.0.3).
- **read coverage**: exact/deferred/skipped/not_checked vocabulary with
  budget and completeness reporting (§7.5).
- **derived failure/attempt/blocking view — machine oracles** (per active
  spec §6.0.3, superseding the former stored-field bidirectional rules):
  1. `route_episode_refs` = all route-scoped Episodes referencing Route R;
     `prior_attempt_refs` = those Episodes sorted `(created_at, id)`.
  2. `known_failure_refs` = failure/inconclusive members not resolved by a
     valid reviewed `route_effect: resolves_failure` Assessment;
     `resolved_failure_refs` = those so resolved. No Route or Episode
     mutation occurs on resolution.
  3. `blocking_assessment_refs` = valid reviewed `route_effect: blocks`
     Assessments minus targets of valid reviewed `route_effect: unblocks`
     Assessments (route sets equal; both Assessments remain in canonical/Git
     audit history).
   Plus: bad/malformed records, inconsistent Route refs, budget/truncation,
   or incomplete coverage yield an `incomplete` derived result and no
   absence assertion; the runtime INDEX is cache only and falls back to the
   canonical scan on commit/coverage mismatch; `enter` shows the derived
   view with provenance; new success does not overwrite old failure.
- **compact checkpoint contract** (active spec §9.1): `aitp checkpoint
  "<summary>"` default compact canonical Episode; bare invocation shows
  usage; `--full` rich path; `--enrich` optional; deterministic scope
  fallback with `--topic` lawful only when no Route context exists; compact
  Episode is complete canonical-format payload, becomes
  canonical durable memory only after lawful writer commit — before commit
  it is a pending CANDIDATE candidate, never a stub/awaiting-enrich - and
  the Agent route-failure return uses envelope `status: blocked` + frozen
  `approval_required` + `result.candidate_state: draft`, not `pending_review`.
- **Episode author/attention gating** (active spec §14.0.1): human-authored
  low-authority Episodes (any scope) and Agent-authored topic/shared or
  route non-failure Episodes are deterministic add-only — with
  decision-overlay records (Episode `kind: research_decision`, Statement
  `kind: decision`) explicitly excluded from every add-only row and governed
  only by the explicit decision-overlay row (Human review, Gate ID
  `human_review`) regardless of author/scope/outcome; Agent-authored
  route-scoped failure/inconclusive Episodes persist to an on-disk draft
  CANDIDATE before command return and require batched exact-diff human
  review of the final candidate revision before canonical commit.
- **persistence and presentation boundary** (active spec §14.0.3): pending
  candidates are on-disk, recoverable through existing workspace/admin
  recovery, reported separately by enter/closeout, and never canonical
  failure truth until approved/committed; routine human presentation folds
  candidate hashes/gate IDs/approval-binding internals while exact diff,
  exact paths, and the validation summary remain visible.
- **gate matrix**: action→minimum gate table frozen (§14.0.1; action classes
  may overlap, and each operation contributes the sorted unique union of all
  applicable gate floors, with a fail-closed default; tests verify effective
  action→gate behavior and legal Gate IDs, not row count).
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
| `checkpoint` | durable-moment triggers, compact default Episode (`<summary>`), bare-invocation usage, `--full`/`--enrich`, deterministic scope fallback, author/scope/outcome gating |
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
Exact additional-field counts per the amended active spec §6.0.2: Route 9
(`prior_attempt_refs`, `known_failure_refs`, `blocking_assessment_refs` removed —
derived per §6.0.3), Episode 4 additional fields plus kind (5 profile fields including kind, `resolution_refs` removed), Assessment 12.

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
                                    SOURCE/derived failure view/next_action
                                    spine (§5.1, §6.0.3)
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
| Route record carrying removed `prior_attempt_refs` / `known_failure_refs` / `blocking_assessment_refs` fields | Rejected as `profile_mismatch` under D9 closed field set; failure sets are derived (§6.0.3), never stored |
| Episode record carrying removed `resolution_refs` | Rejected as `profile_mismatch`; resolution is derived from reviewed `resolves_failure` Assessments |
| Derived scan with malformed record, inconsistent Route ref, or truncated coverage | Derived result reported `incomplete`; no absence assertion permitted |
| Runtime INDEX commit/coverage mismatch treated as authority | INDEX is cache only; canonical scan fallback required (§6.0.3) |
| Pending Agent route-failure candidate treated as canonical failure truth | Pending candidates are excluded from the derived view until approved/committed (§14.0.3) |
| Agent route-failure checkpoint returning without on-disk draft candidate | Persistence-before-return violation (§14.0.1/§14.0.3) |
| Bare `aitp checkpoint` silently launching the rich full-record flow | Must print usage and exit (§9.1) |
| Compact Episode frontmatter carries `record_form`, draft/status, or awaiting-enrich lifecycle fields | The Episode payload is complete canonical-format content; lawful CANDIDATE state `draft`/`review_ready` exists only in CANDIDATE.json, never Episode frontmatter (§9.1, §15.1) |
| Truncated file marked `exact` when itself truncated | Truncated individual item ≠ exact per §7.5; global truncation does not affect unrelated fully-read items |
| Partial search reported as absence | Absence claim requires complete search |
| Profile/Skill version bump lowers gate | Gate matrix floor cannot be downgraded |
| Unknown stage returns silent no-op | Must return `not_available_in_stage` |
| Noncanonical INDEX treated as canonical truth | INDEX is generated, canonical is authoritative |
| `forbidden_canonical_path` not raised for path profile violation | Must reject record at wrong kind path |
| Derived-view oracle violation per §6.0.3 | Resolved failure must leave `known_failure_refs` only via a valid reviewed `resolves_failure` Assessment; `blocks`/`unblocks` derivations follow spec §6.0.2/§6.0.3 |
| Draft Assessment mutates trust/unblocks/resolves | `review_state:draft` must not affect derived states |
| `run-ULID` Asset ID prefix used | All Asset IDs must use `asset-ULID` |
| Decision overlay missing `decided_by` or self-approved by Agent | Canonical decisions require human gate |
| Statement `kind: decision` or Episode `kind: research_decision` staged through deterministic add-only | Decision-overlay records are excluded from every low-authority Episode add-only row; they must carry the exact §6.0.2 decision overlay and pass the explicit decision-overlay matrix row (Human review, Gate ID `human_review`) regardless of author/scope/outcome (§14.0.1) |
| Agent create operation with `created_by: human:*` | Per-operation actor binding rejects `created_by` ≠ operation.actor — `validation_failed` (`check_id: actor_mismatch`) (§D2a) |
| Update operation rewrites original `created_by` to the current operation actor | Writer rejects the mutation; update/delete preserve original `created_by` while the current operation actor determines the gate (§D2a) |
| Operation actor unavailable at the trusted boundary | The operation is classified `fail_closed_agent`; create still requires `created_by` == operation.actor, while update/delete preserve original `created_by` (§D2a) |
| Approval copied from another workspace with otherwise identical revision/tree/paths/hashes/gates | Reject: `approval_binding.protocol` and `approval_binding.workspace_id` are independently bound identity fields (§5.2.2) |

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

### T0 — Post-Amendment Preflight (No Commit)

- **Depends on**: pushed AUTHORITY_COMMIT (the exact SHA of this two-doc
  authority amendment, obtained after push via `git rev-parse HEAD`).
- **Files**: none created.
- **Observable claim**: S0 execution HEAD == AUTHORITY_COMMIT; local == remote;
  tree clean; `check_repository_authority.py` passes. Historical SHAs
  (`389b...`, `7de57f34`, `eec20f6`) are lineage/history checks only — they
  are not the current S0 change baseline. `origin/main` drift from the
  recorded cutover baseline `eec20f6f...` is recorded as metadata in the
  current T2 regeneration/acceptance evidence, not in historical T1a.
- **Main failure modes**: wrong base (HEAD ≠ AUTHORITY_COMMIT); remote
  diverged; dirty tree; authority commit changes more or fewer than the exact
  two tracked docs; baseline drifted without impact review.
- **Steps**:
   1. `git fetch origin`
   2. Verify local HEAD == remote branch HEAD == recorded AUTHORITY_COMMIT:
      `git rev-parse HEAD` equals the authority SHA recorded at push.
   3. Verify the authority commit changes exactly the two tracked docs
      (active spec + S0 plan); no other path is modified.
   4. `git status --porcelain` must be empty.
   5. `python3 scripts/check_repository_authority.py` exits 0.
   6. Verify current HEAD is a descendant of
      `389b3149ef9f6dd054ed82e0e7821c2868a4972e` (historical lineage check):
      `git merge-base --is-ancestor 389b3149ef9f6dd054ed82e0e7821c2868a4972e HEAD`.
   7. Compare `origin/main` SHA against cutover baseline
      `eec20f6faeb089ec2fcdc982ad65adce242a21a9`. If different,
      record the discrepancy as evidence in T2 regeneration/acceptance
      (not in T1a). Perform an authority impact review before proceeding;
      do not auto-merge, rebase, or silently accept.
- **Verification**: all `git` commands pass; guard exits 0; AUTHORITY_COMMIT
  confirmed as exactly two-tracked-doc SHA; baseline impact acknowledged.

### T1a — Authority Interpretation + Blocking Decisions + Authorization Record (Historical Completed)

Retained as historical evidence only, not re-executed; current execution resumes T2 regeneration after AUTHORITY_COMMIT/T0.

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

### T1b — Validator Core And Synthetic Self-Tests (Historical Completed)

Retained as historical evidence only, not re-executed; current execution resumes T2 regeneration after AUTHORITY_COMMIT/T0.

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

### T2 — Reviewed FREEZE.json Oracle + Validator Integration + Synthetic Negatives

> **Modularity amendment (2026-07-23)**: Two implementation attempts triggered the
> pre-existing Council STOP condition: the validator reached 490 NBNC while
> required closed schema validation, executable D3/D4 vectors, full 19/171
> error-priority evidence, and an independent full-mode family guard remained
> absent or presented as descriptive notes rather than executed machine checks. A
> third monolithic dense patch is prohibited. This amendment authorizes a bounded
> modular split by functional responsibility and observable security constraints.
> No new gate or stage is created; T2 acceptance criteria are unchanged.
>
> **Natural implementation amendment (2026-07-24)**: This later amendment applies
> focused T2 plan-only authority changes to remove artificial hard requirements on
> exact module/file count and per-file line caps, while keeping every substantive
> functional requirement unchanged:
> - Behavior/acceptance gates and T2/T3/source boundaries are unchanged.
> - Python module inventory and line counts are implementation evidence, not
>   normative behavior.
> - Implementation may split cohesive stdlib-only test-support modules by
>   responsibility under `tests/aitp2/`.
> - No dense/generated/eval/dynamic-import tricks and no cyclic local imports.
> - Avoid both monolithic piling and gratuitous fragmentation.
>
> **UX behavior supersession (2026-07-24, user-approved)**: The uncommitted
> `tests/fixtures/aitp2/FREEZE.json` and the in-progress T2 validator modules
> encode the superseded stored failure-ref contract (12-field Route,
> `resolution_refs`, bidirectional sync, old checkpoint flow, old gate rows).
> They are superseded by the UX behavior authority amendment and MUST be
> regenerated against the amended active spec before T2 acceptance: Route 9
> profile fields, Episode 4 additional fields plus kind (5 profile fields including kind) with the compact canonical body
> minimum, §6.0.3 derived-view oracles, the compact checkpoint contract, the
> rebuilt gate matrix with author/actor/scope/outcome Episode rows and the
> explicit decision-overlay row, and the
> §14.0.3 persistence/presentation boundary. No stale fixed FREEZE digest,
> reviewed contract digest, or `authority_commit` may be committed in docs or
> oracle files; digests and authority anchors are regenerated from the amended
> authority commit at T2 time. The T2 natural implementation (2026-07-24)
> freezes functional responsibilities, stdlib/no-cycle constraints, and
> security/behavioral acceptance; concrete helper names, file count, and
> import edges are implementation evidence.

- **Depends on**: T0 PASS + historical T1b PASS (T0 confirmed pushed
  AUTHORITY_COMMIT and clean tree; T1b `--decisions-only` pass confirmed,
  no `user-decision-required` entries remain). T2 uses the recorded
  AUTHORITY_COMMIT as its authority anchor/baseline input.
- **Files (create/modify)** — CURRENT INFORMATIVE implementation map.
  Responsibilities and behaviors listed below are normative; helper module
  split, module names, exact file count, and import edges are implementation
  evidence and may change without authority amendment provided behavior,
  scope, and security constraints are preserved. The list below describes
  the current expected implementation:
  1. Create: `tests/fixtures/aitp2/FREEZE.json` — human-reviewed typed oracle
     only; no duplicated prose, no implementation code. Every atomic claim and
     synthetic vector carries `authority_document` + `authority_path`
     (`<full-object-id>:§section`) where the commit component MUST equal
     FREEZE's top-level `authority_commit` exactly (full resolved object ID,
     no abbreviations, no older/different commits); and applicable
     `decision_refs`. Exact Asset kind registry count is 17 (excludes retired
     `patch` per active spec §5 lines 610–628; spec wins, no spec amendment).
     Closed top-level schema; unknown keys rejected.
  2. Modify: `tests/aitp2/check_s0_freeze.py` — CLI entry point. Contains CLI
     argument parsing, mode dispatch (`--decisions-only` /
     `--oracle-only` / default full), unchanged T1b decisions validation, file
     I/O, deterministic JSON error envelope assembly, primary-error selection
     via frozen priority ordering, orchestration of oracle/full phases, and
     default/full entry that runs decisions + oracle then fails closed with
     `not_available_in_stage` (exact T3 fixture evidence absent). Cohesive,
     readable, stdlib-only, bounded by responsibility.
  3. Create: `tests/aitp2/s0_oracle_schema.py` — closed typed FREEZE schema
     validation and registry/claim resolution. Contains POSIX path validation,
     full local Git object-id validation (no fixed hex length, no network),
     committed document loading via local Git object commands followed by
     deterministic section-heading resolution, decision-register resolution
     against the loaded D1–D9/U1 set, exact typed registries (12 commands,
     7+1 roles, 16 predicates, 19 ordered errors, 7 workspace states, 10
     decision IDs, 12 T3 fixture families, 17 Asset kinds with profile→
     canonical-path mappings), machine-valued typed claims with
     authority-document + anchor validation (commit equality enforced, section
     heading verified), required synthetic vector key presence, and full-mode
     completed local provenance checks.
  4. Create: `tests/aitp2/s0_oracle_contracts.py` — pure recursive closed-shape
     engine, field-descriptor grammar, declarative contract/profile shapes,
     reviewed contract digests, structural/cross-contract checks. No I/O, Git,
     provenance parsing, decision loading, CLI, or vector execution.
  5. Create: `tests/aitp2/s0_oracle_vectors.py` — executable synthetic vector
     evaluators. Retains executable synthetic semantics. Contains bounded
     stdlib-only D3/D4 frontmatter
     scalar parser per frozen two-form grammar (plain positional restrictions,
     JSON double-quoted with post-decode newline/control rejection, exact
      `[]`/`{}` sentinels, forbidden YAML forms); 19 singleton + 171 pairwise
      error-priority execution with independent expected-primary verification;
      candidate digest/check-id/integrity/all-pass/one-fail execution; legal
      gate-ID validation; derived failure/attempt/blocking view oracle
      execution (§6.0.3: route_episode/prior_attempt/known_failure/
      resolved_failure/blocking_assessment derivation, incomplete-result
      no-absence rule, INDEX cache-only fallback); compact checkpoint contract
      vectors (§9.1: bare-invocation usage, defaults, mutual exclusion,
      deterministic scope fallback, compact completeness); Episode
        author/scope/outcome gate vectors (§14.0.1: per-operation actor/
        assurance classification, create equality, update/delete preservation,
        mixed-actor gate union) and
        enter/closeout pending-candidate
       + derived-coverage vectors (§14.0.1/§14.0.3); read budget/
      truncation/item-local exactness/mandatory overflow vectors; D8 reorder
      invariance; frontmatter-only boundary; and authority-backed workspace-
      state validation.
  6. Create: `tests/aitp2/test_s0_negative_contracts.py` — real-subprocess /
     `tempfile.TemporaryDirectory` adversarial evidence only. Functional/
     adversarial coverage remains mandatory for every declared contract
     surface. Module inventory and line counts are reported as implementation
     evidence, not pass/fail behavior.
  7. Modify: `tests/aitp2/test_s0_contract_freeze.py` — preserve existing
     behavioral tests and assertions from T1b. Only behavior-/security-relevant
     expectations (stdlib-only, no network, no aitp, no external `.aitp`)
     remain normative. Import topology and test count are implementation
     evidence; tests must not inspect module names, import topology, or fixed
     test count. No dynamic import, subprocess, or eval tricks.
  8. **No other file outside this plan's scope is created or modified.**
     Existing decisions JSON, provenance stubs, spec, plan (except this T2
     section), and authority guard unchanged.

- **Module rules (observable/security constraints only — not normative shape)**:
  - Stdlib-only for test-support modules; no `aitp`, third-party, PyYAML,
    network, external `.aitp`, remote Git, or cyclic imports between modules.
  - No dynamic import, eval, or subprocess dispatch tricks to bypass
    observability.
  - Modules are cohesive, readable, bounded by responsibility, and reviewed
    for unnecessary duplication or complexity. Module inventory, names,
    import edges, and line counts are implementation evidence, not pass/fail
    behavior.
  - Path scope is confined to `tests/aitp2/**`, `tests/fixtures/aitp2/**`,
    the named simplicity script path (`scripts/check_aitp2_simplicity.py`),
    the S0 CI workflow path (`.github/workflows/aitp2-s0-contract.yml`),
    and the S0 acceptance doc path. No production/`src/` changes are
    authorized.
  - **Concrete closed typed payloads**: `contract_present`, description-only /
    note-only placeholders, opaque unchecked blobs, and key-presence-only
    validation are prohibited. Every declared contract surface must carry
    machine-valued, closed typed payloads with explicit evaluator IDs for at
    least: common header fields + kind applicability; per-profile required/
    optional fields, enums, conditionals, body sections; all 17 Asset
    kind→profile→canonical-path mappings; Route navigation fields (9) and the
    §6.0.3 derived view; ref
    grammar/selectors/error mapping; JSON envelope/read/search/budget schemas;
    complete action→gate behavior (classes may overlap, sorted unique union per operation)/legal gate IDs/fail-closed default; CANDIDATE/writer fields, framing,
    integrity, approval binding; derived failure/attempt/blocking view and
    unblocks rules; compact checkpoint contract; pending-candidate
    persistence/presentation boundary; and
    noncanonical INDEX required fields + forbidden canonical path. Every
    declared surface must have an adversarial mutation test that causes
    structured rejection (not traceback or silent pass).
  - **Authority commit equality**: Every atomic claim and synthetic vector
    `authority_path` commit component MUST equal FREEZE's top-level
    `authority_commit` exactly (full resolved object ID, no abbreviations, no
    older/different commits). The validator loads the corresponding committed
    document path via local Git (`git cat-file`) and deterministically
    verifies the section heading exists. Abbreviated commits, older/different
    full commits, missing/fake sections, unknown authority documents, and
    traversal decision-register paths all fail closed with structured errors.
  - No-argument invocation of `check_s0_freeze.py` is default/full mode: it
    runs decisions validation, loads and validates FREEZE.json, executes all
    oracle schema + vector checks, then requires all 12 hard-coded T3 fixture
    family directories present/nonempty with completed local provenance. At T2
    this fails closed with primary error `not_available_in_stage` and lists
    every missing/empty family. The existing T1b `test_no_mode` test in
    `test_s0_contract_freeze.py` remains unchanged and compatible.
  - Full mode uses an implementation-held exact 12-family set (independent of
    mutable FREEZE.json) and verifies that FREEZE declares the identical set;
    mutation/removal of FREEZE `required_families` fails oracle validation.
    No missing, empty, or partial skip-as-pass.
  - T2 no-source boundary remains absolute: no source reads, no snapshot
    hashes, no fixture byte selection or copying. T3 remains blocked until T2
    passes and is committed.

- **Observable claim**:
  - FREEZE.json encodes the complete frozen contract surface with
    `authority_document` + `authority_path` (`<full-object-id>:§section`)
    annotations referencing the active spec and decision register. The commit
    component of every `authority_path` equals FREEZE's top-level
    `authority_commit` exactly; no abbreviated, older, or different commits.
    Every atomic claim resolves its authority anchor by loading the committed
    document via local Git and verifying the section heading exists. The
    frozen surface includes: 12 command groups, 7+1 node/edge roles, 16
    predicates, common header + kind, 17 Asset kind→profile→canonical-path
    mappings (patch retired), ref grammar, Relation contract, store/Git
     ownership, content envelope boundaries (§6.0.1), minimum profile fields
     (§6.0.2), Route navigation fields (§5.1), derived failure/attempt/
     blocking view (§6.0.3), compact checkpoint contract (§9.1), JSON envelope
     (§4.1.1), error
     codes (§7.3), workspace states (§7.4), read coverage semantics (§7.5),
     enter behavior (§7.6), Episode author/attention gating and gate matrix
     (§14.0.1), writer behavioral contract
     (§14.0.2), persistence and presentation boundary (§14.0.3), and
     noncanonical INDEX contract (§5). Every declared contract
     surface carries machine-valued typed payloads with explicit evaluator
     IDs — no `contract_present` or description-only placeholders.
   - `check_s0_freeze.py --oracle-only` validates FREEZE.json closed schema
     correctness, all exact registries, typed claims with resolved authority
     anchors (commit equality enforced, section headings verified) and decision
     refs, executes all synthetic vectors (D3/D4 scalars, 19+171 error
     priorities, candidate digest, gates, derived failure view, compact
     checkpoint, pending-candidate boundary, budget/truncation,
     D8 reorder, frontmatter-only, workspace states), and reports
    `real_fixture_coverage: not_claimed`. It does NOT require real fixture
    families to exist — explicitly reports diagnostic text `oracle-only: no
    real fixture coverage claimed.` Empty fixture directories do NOT cause
    PASS; they are acknowledged as absent.
  - Negative suite (`test_s0_negative_contracts.py`) exercises distinct error
    codes via synthetic `TemporaryDirectory` fixtures. Adversarial coverage
    includes: unknown top/nested keys, deadbeef/abbreviated/older authority
    commit, missing/fake section headings, unknown authority documents,
    traversal decision-register paths, duplicate/omitted/wrong-priority error
     codes, corrupted D3/D4 vector expectations, mutated candidate/gate/
     derived-view/checkpoint/pending-candidate/read/state vectors, empty
     `required_families`, malformed shapes
    without traceback, default/full bypass attempts, and at least one
    adversarial mutation test per declared contract surface causing structured
    rejection.

- **Main failure modes**: FREEZE.json field lacks authority anchor; authority
  commit does not equal FREEZE top-level `authority_commit` (abbreviated, older,
  or different); committed document:path not in local repository; section heading
  not found in committed document; unknown authority document; traversal
  decision-register path; decision ref unresolved; unknown top-level key; wrong
  registry count or member set; D3/D4 vector execution mismatch; error
  singleton/priority mismatch; missing pairwise pair; candidate digest logic
  mismatch; illegal gate ID; empty/missing `required_families` bypasses full mode;
  `contract_present` or description-only placeholder where machine-valued typed
  payload required; declared surface lacks adversarial mutation test; validator
  passes on a violation. D3/D4 frontmatter parser contract is now `frozen` (T1a
  authority amendment 2026-07-23 — see active spec §6 D3/D4); resolution is
  complete and not deferrable. T2 STOP if existing T1b test behavior changes,
  or required closed-schema/vector behavior is implemented as a descriptive
  note rather than executed machine logic.

- **`check_s0_freeze.py` Modes**:
  1. **`--oracle-only`** (T2): Validates decisions, loads FREEZE.json, validates
     closed schema + all registries + typed claims (authority-document identity,
     full commit:path section anchor resolution, decision refs), and executes all
     synthetic vectors. Reports `real_fixture_coverage: not_claimed` and
     diagnostic text. Does NOT require real fixture families. This mode is
     sufficient for T2 completion.
  2. **Default / full mode** (T2 partial, T3+ complete): In addition to all
     `--oracle-only` checks, requires all 12 hard-coded T3 fixture family
     directories present/nonempty and completed local `FIXTURE_PROVENANCE.md`.
     At T2 this fails closed with primary `not_available_in_stage`; at T3 with
     real fixtures it must pass. No skip-as-pass.
  3. **`--decisions-only`** (T1b, unchanged): Validates committed
     `S0_DECISIONS.json` per frozen T1b rules. Does not require FREEZE or
     oracle modules.

- **Steps**:
  1. Author FREEZE.json by hand from active spec and decision register. Every
     claim and vector includes `authority_document` + `authority_path`
     (`<full-object-id>:§section`) where the commit component equals FREEZE's
     top-level `authority_commit` exactly. Exact Asset kind count is 17. No
     `contract_present` or description-only placeholders — every surface
     carries machine-valued typed payloads with explicit evaluator IDs.
   2. Implement schema/authority/vector/CLI orchestration responsibilities using
      the informative implementation map above or any cohesive equivalent within
      the allowed T2 paths. Stdlib-only; cohesive and bounded by responsibility.
   3. Preserve existing T1b behavioral assertions in `test_s0_contract_freeze.py`.
      Static/security checks enforce stdlib-only, no `aitp` import, no network,
      no external `.aitp`, and no dynamic-import/eval/subprocess-dispatch tricks.
      Tests MUST NOT assert module names, module count, import topology, or fixed
      test count.
  4. Write adversarial negative tests (`test_s0_negative_contracts.py`): each
     creates a tempdir, writes a deliberately invalid fixture, runs the
     validator as a real subprocess, and asserts expected primary error code
     and structured JSON output — never a traceback. Cover abbreviated/
     older/wrong authority commit, fake/missing section headings, unknown
     authority documents, traversal decision-register paths, unknown nested
     keys, malformed shapes, duplicate/omitted errors, unexecuted vector
     mutations, default/full bypass attempts, and at least one adversarial
     mutation test per declared contract surface.
  5. D3/D4 (frontmatter YAML lexical policy) are already `frozen` per the T1a
     authority amendment 2026-07-23 (active spec §6 D3/D4). The bounded
     two-form scalar grammar is the sole normative rule. `s0_oracle_vectors.py`
     encodes these frozen D3/D4 rules as executed machine checks — not as
     descriptive notes. Any future change to D3/D4 requires a new reviewed
     authority amendment; deferral to S1 is prohibited.

- **Verification**:
  - `python3 tests/aitp2/check_s0_freeze.py --decisions-only` exits 0
    (unchanged T1b).
  - `python3 -m unittest tests/aitp2/test_s0_contract_freeze.py` exits 0
     (existing T1b behavioral tests preserved; test count is implementation
     evidence, not normative).
  - `python3 tests/aitp2/check_s0_freeze.py --oracle-only` exits 0; reports
    all registries confirmed; all authority anchors resolve with commit
    equality enforced and section headings verified; all synthetic vectors
    executed; `real_fixture_coverage: not_claimed` with exact diagnostic text.
  - `python3 -m unittest tests/aitp2/test_s0_negative_contracts.py` exits 0.
  - `python3 -m unittest discover -s tests/aitp2 -p 'test_*.py'` exits 0
    (all T1b + T2 tests).
  - No-argument default/full invocation exits nonzero with primary error
    `not_available_in_stage` and structured JSON listing all missing/empty
    families.
  - Implementation paths remain confined to the named fixture and
    `tests/aitp2/` T2 support surface; modules are cohesive, readable,
    stdlib-only, bounded by responsibility; no `aitp`, third-party, network,
    or external `.aitp` access.
  - Adversarial mutation test exists for every declared contract surface;
    abbreviated/older commits, fake sections, unknown documents, and traversal
    paths all produce structured rejection.

- **Commit**: `test: reviewed FREEZE.json oracle with authority anchors, modular validators, and synthetic negative suite`

#### T2 Future Negative Evidence (Council Required — Executable at T2)

The following contract surfaces require negative fixture evidence at T2/T3.
They are specified here as planning requirements and are now executable
via the modular T2 vector evaluators (`s0_oracle_vectors.py`); no new files
outside the authorized implementation file set are created now.

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
- Derived failure view oracles (§6.0.3): (1) route_episode/prior_attempt
  derivation and `(created_at, id)` ordering, (2) known vs resolved failure
  partition via valid reviewed `resolves_failure` Assessments, (3) blocking
  derivation via reviewed `blocks` minus reviewed `unblocks` targets; plus
  incomplete-scan no-absence and INDEX cache-only fallback.
- Compact checkpoint contract vectors (§9.1): bare-invocation usage exit,
  `--failed`/`--inconclusive` mutual exclusion, defaults
  (`kind: discussion`, `outcome: progress`), deterministic scope fallback
  (explicit `--route` or exactly one Route; multiple plausible Routes require
  explicit `--route`; any `--topic` supplied with one or more Route refs is
  rejected; only zero Route context permits explicit/default topic scope;
  Agent failure/inconclusive with Route origin remains `scope_kind: route`,
  retains resolved origin Route refs, and requires `exact_diff_human_review`),
  compact Episode completeness without any stub/enrich state.
- Episode author/scope/outcome gating vectors (§14.0.1: per-operation actor/
  assurance classification, create equality, update/delete preservation,
  mixed-actor gate union) and pending-candidate vectors (§14.0.3): Agent route
  failure persisted to a draft CANDIDATE before return; return envelope uses
  `status: blocked` + frozen `approval_required` error +
  `result.candidate_state: draft` + required_gates — no `pending_review`;
  pending candidates excluded from the
  canonical derived view and reported separately by enter/closeout; a
  Statement `kind: decision` or Episode `kind: research_decision` can never
  pass deterministic add-only and must carry the exact §6.0.2 decision
  overlay plus the explicit decision-overlay human gate (Gate ID
  `human_review`), regardless of author/scope/outcome.
- Actor-binding negative vectors (§D2a): (1) Agent create operation where
  `created_by` ≠ operation.actor rejected with `validation_failed`
  (`check_id: actor_mismatch`); (2) Agent create operation with
  `created_by: human:*` rejected (`validation_failed`, `check_id: actor_mismatch`);
  (3) actor-unavailable boundary classified fail-closed as Agent-authored,
  `created_by` carries `agent:`; (4) unknown/raw boundary ⇒
  `fail_closed_agent`; (5) update preserves original `created_by` while
  current operation.actor classifies gate; (6) delete uses operation actor
  only; (7) mixed-actor candidate unions all applicable gate floors.
- Approval-binding negative vector (§5.2.2): copying an approval from another
  workspace fails even when candidate revision, tree, paths, actor bindings,
  content/validation hashes, and required gates match; `protocol` and
  `workspace_id` are independently bound and must match commit metadata.
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
  derived failure view (§6.0.3) / next_action spine,
  content envelope boundaries, read coverage reporting, gate matrix, CLI
  static expected-output contract fixtures, runtime inventory, human decision overlay, and
  derived-scan failure/attempt/blocking coverage (including an
  incomplete-coverage case with no absence assertion). Run and code fixture records are
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
      navigation, read coverage, derived failure view, compact checkpoint,
      Episode author gating, pending-candidate boundary, gate matrix,
      static expected-output contract fixtures,
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
| 12 command groups + 7+1 registry + 16 predicates + content envelopes + navigation + read coverage + gate matrix + CLI contracts + human decision overlay + derived failure view + compact checkpoint + pending-candidate boundary | FREEZE.json + fixtures | `python3 tests/aitp2/check_s0_freeze.py --oracle-only` (T2) / `python3 tests/aitp2/check_s0_freeze.py` (T3+ full) | exit 0, reports all frozen contract surfaces |
| All profiles compliant (common header + additional fields, Entity kinds, SOURCE fields, body sections, route_refs, decision overlay, asset-ULID IDs) | Fixtures | `python3 -m unittest discover -s tests/aitp2 -p 'test_*.py'` | exit 0 |
| Negative structural errors distinct (canonical INDEX/forbidden_canonical_path, removed Route failure-ref fields, Episode `resolution_refs`, incomplete derived scan as absence, INDEX-as-authority, pending candidate as canonical truth, missing on-disk draft before return, bare-checkpoint heavy-flow launch, compact-Episode stub marking, truncated-as-exact, partial-search-as-absence, gate downgrade, decision-overlay record staged via deterministic add-only, unknown-stage silent no-op, inventory second-truth, derived-view oracle violation, draft Assessment trust mutation, run-ULID prefix) | Negative fixtures | same | exit 0, one distinct error per boundary |
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
  overlay, asset-ULID IDs), Route navigation fields (9 additional fields),
  Episode compact canonical body minimum, derived failure/attempt/blocking
  view (§6.0.3), compact checkpoint contract (§9.1), Episode
  author/attention gating (§14.0.1), persistence and presentation boundary
  (§14.0.3), JSON envelope with reads
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
- [ ] `route_refs` present on Episode and Assessment; derived
  failure/attempt/blocking sets verified by machine oracles (active spec
  §6.0.3):
  1. `route_episode_refs` / `prior_attempt_refs` derive from route-scoped
     Episodes, sorted `(created_at, id)`.
  2. `route_effect: resolves_failure` (reviewed, human reviewer, route sets
     equal) moves the target failure Episode from derived
     `known_failure_refs` to derived `resolved_failure_refs` — with no Route
     or Episode mutation and no `resolution_refs` field.
  3. `route_effect: blocks` / `unblocks` derive `blocking_assessment_refs`;
     unblocks excludes its `target_ref` blocker; route sets equal; both
     Assessments remain in audit history.
- [ ] Resolved failures leave the derived `known_failure_refs`
  only via a valid reviewed `route_effect: resolves_failure` Assessment;
  failures are never
  deleted; new success does not overwrite old failure.
- [ ] Decision overlay frozen for Statement(kind=decision) and
  Episode(kind=research_decision); canonical decisions require the explicit
  §14.0.1 decision-overlay human gate (Gate ID `human_review`) and can never
  pass deterministic add-only; Agent may draft but not self-approve.
- [ ] Gate matrix floor enforced with mutation taxonomy + unclassified→human
  review default; add-only semantics for low-authority actions; draft
  Assessment must not change trust/unblock/resolve/promote.
- [ ] Episode author/attention gating enforced per §14.0.1: human-authored
  low-authority Episodes (any scope) and Agent topic/shared or route
  non-failure Episodes are deterministic add-only — decision-overlay records
  (Statement `kind: decision`, Episode `kind: research_decision`) excluded,
  governed only by the explicit decision-overlay row (Human review, Gate ID
  `human_review`) regardless of author/scope/outcome; an Agent-authored
  route-scoped failure/inconclusive Episode is persisted to an on-disk draft
  CANDIDATE before command return and requires batched exact-diff human
  review of the final candidate revision before canonical commit.
- [ ] Compact checkpoint contract enforced per §9.1: `aitp checkpoint
  "<summary>"` default compact canonical Episode; bare invocation shows
  usage; `--full` rich path; `--enrich` optional; deterministic scope
  fallback with `--topic` rejected whenever Route context exists and lawful
  only with zero Route context; a compact Episode is a complete canonical-format payload, becomes
  canonical durable memory only after lawful writer commit — before commit
  it is a pending CANDIDATE in lawful state `draft`/`review_ready` with no
  `record_form` field, and the envelope uses `status: blocked` + frozen
  `approval_required` error + `result.candidate_state: draft` for the
  Agent route-failure case — no `pending_review` state or new lifecycle.
- [ ] Persistence/presentation boundary enforced per §14.0.3: pending
  candidates are on-disk and recoverable, excluded from the canonical
  derived failure view until approved/committed, reported separately by
  enter/closeout; routine presentation folds machine internals while exact
  diff/path and validation summary remain visible.
- [ ] U1 `frozen` per user decision 2026-07-23: S0 = pure contract/
  oracle/fixture/static validation; S1 = production CLI/wheel/resources/
  legacy reader/CLI runtime acceptance.
- [ ] All Asset owner IDs use `asset-<ULID>`; `run-<ULID>` is retired.
- [ ] Route profile carries exactly 9 additional fields; `context_refs` is
  frozen and enter reports it plus the §6.0.3 derived failure view
  (`prior_attempt_refs`, `known_failure_refs`, `resolved_failure_refs`,
  `blocking_assessment_refs`) deterministically, with derivation provenance
  (derived, complete/incomplete, commit).
- [ ] Read coverage vocabulary (exact/deferred/skipped/not_checked) enforced;
  an item whose content was actually truncated or omitted must not be marked
  `exact`; global `budget.truncated: true` can coexist with unaffected,
  fully-read items retaining `status: exact`. Absence claims require complete
  search.
- [ ] Gate matrix floor enforced; no profile/Skill version bump lowers the
  global gate; the explicit decision-overlay row (Statement `kind: decision`
  / Episode `kind: research_decision` → Human review, Gate ID
  `human_review`) is enforced and such records never pass deterministic
  add-only.
- [ ] Actor-binding rule enforced (§D2a): create requires `created_by` ==
  operation.actor; update preserves original `created_by` while classifying
  gate by current operation.actor; delete uses operation actor only; Agent
  create operation with `created_by: human:*` rejected (`validation_failed`,
  `actor_mismatch`); actor-unavailable / unknown boundary classified
  fail-closed as Agent-authored (`fail_closed_agent`); mixed-actor candidates
  union all applicable gate floors.
- [ ] Approval and commit identity bind `protocol` (`aitp/2.0`) and originating
  `workspace_id` in addition to revision/tree/paths/operation actor bindings/
  hashes/gates; cross-workspace copied approval fails even when other fields
  match.
- [ ] static expected-output contract fixtures: JSON envelope, error codes (including
  `not_available_in_stage`), workspace states.
- [ ] Ref grammar constraints verified: store-relative POSIX, no traversal,
  symlink escape rejected, pinned read via `git show`, distinct errors.
- [ ] Each S0 frozen structural invariant has at least one positive or negative
  evidence fixture; safety boundaries (traversal, legacy-write, credential
  rejection) have negative evidence; extended negative cases (canonical INDEX,
  removed Route failure-ref fields, Episode `resolution_refs`, incomplete
  derived scan asserted as absence, INDEX treated as authority, pending
  candidate treated as canonical truth, truncated-as-exact,
  partial-search-as-absence, gate
  downgrade, decision-overlay record (Statement `kind: decision` / Episode
  `kind: research_decision`) staged via deterministic add-only,
  unknown-stage silent no-op, inventory second-truth) are covered.
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

- [ ] **Fail-closed baseline rule**: After the AUTHORITY_COMMIT (the pushed
  SHA of this two-doc amendment), the set of S0 changed/created paths
  relative to that commit MUST be a subset of the Allowed new/modify S0
  paths below. Every tracked path existing at AUTHORITY_COMMIT outside that
  allowlist must remain byte-identical. Under `tests/**`, existing files are
  protected; only new files under `tests/aitp2/**` and
  `tests/fixtures/aitp2/**` are allowed. The active spec and plan are not
  authorized for silent S0 edits; any later normative change requires a
  separate reviewed amendment before S0 continues. The authority guard and
  S0 simplicity ratchet must compare against AUTHORITY_COMMIT and fail on
  any path outside the exact S0 allowlist or any modified pre-existing
  historical file under protected roots.

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
    created only; S0/T2 regeneration begins after pushed AUTHORITY_COMMIT +
    successful T0, then produces reviewed T2 PASS; only after T2 PASS does T3+
    begin. T1a (decision register, provenance stubs), Oracle Gate B, and T1b
    (validator skeleton) are historical completed prerequisites and are not
    repeated. The current execution order is: AUTHORITY_COMMIT → T0 preflight
    → T2 regeneration/validation → reviewed T2 PASS → T3+.
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
two-path authority amendment is separately reviewed and committed (pushed),
the correct dependency order is:
1. T0: clean-tree/remote/guard preflight (depends on pushed AUTHORITY_COMMIT).
2. T2: regenerate FREEZE.json and T2 validator modules from the amended active
   spec, using AUTHORITY_COMMIT as the authority anchor/baseline input;
   execute all oracle/schema/vector/negative validation and achieve reviewed
   T2 PASS. T2's Depends-on explicitly consumes recorded AUTHORITY_COMMIT as
   baseline input.
3. Only after reviewed T2 PASS: T3 (fixture authorization/provenance,
   authorized sanitized structural fixtures with provenance).
4. T4: simplicity ratchet and S0 CI workflow.
5. T5: acceptance packet / S0 Acceptance Gate.

T1a (decision register, provenance stubs), Oracle Gate B, and T1b (validator
skeleton) are historical completed prerequisites and are NOT repeated.

### 10.3 Future S0 Execution Commits

S0 execution follows T0–T5 (T1a/GateB/T1b are historical completed):
1. T0: preflight (rerun after this amendment commit)
2. T2: `test: reviewed FREEZE.json oracle with authority anchors and synthetic negative suite`
3. T3: `test: authorized sanitized structural fixtures with provenance`
4. T4: `ci: S0 simplicity ratchet and contract workflow`
5. T5: `docs: S0 freeze acceptance`

### 10.4 Gate Naming

- **Council review (Phase 1)**: reviews the planning approach (behavior-not-
  code-shape coherence) before Oracle Gate A. Completed and passed for the
  Phase 1 four-path commit.
- **Council review (current)**: reviews the decision coherence and spec
  consistency of this two-path authority amendment. Pending.
- **Oracle Gate A (completed, historical)**: reviewed the Phase 1 amended
  plan only (plan-only, before the four-path commit). Renewed from the
  original Oracle Gate 3 (renamed Gate A) to reflect the Phase 1 scope.
  Gate A passed; commit `7de57f34` reflects the reviewed state.
- **Independent Oracle review (current)**: reviews the exact two tracked
  paths (active spec + S0 plan) of this authority amendment. This is a
  focused review distinct from historical Gate A — it does not re-open
  Gate A's scope and is not a new named gate. Pending.
- **T1a, Oracle Gate B, T1b (historical completed)**: T1a created the
  decision register and provenance stubs; Oracle Gate B reviewed T1a
  artifacts; T1b produced the validator skeleton. All three are historical
  prerequisites and are not repeated in this amendment's execution.
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
