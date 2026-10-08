# AITP in Claude Code

Claude Code uses the same `plugins/aitp/skills/` files as Codex and Hakimi.
Its [plugin manifest](../plugins/aitp/.claude-plugin/plugin.json) supplies native
metadata; the [marketplace](../.claude-plugin/marketplace.json) points to that
plugin directory. No copy of the research instructions, runtime, MCP service,
session hook or global `CLAUDE.md` is required.

Claude scans the default `skills/` directory for the seven core Skills. The
manifest adds the nested `developing-librpa` directory so that the domain method
is selectable too. Its files stay in their existing location, preserving links
to the research Skill and method library. When another domain method needs
direct discovery in Claude, add its directory to this manifest and verify the
component inventory. A linked method does not need a duplicate wrapper Skill.

## Install the development checkout

From the repository root, run:

```sh
claude plugin validate plugins/aitp --strict
claude plugin validate . --strict
claude plugin marketplace add .
claude plugin install aitp@aitp-protocol --scope user
claude plugin list
claude plugin details aitp
```

The user scope enables AITP across this user's projects. Expect seven core Skills
plus `developing-librpa`. Start a new Claude session in the research workspace.
These instructions install the current local checkout; the published `v1.1.0`
release predates the Claude manifest and the two human interaction Skills.

Keep the checkout at its registered location. In the validated Claude Code
2.1.283 setup, fresh sessions loaded this locally registered plugin directly
from the checkout. The installer also created a matching cache, and
`claude plugin list --json` reported that cache as `installPath`. To establish
which files a session actually uses, check its initialization plugin path and
the base directory shown when a Skill loads; installation metadata alone did
not identify the active source. A new session picks up edits to an in-place
plugin.

For a cached or remote installation, advance the Claude manifest version when
distributing a change, then update the marketplace and plugin:

```sh
claude plugin marketplace update aitp-protocol
claude plugin update aitp@aitp-protocol
```

Then start a new session and check the loaded version and files.
The Claude version suffix identifies host packaging;
the substantive instructions remain the shared files.

## Use ordinary research requests

Examples include “Where does this research stand, and what remains unproved?”,
“Explain the projection step I am missing”, and “What should we carry into the
next calculation from this failure?” Skill descriptions let Claude select the
relevant guidance. The optional explicit commands are:

| Command | Role |
| --- | --- |
| `/aitp:aitp-memory` | Recover a topic and retain consequential changes. |
| `/aitp:aitp-research` | Investigate the scientific question and evidence. |
| `/aitp:aitp-writing` | Develop the main argument and supporting explanations. |
| `/aitp:aitp-distill` | Turn demonstrated reusable procedures into local Skills. |
| `/aitp:aitp-human-brainstorming` | Resolve consequential choices with the researcher. |
| `/aitp:aitp-human-learning` | Address conceptual difficulties and learning feedback. |
| `/aitp:developing-librpa` | Trace and develop LibRPA source and numerical methods. |

The Skills use Claude's normal tools and permissions. Installing them neither
grants execution permissions nor initiates research or note migration. The
ordinary read-only request still takes precedence. Natural activation is a model
behavior to test, not a guarantee made by the manifest.

## Verify the installed behavior

Manifest validation and the component inventory check packaging. A separate
fresh-session trial should ask a natural research question in a small disposable
workspace, inspect actual Skill invocations or reads, and check the answer and
file changes. Keep private topic data and evaluation traces outside this repository.
The existing [general cases](../benchmarks/general-v0.1/README.md) can supply
small self-contained material; do not give their evaluator expectations to the
tested session. A successful smoke test does not establish scientific reliability
or resolve known trigger weaknesses on other hosts.

Host behavior and commands follow the official
[plugin manifest reference](https://code.claude.com/docs/en/plugins-reference),
[marketplace guide](https://code.claude.com/docs/en/plugin-marketplaces) and
[Skill guide](https://code.claude.com/docs/en/skills).
