# Working notes, TeX sources and PDF delivery

Read this for a user-requested paper draft, manuscript revision, or TeX/PDF
deliverable. Ordinary research-note maintenance does not activate this workflow.

Identify the intended source and output before editing an existing manuscript.
Inspect the bibliography, included chapters, figures and build instructions
needed by the change. Resolve competing drafts using the user's selection,
project links and source content; a filename or newer timestamp alone does
not establish which argument is current. Ask only if that choice remains
materially ambiguous.

Preserve annotations, reviewer comments, user edits and unrelated source changes.
Do not silently replace a marked draft with a clean regenerated document.
Keep the main source, chapter files, bibliography and necessary figure assets
together. Correct cross-references after moving material.

A living `research.md` can link an extensive TeX derivation or teaching PDF
without duplicating its text. The note carries the current conclusion and any
consequential correction to the older presentation. If the task also revises
the manuscript, update its dependent claims and captions coherently. Otherwise
leave the historical artifact intact and identify the relevant correction in
the working note. A source edit does not update its compiled PDF automatically.

## Choosing and producing a manuscript

Choose purpose and reading assumptions before venue typography. A teaching PDF
in JHEP or another journal layout retains its learning target, worked examples
and agreed derivation depth. Use [learning guidance](learning.md); do not compress
it into an expert article merely because the output is LaTeX. Establish whether
it is a companion read beside the original lecture or a standalone account.
In a companion, give precise source locations and explain the intervening steps.
For standalone reading, supply the necessary explanations or an explicit reading
order through included appendices, not unexplained workstation-only links.
Keep prerequisites available before the reasoning that requires them.

When writing a paper from `research.md`, read the whole current argument and the
specific sources needed for the claims selected for publication. Establish the
paper's intended result and audience from the request; ask about consequential
ambiguity before choosing a different scope. Select a coherent supported claim
and organize its exposition, rather than converting every note section literally.
Keep scientifically relevant negative results, assumptions and limitations. Leave
operational run history and speculative future routes in the research memory
unless they serve the paper's argument. A conjecture included in a paper remains
a conjecture. Do not fill a missing proof or result to complete the manuscript.

Translate Markdown source links into the appropriate scientific references,
equation/section references, figures or supplementary material. Inspect linked
derivations before using their results, and preserve attribution and reproducibility
details. Keep the LaTeX source and bibliography in the established manuscript
location. Include needed figures or use stable project-relative paths; a paper
must not depend on unexplained workstation-specific links.

For a later request to update the paper from the note, compare the new scientific
understanding with the existing manuscript and revise all dependent claims while
preserving the author's edits. Record the source note/version or relevant date
briefly in an existing manuscript README or source comment when needed to avoid
confusing drafts. Neither document overwrites or synchronizes the other by default.

Respect an existing venue or format. For a new theory manuscript, the optional
[JHEP starter](../assets/jheppub-note-template.tex) preserves the former Skill's
familiar format; copy [jheppub.sty](../assets/jheppub.sty) and
[JHEP.bst](../assets/JHEP.bst) beside it if needed, preserving their headers.
The starter is a scaffold with neutral placeholders, not a completed paper.
For a computational article, use the requested venue or existing source rather
than forcing a theory template. A Markdown request stays Markdown.

Choose sections for the actual argument. Do not automatically insert a theorem,
an IMRAD structure, a notation inventory or a long overview. Do not invent
author information, affiliations, email addresses or publication identifiers.
Use inspected primary sources for technical attributions and verify new
bibliographic metadata before treating it as complete.

When PDF output is requested, use the project's build command and engine.
Compile in a way that preserves prior deliverables; rerun bibliography and
reference passes until they stabilize. Check unresolved citations/references,
missing figures and meaningful layout warnings. Inspect rendered pages affected
by the edit, including dense equations, captions and tables; inspect more broadly
when the layout changes globally. A clean log is not visual inspection.

Deliver the actual source/PDF paths and state what was compiled or inspected.
If an unavailable dependency prevents a build, report that limit precisely
without presenting an older PDF as the newly edited result. Do not compile
every linked manuscript merely because a research-memory paragraph changed.
