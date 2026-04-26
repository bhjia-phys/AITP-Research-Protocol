# Phase 166: Public Front Door L0 Source Handoff - Research

**Researched:** 2026-04-13
**Domain:** AITP runtime-side next-action parity for post-bootstrap `L0` source recovery
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- expose one primary "start here" lane:
  `research/knowledge-hub/source-layer/scripts/discover_and_register.py` when
  the operator has a natural-language topic statement or query rather than a
  fixed arXiv id
- list two secondary direct-entry surfaces beside the primary lane:
  `research/knowledge-hub/source-layer/scripts/register_arxiv_source.py` for
  known arXiv ids and `research/knowledge-hub/intake/ARXIV_FIRST_SOURCE_INTAKE.md`
  as the operator runbook
- keep wording plain and action-oriented
- `topic_dashboard.md`, `runtime_protocol.generated.md`, and
  `topic_replay_bundle.md` must surface the same handoff facts from one shared
  runtime payload or source of truth
- keep existing selected-action summary and `return_to_L0` truth visible; the
  new handoff augments rather than replaces the bounded-action record
- keep the handoff advisory and explicit only for real
  `l0_source_expansion` / `return_to_L0` situations
- Phase `166` adds bounded regression coverage only; the fresh-topic
  registration proof remains Phase `166.1`

### the agent's Discretion
- exact field names or helper-object shape for the shared handoff payload
- final markdown layout of the handoff block on each surface
- whether surfaces show inline command examples or path references only

### Deferred Ideas (OUT OF SCOPE)
- change `register_arxiv_source.py` default behavior to contentful download
- broaden the handoff to non-arXiv provider families
- auto-trigger discovery or registration from the runtime queue

</user_constraints>

<research_summary>
## Summary

This phase is not a library-selection problem. The useful research question is
where the current repository already stores "next action" truth and which
surfaces already consume it. The existing architecture already centralizes
selected next action through bootstrap-generated `next_actions.md`,
decision-surface materialization, `topic_synopsis.runtime_focus`, and the
runtime bundle.

The lowest-risk implementation is to keep the existing `l0_source_expansion`
route honest, make the bootstrap-created next-action wording concrete, and add
one structured `L0` handoff payload that dashboard, runtime protocol, and replay
all read from. That avoids per-surface prose drift and keeps the new operator
guidance attached to the actual runtime truth rather than to one markdown file.

**Primary recommendation:** change the seeded `L0` next-action text at
`runtime/scripts/orchestrate_topic.py`, derive one shared `l0_source_handoff`
payload off the active `l0_source_expansion` / `requires_l0_return` state, and
cover parity with targeted service, replay, and bootstrap-facing regression
tests.
</research_summary>

<standard_stack>
## Standard Stack

The established modules for this phase are internal AITP runtime surfaces, not
new external dependencies.

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `runtime/scripts/orchestrate_topic.py` | repo-local | Seeds bootstrap-side `next_actions.md` content | This is the current source of the generic post-bootstrap wording |
| `knowledge_hub/runtime_bundle_support.py` | repo-local | Builds runtime protocol, synopsis, and minimal execution brief | This is the shared runtime truth surface already consumed by multiple outputs |
| `knowledge_hub/topic_shell_support.py` | repo-local | Derives `return_to_L0` explainability and dashboard text | It already knows when a topic is honestly blocked on `L0` |
| `knowledge_hub/topic_replay.py` | repo-local | Materializes replay bundle and markdown | Replay parity belongs here, not in ad hoc CLI glue |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `research/knowledge-hub/L0_SOURCE_LAYER.md` | repo-local | Canonical operator path for discovery-before-registration | Use to keep handoff wording aligned with shipped `L0` policy |
| `research/knowledge-hub/README.md` | repo-local | Documents current discovery entrypoint and acceptance expectations | Use when turning internal truth into operator-facing guidance |
| `research/knowledge-hub/tests/test_aitp_mcp_server.py` | repo-local | Bootstrap/loop API fixture coverage | Update when the visible selected-action wording changes |
| `research/knowledge-hub/tests/test_aitp_service.py` | repo-local | Topic-shell/runtime-bundle/dashboard coverage | Use for cross-surface parity checks |
| `research/knowledge-hub/tests/test_topic_replay.py` | repo-local | Replay bundle and markdown coverage | Use for replay parity checks |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| shared handoff payload | per-surface prose patches | Faster to land once, but guarantees drift across dashboard / protocol / replay |
| advisory handoff | auto-run discovery | More "helpful" in appearance, but violates the phase honesty boundary |
| bootstrap wording change + shared payload | payload-only with generic summary retained | Safer copy isolation, but leaves the selected action itself too abstract |

