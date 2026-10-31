# How selected Ren GW and RPA papers build their arguments

The useful pattern is conditional: the paper's contribution determines what
must be established first. A common numerical framework, a diagrammatic
correction, a periodic implementation and a distributable library have different
burdens of explanation. These observations concern coauthored papers, not the
personal authorship of particular sentences or an official group style.

## Originals and reading limits

Locators below use physical PDF pages, including front matter. The 2015 reprint
has a cover: its printed page 1 is PDF page 2. The 2021 suffix pagination matches
PDF pages. The 2024 and 2026 locators refer to the named preprints, not later
typesetting.

| Key and original | Reading performed for organization |
|---|---|
| **RI12:** Ren et al., *Resolution-of-identity approach to Hartree–Fock, hybrid density functionals, RPA, MP2, and GW with numeric atom-centered orbital basis functions*, NJP **14**, 053020 (2012), [1201.0655v2](https://arxiv.org/abs/1201.0655v2), [PDF](https://arxiv.org/pdf/1201.0655v2) | Abstract, contents and introduction; selected theory from the notation study; §§4.2–4.4; opening and selected comparisons of §4.5; transitions and selected results in §§5–6; conclusion and appendix roles. Not every benchmark datum or integral derivation. |
| **RPA12:** Ren, Rinke, Joas and Scheffler, *Random-phase approximation and its applications in computational chemistry and materials science*, J. Mater. Sci. **47**, 7447–7471 (2012), [1203.5536v2](https://arxiv.org/abs/1203.5536v2), [PDF](https://arxiv.org/pdf/1203.5536v2) | Abstract, introduction, section boundaries; AC/ACFD theory and selected MBPT/CC passages; algorithm and beyond-RPA openings; selected application passages, outlook and appendix roles. Not an exhaustive review of applications or cited literature. |
| **SOSEX15:** Ren et al., *Beyond the GW approximation: A second-order screened exchange correction*, PRB **92**, 081104(R) (2015), [publisher](https://doi.org/10.1103/PhysRevB.92.081104), [PDF](https://acris.aalto.fi/ws/portalfiles/portal/2163742/PhysRevB.92.pdf) | Main argument on PDF pp. 2–6, equations, figure discussions and ending. Supplementary material was not read. |
| **GW21:** Ren et al., *All-electron periodic G0W0 implementation with numerical atomic orbital basis functions: Algorithm and benchmarks*, PR Materials **5**, 013807 (2021), [publisher](https://doi.org/10.1103/PhysRevMaterials.5.013807), [PDF](https://pure.mpg.de/rest/items/item_3263538/component/file_3285757/content) | Abstract and introduction; §II from the notation study; §III and §IV argument-bearing passages; §V comparison and exceptions; §VI outlook. Table I on p. 15 also visually inspected. No independent recalculation. |
| **LibRPA24:** Shi et al., *LibRPA: A Software Package for Low-scaling First-principles Calculations of Random Phase Approximation Electron Correlation Energy Based on Numerical Atomic Orbitals*, [2407.19930v1](https://arxiv.org/abs/2407.19930v1), [PDF](https://arxiv.org/pdf/2407.19930v1); subsequently CPC **309**, 109496 (2025) | Abstract, program summary and introduction; theory from the notation study; software, parallelization and usage sections; performance opening, application discussion, conclusion and appendix roles. Not a current installation test or complete API audit. |
| **GW26:** Zhang et al., *Low-scaling GW calculations of quasi-particle energies for extended systems within the numerical atomic orbital framework*, [2603.27292v2](https://arxiv.org/abs/2603.27292v2), [PDF](https://arxiv.org/pdf/2603.27292v2) | Abstract and introduction; theory from the notation study; implementation structure and selected contractions; workflow and settings; accuracy and efficiency argument-bearing passages; conclusion and appendix roles. Figure 7 on p. 39 visually inspected. Not an implementation or benchmark reproduction. |

## Different contributions produce different article architectures

### A shared numerical framework: RI12

The contents on pp. 2–3 make the dependency visible: §2 establishes the
many-body objects (pp. 6–13); §3 expresses their shared product-space operations
through RI (pp. 14–20); §4 constructs and tests auxiliary bases (pp. 21–31);
§5 tests orbital bases (pp. 32–43); §6 assesses molecular observables
(pp. 43–47). The introduction on pp. 3–6 explains why several methods belong
together before announcing this route.

The opening of §5, p. 32, provides a short anchor: “Having established the
quality of our ABFs”. Its job is to close one uncertainty before opening
another. In §4.5 the orbital representation is held fixed to examine RI;
changing the orbital basis in §5 asks a different question. The later physical
benchmarks inherit those controls.

**Editorial inference:** when the contribution is a common numerical
representation, organize around shared operations and separate sources of
error. **Failure condition:** this order becomes wasteful when a short note
only changes one contraction. Such a note should enter at that contraction.

### A conceptual synthesis: RPA12

The review moves from history and motivation (§I, pp. 1–4) to complementary
theoretical formulations (§II, pp. 5–10), algorithms (§III, pp. 10–11), repairs
beyond RPA (§IV, pp. 11–13), applications (§V, pp. 13–20) and open problems
(§VI, p. 20 onward). The anchor “adiabatic connection” in §II's opening, p. 5,
names the common conceptual entry. The alternative formulations then explain
different properties and computational possibilities.

The coupled-cluster passage, pp. 9–10, develops amplitude equations through
projection and the ring restriction, then identifies the nonunique-solution
issue. Alternative formulations are not presented as interchangeable without
conditions. Corrections appear before the application survey so the reader can
understand what defects they attempt to repair.

**Editorial inference:** a review or comparative teaching note can organize
around different answers to one conceptual question. **Failure condition:**
the review's historical breadth should not become a compulsory introduction
to a narrow GW implementation paper. Its outlook describes the situation in
2012, not the present software state.

### A bounded correction: SOSEX15

This short article has no numbered body sections. On PDF p. 2 the introduction
identifies failures of GW that motivate a specific correction: frontier levels
alone do not resolve relative level positions or all electron affinities. On
p. 3, Eqs. (1)–(7) turn an energy-diagram analogy into an explicit self-energy
operation. The anchor “The key step comes next” marks the exchange of diagram
connections. The same passage immediately discusses perturbative content,
double counting and differences from other screened-exchange constructions.

The computable form and implementation follow on p. 4, alongside the benchmark
definition. The population statistics are followed by benzene and TCNE
(pp. 5–6): examples chosen to expose the failures used in the motivation.
Improved averages do not substitute for resolving those particular spectral
features.

**Editorial inference:** a compact methods contribution can follow
failure → construction → distinction from nearby alternatives → discriminating
tests. **Failure condition:** the diagrammatic analogy proposes the
construction; it does not prove its numerical accuracy. A note can use this
argument without copying the article's claims or rhetorical phrases.

### A periodic implementation: GW21

After the physical and computational motivation, §II (pp. 3–6) connects
continuum quantities to auxiliary matrices and LRI. Section III (pp. 7–9)
handles two problems left unresolved by the formal equations: adequate
auxiliary bases and the Coulomb singularity. The heading “CONVERGENCE TESTS”
at §IV, p. 9, introduces separate tests of auxiliary basis, k sampling and
one-electron basis. Only then does §V (pp. 15–17) compare many solids.

The paper repeatedly distinguishes orbital-basis augmentation from extra
functions used only to generate the auxiliary basis. That distinction makes
the convergence sequence interpretable. Table I, p. 15, groups codes and
PBE/GW levels; the surrounding text distinguishes numerical cross-code
comparisons from experimental comparisons with physical corrections. Residual
disagreements and difficult systems are discussed rather than erased by an
overall statistic.

**Editorial inference:** when implementation choices affect the interpretation
of benchmarks, explain and control them before the broad table.
**Failure condition:** agreement between codes with shared approximations is
not automatically a basis-limit or experimental validation.

### A reusable software package: LibRPA24

The abstract and introduction distinguish the existing low-scaling method
from the package that makes it usable. The theory is compressed in §2
(pp. 4–9), with fuller derivations delegated to earlier work. Section 3
(pp. 9–13) explains components, parallelization choices and interfaces;
Fig. 1, p. 10, locates the input producer, driver/API and calculation core.
The abstract's anchor “software architecture” is fulfilled by these concrete
boundaries, not merely by naming libraries.

Installation and usage (§4, pp. 13–14), performance (§5, pp. 14–15) and a
water/graphene application (§6, pp. 16–18) answer different reader needs.
The application defines adsorption energy before interpreting curves, while
Appendix C, p. 22, supports the basis/BSSE treatment. The program summary and
usage section are appropriate to this software genre.

**Editorial inference:** distinguish an algorithm contribution from a package
contribution, and connect data interfaces to the scientific quantities they
carry. **Failure condition:** ordinary theory papers and short notes do not
need installation instructions; old commands do not establish today's usage.

### A low-scaling evaluation strategy: GW26

Section 2 (pp. 5–17) establishes the objects and transforms. Section 3
(pp. 17–31) reorganizes them into atom-pair contractions, treats remaining
numerical issues and then assembles a workflow. Figure 4, p. 30, comes after
its ingredients and points back to their equations. The algorithmic
rearrangement near Eq. (47), p. 22, explains both equivalence and why the
chosen contraction order saves work.

Section 4 first assesses accuracy (§4.1, pp. 31–36), then efficiency
(§4.2, pp. 36–45). Its accuracy opening on pp. 31–32 explicitly conditions
the comparison on “shared approximations”. The efficiency discussion first
relates filtering thresholds to error and cost, then addresses k sampling,
system size and parallel scaling. These are different scaling variables.
The abstract and conclusion distinguish formal scaling of important stages
from observed combined costs.

**Editorial inference:** a faster evaluation must establish what it preserves
before its speed has meaning. **Failure condition:** agreement within a shared
NAO/LRI representation does not test that representation independently; a
stage's asymptotic operation count is not the measured total runtime.

## How the smaller units do their work

The following are interpretations of the located passages, not rules declared
by the authors. They transfer decisions rather than wording.

### Three passages at paragraph scale

**RI12 §4.4, p. 24: the diagnostic is argued for before it is plotted.** The
first paragraph identifies what construction already controls (accurate on-site
representation at the chosen truncation thresholds), then what remains
uncertain (off-site products), and therefore what
this test must examine. The next paragraph names one fixed N2 product, explains
why its exact target stays unchanged while the auxiliary spaces grow, and
specifies the thresholds. Only after that setup does it read the curves. The
seemingly adverse observation—larger pointwise RI-V residuals—becomes a chance
to explain the metric's purpose: the relevant optimization concerns a Coulomb
integral. The writing gains force from choosing the right question and norm,
not from describing every curve as an improvement. A local adaptation should
keep this distinction; it should not infer general energy accuracy from a
single fitted product.

**SOSEX15 PDF p. 3: novelty and its theoretical liability are adjacent.** The
passage first rewrites the familiar correlation self-energy to expose one bare
and one screened interaction. It then exchanges connections, gives the new
formula and points to the diagram. The following paragraph identifies a cost
of mixing expansions in these interactions: possible double counting. The
authors describe expansion in the bare interaction as their check. They then
distinguish their construction from other SOSEX energy expressions and from
an expansion with two screened lines. The useful operation is to explain a
new object's identity and limitations immediately, before presenting its
successful tests. This reading reconstructs their exposition; it does not
independently prove the full diagrammatic series or read the supplement.

**GW26 §4.1 opening, pp. 31–32: the benchmark's interpretation precedes its
numbers.** The paragraph first states the comparison's purpose, then names
the shared input representation, LRI approximation and singularity treatment.
It uses these shared choices to identify the changed object being assessed:
the low-scaling evaluation strategy, including its time/frequency grids. Its
last step assigns the underlying NAO/LRI framework's assessment to earlier
work. Thus the scope of the evidence is built into the reader's interpretation
before the first convergence figure. The subsequent grid paragraph on p. 32
keeps individual-material statements, exceptions and the mean separate. In
our writing this logic should determine the abstract's claim as well as the
benchmark paragraph; it cannot be repaired only by a late disclaimer.

### Located decisions for other writing problems

| Writing problem | Source decision and locator | Adaptation and limit |
|---|---|---|
| An abstract lists features but gives no contribution | RI12 p. 1 connects several methods through common RI machinery; GW26 pp. 1–2 connects the cost problem to a representation, matched comparisons and qualified scaling | State the bottleneck, intervention, strongest supported result and scope. Include only results actually available. A proposed-method abstract must not sound like completed validation. |
| An introduction surveys the field without selecting a question | SOSEX15 PDF p. 2 names failures that reappear in its tests; GW21 pp. 1–3 identifies periodic obstacles after earlier molecular work | Make the unresolved obstacle concrete and let it determine the contribution paragraph. A citation supports an actual prior result or limitation, not a generic claim that a field is important. |
| The new method is hidden inside background theory | SOSEX15 PDF p. 3 places the connection exchange between the familiar GW expression and the discussion of its perturbative meaning | Mark the operation that changes the theory, state what is retained and explain its relation to alternatives beside the equation. Analogy is motivation, not proof. |
| A list of equations does not explain how to compute the result | GW26 §3.1, especially Eq. (47), p. 22, changes contraction order and exposes a reusable intermediate | Explain mathematical equality before computational advantage. Name the indices/blocks being iterated and what is reused. The notation skill separately checks phases, metrics and contractions. |
| A basis test confirms what construction already controls | RI12 §4.4, pp. 24–25, tests an off-site product after explaining controlled on-site accuracy by construction; compares pointwise residuals with Coulomb-integral error | Choose a diagnostic that can fail. Match the diagnostic norm to the claimed observable; a visually smaller function residual need not mean a better Coulomb fit. |
| A transition simply announces the next section | RI12 §5 opening, p. 32; GW21 §IV.B opening, p. 11 | State what the preceding evidence has controlled and which uncertainty remains. Do not promote partial controls to universal convergence. |
| A result paragraph paraphrases an entire figure | GW21 §IV.A, pp. 10–11, uses Si/MgO behavior and computational cost to motivate a practical ABF choice; §V, pp. 16–17, isolates difficult compounds | Explain the comparison, the consequential trend and exceptions, then the decision it supports. A suspected mechanism needs an uncertainty marker or a discriminating test. |
| Mean error hides a difficult case | GW26 §4.1.1, p. 32, distinguishes the mean from individual-material convergence; §4.1.3, pp. 35–36, discusses outliers | Keep average, maximum and named exceptions distinct. A tolerance met on average is not met by every system. |
| A performance plot has no accuracy contract | GW26 §4.2.1 and Fig. 7, pp. 37–39, give stage-specific thresholds, reference errors, core-hours and hardware | Pair useful cost with achieved accuracy. Copy the comparison logic, not necessarily the dual-axis graphic. Threshold choices may depend on system and size. |
| A cost claim uses an ambiguous denominator | GW26 §§4.2.2–4.2.4, pp. 40–45, distinguish k scaling, system size, a sum of three stage times and parallel speedup | State what is held fixed, what is varied, the timer boundary and the baseline. Do not rename a stage sum as end-to-end cost without evidence. |
| A caption cannot be read independently | GW21 Table I, p. 15, groups methods and levels with technical context; GW26 Fig. 6, p. 34, states the energy reference and path comparison; Fig. 7, p. 39, states error and cost references | Supply observable, units, baseline, labels and the settings that change interpretation. Detailed numerical-table findings remain in the separate display reading. |
| An appendix removes an essential assumption | RI12 Appendix A, pp. 49–52, supports integral evaluation; GW26 Appendix A, pp. 57–58, specifies transforms | Put lengthy recoverable algebra or implementation detail in appendices, but retain the definitions and assumptions needed to understand the main claim beside it. |
| A conclusion recites the contents or promises completed work | RI12 §7, pp. 47–49; GW21 §VI, p. 18; GW26 §5, pp. 46–47 | State the demonstrated capability and its boundary, then derive future work from the remaining limitation. Future SOC, metals or lower-dimensional extensions are not present validation. |

## Adapting these decisions to notes

This is a **editorial adaptation**, not an observed Ren note-writing style:
the corpus consists of papers. A short research note can state its question,
give the minimum definitions, expose the decisive derivation or comparison and
close with the bounded answer. It does not need an abstract, literature survey,
software section or benchmark section when those jobs do not exist.

A teaching note may expand the step between two equations that a methods paper
compresses, using a small example or limit to reveal the mechanism. The example
must be labelled as constructed if it is not a research result. An internal
decision note may retain the unresolved alternative and the calculation that
would distinguish it. Neither should acquire publication-level claims merely
because the prose resembles an article.

These domain-specific observations do not replace an exemplar or notation
already chosen for another purpose. Neither author analogy nor source fidelity
supplies evidence for a new scientific conclusion. The companion source
comparison's printed-equation qualifications still apply.

## What this reading does and does not establish

The source skeletons and located passages support the writing choices above.
They do not establish a universal author template, a full publication survey,
or correctness of every source equation and benchmark. Operational instructions
are kept in the [writing skill](../SKILL.md) and its [section-craft reference](section-craft.md), so that this
source study can be revised without duplicating the writing workflow.


These source observations are a basis for editorial choices, not a benchmark
of improved writing quality. Task-specific draft reviews and unpublished
research examples stay in the consuming project.
