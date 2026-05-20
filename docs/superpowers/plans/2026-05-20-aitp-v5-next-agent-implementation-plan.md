# AITP v5 Next Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Advance AITP v5 from the current typed kernel MVP into a relation-aware theoretical-physics research harness with object/relation records, relation-aware briefs, validation scaffolding, L2 memory governance, and real workflow acceptance tests.

**Architecture:** Keep `brain/v5/` as the typed protocol kernel. CLI, MCP, adapters, hooks, summaries, and skills must remain thin surfaces over kernel functions. Generated summaries, external knowledge connectors, and reference locations are orientation-only; typed records remain authoritative.

**Tech Stack:** Python standard library, dataclasses, pathlib, Markdown+YAML store, pytest, PowerShell command shell on Windows, git worktree workflow.

---

## Current Baseline

Use this worktree unless explicitly told otherwise:

```text
C:\Users\samur\.config\superpowers\worktrees\AITP-Research-Protocol\aitp-v5-kernel-mvp
```

Branch:

```text
codex/aitp-v5-kernel-mvp
```

Current baseline commit:

```text
855a3e6 feat(v5): add pre-tool hook adapter, or a later completed commit from this plan
```

Current focused v5 verification:

```powershell
$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }
pytest $files -q
```

Expected baseline:

```text
318 passed
```

Do not treat old full-suite failures as blockers unless a task modifies legacy code. The v5 focused suite is the working regression gate for this plan.

## Non-Negotiable Protocol Invariants

Every task must preserve these rules:

- Typed records are truth sources. Summary files, generated plans, external notes, IMA/Zotero/Obsidian pointers, and adapter packets are not truth sources.
- `summary_inputs_trusted` must remain `False` for public surfaces that include generated or derived context.
- `ReferenceLocationRecord.orientation_only` must remain `True`; reference locations are pointers, not evidence.
- Any trust-changing action must go through kernel records and contract validation.
- CLI/MCP/runtime-adapter symmetry is required for public kernel capabilities unless the task explicitly says "kernel-only".
- Keep v5 modules focused. Do not turn `contracts.py`, `cli.py`, `mcp_tools.py`, or `brief.py` into monoliths. Add focused contract modules when needed.
- Use TDD for behavior changes: write failing focused tests, confirm red, implement minimal code, confirm green.
- Do not edit unrelated dirty files in the main checkout.
- Commit and push each coherent subfeature.

## Current Implementation Status

Implemented:

- Workspace layout and Markdown store.
- Context, topic, session, claim records.
- Execution brief with risk, flow profile, mandatory reflection, next action candidates, forbidden actions.
- Risk engine and action budgets.
- Dynamic question engine and question intents.
- Evidence records, tool recipes, tool runs, safe built-in tool executors.
- Formal-theory checklist executor for auditable definition, assumption, derivation-step, and counterexample-search checks.
- Code workspace and code state provenance.
- Trust cards and trust-update preflight/apply, including request-bound
  preflight proof tokens required before confidence-state mutation.
- Domain packs and executor recommendations.
- Knowledge connector catalog with IMA as optional example backend.
- Reference location records for external notes/PDFs/Zotero/IMA/Obsidian locations.
- Physics object and object-relation records.
- Relation-aware execution briefs and question intents using structured relation payloads.
- Local sense-making reports.
- Validation contracts and human checkpoint records.
- L2 promotion packets, memory entries, and promotion governance.
- Real FQHE and GW workflow acceptance tests.
- Session summaries as orientation-only derived files.
- CLI, MCP wrappers, public surface contracts, runtime entrypoints, adapter packets.
- Legacy bridge with dry-run audit, explicit v5 migration result, and CLI/MCP/runtime surface.
- Legacy migration converts old L3 candidates into v5 claims/evidence/sense-making reports and old L4 reviews into validation evidence.
- Legacy runtime logs migrate into v5 JSONL trace events as orientation process history.
- Legacy L1 source basis and convention snapshots migrate into v5 evidence plus sense-making reports.
- Legacy L1 derivation anchor maps and contradiction registers migrate into v5 evidence plus sense-making reports and appear in dry-run audit mapping.
- Legacy L1 question contracts and intake notes migrate into v5 evidence plus sense-making reports and appear in dry-run audit mapping.
- Legacy L2 entries, graph nodes, and graph edges migrate into v5 memory entries with `status=legacy_seed`, provenance refs, and review-required checkpoint markers.
- Legacy L0 source metadata anchors (`source_url`, PDF, DOI, arXiv, and note paths) migrate into orientation-only v5 reference locations and appear in dry-run audit mapping.
- Subagent auditor results ingest as typed evidence plus sense-making proposals, never direct confidence changes or L2 promotion.
- Harness audit/evolution skeleton.
- Hook helpers include machine-readable pre-commit, pre-tool, and post-tool shell adapters over kernel decisions and trace events.
- Hook installation contract is documented for Codex, Claude Code, and OpenCode.
- Adapter packets expose typed `runtime_hook_protocols` metadata for installer/runtime bridges.
- Adapter packets derive `runtime_hook_installation` templates from `runtime_hook_protocols`.
- Codex hook bridge instructions can be generated from `runtime_hook_installation`.
- Codex hook bridge instructions can be materialized from an actual adapter packet
  through CLI/MCP/runtime public surfaces.
- Post-tool hook trace events can be persisted from hook stdout through
  CLI/MCP/runtime public surfaces into `.aitp/runtime/hook_trace_events.jsonl`.
- Claude Code hook settings can be generated from an actual adapter packet, and
  the generated `PostToolUse` wrapper persists process trace events through the
  v5 trace bridge.
- Claude Code hook settings can be safely merged into an existing settings file
  without clobbering non-AITP hooks or duplicating AITP hook commands.
- Claude Code `PreToolUse` maps destructive, remote, and expensive Bash tool
  calls to a typed v5 policy block and Claude `permissionDecision=deny`.
- Claude Code `PreToolUse` maps coarse AITP MCP/kernel entrypoints into v5
  actions, denies unqualified direct trust application, and logs typed writes
  such as evidence recording.
- Claude Code `PreToolUse` uses active workspace context for validation and L2
  promotion MCP calls, reusing kernel policy for evidence and code-state
  requirements before tool execution.
- The same context-aware pre-tool policy is now exposed as a shared
  CLI/MCP/runtime public surface:
  `aitp-v5 policy pre-tool <args>` / `aitp_v5_evaluate_pre_tool_policy` /
  `pre_tool_policy_decision`.
- Generated Codex/OpenCode bridge payloads explicitly advertise that shared
  pre-tool policy entrypoint.
- `pre_tool_policy_decision` includes machine-readable `policy_reasons`, so
  denial/warn causes such as summary-sourced trust updates are auditable without
  parsing hook messages.
- Adapter packet gate protocols for `validate_claim` and `promote_to_l2`
  explicitly sequence `evaluate_pre_tool_policy` before preflight/promotion.
- Adapter packet gate protocols for `record_evidence` and `record_tool_run`
  now also sequence `evaluate_pre_tool_policy` before the record mutation, so
  summary-sourced record attempts can be blocked through bridge metadata.
- Generated Codex/OpenCode bridge payloads and Markdown now carry
  `gate_protocols` derived from `runtime_gate_protocols`, so adapter runtimes
  can consume record/validate/promote sequences without prose scraping.
- `brain.v5.adapter_runtime.evaluate_bridge_gate_pre_tool_policy` consumes
  generated bridge `gate_protocols` and delegates actual decisions to the shared
  typed-record-backed pre-tool policy surface. `evaluate_bridge_lifecycle_event`
  maps adapter-neutral `pre_tool` event payloads onto that helper.
- `brain.v5.adapter_runtime.evaluate_platform_pre_tool_event` normalizes
  Codex/OpenCode pre-tool platform payloads into that lifecycle wrapper for
  validation/promotion gate decisions.
- The platform pre-tool event normalizer is now available through
  CLI/MCP/runtime entrypoints:
  `aitp-v5 adapter pre-tool-event <runtime> <session-id> ...` /
  `aitp_v5_evaluate_adapter_pre_tool_event` /
  `pre_tool_policy_decision`.
- Generated Codex/OpenCode bridge payloads now advertise
  `pre_tool_event_entrypoint` metadata for that CLI/MCP runtime surface.
- Generated Codex/OpenCode bridge materializers now write a sibling JSON sidecar
  and return `payload_path`, so runtime hook runners can pass
  `--bridge-path <payload-path>` to the pre-tool event normalizer instead of
  scraping Markdown or embedding large bridge JSON.
