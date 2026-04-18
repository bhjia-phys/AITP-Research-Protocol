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

_JONES_STRATEGY_SEEDS_PATH = Path(__file__).resolve().parent.parent / "config" / "jones_strategy_memory_seeds.json"


def _load_jones_strategy_seeds() -> list[dict[str, Any]]:
    return json.loads(_JONES_STRATEGY_SEEDS_PATH.read_text(encoding="utf-8"))


def jones_strategy_seeds() -> list[dict[str, Any]]:
    return _load_jones_strategy_seeds()



def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_goal_text(goal: str) -> str:
    return " ".join(str(goal or "").strip().split())


def suggest_tactics(
    goal: str,
    *,
    assistant: str = "lean4",
    context: dict[str, Any] | None = None,
    available_lemmas: list[str] | None = None,
) -> list[dict[str, Any]]:
    normalized_goal = _normalize_goal_text(goal)
    if not normalized_goal:
        raise ValueError("goal must not be empty")

    lowered_goal = normalized_goal.lower()
    suggestions: list[dict[str, Any]] = []

    def add_suggestion(tactic: str, reason: str, *, confidence: float = 0.6) -> None:
        if any(str(row.get("tactic") or "") == tactic for row in suggestions):
            return
        suggestions.append(
            {
                "assistant": assistant,
                "tactic": tactic,
                "reason": reason,
                "confidence": confidence,
            }
        )

    if " iff " in f" {lowered_goal} ":
        add_suggestion("constructor", "An iff goal usually splits into two directional implications.", confidence=0.82)
    if any(token in lowered_goal for token in ("exists", "there exists")):
        add_suggestion("refine Exists.intro ?_", "Existential goals often benefit from choosing the witness first.", confidence=0.79)
        add_suggestion("use ?_", "Lean `use` is a compact entrypoint for existential witnesses.", confidence=0.74)
    if any(token in lowered_goal for token in ("=", " equality ", "equal")):
        add_suggestion("rw [...]", "Equality goals often simplify after targeted rewriting.", confidence=0.7)
        add_suggestion("simp", "Try simplification before deeper tactic search on equality-like goals.", confidence=0.66)
        add_suggestion("calc", "A `calc` block can expose the intermediate equalities explicitly.", confidence=0.68)
    if any(token in lowered_goal for token in ("submodule", "range", "codrestrict")):
        add_suggestion(
            "refine LinearMap.codRestrict ?_ ?_",
            "Range/submodule goals often need codRestrict packaging before the final subtype map.",
            confidence=0.84,
        )
    if any(token in lowered_goal for token in ("kernel", "ker ")):
        add_suggestion(
            "have hker := ...",
            "Kernel goals are often easier after isolating the bridge lemma in a named `have`.",
            confidence=0.72,
        )
    if any(token in lowered_goal for token in ("forall", "for all")):
        add_suggestion("intro", "Universal goals usually begin by introducing the quantified variable.", confidence=0.83)
    if any(token in lowered_goal for token in ("+", "-", "*", "/")):
        add_suggestion("ring_nf", "Normalize algebraic expressions before debugging a harder proof state.", confidence=0.64)

    for lemma in available_lemmas or []:
        cleaned = str(lemma or "").strip()
        if cleaned:
            add_suggestion(
                f"rw [{cleaned}]",
                f"Available lemma `{cleaned}` may rewrite the goal into a more tractable form.",
                confidence=0.58,
            )

    for seed in jones_strategy_seeds():
        seed_text = " ".join(
            [
                str(seed.get("summary") or ""),
                str((seed.get("input_context") or {}).get("surface") or ""),
                " ".join(seed.get("reuse_conditions") or []),
            ]
        ).lower()
        overlap = [
            token
            for token in ("range", "submodule", "codrestrict", "kernel", "subtraction", "goal", "shape")
            if token in lowered_goal and token in seed_text
        ]
        if not overlap:
            continue
        add_suggestion(
            "have h_strategy := ...",
            f"Recent proof-engineering memory matches this goal surface ({', '.join(overlap)}). Externalize the bridge step explicitly before deeper search.",
            confidence=float(seed.get("confidence") or 0.6),
        )

    if not suggestions:
        add_suggestion("simp?", "No specialized tactic matched; start with simplification or local theorem search.", confidence=0.5)
        add_suggestion("aesop?", "Fallback search may expose the next missing hypothesis or lemma.", confidence=0.45)

    return suggestions


