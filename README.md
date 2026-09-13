# AITP

AITP helps a research topic develop into a coherent, evidence-supported argument
across sessions. Its memory is an editable article with links to derivations,
code, calculations, references and figures. The agent reads and edits ordinary
files with the host's existing tools.

AITP currently has three parts:

| Part | What it does |
| --- | --- |
| [Memory](plugins/aitp/skills/aitp-memory/SKILL.md) | Understand the complete main note, recover its question and evidence, and integrate consequential changes into the argument. |
| Research skills | [aitp-research](plugins/aitp/skills/aitp-research/SKILL.md) guides physical reasoning, literature use and computation; [aitp-writing](plugins/aitp/skills/aitp-writing/SKILL.md) develops explanations and manuscripts for formal, computational and mixed work. |
| [Learning](plugins/aitp/skills/aitp-distill/SKILL.md) | Extract a demonstrated reusable procedure directly into a Skill; test and improve it through use. |

A separate **AITP taste** component and further extensions remain to be designed.
The dedicated writing Skill replaces the former `witten-style-theory-note`
and absorbs `computational-physics-note`.
Writing and research guidance do not constitute the future taste component.

## A topic is a developing article

Start with `research.md` (or an established TeX main note). Read the whole
argument before a substantive revision. Follow supporting links as needed.
When a result changes the answer, assumptions or next scientific decision,
revise the relevant passages together. Keep useful failed routes and unresolved
objections. An ordinary question or unchanged job poll needs no memory write.

The README briefly explains established material locations. The main note
develops the argument through linked research notes; those notes connect the
relevant derivations, literature, code, data and figures. Direct asset links
remain useful. Independent questions can share code and data in one primary
location. Reuse existing working locations, and update the README when that
navigation changes. AITP does not prescribe a directory tree or a file inventory.
See [asset placement and links](plugins/aitp/skills/aitp-memory/references/local-assets.md)
and the [recording examples](docs/when-to-write.md) for decisions during research.

No Python runtime, ledger CLI, knowledge-card layer, hash protocol, index,
MCP service, hook or background daemon is part of AITP. Git is ordinary source
version control, not a required research-memory protocol. Reading a note does
not certify its scientific correctness or authorize its recorded next action.

## Use and installation

Install [AITP 1.1.0](https://github.com/bhjia-phys/AITP-Research-Protocol/releases/tag/v1.1.0).
Codex and Hakimi expose the same four core Skills and one small teaching example.

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

Use `aitp-writing` to explain, draft or revise the scientific argument. It keeps
the former Witten-style emphasis on faithful examples, explicit central
derivations and assumptions at their point of use. Formal theory follows the
construction or proof; computational work follows the approximation, observable,
controls and result. Its computational guide includes implementation, setup
and benchmark tables from the former computational writing Skill. Mixed work
explains exactly how a numerical test bears on an analytic claim. These are
flexible argument structures, not separate forms.

Research notes keep useful links to working assets. Publication manuscripts use
their appropriate scientific exposition and citations. Existing TeX/PDF sources
remain primary assets, without automatic synchronization or mandatory conversion
of Markdown. The optional JHEP starter and original corpus references are loaded
only when relevant. The [teaching example](plugins/aitp/examples/README.md)
and [validation notes](docs/validation.md) illustrate the guidance and its limits.

## Teaching example

The [oscillator example](plugins/aitp/examples/README.md) contains a main note,
a linked derivation, a small calculation table and one optional distilled Skill.
It is self-contained and uses a textbook problem, with no private research
content or external workstation assets. It demonstrates organization and use,
not superior research performance. See [validation](docs/validation.md) for what
was actually checked and [the transition](docs/transition.md) for the replacement
of the legacy implementation.
