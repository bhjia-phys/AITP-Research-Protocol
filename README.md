# AITP Research Protocol

AITP is a local-first protocol for long-running collaboration between researchers and AI agents.

Its goal is not merely to save notes. A mature AITP collaborator should remember the details that matter, recover why decisions were made, preserve failed attempts, connect knowledge across Topics, extract reusable physical knowledge and technical Skills, and surface new Insights without confusing them with established results.

## North star

After weeks or years of work, a new session should be able to:

- resume a Topic without asking the researcher to repeat its history;
- trace every remembered claim to its source record, and every
  evidence-bearing record to exact pinned evidence;
- recall conventions, constraints, decisions, failures, and open questions;
- connect a current problem to relevant results from other Topics;
- distinguish physical knowledge, reusable procedure, and speculative Insight;
- propose a reusable Skill with provenance and evaluations;
- work with a researcher across many sessions without losing corrections,
  commitments, or the reasoning behind the current direction.

AITP records project memory, not scientific truth. Evidence and human judgment remain authoritative.

## Architecture

AITP's end state has two kinds of objects: **four stores** and **typed,
provenance-carrying, append-only relation records** between them.

```text
L  literature   external (arXiv / INSPIRE / publishers); mirror: references/
M  AITP memory  .aitp append-only records + reviewed artifacts (agent-facing)
H  researcher   judgment and corrections; leaves attributable traces
D  documents    the research itself: theory/, manuscripts/, notes, Obsidian
```

M is memory; D is the research. Notes live in M; derivations and manuscripts
live in D; M pins D and cites L; H gates promotion. Every durable movement
that M relies on uses one of these relation records — cite, ground,
synthesize, decide, supersede, link, review, publish — each with an author,
a time, and an evidence pin where reachable. Proposals live as drafts;
accepted relations are saved records. Not every movement is recorded:
ordinary D edits live in Git, and unwritten H judgments are invisible by
design.

The protocol has three parts:

1. **Schemas** — append-only Markdown records with evidence pins
   ([ledger design](docs/design.md)), reviewed compiled artifacts, and link
   records.
2. **A small deterministic CLI** — the write gate: validate, persist,
   project, benchmark. Nothing semantic runs in Python.
3. **Methodology Skills** — the research discipline: when to read, how to
   survey literature, when to record, how to distill, when to stop and ask.

The original L0–L4 vision is preserved as cognitive discipline and dissolved
as software. See [Roadmap and Product Design](docs/roadmap.md).

## Roadmap

Full plan with scopes, complexity budgets, and gates:
[docs/roadmap.md](docs/roadmap.md).

| Stage | Outcome | Exit gate |
|---|---|---|
| M0 — Ledger | Reliable single-Topic records and Notes | Idempotent writes, pinned evidence, grounded `enter`, real-project use |
| M0.5 — Slim core | One canonical runtime, deduplicated without net growth | No runtime duplication, no oversized module, unchanged ledger contracts |
| M0.6 — Adopt & bootstrap | `init --adopt`, workspace `topics.toml`, lazy legacy bootstrap, executable conformance core | Two dogfood Topics adopted; bootstrap Notes human-confirmed; core suite runs end-to-end; cold-start metrics recorded |
| M1a — Memory that restores | `enter` v2, `show`/`list`, versioned `--json`, resumption discipline | Suite-scored resumption checklist on real Topics vs. control |
| M1b — Open items & behavior pilot | question/prediction lifecycle with typed closures, collaborator pilot | Prediction order and correction persistence measured; one real question advanced |
| M2 — Reviewed artifacts | Knowledge, Skill, Insight, Hypothesis with hash-bound human review | Reviewed knowledge and a reviewed Skill with complete provenance and passing evaluations |
| M3 — Cross-topic links | Catalog plus explicit links; `rg` discovery, no index | Human-confirmed links answer a real cross-Topic question with provenance |
| M4 — Collaborator protocol | Long-horizon question → hypothesis → prediction → test loop, Skill-only | Prospective real-project evaluation passes vs. baseline |

We advance one gate at a time. Later stages may not weaken earlier evidence guarantees.

Multi-user synchronization, permissions, and remote federation are off the
roadmap. For the default single-researcher, non-adversarial model, Git and
author/reviewer provenance are sufficient until a concrete collaboration
failure disproves it.

## Complexity budget

AITP must remain a protocol with a small deterministic tool, not grow into an
agent framework.

