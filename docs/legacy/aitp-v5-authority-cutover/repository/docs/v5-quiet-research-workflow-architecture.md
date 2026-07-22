# AITP v5 Quiet Research Workflow Architecture

Date: 2026-06-27
Status: Phase 1 ObjectiveGraph/CompactBrief, Phase 2 AuthorityRegistry, Phase 3 QuietCheckpoint, Phase 4 NoteOutline, research-distillation candidate compiler, and Codex Context Pack implemented as typed/read-only surfaces

## 1. Architecture Audit Summary

Current implementation locations:

- Execution brief: `brain/v5/brief.py::build_execution_brief`
- Claim relation map: `brain/v5/claim_relation_map.py::build_claim_relation_map`
- Recording navigation: `brain/v5/recording_navigator.py`
- Claim/session binding: `brain/v5/models.py::ClaimRecord`, `SessionBinding`; `brain/v5/workspace.py::bind_session`, `create_claim`
- Typed record registry: `brain/v5/paths.py`, `brain/v5/store.py`, `brain/v5/record_refs.py`
- Public surface validation: `brain/v5/public_surfaces.py`
- CLI/MCP entrypoints: `brain/v5/cli.py`, `brain/v5/cli_status.py`, `brain/v5/mcp_tools.py`

Current data flow:

```text
SessionBinding
  -> active_claim
  -> build_execution_brief
  -> build_claim_relation_map
  -> recording_navigator slot expansion
  -> typed write surface
  -> recording_effect_verification / process_graph_slice
```

Observed failure modes:

- Active claim divergence: `SessionBinding.active_claim` is a single pointer, so a recovered brief can over-focus on an older claim while the live research objective has moved to a different work package.
- Heavy relation map: `build_claim_relation_map` intentionally retains support, limitations, contradictions, historical evidence, sibling claims, and legacy review context. This is correct for audit but too large for default continuation.
- Synchronous recording pressure: `recording_navigator` exposes per-event write slots and verification. That is useful for trust-relevant writes but pushes agents toward step-by-step recording during exploratory derivations.
- Objective/claim mixing: project objectives, work packages, deliverables, and blockers are inferred from claims/routes/runs rather than represented as a first-class runtime focus.
- Authority/convention scattering: sector conventions and result authorities used to fit only indirectly through `sensemaking_report`, `object_relation`, `claim_status`, or prose. Phase 2 now adds a native `authority_record` registry while preserving the no-trust-promotion boundary.

## 2. New Component Design

### ObjectiveGraph

Purpose: expose a read-only objective/work-package projection:

```text
project objective
  -> work packages
  -> claims
  -> artifacts
  -> deliverables
  -> blockers
```

Phase 1 implementation:

- Module: `brain/v5/objective_graph.py`
- Public surface: `objective_graph`
- CLI: `aitp-v5 status objective-graph <session-id>`
- MCP: `aitp_v5_get_objective_graph`
- Source records: session, topic, claims, routes, research runs, artifacts, claim statuses, proof obligations
- Trust boundary: read-only, orientation-only, no kernel mutation, no claim-trust mutation

Future extension:

- Add an explicit `ObjectiveRecord` and `WorkPackageRecord` only after the read-only projection proves useful.
- Extend `SessionBinding` with optional `active_objective` and `active_work_packages` without changing existing `active_claim` semantics.

### QuietResearchSession

Purpose: support research bursts before checkpointing.

Target behavior:

- Do not require per-step typed writes during derivation or numerical exploration.
- Collect changed files, generated artifacts, validation commands, and durable observations in a local batch envelope.
- On checkpoint, emit multiple typed records in one audited batch.
- Keep checkpoint output orientation-only until explicit evidence/validation/trust surfaces are invoked.

Phase 3 implementation:

