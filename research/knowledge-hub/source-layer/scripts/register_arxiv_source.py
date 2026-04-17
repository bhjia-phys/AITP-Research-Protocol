#!/usr/bin/env python3
"""Register an arXiv paper into Layer 0 and create a Layer 1 intake projection."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import tarfile
import textwrap
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}
PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[4]

if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from knowledge_hub.source_intelligence import infer_source_relevance


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "arxiv-paper"


def bounded_slugify(text: str, *, max_length: int = 24) -> str:
    slug = slugify(text)
    if len(slug) <= max_length:
        return slug
    digest = hashlib.sha1(slug.encode("utf-8")).hexdigest()[:8]
    head = slug[: max(8, max_length - len(digest) - 1)].rstrip("-")
    return f"{head}-{digest}"


def short_summary(text: str, limit: int = 260) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 3].rstrip() + "..."


def fetch_url(url: str, timeout: int = 60) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read()


def fetch_metadata(arxiv_id: str) -> dict:
    query = urllib.parse.urlencode(
        {"search_query": f"id:{arxiv_id}", "start": 0, "max_results": 1}
    )
    url = f"https://export.arxiv.org/api/query?{query}"
    payload = fetch_url(url).decode("utf-8")
    root = ET.fromstring(payload)
    entry = root.find("atom:entry", ATOM_NS)
    if entry is None:
        raise SystemExit(f"No arXiv entry found for {arxiv_id}")

    title = entry.findtext("atom:title", default="", namespaces=ATOM_NS).strip()
    summary = entry.findtext("atom:summary", default="", namespaces=ATOM_NS).strip()
    published = entry.findtext("atom:published", default="", namespaces=ATOM_NS).strip()
    updated = entry.findtext("atom:updated", default="", namespaces=ATOM_NS).strip()
    identifier = entry.findtext("atom:id", default="", namespaces=ATOM_NS).strip()
    authors = [
        author.findtext("atom:name", default="", namespaces=ATOM_NS).strip()
        for author in entry.findall("atom:author", ATOM_NS)
    ]
    pdf_url = ""
    for link in entry.findall("atom:link", ATOM_NS):
        if link.attrib.get("title") == "pdf":
            pdf_url = link.attrib.get("href", "")
            break
    versioned_id = identifier.rsplit("/", 1)[-1] if identifier else arxiv_id
    base_id = re.sub(r"v\d+$", "", versioned_id)
    return {
        "title": title,
        "summary": summary,
        "published": published,
        "updated": updated,
        "identifier": identifier,
        "versioned_id": versioned_id,
        "base_id": base_id,
        "authors": authors,
        "pdf_url": pdf_url or f"https://arxiv.org/pdf/{base_id}.pdf",
        "abs_url": identifier or f"https://arxiv.org/abs/{versioned_id}",
        "source_url": f"https://arxiv.org/e-print/{versioned_id}",
    }


def normalize_authors(values: list[Any] | None) -> list[str]:
    authors: list[str] = []
    for value in values or []:
        if isinstance(value, dict):
            candidate = str(
                value.get("name")
                or value.get("full_name")
                or value.get("author")
                or ""
            ).strip()
        else:
            candidate = str(value).strip()
        if candidate:
            authors.append(candidate)
    return authors


def build_metadata_override(arxiv_id: str, metadata_override: dict[str, Any]) -> dict[str, Any]:
    versioned_id = str(
        metadata_override.get("versioned_id")
        or metadata_override.get("arxiv_id")
        or arxiv_id
    ).strip()
    if not versioned_id:
        raise ValueError("Metadata override must include a non-empty arXiv id.")
    base_id = str(metadata_override.get("base_id") or re.sub(r"v\d+$", "", versioned_id)).strip()
    identifier = str(
        metadata_override.get("identifier")
        or metadata_override.get("abs_url")
        or f"https://arxiv.org/abs/{versioned_id}"
    ).strip()
    title = str(metadata_override.get("title") or "").strip()
    if not title:
        raise ValueError("Metadata override must include a non-empty title.")
    summary = str(metadata_override.get("summary") or "").strip()
    published = str(metadata_override.get("published") or "").strip()
    updated = str(metadata_override.get("updated") or published).strip()
    authors = normalize_authors(metadata_override.get("authors"))
    pdf_url = str(
        metadata_override.get("pdf_url")
        or f"https://arxiv.org/pdf/{base_id}.pdf"
    ).strip()
    abs_url = str(metadata_override.get("abs_url") or identifier).strip()
    source_url = str(
        metadata_override.get("source_url")
        or f"https://arxiv.org/e-print/{versioned_id}"
    ).strip()
    return {
        "title": title,
        "summary": summary,
        "published": published,
        "updated": updated,
        "identifier": identifier,
        "versioned_id": versioned_id,
        "base_id": base_id,
        "authors": authors,
        "pdf_url": pdf_url,
        "abs_url": abs_url,
        "source_url": source_url,
    }


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def load_enrich_module(script_path: Path):
    spec = importlib.util.spec_from_file_location("enrich_with_deepxiv_module", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load enrichment module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_graph_module(script_path: Path):
    spec = importlib.util.spec_from_file_location("build_concept_graph_module", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load concept-graph module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_source_slug(metadata: dict[str, Any]) -> str:
    base_id = bounded_slugify(
        str(metadata.get("base_id") or metadata.get("versioned_id") or ""),
        max_length=20,
    )
    digest_input = "|".join(
        [
            str(metadata.get("title") or ""),
            str(metadata.get("versioned_id") or ""),
            str(metadata.get("abs_url") or ""),
        ]
    )
    digest = hashlib.sha1(digest_input.encode("utf-8")).hexdigest()[:8]
    if base_id:
        return f"paper-{base_id}-{digest}"
    return f"paper-{digest}"


def sync_runtime_status_after_registration(
    *,
    knowledge_root: Path,
    topic_slug: str,
    source_id: str,
    updated_by: str,
) -> dict[str, Any]:
    topic_state_path = knowledge_root / "topics" / topic_slug / "runtime" / "topic_state.json"
    if not topic_state_path.exists():
        topic_state_path = knowledge_root / "runtime" / "topics" / topic_slug / "topic_state.json"
    if not topic_state_path.exists():
        return {
            "status": "skipped",
            "reason": "runtime_topic_missing",
            "runtime_protocol_path": "",
            "runtime_protocol_note_path": "",
            "source_count": 0,
            "source_intelligence_summary": "",
        }

    if str(PACKAGE_ROOT) not in sys.path:
        sys.path.insert(0, str(PACKAGE_ROOT))

    from knowledge_hub.aitp_service import AITPService

    service = AITPService(kernel_root=knowledge_root, repo_root=REPO_ROOT)
    human_request = f"Registered source {source_id}; refresh runtime status surfaces."
    service.refresh_runtime_context(
        topic_slug=topic_slug,
        updated_by=updated_by,
        human_request=human_request,
    )
    service.orchestrate(
        topic_slug=topic_slug,
        updated_by=updated_by,
        human_request=human_request,
    )
    payload = service.refresh_runtime_context(
        topic_slug=topic_slug,
        updated_by=updated_by,
        human_request=human_request,
    )
    current_topic_payload = load_json(knowledge_root / "runtime" / "current_topic.json") or {}
    if str(current_topic_payload.get("topic_slug") or "").strip() == topic_slug:
        service.remember_current_topic(
            topic_slug=topic_slug,
            updated_by=updated_by,
            source="source-registration-sync",
            human_request=human_request,
        )
    else:
        service._sync_active_topics_registry(
            topic_slug=topic_slug,
            updated_by=updated_by,
            source="source-registration-sync",
            human_request=human_request,
            focus=False,
        )
    return {
        "status": "refreshed",
        "reason": "runtime_topic_present",
        "runtime_protocol_path": str(payload["runtime_protocol_path"]),
        "runtime_protocol_note_path": str(payload["runtime_protocol_note_path"]),
        "source_count": int(
            (
                ((payload.get("topic_synopsis") or {}).get("l1_source_intake") or {}).get(
                    "source_count"
                )
                or 0
            )
        ),
        "source_intelligence_summary": str(
            (payload.get("source_intelligence") or {}).get("summary") or ""
        ),
    }


def ensure_topic_manifest(topic_root: Path, topic_slug: str, created_at: str) -> None:
    topic_json = topic_root / "topic.json"
    if not topic_json.exists():
        write_json(
            topic_json,
            {
                "topic_slug": topic_slug,
                "title": topic_slug.replace("-", " ").title(),
                "status": "source_active",
                "created_at": created_at,
            },
        )


def ensure_intake_manifest(topic_root: Path, topic_slug: str, created_at: str) -> None:
    topic_json = topic_root / "topic.json"
    if not topic_json.exists():
        write_json(
            topic_json,
            {
                "topic_slug": topic_slug,
                "title": topic_slug.replace("-", " ").title(),
                "status": "intake_active",
                "created_at": created_at,
            },
        )

    status_json = topic_root / "status.json"
    if not status_json.exists():
        write_json(
            status_json,
            {"stage": "L1_active", "next_stage": "L1", "last_updated": created_at},
        )


def build_source_payload(
    metadata: dict,
    topic_slug: str,
    source_json_rel: str,
    snapshot_rel: str,
    bundle_rel: str,
    extract_rel: str,
    registered_by: str,
    acquired_at: str,
) -> dict:
    relevance_tier, _, role_labels = infer_source_relevance(
        source_type="paper",
        title=metadata["title"],
        summary=short_summary(metadata["summary"]),
        provenance={
            "arxiv_id": metadata["versioned_id"],
            "authors": metadata["authors"],
            "published": metadata["published"],
            "updated": metadata["updated"],
            "abs_url": metadata["abs_url"],
            "pdf_url": metadata["pdf_url"],
            "source_url": metadata["source_url"],
            "relevance_tier": metadata.get("relevance_tier"),
            "role_labels": metadata.get("role_labels"),
        },
        canonical_source_id="",
        explicit_relevance_tier=str(metadata.get("relevance_tier") or ""),
        explicit_role_labels=metadata.get("role_labels") if isinstance(metadata.get("role_labels"), list) else [],
    )
    return {
        "source_id": f"paper:{slugify(metadata['title'])}-{metadata['base_id'].replace('.', '-')}",
        "source_type": "paper",
        "title": metadata["title"],
        "topic_slug": topic_slug,
        "provenance": {
            "arxiv_id": metadata["versioned_id"],
            "authors": metadata["authors"],
            "published": metadata["published"],
            "updated": metadata["updated"],
            "abs_url": metadata["abs_url"],
            "pdf_url": metadata["pdf_url"],
            "source_url": metadata["source_url"],
        },
        "locator": {
            "local_path": source_json_rel,
            "snapshot_path": snapshot_rel,
            "preferred_open_sequence": [
                "local_extracted_tex",
                "arxiv_source_tex",
                "arxiv_html",
                "arxiv_pdf",
            ],
            "downloaded_source_bundle": bundle_rel,
            "extracted_source_dir": extract_rel,
        },
        "acquired_at": acquired_at,
        "registered_by": registered_by,
        "summary": short_summary(metadata["summary"]),
        "relevance_tier": relevance_tier,
        "role_labels": role_labels,
    }


def append_unique(rows: list[dict], new_row: dict, key_fields: tuple[str, ...]) -> list[dict]:
    filtered = []
    for row in rows:
        if all(row.get(field) == new_row.get(field) for field in key_fields):
            continue
        filtered.append(row)
    filtered.append(new_row)
    return filtered


def build_projection_snapshot(
    topic_slug: str,
    source_id: str,
    layer0_source_json: str,
    layer0_snapshot: str,
    acquired_at: str,
) -> str:
    return textwrap.dedent(
        f"""\
        # Layer 1 source projection

        Topic: `{topic_slug}`
        Source id: `{source_id}`
        Projection created: `{acquired_at}`

        Layer 0 source of truth:
        - `{layer0_source_json}`

        Layer 0 snapshot:
        - `{layer0_snapshot}`

        This intake-side snapshot is a projection only.
        Use the Layer 0 paths above for durable source reopening.
        """
    )


def build_layer0_snapshot(
    metadata: dict,
    topic_slug: str,
    source_id: str,
    download_status: str,
    extraction_status: str,
    bundle_rel: str,
    extract_rel: str,
    download_error: str,
) -> str:
    return textwrap.dedent(
        f"""\
        # {metadata["title"]}

        Source id: `{source_id}`
        arXiv id: `{metadata["versioned_id"]}`
        Topic: `{topic_slug}`

        ## Access priority
        1. local extracted TeX source
        2. arXiv source package
        3. arXiv HTML
        4. arXiv PDF

        ## Metadata
        - Authors: {", ".join(metadata["authors"]) if metadata["authors"] else "(unknown)"}
        - Published: {metadata["published"] or "(unknown)"}
        - Updated: {metadata["updated"] or "(unknown)"}
        - abs: {metadata["abs_url"]}
        - pdf: {metadata["pdf_url"]}
        - source package: {metadata["source_url"]}

        ## Acquisition status
        - Source bundle download: {download_status}
        - Source extraction: {extraction_status}
        - Local bundle: {bundle_rel or "(not present)"}
        - Local extracted dir: {extract_rel or "(not present)"}
        - Error note: {download_error or "(none)"}

        ## Abstract
        {short_summary(metadata["summary"], limit=1200)}
        """
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--knowledge-root")
    parser.add_argument("--topic-slug", required=True)
    parser.add_argument("--arxiv-id", required=True)
    parser.add_argument("--registered-by", default="codex")
    download_group = parser.add_mutually_exclusive_group()
    download_group.add_argument("--download-source", dest="download_source", action="store_true")
    download_group.add_argument("--metadata-only", dest="download_source", action="store_false")
    parser.set_defaults(download_source=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-intake-projection", action="store_true")
    parser.add_argument("--skip-enrichment", action="store_true")
    parser.add_argument("--skip-graph-build", action="store_true")
    parser.add_argument("--metadata-json")
    parser.add_argument("--enrichment-json")
    parser.add_argument("--graph-json")
    parser.add_argument("--json", action="store_true")
    return parser


def register_arxiv_source(
    *,
    knowledge_root: Path,
    topic_slug: str,
    arxiv_id: str,
    registered_by: str = "codex",
    download_source: bool = True,
    force: bool = False,
    skip_intake_projection: bool = False,
    metadata_override: dict[str, Any] | None = None,
    skip_enrichment: bool = False,
    enrichment_override: dict[str, Any] | None = None,
    skip_graph_build: bool = False,
    graph_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    del force  # Reserved for future parity with the CLI surface.
    metadata = (
        build_metadata_override(arxiv_id, metadata_override)
        if metadata_override is not None
        else fetch_metadata(arxiv_id)
    )
    source_slug = build_source_slug(metadata)

    source_layer_topic_root = knowledge_root / "topics" / topic_slug / "L0"
    layer0_source_root = source_layer_topic_root / "sources" / source_slug
    layer0_source_root.mkdir(parents=True, exist_ok=True)

    bundle_path = layer0_source_root / "source.tar"
    extract_dir = layer0_source_root / "tex-src"
    download_status = "not_requested"
    extraction_status = "not_requested"
    download_error = ""

    if download_source:
        try:
            payload = fetch_url(metadata["source_url"])
            if payload[:2] == b"\x1f\x8b":
                bundle_path = layer0_source_root / "source.tar.gz"
            bundle_path.write_bytes(payload)
            download_status = "downloaded"
            try:
                extract_dir.mkdir(exist_ok=True)
                with tarfile.open(bundle_path, "r:*") as archive:
                    try:
                        archive.extractall(path=extract_dir, filter="data")
                    except TypeError:
                        archive.extractall(path=extract_dir)
                extraction_status = "extracted"
            except tarfile.TarError as exc:
                extraction_status = "failed"
                download_error = f"downloaded source bundle but extraction failed: {exc}"
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            download_status = "failed"
            extraction_status = "skipped"
            download_error = str(exc)

    acquired_at = now_iso()
    ensure_topic_manifest(source_layer_topic_root, topic_slug, acquired_at)

    layer0_source_rel = layer0_source_root.relative_to(knowledge_root).as_posix()
    layer0_source_json_rel = f"{layer0_source_rel}/source.json"
    layer0_snapshot_rel = f"{layer0_source_rel}/snapshot.md"
    bundle_rel = bundle_path.relative_to(knowledge_root).as_posix() if bundle_path.exists() else ""
    extract_rel = extract_dir.relative_to(knowledge_root).as_posix() if extract_dir.exists() else ""

    source_payload = build_source_payload(
        metadata=metadata,
        topic_slug=topic_slug,
        source_json_rel=layer0_source_json_rel,
        snapshot_rel=layer0_snapshot_rel,
        bundle_rel=bundle_rel,
        extract_rel=extract_rel,
        registered_by=registered_by,
        acquired_at=acquired_at,
    )
    source_id = source_payload["source_id"]

    write_json(layer0_source_root / "source.json", source_payload)
    (layer0_source_root / "snapshot.md").write_text(
        build_layer0_snapshot(
            metadata=metadata,
            topic_slug=topic_slug,
            source_id=source_id,
            download_status=download_status,
            extraction_status=extraction_status,
            bundle_rel=bundle_rel,
            extract_rel=extract_rel,
            download_error=download_error,
        ),
        encoding="utf-8",
    )

    topic_index_path = source_layer_topic_root / "source_index.jsonl"
    write_jsonl(
        topic_index_path,
        append_unique(load_jsonl(topic_index_path), source_payload, ("source_id",)),
    )

    global_index_path = knowledge_root / "source-layer" / "global_index.jsonl"
    write_jsonl(
        global_index_path,
        append_unique(
            load_jsonl(global_index_path),
            {
                "source_id": source_id,
                "topic_slug": topic_slug,
                "source_type": source_payload["source_type"],
                "title": source_payload["title"],
                "local_path": layer0_source_json_rel,
                "acquired_at": acquired_at,
            },
            ("source_id", "topic_slug"),
        ),
    )

    intake_projection_root: Path | None = None
    if not skip_intake_projection:
        intake_topic_root = knowledge_root / "topics" / topic_slug / "L1"
        intake_projection_root = intake_topic_root / "sources" / source_slug
        intake_projection_root.mkdir(parents=True, exist_ok=True)
        ensure_intake_manifest(intake_topic_root, topic_slug, acquired_at)
        write_json(intake_projection_root / "source.json", source_payload)
        (intake_projection_root / "snapshot.md").write_text(
            build_projection_snapshot(
                topic_slug=topic_slug,
                source_id=source_id,
                layer0_source_json=layer0_source_json_rel,
                layer0_snapshot=layer0_snapshot_rel,
                acquired_at=acquired_at,
            ),
            encoding="utf-8",
        )
        intake_index_path = intake_topic_root / "source_index.jsonl"
        write_jsonl(
            intake_index_path,
            append_unique(load_jsonl(intake_index_path), source_payload, ("source_id",)),
        )
        status_json = intake_topic_root / "status.json"
        status_payload = load_json(status_json)
        if status_payload is not None:
            status_payload["last_updated"] = acquired_at
            write_json(status_json, status_payload)

    enrichment_status = "skipped" if skip_enrichment else "pending"
    enrichment_receipt_path: Path | None = None
    enrichment_error = ""
    if not skip_enrichment:
        try:
            enrich_script = Path(__file__).resolve().parent / "enrich_with_deepxiv.py"
            enrich_module = load_enrich_module(enrich_script)
            enrichment_result = enrich_module.enrich_registered_source(
                knowledge_root=knowledge_root,
                topic_slug=topic_slug,
                source_id=source_id,
                enriched_by=registered_by,
                enrichment_override=enrichment_override,
            )
            enrichment_status = str(enrichment_result.get("status") or "enriched")
            receipt_text = str(enrichment_result.get("receipt_path") or "").strip()
            if receipt_text:
                enrichment_receipt_path = Path(receipt_text)
        except Exception as exc:  # noqa: BLE001
            enrichment_status = "failed"
            enrichment_error = str(exc)

    graph_build_status = "skipped" if skip_graph_build else "pending"
    concept_graph_path: Path | None = None
    concept_graph_relative_path = ""
    graph_receipt_path: Path | None = None
    graph_error = ""
    if not skip_graph_build:
        try:
            graph_script = Path(__file__).resolve().parent / "build_concept_graph.py"
            graph_module = load_graph_module(graph_script)
            graph_result = graph_module.build_concept_graph_for_registered_source(
                knowledge_root=knowledge_root,
                topic_slug=topic_slug,
                source_id=source_id,
                built_by=registered_by,
                graph_override=graph_override,
            )
            graph_build_status = str(graph_result.get("status") or "built")
            graph_path_text = str(graph_result.get("concept_graph_path") or "").strip()
            if graph_path_text:
                concept_graph_path = Path(graph_path_text)
            concept_graph_relative_path = str(graph_result.get("concept_graph_relative_path") or "").strip()
            receipt_text = str(graph_result.get("receipt_path") or "").strip()
            if receipt_text:
                graph_receipt_path = Path(receipt_text)
        except Exception as exc:  # noqa: BLE001
            graph_build_status = "failed"
            graph_error = str(exc)

    runtime_status_sync = sync_runtime_status_after_registration(
        knowledge_root=knowledge_root,
        topic_slug=topic_slug,
        source_id=source_id,
        updated_by=registered_by,
    )

    return {
        "status": "registered",
        "knowledge_root": knowledge_root,
        "topic_slug": topic_slug,
        "arxiv_id": metadata["versioned_id"],
        "source_id": source_id,
        "source_slug": source_slug,
        "layer0_source_root": layer0_source_root,
        "layer0_source_json": layer0_source_root / "source.json",
        "layer0_snapshot": layer0_source_root / "snapshot.md",
        "intake_projection_root": intake_projection_root,
        "bundle_path": bundle_path if bundle_rel else None,
        "extract_dir": extract_dir if extract_rel else None,
        "metadata": metadata,
        "download_status": download_status,
        "extraction_status": extraction_status,
        "download_error": download_error,
        "enrichment_status": enrichment_status,
        "enrichment_receipt_path": enrichment_receipt_path,
        "enrichment_error": enrichment_error,
        "graph_build_status": graph_build_status,
        "concept_graph_path": concept_graph_path,
        "concept_graph_relative_path": concept_graph_relative_path,
        "graph_receipt_path": graph_receipt_path,
        "graph_error": graph_error,
        "runtime_status_sync": runtime_status_sync,
    }


def main() -> int:
    args = build_parser().parse_args()
    knowledge_root = (
        Path(args.knowledge_root).expanduser().resolve()
        if args.knowledge_root
        else Path(__file__).resolve().parents[2]
    )
    metadata_override = None
    if args.metadata_json:
        metadata_path = Path(args.metadata_json).expanduser().resolve()
        metadata_override = load_json(metadata_path)
        if metadata_override is None:
            raise FileNotFoundError(f"Metadata override file does not exist: {metadata_path}")
    enrichment_override = None
    if args.enrichment_json:
        enrichment_path = Path(args.enrichment_json).expanduser().resolve()
        enrichment_override = load_json(enrichment_path)
        if enrichment_override is None:
            raise FileNotFoundError(f"Enrichment JSON file does not exist: {enrichment_path}")
    graph_override = None
    if args.graph_json:
        graph_path = Path(args.graph_json).expanduser().resolve()
        graph_override = load_json(graph_path)
        if graph_override is None:
            raise FileNotFoundError(f"Graph JSON file does not exist: {graph_path}")

    result = register_arxiv_source(
        knowledge_root=knowledge_root,
        topic_slug=args.topic_slug,
        arxiv_id=args.arxiv_id,
        registered_by=args.registered_by,
        download_source=args.download_source,
        force=args.force,
        skip_intake_projection=args.skip_intake_projection,
        metadata_override=metadata_override,
        skip_enrichment=args.skip_enrichment,
        enrichment_override=enrichment_override,
        skip_graph_build=args.skip_graph_build,
        graph_override=graph_override,
    )
    if args.json:
        payload = {
            "status": result["status"],
            "topic_slug": result["topic_slug"],
            "arxiv_id": result["arxiv_id"],
            "source_id": result["source_id"],
            "layer0_source_json": str(result["layer0_source_json"]),
            "layer0_snapshot": str(result["layer0_snapshot"]),
            "intake_projection_root": (
                str(result["intake_projection_root"])
                if result["intake_projection_root"] is not None
                else ""
            ),
            "bundle_path": str(result["bundle_path"]) if result["bundle_path"] is not None else "",
            "extract_dir": str(result["extract_dir"]) if result["extract_dir"] is not None else "",
            "download_status": result["download_status"],
            "extraction_status": result["extraction_status"],
            "download_error": result["download_error"],
            "enrichment_status": result["enrichment_status"],
            "enrichment_receipt_path": (
                str(result["enrichment_receipt_path"]) if result["enrichment_receipt_path"] is not None else ""
            ),
            "enrichment_error": result["enrichment_error"],
            "graph_build_status": result["graph_build_status"],
            "concept_graph_path": str(result["concept_graph_path"]) if result["concept_graph_path"] is not None else "",
            "concept_graph_relative_path": result["concept_graph_relative_path"],
            "graph_receipt_path": str(result["graph_receipt_path"]) if result["graph_receipt_path"] is not None else "",
            "graph_error": result["graph_error"],
            "runtime_status_sync": result["runtime_status_sync"],
        }
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    print(f"Registered arXiv source {result['source_id']}")
    print(f"- layer0 source.json: {result['layer0_source_json']}")
    print(f"- layer0 snapshot.md: {result['layer0_snapshot']}")
    if result["intake_projection_root"] is not None:
        print(f"- intake projection: {result['intake_projection_root']}")
    if result["enrichment_receipt_path"] is not None:
        print(f"- enrichment receipt: {result['enrichment_receipt_path']}")
    if result["concept_graph_path"] is not None:
        print(f"- concept graph: {result['concept_graph_path']}")
    if result["bundle_path"] is not None:
        print(f"- bundle: {result['bundle_path']}")
    if result["extract_dir"] is not None:
        print(f"- extracted: {result['extract_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
