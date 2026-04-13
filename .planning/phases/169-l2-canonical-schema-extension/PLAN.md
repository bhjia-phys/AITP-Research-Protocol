# Plan: 169-01 — Add negative_result to canonical-unit.schema.json and create runtime proof schemas

**Phase:** 169
**Axis:** Axis 3 (schema evolution) + Axis 2 (inter-layer connection)
**Requirements:** REQ-PROMO-01, REQ-PROMO-02

## Goal

Extend the canonical schema so every unit type that can reach L4 has a valid
promotion path, and formalize the three runtime proof schemas that currently
exist only as ad-hoc Python dicts.

## Context

Two Jones E2E runs validated at L4 (Lean compilation succeeded) but could not
promote to L2 because:

1. `canonical-unit.schema.json` does not include `negative_result` in its
   `unit_type` enum — validated but negative outcomes have no staging→canonical
   path
2. runtime proof artifacts (`lean-ready-packet`, `proof-repair-plan`,
   `statement-compilation-packet`) exist as Python dicts in validation/ but
   have no formal JSON schemas and no promotion path into canonical L2

## Steps

### Step 1: Add `negative_result` to canonical-unit.schema.json

**File:** `research/knowledge-hub/canonical/canonical-unit.schema.json`

- Find the `unit_type` enum array
- Add `"negative_result"` as a new enum value
- Add a corresponding description in any `$comment` or description field
- Verify the change does not break existing canonical units that use the other
  enum values

**Verification:**
- `python -c "import json; s = json.load(open('research/knowledge-hub/canonical/canonical-unit.schema.json')); assert 'negative_result' in s['properties']['unit_type']['enum']"`
- existing canonical units still validate against the schema

### Step 2: Create `lean-ready-packet.schema.json`

**File:** `research/knowledge-hub/schemas/lean-ready-packet.schema.json`

Define a JSON schema with at minimum:
- `statement_id` (string) — the theorem/lemma identifier
- `lean_code` (string) — the Lean 4 source code
- `compilation_status` (enum: `success`, `error`, `timeout`)
- `dependencies` (array of strings) — prerequisite statement IDs
- `source_ref` (string) — path to the source artifact this was derived from
- `promoted_from` (string, const: `"lean-ready-packet"`) — runtime schema tag

### Step 3: Create `proof-repair-plan.schema.json`

**File:** `research/knowledge-hub/schemas/proof-repair-plan.schema.json`

Define a JSON schema with at minimum:
- `statement_id` (string)
- `error_diagnosis` (string) — what went wrong in compilation
- `repair_strategy` (enum: `tactic_adjustment`, `lemma_introduction`, `type_correction`, `abandon`)
- `attempted_repairs` (array of objects with `strategy`, `result`, `timestamp`)
- `source_ref` (string)
- `promoted_from` (string, const: `"proof-repair-plan"`)

### Step 4: Create `statement-compilation-packet.schema.json`

**File:** `research/knowledge-hub/schemas/statement-compilation-packet.schema.json`

Define a JSON schema with at minimum:
- `statement_id` (string)
- `statement_type` (enum: `theorem`, `lemma`, `definition`, `example`)
- `formalization_source` (string) — the informal statement this was derived from
- `compilation_trace` (string) — full Lean compiler output
- `source_ref` (string)
- `promoted_from` (string, const: `"statement-compilation-packet"`)

### Step 5: Register schemas in schema registry

Ensure the three new schemas are discoverable by the promotion pipeline. Check
if there is a schema index or registry file that needs updating, and add the new
schemas to it.

**Verification:**
- all three schema files pass `jsonschema.validate()` against a sample artifact
- schema registry (if exists) lists the new schemas

## Must Do

- Keep the existing `canonical-unit.schema.json` structure unchanged except for
  the enum addition
- Each runtime proof schema must include `promoted_from` as a discriminator
  field so the promotion bridge can identify the source schema type
- Each schema must include `source_ref` for traceability

## Must Not Do

- Do not modify existing canonical units or promotion policy
- Do not change the validation layer's runtime artifact format
- Do not add dependencies on external schema libraries

## Evidence

- [ ] `canonical-unit.schema.json` contains `negative_result` in `unit_type` enum
- [ ] `lean-ready-packet.schema.json` exists and validates a sample artifact
- [ ] `proof-repair-plan.schema.json` exists and validates a sample artifact
- [ ] `statement-compilation-packet.schema.json` exists and validates a sample
  artifact
- [ ] existing canonical units still validate against the updated schema
