"""Contracts and canonical path rules for host-neutral Skill packages."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import re
from typing import Any, Mapping
import unicodedata

from brain.v5.contracts import (
    ContractError,
    ContractResult,
    _require_bool_value,
    _require_list,
    _require_mapping,
    _require_nonempty_str,
)


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_DRIVE = re.compile(r"^[A-Za-z]:")
_TYPED_REF = re.compile(r"^[A-Za-z0-9_-]+:[^:\s]+$")


def canonical_package_path(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("package path must be a non-empty string")
    if unicodedata.normalize("NFC", value) != value:
        raise ValueError("package path must use Unicode NFC")
    if "\\" in value or value.startswith("/") or _DRIVE.match(value):
        raise ValueError("package path must be a relative POSIX path")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("package path contains an empty, dot, or parent segment")
    if any("\x00" in part for part in parts):
        raise ValueError("package path contains NUL")
    return value


def validate_skill_package_preview(
    value: Any,
    *,
    path: str = "skill_package_preview",
) -> ContractResult:
    payload = asdict(value) if is_dataclass(value) else value
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, Mapping):
        return result
    for key in (
        "skill_id", "namespace", "name", "semantic_version", "package_hash",
        "preview_dir", "generator_version", "kind",
    ):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("kind") != "skill_package_preview":
        result.add(f"{path}.kind", "must be 'skill_package_preview'")
    if payload.get("namespace") != "aitp-generated":
        result.add(f"{path}.namespace", "must be 'aitp-generated'")
    _require_sha(payload.get("package_hash"), f"{path}.package_hash", result)
    _validate_pinned_ref(payload.get("candidate_ref"), f"{path}.candidate_ref", result)
    _validate_pinned_ref(payload.get("readiness_ref"), f"{path}.readiness_ref", result)
    _require_mapping(payload.get("manifest"), f"{path}.manifest", result)
    _require_list(payload.get("files"), f"{path}.files", result)
    for index, row in enumerate(payload.get("files") or []):
        _validate_file_row(row, f"{path}.files[{index}]", result, receipt_required=False)
    files = payload.get("files") if isinstance(payload.get("files"), list) else []
    names = {
        row.get("path")
        for row in files
        if isinstance(row, Mapping) and isinstance(row.get("path"), str)
    }
    for required in ("SKILL.md", "manifest.json"):
        if required not in names:
            result.add(f"{path}.files", f"must contain {required}")
    _reject_nested_authority(payload, path, result)
    for field, expected in (("can_install_skill", False), ("can_update_claim_trust", False)):
        _require_bool_value(payload.get(field), expected, f"{path}.{field}", result)
    return result


def validate_skill_package_artifact(
    value: Any,
    *,
    path: str = "skill_package_artifact",
) -> ContractResult:
    payload = asdict(value) if is_dataclass(value) else value
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, Mapping):
        return result
    for key in (
        "artifact_id", "skill_id", "semantic_version", "package_hash", "tree_hash",
        "renderer_blob_ref", "renderer_blob_hash", "generator_version", "kind",
    ):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("kind") != "skill_package_artifact":
        result.add(f"{path}.kind", "must be 'skill_package_artifact'")
    for field in ("package_hash", "tree_hash", "renderer_blob_hash"):
        _require_sha(payload.get(field), f"{path}.{field}", result)
    _validate_pinned_ref(payload.get("candidate_ref"), f"{path}.candidate_ref", result)
    _validate_pinned_ref(payload.get("readiness_ref"), f"{path}.readiness_ref", result)
    _require_list(payload.get("template_refs"), f"{path}.template_refs", result)
    for index, item in enumerate(payload.get("template_refs") or []):
        _validate_pinned_ref(item, f"{path}.template_refs[{index}]", result)
    revision = payload.get("renderer_blob_revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        result.add(f"{path}.renderer_blob_revision", "must be a positive integer")
    _require_list(payload.get("files"), f"{path}.files", result)
    for index, row in enumerate(payload.get("files") or []):
        _validate_file_row(row, f"{path}.files[{index}]", result, receipt_required=True)
    rows = payload.get("files") if isinstance(payload.get("files"), list) else []
    raw_names = [row.get("path") for row in rows if isinstance(row, Mapping)]
    names = [value for value in raw_names if isinstance(value, str)]
    if len(names) == len(raw_names) and names != sorted(names, key=lambda value: value.encode("utf-8")):
        result.add(f"{path}.files", "must use canonical UTF-8 path order")
    if len(names) != len(set(names)):
        result.add(f"{path}.files", "must not contain duplicate paths")
    for required in ("SKILL.md", "manifest.json"):
        if required not in names:
            result.add(f"{path}.files", f"must contain {required}")
    for field, expected in (
        ("immutable", True),
        ("can_install_skill", False),
        ("can_update_claim_trust", False),
    ):
        _require_bool_value(payload.get(field), expected, f"{path}.{field}", result)
    _reject_nested_authority(payload, path, result)
    return result


def validate_skill_proposal(value: Any, *, path: str = "skill_proposal") -> ContractResult:
    payload = asdict(value) if is_dataclass(value) else value
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, Mapping):
        return result
    for key in (
        "proposal_id", "skill_id", "namespace", "name", "semantic_version",
        "package_hash", "tree_hash", "review_status", "application_status", "kind",
    ):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("kind") != "skill_proposal":
        result.add(f"{path}.kind", "must be 'skill_proposal'")
    if payload.get("review_status") != "draft":
        result.add(f"{path}.review_status", "must remain 'draft'")
    if payload.get("application_status") != "not_applied":
        result.add(f"{path}.application_status", "must remain 'not_applied'")
    for field in ("package_hash", "tree_hash"):
        _require_sha(payload.get(field), f"{path}.{field}", result)
    for field in ("candidate_ref", "readiness_ref", "package_artifact_ref"):
        _validate_pinned_ref(payload.get(field), f"{path}.{field}", result)
    for field in ("failure_basis", "applicability_selectors", "manifest"):
        _require_mapping(payload.get(field), f"{path}.{field}", result)
    for field in (
        "source_topic_ids", "recipe_refs", "source_program_refs", "execution_refs",
        "validation_refs", "artifact_refs", "code_state_refs", "environment_refs",
        "source_refs", "file_hashes", "validation_commands",
    ):
        _require_list(payload.get(field), f"{path}.{field}", result)
    for field in (
        "recipe_refs", "source_program_refs", "execution_refs", "validation_refs",
        "artifact_refs", "code_state_refs", "environment_refs", "source_refs",
    ):
        for index, item in enumerate(payload.get(field) or []):
            _validate_pinned_ref(item, f"{path}.{field}[{index}]", result)
    _reject_nested_authority(payload, path, result)
    for field, expected in (
        ("requires_human_review", True),
        ("can_install_skill", False),
        ("can_update_claim_trust", False),
    ):
        _require_bool_value(payload.get(field), expected, f"{path}.{field}", result)
    return result


def require_valid_skill_package_preview(value: Any):
    return _require_valid(value, validate_skill_package_preview)


def require_valid_skill_package_artifact(value: Any):
    return _require_valid(value, validate_skill_package_artifact)


def require_valid_skill_proposal(value: Any):
    return _require_valid(value, validate_skill_proposal)


def _require_valid(value: Any, validator):
    result = validator(value)
    if not result.ok:
        raise ContractError(result)
    return value


def _validate_file_row(value: Any, path: str, result: ContractResult, *, receipt_required: bool) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, Mapping):
        return
    try:
        canonical_package_path(value.get("path"))
    except (TypeError, ValueError) as exc:
        result.add(f"{path}.path", str(exc))
    if value.get("mode") not in {"0644", "0755"}:
        result.add(f"{path}.mode", "must be 0644 or 0755")
    length = value.get("length")
    if isinstance(length, bool) or not isinstance(length, int) or length < 0:
        result.add(f"{path}.length", "must be a non-negative integer")
    _require_sha(value.get("sha256"), f"{path}.sha256", result)
    if receipt_required:
        _require_nonempty_str(value, "blob_receipt_ref", path, result)
        _require_sha(
            value.get("blob_receipt_content_hash"),
            f"{path}.blob_receipt_content_hash",
            result,
        )
        revision = value.get("blob_receipt_revision")
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
            result.add(f"{path}.blob_receipt_revision", "must be a positive integer")


def _validate_pinned_ref(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, Mapping):
        return
    record_ref = value.get("record_ref")
    if not isinstance(record_ref, str) or not _TYPED_REF.fullmatch(record_ref):
        result.add(f"{path}.record_ref", "must be an exact typed record ref")
    _require_sha(value.get("content_hash"), f"{path}.content_hash", result)
    revision = value.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        result.add(f"{path}.revision", "must be a positive integer")


def _reject_nested_authority(value: Any, path: str, result: ContractResult) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in {"can_update_claim_trust", "can_install_skill", "can_write_evidence"} and item is not False:
                result.add(f"{path}.{key}", "must be false")
            _reject_nested_authority(item, f"{path}.{key}", result)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_nested_authority(item, f"{path}[{index}]", result)


def _require_sha(value: Any, path: str, result: ContractResult) -> None:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        result.add(path, "must be lowercase sha256")
