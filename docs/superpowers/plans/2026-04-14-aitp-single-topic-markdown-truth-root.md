# AITP Single-Topic Markdown Truth-Root Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce `topics/<topic_slug>/` as the AITP topic truth root, relocate key runtime/layer helper paths under it, and generate Markdown companion truth surfaces for the most important runtime projections.

**Architecture:** Centralize topic-root path derivation in the service and helper modules, then move service-owned writes to the topic root while preserving compatibility JSON projections where the runtime still requires them. Use Markdown companion files with frontmatter to keep truth surfaces human-readable without breaking current machine readers.

**Tech Stack:** Python, Markdown with YAML frontmatter, unittest, existing AITP runtime helpers

---

### Task 1: Add failing path-layout tests

**Files:**
- Create: `research/knowledge-hub/tests/test_topic_truth_root_layout.py`

- [ ] **Step 1: Write the failing test**

```python
def test_service_uses_topic_root_for_runtime_and_layer_paths(self) -> None:
    service = AITPService(kernel_root=self.kernel_root, repo_root=self.repo_root)
    self.assertEqual(
        service._relativize(service._runtime_root("demo-topic")),
        "topics/demo-topic/runtime",
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest research/knowledge-hub/tests/test_topic_truth_root_layout.py -v`
Expected: FAIL because `_runtime_root()` still returns `runtime/topics/demo-topic`

- [ ] **Step 3: Write minimal implementation**

Update the service and helper modules so topic-scoped roots resolve under:

```python
self.kernel_root / "topics" / topic_slug / "runtime"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest research/knowledge-hub/tests/test_topic_truth_root_layout.py -v`
Expected: PASS

### Task 2: Add failing Markdown companion projection tests

**Files:**
- Modify: `research/knowledge-hub/tests/test_runtime_profiles_and_projections.py`

- [ ] **Step 1: Write the failing test**

```python
self.assertTrue((self.runtime_root / "topic_synopsis.md").exists())
self.assertTrue((self.runtime_root / "pending_decisions.md").exists())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -k "projects_pending_decisions" -v`
Expected: FAIL because only JSON projections exist

- [ ] **Step 3: Write minimal implementation**

Add Markdown writers in the runtime projection handler for:

```python
topic_synopsis.md
pending_decisions.md
promotion_readiness.md
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -k "projects_pending_decisions" -v`
Expected: PASS

### Task 3: Add topic-manifest scaffolding

**Files:**
- Modify: `research/knowledge-hub/knowledge_hub/aitp_service.py`
- Create: `research/knowledge-hub/tests/test_topic_truth_root_layout.py`

- [ ] **Step 1: Write the failing test**

```python
self.assertTrue((self.kernel_root / "topics" / "demo-topic" / "topic_manifest.md").exists())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest research/knowledge-hub/tests/test_topic_truth_root_layout.py -v`
Expected: FAIL because no topic manifest is created

- [ ] **Step 3: Write minimal implementation**

Create the topic root and manifest during topic-shell setup:

```python
topic_root.mkdir(parents=True, exist_ok=True)
(topic_root / "topic_manifest.md").write_text(...)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest research/knowledge-hub/tests/test_topic_truth_root_layout.py -v`
Expected: PASS

### Task 4: Update current-topic runtime-root reporting

**Files:**
- Modify: `research/knowledge-hub/tests/test_runtime_path_hygiene_contracts.py`
- Modify: `research/knowledge-hub/knowledge_hub/aitp_service.py`

- [ ] **Step 1: Write the failing test**

```python
self.assertEqual(payload["runtime_root"], f"topics/{payload['topic_slug']}/runtime")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest research/knowledge-hub/tests/test_runtime_path_hygiene_contracts.py -v`
Expected: FAIL because current-topic memory still emits `runtime/topics/...`

- [ ] **Step 3: Write minimal implementation**

Update current-topic memory materialization to report:

```python
"runtime_root": self._relativize(self._runtime_root(topic_slug))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest research/knowledge-hub/tests/test_runtime_path_hygiene_contracts.py -v`
Expected: PASS

### Task 5: Verify the migration slice

**Files:**
- Modify: `docs/PROJECT_INDEX.md`

- [ ] **Step 1: Run targeted verification**

Run: `python -m pytest research/knowledge-hub/tests/test_topic_truth_root_layout.py research/knowledge-hub/tests/test_runtime_path_hygiene_contracts.py research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -v`
Expected: PASS for the migration slice

- [ ] **Step 2: Update docs**

Document the new root:

```md
`topics/<slug>/runtime/`
```

- [ ] **Step 3: Re-run verification**

Run: `python -m pytest research/knowledge-hub/tests/test_topic_truth_root_layout.py research/knowledge-hub/tests/test_runtime_path_hygiene_contracts.py research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -v`
Expected: PASS