- Module: `brain/v5/quiet_checkpoint.py`
- Contracts: `brain/v5/quiet_checkpoint_contracts.py`
- Public surfaces: `quiet_checkpoint_batch`, `quiet_checkpoint_preview`
- CLI: `aitp-v5 checkpoint preview-batch <session-id> ...`, `aitp-v5 checkpoint apply-batch <session-id> ...`
- MCP: `aitp_v5_preview_quiet_checkpoint_batch`, `aitp_v5_apply_quiet_checkpoint_batch`
- Recording integration: `quiet_checkpoint:<id>` batch refs are accepted by canonical `record_ref_lookup` and `recording_effect_verification`; process graph includes quiet checkpoint nodes.
- Trust boundary: apply can write selected artifact/source/tool-run/sensemaking/run-iteration records and the checkpoint envelope, but cannot create evidence, validation results, L2 memory, or claim-trust updates.

### AuthorityRegistry

Purpose: record the currently adopted definition, sector decomposition, convention, dataset, or code path as a research authority without promoting claim trust.

Target authority types:

- `sector_authority`
- `statistics_convention`
- `formula_convention`
- `dataset_authority`
- `code_path_authority`

Phase 2 implementation:

- Model additions: `brain/v5/models.py::AuthorityRecord`
- Registry path: `registry/authorities`
- APIs: `brain/v5/authorities.py`, `brain/v5/cli_authorities.py`, `brain/v5/mcp_tools.py::aitp_v5_record_authority`, `aitp_v5_list_authorities`
- Public surface: `authority_record`, `authority_registry`
- CLI: `aitp-v5 authority record ...`, `aitp-v5 authority list --topic <topic>`
- MCP: `aitp_v5_record_authority`, `aitp_v5_list_authorities`

Important boundary: an authority record can support research routing and statistics gating, but cannot update claim confidence.

### CompactBriefAPI

Purpose: default to a 20-40 line continuation view and require explicit expansion for full relation-map audit.

Phase 1 implementation:

- Module: `brain/v5/objective_graph.py::build_compact_brief`
- Public surface: `compact_execution_brief`
- CLI: `aitp-v5 status compact-brief <session-id>`
- MCP: `aitp_v5_get_compact_brief`
- Expansion pointers: full execution brief, full relation map, objective graph

### ResearchDistillationCandidates

Purpose: compile recorded research process into reusable-block candidates without turning summaries into truth.

Implemented behavior:

- Module: `brain/v5/research_distillation.py`
- Public surface: `research_distillation_candidates`
- CLI: `aitp-v5 status distillation-candidates <session-id> [--limit N]`
- MCP: `aitp_v5_get_research_distillation_candidates`
- Inputs: session binding, ObjectiveGraph, execution brief, claim relation map, run iteration journals, final output profile
- Candidate kinds: `workflow_recipe_candidate`, `method_capsule_candidate`, `physics_semantic_fragment_candidate`, `failure_playbook_candidate`, `handoff_profile_candidate`
- Required gates: scoped problem, reproducible steps, provenance refs, validation boundary, failure/stop-rule boundary, reuse boundary, and physics semantics where applicable
- Trust boundary: read-only, orientation-only, no skill creation, no L2 memory creation, no kernel mutation, no claim-trust mutation

This component is the second-layer bridge. It answers whether the first-layer records contain enough structured material to draft a reusable workflow or physics fragment. It does not answer whether the physics claim is true; promotion still requires the existing evidence, validation, trust preflight, and human gates.

### AITPContextPack

Purpose: compile the bounded AITP continuation state into a Codex-friendly turn-input fragment without turning summaries into memory or trust.

Implemented behavior:

- Module: `brain/v5/context_pack.py`
- Contract: `brain/v5/context_pack_contracts.py`
- Public surface: `aitp_context_pack`
- CLI: `aitp-v5 status context-pack <session-id> [--max-lines N] [--candidate-limit N]`
- MCP: `aitp_v5_get_context_pack`
- Inputs: CompactBrief and ResearchDistillationCandidates
- Host intent: suitable for a future Codex `TurnInputContributor`; current plugin/skill path can call it explicitly
- Injection policy: inject on first restoration, fingerprint change, or explicit user request; avoid repeated injection for the same fingerprint
- Trust boundary: read-only, orientation-only, no evidence, no validation, no L2 memory, no skill creation, no claim-trust mutation

