# Validation and its limits

## A research backbone and one research cycle, 2026-10-08

A researcher described the architecture they want: `research.md` as the intellectual backbone
and long-term memory of the whole research, with the skills guiding how it grows. Discussions
should become part of the research, the agent should take initiative, and every paper,
question, derivation and numerical experiment should be locatable from the backbone. Two
independent assessments, by Claude and by a GPT model, found that the live design is the right
foundation but not yet enough, and that a request router is not the missing architecture. The
GPT model then drafted the design over two rounds, in which it accepted five objections from
Claude.

The implementation starts from the live tree:

- `aitp-memory` is the single entry and opens with a six-line research cycle.
- The backbone has levels: a root note for the whole research, holding directions,
  connections, seeds, agreed choices and standing agreements; optional programme notes; topics;
  and branches.
- A reachability rule: every retained item has one home and a link path from the root and
  from the note that uses it.
- Homes for discussion outcomes without a topic, and seeds that are proposed as branches when
  ready.
- A visible close that names what the work warrants, with an initiative table separating what
  proceeds within the agreement from what is proposed.
- Status, history and continuation move into a reference.
- New `aitp-verify`, with review cycles folded in and an honest record of how independent a
  second read was.
- New `computational-work.md`: experiment design, the trace from formulation to code, feature
  development, debugging, benchmark suites, paper reproduction, comparison with earlier results,
  and environment placement.
- Synthesis across sources in the literature guide.
- Reviewed plans, and hand-offs with rules for parallel work.
- From the router prototype: the domain method indexes, the Slurm resource and restart
  guidance, and figure and manuscript rules. Its dispatch table and `aitp-investigate` are not
  carried over.
- The version moves to 1.2.0.

An adversarial review of the implementation by the same GPT model raised fourteen findings, ten
important and four minor, none blocking. Fixes:

- **Single wording.** The cycle now uses the design's exact six sentences, placed first in
  memory and reproduced verbatim in the Kimi system prompt.
- **Authorization** can come from the current request or any existing agreement. A standing
  agreement in the root is defined as an explicit instruction with scope and end, never inferred
  from past actions.
- **Discussions.** A missing topic note no longer turns a discussion into a topic.
- **The root** keeps its own content rule rather than every parent rule.
- **Atoms.** A research-derived atom always needs the researcher's confirmation.
- **Environments** go in established, authorized code or development locations, which may lie
  beneath a topic, never in a prose-only reading folder.
- **Plans.** A phase is complete only against its acceptance condition, not because evidence is
  linked.
- **Evidence gaps.** Persistent gaps are recorded; only temporary session limits stay in the reply.
- **Current docs.** The write-decision page now puts status-only requests first and keeps useful
  ideas as seeds.
- **Smaller fixes:**
  - method indexes replace the term "domain pack";
  - moving a root note into a topic is optional;
  - review triage gains an "unresolved" state.
- **Length.** Memory was condensed to about 470 lines by pointing duplicated procedures to their
  references; further consolidation remains possible.

Link, frontmatter, manifest and whitespace checks pass across the plugin and docs. The new
behaviour has not yet been tested with fresh sessions; the review recommends bounded tasks
covering:

- retrieving an obscure item;
- retaining an untethered derivation as a seed;
- correcting a branch through the root;
- plan review, continuation and retirement;
- joining parallel results;
- status without edits.

They should run on more than one host.

## Topic-tree checks, 2026-10-07

