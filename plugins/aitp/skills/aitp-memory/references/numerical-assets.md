# Place code, builds and numerical experiments

Use this when numerical development needs a new working location or an existing
project's locations are unclear. First follow the README and current workflow.
These are optional refinements of [asset placement](local-assets.md), not a
directory template to create or a reason to move functioning projects.

| Material | A useful new location | What to keep clear |
| --- | --- | --- |
| Main source checkout | `code/LibRPA/` | The authoritative working source; an existing external checkout can remain there and be linked. |
| Isolated source change | `worktrees/<change>/` | Only when isolation helps; describe its relationship to the main checkout and local edits. |
| Compiled configuration | `builds/<configuration>/` | Cache, build output and executable for one source/configuration; follow existing out-of-source build conventions. |
| Tool environment or package cache | The established, authorized code, development or environment location, which may lie beneath a topic | Not a prose-only reading or note folder merely because it is the current directory; record its requirements and invocation where the experiment or build is described. Installing needs its own authorization. |
| Component tests and reusable fixtures | The source repository's existing test locations | Keep maintainable tests with their code and protected reference data; avoid a second test suite in the topic. |
| A scientific experiment | `calculations/<question>/<run>/` | Inputs, launch script, outputs and analysis that belong to this attempt. |
| Long derivation or implementation explanation | `notes/<question>.md` | The claim and reasoning, linked to relevant code and experiments. |

A run can keep its small files together. If size or workflow needs separation,
use `input/`, `output/` and `analysis/` inside that run, with figures beside their
generating analysis. Create those directories only as needed. A short `report.md`
is useful when outputs do not explain what was compared and what it establishes;
reuse an existing detailed note if it already does so. Distinguish a run report
from the topic's main argument.

For a code comparison, retain the relevant source revision and local changes,
build options, executable actually used, command, intended parameter variation
and observed numerical difference in ordinary prose or the existing run script.
Record the environment details that affect reproduction, rather than copying
the whole machine configuration. Existing Git references are useful; no file
hashes, rigid run identifiers or separate ledger are required by AITP.

Before building or installing, look for an existing suitable environment, as
[computational work](../../aitp-research/references/computational-work.md#environments-caches-and-resumed-work)
describes. An environment is a tool, not research material: it needs no research
entry, and the research notes record only what is needed to recreate it.

Keep a trusted baseline and its inputs intact. Put a new attempt's outputs in
a fresh working location, including unsuccessful attempts whose failure remains
scientifically useful. Do not replace original results with a reformatted report.
Large raw data may remain remote: record host and precise path, how the retained
local analysis relates to it, and any currently unavailable dependency.

Independent questions can use one code checkout and build infrastructure. Give
their scientific runs an intelligible question/run separation and explain the
shared source once in the family README. Each main note links only the evidence
needed for its argument. Sharing code does not require merging cRPA, QSGW and
other independent research questions into one note.

When the work is ready for a paper, `aitp-writing` can use the established
manuscript location after the researcher requests that deliverable. Normal
simulation or note maintenance does not create a manuscript directory.
