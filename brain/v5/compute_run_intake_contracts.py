"""Trust-neutral contracts for generic compute-run collector intake."""

from __future__ import annotations

import copy
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class ComputeRunIntakeRequest:
    """Detached exact manifest supplied by a local or remote adapter."""

    manifest: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.manifest, Mapping):
            raise ValueError("compute run intake manifest must be a mapping")
        object.__setattr__(self, "manifest", copy.deepcopy(dict(self.manifest)))


@dataclass(frozen=True)
class ComputeRunIntakeReport:
    """Reviewable prefill candidates; never a canonical or scientific write."""

    status: str
    coverage: str
    source_uri: str
    checked_fields: tuple[str, ...] = ()
    missing_fields: tuple[str, ...] = ()
    invalid_fields: tuple[str, ...] = ()
    redacted_fields: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    candidates: dict[str, Any] = field(default_factory=dict)
    writes_records: bool = False
    orientation_only: bool = True
    can_create_scientific_evidence: bool = False
    can_create_validation: bool = False
    can_accept_baseline: bool = False
    can_update_claim_trust: bool = False

    def __post_init__(self) -> None:
        require_trust_neutral_intake(self)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )


def require_trust_neutral_intake(report: ComputeRunIntakeReport) -> None:
    """Reject any future change that turns collector output into authority."""

    if report.writes_records:
        raise ValueError("compute run intake must not write records")
    if not report.orientation_only:
        raise ValueError("compute run intake must remain orientation-only")
    if any(
        (
            report.can_create_scientific_evidence,
            report.can_create_validation,
            report.can_accept_baseline,
            report.can_update_claim_trust,
        )
    ):
        raise ValueError("compute run intake must remain trust-neutral")
    forbidden = {"evidence", "validation_result", "execution_baseline", "claim"}
    overlap = forbidden.intersection(report.candidates)
    if overlap:
        raise ValueError(f"compute run intake contains forbidden candidates: {sorted(overlap)}")
