from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .l2_graph import materialize_canonical_index, read_jsonl, write_jsonl


JONES_TOPIC_SLUG = "jones-von-neumann-algebras"
JONES_RUN_ID = "2026-04-12-jones-proof-engineering-bootstrap"
JONES_PROOF_FRAGMENT_ID = "proof_fragment:jones-codrestrict-comp-subtype-construction-recipe"

_POSTMORTEM_REF = (
    ".planning/phases/165-real-topic-l0-to-l2-e2e-validation/"
    "evidence/jones-von-neumann-algebras/POSTMORTEM.md"
)
_ISSUE_LEDGER_REF = (
    ".planning/phases/165-real-topic-l0-to-l2-e2e-validation/165-ISSUE-LEDGER.md"
)

JONES_STRATEGY_MEMORY_SEEDS: list[dict[str, Any]] = [
    {
        "strategy_id": "strat-jones-codrestrict-comp-subtype",
        "strategy_type": "proof_engineering",
        "summary": (
            "Build the range-facing map in two steps: first `LinearMap.codRestrict` or "
            "`ContinuousLinearMap.codRestrict` into the proved range, then compose with "
            "`Submodule.subtype` instead of trying to force a direct subtype-to-range map."
        ),
        "input_context": {
            "proof_family": "jones-section2-polar-support",
            "surface": "range-facing linear map construction",
        },
        "outcome": "helpful",
        "confidence": 0.93,
        "reuse_conditions": [
            "the proof already has a witness that the map lands in a target submodule",
            "the local goal is a reusable range-facing linear map or linear equivalence",
        ],
        "do_not_apply_when": [
            "the codomain is not a submodule-backed range target",
            "the local obstacle is theorem shape rather than codomain packaging",
        ],
        "human_note": "This is the primary reusable construction recipe recovered from the Jones E2E run.",
    },
    {
        "strategy_id": "strat-jones-clmap-coefun-linear-map-sub",
        "strategy_type": "api_workaround",
        "summary": (
            "When `ContinuousLinearMap` coercions hide the `LinearMap` structure and "
            "`rw [ContinuousLinearMap.map_sub]` stops matching, pull the underlying "
            "`LinearMap.map_sub` fact into a named `have` instead of rewriting directly."
        ),
        "input_context": {
            "proof_family": "jones-section2-polar-support",
            "surface": "continuous-linear-map subtraction rewrites",
        },
        "outcome": "helpful",
        "confidence": 0.88,
        "reuse_conditions": [
            "a ContinuousLinearMap goal fails because CoeFun coercion has already fired",
            "subtraction is easier to expose at the LinearMap layer than at the CLM layer",
        ],
        "do_not_apply_when": [
            "the theorem is already phrased over plain LinearMap",
            "the failure is due to missing simp lemmas rather than coercion shape",
        ],
        "human_note": "Treat CoeFun-triggered rewrite failure as a structure mismatch, not as missing algebra.",
    },
    {
        "strategy_id": "strat-jones-sub-eq-zero-direction",
        "strategy_type": "failure_pattern",
        "summary": (
            "For `sub_eq_zero`, remember the direction: `rw [sub_eq_zero]` rewrites "
            "`a - b = 0` to `a = b`, while `.mpr` is the reliable way to build the subtraction goal from an equality."
        ),
        "input_context": {
            "proof_family": "jones-section2-polar-support",
            "surface": "goal-shape control around subtraction",
        },
        "outcome": "helpful",
        "confidence": 0.9,
        "reuse_conditions": [
            "the local proof moves between equality goals and subtraction-equals-zero goals",
            "a rewrite looks symmetric but Lean needs the constructor direction explicitly",
        ],
        "do_not_apply_when": [
            "the target equality is not actually equivalent to a subtraction-zero form",
            "ring-style normalization is the real blocker",
        ],
        "human_note": "This is a small but frequent Lean proof-direction trap worth keeping explicit.",
    },
    {
        "strategy_id": "strat-jones-starprojection-range-instance",
        "strategy_type": "api_workaround",
        "summary": (
            "If `Submodule.range_starProjection` stalls on instance inference, pass the "
            "submodule parameter explicitly with `(U := ...)` before searching for deeper math reasons."
        ),
        "input_context": {
            "proof_family": "jones-section2-polar-support",
            "surface": "instance inference around starProjection ranges",
        },
        "outcome": "helpful",
        "confidence": 0.84,
        "reuse_conditions": [
            "the target lemma is `Submodule.range_starProjection` or a close relative",
            "Lean reports an instance/inference failure rather than a false statement",
        ],
        "do_not_apply_when": [
            "the failure is a missing hypothesis instead of a missing explicit parameter",
            "the local object is not actually a starProjection-backed range statement",
        ],
        "human_note": "Prefer explicit parameters before inventing new bridging lemmas.",
    },
    {
        "strategy_id": "strat-jones-ker-bridge-positive-part",
        "strategy_type": "proof_engineering",
        "summary": (
            "Use `jonesFiniteCoordinatePolarPositivePart_ker_eq_ker` as the bridge from "
            "`ker |A|` to `ker A` before unpacking kernel membership by hand."
        ),
        "input_context": {
            "proof_family": "jones-section2-polar-support",
            "surface": "kernel membership transfer for polar positive part",
        },
        "outcome": "helpful",
        "confidence": 0.91,
        "reuse_conditions": [
            "the proof needs to move kernel membership from the positive part back to the original operator",
            "the local source already lives inside the Jones finite-coordinate polar setup",
        ],
        "do_not_apply_when": [
            "the proof is outside the finite-coordinate polar decomposition regime",
            "no kernel bridge lemma of this shape exists in the current namespace",
        ],
        "human_note": "Reach for the domain bridge lemma before expanding kernel definitions manually.",
    },
    {
        "strategy_id": "strat-jones-have-rw-goal-shape-mismatch",
        "strategy_type": "failure_pattern",
        "summary": (
            "When `show f (x - y) = 0` fails because the goal is really `f x - f y = 0`, "
            "first materialize the mapped subtraction in a `have`, then `rw` into the exact goal shape."
        ),
        "input_context": {
            "proof_family": "jones-section2-polar-support",
            "surface": "goal-shape alignment after map_sub",
        },
        "outcome": "helpful",
        "confidence": 0.89,
        "reuse_conditions": [
            "a mapped subtraction goal differs syntactically from the target but is propositionally the same",
            "the local obstacle is term shape rather than missing mathematical content",
        ],
        "do_not_apply_when": [
            "the map does not preserve subtraction in the required structure",
            "the mismatch comes from coercions or casts rather than subtraction expansion",
        ],
        "human_note": "Use `have` plus targeted rewrites to align Lean's exact goal shape.",
    },
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _validator(path: Path) -> Draft202012Validator:
    return Draft202012Validator(json.loads(path.read_text(encoding="utf-8")))


def _strategy_memory_path(kernel_root: Path, topic_slug: str, run_id: str) -> Path:
    return kernel_root / "feedback" / "topics" / topic_slug / "runs" / run_id / "strategy_memory.jsonl"


def _proof_fragment_path(kernel_root: Path, unit_id: str) -> Path:
    slug = unit_id.split(":", 1)[1]
    return kernel_root / "canonical" / "proof-fragments" / f"proof_fragment--{slug}.json"


def build_jones_codrestrict_proof_fragment(*, updated_by: str, timestamp: str | None = None) -> dict[str, Any]:
    recorded_at = timestamp or now_iso()
    return {
        "id": JONES_PROOF_FRAGMENT_ID,
        "unit_type": "proof_fragment",
        "title": "Jones codRestrict + subtype composition construction recipe",
        "summary": (
            "Reusable Lean proof fragment for building a range-facing map by first codRestricting into a "
            "proved range target and then composing with the ambient subtype map."
        ),
        "maturity": "human_promoted",
        "created_at": recorded_at,
        "updated_at": recorded_at,
        "topic_completion_status": "promotion-ready",
        "tags": [
            "lean",
            "proof-engineering",
            "jones2015",
            "codrestrict",
            "submodule",
            "support-projection",
        ],
        "assumptions": [
            "A witness already proves that the map lands in the target range or submodule.",
            "The local goal is a reusable range-facing construction rather than a whole-theorem packaging step.",
        ],
        "regime": {
            "domain": "Lean proof engineering for Jones 2015 Section 2 polar-support constructions",
            "approximations": [
                "mathlib codRestrict APIs are available",
                "submodule subtype composition is accepted as the range-facing packaging step",
            ],
            "scale": "bounded local proof fragment",
            "boundary_conditions": [
                "the target codomain is a submodule-backed range object",
                "the proof already has the needed range witness",
            ],
            "exclusions": [
                "whole-theorem promotion decisions",
                "goals whose real blocker is theorem shape rather than codomain packaging",
            ],
        },
        "scope": {
            "applies_to": [
                "range-facing linear map constructions",
                "submodule-to-range LinearEquiv or LinearMap packaging steps",
            ],
            "out_of_scope": [
                "proofs that still need a kernel or range bridge lemma",
                "non-submodule codomain rewrites",
            ],
        },
        "provenance": {
            "source_ids": [
                "source:jones-2015-section2-polar-support",
                "source:phase165-jones-proof-engineering-postmortem",
            ],
            "l1_artifacts": [],
            "l3_runs": [
                "phase165:jones-lean-proof-iteration-rounds-1-7",
            ],
            "l4_checks": [
                "local lake build JonesVonNeumannDefinitions",
                "remote lake build JonesVonNeumannDefinitions.Jones2015.Section2PolarSupportProjection",
            ],
            "citations": [
                _POSTMORTEM_REF,
                _ISSUE_LEDGER_REF,
            ],
        },
        "promotion": {
            "route": "L3->L4->L2",
            "review_mode": "human",
            "canonical_layer": "L2",
            "promoted_by": updated_by,
            "promoted_at": recorded_at,
            "review_status": "accepted",
            "rationale": (
                "Promoted from the Phase 165 Jones E2E findings so the recovered proof-engineering recipe is no longer chat-only."
            ),
        },
        "dependencies": [],
        "related_units": [],
        "payload": {
            "goal": (
                "Produce a reusable range-facing map when the proof already knows the image lands in a target submodule."
            ),
            "inputs": [
                "a LinearMap or ContinuousLinearMap whose image is known to land in the target range",
                "a subtype map from the range/submodule back into the ambient codomain",
            ],
            "construction_steps": [
                "Extract or prove the witness that the map lands in the target submodule or range.",
                "Apply `codRestrict` to package the map into that target codomain.",
                "Compose the restricted map with `Submodule.subtype` or the matching subtype map instead of forcing a direct subtype-to-range morphism.",
                "Only after the codomain shape is fixed, prove the remaining equality or kernel side conditions.",
            ],
            "common_pitfalls": [
                "Trying to build the final subtype-to-range map in one step usually hides the actual codomain witness you already have.",
                "Mixing ContinuousLinearMap and LinearMap rewrites before the codomain is packaged can trigger coercion-shape failures.",
            ],
            "reuse_conditions": [
                "The proof already has a concrete range or kernel bridge into the target submodule.",
                "The target is a local reusable construction step rather than a whole theorem statement.",
            ],
            "do_not_apply_when": [
                "No landing witness has been proved yet.",
                "The real blocker is a missing bridge lemma rather than codomain packaging.",
            ],
            "supporting_lemmas": [
                "jonesFiniteCoordinatePolarPositivePart_ker_eq_ker",
            ],
            "failure_signatures": [
                "Lean keeps asking for a direct subtype-to-range map that should have been built via codRestrict first.",
                "A later `show` goal mismatch appears because the codomain shape was never normalized.",
            ],
            "result_shape": "A range-facing LinearMap or LinearEquiv packaged through codRestrict followed by subtype composition.",
            "verification_status": "remotely_validated",
            "notes": "Seeded from the Jones Phase 165 postmortem as the first canonical proof_fragment instance.",
        },
    }


def materialize_jones_proof_engineering_seed(
    kernel_root: Path,
    *,
    topic_slug: str = JONES_TOPIC_SLUG,
    run_id: str = JONES_RUN_ID,
    updated_by: str = "aitp-cli",
) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    strategy_memory_path = _strategy_memory_path(kernel_root, topic_slug, run_id)
    existing_rows = [
        row
        for row in read_jsonl(strategy_memory_path)
        if str(row.get("strategy_id") or "").strip()
        not in {str(seed["strategy_id"]) for seed in JONES_STRATEGY_MEMORY_SEEDS}
    ]
    timestamp = now_iso()
    seeded_rows = [
        {
            "timestamp": timestamp,
            "topic_slug": topic_slug,
            "run_id": run_id,
            "lane": "formal_derivation",
            "strategy_id": str(seed["strategy_id"]),
            "strategy_type": str(seed["strategy_type"]),
            "summary": str(seed["summary"]),
            "input_context": dict(seed.get("input_context") or {}),
            "outcome": str(seed["outcome"]),
            "confidence": float(seed["confidence"]),
            "evidence_refs": [_POSTMORTEM_REF, _ISSUE_LEDGER_REF],
            "reuse_conditions": list(seed.get("reuse_conditions") or []),
            "do_not_apply_when": list(seed.get("do_not_apply_when") or []),
            "human_note": str(seed.get("human_note") or ""),
            "updated_by": updated_by,
        }
        for seed in JONES_STRATEGY_MEMORY_SEEDS
    ]
    write_jsonl(strategy_memory_path, [*existing_rows, *seeded_rows])

    proof_fragment = build_jones_codrestrict_proof_fragment(updated_by=updated_by, timestamp=timestamp)
    canonical_validator = _validator(kernel_root / "canonical" / "canonical-unit.schema.json")
    proof_fragment_validator = _validator(kernel_root / "schemas" / "proof-fragment.schema.json")
    canonical_validator.validate(proof_fragment)
    proof_fragment_validator.validate(proof_fragment["payload"])

    proof_fragment_path = _proof_fragment_path(kernel_root, proof_fragment["id"])
    _write_json(proof_fragment_path, proof_fragment)
    index_payload = materialize_canonical_index(kernel_root)
    index_rows = read_jsonl(kernel_root / "canonical" / "index.jsonl")
    return {
        "topic_slug": topic_slug,
        "run_id": run_id,
        "strategy_memory_path": str(strategy_memory_path),
        "strategy_memory_row_count": len([row for row in read_jsonl(strategy_memory_path)]),
        "seeded_strategy_ids": [row["strategy_id"] for row in seeded_rows],
        "proof_fragment_id": str(proof_fragment["id"]),
        "proof_fragment_path": str(proof_fragment_path),
        "canonical_index_path": str(kernel_root / "canonical" / "index.jsonl"),
        "canonical_index_row_count": len(index_rows),
        "updated_by": updated_by,
        "canonical_index": index_payload,
    }
