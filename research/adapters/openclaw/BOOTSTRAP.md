# OpenClaw bootstrap

This file defines how a fresh OpenClaw agent should enter the AITP / OMTP workspace without guessing the architecture from scattered notes.

## Purpose

OpenClaw is a host-specific adapter, not the kernel itself.

The kernel is the architecture and artifact contract.
OpenClaw provides:
- tool access,
- file writeback,
- web and media intake,
- execution delegation,
- human-facing coordination.

## Read order for a fresh agent

Read in this order before doing substantial work:

1. `research/knowledge-hub/LAYER_MAP.md`
   Use this to know which directories are the current source-of-truth surfaces and which are legacy or coordination surfaces.

2. `research/knowledge-hub/README.md`
   Use this to load the L1/L2/L3/L4 architecture.

3. `research/knowledge-hub/ROUTING_POLICY.md`
   Use this to understand how new material should enter and move across the layers.

4. `research/knowledge-hub/INDEXING_RULES.md`
   Use this to understand how ids, indexes, retrieval profiles, and cross-layer references actually work during reasoning.

5. `research/knowledge-hub/COMMUNICATION_CONTRACT.md`
   Use this to understand the minimum handoff objects and the distinction between routing, consultation, and writeback edges.

6. `research/knowledge-hub/L2_CONSULTATION_PROTOCOL.md`
   Use this to understand how `L1`, `L3`, and `L4` should consult `L2` as active memory rather than just logging an ad hoc retrieval.

7. `research/knowledge-hub/L0_SOURCE_LAYER.md`
   Use this to understand how later layers may call back into Layer 0 for source reopening, acquisition, and retrieval.

8. `research/knowledge-hub/source-layer/README.md`
   Use this to understand the dedicated persistent Layer 0 storage surface and the source-of-truth rule for registered sources.

9. `research/knowledge-hub/AUTONOMY_AND_OPERATOR_MODEL.md`
   Use this to understand the persistent-research-loop model, the self-modification boundary, and the operator-facing visibility requirements.

10. `research/knowledge-hub/AGENT_CONFORMANCE_PROTOCOL.md`
   Use this to understand what runtime artifacts are required for a run to count as AITP-conformant.

11. `research/knowledge-hub/runtime/README.md`
   Use this when resuming an existing topic or materializing an action queue for the next agent.

12. `research/adapters/openclaw/AITP_AGENT_ENTRYPOINT.md`
   Use this when you want one executable entrypoint for topic bootstrap or resume instead of reconstructing the route by hand.

13. `research/adapters/openclaw/PLUGIN_PROFILE_INSTALL.md` when the task is to seed or migrate this AITP/OpenClaw profile into another workspace.
   Use this to install the OpenClaw plugin, root profile, and minimal kernel surface as one reproducible unit.

14. `research/adapters/openclaw/SKILL_ADAPTATION_PROTOCOL.md`
   Use this when the real blocker is a missing workflow, integration, or external capability and AITP should decide whether to discover, review, vendor, or install a skill.

15. `research/knowledge-hub/intake/ARXIV_FIRST_SOURCE_INTAKE.md` when the task is literature-heavy and arXiv-backed.
   Use this to prefer arXiv source packages over PDF whenever possible.

16. `research/knowledge-hub/validation/BASELINE_REPRODUCTION_AND_UNDERSTANDING_GATES.md`
   Use this before trusting a new numerical backend or claiming that a derivation-heavy method is already understood.

17. `research/knowledge-hub/canonical/CANONICAL_UNIT.md`
   Use this to understand the shared Layer 2 contract.

18. `research/knowledge-hub/canonical/LAYER2_OBJECT_FAMILIES.md`
   Use this to choose the correct Layer 2 type.

19. `research/knowledge-hub/canonical/PROMOTION_POLICY.md`
   Use this to decide whether something belongs in Layer 2 at all.

20. `research/knowledge-hub/canonical/L3_L4_LOOP.md`
   Use this to decide whether work should stay exploratory, move to validation, or promote.

21. `research/knowledge-hub/examples/source-to-canonical-route.md`
   Use this to see one concrete route and one concrete promotion chain before inventing a new one.

22. `/home/bhj/projects/repos/Theoretical-Physics/obsidian-markdown/11 L4 Validation/README.md` when the task is validation-heavy.
   Use this to understand the Layer 4 control plane and how execution is dispatched.

23. `research/knowledge-hub/validation/EXECUTION_PROTOCOL.md` when the task requires execution-backed validation.
   Use this to understand how task records and promotion decisions are serialized.

24. `research/knowledge-hub/canonical/L2_BACKEND_INTEGRATION_PROTOCOL.md` when the task is to connect a formal-theory note library, software repository, or result store to `L2`.
   Use this to keep backend registration explicit and avoid treating an external folder as canonical knowledge by path alone.

25. The active Share_work handoff note for the current thread.
   Use this to pick up the latest local decisions, blockers, and next steps.

