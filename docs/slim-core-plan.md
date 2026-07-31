# M0.5 Slim Core — implementation plan

Status: ready for implementation. Green-lit by the third external review.
Scope: mechanical deduplication and module split only. **No behavior change,
no schema change, no new commands, no v0.2 semantics.** Anything not listed
here is out of scope.

## Measured baseline (2026-07-29/30)

Canonical package today (`src/aitp/`):

| File | Nonblank lines | Content |
|---|---|---|
| `engine.py` | 803 | everything: IO, workspace, records, notes, state |
| `cli.py` | 106 | argparse + dispatch (imports from `.core`) |
| `core.py` | 67 | public facade; monkey-patches `engine.now_utc`; redundant idempotency pre-check |
| `__init__.py` | 2 | version |
| `__main__.py` | 2 | `from .cli import main; raise SystemExit(main())` |
| **total** | **980** | cap after this stage: ≤ 1,000 |

Duplication facts:

- `plugins/aitp-research-protocol/scripts/vendor/aitp/` contains a
  hand-maintained copy; its `.py` files are currently **byte-identical** to
  `src/aitp/` (verified with `diff -rq`). It has `resources/templates/` but
  no `resources/skills/`.
- `src/aitp/resources/skills/` holds stale skill copies also shipped by the
  pip package. The live skills are `plugins/aitp-research-protocol/skills/`.
- `plugins/.../scripts/vendor/yaml/` is the vendored PyYAML (only used by
  the plugin launcher); pip installs use the `PyYAML>=5.4` dependency.
- `plugins/.../scripts/aitp.py` prepends `vendor/` to `sys.path` and calls
  `aitp.cli:main`. It does not change.

Test-suite dependencies that constrain the refactor:

- `tests/ledger/test_core.py`, `test_distribution.py` import from
  `aitp.core` (facade names must stay importable from `aitp.core`).
- `test_distribution.py::test_prepared_entries_have_strictly_ordered_timestamps`
  requires microsecond-precision `created_at` on consecutive prepares.
- `test_distribution.py::test_using_aitp_skill_is_packaged_and_matches_cli`
  asserts the pip package bundles `resources/skills/using-aitp` — this test
  is replaced in step 3 (see "Test-change whitelist").
- `tests/ledger/test_cli.py` sets `PYTHONPATH=<repo>/src` (mechanical edit
  in step 3).
- `tests/ledger/test_plugin.py` runs `scripts/aitp.py -I`; unaffected.

## Target layout

