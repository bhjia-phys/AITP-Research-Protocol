---
name: aitp-memory
description: Start AITP research work and substantive physics discussions here. Runs the research cycle around research.md, the backbone at every level (root, topic and branch) - recover the context, decide what the task settles, use the skills it needs, keep outcomes in their homes and reachable, and close with the warranted next move. Also answers status questions and resumes on "continue".
---

# The research backbone and the research cycle

## The research cycle

Start research work and substantive physics discussions here; a skill opened directly
applies the same cycle. Within an ongoing task, reuse the context already recovered.

1. Recover the request, existing agreement and relevant backbone note; without a topic,
   start from the root without creating one.
2. Read the whole argument before revising it, the relevant parent passage for branch
   work, and the knowledge index once for theory or study.
3. Explain what the task should settle; identify the uncertainty and use the needed
   skills within the agreed scope and plan review.
4. Read, reason, synthesize or experiment; check consequential claims before relying
   on them.
5. Retain durable outcomes in their primary homes; repair reachability and affected uses
   within scope. Read-only work makes no edits.
6. Close with the supported answer and warranted next move: do authorized routine work,
   propose consequential choices, and retain agreed directions in the backbone.

A status-only request (where things stand, what is running, a topic's history or
connections) is answered from the existing records without edits, as
[status and continuation](references/status-and-continuation.md) describes. The cycle
repeats when evidence changes the question; it is not a fixed pipeline, and one task may
pass through several skills without returning to the researcher. Explain an intended
consequential change before making it, without turning every explanation into a request
for approval. No route announcement is needed.

`research.md` is the researcher's long-term memory and the backbone of the research.
Each one is a developing article about the question at its own level: a root note for
the whole research, a note for each topic, and notes for branches inside topics. The
other skills are processes that grow it:
[aitp-human-learning](../aitp-human-learning/SKILL.md) for study and conceptual
difficulty, [aitp-human-brainstorming](../aitp-human-brainstorming/SKILL.md) for the
researcher's choices, [aitp-research](../aitp-research/SKILL.md) for investigation,
synthesis and computation, [aitp-verify](../aitp-verify/SKILL.md) for checking claims,
[aitp-writing](../aitp-writing/SKILL.md) for notes, papers and PDFs, and
[aitp-distill](../aitp-distill/SKILL.md) for reusable methods. This skill keeps the
backbone and runs the cycle around every task.

Help the researcher make the whole research clear. A main note should converge
toward a coherent account of a question, its reasoning, evidence and remaining
obstruction. Convergence can be a qualified result, a precise failure, or a
better question; do not force success or erase uncertainty to make a neat paper.
This account should help a returning agent choose the next useful inference:
what the main question needs, which branch can supply it, and which completed or
failed route no longer needs repeating. It is not a queue of all unfinished work.

## Read when

