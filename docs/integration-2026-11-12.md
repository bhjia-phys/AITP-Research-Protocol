# AITP integration, 2026-11-12

## Scope and provenance

This integration starts from remote `origin/main` at `5780ffe0`. The local source is
the complete pre-integration backup: committed work through `dcecdf49` (including
`4b6a8789` and `c832c9bf`), its tracked working changes and six new reference/assets.
Only the independent integration checkout was edited. The original running checkout,
research data, installed profiles and Git history were not changed by this task.
No commit, stash, reset, rebase, installation or push was performed.

## Integration choices

- **Remote structure and safety win.** Keep the question-owned
  [plan/archive lifecycle](../plugins/aitp/skills/aitp-memory/references/plans.md),
  stage-placement guidance and both admitted/scanned stage directories. The remote
  checker, move tool and their regression suite remain identical to `5780ffe0`
  (after line-ending normalization). This retains duplicate-source preflight,
  symlink-escape refusal and alias-collision controls. Local older copies did not
  replace them.
- **Merge writing overlap once.** Remote `e76ccd17` already contains argument design,
  manuscript review, exemplar practice and the qualified Witten analysis. Retain those
  sections without appending duplicates. Add the local
  [paper plan](../plugins/aitp/skills/aitp-writing/references/paper-design.md),
  [exposition review](../plugins/aitp/skills/aitp-writing/references/exposition-review.md),
  [venue strategies](../plugins/aitp/skills/aitp-writing/references/venue-strategies.md),
  [worked edits](../plugins/aitp/skills/aitp-writing/references/worked-paper-edits.md),
  [derivation starter](../plugins/aitp/skills/aitp-writing/assets/derivation-note.md)
  and their discovery links.
- **Keep optional Git history.** Add
  [version-history guidance](../plugins/aitp/skills/aitp-memory/references/version-history.md)
  and handoff/manuscript provenance links. A checkpoint needs authorization, does not
  validate science and cannot stand in for unrecorded working changes or justify
  discarding later edits.
- **Retain local research interaction.** Keep researcher-owned decisions and short
  verbatim answers, pending questions, the optional
  [story](../plugins/aitp/skills/aitp-writing/references/story.md) and
  [independent reader](../plugins/aitp/agents/aitp-reader.md), with separate claim,
  story and skill-trial scopes. A reader's verdict is not researcher acceptance.
- **Keep tidy controlled.** Retain the optional
  [reply hook](../plugins/aitp/hooks/tidy.py) and
  [consolidation procedure](../plugins/aitp/skills/aitp-memory/references/tidy.md).
  The 400/30/7 thresholds are soft diagnostics, not limits that permit loss of a
  central derivation, a live thread or a qualification. Substantial consolidation
  is proposed and staged, requires agreement and preservation review, and uses the
  existing baseline/staged/latest comparison and shared-writer handoff. Suspected
  scientific drift needs verification, not an organizational rewrite of results.
- **Keep permissions external.** Preserve the optional native permission-rule example,
  without installing it or claiming that prefix rules form an exhaustive sandbox.
- **Version consistently.** The DSH package is `1.4.0`; Claude, Codex and Kimi retain
  their host suffixes, dated `20261112`. Marketplace identities and nested method
  discovery remain unchanged. The published `1.1.0` instructions remain historical
  release instructions, not the development version.

A broad patch applicability check failed on remote-overlapping sections before any
write. Non-overlapping hunks were applied selectively; overlap was reconciled in the
current text. No rejected hunks, conflict markers or duplicate argument-design/review
sections are part of the result.

## Checks performed

All commands used existing tools; no dependency or validation framework was added.
Output was retained in the tool transcript, not as generated repository artifacts.

| Check | Result |
| --- | --- |
| Bundled Windows Python, `hooks/test_tidy.py` | 29 synthetic controls passed. The test now sets both `HOME` and `USERPROFILE` to its temporary home and normalizes escaped path separators in captured JSON. |
| Unchanged remote `scripts/test_topic_tools.py`, WSL Ubuntu | 59 controls passed, including duplicate sources, symlink escapes and internal directory aliases, for dry-run and application. |
| All core and nested Skills, existing `quick_validate.py` | 10 passed: frontmatter, names, descriptions and unfinished-placeholder checks. |
| Existing Claude CLI, plugin and marketplace `plugin validate --strict` | Both passed. This is validation, not installation or runtime discovery. |
| Repository JSON and host identity/version checks | Eight JSON files parsed; four manifest versions/names and explicit nested Skill targets agreed; `story.md`, `plan/` and `archive/` placement remained admitted. |
| Active Markdown navigation | All checked relative targets and Markdown heading fragments resolved. Templates retain intentional destination-relative placeholders; they are not instantiated topic files. |
| Preservation checks | The remote checker, mover, test suite and plan lifecycle matched their baseline; remote benchmark inputs and historical validation observations were retained. |
| Diff hygiene | No whitespace errors or merge conflict markers in the final integration changes. |

### Native Windows boundary: not a passing move-tool validation

The bundled Windows run of the unchanged topic-tool suite did **not** pass:

1. One assertion splits a diagnostic location at its first colon, truncating a
   drive-qualified filename. This is a test portability issue.
2. The external-incoming-link application control also exposed a real product defect.
   A separate one-file move with an outside Markdown link reproduced `WinError 123`:
   the mover's external backup key retains the drive colon, creating an invalid
   `before/_outside/C:` component. Failure occurred while creating the backup, before
   the source move or incoming-link edit; the minimal control preserved both files.
3. Symlink setup stopped with `WinError 1314` because the native process lacked the
   required privilege. Those native symlink cases therefore were not exercised.

The minimal product repair would encode drive and UNC roots into distinct, safe backup
path components and add Windows controls, while preserving the remote preflight checks.
It was deliberately **not** implemented in this integration. Use the passing WSL boundary
for these tools; do not infer native Windows `--rewrite-incoming --apply` safety from it.
The Windows tidy-hook controls are separate and did pass.

## Historical evidence and remaining limits

The supplied local validation account reported Claude Code 2.1.316 synthetic end-to-end
checks of the decision cue and reply hook, a claim-reader trial, and host permission-rule
probes. Those historical accounts motivated the retained features but their private
execution records were not re-inspected or copied into this repository. They are not
fresh host-runtime validation of this merged checkout.

This integration did not run an independent reader session, a manuscript-quality
benchmark, a real research-topic consolidation, a human-learning assessment or a new
host hook execution. The existing remote writing benchmark observations retain their
original scope. Packaging, navigation and synthetic controls establish neither scientific
correctness nor general improvement in writing, discovery or decision quality. DSH
installation and live-catalog verification, if requested, are a separate task.
