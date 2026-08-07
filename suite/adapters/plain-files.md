# Adapter: plain files (control condition)

I/O mechanics for the control condition. The operator hands the agent this
file byte-identical on every run under the fixed name `I-O-APPENDIX.md`,
alongside `policy.md`; it is the only tooling description the agent receives.
Mechanics only — semantics (what to read, what counts as a durable event,
correction handling, closeout discipline) come from `policy.md`.

The control machine has no `aitp` on `PATH`. The workspace has the same
ledger layout as the treatment condition, written and read by hand with
ordinary filesystem tools and `rg`.

## Layout

- `.aitp/topic/TOPIC.md` — topic frontmatter and research goal.
- `.aitp/topic/entries/entry-<32 hex>.md` — Entry records.
- `.aitp/topic/notes/note-<32 hex>.md` — Notes.

## Read memory

- Locate records and notes with `rg` over `.aitp/topic/` (id, kind, or any text), then open the matching files.

## Record a durable event

- Append one new file `entry-<32 hex>.md` (fresh 32-hex ID) in the entries
  directory, in valid v0.1 Markdown: `---`-fenced YAML frontmatter
  (`schema: aitp/lite-entry-0.1`, `id`, `topic`, `created_at`,
  `created_by`, `kind`, `authority`, `summary`, `refs`, `limitations`,
  `resolves`, `supersedes`, `next_action`) plus the kind's h2 sections,
  exact headings:
- `observation` — `Durable Summary`, `Observation And Conditions`, `Locator And Uncertainty`
- `result` — `Durable Summary`, `Basis And Checks`, `Validity And Implication`
- `failure` — `Durable Summary`, `Attempt, Expected, And Observed`, `Evidence And Next Diagnostic`
- `decision` — `Durable Summary`, `Decision And Alternatives`, `Reason, Scope, And Revisit Condition`
- `source` — `Durable Summary`, `Identity And Relevance`, `Exact Locator And Claim Boundary`
- `code_change` — `Durable Summary`, `Change And Revision`, `Verification And Scientific Effect`
- `run` — `Durable Summary`, `Question, Command, And Inputs`, `Outputs, Result, And Status`
- `closeout` — `Durable Summary`, `Accomplished And Unresolved`, `Next Action And Resume Refs`
- `refs` pin a target with `at` (`sha256:<digest>` via `sha256sum`, or
  `git:<commit>`) plus a locator; `resolves`/`supersedes` name Entry IDs of
  files already in the entries directory. Writing means appending new files;
  never edit or delete an existing file.

## Write a note

- Append one new file `note-<32 hex>.md` (fresh 32-hex ID) in the notes
  directory, in valid v0.1 Note Markdown: `schema: aitp/lite-note-0.1`,
  `id`, `topic`, `title`, `mode`, `created_at`, `created_by`,
  `review_state: agent_draft`, `summary`, `basis_refs`, `supersedes`, plus
  the mode's h2 sections, exact headings:
- `working` — `Purpose`, `Scope And Basis`, `Synthesis`, `Evidence Map`,
  `Uncertainty And Omissions`, `Open Questions`, `Next Actions`
- `theory` — `Question And Obstruction`, `Setup And Assumptions`,
  `Central Construction Or Argument`, `Main Result`,
  `Checks, Examples, And Failure Modes`, `Limitations And Open Questions`
- `basis_refs` use the same pin rules as entry refs.

## Closeout

- Record the session's `closeout` entry as one more appended file in the entries directory.
