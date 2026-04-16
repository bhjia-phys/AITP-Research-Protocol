# Global L2 Reuse And Capability Plane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a global reusable `L2` read system, a runtime capability plane, and progressive `L3` reuse contexts so `L3` can plan from explicit reusable knowledge and explicit executable resources.

**Architecture:** Keep canonical `L2` authoritative and global, add derived Markdown mirrors and progressive topic-scoped reuse-context artifacts, and introduce a separate runtime capability plane for tools, servers, environments, and workflows. Wire the new derived contexts into topic-shell and runtime-bundle generation so `L3` planning surfaces can consume bounded read packs instead of free-form memory.

**Tech Stack:** Python, JSON, Markdown, unittest/pytest, existing AITP runtime helpers

---

### Task 1: Lock the new protocol surfaces with failing contract tests

**Files:**
- Create: `research/knowledge-hub/tests/test_capability_plane_contracts.py`
- Modify: `research/knowledge-hub/tests/test_runtime_path_hygiene_contracts.py`
- Modify: `research/knowledge-hub/tests/test_aitp_service.py`

- [ ] **Step 1: Write the failing capability-plane contract test**

```python
def test_write_runtime_capability_card_materializes_registry_and_markdown(self) -> None:
    payload = self.service.write_runtime_capability_card(
        capability_kind="server",
        capability_id="server:el",
        title="EL HPC server",
        summary="Remote Slurm host for backend-heavy numerical runs.",
        declaration_source="human_text",
        properties={
            "host_alias": "el",
            "scheduler": "slurm",
            "allowed_workloads": ["first_principles", "code_method"],
        },
        updated_by="test",
    )
    self.assertEqual(payload["capability_kind"], "server")
    self.assertTrue(Path(payload["json_path"]).exists())
    self.assertTrue(Path(payload["markdown_path"]).exists())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest research/knowledge-hub/tests/test_capability_plane_contracts.py -q`
Expected: FAIL because the capability-plane service path does not exist yet

- [ ] **Step 3: Write the failing reuse-context test**

```python
def test_ensure_topic_shell_surfaces_materializes_progressive_reuse_contexts(self) -> None:
    payload = self.service.ensure_topic_shell_surfaces(topic_slug="demo-topic", updated_by="test")
    self.assertIn("idea_reuse_context", payload)
    self.assertIn("plan_reuse_context", payload)
    self.assertIn("execution_resource_context", payload)
```

- [ ] **Step 4: Run test to verify it fails**

Run: `python -m pytest research/knowledge-hub/tests/test_aitp_service.py -k "progressive_reuse_contexts" -q`
Expected: FAIL because the topic shell does not yet expose those surfaces

- [ ] **Step 5: Add the hygiene expectation**

```python
for snippet in (
    "research/knowledge-hub/runtime/capabilities/",
    "research/knowledge-hub/canonical/compiled/obsidian_l2/",
):
    self.assertIn(snippet, gitignore_text)
```

- [ ] **Step 6: Run the hygiene test to verify it fails**

Run: `python -m pytest research/knowledge-hub/tests/test_runtime_path_hygiene_contracts.py -q -k "gitignore"`
Expected: FAIL because the new local-only generated surfaces are not yet declared

### Task 2: Build the runtime capability plane

**Files:**
- Create: `research/knowledge-hub/knowledge_hub/capability_plane_support.py`
- Modify: `research/knowledge-hub/knowledge_hub/aitp_service.py`
- Modify: `research/knowledge-hub/tests/test_capability_plane_contracts.py`

- [ ] **Step 1: Write the failing natural-language intake test**

```python
def test_record_runtime_capability_declaration_preserves_human_text_and_normalizes_card(self) -> None:
    payload = self.service.record_runtime_capability_declaration(
        capability_kind="server",
        declaration_text="EL can run LibRPA/QSGW via slurm and should be used for backend-heavy numerical jobs.",
        capability_id="server:el",
        title="EL HPC server",
        updated_by="test",
    )
    self.assertEqual(payload["card"]["declaration_source"], "natural_language")
    self.assertIn("slurm", payload["card"]["declaration_text"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest research/knowledge-hub/tests/test_capability_plane_contracts.py -q -k "natural_language"`
Expected: FAIL because the declaration helper does not exist yet

- [ ] **Step 3: Write minimal capability-plane implementation**

```python
def write_runtime_capability_card(...):
    card = {
        "capability_kind": capability_kind,
        "capability_id": capability_id,
        "title": title,
        "summary": summary,
        "declaration_source": declaration_source,
        "properties": dict(properties or {}),
    }
```