- Generated Codex/OpenCode bridge payloads now include
  `pre_tool_event_runner.argv` with the concrete runtime/session sidecar-backed
  pre-tool event command vector.
- `hooks/aitp_v5_adapter_event_runner.py` provides a thin stdin host-runner for
  generated bridge sidecars: it validates runner metadata, fills
  runtime/session/pre-tool defaults, and returns the typed
  `pre_tool_policy_decision` payload plus hook exit code.
- Generated bridge sidecars now advertise the stdin host-runner command vector
  in `pre_tool_event_runner.stdin_runner.argv` or
  `plugin_bridge.pre_tool_event_runner.stdin_runner.argv`.
- Codex can now write a native-ish stdin-runner installation fixture through
  `aitp-v5 adapter install-hooks codex <session-id> --output <path>` and
  `aitp_v5_install_codex_hook_fixture`; the fixture writes the bridge/sidecar
  and points pre-tool events at the stdin runner.
- The shared CLI/MCP pre-tool policy now also blocks summary/task-plan/findings
  orientation surfaces from driving `record_evidence` and `record_tool_run`
  trust-changing record attempts.
- OpenCode plugin bridge instructions can be materialized from an actual adapter
  packet through CLI/MCP/runtime public surfaces.
- A v5 implementation ledger exists for step-by-step review.

Major remaining gaps:

- Hook helpers still need true native Codex/OpenCode lifecycle installer wiring.
  Codex explicit bridge materialization, Claude Code settings template
  generation and merge installation, OpenCode plugin bridge materialization, and
  post-tool trace persistence surfaces exist; Codex/OpenCode now have a
  CLI/MCP-callable runtime event normalizer advertised in generated bridges plus
  a generated bridge JSON sidecar, runner argv, advertised stdin host-runner;
  Codex also has a generated installation fixture, while OpenCode does not yet.
- Pre-tool policy coverage is still partial. It checks trust-apply token
  presence, validation/promotion context, and summary-sourced evidence/tool-run
  record attempts through CLI/MCP/runtime/bridge metadata, but it does not yet
  cover every MCP input or all active risk context.
- Domain tools are useful but intentionally lightweight; formal-theory checks are checklist/provenance checks, not automated theorem proving.
- Subagent packet planning and result ingestion exist, but live external-subagent execution adapters still need integration tests.
- Full legacy test suite remains a historical failure set outside the v5 regression gate.

## Execution Rules For Other AI Agents

Before starting any task:

```powershell
git status --short
git branch --show-current
git log --oneline -5
```

Expected:

```text
branch = codex/aitp-v5-kernel-mvp
working tree has no unrelated dirty v5 files
latest commit is f11b253 or a later commit from this plan
```

After each task:

```powershell
$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }
pytest $files -q
python -m compileall -q brain\v5
git diff --check -- .
git status --short
```

Expected:

```text
all v5 tests pass
compileall passes
git diff --check has no errors
only intentional files are dirty
```

Commit and push after each task:

```powershell
git add <changed-files>
git diff --cached --check -- .
git commit -m "<descriptive message>"
git push origin codex/aitp-v5-kernel-mvp
git fetch origin main
git push origin HEAD:main
```

Use fast-forward-safe main pushes only. Never use destructive git commands.

---

## File Responsibility Map For This Plan

Create or extend:

- `brain/v5/physics_objects.py`: kernel functions for physics object and object-relation records.
- `brain/v5/sensemaking.py`: local claim/object/relation sense-making reports.
- `brain/v5/validation.py`: validation contract and validation result records.
- `brain/v5/checkpoints.py`: human checkpoint request/decision records.
- `brain/v5/memory.py`: L2 memory entries and promotion packets.
- `tests/test_v5_physics_objects.py`: object and relation record tests.
- `tests/test_v5_sensemaking.py`: sense-making report tests.
- `tests/test_v5_validation.py`: validation and checkpoint tests.
- `tests/test_v5_memory.py`: L2 memory and promotion governance tests.
- `tests/test_v5_real_workflows.py`: realistic workflow acceptance tests.

Modify as needed:

- `brain/v5/models.py`: add dataclasses only; keep logic out.
- `brain/v5/paths.py`: add registry/memory directories.
- `brain/v5/brief.py`: add object/relation/reference/sensemaking context to `known_context` and next actions.
- `brain/v5/question_engine.py`: consume relation summaries.
- `brain/v5/question_intents.py`: add relation-aware intents only when tests require them.
- `brain/v5/record_contracts.py`: add write-record validators.
- `brain/v5/contracts.py`: stable re-export wrapper for validators.
- `brain/v5/public_surfaces.py`: public surface names and validators.
- `brain/v5/cli.py`: thin CLI calls.
- `brain/v5/cli_adapters.py`: adapter CLI dispatch helpers; use this instead
  of growing the main CLI module for adapter packet/bridge/hook commands.
- `brain/v5/mcp_tools.py`: thin MCP calls.
- `brain/v5/runtime_entrypoints.py`: CLI/MCP entrypoint registry.
- `brain/v5/adapter_protocols.py`: adapter runtime protocol metadata.
- `brain/v5/adapter_runtime.py`: small runtime helpers that consume generated
  adapter bridge payloads without treating bridge files as truth sources.
- `brain/v5/hook_bridge_markdown.py`: generated Codex/OpenCode bridge Markdown
  renderers; keep this separate from `hook_install_templates.py` so payload
  construction and rendering do not grow into a single large module.
- `brain/v5/hook_install_contracts.py`: host installation fixture contracts;
  keep these out of generic hook protocol contracts.
- `brain/v5/adapter_contracts.py`: only if adapter packet schema changes.
- `brain/v5/summaries.py`: only after typed records exist.

---

## Task 1: Reference Locations In Execution Brief

**Purpose:** Agents should see already-recorded external paper/note locations for the active claim before deciding whether to search again.

**Files:**

- Modify: `brain/v5/brief.py`
- Modify: `brain/v5/references.py`
- Test: `tests/test_v5_reference_locations.py`

- [ ] **Step 1: Write the failing test**

Append this test to `tests/test_v5_reference_locations.py`:

```python
def test_execution_brief_exposes_reference_locations_for_active_claim(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.references import record_reference_location
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Composite-fermion conventions should be compared with prior notes.",
        evidence_profile="literature_synthesis",
        confidence_state="learning",
        active_uncertainty="note and paper locations",
    )
    record_reference_location(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        connector_id="zotero",
        location_type="paper_pdf",
        uri="zotero://select/items/JAIN1989",
        label="Jain 1989 PDF",
        source_ref="paper:jain-1989",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)

    brief = build_execution_brief(ws, "s1")

    locations = brief["known_context"]["reference_locations"]
    assert locations == [
        {
            "location_id": locations[0]["location_id"],
            "connector_id": "zotero",
            "location_type": "paper_pdf",
            "uri": "zotero://select/items/JAIN1989",
            "label": "Jain 1989 PDF",
            "source_ref": "paper:jain-1989",
            "orientation_only": True,
        }
    ]
```

- [ ] **Step 2: Run red**

```powershell
pytest tests\test_v5_reference_locations.py::test_execution_brief_exposes_reference_locations_for_active_claim -q
```

Expected:

```text
FAIL with KeyError: 'reference_locations'
```

- [ ] **Step 3: Implement minimal brief support**

In `brain/v5/references.py`, add:

```python
def reference_location_brief_payload(location: ReferenceLocationRecord) -> dict:
    return {
        "location_id": location.location_id,
        "connector_id": location.connector_id,
        "location_type": location.location_type,
        "uri": location.uri,
        "label": location.label,
        "source_ref": location.source_ref,
        "orientation_only": location.orientation_only,
    }
```

In `brain/v5/brief.py`, import:

```python
from brain.v5.references import list_reference_locations_for_claim, reference_location_brief_payload
```

Inside `build_execution_brief`, initialize:

```python
reference_locations = []
```

When `claim` exists, add:

```python
reference_locations = [
    reference_location_brief_payload(location)
    for location in list_reference_locations_for_claim(ws, claim.claim_id)
]
```

Inside `known_context`, add:

```python
"reference_locations": reference_locations,
```

- [ ] **Step 4: Verify green**

```powershell
pytest tests\test_v5_reference_locations.py -q
```

Expected:

```text
all tests in file pass
```

- [ ] **Step 5: Run focused regression**

```powershell
pytest tests\test_v5_reference_locations.py tests\test_v5_contracts.py tests\test_v5_adapters.py -q
```

Expected: all pass.

- [ ] **Step 6: Commit**

```powershell
git add brain/v5/brief.py brain/v5/references.py tests/test_v5_reference_locations.py
git commit -m "feat: surface reference locations in briefs"
```

