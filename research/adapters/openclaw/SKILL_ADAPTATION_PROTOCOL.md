# OpenClaw external skill adaptation protocol

This file defines how AITP may discover and adopt external skills without
turning third-party installation into an implicit side effect.

The protocol is aligned with the public `skills` CLI ecosystem and the
`find-skills` workflow, but it is stricter about review and persistence inside
the AITP workspace.

## Purpose

Use this protocol when AITP encounters a real capability gap such as:

- missing workflow knowledge,
- missing integration pattern,
- missing intake helper,
- missing validation or execution wrapper,
- repeated manual work that should become a reusable skill.

## Default posture

Discovery is allowed by default.

Installation is not.

The first job is to answer:

1. does a useful external skill appear to exist,
2. is it actually relevant to the current blocker,
3. should AITP read it, vendor it, install it locally, or reject it.

## Safety gates

Before adoption, check:

1. repository owner and source URL,
2. the specific `SKILL.md` or skill directory,
3. whether the skill is needed for the current task,
4. the target install path,
5. whether project policy allows installation there,
6. whether a simpler local implementation is better.

Current AITP workspace policy:

- `skills-shared/` is the canonical internal skill source,
- do not silently install third-party skills into repo root,
- do not silently install third-party skills into global user paths,
- prefer read-only reference or reviewed local rewrite unless installation is
  explicitly requested and its target path is approved.

## Decision outcomes

Every discovery round should end in one of these states:

- `discover_only`
  - candidate exists, but keep it as external reference only
- `review_required`
  - promising candidate, but source review is still pending
- `vendor_local`
  - useful instructions should be rewritten into a reviewed local skill
- `approved_local_install`
  - install is acceptable into an explicitly approved local agent path
- `rejected`
  - irrelevant, unsafe, or lower quality than local alternatives

## Artifact contract

Capability discovery should be materialized under the runtime surface for the
active topic whenever possible:

- `runtime/topics/<topic_slug>/skill_discovery.json`
- `runtime/topics/<topic_slug>/skill_recommendations.md`

These artifacts should record:

- query text,
- raw discovery command,
- discovered candidates,
- review status,
- recommended adoption mode,
- safety notes,
- proposed next command if a later install is approved.

## Wrapper command

Use the AITP wrapper instead of calling `npx skills find` directly when the
result should become part of the runtime state:

```bash
python3 research/adapters/openclaw/scripts/discover_external_skills.py \
  --topic-slug <topic_slug> \
  --query "<capability query>"
```

Use multiple `--query` flags when needed.

## Typical loop

1. detect the blocker,
2. formulate one or more capability queries,
3. run the wrapper command,
4. inspect the recommended candidates,
5. choose one adoption mode,
6. record the decision in runtime or Share_work when architecture is affected.

## Important distinction

External skill discovery is an adapter-level capability loop.

It is:

- not a new knowledge layer,
- not a substitute for `L2`,
- not a license to skip validation,
- a controlled way for AITP to improve how it works.