- [ ] **Step 4: Add registry + Markdown mirror generation**

```python
registry = {
    "generated_at": now_iso,
    "cards": sorted(card_rows, key=lambda row: row["capability_id"]),
}
```

- [ ] **Step 5: Add the service wrappers**

```python
def write_runtime_capability_card(self, *, capability_kind, capability_id, title, summary, declaration_source, properties, updated_by="aitp-cli"):
    return write_runtime_capability_card(...)
```

- [ ] **Step 6: Run the capability-plane tests**

Run: `python -m pytest research/knowledge-hub/tests/test_capability_plane_contracts.py -q`
Expected: PASS

### Task 3: Add topic-linked evidence support to reusable `L2` units and Obsidian mirrors

**Files:**
- Modify: `research/knowledge-hub/canonical/canonical-unit.schema.json`
- Modify: `research/knowledge-hub/tests/test_schema_contracts.py`
- Modify: `research/knowledge-hub/knowledge_hub/l2_compiler.py`
- Modify: `research/knowledge-hub/tests/test_l2_compiler.py`

- [ ] **Step 1: Write the failing schema contract test**

```python
unit_props = payload["properties"]
self.assertIn("origin_topic_refs", unit_props)
self.assertIn("validation_receipts", unit_props)
self.assertIn("reuse_receipts", unit_props)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest research/knowledge-hub/tests/test_schema_contracts.py -q -k "topic_linked_evidence"`
Expected: FAIL because the canonical-unit schema does not expose those fields

- [ ] **Step 3: Extend the canonical-unit schema with optional evidence-link fields**

```json
"origin_topic_refs": { "type": "array", "items": { "type": "string" } },
"validation_receipts": { "type": "array", "items": { "type": "string" } },
"reuse_receipts": { "type": "array", "items": { "type": "string" } }
```

- [ ] **Step 4: Write the failing Obsidian-mirror compiler test**

```python
self.assertTrue((compiled_root / "obsidian_l2" / "index.md").exists())
self.assertTrue((compiled_root / "obsidian_l2" / "families" / "methods").exists())
```

- [ ] **Step 5: Run test to verify it fails**

Run: `python -m pytest research/knowledge-hub/tests/test_l2_compiler.py -q -k "obsidian_l2"`
Expected: FAIL because the fixed-folder Markdown mirror is not generated yet

- [ ] **Step 6: Implement the Markdown mirror in the compiler**

