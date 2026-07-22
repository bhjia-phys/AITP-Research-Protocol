# AITP 2.0 S0 Contract and Fixture Freeze Implementation Plan

> **Status**: proposed, plan-only. This document is a Phase 3 deliverable per the
> cutover design §9.2 item 3.
> It is NOT an S0 execution artifact. No contract freeze, fixture, validator,
> `src/aitp/`, `pyproject.toml`, `__init__.py`, wheel, package resource, CLI,
> CI workflow, real `.aitp`, legacy adapter, or runtime object is created by
> this single commit.
>
> **Authority snapshot** (recorded at plan authorship, not normative for S0 execution):
> - `authority_cutover_commit` / Phase 2 parent: `389b3149ef9f6dd054ed82e0e7821c2868a4972e`
>   (branch `codex/aitp-2-authority-cutover`, tree clean)
> - Live-main baseline: `eec20f6faeb089ec2fcdc982ad65adce242a21a9`
> - Evidence checkpoint (read-only): `869d8e65f19e69404405e4da976876be8fc7f9a0`
>
> The SHA of this plan commit is recorded by Git at commit time; it is not
> self-embedded. At S0 execution T0, the S0 base must be a descendant of the
> reviewed plan commit that includes `389b...` in its ancestry.
>
> **Gating**:
> - S0 execution MUST NOT begin before this plan passes Oracle Gate 3 review
>   (self-review, architecture review, security review, independent audit).
> - S1 CLI implementation MUST NOT begin before S0 execution achieves S0 PASS.
> - Once reviewed, this document is the sole normative S0 execution plan.
>   Previous v5/pre-cutover implementation sequences are historical and
>   non-normative.

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

### 1.1 This Plan Commit

The current commit creates exactly one file:
`docs/superpowers/plans/2026-07-23-aitp-2-0-s0-contract-and-fixture-freeze-plan.md`.
No other files, directories, scaffolding, code, fixtures, or CI changes.

### 1.2 Non-Goals (Plan Commit)

- No `tests/fixtures/aitp2/`, `FREEZE.json`, or fixture content.
- No `src/aitp/`, `pyproject.toml`, `__init__.py`, or Python package.
- No wheel, package resources, or `importlib.resources` metadata.
- No validators (`check_s0_freeze.py`, `test_s0_*.py`, `check_aitp2_simplicity.py`).
- No modification to `.github/workflows/authority-guard.yml` or any CI workflow.
- No real `.aitp`, store records, legacy adapter, CLI, writer, or dispatcher.
- No access to external `.aitp` or private research directories.
- No implementation commit, merge, or PR. After Gate 3 PASS, only the exact
  one-file plan commit and development-branch push described in §10.1 are permitted.

### 1.3 Non-Goals (Future S0 Execution)

Until U1 is resolved, this plan uses the fail-closed provisional boundary below.
If U1 assigns wheel/resources or legacy-reader implementation to S0, this plan
must be amended and pass Oracle Gate 3 again before S0 execution.

S0 execution still does NOT: implement CLI/parser/dispatcher/command behavior;
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
`not_found`, `invalid_ref`, `outside_store`, `revision_not_found`,
`profile_mismatch`, `payload_hash_mismatch`, `anchor_not_found`) are as
specified in active spec §6.1.

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
mutate, promote trust, or make old schemas canonical. Implementation deferred
under the provisional boundary; U1 may instead require a reviewed plan/authority
amendment before execution. See §3.1.

## 3. Blocking Decision Register

S0 execution must carry a machine-readable JSON decision register (NOT YAML)
committed as `tests/fixtures/aitp2/S0_DECISIONS.json`. It is review/test
evidence, not a second authority. Any normative resolution MUST be reflected in
an approved active-spec/disposition authority amendment before it can be marked
`frozen`. The decision register catalogs open items; the spec + disposition
remain the sole normative truth.

### 3.1 Decision Table