---

## Task 2: Physics Object Records

**Purpose:** AITP needs typed records for physical/mathematical objects such as Hamiltonians, operators, Hilbert spaces, sectors, Green functions, self-energies, and algebras.

**Files:**

- Create: `brain/v5/physics_objects.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/paths.py`
- Modify: `brain/v5/record_contracts.py`
- Modify: `brain/v5/contracts.py`
- Modify: `brain/v5/public_surfaces.py`
- Modify: `brain/v5/cli.py`
- Modify: `brain/v5/mcp_tools.py`
- Modify: `brain/v5/runtime_entrypoints.py`
- Modify: `brain/v5/adapter_protocols.py`
- Test: `tests/test_v5_physics_objects.py`
- Test: `tests/test_v5_public_surfaces.py`

- [ ] **Step 1: Write failing kernel/public-surface test**

Create `tests/test_v5_physics_objects.py`:

```python
from __future__ import annotations

from dataclasses import asdict
import json


def test_record_physics_object_persists_typed_record(tmp_path):
    from brain.v5.markdown import read_md
    from brain.v5.physics_objects import record_physics_object
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")

    obj = record_physics_object(
        ws,
        topic_id="fqhe",
        object_type="hilbert_sector",
        name="N=8 Lz=28 sector",
        definition="Many-body Hilbert sector used for finite-size FQHE counting.",
        notation="H_{N=8,Lz=28}",
        assumptions=["lowest Landau level", "fixed particle number"],
        source_refs=["paper:fqhe-counting"],
        metadata={"N": 8, "Lz": 28},
    )

    fm, body = read_md(ws.registry_dir("physics_objects") / f"{obj.object_id}.md")
    assert obj.kind == "physics_object"
    assert obj.object_id.startswith("physics-object-")
    assert fm["object_type"] == "hilbert_sector"
    assert fm["assumptions"] == ["lowest Landau level", "fixed particle number"]
    assert "Many-body Hilbert sector" in body


def test_physics_object_record_is_public_surface_valid(tmp_path):
    from brain.v5.physics_objects import record_physics_object
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="formal-theory", title="Quantum Gravity")
    obj = record_physics_object(
        ws,
        topic_id="qg",
        object_type="von_neumann_algebra",
        name="Local algebra A(O)",
        definition="Operator algebra associated with a spacetime region.",
    )

    payload = {"ok": True, **asdict(obj)}
    assert require_valid_public_surface("physics_object_record", payload) == payload
```

- [ ] **Step 2: Run red**

```powershell
pytest tests\test_v5_physics_objects.py::test_record_physics_object_persists_typed_record tests\test_v5_physics_objects.py::test_physics_object_record_is_public_surface_valid -q
```

Expected:

```text
FAIL because brain.v5.physics_objects does not exist
```

- [ ] **Step 3: Add dataclass and path**

In `brain/v5/models.py`, add:

```python
@dataclass
class PhysicsObjectRecord:
    object_id: str
    topic_id: str
    object_type: str
    name: str
    definition: str
    notation: str = ""
    assumptions: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    linked_records: dict = field(default_factory=dict)
    status: str = "active"
    kind: str = "physics_object"
```

In `brain/v5/paths.py`, ensure `_LAYOUT_DIRS` contains:

```python
"registry/physics_objects",
```

It may already exist; do not duplicate it.

- [ ] **Step 4: Implement kernel function**

Create `brain/v5/physics_objects.py`:

```python
"""Physics object and relation records for AITP v5."""

from __future__ import annotations

from brain.v5.ids import prefixed_id
from brain.v5.models import PhysicsObjectRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_records, write_record


def record_physics_object(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    object_type: str,
    name: str,
    definition: str,
    notation: str = "",
    assumptions: list[str] | None = None,
    source_refs: list[str] | None = None,
    metadata: dict | None = None,
    linked_records: dict | None = None,
    status: str = "active",
) -> PhysicsObjectRecord:
    object_id = prefixed_id("physics-object", f"{topic_id}:{object_type}:{name}", max_slug=64)
    record = PhysicsObjectRecord(
        object_id=object_id,
        topic_id=topic_id,
        object_type=object_type,
        name=name,
        definition=definition,
        notation=notation,
        assumptions=assumptions or [],
        source_refs=source_refs or [],
        metadata=metadata or {},
        linked_records=linked_records or {},
        status=status,
    )
    write_record(
        ws.registry_dir("physics_objects") / f"{object_id}.md",
        record,
        body=f"# Physics Object: {name}\n\n{definition}\n",
    )
    return record


def list_physics_objects_for_topic(ws: WorkspacePaths, topic_id: str) -> list[PhysicsObjectRecord]:
    return [
        obj
        for obj in list_records(ws.registry_dir("physics_objects"), PhysicsObjectRecord)
        if obj.topic_id == topic_id
    ]
```

- [ ] **Step 5: Add public surface validation**

In `brain/v5/record_contracts.py`, add a validator:

```python
def validate_physics_object_record(payload: dict[str, Any], *, path: str = "physics_object_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="physics_object")
    if result.issues:
        return result
    for key in ("object_id", "topic_id", "object_type", "name", "definition", "status"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("assumptions", "source_refs"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    for key in ("metadata", "linked_records"):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
    return result


def require_valid_physics_object_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_physics_object_record(payload), payload)
```

In `brain/v5/contracts.py`, add wrapper functions mirroring other record wrappers:

```python
def validate_physics_object_record(payload: dict[str, Any], *, path: str = "physics_object_record") -> ContractResult:
    from brain.v5.record_contracts import validate_physics_object_record as _validate_physics_object_record

    return _validate_physics_object_record(payload, path=path)


def require_valid_physics_object_record(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.record_contracts import require_valid_physics_object_record as _require_valid_physics_object_record

    return _require_valid_physics_object_record(payload)
```

In `brain/v5/public_surfaces.py`, add:

```python
"physics_object_record",
```

and purpose:

```python
"physics_object_record": "contracted physics-object record for theoretical objects, systems, operators, sectors, and definitions",
```

and validator mapping:

```python
"physics_object_record": require_valid_physics_object_record,
```

Update `tests/test_v5_public_surfaces.py` expected surface set with `"physics_object_record"`.

- [ ] **Step 6: Verify kernel/public-surface green**

```powershell
pytest tests\test_v5_physics_objects.py tests\test_v5_public_surfaces.py -q
```

Expected: all pass.

- [ ] **Step 7: Add CLI/MCP tests**

Append to `tests/test_v5_physics_objects.py`:

```python
def test_cli_physics_object_record_returns_json(tmp_path, capsys):
    from brain.v5.cli import main

    assert main(
        [
            "--base",
            str(tmp_path),
            "object",
            "record",
            "--topic",
            "fqhe",
            "--type",
            "hilbert_sector",
            "--name",
            "N=8 sector",
            "--definition",
            "Finite-size Hilbert sector.",
            "--notation",
            "H_8",
            "--assumption",
            "lowest Landau level",
            "--source-ref",
            "paper:fqhe",
            "--metadata-json",
            '{"N":8}',
        ]
    ) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["kind"] == "physics_object"
    assert payload["object_type"] == "hilbert_sector"
    assert payload["metadata"] == {"N": 8}


def test_mcp_record_physics_object_returns_valid_surface(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_record_physics_object
    from brain.v5.public_surfaces import require_valid_public_surface

    payload = aitp_v5_record_physics_object(
        str(tmp_path),
        topic_id="qg",
        object_type="algebra",
        name="A(O)",
        definition="Local operator algebra.",
    )

    assert payload["ok"] is True
    assert require_valid_public_surface("physics_object_record", payload) == payload
```

- [ ] **Step 8: Run CLI/MCP tests red**

```powershell
pytest tests\test_v5_physics_objects.py::test_cli_physics_object_record_returns_json tests\test_v5_physics_objects.py::test_mcp_record_physics_object_returns_valid_surface -q
```

Expected: fail because CLI/MCP entries do not exist.

- [ ] **Step 9: Implement CLI/MCP/runtime protocol**

In `brain/v5/cli.py`:

```python
from brain.v5.physics_objects import record_physics_object
```

Add parser:

```python
object_parser = subparsers.add_parser("object")
object_sub = object_parser.add_subparsers(dest="object_command", required=True)
object_record = object_sub.add_parser("record")
object_record.add_argument("--topic", required=True, dest="topic_id")
object_record.add_argument("--type", required=True, dest="object_type")
object_record.add_argument("--name", required=True)
object_record.add_argument("--definition", required=True)
object_record.add_argument("--notation", default="")
object_record.add_argument("--assumption", action="append", default=[], dest="assumptions")
object_record.add_argument("--source-ref", action="append", default=[], dest="source_refs")
object_record.add_argument("--metadata-json", default="{}")
object_record.add_argument("--linked-records-json", default="{}")
object_record.add_argument("--status", default="active")
```

