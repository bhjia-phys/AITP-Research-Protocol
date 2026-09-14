# AITP

AITP helps a research topic develop into a coherent, evidence-supported argument
across sessions. Its memory is an editable article with links to derivations,
code, calculations, references and figures. The agent reads and edits ordinary
files with the host's existing tools.

AITP currently has three parts:

| Part | What it does |
| --- | --- |
| [Memory](plugins/aitp/skills/aitp-memory/SKILL.md) | Enter the topic first, locate or establish its main note, recover the argument and current task, and retain consequential changes. |
| Research skills | [aitp-research](plugins/aitp/skills/aitp-research/SKILL.md) guides physical reasoning, literature use and computation; [aitp-writing](plugins/aitp/skills/aitp-writing/SKILL.md) develops explanations and manuscripts for formal, computational and mixed work. |
| [Learning](plugins/aitp/skills/aitp-distill/SKILL.md) | Extract a demonstrated reusable procedure directly into a Skill; test and improve it through use. |

A separate **AITP taste** component and further extensions remain to be designed.
The dedicated writing Skill replaces the former `witten-style-theory-note`
and absorbs `computational-physics-note`.
Writing and research guidance do not constitute the future taste component.

## A topic is a developing article

Begin research-topic work with `aitp-memory`, including derivation, coding and
analysis requests that do not explicitly mention memory. First locate the main
note. If it exists, read its complete argument; if not, establish the question
and working home, then draft a small `research.md`. Existing TeX main notes count,
and scattered research material is not an empty project. Determine the current
session's task from this context and the user's request. Reuse current context
for follow-ups instead of repeating entry on every turn.

For existing work, inspect the main argument and relevant sources;
clarify consequential uncertainty about scope or branch grouping before a
consolidation. Reuse answers already supplied. An agreed exploratory note can
retain open questions without a settled result. See
[starting or organizing a topic](plugins/aitp/skills/aitp-memory/references/starting-a-topic.md)
for the first draft and collaboration guidance.

Use `aitp-research` for the scientific work. At task completion or handoff,
`aitp-memory` decides whether nothing needs recording, only supporting detail
needs updating, or the main argument has changed. `aitp-writing` shapes the first
note and substantive revisions; `aitp-distill` teaches demonstrated reusable
methods from the note and its evidence. These are four roles around one main
account, not four documents or mandatory phases.

Read the whole `research.md` (or established TeX main note) before a substantive
revision. Follow supporting links as needed.
When a result changes the answer, assumptions or next scientific decision,
revise the relevant passages together. Keep useful failed routes and unresolved
objections. An ordinary question or unchanged job poll needs no memory write.

