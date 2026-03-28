# A Real AITP Topic Journey

This document shows what AITP is supposed to feel like when someone uses it on
a real theoretical-physics topic.

The goal is not to teach every schema or command.
The goal is to show the user-facing journey that the runtime, skills, plugins,
and durable artifacts are all trying to support.

## What AITP is trying to automate

AITP is meant to automate a large fraction of the research execution work:

- topic setup
- literature scouting
- source-grounded note intake
- benchmark planning
- derivation or implementation work
- durable status tracking
- candidate knowledge distillation

AITP is not trying to automate away the human researcher.

The human still owns:

- direction
- novelty
- expensive route choices
- whether a result is trusted enough to deserve durable promotion

In practice this means:

- most ordinary research execution should be automatic
- AITP should only stop to ask when the answer changes the route materially

## Shared behavior across every lane

No matter which research lane is active, the user-facing pattern should be the
same.

### 1. The user starts naturally

Examples:

- `I want to study the Haldane-Shastry integrable to chaos transition. Start with the question definition and the first validation route.`
- `Continue this topic and shift the direction toward operator robustness.`
- `Can this paper's argument be turned into a bounded benchmark for my model?`

The user should not need to remember a front-door command language.

### 2. AITP clarifies only if it must

If the request is already specific enough, AITP should start.

If the request is still ambiguous in a way that changes the route, AITP should
ask one short natural-language question, for example:

- `Do you want the first pass to optimize for mechanism understanding or for a reproducible benchmark?`
- `Should I stay with the current topic and redirect it, or should I open a fresh branch?`

AITP should not say:

- `I am emitting a decision_point`
- `I need an L2 consultation`
- `I am switching to a full load profile`

### 3. AITP stays light unless something important happens

Ordinary topic work should stay in a light runtime profile.
That means the agent should only need a small topic synopsis, current steering,
the active research question, and the operator-facing console.

AITP should only expand into the full runtime bundle when something important
happens, such as:

- a benchmark mismatch
- a real scope change
- promotion preparation
- exit audit

### 4. The human can always ask what happened

At any point the user should be able to ask:

- `Where are we on this topic?`
- `Why did you choose that route?`
- `What is still missing before this is closed?`

AITP should answer from durable runtime state, not from chat improvisation.

## Lane 1: Formal theory topic

### User start

`I want to turn Jones Chapter 4 into a bounded formal-theory research topic. Start from the finite-dimensional backbone and tell me what the first honest closure target is.`

### What AITP should do

1. Open or reuse the topic.
2. Determine whether the question is specific enough.
3. Pull the relevant sources and source maps into the active runtime.
4. Build the current bounded question and validation route.
5. Surface only the next proof or derivation lane that is honest now.

### What the user sees

The user should see something like:

`The first honest target is not the whole chapter. The bounded target is the finite-dimensional backbone packet. I can start by checking which definitions, proof obligations, and open gaps are already present, then tell you exactly what remains open.`

### Human checkpoint example

`I can keep this as one topic with a bounded Chapter 4 target, or I can split out a separate branch just for the type-I classification route. The first option keeps the current history cleaner; the second makes the remaining gap more explicit. Which do you want?`

### Resume later

The next day the user says:

`Continue this topic. What is the current blocker?`

AITP should answer from durable state:

- the active bounded target
- the current proof or source gap
- whether the topic needs L0 recovery before deeper proof work

### What gets distilled

As useful results emerge, AITP should create candidate knowledge packets such
as:

- theorem packet
- concept packet
- open-gap packet

These remain candidate or validated packets until promotion gates say
otherwise.

## Lane 2: Toy numerics topic

### User start

`I want to study the Haldane-Shastry model from integrability to quantum chaos. Start by finding the right benchmark surface before we push a new idea.`

### What AITP should do

1. Register the topic and current steering.
2. Gather the baseline papers and source-grounded observables.
3. Separate benchmark reproduction from the target idea implementation.
4. Build the first bounded benchmark route.
5. Only after the benchmark surface is honest, push the new idea.

### What the user sees

`I am going to separate this into two stages: first the exact benchmark surface, then the new chaos-transition idea. That keeps the route honest if the observable definition turns out to be wrong.`

### Human checkpoint example

If the benchmark mismatches:

`The benchmark result is not just slightly off. This looks like either a definition mismatch or a real implementation problem. I can pause the idea work and debug the benchmark first, or I can document the mismatch and keep the idea lane exploratory. Which route do you want?`

### Resume later

The user asks:

`Why did you stop before the larger-system lane?`

AITP should be able to answer:

- which benchmark result was unstable
- which decision trace recorded the route choice
- what the next bounded action is now

### What gets distilled

The reusable outputs are not only final claims.
They also include:

- benchmark packets
- method packets
- regression-status packets
- candidate reusable workflows

## Lane 3: Code-backed method topic

### User start

`I want to turn this paper method into a reproducible implementation path inside the existing codebase. Start by finding the benchmark, then make the smallest working implementation route.`

### What AITP should do

1. Keep the outer user experience natural-language first.
2. Use the agent's normal code-reading, editing, and testing abilities.
3. Treat the coding work as one execution branch inside the topic, not as a detached software task.
4. Keep benchmark, validation, and trust state inside AITP.

### What the user sees

`I will first identify the smallest benchmark that proves the implementation route is sane, then I will map the code changes needed for that route. Once that is stable, I can push the larger method change.`

### Human checkpoint example

`I can make the smallest benchmark-first patch now, or I can try to wire the full method path immediately. The first route is slower upfront but much safer.`

### Why coding inside AITP matters

Coding inside AITP is not just ordinary coding with a physics label.

The outer experience should still feel like Superpowers:

- natural language first
- skills only when relevant
- low context cost by default

But the outputs still enter the AITP research kernel:

- benchmark evidence
- trust audits
- candidate packets
- promotion readiness

## What “high automation” means here

AITP should eventually support long stretches of autonomous work:

- literature gathering
- source-grounded summarization
- benchmark setup
- implementation work
- repeated bounded validation
- durable status writeback

But the near-term target is not fake full autonomy.

The target is:

- the human gives direction and standards
- AITP executes most of the bounded work
- AITP only stops at real route-changing checkpoints

## The success condition

This whole system is working if a user can do the following without learning a
special command language:

1. start a topic from an idea
2. let AITP do the literature and execution work
3. answer only the checkpoints that matter
4. return later and continue the same topic
5. ask what happened and get an honest state answer
6. gradually accumulate reusable knowledge instead of losing everything into chat
