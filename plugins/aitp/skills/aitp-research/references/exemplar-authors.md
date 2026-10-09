# Learn research and writing habits from chosen authors

Use this when the researcher wants to learn from authors they admire, or when choosing the
next decisive calculation and the researcher keeps an index of such an author's passages.
The researcher chooses the authors; there is no global default. A choice in the current
request or workspace instructions is sufficient and persists at its stated scope. Recover
that choice and its collection through ordinary links. The examples below come from
Witten's papers; another workspace can choose different authors.

The target is the author's *decisions*: what to compute, which example keeps the
difficulty, what a result does and does not establish, how an argument is made
reproducible. A distilled style profile or an instruction to "think like" an author
carries little of this. What helps is reading the real passage whose job matches the
problem at hand, then making the analogous decision and checking it.

## Keep the author's library in the researcher's shared knowledge

An author library belongs to the researcher, in their
[shared knowledge collection](../../aitp-memory/references/shared-knowledge.md) and not
in this plugin. It combines three things: the author's source readings, an index from
moves to real passages, and a record of
[how the author organizes a paper](#study-how-the-author-organizes-a-paper). It is not a
summary of results, and the collection's index rows can point into it. The Witten
analysis retained in [aitp-writing](../../aitp-writing/SKILL.md) is that Skill's design
history: it is not an author library and does not make Witten a default. Each entry gives:
- the paper and its arXiv version;
- the section number and title, and the page;
- a short verbatim phrase that finds the passage;
- one sentence on what the passage shows;
- whether the entry was located by an AI or read by the researcher.

Check each locator against the source, because section numbering can be reset in a
manuscript and AI-written readings can misremember. The researcher's own reading replaces
an AI description.

## The moves

Each move says when it applies, what to do, and how it fails.

1. **Protection.** When an answer should not depend on details: state what cannot
   change, why, and under which deformations; compute it in the most convenient
   representative. Fails when a hypothesis (a gap, compactness, a boundary condition)
   breaks along the way. *Example:* cobordism invariance of a fermion partition
   function, arXiv:1508.04715, §2.1.7.
2. **Lost information.** When a convenient description or diagnostic cannot distinguish
   physically different cases, or gives zero: find what it conflates and choose a quantity
   that separates them. Fails when the new diagnostic assumes what it should detect.
   *Example:* a vanishing partition function replaced by an insertion that absorbs the
   zero modes, arXiv:1508.04715, §3.3.
3. **Mechanism behind an identity.** When an identity holds and seems lucky: exhibit two
   operations whose equality is the identity, with the hypotheses that make them equal.
   Fails when those hypotheses do not hold in the system at hand. *Example:* Yang–Baxter
   from the two orders of three pairwise collisions, arXiv:1611.00592, §1.
4. **Count before solving.** When conditions, parameters, powers or dimensions might
   decide the question: count, check independence, and state what the count leaves open.
   Fails when symmetry makes the counted conditions dependent. *Example:* how many
   parameters must be tuned for a level crossing, arXiv:1510.07698, §1.2.
5. **Smallest example that keeps the obstruction.** Remove what is irrelevant, keep what
   could make the inference fail; the faithful example may be infinite. Fails when the
   simplification deletes the difficulty. *Example:* infinitely many qubits keep
   inequivalent representations, arXiv:2112.11614, §2.2.
6. **What constraints force and what they leave free.** Say which part of the answer the
   constraints fix and which needs a calculation; choices of representation need reasons,
   not proofs. Fails when one route is presented as the only possible one. *Example:*
   gauge invariance forces an integer Chern–Simons level without choosing it,
   arXiv:1510.07698, §2.2.
7. **Tests not used to build the proposal.** When a proposal was fitted to something:
   check a consequence the fit did not fix. Fails when the "test" reuses what was fitted.
   *Example:* other topologies test a matrix model whose disk density was fitted,
   arXiv:2006.13414, §9.
8. **Where the conclusion stops.** State exactly what a derivation proves, then find the
   example or missing hypothesis that blocks the stronger claim. Fails when the caveat is
   added at the end instead of where the inference is made. *Example:* focusing gives
   "a focal point, or possibly a singularity", and a bent slice of Minkowski space has
   focal points without one, arXiv:1901.03928, §4.3.
9. **A reproducible decisive operation** (exposition). Give a new operation a visible
   job, practise it on a small case, then perform it on the real variables. Fails when the
   reader can name the operation but not carry it out. *Example:* a Berry connection
   computed first for a mechanical system, then for the electromagnetic field,
   arXiv:1510.07698, §2.5.

## Use a move

1. Name the difficulty and find the matching move.
2. Read the indexed passage in the original.
3. Name the decision made there.
4. Make the analogous decision for the present problem.
5. Check the result by calculation, a source or an independent reader.

A move suggests what to try; it is not evidence for the answer. Skip it when its failure
condition applies. For a consequential choice, make the transfer explicit in the owning
working note when it explains the decision: the obstruction in the present problem,
what the passage suggests doing, which hypotheses survive the transfer, and what check
could reject it. Do not paste a move label into every note or infer the author's insight
from fluent prose. If the original is unavailable, disclose that the adaptation uses a
secondary reading; do not claim to have inspected the paper.

For writing, retrieve a paragraph that does the same job: motivating, defining,
computing, interpreting a display, qualifying, or handing over to the next question.
Reuse its choices, not its phrases. Keep every claim exactly as strong as its evidence.
Isolating a premise must not imply it is the only one, and a closing verdict must be no
stronger than what was shown.

## Study how the author organizes a paper

Moves are decisions inside an argument. Organization is how the author arranges a paper
around them, and it is learned from the papers with a skeleton reading:
1. Read the title, the first and last paragraphs of the introduction, and all section
   titles.
2. Read the first and last two sentences of each section.
3. Write the paper's chain of questions.
4. Name the job each section does.

Jobs seen in practice include:
- posing the question;
- taking up the difficulty the previous section left;
- practising on a smaller system that keeps the obstruction, then returning;
- introducing a new object because the current description lacks something;
- a statement, its proof and its consequences;
- a second look that shows what the first route hid;
- showing where a result stops, often by a counterexample;
- handing over to the next question.

*Example:* a section poses a representation problem, practises it on infinitely many
qubits and then on oscillators, and returns to the field theory, arXiv:2112.11614,
§§2.1–2.4.

Record, with checked passages:
- how the author states and teaches prerequisites;
- how derivations are shown: the goal before the calculation, the argument chosen, which
  case is worked in full;
- where details go: footnotes, statements made for later use, appendices;
- how discussion and the strength of claims are handled;
- where the author compresses, that is, the steps a reader must supply.

Keep this record in the author collection beside the moves. An author has no fixed
template: record the jobs and choices, not a prescribed order of sections. Use the record
when reading, to map a source, and when writing, to find a passage that does the job at
hand.

## Improve and test

Retain a consequential use beside the research it served: the passage, decision and
what its check established. An editorial adaptation needs no separate use log. Success
means a better justified calculation, diagnostic or explanation, not resemblance of tone;
a new scientific insight still needs its own evidence. When a use demonstrates an error in a move, correct it at once
with [aitp-distill](../../aitp-distill/SKILL.md). Examples of such an error are a wrong
failure condition or a passage that does not show what is claimed. One surprising case
justifies narrowing the move or recording a caveat; broadening or redesigning a move
needs repeated evidence.

To test whether a library helps, compare blind, on problems not used to build it:
- a plain prompt;
- "think like the author";
- the moves alone;
- the moves with retrieved passages.

Use tasks of three kinds: reconstruct an omitted step, transfer to a changed setting, and
reject a plausible but invalid identification. Score the physics separately from the
readability. For the researcher, the test of learning is solving a changed problem without
the text.
