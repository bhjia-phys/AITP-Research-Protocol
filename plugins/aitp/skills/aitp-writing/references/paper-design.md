# Plan a paper from the research account

Read this when the researcher asks for a paper plan or outline, a first draft built
from research notes, or a reorganization of a substantial draft. It turns
[scientific argument design](manuscripts.md#scientific-argument-design) into steps
with a visible result. Ordinary note work does not use it, and an already coherent
draft needs no replanning.

The paper continues the reasoning in the notes; it is not a translation of them.
Decide what the paper argues and what establishes each step before writing prose.
Polished sentences cannot supply a missing inference, and a better outline cannot
supply missing evidence.

## Work from the question to the prose

Each step settles one thing, and each has a test that ends it. Return to an earlier
step when a later one fails; a gap found in the evidence audit sends the work back to
research within its agreed scope, not forward to drafting.

| Step | What it settles | Done when |
| --- | --- | --- |
| Question | What the paper answers, for which reader | It can be stated in two sentences without quoting its results |
| Claims | The few results the paper asserts | Each is one sentence with its conditions and its status (below) |
| Evidence audit | What establishes each claim, and what is missing | Every claim points to a located derivation, source passage or numerical report, or its gap is named |
| Thesis | The one statement the paper argues | The abstract could be written by expanding it |
| Argument map | Which claims support which, and what the reader must already know | Every claim either reaches the thesis or is cut, moved to an appendix or kept as a remark |
| Section plan | Each section's question and the display, figure or table that answers it | No section exists only to report a calculation the argument does not use |
| Exposition plan | Definitions, conventions, main-text equations, appendix and supplement content | Every main-text equation has a role; prerequisites precede their use |
| Draft | The prose | Written from the map, not from the order in which the work was done |
| Review | [Exposition passes](exposition-review.md) and [aitp-verify](../../aitp-verify/SKILL.md#review-a-manuscript) | Blocking findings are resolved or the claim is narrowed |
| Revision | Title, abstract, opening and ending | A [reverse outline](../SKILL.md#revise-the-argument-as-a-whole) of the draft matches the map |

Work privately unless the researcher asks to see the plan. When they want it kept,
keep it in the manuscript folder, for example `manuscripts/<paper>/plan.md`. The
research notes remain the home of the claims and their evidence; the plan points into
them and never becomes a second account of the research.

## Audit the evidence before choosing the thesis

For each candidate claim, write the sentence as it would appear in the paper, its
status, the located evidence and what is missing. A compact table is enough:

| Claim as written | Status | Evidence | Missing or could refute it | Used in |
| --- | --- | --- | --- | --- |
| "The splitting decays as $e^{-L/\xi}$ with $\xi$ given by (12) for $\lvert\mu\rvert<2t$" | derived, conditional on the bulk gap | `notes/decay-length.md` §3; numerical check to $L=60$ in `calculations/splitting/report.md` | Oscillating regime not treated | Sec. 3, abstract |

Synthetic example; a real audit links the actual files and sections.

The audit blocks drafting when a central claim has no evidence, when numerics stand in
for a stated proof, when an imported theorem's hypotheses have not been checked
against this setting, or when the result depends on a physical identification that the
text does not state. Resolve the gap or narrow the claim. Record new checks where the
claim lives, as memory's write rules describe, not in the plan.

## State each claim at the strength of its evidence

The verb and its qualifiers carry the epistemic status. Use them consistently in the
title, abstract, introduction, body, captions and conclusion.

| Status | Natural phrasing | Requires | Must not become |
| --- | --- | --- | --- |
| Definition or convention | "We define", "we use the convention" | The choice and, when not obvious, why it is natural | "We show" |
| Proved here | "We prove", "it follows that", a stated theorem | A complete argument in the text or an appendix, with hypotheses stated where used | — |
| Imported | "By Theorem 3.2 of [12]", "as shown in [12]" | A located source whose hypotheses match this setting | An unattributed "it is well known" for a nontrivial result |
| Conditional | "If $X$, then $Y$", "assuming $X$" | $X$ stated where $Y$ is used, and in the abstract when $Y$ is central | $Y$ alone |
| Controlled approximation | "To leading order in $\epsilon$", "up to $O(\epsilon^2)$" | The expansion parameter, retained order and what controls the remainder | "Exactly", "nonperturbatively" |
| Formal or heuristic | "A formal manipulation gives", "heuristically" | The step that is not justified, named | "We derive" |
| Numerical observation | "For $L\le 24$ and the parameters of Table I we find" | Range, uncertainty and convergence evidence | "For all $L$", "in the thermodynamic limit", "proves" |
| Extrapolation | "Extrapolating in $1/L$ with the form (20), we estimate" | A justified fit form and its sensitivity | An exact value |
| Conjecture | "We conjecture", with its evidence and a test | The evidence, and what would confirm or refute it | "It is expected that", or a silent premise of later results |
| Interpretation | "We interpret this as", "this suggests a mechanism in which" | The alternatives considered and why this one is preferred | "This shows that the mechanism is" |

Editing must never move a claim up this table. A stronger verb needs new evidence,
recorded where the claim lives. Keep a researcher's unresolved objection beside the
claim it concerns, in the paper's terms, rather than deleting it during polishing.

## Write a thesis that the abstract can expand

A usable thesis names the object, the result and its decisive condition, says what it
changes relative to what was known, and could turn out to be false. "We study the
Kitaev chain with disorder" is a topic. A hypothetical thesis of the right form is: "For
bond disorder weaker than an explicit bound $W_*(\mu,\Delta)$, the Majorana splitting
decays exponentially in $L$ for every disorder realization, by a transfer-matrix
estimate." It can be checked, and its condition and route are visible. When no single
thesis fits, the paper may be two papers or not yet a paper; say so to the researcher
rather than assembling results side by side.

## Plan sections by the work they do

Give each section a question, the display, figure or table that answers it, and what it
hands to the next section. Order sections by dependency and by what the reader needs,
not by the history of the project. A failed route earns a section only when its failure
is a needed limitation. The [genre organizations](witten-corpus-analysis.md#genre-findings)
show orders that published theory papers have used; adapt them to this argument rather
than copying their sequence.

Give every main-text equation one of these roles: a definition or convention, an
assumption, an approximation, an identity the argument uses, the decisive step, a
result, or a check. An equation with none of these roles goes to an appendix or out of
the paper. Before a substantial display say what it will settle; after it say what it
shows and why the next step is needed, as [writing](../SKILL.md#make-equations-advance-the-explanation)
describes.

Keep in the main text the definitions the reader needs, the decisive step, the
hypothesis that licenses it and the result. Move to an appendix long but routine
calculations, supporting lemmas, alternative derivations and convention translations;
point to the appendix where its result is used. An appendix completes the argument; it
should not be the first place the reader learns why the result holds. Supplementary
material carries reproducibility detail (complete parameter tables, convergence scans,
code and data locations) when the venue keeps the main text short; it must not hide a
step the central claim depends on.

Fix notation once. One symbol names one object throughout the main text, appendices and
figures; signs, units and normalizations agree, or a change is announced where it
happens. When conventions matter, give them a short section or paragraph before first
use. During drafting, keep a private symbol list to check against; publish it only
when it helps the reader.

## Make the introduction and conclusion carry the argument

The introduction has jobs, not compulsory headings:

1. **The question and why it is open.** The specific difficulty, mismatch or limitation,
   stated so that a reader outside the subfield sees what is not understood. The
   importance of the field is not a question.
2. **What is known and why it does not settle the question.** Precise attributions to
   results actually read, with their conditions.
3. **What this paper establishes.** The claims at their true strength, with the main
   condition, early enough that the reader knows what to look for.
4. **How it is established.** The route and the idea that makes it work.
5. **A map, only when the dependency order is not evident.** It explains why the parts
   are needed, rather than repeating the table of contents.

The conclusion states what was established and under which assumptions, what that
changes for the original question, and what remains open as a specific calculation,
obstruction or test. It adds no new claims and does not strengthen earlier ones.
Limitations are written as physics or mathematics: the regime not treated, the
assumption not removed, the size not reached. The abstract follows the same order in
compressed form: question, result with its condition, route, consequence. Every claim
in the title, abstract and conclusion must appear, with the same strength, in the body.

## Position the work against what is known

Locate the closest prior results by reading them, not only their abstracts, and record
their exact claims, as [literature guidance](../../aitp-research/references/literature.md)
describes. Then say what differs: a new result, a new regime, a new method, a new proof
of a known result, a correction, a negative result or a clarification, and why that
difference matters for the question. A sentence that names the content of the
difference is worth more than an adjective.

"First", "novel" or "unprecedented" needs a literature search whose scope is recorded in
the notes; an empty search is not evidence of novelty, and a rederivation in this
project is not a publication novelty. Cite concurrent or overlapping work and state the
relation. Venue fit is a separate judgment: the subject, contribution and readership
against the venue's current scope, as [journal sources](journal-templates.md) explains.
Then use the [venue strategies](venue-strategies.md) to organize the paper for that
readership.

## Keep a path from the paper back to the evidence

The manuscript README or a source comment records the version of the research notes the
draft was built from (the commit when the notes are under
[version history](../../aitp-memory/references/version-history.md), otherwise the date)
and which note owns each central claim. A TeX comment beside a central claim, such as
`% evidence: ../../research.md#decay-length`, lets a later reader return to the argument
and its sources; remove such comments before submission if the researcher prefers. When
the notes change, compare them with the draft as [manuscript handling](manuscripts.md)
describes; neither document updates the other automatically.
