# AITP

AITP helps a research topic develop into a coherent, evidence-supported argument
across sessions. Its memory is an editable article with links to derivations,
code, calculations, references and figures. The agent reads and edits ordinary
files with the host's existing tools.

AITP currently has three parts:

| Part | What it does |
| --- | --- |
| [Memory](plugins/aitp/skills/aitp-memory/SKILL.md) | The single entry and its research cycle. It keeps the research backbone: a root `research.md` with directions, connections, seeds and standing agreements, and topic and branch notes. It recovers context, places outcomes so that they stay reachable, and closes each task with what is supported and what it warrants next. |
| Research skills | [aitp-research](plugins/aitp/skills/aitp-research/SKILL.md) guides physical reasoning, synthesis across sources, literature, calculations, code, debugging and benchmarks; [aitp-verify](plugins/aitp/skills/aitp-verify/SKILL.md) checks consequential claims and other models' reviews; [aitp-writing](plugins/aitp/skills/aitp-writing/SKILL.md) develops explanations and manuscripts for formal, computational and mixed work. |
| [Method distillation](plugins/aitp/skills/aitp-distill/SKILL.md) | Extract a demonstrated reusable procedure directly into a Skill; test and improve it through use. |

Two conditional interaction Skills work across these parts:
[aitp-human-brainstorming](plugins/aitp/skills/aitp-human-brainstorming/SKILL.md)
helps resolve research intent and consequential choices;
[aitp-human-learning](plugins/aitp/skills/aitp-human-learning/SKILL.md)
adapts explanations to the researcher's conceptual needs and feedback. Neither
adds a mandatory interview, phase or document.

A separate **AITP taste** component and further extensions remain to be designed.
The dedicated writing Skill replaces the former `witten-style-theory-note`
and absorbs `computational-physics-note`.
Writing and research guidance do not constitute the future taste component.

## A topic is a developing article

Begin research work and substantive physics discussions with `aitp-memory` and its
research cycle, including derivation, coding and analysis requests that do not
explicitly mention memory. A discussion needs no topic: its durable outcomes land in
the shared collection, in notes beside the root, or as seeds. First locate the main
note. If it exists, recover the context needed by the request and understand its
complete argument before substantive revision. If none exists, draft a small
`research.md` only for an agreed persistent topic or an authorized consolidation, once
the question and working home are clear; a discussion without a topic uses the root. Existing TeX main notes count,
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
methods from the note and its evidence. The two human interaction Skills help
when a consequential choice or learning need arises, and `aitp-verify` checks a
consequential claim before it is relied on. All seven roles work around the same
backbone, without requiring seven documents or mandatory phases.

Read the whole `research.md` (or established TeX main note) before a substantive
revision. Follow supporting links as needed.
When a result changes the answer, assumptions or next scientific decision,
revise the relevant passages together. Keep useful failed routes and unresolved
objections. An ordinary question or unchanged job poll needs no memory write
when the relevant account is already usable.

