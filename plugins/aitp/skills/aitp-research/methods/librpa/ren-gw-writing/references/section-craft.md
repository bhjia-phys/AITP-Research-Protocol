# Section and paragraph craft for GW/RPA writing

Read only the part relevant to the current passage. The [source study](organization.md)
owns the original passages and reading limits. Paper keys below refer to its
six pinned originals. The examples here are editorial constructions, not
quotations or results of LibRPA calculations.

## Title and abstract: name the actual contribution

Choose a title that names the method/object and the domain when the domain
limits the result. The GW21 title specifies a periodic all-electron NAO
implementation and benchmarks; the LibRPA24 title identifies a package and its
scientific operation. A paper about a faster implementation should not imply
a new many-body approximation. A correction paper should identify the correction.

In an abstract, connect the bottleneck to the intervention, then give the
strongest supported result and the regime in which it holds. This is a compact
argument, not a mandatory sentence count. RI12 p. 1 and GW26 pp. 1–2 show
different versions of it. Replace vague claims such as robust, accurate or
efficient with the relevant comparison when space permits.

Keep formal and measured claims separate. If only the response contraction is
quadratic, do not call the whole workflow quadratic. If timings exclude input
production, exchange or analytic continuation, identify the measured stages
instead of claiming end-to-end acceleration. A proposed algorithm without
numerical tests can have a theoretical abstract; it cannot have benchmark
conclusions manufactured to match a source article's structure.

State the strongest affirmative result within its actual domain. For example,
identify a measured sum of stage times and its size range directly, rather
than filling the abstract with a list of workflow claims it does not prove.
Retain the qualification that changes the main result's meaning; a list of
every untested extension usually belongs elsewhere or is unnecessary once the
tested domain is explicit. Accuracy of scope should sharpen the contribution,
not displace it.

## Introduction: make the gap select the work

Use enough physical context to explain why the target observable matters.
Then identify the existing method's concrete limitation and why a plausible
alternative does not already settle it. State the present contribution where
that gap becomes clear. Include a roadmap only if it helps a long argument.

SOSEX15 PDF p. 2 ties its motivation to particular spectral failures, which
return as tests. GW21 pp. 1–3 and GW26 pp. 2–4 connect earlier methods to a
specific representation or cost obstacle. LibRPA24 pp. 2–3 distinguishes
the earlier algorithm from the package being presented. Select the closest
scientific job; do not paste all three introductions into a general GW history.

Prefer paragraph roles over stock openings: establish the physical need;
explain the unresolved obstacle; delimit the contribution and its evidence.
Several roles may fit in one paragraph. Make comparisons fair to prior work,
with citations beside the particular capability, limitation or result claimed.
A source's old outlook is not evidence about today's implementation status.

## Theory: expose the consequential step

Begin from the object required by this claim, not necessarily from Hedin's
equations. Tell the reader what each consequential equation enables. Around a
new definition or approximation, supply enough of the following to make its
meaning recoverable: the reason for introducing it, the equation, its new
symbols and assumptions, and the consequence needed next. Avoid repeating all
four around every elementary line.

For example, a product-fit paragraph should make clear why orbital products
need a representation, which auxiliary space is used, and where that fit enters
the response. Its accuracy is a separate question. A self-energy correction
paragraph should show the actual changed contraction and its perturbative
content; an analogy to an energy functional is insufficient. SOSEX15 PDF p. 3
is the source example of keeping the new operation and its qualifications close.

Use [the notation skill](../../ren-gw-notation/SKILL.md) to keep kernel
expansions, operator matrix elements and weighted vertices distinct. Define a
new shorthand only after the reader knows the objects it compresses. In a
teaching note, expand the nontrivial index or Fourier step and check a relevant
limit. In a paper, move repetitive algebra to an appendix with an explicit
entry point; retain assumptions necessary for interpreting the main equation.
When detailed LRI/LibRI or GW exposition is requested, the notation skill's
detailed routes supply the full endpoint, cell and matrix derivations. Preserve
their consequential intermediate steps in the requested passage; article
brevity is not a reason to skip the very derivation the user asked to see.

## Algorithm and settings: explain why the equations become cheaper

At the passage from mathematics to implementation, identify the block or
index grouping, the independent work units, reusable intermediates and the
source of the cost reduction. Establish that a rearrangement preserves the
quantity before explaining its performance. If thresholding changes it,
state the approximation and connect the threshold to a later accuracy test.
GW26 §3.1, especially Eq. (47), p. 22, models this transition.

Give pseudocode when loop order or data dependencies are part of the
contribution. Do not narrate every line of ordinary code. A workflow diagram
can join already-defined quantities and producer/consumer boundaries, as
GW26 Fig. 4, p. 30, does; it should not substitute for the decisive contraction.
For a software article, explain why the architecture and communication choices
support the scientific operation (LibRPA24 §3 and Fig. 1). A theory note rarely
needs the full module hierarchy.

