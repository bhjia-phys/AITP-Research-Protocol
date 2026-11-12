# Where a file belongs: one quick table

This is the short, shared placement rule used by the AITP skills and by
host adapters (for example a workbench that enforces write locations).
The machine-readable copy is `plugins/aitp/assets/placement-rules.json`;
change both together.

## Directory roles

| Location | Holds |
| --- | --- |
| `research.md`, `README.md` | The living scientific argument and the map of actual material locations. Independent subquestions have their own homes. |
| `plan/<stage>/` | An open stage's design and any stage-owned developing argument. The plan links to the question, foundations, literature method, benchmarks and dependencies. |
| `archive/<stage>/` | A closed stage's design and qualified outcome, including useful negative results or stopped routes. Archiving does not establish a proof. |
| `notes/` | Derivations, reading explanations and discussions, including cross-stage arguments and established supporting notes (Markdown). |
| `references/` | Literature itself: PDF, bib, ris. Not notes. |
| `code/` | Reusable implementation, analysis and post-processing scripts. |
| `calculations/<question>/<run>/` | One attempt: submit script, inputs, logs, outputs, short report. Free-form inside. |
| `data/` | Raw data (`raw/`, read-only) and derived data (`derived/`). |
| `figures/` | Figures retained for presentation; keep their generating analysis and source data reachable. Working figures can stay with their analysis. |
| `manuscripts/` | Paper and lecture TeX sources, bibliography, build assets. |
| `reports/` | Group-meeting/talk material, dated. |
| `results/`, `workspace/`, `sources/`, `scripts/`, `theory/`, `manuscript/`, `development/`, `software/`, `analysis/`, `runs/`, `skills/` | Existing or question-specific working homes. Reuse established locations; consult the owning method or asset guidance before creating a new one. |

These are material roles, not a directory tree to generate. The
[plan/archive lifecycle](plans.md) owns stage design, closure, pauses and link repair.
Shared [knowledge](shared-knowledge.md) and reusable Skills can serve several questions;
link their established homes rather than copying them into each stage. A question's
folder nesting records working ownership, not every scientific dependency.

## Extension routing

- Code and scripts (`.py .sh .c .cpp .f90 .jl .go .js .ts .ipynb .sbatch …`) → `code/` or `calculations/<run>/`.
- Data (`.csv .tsv .json .h5 .npy .npz .dat .xml .out .log …`) → `data/`, `results/`, or `calculations/<run>/`.
- Literature (`.pdf .bib .ris`) → `references/`; an authored PDF or plotted figure keeps its manuscript or analysis role instead.
- Paper/lecture sources (`.tex .sty .bst`) → `manuscripts/`.
- Note that `calculations/<run>/` is intentionally free-form: one run keeps its own inputs, script, logs and outputs together.

## Rules of thumb

- A script used once stays with its run; a script used twice moves to `code/`.
- A figure lives with the analysis that generates it until a manuscript needs a stable `figures/` path.
- Shell redirection is not a placement mechanism: write research files through the host's file tools, and keep command output inside the run.
- Historical evidence is not rewritten to match a new layout; document its location in `README.md` and link it from `research.md`.
- Keep a paused stage in `plan/`. At closure, move only its stage-owned design and argument together to `archive/`, preserving existing evidence owners and repairing affected links.
