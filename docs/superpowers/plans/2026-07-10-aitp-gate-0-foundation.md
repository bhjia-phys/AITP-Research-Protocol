# AITP Gate 0 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the data-integrity, registry, query, performance, context-injection, and module-boundary foundation required before AITP lifecycle, knowledge, execution, and skill features can safely run on the real research store.

**Architecture:** Add compatibility-first registries and repository/query services around the existing Markdown/YAML kernel. Migrate readers and one low-risk writer at a time behind stable public functions, preserve schema-v1 records, and prove every behavior with test-first slices. Derived indexes accelerate reads but never become canonical state.

**Tech Stack:** Python 3, dataclasses, `ast`, pathlib, Markdown/YAML frontmatter, pytest, FastMCP-compatible public surfaces, PowerShell-safe commands.

## Global Constraints

- Run each production-code step only after its named failing test has failed for the expected reason.
- Do not edit or revert the existing uncommitted Harness Feedback files unless a task explicitly names them.
- Do not rewrite the real canonical topic store during Gate 0.
- Do not increase architecture-test line limits.
- Preserve current imports through compatibility re-exports.
- Canonical Markdown remains authoritative; all indexes are derived and disposable.
- A malformed canonical record is reported, not silently converted into absence.
- Use the bundled workspace Python and an explicit writable `--basetemp` when the default environment cannot run pytest.
- Commit only files owned by the current task.
- For a shared file that was already dirty before Gate 0, stage only the current
  task's hunks through an explicit cached patch; never stage the pre-existing
  working-tree diff.

---

## File Structure

| File | Responsibility |
|---|---|
| `brain/v5/runtime_audit.py` | Static and workspace-aware inventory of files, record families, writers, surfaces, and drift. |
| `brain/v5/runtime_audit_rendering.py` | Focused Markdown renderer for the runtime audit, kept separate from inventory logic. |
| `brain/v5/runtime_audit_contracts.py` | Validation of the audit payload and classifications. |
| `brain/v5/record_envelope.py` | Common compatibility envelope and payload hashing. |
| `brain/v5/record_family_registry.py` | Single family specification registry and path/ref metadata. |
| `brain/v5/record_family_contracts.py` | Registry integrity diagnostics. |
| `brain/v5/record_repository.py` | Atomic idempotent canonical read/write/list API. |
| `brain/v5/record_repository_contracts.py` | Write/read result contracts. |
| `brain/v5/query_index.py` | Generation-stamped deterministic derived index. |
| `brain/v5/query_index_contracts.py` | Index manifest/build validation. |
| `brain/v5/research_retrieval.py` | Exact, filtered, and lexical query API with coverage. |
| `brain/v5/retrieval_audit.py` | Persistable trust-neutral query coverage payload. |
| `brain/v5/context_compiler.py` | One bounded context assembly path over retrieval results. |
| `brain/v5/context_compiler_contracts.py` | Token/byte, coverage, and trust-neutral validation. |
| `brain/v5/capability_registry.py` | Single host capability declaration registry. |
| `brain/v5/capability_registry_contracts.py` | MCP/CLI/public/bridge/compact exposure diagnostics. |

## Task 1: Runtime Capability And Family Audit

**Files:**
- Create: `brain/v5/runtime_audit.py`
- Create: `brain/v5/runtime_audit_rendering.py`
- Create: `brain/v5/runtime_audit_contracts.py`
- Create: `tests/test_v5_runtime_audit.py`
- Create: `docs/superpowers/progress/2026-07-10-aitp-runtime-capability-audit.md`
- Modify: `brain/v5/workspace_inventory.py`

**Interfaces:**
- Produces: `build_runtime_capability_audit(repo_root: str | Path, *, workspace_base: str | Path | None = None, plan_path: str | Path | None = None) -> dict[str, Any]`
- Produces: `render_runtime_capability_audit_markdown(payload: dict[str, Any]) -> str`
- Produces: `validate_runtime_capability_audit(payload: dict[str, Any]) -> ContractResult`
- Consumes: `_LAYOUT_DIRS`, literal `WorkspacePaths.registry_dir(...)` calls, actual workspace registry directories, plan file paths, public surface tuple, runtime entrypoint catalog, MCP wrapper names, compact allowlist, and source/test file lists.

- [x] **Step 1: Write the failing static audit test**

```python
from pathlib import Path

from brain.v5.runtime_audit import build_runtime_capability_audit


def test_runtime_audit_finds_registry_drift_and_classifies_every_file(tmp_path):
    repo = tmp_path / "repo"
    (repo / "brain" / "v5").mkdir(parents=True)
    (repo / "hooks").mkdir()
    (repo / "tests").mkdir()
    (repo / "brain" / "v5" / "paths.py").write_text(
        '_LAYOUT_DIRS = ["registry/claims"]\n', encoding="utf-8"
    )
    (repo / "brain" / "v5" / "writer.py").write_text(
        'def write(ws):\n    return ws.registry_dir("insights")\n', encoding="utf-8"
    )
    (repo / "hooks" / "host.py").write_text("pass\n", encoding="utf-8")
    (repo / "tests" / "test_v5_writer.py").write_text("pass\n", encoding="utf-8")
    plan = repo / "plan.md"
    plan.write_text("- Create: `brain/v5/writer.py`\n", encoding="utf-8")

    payload = build_runtime_capability_audit(repo, plan_path=plan)

    assert payload["record_families"]["used_not_layout"] == ["insights"]
    assert payload["inventory"]["classification_counts"]["directly_touched_by_plan"] == 1
    assert all(row["classification"] for row in payload["files"])
```

- [x] **Step 2: Run the test and verify RED**

