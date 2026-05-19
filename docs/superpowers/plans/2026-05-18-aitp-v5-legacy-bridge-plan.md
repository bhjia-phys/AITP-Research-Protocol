# AITP v5 Legacy Bridge Migration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate legacy AITP topics into v5 typed records through explicit dry-run and write steps, without treating old files as continuing truth sources.

**Architecture:** Legacy files are read as provenance and migration input. The v5 kernel writes new typed records; after migration, execution should use v5 records rather than legacy compatibility reads. Generated migration summaries remain orientation-only.

**Tech Stack:** Python standard library, pathlib, Markdown+YAML store, pytest.

---

## File Responsibility Map

- `brain/v5/legacy_bridge.py`: scan, dry-run audit, explicit seed/migration functions.
- `brain/v5/references.py`: reference locations for old source paths and external notes.
- `brain/v5/evidence.py`: evidence records for legacy sources and reviews.
- `brain/v5/validation.py`: validation contracts/results when old L4 reviews are imported.
- `tests/test_v5_legacy_bridge.py`: migration behavior.
- `tests/test_v5_real_workflows.py`: workflow-level acceptance after migration.

## Task 1: Dry-Run Reports What Will Be Preserved

**Files:**
- Modify: `tests/test_v5_legacy_bridge.py`
- Modify: `brain/v5/legacy_bridge.py`

- [ ] **Step 1: Write the failing test**

```python
def test_legacy_topic_dry_run_maps_candidates_and_reviews(tmp_path):
    from brain.v5.legacy_bridge import audit_legacy_topic_migration

    topic = tmp_path / "old-topic"
    (topic / "L0" / "sources" / "paper-a").mkdir(parents=True)
    (topic / "L1").mkdir()
    (topic / "L3" / "candidates").mkdir(parents=True)
    (topic / "L4" / "reviews").mkdir(parents=True)
    (topic / "state.md").write_text("---\ntitle: Old Topic\n---\n# State\n", encoding="utf-8")
    (topic / "L0" / "sources" / "paper-a" / "source.md").write_text("# Paper A\n", encoding="utf-8")
    (topic / "L1" / "question_contract.md").write_text("# Question\n", encoding="utf-8")
    (topic / "L1" / "source_basis.md").write_text("# Sources\n", encoding="utf-8")
    (topic / "L3" / "candidates" / "candidate-a.md").write_text("# Candidate A\n", encoding="utf-8")
    (topic / "L4" / "reviews" / "review-a.md").write_text("# Review A\n", encoding="utf-8")

    audit = audit_legacy_topic_migration(topic)

    assert audit["can_write_v5_records"] is True
    assert audit["mapped_paths"]["L3/candidates/candidate-a.md"] == "claim/candidate seed"
    assert audit["mapped_paths"]["L4/reviews/review-a.md"] == "validation evidence candidate"
    assert audit["summary_inputs_trusted"] is False
```

- [ ] **Step 2: Run red**

```powershell
pytest tests\test_v5_legacy_bridge.py::test_legacy_topic_dry_run_maps_candidates_and_reviews -q
```

Expected: fail until L3/L4 mapping is reported.

- [ ] **Step 3: Implement read-only mapping**

Map:

```text
L0/sources/*/source.md -> reference_location/source evidence candidate
L1/source_basis.md -> source basis/evidence orientation
L3/candidates/*.md -> claim/candidate seed
L4/reviews/*.md -> validation evidence candidate
```

Do not write `.aitp` files inside the dry-run function.

## Task 2: Explicit Migration Writes v5 Records

**Files:**
- Modify: `tests/test_v5_legacy_bridge.py`
- Modify: `brain/v5/legacy_bridge.py`

- [ ] **Step 1: Write the failing test**

```python
def test_explicit_legacy_migration_writes_v5_records_without_rewriting_legacy(tmp_path):
    from brain.v5.legacy_bridge import migrate_legacy_topic_to_v5
    from brain.v5.workspace import init_workspace

    legacy = _write_legacy_topic(tmp_path / "legacy")
    before = (legacy / "state.md").read_text(encoding="utf-8")
    ws = init_workspace(tmp_path / "v5")

    result = migrate_legacy_topic_to_v5(ws, legacy, context_id="legacy-context", session_id="s1")

    assert (legacy / "state.md").read_text(encoding="utf-8") == before
    assert result["kind"] == "legacy_topic_migration_result"
    assert result["summary_inputs_trusted"] is False
    assert result["written_records"]["claims"]
    assert result["written_records"]["evidence"]
```

- [ ] **Step 2: Run red**

```powershell
pytest tests\test_v5_legacy_bridge.py::test_explicit_legacy_migration_writes_v5_records_without_rewriting_legacy -q
```

Expected: fail because explicit migration result is not implemented.

- [ ] **Step 3: Implement explicit migration**

Use existing kernel functions such as `create_context`, `create_topic`, `create_claim`, `record_evidence`, and `record_reference_location`. Return record IDs only; do not copy entire legacy files into frontmatter.

## Task 3: Migration Verification

**Files:**
- Modify only files touched by Tasks 1-2.

- [ ] **Step 1: Run focused checks**

```powershell
pytest tests\test_v5_legacy_bridge.py tests\test_v5_real_workflows.py -q
python -m compileall -q brain\v5
git diff --check -- .
```

Expected: all pass.

- [ ] **Step 2: Commit and push**

```powershell
git add brain/v5/legacy_bridge.py tests/test_v5_legacy_bridge.py tests/test_v5_real_workflows.py
git commit -m "feat(v5): migrate legacy topics into typed records"
git push origin codex/aitp-v5-kernel-mvp
git push origin HEAD:main
```
