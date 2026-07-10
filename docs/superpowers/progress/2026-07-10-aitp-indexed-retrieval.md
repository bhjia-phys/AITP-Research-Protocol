# AITP Indexed Research Retrieval Report

Date: 2026-07-10

## Coverage

The generation-stamped derived index covers all canonical record locations,
not only `registry/` dataclasses:

| Measure | Generation 4 |
|---|---:|
| Indexed records | 9,741 |
| Registry records | 7,235 |
| Memory entries | 2,356 |
| Sessions | 87 |
| Topics | 43 |
| Contexts | 20 |
| Envelope parse issues | 0 |
| Typed materialization ready | 9,717 |
| Typed materialization unavailable | 22 |
| Typed materialization not applicable | 2 |

The 22 legacy simplified records remain searchable and exact-expandable from
the document layer. They are not omitted merely because the current dataclass
requires fields that the historical record does not contain.

## Index Contract

- Canonical Markdown/YAML remains authoritative; `.aitp/indexes` is disposable.
- The manifest records generation, deterministic canonical watermark, cheap
  file-state freshness token, family counts, issue counts, build time, and
  per-file SHA-256 hashes.
- Derived-file tampering is rejected by component hash validation.
- Lexical postings use stable integer document ids, avoiding repeated long refs.
- Latin identifiers and bounded CJK n-grams share one deterministic tokenizer,
  so formal-physics notation and Chinese research language use the same ranking
  contract.
- Exact refs read canonical records first and fall back to indexed documents for
  compatibility-valid records that cannot materialize as current dataclasses.
- Malformed canonical files contribute their file digest to the canonical
  watermark, so an index cannot appear fresh merely because a record failed to
  parse.
- Stale or partial results set `coverage.exhaustive=false` and forbid absolute
  no-result claims.
- Retrieval audits are orientation-only and cannot update kernel state or claim
  trust.

## Real-Store Performance

| Measure | Result |
|---|---:|
| Generation 4 build | 76.959 s |
| `record_documents.json` | 31.44 MB |
| `lexical_index.json` | 12.32 MB |
| Warm index load | 0.308 s |
| Canonical freshness token | 0.098 s |
| Warm representative query | 0.446 s |
| Immediately-after-build cold queries | 2.16-2.43 s |

The representative query was `LibRPA head wing convergence`, filtered to the
`qsgw-headwing-update-librpa` topic. It returned 250 candidates on the expanded
all-record index. Warm query latency is suitable for session recall. Build time
is suitable for explicit refresh or background update, not synchronous
per-message rebuilding.

An initial ref-string posting representation produced an 86.7 MB lexical file.
Integer postings reduced it to 12.3 MB without changing ranking tests.

## Verification

- 10 deterministic index, stale-coverage, special-path, tamper-detection,
  Unicode retrieval, scoped malformed-coverage, filtering, ranking, pagination,
  and legacy exact-fallback tests passed.
- No canonical research record was rewritten by index construction.
