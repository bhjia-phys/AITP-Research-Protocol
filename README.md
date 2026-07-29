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
- collaborate with several people without erasing disagreement or private context.

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
Collaborator memory and context selection
      ↓
Multi-researcher project federation
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

### 5. Collaborator memory

The collaborator layer decides what to read and when to propose a record. It should:

- enter the relevant Topic at session start;
- remember notation, physical conventions, computational constraints, and ownership;
- retrieve prior failures before repeating an attempt;
- notice contradictions and ask for resolution;
- propose durable records at meaningful moments rather than logging every message;
- retain commitments, open questions, and next actions;
- provide compact context instead of dumping the complete archive.

Automatic behavior remains inspectable: the agent explains what it read, what it proposes to write, and which evidence supports it.

### 6. Project federation

Long-term team collaboration requires:

- shared and private memory boundaries;
- author and reviewer identity;
- concurrent edits and explicit conflict handling;
- portable Topic catalogs across machines;
- auditable publication of Knowledge Cards and Skills;
- selective sharing across projects rather than one global memory pool.

## Roadmap

| Stage | Outcome | Exit gate |
|---|---|---|
| M0 — Ledger | Reliable single-Topic records and Notes | Idempotent writes, pinned evidence, grounded `enter`, real-project use |
| M1 — Graph | Multi-Topic catalog, sync, query, and explicit links | Three Topics query with provenance; index rebuild is deterministic |
| M2 — Compilers | Physical knowledge, Skill candidates, Insights, briefs | Complete provenance, contradiction handling, evaluations, human approval |
| M3 — Collaborator | Conversation-aware read/write proposals and context selection | A fresh session resumes real work without hidden state or repeated failures |
| M4 — Team | Multi-researcher permissions, review, merge, and sharing | Concurrent collaboration remains attributable and auditable |
| M5 — Research intelligence | Cross-project synthesis and hypothesis support | Suggestions remain evidence-linked, uncertainty-calibrated, and human-gated |

We advance one gate at a time. Later stages may not weaken earlier evidence guarantees.

## Current state

M0 is implemented as AITP Research Memory:

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

M1 is the active design and implementation stage on `research-graph`.

## Branch policy

```text
main            stable integrated protocol, roadmap, and released capabilities
memory-core     immutable M0 ledger baseline
research-graph  active M1 development
```

The former repository implementation is retained separately as `legacy/v5-final` during repository cutover. Old authority and experimental branches are archival evidence, not active product lines.

Feature branches should be short-lived. Stable milestones land on `main`; permanent branches exist only for explicit historical baselines.

## Repository layout

```text
.agents/plugins/                  local Codex marketplace
docs/                             concise active designs
plugins/aitp-research-memory/     installable Codex plugin
src/aitp/                         standalone runtime
tests/aitp_lite/                  ledger and plugin contracts
```

The repository contains no compatibility runtime for former implementations.

## Use the current ledger

Install the local Codex plugin:

```bash
codex plugin marketplace add /absolute/path/to/AITP-Research-Memory
codex plugin add aitp-research-memory@aitp-memory
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
- not a replacement for Git, notebooks, papers, or human review;
- not a reason to record every conversational detail.

AITP succeeds when it helps humans and agents think together over time while making it easier—not harder—to inspect why they believe something.
