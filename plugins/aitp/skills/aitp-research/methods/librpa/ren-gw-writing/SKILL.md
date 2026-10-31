---
name: ren-gw-writing
description: Draft, organize or revise GW, RPA, RI/NAO and LibRPA papers and research or teaching notes using argument and section-level decisions studied in Xinguo Ren's coauthored papers. Use for outlines, introductions, theory-to-algorithm exposition, results, captions and conclusions; coordinate with ren-gw-notation for equations. Preserve the target's contribution and evidence rather than imposing an author template.
---

# Write GW and RPA articles and notes with a clear argument

Use this skill when the task concerns the structure or exposition of a GW/RPA,
RI/NAO or LibRPA article or note. Its source corpus is Ren's **coauthored papers**;
the transfer to research and teaching notes is a local adaptation. It is neither
an official group standard nor imitation of an individual's phrasing.
For research-topic work, reuse [AITP's research cycle](../../../../aitp-memory/SKILL.md)
and the target's current note; the method does not create a separate workflow.

## Find the contribution that controls the structure

Read the target and its evidence. Recover the physical question, what changes
relative to prior work, what is actually established, and the intended reader.
Reuse the topic's current main note when working inside AITP. For a passage edit,
read enough surrounding definitions and claims to preserve its role; do not
require a new paper plan.

Choose the organization by the work the reader must assess:

| Contribution | Useful argument order | Source model |
|---|---|---|
| Common RI/NAO framework | Shared physical objects → common representation → fitting error → orbital-basis error → observables | 2012 RI |
| New correction or approximation | Specific failure → explicit construction → relation to alternatives → tests of the motivating failure | 2015 SOSEX |
| Periodic or faster evaluation | Formalism → numerical obstacles and algorithm → controlled agreement/convergence → useful cost and applications | 2021 and 2026 GW |
| Software package | Scientific operations → data/interface and parallelization choices → reproducible use → performance and application | 2024 LibRPA |
| Conceptual synthesis | Shared question → alternative derivations and their conditions → computational/physical consequences → unresolved limits | 2012 RPA review |

These are dependency patterns, not required headings or section counts. Combine
or omit jobs that the target does not need. In a short note, enter at the
already-defined object and stop when the requested question is answered.

For an outline, give each proposed section its scientific job and the evidence
or derivation that fulfils it. Do not invent results to complete the outline.
In a finished article, keep task planning and missing-data requests outside the
publication prose; state scientific limitations where they affect the claim.

## Use the source at the decision that needs it

Read the relevant part of [section craft](references/section-craft.md) when
drafting an abstract, introduction, theory/algorithm passage, result discussion,
caption or ending. For a new structural choice, attribution or uncertain
analogy, consult the [source organization study](references/organization.md)
and its located original passage. Retrieve the corresponding PDF when its
exact argument matters. Do not load all six papers for a small revision.

Borrow an operation, such as separating RI error from orbital-basis error or
testing the motivating failure. Write original prose for the present question.
Do not cite Ren in the resulting article merely because the paragraph's
organization was inspired by these papers; scientific attribution follows the
actual method, result or comparison used.

## Coordinate with the notation skill

Use [ren-gw-notation](../ren-gw-notation/SKILL.md) for new or changed equations,
definitions and representation changes. This skill owns the argument and
exposition; that skill owns symbol spaces, conjugation, Fourier phases, metric
factors, spin contractions and equation-consistency checks.

For a substantial theory draft, establish the physical claim and dependency
order here, settle the affected conventions there, then write the passage and
check that the equations support its words. Reuse the settled definitions and
checks; the reciprocal links do not request repeated skill invocation. A
symbol-only correction can use the notation skill alone. A prose-only revision
with unchanged formulas does not require a new derivation audit.

Preserve the user's coherent manuscript notation. In particular, do not rename
their eigenvector $C_{in\alpha}$ merely because a source uses lowercase $c$.
For SOC, cRPA, QSGW or finite temperature, use the target's own established
theory and appropriate primary sources: the present corpus does not validate
all those extensions.

## Keep the comparison's meaning in the prose

Explain what a result controls before using it as evidence. In this domain,
several superficially similar claims have different meanings:

- Agreement between two evaluations with shared NAO/LRI approximations tests
  their evaluation strategy; independent basis/physics accuracy needs its own
  evidence. Experimental agreement may also depend on physical corrections.
- Auxiliary fitting, one-electron basis, k sampling, time/frequency grid and
  analytic continuation are distinct uncertainties. State the controls that
  justify isolating one of them.
- Formal operation count, fitted size scaling, k-point scaling and parallel
  efficiency answer different questions. Name the stage or timer boundary,
  variable, range, baseline and achieved accuracy relevant to the claim.
- A mean error does not bound every material. Preserve exceptions and separate
  an observed trend from a proposed physical or numerical explanation.

Use these distinctions where they affect the argument, not as a checklist
appended to every note. When an unsupported phrase is consequential, narrow it
to the available evidence or identify the specific missing comparison outside
the draft. Do not launch new calculations as a side effect of writing.

Return the requested text, outline or revision at the requested scale. For a
full draft, finish the abstract and conclusion after the body so their scope
matches the results. Briefly identify consequential editorial or claim changes
outside the finished prose. Follow the target's language and format instructions; produce LaTeX/PDF only
when requested.
