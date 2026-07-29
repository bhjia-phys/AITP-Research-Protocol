# M0.5 Slim Core

Status: required before M1 implementation

## Measured baseline

On 2026-07-29:

- canonical package: 1,077 Python lines;
- `engine.py`: 875 lines;
- plugin runtime copy: another 1,077 lines;
- bundled PyYAML: 544 KB;
- plugin `--help`: about 0.19 seconds;
- real-workspace `enter`: about 0.16 seconds.

Runtime speed is currently acceptable. Source duplication and concentration in
one file are not.

## Target

Keep exactly one runtime implementation inside the installable plugin and
package the standalone `aitp` command from that same source:

```text
plugins/aitp-research-protocol/
├── scripts/
│   ├── aitp.py
│   └── runtime/
│       ├── aitp/
│       │   ├── cli.py
│       │   ├── workspace.py
│       │   ├── records.py
│       │   ├── notes.py
│       │   └── state.py
│       └── yaml/          vendored dependency
└── skills/
```

`pyproject.toml` points to this same `runtime/aitp` package. Remove `src/aitp`
after parity tests pass.

The split is mechanical:

- `workspace.py`: root resolution, initialization, store metadata;
- `records.py`: Entry templates, validation, relations, save;
- `notes.py`: Note preparation, validation, save;
- `state.py`: active-state projection and `enter`;
- `cli.py`: argument parsing and dispatch only.

Do not introduce service objects, repositories, dependency injection, control
planes, or compatibility adapters.

## Gates

M0.5 is complete only when:

- all ledger and offline-plugin tests pass unchanged;
- one canonical `aitp` package exists in Git;
- no Python module exceeds 400 nonblank lines;
- `python -m aitp` and the plugin runner use identical code;
- a benchmark covers CLI help, 20 Entries, and 1,000 Entries;
- `--help` remains below 250 ms and 1,000-Entry `enter` below one second on the
  recorded test machine;
- plugin installation and `$aitp` work without MCP, a daemon, or a database.

This milestone adds no user-facing feature.
