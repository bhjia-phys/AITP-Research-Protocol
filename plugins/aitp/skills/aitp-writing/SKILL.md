---
name: aitp-writing
description: Draft, explain, restructure or revise physics research notes and manuscripts with complete central reasoning. Use for formal theory, computational methods and benchmarks, theory with numerical tests, and pedagogical exposition; preserve the requested audience and document format.
---

# Write the scientific argument

Make the question, reasoning and supported answer intelligible to the intended
reader. This Skill develops the researcher's former `witten-style-theory-note`:
introduce objects through a concrete need, use a small example that retains the
difficulty, unfold the central argument, and place qualifications where they
matter. These are structural choices, not imitation of an author's phrasing.
It also incorporates `computational-physics-note` for implementation, calculation
settings and benchmark exposition; neither former Skill is a dependency.

## Choose the task and the reader

Use the requested artifact and existing project conventions. A conceptual
conversation needs an explanation of the disputed step, not a new manuscript.
A research note can remain exploratory or end with a useful obstruction.
A paper needs a coherent supported result, which may itself be negative or
conditional. A teaching note should distinguish reviewed material from new work.
Do not create an outline, file, or full rewrite for an ordinary follow-up answer.

For a substantive AITP main-note revision, use
[aitp-memory](../aitp-memory/SKILL.md) to understand its complete argument.
Reuse that understanding when it is current; do not restart the reading cycle.
For another manuscript, identify the intended source and read enough surrounding
argument to understand what the change affects. Preserve the requested language,
notation, audience and venue. Infer routine choices from the existing material.

Unless a compact expert account is requested, make the central reasoning
accessible to an advanced student who knows the stated prerequisites. Depth
means explaining the conceptual steps the reader would otherwise have to invent.
It does not mean expanding every arithmetic simplification.

## Organize by what establishes the answer

Privately identify the question, strongest supported answer, assumptions,
decisive mechanism, evidence and unresolved obstacle. Use this to decide the
order of explanation; do not create another required status document.

| What carries the claim? | Useful order of exposition |
| --- | --- |
| Formal construction or proof | concrete difficulty; precise objects and hypotheses; mechanism or proof; exceptional cases; physical interpretation |
| A computation or computational method | physical question and approximation; defined observable; method and controls; results with errors; interpretation and convergence limits |
| Theory tested numerically | analytic statement; finite observable that tests it; prediction or possible failure; numerical comparison; scope of the combined conclusion |
| Learning or conceptual explanation | familiar problem; first faithful example; calculation; needed abstraction; return to the original question |

These are dependency orders, not compulsory headings. A method paper may need
its algorithm before an application; a short negative result may need only one
calculation. In mixed work, organize each inference by its evidence, rather
than attaching an unrelated numerics section to a theory essay.

Read [formal theory](references/formal-theory.md) when a construction, theorem
or delicate derivation carries the result. Read
[computational and mixed work](references/computational-and-mixed.md) when
data, algorithms or finite numerical tests carry an inference, including
implementation, computational setup and benchmark tables. A mixed task may
need both; ordinary prose edits need neither in full.

## Make equations advance the explanation

Before a substantial display, explain what it will resolve. After it, explain
what became visible and why the next step is needed. Define a new object when
its purpose is apparent. An elementary example should expose the difficulty
that survives in the general case, rather than remove it by assumption.

Expand transitions involving a new identity, a sign or normalization, a
projection or inverse, a boundary term, a limit, an approximation, or an
inference from data. Show the representative contraction or calculation that
fixes the convention. Mechanical repetition can follow by a stated symmetry or
move to a linked derivation once the reason is clear. The main text must retain
the decisive implication and the hypothesis that licenses it.

Let paragraphs carry motivation, calculation and consequence. Avoid repeated
labels such as “Target”, “Checkpoint” and “Claim status” around every equation.
Do not cross a conceptual gap with “obvious” or “after some algebra”. Do not
manufacture an intermediate identity, proof or uncertainty estimate to make an
unfinished argument look complete; identify the precise missing step.

## Keep the evidence in the right document

In a research-memory note, retain useful relative links to TeX, PDFs, code,
inputs, numerical reports and figures beside the statements they support. Long
derivations and learning material can remain in their primary files. Let the
main note develop its argument through these detailed notes, with specific
assets linked where they support the reasoning. The README explains working
locations; it need not repeat the scientific account. Preserve useful failures
as explanations of why a tempting route does not work.

In a public manuscript, express limitations scientifically and cite the relevant
literature, data or code release. Local queue messages, agent activity and
research-management vocabulary normally belong in the supporting working
records. Keep scientifically relevant numerical tolerances and methods in the
paper; do not remove reproducibility information as mere administration.
Neither artifact is automatically synchronized with the other.

For imported results, use the exact hypotheses and conventions actually read.
Follow [literature guidance](../aitp-research/references/literature.md) when a
needed source is uncertain. Exposition inspired by this Skill is not a reason
to cite Witten. The retained [source analysis](references/witten-corpus-analysis.md)
and [reading census](references/witten-2011-2026-corpus.md) are optional historical
background, not material to load for every writing task.

For TeX or PDF delivery, use [manuscript handling](references/manuscripts.md).
Keep an established format; Markdown is the usual AITP main note. Templates
are optional starting files, not a demand to convert the research into LaTeX.

## Revise the argument as a whole

When a conclusion changes, check its appearance in the opening, assumptions,
dependent derivations, abstract, captions and ending. Repair the affected
passages together. A later disclaimer cannot repair an earlier unconditional
claim. Keep a substantive correction where its scientific consequence belongs.

Read the revised passage as a reader: is the purpose of each object apparent,
is the central step justified, and does the conclusion follow at the stated
generality? Check affected equations, links and figure definitions. Report
what was edited and what was actually checked. Routine editing requires no
separate research log, and polishing does not certify the underlying science.