Run:

```powershell
python -m pytest tests\test_v5_runtime_audit.py::test_runtime_audit_finds_registry_drift_and_classifies_every_file -q -p no:cacheprovider --basetemp tmp\pytest-g0-runtime-audit-red
```

Expected: collection fails with `ModuleNotFoundError: No module named 'brain.v5.runtime_audit'`.

- [x] **Step 3: Implement literal family and file inventory**

Create `brain/v5/runtime_audit.py` with these concrete building blocks:

```python
from __future__ import annotations

import ast
import re
from collections import Counter
from pathlib import Path
from typing import Any


_CLASSIFICATIONS = (
    "directly_touched_by_plan",
    "covered_by_integration_choke_point",
    "adjacent_but_no_change_expected",
    "requires_task_update",
    "deferred_legacy_or_domain_surface",
)
_CHOKE_POINTS = {
    "brain/v5/mcp_tools.py",
    "brain/v5/public_surfaces.py",
    "brain/v5/runtime_entrypoint_catalog.py",
    "brain/v5/runtime_bridge_targets.py",
    "brain/v5/codex_facade.py",
    "brain/v5/workspace_refresh.py",
}


def build_runtime_capability_audit(
    repo_root: str | Path,
    *,
    workspace_base: str | Path | None = None,
    plan_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    planned = _planned_paths(Path(plan_path)) if plan_path else set()
    files = _source_rows(root, planned)
    layout = _layout_families(root / "brain" / "v5" / "paths.py")
    used, users = _literal_registry_families(root / "brain" / "v5")
    actual = _actual_registry_families(Path(workspace_base)) if workspace_base else []
    counts = Counter(row["classification"] for row in files)
    return {
        "kind": "runtime_capability_audit",
        "repo_root": str(root),
        "workspace_base": str(Path(workspace_base).resolve()) if workspace_base else "",
        "inventory": {
            "file_count": len(files),
            "classification_counts": dict(sorted(counts.items())),
        },
        "files": files,
        "record_families": {
            "layout": layout,
            "literal_uses": used,
            "actual_workspace": actual,
            "used_not_layout": sorted(set(used) - set(layout)),
            "actual_not_layout": sorted(set(actual) - set(layout)),
            "layout_not_used": sorted(set(layout) - set(used)),
            "literal_users": users,
        },
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
```

Implement helpers using `ast.parse` for `_LAYOUT_DIRS` and literal
`registry_dir("family")` calls. `_source_rows` scans `brain/v5/*.py`, `hooks/*.py`,
and `tests/test_v5_*.py`; plan-listed paths are `directly_touched_by_plan`,
legacy-prefixed files are `deferred_legacy_or_domain_surface`, choke points are
`covered_by_integration_choke_point`, and all remaining files are
`adjacent_but_no_change_expected`.

- [x] **Step 4: Run the focused test and verify GREEN**

Run the Step 2 command.

Expected: `1 passed`.

- [x] **Step 5: Add actual-workspace and malformed-input tests**

```python
def test_runtime_audit_reports_actual_workspace_families(tmp_path):
    repo = _minimal_repo(tmp_path)
    workspace = tmp_path / "topics"
    (workspace / ".aitp" / "registry" / "claims").mkdir(parents=True)
    (workspace / ".aitp" / "registry" / "unregistered_family").mkdir()

    payload = build_runtime_capability_audit(repo, workspace_base=workspace)

    assert payload["record_families"]["actual_workspace"] == [
        "claims",
        "unregistered_family",
    ]
    assert payload["record_families"]["actual_not_layout"] == ["unregistered_family"]


def test_runtime_audit_reports_python_parse_errors(tmp_path):
    repo = _minimal_repo(tmp_path)
    broken = repo / "brain" / "v5" / "broken.py"
    broken.write_text("def broken(:\n", encoding="utf-8")

    payload = build_runtime_capability_audit(repo)

    row = next(item for item in payload["files"] if item["path"].endswith("broken.py"))
    assert row["classification"] == "requires_task_update"
    assert row["parse_error"]
```

Add this helper above those tests:

```python
def _minimal_repo(tmp_path):
    repo = tmp_path / "repo"
    (repo / "brain" / "v5").mkdir(parents=True)
    (repo / "hooks").mkdir()
    (repo / "tests").mkdir()
    (repo / "brain" / "v5" / "paths.py").write_text(
        '_LAYOUT_DIRS = ["registry/claims"]\n', encoding="utf-8"
    )
    return repo
```

- [x] **Step 6: Run both tests and verify RED**

Run:

```powershell
python -m pytest tests\test_v5_runtime_audit.py -q -p no:cacheprovider --basetemp tmp\pytest-g0-runtime-audit-red2
```

Expected: failures show missing actual-workspace or parse-error handling.

- [x] **Step 7: Add actual family and parse-error handling**

Implement `_actual_registry_families` against
`workspace_base/.aitp/registry`. Catch `SyntaxError` per source file, set
`classification="requires_task_update"`, and retain the formatted error in
`parse_error`.

- [x] **Step 8: Add contract and Markdown renderer tests**

```python
from brain.v5.runtime_audit import render_runtime_capability_audit_markdown
from brain.v5.runtime_audit_contracts import validate_runtime_capability_audit


def test_runtime_audit_contract_and_markdown(tmp_path):
    payload = build_runtime_capability_audit(_minimal_repo(tmp_path))

    result = validate_runtime_capability_audit(payload)
    rendered = render_runtime_capability_audit_markdown(payload)

    assert result.ok
    assert "# AITP Runtime Capability Audit" in rendered
    assert "## Registry Family Drift" in rendered
    assert "can_update_claim_trust: false" in rendered
```

