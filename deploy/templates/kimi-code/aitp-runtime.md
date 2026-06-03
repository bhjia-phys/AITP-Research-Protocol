---
name: aitp-runtime
description: Use after AITP v5 routing has claimed a theoretical-physics task; continue the work through typed records, validation gates, and summary regeneration instead of ad hoc notes.
---

# AITP Runtime v5 - Kimi Code

## Runtime Loop

Every real research turn starts by restoring the typed state:

```text
brief = aitp_v5_get_execution_brief(base=<workspace>, session_id=<session-id>)
```

Then decide the next action from the brief:

- Missing definition or object: record a physics object or relation.
- Missing provenance: record code state, evidence, reference location, or tool run.
- Claim needs testing: create or update a validation contract, run the check, then record a validation result.
- Interpretation needed: record a sensemaking report, clearly marked as orientation-only.
- Trust change or L2 memory: use preflight, promotion packet, and human checkpoint gates.

## Typed Record Boundaries

- `execution_brief` is the working control panel.
- `summary_orientation` is useful for reading but is never a truth source.
- Hook config and hook traces are runtime metadata, not evidence by themselves.
- A validation result supports only the exact checks and failure modes it covers.
- Partial validation should be recorded as a narrow result, not as a pass for a broad contract.

## Kimi Native Hooks

Kimi Code supports TOML lifecycle hooks. AITP v5 installs:

- `PreToolUse`: checks risky or trust-changing tool calls before execution.
- `PostToolUse`: appends trace events after meaningful tools.

Install:

```powershell
python -m brain.v5.cli --base <workspace> adapter install-hooks kimi-code <session-id> --settings <workspace>/.kimi/config.toml
python -m brain.v5.cli --base <workspace> adapter install-hooks kimi-code <session-id> --settings <workspace>/.kimi-code/config.toml
```

Audit:

```powershell
python -m brain.v5.cli --base <workspace> adapter install-audit kimi-code --settings <workspace>/.kimi/config.toml
python -m brain.v5.cli --base <workspace> adapter install-audit kimi-code --settings <workspace>/.kimi-code/config.toml
```

Smoke coverage is visible through:

```powershell
python -m brain.v5.cli adapter smoke-coverage
```

For Kimi CLI builds that support explicit project paths, launch with project
assets directly:

```powershell
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
kimi --work-dir <workspace> --config-file .kimi-code/config.toml --mcp-config-file .kimi-code/mcp.json --skills-dir .kimi-code/skills
```

## Research Workflow

For a natural physics conversation, keep the user-facing flow simple:

1. Restore the brief.
2. Explain the current claim, uncertainty, and next useful check in plain language.
3. Do the math or computation.
4. Record the durable typed objects, evidence, tool runs, validations, and interpretation.
5. Refresh the brief before stating what is now known.

## Failure Discipline

Record these immediately:

- wrong formula or shortcut
- missing source provenance
- dirty or unknown code state behind a numerical result
- incomplete coverage of a validation contract
- finite-size, operator-choice, gauge, normalization, or sector-selection artifacts
- any conclusion that is interpretation rather than validation
