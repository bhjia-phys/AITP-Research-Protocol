from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


_BRAIN_BACKEND_ID = "backend:theoretical-physics-brain"
_TPKN_BACKEND_ID = "backend:theoretical-physics-knowledge-network"


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _pair_paths(kernel_root: Path) -> dict[str, Path]:
    return {
        "pair_contract": kernel_root / "canonical" / "backends" / "THEORETICAL_PHYSICS_PAIRED_BACKEND_CONTRACT.md",
        "pairing_note": kernel_root / "canonical" / "backends" / "THEORETICAL_PHYSICS_BACKEND_PAIRING.md",
        "maintenance_protocol": kernel_root / "canonical" / "L2_PAIRED_BACKEND_MAINTENANCE_PROTOCOL.md",
        "consultation_protocol": kernel_root / "L2_CONSULTATION_PROTOCOL.md",
    }


def _pair_card_details(self, backend_id: str) -> dict[str, Any]:
    card_path, card_payload = self._load_backend_card(backend_id)
    payload = card_payload or {}
    root_values = [str(value).strip() for value in (payload.get("root_paths") or []) if str(value).strip()]
    has_configured_root = any(not value.startswith("__") for value in root_values)
    return {
        "backend_id": backend_id,
        "title": str(payload.get("title") or backend_id),
        "backend_type": str(payload.get("backend_type") or ""),
        "card_status": "present" if payload else "missing",
        "card_path": self._relativize(card_path) if card_path else None,
        "root_status": "configured" if has_configured_root else "unconfigured",
    }


def _semantic_separation(paths: dict[str, Path], promotion_gate_path: Path | None) -> dict[str, dict[str, Any]]:
    return {
        "consultation": {
            "kind": "consultation",
            "protocol_path": str(paths["consultation_protocol"]) if paths["consultation_protocol"].exists() else "",
            "distinct_from_sync": True,
            "distinct_from_promotion": True,
        },
        "promotion": {
            "kind": "promotion",
            "protocol_path": str(promotion_gate_path) if promotion_gate_path and promotion_gate_path.exists() else "",
            "distinct_from_sync": True,
            "distinct_from_consultation": True,
        },
        "sync": {
            "kind": "paired_backend_maintenance",
            "protocol_path": str(paths["maintenance_protocol"]) if paths["maintenance_protocol"].exists() else "",
            "uses_maintenance_protocol": paths["maintenance_protocol"].exists(),
        },
    }


def _paired_backend_runtime_rows(topic_state: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in (topic_state or {}).get("backend_bridges") or []:
        if not isinstance(row, dict):
            continue
        backend_id = str(row.get("backend_id") or "").strip()
        if backend_id:
            rows[backend_id] = row
    return rows


def _pair_status(runtime_rows: dict[str, dict[str, Any]], cards_present: bool) -> tuple[str, str, str]:
    has_brain = _BRAIN_BACKEND_ID in runtime_rows
    has_tpkn = _TPKN_BACKEND_ID in runtime_rows
    if not cards_present:
        return "missing_pair_contract", "not_applicable", "blocking"
    if has_brain and has_tpkn:
        return "paired_active", "audit_required", "unassessed"
    if has_brain or has_tpkn:
        return "partial_pair", "blocking_backend_debt", "blocking"
    return "declared_pair_untracked", "not_audited", "untracked"


def _pair_summary(pairing_status: str, drift_status: str) -> str:
    if pairing_status == "paired_active":
        return "The theoretical-physics pair is active for this topic, but a bounded drift audit is still required before claiming full alignment."
    if pairing_status == "partial_pair":
        return "Only one side of the theoretical-physics pair is active for this topic; treat the missing side as blocking backend debt."
    if pairing_status == "declared_pair_untracked":
        return "The theoretical-physics pair is declared in backend cards, but this topic has not yet materialized both pair members in runtime state."
    return f"Paired-backend audit is unavailable because the pair contract is incomplete ({drift_status})."


def paired_backend_audit_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Paired backend audit",
        "",
        f"- Topic slug: `{payload['topic_slug']}`",
        f"- Pairing status: `{payload['pairing_status']}`",
        f"- Drift status: `{payload['drift_status']}`",
        f"- Backend debt status: `{payload['backend_debt_status']}`",
        f"- Operator-primary backend: `{payload['operator_primary_backend_id']}`",
        f"- Machine-primary backend: `{payload['machine_primary_backend_id']}`",
        "",
        payload["summary"],
        "",
        "## Pair members",
        "",
    ]
    for row in payload["paired_backends"]:
        lines.extend(
            [
                f"- `{row['backend_id']}` role=`{row['pairing_role']}` card_status=`{row['card_status']}` root_status=`{row['root_status']}`",
                f"  card_path=`{row.get('card_path') or '(missing)'}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Semantic separation",
            "",
            f"- consultation distinct_from_sync=`{str(payload['semantic_separation']['consultation']['distinct_from_sync']).lower()}`",
            f"- promotion distinct_from_sync=`{str(payload['semantic_separation']['promotion']['distinct_from_sync']).lower()}`",
            f"- sync uses_maintenance_protocol=`{str(payload['semantic_separation']['sync']['uses_maintenance_protocol']).lower()}`",
            "",
            "## Contracts",
            "",
            f"- Pair contract: `{payload['pair_contract_path'] or '(missing)'}`",
            f"- Pairing note: `{payload['pairing_note_path'] or '(missing)'}`",
            f"- Maintenance protocol: `{payload['maintenance_protocol_path'] or '(missing)'}`",
            "",
        ]
    )
    return "\n".join(lines)