26. Only then read topic-specific run artifacts relevant to the user's actual request.

## Default operating sequence

1. Identify the user's requested surface.
   Decide whether the task begins from:
   - a new source,
   - an existing topic run,
   - a Layer 2 object revision,
   - a validation request,
   - or an adapter/bootstrap request.

1a. When you need an executable bootstrap or resume entrypoint, use:
   - `python3 research/adapters/openclaw/scripts/aitp_loop.py ...` as the preferred single-entry OpenClaw plugin surface for bootstrap, resume, and bounded auto-advance.
   - `python3 research/adapters/openclaw/scripts/aitp_topic_runner.py ...` only as a compatibility wrapper around the same loop surface.
   - `python3 research/knowledge-hub/runtime/scripts/orchestrate_topic.py ...` only when you are explicitly working on the internal runtime materializer itself.

2. Choose the layer before choosing the tool.
   Do not start from tool availability.
   Start from the epistemic role of the work.

3. When the blocker is a missing capability rather than missing evidence, enter the skill-adaptation protocol instead of silently stalling.
   Use `research/adapters/openclaw/SKILL_ADAPTATION_PROTOCOL.md` and the discovery wrapper before deciding whether to vendor, install, or reject an external skill.
   If the queue already contains reviewed auto-runnable capability work, dispatch only through `research/adapters/openclaw/scripts/dispatch_action_queue.py`.

4. Create or update the primary artifact in its canonical location.
   Do not use chat as the primary state surface.

5. Materialize runtime visibility.
   Leave `interaction_state.json` and `operator_console.md` truthful enough that another agent or the human can intervene without reconstructing the route manually.
   For heartbeat-compatible scheduling, prefer a concise workspace `HEARTBEAT.md` plus `HEARTBEAT_AITP.md` that calls `aitp loop --updated-by openclaw-heartbeat --max-auto-steps 1 --json`.
   Keep `research/adapters/openclaw/scripts/heartbeat_bridge.py` only as a compatibility path when explicit adapter-owned heartbeat receipts are needed; it should still only trigger `aitp_loop.py --max-steps 1`.

6. Record cross-agent state in Share_work only when the work creates a durable architecture milestone, handoff need, or unresolved design fork.

7. When execution-heavy work is required, delegate to the appropriate execution surface instead of pretending the result in prose.

## What OpenClaw may create or update directly

OpenClaw may directly create or update:
- Layer 1 intake artifacts,
- Layer 3 run artifacts,
- Layer 4 validation records,
- Layer 2 docs and schemas when the task is explicitly architectural,
- Share_work handoff notes,
- adapter docs under `research/adapters/openclaw/`.

OpenClaw may also propose Layer 2 content objects, but should only canonicalize them when the promotion policy is actually satisfied.

## What should usually require a human checkpoint

Require an explicit human checkpoint before:
- changing the public baseline wording of the layer model,
- changing Layer 2 object-family semantics,
- deleting or merging existing canonical object types,
- promoting a high-impact scientific claim whose scope is still debatable,
- changing the allowed promotion routes,
- pushing ambiguous architecture language into the public repo,
- running costly or irreversible external actions not already requested.

## Delegation policy

Use OpenClaw-native capabilities for:
- web / PDF / transcript intake,
- note and file coordination,
- lightweight repository edits,
- orchestration across artifacts.

Delegate to execution-oriented agents or tools for:
- numerical code changes,
- symbolic or formal proof tooling,
- larger codebase refactors,
- benchmark reproduction,
- tasks where executable evidence matters more than prose.

The important point is:
OpenClaw is allowed to orchestrate execution, but orchestration is not itself validation.

## Layer routing heuristics

### Start in Layer 1 when
- the user provides a paper, URL, PDF, video, or conversation source,
- the material is still source-bound,
- the main need is disciplined understanding rather than canonical writeback.

### Start in Layer 3 when
- the work is already an active research question,
- the task involves interpretation, derivation planning, or unresolved alternatives,
- the material is not yet settled enough for canonical storage.

### Start in Layer 4 when
- a Layer 3 candidate already exists,
- the next task is an explicit check, benchmark, contradiction test, or adjudication step.

### Touch Layer 2 only when
- the output is reusable,
- typed identity is clear,
- provenance is explicit,
- the required promotion route has been satisfied.

## Session-start checklist

At the beginning of a substantial session, confirm:
- the active user request,
- the current handoff note if one exists,
- the target layer,
- the primary artifact path,
- whether execution delegation will be needed,
- whether a human checkpoint is already implied.

## Session-close checklist

Before ending a substantial session:
- update the primary artifact on disk,
- update Share_work if a real handoff or architecture milestone was produced,
- record blockers honestly,
- leave the next action in a state that another agent can continue without re-deriving the context.

## Non-goals

This bootstrap file does not define:
- the final public repo wording,
- topic-specific scientific truth,
- tool-specific syntax for every future runtime.

It only defines how OpenClaw should enter and operate inside the current kernel architecture.
