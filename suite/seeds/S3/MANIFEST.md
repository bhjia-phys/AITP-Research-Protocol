# S3 fixture digest manifest

This directory is a complete AITP workspace fixture. The store, topic
metadata, Entry records, Notes, and pinned evidence files are fixed:
verify any deployed copy against the digests below, and do not modify a
pinned file without updating its digest here.

## Layout

- `.aitp/STORE.toml`, `.aitp/topic/TOPIC.md` — store and topic metadata.
- `.aitp/topic/entries/entry-*.md` — 31 Entry records.
- `.aitp/topic/notes/note-*.md` — 2 Notes.
- `literature/`, `calculations/`, `software/` — pinned evidence files.

## Pinned evidence (sha256)

calculations/binder.dat: d0b2549225f19eb25243001c86afcd08d2aba4f2f7d1cad1f47f3f30da9c872b
calculations/chi-08.dat: 2c9ea0286b60281ca925063629d76dc8804706ff3c44183e8111fb3f6bc40b6a
calculations/magnetization.dat: fbc5252019a6a77d14c8e4c298a9d377aa427acd690bf13a7e830a4369699f42
calculations/q1-data.dat: 4418badc03ca71cfefe5dd39bc249c991fb9ff35940d938d5c4a012bff2d3aed
calculations/specific-heat.dat: 6fc4ba146a9e74136cb3e453d924cf2b311330f3fa8cb7ae139a18ae9fae8b1c
calculations/susceptibility.dat: 63dbbd13097c39caa7a12f2603ec6b05159f672d7dc62bc9ce8fb716e1f20b9c
literature/hasenfratz-notes.md: 33e09cf4851e61bbca61e9f907181188365ad25d76a469ea2e8d038f127d1b9a
software/binder-plot.py: 3b1cc05222498c5d5004fe7c51c4edbdf8b32d0e47504f24f666ad417c024544
software/fit-window.py: 6a6c58b430f8ad8e3993fc11678bf4be68fa57b171dc0efef45164c06e098543

Deployment: copy this directory wholesale into an empty workspace;
verify the deployed copy against this manifest.
