"""On-device text extraction + passage chunking (PRD FR-03).

PDFs are read with PyMuPDF (fitz). We keep page numbers and, when the PDF has a
table of contents, map each page to its section title so citations are checkable
against the original document (PRD FR-05). Scanned/image PDFs that yield no text
raise a clear error instead of failing silently (FR-03 acceptance criterion).
"""

from __future__ import annotations

import os
from typing import List

import config


class ExtractionError(Exception):
    """Raised when a file cannot be turned into usable text."""


def _section_for_page(toc, page_no: int):
    """Best-effort section label from the PDF outline (TOC)."""
    if not toc:
        return None
    current = None
    for _level, title, dest_page in toc:
        if dest_page is None or dest_page < 0:
            continue
        if dest_page <= page_no:
            current = title
        else:
            break
    return current


def _chunk_text(text: str, page: int, section) -> List[dict]:
    """Split a page's text into overlapping chunks under CHUNK_MAX_CHARS."""
    text = " ".join(text.split())
    if not text:
        return []
    size = config.CHUNK_MAX_CHARS
    overlap = config.CHUNK_OVERLAP_CHARS
    chunks: List[dict] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        piece = text[start:end].strip()
        if piece:
            chunks.append({"page": page, "section": section, "content": piece})
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks


def extract_pdf(path: str) -> List[dict]:
    import fitz  # PyMuPDF

    doc = fitz.open(path)
    try:
        toc = doc.get_toc(simple=True)
        chunks: List[dict] = []
        total_chars = 0
        for page_index in range(doc.page_count):
            page = doc.load_page(page_index)
            page_text = page.get_text("text")
            total_chars += len(page_text.strip())
            chunks.extend(
                _chunk_text(page_text, page=page_index + 1,
                            section=_section_for_page(toc, page_index + 1))
            )
        if total_chars == 0:
            raise ExtractionError(
                "No extractable text found. The PDF appears to be scanned or "
                "image-only; OCR is out of scope for this MVP (PRD P2)."
            )
        return chunks
    finally:
        doc.close()


def extract_text_file(path: str) -> List[dict]:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        content = fh.read()
    if not content.strip():
        raise ExtractionError("The text file is empty.")
    # Treat the whole file as one "page" then chunk it.
    return _chunk_text(content, page=1, section=None)


def extract(path: str) -> List[dict]:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return extract_pdf(path)
    if ext in (".txt", ".md"):
        return extract_text_file(path)
    raise ExtractionError(f"Unsupported file type: {ext or 'unknown'}")
