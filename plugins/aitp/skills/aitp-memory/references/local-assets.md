# Locate and connect research assets

Use this when deciding where to save research material, clarifying an unfamiliar
location, or carrying out a requested move. Start with the existing README and
nearby related work. Reuse a useful established location; directory names and
physical separation do not determine the structure of the scientific argument.

## Browse nearby topics and shared knowledge

When another topic may contain useful work, a branch may already have a home,
or a shared explanation is needed, first locate the relevant topic family or
knowledge collection through workspace instructions and README links. If no
entry is known, briefly inspect the current and nearby parent directories
before asking for a location or inventing a new home.

For an unfamiliar location, start with directory names, shallow Markdown filenames,
README entries and candidate note titles and scope descriptions. For example,
use `rg --files --max-depth 2 -g '*.md'`
within a located root, or the host's directory-listing tool, then inspect a
promising subdirectory. A title search on selected Markdown files can expose
relevant notes whose filenames are generic. Keep raw runs, code vendors and
unrelated archives out of this pass; narrow the directory if the listing is large.
Follow a known useful link directly; these are discovery options, not compulsory
levels to traverse. A clearly scoped entry can identify a promising note or an
apparent coverage gap before the full explanation is opened.

Use names, aliases and related terms to search candidate filenames, headings
and then text as needed. Open the plausible notes and compare their questions,
assumptions and qualifications before reuse. A title or index entry locates
material; it neither proves coverage nor validates a claim. One unmatched term
does not establish that the work is absent. Follow the
[shared-knowledge guidance](shared-knowledge.md) when comparing shared atoms or
other explanations.

Stop once the relevant location and context are found. Reuse them within the
current task rather than listing every directory again at each turn. If this
nearby discovery still leaves a consequential location unknown, ask. A newly
established topic or collection entry belongs in the existing README once;
ordinary browsing needs no note, search log or new index.

## Write entries that help choose the next read

Where a title alone is ambiguous, give its link a short description of the question
the note helps answer and the setting actually treated. Add a limitation when it
changes the choice: "Flux integrality for a line bundle on a sphere, proved using
two patches; Hall response is a separate derivation." Useful aliases can help
find it, but need not share a column or sentence with the scope. This is a prose
convention, not a required table or metadata schema.

Keep detailed entries in the nearest useful index; a parent index can describe
and link the collection without copying all its entries. Maintain an entry when
its location or usable scope changes, including a correction that makes the old
description misleading. Routine body edits and unchanged reads need no index
update. Derive the description from the note, not from a planned extension; a
stale or missing description is a reason to inspect a plausible candidate, not
to declare the needed work absent. Group entries when scanning becomes difficult.

Entries guide selection; the note supplies the argument and qualifications.
For substantive topic recovery or main-note revision, understand the complete
main argument as described in [aitp-memory](../SKILL.md); do not substitute an
index blurb for that context. Focused recall and shared-note reuse can read the
relevant passages and follow only the links the question needs.

## Optional layouts for a new home

For a new independent topic or an agreed independent research branch, keep its
material together in a designated folder with a `research.md`. Reuse an existing
folder and main note when they already serve that question. A proposed direction
or short diagnostic does not establish a new branch folder.
The code repository itself may be that folder; an extra workspace layer is not
needed. This is a menu of useful locations, not a tree to generate in advance:

```text
topic/
  README.md                 Folder map and actual material locations, if needed
  research.md               Developing main argument
  notes/                    Detailed derivations, concepts and topic-specific reading
  references/               Papers, bibliography and source documents
  code/                     Reusable code owned by this topic
  results/                  Saved results, with their inputs and producing analysis
  manuscripts/              TeX sources, publication drafts and compiled PDFs
  skills/<method>/SKILL.md   A demonstrated reusable procedure
```

The `research.md` may be enough when a parent README already explains this folder.
Create other locations only as needed. Keep a figure with the analysis that
produces it; a separate `figures/` is useful when the existing manuscript or
analysis workflow needs it. Formal work may need only notes and references,
while numerical work adds results or calculation bundles. Existing `calculations/`,
`runs/` or other useful names keep their layout. New figures can use
`results/figures/` when no suitable location exists; do not split an established
input/output/analysis bundle merely to fill these categories.
Mixed work follows the connections between the theory and its tests.

