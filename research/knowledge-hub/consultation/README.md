# Consultation surface

This directory stores the first-class protocol artifacts for `L2 consultation`.

It is a cross-layer protocol surface, not a new architectural layer.

## Purpose

Use this directory to record:
- what `L1`, `L3`, or `L4` asked `L2`,
- what `L2` returned,
- what was actually applied,
- how that application changed the downstream work.

## Policy

For non-trivial consultation that materially shapes a durable stage artifact, recording here is mandatory.

You may skip this surface only for ephemeral lookups that:
- do not change terminology,
- do not narrow or widen a candidate,
- do not choose a validation route,
- do not attach a warning or contradiction flag,
- and do not affect writeback or promotion.

## Layout

```text
consultation/
  README.md
  schemas/
  topics/<topic_slug>/
    consultation_index.jsonl
    calls/<consultation_slug>/
      request.json
      result.json
      application.json
```

## Relationship to stage-local logs

The files below still exist and remain useful:
- `intake/.../l2_consultation_log.jsonl`
- `feedback/.../l2_consultation_log.jsonl`
- `validation/.../l2_consultation_log.jsonl`

Those are now projections for local readability.
This directory is the protocol source-of-truth.

## Naming

- `consultation_id` keeps the typed form:
  - `consult:l3-foo`
- directory names should stay filesystem-safe:
  - `consult-l3-foo`

Do not use `:` in directory names.

## Helper

To scaffold a new consultation bundle instead of hand-writing all three JSON files:

```bash
python3 consultation/scripts/scaffold_consultation.py --help
```