| # | Decision | Status | Spec ref | Notes |
|---|----------|--------|----------|-------|
| D1 | Timestamp lexical form | `user-decision-required` | active spec §6 | Proposed default: strict ISO-8601 UTC `Z`. Must be explicitly resolved. |
| D2 | `created_by` identity format | `user-decision-required` | active spec §6 | Proposed: `human:<slug>` or `agent:<slug>`. Must be explicitly resolved. |
| D3 | YAML subset for frontmatter | `user-decision-required` | active spec §6 | Proposed: plain scalars, sequences, maps; no tags, anchors, aliases, flow collections at top-level values. YAML parsing policy is non-trivial — stdlib has no YAML parser; a bounded test-only parser vs. defer-to-S1 must be decided. |
| D4 | Duplicate YAML keys | `user-decision-required` | active spec §6 | Proposed: rejected. Cannot be validated with grep; requires YAML parser policy resolution (D3). |
| D5 | ULID case normalization | `user-decision-required` | active spec §6 | Proposed: uppercase Crockford Base32. Must be explicitly resolved. |
| D6 | Encoding and newline | `user-decision-required` | active spec §6 | Proposed: UTF-8 without BOM, LF-only, exactly one trailing newline. Must be explicitly resolved. |
| D7 | Full Git object-id in refs | `frozen` | active spec §6.1 | Use whatever full object-id the owning Git resolves and emits. No fixed hex length. Interactive `show` may accept unambiguous abbreviations but emits the full id. |
| D8 | Field order normative? | `user-decision-required` | active spec §6 | Proposed: no — equality is semantic, not byte-order. Must be explicitly resolved. |
| D9 | Unknown frontmatter fields | `user-decision-required` | active spec §6 | Proposed: rejected. Must be explicitly resolved. |
| **U1** | **S0 wheel/resource and legacy-read stage interpretation** | **`user-decision-required`** | active spec §17 S0, audit disposition §"Re-Review Gate" | **BLOCKING ambiguity**: active spec §17 S0 and audit disposition reference built-wheel resources and legacy searchable as S0 items, while S1 owns package/resources and cutover Phase 3 currently authorizes only this plan-only deliverable. PROJECT_MEMORY.md states "S0 has not started; no installable 2.0 runtime exists." The recommended but not yet approved interpretation is: S0 freezes expectations and guards only; built wheel, package resources, and a legacy reader belong to S1 or a later slice. U1 MUST be explicitly decided by the user (or a designated human authority) at future S0 T1. If not decided, T1 STOP. If a different stage split is chosen, amend this plan and affected authority, then repeat Gate 3 before execution. Oracle Gate 3 only confirms the ambiguity is properly recorded; it does NOT resolve it. |

### 3.2 Statuses

- **`frozen`** — resolved deterministically; S0 machines can enforce.
- **`user-decision-required`** — must be resolved by explicit human decision before S0 PASS. No default assumed.
- **`explicitly-deferred`** — deferred to a named slice with rationale and acceptance criteria.

No `TBD`, `pending`, `discuss`, or blank. Any decision not `frozen` or
`explicitly-deferred` at S0 PASS time blocks S0 PASS.

### 3.3 Resolution Process

1. Resolution is a future S0 T1 activity, not a plan-review activity. At T1 the
   user (or a designated human authority) explicitly decides each
   `user-decision-required` entry or approves the proposed default with
   explicit authority. Oracle Gate 3 does NOT resolve these decisions; it
   only confirms that this plan correctly exposes them as open.
2. If resolution requires amending the active spec or disposition, a separate
   reviewed authority amendment commit is required before the decision can
   be marked `frozen`; the plan must not silently modify the spec.
3. If the active spec is genuinely ambiguous or contradictory on a point not
   covered by an existing decision entry, S0 is BLOCKED at T1. A separate
   reviewed authority amendment must precede any decision freeze.
4. Oracle Gate 3 reviews this plan only. It does NOT resolve future U1/D1–D9,
   fixture authorization, implementation choices, or S0 acceptance. Those
   belong to explicit T1 human decisions and subsequent S0 execution.

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
  S0 artifact commit (T1), not in a separate empty commit.
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

### T1 — Authority Interpretation + Blocking Decisions + Authorization Record