Add dispatch:

```python
if args.command == "object" and args.object_command == "record":
    obj = record_physics_object(
        ws,
        topic_id=args.topic_id,
        object_type=args.object_type,
        name=args.name,
        definition=args.definition,
        notation=args.notation,
        assumptions=args.assumptions,
        source_refs=args.source_refs,
        metadata=_json_object_arg(args.metadata_json, "--metadata-json"),
        linked_records=_json_object_arg(args.linked_records_json, "--linked-records-json"),
        status=args.status,
    )
    return {"ok": True, **require_valid_public_surface("physics_object_record", {"ok": True, **asdict(obj)})}
```

In `brain/v5/mcp_tools.py`, add:

```python
from brain.v5.physics_objects import record_physics_object
```

and wrapper:

```python
def aitp_v5_record_physics_object(
    base: str,
    *,
    topic_id: str,
    object_type: str,
    name: str,
    definition: str,
    notation: str = "",
    assumptions: list[str] | None = None,
    source_refs: list[str] | None = None,
    metadata: dict | None = None,
    linked_records: dict | None = None,
    status: str = "active",
) -> dict:
    ws = init_workspace(Path(base))
    obj = record_physics_object(
        ws,
        topic_id=topic_id,
        object_type=object_type,
        name=name,
        definition=definition,
        notation=notation,
        assumptions=assumptions,
        source_refs=source_refs,
        metadata=metadata,
        linked_records=linked_records,
        status=status,
    )
    return require_valid_public_surface("physics_object_record", {"ok": True, **asdict(obj)})
```

In `brain/v5/runtime_entrypoints.py`, add:

```python
"record_physics_object": {
    "cli": "aitp-v5 object record <args>",
    "mcp": "aitp_v5_record_physics_object",
    "surface": "physics_object_record",
},
```

In `_sample_args_for_template`, add:

```python
if template.startswith("object record"):
    return [
        "--topic",
        "fqhe",
        "--type",
        "hilbert_sector",
        "--name",
        "N=8 sector",
        "--definition",
        "Finite-size Hilbert sector.",
    ]
```

In `brain/v5/adapter_protocols.py`, add `aitp_v5_record_physics_object` to `_KERNEL_ENTRYPOINTS`, add sequence to `_RECORD_SEQUENCE_BY_ACTION`, and add record protocol:

```python
"record_physics_object": [
    "refresh_execution_brief",
    "record_physics_object",
    "refresh_execution_brief",
    "write_session_summary",
],
```

```python
"record_physics_object": {
    "entrypoint": "aitp_v5_record_physics_object",
    "sequence": list(_RECORD_SEQUENCE_BY_ACTION["record_physics_object"]),
    "required_typed_refs": ["topic_id", "object_type", "name", "definition"],
    "accepted_link_fields": ["source_refs", "linked_records"],
    "truth_source": "typed_records",
    "summary_inputs_trusted": False,
},
```

- [ ] **Step 10: Verify full task**

```powershell
pytest tests\test_v5_physics_objects.py tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py tests\test_v5_adapters.py -q
```

Expected: all pass.

- [ ] **Step 11: Run full v5 regression and commit**

```powershell
$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }
pytest $files -q
python -m compileall -q brain\v5
git diff --check -- .
git add brain/v5 tests/test_v5_physics_objects.py tests/test_v5_public_surfaces.py
git commit -m "feat: record physics objects"
```

---

## Task 3: Object Relation Records

**Purpose:** AITP needs typed relations between objects so physics questions can ask about mechanisms, assumptions, limits, and failure modes rather than only claim text.

**Files:**

- Modify: `brain/v5/models.py`
- Modify: `brain/v5/physics_objects.py`
- Modify: `brain/v5/record_contracts.py`
- Modify: `brain/v5/contracts.py`
- Modify: `brain/v5/public_surfaces.py`
- Modify: `brain/v5/cli.py`
- Modify: `brain/v5/mcp_tools.py`
- Modify: `brain/v5/runtime_entrypoints.py`
- Modify: `brain/v5/adapter_protocols.py`
- Test: `tests/test_v5_physics_objects.py`
- Test: `tests/test_v5_public_surfaces.py`

- [ ] **Step 1: Write failing relation tests**

Append to `tests/test_v5_physics_objects.py`:

```python
def test_record_object_relation_links_two_physics_objects(tmp_path):
    from brain.v5.markdown import read_md
    from brain.v5.physics_objects import record_object_relation, record_physics_object
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Counting identifies the edge CFT sector.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size aliasing",
    )
    counting = record_physics_object(
        ws,
        topic_id="fqhe",
        object_type="observable",
        name="edge counting sequence",
        definition="Low-lying entanglement spectrum counting.",
    )
    cft = record_physics_object(
        ws,
        topic_id="fqhe",
        object_type="theory",
        name="edge CFT",
        definition="Conformal field theory describing the edge.",
    )

    relation = record_object_relation(
        ws,
        topic_id="fqhe",
        relation_type="diagnoses",
        subject_id=counting.object_id,
        object_id=cft.object_id,
        statement="The counting sequence diagnoses the candidate edge CFT only in the correct momentum sector.",
        claim_id=claim.claim_id,
        assumptions=["sector assignment is correct"],
        failure_modes=["finite-size aliasing mimics the same sequence"],
        source_refs=["paper:fqhe-counting"],
    )

    fm, body = read_md(ws.registry_dir("object_relations") / f"{relation.relation_id}.md")
    assert relation.kind == "object_relation"
    assert relation.subject_id == counting.object_id
    assert relation.object_id == cft.object_id
    assert fm["failure_modes"] == ["finite-size aliasing mimics the same sequence"]
    assert "diagnoses" in body


def test_object_relation_record_is_public_surface_valid(tmp_path):
    from dataclasses import asdict

    from brain.v5.physics_objects import record_object_relation
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "gw", context_id="gw-methods", title="GW")
    relation = record_object_relation(
        ws,
        topic_id="gw",
        relation_type="implements",
        subject_id="object-self-energy-formula",
        object_id="object-librpa-kernel",
        statement="The kernel implements the correlation self-energy formula.",
    )

    payload = {"ok": True, **asdict(relation)}
    assert require_valid_public_surface("object_relation_record", payload) == payload
```

- [ ] **Step 2: Run red**

```powershell
pytest tests\test_v5_physics_objects.py::test_record_object_relation_links_two_physics_objects tests\test_v5_physics_objects.py::test_object_relation_record_is_public_surface_valid -q
```

Expected: fail because relation record does not exist.

- [ ] **Step 3: Add dataclass**

In `brain/v5/models.py`, add:

```python
@dataclass
class ObjectRelationRecord:
    relation_id: str
    topic_id: str
    relation_type: str
    subject_id: str
    object_id: str
    statement: str
    claim_id: str = ""
    assumptions: list[str] = field(default_factory=list)
    failure_modes: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    status: str = "hypothesis"
    kind: str = "object_relation"
```

`registry/object_relations` already exists in `paths.py`; verify before editing.

- [ ] **Step 4: Add kernel function**

In `brain/v5/physics_objects.py`, import `ObjectRelationRecord` and add:

```python
def record_object_relation(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    relation_type: str,
    subject_id: str,
    object_id: str,
    statement: str,
    claim_id: str = "",
    assumptions: list[str] | None = None,
    failure_modes: list[str] | None = None,
    source_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    metadata: dict | None = None,
    status: str = "hypothesis",
) -> ObjectRelationRecord:
    relation_id = prefixed_id(
        "object-relation",
        f"{topic_id}:{relation_type}:{subject_id}:{object_id}:{statement}",
        max_slug=64,
    )
    record = ObjectRelationRecord(
        relation_id=relation_id,
        topic_id=topic_id,
        relation_type=relation_type,
        subject_id=subject_id,
        object_id=object_id,
        statement=statement,
        claim_id=claim_id,
        assumptions=assumptions or [],
        failure_modes=failure_modes or [],
        source_refs=source_refs or [],
        evidence_refs=evidence_refs or [],
        metadata=metadata or {},
        status=status,
    )
    write_record(
        ws.registry_dir("object_relations") / f"{relation_id}.md",
        record,
        body=f"# Object Relation: {relation_type}\n\n{statement}\n",
    )
    return record


def list_object_relations_for_claim(ws: WorkspacePaths, claim_id: str) -> list[ObjectRelationRecord]:
    return [
        relation
        for relation in list_records(ws.registry_dir("object_relations"), ObjectRelationRecord)
        if relation.claim_id == claim_id
    ]
```

