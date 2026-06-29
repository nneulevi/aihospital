"""Markdown knowledge-base parsing for RAG ingestion."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import RAG_CHUNK_MAX_CHARS, RAG_CHUNK_OVERLAP_CHARS


KNOWLEDGE_DIR = Path(__file__).resolve().parent / "knowledge"


@dataclass(frozen=True)
class KnowledgeDocument:
    source_id: str
    title: str
    doc_type: str
    tags: list[str]
    version: str
    language: str
    content: str
    content_hash: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class KnowledgeChunk:
    source_id: str
    source_document_id: str
    title: str
    doc_type: str
    tags: list[str]
    version: str
    language: str
    content: str
    content_hash: str
    metadata: dict[str, Any]


def _parse_scalar(value: str) -> Any:
    text = value.strip()
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("'\"") for item in inner.split(",") if item.strip()]
    return text.strip("'\"")


def parse_front_matter(markdown: str) -> tuple[dict[str, Any], str]:
    markdown = markdown.lstrip("\ufeff")
    if not markdown.startswith("---"):
        return {}, markdown.strip()
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", markdown, re.DOTALL)
    if not match:
        return {}, markdown.strip()
    metadata: dict[str, Any] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.strip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = _parse_scalar(value)
    return metadata, match.group(2).strip()


def parse_markdown_file(path: Path) -> KnowledgeDocument:
    metadata, content = parse_front_matter(path.read_text(encoding="utf-8-sig"))
    source_id = str(metadata.get("source_id") or path.stem)
    title = str(metadata.get("title") or path.stem)
    doc_type = str(metadata.get("type") or metadata.get("doc_type") or "project_guideline")
    tags = metadata.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    version = str(metadata.get("version") or "v1")
    language = str(metadata.get("language") or "zh-CN")
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return KnowledgeDocument(
        source_id=source_id,
        title=title,
        doc_type=doc_type,
        tags=[str(tag) for tag in tags],
        version=version,
        language=language,
        content=content,
        content_hash=content_hash,
        metadata=metadata,
    )


def load_knowledge_documents(knowledge_dir: Path = KNOWLEDGE_DIR) -> list[KnowledgeDocument]:
    if not knowledge_dir.exists():
        return []
    return [parse_markdown_file(path) for path in sorted(knowledge_dir.glob("*.md"))]


def _split_oversized_text(text: str, *, max_chars: int, overlap_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        if end < len(text):
            boundary_candidates = [
                text.rfind("\n\n", start, end),
                text.rfind("。", start, end),
                text.rfind("；", start, end),
                text.rfind(".", start, end),
                text.rfind(" ", start, end),
            ]
            boundary = max(boundary_candidates)
            if boundary > start + max_chars // 2:
                end = boundary + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(0, end - overlap_chars)
    return chunks


def _iter_heading_sections(content: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    current_heading = ""
    current_lines: list[str] = []
    for line in content.splitlines():
        if line.startswith("#"):
            if current_lines:
                sections.append((current_heading, "\n".join(current_lines).strip()))
                current_lines = []
            current_heading = line.lstrip("#").strip()
            current_lines.append(line)
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_heading, "\n".join(current_lines).strip()))
    return [(heading, text) for heading, text in sections if text]


def split_document_into_chunks(
    document: KnowledgeDocument,
    *,
    max_chars: int = RAG_CHUNK_MAX_CHARS,
    overlap_chars: int = RAG_CHUNK_OVERLAP_CHARS,
) -> list[KnowledgeChunk]:
    """Split one knowledge document into retrieval chunks.

    The external source id remains stable through metadata; each chunk gets a
    deterministic source_id suffix so old whole-document rows can be disabled
    without losing traceability.
    """

    safe_max_chars = max(300, int(max_chars))
    safe_overlap = max(0, min(int(overlap_chars), safe_max_chars // 3))
    chunks: list[KnowledgeChunk] = []
    sections = _iter_heading_sections(document.content) or [("", document.content)]
    for heading, section_text in sections:
        for piece in _split_oversized_text(section_text, max_chars=safe_max_chars, overlap_chars=safe_overlap):
            ordinal = len(chunks)
            chunk_title = document.title if not heading else f"{document.title} / {heading}"
            contextual_content = f"Title: {document.title}\n"
            if heading:
                contextual_content += f"Section: {heading}\n"
            contextual_content += piece
            content_hash = hashlib.sha256(
                f"{document.source_id}:{ordinal}:{contextual_content}".encode("utf-8")
            ).hexdigest()
            metadata = {
                **document.metadata,
                "source_document_id": document.source_id,
                "chunk_id": f"{document.source_id}#chunk-{ordinal:03d}",
                "chunk_index": ordinal,
                "chunk_count_hint": None,
                "heading": heading,
                "retrieval_unit": "chunk",
                "source_title": document.title,
            }
            chunks.append(
                KnowledgeChunk(
                    source_id=f"{document.source_id}#chunk-{ordinal:03d}",
                    source_document_id=document.source_id,
                    title=chunk_title,
                    doc_type=document.doc_type,
                    tags=document.tags,
                    version=document.version,
                    language=document.language,
                    content=contextual_content,
                    content_hash=content_hash,
                    metadata=metadata,
                )
            )
    chunk_count = len(chunks)
    return [
        KnowledgeChunk(
            source_id=chunk.source_id,
            source_document_id=chunk.source_document_id,
            title=chunk.title,
            doc_type=chunk.doc_type,
            tags=chunk.tags,
            version=chunk.version,
            language=chunk.language,
            content=chunk.content,
            content_hash=chunk.content_hash,
            metadata={**chunk.metadata, "chunk_count_hint": chunk_count},
        )
        for chunk in chunks
    ]


def load_knowledge_chunks(knowledge_dir: Path = KNOWLEDGE_DIR) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    for document in load_knowledge_documents(knowledge_dir):
        chunks.extend(split_document_into_chunks(document))
    return chunks
