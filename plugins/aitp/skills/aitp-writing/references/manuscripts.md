# Working notes, TeX sources and PDF delivery

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