- Keep one canonical copy of runtime source. Plugin packaging must not create a
  second hand-maintained implementation.
- Keep each Python module below 400 nonblank lines. Split by stable
  responsibility, not by abstract framework layers.
- Freeze the M0 command surface: `init`, `enter`, `record`, and `note`.
  Later commands are additive and must not weaken these contracts.
- Cumulative runtime budget: stage-end caps in `docs/roadmap.md`; about
  2,000 lines total maximum. M0.5 must deduplicate without net growth.
- Python may parse, validate, persist, project, and benchmark records. Physical
  reasoning, synthesis, literature judgment, and collaboration policy belong in
  Skills and reviewed artifacts.
- Default to no index: `rg` over Markdown is the query path. Add a derived
  cache only if a reproducible realistic benchmark demonstrates the need, and
  only as a disposable artifact.
- Do not add a required database, vector service, MCP server, hook, daemon,
  scheduler, event bus, dependency-injection system, or plugin framework.
- Target installed-plugin startup below 250 ms for `--help` and below one
  second for `enter` on a 1,000-Entry fixture.
- A new feature must include a measured use case, an acceptance test, and its
  effect on code size and startup time.
- Agent behavior conformance is measured by an external suite, never enforced
  by the runtime.

If a milestone cannot fit these constraints, reduce its scope before expanding
the runtime.

## Current state

M0 is implemented as the AITP Evidence Ledger:

```text
aitp init
aitp enter
aitp record prepare|save
aitp note prepare|save
```

Properties:

- Markdown and filesystem are canonical;
- no database, vector service, MCP server, hook, or daemon is required;
- the Codex plugin bundles `$aitp` and `$using-aitp`;
- the ledger has been validated against a real theoretical-physics workspace;
- all current tests pass.

M0.5 (slim core) is the next implementation stage, followed by M0.6 (adopt
and bootstrap). The master plan is [docs/roadmap.md](docs/roadmap.md).

## Branch policy

```text
main            stable integrated protocol, roadmap, and released capabilities
ledger-core     immutable M0 ledger baseline
slim-core       active M0.5 runtime simplification
research-graph  archived; superseded by the M3 cross-topic-links design
```

The former repository implementation is retained separately as `legacy/v5-final` during repository cutover. Old authority and experimental branches are archival evidence, not active product lines.

Feature branches should be short-lived. Stable milestones land on `main`; permanent branches exist only for explicit historical baselines.

## Repository layout

```text
.agents/plugins/                  local Codex marketplace
docs/                             concise active designs
plugins/aitp-research-protocol/   installable Codex plugin
src/aitp/                         standalone runtime
tests/ledger/                     ledger and plugin contracts
```

The repository contains no compatibility runtime for former implementations.

## Use the current ledger

The same bundle under `plugins/aitp-research-protocol/` installs on both
supported agent platforms (CLI + per-platform manifest; no MCP, hooks, or
daemon).

Install the local Codex plugin:

```bash
codex plugin marketplace add /absolute/path/to/AITP-Research-Protocol
codex plugin add aitp-research-protocol@aitp-protocol
```

Start a new Codex session and invoke:

```text
$aitp
```

Use `/skills` to inspect installed Skills. `$aitp` is a Skill invocation; `/aitp` is not a Codex slash command.

Install the same bundle in Kimi Code:

```text
/plugins install /absolute/path/to/AITP-Research-Protocol/plugins/aitp-research-protocol
/reload
```

Kimi Code runs from its managed copy (`~/.kimi-code/plugins/managed/`), so
re-run the install after the bundle changes. Invoke with `/skill:aitp`.

For standalone development:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/pytest -q
```

## Invariants

- Evidence before abstraction.
- Append history; do not silently rewrite it.
- Preserve provenance through every derived layer.
- Distinguish fact, decision, interpretation, and hypothesis.
- Keep local files readable without AITP.
- Make indexes disposable and rebuildable.
- Require explicit human gates for publication and sharing.
- Add complexity only after a real research workflow demonstrates the need.

## What AITP is not

- not a transcript archive;
- not a vector database presented as memory;
- not an autonomous scientific authority;
- not a general-purpose team permissions or synchronization platform;
- not a replacement for Git, notebooks, papers, or human review;
- not a reason to record every conversational detail.

AITP succeeds when it helps humans and agents think together over time while making it easier—not harder—to inspect why they believe something.
