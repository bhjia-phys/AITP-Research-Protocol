# Hand work to another session or model, and work in parallel

A hand-off prompt lets a fresh session or another model continue without this
conversation. Write it so that the receiver could act on it alone.

## What the prompt contains

- **Where:** the repository or topic folder, the branch, and the main note to read first,
  with the parent passage the work serves.
- **Instructions:** one line naming the repository's instruction file and AITP's
  [research cycle](../SKILL.md#the-research-cycle), by path or host invocation, so that
  the receiver works the same way. Do not restate their content or describe their steps.
- **Code state:** for code work, the revision and any uncommitted local changes.
- **Question and current state:** two or three sentences from the main note's opening,
  plus the active plan phase if there is one.
- **Task:** what to produce or decide, and what counts as done.
- **Constraints:** what must not change, such as existing functionality, original outputs
  or a frozen branch, and what is authorized, such as submitting jobs.
- **Files and evidence:** exact paths for the inputs, scripts, reports and figures needed.
- **Live work:** existing jobs and their run reports, who owns submission and integration,
  and which files the receiver may edit and which stay with the coordinator.
- **Checks:** how the receiver should verify its own result.
- **Stop and report:** when to stop and ask, and what to report back.

## What to leave out

Leave out this conversation's history, internal process vocabulary, skill names beyond the
instructions line, and anything the receiver can read in the main note. Point to notes
instead of pasting them. A prompt that a researcher can read in one screen is usually right.

## Work in parallel

Divide work only when it is authorized and the parts can proceed under compatible
assumptions without each other's unfinished result. Two workers changing a shared
numerical definition are not independent because their files differ; independent
reviewers of one draft are.

1. Before work divides, the coordinator states the shared question, the conventions every
   part must use, the allowed files, run and submission ownership, dependencies and
   stopping conditions.
2. Each substantive note or code change has one writer. The parent note, the root note and
   the shared knowledge index have one integrator. Shared inputs and baselines stay
   protected, and new runs get their own locations.
3. Workers return their result, assumptions, evidence locations, the checks actually made,
   unresolved issues and the proposed implication for the parent. They do not rewrite the
   shared parent or index themselves; their branch notes remain the durable accounts.
4. The integrator reads the latest files, checks that conventions and assumptions are
   compatible, verifies consequential claims, tests combined code when needed, and writes
   the parent implication once, preserving concurrent edits. A clean text merge is not
   evidence that the results fit together.
5. A conflict the evidence cannot resolve stays visible as an open scientific question;
   do not average incompatible results into a conclusion.

When delegation is unavailable or not authorized, the same dependencies order the work
sequentially. AITP itself does not spawn agents or schedule jobs.

## After the hand-off

When the other session reports back, integrate its result through memory as for any
other result, after checking it with [aitp-verify](../../aitp-verify/SKILL.md) when it is
consequential. A hand-off prompt is a working artifact; keep it in the topic only when
it will be reused.
