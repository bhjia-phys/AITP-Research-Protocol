"""Review-gated migration candidates for legacy derivation text artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from brain.v5.derivation_contracts import (
    LegacyDerivationCandidate,
    ReviewedDerivationMigrationApply,
)
from brain.v5.derivation_models import DerivationChainRecord
from brain.v5.derivations import record_derivation_chain
from brain.v5.human_approval import checkpoint_can_authorize_trust
from brain.v5.models import HumanCheckpointRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version, pin_current_record
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository
from brain.v5.workspace import get_claim


_UNRESOLVED_MAPPINGS = (
    "step_segmentation",
    "step_dependency_edges",
    "source_anchor_mapping",
    "assumption_and_convention_mapping",
    "local_check_mapping",
)


def derivation_migration_apply_payload_hash(
    candidate: LegacyDerivationCandidate,
    resolved_mappings: tuple[str, ...] | list[str],
    chain: DerivationChainRecord,
) -> str:
    """Bind approval to the exact candidate, mappings, and mapped chain."""

    payload = {
        "candidate": asdict(candidate),
        "resolved_mappings": list(resolved_mappings),
        "chain": asdict(chain),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def migrate_legacy_derivation_candidates(
    ws: WorkspacePaths,
    legacy_topic_root: str | Path,
    *,
    topic_id: str,
    claim_id: str,
    apply_request: ReviewedDerivationMigrationApply | None = None,
    actor: RecordActor | None = None,
) -> dict[str, Any]:
    """Build a lossless dry-run, or apply one exact reviewed draft chain."""

    claim = get_claim(ws, claim_id)
    if claim.topic_id != topic_id:
        raise ValueError("legacy derivation target claim belongs to another topic")
    root = Path(legacy_topic_root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("legacy derivation root must be a directory")
    candidates = _discover_candidates(root, topic_id=topic_id, claim_id=claim_id)
    base = {
        "ok": True,
        "kind": "legacy_derivation_migration",
        "legacy_topic_root": str(root),
        "topic_id": topic_id,
        "claim_id": claim_id,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "truth_source": "legacy_source_bytes",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_claim_trust": False,
    }
    if apply_request is None:
        return {**base, "applied": False, "idempotent": False}
    if actor is None:
        raise ValueError("reviewed legacy derivation apply requires an explicit actor")
    current = _candidate_for_apply(candidates, apply_request)
    _validate_apply_request(
        ws,
        current,
        apply_request,
        topic_id=topic_id,
        claim_id=claim_id,
    )
    chain = _materialize_chain(current, apply_request)
    repository = RecordRepository(ws, actor=actor)
    existing = repository.read(f"derivation_chain:{chain.chain_id}")
    if existing.status == "found" and isinstance(existing.record, DerivationChainRecord):
        if existing.record == chain:
            pin = pin_current_record(ws, f"derivation_chain:{chain.chain_id}")
            return {
                **base,
                "applied": True,
                "idempotent": True,
                "chain_ref": asdict(pin),
            }
        raise ValueError("legacy derivation chain id already exists with different content")
    result = record_derivation_chain(ws, chain, actor=actor)
    pin = PinnedRecordRef(result.record_ref, result.content_hash, result.revision)
    return {
        **base,
        "applied": True,
        "idempotent": False,
        "chain_ref": asdict(pin),
    }


def _discover_candidates(
    root: Path,
    *,
    topic_id: str,
    claim_id: str,
) -> list[LegacyDerivationCandidate]:
    paths: set[Path] = set()
    anchor = root / "L1" / "derivation_anchor_map.md"
    if anchor.is_file():
        paths.add(anchor)
    for relative in ("L3/derive", "L3/trace-derivation"):
        directory = root / relative
        if directory.is_dir():
            paths.update(
                path
                for path in directory.rglob("*.md")
                if path.name.lower() not in {"readme.md", "index.md"}
            )
    runs = root / "L3" / "runs"
    if runs.is_dir():
        paths.update(runs.glob("*/derivation_records.md"))
    candidates = [
        _candidate(root, path, topic_id=topic_id, claim_id=claim_id)
        for path in sorted(paths, key=lambda item: item.as_posix())
    ]
    return candidates


def _candidate(
    root: Path,
    path: Path,
    *,
    topic_id: str,
    claim_id: str,
) -> LegacyDerivationCandidate:
    resolved = path.resolve(strict=True)
    relative = _safe_relative(root, resolved)
    raw = resolved.read_bytes()
    source_hash = hashlib.sha256(raw).hexdigest()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"legacy derivation source is not UTF-8: {relative}") from exc
    kind = "anchor_map" if relative == "L1/derivation_anchor_map.md" else "derivation_text"
    identity = f"{topic_id}:{claim_id}:{relative}:{source_hash}"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    chain_slug = hashlib.sha256(f"{topic_id}:{relative}".encode("utf-8")).hexdigest()[:20]
    return LegacyDerivationCandidate(
        candidate_id=f"legacy-derivation-{digest}",
        source_relative_path=relative,
        source_sha256=source_hash,
        original_text=text,
        candidate_kind=kind,
        proposed_chain_id=f"legacy-derivation-chain-{chain_slug}",
        proposed_target=f"Review and structurally map legacy derivation text from {relative}.",
        unresolved_mappings=_UNRESOLVED_MAPPINGS,
    )


def _candidate_for_apply(
    candidates: list[LegacyDerivationCandidate],
    request: ReviewedDerivationMigrationApply,
) -> LegacyDerivationCandidate:
    for candidate in candidates:
        if candidate.source_relative_path == request.source_relative_path:
            if candidate.source_sha256 != request.expected_source_sha256:
                raise ValueError("legacy derivation source hash changed after review")
            if candidate.candidate_id != request.candidate_id:
                raise ValueError("legacy derivation candidate identity changed after review")
            return candidate
    raise ValueError("reviewed legacy derivation source path is no longer available")


def _validate_apply_request(
    ws: WorkspacePaths,
    candidate: LegacyDerivationCandidate,
    request: ReviewedDerivationMigrationApply,
    *,
    topic_id: str,
    claim_id: str,
) -> None:
    if candidate.candidate_kind != "derivation_text":
        raise ValueError("anchor maps are support inputs and cannot become derivation chains directly")
    if set(request.resolved_mappings) != set(candidate.unresolved_mappings):
        raise ValueError("reviewed apply must resolve every declared legacy mapping")
    chain = request.chain
    if chain.chain_id != candidate.proposed_chain_id:
        raise ValueError("legacy derivation mapped chain must use the proposed chain id")
    expected_payload_hash = derivation_migration_apply_payload_hash(
        candidate,
        request.resolved_mappings,
        chain,
    )
    checkpoint_pin = request.checkpoint_ref
    if pin_current_record(ws, checkpoint_pin.record_ref) != checkpoint_pin:
        raise ValueError("legacy derivation apply checkpoint is stale")
    checkpoint = get_record_version(ws, checkpoint_pin).record
    if (
        not isinstance(checkpoint, HumanCheckpointRecord)
        or checkpoint.topic_id != topic_id
        or checkpoint.claim_id != claim_id
        or checkpoint.action != "apply_derivation_migration"
        or checkpoint.decision != "approve"
        or checkpoint.payload_hash != expected_payload_hash
        or not {f"topic:{topic_id}", f"claim:{claim_id}"} <= set(checkpoint.target_scope_refs)
        or not checkpoint_can_authorize_trust(checkpoint)
    ):
        raise ValueError("legacy derivation apply payload does not match the reviewed checkpoint")
    if chain.topic_id != topic_id or chain.claim_id != claim_id:
        raise ValueError("legacy derivation mapped chain has foreign scope")
    if chain.status != "draft" or chain.ordered_step_refs or chain.imported_chain_bindings:
        raise ValueError("legacy derivation apply may only create an unmapped draft chain")


def _materialize_chain(
    candidate: LegacyDerivationCandidate,
    request: ReviewedDerivationMigrationApply,
) -> DerivationChainRecord:
    return replace(
        request.chain,
        migration_provenance={
            "candidate_id": candidate.candidate_id,
            "source_relative_path": candidate.source_relative_path,
            "source_sha256": candidate.source_sha256,
            "original_text": candidate.original_text,
            "candidate_kind": candidate.candidate_kind,
            "resolved_mappings": list(request.resolved_mappings),
            "checkpoint_ref": asdict(request.checkpoint_ref),
            "trust_effect": "none",
        },
    )


def _safe_relative(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError("legacy derivation source escapes the reviewed topic root") from exc