### NoteOutlineCompiler

Purpose: compile ObjectiveGraph, AuthorityRegistry, and typed research records into a publication/research-note outline coverage surface.

Implemented behavior:

- Module: `brain/v5/note_outline.py`
- Contract: `brain/v5/note_outline_contracts.py`
- Public surface: `note_outline`
- CLI: `aitp-v5 status note-outline <session-id> [--style jhep]`
- MCP: `aitp_v5_compile_note_outline`
- Inputs: session binding, ObjectiveGraph, research-distillation candidates, authority records, claims, source assets, artifacts, tool runs, physics objects, object relations, sensemaking reports, proof obligations, claim statuses, evidence, validation results
- Section readiness: each section is `draftable` only when its required first-layer record types are present; otherwise it returns `missing_requirements` and `recommended_record_actions`
- Hidden-symmetry template: problem/scope, model/conventions, algebraic method, generic alpha, alpha=2, alpha=infinity, level statistics, limitations, appendices
- Trust boundary: read-only, orientation-only, no note writing, no skill creation, no L2 memory creation, no kernel mutation, no claim-trust mutation

This is the second-layer writing/planning bridge. It can say "the alpha=2 section has enough typed support to draft" or "the alpha=infinity section still lacks source records"; it cannot say the section is physically validated.

## 3. Schema Drafts

Implemented Phase 1 `objective_graph` payload:

```json
{
  "kind": "objective_graph",
  "topic_id": "hs-chain",
  "session_id": "s1",
  "current_objective": {
    "objective_id": "objective-hs-chain",
    "title": "Long-range Heisenberg chain",
    "source": "topic_record",
    "status": "active"
  },
  "active_work_packages": [
    {
      "work_package_id": "wp-claim-...",
      "title": "Alpha=2 sectors should be resolved before level-statistics conclusions.",
      "status": "active",
      "claim_ids": ["claim-..."],
      "artifact_ids": [],
      "research_run_ids": [],
      "blockers": [],
      "next_action": "",
      "source": "claim_record"
    }
  ],
  "claims": [],
  "artifacts": [],
  "deliverables": [],
  "blockers": [],
  "orientation_only": true,
  "summary_inputs_trusted": false,
  "can_update_kernel_state": false,
  "can_update_claim_trust": false
}
```

Implemented Phase 1 `compact_execution_brief` payload:

```json
{
  "kind": "compact_execution_brief",
  "session_id": "s1",
  "topic_id": "hs-chain",
  "current_objective": {},
  "active_work_package": {},
  "relevant_claims": [],
  "can_say": [],
  "cannot_say": [],
  "blockers": [],
  "next_valid_actions": [],
  "recent_relevant_artifacts": [],
  "expand": {
    "full_execution_brief_cli": "aitp-v5 brief s1",
    "full_relation_map_cli": "aitp-v5 relation-map s1",
    "objective_graph_cli": "aitp-v5 status objective-graph s1"
  },
  "lines": [],
  "line_count": 0,
  "orientation_only": true,
  "can_update_claim_trust": false
}
```

Implemented `research_distillation_candidates` payload:

