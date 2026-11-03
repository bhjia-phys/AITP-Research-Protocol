# The story paper of a research topic

`research.md` is the working record: precise, dense with links, changing whenever the argument
changes, and written so that a returning agent can continue. The researcher also needs to
understand the topic as a whole. A **story paper** serves that need: a short LaTeX paper, four to
ten pages, that tells the topic's full story and the insights worth keeping, compiled to PDF.

A learning topic needs no story paper: its main note already is a
[story of questions](../../aitp-memory/references/shared-knowledge.md#tell-a-learning-topic-as-a-story-of-questions).

## Why a PDF edition, not a second note

A living Markdown story beside `research.md` would drift into a second working record. The story
paper is kept from that by four rules:

- **It is an edition.** It is built at a milestone, carries its date on the title page, and is
  never edited during work. The next edition is a new build; earlier PDFs stay as they are.
- **It holds no state.** No Current work, next actions, job states or run counts. "What is open"
  states the gap and the test that would decide it, as the record does.
- **It is never a source.** No result appears there first. Agents recover a topic from
  `research.md` and its notes, never from the story paper. When writing it exposes a gap, an
  unclear step or a claim stated more strongly than its evidence, repair the record first, then
  build the paper from the repaired record.
- **Every statement has a record.** Each section ends with a short "Record" line naming the
  `research.md` sections, notes or runs it draws on, and each result carries the strength and
  condition that the record gives it.

## When and where

Produce an edition when the researcher asks; offer one at a milestone (a first consequential
result, a branch closing, before a group meeting or a manuscript). Keep the source in the topic's
`manuscripts/story/`: `main.tex`, any `references.bib` and `figures/`, and the PDF built as
`story-YYYY-MM-DD.pdf`. The topic README maps the folder; `research.md` links the newest edition
from its curated materials. Follow [manuscript handling](manuscripts.md) and the full JHEP
template, with the researcher's own author block and no co-authors, e-mail or acknowledgments
unless the researcher supplies them.

A result is presented as established only after the researcher has accepted it, as
[brainstorming's moments](../../aitp-human-brainstorming/SKILL.md#decide-whether-a-human-answer-is-needed)
describe. Until then the paper calls it provisional, as the record does.

## What it contains

Start from the [story-paper template](../assets/story-paper.tex):

1. an abstract: the question, the approach, the main result at its true strength, the key
   insight and what is open;
2. the question and why it matters;
3. the setting and the conventions needed to read the rest;
4. the story, told by ideas in the order they make sense rather than the order things happened,
   with what each turn and each failed route taught; a branch is a subsection;
5. the key insights, each with its decisive step or number;
6. what is established and how firmly: a table of result, strength, condition and record;
7. what is open, and the next decisive test with what each outcome would mean;
8. how to learn the topic: prerequisites, sources, notes in reading order, and three questions a
   reader should then be able to answer;
9. optionally, an appendix with short sketches of the derivations worth remembering.

Omit a section that would be empty.

## Check that the paper works

At a milestone, an [independent reader](../../../agents/aitp-reader.md) in story mode reads only
the paper's TeX source and answers its three questions, quoting where it found each answer. The
researcher may answer them too, in conversation. A wrong or unsupported answer locates the
passage to repair, in the record first if the gap is there. This diagnoses the paper, not the
researcher, and it is never a gate on the research.