**Installation:**
```bash
# No new dependencies required for Phase 166.
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
runtime/scripts/
├── orchestrate_topic.py          # seed concrete next-action wording at bootstrap

knowledge_hub/
├── runtime_bundle_support.py     # shared structured handoff payload
├── topic_shell_support.py        # dashboard / explainability consumption
└── topic_replay.py               # replay consumption

tests/
├── test_aitp_mcp_server.py       # bootstrap/loop fixture parity
├── test_aitp_service.py          # dashboard/runtime protocol parity
└── test_topic_replay.py          # replay parity
```

### Pattern 1: Shared derived handoff payload
**What:** derive one structured `l0_source_handoff` object from selected action
type plus open-gap state, then let each surface render from that object.
**When to use:** any time the same operator guidance must appear in multiple
runtime truth surfaces.
**Example:**
```python
handoff = {
    "status": "needs_sources",
    "primary_path": "source-layer/scripts/discover_and_register.py",
    "primary_when": "Use when you have a topic query rather than a fixed arXiv id.",
    "alternate_entries": [
        "source-layer/scripts/register_arxiv_source.py",
        "intake/ARXIV_FIRST_SOURCE_INTAKE.md",
    ],
}
```

### Pattern 2: Keep selected action truth and handoff truth separate
**What:** preserve the selected bounded action as the runtime's primary control
fact, but expose a more operator-friendly helper surface beside it.
**When to use:** when the selected action is real and useful, but still too
compressed or abstract for direct operator action.
**Example:**
```python
selected_action_summary = runtime_focus["next_action_summary"]
l0_source_handoff = build_l0_source_handoff(...)
```

### Anti-Patterns to Avoid
- **Per-surface copy forks:** updating dashboard, runtime protocol, and replay
  independently will drift as soon as one wording path changes.
- **Markdown-only guidance:** if the handoff only exists in rendered markdown,
  replay and API consumers cannot stay aligned.
- **Fake progress helpers:** any helper that auto-creates sources or implies the
  topic already has content violates the milestone's honesty boundary.
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| cross-surface guidance | three separate prose blocks | one shared runtime payload | same facts must survive dashboard, protocol, and replay |
| post-bootstrap entry advice | a new helper command | existing `discover_and_register.py` / `register_arxiv_source.py` / intake runbook | the operator path already exists and should stay protocol-first |
| recovery automation | auto-discovery or auto-registration | explicit advisory handoff | missing-source state is still a real research judgment boundary |

**Key insight:** the repo already has the `L0` entry surfaces. The work here is
not to invent new acquisition behavior, but to make the existing path visible
at the exact runtime moment where the user currently gets only generic prose.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Fixing only the bootstrap wording
**What goes wrong:** the selected action becomes concrete in one place, but
dashboard, runtime protocol, and replay still diverge or fail to expose the
same helper facts.
**Why it happens:** the wording change lands only in `orchestrate_topic.py`
without a shared runtime payload.
**How to avoid:** treat bootstrap wording and multi-surface parity as separate
deliverables in the same phase.
**Warning signs:** one surface mentions `discover_and_register.py` while another
still says "convert the topic statement into sources."

### Pitfall 2: Hiding the handoff in markdown only
**What goes wrong:** a markdown section looks correct, but machine-readable
surfaces and replay do not carry the same structure.
**Why it happens:** the implementation bypasses runtime bundle / replay payloads
and writes presentation-only text.
**How to avoid:** derive the handoff in shared support code before rendering.
**Warning signs:** tests can only assert rendered text, not structured fields.

### Pitfall 3: Smuggling in Phase 166.1 behavior
**What goes wrong:** the fix widens into changing registration defaults or
actually running registration from the queue.
**Why it happens:** the helper surface is mistaken for workflow automation.
**How to avoid:** keep this phase advisory only; contentful default registration
stays in Phase `166.1`.
**Warning signs:** `register_arxiv_source.py` behavior changes or tests start
requiring a completed registration lane.
</common_pitfalls>

