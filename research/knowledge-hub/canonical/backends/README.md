# L2 backend registry

This directory registers external knowledge backends that may seed or support `L2`.

It is not a canonical object family.
It is an internal bridge surface for:
- human note libraries,
- software repositories,
- local docs stores,
- result stores.

Use:
- `backend_index.jsonl` as the compact registry
- one `*.json` file per backend as the detailed card

Do not store promoted canonical units here.
Store only backend descriptions and routing rules.