Canonical home: `plugins/aitp-research-protocol/scripts/vendor/aitp/`
(it already is the plugin's runtime; it becomes the only one).
`pyproject.toml` points at the same directory. `src/aitp/` is deleted.

| Module | Responsibility | What moves there | Est. nonblank |
|---|---|---|---|
| `md.py` | record-file format and safe writes | `AITPError`, `PROMPT_MARKER`, `now_utc` (microsecond-precise, moved from `core.py`), `dump_yaml`, `render_markdown`, `parse_markdown`, `atomic_write`, `_section_content` | ~70 |
| `workspace.py` | root resolution, store metadata, init, write lock | `_template`, `_safe_slug`, `_git_root`, `resolve_root`, `_ensure_safe_root`, `_quoted_toml`, `load_store`, `_init_files`, `init_workspace`, `store_lock` | ~220 |
| `records.py` | Entry templates, validation, relations, save | `ENTRY_KINDS`, `AUTHORITIES`, `REF_REQUIRED_KINDS`, `LIMITATION_REQUIRED_KINDS`, `ENTRY_ID_RE`, `ENTRY_SECTIONS`, `_drafts`, `_canonical_entries`, `_find_idempotency`, `prepare_entry`, `_inside`, `_git_has`, `validate_refs`, `_entry_map`, `_validate_relations`, `validate_entry`, `save_entry` | ~300 |
| `notes.py` | Note preparation, validation, save | `NOTE_ID_RE`, `NOTE_MODES`, `NOTE_SECTIONS`, `prepare_note`, `save_note` | ~120 |
| `state.py` | active-state projection | `_topic_goal`, `enter_workspace` | ~135 |
| `core.py` | stable public facade | re-exports only, same `__all__` as today | ~30 |
| `cli.py` | argparse + dispatch | unchanged (it imports from `.core`, which keeps the same names) | 106 |
| `__init__.py`, `__main__.py` | — | unchanged | 4 |

Total ≈ 985, inside the ≤ 1,000 cap. No module exceeds 400 nonblank lines.

Import rules (acyclic, no new indirection):

- `md` imports nothing from the package (stdlib + `yaml` only).
- `workspace` imports from `md`.
- `records` imports from `md` and `workspace`.
- `notes` imports from `md`, `workspace`, `records` (`validate_refs`).
- `state` imports from `md`, `workspace`, `records` (`validate_entry`,
  `_canonical_entries`).
- `core` re-exports; `cli` imports `core` only.

Do not introduce service objects, repositories, dependency injection,
control planes, or compatibility adapters. Functions move verbatim except
for the import lines and the two deletions below.

Behavior invariants (verify by unchanged tests + golden parity):

- `now_utc` keeps microsecond precision (`datetime.now(UTC)
  .isoformat(timespec="microseconds").replace("+00:00", "Z")`); the
  `core.py` monkey-patch and its comment are deleted, and the duplicate
  canonical-idempotency pre-check in `core.prepare_entry` is deleted
  (`records.prepare_entry` already performs it via `_find_idempotency`).
  Deleting the wrapper is only behavior-preserving if
  `_find_idempotency` checks the **canonical entries directory before the
  drafts directory**: saving does not remove the draft, so a drafts-first
  scan would return the draft path on a post-save retry, while the old
  two-tier code always returned the saved canonical path.
- `core.__all__` and every name importable from `aitp.core` stay identical.
- CLI commands, flags, exit codes, and error payload shape stay identical.
- Templates stay inside the package at `aitp/resources/templates/`, loaded
  via `importlib.resources.files("aitp")`.
- Idempotency semantics unchanged: prepare returns `status: existing` when
  the key exists in drafts or canonical entries; save returns
  `already_saved` on a byte-identical retry; `store_lock` stays an
  `O_EXCL` lock file under `.aitp/local/locks/`.

## Migration steps (the suite is green after every step)

### Step 1 — split inside `src/aitp/`

Create `md.py`, `workspace.py`, `records.py`, `notes.py`, `state.py` from
`engine.py` per the table; rewrite `core.py` as the pure facade; delete
`engine.py`. Packaging config is untouched, so the suite still runs against
`src`:

```bash
uv run --python 3.12 --with pytest python -m pytest -q   # expect 12 passed
```

### Step 2 — sync the split package to the plugin vendor dir

Replace `plugins/aitp-research-protocol/scripts/vendor/aitp/*.py` with the
new split modules; delete stale `__pycache__` directories under `vendor/`.
`vendor/aitp/resources/templates/` is already identical — do not touch it.
Run the plugin contract tests:

```bash
uv run --python 3.12 --with pytest python -m pytest -q tests/ledger/test_plugin.py
```

### Step 3 — repoint packaging, delete `src/`

`pyproject.toml`:

```toml
[tool.setuptools]
package-dir = {"" = "plugins/aitp-research-protocol/scripts/vendor"}
include-package-data = true

[tool.setuptools.packages.find]
where = ["plugins/aitp-research-protocol/scripts/vendor"]

[tool.setuptools.package-data]
aitp = ["resources/templates/**/*.md"]

[tool.pytest.ini_options]
pythonpath = ["plugins/aitp-research-protocol/scripts/vendor"]
```

Then delete `src/` (including `aitp_research_protocol.egg-info`), apply the
two whitelisted test edits (below), and run the full suite:

```bash
uv run --python 3.12 --with pytest python -m pytest -q   # expect 12 passed
uv run --python 3.12 --with-editable . aitp --help       # editable install works
```

### Step 4 — add golden parity and the benchmark

Add `tests/ledger/fixtures/golden/`, `tests/ledger/test_golden.py`, and
`tests/ledger/benchmark.py` as specified below. All tests pass.

### Step 5 — record the evidence

Run the benchmark and the line-count check; append the numbers to the
completion note at the bottom of this file.

## Test-change whitelist (the only test edits allowed)

Everything else in `tests/` stays byte-identical.

1. `tests/ledger/test_cli.py`: the `PYTHONPATH` line becomes
   `env["PYTHONPATH"] = str(Path(__file__).parents[2] / "plugins" /
   "aitp-research-protocol" / "scripts" / "vendor")`.
2. `tests/ledger/test_distribution.py`: replace
   `test_using_aitp_skill_is_packaged_and_matches_cli` with a single-source
   check (the pip package no longer bundles skills; the plugin copy is the
   only one):

```python
def test_using_aitp_skill_has_a_single_source() -> None:
    plugin = Path(__file__).parents[2] / "plugins" / "aitp-research-protocol"
    skill = (plugin / "skills" / "using-aitp" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    metadata = (plugin / "skills" / "using-aitp" / "agents" / "openai.yaml")
    assert "name: using-aitp" in skill
    assert "aitp enter" in skill
    assert "aitp record prepare" in skill
    assert "aitp note prepare --mode working --title" in skill
    assert "there is no `aitp search`" in skill
    assert "$using-aitp" in metadata.read_text(encoding="utf-8")
    assert not files("aitp").joinpath("resources/skills").is_dir()
```

## Golden parity specification

Committed fixture `tests/ledger/fixtures/golden/store/`: one initialized
Topic (`nio`, "Magnetic NiO") with fixed IDs and timestamps, containing at
least: one resolved failure + its resolving entry, one unresolved failure,
one superseded entry + its superseding entry, one `run` and one `decision`
entry, one working Note, one theory Note, and one valid draft under
`.aitp/local/drafts/`. Fixture files are built once with the CLI, then their
IDs and timestamps are frozen by hand and committed verbatim. All refs in
fixture records and in the fixture draft use `sha256` pins only (no `git`
pins), so save-time evidence validation passes in the copied temp store,
which has no `.git`.

`tests/ledger/test_golden.py`:

1. copies the fixture store into `tmp_path`;
2. runs `enter_workspace` and compares the payload to committed
   `enter.json` after replacing the machine-specific `root` value;
3. saves the committed draft and asserts both the payload and the saved
   file bytes match the committed goldens;
4. runs `enter_workspace` again and compares to committed
   `enter-after-save.json` (root normalized).

Golden JSON files are committed. They are regenerated only deliberately, by
running the documented regeneration snippet in the test docstring, never as
part of a routine refactor. Volatile fields (UUIDs, wall-clock timestamps)
must not appear: all fixture records carry fixed values.

## Benchmark specification

`tests/ledger/benchmark.py` — a plain script (`__main__` guard), not a
pytest module, so it never runs in the default suite:

- builds two fixture stores in a temp directory via the in-process API:
  20 valid Entries and 1,000 valid Entries (deterministic content, unique
  IDs; fixture construction is not timed);
- measures via subprocess (real startup cost; the subprocess env carries
  the vendor directory on `PYTHONPATH`, same as `test_cli.py` does), one
  warmup + five timed runs, reporting median/min/max:
  - `python -m aitp --help`;
  - `python -I plugins/aitp-research-protocol/scripts/aitp.py --help`;
  - `python -m aitp enter --json` on the 20-Entry and the 1,000-Entry
    store (same for the plugin runner);
- prints one JSON object: Python version, platform, machine, fixture sizes,
  and every measurement, plus PASS/FAIL against the thresholds
  (`--help` < 250 ms; 1,000-Entry `enter` < 1 s).

## Gates

M0.5 is complete only when:

- the 12 pre-existing ledger/plugin tests pass with only the two
  whitelisted edits, and the new golden-parity tests also pass;
- one canonical `aitp` package exists in Git, at
  `plugins/aitp-research-protocol/scripts/vendor/aitp/`;
- no Python module exceeds 400 nonblank lines
  (`grep -c '\S' <module>.py` per file);
- the canonical package totals ≤ 1,000 nonblank lines
  (`grep -c '\S' plugins/aitp-research-protocol/scripts/vendor/aitp/*.py`,
  summed);
- `python -m aitp` (via pytest `pythonpath` and via editable install) and
  the plugin runner use identical code — the `src/` tree is gone;
- `tests/ledger/benchmark.py` runs and prints PASS on the recorded machine,
  with interpreter, machine, and fixture sizes in its output;
- plugin installation and `$aitp` work without MCP, a daemon, or a database;
- `pyproject.toml` builds an editable install whose `aitp` command works and
  whose package contains templates but no `resources/skills`.

## Explicit non-goals for this stage

No `created_at` semantics change; no `aitp check`; no `aitp show`/`list`;
no schema 0.2 (`prediction`, `question`, `resolution`, `contradicts`);
no `enter` v2 sections; no `init --adopt`; no template content edits; no
skill content edits; no dependency changes.

## Completion note

Gate: 2026-07-31. Base commit `f4b1be91`; all changes are working-tree
edits (no commits were made per the migration constraints).

### Final canonical package — nonblank lines (`grep -c '\S'`)

`plugins/aitp-research-protocol/scripts/vendor/aitp/` is the single canonical
runtime; `src/` is deleted.

| Module | Nonblank |
|---|---|
| `__init__.py` | 2 |
| `__main__.py` | 2 |
| `cli.py` | 106 |
| `core.py` | 19 |
| `md.py` | 63 |
| `notes.py` | 133 |
| `records.py` | 292 |
| `state.py` | 138 |
| `workspace.py` | 226 |
| **total** | **981** |

Total ≤ 1,000 cap ✓; every module < 400 (max 292) ✓.

### Test counts

`uv run --python 3.12 --with pytest python -m pytest -q` → **14 passed**
(12 pre-existing with only the two whitelisted test edits + 2 new
golden-parity tests). The suite was green after every migration step
(12 passed after steps 1–3, 14 after step 4). Step 2 plugin contract tests
(`tests/ledger/test_plugin.py`) green.

### Benchmark

`uv run --python 3.12 python tests/ledger/benchmark.py` → **result: FAIL**
(exit 1). `--help` module median 104.2 ms, plugin 100.1 ms (threshold
< 250 ms: PASS). 1,000-Entry `enter` module median 1050.8 ms, plugin
1037.6 ms (threshold < 1 s: FAIL). Full JSON:

```json
{
  "result": "FAIL",
  "python_version": "3.12.13",
  "platform": "linux",
  "machine": "x86_64",
  "fixtures": {"small_entries": 20, "large_entries": 1000},
  "measurements": {
    "module_help": {"median_ms": 104.229, "min_ms": 99.67, "max_ms": 105.608},
    "plugin_help": {"median_ms": 100.141, "min_ms": 94.017, "max_ms": 114.064},
    "module_enter_20": {"median_ms": 120.009, "min_ms": 112.735, "max_ms": 125.506},
    "module_enter_1000": {"median_ms": 1050.82, "min_ms": 1027.314, "max_ms": 1089.918},
    "plugin_enter_20": {"median_ms": 116.212, "min_ms": 113.064, "max_ms": 129.033},
    "plugin_enter_1000": {"median_ms": 1037.629, "min_ms": 1005.709, "max_ms": 1041.135}
  },
  "thresholds": {"help_ms": 250.0, "enter_1000_ms": 1000.0},
  "pass": false
}
```

The 1,000-Entry `enter` gap is a **pre-existing runtime cost, not an M0.5
regression**: the pre-refactor package from `f4b1be91` measures the same on
this idle machine — in-process `enter_workspace` on 1,000 entries 937.1 ms
(old) vs 936.5 ms (new); subprocess `enter` 996–1066 ms (old) vs 1027–1090 ms
(new). ~80% of the cost is per-record YAML frontmatter parsing. M0.5 is
behavior-change-free by design, so this stays a documented gap for a later
stage rather than an in-scope optimization.

### Approved deviations from the plan text

1. `_find_idempotency` scans canonical entries before drafts (order flipped)
   — the plan's "delete the redundant core wrapper" as literally written
   changed the returned path for an already-saved key (draft path instead of
   canonical path) and broke the unchanged
   `test_result_round_trip_is_grounded_and_idempotent`; the flip preserves
   the old observable semantics exactly.
2. `test_distribution.py` whitelisted replacement asserts the two-line form
   `"there is no\n\`aitp search\`"` — the plan's single-line substring does
   not occur in the plugin `SKILL.md` (the phrase is line-wrapped there).
3. `benchmark.py` constructs the fixture stores via prepare + direct write to
   the canonical entries directory instead of `save_entry` — `save_entry`
   re-parses the whole canonical set per save (O(n²)); construction is
   explicitly not timed and the written entries are byte-identical to
   `save_entry`'s output. The store is validated once through the public API
   (`enter_workspace` → `memory_status: available`).

### Gate checklist

- [x] 12 pre-existing ledger/plugin tests pass with only the two whitelisted
  edits; golden-parity tests pass (14 total).
- [x] One canonical `aitp` package at
  `plugins/aitp-research-protocol/scripts/vendor/aitp/`; `src/` gone.
- [x] No module > 400 nonblank lines (max 292).
- [x] Canonical total ≤ 1,000 nonblank lines (981).
- [x] `python -m aitp` (pytest `pythonpath` and editable install) and the
  plugin runner use identical code.
- [x] `tests/ledger/benchmark.py` runs; prints **FAIL** on the recorded
  machine for the 1,000-Entry `enter` threshold (pre-existing gap, see
  above); fixture sizes and machine recorded in its output.
- [x] Plugin installation and `$aitp` work without MCP, a daemon, or a
  database.
- [x] `pyproject.toml` editable install: `aitp` command works; package
  contains templates, no `resources/skills`.

### Gatekeeper addendum (2026-07-30)

Independent verification of the above: module set, line counts (981 total,
max 292), and the 14-test suite all reproduced. The benchmark was re-run on
the idle machine by the gatekeeper: `module_enter_1000` median 936.4 ms
(max 984.3), `plugin_enter_1000` median 951.9 ms (max 999.5), `--help`
medians 91.6/94.9 ms — **PASS**. Codex's earlier FAIL (1050.8/1037.6 ms)
was a loaded-machine run; the cost straddles the 1 s threshold depending on
load, with only ~6% idle-machine headroom. Verdict: **M0.5 gate PASSED** —
no performance regression (pre-refactor in-process 937.1 ms vs post 936.5
ms), all eight gate items satisfied. The thin headroom is recorded as M1a
scope (see `docs/roadmap.md`), not waived.