```python
obsidian_root = canonical_root / "compiled" / "obsidian_l2"
(obsidian_root / "families" / family_dir).mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 7: Re-run the schema + compiler tests**

Run: `python -m pytest research/knowledge-hub/tests/test_schema_contracts.py research/knowledge-hub/tests/test_l2_compiler.py -q`
Expected: PASS

### Task 4: Materialize `idea_reuse_context` and `plan_reuse_context`

**Files:**
- Create: `research/knowledge-hub/knowledge_hub/l2_reuse_context_support.py`
- Modify: `research/knowledge-hub/knowledge_hub/topic_shell_support.py`
- Modify: `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py`
- Modify: `research/knowledge-hub/tests/test_aitp_service.py`
- Modify: `research/knowledge-hub/tests/test_runtime_profiles_and_projections.py`

- [ ] **Step 1: Write the failing service test**

```python
idea = payload["idea_reuse_context"]
self.assertEqual(idea["read_depth"], "quick")
self.assertTrue(idea["canonical_hits"])
self.assertIn("authority_level", idea["canonical_hits"][0])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest research/knowledge-hub/tests/test_aitp_service.py -q -k "idea_reuse_context"`
Expected: FAIL because no reuse-context surface exists yet

- [ ] **Step 3: Write the failing runtime-bundle test**

```python
must_read_paths = {row["path"] for row in bundle["must_read_now"]}
self.assertIn("topics/demo-topic/runtime/idea_reuse_context.md", must_read_paths)
```

- [ ] **Step 4: Run test to verify it fails**

Run: `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -q -k "idea_reuse_context"`
Expected: FAIL because the runtime bundle does not surface the new context

- [ ] **Step 5: Implement bounded reuse-context generation**

```python
consult_payload = consult_canonical_l2(
    service.kernel_root,
    query_text=query_text,
    retrieval_profile="l3_candidate_formation",
    include_staging=True,
    topic_slug=topic_slug,
)
```

- [ ] **Step 6: Split quick and standard projections**

```python
idea_context = {"read_depth": "quick", ...}
plan_context = {"read_depth": "standard", ...}
```

- [ ] **Step 7: Wire them into topic-shell and runtime-bundle payloads**

```python
"idea_reuse_context": idea_reuse_context,
"plan_reuse_context": plan_reuse_context,
```

- [ ] **Step 8: Run the targeted reuse-context slice**

Run: `python -m pytest research/knowledge-hub/tests/test_aitp_service.py research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -q -k "reuse_context"`
Expected: PASS

### Task 5: Materialize `execution_resource_context` and bind it to `L3` planning surfaces

**Files:**
- Modify: `research/knowledge-hub/knowledge_hub/capability_plane_support.py`
- Modify: `research/knowledge-hub/knowledge_hub/topic_shell_support.py`
- Modify: `research/knowledge-hub/knowledge_hub/iteration_journal_support.py`
- Modify: `research/knowledge-hub/tests/test_aitp_service.py`

- [ ] **Step 1: Write the failing resource-context test**

```python
resource = payload["execution_resource_context"]
self.assertEqual(resource["recommended_server"]["capability_id"], "server:el")
self.assertEqual(resource["recommended_environment"]["capability_id"], "environment:el-librpa")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest research/knowledge-hub/tests/test_aitp_service.py -q -k "execution_resource_context"`
Expected: FAIL because the topic shell does not yet derive resource recommendations

- [ ] **Step 3: Write the failing plan-contract assertion**

```python
plan_payload = json.loads(plan_path.read_text(encoding="utf-8"))
self.assertIn("server_ref", plan_payload)
self.assertIn("tool_refs", plan_payload)
self.assertIn("environment_ref", plan_payload)
```

- [ ] **Step 4: Run test to verify it fails**

Run: `python -m pytest research/knowledge-hub/tests/test_aitp_service.py -q -k "plan_contract"`
Expected: FAIL because plan contracts still stop at executor/runtime hints

- [ ] **Step 5: Implement resource-context derivation**

```python
recommended = {
    "recommended_server": best_server,
    "recommended_environment": best_environment,
    "tool_refs": [row["capability_id"] for row in matched_tools],
}
```

- [ ] **Step 6: Bind explicit refs into iteration plans**

```python
"server_ref": resource_context.get("recommended_server", {}).get("capability_id", ""),
"environment_ref": resource_context.get("recommended_environment", {}).get("capability_id", ""),
"tool_refs": resource_context.get("recommended_tool_ids", []),
```

- [ ] **Step 7: Run the planning slice**

Run: `python -m pytest research/knowledge-hub/tests/test_aitp_service.py -q -k "execution_resource_context or plan_contract"`
Expected: PASS

### Task 6: Verify and document the integrated slice

**Files:**
- Modify: `.planning/ROADMAP.md`
- Modify: `research/knowledge-hub/runtime/README.md`
- Modify: `docs/PROJECT_INDEX.md`

- [ ] **Step 1: Run the integrated verification slice**

Run: `python -m pytest research/knowledge-hub/tests/test_capability_plane_contracts.py research/knowledge-hub/tests/test_schema_contracts.py research/knowledge-hub/tests/test_l2_compiler.py research/knowledge-hub/tests/test_runtime_path_hygiene_contracts.py research/knowledge-hub/tests/test_runtime_profiles_and_projections.py research/knowledge-hub/tests/test_aitp_service.py -q`
Expected: PASS

- [ ] **Step 2: Run syntax verification**

Run: `python -m compileall research/knowledge-hub/knowledge_hub/capability_plane_support.py research/knowledge-hub/knowledge_hub/l2_reuse_context_support.py research/knowledge-hub/knowledge_hub/topic_shell_support.py research/knowledge-hub/knowledge_hub/runtime_bundle_support.py research/knowledge-hub/knowledge_hub/iteration_journal_support.py`
Expected: PASS with no syntax errors

- [ ] **Step 3: Update docs**

Document:

- the global `L2` Markdown mirror,
- the runtime capability plane,
- the new reuse-context artifacts,
- and the explicit resource refs in `L3` plan surfaces.

- [ ] **Step 4: Re-run the integrated verification slice**

Run: `python -m pytest research/knowledge-hub/tests/test_capability_plane_contracts.py research/knowledge-hub/tests/test_schema_contracts.py research/knowledge-hub/tests/test_l2_compiler.py research/knowledge-hub/tests/test_runtime_path_hygiene_contracts.py research/knowledge-hub/tests/test_runtime_profiles_and_projections.py research/knowledge-hub/tests/test_aitp_service.py -q`
Expected: PASS
