# Numerical displays in selected Ren papers

Selected table and figure readings support display choices, not a universal
author template or claims about the personal authorship of their layout.

## Checked passages

### RI, RPA and molecular GW: comparison axes and hierarchy

Ren et al., *Resolution-of-identity approach to Hartree–Fock, hybrid density
functionals, RPA, MP2 and GW with numeric atom-centered orbital basis functions*,
NJP **14**, 053020 (2012), [arXiv:1201.0655v2](https://arxiv.org/pdf/1201.0655v2).
The [original](https://arxiv.org/pdf/1201.0655v2)
is the 60-page preprint; the following printed and PDF page numbers coincide.
Published pagination was not checked.

- **Table 3, §5.2.3, p. 42:** locator “HOMO and LUMO values”. Starting-point and
  all-electron/pseudopotential groups organize basis rows; two adjacent energy
  columns use eV and two decimals. Implementation explanations and sources are
  lettered notes beneath the table.
- **Table 4 and Fig. 16, §6.1, p. 44:** locator “Mean error (ME)”. Six methods
  have three statistical columns, with separately identified energy and percentage
  units. The companion histograms show distributions that those statistics hide.
- **Table 5, §6.2, pp. 46–47:** molecule rows, method/reference columns, one-decimal
  values, repeated headers on the continuation and final error statistics. Its
  preprint header/caption omits the unit: that omission is not a practice to adopt.

**Editorial inference:** organize the approximations visibly before comparing
numbers; neither a fixed row limit nor a single display type follows from these
examples.

### Periodic GW: a broad comparison and a focused difficult case

Ren et al., *All-electron periodic G0W0 implementation with numerical atomic
orbital basis functions: Algorithm and benchmarks*, PR Materials **5**, 013807
(2021), [published original](https://pure.mpg.de/rest/items/item_3263538/component/file_3285757/content)
([PDF](https://pure.mpg.de/rest/items/item_3263538/component/file_3285757/content)).

- **Table I, §V, printed 013807-15 / PDF p. 15:** locator “PBE and G0W0@PBE band
  gaps”. Materials are rows; grouped implementation/method columns contain
  numerical gaps, followed by reference-defined MD/MAD rows. Shared conditions
  and qualifications occupy the caption. Horizontal rules replace a cell grid.
- **Table II and Fig. 7, §V, printed 013807-16 / PDF p. 16:** the narrower table
  isolates ZnO implementations, starting points and references; the scatter plot
  reveals the broad calculated-versus-experimental pattern.

The main table has eight columns and a substantial caption, yet its numerical
body remains easy to scan. Its energy unit is contextual rather than explicit,
and the visible material-row count differs from the adjoining prose. These are
reasons to adapt critically, not reproduce the layout uncritically.

### SOSEX: choosing a figure when the question concerns a distribution or spectrum

Ren et al., *Beyond the GW approximation: A second-order screened exchange
correction*, PRB **92**, 081104(R) (2015),
[original electronic reprint](https://acris.aalto.fi/ws/portalfiles/portal/2163742/PhysRevB.92.pdf)
([PDF](https://acris.aalto.fi/ws/portalfiles/portal/2163742/PhysRevB.92.pdf)).
The linked electronic reprint contains a repository cover followed by six journal pages.

- **Fig. 2, printed 081104-3 / PDF p. 4:** locator “Histograms of the vIE error
  distribution”. Four panels compare methods and starting points on common axes,
  with summary errors in the panels.
- **Figs. 3–4, printed 081104-4 / PDF p. 5:** spectra expose peak positions and
  separations. Their caption defines the graphical conventions; the prose
  interprets the remaining discrepancy.

There are no numbered tables in this main article. **Editorial inference:** a
benchmark need not become a table when its decisive information is a distribution,
level ordering, spectrum or parameter dependence.

## Decisions to transfer to a manuscript

The useful common choice is to make the comparison readable before adding
reproducibility detail. These are editorial adaptations, not a universal
author-style prescription:

1. Choose the observable and reference before choosing columns. Put adjacent
   numerical values in the same units when a matched comparison permits them.
2. Group shared methods, input conditions or approximation levels in headers or
   row blocks. Avoid repeating sentences inside every cell.
3. Keep the numerical body compact; define shared conditions, units and norms
   in the caption or notes. Place lengthy execution protocols and record coverage
   in methods or supporting material. A necessary caption can be substantial.
4. Use horizontal rules, whitespace and consistent numerical alignment. Select
   meaningful precision for the comparison, retaining finer raw output elsewhere;
   do not impose a universal number of decimals or columns.
5. Use curves for refinement or iteration, distributions for the spread of errors,
   and tables for selected values. Summary statistics must not conceal a decisive
   outlier, failed criterion or unmatched reference condition.