- [ ] **Step 5: Add contract/public surface**

In `brain/v5/record_contracts.py`, add:

```python
def validate_object_relation_record(payload: dict[str, Any], *, path: str = "object_relation_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="object_relation")
    if result.issues:
        return result
    for key in ("relation_id", "topic_id", "relation_type", "subject_id", "object_id", "statement", "status"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("assumptions", "failure_modes", "source_refs", "evidence_refs"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_mapping(payload.get("metadata"), f"{path}.metadata", result)
    return result


def require_valid_object_relation_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_object_relation_record(payload), payload)
```

Add matching wrappers in `contracts.py`, surface name/purpose/validator in `public_surfaces.py`, and expected surface in `tests/test_v5_public_surfaces.py`.

- [ ] **Step 6: Verify relation kernel/public-surface green**

```powershell
pytest tests\test_v5_physics_objects.py tests\test_v5_public_surfaces.py -q
```

Expected: all pass.

- [ ] **Step 7: Add CLI/MCP/runtime entries**

Use command shape:

```powershell
aitp-v5 relation record --topic fqhe --type diagnoses --subject object-a --object object-b --statement "A diagnoses B"
```

Add parser under a new top-level `relation` command in `brain/v5/cli.py`, and add `aitp_v5_record_object_relation` in `brain/v5/mcp_tools.py`.

Runtime entrypoint:

```python
"record_object_relation": {
    "cli": "aitp-v5 relation record <args>",
    "mcp": "aitp_v5_record_object_relation",
    "surface": "object_relation_record",
},
```

Adapter protocol:

```python
"record_object_relation": {
    "entrypoint": "aitp_v5_record_object_relation",
    "sequence": list(_RECORD_SEQUENCE_BY_ACTION["record_object_relation"]),
    "required_typed_refs": ["topic_id", "relation_type", "subject_id", "object_id", "statement"],
    "accepted_link_fields": ["claim_id", "source_refs", "evidence_refs"],
    "truth_source": "typed_records",
    "summary_inputs_trusted": False,
},
```

- [ ] **Step 8: Add CLI/MCP tests**

Append to `tests/test_v5_physics_objects.py`:

```python
def test_cli_object_relation_record_returns_json(tmp_path, capsys):
    from brain.v5.cli import main

    assert main(
        [
            "--base",
            str(tmp_path),
            "relation",
            "record",
            "--topic",
            "fqhe",
            "--type",
            "diagnoses",
            "--subject",
            "object-counting",
            "--object",
            "object-edge-cft",
            "--statement",
            "Counting diagnoses the edge CFT in a fixed sector.",
            "--claim",
            "claim-fqhe",
            "--failure-mode",
            "finite-size aliasing",
            "--source-ref",
            "paper:fqhe",
        ]
    ) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["kind"] == "object_relation"
    assert payload["failure_modes"] == ["finite-size aliasing"]


def test_mcp_record_object_relation_returns_valid_surface(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_record_object_relation
    from brain.v5.public_surfaces import require_valid_public_surface

    payload = aitp_v5_record_object_relation(
        str(tmp_path),
        topic_id="gw",
        relation_type="implements",
        subject_id="object-formula",
        object_id="object-code",
        statement="The code path implements the formula.",
    )

    assert payload["ok"] is True
    assert require_valid_public_surface("object_relation_record", payload) == payload
```

- [ ] **Step 9: Verify full task and commit**

```powershell
pytest tests\test_v5_physics_objects.py tests\test_v5_runtime_entrypoints.py tests\test_v5_adapters.py -q
$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }
pytest $files -q
python -m compileall -q brain\v5
git diff --check -- .
git add brain/v5 tests/test_v5_physics_objects.py tests/test_v5_public_surfaces.py
git commit -m "feat: record object relations"
```

---

## Task 4: Relation-Aware Execution Brief

**Purpose:** The execution brief must expose active claim objects and relations so agents reason over physical structure, not only text.

**Files:**

- Modify: `brain/v5/brief.py`
- Modify: `brain/v5/physics_objects.py`
- Test: `tests/test_v5_physics_objects.py`

- [ ] **Step 1: Write failing brief test**

Append to `tests/test_v5_physics_objects.py`:

```python
def test_execution_brief_exposes_object_relations_for_active_claim(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.physics_objects import record_object_relation, record_physics_object
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Counting identifies the edge CFT.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size aliasing",
    )
    counting = record_physics_object(
        ws,
        topic_id="fqhe",
        object_type="observable",
        name="counting sequence",
        definition="Low-lying counting data.",
    )
    cft = record_physics_object(
        ws,
        topic_id="fqhe",
        object_type="theory",
        name="edge CFT",
        definition="Candidate edge theory.",
    )
    relation = record_object_relation(
        ws,
        topic_id="fqhe",
        relation_type="diagnoses",
        subject_id=counting.object_id,
        object_id=cft.object_id,
        statement="Counting diagnoses the edge CFT only after sector matching.",
        claim_id=claim.claim_id,
        failure_modes=["wrong momentum sector"],
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)

    brief = build_execution_brief(ws, "s1")

    relations = brief["known_context"]["object_relations"]
    assert relations == [
        {
            "relation_id": relation.relation_id,
            "relation_type": "diagnoses",
            "subject_id": counting.object_id,
            "object_id": cft.object_id,
            "statement": "Counting diagnoses the edge CFT only after sector matching.",
            "failure_modes": ["wrong momentum sector"],
            "status": "hypothesis",
        }
    ]
```

- [ ] **Step 2: Run red**

```powershell
pytest tests\test_v5_physics_objects.py::test_execution_brief_exposes_object_relations_for_active_claim -q
```

Expected: fail with missing `object_relations`.

- [ ] **Step 3: Add brief payload helper**

In `brain/v5/physics_objects.py`, add:

```python
def object_relation_brief_payload(relation: ObjectRelationRecord) -> dict:
    return {
        "relation_id": relation.relation_id,
        "relation_type": relation.relation_type,
        "subject_id": relation.subject_id,
        "object_id": relation.object_id,
        "statement": relation.statement,
        "failure_modes": list(relation.failure_modes),
        "status": relation.status,
    }
```

In `brain/v5/brief.py`, import:

```python
from brain.v5.physics_objects import list_object_relations_for_claim, object_relation_brief_payload
```

Initialize:

```python
object_relations = []
```

When claim exists:

```python
object_relations = [
    object_relation_brief_payload(relation)
    for relation in list_object_relations_for_claim(ws, claim.claim_id)
]
```

In `known_context`, add:

```python
"object_relations": object_relations,
```

- [ ] **Step 4: Verify**

```powershell
pytest tests\test_v5_physics_objects.py tests\test_v5_contracts.py tests\test_v5_adapters.py -q
```

Expected: all pass.

- [ ] **Step 5: Commit**

```powershell
git add brain/v5/brief.py brain/v5/physics_objects.py tests/test_v5_physics_objects.py
git commit -m "feat: surface object relations in briefs"
```

---

## Task 5: Question Engine Consumes Persisted Relations

**Purpose:** The mandatory reflection questions should be conditioned on typed object relations, not manually passed ad hoc strings.

**Files:**

- Modify: `brain/v5/brief.py`
- Modify: `brain/v5/question_engine.py`
- Modify: `brain/v5/question_intents.py`
- Test: `tests/test_v5_physics_objects.py`
- Test: `tests/test_v5_question_intents.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_v5_physics_objects.py`:

```python
def test_mandatory_reflection_mentions_recorded_relation_failure_mode(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.physics_objects import record_object_relation, record_physics_object
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Counting identifies the edge CFT.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size aliasing",
    )
    counting = record_physics_object(ws, topic_id="fqhe", object_type="observable", name="counting", definition="Counting data.")
    cft = record_physics_object(ws, topic_id="fqhe", object_type="theory", name="edge CFT", definition="Candidate theory.")
    record_object_relation(
        ws,
        topic_id="fqhe",
        relation_type="diagnoses",
        subject_id=counting.object_id,
        object_id=cft.object_id,
        statement="Counting diagnoses the edge CFT.",
        claim_id=claim.claim_id,
        failure_modes=["finite-size aliasing"],
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)

    brief = build_execution_brief(ws, "s1")

    questions = "\n".join(item["question"] for item in brief["mandatory_reflection"])
    assert "finite-size aliasing" in questions
```

- [ ] **Step 2: Run red**

