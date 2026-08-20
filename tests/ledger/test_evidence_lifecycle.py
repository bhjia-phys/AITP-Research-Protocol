"""M1e evidence lifecycle: sha256-once and check-policy grading."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from aitp.core import (
    AITPError,
    atomic_write,
    check_workspace,
    init_workspace,
    parse_markdown,
    prepare_entry,
    render_markdown,
    save_entry,
)


def initialized(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    init_workspace(root, "m1e", "M1e lifecycle")
    return root


def pinned_file(root: Path, relative: str, text: str = "evidence\n") -> dict[str, str]:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return {
        "target": relative,
        "at": f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}",
        "locator": "whole file",
    }


def save_result(root: Path, ref: dict[str, str], *, summary: str = "Result.") -> str:
    prepared = prepare_entry(root, "result", "agent", created_by="agent:test")
    path = root / prepared["path"]
    frontmatter, _, _ = parse_markdown(path)
    frontmatter.update(
        {
            "summary": summary,
            "refs": [ref],
            "limitations": ["Boundary."],
            "resolves": [],
            "supersedes": [],
            "next_action": "",
        }
    )
    body = """## Durable Summary

Result.

## Basis And Checks

Pinned evidence.

## Validity And Implication

Conditional result.
"""
    atomic_write(path, render_markdown(frontmatter, body))
    saved = save_entry(root, prepared["path"])
    return saved["path"]


def finding(check: dict, path: str) -> dict | None:
    for item in check["findings"]:
        if item["path"] == path and item["code"] in {
            "hash_mismatch",
            "historical_pin_drift",
            "historical_ref_missing",
            "missing_ref",
            "invalid_check_policy",
        }:
            return item
    return None


def write_policy(root: Path, policy: dict) -> None:
    path = root / ".aitp" / "local" / "check-policy.json"
    atomic_write(path, json.dumps(policy) + "\n")


def test_sha256_once_rejects_bad_digest_at_save(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    ref = pinned_file(root, "theory/check.md")
    ref["at"] = "sha256-once:" + ("0" * 64)
    with pytest.raises(AITPError) as error:
        save_result(root, ref)
    assert error.value.code == "hash_mismatch"


def test_sha256_once_drift_is_warning(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    path = root / "PROJECT_MEMORY.md"
    path.write_text("old\n", encoding="utf-8")
    ref = {
        "target": "PROJECT_MEMORY.md",
        "at": f"sha256-once:{hashlib.sha256(path.read_bytes()).hexdigest()}",
    }
    entry = save_result(root, ref)
    path.write_text("new bytes\n", encoding="utf-8")
    item = finding(check_workspace(root), entry)
    assert item == {
        "level": "warning",
        "code": "historical_pin_drift",
        "path": entry,
        "message": (
            f"sha256-once drift: PROJECT_MEMORY.md: recorded {ref['at'].split(':',1)[1]}, "
            f"current {hashlib.sha256(path.read_bytes()).hexdigest()}"
        ),
    }


def test_sha256_once_missing_is_warning(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    path = root / "live.json"
    path.write_text("old\n", encoding="utf-8")
    ref = {
        "target": "live.json",
        "at": f"sha256-once:{hashlib.sha256(path.read_bytes()).hexdigest()}",
    }
    entry = save_result(root, ref)
    path.unlink()
    item = finding(check_workspace(root), entry)
    assert item is not None
    assert item["level"] == "warning"
    assert item["code"] == "historical_ref_missing"


def test_policy_downgrades_legacy_drift_and_missing(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    write_policy(root, {"schema": "aitp/check-policy-0.1", "mutable": [{"paths": ["mutable/**"]}], "immutable": []})
    path = root / "mutable" / "canon.md"
    path.parent.mkdir()
    path.write_text("old\n", encoding="utf-8")
    ref = {
        "target": "mutable/canon.md",
        "at": f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}",
    }
    entry = save_result(root, ref)
    path.write_text("new\n", encoding="utf-8")
    item = finding(check_workspace(root), entry)
    assert item is not None and item["level"] == "warning" and item["code"] == "historical_pin_drift"

    path.unlink()
    item = finding(check_workspace(root), entry)
    assert item is not None and item["level"] == "warning" and item["code"] == "historical_ref_missing"


def test_policy_immutable_keeps_legacy_error(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    write_policy(
        root,
        {
            "schema": "aitp/check-policy-0.1",
            "mutable": [{"paths": ["mutable/**"]}],
            "immutable": [{"paths": ["evidence/**"]}],
        },
    )
    path = root / "evidence" / "manifest.json"
    path.parent.mkdir()
    path.write_text("old\n", encoding="utf-8")
    ref = {"target": "evidence/manifest.json", "at": f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"}
    entry = save_result(root, ref)
    path.write_text("new\n", encoding="utf-8")
    item = finding(check_workspace(root), entry)
    assert item is not None and item["level"] == "error" and item["code"] == "hash_mismatch"


def test_no_policy_legacy_stays_error(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    path = root / "PROJECT_MEMORY.md"
    path.write_text("old\n", encoding="utf-8")
    ref = {"target": "PROJECT_MEMORY.md", "at": f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"}
    entry = save_result(root, ref)
    path.write_text("new\n", encoding="utf-8")
    item = finding(check_workspace(root), entry)
    assert item is not None and item["level"] == "error" and item["code"] == "hash_mismatch"


def test_malformed_policy_reports_invalid_check_policy(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    path = root / ".aitp" / "local" / "check-policy.json"
    atomic_write(path, "{not json\n")
    report = check_workspace(root)
    assert any(
        f["path"] == ".aitp/local/check-policy.json" and f["code"] == "invalid_check_policy" and f["level"] == "error"
        for f in report["findings"]
    )
    assert report["status"] == "findings"