| When the task involves | Read |
| --- | --- |
| The root note, a seed, or a discussion outcome without a topic | [The backbone](#the-backbone-at-each-level) and [discussion outcomes](#where-discussion-outcomes-land) |
| An agreed new topic, or scattered material that needs a home | [Starting or organizing a topic](references/starting-a-topic.md) |
| Where a script, figure, input or output belongs | [Asset placement and links](references/local-assets.md) |
| Source trees, builds, environments, tests and runs | [Numerical assets](references/numerical-assets.md) |
| Shared concepts, source readings or a pointer row for a result | [Shared knowledge](references/shared-knowledge.md) |
| Where a new result, failure or correction goes | The [placement table](../aitp-writing/references/research-note.md#add-move-and-remove-material-without-losing-the-thread) |
| A note with a parent or branches | [Keeping the topic tree clear](#keep-the-topic-tree-clear) |
| Planning a stage of work | [Plans](references/plans.md) |
| Handing work to another session or model, or work in parallel | [Hand-offs and parallel work](references/handoffs.md) |
| Where things stand, a topic's history or its connections | [Status, history and continuation](references/status-and-continuation.md) |
| A bare "continue" | [Continuing the authorized task](references/status-and-continuation.md#continue-the-authorized-task) |

## The backbone at each level

| Level | What its main note owns |
| --- | --- |
| Root: the `research.md` at the top of the research workspace | The researcher's overarching questions and directions, as they state them; why each topic serves them; consequential cross-topic connections and turning points; unattached seeds; agreed directions; standing agreements about what agents may do without asking. Independent directions can stay independent. |
| Programme, only for a real cross-topic question | The question connecting several topics, their combined implications and the missing relation. Shared software alone does not justify one. |
| Topic | A defined research or learning question: its assumptions, developing answer, decisive reasoning, evidence, limitations and what each branch contributes. |
| Branch | An independent subquestion: its origin and parent relation, agreed scope, method, answer, limits, continuation and what its outcomes mean upstream. |

Each opening states the question, the current answer at its supported strength, the
approach, the decisive limitation and the next step. At the root these describe the
directions and their unresolved relationships; do not invent a single thesis or a
priority order. The root never copies topic answers, measurements or progress; it owns
their implications for the larger questions. The workspace README stays the folder map.
The root links it, the shared knowledge index and each top-level topic, and each
top-level topic links back to the root.

Start a root note only from existing notes and the researcher's documented choices, with a
link to where each choice is recorded, and leave unstated priorities unspecified. When a
topic's role, an important connection, a direction or an agreed next choice changes, the
session that changed it updates the affected root passage before handoff, within its
editing scope. Routine evidence updates do not by themselves require a root edit; update it
when their implications change a direction or connection. One coordinating writer
integrates concurrent root edits.

**Reachability.** Every retained paper, question, derivation, numerical experiment and
output has one primary home and an intelligible link path from the root and from the
main note that uses it. The path may pass through supporting notes, source maps, READMEs
or the knowledge index; keep it short enough to follow. Maintain it when retaining,
moving or correcting material, and say what each link establishes. Useful failed or
detached work stays reachable through an "earlier approaches" passage or an index that
the main note reaches. Unread sources and unavailable remote data carry honest labels
and precise locations. Temporary caches and tool environments need no research entry.

## Where discussion outcomes land

A substantive physics discussion needs no topic. Keep what is durable; a clarification
that is already recorded needs no write.

| Outcome | Primary home, and its route from the backbone |
| --- | --- |
| A concept or framework learned | An existing or new explanation, source reading or story in the [shared collection](references/shared-knowledge.md), with its index row. Root → knowledge index. A checked locator can be enough; write no empty entry per term. |
| A derivation worth keeping | The source's section note or a topic's supporting note; with neither, `notes/<question>.md` beside the root note, linked from the root in context. State assumptions, checks and unresolved steps; do not manufacture a topic. |
| A connection between topics | One explanation in a supporting note, linked from the passages that use it in both topics. The root states its wider implication, marking a conjecture as such. |
| An open question or idea | A short seed in the relevant main note, or in the root when unattached: the question, why it matters, what prompted it, the missing evidence and a possible first check. Mark it uncommitted; link longer reasoning. |

A seed becomes a proposed branch when it has a distinct question, useful grounds, a
discriminating first action and a continuation worth pursuing. Propose it inside an
existing topic when it serves that topic, otherwise as a new topic linked from the root.
Once it is agreed, or already covered by the current request or an existing applicable
agreement, build its home without further instruction: folder, `research.md`, links in
both directions and the README map. Revisit seeds when related work changes their grounds; merge duplicates,
replace a resolved seed with its answer and link, or keep the reason for setting it
aside. Seeds are possible directions, not a queue or a priority order.

Research results stay in their research account, including a standalone derivation
note. A reusable result enters the shared collection only as a provisional index row
naming the question and citing that account; an atom written from a research result
needs the researcher's confirmation.

## Locate the main note, then establish the current task

This is step 1 of the cycle, used before topic-specific derivation, coding, analysis or
substantial writing, even if the user did not ask to record anything. A standalone
physics question does not by itself establish a persistent topic; its durable outcomes
land as [described above](#where-discussion-outcomes-land). Within an ongoing task,
reuse the current topic context; entry does not mean restarting this process on each turn.

First check for the designated `research.md`, or the established main note in
another format. Use the working folder and README links to locate it; do not
assume an unfamiliar subdirectory or missing literal filename means no note exists.

- If a main note exists, recover the context needed by the request as described
  below. Apply [on-use repair](#repair-an-outdated-main-note-during-use) when the
  encountered account has a material gap; substantive revision needs the whole argument.
- If none exists and the researcher has agreed to a persistent topic, or authorized
  consolidating existing material, use [starting or organizing a topic](references/starting-a-topic.md).
  Distinguish an empty project from existing research without a synthesis. Suggest
  the [optional layout](references/local-assets.md#optional-layouts-for-a-new-home)
  when a home is needed, reuse available assets, and draft a small `research.md`
  once the question and location are clear. Do not manufacture completed results.
- For a discussion, a missing topic note is not a reason to create one: locate the root
  through the workspace instructions and maps, and place durable outcomes as the
  [outcome table](#where-discussion-outcomes-land) describes. If the workspace has no root
  yet, do not infer a topic or reorganize the workspace; create a minimal root only within
  authorized organization, and otherwise name the missing navigation and continue the
  permitted discussion.

Connect the user's request to that understanding and state the current task
briefly: what this session should resolve or produce, and what would settle that
task. A historical next step is context, not a substitute for today's request.
No separate goal file, host Goal object or fixed research stage is required. Associate a
host's goal, research line or loop with the existing notes it concerns; do not create
topics to mirror host objects. A host's "completed" describes the task, not an accepted
result.

When work turns to a useful side investigation, retain why it arose, its working
home and how it relates to the originating question. Use
[research's agreement boundary](../aitp-research/SKILL.md#agree-on-consequential-research-choices)
for independent branches and material changes of stage objective or route.
Retain the agreed objective, approach, stopping or reconsideration criteria and
unresolved choices in the branch's `research.md`; distinguish proposals from
decisions actually agreed with the researcher. An agreed direction change is
worth recording before results exist, including why the earlier route changed.
Use [following a side investigation](../aitp-writing/references/supporting-notes.md#follow-a-side-investigation)
to give an agreed independent research branch its own folder and `research.md`,
unless a suitable branch home already exists. Connect its main note and the
originating argument in both directions, and map the folder in the nearest README.
Keep shorter diagnostics in the existing question rather than making a new topic
for every task.

Use [aitp-human-brainstorming](../aitp-human-brainstorming/SKILL.md) when a missing
decision changes the problem, branch scope or intended document. It resolves
human choices before dependent work, without repeating settled questions or
treating missing evidence as missing intent. Within authorized organization,
infer clear main/branch relationships from the material and establish or reuse
their folders and notes; ordinary placement does not need another approval.
Making an existing branch legible does not authorize starting a new investigation.

Then use [aitp-research](../aitp-research/SKILL.md) for the scientific work and
[aitp-writing](../aitp-writing/SKILL.md) when drafting or revising the argument.
Reuse this established context when those Skills refer back here.

## Understand the whole note before changing it

Locate the user-designated main note, normally `research.md`. Several independent
questions may share a code workspace; choose the relevant note rather than
forcing them into one paper. Focused recall reads the relevant passages and
qualifications; branch work also needs its relationship to the originating question,
recovered as in [keeping the topic tree clear](#keep-the-topic-tree-clear).
Before a substantive revision, read the complete main argument, including its
conclusion and open questions. If it exceeds one read, read successive sections
until it is understood. A title, recent tail, abstract or keyword hit is insufficient
for that revision. Reuse a complete, known-current reading within the same work
interval; ordinary turns do not require reading it again.

For whole-topic recovery or substantive revision, privately recover the central
question, physical or mathematical setting, operative assumptions, job of each
section, strongest established result and most consequential gap. This is
comprehension, not another file or mandatory visible table. Reconcile the user's
current request with that whole-topic view. Recover why the relevant branch
matters and what result could change the main answer, rather than selecting
the most recent unfinished task automatically.
When a related main note owns a later scope decision, consult that decision
before recommending continuation across topics. Retaining an older experiment
does not restore its former priority or override the researcher's chosen route.
For a broad exploratory topic, understand the candidate questions and why they
are being compared; do not invent a settled hypothesis or final result.

Then follow links when the task needs more than the main note provides. For a
recall question, answer from the note's clearly supported conclusions and cite
the note; do not recertify them by rereading every source. Describe them as the
recorded understanding, not a fresh independent verification. Inspect source
evidence for a disputed or missing detail, conflicting claims, time-sensitive
state, a changed conclusion, or a new calculation that relies on it. Linked
notes may explain concepts, complete derivations, or identify code and runs.
Do not recursively load every linked file. A historical next action is not
today's scientific state or execution permission.

When asked why a route changed, follow the specific retained comparison or
decision: explain the reason, what the earlier result still supports and what
it no longer establishes. If a choice's reason was not recorded, say so rather
than reconstructing a historical fact from a plausible present-day rationale.

If the note changed externally, re-establish its complete current argument
before editing. If it is missing, establish the scope as above and use the
researcher's material to start a small coherent note; identify unexamined
material without manufacturing conclusions.
Do not initialize a ledger or reconstruct all archived sessions merely to begin.

## Repair an outdated main note during use

As a topic is used, assess the encountered account against the current
[main-note guidance](../aitp-writing/references/research-note.md). If its organization
obscures the supported answer, decisive conditions, evidence, consequential history or
continuation, repair it within the current topic-editing authorization without waiting for
a separate maintenance request; for example, a dated update queue whose opening still
promotes a superseded claim, or completed work still presented as the next prerequisite. A
durable improvement in recovering the argument warrants an edit even without a new
scientific result.

Understand the complete argument and the evidence needed first, then follow writing's
[adaptation guidance](../aitp-writing/references/research-note.md#adapt-an-existing-note-during-use):
preserve the researcher's question, useful reasoning, original observations and reasons for
earlier routes; missing evidence or reasons stay unknown. Judge the content, not a Skill
version or template: a usable note with different headings needs no rewrite, an unchanged
revisit makes no further write, and ordinary recall needs no library-wide audit. Explicit
read-only or restricted scope takes precedence: name the affected claim and the pending
repair instead. Link the repaired note briefly when handing back; no compatibility stamp,
backup ritual or maintenance report is needed.

## Integrate changes into the argument

Identify the question a new derivation, observation, failure, correction or choice
answers, and the existing passage whose meaning changes. Replace that account;
inspect dependent uses, the opening and conclusion, and remove resolved next steps.
Follow the [placement and restructuring procedure](../aitp-writing/references/research-note.md#add-move-and-remove-material-without-losing-the-thread)
and its [worked edits](../aitp-writing/references/worked-note-edits.md).
The main note grows by developing its argument, not appending session summaries.
Its opening states the question, current answer, operative method, decisive
limitation and next step, without recounting experiments. Full setups, repeated
runs and job states belong in the supporting note or run report.
Preserve useful failures, unresolved objections, original observations and reasons
for route changes. Supporting detail has one primary home with a precise link.

A changed hypothesis or conclusion needs a bounded search for dependent claims,
including terminology, aliases and incoming links; a wording change does not.
Removing a link neither invalidates nor deletes its target. Keep useful detached
material discoverable and correct known errors where readers encounter them,
using [corrections and retained notes](../aitp-writing/references/supporting-notes.md#correct-claims-and-keep-earlier-routes-findable).
Name known dependencies beyond the completed scope. This is work during the task,
not background synchronization.

For a learning topic, use [aitp-human-learning](../aitp-human-learning/SKILL.md) for the
interaction; its main note can be a
[story of questions](references/shared-knowledge.md#tell-a-learning-topic-as-a-story-of-questions)
linking source readings and atoms, and it distinguishes an explanation the agent produced
from understanding the learner confirmed. No mastery checklist or learning ledger is needed.

Keep the core implication intelligible in the main text, and move a long derivation,
specialized concept or detailed analysis to its own file when it has an independent role,
leaving the result, decisive condition and link. Reuse a shared atom when its conventions
apply, and state a topic-specific difference where it is used. When the researcher keeps a
[shared knowledge collection](references/shared-knowledge.md), read its index once at the
start of a theoretical derivation, a conceptual question or a reading or study task, open
the entries the task needs, and check it before creating an entry.

For a first main note or a substantive revision, apply
[aitp-writing](../aitp-writing/SKILL.md) and its
[main-note guidance and Markdown templates](../aitp-writing/references/research-note.md).
Choose a compact, theoretical or computational article structure for the whole
research question, retaining the assumptions, decisive reasoning, useful failed
routes and consequential conjectures needed to
continue the research. Memory decides what must survive; writing makes it a
clear argument. They edit the same note, without a separate summary to maintain.

## Keep the topic tree clear

A topic often grows into a tree: a parent main note whose argument uses the answers
of branch main notes, each with its own question and evidence. Keep each level
telling its own part of the story, so that the parent stays readable as work grows.
The root note is the top of every tree. Relationships, reachability and the propagation
of changed meaning apply at every level, but the root's content follows its
[own rule](#the-backbone-at-each-level): implications for the larger questions, not each
topic's current answer and continuation.

When the task's note has a parent or branches, relate them before working. For
branch work, read the parent's opening and the passage that uses this branch; for
parent work, read the openings of the branches the task touches. Privately establish
what the parent needs from the branch, what the branch currently answers, and whether
both notes say so. This bounded read adds no other ancestor, sibling or supporting
file. A material mismatch is an [on-use repair](#repair-an-outdated-main-note-during-use).

Whenever you edit a note in the tree, check that:

- The parent uses each branch where its argument needs the result: the branch's
  question in a clause, its current answer and limitation in a sentence or two,
  what follows for the parent's question, and a link. The branch's numbers, settings,
  step sequences and failed attempts stay in the branch, unless a parent inference
  turns on a particular value. A parent passage that would change whenever the
  branch's evidence changes is carrying that evidence; reduce it to the implication.
  A parent section that narrates one branch's work tends to collect such evidence.
  State the implication once, where the argument uses it; the opening and the
  continuation name it with a link rather than restating it. When an update touches
  a passage that narrates a branch, replace the touched narration instead of
  appending another paragraph to it.
- The branch's opening states which parent inference it serves and what its
  possible outcomes would mean there.
- The parent's opening tells the topic's story: the question, what each branch has
  established or ruled out and how that moved the answer, and which branch or step
  decides what remains open. It names a branch's next step and links it, rather
  than restating that step's details.
- A sibling or related topic is linked at the passage that depends on it, not restated.

At handoff, when a branch's answer, decisive limitation or next step has changed,
revise the branch's opening and the parent's using passage together, and the
parent's opening if its own answer, limitation or next step changed. Continue upward,
to the root when it is affected, only while an ancestor's meaning changes. An unchanged
branch state needs no parent edit.

Before adding material to a main note, ask whether its argument needs it at this
level. A line of work belongs in a branch or supporting note when it has its own
question and acceptance test, accumulates its own runs or derivations, changes more
often than the rest of the note, and is used elsewhere only through its conclusion.
Moving existing work there is ordinary organization within the authorized scope,
following the [restructuring procedure](../aitp-writing/references/research-note.md#add-move-and-remove-material-without-losing-the-thread);
starting a new investigation still needs agreement. A concluded branch's result
becomes part of the parent's argument and its note remains the evidence; an
abandoned branch leaves its reason in one sentence where the parent used it, with
what survives and what would justify reopening it.

These checks belong to entry, editing and handoff, not to a separate audit, status
file or registry; a clear tree needs no rewrite. Mention a tree repair in one
sentence when handing back the task.

## Use ordinary files and meaningful links

The README maps the actual folders; the main note carries the scientific argument through
links to detailed notes, whose passages connect to derivations, code, inputs, results,
papers and figures, so that the [reachability rule](#the-backbone-at-each-level) holds. When
a location is unfamiliar, use the README and
[browse nearby directories and note titles](references/local-assets.md#browse-nearby-topics-and-shared-knowledge)
before searching; this is a bounded step, not a whole-library read. Before saving an asset,
reuse its established location or a suitable place beside related material, keep one
primary copy and link it. [Asset placement and links](references/local-assets.md) covers
unclear cases and moves; its optional layouts create only the locations actual work needs.
Full recovery follows every scientific branch, including useful failed routes.

Prefer descriptive relative Markdown links with precise locators, such as a derivation's
section, a specific report, an input, a data product, a PDF or an image, and say what the
linked material establishes. Use Markdown for the main note unless an established TeX note
or an explicit choice says otherwise. No special IDs, schema, knowledge cards or hashes are
required. After a meaningful edit, reread the changed argument in context, check affected
links and qualifications, and confirm that the opening, reasoning and conclusion agree.
Preserve concurrent edits, and repair relative links when a note moves.

## Close the task visibly

At every substantive close or meaningful pause, say in a few lines what is now
supported, where it was retained, with a link to each changed file, and what the
evidence warrants next. Complete routine follow-through within the agreement, propose
the rest, and record agreed directions in the relevant backbone passage's next step.
An unaccepted suggestion stays a labelled seed. "The question is settled; nothing
further is warranted" is a valid close.

| Signal in the work or discussion | Warranted response within the existing agreement | Propose instead when |
| --- | --- | --- |
| A disputed step, incompatible claims or a delicate limit | Inspect premises and conventions; derive or check the smallest discriminating case with [aitp-verify](../aitp-verify/SKILL.md) | Resolving it means a different physical problem or a substantial independent investigation |
| Competing mechanisms predict different behaviour | Design the calculation or benchmark; run it when numerical work and its resources are covered | It needs an expensive campaign, an installation or a cluster submission outside the agreement |
| A mismatch or a suspiciously easy pass | Trace inputs and baseline, check the diagnostic, then repair the cause and validate | The repair would change the intended equation, a protected reference or an acceptance boundary |
| A reusable explanation or demonstrated operation | Improve existing coverage, add the provisional pointer, or use [aitp-distill](../aitp-distill/SKILL.md) | Confirming a research result, promoting an atom, installing or publishing |
| A new connection, a growing side question or multiplying prerequisites | Ask what success would establish; record a seed or organize existing work | Opening a new investigation or changing priorities |
| A changed implication or a materially stale argument | Repair the primary account and its affected parent and root uses | The task is read-only, or safe integration cannot preserve concurrent edits |

Routine derivations, local diagnostics, authorized implementation and ordinary placement
proceed without repeated permission. A new independent investigation, a material change
of objective or equation, an expensive campaign, an installation, a submission or a
publication outside the agreement needs a concrete proposal: its purpose, the evidence
for it, the first action, the cost and the stopping condition. Cheapness alone is not
authorization, and a purely analytic scope still excludes computation. The root note's
standing agreements record some of what the researcher has authorized in advance, but
authorization can equally come from the current request or another existing agreement and
need not be copied into the root first. A standing agreement retained there records an
explicit researcher instruction: where it was given, the actions and scope it covers, any
resource or review limits, and when it ends. Do not infer one from a historical successful
action; a permission found in an old note is not a new authorization.

## Status, history and "continue"

A status-only request, such as where things stand, what is running, or a topic's history or
connections, is answered from the existing records only: no note creation, on-use repair or
close write-back, even when records look stale. Report stale or conflicting records instead
of editing them. Keep each consequential decision and its reason where it affects the
argument, so that turning points can be assembled on request; the root holds connections
across topics. A bare "continue", in any language, resumes the unfinished authorized task at
its next action; an intervening status question does not replace it. The
[status and continuation guide](references/status-and-continuation.md) gives the details.

## Timing and recovery

When finishing the requested task or handing it back, decide whether its outcome
changes durable understanding or repairs a material gap in the retained argument.
This is an editorial decision, not an automatic end-of-turn write:

- No new durable understanding and no material defect in the retained account:
  answer the user without editing memory.
- Useful supporting detail with the main account still accurate: update or create
  the relevant detailed note or artifact. If the main note already explains the
  implication and links its owning support section, leave it unchanged; each new
  detail does not need its own main-note link.
- First consequential result, changed conclusion, assumption, failed route or
  next research decision: revise the affected main-note passages together and
  link the supporting evidence, including when the result is still provisional.
- A branch's answer, decisive limitation or next step changed: also revise the
  parent's using passage, and its opening when needed, as
  [keeping the topic tree clear](#keep-the-topic-tree-clear) describes.
- An encountered main note materially fails the current guidance: perform the
  [on-use repair](#repair-an-outdated-main-note-during-use), even without new results.

Before handoff, check that the main note states the current model, supported answer
and remaining question. A supporting report alone does not integrate a changed
conclusion. Link the edited main note in the reply; if scope prevents integration,
identify the affected claim and pending work. Check preservation, affected links
and scientific meaning separately, and merge concurrent edits against the latest
files, including changes inside relocated passages. Use the linked restructuring
procedure for a live-note handoff rather than overwriting another session's work.
Temporary limits of this session's own access, such as a cluster connection that is
down, go in the reply, not in the research notes. A persistent gap in the evidence, such
as raw files missing from the retained copy or a remote-only result that cannot be
verified, is recorded in the owning support account, with its location when known and the
limitation it causes.

Record a fragile insight or an expensive experiment's intent before interruption. A first
consequential value found while polling replaces the provisional comparison at its
substantive location, with conditions, even while the job runs; a run-state change without
a scientific result goes in its report only if useful, and an unchanged poll needs no write.
Prepared examples are dated snapshots, and a historical permission is not new authorization.

After consequential work, retain transferable learning where it belongs. A result another
question could use goes to the shared collection as a provisional index row citing its
research section, as [research teaches](references/shared-knowledge.md#add-what-research-teaches)
describes, and an atom waits for the researcher's confirmation. A demonstrated reusable
operation goes through [aitp-distill](../aitp-distill/SKILL.md) within the authorized scope.
Check existing coverage first, link rather than duplicate, and give the location and
limitation alongside the result. No durable learning means no additional write.
