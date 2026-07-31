# AITP Cross-Topic Links (M3)

Status: active design for the M3 stage of `docs/roadmap.md`.
Supersedes: `docs/research-graph-design.md`.

## Scope

The only irreducible cross-topic needs are:

1. a **catalog** of which Topics exist (portable identities vs. local paths);
2. **explicit links** between records in different Topics, each with a
   rationale, an author, and pinned evidence where reachable.

Everything else — discovery, relevance, freshness judgment — is Skill work
over `rg` and per-topic `enter`. There is no sync, no projection, no index,
no graph database. Topic repositories remain the only canonical stores.

## Layout

```text
<workspace>/topics.toml          workspace-level catalog (convention from M0.6)
<workspace>/.aitp-catalog/
├── links/                       link records (append-only Markdown)
└── local/
    └── roots.toml               Topic ID → local absolute path (machine-local)
```

`topics.toml` carries portable identity only:

```toml
[[topics]]
id = "qsgw-librpa"
title = "QSGW / LibRPA method development"
uri = "git+ssh://example/repository.git"   # optional
labels = ["gw", "qsgw", "librpa"]
```

`local/roots.toml` maps Topic IDs to local paths and is never committed.
Portable IDs decouple memory from absolute paths (host migrations).

## Link records

One Markdown file per link under `.aitp-catalog/links/`:

```yaml
---
schema: aitp/lite-link-0.1
id: link-<32hex>
type: related_to | supports | contradicts | uses_method | same_object | extends
source: <topic-id>:<record-id-or-path>
target: <topic-id>:<record-id-or-path>
created_at: <utc>
created_by: human:<name> | agent:<name>
---
## Rationale

<!-- why these two records are related; what a future session should do with it -->

## Evidence

<!-- pinned refs on the locally reachable side -->
```

Validation at save: both Topics exist in the catalog; type is known; locally
reachable sides exist; required sections are filled. Validation does not
follow remote sides.

Compliant Skills keep inferred links as drafts: a Skill may propose a
candidate in conversation or as a draft, but only an explicit `link save`
creates a record (proposals live as drafts; accepted links are saved
records). Saving requires explicit human confirmation; as with `decision`
Entries, an agent may execute the save on the human's behalf, attributed via
`created_by`. Withdrawal is out of scope until real pain demonstrates the
need.

## Commands (M3)

```text
aitp catalog init|add|list
aitp link prepare|save
```

`topics.toml` itself is a plain file convention from M0.6 — agents and humans
can read it without any CLI.

## Skill

`aitp-catalog`: read the catalog; search across Topic roots with `rg`;
present candidate links with rationale as proposals; on human confirmation,
`link prepare → save`. A compliant Skill's answers cite Topic, record, and
exact path, and disclose unavailable roots — measured by the conformance
suite.

## Acceptance

- Three real Topics in one catalog.
- ≥ 5 human-saved links answer a real cross-topic question with exact
  provenance.
- Works with zero index; rebuilding means re-reading the stores.
- A dead link target is visible when followed.
- All ledger tests pass unchanged.
