# M1e — Evidence lifecycle + reviewed workstream backfill (frozen implementation spec)

Date: 2026-08-15
Status: implementation spec for M1e
Supersedes: no frozen contract. M1b/M1c/M1d dispositions and archives are unchanged.

## Natural-demand evidence

Real-store use exposed two protocol gaps:

- `feedback/2026-08-15-gw-librpa-natural-use.md` and direct store audits: 218
  check errors on GW_librpa and 175 on Power_Law_Heisenberg_Chain are dominated
  by historical `sha256:` pins on mutable canonical paths that later changed
  legitimately (`PROJECT_MEMORY.md`, JHEP tex/pdf, execution-note pdf/zip,
  live `execution_note_status.json`, source files). The current runtime has
  only one strict `sha256:` semantics, so normal research edits accumulate
  permanent `hash_mismatch` errors.
- The same stores have hundreds of legacy records without `workstreams`
  (GW_librpa: only 58 of 332). Scoped views are empty for those records, and
  the protocol forbids inference. A reviewed, explicit, idempotent backfill
  path is missing.

This is a protocol-level slice, not a semantic-drift classifier.

## Selected slice

1. New local pin scheme **`sha256-once:`**.
2. Optional store-local **`check-policy`** file that downgrades legacy strict
   pins on reviewed mutable paths to historical findings.
3. New **`aitp backfill workstreams`** command for explicit, human-anchored,
   append-only metadata backfill.

## Non-goals

No automatic drift/damage inference, no old-record content rewrite, no
database/index/daemon/MCP, no new file schema for Entries/Notes, no automatic
workstream inference, no repair of malformed legacy records, no baseline/delta
runtime.

---

## 1. `sha256-once:` pin scheme

`at: sha256-once:<digest>` is a save-time observation of a mutable target.

- Save: the target must be a local file and current bytes must equal
  `<digest>` exactly, or save fails. The rule is as strict as `sha256:` at
  write time.
- Check:
  - current bytes differ => `warning[historical_pin_drift]` with message
    `sha256-once drift: <target>: recorded <digest>, current <actual>`.
  - target missing => `warning[historical_ref_missing]`.
  - unreadable / not a file => `warning[historical_ref_missing]` with the
    observed reason.
- External targets (`http://`, `https://`, `arxiv:`, `doi:`) are invalid for
  `sha256-once:` and produce `error[invalid_sha256_once_ref]`.
- Existing `sha256:` remains strict and byte-unchanged. `git:`, `run:`,
  `version:`, and `retrieved:` are unchanged.

Skill guidance: use `sha256-once:` only for live mutable canonical paths that
a historical record intentionally observes; use `sha256:` for immutable
evidence snapshots/manifests and `git:` for tracked source revisions.

---

## 2. Store-local check policy

Path: `.aitp/local/check-policy.json`. Optional. Absent file => check behavior
is byte-identical to the pre-M1e runtime.

Schema:

```json
{
  "schema": "aitp/check-policy-0.1",
  "mutable": [
    {"paths": ["PROJECT_MEMORY.md", "reports/**"]}
  ],
  "immutable": [
    {"paths": [".aitp/local/archive_backups/**"]}
  ]
}
```

Rules:

- Both keys are required lists; each item is a map with a non-empty `paths`
  list of non-empty strings. Absolute paths and `..` segments are invalid.
- Patterns are workspace-relative POSIX-ish strings. A pattern ending in
  `/**` matches the named directory and everything below it. Other patterns
  use case-sensitive `fnmatch` semantics.
- `immutable` is checked first and wins over `mutable`.
- A target matching `mutable` changes legacy strict findings only:
  - `hash_mismatch` => `historical_pin_drift` warning.
  - `missing_ref` => `historical_ref_missing` warning.
  - Other codes (`ref_escape`, `unreadable_ref`, relation/invalid-schema
    findings) are never downgraded.
- `sha256-once:` findings already carry historical warning codes and are not
  policy-dependent.
- A malformed policy file produces `error[invalid_check_policy]` on path
  `.aitp/local/check-policy.json` and does not downgrade any finding.
