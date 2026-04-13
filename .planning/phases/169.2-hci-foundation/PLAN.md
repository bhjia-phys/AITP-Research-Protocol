# Plan: 169.2-01 — Add structured status output, hello command, and post-bootstrap action guidance

**Phase:** 169.2
**Axis:** Axis 4 (global infrastructure, human experience)
**Requirements:** REQ-HCI-01, REQ-HCI-02

## Goal

Make three targeted HCI improvements so the next E2E test run has a better
operator experience.

## Context

The AITP CLI is functionally complete but hostile to operators:

- `aitp status` dumps 40+ sections with no hierarchy (BACKLOG 999.60)
- there is no `aitp hello` or equivalent zero-config entry point (BACKLOG 999.61)
- after bootstrap, the operator sees no suggested next action (BACKLOG 999.86)

These are the three highest-severity HCI gaps that directly affect E2E test
ergonomics. They are independent of the schema/bridge work in Phases 169/169.1.

## Steps

### Step 1: Structured status output (BACKLOG 999.60)

**File:** `research/knowledge-hub/knowledge_hub/aitp_cli.py` (or equivalent
status rendering module)

Restructure the status output into 3 tiers:

1. **Summary tier** (always shown): current topic slug, milestone phase,
   overall status (one word: `active`, `blocked`, `complete`), and the single
   most important next action — scannable in under 5 seconds
2. **Key sections tier** (`--verbose` or `-v`): top 5-8 sections most relevant
   to the current phase — coverage state, trust status, pending gates
3. **Full detail tier** (`--full` or `-vv`): the complete 40+ section output
   for deep inspection

Default output = summary tier only.

**Implementation approach:**
- Add a `render_status_tier(topic_state, tier="summary")` function
- Modify the existing status command to accept `--verbose` / `--full` flags
- Keep the `--json` output unchanged (machine-readable consumers depend on it)

### Step 2: Zero-config hello command (BACKLOG 999.61)

**File:** `research/knowledge-hub/knowledge_hub/aitp_cli.py`

Add an `aitp hello` command that:

- If no topic exists: prints a welcome message with a one-line description of
  AITP and suggests `aitp bootstrap <topic>` as the first action
- If a topic exists: prints the topic slug, current phase, and suggested next
  action (same as summary tier from Step 1)
- Always completes in under 2 seconds with no network calls

**Implementation approach:**
- Add a `cmd_hello(args)` function to the CLI module
- Register it in the argument parser with `subparsers.add_parser("hello")`
- Reuse the summary-tier rendering from Step 1

### Step 3: Post-bootstrap action guidance (BACKLOG 999.86)

**File:** `research/knowledge-hub/knowledge_hub/` (bootstrap support module)

After a successful `aitp bootstrap`:

- Write a `next_action_hint` field into `topic_state.json` with the value
  `"Run 'aitp status' to see your topic state, or 'aitp run-topic-loop' to start the research loop"`
- Print the hint to stdout at the end of the bootstrap output
- The hint should be a single line, actionable, and not require documentation
  lookup

## Must Do

- Keep all changes additive
- Default status output must be scannable in under 5 seconds (summary tier)
- `--json` output must remain unchanged
- `aitp hello` must work with zero configuration and no network calls

## Must Not Do

- Do not change the `--json` output format (machine consumers depend on it)
- Do not add new external dependencies
- Do not implement PyPI packaging, install verification, or Windows path
  handling (those are BACKLOG 999.48–999.51, separate milestone)
- Do not add command grouping or terminology cleanup (BACKLOG 999.62–999.63)

## Evidence

- [ ] `aitp status` default output is under 10 lines and scannable in 5 seconds
- [ ] `aitp status --verbose` shows key sections without the full dump
- [ ] `aitp status --full` shows the complete output
- [ ] `aitp hello` prints topic summary or welcome message
- [ ] `aitp bootstrap` prints a `next_action_hint` line
- [ ] `aitp status --json` output is unchanged from before