Separate mathematical choices from settings of the reported experiment.
State basis, auxiliary construction, k mesh, time/frequency grid, singularity
treatment, continuation and reference method when they determine the result.
Keep hardware and parallel configuration with performance claims. Do not fill
missing settings from remembered source defaults, and do not present historical
installation commands as verified current usage.

## Validation and results: turn a comparison into an inference

Select the comparison that tests this contribution. A controlled comparison
can isolate a changed evaluation with the representation and shared
approximations matched (GW26 §4.1, pp. 31–32). A convergence study varies one
numerical source while controlling others (RI12 §§4–5; GW21 §IV). A physical
assessment addresses an observable with an appropriate reference, including
corrections needed to compare like with like. These jobs can share a figure
but are not logically interchangeable.

Start the paragraph with the question or comparison, then state the result
that answers it. Discuss the consequential trend and exceptions, offer only
the interpretation the evidence supports, and end with what is now justified
or still unresolved. This sequence can span several paragraphs; it is not a
five-sentence mold. Avoid an exhaustive verbal tour of every plotted point.

An original, conditional paragraph pattern is:

> To isolate the time-grid error, we compare the two evaluations using the
> same orbital and auxiliary bases and the same Coulomb treatment. Increasing
> the grid resolves the discrepancy for the tested states, while the remaining
> outlier requires a separate continuation check. The comparison supports
> agreement of the two evaluations within this representation; it does not
> establish the basis-set limit.

Use this only if each statement matches the supplied evidence. Without a
continuation diagnostic, do not claim continuation *caused* an outlier. When
only aggregate data are available, do not invent the identity or behavior of
individual systems. Report mean and worst-case errors separately when the
conclusion invokes a per-system tolerance.

For performance, specify the accuracy at which cost is useful before comparing
speed. Separate system size from k count and number of workers; name what is
held fixed, the fit range and any small-system crossover. Identify the actual
timer boundary and baseline. GW26 §4.2 supplies examples, including filtering
errors that need not vary monotonically and parallel efficiency well below
ideal at the largest configurations. Do not inherit stronger adjectives than
the measurements support.

## Figures, tables and captions: make the comparison recoverable

Choose a display by the question: convergence curves for a numerical control,
paired error/cost information for a threshold choice, bands or level diagrams
for spectral structure, distributions for error populations, and a table when
individual numerical references matter. SOSEX15 uses spectral plots and error
histograms; it does not need a benchmark table merely because other papers do.

A caption should let the reader identify the observable, units, line/marker or
column meanings, reference/energy zero, and settings essential to interpretation.
For cost include hardware/parallel layout and what the timing measures when
those are not unambiguously established nearby. Distinguish computed,
extrapolated and corrected experimental values. Do not conceal a change of
reference in a caption that contradicts the prose.

Use grouped baselines and levels when they help comparison, as in GW21 Table I,
p. 15. Do not copy unexplained units or layout quirks: the separate
[numerical-display reading](numerical-tables.md)
records both useful decisions and source limitations. Fig. 7 in GW26, p. 39,
supports presenting accuracy and cost together; it does not make dual axes a
required design.

## Ending and appendices: close the demonstrated question

A conclusion should state what the work established, which comparison supports
it and the practical or physical consequence within that scope. Derive outlook
from a remaining limitation. Keep possible extensions distinct from tested
capabilities; source outlooks about SOC, metals or lower-dimensional systems
are examples of scope boundaries, not a description of current LibRPA.

Do not repeat the entire abstract and section list. A short note may need only
one closing sentence stating the answer and its limit. Put an unfinished
research task in its owning main note when recording ongoing work; it does not
automatically belong in publication prose.

Appendices may hold lengthy contractions, transform derivations, integral
algorithms or supplementary data. Their role is recoverability, as in RI12
Appendix A and GW26 Appendix A. State the main text's assumptions and reference
the exact supporting derivation rather than hiding an essential qualification.

## Notes: preserve the reasoning at a smaller scale

For a short derivation note, start with the precise question and existing
notation, perform the decisive step with enough intermediate work, and give
the check or limit that clarifies its meaning. Do not create empty methods,
results and outlook sections. A two-paragraph note may be the correct output.

For a teaching note, spend space on why the step works: an explicit contraction,
a small constructed example, or a limiting case. A learner should be able to
reconstruct the result rather than memorize the final formula. For an internal
comparison note, state the alternatives, the evidence that separates them and
what remains undecided. These are adaptations for the user's work, not claims
that the six-paper corpus establishes Ren's own note-writing practice.