- [x] **Step 9: Run the contract test and verify RED**

Run:

```powershell
python -m pytest tests\test_v5_runtime_audit.py::test_runtime_audit_contract_and_markdown -q -p no:cacheprovider --basetemp tmp\pytest-g0-runtime-audit-contract-red
```

Expected: import failure for `runtime_audit_contracts` or missing renderer.

- [x] **Step 10: Implement the validator and renderer**

Use the repository `ContractResult`/`Issue` pattern. Require the top-level kind,
list-shaped files, all valid classifications, record-family lists, and false
trust/mutation flags. Render inventory counts, drift lists, parse errors, and one
Markdown table row per file.

- [x] **Step 11: Run all Task 1 tests**

Run:

```powershell
python -m pytest tests\test_v5_runtime_audit.py tests\test_v5_workspace_inventory.py -q -p no:cacheprovider --basetemp tmp\pytest-g0-runtime-audit-green
```

Expected: all tests pass.

- [x] **Step 12: Generate the live report**

Run the new renderer against:

```text
repo_root = F:/AI_Workspace/repos/AITP-Research-Protocol
workspace_base = F:/AI_Workspace/Theoretical-Physics/research/aitp-topics
plan_path = docs/superpowers/plans/2026-07-09-aitp-final-research-lifecycle-roadmap.md
```

Write the rendered result to
`docs/superpowers/progress/2026-07-10-aitp-runtime-capability-audit.md` using the
project atomic text writer. Confirm the report is read-only and contains every
file row.

- [x] **Step 13: Commit Task 1**

```powershell
git add brain/v5/runtime_audit.py brain/v5/runtime_audit_rendering.py brain/v5/runtime_audit_contracts.py tests/test_v5_runtime_audit.py docs/superpowers/progress/2026-07-10-aitp-runtime-capability-audit.md docs/superpowers/plans/2026-07-10-aitp-gate-0-foundation.md
git commit -m "v5: add runtime capability audit"
```

## Task 2: RecordFamilySpec Registry

**Files:**
- Create: `brain/v5/record_family_registry.py`
- Create: `brain/v5/record_family_contracts.py`
- Create: `tests/test_v5_record_family_registry.py`
- Create: `docs/superpowers/progress/2026-07-10-aitp-record-family-registry.md`
- Modify: `brain/v5/paths.py`
- Modify: `brain/v5/record_refs.py`
- Modify: `brain/v5/workspace_inventory.py`
- Modify: `brain/v5/lifecycle_events.py`

**Interfaces:**
- Produces: `RecordFamilySpec(family, record_kind, record_class, id_field, relative_dir, exact_ref_aliases, lifecycle_policy, index_fields, auto_write_policy, participates_in)`
- Produces: `record_family_specs() -> dict[str, RecordFamilySpec]`
- Produces: `validate_record_family_registry() -> dict[str, Any]`
- Consumes: the live Task 1 drift report.

- [x] **Step 1: Write failing registry completeness tests**

```python
from brain.v5.record_family_registry import record_family_specs


def test_every_writable_family_has_path_ref_and_inventory_contract():
    specs = record_family_specs()
    assert "claims" in specs
    assert "source_assets" in specs
    assert "monitor_snapshots" in specs
    for family, spec in specs.items():
        assert spec.family == family
        assert spec.relative_dir
        assert spec.id_field
        assert "exact_ref" in spec.participates_in
        assert "inventory" in spec.participates_in


def test_registry_contains_every_literal_registry_family():
    audit = build_runtime_capability_audit(REPO_ROOT)
    assert set(audit["record_families"]["literal_uses"]) <= set(record_family_specs())
```

The test module imports `Path`, `build_runtime_capability_audit`, and defines:

```python
REPO_ROOT = Path(__file__).resolve().parents[1]
```

- [x] **Step 2: Verify RED**

Run:

```powershell
python -m pytest tests\test_v5_record_family_registry.py -q -p no:cacheprovider --basetemp tmp\pytest-g0-family-red
```

Expected: import failure for `record_family_registry`.

- [x] **Step 3: Implement the immutable spec and current-family catalog**

```python
@dataclass(frozen=True)
class RecordFamilySpec:
    family: str
    record_kind: str
    record_class: type[Any] | None
    id_field: str
    relative_dir: str
    exact_ref_aliases: tuple[str, ...] = ()
    lifecycle_policy: str = "append_revision"
    index_fields: tuple[str, ...] = ()
    auto_write_policy: str = "reviewed"
    participates_in: frozenset[str] = frozenset({"exact_ref", "inventory"})
```

Populate the catalog from actual writers and the live report. Include special
paths for sessions, topics, and `memory/l2/entries` without pretending they are
normal `registry/` families.

- [x] **Step 4: Run registry tests and verify GREEN**

Run the Step 2 command.

Expected: all registry tests pass.

- [x] **Step 5: Write failing consumer-convergence tests**

Assert `paths`, `record_refs`, and workspace inventory expose the same normal
registry families as `record_family_specs()`, excluding only documented special
locations.

- [x] **Step 6: Verify RED, then migrate consumers one at a time**

Replace duplicated family lists with registry-derived helpers. Preserve current
public constants as compatibility projections where tests import them.

- [x] **Step 7: Run focused consumers and architecture tests**

```powershell
python -m pytest tests\test_v5_record_family_registry.py tests\test_v5_workspace_inventory.py tests\test_v5_recording_navigator.py tests\test_v5_architecture_boundaries.py -q -p no:cacheprovider --basetemp tmp\pytest-g0-family-green
```

