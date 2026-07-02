# AITP Positioning

AITP is the AI-facing research graph kernel for theoretical and computational
physics. Its job is to preserve the scientific memory that an agent needs in
order to continue research responsibly: what was claimed, where it came from,
what was checked, which routes failed, which methods worked, and which
conclusions are not yet trusted.

This document is the product and architecture positioning for the current v5
line. It does not replace `docs/AITP_SPEC.md`; it explains how the protocol,
typed records, domain packs, and literature surfaces fit together.

## One-Sentence Positioning

AITP is a local research graph kernel and AI research memory layer that exposes
typed, provenance-aware scientific context to agents through MCP, CLI, plugins,
and host adapters.

## What AITP Is

- A durable research graph for physics work.
- A typed memory layer for AI agents and human researchers.
- A context compiler that exposes the right bounded slice of prior research.
- A provenance and trust harness for claims, sources, code runs, validations,
  checkpoints, and memory promotion.
- A base layer on which domain experience packs can make an agent more useful
  in specific research areas.

## What AITP Is Not

- Not a chatbot.
- Not a generic note app.
- Not a plain vector database or RAG index.
- Not an automatic theorem prover.
- Not a replacement for human judgment at theory or trust boundaries.
- Not a separate truth layer inside each host agent.

## Core Architecture

```text
AI host or human workflow
        |
        v
Agent interface: MCP, CLI, Codex plugin, host adapter
        |
        v
Context compiler: briefs, packs, relation maps, source stacks, dashboards
        |
        v
Research graph kernel: typed records under <topics-root>/.aitp/
        |
        v
Domain and literature substrates: source blobs, curated corpora, experience packs
```

The graph kernel is authoritative. Context packs, dashboards, summaries, RAG
snippets, and domain recommendations are orientation surfaces unless they are
converted into typed evidence, validation, or promotion records through the
normal gates.

## Layer 1: Research Graph Kernel

The kernel stores typed scientific state:

- topics, sessions, contexts, and active claims;
- sources, source assets, exact reference locations, and source blobs;
- physics objects, definitions, notation, equations, and object relations;
- evidence, assumptions, proof obligations, and unresolved gaps;
- code state, tool recipes, tool runs, artifacts, and run provenance;
- validation contracts, validation results, failure modes, and audits;
- human checkpoints, promotion packets, trust updates, and memory entries.

This is the part of AITP that should remain stable across hosts. Codex, Claude
Code, Kimi Code, Hakimi, or another agent should all talk to the same store
instead of keeping separate scientific memories.

## Layer 2: Context Compiler

Agents should not load the entire research graph by default. AITP compiles
bounded context for the task:

- compact context packs for startup and continuation;
- execution briefs that show next valid actions;
- claim relation maps and source-reconstruction audits;
- process graphs and dashboards for active research;
- recording navigation surfaces that decide where a durable moment belongs;
- closeout and checkpoint surfaces for handoff.

Compilation is not summarization alone. It should preserve references to typed
records, reliability state, missing evidence, validation status, and known
failure modes.

## Layer 3: Domain Experience Packs

Domain experience packs turn the memory kernel into a more experienced research
collaborator. A pack can recommend:

- workflows;
- validation recipes;
- safe tool executors;
- common failure modes;
- required provenance;
- final-vs-diagnostic lane rules;
- domain-specific source and artifact conventions.

For example, a LibRPA/GW and first-principles pack can encode checks for basis
cutoffs, frequency grids, Coulomb singularity handling, code-state provenance,
Slurm/HPC run status, benchmark recipes, formula-code invariants, and rules
that prevent diagnostic or nonconverged data from becoming final evidence.

Domain packs guide the agent. They do not promote trust by themselves.

## Layer 4: Literature And Knowledge Substrate

AITP can store and index local PDFs, source blobs, notes, and curated corpora.
This is how a host agent can ask for quantum field theory, quantum gravity,
topological order, or computational-physics background without starting from
scratch.

The literature layer should support:

- source acquisition and local blob storage;
- exact page, equation, section, figure, and note references;
- concept and notation extraction;
- source-backed reading routes across multiple papers;
- conflict, dependency, and scope tracking;
- promotion into evidence only when a source is linked to a specific claim.

Retrieved literature context is useful orientation. It becomes claim support
only through typed source, reference-location, evidence, validation, and trust
records.

## Role Of L0-L4

L0-L4 remains useful vocabulary for research semantics:

- L0: source substrate;
- L1: provisional understanding;
- L3: candidate derivation and exploratory work;
- L4: validation and adjudication;
- L2: promoted reusable knowledge.

In the v5 implementation, these are not the primary storage structure. The
source of truth is the typed `.aitp` graph. Legacy L0-L4 files remain important
for migration, review, and historical recovery, but new durable writes should
go through v5 typed records.

## Success Standard

AITP succeeds when a future AI agent can enter a real research problem and
answer these questions from the graph:

- What is the current claim or research focus?
- What is verified, what is only plausible, and what is open?
- Which sources, formulas, code states, and runs support the current view?
- Which domain-specific failure modes must be checked?
- What has already failed or been ruled out?
- What is the next valid action?
- What must not be promoted to long-term memory yet?
