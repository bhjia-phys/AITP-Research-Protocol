# An article-shaped main note that carries the research

Use this when creating or substantively revising `research.md` or the established
main note. Its reader should recover the question, the reason for the present
answer, and the live uncertainty without opening every supporting file. Follow
the user's language and format. The starting files below make this structure
concrete; they are adaptable drafts, not forms to fill mechanically.

The note also directs continuation: explain why the current main line is worth
following, how its branches contribute, and which next inference could change
the answer. Keep these reasons in the scientific prose, not a second action
plan or mandatory status table. A branch can remain useful without remaining a
prerequisite, and a completed question needs no invented next task.

## Choose a starting point for the whole question

| Kind of argument | Markdown starting file |
| --- | --- |
| One compact construction, comparison or obstruction | [Compact argument](../assets/research-letter.md) |
| Formal theory or conceptual learning | [Theory](../assets/research-theory.md) |
| Computation, method development or theory tested numerically | [Computational and mixed](../assets/research-computational.md) |

These share an article's spine: **title; abstract; introduction; the setting and
central argument; discussion; references**. The full versions give the setup,
construction or methods enough room to make the result intelligible. The compact
version merges that work into fewer sections. An optional open-questions ending
preserves the scientific continuation. See the [journal sources and design
choices](journal-templates.md) if the rationale or original TeX templates are
needed; ordinary drafting needs only the appropriate starting file.

For ordinary Markdown, use `$...$` for inline mathematics, including table cells,
and `$$...$$` for displays, unless the project's renderer specifies otherwise.
Keep figures near their interpretation with a caption and evidence link. A TeX
equation environment or cross-reference command needs a suitable renderer; do
not assume that copying it into Markdown reproduces a typeset article.
Use [citation conventions](citations.md) when numbering or referring to formulas,
figures and external notes; use [supporting-note writing](supporting-notes.md)
when a linked explanation needs its own development.

Scope the main note to the agreed research question, not the latest session's
task. A component test in a larger physical investigation normally belongs in
a linked method note. Promote its implication into the main argument if it
changes that investigation. Conversely, a deliberately scoped methodological
question can have a main note of its own. Do not silently shrink a broad project
to the one calculation that currently has a result.

## Focus the argument without making the research look finished

Use informative section titles and connected scientific prose. The abstract
states the question, approach, strongest supported answer and decisive condition.
The introduction explains the difficulty, relevant background and why the question
matters. The body establishes the answer, and the discussion interprets it. A
reader should learn physics or a method from this structure, not just recover a
status report. Compress repetition and routine detail rather than the logical
steps needed to understand the claim; there is no imposed journal length limit.

Open with what is being investigated and the strongest answer currently supported.
For a new topic, that may be a useful question and proposed route. Introduce the
setting and assumptions when they become necessary, develop the decisive argument,
and explain what remains unresolved. A failed approach or conditional result can
be the present answer. An early abstract can honestly summarize a question and
partial understanding. Rename a results section to describe a proposed approach,
or omit it, when there are no results. Delete empty headings and template prompts.
Do not manufacture a successful ending, measurements, proof or novelty.

Make the opening explain how imported inputs and work developed here support the
answer, and which connecting inference remains unestablished. Their provenance
and logical status are separate: a project derivation can remain conditional,
and a rederivation need not be a publication novelty. A section itinerary or a
list of completed checks does not express those relationships.

A main note whose opening is a source inventory, followed by test coverage,
execution status and a task list, is still an operational report even if short.
Put those details in a linked working note. Explain instead what the model or
method does, why the calculation is discriminating, and what follows from it.
Keep the consequential evidence boundary in the scientific account: for example,
an analytic benchmark does not demonstrate that an implementation passes it.

Retain research information that a publication might omit: why a plausible route
failed, an objection that still matters, a conjecture's actual evidence, or the
next discriminating calculation. Put it where it affects the reasoning. A short
ending on open directions is useful when these do not fit earlier; do not append
a chronological session diary. A completed question needs no invented open problem.

## Decide what stays in the main note

Judge the main note by whether its intended reader can explain the overall
question, the decisive reasoning, the supported answer and the remaining gap.
It need not prove every supporting theorem, but it must explain what an imported
result says, why it applies here and what follows from it. A definition list or
a link cannot carry the missing central inference. Keep assumptions next to the
conclusions that need them, including in the abstract and discussion.

For a learning topic, the main note may begin with a small synthesis of the
question and partial understanding. Follow [learning from sources](learning.md)
for the current reading passage and its depth. Let supporting explanations grow
around specific difficulties, then integrate the connections they establish.
Do not make the main note look comprehensive by stating advanced connections
whose explanations are still missing. Preserve the whole topic's open scope
without pretending all its branches have already been learned or derived.

| Keep in the main argument | Link to supporting material when substantial |
| --- | --- |
| Definitions and conventions needed for the central claim | Extended background, literature reading and shared concept explanations |
| Decisive proof step, equation or physical mechanism | Full algebra, subsidiary lemmas and alternative derivations |
| Observable, approximation, decisive comparison and its uncertainty | Input decks, code, complete scans, run reports and analysis scripts |
| Result and conditions of a useful failed route | The sequence of attempts and detailed failure diagnosis |
| A consequential conjecture, what supports it, and what is missing | Exploratory calculations and candidate constructions |

