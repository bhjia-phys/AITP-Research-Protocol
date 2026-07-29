---
name: using-aitp
description: Use AITP Lite as the local research memory while working in an initialized theoretical-physics repository. Trigger when entering or resuming a project, after a durable result, failure, decision, source assessment, code change, reproducible run, or closeout, and when writing a working or theory note from recorded evidence.
---

# Using AITP

Use the `aitp` CLI for durable memory. Use ordinary filesystem tools and `rg` for ad hoc reading; there is no `aitp search`.

## Start or resume work

1. If `.aitp/topic/TOPIC.md` does not exist and the repository is blank except for `.git`, run `aitp init --topic <slug> --title "<title>"`.
2. At the beginning of every research session, run `aitp enter`.
3. Treat its output as the recorded project state, not as scientific truth. Open the cited Entries, Notes, code, calculations, and pinned references before relying on a claim.
4. If `memory_status` is `partial` or `not_established`, say what is missing and inspect the files directly.

Do not infer the real research state merely from directory names, Git history, or the latest modified file.

## Record a durable moment

Record only information that should survive the current conversation:

```text
aitp record prepare --kind <kind> --authority <level> \
  --created-by agent:<name> --idempotency-key <stable-key>
```

Choose one kind: `observation`, `result`, `failure`, `decision`, `source`, `code-change`, `run`, or `closeout`.

Open the returned draft, replace every inline prompt, add precise relations and pinned references, then run:

```text
aitp record save <draft-path>
```

The CLI template is the schema. Do not invent a second record format. Keep claims small, state limitations, and distinguish evidence from interpretation. Use:

- `resolves` only for an active failure that this Entry actually resolves.
- `supersedes` only when replacing an older Entry; never silently rewrite history.
- `git`, `sha256`, `run`, `version`, or `retrieved` pins for evidence that may change.

Reuse the same idempotency key when retrying the same logical write.

## Write a note from memory

Use a note for synthesis, not as the only evidence for a result:

```text
aitp note prepare --mode working --title "<title>" --created-by agent:<name>
aitp note prepare --mode theory --title "<title>" --created-by agent:<name>
```

Fill the generated template and cite supporting pinned sources in `basis_refs`, then save with:

```text
aitp note save <draft-path>
```

A working note explains the current line of attack. A theory note gives a derivation or formal argument with assumptions, conventions, checks, and open gaps.

## Before ending

Run `aitp enter` again. Confirm that the new record is active, its evidence is reachable, unresolved failures are honest, and the next action is concrete. Do not record conversational filler, speculative claims presented as results, duplicate retries, or transient scratch work.
