"""Golden parity for the split runtime.

The committed fixture store under ``fixtures/golden/store`` is a fully
initialized ``nio`` topic ("Magnetic NiO") with fixed record IDs and
timestamps.  It contains one resolved failure plus its resolving decision, one
unresolved failure, one superseded result plus its superseding result, one
``run`` and one ``decision`` entry, a working Note, a theory Note, and one
valid unsaved result draft under ``.aitp/local/drafts/``.  All evidence pins
are ``sha256`` only (no ``git`` pins), so save-time validation passes in the
copied temp store, which has no ``.git``.

Fixture-only adjustments (the store otherwise matches a fresh ``aitp init``):
the store-local gitignore rules that would exclude ``.aitp/local/`` were
neutralized so the draft is committable, and the machine-specific build root
in ``.aitp/local/config.toml`` was normalized to the same ``<golden-store>``
marker used for the payload ``root`` below.

Regeneration is deliberate only: build the store and the golden JSONs with
the CLI and the public API, freeze IDs and timestamps by hand, and replace
the payload ``root`` with ``<golden-store>``.  The scratch builder used for
this fixture is ``/tmp/aitp-m05-fixture/build.py`` (not part of the repo).
Volatile fields (UUIDs, wall-clock timestamps) must never appear in the
fixture records.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from aitp.core import enter_workspace, save_entry

FIXTURES = Path(__file__).parent / "fixtures" / "golden"
STORE = FIXTURES / "store"
ROOT_MARKER = "<golden-store>"
DRAFT_RELATIVE = ".aitp/local/drafts/entry-88888888888888888888888888888888.md"
ENTRY_ID = "entry-88888888888888888888888888888888"


def copy_store(tmp_path: Path) -> Path:
    root = tmp_path / "store"
    shutil.copytree(STORE, root)
    return root


def golden(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def normalized(payload: dict) -> dict:
    payload["root"] = ROOT_MARKER
    return payload


def test_enter_matches_golden_before_save(tmp_path: Path) -> None:
    root = copy_store(tmp_path)
    assert normalized(enter_workspace(root)) == golden("enter.json")


def test_saving_the_fixture_draft_matches_golden(tmp_path: Path) -> None:
    root = copy_store(tmp_path)
    draft = root / DRAFT_RELATIVE
    assert draft.is_file()

    saved = save_entry(root, DRAFT_RELATIVE)
    assert saved == {
        "status": "saved",
        "path": f".aitp/topic/entries/{ENTRY_ID}.md",
    }

    final = root / ".aitp" / "topic" / "entries" / f"{ENTRY_ID}.md"
    assert final.is_file()
    assert final.read_bytes() == draft.read_bytes()

    assert normalized(enter_workspace(root)) == golden("enter-after-save.json")
