"""Project-scope shims for external domain skill discovery."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from brain.v5.domain_packs import builtin_domain_packs
from brain.v5.markdown import write_text_atomic
from brain.v5.paths import WorkspacePaths


def build_domain_skill_shim_manifest(
    ws: WorkspacePaths,
    *,
    pack_ids: list[str] | None = None,
    output_root: str = ".agents/skills",
    apply: bool = False,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Preview or write project-local SKILL.md shims from domain-pack skill refs."""

    packs = builtin_domain_packs()
    selected_pack_ids = _selected_pack_ids(packs, pack_ids or [])
    resolved_output_root = _resolve_output_root(ws, output_root)
    shim_specs = _shim_specs(
        packs,
        selected_pack_ids=selected_pack_ids,
        output_root=resolved_output_root,
        overwrite=overwrite,
    )
    shims = [
        _materialize_or_preview_shim(shim, apply=apply, overwrite=overwrite)
        for shim in shim_specs
    ]
    write_count = sum(1 for shim in shims if shim["status"] in {"created", "updated"})
    blocked_count = sum(1 for shim in shims if shim["status"] == "blocked_existing")
    return {
        "ok": True,
        "kind": "domain_skill_shim_manifest",
        "truth_source": "builtin_domain_pack_skill_refs",
        "workspace_base": str(ws.base),
        "output_root": str(resolved_output_root),
        "relative_output_root": _relative_to_base(ws, resolved_output_root),
        "requested_pack_ids": list(pack_ids or []),
        "selected_pack_ids": selected_pack_ids,
        "selected_pack_count": len(selected_pack_ids),
        "shim_count": len(shims),
        "write_count": write_count,
        "blocked_count": blocked_count,
        "apply": bool(apply),
        "overwrite": bool(overwrite),
        "state_effect": "project_skill_shim_write" if apply else "read_only_preview",
        "shims": shims,
        "required_followup_for_use": [
            "load the generated project-local shim only as orientation",
            "load external skill content from the declared repo and entrypoint when available",
            "write typed AITP records for durable sources, runs, artifacts, evidence, validation, and checkpoints",
            "run trust preflight before any claim confidence or memory promotion",
        ],
        "generation_policy": {
            "default_output_root": ".agents/skills",
            "writes_only_project_shims": True,
            "copies_external_skill_content": False,
            "requires_explicit_apply": True,
            "overwrite_requires_flag": True,
            "forbidden_uses": [
                "evidence_support",
                "source_support_result",
                "validation_result",
                "claim_trust_update",
                "trust_apply",
                "external_skill_content_vendoring",
            ],
        },
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "can_create_evidence": False,
        "can_materialize_external_skill_content": False,
        "external_skill_content_copied": False,
        "writes_project_files": bool(apply),
    }


def _selected_pack_ids(packs: dict[str, Any], requested: list[str]) -> list[str]:
    selected = _nonempty_unique(requested)
    if not selected:
        selected = [pack_id for pack_id, pack in packs.items() if pack.skill_refs]
    unknown = [pack_id for pack_id in selected if pack_id not in packs]
    if unknown:
        raise ValueError(f"unknown domain pack id(s): {', '.join(unknown)}")
    return selected


def _shim_specs(
    packs: dict[str, Any],
    *,
    selected_pack_ids: list[str],
    output_root: Path,
    overwrite: bool,
) -> list[dict[str, Any]]:
    by_skill: dict[str, dict[str, Any]] = {}
    for pack_id in selected_pack_ids:
        pack = packs[pack_id]
        for ref in pack.skill_refs:
            skill_id = str(ref.get("skill_id") or "").strip()
            if not skill_id:
                continue
            shim_name = _skill_name(skill_id)
            spec = by_skill.setdefault(
                shim_name,
                {
                    "shim_name": shim_name,
                    "skill_id": skill_id,
                    "pack_ids": [],
                    "domain_ids": [],
                    "skill_refs": [],
                    "target_path": str(output_root / shim_name / "SKILL.md"),
                    "overwrite": bool(overwrite),
                },
            )
            if pack_id not in spec["pack_ids"]:
                spec["pack_ids"].append(pack_id)
            if pack.domain not in spec["domain_ids"]:
                spec["domain_ids"].append(pack.domain)
            spec["skill_refs"].append(dict(ref))
    specs = []
    for spec in sorted(by_skill.values(), key=lambda item: item["shim_name"]):
        content = _render_skill_shim(spec)
        spec["content_hash"] = hashlib.sha256(content.encode("utf-8")).hexdigest()
        spec["content_preview"] = _content_preview(content)
        spec["_content"] = content
        specs.append(spec)
    return specs


