"""Derived contracts for formal derivation validation and status."""

from __future__ import annotations

from dataclasses import dataclass

from brain.v5.derivation_models import DerivationChainRecord
from brain.v5.pinned_record_refs import PinnedRecordRef


@dataclass(frozen=True)
class DerivationDagValidation:
    chain_id: str
    valid: bool
    ordered_step_ids: tuple[str, ...]
    open_gaps: tuple[str, ...]
    unresolved_conditions: tuple[str, ...]
    checked_refs: tuple[str, ...]
    imported_chain_refs: tuple[str, ...]
    can_update_claim_trust: bool = False


@dataclass(frozen=True)
class DerivationStatusProjection:
    chain_ref: str
    structurally_closed: bool
    source_complete: bool
    reviewed: bool
    validated: bool
    active_review_ref: str = ""
    blocking_reasons: tuple[str, ...] = ()
    can_update_claim_trust: bool = False


@dataclass(frozen=True)
class LegacyDerivationCandidate:
    candidate_id: str
    source_relative_path: str
    source_sha256: str
    original_text: str
    candidate_kind: str
    proposed_chain_id: str
    proposed_target: str
    unresolved_mappings: tuple[str, ...]
    can_apply: bool = False
    can_update_claim_trust: bool = False


@dataclass(frozen=True)
class ReviewedDerivationMigrationApply:
    candidate_id: str
    source_relative_path: str
    expected_source_sha256: str
    checkpoint_ref: PinnedRecordRef
    resolved_mappings: tuple[str, ...]
    chain: DerivationChainRecord
