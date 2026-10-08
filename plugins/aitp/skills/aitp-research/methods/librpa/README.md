# GW, RPA and LibRPA

This method index collects what GW, RPA and constrained-RPA work with LibRPA needs,
whichever capability is doing it: investigating with these methods, writing about
them or learning them. Read only the part the task needs.

## Methods

- [Developing LibRPA](developing-librpa/SKILL.md): review, simplify or extend LibRPA by
  tracing its active GW and RPA paths, API and driver boundaries, matrix ownership and
  relevant regressions.
- The researcher's own GW skills, such as material workflows and producer/consumer
  runs, stay in the workspace. The topic family's README lists them; read that list when
  the task runs or adapts a calculation.

## Conventions and checks

- Before comparing numbers, state the approximation (G0W0, self-consistent or
  quasiparticle self-consistent GW, RPA, constrained RPA), the frequency treatment
  (imaginary axis, analytic continuation, static limit) and the basis (atomic orbitals
  and the auxiliary or resolution-of-identity basis).
- Keep units and normalizations explicit. Response matrices in a native auxiliary
  normalization are not energies, and Hartree and electronvolt values are not
  interchangeable.
- Separate three claims: agreement between implementations, numerical convergence
  (basis, k and q meshes, frequency grid) and physical validity. None establishes another.
- In self-consistent GW, distinguish convergence of the unmixed map, the precision of
  that map and the selection of the quasiparticle branch. A small mixed step or a stable
  gap shows none of these alone.
- In constrained RPA, state which transitions are excluded and in which output frame the
  interaction is contracted. The resulting interaction parameters belong to that model;
  they are not transferable material constants.
- An analytic continuation can be stable without being accurate. Check it against data
  it was not fitted to.

## Resources

Fully stored dense auxiliary response and screened-interaction matrices require storage
proportional to $N_\mathrm{aux}^2 N_q N_\omega$. Self-energy storage depends on the retained
atomic-orbital or Kohn–Sham representation. Estimate resident memory from the actual
implementation, including distribution, replication and temporary arrays, and identify
the peak stage by measurement; the [Slurm guide](../../references/slurm.md)
says what a measurement covers.

## First-divergence audit

When two versions of a calculation disagree, for example after a merge, between branches
or against a reference implementation, diagnose before fixing. Freeze the inputs and
settings, and trace the actual producer and consumer dependency order of the selected
calculation. Compare matched intermediates after aligning conventions, basis and point
ordering; use invariant comparisons where phases or degenerate subspaces are arbitrary.
Narrow the first unexplained discrepancy with a targeted test, prove its cause, and only
then fix. Record the chain in the existing comparison report.

## Standard sources

Cite the original papers for the methods a calculation actually uses; this list is a
starting point, not a requirement to cite every entry. Each entry was checked against its
Crossref record on 2026-10-07. Check any further source with the
[literature guide](../../references/literature.md).

| Method | Source |
| --- | --- |
| GW approximation | L. Hedin, Phys. Rev. 139, A796 (1965), doi:10.1103/PhysRev.139.A796 |
| GW for semiconductors and insulators | M. S. Hybertsen and S. G. Louie, Phys. Rev. B 34, 5390 (1986), doi:10.1103/PhysRevB.34.5390 |
| Reviews | F. Aryasetiawan and O. Gunnarsson, Rep. Prog. Phys. 61, 237 (1998), doi:10.1088/0034-4885/61/3/002; D. Golze, M. Dvorak and P. Rinke, Front. Chem. 7, 377 (2019), doi:10.3389/fchem.2019.00377 |
| Quasiparticle self-consistent GW | M. van Schilfgaarde, T. Kotani and S. Faleev, Phys. Rev. Lett. 96, 226402 (2006), doi:10.1103/PhysRevLett.96.226402; T. Kotani, M. van Schilfgaarde and S. V. Faleev, Phys. Rev. B 76, 165106 (2007), doi:10.1103/PhysRevB.76.165106 |
| Constrained RPA | F. Aryasetiawan, M. Imada, A. Georges, G. Kotliar, S. Biermann and A. I. Lichtenstein, Phys. Rev. B 70, 195104 (2004), doi:10.1103/PhysRevB.70.195104; T. Miyake, F. Aryasetiawan and M. Imada, Phys. Rev. B 80, 155134 (2009), doi:10.1103/PhysRevB.80.155134; E. Şaşıoğlu, C. Friedrich and S. Blügel, Phys. Rev. B 83, 121101 (2011), doi:10.1103/PhysRevB.83.121101 |
| Resolution of identity with numeric atom-centred orbitals | X. Ren, P. Rinke, V. Blum, J. Wieferink, A. Tkatchenko, A. Sanfilippo, K. Reuter and M. Scheffler, New J. Phys. 14, 053020 (2012), doi:10.1088/1367-2630/14/5/053020 |
| Low-scaling RPA in imaginary time | M. Kaltak, J. Klimeš and G. Kresse, J. Chem. Theory Comput. 10, 2498 (2014), doi:10.1021/ct5001268 |
| LibRPA | R. Shi, M.-Y. Zhang, P. Lin, L. He and X. Ren, Comput. Phys. Commun. 309, 109496 (2025), doi:10.1016/j.cpc.2024.109496 |
| Padé analytic continuation | H. J. Vidberg and J. W. Serene, J. Low Temp. Phys. 29, 179 (1977), doi:10.1007/BF00655090 |
