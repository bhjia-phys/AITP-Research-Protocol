# L2 staging protocol

Status: draft

This file defines the quarantine surface for provisional or scratch
`L2`-adjacent material.

## 1. Why this exists

Some outputs are useful enough to keep but not trustworthy enough to promote
into canonical `L2`.

Without an explicit staging surface, those outputs are likely to either:

- disappear,
- stay scattered in ad hoc files,
- or leak into canonical `L2` too early.

This protocol creates a durable third option: keep them, but keep them
quarantined.

## 2. Core stance

Staging is:

- durable,
- inspectable,
- non-canonical,
- and explicitly review-limited.

Short form:

- keep provisional outputs,
- do not confuse them with trusted `L2`.

## 3. Location

Staging lives under:

- `research/knowledge-hub/canonical/staging/`

The initial layout is:

```text
canonical/staging/
  README.md
  workspace_staging_manifest.json
  workspace_staging_manifest.md
  entries/
    <entry_id>.json
    <entry_id>.md
```

## 4. What belongs here

Examples:

- scratch reusable-note drafts
- provisional workflow drafts
- bridge drafts
- warning drafts
- candidate writeback summaries that are not yet canonical
- AI-generated reusable-memory candidates awaiting review

## 5. What does not belong here

Do not use staging for:

- canonical promoted `L2` units
- `L3` candidate and exploratory work that should stay in topic-local runs
- raw `L0` sources
- final `L5` publication outputs

## 6. Entry rule

Every staging entry should record:

- `entry_id`
- `topic_slug`
- `entry_kind`
- `title`
- `summary`
- `status`
- `authoritative = false`
- source artifact refs
- creation/update metadata

The entry should point back to the topic or artifact lineage that caused it to
exist.

## 7. Status rule

The initial status model is:

- `staged`
- `reviewed`
- `dismissed`

These statuses are about quarantine state, not scientific truth.

## 8. Promotion rule

Staging does not promote by itself.

No staged entry becomes canonical merely because it exists for a long time or
appears useful in a compiled view.

Canonical promotion still requires the normal review and promotion path.

## 9. Compiler rule

Compiled `L2` surfaces and hygiene reports may mention that staging exists, but
they must not silently merge staged content into canonical summaries.

If staged content is shown, it must be clearly marked as non-authoritative.

## 10. One-line doctrine

Staging keeps provisional `L2`-adjacent output durable without letting it
pretend to be trusted canonical memory.
