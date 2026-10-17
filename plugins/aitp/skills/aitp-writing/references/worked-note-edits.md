# Worked edits to a living main note

All examples are synthetic. The filenames below illustrate destinations inside
a topic; they do not require those files in every project. Each quoted passage
is the text at that destination, before or after the new evidence.

## Computational: a faster calculation misses the accuracy boundary

The question is whether a reduced method preserves the reference target energy
within 0.01 energy units while reducing elapsed time. At fixed input, the
reference takes 100 s and the reduced method takes 60 s, but their energies
differ by 0.04. Replace the pending comparison in `research.md`:

**Before**

> The reduced method is our candidate accuracy-preserving acceleration. The
> fixed-input comparison is pending. Next, measure its time and energy error.

**After**

> The reduced method fails this comparison's 0.01 energy tolerance: it changes
> the target by 0.04 while reducing elapsed time from 100 to 60 s. It therefore
> does not establish an accuracy-preserving speedup. The original method remains
> the reference. The inputs and measurements are in `fixed-input-report.md`,
> “Reduced versus reference”. Whether a less severe reduction meets the tolerance
> remains open; that requires a new controlled comparison.

At `fixed-input-report.md`, keep the original plan and add the actual observation:

**Before**

> Planned control: one input, same machine and process layout, identical solver
> stopping criterion; vary only the reduction. Accept an absolute target-energy
> difference at most 0.01. Timing ends when the target energy is written.

**After, following the retained plan**

> Synthetic measurement: input `sample-A`, reference implementation `full-v1`,
> reduced implementation `reduced-v1`, one process and one thread on the same
> worker. Both use residual tolerance 1e-8. The reference gives 2.00 in 100 s;
> the reduced calculation gives 2.04 in 60 s. These are single measurements,
> without a timing-variance estimate. The observed factor 100/60 does not meet
> the declared accuracy condition. The plan above records the original intent.

If the opening had said “The reduced method supplies an accuracy-preserving
acceleration”, replace it with “The tested reduction is faster but misses the
energy tolerance; the full method remains the reference.” An opening that only
states the question needs no such correction. Remove the resolved instruction
to obtain the first comparison. A subsequent poll returning these same values
and no new failure produces **no write**, including no appended poll summary.

## Formal: a failed descent and a surviving lemma

Let $M:\mathbb R^2\to\mathbb R$, $M(x,y)=x$, and let $T(x,y)=(y,x)$.
The proposed operator $\bar T$ on the boundary image would obey
$\bar T M=MT$. Replace the application in `research.md`:

**Before**

> Swapping the two bulk coordinates induces a boundary symmetry because the
> boundary map is surjective. We use that symmetry to identify boundary states.

**After**

> The swap does not induce a boundary operator. The bulk vector $(0,1)$ has
> zero boundary image, but its swapped image has boundary value one; an operator
> on the boundary cannot send zero to both zero and one. Surjectivity alone is
> insufficient. The conditional descent lemma survives, but this application
> fails its kernel-preservation hypothesis; see `boundary-descent.md`, “Descent
> criterion”. Boundary states cannot be identified by this swap.

At `boundary-descent.md`, “Descent criterion”:

**Before**

> Define $\bar T(Mv)=MTv$. Since $M$ is onto, this defines the desired operator.

**After**

> For linear $M:V\to W$ and $T:V\to V$, an induced linear operator on
> $\operatorname{im}M$ exists exactly when $T(\ker M)\subseteq\ker M$.
> If $Mv=Mv'$, their difference is in $\ker M$. Kernel preservation makes
> $MTv=MTv'$, so $\bar T(Mv)=MTv$ is independent of the chosen representative.
> Conversely, $\bar T M=MT$ implies $MTv=0$ for every $v\in\ker M$.
> Surjectivity extends this definition to all of $W$; it does not prove
> representative independence. For the swap, $M(0,1)=0$ while $MT(0,1)=1$,
> so the criterion fails.