```json
{
  "kind": "research_distillation_candidates",
  "topic_id": "qsgw-ac-error-molecules",
  "session_id": "s-qsgw",
  "active_claim_id": "claim-...",
  "candidate_count": 1,
  "candidates": [
    {
      "candidate_id": "distill-h2o-ridge-pade-20260608-gap-audit",
      "candidate_kind": "method_capsule_candidate",
      "distillation_state": "draftable",
      "can_draft_reusable_block": true,
      "can_materialize_without_human_review": false,
      "can_promote_claim_trust": false,
      "missing_requirements": [],
      "target_surfaces": ["lane_exemplar_record", "tool_recipe_record", "sensemaking_report_record", "validation_contract_record"],
      "reuse_boundary": {
        "scope": "H2O QSGW first-iteration same-base diagnostic only",
        "non_claims": ["Not molecule-general and not a default LibRPA setting."]
      },
      "orientation_only": true
    }
  ],
  "distillation_boundary": {
    "does_not_create_skills": true,
    "does_not_create_l2_memory": true,
    "does_not_update_claim_trust": true,
    "requires_human_review_before_materialization": true
  },
  "orientation_only": true,
  "can_update_kernel_state": false,
  "can_update_claim_trust": false
}
```

Implemented `aitp_context_pack` payload:

```json
{
  "kind": "aitp_context_pack",
  "designed_for_host": "codex",
  "session_id": "s-qsgw",
  "topic_id": "qsgw-ac-error-molecules",
  "fingerprint": "sha256...",
  "injection_policy": {
    "recommended_hook": "TurnInputContributor",
    "recommended_authority": "contextual_user_fragment",
    "requires_explicit_expand_for": [
      "claim trust updates",
      "evidence support decisions",
      "validation status decisions",
      "full relation-map audit",
      "workflow or skill materialization"
    ]
  },
  "materialization_boundary": {
    "can_create_skill": false,
    "requires_human_review_before_materialization": true
  },
  "orientation_only": true,
  "can_update_kernel_state": false,
  "can_update_claim_trust": false
}
```

Implemented `authority_record` payload:

```json
{
  "ok": true,
  "kind": "authority",
  "authority_id": "authority-hs-alpha2-sector",
  "topic_id": "hs-chain",
  "authority_type": "sector_authority",
  "authority_statement": "Use coefficient-discovered {J0,Q} associative/Yangian motif sectors for alpha=2 sector labels.",
  "work_package": "WP2 alpha=2 HS Yangian/motif sector authority",
  "scope": {
    "alpha_class": "alpha=2",
    "sizes": [5, 6, 7],
    "formula_extension": "L<=16"
  },
  "generator_set": "{J0,Q}",
  "closure_envelope": "Yangian/associative",
  "evidence_refs": [],
  "source_refs": [],
  "artifact_ids": [],
  "limitations": [
    "not all-L Yangian proof",
    "sector-internal P(r) undefined when H is scalar"
  ],
  "status": "research_authority_not_trust_promotion",
  "summary_inputs_trusted": false,
  "orientation_only": true,
  "can_update_claim_trust": false
}
```

Implemented `quiet_checkpoint_batch` payload:

```json
{
  "kind": "quiet_checkpoint_batch",
  "checkpoint_id": "quiet-checkpoint-...",
  "topic_id": "hs-chain",
  "session_id": "s1",
  "claim_id": "claim-...",
  "run_id": "quiet-checkpoint-...",
  "summary": "Alpha=2 sector burst produced finite certificates and a proof-gap note.",
  "inputs": [],
  "outputs": [],
  "changed_files": [],
  "generated_artifacts": [],
  "validation_commands": [],
  "durable_observations": [],
  "claim_boundary": {
    "can_say": [],
    "cannot_say": [],
    "non_claims": []
  },
  "next_blockers": [],
  "status": "recorded_without_trust_promotion",
  "planned_typed_writes": [],
  "written_refs": [],
  "summary_inputs_trusted": false,
  "orientation_only": true,
  "can_update_kernel_state": true,
  "can_update_claim_trust": false
}
```

Implemented `note_outline` payload:

