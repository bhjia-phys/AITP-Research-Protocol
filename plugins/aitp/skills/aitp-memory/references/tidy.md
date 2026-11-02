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
- **Report a clean check** in one line: "architecture check: ok".

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

It writes nothing inside a topic; its only state, the turn start and whether the reply asked
for a decision, is kept in `~/.cache/aitp/turns/`.

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