Retain the old step under “Earlier surjectivity argument” in that same note:

> The earlier definition used a preimage for every boundary vector and concluded
> that surjectivity was sufficient. It overlooked that different preimages must
> give the same answer. The existence of preimages remains useful; the missing
> condition is preservation of the kernel, proved above. This route reopens for
> an operator satisfying that condition, not for the present swap.

Search both links to the derivation and terms such as “boundary swap”,
“coordinate exchange” and “sector identification”. Open plausible applications
even when they have no link to the derivation. In `boundary-sectors.md`, replace:

**Before**

> The boundary swap identifies these sectors, by the induced bulk exchange.

**After**

> The proposed bulk exchange does not descend, so it supplies no identification
> of these boundary sectors. The conditional criterion in `boundary-descent.md`
> remains valid. A sector identification would need a separately justified
> operator preserving the boundary kernel.

The main opening and conclusion must carry the same restriction if they used
the failed identification. Keep frozen editions unchanged; qualify maintained
uses, including a provisional knowledge-index pointer if present. Name a known
application left outside the editing scope instead of claiming it was repaired.

## Multi-thread: a branch changes its next step, then its answer

A topic note `research.md` asks how strongly a model's local interaction depends on the
screening that is excluded. Its branch `screening/research.md` owns the convergence of that
interaction with the k-point mesh. The parent's Current work carries a pointer entry:

> - **Mesh convergence → screening branch** (`screening/research.md`, Current work) —
>   supplies the interaction used in the comparison section; values are from a 4×4 mesh,
>   and their convergence is untested.

**The next step changes.** The branch's 6×6 run is cancelled by a queue limit and
resubmitted. Only the branch's entry changes, with its new date; the cancellation goes to
the run report.

> - **6×6 comparison** — waiting on run · 2026-03-07. The 4×4 interaction is 2.1 energy
>   units; its convergence is untested. Next: compare with the resubmitted 6×6 run under
>   the same inputs. Run report: `runs/mesh-6x6.md`.

The parent's pointer, opening and account stay unchanged: the thread's contribution and
limiting condition did not change.

**The answer changes.** The 6×6 run gives 2.4, outside the 0.1 tolerance that the parent's
comparison assumed. The branch revises its account and its entry:

> - **Mesh convergence** — active · 2026-03-09. The interaction moves from 2.1 at 4×4 to
>   2.4 at 6×6, beyond the 0.1 tolerance, so the 4×4 value is not converged. Next: an 8×8
>   run to bound the remaining change. Comparison: `screening/mesh-comparison.md`.

The parent's limiting condition changed, so its pointer and the passage that used the
value change together:

> - **Mesh convergence → screening branch** (`screening/research.md`, Current work) —
>   supplies the interaction for the comparison section; the 4×4 value is not converged
>   (2.4 at 6×6), so that comparison is provisional.

> The comparison with the reference interaction uses the 4×4 value and is provisional:
> the value changes by 0.3 at 6×6 (`screening/mesh-comparison.md`).

If the parent's opening stated the comparison as a result, its qualification changes too.
When the 8×8 run finishes but has not been analyzed, the branch entry says `waiting on
analysis`, and the parent's comparison passage names that pending result until it is
integrated. The parent never records the 8×8 job state or the branch's next run.

## A short analytic note stays short

A question answered by one derivation needs an opening and its argument. With nothing
live, there is no Current work section and no decisions list:

> # Does the coordinate swap descend to the boundary?
>
> For linear $M:V\to W$ and $T:V\to V$, an induced operator on $\operatorname{im}M$ exists
> exactly when $T(\ker M)\subseteq\ker M$. The swap of the two bulk coordinates fails this
> criterion, so it induces no boundary operator and identifies no boundary sectors.
>
> The criterion, its proof and the earlier surjectivity argument it corrects are in
> `boundary-descent.md`. What survives the failed application is the conditional
> criterion; an operator that preserves the boundary kernel would reopen the question.
