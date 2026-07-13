# AITP Safe RecordRepository Report

Date: 2026-07-10

## Implemented Contract

- Same family/id and identical payload is idempotent and does not rewrite the
  canonical Markdown file.
- Same family/id with different content is rejected unless an explicit
  compare-and-swap revision policy supplies the current record hash.
- Revisions archive the exact previous Markdown before atomically writing the
  replacement and record `revision`, `supersedes`, and the previous hash.
- Family/id lock files serialize concurrent hosts; bounded waiting and explicit
  stale-lock cleanup are tested.
- Exact reads and family reads return malformed paths and errors instead of
  silently converting them into absence.
- New writes validate the selected family dataclass schema and typed-ref syntax
  before taking the lock or creating a canonical file.
- `list_valid_records` now requires one of nine named legacy-migration or
  workspace-recovery operations. Ordinary runtime readers use strict reads;
  a repository-level AST test rejects undeclared tolerant reads.
- Six early schema-v1 shapes have explicit conservative typed-materialization
  adapters. They preserve old ids and payload fields while keeping unknown
  claims empty, old tool runs diagnostic/unreviewed, and incomplete code states
  visibly non-reproducible.
- `record_reference_location` is the first migrated public writer and preserves
  its existing return object and public surface while writing the full envelope.

## Hash Namespace Correction

The repository-integrity key is `record_content_hash`. This is deliberately
separate from domain fields named `content_hash`. The live source-asset family
uses `content_hash` for acquired paper, dataset, or file bytes; treating that
field as an envelope digest incorrectly marked 1,075 valid source records as
corrupt. Regression tests now prove that source-byte hashes remain scientific
payload and that only `record_content_hash` drives repository integrity checks.

## Live Store Strict-Read Baseline

| Measure | Result |
|---|---:|
| All registered canonical locations checked | 9,741 |
| Current typed dataclasses loaded | 9,741 |
| Explicit typed-construction issues | 0 |
| Schema-v1 records conservatively adapted | 22 |
| Canonical records rewritten | 0 |

The 22 adapted records are early simplified records that do not contain every
field required by the current dataclass:

| Family | Checked | Loaded | Issues |
|---|---:|---:|---:|
| `code_states` | 82 | 80 | 2 |
| `evidence` | 783 | 779 | 4 |
| `reference_locations` | 1,839 | 1,835 | 4 |
| `sensemaking_reports` | 699 | 695 | 4 |
| `tool_runs` | 708 | 704 | 4 |
| `validation_results` | 35 | 31 | 4 |

These records are not absent, discarded, or silently treated as current-schema
evidence. The document/envelope layer remains authoritative, and the adapter
uses only conservative compatibility values. New enveloped records and new
write payloads cannot use these defaults to bypass current schema validation.

## Verification

- 86 repository, envelope, source-asset, reference-location, kernel,
  workspace-inventory, runtime-audit, and family-registry tests passed.
- Two focused adapter/record-ref tests passed; their current import/graph path
  required 148.37 seconds and remains performance evidence for the query and
  module-boundary tasks.
- The full `test_v5_adapters.py` invocation did not finish within five minutes,
  so it is not reported as passing.
