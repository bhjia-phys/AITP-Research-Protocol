# Plan: 169.1-01 — Add runtime schema loading and bridging to all three promotion support modules

**Phase:** 169.1
**Axis:** Axis 2 (inter-layer connection) + Axis 3 (data recording)
**Requirements:** REQ-PROMO-03, REQ-PROMO-04, REQ-PROMO-05, REQ-PROMO-06

## Goal

Wire the three promotion support modules to load and forward runtime schema
context during L4→L2 promotion, and create a dedicated bridge module that
translates runtime proof artifacts into canonical L2 units.

## Context

Phase 169 created the schemas. This phase wires them into the promotion
pipeline so the schemas are actually used during promotion decisions.

The three promotion support modules each have a specific gap:

- `candidate_promotion_support.py` `_resolve_promotion_context()` (lines 170-230):
  does not load runtime schemas — promotion context is incomplete
- `auto_promotion_support.py` `_validate_auto_promotion()` (lines 58-105):
  does not check runtime schema validity — auto-promotion may approve
  artifacts without proof schema fields
- `promotion_gate_support.py` `request_promotion()` (lines 214-281):
  does not include runtime schema paths in the gate payload — downstream
  consumers cannot verify promotion provenance

## Steps

### Step 1: Create `runtime_schema_promotion_bridge.py`

**File:** `research/knowledge-hub/knowledge_hub/runtime_schema_promotion_bridge.py`

Create a new module that:
- loads all runtime proof schemas from `research/knowledge-hub/schemas/`
- provides a `translate_to_canonical(runtime_artifact: dict) -> dict` function
  that maps runtime fields to canonical fields
- provides a `validate_runtime_artifact(artifact: dict) -> bool` function that
  checks an artifact against its `promoted_from` schema
- handles `lean-ready-packet`, `proof-repair-plan`, and
  `statement-compilation-packet` artifact types
- raises `ValueError` for unknown artifact types

**Key implementation detail:**
```python
def translate_to_canonical(runtime_artifact: dict) -> dict:
    """Map runtime proof artifact fields to canonical L2 unit fields."""
    schema_type = runtime_artifact.get("promoted_from")
    if schema_type == "lean-ready-packet":
        return {
            "unit_type": "proof_fragment",
            "statement_id": runtime_artifact["statement_id"],
            "content": runtime_artifact["lean_code"],
            "compilation_status": runtime_artifact["compilation_status"],
            "source_ref": runtime_artifact["source_ref"],
        }
    elif schema_type == "proof-repair-plan":
        return {
            "unit_type": "negative_result",
            "statement_id": runtime_artifact["statement_id"],
            "diagnosis": runtime_artifact["error_diagnosis"],
            "repair_strategy": runtime_artifact["repair_strategy"],
            "source_ref": runtime_artifact["source_ref"],
        }
    # ... statement-compilation-packet mapping
```

### Step 2: Update `candidate_promotion_support.py`

**File:** `research/knowledge-hub/knowledge_hub/candidate_promotion_support.py`

In `_resolve_promotion_context()` (around lines 170-230):
- import `runtime_schema_promotion_bridge`
- after loading the existing promotion context, check if the candidate has a
  `promoted_from` field indicating a runtime schema origin
- if yes, call `runtime_schema_promotion_bridge.validate_runtime_artifact()`
  and include the validation result and schema path in the returned context

### Step 3: Update `auto_promotion_support.py`

**File:** `research/knowledge-hub/knowledge_hub/auto_promotion_support.py`

In `_validate_auto_promotion()` (around lines 58-105):
- import `runtime_schema_promotion_bridge`
- add a check: if the candidate has `promoted_from`, verify it passes
  `validate_runtime_artifact()` before approving auto-promotion
- if validation fails, set auto-promotion to denied with a clear reason

### Step 4: Update `promotion_gate_support.py`

**File:** `research/knowledge-hub/knowledge_hub/promotion_gate_support.py`

In `request_promotion()` (around lines 214-281):
- import `runtime_schema_promotion_bridge`
- when building the gate payload, include `runtime_schema_path` and
  `runtime_schema_type` fields if the candidate has a `promoted_from` field
- this allows downstream consumers to verify the promotion provenance

## Must Do

- Keep all changes additive — do not modify existing function signatures
- Use `promoted_from` field as the discriminator for runtime schema artifacts
- Each module change should be a small, targeted addition (≤20 lines per file)
- All new code must have docstrings

## Must Not Do

- Do not refactor existing promotion logic beyond the targeted additions
- Do not change the canonical promotion policy or PROMOTION_POLICY.md
- Do not add new CLI commands (that's Phase 169.2)
- Do not modify the validation layer's artifact generation code

## Evidence

- [ ] `runtime_schema_promotion_bridge.py` exists and translates all 3 artifact
  types
- [ ] `candidate_promotion_support.py` loads runtime schema context
- [ ] `auto_promotion_support.py` validates runtime schema before auto-promotion
- [ ] `promotion_gate_support.py` includes runtime schema paths in gate payload
- [ ] existing promotion tests still pass