- **Depends on**: T0.
- **Files (create)**:
   - `tests/fixtures/aitp2/S0_DECISIONS.json` — populated decision
     register with all U1/D1–D9 entries and their explicit T1 human
     decisions.
   - `tests/fixtures/aitp2/FIXTURE_PROVENANCE.md` — authorization stubs
     with pre-read fields per §4.1 (symbolic source ID/class, owner/approver,
     authorized scope, restrictions, approval evidence); NO snapshot hashes
     or source bytes at this stage.
   - `tests/aitp2/check_s0_freeze.py` — stdlib-only oracle validator skeleton
     supporting `--decisions-only` mode (see below).
   - `tests/aitp2/test_s0_contract_freeze.py` — synthetic temp-dir self-tests
     proving the validator core works (no real fixtures yet).
- **Observable claim**: all `user-decision-required` entries resolved by
  explicit T1 human decisions; U1 explicitly decided; authority traceability
  established; validator core functional; `--decisions-only` passes.
- **Main failure modes**: U1 unresolved → STOP; decision register contains
  `TBD`; spec amendment needed but not done; `--decisions-only` FAIL.
- **`check_s0_freeze.py --decisions-only` Mode** (T1):
  Validates the decision register and authorization stubs without requiring
  FREEZE.json or real fixtures:
  - Exact entry set is U1 + D1–D9; no missing, no extra.
  - Only three statuses allowed: `frozen`, `user-decision-required`,
    `explicitly-deferred`.
  - T1 completion condition: ZERO `user-decision-required` entries remain.
  - D7 is `frozen` and includes an active-spec authority ref.
  - Each `frozen` normative resolution includes an approved
    authority/amendment ref.
  - Each `explicitly-deferred` entry includes named slice, rationale, and
    acceptance criteria.
  - FIXTURE_PROVENANCE.md authorization stub exists and contains pre-read
    fields: symbolic source ID/class, approver, scope, restrictions,
    approval evidence. MUST NOT contain unauthorized snapshot bytes or
    hashes computed before authorization.
  Any failure → STOP; T1 cannot proceed to T2.
- **Steps**:
   1. Populate `S0_DECISIONS.json` with all entries from §3.1.
   2. User/designated human authority explicitly decides each
      `user-decision-required` entry; T1 STOP if any blocker remains.
   3. If resolution requires a normative spec/disposition authority amendment,
      produce that as a separate reviewed commit before continuing. T1 STOP
      until the amendment is independently reviewed and approved.
   4. If any decision reveals a genuine active-spec ambiguity or conflict not
      in the register, BLOCK and obtain explicit user approval for an
      authority amendment before proceeding.
   5. Write FIXTURE_PROVENANCE.md authorization stubs per §4.1.
   6. Implement `check_s0_freeze.py` (stdlib-only) with `--decisions-only`
      mode and its synthetic self-tests.
- **Verification**:
  - `python3 tests/aitp2/check_s0_freeze.py --decisions-only` exits 0.
  - `python3 -m unittest tests/aitp2/test_s0_contract_freeze.py` passes
    synthetic self-tests.
  Any failure → STOP; T1 incomplete.
- **Commit**: `test: establish S0 decisions, authorization, and validator core`

### T2 — Reviewed FREEZE.json + Validator Integration + Synthetic Negatives

