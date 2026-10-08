---
name: aitp-research
description: Investigate theoretical and computational physics - derivations, synthesis across sources, discriminating calculations, implementation, debugging and benchmarks. Runs inside aitp-memory's research cycle; agree on independent branches and material changes of objective or route, then continue within that agreement.
---

# Research toward a clear answer

Start from the unresolved physical or mathematical question and the researcher's
purpose. This skill works inside [memory's research cycle](../aitp-memory/SKILL.md#the-research-cycle),
which locates the main note, recovers the argument and states this session's task;
opened directly, apply that cycle and reuse context that is already current. A
standalone explanation needs no new topic files; what it produces lands as memory's
[discussion outcomes](../aitp-memory/SKILL.md#where-discussion-outcomes-land) describe.
Keep the present step connected to the question. An exploratory topic may need a
useful question before a hypothesis; do not invent a thesis to satisfy an outline.

## Read when

| When the task involves | Read |
| --- | --- |
| An uncertain imported assumption, background, related work, references or novelty | [Literature](references/literature.md) |
| Combining several sources into one argument | [Synthesis across sources](references/literature.md#synthesize-several-sources) |
| Designing, running or debugging a calculation; developing code; a benchmark; reproducing a paper; comparing with an earlier value | [Computational work](references/computational-work.md) |
| Preparing, observing or diagnosing a batch job | [Slurm work](references/slurm.md) |
| A field's methods, conventions and standard sources | [Domain methods](#domain-methods) |
| Checking a consequential claim, number or reference | [aitp-verify](../aitp-verify/SKILL.md) |
| Learning from chosen authors | [Exemplar authors](references/exemplar-authors.md) |
| Finding or retaining a focused procedure | [Method placement and discovery](references/method-library.md) |
| An important explanation, linked derivation or revision of a note | [aitp-writing](../aitp-writing/SKILL.md) |

## Agree on consequential research choices

Use [aitp-human-brainstorming](../aitp-human-brainstorming/SKILL.md) for explicit
brainstorming or unresolved choices of purpose, independent branch scope,
consequential assumptions or success criteria. Before an independent investigation
or a material change of objective or route, resolve choices not already settled
by the current request or earlier agreement. Knowing how to do a calculation
does not establish that it answers the intended question. The interaction Skill
guides what to ask and when; research supplies the evidence and scientific options.

Continue routine derivations, diagnostics and implementation within the agreement.
Return to the researcher when the objective or route changes materially, essential
assumptions conflict with evidence, or resources or scope would exceed it. Resolve
scientific uncertainty by derivation, source checks or discriminating tests, not
by asking the researcher to select a truth. Exploratory work may aim to identify
an obstruction or a better question. Stop when the agreed stopping evidence is present.
Use memory to retain the agreement and its reasons in the
[branch's primary account](../aitp-writing/references/supporting-notes.md#follow-a-side-investigation).

Choose a derivation, example, numerical comparison or source check that could
actually change the current judgment. State the pertinent assumptions and what
different outcomes would mean. Use the smallest informative case before an
expensive expansion, while recognizing when a small case removes the very
obstruction being studied. Do not turn this into fixed phases or require a host
Goal, Research Mode or Action for ordinary work.

During a sustained branch, especially when prerequisites multiply, ask what
perfect success of the next step would establish about the original question.
Separate an error that refinement can control from a missing physical or model
relation that greater precision cannot supply. If that relation remains untouched,
retain the useful result and limitation, then reconsider the next inference or
discuss a material route change. Exploration can still reveal a mechanism or
sharpen a question; state that purpose and when to reassess it. Persistence keeps
the original objective alive, not every unfinished diagnostic on the critical path.

## Reason and respond to objections

Distinguish definitions, exact identities, hypotheses, approximations, numerical
observations and physical interpretations at the point where they matter.
Expose sign, normalization, gauge, boundary, kernel and limit assumptions when
they affect an inference. A failed ansatz excludes that ansatz under its tested
conditions; a working program or small residual does not settle the physics.

When challenged, identify the disputed step, return to a mutually accepted
starting point and rederive or test it. State whether the claim survives, needs
qualification or fails, then revise dependent conclusions. Do not continue a
lecture past an unresolved central objection or agree merely to end disagreement.

For calculations, distinguish intended configuration, executed configuration,
software comparison, numerical error and physical validity. Retain enough input,
output and code location to continue the actual experiment. Select error and
convergence checks for the observable being claimed, and design the experiment before
running it, as [computational work](references/computational-work.md) describes.
Repeated runs without a new discriminating question call for revisiting the method,
not a larger scan. Before a new, changed or disputed consequential claim is relied on,
check it with [aitp-verify](../aitp-verify/SKILL.md), by a route different from the one
that produced it.

## Domain methods

A field's shareable methods, conventions and checks, and the standard sources for its
methods, live under `methods/<domain>/`, indexed by the domain's README. The researcher's
own topic skills stay in the workspace, listed in the topic family's README. Read a
domain index when the task uses that field's methods, whether investigating with them,
writing about them or learning them; no task requires one before research can proceed.
[Method placement](references/method-library.md) explains where a new method belongs.

| Domain | Index |
| --- | --- |
| GW, RPA and LibRPA, including [developing LibRPA](methods/librpa/developing-librpa/SKILL.md) | [methods/librpa](methods/librpa/README.md) |
| Quantum chaos: spectra, OTOCs, operator growth | [methods/quantum-chaos](methods/quantum-chaos/README.md) |

Read only the resources needed for the current task.
Keep machine-specific setup in the project's environment instructions, and tool
environments in their established, authorized location, never in a prose-only reading or
note folder. A known operation needs no new tutorial or
repeated method search.

For placement of scripts, figures, inputs, outputs and shared development,
use the locations explained in the topic or project README and the relevant
research notes. Consult [asset placement and links](../aitp-memory/references/local-assets.md)
when a location is unclear or a move is requested. Keep the main argument linked
to the detailed work, with its analysis, data and figures connected where they
support a claim. Explain newly established locations in the README; reuse known
ones without another inventory or a copy for each note.

## Learn formal theory through a question

For interactive learning or a conceptual difficulty, use
[aitp-human-learning](../aitp-human-learning/SKILL.md) to adapt to the researcher's
question and background, reusing what is already known. It is conditional, not
a prerequisite interview for every theory task. Introduce each consequential
definition at its first use, then work
through a faithful example and the step that makes the claim nontrivial. Return
to the question after the calculation: what did it establish, and what extra
input would connect it to the intended physics? A list of references or a sequence
of named concepts is not yet that explanation.

Distinguish a derivation performed here from a theorem imported from a source and
from a conjectured application. If an objection reveals a missing prerequisite,
resolve that step before extending the argument. Retain substantial background
when it adds lasting understanding, using an existing explanation where suitable;
the main note retains the line of reasoning.
Distill a Skill only when the work teaches a reusable operation, such as checking
an anomaly under stated assumptions, rather than a summary of a theorem.

## Start theoretical work from shared knowledge

Begin a theoretical derivation, a conceptual question, or a reading or study task,
including the theoretical part of a numerical project, from what is already understood. When the researcher
keeps a [shared collection](../aitp-memory/references/shared-knowledge.md), read its
index once at the start, then open the entries for the task's central concepts and
sources. Reuse their conventions or state the difference. This is one bounded read
per task. After it, continue a fluent derivation without further searches. Consult the
collection again for a conceptual obstacle, a questioned assumption, or the coverage check
before creating an atom; that check can reuse the initial read when it already covers
the proposed entry.
Routine coding, job handling and plotting do not trigger this. Their normal
research-memory and source checks still apply.

When the task reads a paper or lecture, start from its reading in the collection
if one exists. When the session establishes something new, leave the reading improved:
locators checked, what the passage establishes, and the index rows it serves. For close reading, use
[learning from a source](../aitp-writing/references/learning.md#read-a-source-closely).
Check for an existing atom before creating one. Read-only reuse needs no update.
Separately, when work produces a useful new explanation, technique, correction or
reusable connection, retain it at a natural pause even if no library lookup or
conceptual obstacle occurred, as described under
[retaining the result](#retain-the-result-and-reusable-learning). Preserve fragile
reasoning sooner if necessary. In learning, understanding is itself
the task; in research, develop background to the depth needed by the current
argument. Do not expand either task into routine library maintenance.

## Retain the result and reusable learning

Explain the supported conclusion, decisive evidence, limits and useful next
step. At a natural pause or handoff after consequential work, apply memory's
[write decision](../aitp-memory/SKILL.md#timing-and-recovery) to both the research
argument and any transferable learning. Some results could be used by another question
beyond this topic, with their assumptions stated: a derivation, a technique (theoretical
or numerical), an example, a counterexample or a correction. These belong in the
researcher's shared collection as well. They go there as an index row citing the research
note's section and naming the question rather than restating the result, marked
provisional and awaiting review. The research note stays the single
home of the claim, and an atom is written only after the researcher confirms the result.
When a collection exists, decide this in the same pass as the topic note; it does not
need a separate request. See
[what research teaches](../aitp-memory/references/shared-knowledge.md#add-what-research-teaches),
which also says where a passage read closely during the work should go. Notice a demonstrated non-obvious
choice, diagnostic sequence, failure-prevention method or correction to an
existing procedure; use [aitp-distill](../aitp-distill/SKILL.md) when it teaches
a reusable operation. Do not wait for an explicit distillation request or repeat
failure. Use writing for substantive note changes. An unchanged query needs no
learning review, and the existing research text and assets can carry the result
without a companion report.