def _materialize_or_preview_shim(
    spec: dict[str, Any],
    *,
    apply: bool,
    overwrite: bool,
) -> dict[str, Any]:
    path = Path(spec["target_path"])
    content = spec["_content"]
    exists = path.exists()
    existing_hash = ""
    if exists:
        existing_hash = hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    content_matches = exists and existing_hash == spec["content_hash"]
    if not apply:
        if content_matches:
            status = "up_to_date"
        elif exists and not overwrite:
            status = "blocked_existing"
        elif exists:
            status = "would_update"
        else:
            status = "would_create"
    elif content_matches:
        status = "up_to_date"
    elif exists and not overwrite:
        status = "blocked_existing"
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        write_text_atomic(path, content)
        status = "updated" if exists else "created"
    payload = {
        key: value
        for key, value in spec.items()
        if key != "_content"
    }
    payload.update(
        {
            "kind": "domain_skill_shim",
            "status": status,
            "exists": exists,
            "existing_content_hash": existing_hash,
            "content_matches_existing": content_matches,
            "write_executed": status in {"created", "updated"},
            "write_blocked": status == "blocked_existing",
            "summary_inputs_trusted": False,
            "orientation_only": True,
            "can_update_claim_trust": False,
            "copies_external_skill_content": False,
        }
    )
    return payload


def _render_skill_shim(spec: dict[str, Any]) -> str:
    refs = spec["skill_refs"]
    first_ref = refs[0]
    description = _frontmatter_description(spec, first_ref)
    lines = [
        "---",
        f"name: {spec['shim_name']}",
        f"description: {_yaml_double_quote(description)}",
        "---",
        "",
        f"# AITP External Skill Shim: {spec['skill_id']}",
        "",
        "This project-local skill is a discovery shim generated from AITP domain pack skill refs.",
        "It points the host agent to external procedural knowledge without copying that external skill into AITP core.",
        "",
        "## Load",
        "",
    ]
    for ref in refs:
        lines.extend(
            [
                f"- Skill id: `{ref.get('skill_id', spec['skill_id'])}`",
                f"- Role: {ref.get('role', 'external domain skill guidance')}",
                f"- Repo: {ref.get('repo', 'not declared')}",
                f"- Entrypoint: `{ref.get('entrypoint', 'not declared')}`",
                f"- Kind: `{ref.get('kind', 'external_skill')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Use When",
            "",
            *_bullet_lines(_load_when(refs)),
            "",
            "## AITP Boundary",
            "",
            "- Treat this shim and the external skill as orientation and procedural memory only.",
            "- Do not treat generated reports, retrieved notes, or run summaries as claim support by default.",
            "- Do not update claim trust or long-term memory from this shim.",
            "- Use typed AITP tools for durable sources, runs, artifacts, evidence, validation, and checkpoints.",
            "",
            "## Required Follow-Up Records",
            "",
            *_bullet_lines(_required_followup_records(refs)),
            "",
            "## Generated From",
            "",
            f"- Domain packs: {', '.join(f'`{pack_id}`' for pack_id in spec['pack_ids'])}",
            f"- Domains: {', '.join(f'`{domain_id}`' for domain_id in spec['domain_ids'])}",
            "- Truth source: `builtin_domain_pack_skill_refs`",
            "- External skill content copied: `false`",
            "",
        ]
    )
    return "\n".join(lines)


def _frontmatter_description(spec: dict[str, Any], ref: dict[str, Any]) -> str:
    load_when = _load_when([ref])
    trigger = load_when[0] if load_when else ref.get("role", "external domain skill guidance")
    return (
        f"Project-local AITP shim for external skill {spec['skill_id']}. "
        f"Use when {trigger}. It is orientation-only and requires typed AITP follow-up records."
    )


def _load_when(refs: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for ref in refs:
        load_when = ref.get("load_when")
        if isinstance(load_when, list):
            values.extend(str(item) for item in load_when)
        elif ref.get("role"):
            values.append(str(ref["role"]))
    return _nonempty_unique(values) or ["the matching domain pack recommends this skill"]


def _required_followup_records(refs: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for ref in refs:
        records = ref.get("required_followup_records")
        if isinstance(records, list):
            values.extend(str(item) for item in records)
    return _nonempty_unique(values) or ["record_reference_location", "evidence", "validation_result"]


def _bullet_lines(values: list[str]) -> list[str]:
    return [f"- {value}" for value in values]


def _skill_name(skill_id: str) -> str:
    clean = re.sub(r"[^a-z0-9-]+", "-", str(skill_id).lower()).strip("-")
    if not clean:
        clean = "aitp-domain-skill"
    if len(clean) <= 63:
        return clean
    suffix = hashlib.sha1(clean.encode("utf-8")).hexdigest()[:8]
    return f"{clean[:54].rstrip('-')}-{suffix}"


def _content_preview(content: str) -> str:
    preview = content[:800]
    return preview if len(content) <= 800 else preview.rstrip() + "\n..."


def _resolve_output_root(ws: WorkspacePaths, output_root: str) -> Path:
    root = Path(str(output_root or ".agents/skills")).expanduser()
    if root.is_absolute():
        return root
    return ws.base / root


def _relative_to_base(ws: WorkspacePaths, path: Path) -> str:
    try:
        return str(path.relative_to(ws.base))
    except ValueError:
        return str(path)


def _yaml_double_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _nonempty_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = str(value).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result
