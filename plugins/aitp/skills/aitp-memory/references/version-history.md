# Version history of research files

Use this when the research files are inside a Git repository and the task needs
to know what changed, to record a checkpoint, to read an earlier version, or to
hand work to another session. Git is optional. Without a repository, or without
Git, every other part of AITP works unchanged; say that history is unavailable
rather than creating a repository.

Git records which text existed when. It does not record why a conclusion holds,
and it is not a second memory: the current `research.md` and its linked evidence
remain the account of the research. A committed claim has exactly the status its
evidence gives it. Never describe a result as checked, verified or established
because it was committed.

## Find the repository, do not create one

Locate the repository that contains the note: `git rev-parse --show-toplevel`
from the topic folder. A research workspace may contain several repositories,
for example a notes repository and separate code checkouts, each with its own
history; use the one that contains the file in question. A code checkout's
revision identifies evaluated code; it does not version the research note.

Do not run `git init` unless the researcher asks for history to start. Never
create a repository inside another one: initialize only a folder for which
`git rev-parse` reports no repository. Do not change Git configuration such as
`safe.directory`, hooks or signing on the researcher's behalf; report the
refusal and its reason instead.

## Keep the right files in history

| In history | Outside history, with a recorded location |
| --- | --- |
| `research.md`, supporting notes, derivations, source readings, plans, READMEs | Raw numerical outputs, checkpoints, wavefunctions, large tables |
| TeX sources, `.bib`, small figure generators and analysis scripts | PDFs of papers, compiled manuscripts unless the researcher keeps them |
| Small input decks and configuration that define a calculation | Caches, environments, build products, agent session state |
| Small data that a figure or table in a note depends on, when the researcher wants it kept | Credentials, tokens, personal data of other people |

A run report keeps the precise location, size and provenance of an output that
stays outside Git. A `.gitignore` prevents new files from being added; it does not
remove files already committed. Never rewrite history to remove a file without the
researcher's explicit request.

## Read what changed before relying on a remembered state

Before revising a note that another session, model or editor may have changed,
and when continuing after a checkpoint, compare the current files with the
version you last knew:

```sh
git status --short -- <topic>            # uncommitted edits and new files
git log --oneline -n 10 -- <topic>       # recent checkpoints for the topic
git diff <commit> -- <topic>/research.md # what changed since that checkpoint
git show <commit>:<topic>/research.md    # an earlier version, without touching the file
```

Uncommitted edits are part of the current state; a view of the last commit alone
misses them. A diff shows which lines changed, not what they mean. Before a
substantive revision, read the affected argument in the current note as
[memory's recovery](../SKILL.md#understand-the-whole-note-before-changing-it) requires.
A small diff can change an assumption that the whole account depends on.

## Record a checkpoint only when it is wanted

Record a checkpoint when the researcher asks for one, or when a standing agreement
in the root covers it. Useful moments include a first consequential result, a
corrected assumption or conclusion, a finished derivation, an agreed change of
route, the state a manuscript draft is built from, and the baseline before a
restructuring. Do not commit every edit, every turn or every session.

1. List the files that belong to this research change. Record those files only:
   `git commit --only -m "<message>" -- <files>`, or stage exactly those files
   and check `git diff --cached --name-only` before committing. Leave other
   staged or unstaged work as it is.
2. Check each new file before it enters history: no credentials, no large or
   binary outputs, nothing the researcher has excluded.
3. Write the message as a research change: "Correct the boundary term in the
   descent argument", not "update notes". Name a check in the message only if
   it was actually done and is recorded in the notes.
4. Let the repository's hooks run. Do not amend, rebase, reset or force anything.
   Do not push, pull or fetch: a remote, when one exists, is the researcher's to
   synchronize.

## Read and recover earlier versions safely

To compare arguments, read the earlier version with `git show` or a host's history
view and compare it with the current text. To restore a passage, edit the current
note so that later valid changes survive; correct the dependent uses as for any
other correction. Do not overwrite a file that has uncommitted changes with an
older version (`git checkout -- <file>`, `git restore`), and do not discard
another session's edits. When a whole earlier file is wanted back, first record or
otherwise preserve the current version, then restore with the researcher's
agreement.

## Use history where it simplifies existing procedures

- **Restructuring.** A checkpoint of the affected notes before applying a
  [substantial restructure](../../aitp-writing/references/research-note.md#add-move-and-remove-material-without-losing-the-thread)
  is the frozen baseline and the rollback route; `git diff` against it shows what
  was removed or moved. The preservation and meaning checks remain necessary: a
  diff finds omitted text, not lost meaning.
- **Hand-offs.** Give the receiver the commit to compare against and say whether
  uncommitted edits exist, as [hand-offs](handoffs.md) describe.
- **Parallel work.** Before integrating, compare the latest shared files with the
  version the worker read. A clean text merge is not evidence that the scientific
  assumptions are compatible; the integrator still checks them.
- **Numerical evidence.** A run report records the code revision it used, with a
  note when the checkout had uncommitted changes; see
  [numerical assets](numerical-assets.md). A reproducible revision can still
  implement the wrong physics.
- **Manuscripts.** A manuscript's README or source comment records the commit of
  the research note it was drafted from, so its claims can be traced back to the
  argument and evidence of that version; see
  [manuscript handling](../../aitp-writing/references/manuscripts.md).

A host may provide history tools for the same operations, such as the research
desk's `research_history` and approval-gated `research_checkpoint`. They follow the
rules above; their presence does not authorize a checkpoint.
