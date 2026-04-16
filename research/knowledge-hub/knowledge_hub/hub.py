from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".tex",
    ".py",
    ".json",
    ".yaml",
    ".yml",
    ".csv",
    ".rst",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sanitize_filename(name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9 _.-]", " ", name).strip()
    safe = re.sub(r"\s+", " ", safe)
    return safe or "knowledge-hub-note"


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9_]+", text.lower())


def _strip_html(html: str) -> str:
    no_script = re.sub(r"<script[\\s\\S]*?</script>", " ", html, flags=re.IGNORECASE)
    no_style = re.sub(r"<style[\\s\\S]*?</style>", " ", no_script, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", no_style)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _chunk_text(text: str, chunk_size: int = 1200, overlap: int = 120) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []
    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    step = max(1, chunk_size - overlap)
    while start < len(cleaned):
        end = min(len(cleaned), start + chunk_size)
        chunks.append(cleaned[start:end])
        if end >= len(cleaned):
            break
        start += step
    return chunks


class KnowledgeHub:
    """File-backed knowledge middleware scaffold for Zotero/OpenCode/Obsidian."""

    def __init__(
        self,
        data_root: Path | None = None,
        zotero_python: str = "C:/Python312/python.exe",
        zotero_db_path: str = "D:/Zotero_main/zotero.sqlite",
        default_vault_path: str | None = None,
    ) -> None:
        self.repo_root = self._detect_repo_root()
        self.data_root = data_root or (
            self.repo_root / "research" / "knowledge-hub" / "data"
        )
        self.data_root.mkdir(parents=True, exist_ok=True)

        self.documents_path = self.data_root / "documents.json"
        self.queries_dir = self.data_root / "queries"
        self.queries_dir.mkdir(parents=True, exist_ok=True)

        self.zotero_python = zotero_python
        self.zotero_db_path = zotero_db_path
        self.default_vault_path = (
            Path(default_vault_path)
            if default_vault_path
            else self.repo_root / "obsidian-markdown"
        )

    def ingest_sources(
        self, sources: list[str], source_kind: str = "auto"
    ) -> dict[str, Any]:
        documents = self._load_documents()
        ingested: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []

        for source in sources:
            try:
                kind = self._resolve_kind(source, source_kind)
                title, text = self._read_source(source, kind)
                if not text.strip():
                    raise ValueError("source content is empty")

                doc_id = hashlib.sha1(
                    f"{kind}|{source}|{len(text)}".encode("utf-8")
                ).hexdigest()[:12]
                chunks = _chunk_text(text)
                chunk_records = []
                for idx, chunk in enumerate(chunks, start=1):
                    chunk_records.append(
                        {
                            "chunk_id": f"c{idx:03d}",
                            "text": chunk,
                            "token_count": len(_tokenize(chunk)),
                        }
                    )

                documents[doc_id] = {
                    "doc_id": doc_id,
                    "kind": kind,
                    "source": source,
                    "title": title,
                    "ingested_at": _utc_now(),
                    "text_length": len(text),
                    "chunks": chunk_records,
                }
                ingested.append(
                    {
                        "doc_id": doc_id,
                        "title": title,
                        "kind": kind,
                        "chunk_count": len(chunk_records),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                failures.append({"source": source, "error": str(exc)})

        self._save_documents(documents)
        return {
            "ingested": len(ingested),
            "failed": len(failures),
            "documents": ingested,
            "failures": failures,
        }

    def query(
        self,
        question: str,
        top_k: int = 6,
        include_zotero: bool = True,
        max_claims: int = 3,
        min_local_score: float = 0.0,
    ) -> dict[str, Any]:
        if not question.strip():
            raise ValueError("question cannot be empty")

        local_hits = self._search_local(question, top_k=top_k)
        if min_local_score > 0:
            local_hits = [
                hit for hit in local_hits if hit.get("score", 0.0) >= min_local_score
            ]

        citations: list[dict[str, Any]] = []

        for hit in local_hits:
            citations.append(
                {
                    "source_type": "local",
                    "ref_id": f"local:{hit['doc_id']}:{hit['chunk_id']}",
                    "title": hit["title"],
                    "snippet": hit["snippet"],
                    "metadata": {
                        "score": hit["score"],
                        "bm25_score": hit.get("bm25_score"),
                        "coverage": hit.get("coverage"),
                        "phrase_hit": hit.get("phrase_hit"),
                        "source": hit["source"],
                    },
                }
            )

        zotero_hits: list[dict[str, Any]] = []
        zotero_error: str | None = None
        if include_zotero:
            try:
                zotero_hits = self._search_zotero(question, limit=max(3, top_k // 2))
                for item in zotero_hits:
                    citations.append(
                        {
                            "source_type": "zotero",
                            "ref_id": item.get("key")
                            or item.get("id")
                            or "zotero:unknown",
                            "title": item.get("title") or "Untitled",
                            "snippet": item.get("abstract") or "",
                            "metadata": {
                                "score": item.get("score"),
                                "year": item.get("year"),
                                "authors": item.get("authors"),
                                "doi": item.get("doi"),
                            },
                        }
                    )
            except Exception as exc:  # noqa: BLE001
                zotero_error = str(exc)

        answer = self._compose_answer(question, local_hits, zotero_hits, zotero_error)
        claims = self._derive_claims(
            question=question, citations=citations, max_claims=max_claims
        )
        query_id = f"q-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        record = {
            "query_id": query_id,
            "question": question,
            "answer": answer,
            "claims": claims,
            "citations": citations,
            "created_at": _utc_now(),
        }
        self._save_query_record(record)
        return record

    def get_provenance(self, query_id: str) -> dict[str, Any]:
        path = self.queries_dir / f"{query_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"query_id not found: {query_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def export_obsidian(
        self,
        query_id: str,
        note_title: str,
        vault_path: str | None = None,
        output_subdir: str = "07 Knowledge Hub",
    ) -> dict[str, Any]:
        record = self.get_provenance(query_id)
        vault = Path(vault_path) if vault_path else self.default_vault_path
        note_dir = vault / output_subdir
        note_dir.mkdir(parents=True, exist_ok=True)

        note_name = f"{_sanitize_filename(note_title)}.md"
        note_path = note_dir / note_name

        lines = [
            "---",
            "type: knowledge-hub-note",
            f"query_id: {record['query_id']}",
            f"created_at: {record['created_at']}",
            "---",
            "",
            f"# {note_title}",
            "",
            "## Question",
            record["question"],
            "",
            "## Draft Answer",
            record["answer"],
            "",
            "## Claim Map",
        ]

        claims = record.get("claims") or []
        if claims:
            for idx, claim in enumerate(claims, start=1):
                claim_text = (claim.get("text") or "").strip()
                refs = claim.get("evidence_refs") or []
                confidence = claim.get("confidence", "unknown")
                lines.append(f"{idx}. {claim_text}")
                if refs:
                    lines.append(f"   - Evidence refs: {', '.join(refs)}")
                lines.append(f"   - Confidence: {confidence}")
        else:
            lines.append("No explicit claims were generated for this query.")

        lines.extend(
            [
                "",
                "## Evidence",
            ]
        )

        for idx, c in enumerate(record.get("citations", []), start=1):
            source_type = c.get("source_type", "unknown")
            title = c.get("title", "Untitled")
            ref_id = c.get("ref_id", "")
            snippet = (c.get("snippet") or "").strip()
            meta = c.get("metadata") or {}
            lines.append(f"{idx}. [{source_type}] {title} ({ref_id})")
            if snippet:
                lines.append(f"   - Snippet: {snippet[:320]}")
            if meta:
                lines.append(f"   - Metadata: {json.dumps(meta, ensure_ascii=False)}")

        note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {"query_id": query_id, "note_path": str(note_path)}

    def refresh_index(self, force_rebuild: bool = False) -> dict[str, Any]:
        status = self._get_zotero_status()
        rebuild_info = {
            "requested": force_rebuild,
            "note": "Run tools/Zotero-Semantic-Search/scripts/update_zotero_bg.py manually for long rebuild jobs.",
        }
        return {"zotero_status": status, "rebuild": rebuild_info}

    def _search_local(self, question: str, top_k: int) -> list[dict[str, Any]]:
        terms = _tokenize(question)
        if not terms:
            return []

        documents = self._load_documents()
        if not documents:
            return []

        query_tf = Counter(terms)
        chunk_rows: list[dict[str, Any]] = []
        df: Counter[str] = Counter()

        for doc in documents.values():
            title = doc.get("title", "Untitled")
            source = doc.get("source", "")
            for chunk in doc.get("chunks", []):
                text = chunk.get("text", "")
                tokens = _tokenize(text)
                if not tokens:
                    continue

                token_tf = Counter(tokens)
                chunk_rows.append(
                    {
                        "doc_id": doc["doc_id"],
                        "chunk_id": chunk["chunk_id"],
                        "title": title,
                        "source": source,
                        "snippet": text[:320].strip(),
                        "token_stream": " ".join(tokens),
                        "dl": len(tokens),
                        "tf": token_tf,
                    }
                )
                df.update(token_tf.keys())

        if not chunk_rows:
            return []

        bm25_k1 = 1.5
        bm25_b = 0.75
        chunk_count = len(chunk_rows)
        avgdl = sum(row["dl"] for row in chunk_rows) / max(1, chunk_count)
        query_phrase = " ".join(terms).strip()
        unique_query_terms = set(query_tf.keys())

        hits: list[dict[str, Any]] = []
        for row in chunk_rows:
            bm25_score = 0.0
            dl = row["dl"]
            tf = row["tf"]

            for term, qf in query_tf.items():
                term_tf = tf.get(term, 0)
                if term_tf <= 0:
                    continue

                term_df = df.get(term, 0)
                idf = math.log(1.0 + (chunk_count - term_df + 0.5) / (term_df + 0.5))
                denom = term_tf + bm25_k1 * (1.0 - bm25_b + bm25_b * (dl / avgdl))
                bm25_score += qf * idf * ((term_tf * (bm25_k1 + 1.0)) / denom)

            if bm25_score <= 0:
                continue

            matched_terms = sum(1 for term in unique_query_terms if tf.get(term, 0) > 0)
            coverage = matched_terms / max(1, len(unique_query_terms))
            token_stream = row["token_stream"]
            phrase_hit = bool(
                query_phrase and len(terms) > 1 and query_phrase in token_stream
            )

            rerank_score = bm25_score * (1.0 + 0.15 * coverage) + (
                0.25 if phrase_hit else 0.0
            )

            hits.append(
                {
                    "doc_id": row["doc_id"],
                    "chunk_id": row["chunk_id"],
                    "title": row["title"],
                    "source": row["source"],
                    "score": round(rerank_score, 6),
                    "bm25_score": round(bm25_score, 6),
                    "coverage": round(coverage, 4),
                    "phrase_hit": phrase_hit,
                    "snippet": row["snippet"],
                }
            )

        hits.sort(key=lambda item: item["score"], reverse=True)
        return hits[: max(1, top_k)]

    def _search_zotero(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        payload = json.dumps(query, ensure_ascii=False)
        code = f"""
import json
from zotero_mcp.semantic_search import create_semantic_search

engine = create_semantic_search()
result = engine.search({payload}, limit={int(limit)})
items = []
for row in result.get('results', []):
    item = row.get('zotero_item', {{}}).get('data', {{}})
    creators = item.get('creators', [])
    author_names = []
    for c in creators:
        last = c.get('lastName', '')
        first = c.get('firstName', '')
        full = (first + ' ' + last).strip()
        if full:
            author_names.append(full)
    items.append({{
        'key': item.get('key'),
        'title': item.get('title', 'Untitled'),
        'abstract': item.get('abstractNote', ''),
        'year': item.get('date', '')[:4],
        'doi': item.get('DOI'),
        'authors': author_names,
        'score': row.get('score'),
    }})
print(json.dumps({{'items': items}}))
"""
        proc = subprocess.run(
            [self.zotero_python, "-c", code],
            check=False,
            capture_output=True,
            text=True,
            timeout=90,
            env=self._zotero_env(),
            stdin=subprocess.DEVNULL,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or "zotero semantic search failed")

        lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        if not lines:
            return []
        data = json.loads(lines[-1])
        return data.get("items", [])

    def _get_zotero_status(self) -> dict[str, Any]:
        code = """
import json
from zotero_mcp.semantic_search import create_semantic_search

engine = create_semantic_search()
print(json.dumps(engine.get_database_status()))
"""
        proc = subprocess.run(
            [self.zotero_python, "-c", code],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
            env=self._zotero_env(),
            stdin=subprocess.DEVNULL,
        )
        if proc.returncode != 0:
            return {
                "status": "unavailable",
                "error": proc.stderr.strip() or "unable to read zotero status",
            }

        lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        if not lines:
            return {"status": "unknown"}
        try:
            return json.loads(lines[-1])
        except json.JSONDecodeError:
            return {"status": "unknown", "raw": lines[-1]}

    def _load_documents(self) -> dict[str, Any]:
        if not self.documents_path.exists():
            return {}
        text = self.documents_path.read_text(encoding="utf-8").strip()
        if not text:
            return {}
        return json.loads(text)

    def _save_documents(self, data: dict[str, Any]) -> None:
        self.documents_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _save_query_record(self, record: dict[str, Any]) -> None:
        path = self.queries_dir / f"{record['query_id']}.json"
        path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _read_source(self, source: str, kind: str) -> tuple[str, str]:
        if kind == "inline":
            return "inline-source", source

        if kind == "url":
            req = Request(source, headers={"User-Agent": "KnowledgeHub/0.1"})
            with urlopen(req, timeout=20) as resp:  # noqa: S310
                payload = resp.read(2_000_000)
            text = payload.decode("utf-8", errors="ignore")
            return source, _strip_html(text)

        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"source file not found: {source}")

        if path.suffix.lower() not in TEXT_EXTENSIONS:
            raise ValueError(
                f"unsupported file extension for v0 ingest: {path.suffix} (convert to .txt/.md/.tex first)"
            )

        return path.name, path.read_text(encoding="utf-8", errors="ignore")

    def _resolve_kind(self, source: str, source_kind: str) -> str:
        if source_kind in {"file", "url", "inline"}:
            return source_kind

        if source.startswith("http://") or source.startswith("https://"):
            return "url"
        if Path(source).exists():
            return "file"
        return "inline"

    def _compose_answer(
        self,
        question: str,
        local_hits: list[dict[str, Any]],
        zotero_hits: list[dict[str, Any]],
        zotero_error: str | None,
    ) -> str:
        lines = [
            "Evidence-first draft answer.",
            f"Question: {question}",
            "",
        ]

        if local_hits:
            lines.append("Local evidence highlights:")
            for hit in local_hits[:3]:
                lines.append(
                    f"- [{hit['title']}] score={hit['score']}: {hit['snippet'][:200]}"
                )
            lines.append("")
        else:
            lines.append("No local chunk matched strongly.")
            lines.append("")

        if zotero_hits:
            lines.append("Related Zotero items:")
            for item in zotero_hits[:3]:
                year = item.get("year") or "n/a"
                lines.append(f"- {item.get('title', 'Untitled')} ({year})")
        elif zotero_error:
            lines.append(f"Zotero semantic retrieval unavailable: {zotero_error}")

        lines.append("")
        lines.append("Use the citations list for final synthesis and claim grounding.")
        return "\n".join(lines).strip()

    def _derive_claims(
        self, question: str, citations: list[dict[str, Any]], max_claims: int = 3
    ) -> list[dict[str, Any]]:
        claims: list[dict[str, Any]] = []
        seen_claims: set[str] = set()
        max_claims = max(1, int(max_claims))
        candidate_limit = max_claims * 4

        for citation in citations[:candidate_limit]:
            snippet = re.sub(r"\s+", " ", (citation.get("snippet") or "").strip())
            if not snippet:
                continue

            claim_text = snippet[:220].rstrip(" ,;:-")
            if len(claim_text) < 40:
                continue
            if claim_text and claim_text[-1] not in ".!?":
                claim_text += "."

            evidence_ref = citation.get("ref_id", "")
            if not evidence_ref:
                continue

            normalized = re.sub(r"\W+", " ", claim_text.lower()).strip()
            if normalized in seen_claims:
                continue
            seen_claims.add(normalized)

            source_type = citation.get("source_type", "unknown")
            score = float((citation.get("metadata") or {}).get("score") or 0.0)
            if source_type == "local":
                if score >= 2.0:
                    confidence = "high"
                elif score >= 0.5:
                    confidence = "medium"
                else:
                    confidence = "low"
            else:
                confidence = "low"

            claims.append(
                {
                    "claim_id": f"claim-{len(claims) + 1:02d}",
                    "text": claim_text,
                    "evidence_refs": [evidence_ref],
                    "confidence": confidence,
                }
            )

            if len(claims) >= max_claims:
                break

        if not claims:
            claims.append(
                {
                    "claim_id": "claim-01",
                    "text": f"No direct evidence snippet was extracted for: {question}",
                    "evidence_refs": [],
                    "confidence": "low",
                }
            )
        return claims

    def _zotero_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.setdefault("ZOTERO_LOCAL", "true")
        if self.zotero_db_path:
            env.setdefault("ZOTERO_DB_PATH", self.zotero_db_path)
        return env

    def _detect_repo_root(self) -> Path:
        here = Path(__file__).resolve()
        for parent in here.parents:
            if (parent / "CLAUDE.md").exists():
                return parent
        return Path.cwd()
