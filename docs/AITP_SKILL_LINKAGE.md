# AITP Skill Linkage Architecture

AITP can work with external skills without turning those skills into a second
research memory. The boundary is simple:

- AITP owns the typed research graph, context compiler, provenance records,
  validation gates, human checkpoints, trust updates, and promoted memory.
- External skills own domain operating knowledge: workflow routing, file intake,
  preflight checks, templates, rule cards, repair patterns, and execution
  discipline.
- Execution briefs expose skill references as orientation-only guidance. A skill
  reference never supports a claim by itself.

This makes AITP the AI research memory layer while letting domain projects make
the agent behave like a more experienced researcher in a specific area.

## Why This Layer Exists

The AITP kernel should not contain every domain workflow. If LibRPA, quantum
field theory, quantum gravity, or another domain evolves, the domain knowledge
should be updateable as a skill bundle while AITP keeps a stable memory and trust
model.

The linkage layer answers four questions:

1. Which external skill should an agent load for this active claim or topic?
2. Which domain manifest, rule cards, templates, or runbooks define that skill's
   operating contract?
3. Which typed AITP records must be written after the skill does meaningful work?
4. Which outputs are only orientation and cannot update claim trust?

## Runtime Flow

```text
active claim or topic
        |
        v
AITP domain pack suggestion
        |
        v
execution brief exposes orientation-only skill_refs and manifest_refs
        |
        v
host agent loads the external skill bundle
        |
        v
skill performs file intake, routing, preflight, execution, debug, or reporting
        |
        v
durable moments are recorded back into AITP typed records
        |
        v
validation and trust gates decide what can become evidence or memory
```

## Brief Payload Contract

Execution briefs may expose domain packs under:

```text
known_context.domain_packs[]
```

Each pack can include:

- `pack_id` and `domain`
- `description`
- `suggested_question_intents`
- `risk_signals`
- `tool_recipes`
- `skill_refs`
- `manifest_refs`
- `integration_boundary`
- `truth_standard_policy`
- `orientation_only=true`

The `orientation_only` flag is part of the public contract. Domain pack data may
tell an agent what to load or check next, but it must not update kernel state,
claim trust, or long-term memory.

## External Skill Reference Shape

AITP uses lightweight references instead of vendoring the skill into the kernel:

```json
{
  "skill_id": "oh-my-librpa",
  "kind": "external_skill_bundle",
  "repo": "https://github.com/AroundPeking/oh-my-LibRPA",
  "entrypoint": "skills/oh-my-librpa/SKILL.md",
  "role": "chat-first front router for ABACUS/FHI-aims + LibRPA workflows",
  "load_when": [
    "LibRPA GW or RPA computation is requested",
    "ABACUS or FHI-aims source bundles, logs, or run artifacts need intake",
    "a first-principles workflow needs route selection, preflight, execution, or debug guidance"
  ],
  "required_followup_records": [
    "code_state",
    "tool_recipe",
    "tool_run",
    "artifact",
    "evidence",
    "validation_contract",
    "validation_result"
  ],
  "orientation_only": true
}
```

The host decides how to load the referenced skill. AITP only records the fact
that this is the right domain experience to consult.

## oh-my-LibRPA Mapping

`oh-my-LibRPA` is the first concrete domain skill bundle for this architecture.
It should live above the AITP kernel as the LibRPA/GW first-principles
experience layer.

| Concern | AITP responsibility | oh-my-LibRPA responsibility |
| --- | --- | --- |
| Research memory | Typed claims, evidence, code state, tool runs, validation, trust, L2 memory | No independent scientific truth layer |
| Context | Execution brief and domain pack recommendation | Load route-specific skill files, rule cards, templates, and runbooks |
| Workflow | Record route choice, run provenance, validation contracts, and outputs | Classify molecule/solid/2D, ABACUS/FHI-aims ownership, GW/RPA/debug/build path |
| Safety | Prevent trust updates without typed evidence and validation | Fresh run directories, static preflight, no overwrite, compute-location handshake |
| Evidence | Evidence records linked to claims, sources, artifacts, tool runs, validation results | Markdown run reports, logs, plots, stage summaries, checks, and artifacts |
| Promotion | Human-gated promotion packets and memory entries | No direct promotion authority |

For LibRPA/GW claims, the built-in `gw_librpa` domain pack now exposes these
external references:

- `oh-my-librpa` as the front router skill.
- `oh-my-librpa-abacus-librpa` as the ABACUS -> LibRPA stack skill.
- `oh-my-librpa-fhi-aims-qsgw` as the FHI-aims -> LibRPA stack skill.
- `registry/domain-manifest.abacus-librpa.json` as the domain operations and
  invariant manifest.
- `docs/aitp-integration.md` as the external integration guide.

## Return Path Into AITP

When an external skill produces something durable, the agent should map it back
into AITP records:

| Skill output | AITP record |
| --- | --- |
| Source bundle, uploaded archive, local paper, existing run directory | `source_asset` or `reference_location` |
| Code checkout, branch, commit, local patches, build metadata | `code_state` |
| Preflight command, route materialization, workflow script | `tool_recipe` |
| SCF, pyatb, NSCF, LibRPA, plotting, benchmark, or debug run | `tool_run` |
| Report, plot, table, log bundle, generated input set, archive | `artifact` |
| Claim-relevant observation from a run or source | `evidence` |
| Planned check for a claim-critical run | `validation_contract` |
| Result of a check against the contract | `validation_result` |
| Ambiguous route, expensive compute, promotion, or failure-mode review | `human_checkpoint` |
| Reusable method or result after evidence, validation, and approval | `promotion_packet` and memory entry |

The skill may create run reports and archives, but those reports are artifacts,
not trusted memory. They become support for a claim only after the appropriate
evidence and validation records are created.

## Extension Pattern For QFT And QG

The same pattern should be used for theory and literature domains:

- A QFT or quantum-gravity skill bundle can contain reading routes, notation
  conventions, source maps, concept dependencies, and failure modes.
- A literature connector or corpus can retrieve PDFs, notes, sections,
  equations, and figures.
- The execution brief can expose those connectors or skills as
  orientation-only context.
- Claim support still requires exact source assets, reference locations,
  evidence records, proof obligations, validation or reconstruction checks, and
  human-gated promotion.

This keeps "understanding physics" grounded in inspectable sources and typed
claim support rather than hidden prompt state.

## Non-Goals

- Do not copy every external skill file into AITP core.
- Do not let a skill write directly into `.aitp/registry` without typed tools.
- Do not treat a run report, summary, rule card, or retrieved note as evidence
  by default.
- Do not let domain pack recommendations override global trust policy.
- Do not use domain skill activation as proof that the underlying science or
  computation is correct.

## Implementation Roadmap

1. Expose `skill_refs` and `manifest_refs` from domain packs in execution
   briefs.
2. Add host-adapter support for loading referenced skill bundles when the host
   supports explicit skill loading.
3. Add project-scope shim generation for external domain skills so Codex,
   Claude Code, Kimi Code, and other hosts can discover the same bundle without
   duplicating it.
4. Add recording-navigation recipes that map common external skill outputs into
   the correct typed AITP write surface.
5. Add domain pack manifests for QFT, quantum gravity, and other literature
   domains using the same orientation-only contract.