def bootstrap_proof_attempt(
    goal: str,
    *,
    assistant: str = "lean4",
    context: dict[str, Any] | None = None,
    available_lemmas: list[str] | None = None,
    updated_by: str = "aitp-cli",
) -> dict[str, Any]:
    normalized_goal = _normalize_goal_text(goal)
    if not normalized_goal:
        raise ValueError("goal must not be empty")
    timestamp = now_iso()
    proof_attempt_id = f"proof_attempt:{normalized_goal.lower().replace(' ', '-')[:48].strip('-') or 'goal'}"
    tactic_suggestions = suggest_tactics(
        normalized_goal,
        assistant=assistant,
        context=context,
        available_lemmas=available_lemmas,
    )
    return {
        "attempt_version": 1,
        "proof_attempt_id": proof_attempt_id,
        "assistant": assistant,
        "goal": normalized_goal,
        "status": "bootstrapped",
        "context": dict(context or {}),
        "available_lemmas": [str(item or "").strip() for item in (available_lemmas or []) if str(item or "").strip()],
        "suggested_tactics": tactic_suggestions,
        "tactic_count": len(tactic_suggestions),
        "bootstrapped_at": timestamp,
        "updated_at": timestamp,
        "updated_by": updated_by,
    }


def check_proof_status(
    proof_attempt: dict[str, Any],
    *,
    transcript: list[dict[str, Any]] | None = None,
    open_goal_count: int | None = None,
    hard_error: str | None = None,
) -> dict[str, Any]:
    transcript_rows = [dict(row) for row in (transcript or [])]
    last_step = transcript_rows[-1] if transcript_rows else {}
    last_step_status = str(last_step.get("status") or "").strip().lower()
    attempt_status = str(proof_attempt.get("status") or "bootstrapped").strip().lower()

    if str(hard_error or "").strip():
        status = "blocked"
        summary = "Proof attempt is blocked by an explicit error."
        next_steps = ["Inspect the failing tactic state and replace the brittle step with a named intermediate lemma."]
    elif open_goal_count == 0 or last_step_status in {"solved", "complete", "closed"}:
        status = "solved"
        summary = "Proof attempt closed all visible goals."
        next_steps = []
    elif transcript_rows or attempt_status in {"running", "in_progress"}:
        status = "in_progress"
        summary = "Proof attempt has started but still leaves open goals."
        next_steps = ["Keep the next tactic local and expose the missing bridge lemma or rewrite explicitly."]
    else:
        status = "not_started"
        summary = "Proof attempt has been bootstrapped but no proof transcript is recorded yet."
        next_steps = ["Start with one of the suggested tactics and record the resulting proof state."]

    return {
        "proof_attempt_id": str(proof_attempt.get("proof_attempt_id") or ""),
        "assistant": str(proof_attempt.get("assistant") or ""),
        "status": status,
        "summary": summary,
        "open_goal_count": open_goal_count,
        "hard_error": str(hard_error or "").strip() or None,
        "last_step_status": last_step_status or None,
        "next_steps": next_steps,
        "updated_at": now_iso(),
    }


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
    return kernel_root / "topics" / topic_slug / "L3" / "runs" / run_id / "strategy_memory.jsonl"


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
        not in {str(seed["strategy_id"]) for seed in jones_strategy_seeds()}
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
        for seed in jones_strategy_seeds()
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
