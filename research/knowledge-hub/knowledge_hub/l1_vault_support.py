from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .obsidian_graph_export import materialize_obsidian_concept_graph_export
from .l1_source_intake_support import l1_contradiction_summary_lines


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(json.dumps(row, ensure_ascii=True) for row in rows)
    path.write_text((body + "\n") if body else "", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = str(value or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def _frontmatter(**fields: str) -> str:
    lines = ["---"]
    for key, value in fields.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def _wiki_link(target: str, label: str) -> str:
    return f"[[{target}|{label}]]"


def _relative_or_none(path: Path, relativize: Callable[[Path], str]) -> str | None:
    return relativize(path) if path.exists() else None


def _vault_root(kernel_root: Path, topic_slug: str) -> Path:
    return kernel_root / "intake" / "topics" / topic_slug / "vault"


def _source_topic_root(kernel_root: Path, topic_slug: str) -> Path:
    return kernel_root / "source-layer" / "topics" / topic_slug


def _build_raw_sources(
    *,
    kernel_root: Path,
    topic_slug: str,
    source_rows: list[dict[str, Any]],
    relativize: Callable[[Path], str],
) -> list[dict[str, Any]]:
    topic_root = _source_topic_root(kernel_root, topic_slug)
    raw_sources: list[dict[str, Any]] = []
    for row in source_rows:
        source_id = str(row.get("source_id") or "").strip()
        source_slug = source_id.replace(":", "-") if source_id else "source"
        snapshot_path = topic_root / "sources" / source_slug / "snapshot.md"
        provenance = row.get("provenance") or {}
        if not isinstance(provenance, dict):
            provenance = {}
        raw_sources.append(
            {
                "source_id": source_id,
                "source_type": str(row.get("source_type") or "").strip(),
                "title": str(row.get("title") or "").strip(),
                "summary": str(row.get("summary") or "").strip(),
                "source_index_path": relativize(topic_root / "source_index.jsonl"),
                "snapshot_path": relativize(snapshot_path) if snapshot_path.exists() else "",
                "absolute_path": str(provenance.get("absolute_path") or "").strip(),
                "abs_url": str(provenance.get("abs_url") or "").strip(),
                "canonical_source_id": str(row.get("canonical_source_id") or "").strip(),
                "read_only": True,
            }
        )
    return raw_sources


def _render_raw_manifest_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# L1 Raw Source Manifest",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Source count: `{payload.get('source_count') or 0}`",
        f"- Source index path: `{payload.get('source_index_path') or '(missing)'}`",
        "",
        "## Rule",
        "",
        "The raw layer is anchored to immutable source-layer inputs. Agents may read these inputs but should not treat this manifest as a writable second source of truth.",
        "",
        "## Sources",
        "",
    ]
    sources = payload.get("sources") or []
    if not sources:
        lines.append("- `(none)`")
    for row in sources:
        lines.extend(
            [
                f"- `{row.get('source_id') or '(missing)'}` type=`{row.get('source_type') or '(missing)'}`",
                f"  - title: {row.get('title') or '(missing)'}",
                f"  - snapshot: `{row.get('snapshot_path') or '(none)'}`",
                f"  - absolute_path: `{row.get('absolute_path') or '(none)'}`",
                f"  - abs_url: `{row.get('abs_url') or '(none)'}`",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _render_wiki_schema_markdown(
    *,
    topic_slug: str,
    protocol_path: str,
    concept_graph_index_path: str,
    updated_at: str,
    updated_by: str,
) -> str:
    return (
        _frontmatter(
            page_type="vault_schema",
            topic_slug=topic_slug,
            authority_level="non_authoritative_compiled_l1",
            updated_at=updated_at,
            updated_by=updated_by,
        )
        + "\n"
        + "\n".join(
            [
                "# Vault Schema",
                "",
                f"- Protocol: `{protocol_path}`",
                "",
                "## Layer rules",
                "",
                "- `raw/` anchors immutable source inputs and manifests only. It must not become a second writable knowledge surface.",
                "- `wiki/` is the Obsidian-compatible L1 compiled layer. Keep lowercase filenames, frontmatter, and wikilinks.",
                "- `output/` stores derived query products. Valuable output may flow back into wiki pages only through explicit receipts.",
                "",
                "## Page types",
                "",
                "- `home.md` -> topic overview and navigation page",
                "- `source-intake.md` -> assumptions, regimes, reading depth, and method specificity",
                "- `open-questions.md` -> ambiguity and uncertainty page",
                "- `runtime-bridge.md` -> compatibility/runtime bridge page",
                f"- `{concept_graph_index_path}` -> concept-graph index page plus community folders of node notes",
                "",
                "## Link rules",
                "",
                f"- Use {_wiki_link('home', 'Home')} as the local root page.",
                f"- Link sibling wiki pages with wikilinks such as {_wiki_link('source-intake', 'Source Intake')}.",
                f"- Link concept-graph notes with wikilinks such as {_wiki_link('concept-graph/index', 'Concept Graph')}.",
                "- Link output and runtime files with explicit relative paths when they live outside `wiki/`.",
                "",
                "## Flowback rule",
                "",
                "Output-derived updates only count as synced when `output/flowback.jsonl` records the target page, source output, and sync reason.",
                "",
            ]
        )
        + "\n"
    )


def _render_wiki_home_markdown(
    *,
    topic_slug: str,
    title: str,
    question: str,
    status: str,
    research_mode: str,
    source_count: int,
    concept_graph_index_path: str,
    output_digest_note_path: str,
    flowback_note_path: str,
    updated_at: str,
    updated_by: str,
) -> str:
    return (
        _frontmatter(
            page_type="topic_home",
            topic_slug=topic_slug,
            authority_level="non_authoritative_compiled_l1",
            updated_at=updated_at,
            updated_by=updated_by,
        )
        + "\n"
        + "\n".join(
            [
                f"# {title}",
                "",
                "## Read path",
                "",
                f"- {_wiki_link('schema', 'Vault Schema')}",
                f"- {_wiki_link('source-intake', 'Source Intake')}",
                f"- {_wiki_link('open-questions', 'Open Questions')}",
                f"- {_wiki_link('runtime-bridge', 'Runtime Bridge')}",
                f"- Concept Graph: `{concept_graph_index_path}`",
                f"- Output digest: `{output_digest_note_path}`",
                f"- Flowback log: `{flowback_note_path}`",
                "",
                "## Current question",
                "",
                question or "(missing)",
                "",
                "## Status",
                "",
                f"- Topic slug: `{topic_slug}`",
                f"- Contract status: `{status or 'missing'}`",
                f"- Research mode: `{research_mode or 'missing'}`",
                f"- Source count: `{source_count}`",
                "",
            ]
        )
        + "\n"
    )


def _render_source_intake_markdown(
    *,
    topic_slug: str,
    l1_source_intake: dict[str, Any],
    updated_at: str,
    updated_by: str,
) -> str:
    lines = [
        _frontmatter(
            page_type="source_intake",
            topic_slug=topic_slug,
            authority_level="non_authoritative_compiled_l1",
            updated_at=updated_at,
            updated_by=updated_by,
        ),
        f"# {_wiki_link('home', 'Home')} / Source Intake",
        "",
        "## Assumptions",
        "",
    ]
    for row in l1_source_intake.get("assumption_rows") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('source_id') or '(missing)'}` [{row.get('reading_depth') or 'skim'}]: {row.get('assumption') or '(missing)'}"
            )
        else:
            lines.append(f"- {row}")
    lines.extend(["", "## Regimes", ""])
    for row in l1_source_intake.get("regime_rows") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('source_id') or '(missing)'}` [{row.get('reading_depth') or 'skim'}]: {row.get('regime') or '(missing)'}"
            )
        else:
            lines.append(f"- {row}")
    lines.extend(["", "## Reading depth", ""])
    for row in l1_source_intake.get("reading_depth_rows") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('source_id') or '(missing)'}` => `{row.get('reading_depth') or 'skim'}` basis=`{row.get('basis') or 'summary_only'}`"
            )
        else:
            lines.append(f"- {row}")
    lines.extend(["", "## Method specificity", ""])
    for row in l1_source_intake.get("method_specificity_rows") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('source_id') or '(missing)'}`: `{row.get('method_family') or '(missing)'}` / `{row.get('specificity_tier') or '(missing)'}`"
            )
        else:
            lines.append(f"- {row}")
    lines.extend(["", "## Contradictions", ""])
    for row in l1_contradiction_summary_lines(l1_source_intake) or ["(none)"]:
        lines.append(f"- {row}")
    lines.extend(["", "## Concept graph", ""])
    concept_graph = l1_source_intake.get("concept_graph") or {}
    lines.append(
        f"- nodes=`{len(concept_graph.get('nodes') or [])}` edges=`{len(concept_graph.get('edges') or [])}` "
        f"hyperedges=`{len(concept_graph.get('hyperedges') or [])}` communities=`{len(concept_graph.get('communities') or [])}` "
        f"god-nodes=`{len(concept_graph.get('god_nodes') or [])}`"
    )
    for row in (concept_graph.get("god_nodes") or [])[:4]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('source_id') or '(missing)'}` foundation: {row.get('label') or row.get('node_id') or '(missing)'}"
            )
    return "\n".join(lines).rstrip() + "\n"


def _render_open_questions_markdown(
    *,
    topic_slug: str,
    open_ambiguities: list[str],
    uncertainty_markers: list[str],
    updated_at: str,
    updated_by: str,
) -> str:
    lines = [
        _frontmatter(
            page_type="open_questions",
            topic_slug=topic_slug,
            authority_level="non_authoritative_compiled_l1",
            updated_at=updated_at,
            updated_by=updated_by,
        ),
        f"# {_wiki_link('home', 'Home')} / Open Questions",
        "",
        "## Open ambiguities",
        "",
    ]
    for item in open_ambiguities or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Uncertainty markers", ""])
    for item in uncertainty_markers or ["(none)"]:
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def _render_runtime_bridge_markdown(
    *,
    topic_slug: str,
    compatibility_refs: list[dict[str, str]],
    topic_dashboard_path: str,
    updated_at: str,
    updated_by: str,
) -> str:
    lines = [
        _frontmatter(
            page_type="runtime_bridge",
            topic_slug=topic_slug,
            authority_level="non_authoritative_compiled_l1",
            updated_at=updated_at,
            updated_by=updated_by,
        ),
        f"# {_wiki_link('home', 'Home')} / Runtime Bridge",
        "",
        "## Compatibility surfaces",
        "",
    ]
    for row in compatibility_refs:
        lines.append(
            f"- `{row.get('kind') or '(missing)'}` status=`{row.get('status') or 'missing'}` path=`{row.get('path') or '(missing)'}`"
        )
    lines.extend(
        [
            "",
            "## Primary runtime projection",
            "",
            f"- Topic dashboard: `{topic_dashboard_path}`",
            "- The runtime bridge preserves legacy/control surfaces instead of replacing them.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _render_output_digest_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# L1 Output Digest",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Contract status: `{payload.get('status') or '(missing)'}`",
        f"- Research mode: `{payload.get('research_mode') or '(missing)'}`",
        f"- Source count: `{payload.get('source_count') or 0}`",
        f"- Flowback targets: `{len(payload.get('flowback_targets') or [])}`",
        "",
        "## Query focus",
        "",
        payload.get("question") or "(missing)",
        "",
        "## Assumption highlights",
        "",
    ]
    for item in payload.get("assumption_highlights") or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Regime highlights", ""])
    for item in payload.get("regime_highlights") or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Open questions", ""])
    for item in payload.get("open_questions") or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Flowback targets", ""])
    for row in payload.get("flowback_targets") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('target_page') or '(missing)'}` <- `{row.get('source_output_path') or '(missing)'}` ({row.get('reason') or '(missing)'})"
            )
        else:
            lines.append(f"- {row}")
    lines.extend(["", "## Source intelligence", "", payload.get("source_intelligence_summary") or "(missing)", ""])
    return "\n".join(lines).rstrip() + "\n"