The same choices apply at the root, topic and any depth of genuine subquestion.
Each main note owns the argument at its level and links to the parent or branches
it serves; material directories are not themselves research branches. Keep original
papers in `references/`, local reading explanations and substantial derivations in
`notes/`, and authored article or lecture sources and their PDFs in `manuscripts/`,
unless an established home already serves that role. Shared PDFs and checkouts stay
in their existing homes and are linked from each use, not copied into every level.

A [shared theoretical collection](shared-knowledge.md) can live outside individual
topics, for example in a sibling `knowledge/` directory. Its index, the README or a
page the README names, lists entries by area. Topic notes link the atoms and source
readings they use. When the collection exists, a new reading of a source that other
questions can use goes there; established readings keep their place. This is optional
ordinary Markdown, with no graph database or required taxonomy.

For code changes, builds, numerical tests and run outputs, consult
[numerical development and experiment locations](numerical-assets.md) when more
detail is needed. Reusable general methods can be included in
[AITP's domain method library](../../aitp-research/references/method-library.md);
the optional local `skills/` directory remains useful for unreviewed work.

When independent questions really need shared development, a family can use:

```text
family/
  README.md                 Links to each question and explains shared assets
  question-a/research.md    One question, with its own supporting material
  question-b/research.md    Another independent question
  workspace/                The actual shared code or calculation workspace
```

Keep topic-specific assets beside their question unless the working code requires
another location. Describe that relationship in the family README. Do not create
a shared workspace merely because this example includes one; shared atoms
or methods likewise need only one primary home when real reuse appears. Existing
projects retain useful layouts and names. These suggestions never require a move.
A family README that already leads to independent main notes is an established
research entry. Recover those questions before treating an absent family-level
`research.md` as a new project or inventing a common scientific conclusion.

The whole research workspace has the same shape one level up, with the
[root note](../SKILL.md#the-backbone-at-each-level) as its main argument:

```text
research-workspace/
  README.md                 Folder map: each topic's location and question
  research.md               Root note: directions, connections, seeds, agreed agenda
  notes/<question>.md       Derivations and connections from discussions without a topic
  topic-a/research.md       A topic, with its own branches and material
  topic-b/research.md
knowledge/                  Optional shared collection, linked from the root
```

The root `notes/` folder holds what a discussion produced and no topic owned at the time.
When a topic adopts such a note, keep it in place and link the relationship, or move it
when that materially improves organization, repairing incoming links and knowledge-index
rows together.

## README explains the folder architecture

Use the nearest suitable README as the map of the actual folder structure. When
a branch folder is established, link its `research.md` from the parent or family
README and say which question the folder serves, how it relates to the other
question folders, and where shared work lives. Also explain established locations
needed to continue the work, such as detailed notes, code, calculations and
literature. Say which question they serve and which are shared.
Only include categories that exist and are useful. Distinguish active working
locations, historical material and remote-only data when that affects their use.

Use a short paragraph or a small table as appropriate. A family README may
already provide sufficient navigation for several questions; do not duplicate
it in a README for every subdirectory. Create a README only when there is no
suitable existing one and a location explanation is needed. It is not a second
research summary, exhaustive asset catalog or status log.

Update this explanation when a relevant folder or location is established,
corrected or changed. Saving another figure in an already described analysis
location does not require another README entry. A known location needs no repeated discovery
scan or per-turn README review.
Read an asset directory as a location: follow the relevant file or bundle report
when the question needs it, without recursively indexing its contents on entry.

## Let the argument connect the evidence

The main note links the detailed notes needed to understand its reasoning,
including useful failed routes. Those notes connect their claims to the actual
derivations, papers, code, inputs, results and figures. Keep the core conclusion,
decisive assumptions and scientific meaning intelligible in the main note.
Follow supporting links only as the question requires. Direct links from the
main note remain useful; a file does not need a new note just to be referenced.

Before creating an asset, check where this kind of work is already being done.
Save it there, or choose a suitable location alongside related material if no
location is established. Describe a newly needed working location in the README
once it has been chosen. Do not scatter copies across topic and shared folders,
pre-create a directory template, or move usable assets for cosmetic consistency.
Keep shared code, concepts and data in one primary place and link them from the
relevant notes. Independent questions may share assets without becoming one paper.

After an authorized write, reopen the saved file at its actual location and check
the affected links. Connect its scientific use from the main argument or an already
linked supporting account: what question it helps answer, under which conditions,
and where the supporting material lives. A file saved successfully is not yet an
integrated argument. Do not add a wrapper note, manifest or parallel summary solely
to register it. These ordinary file and link operations need no workbench or context
plugin.

## Organize materials inside an existing topic

When the task is to arrange an existing topic's materials, keep the topic and
subtopic directories and established main-note paths fixed. Reuse sensible local
layouts; do not rebuild the project tree to fit a UI. Move internal files only
where that improves their actual use within the authorized task. Before moving
them, keep a recoverable backup of those files and the notes whose links will
change. Repair affected incoming and outgoing ordinary links together, and check
the moved files and their uses before retiring the old copies. Shared repositories,
shared source PDFs and large data stay in place; reference their actual locations.
Routine organization already authorized needs no additional confirmation step;
this guide is not itself permission to relocate other research or shared assets.

## Keep an asset usable

Link a figure to its generating script and source data in its caption or nearby
prose. Keep a run's inputs, submission script, outputs and analysis together;
its report should say what actually ran and what the result establishes. Large
raw data need not enter Git. Retain a precise remote location when the dataset
is remote-only, and state the local material needed to interpret it offline.
An unavailable remote dataset is not a locally migrated dataset.
Placing or redrawing a figure does not add scientific validation: retain the
underlying result's conditions and whether the image is a schematic, a diagnostic
or evidence for a checked claim. Do not invent source data for a schematic.

Use relative links between research assets. Resolve scripts relative to their
own location or an explicit command-line project root when practical. Put
machine/account/environment settings in one local environment note or config,
not copied into every Skill. A reference to an old directory inside a historical
report may remain as historical context; active entrypoints must use the new
location. Do not rewrite archived output as though it ran in the new directory.

If an actively used source exists only in a temporary download or cache location,
place a verified copy in its established durable reference home and repair its
uses before treating that location as settled. Preserve the original during
validation; do not re-download or replace a particular edition without checking
which version the argument actually used.

## Recover a whole topic before archiving its old home

Read the whole current main note. Discover research questions from the old
manuscript, source reports and working tree as well as prior research records.
Follow corrections and consequential failures, not just the newest successful
result. Group related attempts into a coherent branch explanation with its
question, decisive reasoning, present conclusion, limitation and asset links.
A branch may be completed, open, rejected or a planned experiment; preserve
the difference. These are prose distinctions, not required metadata.

Retain source code, useful inputs/outputs, manuscripts, figures, references and
uncommitted work. Preserve an existing asset bundle's internal layout unless
there is a concrete reason to reorganize it. Use a backup for old administrative
records; their commands are historical text, not the new workflow. Recover
unique scientific content from them into ordinary notes when needed.

Check that every discovered scientific branch has an intelligible destination,
that active links and symlinks resolve without the old directory, and that an
important script/figure has its inputs. Compare retained file contents when
copying. A file inventory does not establish scientific understanding; valid
links do not establish numerical correctness. Document any unresolved source,
environment or remote-data dependency before calling the old home archivable.
Use one migration note when such a review is requested, not a permanent ledger.

For each existing subquestion, connect the references and reading explanations it
actually uses. Where implementation matters, link the relevant source entrypoint,
inputs, results and reproduction account, not only a large repository or run
folder. Shared sources keep one home and may serve several questions. An empty
collection is not missing science: say when a source is unavailable or code is
not needed instead of inventing resources. Check the decisive links inside the
selected supporting notes too; a working main-note link can conceal broken
relative paths one level deeper.

When a file-backed workbench is part of the task, check the actual topic and source
views as well as filesystem links. Historical copies of a main note must remain
distinguishable from current accounts, and environment or output trees must not
consume discovery before the research backbone is reached. Configure discovery
without making historical evidence unreadable. A source may exist yet be
unavailable through the reader, for example when it rejects symlinks; retain the
working bundle and link its real admitted source rather than silently copying it.
If the workbench identifies records by their paths, keep established account
paths or verify an explicit relocation mechanism before moving them. Check an
existing conversation's source reopening and a fresh subtopic's creation as
separate uses; neither follows from a successful file copy.

Never delete the old home merely because a copy succeeded. Archiving and any
installation or execution use the researcher's actual authorization.
