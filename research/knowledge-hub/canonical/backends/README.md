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
- `backend.template.json` as the generic authoring template
- `examples/` for public example cards that demonstrate recommended patterns

Public starter pack for formal-theory backends:
- `FORMAL_THEORY_BACKEND_STARTER.md`
- `examples/formal-theory-note-library.example.json`
- `../../runtime/scripts/run_formal_theory_backend_smoke.sh`

Do not store promoted canonical units here.
Store only backend descriptions and routing rules.
