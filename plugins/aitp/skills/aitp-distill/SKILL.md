---
name: aitp-distill
description: Turn a demonstrated, useful research procedure directly into a focused Skill, or revise it from new use. Use on an explicit request or a recurring method with concrete evidence; keep topic conclusions and conceptual exposition in research notes.
---

# Distill a usable research method

Extract a procedure that helps another session perform a task. Work directly
from the actual derivation, code, result, failure analysis or research note.
There is no intermediate knowledge-card format, trial ledger or hash protocol.

When distilling from a research topic, first use
[aitp-memory](../aitp-memory/SKILL.md) to recover its question and the requested
scope, reusing current context. Use `research.md` to find the relevant method,
then follow its links to the derivation, code and evidence needed to teach it.
A compressed conclusion alone may omit decisive conditions. A standalone worked
example needs no new research topic merely to support distillation.

## Decide what is reusable

Look for a non-obvious choice, a useful diagnostic ordering, a method that
avoids a demonstrated failure, or a stable way of obtaining and checking a
result. An explicit request can justify a narrow first Skill from one example;
describe that evidence honestly. Repetition alone does not make a procedure good.

A physical conclusion, a reference summary or a theorem's exposition normally
belongs in a linked note. A method for applying a theorem under particular
conditions may be a Skill. Do not turn every interesting paragraph into one.
Inspect relevant existing Skills before duplicating a capability; revise the
matching Skill when its scope really is the same.

The default learning loop is use, notice a reusable choice, write or revise one
Skill, and check it on a concrete use. General shareable methods belong under
`aitp-research/methods/<domain>/<method>/SKILL.md` when inclusion in AITP is within
the task's scope. Topic-specific or unreviewed methods can stay in
`topic/skills/<method>/SKILL.md` or the established shared family location. Follow
[method placement and discovery](../aitp-research/references/method-library.md);
there is no central registry to maintain. Record a meaningful validation limit
beside the example: preparing inputs for another system does not establish a
successful calculation. When use contradicts the method, narrow or repair its instructions
and explain the consequential correction in the relevant research note.

## Write directly for the next use

Create a folder and `SKILL.md` in the location authorized by the researcher.
Give its frontmatter a short `name` and a discriminating `description` explaining
when it is useful. In ordinary prose describe the task, required information,
decisive steps and choices, how to check the result, and when the method stops
being applicable. These are content needs, not mandatory headings.

Separate general steps from one machine's account, path, parameter value or
historical workaround. Put substantial background or a worked example in an
ordinary linked reference only when it helps. Preserve a locator to the example
that motivated the method. Do not require scripts for a procedure that the
agent can perform with existing tools.

## Check with a concrete use

Check name, description, local references and unfinished placeholders with the
host's available Skill validator. Then, when practical, apply the instructions
to a small different instance. Inspect whether they select the relevant evidence,
perform the decisive check, and respect the method's limitations. A formatting
pass is not behavioral validation; a hand walkthrough is not an independent test.
Retain only corrections supported by the observed use.

Ordinary authored examples can stay in the project without another approval
ceremony. Installation into a user's shared skill catalog, publishing, and
changing default behavior use the authorization already supplied for that task;
when absent, prepare the concrete Skill before requesting that additional action.
Do not invent human approval or install a shared Skill merely because drafting
was requested. No fixed number of trials or separate card-approval question is
part of this design.
