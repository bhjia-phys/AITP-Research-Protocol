"""Normalization and identity for bounded host route requests."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json

from brain.v5.host_route_contracts import (
    HOST_ROUTE_MODES,
    HOST_ROUTE_REQUEST_SCHEMA_VERSION,
    HostRouteRequest,
)
from brain.v5.host_route_normalization import (
    bounded_text_tuple,
    clean_text,
    freeze_json_object,
    json_ready,
    record_id,
    record_id_tuple,
    typed_ref_tuple,
)


_MAX_REQUEST_SUMMARY_BYTES = 4096
_MAX_PATH_BYTES = 4096
_MAX_VISIBLE_FILES = 32
_MAX_EXPLICIT_IDS = 8
_MAX_EXACT_REFS = 32
_MAX_SEMANTIC_ASSESSMENT_BYTES = 8192


def normalize_host_route_request(request: HostRouteRequest) -> HostRouteRequest:
    """Canonicalize bounded route inputs without workspace access."""

    if not isinstance(request, HostRouteRequest):
        raise TypeError("request must be a HostRouteRequest")
    if request.schema_version != HOST_ROUTE_REQUEST_SCHEMA_VERSION:
        raise ValueError("unsupported host route request schema")
    mode = clean_text(request.routing_mode, "routing_mode", required=True).casefold()
    if mode not in HOST_ROUTE_MODES:
        raise ValueError(f"unsupported routing mode: {mode}")
    pin = record_id(request.pinned_session_id, "pinned_session_id")
    if mode == "dynamic" and pin:
        raise ValueError("dynamic routing cannot include a pinned session")
    if mode in {"pinned", "pinned_compat"} and not pin:
        raise ValueError(f"{mode} routing requires a pinned session")

    host = clean_text(request.host, "host").casefold()
    host_session_id = clean_text(
        request.host_session_id, "host_session_id", max_bytes=512
    )
    if host_session_id and not host:
        raise ValueError("host_session_id requires host")
    return replace(
        request,
        request_summary=clean_text(
            request.request_summary,
            "request_summary",
            max_bytes=_MAX_REQUEST_SUMMARY_BYTES,
        ),
        host=host,
        host_session_id=host_session_id,
        project_root=clean_text(
            request.project_root, "project_root", max_bytes=_MAX_PATH_BYTES
        ),
        current_path=clean_text(
            request.current_path, "current_path", max_bytes=_MAX_PATH_BYTES
        ),
        repo_id=clean_text(request.repo_id, "repo_id", max_bytes=512),
        branch=clean_text(request.branch, "branch", max_bytes=512),
        visible_files=bounded_text_tuple(
            request.visible_files,
            "visible_files",
            max_items=_MAX_VISIBLE_FILES,
            max_item_bytes=_MAX_PATH_BYTES,
        ),
        explicit_topic_ids=record_id_tuple(
            request.explicit_topic_ids,
            "explicit_topic_ids",
            max_items=_MAX_EXPLICIT_IDS,
        ),
        explicit_session_ids=record_id_tuple(
            request.explicit_session_ids,
            "explicit_session_ids",
            max_items=_MAX_EXPLICIT_IDS,
        ),
        exact_refs=typed_ref_tuple(
            request.exact_refs, "exact_refs", max_items=_MAX_EXACT_REFS
        ),
        pinned_session_id=pin,
        routing_mode=mode,
        semantic_assessment=freeze_json_object(
            request.semantic_assessment,
            "semantic_assessment",
            max_bytes=_MAX_SEMANTIC_ASSESSMENT_BYTES,
        ),
        schema_version=HOST_ROUTE_REQUEST_SCHEMA_VERSION,
    )


def host_route_request_fingerprint(request: HostRouteRequest) -> str:
    normalized = normalize_host_route_request(request)
    payload = {
        "schema_version": normalized.schema_version,
        "request_summary": normalized.request_summary,
        "host": normalized.host,
        "host_session_id": normalized.host_session_id,
        "project_root": normalized.project_root,
        "current_path": normalized.current_path,
        "repo_id": normalized.repo_id,
        "branch": normalized.branch,
        "visible_files": list(normalized.visible_files),
        "explicit_topic_ids": list(normalized.explicit_topic_ids),
        "explicit_session_ids": list(normalized.explicit_session_ids),
        "exact_refs": list(normalized.exact_refs),
        "pinned_session_id": normalized.pinned_session_id,
        "routing_mode": normalized.routing_mode,
        "semantic_assessment": json_ready(normalized.semantic_assessment),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
