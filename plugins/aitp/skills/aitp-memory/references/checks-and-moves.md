# Check a topic and move its notes

Use this for a whole-topic check before a handoff or after reorganizing, and whenever several
files move inside a topic. A single local edit needs only its affected links reread. The two
scripts in [`scripts/`](../scripts/) apply the link and placement rules of
[asset placement and links](local-assets.md) and the [placement table](asset-placement.md).
Run them from this Skill's folder (`aitp-memory/`) or by full path. A check changes nothing, and a clean report establishes navigation,
not the correctness of any claim.

## Check a topic

```bash
python3 scripts/check_topic.py TOPIC \
  --workspace TOPICS_ROOT --workspace KNOWLEDGE_COLLECTION \
  [--skip REL] [--frozen PATTERN] [--json report.json]
```

**Errors:**

- relative links or `#anchors` in active notes that do not resolve;
- links from the named workspace folders into the topic that do not resolve;
- files at a topic root whose type the [placement rules](../../../assets/placement-rules.json)
  do not admit.

**Warnings:**

- links leaving the topic that do not resolve;
- notes loose at a topic root;
- main notes without `## Current work`;
- Current work entries with neither a date nor "change date unrecorded" (pointer entries to an
  owning note are exempt);
- files in a topic's `notes/` that its `research.md` and README never reach.

**Info:**

- a `research.md` inside a run or legacy folder is reported as a study note. The root rules do
  not apply to it.

Frozen copies, meaning a `before/` component or `provenance/snapshots/`, are only counted,
because they keep the link base of the revision they record. Add `--frozen '*-backup*'` or
similar when a topic names its historical copies differently; the pattern matches whole folder
names.

Some trees are skipped automatically, because their files are not the topic's notes:

- nested source repositories, meaning folders holding `.git` (override with `--include-repos`);
- Python and conda environments.

Use `--skip` for archives or run outputs whose old links are historical evidence; do not
"repair" them.

Always name the folders that link into the topic, such as the topics root and the shared
knowledge collection. A check confined to the topic misses the links most likely to break when
its files move.

## Move notes without losing links

1. **Decide the moves within the authorized scope.** Typical moves are a loose note into
   `notes/`, or a gate note beside its branch. Write `MOVES.tsv`, one
   `old<TAB>new<TAB>reason` line per file, paths relative to the topic.
2. **Leave a run bundle where its own files place it.** Do not move a bundle whose scripts,
   commands or receipts depend on its location. Look for:
   - roots computed from `__file__`;
   - commands relative to a workspace root;
   - absolute paths;
   - sibling references such as `../shared_script.py`.

   Map such a bundle to its owning question in the README instead.
3. **Dry-run.** Run `python3 scripts/move_notes.py TOPIC MOVES.tsv --manifest
   moves.json --incoming TOPICS_ROOT --incoming KNOWLEDGE_COLLECTION`. Read its three lists:
   - **Link rewrites inside the topic.**
   - **Incoming links from outside.** They are only reported. A shared collection or another
     topic may lie outside the authorized scope. When it does, do not apply a move that one of
     its links depends on, because a move that breaks an incoming link is not complete. Keep the
     file where it is, keep the staged `MOVES.tsv` and dry-run manifest, and ask the researcher
     whether to authorize `--rewrite-incoming` or to leave the file in place.
   - **Non-Markdown files naming an old path,** such as code strings and JSON receipts. Leave
     them unchanged: original code and outputs are evidence. Record the old-to-new map in the
     nearest README.
4. **Apply.** Add `--apply`. The script refuses to move a frozen file, to overwrite an existing
   path or to leave the topic. It then does four things:
   - backs up every file it will touch, under `<manifest>-backup/before/`, which both scripts
     treat as frozen;
   - moves the files;
   - rewrites only link targets, keeping anchors, `%`-encoding and line endings;
   - verifies that each moved file is byte-identical right after the move, and that each
     rewritten file differs from its backup only in link targets that map correctly.
5. **Check and reread.** Run `check_topic.py` with the same `--workspace` folders. Then reread
   the changed passages and the README in context: a resolving link can still describe the
   wrong location.
6. **Keep the record.** Store the manifest with the organization record, for example under
   `calculations/organization-<date>/`, and link it from the README entry that describes
   the new location.

## Reorganizing a whole topic into a new home

When a topic is copied and reorganized rather than edited in place:

- **Copy beside the original.** Build the new tree at the same depth below the topics root,
  for example `topic-organized/`, so that links into and out of the family resolve during
  verification.
- **Stay on the working filesystem.** Keep the tree where its tools run. Before copying,
  check for:
  - names that differ only by case on a case-insensitive volume;
  - symlinks;
  - very long paths;
  - absolute paths in environments and receipts.
- **Verify the copy before reorganizing.** Compare checksums against an inventory taken
  beforehand.
- **Swap only after a drift check.** Re-inventory the original first, and swap the names only
  when nothing has changed since the copy. Then move the original out of the topics root,
  because discovery treats every `research.md` it finds as a topic.
- **Restart older sessions.** A session started inside the old tree follows the renamed folder.
- **Name environments and caches.** The new tree may lack environments and caches, so say which
  were left behind and how to recreate them.

## Scope of the scripts

Both scripts are standard-library Python 3.8+. [test_topic_tools.py](../scripts/test_topic_tools.py)
builds a synthetic topic with one instance of each defect and unsafe move. It checks every
report, rewrite, refusal and verification.

The procedure comes from the 2026-10-31 reorganization of a large research family:

- about 470 active notes;
- 44 moved files;
- 291 rewritten links;
- 51 incoming knowledge-collection links that a topic-only check had missed.

Its transfer was checked on two differently organized topics, which led to the nested-repository,
environment and `--frozen` rules.

Not exercised:

- Windows paths;
- non-UTF-8 text;
- HTML links;
- rewriting reference-style `[label]: path` definitions. `move_notes.py` rewrites inline links
  only; `check_topic.py` does check definitions.

Heading anchors follow GitHub's rules, compared case-insensitively. Explicit `<a id>`, MyST
`(label)=` and `{#id}` targets are also recognized; other renderers may differ.
