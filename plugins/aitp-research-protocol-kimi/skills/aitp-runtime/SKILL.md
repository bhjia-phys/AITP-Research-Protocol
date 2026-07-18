---
name: aitp-runtime
description: Continue an AITP v5 theoretical-physics topic through typed claims, source provenance, artifacts, evidence, validation gates, human checkpoints, and trust-controlled memory.
---

# AITP Runtime v5 - Kimi Code

Kimi Code uses the same host-neutral compact facade as the Codex plugin. The
public names retain the `aitp_v5_codex_*` prefix for compatibility; they do not
grant Codex-specific authority.

For every active AITP research iteration, decide whether the current request
needs AITP before answering:

```text
aitp_v5_codex_autoroute(base="", request_summary=<current user request>, session_id=<session-id if known>, topics=<topics if known>, semantic_assessment=<model semantic assessment>)
```

If autoroute says `answer_without_aitp`, answer normally and do not write AITP
records. If it returns `enter_existing_session`, `recover_topic`, or
`recover_workspace`, call the returned `recommended_next_tool` with
`recommended_args`, then restore the bounded entry card:

```text
aitp_v5_codex_enter(base="", session_id=<session-id>, request_summary=<current user request>, payload_profile="minimal")
```

Use `base=""` unless the user explicitly provides a topics root. The launcher
resolves the empty base through `AITP_TOPICS_ROOT`.

The entry card is orientation-only. Expand explicitly before trust-sensitive
interpretation:

```text
aitp_v5_codex_expand(base="", session_id=<session-id>, expansion="brief")
aitp_v5_codex_expand(base="", session_id=<session-id>, expansion="relation_map")
```

The full brief is the execution contract. The relation map is the conclusion
boundary: inspect supported, limited, untested, contradicted, can-say,
cannot-say, blocker, and next-action fields before interpreting the claim.

## Typed Runtime Loop

1. Autoroute the request.
2. Restore the minimal entry card only when autoroute enters AITP.
3. Expand brief and relation map only for audit, evidence, validation, trust,
   or final synthesis.
4. Present a human checkpoint plainly and wait when one is required.
5. Collect missing source, evidence, or validation before any trust-changing
   action.
6. Do the physics, code, literature, or numerical work.
7. Record only durable typed outputs.
8. Inspect closeout or checkpoint `record_completeness_audit` before calling
   the research record complete.

## Moment Policy

AITP is not a transcript logger. Record only durable research moments:

- reusable source identity or source location,
- completed tool or code run with research-relevant output,
- artifact, report, table, plot, log, or raw dump,
- result, anomaly, contradiction, negative result, or failed check,
- proof gap, validation gap, missing provenance, route blocker,
- selected, pivoted, abandoned, or split route,
- active claim scope or status change,
- final answer that depends on an active claim,
- trust update, promotion, or human decision request,
- session-end handoff with new durable state.

Do not record generic explanation, unaccepted brainstorming, repeated
summaries, file scans with no research change, or setup checks with no research
information.

## Progressive Recording

Use the lightest compact recording route:

```text
aitp_v5_codex_recording_step(base="", session_id=<session-id>, event_type=<event>, summary=<durable moment>)
aitp_v5_codex_recording_step(base="", session_id=<session-id>, event_type=<event>, summary=<durable moment>, slot=<one slot>)
aitp_v5_codex_record_apply(base="", session_id=<session-id>, slot=<one slot>, payload=<typed slot payload>)
```

If the classifier says `ignore` or `defer`, do not write. Expand one slot at a
time. The apply response includes verification. Full-kernel mutation tools are
maintenance surfaces and are not part of the default Kimi plugin session.

## Record And Trust Boundaries

- Definitions and systems use typed physics-object records.
- Relations and equations use typed object-relation records.
- Numerical and code work needs code state, tool recipe/run, artifact,
  evidence, and validation records appropriate to the result.
- Open theorem or review gaps remain proof obligations.
- Interpretation remains orientation-only sensemaking unless backed by typed
  evidence and validation.
- Source references, artifacts, summaries, RAG chunks, context cards, hooks,
  and Skills are not claim support by themselves.
- Missing recommended closeout slots are plan-only gaps, not silently verified
  records.
- No compact operation may promote claim trust or install a Skill.

## Literature And Writing

Use the compact literature facade for source registration and note recovery:

```text
aitp_v5_codex_literature_step(base="", session_id=<session-id>, action="suggest", uri=<url-or-path>, label=<source label>)
aitp_v5_codex_literature_step(base="", session_id=<session-id>, action="record_reference", uri=<url-or-path>, label=<source label>)
aitp_v5_codex_expand(base="", session_id=<session-id>, expansion="note_outline", style="jhep")
```

Register references in layers: source identity, exact location, reading
artifact, claim-linked evidence, physics object/relation, validation basis, and
trust basis. A paper or note is not evidence until a typed record links it to a
specific claim and scope.

Do not rely on a Kimi Code stop hook for research closeout. Use:

```text
aitp_v5_codex_closeout(base="", session_id=<session-id>, summary=<handoff summary>)
```

Closeout previews by default. Set `apply=true` only for a durable handoff or
quiet checkpoint. It cannot update claim trust.

## Kimi Project Hooks

Plugin MCP registration and repository-local lifecycle hooks are independent.
Only install a project hook when the user explicitly requests it:

```powershell
python -m brain.v5.cli --base <workspace> adapter install-hooks kimi-code <session-id> --settings <workspace>/.kimi/config.toml
python -m brain.v5.cli --base <workspace> adapter install-audit kimi-code --settings <workspace>/.kimi/config.toml
```

The hook is runtime metadata, not evidence or canonical research state.

## Physics Validation Obligations

Before treating a result as strong, check dimensional and algebraic
consistency, relevant limits and symmetries, approximation validity, numerical
convergence, benchmark agreement, and error estimates. Record failed checks as
typed protocol state rather than burying them in prose.

## Fallback Commands

```powershell
uv run --with pyyaml --with jsonschema --with fastmcp --with "pypdf>=5,<7" python scripts/aitp-pm.py doctor
uv run --with pyyaml --with jsonschema --with fastmcp --with "pypdf>=5,<7" python -m brain.v5.cli --base "$env:AITP_TOPICS_ROOT" status context-pack <session-id>
uv run --with pyyaml --with jsonschema --with fastmcp --with "pypdf>=5,<7" python -m brain.v5.cli --base "$env:AITP_TOPICS_ROOT" brief <session-id>
uv run --with pyyaml --with jsonschema --with fastmcp --with "pypdf>=5,<7" python -m brain.v5.cli --base "$env:AITP_TOPICS_ROOT" relation-map <session-id>
```
