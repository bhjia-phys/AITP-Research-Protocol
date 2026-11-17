# Worked paper edits: weak and repaired exposition

These pairs show the [paper plan](paper-design.md) and the
[exposition passes](exposition-review.md) on short passages. Standard physics (anomaly
inflow, the TKNN formula, Kato's theorem) is stated as published; results labelled
hypothetical are invented to show the form of a claim and are not findings. Each repair
changes the reasoning the reader receives, not only the wording.

## An introduction that lists topics, and one that poses a question

Weak:

> Topological phases of matter have attracted enormous interest in recent years [1–25].
> Anomalies play a central role in quantum field theory, and anomaly inflow has been
> studied extensively. In this paper we study anomaly inflow in Chern–Simons theory with
> a boundary. We first review Chern–Simons theory, then compute the boundary variation,
> and finally discuss the edge modes.

Repaired:

> A (1+1)-dimensional theory of chiral fermions coupled to a background U(1) gauge field
> cannot be gauge invariant on its own: under a gauge transformation its effective action
> changes by a term proportional to the difference between the squared charges of left-
> and right-movers. In a quantum Hall system this is not an inconsistency, because the
> edge is the boundary of a bulk whose Chern–Simons action changes by a boundary term
> that cancels the edge anomaly [Callan–Harvey]. The cancellation fixes the edge's anomaly
> coefficient, but not edge modes that carry none, such as a counter-propagating pair of
> equal charge. *The paper's specific question and its answer, with the condition under
> which it holds, follow here.*

What changed: the opening states what fails and why it is resolved, then what the known
mechanism leaves undetermined, which is where a new question can enter. The list of
topics and the itinerary are gone.

## Results side by side, and an argument

Weak:

> Section 3 computes the entanglement entropy of the ground state. Section 4 computes the
> entanglement spectrum. Section 5 presents numerical results for larger systems.

Repaired (hypothetical results):

> The entanglement entropy cannot distinguish the two candidate phases: both obey an area
> law with the same subleading constant within our resolution (Sec. 3). The entanglement
> spectrum can, because in a topological phase its low-lying levels reproduce the
> counting of the edge theory (Sec. 4). Section 5 tests this prediction at sizes $L\ge 16$,
> where the two candidate countings first differ.

What changed: each section now answers a question created by the previous one, and the
numerics are aimed at the one place where the explanations make different predictions.

## Numerical support stated as proof, and calibrated

Weak (hypothetical model):

> We have shown that the gap closes at $g_c=1.32$, proving that the transition is
> continuous.

Repaired:

> For $L\le 24$ the finite-size gap at $g=1.32$ decreases as $L^{-1.00\pm0.03}$ (Fig. 2),
> as expected at a continuous transition with dynamical exponent $z=1$, and the crossings
> of $L\,\Delta E$ locate $g_c=1.32(1)$. These sizes cannot exclude a weakly first-order
> transition whose correlation length exceeds $L=24$.

What changed: the claim is limited to the sizes studied, the inference from scaling to
continuity is stated as consistency with a prediction, and the alternative that the data
cannot exclude is named.

## An equation with no role, and one that does work

Weak:

> The Hall conductivity is given by
> $$\sigma_{xy}=\frac{e^2}{h}\frac{1}{2\pi}\int d^2k\,F_{xy}(k). \tag{7}$$
> Using Eq. (7) we obtain $\sigma_{xy}=e^2/h$ for our model.

Repaired:

> We need to know whether the Hall conductance can change while the gap stays open. For a
> band insulator at zero temperature the Kubo formula reduces to an integral of the Berry
> curvature $F_{xy}=\partial_{k_x}A_y-\partial_{k_y}A_x$ of the occupied Bloch states, with
> $A_j=i\sum_{n\in\mathrm{occ}}\langle u_n|\partial_{k_j}u_n\rangle$ [TKNN]:
> $$\sigma_{xy}=\frac{e^2}{h}\,C,\qquad C=\frac{1}{2\pi}\int_{\mathrm{BZ}}d^2k\,F_{xy}(k), \tag{7}$$
> in the sign convention of the cited reference. Because the Brillouin zone is a closed
> surface, $C$ is an integer, the first Chern number of the occupied bands, and it can
> change only where the gap closes. For our model $C=1$ (Appendix B), so
> $\sigma_{xy}=e^2/h$ throughout the gapped region containing $g=0$.

What changed: the display answers a stated question; its symbols, convention and
conditions (insulator, zero temperature, occupied bands) are given; the text says what
the formula makes visible, integrality, and where it stops applying.

## A novelty claim, and a stated difference

Weak:

> We develop a novel and powerful framework that, for the first time, solves the problem
> of Majorana splitting in disordered wires.

Repaired (hypothetical result):

> In a clean chain the splitting of the end modes follows from the transfer matrix of the
> Bogoliubov–de Gennes equations [refs]. We use the same transfer matrix. What is new is a
> bound on its Lyapunov exponent for bond disorder that holds for each realization
> (Sec. 3), so the decay length follows without averaging over disorder. We are not aware
> of an earlier bound of this kind.

What changed: the reader learns exactly what is reused and what is added, and the
novelty statement is no stronger than the recorded literature search allows.

## A conclusion that restates, and one that synthesizes

Weak:

> In this paper we studied the disordered Kitaev chain. We computed the splitting and
> presented numerical results. Our results may have important implications for
> topological quantum computation.

Repaired (hypothetical results):

> The splitting decays exponentially in $L$ wherever the realization-wise bound of Sec. 3
> holds, with a decay length set by the Lyapunov exponent of each realization rather than
> by the disorder average. The bound fails near the clean-chain transition, where the
> numerically observed decay length grows faster than the bound allows (Fig. 4). Whether
> it diverges at the clean critical point is the question this method cannot settle.

What changed: the ending says what holds and under which condition, where the argument
stops, and which specific question remains; the unsupported claim of implications is gone.

## Polishing that upgrades a conjecture, and polishing that keeps it

The research note says:

> Numerically the ratio is $1.999\pm0.003$ for $L\le16$. I conjecture it is exactly 2, but I
> have no argument that the $1/L$ correction vanishes. Researcher: the $L=14$ point is off
> trend; check the boundary conditions.

Unfaithful polish:

> The ratio equals 2, as confirmed numerically (Table II).

Faithful polish:

> For $L\le16$ the ratio is $1.999\pm0.003$ (Table II). We conjecture that it equals 2
> exactly. We have no argument that the $1/L$ correction vanishes, and the $L=14$ value lies
> off the trend of the other sizes, possibly because of the boundary conditions; a $1/L$
> coefficient below $10^{-2}$ cannot be excluded at these sizes.

What changed: the conjecture stays a conjecture, and the researcher's objection survives
in the paper's terms instead of disappearing in the rewrite.

## A theorem without hypotheses, and one at the resolution of its proof

Weak:

> **Theorem 1.** The Hamiltonian $H$ is self-adjoint.

Repaired:

> **Theorem 1.** Let $V=V_1+V_2$ be real-valued with $V_1\in L^2(\mathbb R^3)$ and
> $V_2\in L^\infty(\mathbb R^3)$. Then $H=-\Delta+V$ is self-adjoint on
> $D(H)=H^2(\mathbb R^3)$ and bounded below.

> This is Kato's theorem (see Reed and Simon, vol. II). It covers the Coulomb potential:
> $1/|x|$ restricted to $|x|<1$ is square integrable in three dimensions, and the rest is
> bounded.

What changed: the statement names the space, the class of potentials, the domain and the
conclusion, so the proof is not asked to recover hypotheses the theorem left out, and the
remark shows the physical case the hypotheses were chosen to include.

## A transition word without an inference, and the inference

Weak:

> The variation of the bulk action reduces to the boundary term (9). Moreover, the edge
> theory is anomalous.

Repaired:

> The variation of the bulk action reduces to the boundary term (9). This term has the
> form of the edge gauge anomaly (5) with the opposite sign when the Chern–Simons level
> equals the edge's anomaly coefficient, so the two cancel: the combined system is gauge
> invariant although neither part is.

What changed: "moreover" joined two facts; the repair states the relation between them,
which is the point of the paragraph.
