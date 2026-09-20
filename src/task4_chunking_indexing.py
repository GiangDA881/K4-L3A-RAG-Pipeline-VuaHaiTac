"""
Task 4 — Chunking, embedding và indexing.

Đọc Markdown trong data/standardized/, chia recursive 500/50, embed bằng
cùng một model rồi upsert ChromaDB (cosine). ID ổn định
`{doc_id}::chunk-{index}` nên chạy lại không nhân bản. Task 5 phải gọi
lại `embed_texts()`.

Tham số giữ starter: CHUNK_SIZE=500, CHUNK_OVERLAP=50, recursive.
Corpus Du lịch Việt Nam có cả điều luật dài và trang tin; 500 ký tự đủ để
giữ một điều/đoạn, overlap 50 giữ câu bị cắt ở biên. Ghi lại các giá trị
này khi đánh giá.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .contracts import validate_document


load_dotenv()

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers").strip()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3").strip() or "BAAI/bge-m3"
EMBEDDING_DIM = 1024
EMBED_BATCH_SIZE = 32

COLLECTION_NAME = "rag_documents"

_HEADING_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_SOURCE_RE = re.compile(r"\*\*Source:\*\*\s*(\S+)")


def _parse_title(content: str, fallback: str) -> str:
    match = _HEADING_RE.search(content)
    title = match.group(1).strip() if match else fallback
    return title or fallback


def _parse_url(content: str) -> str | None:
    match = _SOURCE_RE.search(content)
    if not match:
        return None
    value = match.group(1).strip().strip("`")
    if value.startswith("http://") or value.startswith("https://"):
        return value
    return None


def _chroma_metadata(metadata: dict) -> dict:
    url = metadata.get("url")
    return {
        "source": str(metadata["source"]),
        "title": str(metadata["title"]),
        "doc_type": str(metadata["doc_type"]),
        "url": url if isinstance(url, str) and url else "",
        "chunk_index": int(metadata["chunk_index"]),
    }


@lru_cache(maxsize=1)
def _sentence_transformer():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed texts with the shared provider used for both corpus and queries."""
    if not texts:
        return []
    provider = EMBEDDING_PROVIDER.lower()
    if provider in {"sentence_transformers", "local", ""}:
        model = _sentence_transformer()
        vectors: list[list[float]] = []
        for start in range(0, len(texts), EMBED_BATCH_SIZE):
            batch = texts[start : start + EMBED_BATCH_SIZE]
            encoded = model.encode(
                batch,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            vectors.extend(encoded.tolist())
        return vectors
    raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {EMBEDDING_PROVIDER}")


def get_collection():
    """Mở Chroma collection dùng cosine distance."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
        embedding_function=None,
    )


def load_documents() -> list[dict]:
    """Đọc Markdown và trả về danh sách Document."""
    documents: list[dict] = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue
        doc_type = "legal" if "legal" in path.parts else "news"
        document = {
            "id": path.relative_to(STANDARDIZED_DIR).as_posix(),
            "content": content,
            "metadata": {
                "source": path.name,
                "title": _parse_title(content, path.stem),
                "doc_type": doc_type,
                "url": _parse_url(content),
            },
        }
        validate_document(document)
        documents.append(document)
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id và chunk_index."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks: list[dict] = []
    for document in documents:
        pieces = [text.strip() for text in splitter.split_text(document["content"]) if text.strip()]
        if not pieces:
            continue
        for index, text in enumerate(pieces):
            chunk = {
                "id": f"{document['id']}::chunk-{index}",
                "content": text,
                "metadata": {
                    **document["metadata"],
                    "chunk_index": index,
                },
            }
            validate_document(chunk, require_chunk=True)
            chunks.append(chunk)
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk."""
    vectors = embed_texts([chunk["content"] for chunk in chunks])
    embedded: list[dict] = []
    for chunk, vector in zip(chunks, vectors, strict=True):
        item = dict(chunk)
        item["embedding"] = vector
        embedded.append(item)
    return embedded


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB và xóa ID cũ không còn trong corpus."""
    collection = get_collection()
    if not chunks:
        existing = collection.get(include=[])
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
        return

    batch_size = 100
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        collection.upsert(
            ids=[chunk["id"] for chunk in batch],
            documents=[chunk["content"] for chunk in batch],
            embeddings=[chunk["embedding"] for chunk in batch],
            metadatas=[_chroma_metadata(chunk["metadata"]) for chunk in batch],
        )

    current_ids = {chunk["id"] for chunk in chunks}
    existing = collection.get(include=[])
    stale = [item_id for item_id in existing["ids"] if item_id not in current_ids]
    if stale:
        collection.delete(ids=stale)


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    chunks = chunk_documents(documents)
    embedded_chunks = embed_chunks(chunks)
    index_to_vectorstore(embedded_chunks)
    collection = get_collection()
    print(
        f"Indexed {len(embedded_chunks)} chunks from {len(documents)} documents "
        f"(collection count={collection.count()})"
    )
    print(
        f"chunking={CHUNKING_METHOD} size={CHUNK_SIZE} overlap={CHUNK_OVERLAP} "
        f"model={EMBEDDING_MODEL}"
    )
    for chunk in embedded_chunks[:3]:
        meta = chunk["metadata"]
        print(
            f"  {chunk['id']} | {meta['doc_type']} | {meta['source']} | "
            f"chunk_index={meta['chunk_index']} | url={meta['url']}"
        )


if __name__ == "__main__":
    run_pipeline()
