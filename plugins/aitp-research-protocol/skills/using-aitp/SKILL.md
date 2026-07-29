---
name: using-aitp
description: Use AITP Research Protocol to recover and preserve grounded research state while working in a theoretical-physics repository. Trigger when entering or resuming a project, after a durable result, failure, decision, source assessment, code change, reproducible run, or closeout, and when writing a working or theory note from recorded evidence.
---

# Using AITP

Use the CLI bundled with this plugin. Resolve `../../scripts/aitp.py` relative to this `SKILL.md`, convert it to an absolute path, and invoke it with Python 3.11 or newer:

```text
python3 <absolute-plugin-root>/scripts/aitp.py <command>
```

Do not require a globally installed `aitp` executable. In user-facing explanations, the shorter `aitp <command>` spelling is acceptable. Use ordinary filesystem tools and `rg` for ad hoc reading; there is no `aitp search`.

## Start or resume work

1. If `.aitp/topic/TOPIC.md` does not exist and the repository is blank except for `.git`, run `aitp init --topic <slug> --title "<title>"`.
2. At the beginning of every research session, run `aitp enter`.
3. Treat its output as recorded project state, not as scientific truth. Open cited Entries, Notes, code, calculations, and pinned references before relying on a claim.
4. If `memory_status` is `partial` or `not_established`, state what is missing and inspect files directly.

Never infer the real research state merely from directory names, Git history, or the latest modified file.

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

The CLI template is the schema. Keep claims small, state limitations, and distinguish evidence from interpretation.

- Use `resolves` only for an active failure this Entry actually resolves.
- Use `supersedes` only when replacing an older Entry; never silently rewrite history.
- Use `git`, `sha256`, `run`, `version`, or `retrieved` pins for evidence that may change.
- Reuse the same idempotency key when retrying the same logical write.

## Write a note from recorded evidence

Use a Note for synthesis, not as the only evidence for a result:

```text
aitp note prepare --mode working --title "<title>" --created-by agent:<name>
aitp note prepare --mode theory --title "<title>" --created-by agent:<name>
```

Fill the generated template, cite supporting pinned sources in `basis_refs`, and save with:

```text
aitp note save <draft-path>
```

A working Note explains the current line of attack. A theory Note gives a derivation or formal argument with assumptions, conventions, checks, and open gaps.

## Before ending

Run `aitp enter` again. Confirm that the new record is active, evidence is reachable, unresolved failures are honest, and the next action is concrete. Do not record conversational filler, speculative claims presented as results, duplicate retries, or transient scratch work.