This separation is about relevance to the argument. If a technical detail is the
reason the result holds, keep enough of it in the main text. If removing a passage
would make a future reader repeat a known mistake, retain its implication and a
source link. Link captions or nearby analysis to the data and script behind a
figure; show a figure in the main note when it carries the central comparison.
The README continues to explain locations, not duplicate the scientific account.

Keep useful side investigations visible through their relationship to the main
question, even before they produce results. For an agreed independent branch,
link its `research.md` beside the question it serves and say whether it is a
prerequisite, an alternative or an independent spin-off, and what result would
matter to the main argument. Its main note links back. The nearest README maps
the branch folder; detailed derivations stay with their own question. Use
[side-investigation guidance](supporting-notes.md#follow-a-side-investigation)
without forcing every short diagnostic into a new research question.
Keep one primary account of each branch's detailed argument. The parent retains
its implication and limiting condition, and the child explains its purpose and
dependencies. Directory nesting describes a working home, not every scientific
relationship; a branch may depend on a sibling topic through an ordinary link.

For formal work, keep the hypotheses and central construction or obstruction
visible; distinguish a proved statement from a candidate physical interpretation.
For numerical work, keep the setting, observable, controls and supported accuracy
visible; a successful run is not a convergence result. In mixed work, state which
analytic assertion the finite test probes and what it cannot establish.

## Write failure, uncertainty and evidence precisely

A useful failure explains which route was tried, why it was plausible, and what
specifically obstructed it under the stated conditions. Keep the explanation as
short as the logic allows; do not generalize failure of one ansatz into a no-go
theorem. If later work repairs the route, revise its status and preserve the
earlier limitation where it still teaches something.

Introduce an unproved statement as a conjecture or working hypothesis where it
appears. Give its motivation or evidence and identify the missing proof, control
or counterexample check. A guess without supporting evidence can be recorded as
an idea to investigate, without promotion through polished prose. Literature
claims, derivations and numerical observations should remain distinguishable in
ordinary sentences rather than a mandatory metadata scheme.

For example, agreement between two numerical implementations can support a
regression claim while leaving basis or finite-size convergence unresolved.
Keep that distinction in the main text; move the full comparison table and
commands to supporting evidence. A shorter rewrite must not turn agreement into
a claim of physical convergence.

## Add, move and remove material without losing the thread

Before editing, use the complete current argument recovered by `aitp-memory`.
Decide whether new material changes that argument or only adds supporting detail.
When moving useful detail out, first give it a suitable home beside related work,
then leave its result, decisive conditions and a descriptive relative link in the
main note. Reuse an existing source instead of copying the same explanation.

Place links beside the statements they support, with enough explanation to know
why they matter. Preserve exact source locators for useful derivations, papers,
figures and reports. A detached "see files" list cannot replace these connections.
If a moved section or changed heading has incoming links, repair those affected
links too. Removing prose is not authorization to delete its original assets.

Update the opening, dependent claims, discussion and ending together when an
answer changes. Remove a solved next step from the live account and keep the next
one tied to the current uncertainty; it need not reproduce this session's task
list. Read the shortened note on its own: can the researcher explain what follows,
why it follows, under what conditions, and where to inspect the evidence? Then
check affected links and make sure no useful branch vanished during compression.

## Adapt an existing note during use

For memory's [on-use repair](../../aitp-memory/SKILL.md#repair-an-outdated-main-note-during-use),
identify what a reader cannot reconstruct from the current account. Different
headings, an old date or a newer Skill are not by themselves a defect. Retain the
established language, scope, format and asset locations. Start from the complete
argument and its evidence, not an empty template.

Make the smallest coherent revision that restores the question, supported answer,
decisive conditions, relationships and continuation. A larger rewrite is appropriate
when local patches would leave contradictory claims or an update queue. Reconcile
the opening and ending with the actual current evidence. Keep why an earlier route
changed and what remains usable; do not replace the only complete derivation with
a summary. If substantial detail needs another home, preserve it there and repair
its links before shortening the main text. Original outputs and historical editions
remain evidence of their original setting.

When a completed stage replaces an active plan, inspect its nearby heading,
future-tense instructions, status table and later next-step passages together.
Time-scope useful execution rules as historical conditions and replace completed
prerequisites with the actual remaining inference. A new heading alone does not
repair an old instruction to run the finished stage. If a linked artifact is
unavailable only in a reduced copy or the current access scope, keep the durable
note's original link and explain the verification limit in the reply; change the
note only after establishing that the authoritative asset or claim has changed.
Check the linked supporting notes whose live conclusion or next-step wording
depends on this changed stage. Correct those maintained passages without turning
a dated report into a current-status page or recursively auditing every file.
If the repair renames a heading, preserve its old fragment as an explicit anchor
beside the new heading unless a topic-wide Markdown search confirms that every
incoming link, including links in archived run records, has been updated. A
search limited to the main note or the first-level README cannot establish this.

State missing reasoning as missing, and old job states as dated observations.
Reorganization cannot create a proof, a new execution, learner understanding or
physical validation. Correct only affected maintained uses within the task's scope;
separate manuscripts and lectures keep their existing update boundaries.

Read the revised argument on its own and follow affected links. If it now carries
the needed meaning, stop: a repeated request with unchanged evidence should not
produce another rewrite, parallel summary or compliance record. Explain the useful
repair alongside the requested result and link the note without adding a new log.
