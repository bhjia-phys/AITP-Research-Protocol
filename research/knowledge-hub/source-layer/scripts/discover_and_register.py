#!/usr/bin/env python3
"""Bridge bounded source discovery into the existing Layer 0 arXiv registration path."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any


ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}
ARXIV_ID_PATTERN = re.compile(
    r"(?P<id>(?:\d{4}\.\d{4,5}|[a-z\-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?)",
    re.IGNORECASE,
)


class ProviderError(RuntimeError):
    """Raised when one discovery provider cannot produce usable candidates."""


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def timestamp_slug() -> str:
    return datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")


def slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-+", "-", lowered).strip("-")
    return lowered or "source-discovery"


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", str(text).lower())


def extract_arxiv_id(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    match = ARXIV_ID_PATTERN.search(text)
    return match.group("id") if match else ""


def parse_authors(value: Any) -> list[str]:
    authors: list[str] = []
    if isinstance(value, list):
        for row in value:
            if isinstance(row, dict):
                candidate = str(
                    row.get("name")
                    or row.get("full_name")
                    or row.get("author")
                    or ""
                ).strip()
            else:
                candidate = str(row).strip()
            if candidate:
                authors.append(candidate)
    elif value:
        candidate = str(value).strip()
        if candidate:
            authors.append(candidate)
    return authors


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_url(url: str, timeout: int = 60) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read()


def extract_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("results", "items", "papers", "data", "matches"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
        return [payload]
    raise ProviderError("Search results payload must be a list or object.")


def normalize_provider_score(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    if score < 0:
        return 0.0
    if score <= 1:
        return score
    if score <= 100:
        return min(score / 100.0, 1.0)
    return 1.0


def normalize_candidate(raw: dict[str, Any], provider: str, position: int) -> dict[str, Any]:
    arxiv_id = ""
    for key in ("arxiv_id", "paper_id", "identifier", "id", "url", "abs_url", "link"):
        arxiv_id = extract_arxiv_id(raw.get(key))
        if arxiv_id:
            break
    title = str(raw.get("title") or raw.get("paper_title") or raw.get("name") or "").strip()
    summary = str(raw.get("summary") or raw.get("abstract") or raw.get("snippet") or "").strip()
    published = str(raw.get("published") or raw.get("published_at") or raw.get("date") or "").strip()
    updated = str(raw.get("updated") or raw.get("updated_at") or published).strip()
    authors = parse_authors(raw.get("authors") or raw.get("author_names") or raw.get("author"))
    abs_url = str(
        raw.get("abs_url")
        or raw.get("url")
        or (f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else "")
    ).strip()
    pdf_url = str(
        raw.get("pdf_url")
        or (f"https://arxiv.org/pdf/{re.sub(r'v\\d+$', '', arxiv_id)}.pdf" if arxiv_id else "")
    ).strip()
    source_url = str(raw.get("source_url") or (f"https://arxiv.org/e-print/{arxiv_id}" if arxiv_id else "")).strip()
    return {
        "provider": provider,
        "provider_position": position,
        "arxiv_id": arxiv_id,
        "title": title,
        "summary": summary,
        "published": published,
        "updated": updated,
        "authors": authors,
        "abs_url": abs_url,
        "pdf_url": pdf_url,
        "source_url": source_url,
        "identifier": str(raw.get("identifier") or abs_url).strip(),
        "provider_score": normalize_provider_score(
            raw.get("score") or raw.get("similarity") or raw.get("relevance_score")
        ),
        "raw": raw,
    }


def read_search_results_json(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = load_json(path)
    rows = extract_rows(payload)
    candidates = [
        normalize_candidate(row, provider="search_results_json", position=index)
        for index, row in enumerate(rows)
    ]
    metadata = {
        "provider": "search_results_json",
        "source_path": str(path),
        "result_count": len(candidates),
    }
    return metadata, candidates


def run_deepxiv_cli(*, query: str, max_results: int, deepxiv_bin: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    command = [
        deepxiv_bin,
        "search",
        query,
        "--format",
        "json",
        "--limit",
        str(max(max_results, 1)),
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise ProviderError(f"deepxiv_cli failed: {detail}")
    payload = json.loads(completed.stdout)
    rows = extract_rows(payload)
    candidates = [
        normalize_candidate(row, provider="deepxiv_cli", position=index)
        for index, row in enumerate(rows)
    ]
    metadata = {
        "provider": "deepxiv_cli",
        "command": command,
        "result_count": len(candidates),
    }
    return metadata, candidates


def search_arxiv_api(*, query: str, max_results: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    encoded = urllib.parse.urlencode(
        {"search_query": f"all:{query}", "start": 0, "max_results": max(max_results, 1)}
    )
    url = f"https://export.arxiv.org/api/query?{encoded}"
    payload = fetch_url(url).decode("utf-8")
    root = ET.fromstring(payload)
    rows: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        identifier = entry.findtext("atom:id", default="", namespaces=ATOM_NS).strip()
        versioned_id = identifier.rsplit("/", 1)[-1] if identifier else ""
        title = entry.findtext("atom:title", default="", namespaces=ATOM_NS).strip()
        summary = entry.findtext("atom:summary", default="", namespaces=ATOM_NS).strip()
        published = entry.findtext("atom:published", default="", namespaces=ATOM_NS).strip()
        updated = entry.findtext("atom:updated", default="", namespaces=ATOM_NS).strip()
        authors = [
            author.findtext("atom:name", default="", namespaces=ATOM_NS).strip()
            for author in entry.findall("atom:author", ATOM_NS)
        ]
        rows.append(
            {
                "arxiv_id": versioned_id,
                "title": title,
                "summary": summary,
                "published": published,
                "updated": updated,
                "authors": authors,
                "identifier": identifier,
                "abs_url": identifier or f"https://arxiv.org/abs/{versioned_id}",
                "pdf_url": f"https://arxiv.org/pdf/{re.sub(r'v\\d+$', '', versioned_id)}.pdf",
                "source_url": f"https://arxiv.org/e-print/{versioned_id}",
            }
        )
    candidates = [
        normalize_candidate(row, provider="arxiv_api", position=index)
        for index, row in enumerate(rows)
    ]
    metadata = {
        "provider": "arxiv_api",
        "query_url": url,
        "result_count": len(candidates),
    }
    return metadata, candidates


def execute_provider(
    provider: str,
    *,
    query: str,
    max_results: int,
    search_results_json: Path | None,
    deepxiv_bin: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if provider == "search_results_json":
        if search_results_json is None:
            raise ProviderError("search_results_json provider requires --search-results-json.")
        return read_search_results_json(search_results_json)
    if provider == "deepxiv_cli":
        return run_deepxiv_cli(query=query, max_results=max_results, deepxiv_bin=deepxiv_bin)
    if provider == "arxiv_api":
        return search_arxiv_api(query=query, max_results=max_results)
    raise ProviderError(f"Unsupported provider: {provider}")


def build_provider_chain(args: argparse.Namespace) -> list[str]:
    if args.provider:
        return args.provider
    chain: list[str] = []
    if args.search_results_json:
        chain.append("search_results_json")
    chain.extend(["deepxiv_cli", "arxiv_api"])
    deduped: list[str] = []
    seen: set[str] = set()
    for provider in chain:
        if provider not in seen:
            seen.add(provider)
            deduped.append(provider)
    return deduped


def parse_published_value(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d", "%Y-%m"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return text


def evaluate_candidates(
    *,
    query: str,
    candidates: list[dict[str, Any]],
    preferred_arxiv_id: str = "",
) -> list[dict[str, Any]]:
    query_terms = set(tokenize(query))
    evaluations: list[dict[str, Any]] = []
    preferred = preferred_arxiv_id.strip()
    total_candidates = max(len(candidates), 1)
    for rank, candidate in enumerate(candidates):
        text_terms = set(tokenize(f"{candidate['title']} {candidate['summary']}"))
        overlap = len(query_terms & text_terms) / max(len(query_terms), 1)
        metadata_completeness = sum(
            1
            for value in (
                candidate.get("arxiv_id"),
                candidate.get("title"),
                candidate.get("summary"),
                candidate.get("published"),
                candidate.get("authors"),
            )
            if value
        ) / 5.0
        order_bonus = max((total_candidates - rank) / total_candidates, 0)
        preferred_bonus = 1.0 if preferred and candidate.get("arxiv_id") == preferred else 0.0
        blocked_reasons: list[str] = []
        if not candidate.get("arxiv_id"):
            blocked_reasons.append("missing arxiv_id")
        if not candidate.get("title"):
            blocked_reasons.append("missing title")
        total_score = (
            overlap * 0.5
            + metadata_completeness * 0.2
            + candidate.get("provider_score", 0.0) * 0.15
            + order_bonus * 0.1
            + preferred_bonus * 1.0
        )
        selection_reasons: list[str] = []
        if preferred_bonus:
            selection_reasons.append("matched preferred arxiv_id")
        if overlap:
            selection_reasons.append(f"query overlap={overlap:.2f}")
        if candidate.get("provider_score"):
            selection_reasons.append(f"provider score={candidate['provider_score']:.2f}")
        if metadata_completeness:
            selection_reasons.append(f"metadata completeness={metadata_completeness:.2f}")
        evaluations.append(
            {
                "rank_hint": rank,
                "provider": candidate["provider"],
                "arxiv_id": candidate.get("arxiv_id", ""),
                "title": candidate.get("title", ""),
                "published": parse_published_value(candidate.get("published", "")),
                "blocked_reasons": blocked_reasons,
                "status": "blocked" if blocked_reasons else "viable",
                "score": round(total_score, 6),
                "selection_reasons": selection_reasons,
                "candidate": candidate,
            }
        )
    evaluations.sort(
        key=lambda row: (
            row["status"] != "viable",
            -row["score"],
            row["published"] == "",
            row["published"],
            row["rank_hint"],
        )
    )
    for index, row in enumerate(evaluations, start=1):
        row["rank"] = index
    return evaluations


def select_candidate(evaluations: list[dict[str, Any]], select_index: int) -> dict[str, Any]:
    viable = [row for row in evaluations if row["status"] == "viable"]
    if not viable:
        raise ProviderError("No viable discovery candidate could be selected.")
    if select_index < 0 or select_index >= len(viable):
        raise ProviderError(
            f"select-index {select_index} is out of range for {len(viable)} viable candidates."
        )
    return viable[select_index]


def load_register_module(script_path: Path):
    spec = importlib.util.spec_from_file_location("register_arxiv_source_module", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load registration module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_registration_metadata(candidate: dict[str, Any]) -> dict[str, Any]:
    arxiv_id = str(candidate.get("arxiv_id") or "").strip()
    base_id = re.sub(r"v\d+$", "", arxiv_id)
    return {
        "arxiv_id": arxiv_id,
        "versioned_id": arxiv_id,
        "base_id": base_id,
        "title": str(candidate.get("title") or "").strip(),
        "summary": str(candidate.get("summary") or "").strip(),
        "published": str(candidate.get("published") or "").strip(),
        "updated": str(candidate.get("updated") or candidate.get("published") or "").strip(),
        "authors": list(candidate.get("authors") or []),
        "identifier": str(candidate.get("identifier") or candidate.get("abs_url") or "").strip(),
        "abs_url": str(candidate.get("abs_url") or f"https://arxiv.org/abs/{arxiv_id}").strip(),
        "pdf_url": str(candidate.get("pdf_url") or f"https://arxiv.org/pdf/{base_id}.pdf").strip(),
        "source_url": str(candidate.get("source_url") or f"https://arxiv.org/e-print/{arxiv_id}").strip(),
    }


def build_summary_markdown(
    *,
    topic_slug: str,
    query: str,
    provider_chain: list[str],
    provider_attempts: list[dict[str, Any]],
    selected: dict[str, Any],
    registration: dict[str, Any],
) -> str:
    lines = [
        "# Layer 0 discovery receipt",
        "",
        f"Topic: `{topic_slug}`",
        f"Query: `{query}`",
        f"Provider chain: `{', '.join(provider_chain)}`",
        "",
        "## Provider attempts",
    ]
    for row in provider_attempts:
        status = row.get("status", "unknown")
        provider = row.get("provider", "unknown")
        detail = row.get("detail") or ""
        lines.append(f"- `{provider}` -> `{status}` {detail}".rstrip())
    lines.extend(
        [
            "",
            "## Selected candidate",
            f"- arXiv id: `{selected['arxiv_id']}`",
            f"- title: {selected['title']}",
            f"- provider: `{selected['provider']}`",
            f"- score: `{selected['score']}`",
            "",
            "## Registration path",
            f"- layer0 source.json: `{registration['layer0_source_json']}`",
            f"- layer0 snapshot.md: `{registration['layer0_snapshot']}`",
        ]
    )
    if registration.get("intake_projection_root"):
        lines.append(f"- intake projection: `{registration['intake_projection_root']}`")
    if registration.get("enrichment_receipt_path"):
        lines.append(f"- enrichment receipt: `{registration['enrichment_receipt_path']}`")
    lines.extend(
        [
            "",
            "The search step remains an external provider bridge.",
            "Canonical source identity still flows through `register_arxiv_source.py`.",
        ]
    )
    return "\n".join(lines) + "\n"


def discover_and_register(
    *,
    knowledge_root: Path,
    topic_slug: str,
    query: str,
    provider_chain: list[str],
    search_results_json: Path | None,
    max_results: int,
    deepxiv_bin: str,
    preferred_arxiv_id: str,
    select_index: int,
    registered_by: str,
    download_source: bool = True,
    force: bool = False,
    skip_intake_projection: bool = False,
    skip_enrichment: bool = False,
    enrichment_override: dict[str, Any] | None = None,
    skip_graph_build: bool = False,
    graph_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    discovery_root = (
        knowledge_root
        / "source-layer"
        / "topics"
        / topic_slug
        / "discoveries"
        / f"{timestamp_slug()}-{slugify(query)[:48]}"
    )
    discovery_root.mkdir(parents=True, exist_ok=True)

    query_path = discovery_root / "query.json"
    search_results_path = discovery_root / "search_results.json"
    evaluation_path = discovery_root / "candidate_evaluation.json"
    summary_path = discovery_root / "discovery_summary.md"
    registration_path = discovery_root / "registration_receipt.json"

    provider_attempts: list[dict[str, Any]] = []
    selected_provider_payload: dict[str, Any] | None = None
    selected_candidates: list[dict[str, Any]] = []

    for provider in provider_chain:
        try:
            provider_payload, candidates = execute_provider(
                provider,
                query=query,
                max_results=max_results,
                search_results_json=search_results_json,
                deepxiv_bin=deepxiv_bin,
            )
        except (ProviderError, FileNotFoundError, json.JSONDecodeError, OSError, ET.ParseError) as exc:
            provider_attempts.append(
                {
                    "provider": provider,
                    "status": "failed",
                    "detail": str(exc),
                }
            )
            continue
        provider_attempts.append(
            {
                "provider": provider,
                "status": "ok" if candidates else "empty",
                "detail": f"candidates={len(candidates)}",
            }
        )
        if candidates:
            selected_provider_payload = provider_payload
            selected_candidates = candidates[: max(max_results, 1)]
            break

    query_payload = {
        "status": "search_completed" if selected_candidates else "search_failed",
        "query": query,
        "topic_slug": topic_slug,
        "provider_chain": provider_chain,
        "provider_attempts": provider_attempts,
        "registered_by": registered_by,
        "created_at": now_iso(),
        "search_results_path": str(search_results_path),
        "candidate_evaluation_path": str(evaluation_path),
        "registration_receipt_path": str(registration_path),
        "summary_path": str(summary_path),
    }
    write_json(query_path, query_payload)

    if not selected_candidates or selected_provider_payload is None:
        raise ProviderError("No discovery provider produced usable candidates.")

    write_json(
        search_results_path,
        {
            "status": "search_completed",
            "query": query,
            "provider": selected_provider_payload["provider"],
            "provider_payload": selected_provider_payload,
            "provider_attempts": provider_attempts,
            "candidates": selected_candidates,
        },
    )

    evaluations = evaluate_candidates(
        query=query,
        candidates=selected_candidates,
        preferred_arxiv_id=preferred_arxiv_id,
    )
    selected = select_candidate(evaluations, select_index)
    write_json(
        evaluation_path,
        {
            "status": "evaluated",
            "query": query,
            "preferred_arxiv_id": preferred_arxiv_id,
            "selected_rank": selected["rank"],
            "selected_arxiv_id": selected["arxiv_id"],
            "evaluations": evaluations,
        },
    )

    register_script = Path(__file__).resolve().parent / "register_arxiv_source.py"
    register_module = load_register_module(register_script)
    registration = register_module.register_arxiv_source(
        knowledge_root=knowledge_root,
        topic_slug=topic_slug,
        arxiv_id=selected["arxiv_id"],
        registered_by=registered_by,
        download_source=download_source,
        force=force,
        skip_intake_projection=skip_intake_projection,
        metadata_override=build_registration_metadata(selected["candidate"]),
        skip_enrichment=skip_enrichment,
        enrichment_override=enrichment_override,
        skip_graph_build=skip_graph_build,
        graph_override=graph_override,
    )
    registration_payload = {
        "status": "registered",
        "selected_candidate": {
            "arxiv_id": selected["arxiv_id"],
            "title": selected["title"],
            "provider": selected["provider"],
            "score": selected["score"],
            "selection_reasons": selected["selection_reasons"],
        },
        "layer0_source_json": str(registration["layer0_source_json"]),
        "layer0_snapshot": str(registration["layer0_snapshot"]),
        "intake_projection_root": (
            str(registration["intake_projection_root"])
            if registration["intake_projection_root"] is not None
            else ""
        ),
        "download_status": registration["download_status"],
        "extraction_status": registration["extraction_status"],
        "download_error": registration["download_error"],
        "enrichment_status": registration["enrichment_status"],
        "enrichment_receipt_path": (
            str(registration["enrichment_receipt_path"])
            if registration["enrichment_receipt_path"] is not None
            else ""
        ),
        "enrichment_error": registration["enrichment_error"],
        "graph_build_status": registration["graph_build_status"],
        "concept_graph_path": (
            str(registration["concept_graph_path"])
            if registration["concept_graph_path"] is not None
            else ""
        ),
        "concept_graph_relative_path": registration["concept_graph_relative_path"],
        "graph_receipt_path": (
            str(registration["graph_receipt_path"])
            if registration["graph_receipt_path"] is not None
            else ""
        ),
        "graph_error": registration["graph_error"],
    }
    write_json(registration_path, registration_payload)
    summary_path.write_text(
        build_summary_markdown(
            topic_slug=topic_slug,
            query=query,
            provider_chain=provider_chain,
            provider_attempts=provider_attempts,
            selected=selected,
            registration=registration_payload,
        ),
        encoding="utf-8",
    )
    query_payload["status"] = "registered"
    query_payload["selected_provider"] = selected_provider_payload["provider"]
    query_payload["selected_arxiv_id"] = selected["arxiv_id"]
    write_json(query_path, query_payload)

    return {
        "status": "registered",
        "topic_slug": topic_slug,
        "query": query,
        "provider_chain": provider_chain,
        "provider_attempts": provider_attempts,
        "selected_provider": selected_provider_payload["provider"],
        "selected_candidate": {
            "arxiv_id": selected["arxiv_id"],
            "title": selected["title"],
            "provider": selected["provider"],
            "score": selected["score"],
            "selection_reasons": selected["selection_reasons"],
        },
        "discovery_root": discovery_root,
        "query_path": query_path,
        "search_results_path": search_results_path,
        "candidate_evaluation_path": evaluation_path,
        "registration_receipt_path": registration_path,
        "summary_path": summary_path,
        "layer0_source_json": registration["layer0_source_json"],
        "layer0_snapshot": registration["layer0_snapshot"],
        "intake_projection_root": registration["intake_projection_root"],
        "enrichment_status": registration["enrichment_status"],
        "enrichment_receipt_path": registration["enrichment_receipt_path"],
        "graph_build_status": registration["graph_build_status"],
        "concept_graph_path": registration["concept_graph_path"],
        "concept_graph_relative_path": registration["concept_graph_relative_path"],
        "graph_receipt_path": registration["graph_receipt_path"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--knowledge-root")
    parser.add_argument("--topic-slug", required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument(
        "--provider",
        action="append",
        choices=("search_results_json", "deepxiv_cli", "arxiv_api"),
        default=[],
        help="Ordered provider chain. Omit to use the default fallback order.",
    )
    parser.add_argument("--search-results-json")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--deepxiv-bin", default="deepxiv")
    parser.add_argument("--preferred-arxiv-id", default="")
    parser.add_argument("--select-index", type=int, default=0)
    parser.add_argument("--registered-by", default="codex")
    download_group = parser.add_mutually_exclusive_group()
    download_group.add_argument("--download-source", dest="download_source", action="store_true")
    download_group.add_argument("--metadata-only", dest="download_source", action="store_false")
    parser.set_defaults(download_source=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-intake-projection", action="store_true")
    parser.add_argument("--skip-enrichment", action="store_true")
    parser.add_argument("--skip-graph-build", action="store_true")
    parser.add_argument("--enrichment-json")
    parser.add_argument("--graph-json")
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    knowledge_root = (
        Path(args.knowledge_root).expanduser().resolve()
        if args.knowledge_root
        else Path(__file__).resolve().parents[2]
    )
    search_results_json = (
        Path(args.search_results_json).expanduser().resolve()
        if args.search_results_json
        else None
    )
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
    payload = discover_and_register(
        knowledge_root=knowledge_root,
        topic_slug=args.topic_slug,
        query=args.query,
        provider_chain=build_provider_chain(args),
        search_results_json=search_results_json,
        max_results=args.max_results,
        deepxiv_bin=args.deepxiv_bin,
        preferred_arxiv_id=args.preferred_arxiv_id,
        select_index=args.select_index,
        registered_by=args.registered_by,
        download_source=args.download_source,
        force=args.force,
        skip_intake_projection=args.skip_intake_projection,
        skip_enrichment=args.skip_enrichment,
        enrichment_override=enrichment_override,
        skip_graph_build=args.skip_graph_build,
        graph_override=graph_override,
    )
    if args.json:
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "topic_slug": payload["topic_slug"],
                    "query": payload["query"],
                    "provider_chain": payload["provider_chain"],
                    "provider_attempts": payload["provider_attempts"],
                    "selected_provider": payload["selected_provider"],
                    "selected_candidate": payload["selected_candidate"],
                    "discovery_root": str(payload["discovery_root"]),
                    "query_path": str(payload["query_path"]),
                    "search_results_path": str(payload["search_results_path"]),
                    "candidate_evaluation_path": str(payload["candidate_evaluation_path"]),
                    "registration_receipt_path": str(payload["registration_receipt_path"]),
                    "summary_path": str(payload["summary_path"]),
                    "layer0_source_json": str(payload["layer0_source_json"]),
                    "layer0_snapshot": str(payload["layer0_snapshot"]),
                    "intake_projection_root": (
                        str(payload["intake_projection_root"])
                        if payload["intake_projection_root"] is not None
                        else ""
                    ),
                    "enrichment_status": payload["enrichment_status"],
                    "enrichment_receipt_path": (
                        str(payload["enrichment_receipt_path"])
                        if payload["enrichment_receipt_path"] is not None
                        else ""
                    ),
                    "graph_build_status": payload["graph_build_status"],
                    "concept_graph_path": (
                        str(payload["concept_graph_path"])
                        if payload["concept_graph_path"] is not None
                        else ""
                    ),
                    "concept_graph_relative_path": payload["concept_graph_relative_path"],
                    "graph_receipt_path": (
                        str(payload["graph_receipt_path"])
                        if payload["graph_receipt_path"] is not None
                        else ""
                    ),
                },
                ensure_ascii=True,
                indent=2,
            )
        )
        return 0

    print(f"Selected {payload['selected_candidate']['arxiv_id']} for topic {payload['topic_slug']}")
    print(f"- discovery root: {payload['discovery_root']}")
    print(f"- layer0 source.json: {payload['layer0_source_json']}")
    if payload["intake_projection_root"] is not None:
        print(f"- intake projection: {payload['intake_projection_root']}")
    if payload["enrichment_receipt_path"] is not None:
        print(f"- enrichment receipt: {payload['enrichment_receipt_path']}")
    if payload["concept_graph_path"] is not None:
        print(f"- concept graph: {payload['concept_graph_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