```powershell
pytest tests\test_v5_physics_objects.py::test_mandatory_reflection_mentions_recorded_relation_failure_mode -q
```

Expected: fail because generated questions do not include relation failure modes.

- [ ] **Step 3: Update brief to pass structured relation payloads into question engine**

In `brain/v5/brief.py`, build `object_relations` once using the typed brief payload and pass that payload into `generate_questions`:

```python
raw_object_relations = list_object_relations_for_claim(ws, claim.claim_id)
object_relations = [
    object_relation_brief_payload(relation)
    for relation in raw_object_relations
]
questions = generate_questions(claim, flow, object_relations=object_relations)
```

Do not make relation text the source of truth. The same `object_relations` payload should also be exposed in `known_context`.

- [ ] **Step 4: Normalize structured relation inputs in question intents**

In `brain/v5/question_intents.py`, normalize each relation payload into:

```python
{
    "prompt": "<relation_type>: <statement> Failure modes: <failure_modes>",
    "target": "<relation_id>",
    "failure_modes": ["<mode>"],
}
```

Keep legacy string inputs supported as a compatibility path, but make dict payloads the primary path. Relation-aware intents must store `target_relations` as relation IDs when relation IDs are available.

- [ ] **Step 5: Verify and commit**

```powershell
pytest tests\test_v5_physics_objects.py tests\test_v5_question_intents.py tests\test_v5_kernel.py -q
$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }
pytest $files -q
git add brain/v5/brief.py brain/v5/question_engine.py brain/v5/question_intents.py tests/test_v5_physics_objects.py tests/test_v5_question_intents.py
git commit -m "feat: ask relation-aware physics questions"
```

---

## Task 6: Local Sense-Making Reports

**Purpose:** AITP needs a compact typed report for "what do we currently think and why" about a claim/object/relation cluster. This is not L2 memory and not validation.

**Files:**

- Create: `brain/v5/sensemaking.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/paths.py`
- Modify: `brain/v5/record_contracts.py`
- Modify: `brain/v5/contracts.py`
- Modify: `brain/v5/public_surfaces.py`
- Modify: `brain/v5/cli.py`
- Modify: `brain/v5/mcp_tools.py`
- Modify: `brain/v5/runtime_entrypoints.py`
- Modify: `brain/v5/adapter_protocols.py`
- Test: `tests/test_v5_sensemaking.py`

- [ ] **Step 1: Add failing tests**

Create `tests/test_v5_sensemaking.py`:

```python
from __future__ import annotations

from dataclasses import asdict
import json


def test_record_sensemaking_report_is_orientation_not_validation(tmp_path):
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.sensemaking import record_sensemaking_report
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Counting identifies the edge CFT.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size aliasing",
    )

    report = record_sensemaking_report(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        title="Current interpretation of counting evidence",
        summary="Counting is suggestive but not validated.",
        object_ids=["object-counting", "object-cft"],
        relation_ids=["relation-counting-cft"],
        evidence_refs=["evidence-counting-table"],
        open_questions=["Can another sector mimic this sequence?"],
        next_actions=["run negative control"],
    )

    payload = {"ok": True, **asdict(report)}
    assert report.kind == "sensemaking_report"
    assert report.validation_status == "not_validation"
    assert require_valid_public_surface("sensemaking_report_record", payload) == payload
```

- [ ] **Step 2: Run red**

```powershell
pytest tests\test_v5_sensemaking.py -q
```

Expected: fail because module does not exist.

- [ ] **Step 3: Implement record**

Add dataclass in `models.py`:

```python
@dataclass
class SensemakingReportRecord:
    report_id: str
    topic_id: str
    claim_id: str
    title: str
    summary: str
    object_ids: list[str] = field(default_factory=list)
    relation_ids: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    validation_status: str = "not_validation"
    kind: str = "sensemaking_report"
```

Add path:

```python
"registry/sensemaking_reports",
```

Create `brain/v5/sensemaking.py` with `record_sensemaking_report` using `prefixed_id`, `write_record`, and body `# Sense-Making Report: {title}`.

- [ ] **Step 4: Add contracts and public surfaces**

Use the same pattern as Task 2. Required non-empty fields:

```text
report_id, topic_id, claim_id, title, summary, validation_status
```

Required list fields:

```text
object_ids, relation_ids, evidence_refs, open_questions, next_actions
```

Contract rule:

```python
if payload.get("validation_status") != "not_validation":
    result.add(f"{path}.validation_status", "must be 'not_validation'")
```

- [ ] **Step 5: Add CLI/MCP/runtime**

CLI shape:

```powershell
aitp-v5 sensemaking report record --topic fqhe --claim claim-fqhe --title "Current interpretation" --summary "Suggestive but not validated"
```

MCP wrapper:

```python
aitp_v5_record_sensemaking_report(...)
```

Runtime entrypoint surface:

```text
sensemaking_report_record
```

Adapter record protocol required refs:

```python
["topic_id", "claim_id", "title", "summary"]
```

- [ ] **Step 6: Verify and commit**

```powershell
pytest tests\test_v5_sensemaking.py tests\test_v5_public_surfaces.py tests\test_v5_adapters.py -q
$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }
pytest $files -q
git add brain/v5 tests/test_v5_sensemaking.py tests/test_v5_public_surfaces.py
git commit -m "feat: record sensemaking reports"
```

---

## Task 7: Validation Contract Records

**Purpose:** Validation should become a typed record before L4-style review, not an ad hoc prompt.

**Files:**

- Create: `brain/v5/validation.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/paths.py`
- Modify: contracts/public surfaces/CLI/MCP/runtime/adapters
- Test: `tests/test_v5_validation.py`

- [ ] **Step 1: Add failing test**

Create `tests/test_v5_validation.py`:

```python
from __future__ import annotations

from dataclasses import asdict


def test_create_validation_contract_requires_claim_checks_and_failure_modes(tmp_path):
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.validation import create_validation_contract
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "gw", context_id="gw-methods", title="GW")
    claim = create_claim(
        ws,
        topic_id="gw",
        statement="The modified self-energy kernel reproduces the benchmark.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="formula-code translation",
    )

    contract = create_validation_contract(
        ws,
        topic_id="gw",
        claim_id=claim.claim_id,
        required_checks=["code_state_present", "benchmark_table_within_tolerance"],
        failure_modes=["wrong frequency grid", "dirty worktree"],
        required_evidence_outputs=["evidence_or_provenance", "minimal_check"],
        validator_role="adversarial_reviewer",
    )

    payload = {"ok": True, **asdict(contract)}
    assert contract.kind == "validation_contract"
    assert contract.status == "open"
    assert require_valid_public_surface("validation_contract_record", payload) == payload
```

- [ ] **Step 2: Run red**

```powershell
pytest tests\test_v5_validation.py::test_create_validation_contract_requires_claim_checks_and_failure_modes -q
```

Expected: fail because module does not exist.

- [ ] **Step 3: Implement dataclass**

Add to `models.py`:

```python
@dataclass
class ValidationContractRecord:
    contract_id: str
    topic_id: str
    claim_id: str
    required_checks: list[str] = field(default_factory=list)
    failure_modes: list[str] = field(default_factory=list)
    required_evidence_outputs: list[str] = field(default_factory=list)
    validator_role: str = "adversarial_reviewer"
    status: str = "open"
    kind: str = "validation_contract"
```

Path:

```python
"registry/validation_contracts",
```

Create `brain/v5/validation.py` with `create_validation_contract`.

- [ ] **Step 4: Contract rule**

Validator must reject empty lists for:

```text
required_checks
failure_modes
required_evidence_outputs
```

This prevents "validation" contracts that do not say what could go wrong.

- [ ] **Step 5: Add CLI/MCP/runtime**

CLI shape:

```powershell
aitp-v5 validation contract create --topic gw --claim claim-gw --required-check code_state_present --failure-mode "dirty worktree" --required-output evidence_or_provenance
```

MCP wrapper:

```python
aitp_v5_create_validation_contract(...)
```

Public surface:

```text
validation_contract_record
```

- [ ] **Step 6: Verify and commit**

```powershell
pytest tests\test_v5_validation.py tests\test_v5_public_surfaces.py tests\test_v5_adapters.py -q
$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }
pytest $files -q
git add brain/v5 tests/test_v5_validation.py tests/test_v5_public_surfaces.py
git commit -m "feat: create validation contracts"
```

---

## Task 8: Human Checkpoint Records

**Purpose:** Human checkpoints should be typed records with reasons and decisions, not just booleans inside a brief.

**Files:**

