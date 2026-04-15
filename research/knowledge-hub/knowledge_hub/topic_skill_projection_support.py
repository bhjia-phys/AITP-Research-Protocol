from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .topic_truth_root_support import compatibility_projection_path


def _read_json(path: Path) -> dict[str, Any] | None:
    target = path
    if not target.exists():
        compatibility_path = compatibility_projection_path(path)
        if compatibility_path is None or not compatibility_path.exists():
            return None
        target = compatibility_path
    return json.loads(target.read_text(encoding="utf-8"))


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-+", "-", lowered).strip("-")
    return lowered or "aitp-topic"


def _build_projection_context(
    self,
    *,
    topic_slug: str,
    topic_state: dict[str, Any],
    research_contract: dict[str, Any],
    strategy_memory: dict[str, Any],
    topic_completion: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    latest_run_id = str(topic_state.get("latest_run_id") or "").strip()
    lane = self._lane_for_modes(
        template_mode=research_contract.get("template_mode"),
        research_mode=research_contract.get("research_mode"),
    )
    formal_theory_context = self._formal_theory_projection_candidate_context(
        topic_slug=topic_slug,
        run_id=latest_run_id or None,
        candidate_rows=candidate_rows,
    )
    formal_theory_candidate_id = str((formal_theory_context or {}).get("candidate_id") or "").strip()
    formal_theory_review_path = (formal_theory_context or {}).get("review_path")
    formal_theory_review_status = str((formal_theory_context or {}).get("review_status") or "missing").strip()
    formal_theory_completion_status = str(
        (formal_theory_context or {}).get("completion_status") or topic_completion.get("status") or "not_assessed"
    ).strip()
    trust_audit_path = (
        self._trust_audit_path(topic_slug, latest_run_id)
        if latest_run_id
        else self._runtime_root(topic_slug) / "missing-trust-audit.json"
    )
    trust_audit = _read_json(trust_audit_path) if trust_audit_path.exists() else None
    operation_manifests = self._load_operation_manifests(topic_slug, latest_run_id or None)
    return {
        "latest_run_id": latest_run_id,
        "lane": lane,
        "formal_theory_context": formal_theory_context,
        "formal_theory_candidate_id": formal_theory_candidate_id,
        "formal_theory_review_path": formal_theory_review_path,
        "formal_theory_review_status": formal_theory_review_status,
        "formal_theory_completion_status": formal_theory_completion_status,
        "trust_audit_path": trust_audit_path,
        "trust_audit": trust_audit,
        "operation_manifests": operation_manifests,
        "strategy_memory_rows": int(strategy_memory.get("row_count") or 0),
    }


def _build_projection_reads_and_signals(
    self,
    *,
    topic_slug: str,
    selected_pending_action: dict[str, Any] | None,
    strategy_memory: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, list[str]]:
    lane = context["lane"]
    formal_theory_candidate_id = context["formal_theory_candidate_id"]
    formal_theory_review_path = context["formal_theory_review_path"]
    formal_theory_review_status = context["formal_theory_review_status"]
    formal_theory_completion_status = context["formal_theory_completion_status"]
    trust_audit_path = context["trust_audit_path"]
    operation_manifests = context["operation_manifests"]
    entry_signals = self._dedupe_strings(
        [
            f"lane={lane}",
            f"selected_action={str((selected_pending_action or {}).get('summary') or '').strip() or '(none)'}",
            f"strategy_memory_status={strategy_memory.get('status') or 'absent'}",
            (
                f"theorem_candidate={formal_theory_candidate_id or '(none)'}"
                if lane == "formal_theory"
                else f"operation_count={len(operation_manifests)}"
            ),
            (
                f"formal_theory_review={formal_theory_review_status}"
                if lane == "formal_theory"
                else f"operation_trust={str((context['trust_audit'] or {}).get('overall_status') or 'missing')}"
            ),
            (f"topic_completion={formal_theory_completion_status}" if lane == "formal_theory" else ""),
        ]
    )
    required_first_reads = self._dedupe_strings(
        [
            self._relativize(self._research_question_contract_paths(topic_slug)["note"]),
            self._relativize(self._validation_contract_paths(topic_slug)["note"]),
            self._normalize_artifact_path(strategy_memory.get("latest_path")),
            (
                self._relativize(formal_theory_review_path)
                if lane == "formal_theory" and isinstance(formal_theory_review_path, Path) and formal_theory_review_path.exists()
                else self._relativize(trust_audit_path) if trust_audit_path.exists() else ""
            ),
            (self._relativize(self._topic_completion_paths(topic_slug)["note"]) if lane == "formal_theory" else ""),
            *[str(row.get("summary_path") or row.get("path") or "") for row in operation_manifests],
        ]
    )
    derived_from_artifacts = self._dedupe_strings(
        [
            self._relativize(self._research_question_contract_paths(topic_slug)["json"]),
            self._relativize(self._validation_contract_paths(topic_slug)["json"]),
            self._relativize(self._runtime_root(topic_slug) / "topic_state.json"),
            self._normalize_artifact_path(strategy_memory.get("latest_path")),
            self._relativize(trust_audit_path) if trust_audit_path.exists() else "",
            self._relativize(self._topic_completion_paths(topic_slug)["json"]),
            self._relativize(formal_theory_review_path) if isinstance(formal_theory_review_path, Path) and formal_theory_review_path.exists() else "",
            self._relativize(self._gap_map_path(topic_slug)),
            *[str(row.get("path") or "") for row in operation_manifests],
        ]
    )
    return {
        "entry_signals": entry_signals,
        "required_first_reads": required_first_reads,
        "derived_from_artifacts": derived_from_artifacts,
    }


def _build_projection_rules(
    self,
    *,
    lane: str,
    strategy_memory: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, list[str]]:
    required_first_routes: list[str] = []
    benchmark_first_rules: list[str] = []
    operation_trust_requirements: list[str] = []
    if lane == "formal_theory":
        candidate_label = context["formal_theory_candidate_id"] or "the active theorem-facing candidate"
        required_first_routes.extend(
            [
                f"Read `formal_theory_review.json` for `{candidate_label}` before reusing the theorem-facing route.",
                "Check that `topic_completion.json` still reports `promotion-ready` or `promoted` before treating the route as reusable.",
            ]
        )
        benchmark_first_rules.append(
            f"`{candidate_label}` requires `formal_theory_review.json` overall_status `ready` and topic completion `promotion-ready` or `promoted` before route reuse is trusted."
        )
        operation_trust_requirements.append(
            f"`{candidate_label}`: formal_theory_review_status={context['formal_theory_review_status']}, topic_completion_status={context['formal_theory_completion_status']}, strategy_memory_rows={context['strategy_memory_rows']}."
        )
    else:
        for manifest in context["operation_manifests"]:
            title_hint = str(manifest.get("title") or manifest.get("operation_id") or "(missing)")
            baseline_required = bool(manifest.get("baseline_required"))
            atomic_required = bool(manifest.get("atomic_understanding_required"))
            baseline_status = str(manifest.get("baseline_status") or "missing")
            atomic_status = str(manifest.get("atomic_understanding_status") or "missing")
            if baseline_required:
                required_first_routes.append(
                    f"Close the declared benchmark/baseline for `{title_hint}` before broader workflow claims."
                )
                benchmark_first_rules.append(
                    f"`{title_hint}` requires baseline status `{baseline_status}` before route reuse is trusted."
                )
            if atomic_required:
                required_first_routes.append(
                    f"Complete atomic understanding for `{title_hint}` before claiming reusable method understanding."
                )
            operation_trust_requirements.append(
                f"`{title_hint}`: baseline_required={str(baseline_required).lower()}, baseline_status={baseline_status}, atomic_understanding_required={str(atomic_required).lower()}, atomic_understanding_status={atomic_status}."
            )
        if not benchmark_first_rules:
            benchmark_first_rules.append(
                "Do not claim reusable code-method confidence without a persisted benchmark or trust-ready operation artifact."
            )
    operator_checkpoint_rules = [
        "Raise an operator checkpoint when benchmark mismatch or validation-route ambiguity changes the bounded route.",
        "Require explicit human approval before any L2 promotion of a topic-skill projection.",
        "Translate continue/branch/redirect answers into durable steering artifacts before deeper execution continues.",
    ]
    return {
        "required_first_routes": self._dedupe_strings(required_first_routes),
        "benchmark_first_rules": self._dedupe_strings(benchmark_first_rules),
        "operation_trust_requirements": self._dedupe_strings(operation_trust_requirements),
        "operator_checkpoint_rules": operator_checkpoint_rules,
        "strategy_guidance": self._dedupe_strings(list(strategy_memory.get("guidance") or [])),
    }


def _projection_status_for_lane(
    *,
    lane: str,
    context: dict[str, Any],
) -> tuple[str, str]:
    if lane == "formal_theory":
        if not context["latest_run_id"]:
            return "blocked", "Projection is blocked because the topic has no active run id yet."
        if not context["formal_theory_context"]:
            return "not_applicable", "Topic-skill projection is not applicable because the active run has no theorem-facing candidate rows."
        if not isinstance(context["formal_theory_review_path"], Path) or not context["formal_theory_review_path"].exists():
            return (
                "blocked",
                f"Projection is blocked until `{context['formal_theory_candidate_id'] or 'the active theorem-facing candidate'}` has a durable formal_theory_review.json artifact.",
            )
        if context["formal_theory_review_status"] != "ready":
            return (
                "blocked",
                f"Projection is blocked until `{context['formal_theory_candidate_id'] or 'the active theorem-facing candidate'}` has formal_theory_review overall_status `ready`.",
            )
        if context["formal_theory_completion_status"] not in {"promotion-ready", "promoted"}:
            return "blocked", "Projection is blocked until topic completion reaches `promotion-ready` or `promoted`."
        if context["strategy_memory_rows"] <= 0:
            return "blocked", "Projection is blocked until at least one run-local strategy-memory row exists."
        return (
            "available",
            "Projection is available because the topic is formal_theory, the active theorem-facing review is ready, topic completion is promotion-ready, and route-level strategy memory exists.",
        )
    if lane != "code_method":
        return "not_applicable", "Topic-skill projection v1 only applies to the code_method lane."
    if not context["latest_run_id"]:
        return "blocked", "Projection is blocked because the topic has no active run id yet."
    if not context["operation_manifests"]:
        return "blocked", "Projection is blocked because no operation manifests exist for the active run."
    if not context["trust_audit"] or str(context["trust_audit"].get("overall_status") or "") != "pass":
        return "blocked", "Projection is blocked until operation trust passes for the active run."
    if context["strategy_memory_rows"] <= 0:
        return "blocked", "Projection is blocked until at least one run-local strategy-memory row exists."
    return (
        "available",
        "Projection is available because the topic is code_method, has trust-ready operation manifests, and carries route-level strategy memory.",
    )


def derive_topic_skill_projection(
    self,
    *,
    topic_slug: str,
    updated_by: str,
    topic_state: dict[str, Any],
    research_contract: dict[str, Any],
    validation_contract: dict[str, Any],
    selected_pending_action: dict[str, Any] | None,
    strategy_memory: dict[str, Any],
    topic_completion: dict[str, Any],
    open_gap_summary: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    context = _build_projection_context(
        self,
        topic_slug=topic_slug,
        topic_state=topic_state,
        research_contract=research_contract,
        strategy_memory=strategy_memory,
        topic_completion=topic_completion,
        candidate_rows=candidate_rows,
    )
    projection_id = f"topic_skill_projection:{_slugify(topic_slug)}"
    candidate_hash = hashlib.sha1(topic_slug.encode("utf-8")).hexdigest()[:8]
    candidate_slug = _slugify(topic_slug)[:24].rstrip("-")
    candidate_id = f"candidate:topic-skill-proj-{candidate_slug}-{candidate_hash}"
    title = f"{str(research_contract.get('title') or self._topic_display_title(topic_slug))} Topic Skill Projection"
    signal_bundle = _build_projection_reads_and_signals(
        self,
        topic_slug=topic_slug,
        selected_pending_action=selected_pending_action,
        strategy_memory=strategy_memory,
        context=context,
    )
    rule_bundle = _build_projection_rules(
        self,
        lane=context["lane"],
        strategy_memory=strategy_memory,
        context=context,
    )
    forbidden_proxies = self._dedupe_strings(
        list(research_contract.get("forbidden_proxies") or [])
        + [
            "Do not treat raw code changes, unreviewed configs, or prose-only workflow descriptions as a reusable topic-skill projection.",
            (
                "Do not treat the projection itself as a theorem certificate, proof closure, or completed formal result."
                if context["lane"] == "formal_theory"
                else "Do not claim broader workflow portability before the benchmark-first gate and operation-trust audit are both satisfied."
            ),
        ]
    )
    status, status_reason = _projection_status_for_lane(lane=context["lane"], context=context)
    summary = (
        (
            "Validated reusable execution projection for the topic's theorem-facing formal-theory route."
            if context["lane"] == "formal_theory"
            else "Validated reusable execution projection for the topic's benchmark-first code-method route."
        )
        if status == "available"
        else "Topic-skill projection is not yet reusable enough to treat as an L2-ready execution projection."
    )
    return {
        "id": projection_id,
        "topic_slug": topic_slug,
        "source_topic_slug": topic_slug,
        "run_id": context["latest_run_id"],
        "title": title,
        "summary": summary,
        "lane": context["lane"],
        "status": status,
        "status_reason": status_reason,
        "candidate_id": candidate_id if status == "available" else None,
        "intended_l2_target": projection_id if status == "available" else None,
        "entry_signals": signal_bundle["entry_signals"],
        "required_first_reads": signal_bundle["required_first_reads"],
        "required_first_routes": rule_bundle["required_first_routes"],
        "benchmark_first_rules": rule_bundle["benchmark_first_rules"],
        "operator_checkpoint_rules": rule_bundle["operator_checkpoint_rules"],
        "operation_trust_requirements": rule_bundle["operation_trust_requirements"],
        "strategy_guidance": rule_bundle["strategy_guidance"],
        "forbidden_proxies": forbidden_proxies,
        "derived_from_artifacts": signal_bundle["derived_from_artifacts"],
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }
