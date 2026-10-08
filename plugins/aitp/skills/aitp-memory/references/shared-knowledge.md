# Shared knowledge: atoms, source readings, stories and authors

A shared collection holds understanding that more than one question can use. Its
purpose is practical: a theoretical derivation, a reading or a study session should
start from what is already understood and leave that understanding better, instead
of rebuilding it from memory each time. The topic's main note still carries its own
research argument; primary-source checks and research-memory decisions apply as
usual.

## What the collection holds

One collection can hold several kinds of entry, connected by ordinary links:

- **Atoms.** Each atom covers one concept, theorem, technique, worked example or
  reusable result. It gives the question the idea answers, the statement at its true
  strength, the smallest example that keeps the point, why it holds, where it stops, and
  where to read it. Several stories and research topics can use one atom. Most of the
  guidance below concerns these.
- **Source readings.** These cover a paper or lecture that the researcher uses or
  studies: a map of the source from a skeleton reading, and section notes for the parts
  read closely. Each records the version read and exact locators: section, page or
  equation, and a short verbatim phrase that finds the passage. It also says what each
  passage establishes, and who read it. A reading is a map to the source, not a
  replacement for it; see [keeping source readings usable](#keep-source-readings-usable).
- **Stories.** A story is the main note of a learning topic, playing the role that
  `research.md` plays for research. It is a chain of questions, each arising from the
  previous answer, with short answers at their true strength and links into atoms and
  readings. See [telling a learning topic as a story](#tell-a-learning-topic-as-a-story-of-questions).
- **Author collections.** These are optional, for authors the researcher has chosen. They
  hold an index of the author's moves and a record of how the author organizes a paper,
  both pointing to source passages; see
  [exemplar authors](../../aitp-research/references/exemplar-authors.md).

Good explanations that live inside topics belong to the collection too. Link them
from the index; they need not move. The collection's README can say where each kind
lives. These kinds are a vocabulary, not a required directory layout.

## One index that can be read at once

Keep one index page, the README or a page it names, short enough to scan in one read.
Group its entries by area, and give each row:
- the entry, its aliases and its kind: concept, theorem, technique, example or result;
- the question it helps answer and the setting treated;
- the atom or local explanation, if one exists;
- where to read it in sources, with locators;
- related moves, and the stories or topics that use it.

List each area's stories and source readings beside its rows. Link a source
collection's own README for its full list of papers.

A row is useful before any full explanation exists. A concept with a verified
source locator and a one-line scope already saves the next session a search. Say
two things about each entry, explanation or reading:
- **What supports it:**
  - *derived*: the claim is derived and checked here, by a derivation, calculation or
    script;
  - *source*: the claim rests on a passage located and checked in a source, whether
    or not a local explanation accompanies it;
  - *unchecked*: not yet checked against a source or by a derivation.
- **Who has reviewed it:** the researcher, or so far only an agent. A research-derived
  entry also gives its origin; see [what research teaches](#add-what-research-teaches).

Short labels such as "derived; awaiting review" are enough. When support differs within
one note, label the claim or section rather than the whole note. The researcher's own reading
replaces an AI description. Check every locator against the source version cited.

When several sessions contribute to one collection, give each substantive page one
writer and collect proposed shared-index and navigation edits separately. The integrating
session rereads the current shared file immediately before applying small exact changes.
Preserve unrelated rows and review labels, then check the resulting links. This
coordination can use ordinary proposal notes; it needs no permanent workflow registry.

## When to use it

- **At the start of a theoretical derivation, a conceptual question, or a reading or
  study task.** This includes the theory within a numerical project and a quick "remind
  me why" question: the collection may already hold the explanation, in the researcher's
  conventions, and the answer can point to it. When a collection exists, read
  its index once, as one reads a topic's main note before working on it, then open
  the entries for the task's central concepts and sources. Reuse their conventions,
  or state the difference where it matters. This is one bounded read per task, not
  a search on every term.
- **When a note introduces a concept that has an entry.** Link it, and reuse or
  explicitly adapt its conventions rather than silently re-deriving them.
- **When reading or studying a source.** Start from its existing reading if there
  is one. When the session establishes something new, leave the reading improved and
  add or update index rows for the concepts the source treats. New things include a
  checked locator, a result, a correction (marked by who made it) or missing navigation.
  Unchanged reuse needs no write.
- **At a natural pause after theoretical work.** Retain what another question could
  use (see below). A row with a locator is often enough.
- **When a discussion without a topic explains a concept or framework.** Its durable
  outcome lands here, as memory's
  [discussion outcomes](../SKILL.md#where-discussion-outcomes-land) describe, and the
  root note reaches it through the index. Combining several sources into one explanation
  follows research's [synthesis](../../aitp-research/references/literature.md#synthesize-several-sources).

Routine coding, job handling and plotting do not trigger this. Do not read the
whole collection, chase links recursively, or stop a fluent derivation to polish
entries.

## Start with a small connected collection

Reuse an existing library if it has a suitable home. Otherwise a researcher can
choose a sibling location such as `physics/knowledge/` beside `physics/topics/`.
This is an optional local convention, not a hard-coded dependency of AITP.
One README and a few substantive Markdown notes are sufficient; source readings
can live in a subfolder per author or collection. Link the collection's location
from the topic or parent README once it is established, so another session can
find it.

A session working on the collection often reads only its README and templates, not
this reference. So the collection's README should state its working rules briefly:
- where each kind lives;
- the support and review labels;
- that a paper map may start as a stub;
- how corrections are made visible. Keep its links working when topics are renamed or moved. A broken link
silently hides the entry it points to.

Do not build a complete physics taxonomy, one empty page per term, or numbered
subnote levels. A concept can support several arguments and several concepts can
support one theorem; ordinary links already express this graph. Keep one primary
explanation, linking existing lecture PDFs or TeX for depth. Research-local
conjectures and unfinished applications remain in their topic.

## Find an existing explanation before creating another

The pre-creation check applies to a new atom, including an explanation first written
inside a topic. It is not a prerequisite for every
derivation step, conversational explanation or project-specific analysis note.

Start from the collection index, read at the start of the task, and the current
topic links. If the location or available coverage is unfamiliar, [browse nearby directories and note titles](local-assets.md#browse-nearby-topics-and-shared-knowledge)
before opening full explanations. If needed, search filenames, headings and
Markdown text with the concept's name, plausible aliases and related
terms, starting with the shared collection and current topic. Extend to relevant
existing topic notes when the entry is incomplete or previous work is remembered;
keep raw outputs, vendored code and unrelated archives out of this search. A search
tool such as `rg` is enough. Translate a conversational term into likely note
terminology when helpful. One unmatched phrase is not proof that no note exists.
If its location remains unknown after this brief nearby discovery and materially
affects the choice, ask where it lives rather than inventing a second library.

Read the plausible candidates and compare the objects, assumptions, conventions
and purpose, not just titles. Reuse one that covers the needed claim. Extend an
existing explanation when the new understanding concerns the same object and
scope; keep a model-specific application in its topic. Distinct settings or a
long independently useful extension may merit separate notes with an explicit
relationship. For example, finding a single-state explanation does not establish
that a requested multi-state treatment is already covered.

Stop when the relevant treatment is found or the reasonable nearby candidates
have been checked. Reuse a known-current lookup within the same task. This bounded
search reduces duplicates; it cannot guarantee exhaustive semantic discovery.
It needs no search log, database, mandatory metadata or whole-library audit.

## Teach at the reader's actual starting point

An atom about a concept starts from a concrete difficulty, introduces the
object and its conventions, works through a faithful example, and shows what
the definition enables. Supply a short explanation of a needed prerequisite at
first use, even when a longer note is linked. Graduate-level QFT familiarity
does not automatically imply familiarity with bundles, background fields or
generalized symmetries. Ask about a consequential learning gap when it becomes
apparent; do not conduct a generic prerequisites questionnaire at every entry.

An atom about a theorem states the setting, quantified hypotheses and conclusion,
then gives the mechanism and the decisive proof steps, an example and the boundary
of applicability. Identify whether it is proved here, quoted from an inspected
source, or conjectural. Separate a mathematical theorem from the hypothesis that
identifies its objects with a physical model. A restricted example cannot stand
in for a classification theorem.

The other kinds follow the same pattern:
- **A technique** explains why the technique works, when it applies, how to check it,
  and when it fails. Step-by-step instructions for performing it belong in a Skill
  ([aitp-distill](../../aitp-distill/SKILL.md)). Create both only when each has a
  distinct use, and link them.
- **An example** says which system it uses and what it exhibits, and what it cannot show.
- **A result** says what was found, under which conditions, with which evidence.

Keep a concept and its first small lemma together when that helps understanding.
Split a long theorem or derivation only when it can be read and reused as a
meaningful unit. Use [supporting-note writing](../../aitp-writing/references/supporting-notes.md)
and [citation conventions](../../aitp-writing/references/citations.md). For teaching,
choose [learning depth](../../aitp-writing/references/learning.md#set-a-useful-learning-target)
for the needed calculation rather than demanding proofs of every background
theorem. State what the page enables its reader to explain or reproduce. An
example should expose the actual mechanism; definitions alone do not teach its
use. A difficulty specific to one source can stay in that source's reading or in the
topic's notes; share its explanation as an atom only when its meaning and scope support
independent reuse.

## Keep source readings usable

A reading of a paper or lecture is valuable when another session can go straight
from it to the passage and know what that passage does. It records:
- the version read;
- for each important passage, the section, page or equation, and a short verbatim
  phrase that finds it;
- what the passage establishes, under which hypotheses, and in which conventions;
- who read it: an AI, the researcher, or both.

Keep quoted text short. The source itself is the reference, so the reading points
into it rather than reproducing it.

Check locators in the exact edition used. A TeX search hit may be commented out or
inside an inactive block; included files, custom section macros and reset counters can
change the printed numbering. Distinguish printed page numbers from physical PDF pages.
An equation label or distinctive search phrase locates a passage; it does not by itself
establish the claim attached to it. When a collection must work without the originating
workspace or network, retain or link the permitted local source copy and test that
route. State when an anchor was checked in an external cache instead.

A reading usually grows in two layers:
- **A map of the source**, from a skeleton reading. It gives the source's chain of
  questions and the job of each section, a reading order by dependency, what the source
  establishes at its true strength, its notable details, and where it compresses.
- **Section notes**, for the parts read closely. They give:
  - the steps in source order, including claims made only in prose;
  - the hard steps filled in, each added line labelled as quoted, imported (with its
    locator) or reconstructed (with its check);
  - details worth remembering;
  - what the section depends on and what uses it.

  Give each hard step its own heading, so that other notes can link to it.

State the passages actually covered. A populated page, a checked locator, a completed
source reading, a reconstructed proof, and the researcher's review are different facts.
A section can be read completely while importing a theorem whose proof remains
external; a selected calculation does not make the surrounding section completely read.
When full source coverage is requested, account for omitted prose, footnotes and figure
arguments as well as equations. A compact source-to-note checklist can help a large
build, but is not required for ordinary notes. Keep unfinished coverage visible in the
map and story; do not infer the reader's progress from authored material.

How to read closely is in [learning from a source](../../aitp-writing/references/learning.md#read-a-source-closely).

When the researcher studies a source, their corrections and questions belong in the
reading, marked as theirs. A disagreement with the source is recorded as such, with
the check that settles it if one was made. One collection folder per author or
series keeps readings findable. Its README lists the sources, the depth to which
each was read, and the concepts each serves, so that the main index needs only
one row per collection and the index rows that point into it.

## Tell a learning topic as a story of questions

A learning topic needs a main line as much as a research topic does. Its story is a
developing article, not a course that retells the sources. It is a chain of questions,
each arising from the difficulty the previous answer left. For each question, give a short
answer at its true strength, what to read, and the key step. Link into atoms and section
notes rather than copying them.

Where two sources reach the same structure by different routes, show both and what
each assumes. Keep in the story:
- the researcher's own questions;
- their status on each question;
- the open questions.

Revise the story as the reading progresses, as one revises `research.md`.

A learning topic has one main note. Its story can be the topic folder's `research.md`
written as a chain of questions, or a story kept in the shared collection; do not keep
both. Whichever holds the main line links to the other material.

The story follows the learner's logic, while source readings follow each source's own
order. Link the two rather than cutting a source into questions.

## Give links a reason and read selectively

Explain relationships in ordinary sentences, for example:

- "This proof uses the transition functions introduced in the bundle note."
- "The anomaly example applies background coupling to a boundary theory."
- "The Berry connection is a related geometric construction on parameter space;
  it is not automatically the electromagnetic field on spacetime."

Distinguish a needed prerequisite from an optional related idea and from a
project-specific application. These need no edge schema or mandatory labels.
Useful selected backlinks can show applications; there is no requirement to
maintain every inverse link by hand. Search can discover other incoming uses.

Enter through the current research question. Read the relevant shared note or
section, follow a prerequisite only when it blocks the present explanation, and
return to the research argument once the needed claim is intelligible. Do not
recursively read all links, chase cycles, or expand a short question into an
encyclopedia project. When navigation itself becomes an obstacle, explain the
missing step locally rather than adding another compulsory hop.

## Add what research teaches

Most of what is worth sharing comes out of research. Examples:
- a derivation of a general fact;
- a technique that worked, with the condition under which it fails;
- a worked example or a counterexample;
- a convention translated between sources;
- a corrected claim.

At a natural pause after useful theoretical or methodological work, numerical methods
included, identify whether the work supplied something another question could use. Do
this even when the work was fluent and needed no lookup in the collection.

When the researcher keeps a collection, recording a result includes this decision. Make
it in the same pass as the topic note, within the authorized research scope, without
waiting for a separate request.

**The test is reuse beyond this topic.** Could another question use the result, with
its assumptions stated, without relying on this topic's open hypotheses or unfinished
argument?
- A model-specific example or counterexample can pass, when its system and conditions
  are stated.
- Conjectures, unfinished applications, and results that depend on the topic's
  unresolved choices stay with their question.

What is shared carries the assumptions, conventions, decisive reasoning, sources and
limits it needs.

**Check what is already recorded.** Look in the index and in the topic's own notes, and
extend an existing record rather than starting another.

**Point to the research; do not copy it.** A research result enters the collection as an
index row citing the exact section of the research note, with its status. The research
note stays the single home of the claim, so later corrections there apply at once. The
collection holds no second copy that could go stale.
- **The row** gives:
  - the entry and its kind;
  - the question it answers;
  - the cited section;
  - a status such as "provisional (research: topic name); awaiting review".

  It names the question, not the result, so that the claim and its qualifications live
  only in the research note. A session that needs the answer opens the cited section.
  Once the researcher confirms the result, the row may state it.
- **Promotion to an atom needs the researcher's confirmation.** Write an atom from a
  research result only after the researcher confirms the result. Independent checks
  strengthen a provisional pointer's support; they do not supply that confirmation, and
  they do not turn a research result into source-based learning. Explanations grounded in
  sources rather than in the topic's research, such as source readings, follow the
  collection's own learning rules. Until confirmation, propose the atom in the handoff
  rather than writing it. When promoting, extend an
  existing atom if the object and scope match, rather than writing a second one.
- **Not research claims.** Readings of sources made during the work, and corrections to
  existing entries, follow their own rules below.

A new entry gets its index row in the same edit. Update the row whenever the entry's
location, scope, support, review state or qualifications change; a routine edit to a
note's body needs no index change.

**Record provenance and review state.** A research-derived entry says:
- where it came from, linking the topic's note or section;
- how it was checked: a derivation, a calculation, a script or an independent reader;
- whether the researcher has reviewed it, or it is still awaiting review.

Sharing does not promote an uncertain claim into an established fact, or authorize
publishing local research.

**Keep pointers true.** When a cited research note changes, review its index rows in
the same edit. Update only affected locations, scope, support, review state or
qualifications, including a corrected or withdrawn claim or a moved section.
An unrelated result elsewhere in that file needs no row change. Dated correction
lines explain an actual correction; do not add dated acknowledgements that a row
remains unchanged. A withdrawn result keeps a short visible line until the researcher
removes it. Check moved links and repair affected targets.

**Link a promoted atom both ways.** The research note links to the atom where it uses it,
and the atom names the research notes that use it. The research note keeps its own
argument and result, and the atom keeps the general explanation; neither copies the
other. Preserve convention differences at the application site. A row that only points to
a research note needs no reverse link.

**Put readings made during research where others will find them.** Research sometimes
needs a passage read closely, to check a formula, a convention or a hypothesis.
- **Existing reading.** If the source already has an established reading, use it.
- **With a shared collection.** A new reading that other questions can use goes into the
  source's map or section note there, with the exact step linked from the research note.
  A difficulty that matters only to this topic can stay in the topic's notes.
- **Without a collection.** Keep the reading in the topic and link it.

**Retain only what is new, at a pause.**
- Read-only reuse needs no edit. If the existing explanation already covers the
  understanding, reuse it as it is.
- Save a useful new explanation, correction, failed argument or reusable connection at a
  natural pause. Preserve a fragile insight earlier when necessary.
- Keep a short clarification in its current context when that is sufficient. Do not
  interrupt fluent reasoning to polish the collection.
- The agent maintains the relevant index row with the substantive edit; the
  researcher need not maintain every backlink.
- If duplicate explanations are found later, reconcile their valid content and sources,
  repair affected references and preserve unique material. Repeated derivations in
  independent sources can strengthen understanding, but duplicate Markdown copies are not
  independent evidence.
- A move is optional and must respect existing asset paths.

**Correct where the error lives.** Before a substantive change to a shared note,
understand its whole argument and the relevant source.
- When research shows an atom or reading to be wrong or too strong, correct it in place.
  Add a short dated correction line in the note saying what was wrong, what the source or
  check shows, and where. Keep the index row's qualifications in step. A reader who used
  the earlier version can then notice the change.
- Search the collection and the topics for other uses of the corrected claim. Update those
  whose conclusions depend on it, and say which you checked.
- If a hypothesis, sign or theorem statement changes, inspect the known dependent uses and
  update those whose conclusions are affected. A prose clarification does not require
  refreshing every topic.
- Preserve a useful failed argument when its cause prevents a repeat.
- A claim that a source itself is wrong goes in that source's reading, kept apart until an
  independent check confirms it.
- Use [corrections and retained notes](../../aitp-writing/references/supporting-notes.md#correct-claims-and-keep-earlier-routes-findable)
  when a claim changes or loses its main-note citation. Search by the claim as well as by
  incoming links, so that detached explanations remain discoverable. On reuse, inspect
  recorded qualifications before adopting a formula.

An index locates explanations, including disputed or superseded ones, without declaring
them correct.

A research topic needs no story: its `research.md` is its main line, and it links into
the shared atoms and readings it uses. Knowledge and Skills also have different uses. An
atom explains what an object or result means and why it holds; a distilled Skill teaches
a reusable procedure, through [aitp-distill](../../aitp-distill/SKILL.md). One piece of
work can feed both, with each linked to the other. Neither is created automatically from
every conversation.