```json
{
  "kind": "note_outline",
  "outline_id": "note-outline:quantum-chaos-long-range-spin-chains:s-hs:jhep",
  "topic_id": "quantum-chaos-long-range-spin-chains",
  "session_id": "s-hs",
  "style": "jhep",
  "active_claim_id": "claim-...",
  "sections": [
    {
      "section_id": "alpha_2",
      "title": "Alpha=2 Sector",
      "readiness_state": "draftable",
      "record_refs": {
        "authorities": ["authority:authority-..."],
        "object_relations": ["object_relation:object-relation-..."]
      },
      "source_refs": ["source_asset:hs-alpha-axis-notes"],
      "missing_requirements": [],
      "trust_boundary": "Section outline only; draft from typed records and validate claims separately.",
      "orientation_only": true
    },
    {
      "section_id": "alpha_infinity",
      "title": "Alpha=Infinity Limit",
      "readiness_state": "needs_records",
      "missing_requirements": ["source_assets"],
      "recommended_record_actions": [
        {
          "action": "complete_first_layer_records",
          "record_type": "source_assets"
        }
      ],
      "orientation_only": true
    }
  ],
  "note_boundary": {
    "does_not_write_note": true,
    "does_not_create_skills": true,
    "does_not_create_l2_memory": true,
    "does_not_update_claim_trust": true,
    "requires_human_review_before_publication": true
  },
  "orientation_only": true,
  "can_update_kernel_state": false,
  "can_update_claim_trust": false
}
```

## 4. CLI/MCP API Drafts

Implemented:

- `aitp-v5 status objective-graph <session-id>`
- `aitp-v5 status compact-brief <session-id> [--max-lines N]`
- `aitp-v5 status context-pack <session-id> [--max-lines N] [--candidate-limit N]`
- `aitp-v5 status distillation-candidates <session-id> [--limit N]`
- `aitp-v5 status note-outline <session-id> [--style jhep] [--candidate-limit N]`
- `aitp-v5 authority record --topic <topic> --type <authority-type> --statement <text> ...`
- `aitp-v5 authority list --topic <topic> [--work-package <id>]`
- `aitp-v5 checkpoint preview-batch <session-id> --summary <text> ...`
- `aitp-v5 checkpoint apply-batch <session-id> --summary <text> ...`
- `aitp_v5_get_objective_graph(base, session_id=...)`
- `aitp_v5_get_compact_brief(base, session_id=..., max_lines=40)`
- `aitp_v5_get_context_pack(base, session_id=..., max_lines=60, candidate_limit=3)`
- `aitp_v5_get_research_distillation_candidates(base, session_id=..., limit=8)`
- `aitp_v5_compile_note_outline(base, session_id=..., style="jhep", candidate_limit=8)`
- `aitp_v5_record_authority(...)`
- `aitp_v5_list_authorities(...)`
- `aitp_v5_preview_quiet_checkpoint_batch(...)`
- `aitp_v5_apply_quiet_checkpoint_batch(...)`

## 5. Minimal Implementation Steps

Phase 1, implemented:

- Add read-only ObjectiveGraph projection.
- Add compact brief public surface.
- Add read-only research-distillation candidate compiler.
- Add CLI/MCP entrypoints.
- Register runtime entrypoints.
- Add tests proving old brief remains usable and new compact brief stays short/read-only.
- Add tests proving reusable-block candidates remain candidate-only and surface missing first-layer gates.

Phase 2, implemented:

- Add `AuthorityRecord` dataclass and registry family.
- Add authority write/list CLI/MCP.
- Add contracts that hard-code `can_update_claim_trust=false`.
- Add policy test: authority refs cannot satisfy trust update or promotion gates.

Phase 3, implemented:

- Add quiet checkpoint preview/apply surfaces.
- Batch typed write plans for artifacts/source assets/tool runs/sensemaking/run iterations.
- Extend `recording_effect_verification` with batch ref checks.
- Keep checkpoint application separate from trust preflight or promotion.

Phase 4, implemented:

- Add note outline compiler skeleton.
- Compile sections from ObjectiveGraph, AuthorityRegistry, and typed records.
- Initial target outline: model, method, generic alpha, alpha=2, alpha=infinity, level statistics, limitations, appendices.
- Keep section readiness distinct from physics validation or claim trust.

