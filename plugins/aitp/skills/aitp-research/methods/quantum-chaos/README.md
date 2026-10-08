# Quantum chaos: spectra, OTOCs and operator growth

This method index collects what work on spectral statistics, out-of-time-order
correlators and Krylov operator growth needs, whichever capability is doing it:
investigating, writing or learning. Read only the part the task needs.

## Methods

AITP has no general quantum-chaos method Skill yet. The researcher's own skills, such as
audits of charge or symmetry spaces, stay in the workspace; the topic family's README
should list them so that they can be found.

## Conventions and checks

- **Resolve symmetries first.** Resolve the appropriate irreducible unitary-symmetry
  blocks and state how multiplicities were handled; mixing blocks superimposes independent
  spectra. Non-commuting charges, such as SU(2), make multiplets that must be handled
  explicitly.
- **Unfold, or use an unfolding-free measure.** Spacing distributions need the local
  density of states removed; the ratio of consecutive spacings avoids that step. Report
  which was used and the energy window, since spectral edges distort both.
- **Choose the right chaotic reference.** For ordinary Hermitian bulk statistics, use the
  antiunitary symmetry acting within each analysed block: GOE when it squares to +1, GSE
  when it squares to −1 (handle Kramers degeneracy explicitly), GUE when there is none.
  Poisson is a separate expectation that needs its own justification, not a consequence of
  symmetry alone. A crossover needs more than one system size.
- **Define the OTOC before reading it.** State the correlator, the state or ensemble,
  temperature, normalization and regularization. Distinguish the short-time expansion, any
  demonstrated exponential regime, spatial spreading and saturation, and report how fits
  depend on the window. Do not infer a Lyapunov exponent or apply the thermal chaos bound
  without checking the required regime and assumptions.
- **Krylov growth.** Lanczos basis operators lose orthogonality in finite precision. State
  the inner product, the starting operator and the coefficient range supported by the
  precision or by independent small-system checks. Apply growth hypotheses with their
  locality, dimensionality and limit assumptions, including the one-dimensional logarithmic
  correction where it applies; linear growth is not by itself a proof of chaos.
- **Finite size.** State the sizes used and whether a trend persists across them;
  integrable points and near-integrable regions need special care.

## Standard sources

Cite the original papers for the measures a calculation uses; this list is a starting
point. Each entry was checked against its Crossref record on 2026-10-07. Check any
further source with the [literature guide](../../references/literature.md).

| Topic | Source |
| --- | --- |
| Chaos and random-matrix level statistics | O. Bohigas, M. J. Giannoni and C. Schmit, Phys. Rev. Lett. 52, 1 (1984), doi:10.1103/PhysRevLett.52.1 |
| Ratio of consecutive spacings | V. Oganesyan and D. A. Huse, Phys. Rev. B 75, 155111 (2007), doi:10.1103/PhysRevB.75.155111; Y. Y. Atas, E. Bogomolny, O. Giraud and G. Roux, Phys. Rev. Lett. 110, 084101 (2013), doi:10.1103/PhysRevLett.110.084101 |
| Thermalization and chaos, review | L. D'Alessio, Y. Kafri, A. Polkovnikov and M. Rigol, Adv. Phys. 65, 239 (2016), doi:10.1080/00018732.2016.1198134 |
| Bound on chaos from OTOCs | J. Maldacena, S. H. Shenker and D. Stanford, JHEP 08 (2016) 106, doi:10.1007/JHEP08(2016)106 |
| Operator growth and Krylov complexity | D. E. Parker, X. Cao, A. Avdoshkin, T. Scaffidi and E. Altman, Phys. Rev. X 9, 041017 (2019), doi:10.1103/PhysRevX.9.041017 |
| Inverse-square (Haldane–Shastry) chain | F. D. M. Haldane, Phys. Rev. Lett. 60, 635 (1988), doi:10.1103/PhysRevLett.60.635; B. S. Shastry, Phys. Rev. Lett. 60, 639 (1988), doi:10.1103/PhysRevLett.60.639 |