Expected: family/consumer tests pass; pre-existing unrelated oversized-module
failures may remain until Task 9 and must be reported exactly.

- [x] **Step 8: Commit Task 2**

```powershell
git add brain/v5/record_family_registry.py brain/v5/record_family_contracts.py brain/v5/paths.py brain/v5/record_refs.py brain/v5/workspace_inventory.py brain/v5/lifecycle_events.py brain/v5/runtime_audit.py tests/test_v5_record_family_registry.py tests/test_v5_runtime_audit.py docs/superpowers/progress/2026-07-10-aitp-record-family-registry.md docs/superpowers/progress/2026-07-10-aitp-runtime-capability-audit.md docs/superpowers/plans/2026-07-10-aitp-gate-0-foundation.md
git commit -m "v5: centralize record family registry"
```

## Task 3: RecordEnvelope Compatibility Layer

**Files:**
- Create: `brain/v5/record_envelope.py`
- Create: `brain/v5/record_envelope_audit.py`
- Create: `tests/test_v5_record_envelope.py`
- Create: `tests/test_v5_record_envelope_audit.py`
- Create: `docs/superpowers/progress/2026-07-10-aitp-record-envelope-compatibility.md`
- Modify: `brain/v5/record_family_registry.py`
- Modify: `brain/v5/record_family_contracts.py`

**Interfaces:**
- Produces: `RecordEnvelope`
- Produces: `envelope_for_record(record, *, family, actor, timestamp=None) -> RecordEnvelope`
- Produces: `canonical_record_hash(frontmatter: Mapping[str, Any], body: str) -> str`
- Produces: `read_envelope_compat(frontmatter, family_spec, path) -> RecordEnvelope`

- [x] **Step 1: Write failing hash and schema-v1 compatibility tests**

```python
def test_envelope_hash_is_stable_for_key_order():
    left = canonical_record_hash({"kind": "claim", "claim_id": "c1"}, "# Claim\n")
    right = canonical_record_hash({"claim_id": "c1", "kind": "claim"}, "# Claim\n")
    assert left == right


def test_schema_v1_record_gets_compatibility_envelope(tmp_path):
    envelope = read_envelope_compat(
        {"claim_id": "c1", "topic_id": "t1", "kind": "claim"},
        record_family_specs()["claims"],
        tmp_path / "c1.md",
    )
    assert envelope.record_id == "c1"
    assert envelope.schema_version == "v1-compat"
    assert envelope.trust_effect == "trust_path_input"
```

- [x] **Step 2: Verify RED**

Run:

```powershell
python -m pytest tests\test_v5_record_envelope.py -q -p no:cacheprovider --basetemp tmp\pytest-g0-envelope-red
```

Expected: import failure for `record_envelope`.

- [x] **Step 3: Implement stable hashing and compatibility envelopes**

Use sorted JSON-compatible frontmatter normalization and SHA-256. Exclude no
scientific fields. Compatibility envelopes derive ids and scopes from
`RecordFamilySpec`, use file mtime only as an explicitly labeled fallback
creation timestamp, and never write the derived fallback into canonical files.

- [x] **Step 4: Add actor/revision/trust-effect validation tests**

Require actor type in `human|model|tool|migration`, positive revisions,
registered family, non-empty hash, and trust effect in
`none|candidate_only|trust_path_input`.

- [x] **Step 5: Run envelope and representative model tests**

```powershell
python -m pytest tests\test_v5_record_envelope.py tests\test_v5_kernel.py -q -p no:cacheprovider --basetemp tmp\pytest-g0-envelope-green
```

Expected: all selected tests pass.

- [x] **Step 5a: Audit every real registry record through the compatibility layer**

Add a bounded, read-only audit that reports checked, loaded, and malformed
counts separately. Verify YAML `date` values, generic schema-v1 `id`/`topic`
fields, and family-specific legacy ID fields without rewriting canonical
Markdown. Record the measured full-store result and wall-clock baseline in the
progress report.

- [x] **Step 6: Commit Task 3**

```powershell
git add brain/v5/record_envelope.py brain/v5/record_envelope_audit.py brain/v5/record_family_registry.py brain/v5/record_family_contracts.py tests/test_v5_record_envelope.py tests/test_v5_record_envelope_audit.py tests/test_v5_record_family_registry.py docs/superpowers/progress/2026-07-10-aitp-record-envelope-compatibility.md docs/superpowers/plans/2026-07-10-aitp-gate-0-foundation.md
git commit -m "v5: add record envelope compatibility"
```

## Task 4: RecordRepository Safe Canonical Access

**Files:**
- Create: `brain/v5/record_repository.py`
- Create: `brain/v5/record_repository_contracts.py`
- Create: `tests/test_v5_record_repository.py`
- Modify: `brain/v5/store.py`
- Modify: `brain/v5/markdown.py`
- Modify: `brain/v5/references.py`

**Interfaces:**
- Produces: `WritePolicy(mode="create_or_idempotent" | "revision", expected_hash="")`
- Produces: `WriteResult(status, record_ref, path, content_hash, previous_hash="")`
- Produces: `RecordReadReport(records, checked_count, loaded_count, malformed, missing)`
- Produces: `RecordRepository.write(...)`, `.read(...)`, and `.list(...)`.

- [x] **Step 1: Write failing idempotency and collision tests**

```python
def test_repository_same_content_is_idempotent(tmp_path):
    repo = _repository(tmp_path)
    first = repo.write("claims", CLAIM, body="# Claim\n")
    second = repo.write("claims", CLAIM, body="# Claim\n")
    assert first.status == "created"
    assert second.status == "unchanged"


def test_repository_rejects_same_id_with_different_content(tmp_path):
    repo = _repository(tmp_path)
    repo.write("claims", CLAIM, body="# Claim\n")
    changed = replace(CLAIM, statement="different")
    with pytest.raises(RecordCollisionError):
        repo.write("claims", changed, body="# Changed\n")
```

