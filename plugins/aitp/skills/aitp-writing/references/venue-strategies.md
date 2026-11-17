# Organize a paper for its readership

Read this after the [paper plan](paper-design.md) has a thesis and an argument map. The
venue decides who reads the paper, how many claims it can carry, how much derivation the
main text holds and where the rest goes. It does not decide what is true, how strong a
claim is, or how carefully it is attributed.

The venues named below are examples of readerships, and the characterizations are
editorial guidance, not official requirements. Length limits, abstract limits,
supplementary material rules and required summaries change: check the venue's current
author guidance before submission, starting from the sources in
[journal sources](journal-templates.md). A template is not evidence that a paper suits a
venue.

## The strategies at a glance

| Strategy | Example venues | Reader | Claims | The main text carries | Elsewhere |
| --- | --- | --- | --- | --- | --- |
| Letter for a broad physics readership | PRL; letter sections of PRB or PRResearch | Physicists outside the subfield | One central result | The question, the result with its condition, the idea that makes it work, the decisive evidence | Supplemental material: complete derivations, further data, methods |
| Long-form theory paper | JHEP, PRD, SciPost Physics | Specialists willing to work through the construction | A connected set of results building one structure | Setup and conventions, construction, consequences, comparison with known results | Appendices: long calculations, lemmas, alternative derivations |
| Detailed condensed-matter or computational study | PRB, PRResearch | Specialists in the system or the method | Several controlled results answering one question | Model, method and its approximations, controlled comparisons, interpretation | Appendices or supplement: convergence, parameter tables, code and data |
| Article whose significance must be argued | PRX and similar | Physicists across fields | One or a few results with broad consequences | Motivation and interpretation developed at length, an accessible core argument | Technical sections and appendices |
| Mathematical physics | CMP, JMP, LMP, AHP | Mathematicians and mathematical physicists | Theorems with exact hypotheses | Definitions, statements, proofs or proof maps, physical motivation | Appendices: technical lemmas |
| Method development | Method sections of PRB, JCP, JCTC, CPC, SciPost Codebases | Users and developers of methods | What the method makes possible, at what accuracy and cost | Derivation, algorithm, cost, validation against known answers, limitations | Implementation details, benchmark tables, code and data |
| Review | RMP, Physics Reports, Rep. Prog. Phys. | Entrants and neighbouring specialists | A synthesis organized by questions | The questions, established arguments with attribution, controversies, open problems | — |
| Lecture notes | SciPost Lecture Notes, school proceedings | Students with stated prerequisites | Standard material and a perspective on it | A reader contract, worked examples, the derivations to reproduce, exercises | Further reading |

## Letter

The first paragraph makes the question matter to a physicist outside the subfield by
stating what is not understood, not by praising the field. The result appears on the
first page with its main condition. One idea carries the paper; the reader should be
able to say what it is. Each figure does inferential work, usually one figure carries the
decisive evidence, and the text says what the reader should see in it.

The main text keeps the definitions the argument needs, the decisive equations and the
evidence that the central claim is right. Complete derivations, further checks and
methods go to supplemental material, cited at the point of use; a step the central claim
depends on is at least sketched in the main text. Omit the paragraph that lists the
sections. The ending says what the result changes. The usual failure is a long paper
compressed: several claims, each under-argued. Choose the one claim the evidence supports
best.

## Long-form theory paper

The introduction states the results with their conditions and explains the dependency
order of the paper when it is not evident; it should not paraphrase the table of
contents. Conventions come before first use. The construction can move from a controlled
prototype to the general machinery and then to the target theory, saying what changes at
each step, as the [construction genre](witten-corpus-analysis.md#long-technical-construction-paper)
illustrates. Comparisons with known results appear where they test the construction, not
only in a closing section.

Appendices carry long but routine calculations, lemmas and alternative derivations; the
main text keeps the object, the essential hypothesis, the decisive step and the result.
A discussion section names specific open problems and what would resolve them. The usual
failures are a chronological account of the work, and the reason a result holds appearing
first in an appendix.

## Detailed condensed-matter or computational study

Define the model with its parameters, units and conventions, and say which physical
question it answers and what it leaves out. Describe each method with its approximations
and the controls that bound their effect: basis, cutoff, finite size, convergence,
statistical error. Organize results by the question or observable, not by the order of
the runs. Compare with experiment or other methods with stated uncertainties, and say
what each comparison can discriminate.

Interpretation follows the evidence and names the alternatives it excludes. Parameter
tables, convergence scans and code or data locations go to appendices or supplementary
material. Agreement between methods that share an approximation is consistency, not
validation of that approximation; see [computational and mixed work](computational-and-mixed.md).

## Article whose significance must be argued

The motivation and the interpretation have room to develop, because the reader must be
shown why the result matters across fields. Present the core argument accessibly before
the technical development, and keep its conditions visible in the accessible version.
Significance is argued from what the result changes, never asserted with adjectives.
Check whether the venue asks for a popular or lay summary; write it from the paper's
actual claims at their actual strength.

## Mathematical physics

State definitions and hypotheses precisely, and state each theorem at the resolution its
proof uses: the space, the operator or map, regularity, boundary or domain conditions,
and the exact conclusion. Give a map of the proof before its lemmas, in dependency order,
as the [proof genre](witten-corpus-analysis.md#theorem-or-proof-paper) shows. Mark formal,
heuristic and conjectural arguments as such where they occur. Explain the physical
motivation and the relation to the physics literature, including which physics statements
the theorems do and do not establish. Examples that violate a hypothesis show whether it
is necessary. The usual failures are a theorem stated without its hypotheses and a physics
heuristic presented as a proof.

## Method development

Begin with what existing methods cannot do: the accuracy, cost, scaling or regime that is
out of reach and why. Derive the method from the physics, then give the algorithm in a
form someone else could implement, with its cost and memory scaling. Validate on cases
with known answers (exact solutions or trusted high-accuracy references) using controlled
comparisons: the same inputs and approximations except the method under test, and timings
that include setup when the workload does. Report failure modes and the regime where the
method should not be used. State where the code and data are available. The usual
failures are benchmarks chosen only where the method works and timing comparisons with
different setups.

## Review

Organize by questions and concepts, not by chronology or by research group. Give the
arguments, not only the results, so the reader learns why things are believed. Attribute
carefully and fairly, and separate what is established, what is debated and what is open,
saying why. Give the reader a map of the subject and its prerequisites early. End with
open problems specific enough to work on.

## Lecture notes

Start with a reader contract written as prose: the intended reader and prerequisites,
the purpose, what is standard and what is a new perspective, important omissions, and
whether arguments are proved, sketched or heuristic, as the
[pedagogical genre](witten-corpus-analysis.md#pedagogical-or-review-note) describes. Use
a worked example before the abstraction it motivates, and return to the motivating
question. Exercises test whether the reader can reconstruct an operation; they never
replace an explanation the text owes. Follow [learning from sources](learning.md) for
depth and companion reading.

## Mixed cases

A theory letter with substantial numerics keeps the analytic statement and the decisive
numerical test in the main text and the convergence evidence in the supplement. A paper
that both introduces a method and applies it must decide which is the thesis: either the
method is validated and the application demonstrates it, or the application answers a
physical question and the method is described as far as that answer needs. When the
argument does not fit the venue the researcher wants, say so with the reason; do not cut
the conditions of a claim to make it fit.
