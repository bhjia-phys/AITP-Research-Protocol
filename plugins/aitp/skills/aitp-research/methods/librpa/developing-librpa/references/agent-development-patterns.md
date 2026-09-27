# Development instructions learned from Codex and Kimi Code

This source study informs maintenance of the LibRPA development Skill. Read it
when changing agent instructions, not as a prerequisite for every numerical
edit. The inspected snapshots are
[Codex d3812ddb](https://github.com/openai/codex/tree/d3812ddbb3b62f46fd9b70fdb96af04d45556e78) and
[Kimi Code CLI 86f13642](https://github.com/MoonshotAI/kimi-cli/tree/86f136422a0aae6b217ea49e7ea1d2e8a1defcd2).
These identify the studied source versions; they do not prescribe calculation bookkeeping.

## Repository guidance, task instructions, and execution have different roles

Codex's [AGENTS.md](https://github.com/openai/codex/blob/d3812ddbb3b62f46fd9b70fdb96af04d45556e78/AGENTS.md)
specifies concrete conventions, scoped test commands, dependency/schema update
obligations, and review rules. Kimi's
[AGENTS.md](https://github.com/MoonshotAI/kimi-cli/blob/86f136422a0aae6b217ea49e7ea1d2e8a1defcd2/AGENTS.md)
also maps the actual CLI, runtime, agent, tool, and UI entry points. Its
[tools instructions](https://github.com/MoonshotAI/kimi-cli/blob/86f136422a0aae6b217ea49e7ea1d2e8a1defcd2/src/kimi_cli/tools/AGENTS.md)
give a precise import boundary rather than a generic request for clean code.

Skills carry task procedures. Codex's
[review orchestrator](https://github.com/openai/codex/blob/d3812ddbb3b62f46fd9b70fdb96af04d45556e78/.codex/skills/code-review/SKILL.md)
assigns the separate review Skills to workers. Its
[testing Skill](https://github.com/openai/codex/blob/d3812ddbb3b62f46fd9b70fdb96af04d45556e78/.codex/skills/code-review-testing/SKILL.md)
names integration fixtures and behaviors to cover. Its
[PR-body Skill](https://github.com/openai/codex/blob/d3812ddbb3b62f46fd9b70fdb96af04d45556e78/.codex/skills/codex-pr-body/SKILL.md)
describes the motivation, net change, preserved context, and relevant verification.
These are actionable decisions attached to a specific task.

The runtime supplies capabilities; a Markdown file does not itself create an
agent scheduler or enforce a safety boundary. In Codex,
[skill selection](https://github.com/openai/codex/blob/d3812ddbb3b62f46fd9b70fdb96af04d45556e78/codex-rs/skills/src/selection.rs)
resolves explicit mentions, and the
[turn builder](https://github.com/openai/codex/blob/d3812ddbb3b62f46fd9b70fdb96af04d45556e78/codex-rs/core/src/session/turn.rs)
loads selected prompts. Kimi's
[skill module](https://github.com/MoonshotAI/kimi-cli/blob/86f136422a0aae6b217ea49e7ea1d2e8a1defcd2/src/kimi_cli/skill/__init__.py)
formats names, descriptions, paths, and scopes for discovery; its
[system prompt](https://github.com/MoonshotAI/kimi-cli/blob/86f136422a0aae6b217ea49e7ea1d2e8a1defcd2/src/kimi_cli/agents/default/system.md)
instructs the model to read detailed Skills when needed.

For LibRPA, keep stable project rules in the maintained developer documentation
or an applicable repository instruction file. The Skill should explain how to
find the active calculation, place a change, and select evidence. Link detailed
architecture and worked examples conditionally. Do not duplicate the entire
manual or create another configuration/registration framework.

## Agents need bounded work and reviewable evidence

Kimi's [agent specification](https://github.com/MoonshotAI/kimi-cli/blob/86f136422a0aae6b217ea49e7ea1d2e8a1defcd2/src/kimi_cli/agents/default/agent.yaml)
defines coder, explorer, and planner roles. The explorer's prompt requires
read-only work and its tool list omits direct file-edit tools; shell access
still means this is not by itself filesystem isolation. Its
[Codex worker Skill](https://github.com/MoonshotAI/kimi-cli/blob/86f136422a0aae6b217ea49e7ea1d2e8a1defcd2/.agents/skills/codex-worker/SKILL.md)
uses separate worktrees and explicit task handoffs for concurrent development.
These designs make task ownership and returned evidence explicit.

For LibRPA, a useful split might be producer-convention inspection, a numerical
kernel edit, and a regression review, provided the tasks are independent and
delegation is available and authorized. Specify files, assumptions, expected
findings or outputs, and whether edits are allowed. Review the integrated tree
afterward. Parallelism is an optional execution choice, not a requirement of a
good development Skill or evidence of faster scientific progress.

Do not transplant another repository's model choices, worker quotas, hard line
limits, approval-bypass flags, or automatic PR labels. Those are local workflow
choices, not LibRPA architecture. Ordinary portable instructions suffice here;
Kimi-specific flow Skills and tmux workers are not required.

## Check the behavior that motivated the edit

Kimi's [feature smoke-test Skill](https://github.com/MoonshotAI/kimi-cli/blob/86f136422a0aae6b217ea49e7ea1d2e8a1defcd2/.agents/skills/feature-smoke-test/SKILL.md)
derives scenarios from the change, runs the real entry point in an isolated
workspace, and inspects outputs and failures. Codex's testing guidance favors
existing integration fixtures for agent behavior. Its
[remote-test Skill](https://github.com/openai/codex/blob/d3812ddbb3b62f46fd9b70fdb96af04d45556e78/.codex/skills/remote-tests/SKILL.md)
distinguishes failures caused by different executor environments.

The transferable principle is to choose evidence that can falsify the promised
behavior, using the existing test machinery. In LibRPA this often means a small
numerical end-to-end case, with the actual producer, basis, frequency grid, and
MPI layout. It does not mean reproducing an agent application's wire-protocol
or UI test matrix around scientific input parsing. The QSGW cleanup's agreed
end-to-end scope remains appropriate; an uncovered numerical invariant can
justify a targeted component test in other work.

## Scope of the adaptation check

The revised instructions were walked through against three existing LibRPA
paths: shared `nfreq` initialization and Fortran synchronization; driver-only
`fn_vxc_scf`/`qsgw_vxc_basis` parsing and readers; and the QSGW task's build
registration, Dataset invalidation, and reference projection. These require
different edit locations and validation, which the Skill now distinguishes.

The existing options checker passed with 77 shared fields, and regression
`list` selected the named H2O QSGW case. These checks verified source routing
and command selection; no new numerical calculation or independent agent
session was run for this instruction revision. The earlier executed QSGW
regressions are documented separately in the worked example. This study does
not measure either project's development productivity or this Skill's effect
on an unfamiliar agent.