Phase 5, implemented:

- Add Codex-friendly `aitp_context_pack` surface.
- Add stable pack fingerprint and `pack_id`.
- Add explicit Codex injection policy for future `TurnInputContributor` integration.
- Merge compact brief and distillation gate summary without materializing skills or L2 memory.
- Keep the full relation map as an explicit expansion path.

## 6. Test Plan

Implemented tests:

- `tests/test_v5_authorities.py`
- `tests/test_v5_quiet_checkpoint.py`
- `tests/test_v5_note_outline.py`
- `tests/test_v5_context_pack.py`
- `tests/test_v5_research_distillation.py`
- `tests/test_v5_objective_graph_compact_brief.py`
- `tests/test_v5_public_surfaces.py`
- `tests/test_v5_runtime_entrypoints.py`
- `tests/test_v5_trust_updates.py`
- `tests/test_v5_recording_navigator.py`
- `tests/test_v5_cli.py`

Executed validation:

```text
uv run --with pytest --with pyyaml --with jsonschema --with fastmcp python -m pytest \
  tests/test_v5_context_pack.py \
  tests/test_v5_authorities.py \
  tests/test_v5_quiet_checkpoint.py \
  tests/test_v5_note_outline.py \
  tests/test_v5_research_distillation.py \
  tests/test_v5_objective_graph_compact_brief.py \
  tests/test_v5_public_surfaces.py \
  tests/test_v5_runtime_entrypoints.py \
  tests/test_v5_trust_updates.py \
  tests/test_v5_recording_navigator.py \
  tests/test_v5_cli.py
```

Result: 82 passed.

Context-pack slice validation:

```text
uv run --with pytest --with pyyaml --with jsonschema --with fastmcp python -m pytest \
  tests/test_v5_context_pack.py \
  tests/test_v5_objective_graph_compact_brief.py \
  tests/test_v5_research_distillation.py \
  tests/test_v5_public_surfaces.py \
  tests/test_v5_runtime_entrypoints.py -q
```

Result: 36 passed.

Future tests:

- Statistics gates reject final P(r) if no matching sector/statistics authority exists.

## 7. Risks and Compatibility

Compatibility preserved:

- Existing `build_execution_brief` payload is unchanged.
- Existing `build_claim_relation_map` payload is unchanged.
- Existing `SessionBinding.active_claim` remains unchanged.
- Existing recording navigation/write/verify surfaces remain unchanged.
- New surfaces are additive and read-only.

Risks:

- ObjectiveGraph is currently inferred; it may group work packages too coarsely until explicit Objective/WorkPackage records exist.
- Compact brief uses relation-map conclusions, so relation-map compute cost is still paid internally in Phase 1. Later optimization can add a direct compact relation-map builder.
- AuthorityRegistry must not be allowed to become a trust shortcut. Current policy tests block authority-only trust preflight, and future authority-dependent gates should keep this boundary.
- Quiet checkpoint apply could become a bulk trust bypass if it writes evidence without validation gates. It should write records only through existing typed write functions and policy checks.
- NoteOutline could be mistaken for a paper-ready conclusion if downstream agents ignore section `missing_requirements`. It is therefore registered as an orientation-only/trust-blocked source kind.

## 8. Real Topic Optimization Examples

The implementation was calibrated against existing topic shapes in `F:/AI_Workspace/Theoretical-Physics/research/aitp-topics`.

- `qsgw-ac-error-molecules`: run iteration journals already contain plan/checks/deliverables/L3 synthesis/L4 return/decision/stop rules. These can form a `method_capsule_candidate`, but only inside the H2O/same-base diagnostic scope and with no trust update.
- `quantum-chaos-long-range-spin-chains`: relation-map and run records expose finite symbolic certificates plus open all-L proof obligations. These can form a `physics_semantic_fragment_candidate`, not a theorem or promoted memory.
- `quantum-chaos-long-range-spin-chains` note outline: alpha=2 sections can become `draftable` when authority/object-relation/sensemaking records exist, while alpha=infinity or all-L theorem sections remain `needs_records` until their source/proof records are added.
- `qsgw-headwing-update-librpa`: final/diagnostic lane contradictions and stale artifacts should appear as missing gates or blockers before any final-lane workflow is reusable.