Memory now includes [keeping the topic tree clear](../plugins/aitp/skills/aitp-memory/SKILL.md#keep-the-topic-tree-clear).
When a main note has a parent or branches, a session relates them at entry. The
parent states each branch's implication once, where its argument uses it, with a
link; the branch keeps its numbers, settings and step history. A changed branch
answer reaches the parent at handoff, and a line of work that has grown its own
question and evidence moves out of the parent.

A read-only survey of a researcher's fifteen main notes found four parent/branch
trees, all linked in both directions. Three parents re-narrated their branch's
evidence, in one case at about 700 words, although the writing guide already said
that the child owns the detail.

Fresh `codex exec` subjects ran four ordinary requests inside a filesystem boundary.
Each boundary contained a disposable Markdown copy of one real topic tree and read-only
frozen skills. Each request ran once with the previous guidance and once with the new.
Synthetic run summaries supplied the new results, and the prompts did not mention
parents or branches. Sealed expectations were written before any subject ran. A Claude
Opus judge scored each run blind to the guidance version and compared each pair. When
it reached a usage limit, DeepSeek V4.1 Flash scored the four remaining judgments, and
Claude repeated them after the limit reset.

| Request | Previous guidance | New guidance |
| --- | --- | --- |
| Record a branch result that changes a parent claim | Parent +52 words, six branch values copied in; clarity 5/10 | Parent +8 words, no new values; clarity 8/10; preferred in the pair comparison |
| Record a completed branch diagnostic | Parent +59 words, three values copied in; clarity 5/10 | Parent +39 words, no new values; clarity 7/10; preferred |
| Record a rerun that reproduces the record | Supporting note only | Supporting note only; tie |
| Improve a cluttered parent's structure | Sections rearranged, branch values kept; clarity 3/10 (DeepSeek 6/10) | Parent 259 words shorter, 32 duplicated values removed; clarity 7/10 (DeepSeek 8/10); preferred by both judges |

Correctness was equal or higher with the new guidance in every request. The judges'
notes prompted one refinement: state the implication once, and replace touched
narration of a branch rather than appending to it. Re-running the first two requests
with it gave parents 53 words shorter and 23 words longer, with no new values; their
blind scores were 9/9/9 and 7/8/8 for clarity, correctness and preservation, and all
expectations passed. Every value removed from a parent was traced across the complete
fixture to a branch, supporting note or sibling topic that still holds it.

Limits:
- One subject per arm, from one model family.
- Synthetic results and single-turn sessions; no live concurrent editing.
- The refinement was re-tested on two requests, without a new previous-guidance arm.
- The judges saw reduced file sets, so preservation was checked separately.
- The fixture author also wrote the expectations.

The researcher's live notes were not restructured. Strict plugin validation and local
link checks passed after this change.

## A large learning collection built in parallel, 2026-10-06

Several fresh sessions extended a learning collection on an operator-algebra topic,
built from public papers and lecture notes. Each owned its own pages: atoms, paper maps,
section notes and story questions.

**Review.** A fresh reviewer checked each builder's pages against the cached sources, and
the builder fixed the findings.
- **Locators:** about 3% of sampled locators failed before repair. These were wrong
  sections or claims the passage did not support. No verbatim anchor was misquoted.
- **Mathematics:** the reviewers found errors in reconstructed mathematics that the
  existing check scripts had passed.
- **After integration,** a random audit of about 10% of locators found 0.5% failing. The
  failures were corrected.

**Learning trials.** Four fresh sessions in a sandbox answered transfer questions using
only a read-only copy of the collection. An independent scorer graded them against sealed
expectations, and all four received full marks.

**The guidance changes** respond to these observations:
- coverage, checked locators, proof and review are recorded as distinct facts;
- locators are checked in the exact edition;
- checks must be able to fail;
- a source error, a note error and an unproved premise are kept separate;
- attribution is placed where support changes;
- fresh-session trials are described as an optional diagnostic;
- concurrent builders use single page ownership with proposed shared edits.

**Limits:**
- one topic and one model family;
- the trials were open-book, so they test retrieval and transfer from the collection,
  not a learner's mastery;
- most section notes remain marked partial;
- the builders' own self-checks missed errors the reviewers found.

## Main and supporting research-note redesign, 2026-10-05

The redesign makes each main note develop its current argument: new evidence
replaces the passage it changes, while detailed setups, repeated measurements
and historical observations remain in linked support. Guidance distinguishes
computational campaigns, formal theory, learning, branches and deliverables,
with synthetic worked edits showing placement and correction propagation.

Fresh `codex exec` subjects ran ordinary research requests inside a filesystem
boundary containing one disposable case and read-only frozen AITP skills.
Guidance digests, sealed expectations, complete transcripts and pre/post file
inventories were retained. A separate scorer reviewed answers and artifacts
independently of the subject sessions; that scorer also authored fixtures, so
this was not a blinded external audit. Live notes and sealed answers were outside
the subjects' filesystem view.

| Round | What was tested | Result |
| --- | --- | --- |
| First retrieval round | 14 before/after retrieval runs on two pilot notes | All scored 8/8 without material overclaim; both editions supported correct retrieval |
| First editing round | 6 updates, polling, correction and handoff tasks | 4 passed; a support-only clarification unnecessarily changed the main note, and a correction missed an unlinked dependent use |
| Version 2 | 8 runs, including 2 replacement held-outs and retrieval regressions | 6 passed; the two remaining failures duplicated detailed report setup in the main note despite correct scientific integration |
| Version 3 | 4 editing runs: two re-tests and two new held-outs | All passed, including setup ownership, provisional scope, index restraint and evidence preservation |
| Final reading verification, using frozen version 2 | 8 runs on real-note copies, including 2 before/after pairs | 7 scored 8/8; one scored 7/8 by omitting an explicitly stated method-order condition. No material overclaim or research write |

Retrieval required four answers scored 0/1/2, with 8/8 and no material overclaim
to pass. Editing conditions were conjunctive. Earlier scores were retained when
later rounds added explicit editorial gates.

Version 2 clarified leaving an already accurate main passage alone, searching
aliases and unlinked dependent claims when correcting results, updating only
affected index entries, and keeping full setups in support. Version 3 explicitly
extended setup ownership to first provisional values and inherited pending
passages. Rollout review also prompted a clarification that unchanged headings
already supply anchors. Exposed candidate held-outs were retired before execution;
replacements were authored after the guidance freeze. Version 3's subjects ran
concurrently despite the prescribed re-test-first order, with unchanged sealed
guidance and separate case mounts.

The rollout restructured 15 main notes, adapting usable existing text to each
note's purpose. Every restructure was independently reviewed, and incoming links
were verified. All 15 are applied. Four notes that live sessions were still editing were
applied only after the researcher paused those sessions and their edits were
merged into the restructure.

Limits: one subject per case and one model family; no old-versus-new guidance
arm. Before/after reading-volume and timing differences are descriptive, not
causal estimates. Explicit skill loading varied across reading subjects.
Editing results used synthetic observations; they do not validate the underlying
science. Reduced fixtures caused some optional-asset detours. Boundary probes
were reused rather than repeated for every run, and filesystem isolation does
not establish network isolation. The small editing cases do not independently
validate anchor handling during large restructures. Strict plugin validation
and Markdown consistency checks passed after this entry was added.

## Research results as pointers into research notes, 2026-10-05

At the researcher's request, research now reaches the shared collection only through
citations, so that research errors do not spread into it:
- A result enters as a provisional index row that cites the research note and names the
  question, not the result.
- An atom is written from research only after the researcher confirms the result.
- Rows are updated whenever a cited research note is corrected, withdrawn, moved or
  renamed.
- The researcher's collection gained a report-only link checker.

Fresh `claude -p` sessions were run with write access in complete isolated copies:

| Task | Result |
|---|---|
| Record a numerical finding (old rule) | Provisional row, no atom, but the row restated the result |
| Same, after the question-not-result rule | The row names only the question and cites a new subsection; no atom |
| Fix links after a cited research note was renamed | All topic links and the index row updated; anchors checked |
| Correct a recorded finding that proved wrong | Dated correction in the research note, failed route kept; row rewritten to the question with the correction; status kept |

Shell writes needing approval were refused, and the sessions used ordinary edits. No
session ran the checker unprompted.

Real use between runs supported the rule. Other sessions added provisional research rows
that cited their notes as designed. One of them grew to about 4,000 characters of
evolving results, including live job status: the stale copy the new rule prevents.

Limits: one session per test, one host. Strict validation passed.

## Real-work writing sessions for shared knowledge, 2026-10-03

Fresh `claude -p` sessions were given real tasks with write access:
- **Tools:** Skill, Read, Glob, Grep, Edit, Write; `acceptEdits`.
- **Workspace:** an isolated copy of a researcher's collection and topics, with writes to
  the real tree denied.
- **AITP:** loaded from this checkout.
- **Requests:** ordinary ones that named neither the collection nor AITP.

Five tasks were run. Failing behaviours were fixed and the tasks re-run:

| Task | Problem found | Fix | After |
|---|---|---|---|
| Record a numerical-methods finding | The topic note was integrated well, but nothing went to the collection; the session only offered | The research route covers methodological and numerical work, decided in the same pass as the topic note | An index row added with origin and review state |
| Write close-reading notes for one section | Step-level note followed the guidance, but there was no paper map | The rule that a map may start as a stub, also stated in the collection's README and section template | Map stub created, and the section note links it |
| Set up a learning topic | none | — | One main note as a story; index entry; unverified identifiers labelled |
| Answer a "remind me why" question | Correct answer, but the collection was never read | "Conceptual question" added to the start-of-task trigger | Read the index and atom, and answered from it |
| Correct a planted overclaim in an atom | Correct sourced fix, but no visible correction | Correction rule stated at the top of the collection's index and in the workspace instructions | Dated correction line, qualified index row, other uses searched |

Main lesson: for collection tasks, sessions follow the workspace instructions and the
collection's own index, README and templates. They often never load the Skill reference.
The shared-knowledge reference now says the collection's README should state its working
rules.

Limits:
- one host, one model, one session per variant;
- some re-runs used the previous round's files;
- Codex, Hakimi and interactive permissions were not tested.

Strict validation passed after the edits.

## Self-consistency pass after the shared-knowledge changes, 2026-10-02

After the day's changes, every Skill, reference, starting file, both READMEs and the two
explanatory docs were reread for contradictions. Fixes:
- **One vocabulary.** Atom, index row, source reading, story and author collection replace
  "concept note/row", "standalone concept or theorem note", "reading note" and "discovery
  entry".
- **Two label axes.** What supports a claim (derived, source or unchecked) is separate from
  who has reviewed it.
- **One main note per learning topic,** either `research.md` or a story.
- **The retained Witten corpus analysis** is labelled design history, not an author
  library.
- **Stale statements corrected.** Two READMEs still had the old obstacle-only collection
  trigger. `docs/transition.md` counted four Skills instead of six core Skills.
- **`docs/when-to-write.md`** gained rows for close reading, stories, the research route
  and exemplar authors.

A read-only Codex review (`gpt-6-astra`) of the whole plugin then reported 14
inconsistencies, three of them high. All were checked against the files, confirmed and
fixed:
- **High:**
  - close reading had made the learner's attempt sound compulsory;
  - a move's correction waited for repeated failures, unlike distillation;
  - the packaged README kept the old trigger.
- **Medium:**
  - the support labels did not fit source-backed explanations;
  - technique atoms overlapped with Skills;
  - the reuse test was too absolute for stated-condition examples;
  - reading placement lacked a single rule, including a fallback without a collection;
  - several reads triggered writes unconditionally;
  - index updates were required for routine edits;
  - `research.md` was assumed as the learning main note;
  - the row-only case lacked a link rule.
- **Low:**
  - the story form read as mandatory;
  - "core" was used inconsistently;
  - three moves lacked failure conditions.

A second read-only pass by the same reviewer found 13 findings resolved and one partly
resolved. That one was the theory template's placement of existing readings. The pass also
found one new conflict: a repeat-lookup restriction that excluded the pre-creation coverage
check. Both were then fixed.

Strict plugin and marketplace validation passed, and all 239 links and heading anchors in
the plugin, READMEs and docs resolve. These are document-consistency checks. They do not
show that agents follow the guidance better.

## Adding what research teaches to shared knowledge, 2026-10-02

The story vocabulary below serves reading and study, but most shared entries come from
research. The shared-knowledge section on growing the collection became "Add what research
teaches", reorganized without dropping its earlier rules. It covers:
- the test of reuse without the topic's own assumptions;
- checking what the index and the topic already record;
- the lightest form that works: an index row, an atom of the right kind, or the research
  note itself as the home;
- provenance, meaning origin, checks and review state;
- links in both directions;
- passages read closely during research going into the source's reading;
- corrections made where the error lives;
- the rule that a research topic needs no story.

Research, memory and supporting-note guidance now point to it.

A fresh read-only `claude -p` session in a research-topic folder was given a real
numerical-stability finding. It was asked whether and how to record it beyond the topic,
without naming the collection or AITP. It:
- read the collection index and README, and applied the reuse test;
- kept the research note as the primary home, including correcting an earlier claim;
- proposed a technique atom with its origin and an awaiting-review state, and an index row
  added in the same edit that extends the existing related row;
- explained why the finding is knowledge rather than a Skill, and wrote nothing.

It did not check the topic's own notes for an existing record before proposing a home.
The "check what is already recorded" sentence was added in response. That sentence has not
been retested. Strict plugin validation passed.

## Close reading, stories and atoms in shared knowledge, 2026-10-02

The shared-knowledge guidance gained a vocabulary of entries:
- atoms: one concept, theorem, technique, example or result each;
- source readings: a map from a skeleton reading, plus section notes;
- stories: a learning topic's main note, told as a chain of questions;
- author collections, which now also record how an author organizes a paper.

The index is grouped by area, and each entry names its kind. The writing guidance gained
a close-reading procedure:
- the unit is a step of the argument, including claims made only in prose;
- hard steps are filled under a "try first" prompt, each added line labelled quoted,
  imported or reconstructed;
- rigor gaps form an optional layer;
- notable details and compressions are recorded;
- claims that a source errs are kept separate until independently checked.

The exemplar guidance gained the study of an author's organization: skeleton reading,
section jobs, and the handling of prerequisites, derivations, details and discussion.
None of this prescribes a directory layout.

These changes came from a private pilot: a researcher's collection and an agent's close
reading of two papers. In that pilot:
- every verbatim anchor of the organization record was checked against the source TeX;
- the close reading found a missing truncation in one cyclicity argument and a swapped
  derivative and logarithm in a displayed formula. Both were confirmed by a second model.

Strict plugin and marketplace validation passed. Links and heading anchors in the Skill
files resolve, apart from one pre-existing illustrative path in the citation guide.

One fresh read-only `claude -p` session was run in a research-topic folder, with the
collection as an allowed directory. It was asked where close-reading notes for a paper
section should live and what they should contain, without naming the collection or AITP.
- It read the collection index first, then the README describing the kinds of entry, and
  found the section and paper templates and the existing atoms.
- It placed the reading where the collection's README says, and proposed linking the atoms
  rather than restating them.
- It listed the step-level contents the guidance names: coverage, hard steps under a
  "try first" prompt, notable details and compressions. It noted that index rows change in
  the same edit, and wrote nothing.
- It could not open linked material outside its allowed directories.

This is one read-only trial of one host. It does not test writing, Codex or Hakimi copies,
or whether the format improves learning.

## Shared knowledge read at the start of theoretical work, 2026-10-01

The shared-knowledge guidance was rewritten. A collection now holds concept
explanations, source readings with checked locators, and optional author moves,
indexed by one README. Theoretical derivation, reading and study tasks read that index
once at the start, instead of consulting it only at a recognized obstacle. The local
collection gained a Witten source collection and concept rows pointing into it.

Three fresh `claude -p` sessions were run in research-topic folders, with read-only
tools (Skill, Read, Glob, Grep), no MCP and no session persistence. They were asked
ordinary study questions that named neither the collection nor AITP.
- In every session the first action was to read the collection index, including in a
  topic that had never linked to it.
- In the first session the read was denied, because the collection lies outside the
  working directory and a non-interactive session cannot request permission.
- With the collection added as a readable directory, both remaining sessions built
  their answers on the matching rows and kept the rows' support labels. Each offered to
  retain a missing derivation as a linked note.
- One session left unresolved a point that a linked PDF settles. This suggests that a
  row's scope sentence should carry its key result.

These are three read-only trials of one host. They do not test retention edits,
interactive permission handling, Codex or Hakimi installed copies, or scientific
correctness. Hosts that confine file access to the working directory need the
collection added as an allowed directory.

## Claude Code installation, 2026-09-27

The development plugin gained a native Claude manifest and repository marketplace,
sharing the existing Skill files with Codex and Hakimi. Claude Code 2.1.283
installed `aitp@aitp-protocol` at user scope, enabled, with version
`1.1.0+claude.20260927`. Strict plugin and marketplace validation passed. The
inventory contained six core Skills and the explicitly exposed nested LibRPA
method, with no agents, hooks, MCP or LSP servers. All seven Skill frontmatters
validated, and the installer's 38-file cache matched the source.

Two fresh CLI sessions, reporting model `claude-opus-5-5`, then received ordinary
Chinese questions without Skill names or loading instructions. A copy of G01's
workspace tested recall: Claude invoked `aitp:aitp-memory`, read the main and
supporting notes, and separated agreement of two implementations from controlled
integration error. A standalone two-dimensional unitary/projection question
invoked `aitp:aitp-human-learning` and explained why a norm-preserving operator
can have zero compression to a subspace. The requested explanations completed;
workspace contents stayed unchanged. These trials exposed only Skill, Read,
Glob and Grep tools, disabled automatic memory and external MCP configuration,
and did not test autonomous writing or numerical execution.

Session initialization identified the active plugin path as the local source
checkout, although `plugin list --json` recorded a cache path. The
[Claude guide](claude-code.md) distinguishes active loading from installation
metadata. User configuration changes were limited to registering and enabling
the plugin; other settings were preserved. Prompts, events, answers and setting
backups remain outside this repository.

This verifies packaging and two bounded natural-trigger cases. It does not
establish all Skill transitions, general scientific reliability, superiority
over another host, or fixes for earlier complex-topic trigger failures.

## Installed-plugin discovery, 2026-09-27

After source commit `f393c1cd` was pushed, eight ordinary requests were run in
fresh Codex CLI sessions using the installed plugin
`1.1.0+codex.20260927155546`. Prompts named no AITP Skill and gave no loading
instructions. The sessions retained normal user configuration and plugin/Skill
discovery, with historical memory disabled and a workspace-write sandbox. All
used CLI 0.157.1, gpt-6-astra and xhigh reasoning. Initial-context inspection
confirmed the new plugin catalog without the historical memory summary or
evaluator material; command traces record actual installed-Skill reads.

The tasks reused general G01/G04/G08 and human-interaction H01–H04, plus a
nonresearch README-title edit. Recall recovered the evidence boundary without
writes; the source correction revised the argument while retaining the valid
projected result and original inputs; method repair corrected the existing
Skill and preserved its earlier output. Teaching delivered the requested complete
artifact, and the objection case verified the counterexample and retracted the
overclaim. Authorized organization established a branch folder and reciprocal
main-note links without another approval. The nonresearch edit loaded no AITP
Skill and changed only the requested title. Artifact review found the intended
behaviors in these seven cases.

The remaining case, H02, exposed an ambiguity in its expectation of a required
question: its actual request tells the agent to choose a direction. The session
read brainstorming, attributed its selection to that delegated choice, and
wrote a main line without inventing a separate researcher confirmation or new
results. It did not satisfy the rubric's question requirement, but that alone
does not establish an authorization failure. The original observation and
expectation were retained. A ninth, separately identified follow-up used the
same starting note and a request whose research target remained undecided. It
offered a conditional recommendation, kept the route unselected, and asked one
question about the value of a mechanism result without material prediction.
No Skill changed between these runs.

All six core Skills were read in relevant sessions; no case had to load all six.
All nine sessions completed. Five recovered from an unavailable `python` command
by using `python3`; these errors remain in the traces. This is one execution per
authored case, with an adaptive follow-up and coordinator review, not a blind
evaluation, an activation-rate estimate or a controlled improvement comparison.
Skill reads alone are not proof of correct behavior. Task snapshots, commands,
complete traces, outputs and assessments remain outside the published tree.
The plugin's 37 installed files matched the committed source; frontmatter,
manifest and link checks establish packaging validity only.

## Conditional human interaction, 2026-09-27

Two new Skills separate consequential research choices from interactive learning,
with conditional links from memory, research and writing. Main-note guidance now
also asks whether a returning agent can select a useful next inference and recover
the relationship and current scope of its branches. This adds no runtime, mandatory
interview or interaction ledger.

Four fresh-context subagent sessions explicitly read the source Skills and executed
the [generic interaction cases](../benchmarks/human-interaction-v0.1/README.md).
The organization case created a branch main note and reciprocal links, preserved
the original diagnostic and returned to the unanswered comparison without another
approval. The research-choice case recommended a direction and asked one focused
target question without recording the proposal as agreed. The teaching case
delivered a complete two-level calculation without an intake or quiz gate. The
objection case verified the learner's counterexample and retracted the assistant's
overstrong claim rather than diagnosing the learner as confused. Review of the
actual outputs found the intended boundaries in all four cases.

These are small authored development tasks with explicit Skill loading, not a
blind benchmark, implicit-routing test or observation of a real learner. They do
not demonstrate that the new instructions caused an improvement over the prior
Skills. A separate real-topic application, version comparisons, intermediate
failures and subsequent recovery checks are retained outside the public tree;
they do not enter a public aggregate score. No physics calculation was rerun.

All seven source Skills, including the nested domain method, passed frontmatter
validation. Plugin validation and affected local link/heading checks passed.
Packaging checks establish valid files and references, not scientific correctness
or better research decisions. Installed-cache equality is checked separately
when reinstalling; a fresh host thread is needed to load the revision.

## Independent branch folders, 2026-09-26

The source guidance now makes an agreed independent research branch a question
folder with its own `research.md`, while the nearest README maps that folder and
the two main notes explain their relationship through reciprocal links. Proposed
directions and short diagnostics do not trigger a new folder; existing suitable
branch homes are reused. An authored temporary oscillator/damping-limit
walkthrough checked the folder map, reciprocal relative links and absence of a
redundant child README. Both affected Skills passed frontmatter validation;
manifest names, local link targets and `git diff --check` passed. This was a
manual walkthrough of file roles and links, not an independent agent session or
evidence that a host will reliably activate the Skills. The local Codex plugin
was reinstalled at `1.1.0+codex.20260926080826`; the installed copies of the
affected memory and branch guidance match this source. A new host thread is
needed to pick up the installed revision.

## Complete general regression and fresh continuation, 2026-09-22

All twelve [general-v0.1 cases](../benchmarks/general-v0.1/README.md) were run
from clean fixture copies in separate Codex CLI sessions against one frozen,
dirty source snapshot. The source now also clarifies sustained route relevance,
opening synthesis and provenance, early provisional results in job guidance,
and the surviving use of a result when recalling why a route changed. Distill's
existing method-versus-concept rules were tested without adding new obligations.

All twelve completed cases received 2/2 under the published semantic rubric.
G01/G02 made no writes; G03 added supporting detail; G04 preserved a valid
projected result while correcting the full equation; G05 separated imported,
derived and conditional contributions. G06 retained the missing target relation
despite one bounded numerical refinement, while G07 resolved its defined target
with a controlled bound. G08 repaired the existing method, G09 retained a concept
without a new Skill, and G10 reprocessed records without rewriting its baseline.
G11 integrated its first provisional result; G12 left the workspace byte-identical
and identified the pending correction. Original inputs and historical outputs
survived; G06/G07 appended new grid rows while preserving the old rows.

A fresh G04 continuation received the actual first session's files without its
chat or an evaluator repair. It recovered the changed premise, incompatibility
and surviving old result, and made no writes. A separate artifact/trace review
confirmed the G01, G06 and G08 scores, including their acceptable alternatives.
One G04 attempt was interrupted by model-service capacity before completion;
its trace and unchanged workspace were retained, followed by a clean successful
retry. This infrastructure interruption is separate from a scientific score.

All scored CLI runs used gpt-6-astra with xhigh reasoning and explicitly loaded
the same Skill snapshot. User config, memory injection, automatic plugins, apps,
hooks, multi-agent spawning and host Skill discovery were disabled. Tasks,
commands, JSONL events, final answers, before/after files and usage were retained
outside the published tree. The twelve completed runs used 124 command executions
and 2,130 seconds of summed session time; runs overlapped. Reported usage totals
were 1,955,412 input tokens, including 1,578,240 cached tokens, and 46,768 output
tokens. Input usage includes repeated context across calls. These counts exclude
the interruption, continuation and preliminary pilots; they are not a cost saving.

Four earlier new-context subagent pilots remain separate evidence under different
host conditions. Their G02 answer omitted the old comparison's surviving use
(1/2); the later source clarified historical recovery. No controlled old-versus-new
or ordinary-note comparison was executed, so the later success does not establish
causal improvement or superiority. This authored development set is not an unseen
physics test, an implicit-activation measurement or general reliability evidence.
Source validation passed; the installed plugin cache was not updated.

## On-use revision of an outdated main note, 2026-09-22

The [on-use revision exercise](../benchmarks/on-use-v0.1/README.md) supplies a
chronological note whose opening drops a normalization condition and whose next
test is already complete. Correct derivations and raw observations are present.
The ordinary research-continuation prompt does not request a rewrite. This is
a separate development case; the existing general-v0.1 suite remains unchanged.

Three fresh-context subagent sessions explicitly loaded a snapshot of the updated
AITP source. The first integrated the supported answer, valid conditional proof,
reason for the earlier mistake and actual continuation into the main note. Only
research.md changed; supporting derivations and raw observations were preserved.
A fresh second session received that actual output without the first conversation
or new findings. It recovered the recorded conclusions and left all files
byte-identical. A separate read-only session started from the original fixture,
reported the correct answer and pending main-note correction, and also left all
files unchanged. Artifact and response inspection gave 2/2 for each of the three
checks under the published rubric.

Actors received neither the authoring conversation nor evaluator material.
Host-injected instructions and catalog metadata were not independently filtered;
complete per-tool traces and token/time costs were not separately archived.
These observations cover one synthetic task, not implicit Skill activation,
an old-versus-new comparison, a background upgrade or general research quality.
Source snapshots, before/after files, actor deliveries and assessment records stay
outside the published tree. Affected frontmatter, plugin manifests, local links
and heading anchors passed validation. The installed plugin was not updated.

## General research-work benchmark, 2026-09-22

The [v0.1 general benchmark](../benchmarks/general-v0.1/README.md) contains 12
small synthetic tasks, copyable workspaces and separate evaluator expectations.
Its materials exercise recall, correction, exposition, route selection, method
learning, provenance and scoped handoff. It adds no runner or runtime to AITP.
The corpus is an openly authored development/regression set, not unseen tasks.

Checks covered required case files, relative links, Python syntax, supplied
arithmetic and the intentional differences in paired fixtures. Three new-context
subagent pilots explicitly used a copied current AITP source bundle: G07 completed
a justified numerical refinement and integrated the result; G08 repaired an
existing averaging method and retained the original records/output; G12 provided
a read-only provisional-result handoff with no workspace changes. The evaluator
inspected the resulting files and before/after differences. These observations
support task readiness, not a general performance or automatic-activation claim.

The pilots did not inherit the authoring conversation or receive evaluator files.
However, complete isolation of host-injected instructions, memory descriptions
and the installed Skill catalog was not established. Full per-tool traces and
token/time costs were not separately archived. Rubric consistency was refined
during authoring, so these are not a preregistered comparative baseline. Exact
source/fixture copies, actor deliveries and artifact observations are retained
outside the published tree. At that point nine cases remained unrun; those pilots
did not test cross-session continuation, an ordinary-note control or an
optimized-version comparison.

## Branch agreements and reusable learning, 2026-09-20

An authored synthetic walkthrough applied the revised source Skills to a
two-state basis-change investigation. A proposed branch first retained its
question without executing the calculation. A supplied synthetic agreement
then settled its objective, method and stopping boundary; routine preparation,
calculation and note updates proceeded within that scope. A later proposed
interacting-chain extension remained pending instead of becoming an automatic
next action. This was a manual application by the instruction author, not an
independent agent session or a test of implicit Skill selection.

The executed control kept an operator unchanged while transforming its state.
Its spectrum agreed, but its action and expectation did not. The consistent
transformation passed those checks; a different two-state example reproduced
the distinction. The branch linked its script and raw output, and its parent
retained both the result and the untested larger target. The same evidence
extended an existing shared explanation and corrected an existing local Skill,
without a duplicate note or method. Retention did not depend on encountering a
conceptual obstacle during the calculation. An unchanged recall made no edits.

The fixture and authored observations remain outside the published tree.
Checks cover affected Skill frontmatter, local link targets and heading anchors,
host manifest names and paths, and preservation of unrelated pre-existing edits.
They do not establish autonomous agreement handling, reliable learning triggers,
scientific productivity or behavior of an already installed plugin cache. No
runtime, hook or evaluation framework was added.

## Corrections and detached supporting notes, 2026-09-14

An authored synthetic walkthrough started with a main note that no longer cited
an earlier argument, a second topic that still relied on it, and a valid local
result. Searching by claim and filename recovered the earlier note and its use.
The retained argument received a visible correction, a link to the replacement
reasoning and an entry in the existing README. Its dependent conclusion was
withdrawn; the valid local result was unchanged and no notes were deleted.
This was a manual application, not an independent agent session. It does not
establish exhaustive discovery, automatic synchronization or error detection.

## Main and supporting teaching notes, 2026-09-14

The revised writing guidance was applied in an authored walkthrough to an
existing geometry explanation and its main-note use. This was a manual reading
and calculation exercise, not an independent Codex session or activation test.
With explicit elementary prerequisites, the linked state-vector calculation
and patch argument supply a nonzero example and its obstruction. A later
multi-state claim instead uses a construction outside those prerequisites;
the walkthrough identifies that missing teaching step without classifying the
correct expert formula as a mathematical error. The source notes were unchanged.

The walkthrough also distinguishes an imported theorem from a proof supplied
in the note, teaching depth from journal typography, interactive feedback from
an approval gate, and an ordinary follow-up from a durable memory update. It
retains the whole topic's question while allowing one supporting argument to
receive detailed treatment. Private source material and the walkthrough record
remain outside the published tree.

Skill frontmatter, host manifest identity and Markdown links were checked.
These are bounded standards and packaging checks. No new reader study, model
writing comparison, manuscript build or research-productivity advantage was
established by this revision.

## Independent Codex CLI trials on 2026-09-14

Six new CLI sessions exercised the development bundle on isolated examples:
a new LibRPA numerical account, a formal-theory continuation, ordinary recall,
a repeat with host memory disabled, a filtered no-AITP comparison, and an invalid
initial attempt to disable AITP. These are actual model sessions. Their prompts,
input copies, generated notes, events and exact plugin snapshot remain in the
local review archive pending the researcher's publication review.

The AITP sessions selected the relevant Skills without a named Skill request.
The numerical account retained the missing execution evidence. The theory
session integrated a correct planar constraint count into the main argument,
linked a full derivation and preserved the original torus note. Both recall
sessions left all topic files unchanged. No manuscript was created.

The first plugin-disable override failed to remove AITP from the model input;
that run is not a valid no-AITP control. Filtering the five AITP Skill files
removed their descriptions and reads. The filtered session obtained the same
correct matrices and numerical limitations. AITP added a main-note link to the
README, but its main note was longer (894 versus 788 words). Both contained
peripheral source-coverage detail. This one example establishes no reasoning
or productivity advantage.

Host memory was injected in the initial sessions; ordinary recall and the
filtered comparison also searched it despite the requested topic boundary.
Consequently these are not fully isolated from historical context. The recall
repeat explicitly disabled host-memory injection and generation; its recorded
input and reads confirm recovery from the local topic with AITP, without a
host-memory search or any file change. No global settings were altered.

Actual Codex input listed the four core roles plus the nested LibRPA method;
Hakimi had discovered four containing bundles. Documentation now distinguishes
these catalogs, and the domain method explicitly routes topic work to memory.
The method also explains why unequal weights and complex entry checks remain
necessary. The trials tested the archived bundle before those narrow edits.

No LibRPA build, production calculation, Si-to-BN distillation/reuse or requested
LaTeX paper was tested. These cases do not measure long-term research quality
or a general activation success rate. Ordinary research requires no evaluation
ritual or additional runtime.

## Earlier authored domain-method and review-draft checks

The current development work uses LibRPA and a formal topological-model example.
Its research drafts remain outside the public tree pending author review. The
former oscillator exercise is retained below only as historical evidence.

The LibRPA method was walked through on a public complex Hamiltonian-mixing
test. Independent exact arithmetic checked its grid and band expectations and
a second mixing fraction; no LibRPA binary was built or executed. The formal
draft reconstructs a torus constraint count from a primary source. Temporary
binary linear algebra checked commuting supports and constraint ranks on two
small tori; this does not compute an anomaly or replace the general argument.

Note-only versus requested-manuscript routing and the no-write, supporting-only
and consequential-correction choices were reviewed against those drafts.
These are authored walkthroughs, not independent sessions or measured activation
reliability. No comparison with an agent without AITP was performed. The source
and build separation in the method is guidance, not evidence of a new physical
result or a validated OML integration.

All five Skill files (four entrypoints and the nested LibRPA method) passed
frontmatter validation. All 94 relative Markdown targets and section links
across the repository and local review drafts resolved. Both host manifests
validated and the development bundle was reinstalled locally in Codex and
Hakimi. All 24 source files matched each installed copy, without obsolete example
files. Hakimi discovered four enabled core Skills without diagnostics. The
published 1.1.0 release was not changed by this local installation.

## Historical 1.1.0 example

The [oscillator example in 1.1.0](https://github.com/bhjia-phys/AITP-Research-Protocol/tree/v1.1.0/plugins/aitp/examples) was a small,
self-contained teaching exercise. It illustrates a coherent main argument,
linked derivation and calculation, a useful failed shortcut, and direct method
distillation. Its read/write walkthrough is authored, not an independent session.

For that release, the eight table rows were checked with exact rational
arithmetic. Gaussian normalization and kinetic/potential expectations were also
checked by direct numerical quadrature. The analytic lower bound, rather than
the table or quadrature, establishes the example's ground-state claim. The
frequency-two instance exercises the distilled procedure within the same model.

Skill frontmatter, plugin manifests, local Markdown links and section targets
were checked. The public tree and new commit were reviewed for private project
content and workstation paths. These checks establish packaging and the stated
bounded mathematical example; they do not establish AITP's research superiority,
reliable automatic activation or reduced user effort.

The writing Skill retains separate formal, computational/mixed and manuscript
guidance. Its optional TeX starter previously compiled with two passes and both
pages were inspected; it has not changed in this release. The inherited style
and bibliography files retain their original contents. A whitespace warning in
that bibliography style is inherited, not a change to the example's calculation.
The optional Witten corpus references retain their attribution and reading
limits; their literature claims were not revalidated by these packaging checks.

Earlier project-specific examples and evaluation records are preserved locally
and are not part of the public teaching example. This release makes no controlled
comparison with ordinary notes or another memory tool. Further evaluation should
use a separate task and evidence rather than interrupt ordinary research with
mandatory self-assessment.

## Topic-entry walkthroughs after 1.1.0

The added entry guidance and optional layouts were exercised in temporary
directories using the generic oscillator material. These were authored
walkthroughs with simulated user input, not independent model sessions:

| Case | Walkthrough outcome |
| --- | --- |
| New request with an unspecified physical domain | Asked whether the problem was on the whole line or had hard walls; created no topic files while that choice was unresolved. |
| New request specifying an English whole-line study and its working home | Wrote only a README and a small initial research note; proposed calculations remained unperformed, with no empty asset directories. |
| Existing whole-line results and an unfinished hard-wall proposal | Asked about question grouping, then used a simulated answer choosing separate questions. Reused the existing main note, added an explicitly open hard-wall note, and explained both locations in the README. |
| Follow-up about the recorded whole-line minimum | Answered from the existing argument without another intake question or a memory write. |

The original files in the organization case remained byte-for-byte unchanged;
the width table had one copy. Relative links in the generated notes were checked.
These exercises expose the intended distinction between clarification and an
ordinary open research question. They do not show that an independent agent will
reliably make that distinction or complete a real research project. No new live
research migration or scientific-performance comparison was performed.

## Main-note routing and writing walkthroughs

The memory-first revision was exercised with further temporary oscillator
materials. These were again authored walkthroughs, not independent sessions:

- An existing TeX main note was found through its README and used for recall;
  no duplicate `research.md` was created and no source file changed.
- Existing derivation and calculation files without a main note were synthesized
  into a compact argument while retaining their original contents and locations.
- A verbose draft with a duplicated table and an unsupported exactness claim was
  shortened. The independent lower bound, its domain and the reason the potential-
  only shortcut failed remained in the main text, with links to detailed evidence.
- Three exact width values for frequency three were added only to supporting
  calculations; the still-accurate main note remained unchanged.
- An initial quartic-oscillator question retained an explicitly untested working
  hypothesis and missing error assessment, without presenting planned work as done.

These cases check concrete editorial outcomes and source preservation. They do
not measure implicit Skill selection, automatic ordering of Skill loads, or
scientific productivity. Memory-first routing is expressed in Skill instructions
and host entry guidance; no executable router or mandatory session hook was added.

## Installable release

The versioned plugin ZIP was installed through Hakimi's native URL download,
archive extraction and manifest-discovery path in an isolated installation,
using a temporary local HTTP server. It discovered four enabled core Skills
without diagnostics. All local Markdown links in the extracted plugin resolve
inside it. The package includes both host manifests and the repository license.
The Codex installation command was checked against CLI 0.154.0; it selects the
repository marketplace at the release tag. These are installation checks,
separate from scientific or independent-session behavior evaluation.

## Journal-based Markdown templates, 2026-09-14

The new compact, theoretical and computational starting files were designed
after reading the APS `apstemplate.tex` and `apssamp.tex`, the APS author guidance
for PRL, PRX and PRB, and the official `jhepexample.tex`. The linked
[source guide](../plugins/aitp/skills/aitp-writing/references/journal-templates.md)
distinguishes the journal packages from AITP's original Markdown adaptations.

A fresh Codex CLI session used the installed AITP development bundle to revise
an isolated theoretical learning note. The command disabled host-memory use and
generation. Its recorded reads include memory and writing guidance, the new
theory template, the complete main note and both supporting derivations. It
produced an abstract, scientific motivation, precise setup, central argument and
interpretation. Inspection retained the boundary prescription, independent-rank
and sign reasoning, a failed transfer of an argument, and the unresolved
scientific continuation. The supporting notes and README were unchanged.

That raw output retained TeX-style math delimiters from its input. The review copy
normalizes only those delimiters to Markdown dollar notation; the exact model
output is preserved separately. The templates and main-note guide now explicitly
state that notation. This final instruction addition was not independently
retested. A separate computational-method example was an authored walkthrough:
it keeps the discriminating analytic comparison in the main argument and moves
the full source-coverage report to a linked note. The two examples are local
review material and are not included in the public plugin.

Checks covered source preservation, local link targets, the displayed benchmark
arithmetic, Skill frontmatter, manifest identity and installed file equality.
These are bounded editorial and packaging observations. No rendering test,
new physical simulation, automatic-trigger reliability study or research-efficiency
comparison was performed. A readable article structure does not itself establish
the validity or novelty of the underlying research.

## Supporting citations and shared theory, 2026-09-14

The added guidance was applied to local working material: a concept explanation
links a scoped theorem, that proof links its prerequisite, and a second concept
route connects a background field to a boundary-variation calculation. Topic
notes reuse those explanations without moving their physical hypotheses into a
shared fact. The examples distinguish related geometry from an identified
physical response and preserve a failed use of a global potential.

A computational starting note pairs a block-inverse identity with specific source
entrypoints and an explicitly unperformed convergence investigation. Existing
research outputs and historical conclusions were preserved. Cross-file equation
references give the linked note, scientific meaning and local number. Visible
prose equation labels avoid assuming support for automatic tags or cross-file
TeX references.

These were authored applications and navigation/argument checks, not independent
agent sessions. Local target existence, affected Skill frontmatter and plugin
manifests were checked. No particular Markdown renderer, recursive-recall behavior,
scientific productivity advantage or new physical computation was validated.
The working examples stay outside the public repository for researcher review.

## Shared-theory triggers and discovery, 2026-09-14

An authored walkthrough checked the new boundary: a fluent derivation or routine
plotting task does not initiate shared-theory search, while an actual conceptual
gap can. The pre-creation check applies when saving a standalone concept or theorem
explanation. These routing cases are editorial applications, not observations
from an independent agent session.

A concrete local lookup used "geometric phase" and "Berry phase", phrases that
previously produced no exact-phrase matches. A short README discovery entry now
finds the existing explanation under either phrase. Following that link exposes
its single-state scope and explicit lack of a multi-state derivation; finding a
related page therefore does not justify claiming the extension is already covered.
No duplicate concept page was created or scientific body changed. Related search
terms guide retrieval without declaring the terms equivalent.

Checks covered affected Skill frontmatter, local file targets, manifest identity
and installed file equality. No runtime or search framework was added. This
walkthrough does not establish automatic-trigger reliability, exhaustive semantic
retrieval or a research-speed advantage. The local application stays outside the
public repository.

## Research-cycle consistency review, 2026-10-08

Development version 1.2.1 clarifies context reuse, parent/branch propagation,
actual evidence-route inspection, scoped verification, persistent exemplar-author
choices and the timing and transfer checks for method distillation. Root and
topic-tree detail now have focused references; the mandatory entry retains their
essential constraints. No runtime hook or recording framework was introduced.

Three synthetic tasks were executed by fresh agents using either the original
1.2.0 snapshot or a revised snapshot: completed-data integration with two
scientific users; reconstruction of a supplied original paper passage; and
repair of an existing complex basis-transformation method. Each configuration
met all fifteen initial artifact-based expectations. Execution was independent;
the coordinating assistant's grading was not blinded. There was one run per
task/configuration, so these results do not establish a general performance
advantage, automatic triggering or a reliable failure-rate estimate.

Artifact review found a regression outside those initial expectations: the
first revised calculation run copied measurements and settings into the root
note. The old run did not. Restoring the root-scope constraint to the mandatory
entry was followed by one fresh same-prompt retest, which kept the root at the
level of shared implications. That added diagnostic is reported separately,
not retroactively hidden in the original pass count. Calculation and reading
used the first revised snapshot; distillation and the targeted retest used the
corrected snapshot. Private fixtures, outputs, preservation checks, scores and
the review page remain outside this repository. Timing and token comparisons
were not available from the host and were not estimated.

The accompanying topic review followed changed claims to existing source or
numerical support, preserved original evidence and anchors, and repaired stale
continuations and parent duplication. This is editorial and navigation evidence,
not a fresh scientific recertification of the research archive or evidence of
human learning, physical insight or model-independent behavior.

## Algorithm-choice timing, development version 1.2.2

Consequential numerical-method choices are now explicit even when the physical
equation is unchanged. The entry cycle, research procedure and LibRPA guidance
route unresolved choices through human brainstorming before dependent edits or runs.
Reserved choices, prior selections and explicit delegation retain their actual scope.

A coordinating-assistant walkthrough examined an unagreed solver replacement,
repair of an agreed algorithm, an authorized two-method comparison, explicit bounded
delegation, an unanswered required choice, and an accuracy-changing shortcut.
The first, fifth and sixth require a choice before adoption; the other cases permit
the already authorized work without repeated questions. This was an instruction
walkthrough, not an independent executor trial or an automatic-trigger measurement.
The earlier 1.2.1 trial counts are not reused as evidence for this revision.

## General rules and local agreements, development version 1.2.3

The algorithm-choice default now explicitly belongs to AITP and needs no local
standing-agreement entry. General procedures stay in their owning Skills; workspace
instructions supply local context, personal preferences and actual overrides, while
root agreements retain concrete workspace-wide delegations or exceptions.

A coordinating-assistant walkthrough checked a workspace with no personal agreement,
an explicit bounded delegation and retention of a concrete topic decision. The first
still requires a consequential method choice, the second proceeds within its scope,
and the third records the scientific choice without duplicating the general protocol.
This is a placement and instruction walkthrough, not an independent execution test.

## Skill-selection boundaries, development version 1.2.4

This revision corrects two contradictory routes: sharing a research note no longer
selects manuscript production, and close reading no longer prescribes a try-first
prompt for every difficult step. Practice is conditional on the learner's purpose;
a requested complete explanation has no exercise or response gate. Memory's
description scopes status and continuation to research. Verification's description
and writing's route distinguish a requested review or changed consequential claim
from routine wording edits and unchanged, still-applicable checks.

The memory entry selects guidance for the current unmet need and reconsiders it when
new evidence changes that need. A link is not itself a call. The cycle explicitly
routes new, changed or disputed consequential claims to verification and reaches
the existing write/distillation decision at a natural pause or handoff. It neither
loads every Skill nor makes every turn a write or a distillation opportunity.

The coordinating assistant checked these concrete boundaries against the revised
instructions. These are authored walkthroughs, not independent executions or a
measurement of automatic selection:

| Request and evidence | Behavior required by the instructions |
| --- | --- |
| Explain the recorded topic status, with no new evidence | Recover the relevant account and answer without edits, new calculations or method distillation. |
| Change a README title in an unrelated software project | No physics research cycle follows merely from the word "edit". |
| Prepare a Markdown research note for sharing; it reports a 90% acceptance rate from 12 accepted of 15 attempts | Trace the arithmetic, correct or report 80% according to editing scope, and retain Markdown; no manuscript production. |
| Produce the requested teaching PDF from a completed derivation | Writing's manuscript handling applies; preserve teaching depth and deliver the requested artifact. |
| Explain the entire missing projection step without exercises | Supply the complete inference; do not insert try-first questions or stop at a skeleton. |
| Practise that projection step interactively | Offer a targeted attempt and use the response to choose the next explanation; do not infer mastery from silence. |
| Change only wording around an unchanged, checked result | Check preservation of meaning; no fresh scientific audit, exemplar reading or distillation solely because wording changed. |
| A new calculation contradicts the main note's conclusion | Check the discrepancy before adopting it, preserve raw evidence, and integrate the supported change into the owning note and affected uses. |
| Add a diagnostic detail that changes no conclusion or next step | Keep it in the existing support account; leave an accurate main note and parent unchanged. |
| An implementation bug violates the already selected algorithm | Repair it and run relevant checks; no repeated algorithm-choice question. |
| A faster proposal changes the solver or drops matrix terms, without a settled choice or delegation | Present the consequential choice before dependent implementation or runs. |
| A demonstrated diagnostic corrects an existing method, versus an interesting theorem summary | Repair the existing method at a natural pause; keep the theorem's explanation in notes, without a duplicate Skill. |

The hand review found no remaining conflict in these routes. That result does not
establish that an independent model will select or execute them reliably. Earlier
natural-language discovery trials concerned older versions; their outcomes are not
relabelled as tests of 1.2.4. A future independent trial should withhold Skill names
and loading instructions, inspect actual reads and resulting artifacts, and check
both missed work and unnecessary work. Packaging and installed-host discovery are
separate checks, not substitutes for that behavioral evidence.

All eight Skill frontmatters, three 1.2.4 manifests and 361 local links passed
structural checks. All 49 plugin files matched the installed Windows Codex, WSL
Codex, Claude Code and Hakimi copies. Fresh passive Codex loaders on Windows and
WSL discovered eight enabled Skills from 1.2.4 with no AITP errors; no model turn
was started by those checks. Hakimi's native manager reported seven core roots
and no errors. These results do not imply that already-running conversations
reloaded their instructions.
