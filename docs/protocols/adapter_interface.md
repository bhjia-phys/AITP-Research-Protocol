# Adapter Interface

Domain: Interaction
Authority: subordinate to AITP SPEC S12.
Merges: AGENT_CONFORMANCE_PROTOCOL.md.

---

## AD1. Role

Agent platforms (Claude Code, Codex, OpenClaw, OpenCode, and future agents)
execute AITP through adapters. Adapters are protocol executors, not protocol
definers (Charter Article 10).

## AD2. Adapter Obligations

Every adapter MUST:

1. **Load the AITP skill at session start** — the `using-aitp` skill
   determines whether AITP should be activated for the current request.

2. **Route through the front-door** — user requests must go through AITP's
   front-door before free-form processing. The front-door decides whether
   the request is an AITP topic action, a topic continuation, or a non-AITP
   task.

3. **Produce required artifacts** — every AITP run must leave the required
   artifacts on disk: topic state, action decisions, decision traces,
   runtime bundles.

4. **Handle popups** — when the Brain activates a popup gate, the adapter
   must present the popup to the human and return the chosen option.

5. **Maintain conformance** — a run may claim to be AITP work only if it
   passes declared conformance checks (Charter Article 9).

6. **Respect the Charter** — adapters may add convenience, but may NOT weaken
   evidence discipline, artifact discipline, or promotion discipline.

## AD3. Conformance Requirements

A conformant AITP run must have:

- topic state artifact that is well-formed and up-to-date,
- all required mode transitions recorded in the decision trace,
- promotion gates respected (no L2 writes without human approval),
- evidence levels not silently merged,
- uncertainty markers preserved (gaps recorded, not hidden),
- mode envelopes followed (no forbidden transitions),
- session chronicle produced at session end.

### Implementation Status

Conformance is declared but NOT YET operationally checked. No adapter
currently implements a conformance verification step that validates these
requirements at session end. The session chronicle is produced as soft
guidance rather than a hard requirement.

Non-conformant runs may still produce useful work, but they may not claim
AITP conformance.

## AD4. Popup Gate Protocol

When the Brain activates a popup gate, the adapter must:

1. Call `aitp_get_topic_popup(topic_slug=<current>)`.
2. If `kind` is `"none"`, continue normally.
3. If `kind` is not `"none"`, a human-blocking gate is active. Stop all
   other work.
4. Present the popup with title, summary, and options.
5. Once the user chooses, call
   `aitp_resolve_popup_choice(topic_slug=<current>, choice=<index>,
   comment="<rationale>")`.
6. Only after resolution should the adapter continue.

### Platform-Specific Popup Handling

- **Claude Code**: `AskUserQuestion` tool with structured options.
- **OpenCode**: `question` tool or numbered Markdown list fallback.
- **Other platforms**: Render as natural-language text with numbered options.

This popup gate protocol is implemented in the `using-aitp` skill and is
NOT described in the original adapter interface protocol.

## AD5. Conversation Style Rules

The `using-aitp` skill enforces conversation style rules that adapters
must respect:

- Do not expose protocol jargon to users (no `decision_point`, `L2
  consultation`, `load profile`, `runtime surface`).
- Ask in plain language, as if you are a research collaborator.
- Ask one question at a time by default.
- If the user says "just go", "直接做", or equivalent, record authorization
  durably and continue.
- When giving options, explain routes and tradeoffs in natural language.

## AD6. Clarification Sub-Protocol

When the research question contract has vague scope, assumptions, or target
claims:

1. Tighten the active contract before substantive execution.
2. Ask at most 3 clarification rounds, with 1-3 questions per round.
3. Prefer questions that remove the biggest ambiguity first.
4. If the human says "skip clarification", proceed and mark missing fields
   as `clarification_deferred: true`.
5. Only enter normal L0-L4 routing after clarification is complete or
   explicitly skipped.

This sub-protocol is implemented in the `using-aitp` skill.

## AD7. Runtime Support Matrix

Each adapter platform has a different level of AITP support:

| Feature | Claude Code | Codex | OpenCode | OpenClaw |
|---------|-------------|-------|----------|----------|
| AITP skill loading | Auto (CLAUDE.md) | .codex/ config | opencode.json | Plugin manifest |
| Front-door routing | Full | Full | Partial | Bypasses |
| Popup handling | AskUserQuestion | Question tool | Question tool | Plugin UI |
| Hook integration | Full | Partial | None | None |
| Session chronicle | Produced | Not verified | Not verified | Not verified |
| Conformance checking | Declared only | Declared only | Declared only | Declared only |

### Front-Door Routing Notes

OpenClaw currently bypasses the front-door routing. User requests go directly
to processing without the AITP front-door deciding whether the request is
an AITP topic action. This is a known conformance gap.

## AD8. Platform-Specific Adapters

### Claude Code
- Integration: hooks (posttooluse, pretooluse, stop, userpromptsubmit).
- Skill loading: CLAUDE.md / AGENTS.md auto-load.
- Popup handling: AskUserQuestion tool.
- Install: `docs/INSTALL_CLAUDE_CODE.md`.

### Codex
- Integration: `.codex/` configuration.
- Skill loading: Codex skill system.
- Popup handling: native question mechanism.
- Install: `docs/INSTALL_CODEX.md`.

### OpenClaw
- Integration: plugin system.
- Skill loading: plugin manifest.
- Popup handling: plugin UI.
- Install: `docs/INSTALL_OPENCLAW.md`.
- **Known gap:** Bypasses front-door routing.