- [x] **Step 2: Verify RED**

Run:

```powershell
python -m pytest tests\test_v5_record_repository.py -q -p no:cacheprovider --basetemp tmp\pytest-g0-repository-red
```

Expected: import failure for `record_repository`.

- [x] **Step 3: Implement create-or-idempotent writes with atomic lock files**

Resolve paths through `RecordFamilySpec`, compute canonical hash before write,
acquire a family/id lock under `.aitp/runtime/locks`, compare existing content,
and call the existing atomic Markdown writer only for creation. Always release
the lock in `finally`.

- [x] **Step 4: Add malformed-read reporting test**

```python
def test_repository_list_reports_malformed_record(tmp_path):
    repo = _repository(tmp_path)
    bad = tmp_path / ".aitp" / "registry" / "claims" / "bad.md"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text("---\nclaim_id: [\n---\n", encoding="utf-8")
    report = repo.list("claims")
    assert report.checked_count == 1
    assert report.loaded_count == 0
    assert report.malformed[0].path == str(bad)
```

- [x] **Step 5: Verify RED, then implement strict read reports**

Do not catch-and-drop parse or constructor errors. Return path, family, error
type, and message. Keep the old `list_valid_records` only as an explicitly
legacy compatibility function and document it as unsuitable for exhaustive
queries.

- [x] **Step 6: Add revision and compare-and-swap tests**

Test explicit supersession, expected-hash mismatch, stale lock cleanup policy,
and concurrent same-content creation.

- [x] **Step 7: Migrate one low-risk writer**

Migrate `record_reference_location` or another low-risk orientation/process
writer selected by the live audit. Preserve its public return type and body.

- [x] **Step 8: Run repository, writer, and record-ref tests**

```powershell
python -m pytest tests\test_v5_record_repository.py tests\test_v5_reference_locations.py tests\test_v5_adapters.py -q -p no:cacheprovider --basetemp tmp\pytest-g0-repository-green
```

Expected: all selected tests pass.

The persisted repository-integrity field is `record_content_hash`, not
`content_hash`. This avoids colliding with domain fields such as
`SourceAssetRecord.content_hash`, which denotes source bytes and remains part
of the scientific record payload.

- [x] **Step 9: Commit Task 4**

```powershell
git add brain/v5/record_repository.py brain/v5/record_repository_contracts.py brain/v5/store.py brain/v5/markdown.py brain/v5/paths.py brain/v5/record_envelope.py brain/v5/references.py tests/test_v5_record_repository.py tests/test_v5_record_envelope.py tests/test_v5_reference_locations.py docs/superpowers/progress/2026-07-10-aitp-record-repository.md docs/superpowers/progress/2026-07-10-aitp-runtime-capability-audit.md docs/superpowers/specs/2026-07-10-aitp-final-research-operating-memory-design.md docs/superpowers/plans/2026-07-10-aitp-gate-0-foundation.md
git commit -m "v5: add safe record repository"
```

## Task 5: Generation-Stamped Query Index And Retrieval

**Files:**
- Create: `brain/v5/query_index.py`
- Create: `brain/v5/query_index_contracts.py`
- Create: `brain/v5/research_retrieval.py`
- Create: `brain/v5/retrieval_audit.py`
- Create: `tests/test_v5_query_index.py`
- Create: `tests/test_v5_research_retrieval.py`
- Modify: `brain/v5/paths.py`
- Modify: `brain/v5/record_repository.py`

**Interfaces:**
- Produces: `IndexManifest`, `IndexBuildReport`, `ResearchQuery`,
  `RetrievalResult`, and `RetrievalCoverage`.
- Produces: `build_query_index(ws)`, `load_query_index(ws)`,
  `query_records(ws, query)`, and `exact_expand(ws, refs, limit=50)`.

- [x] **Step 1: Write failing deterministic-index test**

Create claims and source records in two insertion orders, build indexes, and
assert identical manifest content hash, sorted record refs, family counts, and
canonical watermark.

- [x] **Step 2: Verify RED**

```powershell
python -m pytest tests\test_v5_query_index.py -q -p no:cacheprovider --basetemp tmp\pytest-g0-index-red
```

Expected: import failure for `query_index`.

- [x] **Step 3: Implement deterministic metadata/lexical index files**

Use `RecordRepository` read reports. Persist a manifest plus normalized document
rows and inverted lexical terms under `.aitp/indexes`. Include generation,
canonical watermark, family counts, malformed records, build timestamp, and
manifest hash. Index build never writes canonical records.

- [x] **Step 4: Write failing stale-index and partial-coverage tests**

After index build, create a new canonical record and assert query result reports
`index_status="stale"`, `coverage.exhaustive=False`, and forbids absolute
no-result language.

- [x] **Step 5: Implement freshness and coverage**

Compare the canonical watermark against manifest state. Query exact refs through
the repository even when the index is stale. Metadata/lexical searches return
stale diagnostics and checked/unchecked families.

- [x] **Step 6: Write failing exact, filter, and lexical retrieval tests**

Cover topic/family/status filters, exact refs, deterministic lexical ranking,
pagination, truncation, malformed-record propagation, and excluded candidates.

- [x] **Step 7: Implement retrieval and audit payload**

Keep ranking transparent: exact score, lexical score, scope filter, lifecycle
filter, and stable tie-break id. `retrieval_audit.py` creates a trust-neutral
persistable payload but does not write it during Gate 0.

