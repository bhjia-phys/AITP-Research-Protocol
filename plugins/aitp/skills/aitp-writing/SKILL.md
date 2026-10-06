---
name: aitp-writing
description: Write and revise physics research notes, expand lecture derivations for a learner, and develop clear arguments with linked evidence. First use aitp-memory for research.md. Produce or revise a LaTeX manuscript only when requested.
---

# Write the scientific argument

Make the question, reasoning and supported answer intelligible to the intended
reader. Introduce objects through a concrete need, use a small example that retains
the difficulty, unfold the central argument, and place qualifications where they
matter. These are structural choices, not imitation of an author's phrasing; this
Skill developed them from the former `witten-style-theory-note`. When the researcher
has chosen authors to learn from, use [exemplar authors](../aitp-research/references/exemplar-authors.md)
to read a passage that does the same job as the one being written.
It also incorporates `computational-physics-note` for implementation, calculation
settings and benchmark exposition; neither former Skill is a dependency.

## Choose the task and the reader

Choose the purpose before the format: a research synthesis, a learning explanation,
or a paper for a specialist audience. During research, write or revise the working
note and its supporting explanations. Use
[aitp-human-learning](../aitp-human-learning/SKILL.md) when learning needs interaction
or adaptation to a conceptual difficulty; [learning from sources](references/learning.md)
guides the explanation itself. Reuse the stated audience and deliver a requested
complete artifact without a compulsory interview. For user-requested TeX/PDF or paper
work, also use [manuscript handling](references/manuscripts.md). A JHEP layout does
not change a teaching document into an expert paper. A meaningful note update or
completed result does not itself request manuscript production; keep that guide
unloaded during ordinary note work.

Use the requested artifact and existing project conventions. A conceptual
conversation needs an explanation of the disputed step, not a new manuscript.
A research note can remain exploratory or end with a useful obstruction.
A paper needs a coherent supported result, which may itself be negative or
conditional. A teaching note should distinguish reviewed material from new work.
An ordinary follow-up needs no new outline or full rewrite when the existing
account is usable. If use exposes a material gap, follow memory's
[on-use repair](../aitp-memory/SKILL.md#repair-an-outdated-main-note-during-use)
within the current editing scope; no separate rewrite request is needed.
Use [adapting an existing note](references/research-note.md#adapt-an-existing-note-during-use)
for that revision, including when the scientific results themselves are unchanged.

For a first AITP main note or a substantive revision, first use
[aitp-memory](../aitp-memory/SKILL.md) to locate the note, clarify the current
task and understand its complete argument. Reuse that understanding when current;
do not restart the reading cycle. Apply [main-note writing](references/research-note.md).
For a new note, optional Markdown starting files are [compact argument](assets/research-letter.md),
[formal theory or learning](assets/research-theory.md), or
[computational and mixed work](assets/research-computational.md). Write an article's
question, abstract, reasoning and discussion, preserving useful failures,
uncertainty and links to detailed evidence. Adapt the headings to the whole
question and remove unused prompts; do not turn the note into a source inventory
or test-status report. Memory and writing act on the same
document; do not make a second narrative for the session.
For another manuscript, identify the intended source and read enough surrounding
argument to understand what the change affects. Preserve the requested language,
notation, audience and venue. Infer routine choices from the existing material.

The main note must let its reader explain the question, supported answer, decisive
reasoning and remaining gap, and choose a next inference that serves the question.
Explain which branch supplies which part of that argument; a list of links alone
does not do this. A supporting note must let its reader follow and use
one result from stated prerequisites. Put substantial detail there while retaining
the central implication in the main note. For teaching, distinguish understanding
an argument, reproducing a calculation and proving its imported theorems; choose
depth for the actual task. A graduate-level label alone does not establish what
the reader knows. Depth means explaining conceptual steps, not every arithmetic
simplification.

For a detailed concept, source reading, proof, method, experiment or exploratory
route within one question, use [supporting-note writing](references/supporting-notes.md).
An agreed independent research branch has its own folder and `research.md`;
the same guide explains how to connect it to the originating question. For equation
numbers and links across files, use [citation conventions](references/citations.md).
Before creating a shared atom (a concept, theorem, technique, example or result
explanation), use [shared knowledge](../aitp-memory/references/shared-knowledge.md)
to find and compare existing explanations. When a note introduces a central concept that has a
shared entry, link it and reuse or explicitly adapt its conventions rather than
re-deriving it silently. Reuse a current search result; a prose clarification
does not require another search. Writing an answer does not itself require a
durable knowledge page. Load these guides when that task arises, not for every
prose edit.

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

Let paragraphs carry motivation, calculation and consequence. Say what kind of
argument is coming when it matters (preliminary, schematic, an oversimplified route).
Give the premise an inference rests on its own sentence without implying it is the only
one, and locate a failure in one sentence where it occurs. State an outcome plainly and
no more strongly than what was shown. Say separately whether a result is right and
whether the argument given proves it. Avoid repeated
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
background, not material to load for every writing task. They record where this
Skill's structural guidance came from; they are not an author library and do not make
Witten a default. Authors the researcher chooses to learn from have their libraries in
the researcher's shared collection, as described in
[exemplar authors](../aitp-research/references/exemplar-authors.md).

For requested TeX or PDF delivery, use [manuscript handling](references/manuscripts.md).
Keep an established format; Markdown is the usual AITP main note. Templates
are optional starting files, not a demand to convert the research into LaTeX.

## Revise the argument as a whole

When a conclusion changes, check its appearance in the opening, assumptions,
dependent derivations, abstract, captions and ending. Repair the affected
passages together. A later disclaimer cannot repair an earlier unconditional
claim. Keep a substantive correction where its scientific consequence belongs.
For changed dependencies or a supporting note removed from the main argument,
use [corrections and retained notes](references/supporting-notes.md#correct-claims-and-keep-earlier-routes-findable).

Read the revised passage as a reader: is the purpose of each object apparent,
is the central step justified, and does the conclusion follow at the stated
generality? For a learning passage, try its target calculation using only the
stated prerequisites and earlier explanations; identify the first unsupported
step instead of supplying it silently from expert knowledge. Such a review can
expose gaps but cannot establish that the learner has understood. Check affected
equations, links and figure definitions. Report
what was edited and what was actually checked. Routine editing requires no
separate research log, and polishing does not certify the underlying science.
