# Check a reply's changes against the topic architecture

At the end of a reply, the files that reply changed should still fit the topic's architecture:

- each file sits where its kind and its question keep such material;
- the `research.md` passage or note that uses its result links it;
- a thread whose state changed says so in its Current work.

This check keeps a topic clear around its main note, reply by reply, instead of in large
reorganizations. It writes no new science.

## When

- **After every reply.** In Claude Code and Codex the AITP plugin runs it as a hook.
  `UserPromptSubmit` records when the reply began. `Stop` lists the files changed since then:
  every file in the session's topic with a later modification time, which includes the work of
  subagents and shell commands, plus files the transcript shows were edited in other topics. If
  there are any, the hook asks once for this check.
- **On request.** When the researcher says "tidy", apply the same questions to a longer window.
  `python3 <plugin>/hooks/tidy.py --status [DIR] --hours H` lists the files changed in the last
  `H` hours.

## Three questions for each changed file

1. **What is it?** A note, script, data, figure, run output, record or scratch.
2. **Which question does it serve?** Name the main note, branch or shared area, using the
   topic's README map, which shows where that kind of material lives, and
   [asset placement](asset-placement.md).
3. **Is it in that home, and is it linked from the passage that uses its result?**

## What to do

- **Fix your own misplacements.** Files this reply created or changed and that are clearly
  misplaced or unlinked are fixed within the task's scope, as ordinary placement: move a stray
  script into its run folder or `code/`, move a note into `notes/`, add the missing link, or
  update the owning Current work entry. Several linked Markdown files move with the
  [move procedure](checks-and-moves.md#move-notes-without-losing-links).
- **List the rest.** In at most five lines, give what needs the researcher: files they or another
  session made, unclear purpose, or a choice of home.
- **A clean check needs no report.** End without further comment on it.

## Limits

The check never does any of these:

- changes a number, conclusion or qualification;
- deletes a file;
- edits frozen copies, archives or another person's files without approval.

A larger reorganization is not this check; it follows [checks and moves](checks-and-moves.md)
and its own agreement.

## Hook behaviour

The hook stays silent in these cases:

- nothing changed;
- the session is outside a topic and edited none;
- the stop is the hook's own continuation (`stop_hook_active`);
- `AITP_TIDY` is `off`, which is useful for automated runs.

It skips:

- hidden folders and caches;
- environments;
- nested repositories;
- build output;
- frozen `before/` and `provenance/snapshots/` copies.

It writes nothing inside a topic; its only state (the turn start, whether the reply asked for a
decision, and when each topic was last offered a consolidation pass) is kept in `~/.cache/aitp/`.

## The decision reminder

When a reply asks the researcher for a decision with a `Decision needed:` line, as
[brainstorming](../../aitp-human-brainstorming/SKILL.md#make-the-question-answerable) writes
every request, the check also asks whether the owning Current work entry says
`waiting on the researcher`. At the next prompt the hook adds one line of context: if the
message answers the question, record the decision in the owning note's
[decisions](../../aitp-writing/references/research-note.md#decisions-and-retained-alternatives)
with the date, the scope and the researcher's own words, and update the waiting entry;
otherwise the entry stays waiting. The reminder fires once and never decides what counts as
an answer: the agent does, and never records a decision the researcher did not make.

## The consolidation pass

The reply check keeps each reply's files in their homes, but a main note still grows: adding
is always the easy edit, and nothing else removes material. The consolidation pass is the
periodic counterpart, modelled on how Claude Code consolidates its own memory: a pass with a
[size budget](../../aitp-writing/references/research-note.md#decide-what-stays-in-the-main-note)
whose job is to make the note shorter and truer without losing anything.

**When.** When the researcher asks ("tidy", "consolidate", 整理), or when the hook says that a
topic's main note is over its budget. Offer the pass at a natural point in the session; do not
start it without the researcher's agreement. The hook offers once, then again only after a day
and about 10% further growth, so a longer note the researcher has accepted stops prompting. A pass covers
one main note and the notes it links to; a parent and its branches are separate passes.

1. **Orient.** Read the opening, Current work, the headings and the README map. Know what
   already exists before proposing a new file, so that moved material extends an existing
   supporting note rather than duplicating it.
2. **Gather.** List what changed since the last pass (`tidy.py --status DIR --hours H`). Look
   first for drift: claims in the note that newer notes, runs or decisions contradict, threads
   that ended but are still listed, and passages that repeat what a supporting note owns. Search
   transcripts or old notes only for something already suspected; do not reread everything.
3. **Consolidate.** Replace each passage whose meaning has changed with the current account,
   rather than adding to it. Fold concluded threads into the account and remove their Current
   work entries. Merge entries that are one thread. Turn relative dates into absolute ones.
   Correct a contradiction where the wrong claim lives, with the correction visible.
4. **Prune.** Bring the note under its budget. Move each finished section with an independent
   role, verbatim, into a supporting note (an existing one if it fits), with relative links
   rewritten, and leave in the main note its result, decisive condition and link. A binding
   decision that no longer binds becomes a one-line retained alternative. Keep central
   derivations, assumptions and qualifications in the main note whatever their length.

**When the central argument alone exceeds the budget**, stop pruning and say so: the note keeps
its length, and the researcher's acceptance ends further offers until it grows. Propose a branch
split only for a part with its own maintainable question, evidence and continuation; a long proof
belongs in a supporting note, not a new topic. For each candidate branch give its question, the
sections it would take, the assets it uses, what the parent keeps (its implication and limit),
the remaining dependencies and the resulting lengths, and always include the option of keeping one
longer note.

**Never** delete scientific content: a contradicted claim is corrected and its route kept as a
retained alternative, and moved text keeps every condition. Do not change a number, conclusion
or qualification; the pass rewrites organization, not results.

**Propose, then apply.** The pass returns a proposal: the new outline with the line count of each
part, the list of moves (section → target note), the threads folded or merged, and any drift
found. Stage the rewritten note and the receiving notes outside the topic and check their links.
Apply only after the researcher agrees, after the [AITP reviewer](../../../agents/aitp-reviewer.md)
has compared the staged files with a baseline copy (a restructuring needs that review), and after
confirming that the live note has not changed since the baseline. If nothing needs to change, say
so: "the note is within its budget and current" is a valid result.