- [x] **Step 8: Run query tests and a real-store read-only benchmark**

```powershell
python -m pytest tests\test_v5_query_index.py tests\test_v5_research_retrieval.py -q -p no:cacheprovider --basetemp tmp\pytest-g0-index-green
```

Expected: all selected tests pass. Record index-build and query timings against
the real store without modifying canonical files.

- [x] **Step 9: Commit Task 5**

```powershell
git add brain/v5/query_index.py brain/v5/query_index_contracts.py brain/v5/research_retrieval.py brain/v5/retrieval_audit.py brain/v5/paths.py brain/v5/record_repository.py tests/test_v5_query_index.py tests/test_v5_research_retrieval.py docs/superpowers/progress/2026-07-10-aitp-indexed-retrieval.md docs/superpowers/progress/2026-07-10-aitp-runtime-capability-audit.md docs/superpowers/plans/2026-07-09-aitp-final-research-lifecycle-roadmap.md docs/superpowers/plans/2026-07-10-aitp-gate-0-foundation.md
git commit -m "v5: add indexed research retrieval"
```

## Task 6: Unified Context Compiler And Exact Expansion

**Files:**
- Create: `brain/v5/context_compiler.py`
- Create: `brain/v5/context_compiler_contracts.py`
- Create: `brain/v5/context_pack_projection.py`
- Create: `brain/v5/indexed_topic_snapshot.py`
- Create: `brain/v5/research_timeline_time.py`
- Create: `tests/test_v5_context_compiler.py`
- Create: `tests/test_v5_context_performance.py`
- Create: `tests/fixtures/v5_context_10000_fixture.json`
- Modify: `brain/v5/context_pack.py`
- Modify: `brain/v5/context_pack_contracts.py`
- Modify: `brain/v5/active_claim_focus.py`
- Modify: `brain/v5/objective_graph.py`
- Modify: `brain/v5/research_distillation.py`
- Modify: `brain/v5/claim_relation_map.py`
- Modify: `brain/v5/research_timeline.py`
- Modify: `brain/v5/codex_facade.py`
- Modify: `brain/v5/mcp_tools.py`
- Modify: `brain/v5/query_index.py`
- Modify: `brain/v5/record_repository.py`
- Modify: `brain/v5/research_retrieval.py`
- Modify: `brain/v5/retrieval_audit.py`

**Interfaces:**
- Produces: `ContextRequest`, `ContextBundle`,
  `compile_research_context(ws, request)`, and compact `record_refs` expansion.

- [x] **Step 1: Write a failing no-whole-store-rescan test**

Inject a counting repository/query index into the compiler and assert compact
context uses one query plan rather than invoking independent full-family scans
from compact brief, relation map, and distillation.

- [x] **Step 2: Verify RED**

```powershell
python -m pytest tests\test_v5_context_compiler.py -q -p no:cacheprovider --basetemp tmp\pytest-g0-context-red
```

Expected: import failure for `context_compiler`.

- [x] **Step 3: Implement ContextRequest and bounded compilation**

Compile objective, current boundary, recent process refs, candidate summaries,
coverage, errors, and expansion handles from one retrieval result. Estimate
tokens deterministically and enforce both token and byte limits.

- [x] **Step 4: Add failing stale/read-error/truncation contract tests**

Assert context reports partial coverage, cannot claim no prior result, and
requires exact expansion before trust-sensitive conclusions.

- [x] **Step 5: Implement contracts and compact facade `record_refs` expansion**

Add `record_refs` to the allowed expansion names with bounded refs and page size.
Keep full record bodies out of the default context.

- [x] **Step 6: Migrate context builders incrementally**

Add query-backed paths to context pack, objective graph, relation map, timeline,
and distillation while preserving old public function signatures. Remove old
whole-store fallbacks only after parity tests pass.

- [x] **Step 7: Run context/facade/parity tests**

```powershell
python -m pytest tests\test_v5_context_compiler.py tests\test_v5_context_pack.py tests\test_v5_codex_facade.py tests\test_v5_claim_relation_map.py tests\test_v5_research_timeline.py -q -p no:cacheprovider --basetemp tmp\pytest-g0-context-green
```

Expected: all selected tests pass.

- [x] **Step 8: Run 10,000-record performance acceptance**

Measure cold/warm minimal entry, normal expansion, exact ref lookup, context
bytes/tokens, and full-scan count. Fail the performance test if warm minimal
entry is at least 1 second, cold minimal entry at least 3 seconds, normal warm
expansion at least 2 seconds, or exact-ref lookup at least 250 milliseconds.

- [x] **Step 9: Commit Task 6**

```powershell
git add brain/v5/context_compiler.py brain/v5/context_compiler_contracts.py brain/v5/context_pack.py brain/v5/context_pack_contracts.py brain/v5/context_pack_projection.py brain/v5/indexed_topic_snapshot.py brain/v5/research_timeline_time.py brain/v5/active_claim_focus.py brain/v5/objective_graph.py brain/v5/research_distillation.py brain/v5/claim_relation_map.py brain/v5/research_timeline.py brain/v5/codex_facade.py brain/v5/query_index.py brain/v5/record_repository.py brain/v5/research_retrieval.py brain/v5/retrieval_audit.py tests/test_v5_context_compiler.py tests/test_v5_context_performance.py tests/fixtures/v5_context_10000_fixture.json docs/superpowers/progress/2026-07-10-aitp-context-compiler.md docs/superpowers/plans/2026-07-09-aitp-final-research-lifecycle-roadmap.md docs/superpowers/plans/2026-07-10-aitp-gate-0-foundation.md
git commit -m "v5: compile context from indexed queries"
```

