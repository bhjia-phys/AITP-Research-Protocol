# Scientific argument writing cases

Five small, self-contained development cases cover manuscript organization,
unsupported conclusions, motivation of a definition, exemplar transfer and an
already-clear negative control. They add no runtime or required research artifact.
The physical materials are synthetic; W04 includes a labelled paraphrase of a
located original source. No private research inputs are included.

For actual prose, rendered figures, numerical tables and executable figure generators,
use [writing v0.2](../writing-v0.2/README.md), which retains separate scientific and
communication judgments and adds a transfer case and evaluator controls.

Give an executor only the requested case files in `cases/`, the same resource
limits, and the guidance allowed by its condition. The cases can be run separately
or in one batch; report which, and do not treat answers from one batch as independent
sessions. Keep this README and [grading guidance](evaluator.md) away from the executor.
Ask for answers in chat; no computation, manuscript files, network or installation
is needed. Preserve the initial materials and all outputs outside the public tree.

Compare a plain baseline, a frozen current AITP snapshot and the revised snapshot
with the same model, reasoning settings, tools, cases and budget. Freeze actual
loaded files, not just HEAD when the tree is dirty. Exclude host memory, Skills
catalogs and parent instructions from the plain baseline, or report the contamination.
Keep explicit-guidance trials distinct from natural Skill-discovery tests. See
[the existing comparison rules](../general-v0.1/README.md#分开测三种条件).

Use the two separate evaluator scores and located reasons; retain failures and
uncertain judgments. These are public development cases, so subsequent scores on
them are regressions rather than evidence of unseen-task generalization. Use a
different physical instance before claiming transfer. Current observations and
their limits belong in [validation](../../docs/validation.md), not in executor input.
