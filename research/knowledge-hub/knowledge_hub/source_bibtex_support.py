from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .source_catalog import build_source_citation_traversal, read_jsonl, write_json, write_text
from .source_intelligence import (
    derive_canonical_source_id,
    extract_reference_ids,
    normalize_arxiv_id,
    normalize_doi,
)


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _slugify(text: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", str(text or "").lower())).strip("-") or "source"


def _source_layer_root(kernel_root: Path) -> Path:
    return kernel_root / "topics"


def _compiled_root(kernel_root: Path) -> Path:
    return kernel_root / "canonical" / "compiled"


def _bibtex_export_root(kernel_root: Path) -> Path:
    return _compiled_root(kernel_root) / "bibtex_exports"


def _bibtex_import_root(kernel_root: Path) -> Path:
    return _compiled_root(kernel_root) / "bibtex_imports"


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


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )


def _normalize_source_row(row: dict[str, Any], *, topic_slug: str) -> dict[str, Any]:
    title = str(row.get("title") or "").strip()
    summary = str(row.get("summary") or "").strip()
    source_type = str(row.get("source_type") or "").strip() or "unknown"
    provenance = row.get("provenance") if isinstance(row.get("provenance"), dict) else {}
    locator = row.get("locator") if isinstance(row.get("locator"), dict) else {}
    canonical_source_id = str(row.get("canonical_source_id") or "").strip() or derive_canonical_source_id(
        source_type=source_type,
        title=title,
        summary=summary,
        provenance=provenance,
        locator=locator,
    )
    references = _dedupe_strings(
        [str(item) for item in (row.get("references") or []) if str(item).strip()]
        or extract_reference_ids(text=f"{title} {summary}", provenance=provenance)
    )
    return {
        **row,
        "topic_slug": topic_slug,
        "source_id": str(row.get("source_id") or "").strip() or f"source:{_slugify(title)}",
        "source_type": source_type,
        "title": title or canonical_source_id,
        "summary": summary or "(missing)",
        "provenance": provenance,
        "locator": locator,
        "references": references,
        "canonical_source_id": canonical_source_id,
    }


