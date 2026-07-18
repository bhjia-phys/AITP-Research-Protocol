"""Disposable, integrity-bound host-session continuity for selected routes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import unicodedata

from brain.v5.context_injection_contracts import hash_json, workspace_identity
from brain.v5.host_route_contracts import (
    HostRouteDecision,
    HostRouteRequest,
    normalize_host_route_request,
)
from brain.v5.host_route_normalization import is_sha256
from brain.v5.markdown import write_text_atomic
from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository
from brain.v5.research_retrieval import (
    QuerySnapshotSession,
    ResearchQuery,
    query_records,
)


HOST_ROUTE_MAPPING_SCHEMA_VERSION = "aitp.host_route_mapping.v1"
HOST_ROUTE_MAPPING_TTL = timedelta(hours=24)


@dataclass(frozen=True)
class HostRouteMapping:
    workspace_identity: str
    namespace_sha256: str
    host: str
    host_session_id: str
    continuity_fingerprint: str
    source_request_fingerprint: str
    selected_topic_id: str
    selected_session_id: str
    selected_exact_refs: tuple[str, ...]
    index_generation: int
    canonical_watermark: str
    created_at: str
    verified_at: str
    expires_at: str
    runtime_path: str
    integrity_hash: str
    schema_version: str = HOST_ROUTE_MAPPING_SCHEMA_VERSION
    orientation_only: bool = True
    canonical_write_allowed: bool = False
    can_update_claim_trust: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != HOST_ROUTE_MAPPING_SCHEMA_VERSION:
            raise ValueError("unsupported host route mapping schema")
        for label, value in (
            ("workspace_identity", self.workspace_identity),
            ("host", self.host),
            ("host_session_id", self.host_session_id),
            ("selected_topic_id", self.selected_topic_id),
            ("selected_session_id", self.selected_session_id),
            ("runtime_path", self.runtime_path),
        ):
            if not isinstance(value, str) or not value:
                raise ValueError(f"{label} must be a non-empty string")
            if value != unicodedata.normalize("NFC", value):
                raise ValueError(f"{label} must be NFC-normalized")
        for label, value in (
            ("namespace_sha256", self.namespace_sha256),
            ("continuity_fingerprint", self.continuity_fingerprint),
            ("source_request_fingerprint", self.source_request_fingerprint),
            ("canonical_watermark", self.canonical_watermark),
            ("integrity_hash", self.integrity_hash),
        ):
            if not is_sha256(value):
                raise ValueError(f"{label} must be a SHA-256 digest")
        if not isinstance(self.index_generation, int) or self.index_generation < 1:
            raise ValueError("index_generation must be a positive integer")
        if not isinstance(self.selected_exact_refs, tuple) or not self.selected_exact_refs:
            raise ValueError("selected_exact_refs must be a non-empty tuple")
        if len(self.selected_exact_refs) > 32:
            raise ValueError("selected_exact_refs exceeds the route bound")
        for timestamp in (self.created_at, self.verified_at, self.expires_at):
            _parse_timestamp(timestamp)
        if self.orientation_only is not True:
            raise ValueError("orientation_only must be true")
        if self.canonical_write_allowed is not False:
            raise ValueError("canonical_write_allowed must be false")
        if self.can_update_claim_trust is not False:
            raise ValueError("can_update_claim_trust must be false")


def write_host_route_mapping(
    ws: WorkspacePaths,
    request: HostRouteRequest,
    decision: HostRouteDecision,
) -> HostRouteMapping:
    normalized = _cache_request(request)
    if decision.status != "selected" or not decision.coverage.strong_selection_eligible:
        raise ValueError("only a strongly verified selected route can be cached")
    candidate = next(
        (
            item
            for item in decision.candidates
            if not item.supporting_only
            and item.topic_id == decision.selected_topic_id
            and item.session_id == decision.selected_session_id
        ),
        None,
    )
    if candidate is None:
        raise ValueError("selected route has no matching primary candidate")
    exact_refs = tuple(
        dict.fromkeys(
            (
                f"session:{decision.selected_session_id}",
                f"topic:{decision.selected_topic_id}",
                *candidate.exact_refs,
            )
        )
    )
    if _verify_exact_refs(ws, normalized, exact_refs):
        raise ValueError("selected route exact anchors are unavailable")

    namespace = _namespace_digest(ws, normalized)
    path = _mapping_path(ws, namespace)
    now = _utc_now()
    payload = {
        "schema_version": HOST_ROUTE_MAPPING_SCHEMA_VERSION,
        "workspace_identity": workspace_identity(ws),
        "namespace_sha256": namespace,
        "host": _nfc(normalized.host),
        "host_session_id": _nfc(normalized.host_session_id),
        "continuity_fingerprint": _continuity_fingerprint(ws, normalized),
        "source_request_fingerprint": decision.request_fingerprint,
        "selected_topic_id": decision.selected_topic_id,
        "selected_session_id": decision.selected_session_id,
        "selected_exact_refs": list(exact_refs),
        "index_generation": decision.coverage.index_generation,
        "canonical_watermark": decision.coverage.canonical_watermark,
        "created_at": now.isoformat(),
        "verified_at": now.isoformat(),
        "expires_at": (now + HOST_ROUTE_MAPPING_TTL).isoformat(),
        "runtime_path": path.relative_to(ws.base.resolve(strict=False)).as_posix(),
        "orientation_only": True,
        "canonical_write_allowed": False,
        "can_update_claim_trust": False,
    }
    payload["integrity_hash"] = _integrity_hash(payload)
    mapping = _mapping_from_payload(payload)
    write_text_atomic(path, _serialize(payload))
    return mapping


def read_host_route_mapping(
    ws: WorkspacePaths,
    request: HostRouteRequest,
) -> HostRouteMapping | None:
    try:
        normalized = _cache_request(request)
        namespace = _namespace_digest(ws, normalized)
        path = _mapping_path(ws, namespace)
        if not path.exists() or not path.is_file():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        mapping = _mapping_from_payload(payload)
        if mapping.integrity_hash != _integrity_hash(payload):
            return None
        expected_runtime = path.relative_to(ws.base.resolve(strict=False)).as_posix()
        expected = {
            "workspace_identity": workspace_identity(ws),
            "namespace_sha256": namespace,
            "host": _nfc(normalized.host),
            "host_session_id": _nfc(normalized.host_session_id),
            "continuity_fingerprint": _continuity_fingerprint(ws, normalized),
            "runtime_path": expected_runtime,
        }
        if any(getattr(mapping, key) != value for key, value in expected.items()):
            return None
        now = _utc_now()
        if now >= _parse_timestamp(mapping.expires_at):
            return None
        if _parse_timestamp(mapping.created_at) > now + timedelta(minutes=5):
            return None
        if not _mapping_index_is_current(ws, mapping):
            return None
        if _verify_exact_refs(ws, normalized, mapping.selected_exact_refs):
            return None
        return mapping
    except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError):
        return None


def clear_host_route_mapping(ws: WorkspacePaths, request: HostRouteRequest) -> bool:
    normalized = _cache_request(request)
    path = _mapping_path(ws, _namespace_digest(ws, normalized))
    if not path.exists():
        return False
    path.unlink()
    return True


def _cache_request(request: HostRouteRequest) -> HostRouteRequest:
    normalized = normalize_host_route_request(request)
    if not normalized.host or not normalized.host_session_id:
        raise ValueError("route continuity requires host and host_session_id")
    return normalized


def _namespace_digest(ws: WorkspacePaths, request: HostRouteRequest) -> str:
    return hash_json(
        {
            "schema_version": HOST_ROUTE_MAPPING_SCHEMA_VERSION,
            "workspace_identity": workspace_identity(ws),
            "host": _nfc(request.host),
            "host_session_id": _nfc(request.host_session_id),
        }
    )


def _continuity_fingerprint(ws: WorkspacePaths, request: HostRouteRequest) -> str:
    return hash_json(
        {
            "workspace_identity": workspace_identity(ws),
            "host": _nfc(request.host),
            "host_session_id": _nfc(request.host_session_id),
            "project_root": _path_identity(request.project_root),
            "repo_id": _nfc(request.repo_id),
            "branch": _nfc(request.branch),
            "explicit_topic_ids": [_nfc(item) for item in request.explicit_topic_ids],
            "explicit_session_ids": [
                _nfc(item) for item in request.explicit_session_ids
            ],
            "exact_refs": [_nfc(item) for item in request.exact_refs],
            "pinned_session_id": _nfc(request.pinned_session_id),
            "routing_mode": request.routing_mode,
        }
    )


def _mapping_path(ws: WorkspacePaths, namespace: str) -> Path:
    if not is_sha256(namespace):
        raise ValueError("host route namespace is not a SHA-256 digest")
    workspace_root = ws.root.resolve(strict=False)
    runtime_root = (ws.root / "runtime").resolve(strict=False)
    if not runtime_root.is_relative_to(workspace_root):
        raise ValueError("AITP runtime root escapes the workspace")
    root = (runtime_root / "host_routes").resolve(strict=False)
    if not root.is_relative_to(runtime_root):
        raise ValueError("host route runtime root escapes AITP runtime")
    path = (root / namespace[:2] / f"{namespace}.json").resolve(strict=False)
    if not path.is_relative_to(root):
        raise ValueError("host route mapping path escapes AITP runtime")
    return path


def _mapping_index_is_current(ws: WorkspacePaths, mapping: HostRouteMapping) -> bool:
    query_session = QuerySnapshotSession()
    result = query_records(
        ws,
        ResearchQuery(
            exact_refs=mapping.selected_exact_refs,
            limit=len(mapping.selected_exact_refs),
            verification_mode="strong",
            exact_only=True,
        ),
        query_session=query_session,
    )
    snapshot = query_session.snapshot
    return bool(
        snapshot is not None
        and result.index_status == "fresh"
        and result.coverage.scope_fresh
        and result.coverage.scope_content_verified
        and result.coverage.malformed_count == 0
        and not result.coverage.read_errors
        and not result.truncated
        and not result.excluded_candidates
        and len(result.items) == len(mapping.selected_exact_refs)
        and snapshot.manifest.generation == mapping.index_generation
        and snapshot.manifest.canonical_watermark == mapping.canonical_watermark
    )


def _verify_exact_refs(ws, request, refs) -> tuple[str, ...]:
    repository = RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="tool",
            actor_id="host-route-cache-read",
            host=request.host,
        ),
    )
    errors = []
    records = {}
    for ref in refs:
        result = repository.read(ref)
        if result.status != "found" or result.record is None:
            errors.append(f"{ref}: {result.status}")
        else:
            records[ref] = result.record
    session = records.get(next((ref for ref in refs if ref.startswith("session:")), ""))
    topic_ref = next((ref for ref in refs if ref.startswith("topic:")), "")
    if session is not None and topic_ref:
        topic_id = topic_ref.partition(":")[2]
        if str(getattr(session, "topic_id", "") or "") != topic_id:
            errors.append("cached session topic binding changed")
    return tuple(errors)


def _mapping_from_payload(payload: object) -> HostRouteMapping:
    if not isinstance(payload, dict):
        raise ValueError("host route mapping payload must be an object")
    expected = set(HostRouteMapping.__dataclass_fields__)
    if set(payload) != expected:
        raise ValueError("host route mapping payload fields are invalid")
    values = dict(payload)
    refs = values.get("selected_exact_refs")
    if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
        raise ValueError("selected_exact_refs must be a string list")
    values["selected_exact_refs"] = tuple(refs)
    return HostRouteMapping(**values)


def _integrity_hash(payload: dict) -> str:
    sealed = dict(payload)
    sealed.pop("integrity_hash", None)
    return hash_json(sealed)


def _serialize(payload: dict) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    ) + "\n"


def _parse_timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("host route mapping timestamp is missing")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("host route mapping timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _path_identity(value: str) -> str:
    if not value:
        return ""
    return _nfc(os.path.normcase(os.path.normpath(value)))


def _nfc(value: str) -> str:
    return unicodedata.normalize("NFC", str(value or ""))


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