- The policy file is local, reviewed configuration, not a ledger record. The
  check payload keeps the existing `aitp/check-report-0.1` /
  `aitp/check-report-0.2` envelopes; policy presence is visible through the
  finding codes and the file itself. No-flag and scoped outputs remain
  byte-unchanged for stores without a policy file.

---

## 3. `aitp backfill workstreams`

Command:

```text
aitp backfill workstreams --mapping <path> --decision <entry-id> [--cwd PATH] [--apply] [--json]
```

Default is dry-run. `--apply` is required to write. Exit 0 on a valid
dry-run/apply; exit 2 on missing/invalid mapping, missing/invalid human
decision, an unanchored mapping, duplicate IDs, invalid slugs, or write
failure. The command never creates a ledger record automatically.

Mapping schema (`<mapping>` must be a workspace-contained JSON file):

```json
{
  "schema": "aitp/backfill-workstreams-0.1",
  "entries": {"magnetic-symmetry": ["entry-…"]},
  "notes": {"algebra-flow": ["note-…"]}
}
```

Rules:

- `entries` and `notes` are required maps. Keys are valid workstream slugs.
  Values are non-empty lists of valid Entry/Note IDs, respectively.
- The same record ID must not appear twice in the mapping (across both maps).
- Every ID must exist, parse, and be unique in the canonical store.
- `--decision` must be an existing Entry with `kind: decision` and
  `authority: human`, and its `refs` must contain a `sha256:` pin of the
  mapping file itself. This is the human review anchor.
- Apply adds only the missing `workstreams` frontmatter key/values. Existing
  memberships are preserved and not duplicated. `summary`, body, refs,
  timestamps, and relations are never modified. The body bytes are preserved;
  only the YAML frontmatter workstreams block is added/replaced.
- Apply is idempotent: if every mapped membership is already present, status
  is `applied` with `changed: []`.
- `workstreams` is written as a block list in mapping order, after existing
  memberships.

JSON success envelope:

```json
{
  "schema": "aitp/backfill-0.1",
  "status": "applied" | "dry_run",
  "mapping": "<workspace-relative mapping path>",
  "decision": "<entry-id>",
  "changed": [
    {"path": ".aitp/topic/entries/entry-….md", "workstreams": ["crpa"]}
  ],
  "unchanged": ["entry-…"]
}
```

Text view prints status, mapping/decision, then one line per changed path.

---

## 4. Determinism and zero-write boundaries

- `check` remains read-only and zero-write. Policy loading never creates,
  caches, or repairs files.
- `backfill` without `--apply` writes nothing.
- `backfill --apply` writes only the selected canonical Entry/Note files with
  atomic replace and only changes the frontmatter `workstreams` block.
- No flag/argument changes any existing command's no-flag output unless a
  `check-policy.json` file is present, which is a new reviewed store input.

## 5. Budget

Cumulative canonical runtime target ≤ 1,800 nonblank lines, hard cap ≤ 1,850.
Every Python module < 400 lines. Existing M1d budget record (1,543) is
superseded by this stage record.

## 6. Required tests

1. `sha256-once` save-time mismatch fails; check-time mismatch/missing are
   warnings with exact codes.
2. Policy downgrades legacy `hash_mismatch`/`missing_ref` only on mutable
   matches; immutable matches and unmatched paths stay errors.
3. Malformed policy produces `invalid_check_policy`.
4. No-policy check JSON/text/exit byte-parity against pre-M1e behavior.
5. Backfill dry-run writes nothing; apply adds and merges `workstreams` for
   Entries and Notes; body and non-workstream frontmatter bytes preserved.
6. Backfill rejects missing/non-human/unpinned decision, duplicate IDs,
   invalid slugs, missing IDs, and mapping outside the workspace.
7. Backfill idempotence and JSON/text success envelopes.
8. Scoped `check --workstream` with policy applies the same grading and
   preserves outside_scope semantics.

## Claims and boundaries

M1e claims deterministic implementation and read-only compatibility. It does
not classify which mismatches are semantically benign; it executes only
explicit record-time schemes and reviewed store policy. It does not repair
malformed records, does not infer workstreams, and claims no behavioral or
treatment-advantage evidence.
