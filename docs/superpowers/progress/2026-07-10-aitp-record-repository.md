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
- `list_valid_records` remains available only as a documented legacy-tolerant
  helper and is forbidden for exhaustive queries or absence claims.
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
| Registry Markdown checked | 7,235 |
| Current typed dataclasses loaded | 7,213 |
| Explicit typed-construction issues | 22 |
| Full strict scan wall time | 46.232 s |
| Canonical records rewritten | 0 |

The 22 issues are early simplified records that have a valid compatibility
envelope but do not contain every field required by the current dataclass:

| Family | Checked | Loaded | Issues |
|---|---:|---:|---:|
| `code_states` | 82 | 80 | 2 |
| `evidence` | 783 | 779 | 4 |
| `reference_locations` | 1,839 | 1,835 | 4 |
| `sensemaking_reports` | 699 | 695 | 4 |
| `tool_runs` | 708 | 704 | 4 |
| `validation_results` | 35 | 31 | 4 |

These records are not absent and are not discarded. The compatibility-envelope
audit loads all 7,235 records. Gate 0 query indexing must therefore index the
document/envelope layer and separately expose typed-materialization readiness;
the 22 records become an explicit migration backlog rather than disappearing
from retrieval.

## Verification

- 86 repository, envelope, source-asset, reference-location, kernel,
  workspace-inventory, runtime-audit, and family-registry tests passed.
- Two focused adapter/record-ref tests passed; their current import/graph path
  required 148.37 seconds and remains performance evidence for the query and
  module-boundary tasks.
- The full `test_v5_adapters.py` invocation did not finish within five minutes,
  so it is not reported as passing.