## Task 7: Bounded Host Autoroute Injection

**Files:**
- Modify: `deploy/hooks/aitp-keyword-router.py`
- Modify: `deploy/templates/claude-code/aitp-keyword-router.py`
- Modify: `tests/test_aitp_pm_deploy_surfaces.py`
- Create: `brain/v5/compact_context_boundary.py`
- Create: `brain/v5/topic_status_startup.py`
- Modify: `brain/v5/topic_status.py`
- Modify: `brain/v5/topic_status_contracts.py`
- Modify: `brain/v5/workspace_refresh.py`
- Modify: `brain/v5/workspace_refresh_contracts.py`
- Create: `tests/test_v5_context_injection_budget.py`
- Create: `docs/superpowers/progress/2026-07-10-aitp-bounded-host-injection.md`

**Interfaces:**
- Produces a bounded route hint with matched signal, candidate topic ids/titles,
  base path, compact facade entrypoint, and no topic-memory bodies.

- [x] **Step 1: Write failing no-memory-body and UTF-8 tests**

Create two topics with large `MEMORY.md` files, invoke the deployed router with a
Chinese theoretical-physics request, and assert output includes topic ids but
none of either memory body. Assert the serialized additional context stays under
4,096 bytes.

- [x] **Step 2: Verify RED**

```powershell
python -m pytest tests\test_aitp_pm_deploy_surfaces.py tests\test_v5_context_injection_budget.py -q -p no:cacheprovider --basetemp tmp\pytest-g0-router-red
```

Expected: current router leaks memory text or exceeds the byte budget.

- [x] **Step 3: Remove memory reads and fix keyword encoding**

Keep state/topic title and a short question excerpt. Replace mojibake literals
with valid UTF-8 Chinese strings already used by tests. Emit only autoroute and
exact-expansion instructions.

- [x] **Step 4: Add session-start consistency test**

Assert generated topic status and workspace startup use the same compact context
fingerprint/coverage boundary and remain orientation-only.

- [x] **Step 5: Run router/startup tests**

```powershell
python -m pytest tests\test_aitp_pm_deploy_surfaces.py tests\test_v5_context_injection_budget.py tests\test_v5_topic_status.py tests\test_v5_workspace_refresh.py -q -p no:cacheprovider --basetemp tmp\pytest-g0-router-green
```

Expected: all selected tests pass.

- [x] **Step 6: Commit Task 7**

```powershell
git add deploy/hooks/aitp-keyword-router.py deploy/templates/claude-code/aitp-keyword-router.py brain/v5/compact_context_boundary.py brain/v5/topic_status.py brain/v5/topic_status_contracts.py brain/v5/topic_status_startup.py brain/v5/workspace_refresh.py brain/v5/workspace_refresh_contracts.py tests/test_aitp_pm_deploy_surfaces.py tests/test_v5_context_injection_budget.py docs/superpowers/progress/2026-07-10-aitp-bounded-host-injection.md docs/superpowers/plans/2026-07-09-aitp-final-research-lifecycle-roadmap.md docs/superpowers/plans/2026-07-10-aitp-gate-0-foundation.md
git commit -m "v5: bound host research context injection"
```

## Task 8: CapabilitySpec Registry

**Files:**
- Create: `brain/v5/capability_registry.py`
- Create: `brain/v5/capability_registry_data.py`
- Create: `brain/v5/capability_registry_contracts.py`
- Create: `brain/v5/capability_surface_contracts.py`
- Create: `brain/v5/mcp_capabilities.py`
- Create: `tests/test_v5_capability_registry.py`
- Create: `docs/superpowers/progress/2026-07-10-aitp-capability-registry.md`
- Modify: `brain/v5/mcp_tools.py`
- Modify: `brain/v5/public_surfaces.py`
- Modify: `brain/v5/runtime_entrypoint_catalog.py`
- Modify: `brain/v5/runtime_bridge_targets.py`
- Modify: `brain/v5/codex_facade.py`

**Interfaces:**
- Produces: `CapabilitySpec(operation, mcp_name, cli_route, public_surface, state_effect, compact_visibility, bridge_target)`
- Produces: `capability_specs() -> dict[str, CapabilitySpec]`
- Produces: `audit_capability_registry() -> dict[str, Any]`

- [x] **Step 1: Write failing parity tests**

Assert every runtime entrypoint MCP name exists in `mcp_tools`, every declared
surface exists in public surfaces, compact operations are allowlisted, and no
operation has conflicting state effects.

- [x] **Step 2: Verify RED**

```powershell
python -m pytest tests\test_v5_capability_registry.py -q -p no:cacheprovider --basetemp tmp\pytest-g0-capability-red
```

Expected: import failure for `capability_registry`.

- [x] **Step 3: Implement the registry for Gate 0 capabilities first**

Register runtime audit, index build/status, exact retrieval, context compile,
and compact exact expansion. Add adapters that validate existing catalogs
without deleting compatibility constants.

- [x] **Step 4: Expand the registry to all current public runtime operations**

Use the Task 1 audit to add every current operation. Record explicit
`compact|full|hidden` visibility and `read_only|runtime_write|kernel_write`
state effect. Resolve each mismatch rather than suppressing it.

- [x] **Step 5: Run public/bridge/adapter parity tests**

```powershell
python -m pytest tests\test_v5_capability_registry.py tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py tests\test_v5_runtime_mcp_bridge_acceptance.py tests\test_v5_adapters.py -q -p no:cacheprovider --basetemp tmp\pytest-g0-capability-green
```

Expected: all selected tests pass.