def _render_flowback_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# L1 Flowback Log",
        "",
        "## Entries",
        "",
    ]
    if not rows:
        lines.append("- `(none)`")
    for row in rows:
        lines.append(
            f"- `{row.get('target_page') or '(missing)'}` status=`{row.get('status') or 'missing'}` source=`{row.get('source_output_path') or '(missing)'}`"
        )
        lines.append(f"  - reason: {row.get('reason') or '(missing)'}")
        lines.append(f"  - preview: {row.get('content_preview') or '(none)'}")
    return "\n".join(lines).rstrip() + "\n"


def _render_vault_manifest_markdown(payload: dict[str, Any]) -> str:
    raw = payload.get("raw") or {}
    wiki = payload.get("wiki") or {}
    output = payload.get("output") or {}
    lines = [
        "# L1 Vault Manifest",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Root path: `{payload.get('root_path') or '(missing)'}`",
        f"- Protocol path: `{payload.get('protocol_path') or '(missing)'}`",
        "",
        "## Raw layer",
        "",
        f"- Manifest JSON: `{raw.get('manifest_path') or '(missing)'}`",
        f"- Manifest note: `{raw.get('note_path') or '(missing)'}`",
        f"- Source count: `{raw.get('source_count') or 0}`",
        "",
        "## Wiki layer",
        "",
        f"- Schema page: `{wiki.get('schema_path') or '(missing)'}`",
        f"- Home page: `{wiki.get('home_page_path') or '(missing)'}`",
        f"- Page count: `{wiki.get('page_count') or 0}`",
        "",
        "## Output layer",
        "",
        f"- Digest JSON: `{output.get('digest_path') or '(missing)'}`",
        f"- Digest note: `{output.get('digest_note_path') or '(missing)'}`",
        f"- Flowback log: `{output.get('flowback_log_path') or '(missing)'}`",
        f"- Flowback entries: `{output.get('flowback_entry_count') or 0}`",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def materialize_l1_vault(
    *,
    kernel_root: Path,
    topic_slug: str,
    title: str,
    research_contract: dict[str, Any],
    source_rows: list[dict[str, Any]],
    source_intelligence: dict[str, Any],
    research_contract_json_path: Path,
    research_contract_note_path: Path,
    control_note_path: Path,
    operator_console_path: Path,
    topic_dashboard_path: Path,
    updated_by: str,
    relativize: Callable[[Path], str],
) -> dict[str, Any]:
    updated_at = now_iso()
    vault_root = _vault_root(kernel_root, topic_slug)
    raw_root = vault_root / "raw"
    wiki_root = vault_root / "wiki"
    output_root = vault_root / "output"
    protocol_path = "intake/L1_VAULT_PROTOCOL.md"

    raw_manifest_json_path = raw_root / "source-manifest.json"
    raw_manifest_note_path = raw_root / "source-manifest.md"
    wiki_schema_path = wiki_root / "schema.md"
    wiki_home_path = wiki_root / "home.md"
    wiki_source_intake_path = wiki_root / "source-intake.md"
    wiki_open_questions_path = wiki_root / "open-questions.md"
    wiki_runtime_bridge_path = wiki_root / "runtime-bridge.md"
    output_digest_path = output_root / "current-query.json"
    output_digest_note_path = output_root / "current-query.md"
    flowback_log_path = output_root / "flowback.jsonl"
    flowback_note_path = output_root / "flowback.md"
    manifest_json_path = vault_root / "vault_manifest.json"
    manifest_note_path = vault_root / "vault_manifest.md"
    concept_graph_export = materialize_obsidian_concept_graph_export(
        kernel_root=kernel_root,
        topic_slug=topic_slug,
        source_rows=source_rows,
        l1_source_intake=research_contract.get("l1_source_intake") or {},
        updated_by=updated_by,
        relativize=relativize,
    )
    concept_graph_export_payload = concept_graph_export["payload"]

    raw_sources = _build_raw_sources(
        kernel_root=kernel_root,
        topic_slug=topic_slug,
        source_rows=source_rows,
        relativize=relativize,
    )
    raw_manifest_payload = {
        "kind": "l1_raw_source_manifest",
        "manifest_version": 1,
        "topic_slug": topic_slug,
        "source_count": len(raw_sources),
        "source_index_path": relativize(_source_topic_root(kernel_root, topic_slug) / "source_index.jsonl"),
        "sources": raw_sources,
        "updated_at": updated_at,
        "updated_by": updated_by,
    }
    write_json(raw_manifest_json_path, raw_manifest_payload)
    write_text(raw_manifest_note_path, _render_raw_manifest_markdown(raw_manifest_payload))

    compatibility_refs = [
        {
            "kind": "research_question_contract_json",
            "path": relativize(research_contract_json_path),
            "status": "available",
        },
        {
            "kind": "research_question_contract_note",
            "path": relativize(research_contract_note_path),
            "status": "available",
        },
        {
            "kind": "control_note",
            "path": relativize(control_note_path),
            "status": "available" if control_note_path.exists() else "expected_but_missing",
        },
        {
            "kind": "operator_console",
            "path": relativize(operator_console_path),
            "status": "available" if operator_console_path.exists() else "expected_but_missing",
        },
    ]

    flowback_entries = [
        {
            "flowback_id": f"l1_flowback:{topic_slug}:home",
            "target_page": relativize(wiki_home_path),
            "source_output_path": relativize(output_digest_note_path),
            "status": "applied",
            "reason": "Refresh the current question, status, and local read path from the output digest.",
            "content_preview": str(research_contract.get("question") or "").strip(),
        },
        {
            "flowback_id": f"l1_flowback:{topic_slug}:source-intake",
            "target_page": relativize(wiki_source_intake_path),
            "source_output_path": relativize(output_digest_note_path),
            "status": "applied",
            "reason": "Sync source-backed assumptions, regimes, reading depth, and method specificity into the wiki intake page.",
            "content_preview": "; ".join(
                _dedupe_strings(
                    [
                        str(row.get("assumption") or "").strip()
                        for row in (research_contract.get("l1_source_intake") or {}).get("assumption_rows") or []
                    ]
                )[:2]
            ),
        },
        {
            "flowback_id": f"l1_flowback:{topic_slug}:open-questions",
            "target_page": relativize(wiki_open_questions_path),
            "source_output_path": relativize(output_digest_note_path),
            "status": "applied",
            "reason": "Sync open ambiguities and uncertainty markers back into the wiki question page.",
            "content_preview": "; ".join((research_contract.get("open_ambiguities") or [])[:2]),
        },
        {
            "flowback_id": f"l1_flowback:{topic_slug}:runtime-bridge",
            "target_page": relativize(wiki_runtime_bridge_path),
            "source_output_path": relativize(output_digest_note_path),
            "status": "applied",
            "reason": "Sync compatibility/runtime paths so the vault keeps the legacy bridge visible.",
            "content_preview": "; ".join(row["path"] for row in compatibility_refs[:3]),
        },
    ]

    output_digest_payload = {
        "kind": "l1_vault_output_digest",
        "digest_version": 1,
        "topic_slug": topic_slug,
        "title": title,
        "status": str(research_contract.get("status") or "").strip(),
        "research_mode": str(research_contract.get("research_mode") or "").strip(),
        "question": str(research_contract.get("question") or "").strip(),
        "source_count": int(((research_contract.get("l1_source_intake") or {}).get("source_count")) or 0),
        "assumption_highlights": _dedupe_strings(
            [
                str(row.get("assumption") or "").strip()
                for row in (research_contract.get("l1_source_intake") or {}).get("assumption_rows") or []
                if str(row.get("assumption") or "").strip()
            ]
        )[:5],
        "regime_highlights": _dedupe_strings(
            [
                str(row.get("regime") or "").strip()
                for row in (research_contract.get("l1_source_intake") or {}).get("regime_rows") or []
                if str(row.get("regime") or "").strip()
            ]
        )[:5],
        "open_questions": _dedupe_strings([str(item) for item in research_contract.get("open_ambiguities") or []])[:6],
        "source_intelligence_summary": str(source_intelligence.get("summary") or "").strip(),
        "compatibility_refs": compatibility_refs,
        "flowback_targets": flowback_entries,
        "updated_at": updated_at,
        "updated_by": updated_by,
    }
    write_json(output_digest_path, output_digest_payload)
    write_text(output_digest_note_path, _render_output_digest_markdown(output_digest_payload))
    write_jsonl(flowback_log_path, flowback_entries)
    write_text(flowback_note_path, _render_flowback_markdown(flowback_entries))

    write_text(
        wiki_schema_path,
        _render_wiki_schema_markdown(
            topic_slug=topic_slug,
            protocol_path=protocol_path,
            concept_graph_index_path=str(concept_graph_export_payload.get("index_path") or "concept-graph/index.md"),
            updated_at=updated_at,
            updated_by=updated_by,
        ),
    )
    write_text(
        wiki_home_path,
        _render_wiki_home_markdown(
            topic_slug=topic_slug,
            title=title,
            question=str(research_contract.get("question") or "").strip(),
            status=str(research_contract.get("status") or "").strip(),
            research_mode=str(research_contract.get("research_mode") or "").strip(),
            source_count=int(((research_contract.get("l1_source_intake") or {}).get("source_count")) or 0),
            concept_graph_index_path=str(concept_graph_export_payload.get("index_path") or "concept-graph/index.md"),
            output_digest_note_path="../output/current-query.md",
            flowback_note_path="../output/flowback.md",
            updated_at=updated_at,
            updated_by=updated_by,
        ),
    )
    write_text(
        wiki_source_intake_path,
        _render_source_intake_markdown(
            topic_slug=topic_slug,
            l1_source_intake=research_contract.get("l1_source_intake") or {},
            updated_at=updated_at,
            updated_by=updated_by,
        ),
    )
    write_text(
        wiki_open_questions_path,
        _render_open_questions_markdown(
            topic_slug=topic_slug,
            open_ambiguities=[str(item) for item in research_contract.get("open_ambiguities") or []],
            uncertainty_markers=[str(item) for item in research_contract.get("uncertainty_markers") or []],
            updated_at=updated_at,
            updated_by=updated_by,
        ),
    )
    write_text(
        wiki_runtime_bridge_path,
        _render_runtime_bridge_markdown(
            topic_slug=topic_slug,
            compatibility_refs=compatibility_refs,
            topic_dashboard_path=relativize(topic_dashboard_path),
            updated_at=updated_at,
            updated_by=updated_by,
        ),
    )

    manifest_payload = {
        "vault_version": 1,
        "status": "materialized",
        "topic_slug": topic_slug,
        "title": title,
        "authority_level": "non_authoritative_compiled_l1",
        "protocol_path": protocol_path,
        "root_path": relativize(vault_root),
        "raw": {
            "manifest_path": relativize(raw_manifest_json_path),
            "note_path": relativize(raw_manifest_note_path),
            "source_count": len(raw_sources),
        },
        "wiki": {
            "schema_path": relativize(wiki_schema_path),
            "home_page_path": relativize(wiki_home_path),
            "page_count": 4 + int((concept_graph_export_payload.get("summary") or {}).get("page_count") or 0),
            "page_paths": [
                relativize(wiki_home_path),
                relativize(wiki_source_intake_path),
                relativize(wiki_open_questions_path),
                relativize(wiki_runtime_bridge_path),
                str(concept_graph_export_payload.get("index_path") or ""),
                *list(concept_graph_export_payload.get("community_page_paths") or []),
                *list(concept_graph_export_payload.get("note_paths") or []),
            ],
            "concept_graph_export": concept_graph_export_payload,
        },
        "output": {
            "digest_path": relativize(output_digest_path),
            "digest_note_path": relativize(output_digest_note_path),
            "flowback_log_path": relativize(flowback_log_path),
            "flowback_note_path": relativize(flowback_note_path),
            "flowback_entry_count": len(flowback_entries),
        },
        "compatibility_refs": compatibility_refs,
        "updated_at": updated_at,
        "updated_by": updated_by,
    }
    write_json(manifest_json_path, manifest_payload)
    write_text(manifest_note_path, _render_vault_manifest_markdown(manifest_payload))

    return {
        "payload": manifest_payload,
        "path": str(manifest_json_path),
        "note_path": str(manifest_note_path),
        "raw_manifest_path": str(raw_manifest_json_path),
        "raw_manifest_note_path": str(raw_manifest_note_path),
        "wiki_home_path": str(wiki_home_path),
        "wiki_schema_path": str(wiki_schema_path),
        "wiki_source_intake_path": str(wiki_source_intake_path),
        "wiki_open_questions_path": str(wiki_open_questions_path),
        "wiki_runtime_bridge_path": str(wiki_runtime_bridge_path),
        "output_digest_path": str(output_digest_path),
        "output_digest_note_path": str(output_digest_note_path),
        "flowback_log_path": str(flowback_log_path),
        "flowback_note_path": str(flowback_note_path),
    }
