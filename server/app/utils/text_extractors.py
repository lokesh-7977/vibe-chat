from __future__ import annotations

import io
import re

from pypdf import PdfReader


def extract_text_from_document_bytes(data: bytes, *, mime_type: str) -> str:
    mt = (mime_type or "").lower().strip()
    if mt == "application/pdf" or data[:4] == b"%PDF":
        reader = PdfReader(io.BytesIO(data))
        parts: list[str] = []
        for page in reader.pages:
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                continue
        text = "\n".join(parts).strip()
        if not text:
            raise RuntimeError("Unable to extract text from PDF")
        return text

    if mt in {"text/plain", "text/markdown"}:
        return data.decode("utf-8", errors="replace")

    # Basic fallback.
    return data.decode("utf-8", errors="replace")


def chunk_text(text: str, *, max_chars: int = 1400, overlap: int = 150) -> list[str]:
    cleaned = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not cleaned:
        return []

    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=max_chars,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        return [c for c in splitter.split_text(cleaned) if c.strip()]
    except Exception:
        chunks: list[str] = []
        i = 0
        while i < len(cleaned):
            end = min(len(cleaned), i + max_chars)
            chunk = cleaned[i:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(cleaned):
                break
            i = max(0, end - overlap)
        return chunks