- [x] **Step 6: Commit Task 8**

```powershell
git add brain/v5/capability_registry.py brain/v5/capability_registry_data.py brain/v5/capability_registry_contracts.py brain/v5/capability_surface_contracts.py brain/v5/mcp_capabilities.py brain/v5/runtime_entrypoint_catalog.py brain/v5/runtime_bridge_targets.py brain/v5/codex_facade.py tests/test_v5_capability_registry.py tests/test_v5_public_surfaces.py docs/superpowers/progress/2026-07-10-aitp-capability-registry.md docs/superpowers/plans/2026-07-09-aitp-final-research-lifecycle-roadmap.md docs/superpowers/plans/2026-07-10-aitp-gate-0-foundation.md
# Stage only reviewed Task 8 hunks from the already-dirty mcp_tools.py and
# public_surfaces.py through an explicit git apply --cached patch.
git commit -m "v5: centralize runtime capability registry"
```

## Task 9: Restore Module Boundaries And Gate 0 Release Audit

**Files:**
- Create: `brain/v5/mcp_query.py`
- Create: `brain/v5/mcp_context.py`
- Create: `brain/v5/cli_query.py`
- Create: `brain/v5/cli_context.py`
- Create: `tests/test_v5_gate0_release.py`
- Create: `docs/superpowers/progress/2026-07-10-aitp-gate-0-release-audit.md`
- Modify: `brain/v5/mcp_tools.py`
- Modify: `brain/v5/process_graph.py`
- Modify: `brain/v5/codex_facade.py`
- Modify: `brain/v5/cli.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/public_surfaces.py`
- Modify: `tests/test_v5_architecture_boundaries.py`

**Interfaces:**
- Produces focused compatibility modules and a Gate 0 release audit.

- [ ] **Step 1: Capture current architecture failures as the RED baseline**

Run:

```powershell
python -m pytest tests\test_v5_architecture_boundaries.py -q -p no:cacheprovider --basetemp tmp\pytest-g0-architecture-red
```

Expected: the test reports the exact oversized modules. Save the list in the
Gate 0 progress audit.

- [ ] **Step 2: Split Gate 0 MCP and CLI responsibilities**

Move query/index wrappers to `mcp_query.py`, context wrappers to
`mcp_context.py`, query CLI dispatch to `cli_query.py`, and context dispatch to
`cli_context.py`. Re-export public wrapper names so native MCP discovery remains
stable.

- [ ] **Step 3: Split process-graph, facade, model, and surface responsibilities**

Use the architecture failure list and CapabilitySpec dependencies to extract
focused loaders/renderers/contracts. Each extraction must have a characterization
test before moving code and must preserve existing public imports.

- [ ] **Step 4: Run architecture and broad Gate 0 tests after each extraction**

```powershell
python -m pytest tests\test_v5_architecture_boundaries.py tests\test_v5_runtime_audit.py tests\test_v5_record_family_registry.py tests\test_v5_record_repository.py tests\test_v5_query_index.py tests\test_v5_context_compiler.py tests\test_v5_capability_registry.py -q -p no:cacheprovider --basetemp tmp\pytest-g0-architecture-green
```

Expected: all selected tests pass without changed size limits.

- [ ] **Step 5: Run the Gate 0 compatibility matrix**

Add current record refs, workspace inventory, context pack, relation map,
timeline, Codex facade, public surface, runtime entrypoint, bridge, adapter,
topic status, workspace refresh, and deployed-router tests to the command. Split
the command into named CI lanes when its runtime exceeds two minutes.

- [ ] **Step 6: Run real-store read-only performance and integrity audit**

Build the derived index, run representative exact/filter/lexical/context
queries, verify latency budgets, list malformed records, and prove no canonical
file content hash changed.

- [ ] **Step 7: Update docs and write the release audit**

Document the canonical/derived boundary, RecordRepository write rules, index
rebuild, compact context, performance budgets, known migration gaps, rollback,
and the exact test commands/results.

- [ ] **Step 8: Verify docs and staged diff**

```powershell
git diff --check -- .
python -m compileall brain\v5
```

Expected: no whitespace errors and successful compilation.

- [ ] **Step 9: Commit Task 9**

```powershell
git add brain/v5/mcp_query.py brain/v5/mcp_context.py brain/v5/cli_query.py brain/v5/cli_context.py tests/test_v5_gate0_release.py docs/superpowers/progress/2026-07-10-aitp-gate-0-release-audit.md docs/superpowers/plans/2026-07-10-aitp-gate-0-foundation.md
git commit -m "v5: complete Gate 0 research-memory foundation"
```

## Gate 0 Completion Checklist

- [ ] Runtime audit covers every source, hook, test, actual family, writer, and host surface.
- [ ] Record-family drift is zero or explicitly classified in the release audit.
- [ ] Existing schema-v1 records remain readable.
- [ ] Conflicting same-id writes are rejected; identical writes are idempotent.
- [ ] Malformed canonical records are reported and block exhaustive recall claims.
- [ ] Derived indexes are generation stamped, disposable, and freshness checked.
- [ ] Exact refs, filtered retrieval, lexical retrieval, and coverage are tested.
- [ ] Context builders no longer independently scan the whole store on the indexed path.
- [ ] Startup and one normal expansion meet the stated latency and token/byte budgets.
- [ ] The deployed keyword router never injects topic memory bodies.
- [ ] Capability parity is generated and compact visibility is explicit.
- [ ] Architecture tests pass without relaxed limits.
- [ ] Real-store read-only audit proves no canonical rewrite or trust inflation.
- [ ] The architecture spec, final roadmap, Gate 0 plan, and Gate 0 release audit agree.
