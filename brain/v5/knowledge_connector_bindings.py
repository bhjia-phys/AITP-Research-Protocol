"""Workspace-local bindings for external knowledge connectors."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from brain.v5.knowledge_connectors import builtin_knowledge_connectors
from brain.v5.markdown import write_text_atomic
from brain.v5.paths import WorkspacePaths

_BINDINGS_REL = Path("knowledge_connectors") / "bindings.json"


def list_knowledge_connector_bindings(
    ws: WorkspacePaths,
    *,
    connector_id: str = "",
    include_connector_catalog: bool = False,
    state_effect: str = "read_only",
) -> dict[str, Any]:
    """Return configured connector bindings without reading any corpus content."""

    connectors = builtin_knowledge_connectors()
    bindings = _load_bindings(ws)
    selected = [
        binding
        for binding in bindings
        if not connector_id or binding.get("connector_id") == connector_id
    ]
    payload: dict[str, Any] = {
        "ok": True,
        "kind": "knowledge_connector_binding_registry",
        "truth_source": "workspace_connector_binding_config",
        "state_effect": state_effect,
        "workspace_config_path": str(_bindings_path(ws)),
        "connector_filter": connector_id,
        "known_connector_ids": list(connectors.keys()),
        "binding_count": len(selected),
        "bindings": selected,
        "missing_connector_ids": [
            binding.get("connector_id", "")
            for binding in selected
            if binding.get("connector_id") not in connectors
        ],
        "required_followup_for_use": [
            "retrieved connector content is orientation only",
            "record source_asset and reference_location before using a source",
            "create evidence or validation records only from source-backed claim-scoped material",
        ],
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "can_create_evidence": False,
    }
    if include_connector_catalog:
        payload["connectors"] = [
            {
                "connector_id": connector.connector_id,
                "display_name": connector.display_name,
                "connector_kind": connector.connector_kind,
                "configured_binding_count": _binding_count(bindings, connector.connector_id),
            }
            for connector in connectors.values()
        ]
    return payload


def bind_knowledge_connector(
    ws: WorkspacePaths,
    *,
    connector_id: str,
    root_uri: str,
    corpus_id: str = "",
    label: str = "",
    file_globs: list[str] | None = None,
    domain_hints: list[str] | None = None,
    topic_hints: list[str] | None = None,
    priority: str = "medium",
    status: str = "active",
    notes: str = "",
) -> dict[str, Any]:
    """Persist one workspace-local connector binding as configuration metadata."""

    if connector_id not in builtin_knowledge_connectors():
        raise ValueError(f"unknown connector_id: {connector_id}")
    clean_root = str(root_uri or "").strip()
    if not clean_root:
        raise ValueError("root_uri is required")
    bindings = _load_bindings(ws)
    binding = _binding_payload(
        connector_id=connector_id,
        root_uri=clean_root,
        corpus_id=corpus_id,
        label=label,
        file_globs=file_globs or [],
        domain_hints=domain_hints or [],
        topic_hints=topic_hints or [],
        priority=priority,
        status=status,
        notes=notes,
    )
    remaining = [item for item in bindings if item.get("binding_id") != binding["binding_id"]]
    remaining.append(binding)
    _write_bindings(ws, sorted(remaining, key=lambda item: (item.get("connector_id", ""), item.get("binding_id", ""))))
    return list_knowledge_connector_bindings(
        ws,
        connector_id=connector_id,
        include_connector_catalog=True,
        state_effect="knowledge_connector_binding_config_write",
    )


def attach_configured_bindings(ws: WorkspacePaths, connectors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Annotate connector payloads with matching workspace bindings."""

    bindings = _load_bindings(ws)
    by_connector: dict[str, list[dict[str, Any]]] = {}
    for binding in bindings:
        if binding.get("status") != "active":
            continue
        by_connector.setdefault(str(binding.get("connector_id") or ""), []).append(binding)
    enriched: list[dict[str, Any]] = []
    for connector in connectors:
        copied = dict(connector)
        configured = by_connector.get(str(copied.get("connector_id") or ""), [])
        copied["configured_bindings"] = configured
        copied["configured_binding_count"] = len(configured)
        copied["binding_status"] = "configured" if configured else "unconfigured"
        enriched.append(copied)
    return enriched


def _bindings_path(ws: WorkspacePaths) -> Path:
    return ws.root / _BINDINGS_REL


def _load_bindings(ws: WorkspacePaths) -> list[dict[str, Any]]:
    path = _bindings_path(ws)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    bindings = data.get("bindings", []) if isinstance(data, dict) else []
    return [dict(item) for item in bindings if isinstance(item, dict)]


def _write_bindings(ws: WorkspacePaths, bindings: list[dict[str, Any]]) -> None:
    payload = {
        "kind": "knowledge_connector_binding_config",
        "truth_source": "workspace_connector_binding_config",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "bindings": bindings,
    }
    write_text_atomic(_bindings_path(ws), json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2) + "\n")


def _binding_payload(
    *,
    connector_id: str,
    root_uri: str,
    corpus_id: str,
    label: str,
    file_globs: list[str],
    domain_hints: list[str],
    topic_hints: list[str],
    priority: str,
    status: str,
    notes: str,
) -> dict[str, Any]:
    binding_id = "knowledge-connector-binding-" + hashlib.sha1(
        f"{connector_id}:{root_uri}:{corpus_id}".encode("utf-8")
    ).hexdigest()[:12]
    return {
        "binding_id": binding_id,
        "connector_id": connector_id,
        "label": label or connector_id,
        "root_uri": root_uri,
        "corpus_id": corpus_id,
        "file_globs": list(file_globs),
        "domain_hints": list(domain_hints),
        "topic_hints": list(topic_hints),
        "priority": priority or "medium",
        "status": status or "active",
        "notes": notes,
        "retrieval_boundary": "binding only; corpus content remains orientation until source-backed typed records exist",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_claim_trust": False,
    }


def _binding_count(bindings: list[dict[str, Any]], connector_id: str) -> int:
    return sum(1 for binding in bindings if binding.get("connector_id") == connector_id)
