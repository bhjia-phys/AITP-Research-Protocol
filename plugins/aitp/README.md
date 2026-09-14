# AITP

Based on version 1.1.0: article-centred research memory, research and writing guidance,
and direct Skill distillation. The bundle contains instructions and
optional manuscript assets, with no runtime. This development tree adds memory-first
entry, main and supporting note standards, source-based learning, domain methods
and numerical layout guidance beyond
the published 1.1.0 release below. Real research examples are pending review.

Install the versioned release in **Hakimi** with:

```text
/plugins install https://github.com/bhjia-phys/AITP-Research-Protocol/releases/download/v1.1.0/aitp-1.1.0.zip
```

For **Codex**, use the repository marketplace:

```sh
codex plugin marketplace add bhjia-phys/AITP-Research-Protocol --ref v1.1.0
codex plugin add aitp@aitp-protocol
```

Start a new host thread after installation.

- [aitp-memory](skills/aitp-memory/SKILL.md) is the first step for research-topic
  work: locate or create the main note, recover context, establish the current
  task, and decide what understanding to retain after the work.
- [aitp-research](skills/aitp-research/SKILL.md) guides physical reasoning,
  literature use and computational work.
- [aitp-writing](skills/aitp-writing/SKILL.md) develops research notes and,
  when explicitly requested, LaTeX manuscripts for formal theory, numerical
  studies and mixed work, replacing
  the former Witten-style and computational-physics-note writing Skills.
- [aitp-distill](skills/aitp-distill/SKILL.md) extracts and improves a reusable
  procedure directly as a Skill.

The first note and substantive revisions use
[main-note writing](skills/aitp-writing/references/research-note.md): a concise,
connected argument with decisive conditions, useful failures and uncertainty,
linked to full derivations and assets. Start from the English Markdown template
for a [compact argument](skills/aitp-writing/assets/research-letter.md),
[theory or learning](skills/aitp-writing/assets/research-theory.md), or
[computational and mixed work](skills/aitp-writing/assets/research-computational.md).
Their [journal sources](skills/aitp-writing/references/journal-templates.md) explain
what was adapted from PRL, PRX, JHEP and PRB. These are article structures, with
flexible headings and no prescribed length. Memory and writing edit the same account.

[Side investigations](skills/aitp-writing/references/supporting-notes.md#follow-a-side-investigation)
keep their motivation and connection to the originating question, even before
results exist. Reuse an existing topic or supporting note and link dependencies;
keep one primary account rather than nesting or duplicating every branch.

Use [supporting-note writing](skills/aitp-writing/references/supporting-notes.md)
for detailed explanations and [citation conventions](skills/aitp-writing/references/citations.md)
for equations and evidence links. Reusable concepts and theorems can live in an
optional [shared collection outside topics](skills/aitp-memory/references/shared-knowledge.md).
Consult it for an actual need during theoretical derivation or learning, including
theory within numerical work. Check for an existing explanation before creating
a standalone concept or theorem note. A short README entry with related terms
helps another topic find it. Reuse needs no write; retain useful new understanding
at a natural pause. Link prerequisites, related ideas and applications in ordinary
prose, following only what the current argument needs.

For learning, use [learning from sources](skills/aitp-writing/references/learning.md).
The main note explains the developing whole-topic argument; a supporting note
lets its reader follow and use a specific result from stated prerequisites.
Choose whether a passage should support understanding, reproduction or proof.
Expand a primary lecture around concrete difficulties and use reader feedback
to improve the next explanation. A teaching PDF retains that purpose and depth
when using journal typography. These are writing choices, not additional Skills,
required records or automatic proof of understanding.

[Corrections follow affected claims](skills/aitp-writing/references/supporting-notes.md#correct-claims-and-keep-earlier-routes-findable)
across main and supporting notes. Useful material omitted from the main account
can remain linked from an existing README or index. Known errors or unresolved
objections stay visible where the old material is read, with corrected treatment
linked when available. No automatic synchronization or deletion is implied.

Use normal read, search and edit tools. There is no ledger command, adapter
contract, automatic session hook or required service. Host permissions govern
execution and publication. Skills guide behavior; they cannot guarantee activation,
crash recovery or scientific correctness.

For a persistent workspace instruction, a researcher may put the following in
its existing `AGENTS.md`, or state it in the conversation:

> For work on a research topic, first use aitp-memory to locate or establish the
> main note and determine the current task. Reuse that context for follow-ups.
> At completion, retain meaningful changes using aitp-memory and aitp-writing.

This assumes AITP is available in the host. It is optional workspace guidance,
not a new required file. The four Skill descriptions and cross-references request
the same routing; Hakimi also supplies an entry reminder from the plugin manifest.
These are instructions for the agent, not an executable router or session hook.

For a new or unfamiliar topic, use
[starting or organizing a topic](skills/aitp-memory/references/starting-a-topic.md).
Clarify consequential uncertainty before writing around it; use earlier answers
and proceed directly when the scope is clear.
The [example status](examples/README.md) explains the replacement of the former
teaching exercise by reviewable research examples.
[Asset guidance](skills/aitp-memory/references/local-assets.md) explains how the
README locates material and the main argument links detailed notes and their
assets. It offers optional layouts for new topics and shared development;
reuse established locations and create folders only when the work needs them.
For unfamiliar related work, [browse directory entries and note titles first](skills/aitp-memory/references/local-assets.md#browse-nearby-topics-and-shared-knowledge),
then search and read selected notes. Short scope descriptions help choose a note;
known useful links can be followed directly. Reuse the located context within the task.
Its [numerical guidance](skills/aitp-memory/references/numerical-assets.md)
distinguishes working source, optional worktrees, builds, tests and scientific
runs. General procedures live in the research Skill's
[domain library](skills/aitp-research/references/method-library.md), starting with
[developing LibRPA](skills/aitp-research/methods/librpa/developing-librpa/SKILL.md)
for source analysis and numerical development.
They are linked for reading on demand, without another registry. Codex can also
list nested method Skills directly; Hakimi exposes the four containing bundles.
The four core roles therefore need not equal the host's total selectable count.
Research examples and unpublished evidence follow the author's publication
permissions; adding a general method does not publish its originating project.
See the [repository README](https://github.com/bhjia-phys/AITP-Research-Protocol/tree/v1.1.0)
for further usage guidance.