- Create: `brain/v5/checkpoints.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/paths.py`
- Modify: contracts/public surfaces/CLI/MCP/runtime/adapters
- Test: `tests/test_v5_validation.py`

- [ ] **Step 1: Add failing test**

Append to `tests/test_v5_validation.py`:

```python
def test_human_checkpoint_records_reason_and_decision(tmp_path):
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")

    checkpoint = request_human_checkpoint(
        ws,
        topic_id="fqhe",
        claim_id="claim-fqhe",
        reason="Promotion to reusable L2 memory requires human judgment.",
        requested_by="risk_policy",
        options=["approve", "revise", "reject"],
    )
    decided = decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="revise",
        rationale="Need a negative control before promotion.",
        decided_by="human",
    )

    assert decided.status == "decided"
    assert decided.decision == "revise"
    assert require_valid_public_surface("human_checkpoint_record", {"ok": True, **decided.__dict__})
```

- [ ] **Step 2: Implement record**

Dataclass:

```python
@dataclass
class HumanCheckpointRecord:
    checkpoint_id: str
    topic_id: str
    claim_id: str
    reason: str
    requested_by: str
    options: list[str] = field(default_factory=list)
    status: str = "open"
    decision: str = ""
    rationale: str = ""
    decided_by: str = ""
    kind: str = "human_checkpoint"
```

Path:

```python
"registry/checkpoints",
```

This path already exists; verify before editing.

- [ ] **Step 3: Contract rule**

Open checkpoints require:

```text
checkpoint_id, topic_id, reason, requested_by
options list is non-empty
status in {"open", "decided"}
```

Decided checkpoints additionally require:

```text
decision, rationale, decided_by
decision must be one of options
```

- [ ] **Step 4: Add CLI/MCP/runtime**

CLI commands:

```powershell
aitp-v5 checkpoint request --topic fqhe --claim claim-fqhe --reason "Promotion requires human judgment" --requested-by risk_policy --option approve --option revise
aitp-v5 checkpoint decide <checkpoint-id> --decision revise --rationale "Need negative control" --decided-by human
```

MCP wrappers:

```python
aitp_v5_request_human_checkpoint(...)
aitp_v5_decide_human_checkpoint(...)
```

Public surface:

```text
human_checkpoint_record
```

- [ ] **Step 5: Verify and commit**

```powershell
pytest tests\test_v5_validation.py tests\test_v5_public_surfaces.py tests\test_v5_adapters.py -q
$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }
pytest $files -q
git add brain/v5 tests/test_v5_validation.py tests/test_v5_public_surfaces.py
git commit -m "feat: record human checkpoints"
```

---

## Task 9: L2 Memory Entry And Promotion Packet

**Purpose:** L2 should store reusable trusted/scoped knowledge, not process history. Promotion must be explicit and evidence-backed.

**Files:**

- Create: `brain/v5/memory.py`
- Modify: `brain/v5/models.py`
- Modify: `brain/v5/paths.py`
- Modify: contracts/public surfaces/CLI/MCP/runtime/adapters
- Test: `tests/test_v5_memory.py`

- [ ] **Step 1: Add failing tests**

Create `tests/test_v5_memory.py`:

```python
from __future__ import annotations

from dataclasses import asdict


def test_create_promotion_packet_requires_evidence_and_scope(tmp_path):
    from brain.v5.memory import create_promotion_packet
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Counting identifies the edge CFT in the recorded sector.",
        evidence_profile="toy_numeric",
        confidence_state="locally_checked",
        active_uncertainty="scope of finite-size evidence",
    )

    packet = create_promotion_packet(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        proposed_memory_kind="scoped_claim",
        scope="N<=10 exact diagonalization, fixed momentum sector",
        evidence_refs=["evidence-counting-table"],
        non_claims=["Does not prove thermodynamic stability."],
        known_failure_modes=["sector misassignment"],
    )

    assert packet.kind == "promotion_packet"
    assert packet.status == "pending_human_checkpoint"
    assert require_valid_public_surface("promotion_packet_record", {"ok": True, **asdict(packet)}) == {"ok": True, **asdict(packet)}
```

- [ ] **Step 2: Run red**

```powershell
pytest tests\test_v5_memory.py::test_create_promotion_packet_requires_evidence_and_scope -q
```

Expected: fail because `memory.py` does not exist.

- [ ] **Step 3: Add dataclasses**

Add:

```python
@dataclass
class PromotionPacketRecord:
    packet_id: str
    topic_id: str
    claim_id: str
    proposed_memory_kind: str
    scope: str
    evidence_refs: list[str] = field(default_factory=list)
    non_claims: list[str] = field(default_factory=list)
    known_failure_modes: list[str] = field(default_factory=list)
    status: str = "pending_human_checkpoint"
    human_checkpoint_id: str = ""
    kind: str = "promotion_packet"


@dataclass
class MemoryEntryRecord:
    memory_id: str
    memory_kind: str
    statement: str
    scope: str
    evidence_refs: list[str] = field(default_factory=list)
    source_claim_id: str = ""
    source_topic_id: str = ""
    non_claims: list[str] = field(default_factory=list)
    known_failure_modes: list[str] = field(default_factory=list)
    status: str = "active"
    kind: str = "memory_entry"
```

Paths:

```text
registry/promotion_packets
memory/l2/entries
```

- [ ] **Step 4: Contract rules**

Promotion packets require non-empty:

```text
packet_id, topic_id, claim_id, proposed_memory_kind, scope
evidence_refs
known_failure_modes
```

Memory entries require non-empty:

```text
memory_id, memory_kind, statement, scope, evidence_refs, source_claim_id, source_topic_id
```

- [ ] **Step 5: Add `create_promotion_packet` only**

Do not implement final promotion yet. This task only creates the packet and public surface.

Function:

```python
def create_promotion_packet(...)
```

writes:

```text
.aitp/registry/promotion_packets/<packet_id>.md
```

- [ ] **Step 6: Verify and commit**

```powershell
pytest tests\test_v5_memory.py tests\test_v5_public_surfaces.py tests\test_v5_adapters.py -q
$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }
pytest $files -q
git add brain/v5 tests/test_v5_memory.py tests/test_v5_public_surfaces.py
git commit -m "feat: create promotion packets"
```

---

## Task 10: Apply Promotion After Human Checkpoint

**Purpose:** Convert a promotion packet into an L2 memory entry only after a decided human checkpoint approves it.

**Files:**

- Modify: `brain/v5/memory.py`
- Modify: `brain/v5/checkpoints.py`
- Test: `tests/test_v5_memory.py`

- [ ] **Step 1: Add failing test**

Append to `tests/test_v5_memory.py`:

```python
def test_apply_promotion_requires_approved_human_checkpoint(tmp_path):
    import pytest

    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.memory import apply_promotion_packet, create_promotion_packet
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Counting identifies the edge CFT in the recorded sector.",
        evidence_profile="toy_numeric",
        confidence_state="locally_checked",
        active_uncertainty="promotion readiness",
    )
    packet = create_promotion_packet(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        proposed_memory_kind="scoped_claim",
        scope="fixed sector ED",
        evidence_refs=["evidence-counting"],
        known_failure_modes=["sector misassignment"],
    )

    with pytest.raises(ValueError, match="approved human checkpoint"):
        apply_promotion_packet(ws, packet_id=packet.packet_id, checkpoint_id="")

    checkpoint = request_human_checkpoint(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        reason="L2 promotion requires approval.",
        requested_by="promotion_policy",
        options=["approve", "revise"],
    )
    decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve",
        rationale="Evidence and scope are explicit.",
        decided_by="human",
    )
    memory = apply_promotion_packet(ws, packet_id=packet.packet_id, checkpoint_id=checkpoint.checkpoint_id)

    assert memory.kind == "memory_entry"
    assert memory.source_claim_id == claim.claim_id
    assert memory.evidence_refs == ["evidence-counting"]
```

- [ ] **Step 2: Implement minimal apply logic**

`apply_promotion_packet` must:

1. Read `PromotionPacketRecord`.
2. Read `HumanCheckpointRecord`.
3. Require checkpoint status `decided`.
4. Require checkpoint decision `approve`.
5. Create `MemoryEntryRecord`.
6. Update packet status to `promoted` and set `human_checkpoint_id`.

- [ ] **Step 3: Verify and commit**

```powershell
pytest tests\test_v5_memory.py tests\test_v5_validation.py -q
$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }
pytest $files -q
git add brain/v5 tests/test_v5_memory.py
git commit -m "feat: promote approved packets to l2 memory"
```

---

## Task 11: Legacy Topic Migration Dry-Run Completeness

**Purpose:** The old topic bridge must tell us what will be preserved before writing v5 records.