The design implication is that AITP first records typed points and relations, then the compiler checks whether the typed graph is complete enough for a second-layer candidate. If not, it returns the missing first-layer records instead of inventing a polished workflow.

## 9. Hidden-Symmetry Migration Example

Objective:

```json
{
  "objective_id": "objective-hs-sector-statistics-note",
  "title": "Complete hidden symmetry and sector-resolved level statistics for the long-range Heisenberg chain, then assemble a JHEP-style note",
  "status": "active"
}
```

Work packages:

```json
[
  {
    "work_package_id": "wp-generic-finite-alpha",
    "title": "Generic finite-alpha symmetry and sector authority",
    "claim_ids": ["claim-generic-alpha-family-common-center"],
    "authority_ids": ["authority-generic-alpha-matrix-unit-center"]
  },
  {
    "work_package_id": "wp-alpha2-yangian",
    "title": "Alpha=2 HS Yangian/motif sector authority",
    "claim_ids": ["claim-alpha2-yangian-motif-sector"],
    "authority_ids": ["authority-alpha2-j0-q-sector"]
  },
  {
    "work_package_id": "wp-alpha-infinity-xxx",
    "title": "Alpha=infinity XXX integrability sector authority",
    "claim_ids": ["claim-alpha-infinity-lie-casimir-sector"],
    "authority_ids": ["authority-alpha-infinity-convention-pending"]
  },
  {
    "work_package_id": "wp-final-level-statistics",
    "title": "Final level statistics under resolved sectors",
    "claim_ids": ["claim-sector-resolved-pr-final"],
    "required_authority_types": ["sector_authority", "statistics_convention"]
  },
  {
    "work_package_id": "wp-jhep-note",
    "title": "JHEP note assembly",
    "deliverables": ["artifact-jhep-note-outline", "artifact-jhep-note-draft"]
  }
]
```

Authority examples:

```json
[
  {
    "authority_type": "sector_authority",
    "work_package_id": "wp-generic-finite-alpha",
    "authority_statement": "Use matrix-unit family-common center as the generic finite-alpha sector authority.",
    "limitations": ["does not settle alpha=2 motif/Yangian labels", "all-L proof obligations remain explicit"]
  },
  {
    "authority_type": "sector_authority",
    "work_package_id": "wp-alpha2-yangian",
    "authority_statement": "Use coefficient-discovered {J0,Q} associative/Yangian motif sectors for alpha=2.",
    "limitations": ["not all-L Yangian proof", "sector-internal P(r) undefined when H is scalar"]
  },
  {
    "authority_type": "statistics_convention",
    "work_package_id": "wp-alpha-infinity-xxx",
    "authority_statement": "XXX-sector convention remains pending between coefficient Lie/Casimir sectors and transfer/Bethe labels.",
    "status": "pending_research_authority"
  }
]
```

Expected compact brief behavior:

- Default brief shows current objective and active work package.
- It lists only relevant claims for the active work package.
- It states what can/cannot be said about the current sector convention.
- It keeps final P(r) actions blocked until the matching statistics authority exists.
- Full relation-map expansion remains explicit for audit or recovery.

Expected note-outline behavior:

- `Model, Sectors, And Statistics Conventions` is draftable only when physics objects and authority records exist.
- `Alpha=2 Sector` is draftable only when an authority record and object relation support the section.
- `Alpha=Infinity Limit` remains `needs_records` if no dedicated source/proof/authority records exist, even if the global topic is already active.
- `Level Statistics And Finite Certificates` remains a diagnostic section until validation/evidence gates are separately satisfied.
