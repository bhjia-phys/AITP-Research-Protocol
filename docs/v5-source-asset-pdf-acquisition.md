# AITP v5 Source Asset PDF Acquisition

This v5 feature stores locally readable literature PDFs without changing the
AITP evidence or trust model.

## Current v5 behavior

- `aitp-v5 asset register` records a typed source identity. It does not download
  ordinary URLs or arXiv URLs.
- `aitp-v5 asset capture-auto --path <local-file>` records an existing local
  file path and hash. By default it does not copy that file into the AITP store.
- Legacy `research/knowledge-hub/source-layer` documentation may mention
  arXiv downloader scripts, but those legacy L0/L1 paths are not the v5 truth
  layer. The v5 truth layer is `registry/source_assets`.

## Storage layout

Acquired files are copied into the v5 store:

```text
.aitp/source_blobs/<topic_id>/<asset_id>/original.pdf
```

The corresponding `registry/source_assets/<asset_id>.md` record stores:

- `uri`: original normalized source URL, for example `https://arxiv.org/pdf/...`
- `content_hash` and `hash_algorithm`
- `metadata.local_path`
- `metadata.blob_path`
- `metadata.source_url`
- `metadata.final_url`
- `metadata.mime_type`
- `metadata.size_bytes`
- `metadata.acquisition_status`
- `metadata.failure_reason`, when acquisition fails

`metadata.blob_path` is stored as a stable path relative to `.aitp`.

## CLI

Acquire a PDF URL:

```text
aitp-v5 asset acquire-pdf --topic <topic-id> --url <http/https/file-url> --title <title>
```

Acquire an arXiv PDF:

```text
aitp-v5 asset acquire-arxiv --topic <topic-id> --arxiv-id <arxiv-id> --title <title>
```

Copy an existing local file into the v5 store while preserving the original
source path:

```text
aitp-v5 asset capture-auto --path <local-file> --topic <topic-id> --copy-to-store
```

## MCP tools

- `aitp_v5_acquire_pdf_source_asset`
- `aitp_v5_acquire_arxiv_source_asset`
- `aitp_v5_capture_source_asset_auto(..., copy_to_store=True)`

The tools return the same `source_asset_record` public surface as existing v5
source asset registration.

## Safety and trust boundary

- Allowed acquisition sources are `http`, `https`, `file`, and `arxiv:`.
- `file://` acquisition must resolve under the topics root or the AITP
  `source_blobs` store. For arbitrary local files, use `capture-auto`; add
  `--copy-to-store` only when a store copy is desired.
- Blob destinations are constrained to `.aitp/source_blobs`.
- Existing blobs with identical bytes are reused. Existing blobs with different
  bytes are not overwritten unless `--force-refresh` is supplied.
- Download failures and validation failures produce honest failed source asset
  records; they do not create fake hashes or fake local paths.
- Source assets are orientation-only source identities. They are not evidence
  and cannot update claim trust.

## Later reading path

Agents should read `metadata.local_path` from the source asset record when they
need the local PDF. Text extraction and chunking should produce separate typed
artifacts or curated RAG chunks linked back to the source asset, and any claim
support still needs explicit evidence and validation records.