**Files:**

- Modify: `brain/v5/legacy_bridge.py`
- Test: `tests/test_v5_legacy_bridge.py`

- [ ] **Step 1: Add failing test**

Append to `tests/test_v5_legacy_bridge.py`:

```python
def test_legacy_topic_dry_run_reports_missing_and_mapped_sections(tmp_path):
    from pathlib import Path

    from brain.v5.legacy_bridge import audit_legacy_topic_migration

    topic = tmp_path / "old-topic"
    (topic / "L0" / "sources" / "paper-a").mkdir(parents=True)
    (topic / "L1").mkdir()
    (topic / "state.md").write_text("---\ntitle: Old Topic\n---\n# State\n", encoding="utf-8")
    (topic / "L0" / "sources" / "paper-a" / "source.md").write_text("# Paper A\n", encoding="utf-8")
    (topic / "L1" / "question_contract.md").write_text("# Question\n", encoding="utf-8")

    audit = audit_legacy_topic_migration(topic)

    assert audit["kind"] == "legacy_topic_migration_audit"
    assert audit["can_write_v5_records"] is False
    assert "L1/source_basis.md" in audit["missing_expected_paths"]
    assert audit["mapped_paths"]["state.md"] == "topic/runtime metadata"
    assert audit["mapped_paths"]["L0/sources/paper-a/source.md"] == "reference_location/source evidence candidate"
```

- [ ] **Step 2: Implement audit without writing records**

Add function:

```python
def audit_legacy_topic_migration(topic_path: str | Path) -> dict:
```

Return fields:

```text
kind
topic_path
mapped_paths
missing_expected_paths
can_write_v5_records
summary_inputs_trusted=False
```

Do not write `.aitp` files in this function.

- [ ] **Step 3: Verify and commit**

```powershell
pytest tests\test_v5_legacy_bridge.py -q
$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }
pytest $files -q
git add brain/v5/legacy_bridge.py tests/test_v5_legacy_bridge.py
git commit -m "feat: audit legacy topic migration"
```

---

## Task 12: Real Workflow Acceptance Skeleton

**Purpose:** Establish executable acceptance tests for the actual workflows this harness is meant to support.

**Files:**

- Create: `tests/test_v5_real_workflows.py`

- [ ] **Step 1: Add FQHE workflow skeleton**

Create `tests/test_v5_real_workflows.py`:

```python
from __future__ import annotations


def test_fqhe_learning_to_idea_to_toy_check_workflow(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.evidence import record_evidence
    from brain.v5.physics_objects import record_object_relation, record_physics_object
    from brain.v5.references import record_reference_location
    from brain.v5.tool_executors import execute_registered_tool_result
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="The counting sequence matches the candidate edge CFT in the recorded sector.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size aliasing",
    )
    record_reference_location(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        connector_id="local_pdf",
        location_type="paper_pdf",
        uri="file:///papers/fqhe/counting.pdf",
        label="FQHE counting reference",
        source_ref="paper:fqhe-counting",
    )
    counting = record_physics_object(ws, topic_id="fqhe", object_type="observable", name="counting", definition="Counting table.")
    cft = record_physics_object(ws, topic_id="fqhe", object_type="theory", name="edge CFT", definition="Candidate edge theory.")
    record_object_relation(
        ws,
        topic_id="fqhe",
        relation_type="matches",
        subject_id=counting.object_id,
        object_id=cft.object_id,
        statement="Counting table matches the edge CFT sequence.",
        claim_id=claim.claim_id,
        failure_modes=["wrong sector"],
    )
    result = execute_registered_tool_result(
        ws,
        executor_id="metric_table_check",
        recipe_id="recipe-fqhe-counting-table",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        inputs={
            "metrics": [
                {"name": "level-0", "observed": 1, "expected": 1, "tolerance": 0},
                {"name": "level-1", "observed": 1, "expected": 1, "tolerance": 0},
            ]
        },
        evidence_status="supports",
        supports_outputs=["evidence_or_provenance", "minimal_check"],
        evidence_type="toy_numeric",
    )
    record_evidence(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        evidence_type="literature_synthesis",
        status="supports",
        summary="Reference location and convention source recorded.",
        supports_outputs=["evidence_or_provenance"],
        source_refs=["paper:fqhe-counting"],
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)

    brief = build_execution_brief(ws, "s1")

    assert result.evidence is not None
    assert brief["evidence_coverage"]["satisfied_outputs"]
    assert brief["known_context"]["reference_locations"]
    assert brief["known_context"]["object_relations"]
```

- [ ] **Step 2: Run test**

```powershell
pytest tests\test_v5_real_workflows.py::test_fqhe_learning_to_idea_to_toy_check_workflow -q
```

Expected: pass after Tasks 1-5 are complete.

- [ ] **Step 3: Add GW workflow skeleton**

Append:

```python
def test_gw_formula_code_translation_records_code_state_and_benchmark(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.code import record_code_state
    from brain.v5.physics_objects import record_object_relation, record_physics_object
    from brain.v5.tool_executors import execute_registered_tool_result
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The code path reproduces the benchmark after the self-energy change.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="formula-code translation",
    )
    code_state = record_code_state(
        ws,
        repo_id="librpa",
        upstream_remote="origin",
        upstream_branch="master",
        upstream_commit="abc123",
        local_branch="topic/self-energy",
        worktree_path="D:/worktrees/librpa/self-energy",
        dirty=False,
        linked_records={"claim_id": claim.claim_id},
    )
    formula = record_physics_object(ws, topic_id="librpa-gw", object_type="formula", name="correlation self-energy", definition="GW correlation self-energy formula.")
    kernel = record_physics_object(ws, topic_id="librpa-gw", object_type="code_path", name="LibRPA self-energy kernel", definition="Implementation path under test.")
    record_object_relation(
        ws,
        topic_id="librpa-gw",
        relation_type="implements",
        subject_id=kernel.object_id,
        object_id=formula.object_id,
        statement="The code path implements the correlation self-energy formula.",
        claim_id=claim.claim_id,
        failure_modes=["frequency grid mismatch", "basis cutoff mismatch"],
    )
    execute_registered_tool_result(
        ws,
        executor_id="metric_table_check",
        recipe_id="recipe-librpa-gw-benchmark-table",
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        inputs={"metrics": [{"name": "gap_ev", "observed": 1.2, "expected": 1.2, "tolerance": 0.01}]},
        evidence_status="supports",
        code_state_ids=[code_state.code_state_id],
        supports_outputs=["evidence_or_provenance", "minimal_check"],
        evidence_type="code_method",
    )
    bind_session(ws, "s1", topic_id="librpa-gw", context_id="gw-methods", active_claim=claim.claim_id)

    brief = build_execution_brief(ws, "s1")

    assert brief["known_context"]["object_relations"]
    assert "evidence_or_provenance" in brief["evidence_coverage"]["satisfied_outputs"]
```

- [ ] **Step 4: Verify and commit**

```powershell
pytest tests\test_v5_real_workflows.py -q
$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }
pytest $files -q
git add tests/test_v5_real_workflows.py
git commit -m "test: add v5 real workflow acceptance skeletons"
```

---

## Suggested Execution Order

Execute tasks in this order:

1. Task 1: Reference locations in execution brief.
2. Task 2: Physics object records.
3. Task 3: Object relation records.
4. Task 4: Relation-aware execution brief.
5. Task 5: Question engine consumes persisted relations.
6. Task 6: Local sense-making reports.
7. Task 7: Validation contract records.
8. Task 8: Human checkpoint records.
9. Task 9: L2 promotion packet.
10. Task 10: Apply promotion after human checkpoint.
11. Task 11: Legacy migration dry-run completeness.
12. Task 12: Real workflow acceptance skeleton.

Do not batch Tasks 2 and 3 unless using separate subagents with disjoint write scopes. They both touch the same files and will conflict.

## Stop Conditions

Stop and report if:

- v5 full focused suite fails after implementation and the failure is not directly tied to the current task.
- A planned file has grown beyond the architecture-boundary test limit.
- A required public surface cannot be validated without weakening contracts.
- A task would require changing legacy behavior outside `brain/v5/` unexpectedly.
- Main checkout dirty files are needed to proceed.

## Final Verification For This Plan

After all tasks are complete:

```powershell
$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }
pytest $files -q
python -m compileall -q brain\v5
git diff --check -- .
```

Expected:

```text
all v5 tests pass
compileall passes
diff check has no errors
```

Then run a non-blocking legacy baseline:

```powershell
pytest tests -q
```

If legacy failures remain historical, record the count and do not fix unrelated legacy failures inside this plan.
