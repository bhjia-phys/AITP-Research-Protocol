"""Deterministic text and PDF extraction for the disposable source shelf."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


TEXT_SUFFIXES = {".md", ".markdown", ".txt", ".tex"}
SUPPORTED_SUFFIXES = {*TEXT_SUFFIXES, ".pdf"}


class SourceShelfExtractionError(RuntimeError):
    """A source could not be read without weakening shelf coverage."""

    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class ExtractedPassage:
    page_start: int | None
    page_end: int | None
    section: str
    anchor_kinds: tuple[str, ...]
    anchor_labels: tuple[str, ...]
    text: str


@dataclass(frozen=True)
class _Paragraph:
    page_number: int | None
    section: str
    text: str
    anchor_kinds: tuple[str, ...]
    anchor_labels: tuple[str, ...]


_ANCHOR_PATTERNS = (
    ("definition", re.compile(r"\bDefinition\s+([\w.-]+)", re.IGNORECASE)),
    ("theorem", re.compile(r"\b(?:Theorem|Proposition|Lemma)\s+([\w.-]+)", re.IGNORECASE)),
    ("assumption", re.compile(r"\bAssumption\s+([\w.-]+)", re.IGNORECASE)),
    ("derivation_step", re.compile(r"\bDerivation\s+step\s+([\w.-]+)", re.IGNORECASE)),
    ("figure_caption", re.compile(r"\b(?:Figure|Fig\.)\s+([\w.-]+)", re.IGNORECASE)),
    ("caveat", re.compile(r"\b(?:Caveat|Warning|Limitation)\b", re.IGNORECASE)),
    ("bibliography", re.compile(r"\b(?:Bibliography|References)\s*:", re.IGNORECASE)),
    ("symbols", re.compile(r"\b(?:Symbols?|Notation)\s*:", re.IGNORECASE)),
    (
        "equation",
        re.compile(
            r"\\tag\{([^}]+)\}|\b(?:Eq(?:uation)?\.?)[\s~]*(?:\(|\[)?([\w.-]+)",
            re.IGNORECASE,
        ),
    ),
)


def extract_source_passages(
    path: Path,
    *,
    max_passage_chars: int,
) -> tuple[ExtractedPassage, ...]:
    """Extract bounded passages while retaining page, section, and formal anchors."""

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise SourceShelfExtractionError(
            "unsupported_source_format",
            f"source suffix {suffix or '<none>'} is not supported",
        )
    if suffix == ".pdf":
        pages = _read_pdf_pages(path)
    else:
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeError as exc:
            raise SourceShelfExtractionError(
                "source_text_decode_failed",
                f"source is not valid UTF-8 text: {exc}",
            ) from exc
        pages = ((None, text),)
    paragraphs: list[_Paragraph] = []
    for page_number, text in pages:
        paragraphs.extend(_paragraphs(text, page_number=page_number))
    if not paragraphs:
        raise SourceShelfExtractionError(
            "source_text_empty",
            "reader produced no non-empty source text",
        )
    return _pack_paragraphs(paragraphs, max_passage_chars=max_passage_chars)


def _read_pdf_pages(path: Path) -> tuple[tuple[int, str], ...]:
    try:
        reader = PdfReader(str(path))
    except Exception as exc:  # noqa: BLE001 - malformed PDFs need explicit coverage.
        raise SourceShelfExtractionError(
            "source_reader_failed",
            f"PDF reader failed: {type(exc).__name__}: {exc}",
        ) from exc
    if reader.is_encrypted:
        raise SourceShelfExtractionError(
            "encrypted_source",
            "encrypted PDF requires an explicit decrypted acquisition",
        )
    pages: list[tuple[int, str]] = []
    try:
        for page_number, page in enumerate(reader.pages, start=1):
            pages.append((page_number, page.extract_text() or ""))
    except Exception as exc:  # noqa: BLE001 - page extraction cannot fail open.
        raise SourceShelfExtractionError(
            "source_reader_failed",
            f"PDF page extraction failed: {type(exc).__name__}: {exc}",
        ) from exc
    return tuple(pages)


def _paragraphs(text: str, *, page_number: int | None) -> list[_Paragraph]:
    section = ""
    buffered: list[str] = []
    result: list[_Paragraph] = []

    def flush() -> None:
        if not buffered:
            return
        paragraph_text = "\n".join(buffered).strip()
        buffered.clear()
        if not paragraph_text:
            return
        kinds, labels = _classify(paragraph_text)
        result.append(
            _Paragraph(
                page_number=page_number,
                section=section,
                text=paragraph_text,
                anchor_kinds=kinds,
                anchor_labels=labels,
            )
        )

    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.rstrip()
        heading = re.match(r"^\s*#{1,6}\s+(.+?)\s*$", line)
        if heading:
            flush()
            section = heading.group(1).strip()
            continue
        if not line.strip():
            flush()
            continue
        buffered.append(line)
    flush()
    return result


def _classify(text: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    kinds: list[str] = []
    labels: list[str] = []
    for kind, pattern in _ANCHOR_PATTERNS:
        matches = list(pattern.finditer(text))
        if not matches:
            continue
        kinds.append(kind)
        for match in matches:
            captured = next((value for value in match.groups() if value), "")
            label = f"{kind}:{captured}" if captured else kind
            if label not in labels:
                labels.append(label)
    return tuple(kinds), tuple(labels)


def _pack_paragraphs(
    paragraphs: list[_Paragraph],
    *,
    max_passage_chars: int,
) -> tuple[ExtractedPassage, ...]:
    if max_passage_chars < 256:
        raise ValueError("max_passage_chars must be at least 256")
    expanded: list[_Paragraph] = []
    for paragraph in paragraphs:
        expanded.extend(_split_long_paragraph(paragraph, max_passage_chars))
    result: list[ExtractedPassage] = []
    current: list[_Paragraph] = []

    def flush() -> None:
        if not current:
            return
        result.append(_passage(current))
        current.clear()

    for paragraph in expanded:
        prospective = sum(len(item.text) for item in current) + 2 * len(current) + len(paragraph.text)
        section_changed = bool(current and paragraph.section != current[-1].section)
        page_changed = bool(current and paragraph.page_number != current[-1].page_number)
        if current and (prospective > max_passage_chars or section_changed or page_changed):
            flush()
        current.append(paragraph)
    flush()
    return tuple(result)


def _split_long_paragraph(paragraph: _Paragraph, limit: int) -> list[_Paragraph]:
    if len(paragraph.text) <= limit:
        return [paragraph]
    chunks: list[str] = []
    remaining = paragraph.text
    while remaining:
        if len(remaining) <= limit:
            chunks.append(remaining)
            break
        split_at = remaining.rfind(" ", 0, limit + 1)
        if split_at < limit // 2:
            split_at = limit
        chunks.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip()
    return [
        _Paragraph(
            page_number=paragraph.page_number,
            section=paragraph.section,
            text=chunk,
            anchor_kinds=_classify(chunk)[0],
            anchor_labels=_classify(chunk)[1],
        )
        for chunk in chunks
        if chunk
    ]


def _passage(paragraphs: list[_Paragraph]) -> ExtractedPassage:
    pages = [item.page_number for item in paragraphs if item.page_number is not None]
    kinds = tuple(dict.fromkeys(kind for item in paragraphs for kind in item.anchor_kinds))
    labels = tuple(dict.fromkeys(label for item in paragraphs for label in item.anchor_labels))
    return ExtractedPassage(
        page_start=min(pages) if pages else None,
        page_end=max(pages) if pages else None,
        section=paragraphs[0].section,
        anchor_kinds=kinds,
        anchor_labels=labels,
        text="\n\n".join(item.text for item in paragraphs),
    )