- **Depends on**: T1 (`--decisions-only` pass confirmed; no `user-decision-required`
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
    register.
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
  unresolved → T2 STOP unless authority amendment (see §7.1).
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
   4. If D3/D4 (frontmatter YAML lexical policy) is not yet frozen by an
      approved T1 authority amendment defining the bounded test-only parser
      contract, then S0 claim must be narrowed by a separate reviewed
      authority acceptance amendment — otherwise T2 STOP. Silent deferral to
      S1 without amendment is prohibited (see §7.1).
- **Verification**:
  - `python3 tests/aitp2/check_s0_freeze.py --oracle-only` exits 0; reports
    12/7+1/16 counts confirmed; all authority anchors present; synthetic
    negatives produce distinct errors.
  - `python3 -m unittest tests/aitp2/test_s0_negative_contracts.py` exits 0.
- **Commit**: `test: reviewed FREEZE.json oracle with authority anchors and synthetic negative suite`

### T3 — Provenance + Minimal Sanitized Structural Fixtures

- **Depends on**: T2 (validator exists with `--oracle-only` mode verified).
- **Files (create)**: all positive and negative fixture families under
  `tests/fixtures/aitp2/quantum-chaos/`, `nio/`, `shared-paper/`,
  `knowledge-card/`, `skill/`, `negative/`. Updates to FIXTURE_PROVENANCE.md.
- **Observable claim**: validator default/full mode (no `--oracle-only` flag)
  passes on all positive fixtures and reports expected failures on all negative
  fixtures; FIXTURE_PROVENANCE.md records source class, snapshot hashes,
  redactions, and `seeding` declarations; no private path/credential/host/URL
  exists. Missing fixture families → FAIL (no skip-as-pass in full mode).
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
  2. Fill acceptance checklist from §9.1.
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
| Decision register complete + authorization stubs valid | S0_DECISIONS.json + FIXTURE_PROVENANCE.md | `python3 tests/aitp2/check_s0_freeze.py --decisions-only` (T1) | exit 0, zero `user-decision-required`, frozen entries authority-ref'd |
| 12 command groups + 7+1 registry | FREEZE.json + fixtures | `python3 tests/aitp2/check_s0_freeze.py --oracle-only` (T2) / `python3 tests/aitp2/check_s0_freeze.py` (T3+ full) | exit 0, reports 12 commands, 7 nodes, 1 edge, 16 predicates |
| All profiles compliant | Fixtures | `python3 -m unittest discover -s tests/aitp2 -p 'test_*.py'` | exit 0 |
| Negative structural errors distinct | Negative fixtures | same | exit 0, one distinct error per boundary |
| Simplicity — S0 production absence | `src/aitp/`, `pyproject.toml` | `python3 scripts/check_aitp2_simplicity.py --phase s0` | exit 0 |
| Repository authority intact | All tracked files | `python3 scripts/check_repository_authority.py` | exit 0 |
| Whitespace clean | Changed files | `git diff --check` | exit 0, no warnings |

### 7.1 Constraints

- Tests must NOT judge scientific truth, semantic relevance, or command intent.
- Negative tests use `tempfile.TemporaryDirectory`; never touch external `.aitp`.
- No network, external Git remote, or external filesystem access in any test.
- Frontmatter YAML lexical validation (duplicate keys, anchors, aliases, tags,
  flow collections at top-level values) requires a bounded test-only parser
  contract. If S0 PASS must claim machine-checkable Markdown frontmatter
  (§9.1), then D3/D4 MUST be frozen at T1 as an approved bounded test-only
  parser contract, and implemented by T2. If the user/designated authority
  defers this to S1, the S0 claim MUST first be narrowed by a separate
  reviewed authority/S0 acceptance amendment — without it, T2 STOP. Silent
  deferral and skip without amendment is prohibited.

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
  relation predicates; every field has `authority_path` annotation.
- [ ] Common header (7 fields + optional `kind`) machine-checkable.
- [ ] Every Asset kind has a scope-sensitive path profile; records match exactly
  one legitimate template.
- [ ] Ref grammar constraints verified: store-relative POSIX, no traversal,
  symlink escape rejected, pinned read via `git show`, distinct errors.
- [ ] Each S0 frozen structural invariant has at least one positive or negative
  evidence fixture; safety boundaries (traversal, legacy-write, credential
  rejection) have negative evidence.
- [ ] No legacy import, write, dual-write, or fallback in 2.0 contract surface.
- [ ] One canonical writer finish-path invariant frozen and testable.
- [ ] Simplicity ratchet passes in `--phase s0` — zero production code/package.
- [ ] All protected paths (historical KEEP-HISTORICAL, external `.aitp`,
  `research/knowledge-hub/canonical/`, `contracts/`, `schemas/`) zero modifications.
- [ ] Zero unresolved `user-decision-required` in decision register.
- [ ] Local HEAD equals remote HEAD for this branch.
- [ ] `python3 scripts/check_repository_authority.py` exits 0.
- [ ] Separate S0 CI workflow passes.
- [ ] Independent S0 Acceptance Gate review confirms no blocking findings.

### 9.2 S0 FAIL

Any one of: CLI scaffold/parser/writer exists; any repository-local production
artifact listed in §8.1 exists; installed Skill content committed (not fixture
exemplar); real `.aitp` created/modified; external store accessed; v5 record
mutated; migration/dual-write/coercion exists; semantic validator judging
physics truth exists; MCP/hook/compiler/database/index/scanner exists; fixture
without provenance; private credential/path committed; implementation-defined
contract asserted as normative.

## 10. Review and Commit Strategy

### 10.1 This Plan Commit

- **Exact change**: one new file
  `docs/superpowers/plans/2026-07-23-aitp-2-0-s0-contract-and-fixture-freeze-plan.md`.
- **Commit message**: `docs: plan AITP 2.0 S0 contract and fixture freeze`
- **Allowlist**: exactly the one plan file.
- **Pre-commit**: `git status --short --untracked-files=all` shows only this
  file; `git diff --check --no-index /dev/null <file>` no whitespace errors;
  `python3 scripts/check_repository_authority.py` exits 0.
- **After push**: verify remote SHA matches local HEAD. Then STOP. No further
  commits, no merge, no S0 execution.

### 10.2 Oracle Gate 3

Oracle Gate 3 reviews this plan only. It does NOT resolve future fixture
authorization, implementation choices, U1/D1–D9 decisions, or S0 acceptance.
Gate 3 confirms:
- Plan consistency with authoritative references.
- No implementation coupling, semantic validators, or hidden infrastructure.
- Fixture authorization/provenance/redaction rules sufficient.
- U1, D1–D6, D8–D9 are correctly exposed with status
  `user-decision-required`; D7 is already `frozen` per the active spec
  §6.1 and is authority-traceable (the spec is the sole normative source;
  no separate amendment is needed). All `user-decision-required` decisions
  remain open; they are resolved by the user/designated human authority at
  S0 T1.
- Plan does not silently modify the active spec or audit disposition.

### 10.3 Future S0 Execution Commits

S0 execution (when authorized) follows T0–T5:
1. T1: `test: establish S0 decisions, authorization, and validator core`
2. T2: `test: reviewed FREEZE.json oracle with authority anchors and synthetic negative suite`
3. T3: `test: authorized sanitized structural fixtures with provenance`
4. T4: `ci: S0 simplicity ratchet and contract workflow`
5. T5: `docs: S0 freeze acceptance`

### 10.4 Gate Naming

- Oracle Gate 3: reviews this plan (plan-only, before S0 execution).
- S0 Acceptance Gate: final S0 execution gate. No "Gate 4" numbering is used;
  the next distinct gate after the plan review is simply the S0 acceptance gate.

## 11. Risks, Stop Conditions, and Explicit Stop Before S1

### 11.1 Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Insufficient authorized material | S0 BLOCKED; `seeding` | Obtain additional authorization or amend vertical requirements via governance |
| U1 unresolved | S0 cannot proceed past T1 | Explicit decision during T1 before any fixture or source work |
| Active spec genuinely ambiguous on unregistered point | S0 BLOCKED | Separate spec amendment + disposition update before resuming |
| Production artifact accidentally scaffolded in S0 | Ratchet FAIL | Local verification before commit + required S0 CI blocks |
| Plan confused with execution | Premature S0 PASS | Frontmatter states "proposed, plan-only"; no fixture/validator created |
| YAML lexical policy unresolved (D3/D4) | Cannot validate duplicate keys/anchors; S0 claim overbroad if frontmatter machine-checkability asserted | Freeze D3/D4 as bounded test-only parser contract at T1 and implement in T2, OR narrow S0 claim via separate authority/S0 acceptance amendment before T2; T2 STOP otherwise |

### 11.2 Stop Conditions

STOP and do NOT proceed to S1 if:

- Any `user-decision-required` remains unresolved.
- U1 not explicitly decided.
- FIXTURE_PROVENANCE.md lacks explicit authorization for any real source used.
- Any committed file contains a machine path, credential, hostname, private URL,
  or restricted binary byte.
- FREEZE.json disagrees with active spec (spec is normative).
- Simplicity ratchet reports FAIL in `--phase s0`.
- `check_repository_authority.py` reports FAIL.
- S0 Acceptance Gate review reports any blocking finding.
- Any repository-local production artifact listed in §8.1 exists.
- Any v5 canonical record is mutated.

### 11.3 Explicit Stop Before S1

S0 PASS is a hard gate. S1 CLI implementation MUST NOT begin until S0 achieves
PASS per §9.1, all S0 execution commits are on the dev branch, and S0 Acceptance
Gate is recorded. No conditional/parallel S0/S1 work, and no S1 feature may be
"mostly done" before S0 closes.
