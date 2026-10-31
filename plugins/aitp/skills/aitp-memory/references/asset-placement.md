# Where a file belongs: one quick table

This is the short, shared placement rule used by the AITP skills and by
host adapters (for example a workbench that enforces write locations).
The machine-readable copy is `plugins/aitp/assets/placement-rules.json`;
change both together.

## Directory roles

| Location | Holds |
| --- | --- |
| `research.md`, `README.md` | The living note and the material map; nothing else at the topic root. |
| `notes/` | Derivations, reading notes, plans, meeting discussions (Markdown). |
| `references/` | Literature itself: PDF, bib, ris. Not notes. |
| `code/` | Reusable implementation, analysis and post-processing scripts. |
| `calculations/<question>/<run>/` | One attempt: submit script, inputs, logs, outputs, short report. Free-form inside. |
| `data/` | Raw data (`raw/`, read-only) and derived data (`derived/`). |
| `figures/` | Final figures only; they must be rebuildable from code or a run. |
| `manuscripts/` | Paper and lecture TeX sources, bibliography, build assets. |
| `reports/` | Group-meeting/talk material, dated. |
| `results/`, `workspace/`, `sources/`, `scripts/`, `theory/`, `manuscript/`, `development/`, `software/`, `plan/`, `analysis/` | Existing historical names. Reuse them where they already hold work; do not create them for new work. |

## Extension routing

- Code and scripts (`.py .sh .c .cpp .f90 .jl .go .js .ts .ipynb .sbatch …`) → `code/` or `calculations/<run>/`.
- Data (`.csv .tsv .json .h5 .npy .npz .dat .xml .out .log …`) → `data/`, `results/`, or `calculations/<run>/`.
- Literature (`.pdf .bib .ris`) → `references/`.
- Paper/lecture sources (`.tex .sty .bst`) → `manuscripts/`.
- Note that `calculations/<run>/` is intentionally free-form: one run keeps its own inputs, script, logs and outputs together.

## Rules of thumb

- A script used once stays with its run; a script used twice moves to `code/`.
- A figure lives with the analysis that generates it until a manuscript needs a stable `figures/` path.
- Shell redirection is not a placement mechanism: write research files through the host's file tools, and keep command output inside the run.
- Historical evidence is not rewritten to match a new layout; document its location in `README.md` and link it from `research.md`.
