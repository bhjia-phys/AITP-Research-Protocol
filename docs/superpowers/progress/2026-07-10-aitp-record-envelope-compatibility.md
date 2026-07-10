# AITP RecordEnvelope Compatibility Report

Date: 2026-07-10

## Result

The Gate 0 compatibility layer can derive a validated, non-writing
`RecordEnvelope` for every canonical registry Markdown record in the live
theoretical-physics topic store.

| Measure | Result |
|---|---:|
| Registry Markdown checked | 7,235 |
| Compatibility envelopes loaded | 7,235 |
| Malformed or unexplainable records | 0 |
| Canonical records rewritten | 0 |
| Claim trust updates | 0 |
| Full scan wall time | 39.674 s |

The wall time is a measured cold full-scan baseline, not a target. It confirms
why Gate 0 still needs a derived incremental query index before automatic
session recall can be enabled.

## Compatibility Decisions Proven Against Real Records

- YAML date scalars are normalized to ISO dates before canonical hashing.
- Repository integrity uses `record_content_hash`; a domain field named
  `content_hash` remains scientific payload (for example source-asset bytes).
- Current family-specific IDs remain canonical for new records.
- Schema-v1 generic `id` and `topic` fields are accepted only as labeled
  compatibility sources.
- Historical `reference_location_id` and `validation_result_id` fields are
  accepted through family-registry aliases.
- File modification time is used only as an explicitly labeled creation-time
  fallback and is never written back to the source record.
- Every compatibility derivation is orientation and migration metadata. It
  cannot update kernel state or claim trust.

## Largest Live Families

| Family | Records | Loaded | Malformed |
|---|---:|---:|---:|
| `reference_locations` | 1,839 | 1,839 | 0 |
| `source_assets` | 1,198 | 1,198 | 0 |
| `evidence` | 783 | 783 | 0 |
| `tool_runs` | 708 | 708 | 0 |
| `sensemaking_reports` | 699 | 699 | 0 |
| `legacy_l2_seed_group_reviews` | 435 | 435 | 0 |
| `artifacts` | 322 | 322 | 0 |
| `object_relations` | 206 | 206 | 0 |
| `physics_objects` | 204 | 204 | 0 |

## Boundary

This report proves compatibility-envelope coverage, not semantic validity of
every scientific statement. The canonical Markdown/YAML records remain the
source of truth. A future repository layer must report parse failures and
collisions explicitly; a future index may accelerate reads but remains fully
derived and disposable.