When use exposes a material gap in an older main note, memory and writing
[repair it in place](plugins/aitp/skills/aitp-memory/SKILL.md#repair-an-outdated-main-note-during-use)
within the current editing scope, without a separate maintenance request.
This can improve the retained argument even without a new scientific result.
Preserve complete useful reasoning, evidence and history. Judge actual meaning,
not exact template headings or a Skill version; a usable note and an unchanged
revisit need no rewrite. Explicit read-only scope still applies. The upgrade
happens while the topic is used, not when the plugin is installed or in the background.

[Side investigations](plugins/aitp/skills/aitp-writing/references/supporting-notes.md#follow-a-side-investigation)
retain their origin, agreed objective and approach, evidence and route back to
the larger work. Before an independent branch or a material change of stage
objective or research route, `aitp-research` discusses the choice and obtains
agreement; work inside an existing agreement continues without repeated
confirmation. `aitp-memory` preserves the agreement and its reasons in the
branch's `research.md`, and `aitp-writing` develops the account with links to
plans, implementation and results. An agreed independent research branch gets
its own folder and main note unless a suitable home already exists; a short
diagnostic can stay in the current account. Branches can reuse other topics and
shared code through links without forcing nested directories.

The README maps the established folder architecture, including branch folders
and shared working locations. The originating and branch main notes link each
other and explain whether the branch is a prerequisite, alternative or independent
spin-off, and what its result means for the larger question. The main note
develops the argument through linked research notes; those notes connect the
relevant derivations, literature, code, data and figures. Direct asset links
remain useful. Independent questions can share code and data in one primary
location. Reuse existing working locations, and update the README when that
navigation changes. New topics have optional layout suggestions; existing work
does not need a prescribed tree or a file inventory. Within authorized organization,
the agent can infer clear branch relationships and create or reuse their folders
and notes. It asks only when unresolved human intent would change that structure
or scientific scope. The main note should explain which branch advances which
part of the question, and what next inference could change the answer.
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
The research backbone and cycle, verification, computational and benchmark procedures,
main and supporting note standards, source-based learning, domain methods and numerical
layouts in this development tree are newer than that release. This development tree
exposes seven core Skills to Codex, Claude Code and Hakimi; the published release has four.
The release contains the former teaching exercise; the current research examples
are pending review. Codex and Claude Code additionally expose the LibRPA domain
method as a selectable Skill; Hakimi discovers the containing bundles. The linked
method library works in all three.

For **Codex**, run in a terminal:

```sh
codex plugin marketplace add bhjia-phys/AITP-Research-Protocol --ref v1.1.0
codex plugin add aitp@aitp-protocol
```

For **Hakimi**, run inside a session:

```text
/plugins install https://github.com/bhjia-phys/AITP-Research-Protocol/releases/download/v1.1.0/aitp-1.1.0.zip
```

For **Claude Code**, install this development checkout from its repository root:

```sh
claude plugin marketplace add .
claude plugin install aitp@aitp-protocol --scope user
```

Claude support is in this checkout, not the published `v1.1.0` release.
The [Claude Code guide](docs/claude-code.md) explains the shared Skill layout,
natural-language use, verification and updates.

Start a new host thread after installation. The attached
[plugin ZIP](https://github.com/bhjia-phys/AITP-Research-Protocol/releases/download/v1.1.0/aitp-1.1.0.zip)
contains an `aitp/` folder with its manifests, Skills, example and license.
Hakimi uses this ZIP; GitHub's automatic source archives contain the full
repository, where the plugin is nested under `plugins/aitp`.

For local development, add this checkout as the Codex marketplace source and
install `aitp@aitp-protocol`, use the Claude Code commands above, or give Hakimi
the absolute path to `plugins/aitp`.
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

[Close reading](plugins/aitp/skills/aitp-writing/references/learning.md#read-a-source-closely)
works in two passes:
1. A skeleton reading maps the source's chain of questions.
2. Section notes follow the argument step by step, including claims made only in prose.
   Hard steps are filled in under a "try first" prompt, notable details and compressions
   are recorded, and the reader's own sticking points come first.

A learning topic's single main note can be told as a story of questions. When the
researcher chooses authors to learn from, [exemplar authors](plugins/aitp/skills/aitp-research/references/exemplar-authors.md)
keeps an index of their moves and a record of how they organize a paper, in the
researcher's own collection. AITP has no default author.

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
depend on the reader.

A [shared theoretical collection](plugins/aitp/skills/aitp-memory/references/shared-knowledge.md)
may live outside individual topics. It holds:
- atoms: one concept, theorem, technique, example or result each;
- source readings: a paper map plus section notes;
- stories for learning topics;
- optional author collections.

One index lists these by area. At the start of a theoretical derivation, a conceptual
question, or a reading or study task, read that index once and open the entries the task
needs. After that, a theoretical
term or a routine numerical operation does not trigger another search. Before creating an
atom, check the existing entry and relevant notes using names and related terms. Reuse
needs no write.

Most entries come from research. At a natural pause, and whether or not a lookup was
needed, retain an explanation, technique, derivation or correction that another question
could use beyond the topic, with its assumptions stated. It enters as an index row that
cites the research note and names the question rather than restating the result, marked
provisional. The research note stays the single home, so its
corrections apply at once. A shared atom is written from it only after the researcher
confirms the result. Review rows when their cited note changes; update only affected
locations, scope, support, review state or qualifications. A link check reports stale
targets. The collection's kinds are a vocabulary, not a
directory layout. No database or recursive loading is required.

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

After consequential work, notice transferable choices, diagnostic sequences,
failure-prevention methods and corrections to existing procedures. Use
`aitp-distill` to create or revise a local Skill within the authorized scope.
One worked case can support a narrow method with explicit evidence and limits;
an explicit distillation request or repeated failure is not required. Concepts
and theorems remain explanations. No new learning means no additional write;
retaining a local method does not install or publish it.

Proposed LibRPA and topological-phase/anomaly notes are being prepared outside
the public tree for author review. They may be published in part after that
review. The former oscillator exercise is retired from the current example set;
its release snapshot and observations remain historical evidence. See
[example status](plugins/aitp/examples/README.md), [validation](docs/validation.md)
and [the transition](docs/transition.md).

[Research-use feedback](docs/feedback.md) records observed workflow failures,
recovery and proposed improvements separately from validated behavior changes.

The [general research-work benchmark](benchmarks/general-v0.1/README.md) provides
12 small synthetic tasks with separate evaluator expectations for recall,
argument revision, research choices, method learning and evidence handling.
It is a static development and regression set, outside the installed plugin;
actual runs and private research evaluations are kept outside the published tree.
The separate [on-use revision exercise](benchmarks/on-use-v0.1/README.md) checks
automatic repair of an outdated main note, an unchanged revisit and read-only scope.
The [human-interaction cases](benchmarks/human-interaction-v0.1/README.md) check
authorized branch organization, an unresolved research choice, complete teaching
delivery and a learner's valid objection. Each has explicit behavioral expectations;
[validation](docs/validation.md#installed-plugin-discovery-2026-09-27) distinguishes
explicit-loading trials from installed-plugin discovery observations. These small
tests establish neither actual human understanding nor general activation reliability.
