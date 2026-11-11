Write a short scientific methods note in English from the accompanying materials and CSV files. Its audience knows linear response but should not need to inspect your code to understand the conclusion. The note should connect the scalar screening model, numerical approximation, quantitative results, and choice of implementation for a specified workload in one coherent argument. Keep it approximately 700–1100 words, excluding the numerical table and caption.

Create these three deliverables in the output directory supplied by the runner, or in `./output/` if none is supplied:

- `article.md`, including displayed equations, one numerical table written directly in Markdown, result prose, and an embedded relative link to the figure;
- `convergence.png`, a readable figure with two panels: convergence versus the number of midpoint cells, and total cost versus the number of repeated evaluations;
- `plot_convergence.py`, a runnable Python generator for that figure using the supplied CSV files and the analytic model. It must accept `--data-dir` and `--output-dir` arguments, and must reproduce the submitted PNG without manual changes.

Use Python 3, NumPy, Matplotlib, and the standard library already available locally. Do not install anything, browse the web, cite external literature, or time new calculations. The supplied timing data are synthetic observations for this controlled exercise and must remain identified as such. You may recompute the quadrature to check the supplied numerical data.

Derive an analytic reference from the model, separate finite-cutoff and quadrature errors, and assess the corrected estimator against the requested absolute accuracy. The Markdown table must cover every supplied grid and report the raw estimate, the estimate with the analytic tail restored, and their absolute errors relative to the full integral. Give enough digits to judge the requested tolerance. Discuss agreement between the two implementations separately from these errors. State a supported positive numerical result and a supported statement about screening in this model, with their scope made clear.

Use the supplied setup and evaluation measurements to compare the two implementations at equal numerical accuracy. Explain what changes between a single evaluation and a reused setup, quantify the crossover in the number of evaluations, and relate the plotted costs to the same convention. Close with a concrete implementation choice for the two workloads specified in the materials.

For the convergence-panel caption, retain this checked fragment unchanged if it remains applicable to your figure. If your design makes it inaccurate, explain the reason for changing it in a short note after the caption:

> The horizontal cutoff line is the analytic contribution from frequencies above the cutoff. It is independent of the number of midpoint cells, so refinement at fixed cutoff cannot remove it.

The finished article should stand alone. Identify which conclusions are exact properties of the model, which are established by the supplied calculations, and which depend on the synthetic timing convention, without turning the note into a checklist.