<code_examples>
## Code Examples

Verified patterns from existing repository code:

### Bootstrap seeds the first `L0` next action
```python
# Source: research/knowledge-hub/runtime/scripts/orchestrate_topic.py
write_text(
    run_root / "next_actions.md",
    "# Next actions\\n\\n1. ...\\n",
)
```

### Topic shell already recognizes honest `return_to_L0`
```python
# Source: research/knowledge-hub/knowledge_hub/topic_shell_support.py
requires_l0_return = (
    selected_action_type == "l0_source_expansion"
    or bool(open_gap_summary.get("requires_l0_return"))
)
```

### Runtime bundle already centralizes selected-action parity
```python
# Source: research/knowledge-hub/knowledge_hub/runtime_bundle_support.py
"next_action_summary": str(runtime_focus.get("next_action_summary") or "..."),
```
</code_examples>

<sota_updates>
## State of the Art (2026 Repository State)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| generic `L0` next action only | concrete bootstrap wording plus structured handoff payload | target of Phase `166` | operator can act immediately without losing runtime honesty |
| per-surface manual summaries | shared runtime truth consumed by multiple surfaces | already the dominant runtime pattern | parity becomes testable instead of fragile |

**New tools/patterns to consider:**
- shared helper objects in runtime bundle for operator-facing explanations that
  still need machine-readable parity
- replay-level structured fields for any new runtime truth surface that must
  survive retrospective inspection

**Deprecated/outdated:**
- treating a generic prose next action as sufficient after a fresh public
  bootstrap
</sota_updates>

<open_questions>
## Open Questions

1. **Should `selected_action_summary` itself become fully concrete, or should
   the structured handoff carry most of the detail?**
   - What we know: the seeded bootstrap summary is currently too generic.
   - What's unclear: how much concrete path detail belongs in the summary versus
     the new handoff object.
   - Recommendation: make the summary concrete enough to name the primary lane,
     but keep alternate entries in the structured handoff block.

2. **How strict should the new tests be about exact prose?**
   - What we know: tests must protect against regression to generic wording.
   - What's unclear: whether exact sentence matching will be too brittle.
   - Recommendation: assert required action type plus presence of the three
     canonical path fragments instead of pinning one long sentence verbatim.
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- `.planning/phases/166-public-front-door-l0-source-handoff/166-CONTEXT.md` -
  locked phase decisions and scope boundary
- `research/knowledge-hub/runtime/scripts/orchestrate_topic.py` - current
  bootstrap-seeded next-action source
- `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py` - current
  runtime truth model and protocol rendering path
- `research/knowledge-hub/knowledge_hub/topic_shell_support.py` - current
  `return_to_L0` explainability path
- `research/knowledge-hub/knowledge_hub/topic_replay.py` - current replay
  truth model

### Secondary (MEDIUM confidence)
- `research/knowledge-hub/L0_SOURCE_LAYER.md` - current documented discovery /
  registration operator path
- `research/knowledge-hub/README.md` - bounded discovery entrypoint and
  acceptance framing
- `research/knowledge-hub/tests/test_aitp_mcp_server.py` - bootstrap-facing
  visible summary fixture
- `research/knowledge-hub/tests/test_aitp_service.py` - topic shell parity
- `research/knowledge-hub/tests/test_topic_replay.py` - replay parity

### Tertiary (LOW confidence - needs validation)
- None. This phase is grounded in current repository artifacts rather than
  external ecosystem research.
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: runtime-side next-action materialization
- Ecosystem: internal AITP runtime modules and tests
- Patterns: shared payload derivation, cross-surface parity, honest `L0` return
- Pitfalls: drift, markdown-only fixes, phase-scope widening

**Confidence breakdown:**
- Standard stack: HIGH - entirely internal repo-local modules
- Architecture: HIGH - follows existing runtime bundle and replay patterns
- Pitfalls: HIGH - directly inferred from current code/data flow
- Code examples: HIGH - extracted from current repository code

**Research date:** 2026-04-13
**Valid until:** 2026-05-13
</metadata>

---

*Phase: 166-public-front-door-l0-source-handoff*
*Research completed: 2026-04-13*
*Ready for planning: yes*
