# Adapter: AITP CLI (treatment condition)

I/O mechanics for the treatment condition. The operator hands the agent this
file byte-identical on every run under the fixed name `I-O-APPENDIX.md`,
alongside `policy.md`; it is the only tooling description the agent receives.
Mechanics only — semantics (what to read, what counts as a durable event,
correction handling, closeout discipline) come from `policy.md`.

## Environment contract (fixed before the run)

The operator verifies and records pre-run that the treatment invocation works
from the workspace root and stays fixed for the whole session. The CLI has no
`--version` flag (the runtime implements no version subcommand or option), so
treatment identity is recorded deterministically from fixed files and the
interpreter, never from the CLI:

- One fixed absolute launcher with a fixed interpreter, declared pre-run as
  `<python3.11> <absolute-launcher>` (the CLI requires Python ≥ 3.11; the
  bundled launcher is `plugins/aitp-research-protocol/scripts/aitp.py`). If
  `aitp` is on `PATH`, resolve it pre-run with `command -v aitp` and use the
  resolved absolute path — still that one fixed launcher, hashed below.
- Record pre-run, as the treatment identity block:
  - launcher absolute path + sha256 (`sha256sum <absolute-launcher>`);
  - interpreter absolute path (`command -v python3.11`) and its `--version`
    output (`python3.11 --version`);
  - installed plugin manifest version — read the `version` field of the
    installed `kimi.plugin.json` (or `.codex-plugin/plugin.json` if that is
    the installed manifest) — plus the manifest file's sha256;
  - canonical runtime revision/tree hash: repo commit (`git rev-parse
    HEAD`), `git status --porcelain` on the runtime path, and a sha256 tree
    manifest (sorted `path<TAB>sha256` lines) over every file in
    `plugins/aitp-research-protocol/scripts/vendor/aitp/`;
  - Skill hashes: `SKILL.md` path + sha256 for `aitp` and `using-aitp`, as
    delivered to the agent.
- Record the exact command line and the interpreter version pre-run. Every
  command in this appendix runs with exactly that invocation for the whole
  treatment session; the agent never needs a per-turn operator grant.

The workspace is a ledger store initialized with the CLI. Run every command
from the workspace root. Store layout: `.aitp/topic/TOPIC.md`,
`.aitp/topic/entries/entry-<32 hex>.md`, `.aitp/topic/notes/note-<32 hex>.md`;
entry and note drafts appear under `.aitp/local/drafts/`. Session commands:
`enter`, `record prepare`, `record save`, `note prepare`, `note save` (`init`
and `inventory` are operator setup only).

## Read memory

- Run `aitp enter`. Its output carries the recorded state projection: recent
  entries (id, kind, summary, limitations, authority, created_at, refs,
  source path), unresolved failures, next action, recent notes, counts
  (active, omitted_active), and warnings naming malformed files.
- Open the exact `source` path an entry or note reports, and locate evidence
  within it with `rg`. Reading beyond the returned window is ordinary
  filesystem tooling.
- If `enter` reports `not_established` or `partial`, read the files named in
  its `warnings` directly.

## Record a durable event

- `aitp record prepare --kind <kind> --authority <human|agent|source|tool>`
  writes a draft under `.aitp/local/drafts/` and prints its path. Kinds:
  `observation`, `result`, `failure`, `decision`, `source`, `code_change`,
  `run`, `closeout`.
- Edit the draft (a v0.1 Markdown file): replace every `<!-- aitp:` template
  prompt, fill in `summary`, `limitations`, `refs`, `resolves`,
  `supersedes`, and `next_action`. Refs pin a target with `at` (a `sha256:`
  or `git:` pin) plus a locator; `resolves` and `supersedes` take Entry IDs.
- `aitp record save <draft>` validates the entry (pins must resolve,
  relations must name existing entries, required sections must be non-empty)
  and moves it into `.aitp/topic/entries/`. To retry the same logical write
  without accumulating duplicates, prepare again with the same
  `--idempotency-key`.

## Write a note

- `aitp note prepare --mode <working|theory> --title <title>` writes a draft;
  edit it the same way (template prompts, `summary`, pinned `basis_refs`,
  sections), then `aitp note save <draft>` validates it and moves it into
  `.aitp/topic/notes/`.

## Closeout

- Record the session's `closeout` entry with the same `record prepare` /
  `record save` commands, then re-run `aitp enter` to read the resulting
  state.
