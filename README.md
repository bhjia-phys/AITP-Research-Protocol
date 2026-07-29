# AITP Research Protocol

AITP is a local-first protocol for long-running collaboration between researchers and AI agents.

Its goal is not merely to save notes. A mature AITP collaborator should remember the details that matter, recover why decisions were made, preserve failed attempts, connect knowledge across Topics, extract reusable physical knowledge and technical Skills, and surface new Insights without confusing them with established results.

## North star

After weeks or years of work, a new session should be able to:

- resume a Topic without asking the researcher to repeat its history;
- cite the exact evidence behind every remembered claim;
- recall conventions, constraints, decisions, failures, and open questions;
- connect a current problem to relevant results from other Topics;
- distinguish physical knowledge, reusable procedure, and speculative Insight;
- propose a reusable Skill with provenance and evaluations;
- work with a researcher across many sessions without losing corrections,
  commitments, or the reasoning behind the current direction.

AITP records project memory, not scientific truth. Evidence and human judgment remain authoritative.

## Architecture

```text
Research artifacts
      ↓
Evidence ledger
      ↓
Research graph
      ↓
Knowledge / Skill / Insight compilers
      ↓
Conversation memory orchestration
      ↓
Scientific collaborator loop
```

### 1. Research artifacts

Code, derivations, data, figures, literature, run outputs, and manuscripts remain in ordinary repositories. AITP references them with exact locators and immutable pins.

### 2. Evidence ledger

The ledger preserves small durable events:

```text
observation  result  failure  decision
source       code-change  run  closeout
```

Entries are append-only. `resolves` closes a failure; `supersedes` replaces an older record without rewriting history. Notes synthesize pinned evidence.

### 3. Research graph

The graph projects multiple Topic ledgers into a rebuildable knowledge view:

- Topic, Entry, Note, artifact, and candidate nodes;
- evidence, resolution, contradiction, method, and extension edges;
- grounded cross-Topic query with exact sources and freshness;
- explicit saved links; inferred links remain proposals.

The graph never replaces Topic repositories. See [Research Graph Design](docs/research-graph-design.md).

### 4. Research compilers

The same evidence can produce different reviewed artifacts:

- **Physical knowledge** — claims, assumptions, validity domains, checks, and contradictions.
- **Technical Skill** — repeatable procedure, prerequisites, commands, failure modes, and evaluations.
- **Insight** — a potentially useful connection or hypothesis, clearly marked as unverified.
- **Research brief** — the minimum grounded context needed to resume or hand off work.

Every compiled statement must map back to source records. Compilation never silently promotes a hypothesis into knowledge.

### 5. Conversation memory orchestration

M3 connects the preceding layers to each research conversation. It does not
add another source of truth. It:

- detects the current workspace, Topic, task, and context budget;
- builds a compact Context Packet containing the active question, conventions,
  constraints, relevant decisions and failures, reviewed knowledge, useful
  Skills, candidate Insights, open commitments, and exact evidence references;
- refreshes that packet when the task, object, method, or assumptions change;
- proposes an Entry only at a durable research event, using the existing
  `prepare → validate on save → commit` path;
- records corrections and closeout state so the next session can resume;
- explains why each item was included, omitted, or marked stale.

The agent may write an attributable agent Entry when workspace policy allows
it. Decisions, promoted knowledge, published Skills, and accepted Insights
remain human-gated. See [Collaborator Design](docs/collaborator-design.md).

### 6. Scientific collaborator loop

M4 is the actual research-collaboration layer. It uses grounded memory to:

- maintain active questions, competing hypotheses, assumptions, predictions,
  tests, outcomes, and contradictions;
- challenge a proposed step with known failures or validity limits;
- suggest the next derivation, calculation, source check, or numerical test;
- record predictions before seeing outcomes and compare the result afterward;
- turn supported Insights into reviewed knowledge while preserving rejected
  alternatives and uncertainty.

M4 is not a claim that the agent is an autonomous scientist. Its contribution
must remain inspectable, evidence-linked, uncertainty-aware, and correctable.

## Roadmap

| Stage | Outcome | Exit gate |
|---|---|---|
| M0 — Ledger | Reliable single-Topic records and Notes | Idempotent writes, pinned evidence, grounded `enter`, real-project use |
| M0.5 — Slim core | One small canonical runtime with measured startup and no copied implementation | No runtime source duplication, no oversized module, unchanged ledger contracts |
| M1 — Graph | Multi-Topic catalog, sync, query, and explicit links | Three Topics query with provenance; index rebuild is deterministic |
| M2 — Compilers | Physical knowledge, Skill candidates, Insights, briefs | Complete provenance, contradiction handling, evaluations, human approval |
| M3 — Context engine | Task-aware Context Packets and inspectable write policy | A fresh session resumes real work with correct conventions, evidence, failures, and commitments |
| M4 — Scientific collaborator | Long-horizon question → hypothesis → prediction → test → outcome loop | Real projects are advanced without unsupported recall, hidden state, or hindsight rewriting |

We advance one gate at a time. Later stages may not weaken earlier evidence guarantees.

Multi-user synchronization, permissions, and remote federation are optional
infrastructure, not a core milestone. Git and author/reviewer provenance are
sufficient until real team use demonstrates a stronger requirement.

## Complexity budget

AITP must remain a protocol with a small deterministic tool, not grow into an
agent framework.

- Keep one canonical copy of runtime source. Plugin packaging must not create a
  second hand-maintained implementation.
- Keep each Python module below 400 nonblank lines. Split by stable
  responsibility, not by abstract framework layers.
- Freeze the M0 command surface: `init`, `enter`, `record`, and `note`.
- Python may parse, validate, persist, project, and benchmark records. Physical
  reasoning, synthesis, and collaboration policy belong in Skills and reviewed
  artifacts.
- Build the first graph projection as deterministic JSONL. Add SQLite/FTS only
  if a reproducible realistic benchmark shows JSONL lookup is insufficient.
- Do not add a required database, vector service, MCP server, hook, daemon,
  scheduler, event bus, dependency-injection system, or plugin framework.
- Target installed-plugin startup below 250 ms for `--help` and below one
  second for `enter` on a 1,000-Entry fixture.
- A new feature must include a measured use case, an acceptance test, and its
  effect on code size and startup time.

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

M0.5 is the next implementation stage. M1 remains the active product design,
but graph code must not land until the slim-core gate passes.

## Branch policy

```text
main            stable integrated protocol, roadmap, and released capabilities
ledger-core     immutable M0 ledger baseline
slim-core       active M0.5 runtime simplification
research-graph  M1 design baseline; runtime work waits for M0.5
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