def _load_normalized_source_rows(kernel_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    topics_root = _source_layer_root(kernel_root)
    for source_index_path in sorted(topics_root.glob("*/L0/source_index.jsonl")):
        topic_slug = source_index_path.parent.parent.name
        rows.extend(
            _normalize_source_row(row, topic_slug=topic_slug)
            for row in read_jsonl(source_index_path)
        )
    return rows


def _rows_by_canonical_source_id(source_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in source_rows:
        grouped.setdefault(str(row.get("canonical_source_id") or ""), []).append(row)
    return grouped


def _first_nonempty(*values: object) -> str:
    for value in values:
        normalized = str(value or "").strip()
        if normalized:
            return normalized
    return ""


def _authors_field_from_rows(rows: list[dict[str, Any]]) -> str:
    for row in rows:
        authors = row.get("authors")
        if isinstance(authors, list):
            joined = " and ".join(str(item).strip() for item in authors if str(item).strip())
            if joined:
                return joined
        if isinstance(authors, str) and authors.strip():
            return authors.strip()
        provenance = row.get("provenance") if isinstance(row.get("provenance"), dict) else {}
        prov_authors = provenance.get("authors")
        if isinstance(prov_authors, list):
            joined = " and ".join(str(item).strip() for item in prov_authors if str(item).strip())
            if joined:
                return joined
        if isinstance(prov_authors, str) and prov_authors.strip():
            return prov_authors.strip()
    return ""


def _field_from_rows(rows: list[dict[str, Any]], *field_names: str) -> str:
    for row in rows:
        for field_name in field_names:
            value = row.get(field_name)
            normalized = str(value or "").strip()
            if normalized:
                return normalized
            provenance = row.get("provenance") if isinstance(row.get("provenance"), dict) else {}
            prov_value = provenance.get(field_name)
            prov_normalized = str(prov_value or "").strip()
            if prov_normalized:
                return prov_normalized
    return ""


def _doi_from_rows(rows: list[dict[str, Any]]) -> str:
    for row in rows:
        provenance = row.get("provenance") if isinstance(row.get("provenance"), dict) else {}
        doi = normalize_doi(str(row.get("doi") or provenance.get("doi") or ""))
        if doi:
            return doi
    return ""


def _arxiv_id_from_rows(rows: list[dict[str, Any]]) -> str:
    for row in rows:
        provenance = row.get("provenance") if isinstance(row.get("provenance"), dict) else {}
        arxiv_id = normalize_arxiv_id(
            str(
                row.get("arxiv_id")
                or provenance.get("arxiv_id")
                or provenance.get("versioned_id")
                or provenance.get("abs_url")
                or provenance.get("source_url")
                or ""
            )
        )
        if arxiv_id:
            return arxiv_id
    return ""


def _url_from_rows(rows: list[dict[str, Any]]) -> str:
    for row in rows:
        provenance = row.get("provenance") if isinstance(row.get("provenance"), dict) else {}
        url = _first_nonempty(
            provenance.get("abs_url"),
            provenance.get("source_url"),
            provenance.get("journal_url"),
            row.get("url"),
        )
        if url:
            return url
    return ""


def _entry_type_for_rows(rows: list[dict[str, Any]], *, doi: str, arxiv_id: str) -> str:
    source_type = str((rows[0].get("source_type") if rows else "") or "").strip().lower()
    if source_type == "book":
        return "book"
    if source_type in {"thesis", "phdthesis", "mastersthesis"}:
        return "phdthesis"
    if doi:
        return "article"
    if arxiv_id:
        return "misc"
    return "misc"


def _initial_bibtex_fields(rows: list[dict[str, Any]], *, canonical_source_id: str) -> dict[str, str]:
    title = _field_from_rows(rows, "title")
    summary = _field_from_rows(rows, "summary")
    authors = _authors_field_from_rows(rows)
    year = _field_from_rows(rows, "year")
    journal = _field_from_rows(rows, "journal")
    doi = _doi_from_rows(rows)
    arxiv_id = _arxiv_id_from_rows(rows)
    url = _url_from_rows(rows)
    fields: dict[str, str] = {}
    if title:
        fields["title"] = title
    if authors:
        fields["author"] = authors
    if year:
        fields["year"] = year
    if journal and doi:
        fields["journal"] = journal
    if doi:
        fields["doi"] = doi
    if arxiv_id:
        fields["eprint"] = arxiv_id
        fields["archiveprefix"] = "arXiv"
    if url:
        fields["url"] = url
    if summary and summary != "(missing)":
        fields["abstract"] = summary
    fields["note"] = f"AITP canonical source id: {canonical_source_id}"
    return fields


def _base_citekey(*, doi: str, arxiv_id: str, title: str, canonical_source_id: str) -> str:
    if doi:
        return f"doi-{_slugify(doi)}"
    if arxiv_id:
        return f"arxiv-{_slugify(arxiv_id)}"
    if title:
        return _slugify(title)
    return _slugify(canonical_source_id)


def _unique_citekey(citekey: str, used: set[str]) -> str:
    candidate = citekey
    counter = 2
    while candidate in used:
        candidate = f"{citekey}-{counter}"
        counter += 1
    used.add(candidate)
    return candidate


def _merge_topic_slugs(rows: list[dict[str, Any]]) -> list[str]:
    return _dedupe_strings([str(row.get("topic_slug") or "") for row in rows])


def _prefer_bibtex_payload(rows: list[dict[str, Any]]) -> tuple[str, str, dict[str, str]] | None:
    for row in rows:
        bibtex = row.get("bibtex")
        if not isinstance(bibtex, dict):
            continue
        entry_type = str(bibtex.get("entry_type") or "").strip().lower()
        citekey = str(bibtex.get("citekey") or "").strip()
        fields = bibtex.get("fields")
        if entry_type and citekey and isinstance(fields, dict):
            normalized_fields = {
                str(key).strip().lower(): str(value).strip()
                for key, value in fields.items()
                if str(key).strip() and str(value).strip()
            }
            if normalized_fields:
                return entry_type, citekey, normalized_fields
    return None


def build_source_bibtex_export(
    kernel_root: Path,
    *,
    canonical_source_id: str,
    include_neighbors: bool = False,
) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    source_rows = _load_normalized_source_rows(kernel_root)
    grouped_rows = _rows_by_canonical_source_id(source_rows)
    seed_rows = grouped_rows.get(canonical_source_id)
    if not seed_rows:
        raise ValueError(f"Unknown canonical_source_id: {canonical_source_id}")

    included_canonical_source_ids = [canonical_source_id]
    if include_neighbors:
        traversal = build_source_citation_traversal(kernel_root, canonical_source_id=canonical_source_id)
        included_canonical_source_ids.extend(
            str(row.get("target_canonical_source_id") or "")
            for row in (traversal.get("outgoing_links") or [])
        )
        included_canonical_source_ids.extend(
            str(row.get("source_canonical_source_id") or "")
            for row in (traversal.get("incoming_links") or [])
        )
    included_canonical_source_ids = _dedupe_strings(included_canonical_source_ids)

    entries: list[dict[str, Any]] = []
    used_citekeys: set[str] = set()
    for current_canonical_source_id in included_canonical_source_ids:
        rows = grouped_rows.get(current_canonical_source_id) or []
        preserved_bibtex = _prefer_bibtex_payload(rows)
        if preserved_bibtex is not None:
            entry_type, citekey, fields = preserved_bibtex
        else:
            doi = _doi_from_rows(rows)
            arxiv_id = _arxiv_id_from_rows(rows)
            title = _field_from_rows(rows, "title")
            entry_type = _entry_type_for_rows(rows, doi=doi, arxiv_id=arxiv_id)
            citekey = _base_citekey(
                doi=doi,
                arxiv_id=arxiv_id,
                title=title,
                canonical_source_id=current_canonical_source_id,
            )
            fields = _initial_bibtex_fields(rows, canonical_source_id=current_canonical_source_id)
        entries.append(
            {
                "canonical_source_id": current_canonical_source_id,
                "citekey": _unique_citekey(citekey, used_citekeys),
                "entry_type": entry_type,
                "fields": fields,
                "topic_slugs": _merge_topic_slugs(rows),
            }
        )

    seed_title = _field_from_rows(seed_rows, "title") or canonical_source_id
    return {
        "kind": "aitp_source_bibtex_export",
        "compiler_version": 1,
        "generated_at": now_iso(),
        "seed": {
            "canonical_source_id": canonical_source_id,
            "representative_title": seed_title,
        },
        "summary": {
            "entry_count": len(entries),
            "included_neighbor_count": max(0, len(entries) - 1),
            "include_neighbors": include_neighbors,
        },
        "entries": entries,
    }


def _ordered_bibtex_fields(fields: dict[str, str]) -> list[tuple[str, str]]:
    preferred = [
        "title",
        "author",
        "year",
        "journal",
        "booktitle",
        "doi",
        "eprint",
        "archiveprefix",
        "url",
        "abstract",
        "note",
    ]
    ordered: list[tuple[str, str]] = []
    for key in preferred:
        value = str(fields.get(key) or "").strip()
        if value:
            ordered.append((key, value))
    for key in sorted(fields):
        if key in {item[0] for item in ordered}:
            continue
        value = str(fields.get(key) or "").strip()
        if value:
            ordered.append((key, value))
    return ordered


def render_source_bibtex_text(payload: dict[str, Any]) -> str:
    chunks: list[str] = []
    for entry in payload.get("entries") or []:
        chunks.append(f"@{entry.get('entry_type') or 'misc'}{{{entry.get('citekey') or 'source'},")
        for key, value in _ordered_bibtex_fields(entry.get("fields") or {}):
            chunks.append(f"  {key} = {{{value}}},")
        chunks.append("}")
        chunks.append("")
    return "\n".join(chunks).rstrip() + "\n"


def render_source_bibtex_export_markdown(payload: dict[str, Any]) -> str:
    seed = payload.get("seed") or {}
    summary = payload.get("summary") or {}
    lines = [
        "# Source BibTeX Export",
        "",
        f"- Canonical source id: `{seed.get('canonical_source_id') or '(missing)'}`",
        f"- Representative title: {seed.get('representative_title') or '(missing)'}",
        f"- Entry count: `{summary.get('entry_count', 0)}`",
        f"- Included neighbors: `{summary.get('included_neighbor_count', 0)}`",
        "",
        "## Entries",
        "",
    ]
    for entry in payload.get("entries") or []:
        fields = entry.get("fields") or {}
        lines.append(
            f"- `{entry.get('citekey')}` -> `{entry.get('canonical_source_id')}` "
            f"({fields.get('title') or '(missing title)'})"
        )
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def materialize_source_bibtex_export(
    kernel_root: Path,
    *,
    canonical_source_id: str,
    include_neighbors: bool = False,
) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    payload = build_source_bibtex_export(
        kernel_root,
        canonical_source_id=canonical_source_id,
        include_neighbors=include_neighbors,
    )
    basename = _slugify(canonical_source_id)
    json_path = _bibtex_export_root(kernel_root) / f"{basename}.json"
    markdown_path = _bibtex_export_root(kernel_root) / f"{basename}.md"
    bibtex_path = _bibtex_export_root(kernel_root) / f"{basename}.bib"
    write_json(json_path, payload)
    write_text(markdown_path, render_source_bibtex_export_markdown(payload))
    write_text(bibtex_path, render_source_bibtex_text(payload))
    return {
        "payload": payload,
        "json_path": str(json_path),
        "markdown_path": str(markdown_path),
        "bibtex_path": str(bibtex_path),
    }


def _split_bibtex_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    cursor = 0
    while cursor < len(text):
        start = text.find("@", cursor)
        if start < 0:
            break
        brace_index = -1
        for idx in range(start, len(text)):
            if text[idx] in "{(":
                brace_index = idx
                break
        if brace_index < 0:
            break
        open_char = text[brace_index]
        close_char = "}" if open_char == "{" else ")"
        depth = 0
        quote_open = False
        end_index = None
        for idx in range(brace_index, len(text)):
            char = text[idx]
            prev = text[idx - 1] if idx > 0 else ""
            if char == '"' and prev != "\\":
                quote_open = not quote_open
            if quote_open:
                continue
            if char == open_char:
                depth += 1
            elif char == close_char:
                depth -= 1
                if depth == 0:
                    end_index = idx + 1
                    break
        if end_index is None:
            break
        blocks.append(text[start:end_index].strip())
        cursor = end_index
    return blocks


def _split_top_level_csv(text: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    brace_depth = 0
    quote_open = False
    for idx, char in enumerate(text):
        prev = text[idx - 1] if idx > 0 else ""
        if char == '"' and prev != "\\":
            quote_open = not quote_open
            current.append(char)
            continue
        if not quote_open:
            if char == "{":
                brace_depth += 1
            elif char == "}":
                brace_depth = max(0, brace_depth - 1)
            elif char == "," and brace_depth == 0:
                item = "".join(current).strip()
                if item:
                    items.append(item)
                current = []
                continue
        current.append(char)
    tail = "".join(current).strip()
    if tail:
        items.append(tail)
    return items


def _strip_wrapping(value: str) -> str:
    normalized = str(value or "").strip().rstrip(",").strip()
    while True:
        if len(normalized) >= 2 and normalized[0] == normalized[-1] == '"':
            normalized = normalized[1:-1].strip()
            continue
        if len(normalized) >= 2 and normalized[0] == "{" and normalized[-1] == "}":
            normalized = normalized[1:-1].strip()
            continue
        break
    return re.sub(r"\s+", " ", normalized).strip()


def _parse_bibtex_entry(block: str) -> dict[str, Any]:
    match = re.match(r"\s*@\s*(?P<entry_type>[A-Za-z]+)\s*(?P<delimiter>[({])", block)
    if match is None:
        raise ValueError(f"Invalid BibTeX entry: {block[:40]}")
    entry_type = str(match.group("entry_type") or "").strip().lower()
    open_char = match.group("delimiter")
    close_char = "}" if open_char == "{" else ")"
    body = block[match.end():].strip()
    if body.endswith(close_char):
        body = body[:-1].strip()
    items = _split_top_level_csv(body)
    if not items:
        raise ValueError("BibTeX entry body is empty")
    citekey = items[0].strip()
    fields: dict[str, str] = {}
    for item in items[1:]:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        normalized_key = str(key or "").strip().lower()
        normalized_value = _strip_wrapping(value)
        if normalized_key and normalized_value:
            fields[normalized_key] = normalized_value
    return {
        "entry_type": entry_type,
        "citekey": citekey,
        "fields": fields,
    }


def _parse_bibtex_entries(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    return [_parse_bibtex_entry(block) for block in _split_bibtex_blocks(text)]


def _source_type_for_entry(entry_type: str, *, fields: dict[str, str]) -> str:
    normalized = str(entry_type or "").strip().lower()
    if normalized in {"book"}:
        return "book"
    if normalized in {"phdthesis", "mastersthesis", "thesis"}:
        return "thesis"
    if normalized in {"article", "inproceedings", "incollection", "proceedings"}:
        return "paper"
    if normalize_doi(fields.get("doi") or "") or normalize_arxiv_id(fields.get("eprint") or ""):
        return "paper"
    return "unknown"


def _author_list(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"\s+and\s+", str(value or "").strip()) if item.strip()]


def _import_row_from_bibtex_entry(
    entry: dict[str, Any],
    *,
    updated_by: str,
) -> dict[str, Any]:
    fields = entry.get("fields") if isinstance(entry.get("fields"), dict) else {}
    citekey = str(entry.get("citekey") or "").strip()
    entry_type = str(entry.get("entry_type") or "").strip().lower()
    title = str(fields.get("title") or citekey or "Imported source").strip()
    summary = str(fields.get("abstract") or fields.get("note") or f"Imported from BibTeX entry {citekey}.").strip()
    doi = normalize_doi(str(fields.get("doi") or ""))
    arxiv_id = normalize_arxiv_id(str(fields.get("eprint") or fields.get("arxiv") or ""))
    url = _first_nonempty(fields.get("url"), f"https://doi.org/{doi}" if doi else "")
    authors = _author_list(str(fields.get("author") or ""))
    source_type = _source_type_for_entry(entry_type, fields=fields)
    provenance = {
        "doi": doi,
        "arxiv_id": arxiv_id,
        "source_url": url,
        "abs_url": url,
        "authors": authors,
        "year": str(fields.get("year") or "").strip(),
        "journal": _first_nonempty(fields.get("journal"), fields.get("booktitle")),
        "bibtex_citekey": citekey,
        "bibtex_entry_type": entry_type,
        "bibtex_imported_by": updated_by,
    }
    references = extract_reference_ids(
        text=" ".join(str(value) for value in fields.values()),
        provenance=provenance,
    )
    canonical_source_id = derive_canonical_source_id(
        source_type=source_type,
        title=title,
        summary=summary,
        provenance=provenance,
        locator={},
    )
    return {
        "source_id": f"bibtex:{citekey or _slugify(title)}",
        "source_type": source_type,
        "title": title,
        "summary": summary,
        "canonical_source_id": canonical_source_id,
        "references": references,
        "provenance": provenance,
        "bibtex": {
            "entry_type": entry_type or "misc",
            "citekey": citekey or _slugify(title),
            "fields": fields,
        },
    }


def render_bibtex_import_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# BibTeX Source Import",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Source file: `{payload.get('bibtex_path') or '(missing)'}`",
        f"- Total entries: `{summary.get('total_entry_count', 0)}`",
        f"- Imported entries: `{summary.get('imported_entry_count', 0)}`",
        f"- Duplicate entries: `{summary.get('duplicate_entry_count', 0)}`",
        f"- Skipped entries: `{summary.get('skipped_entry_count', 0)}`",
        "",
        "## Imported Entries",
        "",
    ]
    for row in payload.get("imported_entries") or ["(none)"]:
        if isinstance(row, str):
            lines.append(f"- `{row}`")
            continue
        lines.append(
            f"- `{row.get('source_id')}` -> `{row.get('canonical_source_id')}` "
            f"({row.get('title') or '(missing title)'})"
        )
    lines.extend(["", "## Duplicate Entries", ""])
    duplicates = payload.get("duplicate_entries") or []
    if not duplicates:
        lines.append("- `(none)`")
    for row in duplicates:
        lines.append(
            f"- `{row.get('citekey') or '(missing)'}` -> `{row.get('canonical_source_id') or '(missing)'}`"
        )
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def import_bibtex_sources(
    kernel_root: Path,
    *,
    topic_slug: str,
    bibtex_path: str,
    updated_by: str,
) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    source_index_path = kernel_root / "topics" / topic_slug / "L0" / "source_index.jsonl"
    existing_rows = read_jsonl(source_index_path)
    existing_normalized_rows = [_normalize_source_row(row, topic_slug=topic_slug) for row in existing_rows]
    existing_canonical_source_ids = {
        str(row.get("canonical_source_id") or "").strip()
        for row in existing_normalized_rows
        if str(row.get("canonical_source_id") or "").strip()
    }

    parsed_entries = _parse_bibtex_entries(Path(bibtex_path).expanduser().resolve())
    imported_rows: list[dict[str, Any]] = []
    duplicate_entries: list[dict[str, str]] = []
    skipped_entries: list[dict[str, str]] = []
    imported_canonical_source_ids: set[str] = set()

    for entry in parsed_entries:
        if not str(entry.get("citekey") or "").strip():
            skipped_entries.append({"reason": "missing_citekey"})
            continue
        row = _import_row_from_bibtex_entry(entry, updated_by=updated_by)
        canonical_source_id = str(row.get("canonical_source_id") or "").strip()
        if canonical_source_id in existing_canonical_source_ids or canonical_source_id in imported_canonical_source_ids:
            duplicate_entries.append(
                {
                    "citekey": str(entry.get("citekey") or "").strip(),
                    "canonical_source_id": canonical_source_id,
                }
            )
            continue
        imported_canonical_source_ids.add(canonical_source_id)
        imported_rows.append(row)

    merged_rows = existing_rows + imported_rows
    _write_jsonl(source_index_path, merged_rows)

    payload = {
        "kind": "aitp_bibtex_source_import",
        "compiler_version": 1,
        "generated_at": now_iso(),
        "topic_slug": topic_slug,
        "bibtex_path": str(Path(bibtex_path).expanduser().resolve()),
        "source_index_path": str(source_index_path),
        "summary": {
            "total_entry_count": len(parsed_entries),
            "imported_entry_count": len(imported_rows),
            "duplicate_entry_count": len(duplicate_entries),
            "skipped_entry_count": len(skipped_entries),
        },
        "imported_entries": imported_rows,
        "duplicate_entries": duplicate_entries,
        "skipped_entries": skipped_entries,
    }

    basename = f"{_slugify(topic_slug)}-{_slugify(Path(bibtex_path).stem)}"
    json_path = _bibtex_import_root(kernel_root) / f"{basename}.json"
    markdown_path = _bibtex_import_root(kernel_root) / f"{basename}.md"
    write_json(json_path, payload)
    write_text(markdown_path, render_bibtex_import_markdown(payload))
    return {
        "payload": payload,
        "json_path": str(json_path),
        "markdown_path": str(markdown_path),
        "source_index_path": str(source_index_path),
    }
