# Learn from a source and develop the explanation

Use this for conceptual learning, a lecture companion, or a teaching derivation.
Use the existing main-note context when this belongs to a persistent topic.
An ordinary explanation needs no new files. Teaching prose, research synthesis
and publication prose have different jobs even when they share a PDF format.

## Set a useful learning target

Use the reader's stated prerequisites, question and intended outcome. For
interactive calibration and conceptual feedback, use
[aitp-human-learning](../../aitp-human-learning/SKILL.md); do not add a separate
intake or assessment here. A field-standard method may still be new to a graduate
student. This guide concerns the explanation's content and structure.

Choose the needed depth for the passage; different parts can have different jobs:

| Intended use | What the explanation must supply |
| --- | --- |
| Understand | Meaning, conditions, mechanism and the role of each imported result. |
| Reproduce | Stated inputs and justified steps sufficient to repeat the calculation; explicitly stated technical theorems may remain external. |
| Prove | Proofs of indispensable results beyond the agreed prerequisites, to the strength used. |

For a requested detailed derivation, normally make the central calculation
reproducible. Do not infer a demand to prove every background theorem from
"self-contained". For an imported theorem, explain its objects, hypotheses,
conclusion, relevant normalization and exact use; a citation alone does not do
this. A missing proof remains an external dependency, not a proof supplied here.
Keep formal manipulations and physical assumptions identifiable at their use.

## Keep a primary reading thread

When learning an existing lecture or paper, retain its argument as the current
thread and identify the relevant version, section and equation. If the shared
collection has a reading of the source, start from it, and improve it when the session
establishes something new; see
[source readings](../../aitp-memory/references/shared-knowledge.md#keep-source-readings-usable). Explain the
problem that motivates the passage before expanding its steps. Preserve the
source and write complementary explanations at useful logical boundaries;
wholesale rewriting or a multi-source survey is not the default.

Bring in another source to resolve a specific missing prerequisite, supply a
different example, check a disputed step or extend beyond the primary source's
scope. Translate conventions before combining formulas. Distinguish what the
source states, what the note reconstructs and what remains unresolved. Return
to the original passage after the gap is addressed. Broad synthesis is useful
when it is the requested task or the relevant connections have been developed.

The topic's main note can initially give a short account of the overall question,
the connections established so far and the remaining obstacles. Put sustained
reading and calculations in supporting notes and integrate their implications
when they change that account. A concise main note does not constrain the length
of a teaching derivation.

## Read a source closely

To study a source in depth, read it in two passes.

**First, a skeleton reading.** Read the introduction's opening and ending, all section
titles, and the first and last sentences of each section. Write the source's chain of
questions and the job of each section. This map sets the reading order, which can follow
dependencies rather than the source's own order. For example, a finite-dimensional
section can be read before the general section it motivates.

When the first section note of a source is written and the source has no map yet, create
one. A stub is enough: the version, the section list, and a link to the note. Complete the
skeleton as the reading extends.

**Then read section by section.** The unit is a step of the argument, whether a displayed
equation or a sentence; gaps often sit in prose such as "in exactly the same way". Read
every sentence, footnote and equation, and record that coverage. Write out only what the
reader cannot supply:

- **Hard steps.** Supply the complete missing inference. When practice serves the
  learner's request, offer a short optional try-first prompt before its explanation;
  direct exposition and a requested complete note need no exercise gate. Label each added
  line as quoted from the source, imported (with the theorem and its locator), or
  reconstructed (with how it was checked). Filled steps are where a written explanation
  most often errs.

  A displayed calculation can inherit the attribution of its introducing block. Split a
  block where its support changes; do not repeat a label on every mechanical line or
  purely editorial heading. Give a substantial missing inference a stable heading for
  direct links; keep routine substitutions in the explanation. A question page should reach the needed atom, exact
  source step and return to the question without requiring the reader to navigate an
  entire bibliography.
- **Two layers.** Gaps that block following the argument come first. Rigor gaps, such as
  domains, unbounded operators and truncations, can sit in an optional layer.
- **Details worth remembering.** Record each briefly, with what it does and where it leads:
  a footnote that reveals a choice, a general statement made for later use, an analogy, a
  surprise, or an alternative route. Such a detail often explains a hard step.
- **Compressions and claimed errors.** Mark the steps the source compresses. Distinguish a
  wrong source formula from an error in the note, and distinguish both from a premise that
  the source assumes without proving. Keep a source-error claim separate until an
  independent derivation, limiting case or counterexample checks it; record the edition
  and exact passage beside that step. Explain which downstream uses change and which
  remain conditional. A counterexample to a general lemma does not automatically refute
  the special physical family that motivated it. Keep unresolved research consequences
  provisional under the shared-knowledge rules.

**Let the reader steer.** The reader reads the section and marks where they got stuck, and
those steps come first. For a load-bearing derivation, the reader's own rederivation is
the best note; the written filled step is its answer key.

A learning topic's main line can then be told as a chain of questions that links into
these readings; see [stories](../../aitp-memory/references/shared-knowledge.md#tell-a-learning-topic-as-a-story-of-questions).

## Develop one result far enough to use it

Choose a meaningful result, not a fixed page count or one isolated display.
Introduce its physical question, work a small example that retains the actual
difficulty, and introduce abstraction when it becomes useful. Continue through
the decisive calculation, a relevant check and the interpretation. These are
expository needs, not mandatory headings or nine repeated boxes.

For each substantive step ask: can the reader perform it from a previously
explained operation and the allowed prerequisites? Expand a new idea, theorem,
boundary condition or convention-sensitive transformation where needed. Several
mechanical operations may share a display. A name or dictionary definition of
an object is not necessarily enough to use it in a calculation.

An example of an obstruction must exhibit the obstruction. A zero or trivial
case may check notation but cannot replace a case with nonzero curvature,
noncommuting operators or the boundary term being studied. Give a representative
worked calculation before assigning a related exercise; an exercise must not
carry the missing central argument. Link longer prerequisites with an explicit
reading order when necessary, and keep enough local explanation to follow the
present step. Apply [supporting-note guidance](supporting-notes.md) to the whole
explanation, including its captions and exercises.

Tie a check to the formula and inference actually written. Reusing the same mistaken
expression on both sides does not test it. Where useful, compare with an independent
identity or a case that distinguishes the proposed answer from a plausible wrong one:
noncommuting densities, a nonzero boundary term, a complex phase, or a normalization
fixed by a second method. State the reach of a finite calculation. It may refute a
universal assertion, but a successful finite test does not prove an infinite-dimensional
closure, domain, limit or gravitational-identification theorem.

## Use feedback and review to improve the next passage

Use [aitp-human-learning](../../aitp-human-learning/SKILL.md) for dialogue and
interpretation of learner feedback. Deliver the agreed artifact and distinguish
an authored explanation from understanding demonstrated by the learner.

Read the passage in order using the declared prerequisites. Try to reconstruct
its target calculation and identify the earliest missing definition, premise,
operation or physical interpretation. Check that a change of assumptions does
what the prose claims. Correct a local gap and its affected uses; do not expand
every linked prerequisite into a textbook. Distinguish a derivation error from
a valid argument that still needs better teaching. Source checks, a reviewer
exercise and the learner's feedback provide different evidence. Report their
actual scope without a mandatory audit manifest or a claim of proven pedagogy.