def build_paired_backend_audit_payload(
    self,
    *,
    topic_slug: str,
    topic_state: dict[str, Any] | None,
    backend_id: str | None,
    updated_by: str,
) -> dict[str, Any]:
    paths = _pair_paths(self.kernel_root)
    runtime_rows = _paired_backend_runtime_rows(topic_state)
    brain = _pair_card_details(self, _BRAIN_BACKEND_ID)
    tpkn = _pair_card_details(self, _TPKN_BACKEND_ID)
    cards_present = all(row["card_status"] == "present" for row in (brain, tpkn))
    pairing_status, drift_status, backend_debt_status = _pair_status(runtime_rows, cards_present)
    promotion_gate_path = self._promotion_gate_paths(topic_slug)["json"]
    semantic_separation = _semantic_separation(paths, promotion_gate_path)

    return {
        "topic_slug": topic_slug,
        "backend_id": backend_id or _TPKN_BACKEND_ID,
        "updated_at": _now_iso(),
        "updated_by": updated_by,
        "operator_primary_backend_id": _BRAIN_BACKEND_ID,
        "machine_primary_backend_id": _TPKN_BACKEND_ID,
        "pairing_status": pairing_status,
        "drift_status": drift_status,
        "backend_debt_status": backend_debt_status,
        "pair_contract_path": str(paths["pair_contract"]) if paths["pair_contract"].exists() else "",
        "pairing_note_path": str(paths["pairing_note"]) if paths["pairing_note"].exists() else "",
        "maintenance_protocol_path": str(paths["maintenance_protocol"]) if paths["maintenance_protocol"].exists() else "",
        "paired_backends": [
            {**brain, "pairing_role": "operator_primary"},
            {**tpkn, "pairing_role": "machine_primary"},
        ],
        "semantic_separation": semantic_separation,
        "summary": _pair_summary(pairing_status, drift_status),
    }


def enrich_backend_bridge_rows(
    self,
    *,
    topic_slug: str,
    topic_state: dict[str, Any] | None,
    backend_bridges: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    payload = build_paired_backend_audit_payload(
        self,
        topic_slug=topic_slug,
        topic_state=topic_state,
        backend_id=_TPKN_BACKEND_ID,
        updated_by="runtime-bundle",
    )
    pair_meta = {
        _BRAIN_BACKEND_ID: ("operator_primary", _TPKN_BACKEND_ID),
        _TPKN_BACKEND_ID: ("machine_primary", _BRAIN_BACKEND_ID),
    }
    enriched: list[dict[str, Any]] = []
    for row in backend_bridges:
        backend_id = str(row.get("backend_id") or "")
        pairing_role, paired_backend_id = pair_meta.get(backend_id, ("not_paired", None))
        enriched.append(
            {
                **row,
                "pairing_role": pairing_role,
                "paired_backend_id": paired_backend_id,
                "pairing_status": payload["pairing_status"] if paired_backend_id else "not_paired",
                "drift_status": payload["drift_status"] if paired_backend_id else "not_applicable",
                "backend_debt_status": payload["backend_debt_status"] if paired_backend_id else "not_applicable",
                "maintenance_protocol_path": self._relativize(Path(payload["maintenance_protocol_path"])) if payload["maintenance_protocol_path"] else None,
                "semantic_separation": payload["semantic_separation"] if paired_backend_id else {
                    "consultation": {"distinct_from_sync": True},
                    "promotion": {"distinct_from_sync": True},
                    "sync": {"uses_maintenance_protocol": False},
                },
            }
        )
    return enriched


def build_runtime_backend_bridges(
    self,
    *,
    topic_slug: str,
    topic_state: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    backend_bridges: list[dict[str, Any]] = []
    for row in (topic_state or {}).get("backend_bridges") or []:
        if not isinstance(row, dict):
            continue
        backend_bridges.append(
            {
                "backend_id": str(row.get("backend_id") or "").strip() or "(missing)",
                "title": str(row.get("title") or row.get("backend_id") or "").strip() or "(missing)",
                "backend_type": str(row.get("backend_type") or "").strip() or "(missing)",
                "status": str(row.get("status") or "").strip() or "(missing)",
                "card_status": str(row.get("card_status") or "").strip() or "(missing)",
                "card_path": str(row.get("card_path") or "").strip() or None,
                "backend_root": str(row.get("backend_root") or "").strip() or None,
                "artifact_kinds": self._dedupe_strings(list(row.get("artifact_kinds") or [])),
                "canonical_targets": self._dedupe_strings(list(row.get("canonical_targets") or [])),
                "l0_registration_script": str(row.get("l0_registration_script") or "").strip() or None,
                "source_count": int(row.get("source_count") or 0),
            }
        )
    return enrich_backend_bridge_rows(
        self,
        topic_slug=topic_slug,
        topic_state=topic_state,
        backend_bridges=backend_bridges,
    )


def paired_backend_audit(self, *, topic_slug: str, backend_id: str | None = None, updated_by: str = "aitp-cli") -> dict[str, Any]:
    runtime_root = self._ensure_runtime_root(topic_slug)
    topic_state = _read_json(runtime_root / "topic_state.json") or {}
    payload = build_paired_backend_audit_payload(
        self,
        topic_slug=topic_slug,
        topic_state=topic_state,
        backend_id=backend_id,
        updated_by=updated_by,
    )
    json_path = runtime_root / "paired_backend_alignment.audit.json"
    note_path = runtime_root / "paired_backend_alignment.audit.md"
    _write_json(json_path, payload)
    _write_text(note_path, paired_backend_audit_markdown(payload))
    return {
        **payload,
        "audit_path": str(json_path),
        "audit_note_path": str(note_path),
    }
