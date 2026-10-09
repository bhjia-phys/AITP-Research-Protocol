---
name: aitp-verify
description: Check research claims, results, numbers, references and documents, or assess another model's review. Use before a new, changed or disputed consequential claim enters a decision, a main note's opening or a manuscript, or when asked to check, review or audit. Reuse applicable checks for unchanged claims; routine wording edits do not require scientific revalidation.
---

# Check work before it is relied on

A claim is relied on once it enters a decision, a main note's opening, a hand-off or a
manuscript. Before relying on a new, changed or disputed consequential claim, check the
evidence relevant to that use. Ask which plausible error could survive the way the
result was produced, and choose the check that would expose it. Reuse documented checks
while their assumptions, inputs and implementation still apply. A full document audit
checks all reported quantities and citations; a local change checks the affected claims
and their dependencies. Unchecked observations may be kept, marked provisional; they
must not gain authority by being repeated.

Identify the audit actually requested. An editorial or navigation revision checks
preservation, logical qualifications and evidence routes; it does not freshly certify
every scientific result in the archive. Reuse the retained checks, identifying them as
such, and investigate a specific conflict before rewriting its conclusion. A scientific
validation request requires the corresponding derivations, source inspections or numerical
checks. Report these scopes separately.

Checking is separate from producing: use a different route from the one that made the
result. When an audit needs a new derivation, calculation or debugging, do that work
through [aitp-research](../aitp-research/SKILL.md) and return its evidence here. This
skill runs inside [memory's research cycle](../aitp-memory/SKILL.md#the-research-cycle);
opened directly, apply the cycle and reuse context already recovered.

## Read when

| When the task involves | Read |
| --- | --- |
| A derivation or formula | The checks below, and the field's [domain methods](../aitp-research/SKILL.md#domain-methods) for its conventions |
| Numbers in a note, table, figure or paper | Their raw outputs and run reports, located through [memory](../aitp-memory/SKILL.md) |
| A numerical result, a benchmark or a code change | [Computational work](../aitp-research/references/computational-work.md) |
| References and attributions | [Literature](../aitp-research/references/literature.md) |
| A research note being reviewed or prepared for sharing | The checks relevant to its claims below; sharing alone does not request a manuscript or PDF |
| A requested paper draft, manuscript revision or TeX/PDF deliverable | [Manuscript handling](../aitp-writing/references/manuscripts.md) |

## Check a derivation

Distinguish an independent derivation from consistency checks. Re-derive a decisive step
by a route that does not copy the original, such as another gauge, basis or order of
operations, or a numerical evaluation. Dimensions and units, symmetries, limiting and
special cases, sum rules and small explicit examples test specific failure modes; they do
not prove the general claim. Record which steps were re-derived, which were only checked
for consistency, which results were imported from a source, and what remains unchecked.
A check that cannot fail does not count.

## Trace the numbers

Follow each reported number in scope to the file that produced it, and recompute any derived
difference, ratio or percentage. Confirm that units, normalization and conditions
match the text. Mark each number as traced, mismatched (with both values and both
locations) or untraceable. Correct a number only from its source; otherwise flag it.

## Verify references and attributions

Check each reference's authors, title, journal, volume, pages, year and DOI against the
publisher's or Crossref's record, and check that the cited passage supports the claim
attributed to it. A real paper cited for a claim it does not make is an error.

## Test claims against their evidence

Compare each claim's strength with what was shown. Agreement between codes that share an
approximation is not validation of that approximation, a finite-size trend is not a
limit, a theorem under stated hypotheses does not establish that those hypotheses describe
the physical system, and a passed test is not physical validity. Qualify a claim where it
reaches further than its evidence.

## Report

List what was checked, what failed with exact locations, what could not be checked and
why, and what must change before the result is relied on. For changed research notes,
check both directions: the main claim reaches evidence that actually supports it, and a
changed supporting conclusion is reflected in its maintained parent and other known uses.
A passing link checker establishes neither of these semantic relationships. For an assessment request,
return the findings without revising the artifact. When revision is in scope, fix an
error at its source and correct the passages that depend on it, following memory's write
rules: a qualification or correction beside the claim, substantial check evidence in the
derivation or report that owns it. A clean report is short, but the checks must have been
done.

## Commission a second read

For a consequential result or a manuscript, a second read by another model or a fresh
session adds evidence when the researcher's authorization and the host allow it; it is not
a required step for every task. Write a reviewer prompt that stands on its own:

- the reviewer's role and field, the document's intended reader, the files to read with
  their versions, and the question the document must answer;
- what to look for: scientific errors, logical gaps, unsupported claims, and for a
  teaching note, steps a reader at the stated level could not follow;
- that every finding needs a location (section, equation or page), a reason and a
  severity: blocking, important or minor;
- what to avoid: generic praise, rewriting the document, and style preferences
  presented as errors.

Give the reader only the document and its sources, and keep your own expectations out of
the prompt. Record honestly how independent the read was: which model read it, whether it
could see other files, and whether it shared the author's model. A re-read inside the same
session is not an independent read. For a second round, supply the earlier findings and
the response, and ask the reviewer to re-derive the core formulas and check each claimed fix.

## Assess another model's review

Check every finding against the document and its sources before accepting it. Mark each
as valid, partly valid, invalid, out of scope, or unresolved pending specified evidence,
with the evidence for that decision; for an unresolved finding, name what cannot yet be
relied on.
A reviewer can be confident and wrong; agreement between models is not verification.
Watch for over-design as well: a suggestion whose cost or added complexity exceeds what it
fixes can be declined with a reason.

For an assessment request, such as whether a review is sound or over-designed, return
the triage without revising the document. When revision is in scope, answer each finding
by its number (what changed and where, or why nothing changed), revise, and check that the
revision did not break the passages that depend on it. Keep the review and the response as
supporting files only when requested or when they record reasoning needed later; otherwise
the reply is enough. Update the main note's opening whenever its answer, method, decisive
conditions, limitation or next step has become inaccurate.

Stop when the blocking and important findings are resolved or deferred with a stated
reason. A deferred finding keeps its consequences: state what it leaves unestablished.
Another round is warranted when the revision was substantial or a resolution is disputed.
