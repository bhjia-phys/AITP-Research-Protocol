# Phase 122: BibTeX Runtime And CLI Surface - Context

**Gathered:** 2026-04-11
**Status:** Implemented and verified
**Mode:** Main production phase for `v1.63`

<domain>
## Phase Boundary

Materialize the BibTeX export/import surface through extracted helpers and thin
CLI/service routing.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- add a new helper boundary instead of bloating `source_catalog.py`
- keep `aitp_service.py` and `aitp_cli.py` to thin command-family wiring
- require durable `.bib`, `.json`, and `.md` artifacts for export or import

</decisions>

---

*Phase: 122-bibtex-runtime-and-cli-surface*
*Context captured on 2026-04-11 after Phase 122 implementation and verification*