[Side investigations](plugins/aitp/skills/aitp-writing/references/supporting-notes.md#follow-a-side-investigation)
retain their origin, local question, evidence and route back to the larger work.
They can reuse other topics and shared code through links; each detour does not
require a new main note or nested directory tree.

The README briefly explains established material locations. The main note
develops the argument through linked research notes; those notes connect the
relevant derivations, literature, code, data and figures. Direct asset links
remain useful. Independent questions can share code and data in one primary
location. Reuse existing working locations, and update the README when that
navigation changes. New topics have optional layout suggestions; existing work
does not need a prescribed tree or a file inventory.
When related work or shared knowledge is needed, first browse the relevant
directories, README entries and note titles, then read likely candidates. Short
scope descriptions help choose a note; known useful links can be followed directly.
See [asset placement and discovery](plugins/aitp/skills/aitp-memory/references/local-assets.md)
and the [recording examples](docs/when-to-write.md) for decisions during research.

No Python runtime, ledger CLI, knowledge-card layer, hash protocol, search service,
MCP service, hook or background daemon is part of AITP. Git is ordinary source
version control, not a required research-memory protocol. Reading a note does
not certify its scientific correctness or authorize its recorded next action.

## Use and installation

Install [AITP 1.1.0](https://github.com/bhjia-phys/AITP-Research-Protocol/releases/tag/v1.1.0).
Memory-first entry, main and supporting note standards, source-based learning,
domain methods and numerical layouts in
this development tree are newer than that release. Codex and Hakimi expose the
same four core Skills. The release contains the former teaching exercise;
the current research examples are pending review.
Codex can additionally list nested domain methods as selectable Skills; Hakimi
discovers the four containing bundles. The linked method library works in both.

For **Codex**, run in a terminal:

```sh
codex plugin marketplace add bhjia-phys/AITP-Research-Protocol --ref v1.1.0
codex plugin add aitp@aitp-protocol
```

For **Hakimi**, run inside a session:

```text
/plugins install https://github.com/bhjia-phys/AITP-Research-Protocol/releases/download/v1.1.0/aitp-1.1.0.zip
```

Start a new host thread after installation. The attached
[plugin ZIP](https://github.com/bhjia-phys/AITP-Research-Protocol/releases/download/v1.1.0/aitp-1.1.0.zip)
contains an `aitp/` folder with its manifests, Skills, example and license.
Hakimi uses this ZIP; GitHub's automatic source archives contain the full
repository, where the plugin is nested under `plugins/aitp`.

For local development, add this checkout as the Codex marketplace source and
install `aitp@aitp-protocol`, or give Hakimi the absolute path to `plugins/aitp`.
Without installation, an agent can read the memory Skill and the topic's main note.

The repository and marketplace keep their historical names; the product and
plugin are **AITP**, with plugin identifier `aitp`. AITP does not
provide the legacy `aitp` command or native ledger tools. Hosts that implemented
the old adapter must explicitly retire that integration; this is a major-version
replacement, not adapter-contract compatibility.

## Writing

Main notes and supporting notes have different reading requirements. The main
note explains the whole question, decisive argument, supported answer and live
gap; a supporting note develops one result far enough to understand and use it
from stated prerequisites. Links preserve this relationship without replacing
the implication needed in the main text.

[Corrections follow the affected argument](plugins/aitp/skills/aitp-writing/references/supporting-notes.md#correct-claims-and-keep-earlier-routes-findable),
including useful notes no longer cited by the main account. Existing READMEs or
indexes keep those routes discoverable; the notes themselves expose known errors,
unresolved objections and replacement explanations.

For learning, [source-based teaching](plugins/aitp/skills/aitp-writing/references/learning.md)
keeps a primary lecture or paper as the reading thread, expands concrete gaps,
and distinguishes understanding, reproducing calculations and proving imported
theorems. Reader feedback guides later explanations. A learning note may start
small and grow into a synthesis. Journal typography does not change its reader
or justify compressing away the teaching steps.

Use `aitp-writing` to explain, draft or revise the scientific argument. It keeps
the former Witten-style emphasis on faithful examples, explicit central
derivations and assumptions at their point of use. Formal theory follows the
construction or proof; computational work follows the approximation, observable,
controls and result. Its computational guide includes implementation, setup
and benchmark tables from the former computational writing Skill. Mixed work
explains exactly how a numerical test bears on an analytic claim. These are
flexible argument structures with optional Markdown starting files.

For `research.md`, the [main-note guide](plugins/aitp/skills/aitp-writing/references/research-note.md)
provides three English Markdown starting files:
[compact argument](plugins/aitp/skills/aitp-writing/assets/research-letter.md),
[formal theory or learning](plugins/aitp/skills/aitp-writing/assets/research-theory.md),
and [computational or mixed work](plugins/aitp/skills/aitp-writing/assets/research-computational.md).
They use an article's abstract, introduction, central argument and discussion,
with useful failures, uncertainty and linked evidence for continuing research.
The [design and official TeX sources](plugins/aitp/skills/aitp-writing/references/journal-templates.md)
explain the adaptations from PRL, PRX, JHEP and PRB. Keep decisive reasoning in
the main text and extended derivations, implementation and data in linked notes.
The templates impose no journal length limit or claim of completed research.

[Supporting-note guidance](plugins/aitp/skills/aitp-writing/references/supporting-notes.md)
distinguishes concepts, source readings, proofs, methods, calculations and
exploratory branches without imposing document schemas.
[Citation conventions](plugins/aitp/skills/aitp-writing/references/citations.md)
use local equation numbers and meaningful file links; precise rendered anchors
depend on the reader. A [shared theoretical collection](plugins/aitp/skills/aitp-memory/references/shared-knowledge.md)
may live outside individual topics. Consult it when theoretical derivation or
learning needs an explanation; a theoretical term or routine numerical operation
does not trigger a search. Before creating a standalone concept or theorem note,
check the existing entry and relevant notes using names and related terms. Reuse
needs no write. Retain useful new understanding at a natural pause, updating a
short README discovery entry when needed. No database or recursive loading is required.

Research notes keep useful links to working assets. Only an explicit manuscript
request activates the [Note-to-LaTeX guidance](plugins/aitp/skills/aitp-writing/references/manuscripts.md),
including later revisions based on the note. Ordinary note maintenance does not
produce or synchronize a paper. Publication manuscripts use
their appropriate scientific exposition and citations. Existing TeX/PDF sources
remain primary assets, without automatic synchronization or mandatory conversion
of Markdown. The optional JHEP starter and original corpus references are loaded
only when relevant. See [validation notes](docs/validation.md) for the checks
and their limits.

## Methods and research examples

General procedures belong under `aitp-research/methods/<domain>/<method>/SKILL.md`.
The initial [LibRPA development Skill](plugins/aitp/skills/aitp-research/methods/librpa/developing-librpa/SKILL.md)
connects formulas and iteration state to source, and guides build selection and
numerical validation when executing a change. Follow the
[method guide](plugins/aitp/skills/aitp-research/references/method-library.md) for
local and shared methods; no knowledge-card layer is needed. Numerical projects
can use the [asset recommendations](plugins/aitp/skills/aitp-memory/references/numerical-assets.md)
to explain code, builds, tests and run locations in their README.

Proposed LibRPA and topological-phase/anomaly notes are being prepared outside
the public tree for author review. They may be published in part after that
review. The former oscillator exercise is retired from the current example set;
its release snapshot and observations remain historical evidence. See
[example status](plugins/aitp/examples/README.md), [validation](docs/validation.md)
and [the transition](docs/transition.md).
