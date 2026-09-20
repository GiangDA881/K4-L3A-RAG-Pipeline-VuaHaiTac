"""
Task 5 — Semantic search.

Embed query bằng chính hàm của Task 4, query ChromaDB và đổi cosine distance
thành similarity. Output phải theo SearchResult, sort giảm dần và không quá top_k.
"""

from .contracts import validate_search_results
from .task4_chunking_indexing import embed_texts, get_collection


def _result_metadata(raw: dict | None) -> dict:
    data = raw or {}
    chunk_index = data.get("chunk_index", 0)
    if isinstance(chunk_index, str) and chunk_index.isdigit():
        chunk_index = int(chunk_index)
    url = data.get("url")
    if url == "":
        url = None
    return {
        "source": str(data.get("source") or ""),
        "title": str(data.get("title") or ""),
        "doc_type": str(data.get("doc_type") or ""),
        "url": url if url is None or isinstance(url, str) else str(url),
        "chunk_index": int(chunk_index),
    }


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về dense SearchResult theo score giảm dần."""
    if top_k <= 0:
        return []

    collection = get_collection()
    n_results = top_k
    count_fn = getattr(collection, "count", None)
    if callable(count_fn):
        count = count_fn()
        if count == 0:
            return []
        n_results = min(top_k, count)

    query_vector = embed_texts([query])[0]
    response = collection.query(
        query_embeddings=[query_vector],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    ids = (response.get("ids") or [[]])[0]
    documents = (response.get("documents") or [[]])[0]
    metadatas = (response.get("metadatas") or [[]])[0]
    distances = (response.get("distances") or [[]])[0]

    results: list[dict] = []
    seen: set[str] = set()
    for item_id, content, metadata, distance in zip(ids, documents, metadatas, distances):
        if not item_id or item_id in seen:
            continue
        seen.add(item_id)
        results.append(
            {
                "id": item_id,
                "content": content or "",
                "score": max(0.0, 1.0 - float(distance)),
                "metadata": _result_metadata(metadata),
                "retrieval_method": "dense",
            }
        )
    results.sort(key=lambda item: (-item["score"], item["id"]))
    output = results[:top_k]
    validate_search_results(output, top_k=top_k, expected_method="dense")
    return output


if __name__ == "__main__":
    for result in semantic_search("visa e-visa 90 ngày khách du lịch Việt Nam", top_k=3):
        print(f"{result['score']:.3f} {result['id']} {result['metadata']['title']}")