### OpenCode
- Integration: `opencode.json` plugin.
- Skill loading: plugin configuration.
- Popup handling: question tool or numbered Markdown list.
- Install: `docs/INSTALL_OPENCODE.md`.

### New Platforms
New adapters should:
1. Implement the six obligations from AD2.
2. Provide an install guide.
3. Map platform-specific mechanisms to AITP protocol actions.
4. Implement popup gate protocol (AD4).
5. Implement clarification sub-protocol (AD6).
6. Not redefine the protocol.

## AD9. Domain Skills

Domain skills are adapters that provide domain-specific tools, knowledge, and
workflow templates for particular physics subfields (e.g., DFT calculations,
many-body methods, lattice models). Unlike platform adapters (Claude Code,
Codex, etc.) which adapt AITP to an agent platform, domain skills adapt AITP
to a research domain.

### Domain Skill Interface

Every domain skill MUST:

1. **Declare its domain scope** — which physics subfield and which methods it
   covers.
2. **Provide L3-P templates** — workflow plans that the Brain can use when
   dispatching to L3-P (Planning) in `learn` or `implement` modes.
3. **Expose tool interfaces** — CLI commands, scripts, or API endpoints that
   L3-A (Analysis) can invoke during plan execution.
4. **Define L4 validation rules** — domain-specific criteria for what counts
   as a passed validation (convergence thresholds, symmetry checks, etc.).
5. **Reference L2 canonical knowledge** — link to established methods, theorems,
   and parameter conventions that belong in L2.

### Domain Skill Registration

Domain skills are registered in the adapter manifest with type `domain`:

```json
{
  "type": "domain",
  "name": "oh-my-librpa",
  "domain": "first-principles-many-body",
  "methods": ["GW", "BSE", "RPA"],
  "templates": ["gw-convergence-plan", "bse-spectrum-plan"],
  "tools": ["librpa-cli", "abacus-interface"],
  "l4_rules": ["energy-convergence", "symmetry-check"]
}
```

### Integration Points

| AITP Layer | Domain Skill Role |
|-----------|------------------|
| L3-P | Provide workflow templates for domain-specific plans |
| L3-A | Execute plans using domain tools |
| L4 | Apply domain-specific validation criteria |
| L2 | Reference domain canonical knowledge (methods, parameters) |

Domain skills do NOT modify the Brain, mode envelope, or layer model. They
extend the tool surface available to L3 and L4.

## AD10. Adapter Boundary

Adapters may:
- Add convenience commands and shortcuts.
- Optimize context loading for their platform.
- Customize display of topic state and dashboards.
- Add platform-specific tool integrations.

Adapters may NOT:
- Redefine the layer model.
- Weaken evidence or promotion discipline.
- Skip required artifacts.
- Auto-promote to L2 without human approval.
- Treat their platform's capabilities as a substitute for protocol compliance.
- Bypass the front-door routing.
- Expose protocol jargon to users.

## AD11. Agent Model

The agent that runs AITP is:
- a protocol executor, not a protocol author,
- persistent across sessions within a topic,
- capable of reading and writing durable artifacts,
- able to call AITP CLI tools or MCP tools,
- responsible for following the mode envelope.

The agent does NOT:
- invent the research workflow in hidden logic,
- silently upgrade claims,
- weaken research contracts into prose-only summaries,
- substitute proxy-success signals for declared validation evidence,
- replace missing contracts with unrestricted heuristics.

## AD12. Skill System

AITP provides two core skills:

### using-aitp (session start)
- Determines whether AITP should be activated.
- Routes to AITP front-door or normal processing.
- Implements popup gate protocol, clarification sub-protocol, and
  conversation style rules.
- Location: `skills/using-aitp/SKILL.md`.

### aitp-runtime (after activation)
- Reads the runtime bundle.
- Follows the protocol.
- Emits decisions and artifacts.
- Location: `skills/aitp-runtime/SKILL.md`.

Adapters must ensure that at least the `using-aitp` skill is loaded at
session start.

## AD13. Charter Document

The Charter document defines the constitutional rules for AITP. Adapters
must respect the Charter as the highest authority in the protocol hierarchy.

**Implementation note:** A standalone Charter document does NOT YET EXIST.
Charter articles are referenced throughout the SPEC and protocol documents
but have not been consolidated into a single Charter.md file. This is a
known gap.

## AD14. Implementation Status

### Currently implemented
- Claude Code adapter with full hook integration.
- AITP skill loading at session start (using-aitp, aitp-runtime).
- Popup gate protocol with structured options (Claude Code, OpenCode).
- Conversation style rules in using-aitp skill.
- Clarification sub-protocol in using-aitp skill.
- Runtime support matrix (partial coverage per platform).

### Not yet implemented
- Operational conformance checking in any adapter.
- Front-door routing in OpenClaw.
- Session chronicle as hard requirement.
- Standalone Charter document.
- Conformance verification at session end.
- Codex adapter full implementation.
- OpenCode adapter full implementation.

## AD15. What Adapters Should Not Do

- Claim AITP conformance without meeting conformance requirements.
- Expose protocol jargon to users unnecessarily.
- Replace protocol-governed decisions with platform-specific shortcuts.
- Treat the adapter as the authority; the protocol is the authority.
- Create a parallel protocol that competes with AITP.
- Bypass front-door routing for convenience.
- Treat session chronicle as optional soft guidance.
